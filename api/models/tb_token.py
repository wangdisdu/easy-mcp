"""
Token model.

Access tokens for authenticating MCP transport endpoints (SSE / Streamable
HTTP). Each token is associated with a specific set of tools, which scopes
both tool listing and tool execution for requests using that token.
"""

from typing import Optional

from sqlalchemy import BigInteger, Index, Text
from sqlmodel import Field, SQLModel


class TbToken(SQLModel, table=True):
    """
    Token table model.

    Attributes:
        id: Token ID
        name: Token name (human-readable label)
        description: Token description
        token: Token secret value (stored in plaintext, used as bearer)
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_token"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)
    token: str = Field(unique=True, index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)


class TbTokenTool(SQLModel, table=True):
    """
    Token-Tool association table model.

    A token only grants access to the tools explicitly associated here. A
    token with no associations grants access to no tools (least privilege).

    Attributes:
        id: Association ID
        token_id: Token ID
        tool_id: Tool ID
        created_at: Creation time (UnixMS)
        created_by: Creator username
    """

    __tablename__ = "tb_token_tool"

    id: int = Field(primary_key=True)
    token_id: int = Field(index=True)
    tool_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index("ix_tb_token_tool_token_id_tool_id", "token_id", "tool_id", unique=True),
    )
