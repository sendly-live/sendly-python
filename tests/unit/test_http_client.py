"""Tests for HTTP client with retry logic."""

import json
import time
from unittest.mock import Mock, patch, call
import pytest
import requests

from sendly.utils.http_client import HttpClient
from sendly.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ValidationError
)


class TestHttpClient:
    """Test cases for HTTP client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = 'sl_test_1234567890123456789012345678901234567890'
        self.base_url = 'https://api.sendly.example.com'
        self.client = HttpClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=30.0,
            max_retries=3
        )
    
    def test_client_initialization(self):
        """Test HTTP client initialization."""
        client = HttpClient(
            base_url='https://api.example.com/',  # With trailing slash
            api_key='test-key',
            timeout=60.0,
            max_retries=5,
            user_agent='custom-agent/1.0'
        )
        
        assert client.base_url == 'https://api.example.com'  # Trailing slash removed
        assert client.api_key == 'test-key'
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.base_delay == 1.0
        
        # Check session headers
        assert client.session.headers['Authorization'] == 'Bearer test-key'
        assert client.session.headers['Content-Type'] == 'application/json'
        assert client.session.headers['User-Agent'] == 'custom-agent/1.0'
    
    def test_client_default_initialization(self):
        """Test HTTP client with default parameters."""
        client = HttpClient(
            base_url='https://api.example.com',
            api_key='test-key'
        )
        
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.session.headers['User-Agent'] == 'sendly-python/0.1.0'
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_successful_post_request(self, mock_session_class):
        """Test successful POST request."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'status': 'success', 'id': '123'}
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Create client (will use mocked session)
        client = HttpClient(self.base_url, self.api_key)
        
        # Make request
        result = client.post('/v1/send', {'to': '+14155552671', 'text': 'Hello'})
        
        # Verify request was made correctly
        mock_session.request.assert_called_once_with(
            method='POST',
            url='https://api.sendly.example.com/v1/send',
            json={'to': '+14155552671', 'text': 'Hello'},
            params=None,
            timeout=30.0
        )
        
        # Verify response
        assert result == {'status': 'success', 'id': '123'}
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_successful_get_request(self, mock_session_class):
        """Test successful GET request."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'data': 'test'}
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Create client
        client = HttpClient(self.base_url, self.api_key)
        
        # Make request
        result = client.get('/v1/status', {'filter': 'active'})
        
        # Verify request was made correctly
        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.sendly.example.com/v1/status',
            json=None,
            params={'filter': 'active'},
            timeout=30.0
        )
        
        # Verify response
        assert result == {'data': 'test'}
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_invalid_json_response(self, mock_session_class):
        """Test handling of invalid JSON response."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError('Invalid JSON')
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key)
        
        with pytest.raises(APIError, match='Invalid JSON in response'):
            client.post('/v1/send', {})
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_validation_error_400(self, mock_session_class):
        """Test 400 validation error handling."""
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'validation_error',
            'message': 'Invalid phone number format'
        }
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key)
        
        with pytest.raises(ValidationError, match='Invalid phone number format'):
            client.post('/v1/send', {})
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_authentication_error_401(self, mock_session_class):
        """Test 401 authentication error handling."""
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': 'authentication_error',
            'message': 'Invalid API key'
        }
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key)
        
        with pytest.raises(AuthenticationError, match='Invalid API key'):
            client.post('/v1/send', {})
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_rate_limit_error_429_retry(self, mock_sleep, mock_session_class):
        """Test 429 rate limit error with retry."""
        # Mock rate limit response followed by success
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'Rate limit exceeded',
            'retry_after': 2
        }
        
        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = {'status': 'success'}
        
        mock_session = Mock()
        mock_session.request.side_effect = [rate_limit_response, success_response]
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=1)
        
        # Should succeed after retry
        result = client.post('/v1/send', {})
        
        # Verify retry delay used server-provided value
        mock_sleep.assert_called_once_with(2.0)
        
        # Verify two requests were made
        assert mock_session.request.call_count == 2
        
        # Verify final result
        assert result == {'status': 'success'}
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_rate_limit_error_429_max_retries(self, mock_sleep, mock_session_class):
        """Test 429 rate limit error exceeding max retries."""
        # Mock rate limit response
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'Rate limit exceeded'
        }
        
        mock_session = Mock()
        mock_session.request.return_value = rate_limit_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=2)
        
        with pytest.raises(RateLimitError, match='Rate limit exceeded'):
            client.post('/v1/send', {})
        
        # Verify all retries were attempted
        assert mock_session.request.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_server_error_500_retry(self, mock_sleep, mock_session_class):
        """Test 500 server error with retry."""
        # Mock server error response followed by success
        server_error_response = Mock()
        server_error_response.ok = False
        server_error_response.status_code = 500
        server_error_response.json.return_value = {
            'error': 'internal_server_error',
            'message': 'Internal server error'
        }
        
        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = {'status': 'success'}
        
        mock_session = Mock()
        mock_session.request.side_effect = [server_error_response, success_response]
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=1)
        
        # Should succeed after retry
        result = client.post('/v1/send', {})
        
        # Verify exponential backoff delay
        mock_sleep.assert_called_once_with(1.0)  # 2^0 * 1.0
        
        # Verify result
        assert result == {'status': 'success'}
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_api_error_non_retryable(self, mock_session_class):
        """Test non-retryable API error."""
        # Mock 404 error response
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 404
        error_response.json.return_value = {
            'error': 'not_found',
            'message': 'Resource not found'
        }
        
        mock_session = Mock()
        mock_session.request.return_value = error_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key)
        
        with pytest.raises(APIError) as exc_info:
            client.post('/v1/send', {})
        
        # Verify error details
        assert exc_info.value.message == 'Resource not found'
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == 'not_found'
        
        # Verify no retries for non-retryable error
        assert mock_session.request.call_count == 1
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_api_error_invalid_json_response(self, mock_session_class):
        """Test API error with invalid JSON response."""
        # Mock error response with invalid JSON
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 500
        error_response.json.side_effect = ValueError('Invalid JSON')
        error_response.text = 'Internal Server Error'
        error_response.reason = 'Internal Server Error'
        
        mock_session = Mock()
        mock_session.request.return_value = error_response
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=0)  # No retries
        
        with pytest.raises(APIError) as exc_info:
            client.post('/v1/send', {})
        
        # Should use fallback error message
        assert 'Internal Server Error' in exc_info.value.message
        assert exc_info.value.status_code == 500
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_timeout_error_retry(self, mock_sleep, mock_session_class):
        """Test timeout error with retry."""
        mock_session = Mock()
        mock_session.request.side_effect = [
            requests.exceptions.Timeout(),
            Mock(ok=True, json=lambda: {'status': 'success'})
        ]
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=1)
        
        # Should succeed after retry
        result = client.post('/v1/send', {})
        
        # Verify retry with exponential backoff
        mock_sleep.assert_called_once_with(1.0)
        assert result == {'status': 'success'}
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_timeout_error_max_retries(self, mock_sleep, mock_session_class):
        """Test timeout error exceeding max retries."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.Timeout()
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=2)
        
        with pytest.raises(NetworkError, match='Request timed out'):
            client.post('/v1/send', {})
        
        # Verify all retries were attempted
        assert mock_session.request.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_connection_error_retry(self, mock_sleep, mock_session_class):
        """Test connection error with retry."""
        mock_session = Mock()
        mock_session.request.side_effect = [
            requests.exceptions.ConnectionError(),
            Mock(ok=True, json=lambda: {'status': 'success'})
        ]
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=1)
        
        # Should succeed after retry
        result = client.post('/v1/send', {})
        
        # Verify retry
        mock_sleep.assert_called_once_with(1.0)
        assert result == {'status': 'success'}
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_connection_error_max_retries(self, mock_session_class):
        """Test connection error exceeding max retries."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.ConnectionError()
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=1)
        
        with pytest.raises(NetworkError, match='Connection error'):
            client.post('/v1/send', {})
    
    @patch('sendly.utils.http_client.requests.Session')
    def test_generic_request_exception(self, mock_session_class):
        """Test generic request exception."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.RequestException('Network failure')
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key)
        
        with pytest.raises(NetworkError, match='Request failed: Network failure'):
            client.post('/v1/send', {})
    
    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        client = HttpClient(self.base_url, self.api_key)
        
        # Test exponential backoff: 1s, 2s, 4s
        assert client._calculate_delay(0) == 1.0
        assert client._calculate_delay(1) == 2.0
        assert client._calculate_delay(2) == 4.0
        assert client._calculate_delay(3) == 8.0
    
    def test_calculate_delay_with_retry_after(self):
        """Test delay calculation with server-provided retry_after."""
        client = HttpClient(self.base_url, self.api_key)
        
        # Should use server-provided value
        assert client._calculate_delay(0, retry_after=5) == 5.0
        assert client._calculate_delay(2, retry_after=10) == 10.0
    
    def test_is_retryable_error(self):
        """Test retryable error detection."""
        client = HttpClient(self.base_url, self.api_key)
        
        # Retryable errors
        assert client._is_retryable_error(429) is True  # Rate limit
        assert client._is_retryable_error(500) is True  # Server error
        assert client._is_retryable_error(502) is True  # Bad gateway
        assert client._is_retryable_error(503) is True  # Service unavailable
        assert client._is_retryable_error(504) is True  # Gateway timeout
        
        # Non-retryable errors
        assert client._is_retryable_error(400) is False  # Bad request
        assert client._is_retryable_error(401) is False  # Unauthorized
        assert client._is_retryable_error(403) is False  # Forbidden
        assert client._is_retryable_error(404) is False  # Not found
    
    def test_serialize_params_basic(self):
        """Test basic parameter serialization."""
        client = HttpClient(self.base_url, self.api_key)
        
        params = {
            'string_param': 'value',
            'int_param': 123,
            'bool_param': True,
            'none_param': None
        }
        
        result = client._serialize_params(params)
        
        expected = {
            'string_param': 'value',
            'int_param': '123',
            'bool_param': 'True'
            # none_param should be excluded
        }
        assert result == expected
    
    def test_serialize_params_arrays(self):
        """Test array parameter serialization."""
        client = HttpClient(self.base_url, self.api_key)
        
        params = {
            'tags': ['tag1', 'tag2', 'tag3'],
            'numbers': [1, 2, 3],
            'empty_array': [],
            'single_item': ['item']
        }
        
        result = client._serialize_params(params)
        
        expected = {
            'tags': ['tag1', 'tag2', 'tag3'],
            'numbers': [1, 2, 3],
            'empty_array': [],
            'single_item': ['item']
        }
        assert result == expected
    
    def test_context_manager(self):
        """Test HTTP client as context manager."""
        with patch('sendly.utils.http_client.requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            with HttpClient(self.base_url, self.api_key) as client:
                assert client is not None
            
            # Session should be closed after context exit
            mock_session.close.assert_called_once()
    
    def test_manual_close(self):
        """Test manual client closure."""
        with patch('sendly.utils.http_client.requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            client = HttpClient(self.base_url, self.api_key)
            client.close()
            
            # Session should be closed
            mock_session.close.assert_called_once()
    
    @patch('sendly.utils.http_client.requests.Session')
    @patch('sendly.utils.http_client.time.sleep')
    def test_exponential_backoff_sequence(self, mock_sleep, mock_session_class):
        """Test the full exponential backoff sequence."""
        # Mock multiple failures followed by success
        mock_session = Mock()
        mock_session.request.side_effect = [
            requests.exceptions.Timeout(),  # Attempt 0
            requests.exceptions.Timeout(),  # Attempt 1 
            requests.exceptions.Timeout(),  # Attempt 2
            Mock(ok=True, json=lambda: {'status': 'success'})  # Attempt 3
        ]
        mock_session_class.return_value = mock_session
        
        client = HttpClient(self.base_url, self.api_key, max_retries=3)
        
        result = client.post('/v1/send', {})
        
        # Verify exponential backoff delays: 1s, 2s, 4s
        expected_delays = [call(1.0), call(2.0), call(4.0)]
        mock_sleep.assert_has_calls(expected_delays)
        
        # Verify success after retries
        assert result == {'status': 'success'}
        assert mock_session.request.call_count == 4