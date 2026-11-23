from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ticket


def get_by_id(db: Session, ticket_id: UUID) -> Ticket | None:
    return db.get(Ticket, ticket_id)


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Ticket]:
    statement = (
        select(Ticket).order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    )

    return list(db.scalars(statement).all())


def create(db: Session, ticket: Ticket) -> Ticket:
    db.add(ticket)
    db.flush()
    db.refresh(ticket)
    return ticket


def update(
    db: Session,
    ticket: Ticket,
    update_data: dict,
) -> Ticket:
    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.flush()
    db.refresh(ticket)
    return ticket


def delete(db: Session, ticket: Ticket) -> None:
    db.delete(ticket)
    db.flush()
