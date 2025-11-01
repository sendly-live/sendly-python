"""Integration tests for error scenarios and edge cases."""

import json
import pytest
import responses
from unittest.mock import patch
import requests

from sendly import Sendly
from sendly.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ValidationError
)


class TestErrorScenarios:
    """Integration tests for various error scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = 'sl_test_1234567890123456789012345678901234567890'
        self.base_url = 'https://api.sendly.test'
        self.client = Sendly(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=5.0,
            max_retries=2
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()
    
    @responses.activate
    def test_malformed_json_response(self):
        """Test handling of malformed JSON response."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            body='{"invalid": json malformed',  # Invalid JSON
            status=200,
            content_type='application/json'
        )
        
        with pytest.raises(APIError, match='Invalid JSON in response'):
            self.client.sms.send(
                to='+14155552671',
                text='Test malformed JSON'
            )
    
    @responses.activate
    def test_empty_response_body(self):
        """Test handling of empty response body."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            body='',
            status=200,
            content_type='application/json'
        )
        
        with pytest.raises(APIError, match='Invalid JSON in response'):
            self.client.sms.send(
                to='+14155552671',
                text='Test empty response'
            )
    
    @responses.activate
    def test_non_json_error_response(self):
        """Test handling of non-JSON error response."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            body='Internal Server Error',
            status=500,
            content_type='text/html'
        )
        
        with pytest.raises(APIError) as exc_info:
            self.client.sms.send(
                to='+14155552671',
                text='Test non-JSON error'
            )
        
        # Should handle non-JSON error gracefully
        assert 'Internal Server Error' in exc_info.value.message
        assert exc_info.value.status_code == 500
    
    @responses.activate
    def test_rate_limit_without_retry_after_header(self):
        """Test rate limit error without retry-after header."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'rate_limit_exceeded',
                'message': 'Too many requests'
            },
            status=429
        )
        
        # Add success response for retry
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_after_rate_limit',
                'status': 'queued',
                'routing': {}
            },
            status=200
        )
        
        with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
            response = self.client.sms.send(
                to='+14155552671',
                text='Rate limit without retry-after'
            )
            
            # Should use exponential backoff when no retry-after provided
            mock_sleep.assert_called_once_with(1.0)  # First retry delay
            assert response.id == 'msg_after_rate_limit'
    
    @responses.activate
    def test_mixed_error_responses_in_retries(self):
        """Test different error types across retry attempts."""
        # First attempt: rate limit
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'rate_limit_exceeded',
                'message': 'Rate limit exceeded'
            },
            status=429
        )
        
        # Second attempt: server error
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'internal_server_error',
                'message': 'Database connection failed'
            },
            status=500
        )
        
        # Third attempt: success
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_mixed_errors',
                'status': 'queued',
                'routing': {}
            },
            status=200
        )
        
        with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
            response = self.client.sms.send(
                to='+14155552671',
                text='Mixed errors test'
            )
            
            # Should retry through different error types
            assert mock_sleep.call_count == 2
            assert response.id == 'msg_mixed_errors'
            assert len(responses.calls) == 3
    
    @responses.activate
    def test_authentication_error_no_retry(self):
        """Test that authentication errors are not retried."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'authentication_error',
                'message': 'Invalid API key'
            },
            status=401
        )
        
        with pytest.raises(AuthenticationError, match='Invalid API key'):
            self.client.sms.send(
                to='+14155552671',
                text='Auth error test'
            )
        
        # Should not retry authentication errors
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_validation_error_no_retry(self):
        """Test that validation errors are not retried."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'validation_error',
                'message': 'Invalid message format'
            },
            status=400
        )
        
        with pytest.raises(ValidationError, match='Invalid message format'):
            self.client.sms.send(
                to='+14155552671',
                text='Validation error test'
            )
        
        # Should not retry validation errors
        assert len(responses.calls) == 1
    
    def test_timeout_with_retries(self):
        """Test timeout error with retry behavior."""
        def timeout_callback(request):
            raise requests.exceptions.Timeout('Request timed out')
        
        with responses.RequestsMock() as rsps:
            # First two attempts timeout
            rsps.add_callback(
                responses.POST,
                f'{self.base_url}/v1/send',
                callback=timeout_callback
            )
            rsps.add_callback(
                responses.POST,
                f'{self.base_url}/v1/send',
                callback=timeout_callback
            )
            
            # Third attempt succeeds
            rsps.add(
                responses.POST,
                f'{self.base_url}/v1/send',
                json={
                    'messageId': 'msg_timeout_recovery',
                    'status': 'queued',
                    'routing': {}
                },
                status=200
            )
            
            with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
                response = self.client.sms.send(
                    to='+14155552671',
                    text='Timeout recovery test'
                )
                
                # Verify retries with exponential backoff
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(1.0)  # First retry
                mock_sleep.assert_any_call(2.0)  # Second retry
                
                assert response.id == 'msg_timeout_recovery'
    
    def test_connection_error_max_retries(self):
        """Test connection error exceeding max retries."""
        def connection_error_callback(request):
            raise requests.exceptions.ConnectionError('Connection refused')
        
        with responses.RequestsMock() as rsps:
            # All attempts fail with connection error
            for _ in range(3):  # max_retries + 1
                rsps.add_callback(
                    responses.POST,
                    f'{self.base_url}/v1/send',
                    callback=connection_error_callback
                )
            
            with patch('sendly.utils.http_client.time.sleep') as mock_sleep:
                with pytest.raises(NetworkError, match='Connection error'):
                    self.client.sms.send(
                        to='+14155552671',
                        text='Connection error test'
                    )
                
                # Should attempt all retries
                assert mock_sleep.call_count == 2  # max_retries
    
    @responses.activate
    def test_partial_success_response(self):
        """Test handling of partial/incomplete success response."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_partial',
                # Missing most fields that would normally be present
                'routing': {}  # Minimal routing info
            },
            status=200
        )
        
        response = self.client.sms.send(
            to='+14155552671',
            text='Partial response test'
        )
        
        # Should handle missing fields gracefully with defaults
        assert response.id == 'msg_partial'
        assert response.status == ''  # Default empty string
        assert response.from_ == ''  # Default empty string
        assert response.to == ''  # Default empty string
        assert response.segments == 1  # Default value
        assert response.direction == 'outbound'  # Default value
        assert response.cost is None  # No cost info provided
    
    @responses.activate
    def test_unexpected_success_status_code(self):
        """Test handling of unexpected success status codes."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'messageId': 'msg_202',
                'status': 'accepted',
                'routing': {}
            },
            status=202  # Accepted instead of 200
        )
        
        # Should treat 202 as success
        response = self.client.sms.send(
            to='+14155552671',
            text='202 status test'
        )
        
        assert response.id == 'msg_202'
        assert response.status == 'accepted'
    
    @responses.activate
    def test_error_response_with_extra_fields(self):
        """Test error response with additional fields."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'validation_error',
                'message': 'Phone number validation failed',
                'field': 'to',
                'code': 'INVALID_PHONE_FORMAT',
                'documentation_url': 'https://docs.sendly.com/errors',
                'request_id': 'req_123456789'
            },
            status=400
        )
        
        with pytest.raises(ValidationError) as exc_info:
            self.client.sms.send(
                to='invalid-phone',
                text='Extra fields error test'
            )
        
        # Should extract the message correctly despite extra fields
        assert exc_info.value.message == 'Phone number validation failed'
        assert exc_info.value.code == 'validation_error'
    
    @responses.activate
    def test_api_error_with_custom_code(self):
        """Test API error with custom error code."""
        responses.add(
            responses.POST,
            f'{self.base_url}/v1/send',
            json={
                'error': 'insufficient_credits',
                'message': 'Account has insufficient credits to send message'
            },
            status=402  # Payment required
        )
        
        with pytest.raises(APIError) as exc_info:
            self.client.sms.send(
                to='+14155552671',
                text='Insufficient credits test'
            )
        
        assert exc_info.value.message == 'Account has insufficient credits to send message'
        assert exc_info.value.status_code == 402
        assert exc_info.value.code == 'insufficient_credits'
    
    def test_client_with_invalid_base_url(self):
        """Test client behavior with invalid base URL."""
        # This should work during initialization but fail during requests
        client = Sendly(
            api_key=self.api_key,
            base_url='invalid-url-format'
        )
        
        try:
            with pytest.raises(NetworkError):
                client.sms.send(
                    to='+14155552671',
                    text='Invalid URL test'
                )
        finally:
            client.close()
    
    @responses.activate
    def test_concurrent_requests_independence(self):
        """Test that concurrent requests don't interfere with each other."""
        # Add multiple identical responses
        for i in range(3):
            responses.add(
                responses.POST,
                f'{self.base_url}/v1/send',
                json={
                    'messageId': f'msg_concurrent_{i}',
                    'status': 'queued',
                    'routing': {}
                },
                status=200
            )
        
        # Create multiple clients to simulate concurrent usage
        client1 = Sendly(api_key='sl_test_key1', base_url=self.base_url)
        client2 = Sendly(api_key='sl_test_key2', base_url=self.base_url)
        client3 = Sendly(api_key='sl_test_key3', base_url=self.base_url)
        
        try:
            # Send messages concurrently (simulated)
            response1 = client1.sms.send(to='+14155552671', text='Message 1')
            response2 = client2.sms.send(to='+14155552672', text='Message 2')
            response3 = client3.sms.send(to='+14155552673', text='Message 3')
            
            # Each should get their own response
            assert response1.id == 'msg_concurrent_0'
            assert response2.id == 'msg_concurrent_1'
            assert response3.id == 'msg_concurrent_2'
            
            # Verify different API keys were used
            assert 'sl_test_key1' in responses.calls[0].request.headers['Authorization']
            assert 'sl_test_key2' in responses.calls[1].request.headers['Authorization']
            assert 'sl_test_key3' in responses.calls[2].request.headers['Authorization']
            
        finally:
            client1.close()
            client2.close()
            client3.close()
    
    def test_memory_cleanup_after_multiple_requests(self):
        """Test that memory is properly managed across multiple requests."""
        # This is more of a smoke test to ensure no obvious memory leaks
        client = Sendly(api_key=self.api_key, base_url=self.base_url)
        
        try:
            # Simulate multiple failed requests (which would create exception objects)
            for i in range(10):
                try:
                    with pytest.raises(ValidationError):
                        client.sms.send(
                            to='invalid-phone',
                            text=f'Memory test {i}'
                        )
                except:
                    pass  # Expected to fail
            
            # Client should still be functional
            assert client.sms is not None
            assert client._http_client is not None
            
        finally:
            client.close()