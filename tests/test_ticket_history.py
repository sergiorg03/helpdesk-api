from app.models import User
from app.services import ticket as ticket_service
from app.services import ticket_history as history_service


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


def create_test_ticket(db_session, customer):
    return ticket_service.create_ticket(
        db_session,
        {
            "title": "Test ticket",
            "description": "This is a test ticket description.",
        },
        customer,
    )


def test_status_change_is_recorded(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.update_ticket(
        db_session,
        ticket.id,
        {"status": "IN_PROGRESS"},
        technician,
    )

    history = history_service.get_ticket_history(
        db_session,
        ticket.id,
        technician,
    )

    assert len(history) == 1
    assert history[0].field_changed == "status"
    assert history[0].old_value == "OPEN"
    assert history[0].new_value == "IN_PROGRESS"
    assert history[0].changed_by_id == technician.id


def test_priority_change_is_recorded(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.update_ticket(
        db_session,
        ticket.id,
        {"priority": "HIGH"},
        technician,
    )

    history = history_service.get_ticket_history(
        db_session,
        ticket.id,
        technician,
    )

    assert len(history) == 1
    assert history[0].field_changed == "priority"
    assert history[0].old_value == "MEDIUM"
    assert history[0].new_value == "HIGH"


def test_assigned_technician_change_is_recorded(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.update_ticket(
        db_session,
        ticket.id,
        {"assigned_to_id": technician.id},
        technician,
    )

    history = history_service.get_ticket_history(
        db_session,
        ticket.id,
        technician,
    )

    assert len(history) == 1
    assert history[0].field_changed == "assigned_to_id"
    assert history[0].old_value is None
    assert history[0].new_value == str(technician.id)


def test_unchanged_values_do_not_create_history(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.update_ticket(
        db_session,
        ticket.id,
        {"status": "OPEN"},
        technician,
    )

    history = history_service.get_ticket_history(
        db_session,
        ticket.id,
        technician,
    )

    assert history == []


def test_multiple_changes_create_separate_history_entries(db_session):
    customer = create_test_user(db_session, "customer", "CUSTOMER")
    technician = create_test_user(db_session, "technician", "TECHNICIAN")
    ticket = create_test_ticket(db_session, customer)

    ticket_service.update_ticket(
        db_session,
        ticket.id,
        {
            "status": "IN_PROGRESS",
            "priority": "HIGH",
            "assigned_to_id": technician.id,
        },
        technician,
    )

    history = history_service.get_ticket_history(
        db_session,
        ticket.id,
        technician,
    )

    assert len(history) == 3
    assert {entry.field_changed for entry in history} == {
        "status",
        "priority",
        "assigned_to_id",
    }
