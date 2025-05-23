"""
Tool log schemas.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ToolLogResponse(BaseModel):
    """
    Tool log response schema.

    Attributes:
        id: Log ID
        tool_name: Tool name
        tool_id: Tool ID
        call_type: Call type (mcp, debug)
        request_time: Request time (UnixMS)
        response_time: Response time (UnixMS)
        duration_ms: Duration in milliseconds
        is_success: Whether the call was successful
        error_message: Error message if failed
        request_params: Request parameters
        response_data: Response data
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Creation time (UnixMS)
    """

    id: int = Field(description="Log ID")
    tool_name: str = Field(description="Tool name")
    tool_id: Optional[int] = Field(default=None, description="Tool ID")
    call_type: str = Field(description="Call type (mcp, debug)")
    request_time: int = Field(description="Request time (UnixMS)")
    response_time: Optional[int] = Field(
        default=None, description="Response time (UnixMS)"
    )
    duration_ms: Optional[int] = Field(
        default=None, description="Duration in milliseconds"
    )
    is_success: bool = Field(description="Whether the call was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    request_params: Optional[str] = Field(
        default=None, description="Request parameters"
    )
    response_data: Optional[str] = Field(default=None, description="Response data")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    created_at: int = Field(description="Creation time (UnixMS)")

    class Config:
        from_attributes = True


class ToolStatsResponse(BaseModel):
    """
    Tool statistics response schema.

    Attributes:
        total_calls: Total number of calls
        success_calls: Number of successful calls
        failed_calls: Number of failed calls
        success_rate: Success rate percentage
        avg_duration_ms: Average duration in milliseconds
        calls_today: Number of calls today
        calls_this_week: Number of calls this week
        calls_this_month: Number of calls this month
        mcp_calls: Number of MCP calls
        debug_calls: Number of debug calls
    """

    total_calls: int = Field(description="Total number of calls")
    success_calls: int = Field(description="Number of successful calls")
    failed_calls: int = Field(description="Number of failed calls")
    success_rate: float = Field(description="Success rate percentage")
    avg_duration_ms: Optional[float] = Field(
        default=None, description="Average duration in milliseconds"
    )
    calls_today: int = Field(description="Number of calls today")
    calls_this_week: int = Field(description="Number of calls this week")
    calls_this_month: int = Field(description="Number of calls this month")
    mcp_calls: int = Field(description="Number of MCP calls")
    debug_calls: int = Field(description="Number of debug calls")


class ToolTrendResponse(BaseModel):
    """
    Tool trend response schema.

    Attributes:
        date: Date (YYYY-MM-DD format)
        total_calls: Total number of calls
        success_calls: Number of successful calls
        failed_calls: Number of failed calls
        mcp_calls: Number of MCP calls
        debug_calls: Number of debug calls
        avg_duration_ms: Average duration in milliseconds
    """

    date: str = Field(description="Date (YYYY-MM-DD format)")
    total_calls: int = Field(description="Total number of calls")
    success_calls: int = Field(description="Number of successful calls")
    failed_calls: int = Field(description="Number of failed calls")
    mcp_calls: int = Field(description="Number of MCP calls")
    debug_calls: int = Field(description="Number of debug calls")
    avg_duration_ms: Optional[float] = Field(
        default=None, description="Average duration in milliseconds"
    )


class ToolUsageStatsResponse(BaseModel):
    """
    Tool usage statistics response schema.

    Attributes:
        tool_name: Tool name
        tool_id: Tool ID
        total_calls: Total number of calls
        success_calls: Number of successful calls
        failed_calls: Number of failed calls
        mcp_calls: Number of MCP calls
        debug_calls: Number of debug calls
        success_rate: Success rate percentage
        avg_duration_ms: Average duration in milliseconds
        last_call_time: Last call time (UnixMS)
    """

    tool_name: str = Field(description="Tool name")
    tool_id: Optional[int] = Field(default=None, description="Tool ID")
    total_calls: int = Field(description="Total number of calls")
    success_calls: int = Field(description="Number of successful calls")
    failed_calls: int = Field(description="Number of failed calls")
    mcp_calls: int = Field(description="Number of MCP calls")
    debug_calls: int = Field(description="Number of debug calls")
    success_rate: float = Field(description="Success rate percentage")
    avg_duration_ms: Optional[float] = Field(
        default=None, description="Average duration in milliseconds"
    )
    last_call_time: Optional[int] = Field(
        default=None, description="Last call time (UnixMS)"
    )
