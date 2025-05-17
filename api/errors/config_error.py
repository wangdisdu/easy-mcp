"""
Configuration-related error classes.
"""

from typing import Optional, Dict, Any
from api.errors.base_error import ServiceError


class ConfigNotFoundError(ServiceError):
    """
    Exception raised when a configuration is not found.
    """

    def __init__(
        self,
        config_id: Optional[int] = None,
        name: Optional[str] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        if config_id is not None:
            details["config_id"] = config_id

        if name is not None:
            details["name"] = name

        identifier = config_id or name

        if reason is None:
            reason = "未找到配置"

        if description is None:
            if identifier is not None:
                description = f"未找到配置: {identifier}"
            else:
                description = "未找到配置"

        super().__init__(
            reason=reason,
            description=description,
            code="CONFIG_NOT_FOUND",
            details=details,
        )


class ConfigAlreadyExistsError(ServiceError):
    """
    Exception raised when a configuration already exists.
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
            reason = "配置已存在"

        if description is None:
            description = f"配置已存在: name={name}"

        super().__init__(
            reason=reason,
            description=description,
            code="CONFIG_ALREADY_EXISTS",
            details=details,
        )


class ConfigInUseError(ServiceError):
    """
    Exception raised when a configuration is in use and cannot be modified or deleted.
    """

    def __init__(
        self,
        config_id: int,
        used_by_tools: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["config_id"] = config_id

        if used_by_tools:
            details["used_by_tools"] = used_by_tools

        if reason is None:
            reason = "配置正在使用中"

        if description is None:
            description = "配置正在被工具使用，无法删除"

        super().__init__(
            reason=reason,
            description=description,
            code="CONFIG_IN_USE",
            details=details,
        )


class ConfigValidationError(Exception):
    """
    Exception raised when configuration validation fails.
    """

    def __init__(
        self,
        config_id: int,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.config_id = config_id
        self.error_message = error_message
        self.details = details or {}

        super().__init__(f"配置验证失败: {error_message}")
