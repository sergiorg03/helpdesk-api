from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Comment, User
from app.models.enums import UserRole
from app.repositories import comment as comment_repository
from app.services import ticket as ticket_service


def create_comment(
    db: Session,
    ticket_id: UUID,
    content: str,
    current_user: User,
) -> Comment:
    ticket = ticket_service.get_ticket(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
    )

    comment = Comment(
        content=content,
        ticket_id=ticket.id,
        user_id=current_user.id,
    )

    comment_repository.create(db, comment)
    db.commit()
    db.refresh(comment)

    return comment


def get_comments(
    db: Session,
    ticket_id: UUID,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[Comment]:
    # Comprueba que el ticket existe y que el usuario puede acceder.
    ticket_service.get_ticket(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
    )

    return comment_repository.get_by_ticket(
        db=db,
        ticket_id=ticket_id,
        skip=skip,
        limit=limit,
    )


def delete_comment(
    db: Session,
    comment_id: UUID,
    current_user: User,
) -> None:
    comment = comment_repository.get_by_id(db, comment_id)

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if current_user.role != UserRole.ADMIN and comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this comment",
        )

    comment_repository.delete(db, comment)
    db.commit()
