from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models import User


def get_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def get_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    statement = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)

    return list(db.scalars(statement).all())


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def update(db: Session, user: User, update_data: dict) -> User:
    for field, value in update_data.items():
        setattr(user, field, value)

    db.flush()
    db.refresh(user)

    return user


def count_active_admins(db: Session) -> int:
    statement = select(func.count(User.id)).where(
        User.role == "ADMIN",
        User.is_active.is_(True),
    )

    return db.scalar(statement) or 0


def lock_admin_changes(db: Session) -> None:
    """
    Serialize operations that can change active administrator membership.
    PostgreSQL only; SQLite tests do not require this lock.
    """
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(74201931)"))


def refresh_user(db: Session, user: User) -> User:
    db.refresh(user)
    return user
