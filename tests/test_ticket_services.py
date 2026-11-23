import pytest

from fastapi import HTTPException

from app.models import User
from app.services import ticket as ticket_service
from app.repositories import ticket as ticket_repository


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


def create_test_ticket(db_session, user, title="Test ticket"):
    return ticket_service.create_ticket(
        db_session,
        {
            "title": title,
            "description": "This is a test ticket description.",
        },
        user,
    )


def test_customer_can_create_ticket(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    ticket = create_test_ticket(db_session, customer)

    assert ticket.id is not None
    assert ticket.created_by_id == customer.id
    assert ticket.status == "OPEN"


def test_customer_can_access_own_ticket(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, customer)

    result = ticket_service.get_ticket(db_session, ticket.id, customer)

    assert result.id == ticket.id


def test_customer_cannot_access_another_customer_ticket(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_customer = create_test_user(db_session, "another_customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, another_customer)

    with pytest.raises(HTTPException) as exc:
        ticket_service.get_ticket(db_session, ticket.id, customer)

    assert exc.value.status_code == 403


def test_customer_only_sees_own_tickets(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    another_customer = create_test_user(db_session, "another_customer", "CUSTOMER")

    own_ticket = create_test_ticket(db_session, customer, "My ticket")
    create_test_ticket(db_session, another_customer, "Other ticket")

    tickets = ticket_service.get_tickets(db_session, customer)

    assert len(tickets) == 1
    assert tickets[0].id == own_ticket.id


@pytest.mark.parametrize("role", ["TECHNICIAN", "ADMIN"])
def test_staff_can_see_all_tickets(db_session, role):
    staff = create_test_user(db_session, f"staff_{role.lower()}", role)
    customer = create_test_user(db_session, "customer", "CUSTOMER")

    create_test_ticket(db_session, customer, "Ticket one")
    create_test_ticket(db_session, customer, "Ticket two")

    tickets = ticket_service.get_tickets(db_session, staff)

    assert len(tickets) == 2


def test_customer_cannot_update_ticket(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, customer)

    with pytest.raises(HTTPException) as exc:
        ticket_service.update_ticket(
            db_session,
            ticket.id,
            {"title": "Updated title"},
            customer,
        )

    assert exc.value.status_code == 403


def test_technician_can_update_ticket(db_session):
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, customer)

    updated = ticket_service.update_ticket(
        db_session,
        ticket.id,
        {"title": "Updated by technician"},
        technician,
    )

    assert updated.title == "Updated by technician"


def test_technician_cannot_delete_ticket(db_session):
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, customer)

    with pytest.raises(HTTPException) as exc:
        ticket_service.delete_ticket(db_session, ticket.id, technician)

    assert exc.value.status_code == 403


def test_admin_can_delete_ticket(db_session):
    admin = create_test_user(db_session, "admin", "ADMIN")
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.delete_ticket(db_session, ticket.id, admin)

    assert ticket_repository.get_by_id(db_session, ticket.id) is None
