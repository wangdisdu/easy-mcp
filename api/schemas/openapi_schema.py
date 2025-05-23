"""
OpenAPI schemas.
"""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class OpenApiEndpoint(BaseModel):
    """
    OpenAPI endpoint information.

    Attributes:
        path: Endpoint path
        method: HTTP method
        tool: Generated tool name
        description: Generated tool description
        parameters: JSON Schema of endpoint parameters
    """

    path: str = Field(description="Endpoint path")
    method: str = Field(description="HTTP method")
    tool: str = Field(description="Generated tool name")
    description: Optional[str] = Field(
        default=None, description="Generated tool description"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON Schema of endpoint parameters"
    )


class OpenApi(BaseModel):
    """
    OpenAPI model for both response and import request.

    Attributes:
        server: API server URL
        apis: List of API endpoints
    """

    server: str = Field(description="API server URL")
    apis: List[OpenApiEndpoint] = Field(description="List of API endpoints")
