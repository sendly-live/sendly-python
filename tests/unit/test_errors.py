"""Tests for error hierarchy."""

import pytest

from sendly.errors import (
    SendlyError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NetworkError
)


class TestSendlyError:
    """Test cases for base SendlyError class."""
    
    def test_sendly_error_with_message_only(self):
        """Test SendlyError with message only."""
        error = SendlyError("Something went wrong")
        
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code is None
    
    def test_sendly_error_with_message_and_code(self):
        """Test SendlyError with message and code."""
        error = SendlyError("Something went wrong", code="custom_error")
        
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code == "custom_error"
    
    def test_sendly_error_inheritance(self):
        """Test that SendlyError inherits from Exception."""
        error = SendlyError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, SendlyError)


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid phone number format")
        
        assert str(error) == "Invalid phone number format"
        assert error.message == "Invalid phone number format"
        assert error.code == "validation_error"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inheritance."""
        error = ValidationError("Validation failed")
        
        assert isinstance(error, SendlyError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, Exception)
    
    def test_validation_error_can_be_raised_and_caught(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error")
        
        assert exc_info.value.message == "Test validation error"
        assert exc_info.value.code == "validation_error"
    
    def test_validation_error_caught_as_sendly_error(self):
        """Test that ValidationError can be caught as SendlyError."""
        with pytest.raises(SendlyError) as exc_info:
            raise ValidationError("Test validation error")
        
        assert isinstance(exc_info.value, ValidationError)
        assert exc_info.value.message == "Test validation error"


class TestAuthenticationError:
    """Test cases for AuthenticationError."""
    
    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        error = AuthenticationError("Invalid API key")
        
        assert str(error) == "Invalid API key"
        assert error.message == "Invalid API key"
        assert error.code == "authentication_error"
    
    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inheritance."""
        error = AuthenticationError("Auth failed")
        
        assert isinstance(error, SendlyError)
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)
    
    def test_authentication_error_can_be_raised_and_caught(self):
        """Test that AuthenticationError can be raised and caught."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Invalid credentials")
        
        assert exc_info.value.message == "Invalid credentials"
        assert exc_info.value.code == "authentication_error"
    
    def test_authentication_error_caught_as_sendly_error(self):
        """Test that AuthenticationError can be caught as SendlyError."""
        with pytest.raises(SendlyError) as exc_info:
            raise AuthenticationError("Invalid credentials")
        
        assert isinstance(exc_info.value, AuthenticationError)


class TestRateLimitError:
    """Test cases for RateLimitError."""
    
    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded")
        
        assert str(error) == "Rate limit exceeded"
        assert error.message == "Rate limit exceeded"
        assert error.code == "rate_limit_exceeded"
        assert error.retry_after is None
    
    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=30)
        
        assert str(error) == "Rate limit exceeded"
        assert error.message == "Rate limit exceeded"
        assert error.code == "rate_limit_exceeded"
        assert error.retry_after == 30
    
    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inheritance."""
        error = RateLimitError("Rate limit exceeded")
        
        assert isinstance(error, SendlyError)
        assert isinstance(error, RateLimitError)
        assert isinstance(error, Exception)
    
    def test_rate_limit_error_can_be_raised_and_caught(self):
        """Test that RateLimitError can be raised and caught."""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError("Too many requests", retry_after=60)
        
        assert exc_info.value.message == "Too many requests"
        assert exc_info.value.code == "rate_limit_exceeded"
        assert exc_info.value.retry_after == 60
    
    def test_rate_limit_error_caught_as_sendly_error(self):
        """Test that RateLimitError can be caught as SendlyError."""
        with pytest.raises(SendlyError) as exc_info:
            raise RateLimitError("Too many requests", retry_after=30)
        
        assert isinstance(exc_info.value, RateLimitError)
        assert exc_info.value.retry_after == 30


