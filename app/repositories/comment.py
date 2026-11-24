from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Comment


def get_by_id(db: Session, comment_id: UUID) -> Comment | None:
    return db.get(Comment, comment_id)


def get_by_ticket(
    db: Session,
    ticket_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Comment]:
    statement = (
        select(Comment)
        .where(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def create(db: Session, comment: Comment) -> Comment:
    db.add(comment)
    db.flush()
    db.refresh(comment)
    return comment


def delete(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.flush()
