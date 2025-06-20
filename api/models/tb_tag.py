"""
Tag model.
"""

from typing import Optional

from sqlalchemy import BigInteger, Index, Text
from sqlmodel import Field, SQLModel


class TbTag(SQLModel, table=True):
    """
    Tag table model.

    Attributes:
        id: Tag ID
        name: Tag name
        description: Tag description
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_tag"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)


class TbToolTag(SQLModel, table=True):
    """
    Tool-Tag association table model.

    Attributes:
        id: Association ID
        tool_id: Tool ID
        tag_id: Tag ID
        created_at: Creation time (UnixMS)
        created_by: Creator username
    """

    __tablename__ = "tb_tool_tag"

    id: int = Field(primary_key=True)
    tool_id: int = Field(index=True)
    tag_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index("ix_tb_tool_tag_tool_id_tag_id", "tool_id", "tag_id", unique=True),
    )
