"""
Tool schemas.
"""

import json
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator


class ToolBase(BaseModel):
    """
    Base tool schema.

    Attributes:
        name: Tool name
        description: Tool description
        type: Tool type (basic or http)
        setting: Advanced settings (JSON string)
        parameters: Tool parameters (JSON Schema)
        code: Tool implementation code
    """

    name: str = Field(description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    type: str = Field(default="basic", description="Tool type (basic or http)")
    setting: Dict[str, Any] = Field(
        default_factory=dict, description="Advanced settings (JSON string)"
    )
    parameters: Dict[str, Any] = Field(description="Tool parameters (JSON Schema)")
    code: str = Field(description="Tool implementation code")


class ToolCreate(ToolBase):
    """
    Tool creation schema.

    Attributes:
        config_ids: Config IDs
        func_ids: Function IDs
    """

    config_ids: Optional[List[int]] = Field(
        default_factory=list, description="Config IDs"
    )
    func_ids: Optional[List[int]] = Field(
        default_factory=list, description="Function IDs"
    )


class ToolUpdate(ToolBase):
    """
    Tool update schema.

    Attributes:
        config_ids: Config IDs
        func_ids: Function IDs
    """

    config_ids: Optional[List[int]] = Field(
        default_factory=list, description="Config IDs"
    )
    func_ids: Optional[List[int]] = Field(
        default_factory=list, description="Function IDs"
    )


class ToolResponse(ToolBase):
    """
    Tool response schema.

    Attributes:
        id: Tool ID
        is_enabled: Whether the tool is enabled
        current_version: Current version number
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    id: int = Field(description="Tool ID")
    is_enabled: bool = Field(description="Whether the tool is enabled")
    current_version: Optional[int] = Field(
        default=None, description="Current version number"
    )
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    updated_by: Optional[str] = Field(default=None, description="Updater username")

    class Config:
        from_attributes = True

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_parameters(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @field_validator("setting", mode="before")
    @classmethod
    def parse_setting(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


class ToolDeployBase(BaseModel):
    """
    Base tool deployment schema.

    Attributes:
        version: Version number
        parameters: Tool parameters (JSON Schema)
        type: Tool type (basic or http)
        setting: Advanced settings (JSON string)
        code: Tool implementation code
        description: Version description
    """

    version: int = Field(description="Version number")
    parameters: Dict[str, Any] = Field(description="Tool parameters (JSON Schema)")
    type: str = Field(default="basic", description="Tool type (basic or http)")
    setting: Dict[str, Any] = Field(
        default_factory=dict, description="Advanced settings (JSON string)"
    )
    code: str = Field(description="Tool implementation code")
    description: Optional[str] = Field(default=None, description="Version description")


class ToolDeployResponse(ToolDeployBase):
    """
    Tool deployment response schema.

    Attributes:
        id: Deployment record ID
        tool_id: Tool ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    id: int = Field(description="Deployment record ID")
    tool_id: int = Field(description="Tool ID")
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    updated_by: Optional[str] = Field(default=None, description="Updater username")

    class Config:
        from_attributes = True

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_parameters(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @field_validator("setting", mode="before")
    @classmethod
    def parse_setting(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


class ToolDebugRequest(BaseModel):
    """
    Tool debug request schema.

    Attributes:
        parameters: Tool parameters
    """

    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )


class ToolDebugResponse(BaseModel):
    """
    Tool debug response schema.

    Attributes:
        result: Debug result
        logs: Debug logs
        success: Whether the execution was successful
        error_message: Error message if execution failed
    """

    result: Optional[Any] = Field(default=None, description="Debug result")
    logs: List[str] = Field(default_factory=list, description="Debug logs")
    success: bool = Field(
        default=True, description="Whether the execution was successful"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )


class BuiltinToolInfo(BaseModel):
    """
    Builtin tool information schema.

    Attributes:
        id: Tool ID (directory name)
        name: Tool name
        description: Tool description
        has_config: Whether the tool has configuration
    """

    id: str = Field(description="Tool ID (directory name)")
    name: str = Field(description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    has_config: bool = Field(
        default=False, description="Whether the tool has configuration"
    )


class BuiltinToolListResponse(BaseModel):
    """
    Builtin tool list response schema.

    Attributes:
        tools: List of builtin tools
    """

    tools: List[BuiltinToolInfo] = Field(description="List of builtin tools")


class BuiltinToolImportRequest(BaseModel):
    """
    Builtin tool import request schema.

    Attributes:
        tool_id: Tool ID to import
    """

    tool_id: str = Field(description="Tool ID to import")
