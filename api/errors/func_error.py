"""
Function-related error classes.
"""

from typing import Optional, Dict, Any, List

from api.errors.base_error import ServiceError


class FuncNotFoundError(ServiceError):
    """
    Exception raised when a function is not found.
    """

    def __init__(
        self,
        func_id: Optional[int] = None,
        name: Optional[str] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        if func_id is not None:
            details["func_id"] = func_id

        if name is not None:
            details["name"] = name

        identifier = func_id or name

        if reason is None:
            reason = "未找到函数"

        if description is None:
            if identifier is not None:
                description = f"未找到函数: {identifier}"
            else:
                description = "未找到函数"

        super().__init__(
            reason=reason,
            description=description,
            code="FUNC_NOT_FOUND",
            details=details,
        )


class FuncAlreadyExistsError(ServiceError):
    """
    Exception raised when a function already exists.
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
            reason = "函数已存在"

        if description is None:
            description = f"函数已存在: name={name}"

        super().__init__(
            reason=reason,
            description=description,
            code="FUNC_ALREADY_EXISTS",
            details=details,
        )


class FuncInUseError(ServiceError):
    """
    Exception raised when a function is in use and cannot be modified or deleted.
    """

    def __init__(
        self,
        func_id: int,
        used_by_tools: Optional[List[Dict[str, Any]]] = None,
        used_by_funcs: Optional[List[Dict[str, Any]]] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["func_id"] = func_id

        if used_by_tools:
            details["used_by_tools"] = used_by_tools

        if used_by_funcs:
            details["used_by_funcs"] = used_by_funcs

        if reason is None:
            reason = "函数正在使用中"

        if description is None:
            description = "函数正在被其他工具或函数使用，无法删除"

        super().__init__(
            reason=reason,
            description=description,
            code="FUNC_IN_USE",
            details=details,
        )


class FuncVersionNotFoundError(ServiceError):
    """
    Exception raised when a function version is not found.
    """

    def __init__(
        self,
        func_id: int,
        version: int,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["func_id"] = func_id
        details["version"] = version

        if reason is None:
            reason = "未找到函数版本"

        if description is None:
            description = f"未找到函数版本: 函数ID={func_id}, 版本={version}"

        super().__init__(
            reason=reason,
            description=description,
            code="FUNC_VERSION_NOT_FOUND",
            details=details,
        )


class CircularDependencyError(ServiceError):
    """
    Exception raised when a circular dependency is detected.
    """

    def __init__(
        self,
        func_id: int,
        dependency_path: List[int],
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        details["func_id"] = func_id
        details["dependency_path"] = dependency_path

        path_str = " -> ".join(map(str, dependency_path + [func_id]))

        if reason is None:
            reason = "检测到循环依赖"

        if description is None:
            description = f"检测到循环依赖: {path_str}"

        super().__init__(
            reason=reason,
            description=description,
            code="CIRCULAR_DEPENDENCY",
            details=details,
        )
