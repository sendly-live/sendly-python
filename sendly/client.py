"""Main Sendly client for the Python SDK."""

import os
from typing import Optional

from .errors import ValidationError
from .resources.sms import SMS
from .utils.http_client import HttpClient
from .utils.validation import is_valid_api_key


class Sendly:
    """Main Sendly client for sending SMS/MMS messages."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://sendly.live/api",
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: Optional[str] = None
    ):
        """Initialize Sendly client.
        
        Args:
            api_key: Sendly API key (sl_live_* or sl_test_*). 
                    If not provided, will try SENDLY_API_KEY environment variable.
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: Custom user agent string
            
        Raises:
            ValidationError: If API key is missing or invalid
        """
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv('SENDLY_API_KEY')
        
        if not api_key:
            raise ValidationError(
                'API key is required. Provide it as a parameter or set SENDLY_API_KEY environment variable.'
            )
        
        # Validate API key format
        if not is_valid_api_key(api_key):
            raise ValidationError(
                'Invalid API key format. Expected: sl_test_*** or sl_live_***'
            )
        
        # Initialize HTTP client
        self._http_client = HttpClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            user_agent=user_agent or "sendly-python/0.1.0"
        )
        
        # Initialize resources
        self.sms = SMS(self._http_client)
    
    def close(self) -> None:
        """Close the HTTP client session."""
        self._http_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()