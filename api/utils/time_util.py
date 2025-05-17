"""
Time utility functions.
"""

import time
from datetime import datetime, timezone


def get_current_unix_ms() -> int:
    """
    Get current time as Unix timestamp in milliseconds.

    Returns:
        int: Current time as Unix timestamp in milliseconds
    """
    return int(time.time() * 1000)


def unix_ms_to_datetime(unix_ms: int) -> datetime:
    """
    Convert Unix timestamp in milliseconds to datetime.

    Args:
        unix_ms: Unix timestamp in milliseconds

    Returns:
        datetime: Datetime object
    """
    return datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc)


def datetime_to_unix_ms(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp in milliseconds.

    Args:
        dt: Datetime object

    Returns:
        int: Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)
