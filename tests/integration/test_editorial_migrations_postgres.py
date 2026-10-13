"""Incremental 0003->0004 verification in a separate, initially empty PostgreSQL database."""

import asyncio
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from test_audit_postgres import actor, graph_for

from libris.modules.bibliographic.application.audit import content_event, editorial_event
from libris.modules.bibliographic.application.editorial import EditorialService
from libris.modules.bibliographic.application.editorial_postgres import (
    PostgresEditorialTransactions,
)
from libris.modules.bibliographic.application.history import HistoryService
from libris.modules.bibliographic.application.service import prepare_document
from libris.modules.bibliographic.domain.audit import AuditEventType
from libris.modules.bibliographic.domain.editorial import EditorialRecord, prepare_transition
from libris.modules.bibliographic.domain.models import Provenance, ResourceIdentity, Revision
from libris.modules.bibliographic.infrastructure.audit import AuditStore
from libris.modules.bibliographic.infrastructure.persistence import RevisionStore
from libris.modules.bibliographic.infrastructure.validation import INSTITUTIONAL_PROFILE_ID

pytestmark = pytest.mark.integration


def test_editorial_upgrade_from_previous_head_and_safe_downgrade() -> None:
    url = os.environ.get("TEST_EDITORIAL_MIGRATION_DATABASE_URL")
    if not url:
        pytest.skip("TEST_EDITORIAL_MIGRATION_DATABASE_URL exige terceiro banco vazio descartável.")
    if not url.startswith("postgresql+asyncpg://") or url in {
        os.environ.get("TEST_DATABASE_URL"),
        os.environ.get("TEST_MIGRATION_DATABASE_URL"),
    }:
        pytest.fail("Migração exige PostgreSQL descartável exclusivo e vazio.")
    api = Path(__file__).resolve().parents[2] / "apps/api"

    def alembic(*arguments: str, succeeds: bool = True) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=api,
            env=os.environ | {"DATABASE_URL": url},
            capture_output=True,
            text=True,
            check=False,
        )
        if succeeds:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0
            assert "Downgrade incompatível" in result.stdout + result.stderr

    async def assert_empty() -> None:
        engine = create_async_engine(url)
        try:
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(
                        text(
                            "SELECT count(*) FROM information_schema.tables "
                            "WHERE table_schema='public'"
                        )
                    )
                    == 0
                ), "Banco deve começar vazio; nunca migrar dados de trabalho."
        finally:
            await engine.dispose()

    asyncio.run(assert_empty())
    alembic("upgrade", "0003_semantic_audit")
    identity = ResourceIdentity(uuid4(), f"https://legacy43.example.invalid/{uuid4()}")
    revision = Revision(
        identity, 1, datetime.now(UTC), Provenance("legacy", "legacy"), INSTITUTIONAL_PROFILE_ID
    )
    document = prepare_document(graph_for(identity), identity.uri, revision.profile)

    async def seed() -> None:
        engine = create_async_engine(url)
        try:
            sessions = async_sessionmaker(engine)
            async with sessions() as session, session.begin():
                await RevisionStore().create(session, identity)
                await RevisionStore().save(session, revision, document)
                await AuditStore().append(
                    session, content_event(revision, AuditEventType.CREATED, None)
                )
                # Valid envelopes accepted by #28; no persisted state and repeated version.
                for _ in range(2):
                    change = prepare_transition(
                        EditorialRecord(identity),
                        "in_review",
                        expected_version=1,
                        expected_current_revision=1,
                        selected_revision=1,
                        actor_id=actor().actor_id,
                        occurred_at=datetime.now(UTC),
                    )
                    await AuditStore().append(
                        session,
                        editorial_event(
                            change.event, revision, Provenance("legacy", "prepared"), actor=actor()
                        ),
                    )
        finally:
            await engine.dispose()

    asyncio.run(seed())

    async def snapshot() -> tuple[object, ...]:
        engine = create_async_engine(url)
        try:
            async with engine.connect() as connection:
                stored = (
                    await connection.execute(
                        text("SELECT * FROM experimental_semantic_revisions WHERE resource_id=:id"),
                        {"id": identity.internal_id},
                    )
                ).one()
                events = (
                    await connection.execute(
                        text(
                            "SELECT * FROM experimental_semantic_audit_events "
                            "WHERE resource_id=:id "
                            "ORDER BY occurred_at,event_id"
                        ),
                        {"id": identity.internal_id},
                    )
                ).all()
                return tuple(stored), tuple(tuple(event) for event in events)
        finally:
            await engine.dispose()

    before = asyncio.run(snapshot())
    alembic("upgrade", "head")
    alembic("check")
    assert asyncio.run(snapshot()) == before

    async def verify_legacy() -> None:
        engine = create_async_engine(url)
        try:
            history = await HistoryService(async_sessionmaker(engine)).read_editorial(
                identity.internal_id, actor=actor()
            )
            assert history.state is None and len(history.events) == 3
            assert history.current == revision
        finally:
            await engine.dispose()

    asyncio.run(verify_legacy())
    alembic("downgrade", "0003_semantic_audit")
    assert asyncio.run(snapshot()) == before
    alembic("upgrade", "head")
    asyncio.run(verify_legacy())

    async def return_record() -> None:
        engine = create_async_engine(url)
        try:
            factory = PostgresEditorialTransactions(
                async_sessionmaker(engine),
                actor=actor(),
                provenance=Provenance("fixture", "editorial"),
            )
            service = EditorialService(factory)
            for version, target in ((1, "in_review"), (2, "draft")):
                await service.transition(
                    identity.internal_id,
                    target,
                    actor=actor(),
                    expected_version=version,
                    expected_current_revision=1,
                    selected_revision=1,
                    justification="Synthetic return" if target == "draft" else None,
                )
        finally:
            await engine.dispose()

    asyncio.run(return_record())
    final = asyncio.run(snapshot())
    alembic("downgrade", "0003_semantic_audit", succeeds=False)
    assert asyncio.run(snapshot()) == final
    alembic("check")
