"""Tests for SMS resource."""

import pytest
from unittest.mock import Mock, patch

from sendly.resources.sms import SMS
from sendly.types import SMSResponse, CostInfo, RoutingInfo
from sendly.errors import ValidationError, APIError, AuthenticationError, RateLimitError
from sendly.utils.http_client import HttpClient


class TestSMS:
    """Test cases for SMS resource."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_http_client = Mock(spec=HttpClient)
        self.sms = SMS(self.mock_http_client)
    
    def test_send_basic_sms(self):
        """Test sending a basic SMS message."""
        # Mock API response
        mock_response = {
            'messageId': 'msg_123456789',
            'status': 'queued',
            'from': '+18005551234',
            'to': '+14155552671',
            'text': 'Hello world',
            'created_at': '2023-10-01T12:00:00Z',
            'segments': 1,
            'direction': 'outbound',
            'routing': {
                'numberType': 'toll-free',
                'rateLimit': 10,
                'coverage': 'high',
                'reason': 'smart-routing',
                'countryCode': '1'
            },
            'cost': {
                'amount': 0.0075,
                'currency': 'USD'
            }
        }
        self.mock_http_client.post.return_value = mock_response
        
        # Send SMS
        response = self.sms.send(
            to='+14155552671',
            text='Hello world'
        )
        
        # Verify HTTP client was called correctly
        self.mock_http_client.post.assert_called_once_with('/v1/send', {
            'to': '+14155552671',
            'text': 'Hello world'
        })
        
        # Verify response structure
        assert isinstance(response, SMSResponse)
        assert response.id == 'msg_123456789'
        assert response.status == 'queued'
        assert response.from_ == '+18005551234'
        assert response.to == '+14155552671'
        assert response.text == 'Hello world'
        assert response.segments == 1
        
        # Verify routing info
        assert response.routing.number_type == 'toll-free'
        assert response.routing.rate_limit == 10
        assert response.routing.coverage == 'high'
        
        # Verify cost info
        assert response.cost.amount == 0.0075
        assert response.cost.currency == 'USD'
    
    def test_send_mms_with_all_parameters(self):
        """Test sending MMS with all optional parameters."""
        mock_response = {
            'messageId': 'msg_987654321',
            'status': 'queued',
            'from': '+14155551234',
            'to': '+447700900123',
            'text': 'Check out this image!',
            'created_at': '2023-10-01T12:00:00Z',
            'segments': 1,
            'direction': 'outbound',
            'messageType': 'marketing',
            'mediaType': 'image/jpeg',
            'media_urls': ['https://example.com/image.jpg'],
            'subject': 'Cool Image',
            'webhook_url': 'https://example.com/webhook',
            'webhook_failover_url': 'https://example.com/webhook-backup',
            'tags': ['campaign-a', 'promo'],
            'routing': {
                'numberType': 'local',
                'rateLimit': 5,
                'coverage': 'medium',
                'reason': 'local-routing',
                'countryCode': '44'
            }
        }
        self.mock_http_client.post.return_value = mock_response
        
        # Send MMS
        response = self.sms.send(
            to='+447700900123',
            text='Check out this image!',
            from_='+14155551234',
            message_type='marketing',
            media_urls=['https://example.com/image.jpg'],
            subject='Cool Image',
            webhook_url='https://example.com/webhook',
            webhook_failover_url='https://example.com/webhook-backup',
            tags=['campaign-a', 'promo']
        )
        
        # Verify HTTP client was called with all parameters
        expected_payload = {
            'to': '+447700900123',
            'text': 'Check out this image!',
            'from': '+14155551234',
            'messageType': 'marketing',
            'media_urls': ['https://example.com/image.jpg'],
            'subject': 'Cool Image',
            'webhook_url': 'https://example.com/webhook',
            'webhook_failover_url': 'https://example.com/webhook-backup',
            'tags': ['campaign-a', 'promo']
        }
        self.mock_http_client.post.assert_called_once_with('/v1/send', expected_payload)
        
        # Verify response
        assert response.id == 'msg_987654321'
        assert response.message_type == 'marketing'
        assert response.media_urls == ['https://example.com/image.jpg']
        assert response.subject == 'Cool Image'
        assert response.tags == ['campaign-a', 'promo']
    
    def test_send_media_only_mms(self):
        """Test sending MMS with media only (no text)."""
        mock_response = {
            'messageId': 'msg_media_only',
            'status': 'queued',
            'from': '+18005551234',
            'to': '+14155552671',
            'created_at': '2023-10-01T12:00:00Z',
            'segments': 1,
            'direction': 'outbound',
            'mediaType': 'image/png',
            'media_urls': ['https://example.com/photo.png'],
            'routing': {
                'numberType': 'toll-free',
                'rateLimit': 10,
                'coverage': 'high',
                'reason': 'smart-routing',
                'countryCode': '1'
            }
        }
        self.mock_http_client.post.return_value = mock_response
        
        # Send media-only MMS
        response = self.sms.send(
            to='+14155552671',
            media_urls=['https://example.com/photo.png']
        )
        
        # Verify payload excludes text field
        expected_payload = {
            'to': '+14155552671',
            'media_urls': ['https://example.com/photo.png']
        }
        self.mock_http_client.post.assert_called_once_with('/v1/send', expected_payload)
        
        # Verify response
        assert response.text is None
        assert response.media_urls == ['https://example.com/photo.png']
    
    @patch('sendly.resources.sms.validate_sms_request')
    def test_validation_called(self, mock_validate):
        """Test that request validation is called."""
        mock_response = {'messageId': 'test', 'status': 'queued', 'routing': {}}
        self.mock_http_client.post.return_value = mock_response
        
        self.sms.send(to='+14155552671', text='Hello')
        
        # Verify validation was called
        mock_validate.assert_called_once()
        request_arg = mock_validate.call_args[0][0]
        assert request_arg.to == '+14155552671'
        assert request_arg.text == 'Hello'
    
    @patch('sendly.resources.sms.validate_sms_request')
    def test_validation_error_propagated(self, mock_validate):
        """Test that validation errors are propagated."""
        mock_validate.side_effect = ValidationError('Invalid phone number')
        
        with pytest.raises(ValidationError, match='Invalid phone number'):
            self.sms.send(to='invalid', text='Hello')
        
        # HTTP client should not be called if validation fails
        self.mock_http_client.post.assert_not_called()
    
    def test_authentication_error(self):
        """Test handling of authentication errors."""
        self.mock_http_client.post.side_effect = AuthenticationError('Invalid API key')
        
        with pytest.raises(AuthenticationError, match='Invalid API key'):
            self.sms.send(to='+14155552671', text='Hello')
    
    def test_rate_limit_error(self):
        """Test handling of rate limit errors."""
        self.mock_http_client.post.side_effect = RateLimitError('Rate limit exceeded')
        
        with pytest.raises(RateLimitError, match='Rate limit exceeded'):
            self.sms.send(to='+14155552671', text='Hello')
    
    def test_api_error(self):
        """Test handling of general API errors."""
        self.mock_http_client.post.side_effect = APIError('Server error')
        
        with pytest.raises(APIError, match='Server error'):
            self.sms.send(to='+14155552671', text='Hello')
    
    def test_response_without_cost(self):
        """Test response transformation when cost info is missing."""
        mock_response = {
            'messageId': 'msg_no_cost',
            'status': 'queued',
            'to': '+14155552671',
            'routing': {}
        }
        self.mock_http_client.post.return_value = mock_response
        
        response = self.sms.send(to='+14155552671', text='Hello')
        
        assert response.cost is None
        assert response.id == 'msg_no_cost'
    
    def test_response_with_minimal_data(self):
        """Test response transformation with minimal API response."""
        mock_response = {
            'routing': {}
        }
        self.mock_http_client.post.return_value = mock_response
        
        response = self.sms.send(to='+14155552671', text='Hello')
        
        # Verify defaults are set correctly
        assert response.id == ''
        assert response.status == ''
        assert response.from_ == ''
        assert response.to == ''
        assert response.segments == 1
        assert response.direction == 'outbound'
        assert response.routing.number_type == ''
        assert response.routing.rate_limit == 0
    
    def test_build_payload_excludes_none_values(self):
        """Test that payload builder excludes None values."""
        # Create SMS instance to access private method
        sms = SMS(Mock())
        
        # Create request with some None values
        from sendly.types import SMSRequest
        request = SMSRequest(
            to='+14155552671',
            text='Hello',
            from_=None,
            message_type=None,
            media_urls=None
        )
        
        payload = sms._build_payload(request)
        
        # Verify only non-None values are included
        expected_payload = {
            'to': '+14155552671',
            'text': 'Hello'
        }
        assert payload == expected_payload
    
    def test_build_payload_includes_all_values(self):
        """Test that payload builder includes all non-None values."""
        sms = SMS(Mock())
        
        from sendly.types import SMSRequest
        request = SMSRequest(
            to='+14155552671',
            text='Hello world',
            from_='+18005551234',
            message_type='transactional',
            media_urls=['https://example.com/image.jpg'],
            subject='Test Subject',
            webhook_url='https://example.com/webhook',
            webhook_failover_url='https://example.com/backup',
            tags=['test', 'unit']
        )
        
        payload = sms._build_payload(request)
        
        expected_payload = {
            'to': '+14155552671',
            'text': 'Hello world',
            'from': '+18005551234',
            'messageType': 'transactional',
            'media_urls': ['https://example.com/image.jpg'],
            'subject': 'Test Subject',
            'webhook_url': 'https://example.com/webhook',
            'webhook_failover_url': 'https://example.com/backup',
            'tags': ['test', 'unit']
        }
        assert payload == expected_payload
    
    def test_transform_response_with_all_fields(self):
        """Test response transformation with all possible fields."""
        sms = SMS(Mock())
        
        api_response = {
            'messageId': 'msg_full',
            'status': 'delivered',
            'from': '+18005551234',
            'to': '+14155552671',
            'text': 'Hello world',
            'created_at': '2023-10-01T12:00:00Z',
            'segments': 2,
            'direction': 'outbound',
            'messageType': 'marketing',
            'mediaType': 'image/jpeg',
            'media_urls': ['https://example.com/image.jpg'],
            'subject': 'Test Subject',
            'webhook_url': 'https://example.com/webhook',
            'webhook_failover_url': 'https://example.com/backup',
            'tags': ['test', 'marketing'],
            'carrier': 'Verizon',
            'lineType': 'mobile',
            'parts': 2,
            'encoding': 'GSM-7',
            'media': {'type': 'image', 'size': 1024},
            'cost': {
                'amount': 0.015,
                'currency': 'USD'
            },
            'routing': {
                'numberType': 'toll-free',
                'rateLimit': 10,
                'coverage': 'high',
                'reason': 'smart-routing',
                'countryCode': '1'
            }
        }
        
        response = sms._transform_response(api_response)
        
        # Verify all fields are mapped correctly
        assert response.id == 'msg_full'
        assert response.status == 'delivered'
        assert response.from_ == '+18005551234'
        assert response.to == '+14155552671'
        assert response.text == 'Hello world'
        assert response.created_at == '2023-10-01T12:00:00Z'
        assert response.segments == 2
        assert response.direction == 'outbound'
        assert response.message_type == 'marketing'
        assert response.media_type == 'image/jpeg'
        assert response.media_urls == ['https://example.com/image.jpg']
        assert response.subject == 'Test Subject'
        assert response.webhook_url == 'https://example.com/webhook'
        assert response.webhook_failover_url == 'https://example.com/backup'
        assert response.tags == ['test', 'marketing']
        assert response.carrier == 'Verizon'
        assert response.line_type == 'mobile'
        assert response.parts == 2
        assert response.encoding == 'GSM-7'
        assert response.media == {'type': 'image', 'size': 1024}
        
        # Verify cost info
        assert response.cost.amount == 0.015
        assert response.cost.currency == 'USD'
        
        # Verify routing info
        assert response.routing.number_type == 'toll-free'
        assert response.routing.rate_limit == 10
        assert response.routing.coverage == 'high'
        assert response.routing.reason == 'smart-routing'
        assert response.routing.country_code == '1'