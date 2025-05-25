"""
User model.
"""

from typing import Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class TbUser(SQLModel, table=True):
    """
    User table model.

    Attributes:
        id: User ID
        username: Username
        password: Password (hashed)
        email: Email address
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
        updated_by: Updater username
    """

    __tablename__ = "tb_user"

    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str = Field()
    email: str = Field()
    created_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    updated_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
