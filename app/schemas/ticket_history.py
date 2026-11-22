from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketHistoryResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    changed_by_id: UUID
    field_changed: str
    old_value: str | None
    new_value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
