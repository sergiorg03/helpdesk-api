from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.comment import Comment
    from app.models.ticket_history import TicketHistory


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="created_by",
        foreign_keys="Ticket.created_by_id",
    )

    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="assigned_to",
        foreign_keys="Ticket.assigned_to_id",
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="user",
    )

    ticket_history: Mapped[list["TicketHistory"]] = relationship(
        back_populates="changed_by",
    )
