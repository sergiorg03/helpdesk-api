from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Ticket, User, TicketHistory
from app.models.enums import UserRole

from app.repositories import (
    ticket as ticket_repository,
    ticket_history as history_repository,
)

from app.schemas import TicketUpdate


def create_ticket(
    db: Session,
    ticket_data: dict,
    current_user: User,
) -> Ticket:
    ticket = Ticket(
        **ticket_data,
        created_by_id=current_user.id,
    )

    ticket_repository.create(db, ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def get_ticket(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> Ticket:
    ticket = ticket_repository.get_by_id(db, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    if (
        current_user.role == UserRole.CUSTOMER
        and ticket.created_by_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this ticket",
        )

    return ticket


def get_tickets(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[Ticket]:
    if current_user.role == UserRole.CUSTOMER:
        from sqlalchemy import select

        statement = (
            select(Ticket)
            .where(Ticket.created_by_id == current_user.id)
            .order_by(Ticket.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(statement).all())

    return ticket_repository.get_all(db, skip, limit)


def update_ticket(
    db: Session,
    ticket_id: UUID,
    update_data: dict,
    current_user: User,
) -> Ticket:
    ticket = get_ticket(db, ticket_id, current_user)

    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot update tickets",
        )

    tracked_fields = {"status", "priority", "assigned_to_id"}

    for field, new_value in update_data.items():
        old_value = getattr(ticket, field)

        if field in tracked_fields and old_value != new_value:
            history_entry = TicketHistory(
                ticket_id=ticket.id,
                changed_by_id=current_user.id,
                field_changed=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else "UNASSIGNED",
            )

            history_repository.create(db, history_entry)

        setattr(ticket, field, new_value)

    db.commit()
    db.refresh(ticket)

    return ticket


def delete_ticket(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tickets",
        )

    ticket = ticket_repository.get_by_id(db, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    ticket_repository.delete(db, ticket)
    db.commit()
