"""Editorial metadata and governed audit taxonomy; no historical state backfill."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_semantic_editorial"
down_revision: str | None = "0003_semantic_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EDITORIAL_CHECKS = {
    "ck_editorial_positive": ("version > 0 AND current_revision > 0"),
    "ck_editorial_state": (
        "editorial_state IN ('draft','in_review','approved','published','withdrawn','archived')"
    ),
    "ck_editorial_pointers": (
        "(approved_revision IS NULL OR approved_revision BETWEEN 1 AND current_revision) "
        "AND (published_revision IS NULL OR published_revision BETWEEN 1 AND "
        "current_revision)"
    ),
    "ck_editorial_public": (
        "(editorial_state IN ('published','withdrawn','archived') AND published_revision "
        "IS NOT NULL) OR (editorial_state IN ('draft','in_review','approved') AND "
        "published_revision IS NULL)"
    ),
    "ck_editorial_candidate": (
        "(candidate_state IS NULL AND (editorial_state NOT IN ('published','withdrawn') "
        "OR current_revision = published_revision)) OR (candidate_state IS NOT NULL AND "
        "candidate_state IN ('draft','in_review','approved') AND editorial_state IN "
        "('published','withdrawn') AND current_revision <> published_revision)"
    ),
    "ck_editorial_approval": (
        "COALESCE((CASE WHEN COALESCE(candidate_state,editorial_state) = 'approved' THEN "
        "approved_revision = current_revision WHEN "
        "COALESCE(candidate_state,editorial_state) IN ('draft','in_review') THEN "
        "approved_revision IS NULL WHEN candidate_state IS NULL AND editorial_state IN "
        "('published','withdrawn') THEN approved_revision = published_revision ELSE "
        "approved_revision IS NULL END), false)"
    ),
}
NEW_AUDIT_CHECKS = {
    "ck_audit_type": (
        "event_type IN "
        "('record.created','record.revised','record.submitted','record.approved','record.published','record.withdrawn','record.restored','record.superseded','record.returned','record.archived')"
    ),
    "ck_audit_states": (
        "(event_type IN ('record.created','record.revised','record.superseded') OR "
        "(event_type = 'record.restored' AND restoration_kind = 'content')) AND "
        "previous_state IS NULL AND new_state IS NULL AND scope IS NULL AND "
        "previous_version IS NULL AND new_version IS NULL OR (previous_state IS NOT NULL "
        "AND new_state IS NOT NULL AND scope IS NOT NULL AND previous_version IS NOT NULL"
        " AND new_version IS NOT NULL AND actor_type IS NOT NULL AND actor_type = 'human'"
        " AND previous_version > 0 AND new_version = previous_version + 1 AND "
        "((event_type = 'record.submitted' AND previous_state = 'draft' AND new_state = "
        "'in_review' AND scope IN ('record','candidate')) OR (event_type = "
        "'record.approved' AND previous_state = 'in_review' AND new_state = 'approved' "
        "AND scope IN ('record','candidate')) OR (event_type = 'record.published' AND "
        "previous_state = 'approved' AND new_state = 'published' AND scope IN "
        "('record','candidate')) OR (event_type = 'record.withdrawn' AND previous_state ="
        " 'published' AND new_state = 'withdrawn' AND scope = 'record' AND reason IS NOT "
        "NULL) OR (event_type = 'record.returned' AND previous_state IN "
        "('in_review','approved') AND new_state = 'draft' AND scope IN "
        "('record','candidate') AND reason IS NOT NULL) OR (event_type = "
        "'record.archived' AND previous_state = 'withdrawn' AND new_state = 'archived' "
        "AND scope = 'record' AND reason IS NOT NULL) OR (event_type = 'record.restored' "
        "AND restoration_kind = 'editorial' AND previous_state = 'withdrawn' AND "
        "new_state = 'published' AND scope = 'record')))"
    ),
}
OLD_AUDIT_CHECKS = {
    "ck_audit_type": (
        "event_type IN "
        "('record.created','record.revised','record.submitted','record.approved','record.published','record.withdrawn','record.restored','record.superseded')"
    ),
    "ck_audit_states": (
        "(event_type IN ('record.created','record.revised','record.superseded') OR "
        "(event_type = 'record.restored' AND restoration_kind = 'content')) AND "
        "previous_state IS NULL AND new_state IS NULL AND scope IS NULL AND "
        "previous_version IS NULL AND new_version IS NULL OR (previous_state IS NOT NULL "
        "AND new_state IS NOT NULL AND scope IS NOT NULL AND previous_version IS NOT NULL"
        " AND new_version IS NOT NULL AND actor_type IS NOT NULL AND actor_type = 'human'"
        " AND previous_version > 0 AND new_version = previous_version + 1 AND "
        "((event_type = 'record.submitted' AND previous_state = 'draft' AND new_state = "
        "'in_review' AND scope IN ('record','candidate')) OR (event_type = "
        "'record.approved' AND previous_state = 'in_review' AND new_state = 'approved' "
        "AND scope IN ('record','candidate')) OR (event_type = 'record.published' AND "
        "previous_state = 'approved' AND new_state = 'published' AND scope IN "
        "('record','candidate')) OR (event_type = 'record.withdrawn' AND previous_state ="
        " 'published' AND new_state = 'withdrawn' AND scope = 'record' AND reason IS NOT "
        "NULL) OR (event_type = 'record.restored' AND restoration_kind = 'editorial' AND "
        "previous_state = 'withdrawn' AND new_state = 'published' AND scope = 'record')))"
    ),
}


def upgrade() -> None:
    op.create_table(
        "experimental_semantic_editorial_states",
        sa.Column("resource_id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("editorial_state", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("current_revision", sa.Integer(), nullable=False),
        sa.Column("approved_revision", sa.Integer(), nullable=True),
        sa.Column("published_revision", sa.Integer(), nullable=True),
        sa.Column("candidate_state", sa.String(), nullable=True),
        *(
            sa.CheckConstraint(expression, name=name)
            for name, expression in EDITORIAL_CHECKS.items()
        ),
        *(
            sa.ForeignKeyConstraint(
                ["resource_id", field],
                [
                    "experimental_semantic_revisions.resource_id",
                    "experimental_semantic_revisions.number",
                ],
                name=f"fk_editorial_{field}",
            )
            for field in ("current_revision", "approved_revision", "published_revision")
        ),
    )
    for name, expression in NEW_AUDIT_CHECKS.items():
        op.drop_constraint(name, "experimental_semantic_audit_events", type_="check")
        op.create_check_constraint(name, "experimental_semantic_audit_events", expression)
    op.create_index(
        "ix_audit_editorial_version",
        "experimental_semantic_audit_events",
        ["resource_id", "new_version"],
        postgresql_where=sa.text("new_version IS NOT NULL"),
    )


def downgrade() -> None:
    # Refuse to reinterpret or erase RETURN/ARCHIVE evidence under the old taxonomy.
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM experimental_semantic_audit_events
        WHERE event_type IN ('record.returned','record.archived')) THEN
        RAISE EXCEPTION 'Downgrade incompatível com eventos RETURN/ARCHIVE';
        END IF; END $$""")
    op.drop_index("ix_audit_editorial_version", table_name="experimental_semantic_audit_events")
    for name, expression in OLD_AUDIT_CHECKS.items():
        op.drop_constraint(name, "experimental_semantic_audit_events", type_="check")
        op.create_check_constraint(name, "experimental_semantic_audit_events", expression)
    op.drop_table("experimental_semantic_editorial_states")
