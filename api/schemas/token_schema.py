"""
Token schemas.
"""

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class TokenBase(BaseModel):
    """
    Base token schema.

    Attributes:
        name: Token name
        description: Token description
    """

    name: str = Field(description="Token name", min_length=1, max_length=50)
    description: Optional[str] = Field(
        default=None, description="Token description", max_length=500
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate token name is not blank."""
        if not v or not v.strip():
            raise ValueError("Token name cannot be empty")
        return v.strip()


class TokenCreate(TokenBase):
    """
    Token creation schema.

    Attributes:
        tool_ids: Tool IDs this token is allowed to access
    """

    tool_ids: List[int] = Field(
        default_factory=list, description="Tool IDs this token can access"
    )


class TokenUpdate(BaseModel):
    """
    Token update schema.

    Attributes:
        name: Token name
        description: Token description
        tool_ids: Tool IDs this token is allowed to access (replaces existing)
    """

    name: Optional[str] = Field(
        default=None, description="Token name", min_length=1, max_length=50
    )
    description: Optional[str] = Field(
        default=None, description="Token description", max_length=500
    )
    tool_ids: Optional[List[int]] = Field(
        default=None, description="Tool IDs this token can access (replaces existing)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate token name is not blank when provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Token name cannot be empty")
            return v.strip()
        return v


class TokenResponse(TokenBase):
    """
    Token response schema.

    Attributes:
        id: Token ID
        token: Token secret value
        tool_ids: Tool IDs this token can access
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    id: int = Field(description="Token ID")
    token: str = Field(description="Token secret value")
    tool_ids: List[int] = Field(
        default_factory=list, description="Tool IDs this token can access"
    )
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    updated_by: Optional[str] = Field(default=None, description="Updater username")


class TokenToolsRequest(BaseModel):
    """
    Token tool binding request schema.

    Attributes:
        tool_ids: List of tool IDs to associate with the token
    """

    tool_ids: List[int] = Field(description="List of tool IDs")
