import pytest
from fastapi import HTTPException

from app.core.security import verify_password

from app.models import User
from app.models.enums import UserRole

from app.schemas import UserUpdate, UserRoleUpdate, UserCreate

from app.services import user as user_service
from app.services.user import create_user

from app.repositories import user as user_repository


def create_test_user(db_session, username, role, is_active=True):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="fake_hash",
        role=role,
        is_active=is_active,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_admin_can_list_users(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    create_test_user(db_session, "customer", "CUSTOMER")

    users = user_service.get_users(db_session, admin)

    assert len(users) == 2


def test_customer_cannot_list_users(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    with pytest.raises(HTTPException) as exc:
        user_service.get_users(db_session, customer)

    assert exc.value.status_code == 403


def test_user_can_access_own_profile(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    result = user_service.get_user(db_session, customer.id, customer)

    assert result.id == customer.id


def test_customer_cannot_access_another_profile(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_user = create_test_user(db_session, "another", "CUSTOMER")

    with pytest.raises(HTTPException) as exc:
        user_service.get_user(db_session, another_user.id, customer)

    assert exc.value.status_code == 403


def test_admin_can_update_user(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    updated = user_service.update_user(
        db_session,
        customer.id,
        UserUpdate(username="new_customer"),
        admin,
    )

    assert updated.username == "new_customer"


def test_customer_can_update_own_profile(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    updated = user_service.update_user(
        db_session,
        customer.id,
        UserUpdate(username="new_customer"),
        customer,
    )

    assert updated.username == "new_customer"


def test_customer_cannot_deactivate_account(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    with pytest.raises(HTTPException) as exc:
        user_service.update_user(
            db_session,
            customer.id,
            UserUpdate(is_active=False),
            customer,
        )

    assert exc.value.status_code == 403


def test_admin_can_change_user_role(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    updated = user_service.update_user_role(
        db_session,
        customer.id,
        UserRoleUpdate(role=UserRole.TECHNICIAN),
        admin,
    )

    assert updated.role == UserRole.TECHNICIAN


def test_admin_can_promote_another_user_to_admin(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    updated = user_service.update_user_role(
        db_session,
        customer.id,
        UserRoleUpdate(role=UserRole.ADMIN),
        admin,
    )

    assert updated.role == UserRole.ADMIN


def test_admin_cannot_change_own_role(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")

    with pytest.raises(HTTPException) as exc:
        user_service.update_user_role(
            db_session,
            admin.id,
            UserRoleUpdate(role=UserRole.CUSTOMER),
            admin,
        )

    assert exc.value.status_code == 400


def test_admin_cannot_deactivate_own_account(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")

    with pytest.raises(HTTPException) as exc:
        user_service.update_user(
            db_session,
            admin.id,
            UserUpdate(is_active=False),
            admin,
        )

    assert exc.value.status_code == 400


def test_admin_can_deactivate_another_admin_when_multiple_exist(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    another_admin = create_test_user(db_session, "another_admin", "ADMIN")

    updated = user_service.update_user(
        db_session,
        another_admin.id,
        UserUpdate(is_active=False),
        admin,
    )

    assert updated.is_active is False
    assert user_repository.count_active_admins(db_session) == 1


def test_admin_can_demote_another_admin_when_multiple_exist(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    another_admin = create_test_user(db_session, "another_admin", "ADMIN")

    updated = user_service.update_user_role(
        db_session,
        another_admin.id,
        UserRoleUpdate(role=UserRole.TECHNICIAN),
        admin,
    )

    assert updated.role == UserRole.TECHNICIAN


def test_admin_can_create_customer(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")

    user_data = UserCreate(
        username="new_customer",
        email="new@example.com",
        password="SecurePassword123",
    )

    user = create_user(db_session, user_data, admin)

    assert user.username == "new_customer"
    assert user.email == "new@example.com"
    assert user.role == UserRole.CUSTOMER
    assert user.is_active is True
    assert user.hashed_password != "SecurePassword123"
    assert verify_password("SecurePassword123", user.hashed_password)


def test_admin_can_create_user_with_custom_role(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")

    user_data = UserCreate(
        username="new_technician",
        email="technician@example.com",
        password="SecurePassword123",
        role=UserRole.TECHNICIAN,
    )

    user = create_user(db_session, user_data, admin)

    assert user.role == UserRole.TECHNICIAN


def test_customer_cannot_create_users(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    user_data = UserCreate(
        username="new_user",
        email="new@example.com",
        password="SecurePassword123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(db_session, user_data, customer)

    assert exc.value.status_code == 403


def test_create_user_rejects_duplicate_username(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    create_test_user(db_session, "existing", "CUSTOMER")

    user_data = UserCreate(
        username="existing",
        email="different@example.com",
        password="SecurePassword123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(db_session, user_data, admin)

    assert exc.value.status_code == 409


def test_create_user_rejects_duplicate_email(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    create_test_user(db_session, "existing", "CUSTOMER")

    user_data = UserCreate(
        username="new_user",
        email="existing@example.com",
        password="SecurePassword123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(db_session, user_data, admin)

    assert exc.value.status_code == 409
