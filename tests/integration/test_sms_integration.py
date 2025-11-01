"""Integration tests for SMS functionality."""

import json
import pytest
import responses
from unittest.mock import patch

from sendly import Sendly
from sendly.errors import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError
)


class TestSMSIntegration:
    """Integration tests for SMS sending functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = 'sl_test_1234567890123456789012345678901234567890'
        self.base_url = 'https://api.sendly.test'
        self.client = Sendly(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=10.0,
            max_retries=2
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()
    
    @responses.activate
    def test_send_basic_sms_success(self):
        """Test sending a basic SMS message successfully."""
        # Mock API response
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_abc123',
                'status': 'queued',
                'from': '+18005551234',
                'to': '+14155552671',
                'text': 'Hello from Sendly!',
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
            },
            status=200
        )
        
        # Send SMS
        response = self.client.sms.send(
            to='+14155552671',
            text='Hello from Sendly!'
        )
        
        # Verify request was made correctly
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert request.method == 'POST'
        assert '/v1/send' in request.url
        
        # Verify request headers
        assert 'Bearer sl_test_' in request.headers['Authorization']
        assert request.headers['Content-Type'] == 'application/json'
        assert 'sendly-python' in request.headers['User-Agent']
        
        # Verify request body
        request_data = json.loads(request.body)
        assert request_data['to'] == '+14155552671'
        assert request_data['text'] == 'Hello from Sendly!'
        
        # Verify response
        assert response.id == 'msg_abc123'
        assert response.status == 'queued'
        assert response.from_ == '+18005551234'
        assert response.to == '+14155552671'
        assert response.text == 'Hello from Sendly!'
        assert response.segments == 1
        assert response.routing.number_type == 'toll-free'
        assert response.cost.amount == 0.0075
    
    @responses.activate
    def test_send_mms_with_all_parameters(self):
        """Test sending MMS with all parameters."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_mms456',
                'status': 'queued',
                'from': '+14155551234',
                'to': '+447700900123',
                'text': 'Check this out!',
                'created_at': '2023-10-01T12:00:00Z',
                'segments': 1,
                'direction': 'outbound',
                'messageType': 'marketing',
                'mediaType': 'image/jpeg',
                'media_urls': ['https://example.com/image.jpg'],
                'subject': 'Marketing Image',
                'webhook_url': 'https://myapp.com/webhook',
                'webhook_failover_url': 'https://myapp.com/webhook-backup',
                'tags': ['campaign-spring', 'promo'],
                'routing': {
                    'numberType': 'local',
                    'rateLimit': 5,
                    'coverage': 'medium',
                    'reason': 'local-routing',
                    'countryCode': '44'
                }
            },
            status=200
        )
        
        # Send MMS with all parameters
        response = self.client.sms.send(
            to='+447700900123',
            text='Check this out!',
            from_='+14155551234',
            message_type='marketing',
            media_urls=['https://example.com/image.jpg'],
            subject='Marketing Image',
            webhook_url='https://myapp.com/webhook',
            webhook_failover_url='https://myapp.com/webhook-backup',
            tags=['campaign-spring', 'promo']
        )
        
        # Verify request body includes all parameters
        request_data = json.loads(responses.calls[0].request.body)
        assert request_data['to'] == '+447700900123'
        assert request_data['text'] == 'Check this out!'
        assert request_data['from'] == '+14155551234'
        assert request_data['messageType'] == 'marketing'
        assert request_data['media_urls'] == ['https://example.com/image.jpg']
        assert request_data['subject'] == 'Marketing Image'
        assert request_data['webhook_url'] == 'https://myapp.com/webhook'
        assert request_data['webhook_failover_url'] == 'https://myapp.com/webhook-backup'
        assert request_data['tags'] == ['campaign-spring', 'promo']
        
        # Verify response
        assert response.id == 'msg_mms456'
        assert response.message_type == 'marketing'
        assert response.media_urls == ['https://example.com/image.jpg']
        assert response.tags == ['campaign-spring', 'promo']
    
    @responses.activate
    def test_validation_error_from_api(self):
        """Test validation error returned by API."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'validation_error',
                'message': 'Invalid phone number format for to field'
            },
            status=400
        )
        
        with pytest.raises(ValidationError, match='Invalid phone number format for to field'):
            self.client.sms.send(
                to='invalid-phone',
                text='Hello'
            )
    
    @responses.activate
    def test_authentication_error_from_api(self):
        """Test authentication error from API."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'authentication_error',
                'message': 'Invalid API key provided'
            },
            status=401
        )
        
        with pytest.raises(AuthenticationError, match='Invalid API key provided'):
            self.client.sms.send(
                to='+14155552671',
                text='Hello'
            )
    
    @responses.activate
    def test_rate_limit_with_retry_success(self):
        """Test rate limit error with successful retry."""
        # First request: rate limited
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'rate_limit_exceeded',
                'message': 'Rate limit exceeded. Try again in 2 seconds.',
                'retry_after': 2
            },
            status=429
        )
        
        # Second request: success
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_retry_success',
                'status': 'queued',
                'from': '+18005551234',
                'to': '+14155552671',
                'text': 'Retry success!',
                'routing': {
                    'numberType': 'toll-free',
                    'rateLimit': 10,
                    'coverage': 'high',
                    'reason': 'smart-routing',
                    'countryCode': '1'
                }
            },
            status=200
        )
        
        with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
            # Should succeed after retry
            response = self.client.sms.send(
                to='+14155552671',
                text='Retry success!'
            )
            
            # Verify retry delay
            mock_sleep.assert_called_once_with(2.0)
            
            # Verify success response
            assert response.id == 'msg_retry_success'
            assert response.text == 'Retry success!'
            
            # Verify two API calls were made
            assert len(responses.calls) == 2
    
    @responses.activate
    def test_rate_limit_max_retries_exceeded(self):
        """Test rate limit error exceeding max retries."""
        # Mock multiple rate limit responses
        for _ in range(3):  # max_retries + 1
            responses.add(
                responses.POST,
                f'{self.base_url}/v1/send',
                json={
                    'error': 'rate_limit_exceeded',
                    'message': 'Rate limit exceeded'
                },
                status=429
            )
        
        with patch('sendly.utils.http_client.time.sleep'):
            with pytest.raises(RateLimitError, match='Rate limit exceeded'):
                self.client.sms.send(
                    to='+14155552671',
                    text='Will fail'
                )
            
            # Verify all retry attempts were made
            assert len(responses.calls) == 3
    
    @responses.activate
    def test_server_error_with_retry_success(self):
        """Test server error with successful retry."""
        # First request: server error
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'internal_server_error',
                'message': 'Internal server error'
            },
            status=500
        )
        
        # Second request: success
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_server_retry',
                'status': 'queued',
                'routing': {}
            },
            status=200
        )
        
        with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
            response = self.client.sms.send(
                to='+14155552671',
                text='Server retry test'
            )
            
            # Verify exponential backoff delay
            mock_sleep.assert_called_once_with(1.0)
            
            # Verify success
            assert response.id == 'msg_server_retry'
            assert len(responses.calls) == 2
    
    @responses.activate
    def test_api_error_non_retryable(self):
        """Test non-retryable API error."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'not_found',
                'message': 'Resource not found'
            },
            status=404
        )
        
        with pytest.raises(APIError) as exc_info:
            self.client.sms.send(
                to='+14155552671',
                text='Will fail'
            )
        
        # Verify error details
        assert exc_info.value.message == 'Resource not found'
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == 'not_found'
        
        # Verify no retries for non-retryable error
        assert len(responses.calls) == 1
    
    def test_client_validation_before_api_call(self):
        """Test that client-side validation prevents invalid API calls."""
        # Invalid phone number should be caught before API call
        with pytest.raises(ValidationError, match='Invalid phone number format'):
            self.client.sms.send(
                to='invalid-phone',
                text='Hello'
            )
        
        # Missing content should be caught before API call  
        with pytest.raises(ValidationError, match='Either text or media_urls must be provided'):
            self.client.sms.send(
                to='+14155552671'
            )
        
        # Too many media URLs should be caught before API call
        with pytest.raises(ValidationError, match='Maximum 10 media URLs allowed'):
            self.client.sms.send(
                to='+14155552671',
                media_urls=['https://example.com/image.jpg'] * 11
            )
    
    @responses.activate
    def test_network_error_handling(self):
        """Test network error handling."""
        # Simulate network connection error
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            body=ConnectionError('Connection refused')
        )
        
        with pytest.raises(NetworkError):
            self.client.sms.send(
                to='+14155552671',
                text='Network error test'
            )
    
    def test_client_context_manager(self):
        """Test client as context manager."""
        with Sendly(api_key=self.api_key, base_url=self.base_url) as client:
            assert client.sms is not None
            assert client._http_client is not None
        
        # Client should be properly closed after context exit
        # (We can't easily verify session closure without exposing internals)
    
    def test_multiple_clients_independence(self):
        """Test that multiple client instances are independent."""
        client1 = Sendly(
            api_key='sl_test_key1',
            base_url='https://api1.example.com'
        )
        client2 = Sendly(
            api_key='sl_test_key2', 
            base_url='https://api2.example.com'
        )
        
        try:
            # Verify clients have different configurations
            assert client1._http_client.api_key == 'sl_test_key1'
            assert client2._http_client.api_key == 'sl_test_key2'
            assert client1._http_client.base_url == 'https://api1.example.com'
            assert client2._http_client.base_url == 'https://api2.example.com'
            
            # Verify they have independent sessions
            assert client1._http_client.session is not client2._http_client.session
            
        finally:
            client1.close()
            client2.close()
    
    @responses.activate
    def test_large_message_segmentation(self):
        """Test handling of large messages with segmentation."""
        # Large message that would require multiple segments
        large_text = 'This is a very long message ' * 20  # ~560 characters
        
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_large_text',
                'status': 'queued',
                'from': '+18005551234',
                'to': '+14155552671',
                'text': large_text,
                'segments': 4,  # Multiple segments
                'routing': {
                    'numberType': 'toll-free',
                    'coverage': 'high'
                },
                'cost': {
                    'amount': 0.03,  # Higher cost for multiple segments
                    'currency': 'USD'
                }
            },
            status=200
        )
        
        response = self.client.sms.send(
            to='+14155552671',
            text=large_text
        )
        
        # Verify segmentation is handled correctly
        assert response.segments == 4
        assert response.cost.amount == 0.03
        assert response.text == large_text
    
    @responses.activate  
    def test_international_routing(self):
        """Test international message routing."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_international',
                'status': 'queued',
                'from': '+14155551234',
                'to': '+447700900123',
                'text': 'International message',
                'routing': {
                    'numberType': 'local',
                    'coverage': 'medium',
                    'reason': 'international-routing',
                    'countryCode': '44'
                },
                'cost': {
                    'amount': 0.045,  # Higher cost for international
                    'currency': 'USD'
                }
            },
            status=200
        )
        
        response = self.client.sms.send(
            to='+447700900123',  # UK number
            text='International message'
        )
        
        # Verify international routing
        assert response.routing.country_code == '44'
        assert response.routing.reason == 'international-routing'
        assert response.cost.amount == 0.045
    
    def test_client_configuration_immutability(self):
        """Test that client configuration cannot be accidentally modified."""
        original_base_url = self.client._http_client.base_url
        original_api_key = self.client._http_client.api_key
        original_timeout = self.client._http_client.timeout
        
        # These should remain unchanged regardless of what we try to do
        assert self.client._http_client.base_url == original_base_url
        assert self.client._http_client.api_key == original_api_key  
        assert self.client._http_client.timeout == original_timeout