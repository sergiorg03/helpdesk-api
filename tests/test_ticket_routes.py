from uuid import uuid4

from app.core.security import create_access_token
from app.models import Ticket, User
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


def test_customer_can_create_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)

    response = client.post(
        "/tickets/",
        json={
            "title": "Internet connection problem",
            "description": "The computer loses its internet connection.",
            "priority": "HIGH",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 201
    assert response.json()["created_by_id"] == str(customer.id)
    assert response.json()["status"] == "OPEN"
    assert response.json()["priority"] == "HIGH"


def test_customer_can_list_own_tickets(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    other_customer = create_test_user(db_session, "other", UserRole.CUSTOMER)

    create_test_ticket(db_session, customer)
    create_test_ticket(db_session, other_customer)

    response = client.get("/tickets/", headers=auth_headers(customer))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_customer_can_get_own_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(customer),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(ticket.id)


def test_get_nonexistent_ticket_returns_404(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)

    response = client.get(
        f"/tickets/{uuid4()}",
        headers=auth_headers(customer),
    )

    assert response.status_code == 404


def test_invalid_ticket_uuid_returns_422(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)

    response = client.get(
        "/tickets/not-a-valid-uuid",
        headers=auth_headers(customer),
    )

    assert response.status_code == 422


def test_customer_cannot_update_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    response = client.patch(
        f"/tickets/{ticket.id}",
        json={"status": "CLOSED"},
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


def test_technician_can_update_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    technician = create_test_user(db_session, "technician", UserRole.TECHNICIAN)
    ticket = create_test_ticket(db_session, customer)

    response = client.patch(
        f"/tickets/{ticket.id}",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers(technician),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_technician_cannot_delete_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    technician = create_test_user(db_session, "technician", UserRole.TECHNICIAN)
    ticket = create_test_ticket(db_session, customer)

    response = client.delete(
        f"/tickets/{ticket.id}",
        headers=auth_headers(technician),
    )

    assert response.status_code == 403


def test_admin_can_delete_ticket(client, db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    admin = create_test_user(db_session, "admin", UserRole.ADMIN)
    ticket = create_test_ticket(db_session, customer)

    response = client.delete(
        f"/tickets/{ticket.id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(admin),
    )

    assert get_response.status_code == 404
