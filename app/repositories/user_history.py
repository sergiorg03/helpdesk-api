from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserHistory


def get_by_user(db: Session, user_id: UUID) -> list[UserHistory]:
    statement = (
        select(UserHistory)
        .where(UserHistory.user_id == user_id)
        .order_by(UserHistory.created_at.asc())
    )
    return list(db.scalars(statement).all())


def create(db: Session, history_entry: UserHistory) -> UserHistory:
    db.add(history_entry)
    db.flush()
    db.refresh(history_entry)
    return history_entry
