"""Optional authenticated actor; preserve historical and technical provenance."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_revision_actor"
down_revision: str | None = "0001_semantic"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "experimental_semantic_revisions", sa.Column("actor_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("experimental_semantic_revisions", "actor_id")
