"""
Audit utility functions.
"""

import functools
import inspect
import json
from typing import Optional, Any, Callable, TypeVar, Awaitable, cast

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.tb_audit import TbAudit
from api.utils.time_util import get_current_unix_ms

# Type variables for function signatures
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def audit(operation_type: str, object_type: str) -> Callable[[F], F]:
    """
    Decorator to audit operations.

    Args:
        operation_type: Type of operation (create, update, delete, etc.)
        object_type: Type of object (user, tool, function, etc.)

    Returns:
        Callable: Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Extract parameters
            db: Optional[AsyncSession] = None
            current_user: Optional[str] = None
            request: Optional[Request] = None
            resource_id: Optional[int] = None
            resource_name: Optional[str] = None

            # Find parameters in bound arguments
            for param_name, param_value in bound_args.arguments.items():
                if param_name == "db" and isinstance(param_value, AsyncSession):
                    db = param_value
                elif param_name == "current_user" and param_value is not None:
                    if hasattr(param_value, "username"):
                        current_user = param_value.username
                    else:
                        current_user = str(param_value)
                elif param_name == "request" and isinstance(param_value, Request):
                    request = param_value
                elif param_name.endswith("_id") and isinstance(param_value, int):
                    resource_id = param_value
                elif param_name in ["name", "username"] and isinstance(
                    param_value, str
                ):
                    resource_name = param_value

            # Execute the function
            try:
                result = await func(*args, **kwargs)

                # Create audit log if db is available
                if db is not None:
                    # If result has id and resource_id is None, use result.id
                    if (
                        resource_id is None
                        and result is not None
                        and hasattr(result, "id")
                    ):
                        resource_id = result.id

                    # If result has name and resource_name is None, use result.name or result.username
                    if resource_name is None and result is not None:
                        if hasattr(result, "name"):
                            resource_name = result.name
                        elif hasattr(result, "username"):
                            resource_name = result.username

                    # Create audit log
                    audit_log = TbAudit(
                        username=current_user or "system",
                        action=operation_type,
                        resource_type=object_type,
                        resource_id=resource_id,
                        resource_name=resource_name,
                        details="{}",  # Could add more details if needed
                        ip_address=request.client.host if request else None,
                        created_at=get_current_unix_ms(),
                    )

                    db.add(audit_log)
                    await db.commit()

                return result

            except Exception as e:
                # Log error in audit log if db is available
                if db is not None:
                    audit_log = TbAudit(
                        username=current_user or "system",
                        action=f"{operation_type}_error",
                        resource_type=object_type,
                        resource_id=resource_id,
                        resource_name=resource_name,
                        details=json.dumps({"error": str(e)}),
                        ip_address=request.client.host if request else None,
                        created_at=get_current_unix_ms(),
                    )

                    db.add(audit_log)
                    await db.commit()

                # Re-raise the exception
                raise

        return cast(F, wrapper)

    return decorator
