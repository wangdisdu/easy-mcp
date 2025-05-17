"""
Usage relationship schemas.
"""

from typing import List

from pydantic import BaseModel, Field

from api.schemas.func_schema import FuncResponse
from api.schemas.tool_schema import ToolResponse


class ConfigUsageResponse(BaseModel):
    """
    Configuration usage response schema.

    Attributes:
        tools: List of tools using this configuration
    """

    tools: List[ToolResponse] = Field(
        description="List of tools using this configuration"
    )


class FuncUsageResponse(BaseModel):
    """
    Function usage response schema.

    Attributes:
        tools: List of tools using this function
        funcs: List of functions that depend on this function
    """

    tools: List[ToolResponse] = Field(description="List of tools using this function")
    funcs: List[FuncResponse] = Field(
        description="List of functions that depend on this function"
    )
