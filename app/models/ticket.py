import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.comment import Comment
    from app.models.ticket_history import TicketHistory


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_by: Mapped["User"] = relationship(
        back_populates="created_tickets",
        foreign_keys=[created_by_id],
    )

    assigned_to: Mapped["User | None"] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[assigned_to_id],
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    history: Mapped[list["TicketHistory"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
