"""
Timezone utilities for consistent timestamp handling across the application.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# Indian Standard Time (IST) timezone
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    """Get current datetime in IST timezone.
    
    Returns:
        Current datetime in IST timezone
    """
    return datetime.now(IST_TIMEZONE)


def get_ist_timestamp() -> str:
    """Get current timestamp string in IST timezone (ISO format).
    
    Returns:
        Current timestamp string in IST
    """
    return get_ist_now().isoformat()


def get_ist_timestamp_formatted(format_str: str = '%Y-%m-%d %H:%M:%S IST') -> str:
    """Get current timestamp string in IST timezone with custom formatting.
    
    Args:
        format_str: Custom format string for timestamp
        
    Returns:
        Formatted timestamp string in IST
    """
    return get_ist_now().strftime(format_str)


def convert_to_ist(dt: datetime) -> datetime:
    """Convert a datetime object to IST timezone.
    
    Args:
        dt: Datetime object to convert
        
    Returns:
        Datetime object in IST timezone
    """
    if dt.tzinfo is None:
        # If naive datetime, assume it's already in IST
        return dt.replace(tzinfo=IST_TIMEZONE)
    else:
        # If timezone-aware, convert to IST
        return dt.astimezone(IST_TIMEZONE)


def parse_datetime_to_ist(date_str: str) -> Optional[datetime]:
    """Parse date string and convert to IST timezone.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Datetime object in IST timezone or None if parsing fails
    """
    try:
        from dateutil import parser
        parsed_date = parser.parse(date_str)
        return convert_to_ist(parsed_date)
    except:
        return None 