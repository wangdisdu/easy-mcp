"""
Base error classes for the application.
"""

from typing import Optional, Dict, Any


class ServiceError(ValueError):
    """
    Base class for all service-level exceptions in the application.

    This exception is used for all business logic errors that need to communicate
    specific error messages and reasons to the client.

    Attributes:
        code: String code identifying the type of error
        reason: Human-readable reason for the error
        description: More detailed description of the error
        details: Additional details about the error (optional)
    """

    def __init__(
        self,
        reason: str,
        description: Optional[str] = None,
        code: str = "SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.reason = reason
        self.description = description or reason
        self.details = details or {}
        super().__init__(self.description)


class ValidationError(ServiceError):
    """
    Exception raised when validation fails.
    """

    def __init__(
        self,
        reason: str = "验证失败",
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            reason=reason,
            description=description,
            code="VALIDATION_ERROR",
            details=details,
        )
