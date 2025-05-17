"""
Tool model.
"""

from typing import Optional

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class TbTool(SQLModel, table=True):
    """
    Tool table model.

    Attributes:
        id: Tool ID
        name: Tool name
        description: Tool description
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

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    parameters: str = Field(default="{}")
    code: str = Field()
    is_enabled: bool = Field(default=True)
    current_version: Optional[int] = Field(default=None)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)


class TbToolDeploy(SQLModel, table=True):
    """
    Tool deployment history table model.

    Attributes:
        id: Deployment record ID
        tool_id: Tool ID
        version: Version number
        parameters: Tool parameters (JSON Schema)
        code: Tool implementation code
        description: Version description
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tool_deploy"

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_id: int = Field(index=True)
    version: int = Field()
    parameters: str = Field(default="{}")
    code: str = Field()
    description: Optional[str] = Field(default=None)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default=None)
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

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_id: int = Field(index=True)
    func_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default=None)
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

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_id: int = Field(index=True)
    config_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index(
            "ix_tb_tool_config_tool_id_config_id", "tool_id", "config_id", unique=True
        ),
    )
