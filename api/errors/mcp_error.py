"""
MCP-related error classes.
"""

from typing import Optional, Dict, Any

from api.errors.base_error import ServiceError


class McpMessageHandlingError(ServiceError):
    """
    Exception raised when handling MCP messages fails.
    """

    def __init__(
        self,
        error_message: str,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["error_message"] = error_message

        if reason is None:
            reason = "MCP 消息处理失败"

        if description is None:
            description = f"MCP 消息处理失败: {error_message}"

        super().__init__(
            reason=reason,
            description=description,
            code="MCP_MESSAGE_HANDLING_ERROR",
            details=details,
        )


class McpToolExecutionError(ServiceError):
    """
    Exception raised when MCP tool execution fails.
    """

    def __init__(
        self,
        tool_name: str,
        error_message: str,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["tool_name"] = tool_name
        details["error_message"] = error_message

        if reason is None:
            reason = "MCP 工具执行失败"

        if description is None:
            description = f"MCP 工具 '{tool_name}' 执行失败: {error_message}"

        super().__init__(
            reason=reason,
            description=description,
            code="MCP_TOOL_EXECUTION_ERROR",
            details=details,
        )
