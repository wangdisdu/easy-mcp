"""
Tool constants definition.
"""


# Tool types
class ToolType:
    """Tool type constants."""

    BASIC = "basic"
    HTTP = "http"
    DATABASE = "database"

    # All valid tool types
    ALL_TYPES = [BASIC, HTTP, DATABASE]

    @classmethod
    def is_valid(cls, tool_type: str) -> bool:
        """Check if tool type is valid."""
        return tool_type in cls.ALL_TYPES

    @classmethod
    def get_display_name(cls, tool_type: str) -> str:
        """Get display name for tool type."""
        display_names = {
            cls.BASIC: "基础工具",
            cls.HTTP: "HTTP工具",
            cls.DATABASE: "数据库工具",
        }
        return display_names.get(tool_type, "未知工具")
