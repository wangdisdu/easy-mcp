"""
Audit log schemas.
"""

import json
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class AuditResponse(BaseModel):
    """
    Audit log response schema.

    Attributes:
        id: Log ID
        user_id: User ID
        username: Username
        action: Action type
        resource_type: Resource type
        resource_id: Resource ID
        resource_name: Resource name
        details: Action details
        ip_address: IP address
        created_at: Creation time (UnixMS)
    """

    id: int = Field(description="Log ID")
    user_id: Optional[int] = Field(default=None, description="User ID")
    username: str = Field(description="Username")
    action: str = Field(description="Action type")
    resource_type: str = Field(description="Resource type")
    resource_id: Optional[int] = Field(default=None, description="Resource ID")
    resource_name: Optional[str] = Field(default=None, description="Resource name")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Action details"
    )
    ip_address: Optional[str] = Field(default=None, description="IP address")
    created_at: int = Field(description="Creation time (UnixMS)")

    class Config:
        from_attributes = True

    @field_validator("details", mode="before")
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
