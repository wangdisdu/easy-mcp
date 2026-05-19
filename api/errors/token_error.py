"""
Token error definitions.
"""

from api.errors.base_error import ServiceError


class TokenError(ServiceError):
    """Base token error."""

    def __init__(self, message: str, error_code: str = "TOKEN_ERROR"):
        super().__init__(message, error_code)


class TokenNotFoundError(TokenError):
    """Token not found error."""

    def __init__(self, token_id: int = None, name: str = None):
        if token_id:
            message = f"Token with ID {token_id} not found"
        elif name:
            message = f"Token with name '{name}' not found"
        else:
            message = "Token not found"
        super().__init__(message, "TOKEN_NOT_FOUND")


class TokenAlreadyExistsError(TokenError):
    """Token already exists error."""

    def __init__(self, name: str):
        message = f"Token with name '{name}' already exists"
        super().__init__(message, "TOKEN_ALREADY_EXISTS")
