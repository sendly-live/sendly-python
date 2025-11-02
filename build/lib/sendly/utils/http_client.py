"""HTTP client with retry logic for the Sendly Python SDK."""

import time
from typing import Any, Dict, Optional, TypeVar
from urllib.parse import urlencode

import requests

from ..errors import APIError, NetworkError, RateLimitError

T = TypeVar('T')


class HttpClient:
    """HTTP client with exponential backoff retry logic."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "sendly-python/0.1.0"
    ):
        """Initialize HTTP client.
        
        Args:
            base_url: Base URL for API requests
            api_key: Sendly API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: User agent string
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = 1.0  # Base delay for exponential backoff
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
        })
    
    def post(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """Make a POST request.
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Request data to send as JSON
            
        Returns:
            Response data as dictionary
            
        Raises:
            ValidationError: For 400 status codes
            AuthenticationError: For 401 status codes
            RateLimitError: For 429 status codes
            APIError: For other HTTP errors
            NetworkError: For network-related errors
        """
        return self._make_request('POST', endpoint, json=data)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            ValidationError: For 400 status codes
            AuthenticationError: For 401 status codes
            RateLimitError: For 429 status codes
            APIError: For other HTTP errors
            NetworkError: For network-related errors
        """
        return self._make_request('GET', endpoint, params=params)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            json: JSON data for request body
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            Various Sendly exceptions based on error type
        """
        url = f"{self.base_url}{endpoint}"
        
        # Build query string for array parameters
        if params:
            params = self._serialize_params(params)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    timeout=self.timeout
                )
                
                # Handle successful response
                if response.ok:
                    try:
                        return response.json()
                    except ValueError as e:
                        raise APIError(f"Invalid JSON in response: {e}")
                
                # Handle error responses
                self._handle_error_response(response, attempt)
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    continue
                raise NetworkError("Request timed out")
            
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    continue
                raise NetworkError("Connection error")
            
            except requests.exceptions.RequestException as e:
                raise NetworkError(f"Request failed: {e}")
        
        # This should never be reached
        raise RateLimitError("Max retry attempts exceeded")
    
    def _handle_error_response(self, response: requests.Response, attempt: int) -> None:
        """Handle error responses with retry logic.
        
        Args:
            response: HTTP response object
            attempt: Current attempt number
            
        Raises:
            Various Sendly exceptions based on error type
        """
        try:
            error_data = response.json()
        except ValueError:
            error_data = {
                'error': 'unknown',
                'message': response.text or response.reason
            }
        
        # Check if this is a retryable error
        if self._is_retryable_error(response.status_code) and attempt < self.max_retries:
            delay = self._calculate_delay(attempt, error_data.get('retry_after'))
            time.sleep(delay)
            return
        
        # Import here to avoid circular imports
        from ..errors import AuthenticationError, ValidationError
        
        # Handle specific error types
        if response.status_code == 400:
            raise ValidationError(error_data.get('message', 'Validation error'))
        elif response.status_code == 401:
            raise AuthenticationError(error_data.get('message', 'Authentication failed'))
        elif response.status_code == 429:
            raise RateLimitError(
                error_data.get('message', 'Rate limit exceeded'),
                retry_after=error_data.get('retry_after')
            )
        else:
            raise APIError(
                error_data.get('message', f'HTTP {response.status_code}: {response.reason}'),
                status_code=response.status_code,
                code=error_data.get('error')
            )
    
    def _is_retryable_error(self, status_code: int) -> bool:
        """Check if error is retryable.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if error should be retried
        """
        # Retry on rate limits (429) and server errors (5xx)
        return status_code == 429 or (500 <= status_code < 600)
    
    def _calculate_delay(self, attempt: int, retry_after: Optional[int] = None) -> float:
        """Calculate delay for exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            retry_after: Server-specified retry delay in seconds
            
        Returns:
            Delay in seconds
        """
        if retry_after:
            return float(retry_after)
        
        # Exponential backoff: 1s, 2s, 4s
        return self.base_delay * (2 ** attempt)
    
    def _serialize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize parameters, handling arrays properly.
        
        Args:
            params: Parameters to serialize
            
        Returns:
            Serialized parameters
        """
        serialized = {}
        
        for key, value in params.items():
            if value is None:
                continue
            elif isinstance(value, list):
                # Handle array parameters (e.g., tags)
                serialized[key] = value
            else:
                serialized[key] = str(value)
        
        return serialized
    
    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()