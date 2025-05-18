"""
Tool-related error classes.
"""

from typing import Optional, Dict, Any

from api.errors.base_error import ServiceError


class ToolNotFoundError(ServiceError):
    """
    Exception raised when a tool is not found.
    """

    def __init__(
        self,
        tool_id: Optional[int] = None,
        name: Optional[str] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        if tool_id is not None:
            details["tool_id"] = tool_id

        if name is not None:
            details["name"] = name

        identifier = tool_id or name

        if reason is None:
            reason = "未找到工具"

        if description is None:
            if identifier is not None:
                description = f"未找到工具: {identifier}"
            else:
                description = "未找到工具"

        super().__init__(
            reason=reason,
            description=description,
            code="TOOL_NOT_FOUND",
            details=details,
        )


class ToolAlreadyExistsError(ServiceError):
    """
    Exception raised when a tool already exists.
    """

    def __init__(
        self,
        name: str,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["name"] = name

        if reason is None:
            reason = "工具已存在"

        if description is None:
            description = f"工具已存在: name={name}"

        super().__init__(
            reason=reason,
            description=description,
            code="TOOL_ALREADY_EXISTS",
            details=details,
        )


class ToolInUseError(ServiceError):
    """
    Exception raised when a tool is in use and cannot be modified or deleted.
    """

    def __init__(
        self,
        tool_id: int,
        reason: Optional[str] = None,
        description: str = "工具正在使用中，无法删除",
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["tool_id"] = tool_id

        if reason is None:
            reason = "工具正在使用中"

        super().__init__(
            reason=reason,
            description=description,
            code="TOOL_IN_USE",
            details=details,
        )


class ToolVersionNotFoundError(ServiceError):
    """
    Exception raised when a tool version is not found.
    """

    def __init__(
        self,
        tool_id: int,
        version: int,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["tool_id"] = tool_id
        details["version"] = version

        if reason is None:
            reason = "未找到工具版本"

        if description is None:
            description = f"未找到工具版本: 工具ID={tool_id}, 版本={version}"

        super().__init__(
            reason=reason,
            description=description,
            code="TOOL_VERSION_NOT_FOUND",
            details=details,
        )


class ToolExecutionError(ServiceError):
    """
    Exception raised when a tool execution fails.
    """

    def __init__(
        self,
        tool_id: int,
        error_message: str,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["tool_id"] = tool_id
        details["error_message"] = error_message

        if reason is None:
            reason = "工具执行失败"

        if description is None:
            description = f"工具执行失败: {error_message}"

        super().__init__(
            reason=reason,
            description=description,
            code="TOOL_EXECUTION_ERROR",
            details=details,
        )
