from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TicketHistory


def get_by_ticket(
    db: Session,
    ticket_id: UUID,
) -> list[TicketHistory]:
    statement = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
    )

    return list(db.scalars(statement).all())


def create(
    db: Session,
    history_entry: TicketHistory,
) -> TicketHistory:
    db.add(history_entry)
    db.flush()
    db.refresh(history_entry)

    return history_entry
