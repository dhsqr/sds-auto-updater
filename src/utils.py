"""
Utility functions for input validation, error handling, and common operations.
"""

import re
import logging
from typing import Optional, Dict, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_cas_number(cas_number: str) -> bool:
    """
    Validate CAS registry number format.

    Format: XXXXX-XX-X where X is a digit
    Example: 1310-73-2

    Args:
        cas_number: CAS number to validate

    Returns:
        True if valid, False otherwise
    """
    if not cas_number:
        return False

    # CAS number pattern: 2-7 digits, dash, 2 digits, dash, 1 digit
    pattern = r'^\d{2,7}-\d{2}-\d$'

    if not re.match(pattern, cas_number):
        return False

    # Validate check digit
    try:
        parts = cas_number.split('-')
        # Remove dashes and reverse
        digits = (parts[0] + parts[1] + parts[2])[::-1]

        # Calculate checksum
        checksum = sum(int(digit) * (i + 1) for i, digit in enumerate(digits[1:]))
        check_digit = checksum % 10

        return check_digit == int(digits[0])
    except (ValueError, IndexError):
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:190] + (f'.{ext}' if ext else '')

    return filename or 'unnamed'


def validate_supplier(supplier: str) -> bool:
    """
    Validate supplier name against known suppliers.

    Args:
        supplier: Supplier name/key

    Returns:
        True if valid supplier, False otherwise
    """
    valid_suppliers = ['sigma_aldrich', 'merck', 'srl_chemicals']
    return supplier.lower() in valid_suppliers


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


def safe_cast(value: Any, type_func: type, default: Any = None) -> Any:
    """
    Safely cast a value to a type, returning default on failure.

    Args:
        value: Value to cast
        type_func: Type function to cast to (int, float, str, etc.)
        default: Default value if cast fails

    Returns:
        Casted value or default
    """
    try:
        return type_func(value)
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 500, suffix: str = '...') -> str:
    """
    Truncate text to a maximum length, adding suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, max_calls: int, time_window: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def __call__(self, func):
        """Decorator to apply rate limiting to a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()

            # Remove calls outside the time window
            self.calls = [call_time for call_time in self.calls
                         if now - call_time < self.time_window]

            if len(self.calls) >= self.max_calls:
                # Calculate time to wait
                oldest_call = min(self.calls)
                wait_time = self.time_window - (now - oldest_call)

                if wait_time > 0:
                    logger.warning(
                        f"Rate limit reached for {func.__name__}. "
                        f"Waiting {wait_time:.1f} seconds"
                    )
                    time.sleep(wait_time)
                    # Remove old calls again after waiting
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls
                                 if now - call_time < self.time_window]

            # Record this call
            self.calls.append(now)

            return func(*args, **kwargs)

        return wrapper

    def check_limit(self) -> bool:
        """
        Check if rate limit would be exceeded.

        Returns:
            True if call is allowed, False if rate limited
        """
        now = time.time()
        self.calls = [call_time for call_time in self.calls
                     if now - call_time < self.time_window]
        return len(self.calls) < self.max_calls


def create_error_response(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.

    Args:
        error: Exception that occurred
        context: Additional context information

    Returns:
        Error response dictionary
    """
    return {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
        'context': context or {}
    }


def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """
    Create a standardized success response dictionary.

    Args:
        data: Response data
        message: Success message

    Returns:
        Success response dictionary
    """
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return response
