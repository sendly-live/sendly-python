"""Tests for validation utilities."""

import pytest

from sendly.errors import ValidationError
from sendly.types import SMSRequest
from sendly.utils.validation import (
    is_valid_phone_number,
    is_valid_api_key,
    is_valid_url,
    get_country_code,
    is_toll_free,
    validate_toll_free_routing,
    validate_sms_request,
)


class TestPhoneNumberValidation:
    """Test phone number validation."""
    
    def test_valid_phone_numbers(self):
        """Test various valid phone numbers."""
        valid_numbers = [
            '+14155552671',
            '+447700900123',
            '+33123456789',
            '+8613800138000',
            '+12345678901234',  # Maximum length (15 digits)
            '+1234567890',      # Minimum realistic length
        ]
        
        for number in valid_numbers:
            assert is_valid_phone_number(number), f"Should be valid: {number}"
    
    def test_invalid_phone_numbers(self):
        """Test various invalid phone numbers."""
        invalid_numbers = [
            '14155552671',      # Missing +
            '+014155552671',    # Starts with 0
            '+1415555267',      # Too short
            '+123456789012345', # Too long (16 digits)
            '+1-415-555-2671',  # Contains dashes
            '+1 415 555 2671',  # Contains spaces
            '+1(415)555-2671',  # Contains parentheses
            'invalid',          # Not a number
            '',                 # Empty string
            '+',                # Just plus sign
        ]
        
        for number in invalid_numbers:
            assert not is_valid_phone_number(number), f"Should be invalid: {number}"


class TestAPIKeyValidation:
    """Test API key validation."""
    
    def test_valid_api_keys(self):
        """Test various valid API key formats."""
        valid_keys = [
            'sl_test_1234567890123456789012345678901234567890',
            'sl_live_abcdefghijklmnopqrstuvwxyz1234567890abcd',
            'sl_test_ABC123_def456_GHI789',
            'sl_live_short123456789012345678',
        ]
        
        for key in valid_keys:
            assert is_valid_api_key(key), f"Should be valid: {key}"
    
    def test_invalid_api_keys(self):
        """Test various invalid API key formats."""
        invalid_keys = [
            'invalid-key',
            'sl_invalid_1234567890123456789012345678901234567890',
            'sl_test_short',
            'sl_live_',
            'test_1234567890123456789012345678901234567890',
            '',
            'sl_test',
            'sl_live',
        ]
        
        for key in invalid_keys:
            assert not is_valid_api_key(key), f"Should be invalid: {key}"


class TestURLValidation:
    """Test URL validation."""
    
    def test_valid_urls(self):
        """Test various valid URLs."""
        valid_urls = [
            'https://example.com',
            'http://example.com',
            'https://subdomain.example.com/path',
            'https://example.com:8080/webhook',
            'https://example.com/webhook?param=value',
        ]
        
        for url in valid_urls:
            assert is_valid_url(url), f"Should be valid: {url}"
    
    def test_invalid_urls(self):
        """Test various invalid URLs."""
        invalid_urls = [
            'not-a-url',
            'example.com',
            'ftp://example.com',
            '',
            'https://',
            '://example.com',
        ]
        
        for url in invalid_urls:
            assert not is_valid_url(url), f"Should be invalid: {url}"


class TestCountryCodeDetection:
    """Test country code detection."""
    
    def test_country_code_detection(self):
        """Test country code extraction from phone numbers."""
        test_cases = [
            ('+14155552671', '1'),      # US
            ('+1234567890', '1'),       # US/Canada
            ('+447700900123', '44'),    # UK
            ('+33123456789', '33'),     # France
            ('+8613800138000', '86'),   # China
            ('+27123456789', '27'),     # South Africa
            ('+81123456789', '81'),     # Japan
            ('+99123456789', 'unknown'), # Unknown country
        ]
        
        for phone, expected_code in test_cases:
            actual_code = get_country_code(phone)
            assert actual_code == expected_code, f"Phone {phone} should have country code {expected_code}, got {actual_code}"


class TestTollFreeDetection:
    """Test toll-free number detection."""
    
    def test_toll_free_numbers(self):
        """Test toll-free number detection."""
        toll_free_numbers = [
            '+18005551234',
            '+18335551234',
            '+18445551234',
            '+18555551234',
            '+18665551234',
            '+18775551234',
            '+18885551234',
        ]
        
        for number in toll_free_numbers:
            assert is_toll_free(number), f"Should be toll-free: {number}"
    
    def test_non_toll_free_numbers(self):
        """Test non-toll-free number detection."""
        non_toll_free_numbers = [
            '+14155551234',  # Regular US number
            '+447700900123', # UK number
            '+18125551234',  # Non-toll-free US number
        ]
        
        for number in non_toll_free_numbers:
            assert not is_toll_free(number), f"Should not be toll-free: {number}"


