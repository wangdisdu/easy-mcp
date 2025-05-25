"""
Configuration model.
"""

from typing import Optional

from sqlalchemy import BigInteger, Text
from sqlmodel import Field, SQLModel


class TbConfig(SQLModel, table=True):
    """
    Configuration table model.

    Attributes:
        id: Configuration ID
        name: Configuration name
        description: Configuration description
        conf_schema: Configuration schema (JSON Schema)
        conf_value: Configuration values
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_config"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)
    conf_schema: str = Field(default="{}", sa_type=Text)
    conf_value: Optional[str] = Field(default=None, sa_type=Text)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
