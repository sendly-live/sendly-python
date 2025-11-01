#!/usr/bin/env python3
"""
Advanced Usage Examples for Sendly Python SDK

This example demonstrates advanced features:
- Webhook handling and verification
- Batch message processing
- Retry logic and error recovery
- Custom configuration
- Performance monitoring
"""

import os
import time
import hmac
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from sendly import Sendly
from sendly.errors import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NetworkError
)

def webhook_verification_example():
    """Demonstrate webhook signature verification."""
    print("🔐 Webhook Verification Example")
    print("-" * 35)
    
    # Example webhook payload (what you'd receive in your webhook endpoint)
    webhook_payload = {
        "messageId": "msg_abc123",
        "status": "delivered",
        "to": "+14155552671",
        "timestamp": "2023-10-01T12:00:00Z",
        "eventType": "message.delivered"
    }
    
    # Example webhook signature (from X-Sendly-Signature header)
    webhook_secret = "whsec_your_webhook_secret_here"
    webhook_signature = "sha256=abc123def456..."  # This would be in the header
    
    def verify_webhook_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """Verify webhook signature for security."""
        import json
        
        # Create expected signature
        payload_string = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (use hmac.compare_digest for security)
        expected_header = f"sha256={expected_signature}"
        return hmac.compare_digest(expected_header, signature)
    
    # In a real webhook handler, you'd verify the signature first
    print("🔍 Webhook payload received:")
    print(f"   Message ID: {webhook_payload['messageId']}")
    print(f"   Status: {webhook_payload['status']}")
    print(f"   Event Type: {webhook_payload['eventType']}")
    print(f"   Timestamp: {webhook_payload['timestamp']}")
    
    # Simulate signature verification (would use actual signature in production)
    # is_valid = verify_webhook_signature(webhook_payload, webhook_signature, webhook_secret)
    # print(f"   Signature Valid: {is_valid}")
    
    print("✅ Webhook processed successfully")
    print()

def batch_processing_example():
    """Demonstrate batch message processing with proper rate limiting."""
    print("📊 Batch Processing Example")
    print("-" * 30)
    
    client = Sendly(
        api_key=os.environ.get('SENDLY_API_KEY'),
        max_retries=3,
        timeout=30.0
    )
    
    # Example: Send personalized messages to multiple recipients
    recipients = [
        {'phone': '+14155552671', 'name': 'Alice', 'code': 'ABC123'},
        {'phone': '+14155552672', 'name': 'Bob', 'code': 'DEF456'},
        {'phone': '+14155552673', 'name': 'Charlie', 'code': 'GHI789'},
        {'phone': '+14155552674', 'name': 'Diana', 'code': 'JKL012'},
        {'phone': '+14155552675', 'name': 'Eve', 'code': 'MNO345'},
    ]
    
    def send_message(recipient: Dict[str, str]) -> Dict[str, Any]:
        """Send a message to a single recipient."""
        try:
            response = client.sms.send(
                to=recipient['phone'],
                text=f"Hi {recipient['name']}! Your verification code is: {recipient['code']}",
                message_type='otp',
                tags=['batch-send', 'verification', f"user-{recipient['name'].lower()}"]
            )
            
            return {
                'recipient': recipient,
                'success': True,
                'message_id': response.id,
                'status': response.status,
                'cost': response.cost.amount if response.cost else 0,
                'error': None
            }
            
        except RateLimitError as e:
            print(f"⏳ Rate limited for {recipient['name']}, retrying after {e.retry_after or 1}s...")
            time.sleep(e.retry_after or 1)
            return send_message(recipient)  # Retry once
            
        except Exception as e:
            return {
                'recipient': recipient,
                'success': False,
                'message_id': None,
                'status': 'failed',
                'cost': 0,
                'error': str(e)
            }
    
    print(f"📤 Sending messages to {len(recipients)} recipients...")
    
    # Sequential processing (recommended for rate limit compliance)
    results = []
    total_cost = 0.0
    successful_sends = 0
    
    for i, recipient in enumerate(recipients, 1):
        print(f"   Sending {i}/{len(recipients)} to {recipient['name']}...")
        
        result = send_message(recipient)
        results.append(result)
        
        if result['success']:
            successful_sends += 1
            total_cost += result['cost']
            print(f"   ✅ Sent to {recipient['name']} (ID: {result['message_id']})")
        else:
            print(f"   ❌ Failed to send to {recipient['name']}: {result['error']}")
        
        # Rate limiting: wait between requests
        if i < len(recipients):
            time.sleep(0.1)  # 100ms delay between requests
    
    print(f"\n📈 Batch Processing Summary:")
    print(f"   Total Messages: {len(recipients)}")
    print(f"   Successful: {successful_sends}")
    print(f"   Failed: {len(recipients) - successful_sends}")
    print(f"   Total Cost: ${total_cost:.4f}")
    print(f"   Average Cost: ${total_cost/successful_sends:.4f}" if successful_sends > 0 else "   Average Cost: N/A")
    
    client.close()
    print()

