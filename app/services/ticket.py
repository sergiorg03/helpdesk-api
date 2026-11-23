from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Ticket, User
from app.models.enums import UserRole
from app.repositories import ticket as ticket_repository


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

    ticket_repository.update(db, ticket, update_data)
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
