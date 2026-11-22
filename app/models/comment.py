from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ticket: Mapped["Ticket"] = relationship(
        back_populates="comments",
    )

    user: Mapped["User"] = relationship(
        back_populates="comments",
    )
