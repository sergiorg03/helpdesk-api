from uuid import UUID
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models.enums import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    email: EmailStr | None = None
    is_active: bool | None = None

    @field_validator("username", "email", "is_active", mode="before")
    @classmethod
    def reject_null_values(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    changed_by_id: UUID
    field_changed: str
    old_value: str | None
    new_value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