class TestTollFreeRouting:
    """Test toll-free routing validation."""
    
    def test_valid_toll_free_routing(self):
        """Test valid toll-free routing (US to US/Canada)."""
        # Should not raise exception
        validate_toll_free_routing('+18005551234', '+14155552671')  # US to US
        validate_toll_free_routing('+18005551234', '+12345678901')  # US to Canada
    
    def test_invalid_toll_free_routing(self):
        """Test invalid toll-free routing (toll-free to international)."""
        with pytest.raises(ValidationError, match='Toll-free number .* cannot send to international destination'):
            validate_toll_free_routing('+18005551234', '+447700900123')  # US toll-free to UK
        
        with pytest.raises(ValidationError, match='Toll-free number .* cannot send to international destination'):
            validate_toll_free_routing('+18005551234', '+8613800138000')  # US toll-free to China
    
    def test_non_toll_free_routing(self):
        """Test that non-toll-free numbers can send internationally."""
        # Should not raise exception
        validate_toll_free_routing('+14155552671', '+447700900123')  # US regular to UK
        validate_toll_free_routing('+14155552671', '+8613800138000')  # US regular to China


class TestSMSRequestValidation:
    """Test SMS request validation."""
    
    def test_valid_sms_request(self):
        """Test valid SMS request validation."""
        request = SMSRequest(
            to='+14155552671',
            text='Hello world'
        )
        
        # Should not raise exception
        validate_sms_request(request)
    
    def test_missing_to_field(self):
        """Test validation fails for missing 'to' field."""
        request = SMSRequest(to='', text='Hello world')
        
        with pytest.raises(ValidationError, match='to is required'):
            validate_sms_request(request)
    
    def test_missing_content(self):
        """Test validation fails for missing content."""
        request = SMSRequest(to='+14155552671')
        
        with pytest.raises(ValidationError, match='Either text or media_urls must be provided'):
            validate_sms_request(request)
    
    def test_invalid_phone_numbers(self):
        """Test validation fails for invalid phone numbers."""
        # Invalid 'to' number
        request = SMSRequest(to='invalid', text='Hello')
        with pytest.raises(ValidationError, match='Invalid phone number format for to'):
            validate_sms_request(request)
        
        # Invalid 'from_' number
        request = SMSRequest(to='+14155552671', from_='invalid', text='Hello')
        with pytest.raises(ValidationError, match='Invalid phone number format for from_'):
            validate_sms_request(request)
    
    def test_media_url_validation(self):
        """Test media URL validation."""
        # Too many media URLs
        request = SMSRequest(
            to='+14155552671',
            media_urls=['https://example.com'] * 11
        )
        with pytest.raises(ValidationError, match='Maximum 10 media URLs allowed'):
            validate_sms_request(request)
        
        # Invalid URL format
        request = SMSRequest(
            to='+14155552671',
            media_urls=['invalid-url']
        )
        with pytest.raises(ValidationError, match='Invalid URL format in media_urls'):
            validate_sms_request(request)
        
        # HTTP instead of HTTPS
        request = SMSRequest(
            to='+14155552671',
            media_urls=['http://example.com/image.jpg']
        )
        with pytest.raises(ValidationError, match='Media URLs must use HTTPS'):
            validate_sms_request(request)
    
    def test_webhook_url_validation(self):
        """Test webhook URL validation."""
        # Invalid webhook URL
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            webhook_url='invalid-url'
        )
        with pytest.raises(ValidationError, match='Invalid webhook URL format'):
            validate_sms_request(request)
        
        # HTTP instead of HTTPS
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            webhook_url='http://example.com/webhook'
        )
        with pytest.raises(ValidationError, match='Webhook URL must use HTTPS'):
            validate_sms_request(request)
        
        # Invalid failover URL
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            webhook_failover_url='http://example.com/webhook'
        )
        with pytest.raises(ValidationError, match='Webhook failover URL must use HTTPS'):
            validate_sms_request(request)
    
    def test_tag_validation(self):
        """Test tag validation."""
        # Too many tags
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            tags=['tag'] * 21
        )
        with pytest.raises(ValidationError, match='Maximum 20 tags allowed'):
            validate_sms_request(request)
        
        # Empty tag
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            tags=['valid-tag', '']
        )
        with pytest.raises(ValidationError, match='Tags cannot be empty'):
            validate_sms_request(request)
        
        # Tag too long
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            tags=['x' * 51]
        )
        with pytest.raises(ValidationError, match='Tag length cannot exceed 50 characters'):
            validate_sms_request(request)
    
    def test_message_type_validation(self):
        """Test message type validation."""
        # Valid message types
        valid_types = ['transactional', 'marketing', 'otp', 'alert', 'promotional']
        for msg_type in valid_types:
            request = SMSRequest(
                to='+14155552671',
                text='Hello',
                message_type=msg_type
            )
            validate_sms_request(request)  # Should not raise
        
        # Invalid message type
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            message_type='invalid'
        )
        with pytest.raises(ValidationError, match='Invalid message_type'):
            validate_sms_request(request)