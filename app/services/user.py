from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, UserHistory
from app.models.enums import UserRole
from app.repositories import (
    user as user_repository,
    user_history as user_history_repository,
)
from app.schemas import UserUpdate, UserRoleUpdate, UserCreate

from app.core.security import hash_password


def get_users(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users",
        )

    return user_repository.get_all(db, skip, limit)


def get_user(
    db: Session,
    user_id: UUID,
    current_user: User,
) -> User:
    user = user_repository.get_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if current_user.role != UserRole.ADMIN and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this user",
        )

    return user


def update_user(
    db: Session,
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User,
) -> User:
    user = get_user(db, user_id, current_user)

    if (
        "is_active" in user_data.model_fields_set
        and user.role == UserRole.ADMIN
        and user.is_active
        and user_data.is_active is False
    ):
        user_repository.lock_admin_changes(db)
        user_repository.refresh_user(db, user)

    update_data = user_data.model_dump(exclude_unset=True)

    if "is_active" in update_data:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can change account status",
            )

        if user.id == current_user.id and update_data["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account",
            )

        if (
            user.role == UserRole.ADMIN
            and user.is_active
            and update_data["is_active"] is False
            and user_repository.count_active_admins(db) <= 1
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active administrator",
            )

    if "username" in update_data:
        existing_user = user_repository.get_by_username(
            db,
            update_data["username"],
        )

        if existing_user is not None and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

    if "email" in update_data:
        existing_user = user_repository.get_by_email(
            db,
            update_data["email"],
        )

        if existing_user is not None and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    _record_user_changes(
        db,
        user,
        current_user,
        update_data,
    )
    user_repository.update(db, user, update_data)
    db.commit()
    db.refresh(user)

    return user


def update_user_role(
    db: Session,
    user_id: UUID,
    role_data: UserRoleUpdate,
    current_user: User,
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can change user roles",
        )

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot change their own role",
        )

    user = user_repository.get_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if (
        user.role == UserRole.ADMIN
        and user.is_active
        and role_data.role != UserRole.ADMIN
    ):
        user_repository.lock_admin_changes(db)
        user_repository.refresh_user(db, user)

    if (
        user.role == UserRole.ADMIN
        and user.is_active
        and role_data.role != UserRole.ADMIN
        and user_repository.count_active_admins(db) <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the role of the last active administrator",
        )

    _record_user_changes(
        db,
        user,
        current_user,
        {"role": role_data.role},
    )

    user.role = role_data.role
    db.commit()
    db.refresh(user)

    return user


def _record_user_changes(
    db: Session,
    user: User,
    current_user: User,
    changes: dict,
) -> None:
    for field, new_value in changes.items():
        old_value = getattr(user, field)

        if old_value == new_value:
            continue

        history_entry = UserHistory(
            user_id=user.id,
            changed_by_id=current_user.id,
            field_changed=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value),
        )

        user_history_repository.create(db, history_entry)


def get_user_history(
    db: Session,
    user_id: UUID,
    current_user: User,
) -> list[UserHistory]:
    # Reutiliza las comprobaciones de existencia y permisos.
    get_user(db, user_id, current_user)

    return user_history_repository.get_by_user(db, user_id)


def create_user(
    db: Session,
    user_data: UserCreate,
    current_user: User,
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if user_repository.get_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    if user_repository.get_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )

    user_repository.create(db, new_user)

    db.commit()
    db.refresh(new_user)

    return new_user
