"""Observed immutable audit events; destructive downgrade only in disposable databases."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_semantic_audit"
down_revision: str | None = "0002_revision_actor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "experimental_semantic_revisions", sa.Column("reason", sa.String(), nullable=True)
    )
    op.create_table(
        "experimental_semantic_audit_events",
        sa.Column("event_id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column("actor_type", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("process", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("previous_state", sa.String(), nullable=True),
        sa.Column("new_state", sa.String(), nullable=True),
        sa.Column("related_resource_id", sa.Uuid(), nullable=True),
        sa.Column("restoration_kind", sa.String(), nullable=True),
        sa.Column("source_revision", sa.Integer(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("previous_version", sa.Integer(), nullable=True),
        sa.Column("new_version", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('record.created','record.revised','record.submitted',"
            "'record.approved','record.published','record.withdrawn',"
            "'record.restored','record.superseded')",
            name="ck_audit_type",
        ),
        sa.CheckConstraint(
            "revision_number > 0 AND (event_type <> 'record.created' OR revision_number = "
            "1) AND (event_type <> 'record.revised' OR revision_number > 1)",
            name="ck_audit_revision",
        ),
        sa.CheckConstraint(
            "length(trim(source)) > 0 AND length(trim(process)) > 0", name="ck_audit_source"
        ),
        sa.CheckConstraint("reason IS NULL OR length(trim(reason)) > 0", name="ck_audit_reason"),
        sa.CheckConstraint(
            '(actor_id IS NULL AND actor_type IS NULL) OR (actor_id IS NOT NULL AND '
            "actor_type IS NOT NULL AND ((actor_type = 'human' AND actor_id ~ "
            "'^oidc:sha256:[0-9a-f]{64}$') OR (actor_type IN ('service','automated') AND "
            "actor_id ~ ('^' || actor_type || ':[a-z][a-z0-9_.-]{0,63}$'))))",
            name="ck_audit_actor",
        ),
        sa.CheckConstraint(
            "(event_type = 'record.superseded' AND related_resource_id IS NOT NULL AND "
            'related_resource_id <> resource_id AND reason IS NOT NULL) OR (event_type <> '
            "'record.superseded' AND related_resource_id IS NULL)",
            name="ck_audit_successor",
        ),
        sa.CheckConstraint(
            "(event_type <> 'record.restored' AND restoration_kind IS NULL AND "
            "source_revision IS NULL) OR (event_type = 'record.restored' AND "
            "restoration_kind IS NOT NULL AND ((restoration_kind = 'content' AND "
            'source_revision IS NOT NULL AND source_revision > 0 AND source_revision < '
            "revision_number) OR (restoration_kind = 'editorial' AND source_revision IS "
            'NULL)))',
            name="ck_audit_restore",
        ),
        sa.CheckConstraint(
            "(event_type IN ('record.created','record.revised','record.superseded') OR "
            "(event_type = 'record.restored' AND restoration_kind = 'content')) AND "
            'previous_state IS NULL AND new_state IS NULL AND scope IS NULL AND '
            'previous_version IS NULL AND new_version IS NULL OR (previous_state IS NOT '
            'NULL AND new_state IS NOT NULL AND scope IS NOT NULL AND previous_version IS '
            'NOT NULL AND new_version IS NOT NULL AND actor_type IS NOT NULL AND '
            "actor_type = 'human' AND previous_version > 0 AND new_version = "
            "previous_version + 1 AND ((event_type = 'record.submitted' AND previous_state "
            "= 'draft' AND new_state = 'in_review' AND scope IN ('record','candidate')) OR "
            "(event_type = 'record.approved' AND previous_state = 'in_review' AND "
            "new_state = 'approved' AND scope IN ('record','candidate')) OR (event_type = "
            "'record.published' AND previous_state = 'approved' AND new_state = "
            "'published' AND scope IN ('record','candidate')) OR (event_type = "
            "'record.withdrawn' AND previous_state = 'published' AND new_state = "
            "'withdrawn' AND scope = 'record' AND reason IS NOT NULL) OR (event_type = "
            "'record.restored' AND restoration_kind = 'editorial' AND previous_state = "
            "'withdrawn' AND new_state = 'published' AND scope = 'record')))",
            name="ck_audit_states",
        ),
        sa.ForeignKeyConstraint(
            ["resource_id", "revision_number"],
            [
                "experimental_semantic_revisions.resource_id",
                "experimental_semantic_revisions.number",
            ],
            name="fk_audit_revision",
        ),
        sa.ForeignKeyConstraint(
            ["resource_id", "source_revision"],
            [
                "experimental_semantic_revisions.resource_id",
                "experimental_semantic_revisions.number",
            ],
            name="fk_audit_source_revision",
        ),
        sa.ForeignKeyConstraint(
            ["related_resource_id"],
            ["experimental_semantic_resources.id"],
            name="fk_audit_successor",
        ),
    )
    op.create_index(
        "ix_audit_resource_time",
        "experimental_semantic_audit_events",
        ["resource_id", "occurred_at", "event_id"],
    )
    op.create_index(
        "ix_audit_resource_revision",
        "experimental_semantic_audit_events",
        ["resource_id", "revision_number"],
    )
    op.execute("""CREATE FUNCTION libris_reject_audit_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
        RAISE EXCEPTION 'Eventos de auditoria são imutáveis'; END; $$""")
    op.execute("""CREATE TRIGGER immutable_semantic_audit
        BEFORE UPDATE OR DELETE ON experimental_semantic_audit_events
        FOR EACH ROW EXECUTE FUNCTION libris_reject_audit_mutation()""")
    op.execute("""CREATE TRIGGER immutable_semantic_audit_truncate
        BEFORE TRUNCATE ON experimental_semantic_audit_events
        FOR EACH STATEMENT EXECUTE FUNCTION libris_reject_audit_mutation()""")


def downgrade() -> None:
    # Drops ALL audit evidence and revision reasons. Never run on working/production data.
    op.drop_table("experimental_semantic_audit_events")
    op.execute("DROP FUNCTION libris_reject_audit_mutation()")
    op.drop_column("experimental_semantic_revisions", "reason")
