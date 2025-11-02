"""Error classes for the Sendly Python SDK."""

from typing import Optional


class SendlyError(Exception):
    """Base exception for all Sendly errors."""
    
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationError(SendlyError):
    """Raised for validation errors in request parameters."""
    
    def __init__(self, message: str):
        super().__init__(message, code='validation_error')


class AuthenticationError(SendlyError):
    """Raised for authentication failures."""
    
    def __init__(self, message: str):
        super().__init__(message, code='authentication_error')


class RateLimitError(SendlyError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, code='rate_limit_exceeded')
        self.retry_after = retry_after


class APIError(SendlyError):
    """Raised for general API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message, code)
        self.status_code = status_code


class NetworkError(SendlyError):
    """Raised for network-related errors."""
    
    def __init__(self, message: str):
        super().__init__(message, code='network_error')