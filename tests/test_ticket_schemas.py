import pytest
from pydantic import ValidationError

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate


def test_ticket_create_default_priority():
    ticket = TicketCreate(
        title="Computer not working",
        description="The computer does not start correctly.",
    )

    assert ticket.priority == TicketPriority.MEDIUM


@pytest.mark.parametrize(
    "priority",
    [
        TicketPriority.LOW,
        TicketPriority.MEDIUM,
        TicketPriority.HIGH,
        TicketPriority.CRITICAL,
    ],
)
def test_ticket_create_valid_priorities(priority):
    ticket = TicketCreate(
        title="Computer not working",
        description="The computer does not start correctly.",
        priority=priority,
    )

    assert ticket.priority == priority


def test_ticket_create_invalid_priority():
    with pytest.raises(ValidationError):
        TicketCreate(
            title="Computer not working",
            description="The computer does not start correctly.",
            priority="URGENT",
        )


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.OPEN,
        TicketStatus.IN_PROGRESS,
        TicketStatus.PENDING,
        TicketStatus.CLOSED,
    ],
)
def test_ticket_update_valid_statuses(status):
    ticket = TicketUpdate(status=status)

    assert ticket.status == status


def test_ticket_update_invalid_status():
    with pytest.raises(ValidationError):
        TicketUpdate(status="FINISHED")


def test_ticket_update_invalid_priority():
    with pytest.raises(ValidationError):
        TicketUpdate(priority="EXTREME")
