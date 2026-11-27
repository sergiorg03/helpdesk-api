import pytest

from fastapi import HTTPException

from app.models.enums import UserRole
from app.schemas import UserUpdate, UserRoleUpdate
from app.services.user import (
    update_user,
    update_user_role,
    get_user_history,
)

from tests.test_user_services import create_test_user


def test_user_history_records_username_change(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    update_user(
        db_session,
        customer.id,
        UserUpdate(username="new_customer"),
        admin,
    )

    history = get_user_history(db_session, customer.id, admin)

    assert len(history) == 1
    assert history[0].field_changed == "username"
    assert history[0].old_value == "customer"
    assert history[0].new_value == "new_customer"


def test_user_history_records_email_change(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    update_user(
        db_session,
        customer.id,
        UserUpdate(email="new@example.com"),
        admin,
    )

    history = get_user_history(db_session, customer.id, admin)

    assert len(history) == 1
    assert history[0].field_changed == "email"
    assert (
        history[0].old_value == customer.email
        or history[0].old_value == "customer@example.com"
    )
    assert history[0].new_value == "new@example.com"


def test_user_history_records_role_change(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    update_user_role(
        db_session,
        customer.id,
        UserRoleUpdate(role=UserRole.TECHNICIAN),
        admin,
    )

    history = get_user_history(db_session, customer.id, admin)

    assert len(history) == 1
    assert history[0].field_changed == "role"
    assert history[0].old_value == "CUSTOMER"
    assert history[0].new_value == "TECHNICIAN"


def test_user_history_records_active_status_change(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    update_user(
        db_session,
        customer.id,
        UserUpdate(is_active=False),
        admin,
    )

    history = get_user_history(db_session, customer.id, admin)

    assert len(history) == 1
    assert history[0].field_changed == "is_active"
    assert history[0].old_value == "True"
    assert history[0].new_value == "False"


def test_user_history_does_not_record_unchanged_values(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    update_user(
        db_session,
        customer.id,
        UserUpdate(username="customer"),
        admin,
    )

    history = get_user_history(db_session, customer.id, admin)

    assert history == []


def test_user_cannot_access_another_user_history(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_customer = create_test_user(db_session, "another", "CUSTOMER")

    with pytest.raises(HTTPException) as exc:
        get_user_history(db_session, another_customer.id, customer)

    assert exc.value.status_code == 403
