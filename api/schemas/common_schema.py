"""
Common schemas.
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any

from pydantic import BaseModel, Field

# Type variable for generic models
T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination parameters.

    Attributes:
        page: Page number (1-based)
        size: Page size
    """

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response.

    Attributes:
        code: Response code (0 for success)
        message: Response message
        data: Response data
        total: Total number of items
    """

    code: int = Field(default=0, description="Response code (0 for success)")
    message: str = Field(default="success", description="Response message")
    data: List[T] = Field(default_factory=list, description="Response data")
    total: int = Field(default=0, description="Total number of items")


class Response(BaseModel, Generic[T]):
    """
    Standard response.

    Attributes:
        code: Response code (0 for success)
        message: Response message
        data: Response data
    """

    code: int = Field(default=0, description="Response code (0 for success)")
    message: str = Field(default="success", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")


class ErrorResponse(BaseModel):
    """
    Error response.

    Attributes:
        code: Error code
        message: Error message
        details: Error details
    """

    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
