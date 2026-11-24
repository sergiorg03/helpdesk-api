import pytest
from fastapi import HTTPException

from app.models import User
from app.models.enums import UserRole
from app.services import comment as comment_service
from app.services import ticket as ticket_service


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
    return ticket_service.create_ticket(
        db_session,
        {
            "title": "Test ticket",
            "description": "This is a test ticket description.",
        },
        user,
    )


def test_customer_can_create_comment(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    comment = comment_service.create_comment(
        db_session,
        ticket.id,
        "This is a test comment.",
        customer,
    )

    assert comment.content == "This is a test comment."
    assert comment.ticket_id == ticket.id
    assert comment.user_id == customer.id


def test_customer_can_get_ticket_comments(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    comment_service.create_comment(db_session, ticket.id, "First comment", customer)
    comment_service.create_comment(db_session, ticket.id, "Second comment", customer)

    comments = comment_service.get_comments(db_session, ticket.id, customer)

    assert len(comments) == 2
    assert comments[0].content == "First comment"
    assert comments[1].content == "Second comment"


def test_customer_cannot_access_comments_of_another_customer(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    other_customer = create_test_user(db_session, "other", UserRole.CUSTOMER)

    ticket = create_test_ticket(db_session, customer)

    with pytest.raises(HTTPException) as exc_info:
        comment_service.get_comments(db_session, ticket.id, other_customer)

    assert exc_info.value.status_code == 403


def test_author_can_delete_own_comment(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    ticket = create_test_ticket(db_session, customer)

    comment = comment_service.create_comment(
        db_session, ticket.id, "My comment", customer
    )

    comment_service.delete_comment(db_session, comment.id, customer)

    comments = comment_service.get_comments(db_session, ticket.id, customer)

    assert comments == []


def test_customer_cannot_delete_another_users_comment(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    other_customer = create_test_user(db_session, "other", UserRole.CUSTOMER)

    ticket = create_test_ticket(db_session, customer)
    comment = comment_service.create_comment(
        db_session, ticket.id, "My comment", customer
    )

    with pytest.raises(HTTPException) as exc_info:
        comment_service.delete_comment(db_session, comment.id, other_customer)

    assert exc_info.value.status_code == 403


def test_admin_can_delete_another_users_comment(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)
    admin = create_test_user(db_session, "admin", UserRole.ADMIN)

    ticket = create_test_ticket(db_session, customer)
    comment = comment_service.create_comment(
        db_session, ticket.id, "My comment", customer
    )

    comment_service.delete_comment(db_session, comment.id, admin)

    comments = comment_service.get_comments(db_session, ticket.id, customer)

    assert comments == []


def test_delete_nonexistent_comment_returns_404(db_session):
    customer = create_test_user(db_session, "customer", UserRole.CUSTOMER)

    from uuid import uuid4

    with pytest.raises(HTTPException) as exc_info:
        comment_service.delete_comment(db_session, uuid4(), customer)

    assert exc_info.value.status_code == 404
