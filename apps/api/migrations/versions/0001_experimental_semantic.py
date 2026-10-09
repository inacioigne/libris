"""Experimental resources and immutable RDF revisions; no administrative inventory."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_semantic"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experimental_semantic_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("uri", sa.String(), nullable=False, unique=True),
        sa.Column("current_revision", sa.Integer(), nullable=False),
        sa.CheckConstraint("current_revision > 0", name="ck_semantic_current_positive"),
    )
    op.create_table(
        "experimental_semantic_revisions",
        sa.Column("resource_id", sa.Uuid(), primary_key=True),
        sa.Column("number", sa.Integer(), primary_key=True),
        sa.Column("document", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("process", sa.String(), nullable=False),
        sa.Column("profile", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["experimental_semantic_resources.id"]),
        sa.CheckConstraint("number > 0", name="ck_semantic_revision_positive"),
        sa.CheckConstraint("jsonb_typeof(document) = 'array'", name="ck_semantic_document_array"),
        sa.CheckConstraint("length(trim(source)) > 0", name="ck_semantic_source"),
        sa.CheckConstraint("length(trim(process)) > 0", name="ck_semantic_process"),
    )
    op.create_foreign_key(
        "fk_semantic_current",
        "experimental_semantic_resources",
        "experimental_semantic_revisions",
        ["id", "current_revision"],
        ["resource_id", "number"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.execute("""CREATE FUNCTION libris_reject_revision_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
        RAISE EXCEPTION 'Revisões semânticas são imutáveis'; END; $$""")
    op.execute("""CREATE TRIGGER immutable_semantic_revision
        BEFORE UPDATE OR DELETE ON experimental_semantic_revisions
        FOR EACH ROW EXECUTE FUNCTION libris_reject_revision_mutation()""")


def downgrade() -> None:
    op.drop_constraint("fk_semantic_current", "experimental_semantic_resources", type_="foreignkey")
    op.drop_table("experimental_semantic_revisions")
    op.drop_table("experimental_semantic_resources")
    op.execute("DROP FUNCTION libris_reject_revision_mutation()")
