"""
User schemas.
"""

from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """
    Base user schema.

    Attributes:
        username: Username
        email: Email address
    """

    username: str = Field(description="Username")
    email: str = Field(description="Email address")


class UserCreate(UserBase):
    """
    User creation schema.

    Attributes:
        password: Password
    """

    password: str = Field(description="Password")


class UserUpdate(BaseModel):
    """
    User update schema.

    Attributes:
        email: Email address
        password: Password
    """

    email: Optional[str] = Field(default=None, description="Email address")
    password: Optional[str] = Field(default=None, description="Password")


class UserResponse(UserBase):
    """
    User response schema.

    Attributes:
        id: User ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
    """

    id: int = Field(description="User ID")
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Login request schema.

    Attributes:
        username: Username
        password: Password
    """

    username: str = Field(description="Username")
    password: str = Field(description="Password")


class TokenResponse(BaseModel):
    """
    Token response schema.

    Attributes:
        token: JWT token
    """

    token: str = Field(description="JWT token")
