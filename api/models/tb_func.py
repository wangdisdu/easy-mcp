"""
Function model.
"""

from typing import Optional

from sqlalchemy import BigInteger, Index, Text
from sqlmodel import Field, SQLModel


class TbFunc(SQLModel, table=True):
    """
    Function table model.

    Attributes:
        id: Function ID
        name: Function name
        description: Function description
        code: Function implementation code
        current_version: Current version number
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_func"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)
    code: str = Field(sa_type=Text)
    current_version: Optional[int] = Field(default=None)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)


class TbFuncDeploy(SQLModel, table=True):
    """
    Function deployment history table model.

    Attributes:
        id: Deployment record ID
        func_id: Function ID
        version: Version number
        code: Function implementation code
        description: Version description
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_func_deploy"

    id: int = Field(primary_key=True)
    func_id: int = Field(index=True)
    version: int = Field()
    code: str = Field(sa_type=Text)
    description: Optional[str] = Field(default=None, sa_type=Text)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index("ix_tb_func_deploy_func_id_version", "func_id", "version", unique=True),
    )


class TbFuncDepends(SQLModel, table=True):
    """
    Function dependency table model.

    Attributes:
        id: Dependency ID
        func_id: Function ID
        depends_on_func_id: Dependency function ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_func_depends"

    id: int = Field(primary_key=True)
    func_id: int = Field(index=True)
    depends_on_func_id: int = Field(index=True)
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)

    __table_args__ = (
        Index(
            "ix_tb_func_depends_func_id_depends_on_func_id",
            "func_id",
            "depends_on_func_id",
            unique=True,
        ),
    )
