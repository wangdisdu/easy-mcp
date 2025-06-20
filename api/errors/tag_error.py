"""
Tag error definitions.
"""

from api.errors.base_error import ServiceError


class TagError(ServiceError):
    """Base tag error."""

    def __init__(self, message: str, error_code: str = "TAG_ERROR"):
        super().__init__(message, error_code)


class TagNotFoundError(TagError):
    """Tag not found error."""

    def __init__(self, tag_id: int = None, name: str = None):
        if tag_id:
            message = f"Tag with ID {tag_id} not found"
        elif name:
            message = f"Tag with name '{name}' not found"
        else:
            message = "Tag not found"
        super().__init__(message, "TAG_NOT_FOUND")


class TagAlreadyExistsError(TagError):
    """Tag already exists error."""

    def __init__(self, name: str):
        message = f"Tag with name '{name}' already exists"
        super().__init__(message, "TAG_ALREADY_EXISTS")


class TagInUseError(TagError):
    """Tag in use error."""

    def __init__(self, tag_id: int, tool_count: int):
        message = f"Tag with ID {tag_id} is in use by {tool_count} tool(s) and cannot be deleted"
        super().__init__(message, "TAG_IN_USE")
