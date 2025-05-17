"""
Audit log model.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class TbAudit(SQLModel, table=True):
    """
    Audit log table model.

    Attributes:
        id: Log ID
        user_id: User ID
        username: Username
        action: Action type
        resource_type: Resource type
        resource_id: Resource ID
        resource_name: Resource name
        details: Action details
        ip_address: IP address
        created_at: Creation time (UnixMS)
    """

    __tablename__ = "tb_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    username: str = Field(index=True)
    action: str = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: Optional[int] = Field(default=None, index=True)
    resource_name: Optional[str] = Field(default=None, index=True)
    details: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    created_at: int = Field(index=True)