def concurrent_processing_example():
    """Demonstrate concurrent processing with thread safety."""
    print("⚡ Concurrent Processing Example")
    print("-" * 35)
    
    # Note: Each thread should have its own client instance for thread safety
    def create_client():
        return Sendly(
            api_key=os.environ.get('SENDLY_API_KEY'),
            max_retries=2,
            timeout=15.0
        )
    
    # Example: Send different message types concurrently
    message_tasks = [
        {
            'to': '+14155552671',
            'text': 'Your order has been confirmed! 📦',
            'message_type': 'transactional',
            'tags': ['order', 'confirmation']
        },
        {
            'to': '+14155552672',
            'text': 'Your verification code: 987654',
            'message_type': 'otp',
            'tags': ['auth', 'verification']
        },
        {
            'to': '+14155552673',
            'text': 'Flash sale: 30% off everything! 🏷️',
            'message_type': 'marketing',
            'tags': ['marketing', 'sale']
        },
        {
            'to': '+14155552674',
            'text': 'Server maintenance tonight at 2 AM ⚠️',
            'message_type': 'alert',
            'tags': ['system', 'maintenance']
        }
    ]
    
    def send_concurrent_message(task: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message in a separate thread."""
        client = create_client()
        try:
            response = client.sms.send(**task)
            return {
                'task': task,
                'success': True,
                'message_id': response.id,
                'routing': response.routing.reason if response.routing else None,
                'error': None
            }
        except Exception as e:
            return {
                'task': task,
                'success': False,
                'message_id': None,
                'routing': None,
                'error': str(e)
            }
        finally:
            client.close()
    
    print(f"🚀 Sending {len(message_tasks)} messages concurrently...")
    
    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(send_concurrent_message, task): task 
            for task in message_tasks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_task):
            result = future.result()
            task = result['task']
            
            if result['success']:
                print(f"   ✅ {task['message_type'].title()}: {result['message_id']}")
                if result['routing']:
                    print(f"      Routing: {result['routing']}")
            else:
                print(f"   ❌ {task['message_type'].title()}: {result['error']}")
    
    print("✅ Concurrent processing completed")
    print()

def custom_configuration_example():
    """Demonstrate custom client configuration for different use cases."""
    print("⚙️  Custom Configuration Example")
    print("-" * 35)
    
    # Configuration for high-volume production usage
    production_client = Sendly(
        api_key=os.environ.get('SENDLY_API_KEY'),
        base_url='https://api.sendly.live',  # Production endpoint
        timeout=60.0,  # Longer timeout for reliability
        max_retries=5,  # More retries for resilience
        user_agent='MyApp/1.0 (production)'
    )
    
    # Configuration for development/testing
    dev_client = Sendly(
        api_key=os.environ.get('SENDLY_API_KEY'),
        base_url='https://api.sendly.dev',  # Development endpoint
        timeout=10.0,  # Shorter timeout for faster feedback
        max_retries=1,  # Fewer retries for faster development
        user_agent='MyApp/1.0 (development)'
    )
    
    # Configuration for batch processing
    batch_client = Sendly(
        api_key=os.environ.get('SENDLY_API_KEY'),
        timeout=30.0,
        max_retries=3,
        user_agent='MyApp/1.0 (batch-processor)'
    )
    
    print("🏭 Production client configured:")
    print(f"   Base URL: {production_client._http_client.base_url}")
    print(f"   Timeout: {production_client._http_client.timeout}s")
    print(f"   Max Retries: {production_client._http_client.max_retries}")
    print(f"   User Agent: {production_client._http_client.session.headers['User-Agent']}")
    
    print("\n🔧 Development client configured:")
    print(f"   Base URL: {dev_client._http_client.base_url}")
    print(f"   Timeout: {dev_client._http_client.timeout}s")
    print(f"   Max Retries: {dev_client._http_client.max_retries}")
    
    # Clean up
    production_client.close()
    dev_client.close()
    batch_client.close()
    print()

def performance_monitoring_example():
    """Demonstrate performance monitoring and metrics collection."""
    print("📊 Performance Monitoring Example")
    print("-" * 37)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    # Metrics collection
    metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'total_cost': 0.0,
        'response_times': [],
        'error_types': {}
    }
    
    def send_monitored_message(to: str, text: str, **kwargs) -> Dict[str, Any]:
        """Send a message with performance monitoring."""
        start_time = time.time()
        metrics['total_requests'] += 1
        
        try:
            response = client.sms.send(to=to, text=text, **kwargs)
            
            # Record success metrics
            metrics['successful_requests'] += 1
            if response.cost:
                metrics['total_cost'] += response.cost.amount
            
            response_time = time.time() - start_time
            metrics['response_times'].append(response_time)
            
            return {
                'success': True,
                'response': response,
                'response_time': response_time,
                'error': None
            }
            
        except Exception as e:
            # Record error metrics
            metrics['failed_requests'] += 1
            error_type = type(e).__name__
            metrics['error_types'][error_type] = metrics['error_types'].get(error_type, 0) + 1
            
            response_time = time.time() - start_time
            metrics['response_times'].append(response_time)
            
            return {
                'success': False,
                'response': None,
                'response_time': response_time,
                'error': str(e)
            }
    
    # Send test messages with monitoring
    test_messages = [
        ('+14155552671', 'Performance test message 1'),
        ('+14155552672', 'Performance test message 2'),
        ('+14155552673', 'Performance test message 3'),
        ('invalid-phone', 'This will cause a validation error'),  # Intentional error
        ('+14155552674', 'Performance test message 4'),
    ]
    
    print("🧪 Sending test messages with performance monitoring...")
    
    for i, (to, text) in enumerate(test_messages, 1):
        print(f"   Test {i}: ", end='', flush=True)
        result = send_monitored_message(to, text, message_type='transactional')
        
        if result['success']:
            print(f"✅ Success ({result['response_time']:.3f}s)")
        else:
            print(f"❌ Error: {result['error']} ({result['response_time']:.3f}s)")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Calculate and display metrics
    avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
    success_rate = (metrics['successful_requests'] / metrics['total_requests']) * 100
    
    print(f"\n📈 Performance Metrics:")
    print(f"   Total Requests: {metrics['total_requests']}")
    print(f"   Successful: {metrics['successful_requests']}")
    print(f"   Failed: {metrics['failed_requests']}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Average Response Time: {avg_response_time:.3f}s")
    print(f"   Total Cost: ${metrics['total_cost']:.4f}")
    
    if metrics['error_types']:
        print(f"   Error Types:")
        for error_type, count in metrics['error_types'].items():
            print(f"     {error_type}: {count}")
    
    client.close()
    print()

def error_recovery_example():
    """Demonstrate advanced error recovery strategies."""
    print("🔄 Error Recovery Example")
    print("-" * 26)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    def send_with_recovery(to: str, text: str, max_attempts: int = 3) -> bool:
        """Send message with custom retry logic."""
        
        for attempt in range(max_attempts):
            try:
                response = client.sms.send(to=to, text=text)
                print(f"   ✅ Success on attempt {attempt + 1}: {response.id}")
                return True
                
            except RateLimitError as e:
                print(f"   ⏳ Rate limited on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    wait_time = e.retry_after or (2 ** attempt)  # Exponential backoff
                    print(f"      Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Max attempts reached, giving up")
                    return False
                    
            except NetworkError as e:
                print(f"   🌐 Network error on attempt {attempt + 1}: {e.message}")
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"      Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Max attempts reached, network still unavailable")
                    return False
                    
            except (ValidationError, AuthenticationError) as e:
                # Don't retry these errors - they won't succeed on retry
                print(f"   ❌ Non-retryable error: {e.message}")
                return False
                
            except Exception as e:
                print(f"   ❓ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    print(f"      Retrying...")
                    time.sleep(1)
                    continue
                else:
                    print(f"   ❌ Max attempts reached")
                    return False
        
        return False
    
    # Test error recovery scenarios
    test_cases = [
        ('+14155552671', 'This should succeed'),
        ('invalid-phone', 'This will fail validation (no retry)'),
        ('+14155552672', 'This might hit rate limits'),
    ]
    
    for to, text in test_cases:
        print(f"🧪 Testing recovery for: {text[:30]}...")
        success = send_with_recovery(to, text)
        print(f"   Final result: {'✅ Success' if success else '❌ Failed'}")
        print()
    
    client.close()

def main():
    """Run all advanced examples."""
    print("🚀 Sendly Python SDK - Advanced Examples")
    print("=" * 55)
    print()
    
    # Check for API key
    if not os.environ.get('SENDLY_API_KEY'):
        print("❌ Please set SENDLY_API_KEY environment variable")
        print("   export SENDLY_API_KEY='sl_test_your_api_key_here'")
        return
    
    # Run advanced examples
    webhook_verification_example()
    batch_processing_example()
    concurrent_processing_example()
    custom_configuration_example()
    performance_monitoring_example()
    error_recovery_example()
    
    print("✨ All advanced examples completed!")

if __name__ == '__main__':
    main()