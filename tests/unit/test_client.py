"""Tests for the Sendly client."""

import os
import pytest
from unittest.mock import patch

from sendly import Sendly
from sendly.errors import ValidationError
from sendly.resources.sms import SMS


class TestSendlyClient:
    """Test cases for the Sendly client."""
    
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key parameter."""
        client = Sendly('sl_test_1234567890123456789012345678901234567890')
        
        assert client.sms is not None
        assert isinstance(client.sms, SMS)
    
    def test_client_initialization_with_env_var(self):
        """Test client initialization with environment variable."""
        with patch.dict(os.environ, {'SENDLY_API_KEY': 'sl_test_1234567890123456789012345678901234567890'}):
            client = Sendly()
            
            assert client.sms is not None
            assert isinstance(client.sms, SMS)
    
    def test_client_initialization_missing_api_key(self):
        """Test client initialization fails with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError, match='API key is required'):
                Sendly()
    
    def test_client_initialization_invalid_api_key_format(self):
        """Test client initialization fails with invalid API key format."""
        with pytest.raises(ValidationError, match='Invalid API key format'):
            Sendly('invalid-api-key')
    
    def test_client_initialization_with_custom_config(self):
        """Test client initialization with custom configuration."""
        client = Sendly(
            api_key='sl_test_1234567890123456789012345678901234567890',
            base_url='https://api.example.com',
            timeout=60.0,
            max_retries=5
        )
        
        assert client.sms is not None
        assert client._http_client.base_url == 'https://api.example.com'
        assert client._http_client.timeout == 60.0
        assert client._http_client.max_retries == 5
    
    def test_valid_api_key_formats(self):
        """Test various valid API key formats."""
        valid_keys = [
            'sl_test_1234567890123456789012345678901234567890',
            'sl_live_abcdefghijklmnopqrstuvwxyz1234567890abcd',
            'sl_test_ABC123_def456_GHI789',
            'sl_live_short123456789012345678'
        ]
        
        for key in valid_keys:
            client = Sendly(key)
            assert client.sms is not None
    
    def test_invalid_api_key_formats(self):
        """Test various invalid API key formats."""
        invalid_keys = [
            'invalid-key',
            'sl_invalid_1234567890123456789012345678901234567890',
            'sl_test_short',
            'sl_live_',
            'test_1234567890123456789012345678901234567890',
            ''
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValidationError):
                Sendly(key)
    
    def test_context_manager(self):
        """Test client as context manager."""
        with Sendly('sl_test_1234567890123456789012345678901234567890') as client:
            assert client.sms is not None
        
        # Client should be closed after context exit
        # Note: We can't easily test if session is closed without exposing internals
    
    def test_manual_close(self):
        """Test manual client closure."""
        client = Sendly('sl_test_1234567890123456789012345678901234567890')
        client.close()
        
        # Client should be closed
        # Note: We can't easily test if session is closed without exposing internals