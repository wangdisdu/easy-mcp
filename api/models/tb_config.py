"""
Configuration model.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class TbConfig(SQLModel, table=True):
    """
    Configuration table model.

    Attributes:
        id: Configuration ID
        name: Configuration name
        description: Configuration description
        schema: Configuration schema (JSON Schema)
        values: Configuration values
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    conf_schema: str = Field(default="{}")
    conf_value: Optional[str] = Field(default=None)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
