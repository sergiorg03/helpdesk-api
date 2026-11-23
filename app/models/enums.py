from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    TECHNICIAN = "TECHNICIAN"
    CUSTOMER = "CUSTOMER"

class TicketStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    CLOSED = "CLOSED"


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"