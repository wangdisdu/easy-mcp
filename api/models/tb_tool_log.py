"""
Tool log model.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class TbToolLog(SQLModel, table=True):
    """
    Tool log table model.

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
        request_params: Request parameters (JSON string)
        response_data: Response data (JSON string)
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Creation time (UnixMS)
    """

    __tablename__ = "tb_tool_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_name: str = Field(index=True)
    tool_id: Optional[int] = Field(default=None, index=True)
    call_type: str = Field(index=True)  # mcp, debug
    request_time: int = Field(index=True)
    response_time: Optional[int] = Field(default=None)
    duration_ms: Optional[int] = Field(default=None, index=True)
    is_success: bool = Field(default=False, index=True)
    error_message: Optional[str] = Field(default=None)
    request_params: Optional[str] = Field(default=None)
    response_data: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: int = Field(index=True)
