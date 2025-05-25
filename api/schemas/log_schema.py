"""
Log schemas.
"""

from typing import List

from pydantic import BaseModel, Field


class LogFileInfo(BaseModel):
    """
    Log file information schema.

    Attributes:
        name: File name
        path: File path
        size: File size in bytes
        size_human: Human-readable file size
        modified_at: Modification time (UnixMS)
        modified_at_human: Human-readable modification time
    """

    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    size_human: str = Field(..., description="Human-readable file size")
    modified_at: int = Field(..., description="Modification time (UnixMS)")
    modified_at_human: str = Field(..., description="Human-readable modification time")


class LogFilesResponse(BaseModel):
    """
    Log files response schema.

    Attributes:
        files: List of log files
    """

    files: List[LogFileInfo] = Field(..., description="List of log files")


class LogContentResponse(BaseModel):
    """
    Log content response schema.

    Attributes:
        file_name: Log file name
        content: Log content
        total_lines: Total number of lines in the file
        displayed_lines: Number of lines displayed
    """

    file_name: str = Field(..., description="Log file name")
    content: str = Field(..., description="Log content")
    total_lines: int = Field(..., description="Total number of lines in the file")
    displayed_lines: int = Field(..., description="Number of lines displayed")
