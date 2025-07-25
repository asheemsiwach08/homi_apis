import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_datetime_to_date(datetime_string):
    """
    Convert a datetime string to date format.
    
    Args:
        datetime_string (str): Datetime string in format like '2025-07-08T18:05:43.769963'
    
    Returns:
        str: Date string in format 'YYYY-MM-DD'
    """
    try:
        # Parse the datetime string
        dt = datetime.fromisoformat(datetime_string)
        # Extract just the date part
        date_only = dt.date()
        # Convert to string format
        return date_only.isoformat()
    except ValueError as e:
        logger.error(f"Error parsing datetime string: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Your example datetime string
    datetime_str = "2025-07-08T18:05:43.769963"
    
    # Convert to date
    date_result = convert_datetime_to_date(datetime_str)
    
    logger.info(f"Original datetime: {datetime_str}")
    logger.info(f"Converted date: {date_result}")
    
    # Alternative method using string slicing (if you know the format is always the same)
    def simple_date_extraction(datetime_string):
        """Simple method using string slicing for consistent format."""
        return datetime_string.split('T')[0]
    
    simple_result = simple_date_extraction(datetime_str)
    logger.info(f"Simple extraction: {simple_result}")    