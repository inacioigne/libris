"""Create or adopt the isolated BFF schema without rewriting existing sessions."""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_web_auth"
down_revision: str | None = "0004_semantic_editorial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen definitions: independent of frontend files, ORM models and later releases.
TABLES = {
    "auth_transactions": """
        state_hash text PRIMARY KEY CHECK (length(state_hash) = 64),
        browser_hash text NOT NULL CHECK (length(browser_hash) = 64),
        payload text NOT NULL,
        expires_at bigint NOT NULL
    """,
    "sessions": """
        id_hash text PRIMARY KEY CHECK (length(id_hash) = 64),
        payload text NOT NULL,
        expires_at bigint NOT NULL
    """,
    "auth_quotas": """
        route text PRIMARY KEY CHECK (route IN ('login', 'callback', 'logout')),
        window_started timestamptz NOT NULL,
        attempts integer NOT NULL CHECK (attempts > 0)
    """,
}


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS libris_web")
    for table, columns in TABLES.items():
        reference = f"libris_expected_{table}"
        # PostgreSQL canonicalizes the expected definitions itself. Temporary tables
        # allow identical validation online and in offline-generated SQL scripts.
        op.execute(f"CREATE TEMP TABLE {reference} ({columns}) ON COMMIT DROP")
        op.execute(f"CREATE TABLE IF NOT EXISTS libris_web.{table} ({columns})")
        if table != "auth_quotas":
            op.execute(f"CREATE INDEX {reference}_expiry ON {reference} (expires_at)")
            op.execute(
                f"CREATE INDEX IF NOT EXISTS {table}_expiry "
                f"ON libris_web.{table} (expires_at)"
            )
        # Refuse drift rather than silently adopting an incompatible legacy object.
        # Compare both directions, including extra columns/constraints/indexes.
        queries = [
            "SELECT attname, format_type(atttypid, atttypmod), attnotnull, "
            "attidentity, attgenerated, attcollation, pg_get_expr(d.adbin, d.adrelid) "
            "FROM pg_attribute a LEFT JOIN pg_attrdef d "
            "ON d.adrelid = a.attrelid AND d.adnum = a.attnum "
            "WHERE a.attrelid = {relation}::regclass AND a.attnum > 0 AND NOT a.attisdropped",
            "SELECT contype, pg_get_constraintdef(oid), convalidated, condeferrable, condeferred "
            "FROM pg_constraint WHERE conrelid = {relation}::regclass",
            "SELECT substring(pg_get_indexdef(indexrelid) from ' USING .*'), "
            "indisunique, indisvalid, indisready "
            "FROM pg_index WHERE indrelid = {relation}::regclass",
        ]
        for query in queries:
            actual = query.format(relation=f"'libris_web.{table}'")
            expected = query.format(relation=f"'pg_temp.{reference}'")
            op.execute(f"""DO $$ BEGIN
                IF EXISTS (({actual}) EXCEPT ({expected}))
                    OR EXISTS (({expected}) EXCEPT ({actual})) THEN
                    RAISE EXCEPTION 'Incompatible libris_web.{table}; migration aborted';
                END IF;
                END $$""")
        op.execute(f"""DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class
                WHERE oid = 'libris_web.{table}'::regclass AND relkind = 'r'
                AND relpersistence = 'p'
                AND NOT relrowsecurity AND NOT relforcerowsecurity AND NOT relispartition)
                OR EXISTS (SELECT 1 FROM pg_trigger
                    WHERE tgrelid = 'libris_web.{table}'::regclass AND NOT tgisinternal) THEN
                RAISE EXCEPTION 'Incompatible libris_web.{table}; migration aborted';
            END IF;
            END $$""")


def downgrade() -> None:
    # Adoption cannot tell which live rows predate Alembic. Retain the schema and
    # its data on rollback; re-upgrade validates/adopts it again (ADR 0034).
    pass
