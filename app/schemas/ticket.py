from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=150)
    description: str | None = Field(default=None, min_length=10)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to_id: UUID | None = None


class TicketResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: str
    priority: str
    created_by_id: UUID
    assigned_to_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
