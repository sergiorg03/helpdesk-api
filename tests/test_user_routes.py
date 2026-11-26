import pytest

from app.models import User
from app.core.security import create_access_token


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


def get_auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_users(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    create_test_user(db_session, "customer", "CUSTOMER")
    create_test_user(db_session, "technician", "TECHNICIAN")

    response = client.get(
        "/users/",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["username"] in {
        "admin",
        "customer",
        "technician",
    }


def test_customer_cannot_list_users(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.get(
        "/users/",
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 403


def test_user_can_access_own_profile(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.get(
        f"/users/{customer.id}",
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)
    assert response.json()["username"] == "customer"
    assert response.json()["role"] == "CUSTOMER"


def test_customer_cannot_access_another_profile(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_customer = create_test_user(db_session, "another_customer", "CUSTOMER")

    response = client.get(
        f"/users/{another_customer.id}",
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 403


def test_admin_can_access_another_user_profile(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.get(
        f"/users/{customer.id}",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["username"] == "customer"
    assert response.json()["role"] == "CUSTOMER"


def test_admin_can_update_user(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}",
        json={
            "username": "updated_customer",
            "email": "updated@example.com",
        },
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["username"] == "updated_customer"
    assert response.json()["email"] == "updated@example.com"


def test_customer_can_update_own_profile(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}",
        json={"username": "new_customer"},
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 200
    assert response.json()["username"] == "new_customer"


def test_customer_cannot_deactivate_own_account(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}",
        json={"is_active": False},
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 403


def test_admin_can_change_user_role(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}/role",
        json={"role": "TECHNICIAN"},
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "TECHNICIAN"


def test_customer_cannot_change_user_role(client, db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_customer = create_test_user(db_session, "another_customer", "CUSTOMER")

    response = client.patch(
        f"/users/{another_customer.id}/role",
        json={"role": "ADMIN"},
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 403


def test_admin_cannot_change_own_role(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")

    response = client.patch(
        f"/users/{admin.id}/role",
        json={"role": "CUSTOMER"},
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 400


def test_admin_can_promote_customer_to_admin(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}/role",
        json={"role": "ADMIN"},
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


def test_admin_can_deactivate_another_user(client, db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.patch(
        f"/users/{customer.id}",
        json={"is_active": False},
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_user_cannot_access_nonexistent_profile(client, db_session):
    from uuid import uuid4

    customer = create_test_user(db_session, "customer", "CUSTOMER")

    response = client.get(
        f"/users/{uuid4()}",
        headers=get_auth_headers(customer),
    )

    assert response.status_code == 404


def test_unauthenticated_user_cannot_list_users(client):
    response = client.get("/users/")

    assert response.status_code == 401
