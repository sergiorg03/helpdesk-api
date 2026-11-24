from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models import User
from app.schemas import TicketHistoryResponse
from app.services import ticket_history as history_service

router = APIRouter(tags=["Ticket History"])


@router.get(
    "/tickets/{ticket_id}/history",
    response_model=list[TicketHistoryResponse],
)
def get_ticket_history(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return history_service.get_ticket_history(
        db,
        ticket_id,
        current_user,
    )
