from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["operator", "engineer", "admin"] = "operator"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john.doe",
                "email": "john.doe@plant.com",
                "password": "s3cur3P@ss!",
                "role": "operator",
            }
        }
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "username": "john.doe",
                "email": "john.doe@plant.com",
                "role": "operator",
                "is_active": True,
            }
        },
    )

    id: int
    username: str
    email: str
    role: str
    is_active: bool


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"username": "admin", "password": "password"}
        }
    )


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class UserUpdateRequest(BaseModel):
    role: Literal["operator", "engineer", "admin"] | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "engineer", "is_active": True}}
    )


class ChangePasswordRequest(BaseModel):
    """Used by any authenticated user to change their own password."""

    current_password: str
    new_password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "old_password",
                "new_password": "new_s3cur3P@ss!",
            }
        }
    )


class AdminChangePasswordRequest(BaseModel):
    """Used by admin to set any user's password without requiring the current password."""

    new_password: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"new_password": "new_s3cur3P@ss!"}}
    )
