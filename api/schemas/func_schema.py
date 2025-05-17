"""
Function schemas.
"""

from typing import Optional, List

from pydantic import BaseModel, Field


class FuncBase(BaseModel):
    """
    Base function schema.

    Attributes:
        name: Function name
        description: Function description
        code: Function implementation code
    """

    name: str = Field(description="Function name")
    description: Optional[str] = Field(default=None, description="Function description")
    code: str = Field(description="Function implementation code")


class FuncCreate(FuncBase):
    """
    Function creation schema.

    Attributes:
        depend_ids: Dependency function IDs
    """

    depend_ids: Optional[List[int]] = Field(
        default_factory=list, description="Dependency function IDs"
    )


class FuncUpdate(FuncBase):
    """
    Function update schema.

    Attributes:
        depend_ids: Dependency function IDs
    """

    depend_ids: Optional[List[int]] = Field(
        default_factory=list, description="Dependency function IDs"
    )


class FuncResponse(FuncBase):
    """
    Function response schema.

    Attributes:
        id: Function ID
        current_version: Current version number
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
    """

    id: int = Field(description="Function ID")
    current_version: Optional[int] = Field(
        default=None, description="Current version number"
    )
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")

    class Config:
        from_attributes = True


class FuncDeployBase(BaseModel):
    """
    Base function deployment schema.

    Attributes:
        version: Version number
        code: Function implementation code
        description: Version description
    """

    version: int = Field(description="Version number")
    code: str = Field(description="Function implementation code")
    description: Optional[str] = Field(default=None, description="Version description")


class FuncDeployResponse(FuncDeployBase):
    """
    Function deployment response schema.

    Attributes:
        id: Deployment record ID
        func_id: Function ID
        created_at: Creation time (UnixMS)
        updated_at: Update time (UnixMS)
        created_by: Creator username
    """

    id: int = Field(description="Deployment record ID")
    func_id: int = Field(description="Function ID")
    created_at: Optional[int] = Field(
        default=None, description="Creation time (UnixMS)"
    )
    updated_at: Optional[int] = Field(default=None, description="Update time (UnixMS)")
    created_by: Optional[str] = Field(default=None, description="Creator username")

    class Config:
        from_attributes = True
