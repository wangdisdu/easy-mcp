"""
Configuration schemas.
"""

import json
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class ConfigBase(BaseModel):
    """
    Base configuration schema.

    Attributes:
        name: Configuration name
        description: Configuration description
        conf_schema: Configuration schema definition (JSON Schema)
    """

    name: str = Field(description="Configuration name")
    description: Optional[str] = Field(
        default=None, description="Configuration description"
    )
    conf_schema: Dict[str, Any] = Field(
        description="Configuration schema definition (JSON Schema)"
    )


class ConfigCreate(ConfigBase):
    """
    Configuration creation schema.

    Attributes:
        conf_value: Configuration values
    """

    conf_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration values"
    )


class ConfigUpdate(ConfigBase):
    """
    Configuration update schema.

    Attributes:
        conf_value: Configuration values
    """

    conf_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration values"
    )


class ConfigResponse(ConfigBase):
    """
    Configuration response schema.

    Attributes:
        id: Configuration ID
        conf_value: Configuration values
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
    """

    id: int = Field(description="Configuration ID")
    conf_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration values"
    )
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")

    class Config:
        from_attributes = True

    @field_validator("conf_schema", "conf_value", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
