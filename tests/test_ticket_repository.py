from app.models import Ticket, User
from app.repositories import ticket as ticket_repository


def create_test_user(db_session):
    user = User(
        username="repository_user",
        email="repository@example.com",
        hashed_password="fake_hash",
        role="CUSTOMER",
    )

    db_session.add(user)
    db_session.flush()

    return user


def create_test_ticket(db_session, user, title="Test ticket"):
    ticket = Ticket(
        title=title,
        description="This is a test ticket description.",
        created_by_id=user.id,
    )

    return ticket_repository.create(db_session, ticket)


def test_create_ticket(db_session):
    user = create_test_user(db_session)

    ticket = create_test_ticket(db_session, user)

    assert ticket.id is not None
    assert ticket.title == "Test ticket"
    assert ticket.created_by_id == user.id


def test_get_ticket_by_id(db_session):
    user = create_test_user(db_session)
    ticket = create_test_ticket(db_session, user)

    result = ticket_repository.get_by_id(db_session, ticket.id)

    assert result is not None
    assert result.id == ticket.id


def test_get_nonexistent_ticket(db_session):
    from uuid import uuid4

    result = ticket_repository.get_by_id(db_session, uuid4())

    assert result is None


def test_get_all_tickets_with_pagination(db_session):
    user = create_test_user(db_session)

    create_test_ticket(db_session, user, "Ticket one")
    create_test_ticket(db_session, user, "Ticket two")
    create_test_ticket(db_session, user, "Ticket three")

    first_page = ticket_repository.get_all(
        db_session,
        skip=0,
        limit=2,
    )

    second_page = ticket_repository.get_all(
        db_session,
        skip=2,
        limit=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1


def test_update_ticket(db_session):
    user = create_test_user(db_session)
    ticket = create_test_ticket(db_session, user)

    updated_ticket = ticket_repository.update(
        db_session,
        ticket,
        {"title": "Updated ticket", "status": "IN_PROGRESS"},
    )

    assert updated_ticket.title == "Updated ticket"
    assert updated_ticket.status == "IN_PROGRESS"


def test_delete_ticket(db_session):
    user = create_test_user(db_session)
    ticket = create_test_ticket(db_session, user)

    ticket_repository.delete(db_session, ticket)

    result = ticket_repository.get_by_id(db_session, ticket.id)

    assert result is None
