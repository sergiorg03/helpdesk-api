import pytest
from pydantic import ValidationError

from app.schemas import UserUpdate


@pytest.mark.parametrize(
    "field",
    ["username", "email", "is_active"],
)
def test_user_update_rejects_null_values(field):
    with pytest.raises(ValidationError):
        UserUpdate(**{field: None})


def test_user_update_accepts_empty_payload():
    user_data = UserUpdate()

    assert user_data.model_dump(exclude_unset=True) == {}


def test_user_update_accepts_valid_values():
    user_data = UserUpdate(
        username="new_username",
        email="new@example.com",
        is_active=False,
    )

    assert user_data.username == "new_username"
    assert user_data.email == "new@example.com"
    assert user_data.is_active is False
