from uuid import uuid4

from app.core.security import create_access_token
from app.models import User, Ticket
from app.models.enums import UserRole


def create_test_user(db_session, username, role):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="fake_hash",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_ticket(db_session, user):
    ticket = Ticket(
        title="Test ticket",
        description="This is a test ticket description.",
        created_by_id=user.id,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_customer_can_create_comment(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    response = client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "This is a test comment."},
        headers=auth_headers(customer),
    )

    assert response.status_code == 201
    assert response.json()["content"] == "This is a test comment."
    assert response.json()["user_id"] == str(customer.id)
    assert response.json()["ticket_id"] == str(ticket.id)


def test_customer_can_list_comments(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "First comment"},
        headers=auth_headers(customer),
    )
    client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "Second comment"},
        headers=auth_headers(customer),
    )

    response = client.get(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(customer),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_customer_cannot_access_another_customers_comments(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    other_customer = create_test_user(db_session, "other", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    response = client.get(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(other_customer),
    )

    assert response.status_code == 403


def test_customer_can_delete_own_comment(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    create_response = client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "My comment"},
        headers=auth_headers(customer),
    )
    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/comments/{comment_id}",
        headers=auth_headers(customer),
    )

    assert response.status_code == 204


def test_customer_cannot_delete_another_users_comment(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    other_customer = create_test_user(db_session, "other", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    create_response = client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "My comment"},
        headers=auth_headers(customer),
    )
    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/comments/{comment_id}",
        headers=auth_headers(other_customer),
    )

    assert response.status_code == 403


def test_admin_can_delete_another_users_comment(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    admin = create_test_user(db_session, "admin", UserRole.ADMIN)
    ticket = create_test_ticket(db_session, customer)

    create_response = client.post(
        f"/tickets/{ticket.id}/comments",
        json={"content": "My comment"},
        headers=auth_headers(customer),
    )
    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/comments/{comment_id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 204


def test_delete_nonexistent_comment_returns_404(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)

    response = client.delete(
        f"/comments/{uuid4()}",
        headers=auth_headers(customer),
    )

    assert response.status_code == 404
