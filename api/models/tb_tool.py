"""
Tool model.
"""

from typing import Optional

from sqlalchemy import BigInteger, Index, Text
from sqlmodel import Field, SQLModel


class TbTool(SQLModel, table=True):
    """
    Tool table model.

    Attributes:
        id: Tool ID
        name: Tool name
        description: Tool description
        type: Tool type (basic or http)
        setting: Advanced settings (JSON string)
        parameters: Tool parameters (JSON Schema)
        code: Tool implementation code
        is_enabled: Whether the tool is enabled
        current_version: Current version number
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tool"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)
    type: str = Field(default="basic")
    setting: str = Field(default="{}", sa_type=Text)
    parameters: str = Field(default="{}", sa_type=Text)
    code: str = Field(sa_type=Text)
    is_enabled: bool = Field(default=True)
    current_version: Optional[int] = Field(default=None)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)


class TbToolDeploy(SQLModel, table=True):
    """
    Tool deployment history table model.

    Attributes:
        id: Deployment record ID
        tool_id: Tool ID
        version: Version number
        type: Tool type (basic or http)
        setting: Advanced settings (JSON string)
        parameters: Tool parameters (JSON Schema)
        code: Tool implementation code
        description: Version description
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tool_deploy"

    id: int = Field(primary_key=True)
    tool_id: int = Field(index=True)
    version: int = Field()
    type: str = Field(default="basic")
    setting: str = Field(default="{}", sa_type=Text)
    parameters: str = Field(default="{}", sa_type=Text)
    code: str = Field(sa_type=Text)
    description: Optional[str] = Field(default=None, sa_type=Text)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index("ix_tb_tool_deploy_tool_id_version", "tool_id", "version", unique=True),
    )


class TbToolFunc(SQLModel, table=True):
    """
    Tool-Function association table model.

    Attributes:
        id: Association ID
        tool_id: Tool ID
        func_id: Function ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tool_func"

    id: int = Field(primary_key=True)
    tool_id: int = Field(index=True)
    func_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index("ix_tb_tool_func_tool_id_func_id", "tool_id", "func_id", unique=True),
    )


class TbToolConfig(SQLModel, table=True):
    """
    Tool-Config association table model.

    Attributes:
        id: Association ID
        tool_id: Tool ID
        config_id: Config ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tool_config"

    id: int = Field(primary_key=True)
    tool_id: int = Field(index=True)
    config_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index(
            "ix_tb_tool_config_tool_id_config_id", "tool_id", "config_id", unique=True
        ),
    )


class TbToolLog(SQLModel, table=True):
    """
    Tool log table model.

    Attributes:
        id: Log ID
        tool_name: Tool name
        tool_id: Tool ID
        call_type: Call type (mcp, debug)
        request_time: Request time (Unix seconds)
        response_time: Response time (Unix seconds)
        duration_ms: Duration in milliseconds
        is_success: Whether the call was successful
        error_message: Error message if failed
        request_params: Request parameters (JSON string)
        response_data: Response data (JSON string)
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Creation time (UnixMS)
    """

    __tablename__ = "tb_tool_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_name: str = Field(index=True)
    tool_id: Optional[int] = Field(default=None, index=True)
    call_type: str = Field(index=True)  # mcp, debug
    request_time: int = Field(index=True, sa_type=BigInteger)
    response_time: Optional[int] = Field(default=None, sa_type=BigInteger)
    duration_ms: Optional[int] = Field(default=None, index=True)
    is_success: bool = Field(default=False, index=True)
    error_message: Optional[str] = Field(default=None)
    request_params: Optional[str] = Field(default=None)
    response_data: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: int = Field(index=True, sa_type=BigInteger)
