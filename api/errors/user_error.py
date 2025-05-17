"""
User-related error classes.
"""

from typing import Optional, Dict, Any

from api.errors.base_error import ServiceError


class UserNotFoundError(ServiceError):
    """
    Exception raised when a user is not found.
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        if user_id is not None:
            details["user_id"] = user_id

        if username is not None:
            details["username"] = username

        if email is not None:
            details["email"] = email

        identifier = user_id or username or email

        if reason is None:
            reason = "未找到用户"

        if description is None:
            if identifier is not None:
                description = f"未找到用户: {identifier}"
            else:
                description = "未找到用户"

        super().__init__(
            reason=reason,
            description=description,
            code="USER_NOT_FOUND",
            details=details,
        )


class UserAlreadyExistsError(ServiceError):
    """
    Exception raised when a user already exists.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        reason: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}

        if username is not None:
            details["username"] = username

        if email is not None:
            details["email"] = email

        if reason is None:
            reason = "用户已存在"

        if description is None:
            desc_parts = []
            if username is not None:
                desc_parts.append(f"username={username}")
            if email is not None:
                desc_parts.append(f"email={email}")
            description = f"用户已存在: {', '.join(desc_parts)}"

        super().__init__(
            reason=reason,
            description=description,
            code="USER_ALREADY_EXISTS",
            details=details,
        )


class InvalidCredentialsError(ServiceError):
    """
    Exception raised when user credentials are invalid.
    """

    def __init__(
        self,
        reason: str = "无效的凭据",
        description: str = "用户名或密码不正确",
    ):
        super().__init__(
            reason=reason,
            description=description,
            code="INVALID_CREDENTIALS",
        )
