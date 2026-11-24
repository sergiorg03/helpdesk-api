from uuid import UUID

from sqlalchemy.orm import Session

from app.models import TicketHistory, User
from app.services import ticket as ticket_service
from app.repositories import ticket_history as history_repository


def get_ticket_history(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> list[TicketHistory]:
    # Comprueba que el ticket existe y que el usuario puede acceder a él.
    ticket_service.get_ticket(db, ticket_id, current_user)

    return history_repository.get_by_ticket(db, ticket_id)