class TestAPIError:
    """Test cases for APIError."""
    
    def test_api_error_minimal(self):
        """Test APIError with minimal parameters."""
        error = APIError("Server error")
        
        assert str(error) == "Server error"
        assert error.message == "Server error"
        assert error.code is None
        assert error.status_code is None
    
    def test_api_error_with_status_code(self):
        """Test APIError with status code."""
        error = APIError("Server error", status_code=500)
        
        assert str(error) == "Server error"
        assert error.message == "Server error"
        assert error.code is None
        assert error.status_code == 500
    
    def test_api_error_with_code(self):
        """Test APIError with error code."""
        error = APIError("Server error", code="internal_server_error")
        
        assert str(error) == "Server error"
        assert error.message == "Server error"
        assert error.code == "internal_server_error"
        assert error.status_code is None
    
    def test_api_error_with_all_parameters(self):
        """Test APIError with all parameters."""
        error = APIError("Server error", status_code=500, code="internal_server_error")
        
        assert str(error) == "Server error"
        assert error.message == "Server error"
        assert error.code == "internal_server_error"
        assert error.status_code == 500
    
    def test_api_error_inheritance(self):
        """Test APIError inheritance."""
        error = APIError("Server error")
        
        assert isinstance(error, SendlyError)
        assert isinstance(error, APIError)
        assert isinstance(error, Exception)
    
    def test_api_error_can_be_raised_and_caught(self):
        """Test that APIError can be raised and caught."""
        with pytest.raises(APIError) as exc_info:
            raise APIError("Bad request", status_code=400, code="bad_request")
        
        assert exc_info.value.message == "Bad request"
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "bad_request"
    
    def test_api_error_caught_as_sendly_error(self):
        """Test that APIError can be caught as SendlyError."""
        with pytest.raises(SendlyError) as exc_info:
            raise APIError("Bad request", status_code=400)
        
        assert isinstance(exc_info.value, APIError)
        assert exc_info.value.status_code == 400


class TestNetworkError:
    """Test cases for NetworkError."""
    
    def test_network_error_creation(self):
        """Test NetworkError creation."""
        error = NetworkError("Connection timeout")
        
        assert str(error) == "Connection timeout"
        assert error.message == "Connection timeout"
        assert error.code == "network_error"
    
    def test_network_error_inheritance(self):
        """Test NetworkError inheritance."""
        error = NetworkError("Network failed")
        
        assert isinstance(error, SendlyError)
        assert isinstance(error, NetworkError)
        assert isinstance(error, Exception)
    
    def test_network_error_can_be_raised_and_caught(self):
        """Test that NetworkError can be raised and caught."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError("DNS resolution failed")
        
        assert exc_info.value.message == "DNS resolution failed"
        assert exc_info.value.code == "network_error"
    
    def test_network_error_caught_as_sendly_error(self):
        """Test that NetworkError can be caught as SendlyError."""
        with pytest.raises(SendlyError) as exc_info:
            raise NetworkError("Connection refused")
        
        assert isinstance(exc_info.value, NetworkError)


class TestErrorHierarchy:
    """Test cases for error hierarchy behavior."""
    
    def test_all_errors_inherit_from_sendly_error(self):
        """Test that all specific errors inherit from SendlyError."""
        validation_error = ValidationError("Validation failed")
        auth_error = AuthenticationError("Auth failed")
        rate_limit_error = RateLimitError("Rate limit exceeded")
        api_error = APIError("API failed")
        network_error = NetworkError("Network failed")
        
        assert isinstance(validation_error, SendlyError)
        assert isinstance(auth_error, SendlyError)
        assert isinstance(rate_limit_error, SendlyError)
        assert isinstance(api_error, SendlyError)
        assert isinstance(network_error, SendlyError)
    
    def test_can_catch_all_errors_as_sendly_error(self):
        """Test that all errors can be caught as SendlyError."""
        errors = [
            ValidationError("Validation failed"),
            AuthenticationError("Auth failed"),
            RateLimitError("Rate limit exceeded"),
            APIError("API failed"),
            NetworkError("Network failed"),
        ]
        
        for error in errors:
            try:
                raise error
            except SendlyError as e:
                assert isinstance(e, SendlyError)
                assert e.message is not None
                assert hasattr(e, 'code')
    
    def test_error_codes_are_set_correctly(self):
        """Test that error codes are set correctly for each error type."""
        validation_error = ValidationError("Validation failed")
        auth_error = AuthenticationError("Auth failed")
        rate_limit_error = RateLimitError("Rate limit exceeded")
        network_error = NetworkError("Network failed")
        
        assert validation_error.code == "validation_error"
        assert auth_error.code == "authentication_error"
        assert rate_limit_error.code == "rate_limit_exceeded"
        assert network_error.code == "network_error"
    
    def test_error_specific_attributes(self):
        """Test error-specific attributes."""
        # RateLimitError has retry_after
        rate_error = RateLimitError("Too many requests", retry_after=30)
        assert hasattr(rate_error, 'retry_after')
        assert rate_error.retry_after == 30
        
        # APIError has status_code
        api_error = APIError("Server error", status_code=500)
        assert hasattr(api_error, 'status_code')
        assert api_error.status_code == 500
        
        # Other errors don't have these attributes
        validation_error = ValidationError("Validation failed")
        assert not hasattr(validation_error, 'retry_after')
        assert not hasattr(validation_error, 'status_code')
    
    def test_error_messages_preserved(self):
        """Test that error messages are preserved through inheritance."""
        base_error = SendlyError("Base error")
        validation_error = ValidationError("Validation error")
        
        assert str(base_error) == "Base error"
        assert str(validation_error) == "Validation error"
        assert base_error.message == "Base error"
        assert validation_error.message == "Validation error"