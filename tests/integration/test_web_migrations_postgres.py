"""Alembic adoption tests: opt-in, initially empty disposable PostgreSQL only."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration


def test_web_migrations_adopt_preserve_and_reject_drift() -> None:
    url = os.environ.get("TEST_WEB_MIGRATION_DATABASE_URL")
    if not url:
        pytest.skip("TEST_WEB_MIGRATION_DATABASE_URL requires fresh disposable PostgreSQL")
    assert os.environ.get("TEST_WEB_ISOLATED") == "1"
    assert url.startswith("postgresql+asyncpg://")
    assert url not in {
        os.environ.get("DATABASE_URL"), os.environ.get("TEST_DATABASE_URL"),
        os.environ.get("TEST_MIGRATION_DATABASE_URL"),
    }
    root = Path(__file__).resolve().parents[2]
    env = os.environ | {
        "DATABASE_URL": url, "APP_ENV": "test", "OIDC_ENABLED": "false", "CORS_ORIGINS": "[]",
    }

    def alembic(*arguments: str, success: bool = True) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments], cwd=root / "apps/api",
            env=env, capture_output=True, text=True, check=False,
        )
        # Do not include SQL/connection context from subprocesses in failures.
        assert (result.returncode == 0) == success, "Unexpected Alembic migration result"

    async def sql(statement: str) -> list[tuple[object, ...]]:
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                result = await connection.execute(text(statement))
                return [tuple(row) for row in result] if result.returns_rows else []
        finally:
            await engine.dispose()

    def query(statement: str) -> list[tuple[object, ...]]:
        return asyncio.run(sql(statement))

    assert query(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema NOT IN ('pg_catalog','information_schema')"
    ) == [(0,)], "Database must start empty; never reset existing data"
    alembic("upgrade", "0004_semantic_editorial")
    query("CREATE SCHEMA legacy_probe")
    query("CREATE TABLE legacy_probe.records (value text)")
    query("INSERT INTO legacy_probe.records VALUES ('preserved')")

    def legacy(name: str) -> None:
        # Historical SQL is only a fixture for pre-Alembic databases.
        script = (root / "apps/web/migrations" / f"{name}.up.sql").read_text()
        script = "\n".join(
            line for line in script.splitlines() if not line.lstrip().startswith("--")
        )
        for statement in script.split(";"):
            if statement.strip() not in {"", "BEGIN", "COMMIT"}:
                query(statement)

    for installed in (0, 1, 2):
        if installed:
            legacy("0001_oidc_sessions")
            query("INSERT INTO libris_web.sessions VALUES (repeat('a',64),'opaque-session',123)")
            query(
                "INSERT INTO libris_web.auth_transactions "
                "VALUES (repeat('b',64),repeat('c',64),'opaque-transaction',456)"
            )
        if installed == 2:
            legacy("0002_auth_quotas")
            query("INSERT INTO libris_web.auth_quotas VALUES ('login',now(),7)")
        alembic("upgrade", "head")
        alembic("check")
        assert query("SELECT count(*) FROM libris_web.auth_quotas") == [
            (1 if installed == 2 else 0,)
        ]
        if installed:
            assert query("SELECT payload,expires_at FROM libris_web.sessions") == [
                ("opaque-session", 123)
            ]
            assert query("SELECT payload,expires_at FROM libris_web.auth_transactions") == [
                ("opaque-transaction", 456)
            ]
        if installed == 2:
            assert query("SELECT attempts FROM libris_web.auth_quotas") == [(7,)]
        # Rollback of this adoption boundary deliberately retains all BFF data.
        before = query("SELECT * FROM libris_web.sessions")
        alembic("downgrade", "0004_semantic_editorial")
        assert query("SELECT * FROM libris_web.sessions") == before
        alembic("upgrade", "head")
        assert query("SELECT * FROM libris_web.sessions") == before
        alembic("downgrade", "0004_semantic_editorial")
        assert query("SELECT value FROM legacy_probe.records") == [("preserved",)]
        # Only the schema created in this initially empty, opt-in test database.
        query("DROP SCHEMA libris_web CASCADE")

    for drift in (
        "ALTER TABLE libris_web.sessions ALTER COLUMN expires_at TYPE text",
        "ALTER TABLE libris_web.sessions DROP CONSTRAINT sessions_id_hash_check",
        "ALTER TABLE libris_web.sessions ADD COLUMN unexpected text",
        (
            "DROP INDEX libris_web.sessions_expiry; "
            "CREATE INDEX sessions_expiry ON libris_web.sessions (payload)"
        ),
    ):
        legacy("0001_oidc_sessions")
        query("INSERT INTO libris_web.sessions VALUES (repeat('a',64),'keep',123)")
        for statement in drift.split(";"):
            query(statement)
        alembic("upgrade", "head", success=False)
        assert query("SELECT payload FROM libris_web.sessions") == [("keep",)]
        assert query("SELECT version_num FROM alembic_version") == [("0004_semantic_editorial",)]
        assert query("SELECT to_regclass('libris_web.auth_quotas')") == [(None,)]
        query("DROP SCHEMA libris_web CASCADE")
    assert query("SELECT value FROM legacy_probe.records") == [("preserved",)]
