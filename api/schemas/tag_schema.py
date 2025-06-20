"""
Tag schemas.
"""

from typing import Optional, List
import re

from pydantic import BaseModel, Field, field_validator


class TagBase(BaseModel):
    """
    Base tag schema.

    Attributes:
        name: Tag name
        description: Tag description
    """

    name: str = Field(description="Tag name", min_length=1, max_length=50)
    description: Optional[str] = Field(
        default=None, description="Tag description", max_length=500
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate tag name - only alphanumeric characters allowed."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        # Check for valid characters (only alphanumeric)
        if not re.match(r"^[a-zA-Z0-9]+$", v.strip()):
            raise ValueError("Tag name can only contain letters and numbers")
        return v.strip()


class TagCreate(TagBase):
    """
    Tag creation schema.
    """

    pass


class TagUpdate(BaseModel):
    """
    Tag update schema.

    Attributes:
        name: Tag name
        description: Tag description
    """

    name: Optional[str] = Field(
        default=None, description="Tag name", min_length=1, max_length=50
    )
    description: Optional[str] = Field(
        default=None, description="Tag description", max_length=500
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate tag name - only alphanumeric characters allowed."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Tag name cannot be empty")
            # Check for valid characters (only alphanumeric)
            if not re.match(r"^[a-zA-Z0-9]+$", v.strip()):
                raise ValueError("Tag name can only contain letters and numbers")
            return v.strip()
        return v


class TagResponse(TagBase):
    """
    Tag response schema.

    Attributes:
        id: Tag ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    id: int = Field(description="Tag ID")
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    updated_by: Optional[str] = Field(default=None, description="Updater username")


class ToolTagRequest(BaseModel):
    """
    Tool tag management request schema.

    Attributes:
        tag_ids: List of tag IDs to associate with the tool
    """

    tag_ids: List[int] = Field(description="List of tag IDs")


class TagWithToolCount(TagResponse):
    """
    Tag response with tool count.

    Attributes:
        tool_count: Number of tools associated with this tag
    """

    tool_count: int = Field(description="Number of tools associated with this tag")
