"""
Log service for managing system logs.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Create logger
logger = logging.getLogger(__name__)


class LogService:
    """
    Service for managing system logs.
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize log service.

        Args:
            log_dir: Directory containing log files. If None, uses default logs directory.
        """
        # Use provided log directory or default to logs directory
        self.log_dir = Path(log_dir) if log_dir else Path("logs")

        # Create logs directory if it doesn't exist
        if not self.log_dir.exists():
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created logs directory: {self.log_dir}")
            except Exception as e:
                logger.error(f"Failed to create logs directory: {str(e)}")

    def get_log_files(self) -> List[Dict[str, Any]]:
        """
        Get list of available log files.

        Returns:
            List[Dict[str, Any]]: List of log file information
        """
        log_files = []

        try:
            # Get all files in log directory
            for file_path in self.log_dir.glob("*.log*"):
                if file_path.is_file():
                    # Get file stats
                    stats = file_path.stat()

                    # Create file info
                    file_info = {
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stats.st_size,
                        "size_human": self._format_size(stats.st_size),
                        "modified_at": int(stats.st_mtime * 1000),  # Convert to UnixMS
                        "modified_at_human": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    }

                    log_files.append(file_info)

            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x["modified_at"], reverse=True)

        except Exception as e:
            logger.error(f"Error getting log files: {str(e)}")

        return log_files

    def get_log_content(self, file_name: str, max_lines: int = 1000, tail: bool = True) -> Tuple[str, int]:
        """
        Get content of a log file.

        Args:
            file_name: Name of the log file
            max_lines: Maximum number of lines to return
            tail: If True, returns the last max_lines, otherwise returns from the beginning

        Returns:
            Tuple[str, int]: Log content and total number of lines
        """
        file_path = self.log_dir / file_name
        content = ""
        total_lines = 0

        try:
            # Check if file exists and is within the logs directory
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Log file not found: {file_name}")
                return f"Log file not found: {file_name}", 0

            # Security check: ensure the file is within the logs directory
            if not str(file_path.resolve()).startswith(str(self.log_dir.resolve())):
                logger.warning(f"Attempted to access file outside logs directory: {file_name}")
                return "Access denied: File is outside logs directory", 0

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                if tail:
                    # Count total lines first
                    lines = f.readlines()
                    total_lines = len(lines)

                    # Get the last max_lines
                    start_line = max(0, total_lines - max_lines)
                    content_lines = lines[start_line:]
                    content = "".join(content_lines)
                else:
                    # Read from beginning
                    lines = []
                    for i, line in enumerate(f):
                        if i < max_lines:
                            lines.append(line)
                        total_lines = i + 1

                    content = "".join(lines)

        except Exception as e:
            logger.error(f"Error reading log file {file_name}: {str(e)}")
            content = f"Error reading log file: {str(e)}"
            total_lines = 0

        return content, total_lines

    # 日志文件下载功能已移除

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Human-readable size
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024 or unit == "GB":
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
