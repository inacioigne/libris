from datetime import datetime

from sqlalchemy import ForeignKey, String

from core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
# from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import JSON, UUID

class CatalogingWorkspace(Base):
    __tablename__ = "cataloging_workspace"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="bibliographic",
    )

    data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime]

    updated_at: Mapped[datetime]

    published_at: Mapped[datetime | None]

    published_work_id: Mapped[uuid.UUID | None]