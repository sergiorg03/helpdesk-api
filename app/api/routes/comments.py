from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services import comment as comment_service

router = APIRouter(tags=["Comments"])


@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    ticket_id: UUID,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return comment_service.create_comment(
        db=db,
        ticket_id=ticket_id,
        content=comment_data.content,
        current_user=current_user,
    )


@router.get(
    "/tickets/{ticket_id}/comments",
    response_model=list[CommentResponse],
)
def get_comments(
    ticket_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return comment_service.get_comments(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment_service.delete_comment(
        db=db,
        comment_id=comment_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
