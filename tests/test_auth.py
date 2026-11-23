from sqlalchemy import select

from app.core.security import decode_access_token, hash_password
from app.models import User

from datetime import timedelta
from app.core.security import create_access_token


def test_login_success(client, db_session):
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=hash_password("TestPassword123!"),
        role="ADMIN",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/auth/login",
        data={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert "access_token" in data

    payload = decode_access_token(data["access_token"])

    assert payload["sub"] == str(user.id)


def test_login_invalid_password(client, db_session):
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("CorrectPassword123!"),
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_get_current_user(client, db_session):
    user = User(
        username="currentuser",
        email="currentuser@example.com",
        hashed_password=hash_password("TestPassword123!"),
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "currentuser",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["username"] == "currentuser"
    assert response.json()["role"] == "CUSTOMER"
    assert "hashed_password" not in response.json()


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_admin_access(client, db_session):
    user = User(
        username="admin_test",
        email="admin_test@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        role="ADMIN",
    )

    db_session.add(user)
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "admin_test",
            "password": "AdminPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/admin-check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "You have administrator permissions"


def test_technician_cannot_access_admin_route(client, db_session):
    user = User(
        username="technician_test",
        email="technician_test@example.com",
        hashed_password=hash_password("TechnicianPassword123!"),
        role="TECHNICIAN",
    )

    db_session.add(user)
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "technician_test",
            "password": "TechnicianPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/admin-check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action"
    )


def test_inactive_user_cannot_login(client, db_session):
    user = User(
        username="inactive_user",
        email="inactive@example.com",
        hashed_password=hash_password("InactivePassword123!"),
        role="CUSTOMER",
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "inactive_user",
            "password": "InactivePassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user"


def test_login_unknown_user(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent",
            "password": "SomePassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_with_expired_token(client):
    token = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_use_existing_token(client, db_session):
    user = User(
        username="deactivated_user",
        email="deactivated@example.com",
        hashed_password=hash_password("TestPassword123!"),
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "deactivated_user",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    user.is_active = False
    db_session.commit()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user"
