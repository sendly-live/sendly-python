"""
Sendly Sandbox Testing Example

This example demonstrates comprehensive testing using test numbers
in the Sendly sandbox environment. Use this with test API keys (sl_test_*)
to validate your integration without incurring charges.
"""

import os
import time
from sendly import Sendly, MAGIC_NUMBERS, RateLimitError, ValidationError, APIError


def main():
    """Run complete sandbox test suite."""
    
    # Initialize the client with test API key
    api_key = os.getenv('SENDLY_TEST_KEY', 'sl_test_YOUR_TEST_KEY')
    client = Sendly(api_key=api_key)
    
    print("Starting Sendly Sandbox Tests")
    print("=" * 50)
    
    # Run test suites
    test_success_scenarios(client)
    test_error_scenarios(client)
    test_delay_scenarios(client)
    test_carrier_scenarios(client)
    test_webhook_scenarios(client)
    test_mms_functionality(client)
    test_message_tagging(client)
    
    print("\n" + "=" * 50)
    print("Sandbox tests completed")


def test_success_scenarios(client):
    """Test successful delivery scenarios."""
    print("\n[SUCCESS SCENARIOS]\n")
    
    # Test instant delivery
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text='Testing instant delivery'
        )
        print(f"✓ Instant delivery: {response.status} (ID: {response.id})")
    except Exception as e:
        print(f"✗ Instant delivery failed: {e}")
    
    # Test delayed delivery
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['delay_5s'],
            text='Testing 5 second delay'
        )
        print(f"✓ Delayed delivery: queued (ID: {response.id})")
        print("  Message will be delivered after 5 seconds")
    except Exception as e:
        print(f"✗ Delayed delivery failed: {e}")
    
    # Test carrier simulation
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['verizon_carrier'],
            text='Testing Verizon carrier simulation'
        )
        print(f"✓ Verizon simulation: {response.status}")
        if hasattr(response, 'routing') and response.routing:
            print(f"  Carrier: {response.routing.get('carrier', 'N/A')}")
    except Exception as e:
        print(f"✗ Verizon simulation failed: {e}")


def test_error_scenarios(client):
    """Test error handling scenarios."""
    print("\n[ERROR SCENARIOS]\n")
    
    # Test invalid number error
    try:
        client.sms.send(
            to=MAGIC_NUMBERS['errors']['invalid_number'],
            text='Testing invalid number'
        )
        print("✗ Invalid number: Expected error but got success")
    except ValidationError as e:
        print(f"✓ Invalid number error caught: {e}")
    except Exception as e:
        print(f"✓ Invalid number error caught: {e}")
    
    # Test carrier rejection
    try:
        client.sms.send(
            to=MAGIC_NUMBERS['errors']['carrier_rejection'],
            text='Testing carrier rejection'
        )
        print("✗ Carrier rejection: Expected error but got success")
    except Exception as e:
        print(f"✓ Carrier rejection caught: {e}")
    
    # Test rate limit error
    try:
        client.sms.send(
            to=MAGIC_NUMBERS['errors']['rate_limit'],
            text='Testing rate limit'
        )
        print("✗ Rate limit: Expected error but got success")
    except RateLimitError as e:
        print(f"✓ Rate limit error caught: {e}")
        if hasattr(e, 'retry_after'):
            print(f"  Retry after: {e.retry_after} seconds")
    except Exception as e:
        print(f"✓ Rate limit error caught: {e}")
    
    # Test timeout error
    try:
        client.sms.send(
            to=MAGIC_NUMBERS['errors']['timeout'],
            text='Testing timeout'
        )
        print("✗ Timeout: Expected error but got success")
    except Exception as e:
        print(f"✓ Timeout error caught: {e}")
    
    # Test insufficient balance error
    try:
        client.sms.send(
            to=MAGIC_NUMBERS['errors']['insufficient_balance'],
            text='Testing insufficient balance'
        )
        print("✗ Insufficient balance: Expected error but got success")
    except Exception as e:
        print(f"✓ Insufficient balance caught: {e}")


def test_delay_scenarios(client):
    """Test various delay scenarios."""
    print("\n[DELAY SCENARIOS]\n")
    
    delays = [
        (MAGIC_NUMBERS['delays']['10_seconds'], '10 seconds'),
        (MAGIC_NUMBERS['delays']['30_seconds'], '30 seconds'),
        (MAGIC_NUMBERS['delays']['60_seconds'], '60 seconds'),
    ]
    
    for number, duration in delays:
        try:
            response = client.sms.send(
                to=number,
                text=f'Testing {duration} delay'
            )
            print(f"✓ {duration} delay: Message queued (ID: {response.id})")
            print(f"  Status progression will take {duration}")
        except Exception as e:
            print(f"✗ {duration} delay failed: {e}")


def test_carrier_scenarios(client):
    """Test carrier-specific behaviors."""
    print("\n[CARRIER SCENARIOS]\n")
    
    carriers = [
        (MAGIC_NUMBERS['carriers']['verizon'], 'Verizon'),
        (MAGIC_NUMBERS['carriers']['att'], 'AT&T'),
        (MAGIC_NUMBERS['carriers']['tmobile'], 'T-Mobile'),
    ]
    
    for number, carrier in carriers:
        try:
            response = client.sms.send(
                to=number,
                text=f'Testing {carrier} carrier behavior'
            )
            print(f"✓ {carrier}: Message sent (ID: {response.id})")
            if hasattr(response, 'routing') and response.routing:
                print(f"  Simulated carrier: {response.routing.get('carrier', 'N/A')}")
        except Exception as e:
            print(f"✗ {carrier} test failed: {e}")


def test_webhook_scenarios(client):
    """Test webhook simulation scenarios."""
    print("\n[WEBHOOK SCENARIOS]\n")
    
    webhook_url = 'https://example.com/webhook'
    webhook_failover_url = 'https://example.com/webhook-failover'
    
    # Test successful webhook
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['webhooks']['success'],
            text='Testing webhook success',
            webhook_url=webhook_url
        )
        print(f"✓ Webhook success: Message sent (ID: {response.id})")
        print(f"  Webhook will be simulated to: {webhook_url}")
    except Exception as e:
        print(f"✗ Webhook success failed: {e}")
    
    # Test webhook timeout
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['webhooks']['timeout'],
            text='Testing webhook timeout',
            webhook_url=webhook_url,
            webhook_failover_url=webhook_failover_url
        )
        print(f"✓ Webhook timeout: Message sent (ID: {response.id})")
        print(f"  Timeout simulation will trigger failover")
    except Exception as e:
        print(f"✗ Webhook timeout failed: {e}")
    
    # Test webhook error with retry
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['webhooks']['error_500'],
            text='Testing webhook error',
            webhook_url=webhook_url
        )
        print(f"✓ Webhook error: Message sent (ID: {response.id})")
        print(f"  500 error will trigger retry logic")
    except Exception as e:
        print(f"✗ Webhook error failed: {e}")


def test_mms_functionality(client):
    """Test MMS functionality with test numbers."""
    print("\n[MMS SCENARIOS]\n")
    
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text='Testing MMS with media',
            media_urls=['https://example.com/image.jpg'],
            subject='MMS Test'
        )
        print(f"✓ MMS sent: {response.status} (ID: {response.id})")
        if hasattr(response, 'media_type'):
            print(f"  Media type: {response.media_type}")
    except Exception as e:
        print(f"✗ MMS failed: {e}")


def test_message_tagging(client):
    """Test message tagging and analytics."""
    print("\n[TAGGING SCENARIOS]\n")
    
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text='Testing message tags',
            tags=['test', 'sandbox', 'automated', 'v1.0']
        )
        print(f"✓ Tagged message sent (ID: {response.id})")
        if hasattr(response, 'tags') and response.tags:
            print(f"  Tags: {', '.join(response.tags)}")
    except Exception as e:
        print(f"✗ Tagged message failed: {e}")


def test_batch_processing(client):
    """Test batch message processing."""
    print("\n[BATCH PROCESSING]\n")
    
    recipients = [
        MAGIC_NUMBERS['success']['instant'],
        MAGIC_NUMBERS['success']['delay_5s'],
        MAGIC_NUMBERS['carriers']['verizon'],
    ]
    
    success_count = 0
    error_count = 0
    
    for idx, recipient in enumerate(recipients, 1):
        try:
            response = client.sms.send(
                to=recipient,
                text=f'Batch message #{idx}',
                tags=['batch', f'message-{idx}']
            )
            print(f"✓ Message {idx}: Sent to {recipient}")
            success_count += 1
            
            # Small delay between messages
            time.sleep(0.1)
        except Exception as e:
            print(f"✗ Message {idx}: Failed - {e}")
            error_count += 1
    
    print(f"\nBatch results: {success_count} success, {error_count} failures")


def test_comprehensive_flow(client):
    """Test a comprehensive real-world flow."""
    print("\n[COMPREHENSIVE FLOW TEST]\n")
    
    # Simulate a user verification flow
    print("Simulating user verification flow:")
    
    # Step 1: Send OTP
    try:
        otp = "123456"
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text=f'Your verification code is: {otp}',
            message_type='otp',
            tags=['verification', 'otp']
        )
        print(f"1. OTP sent: {response.id}")
    except Exception as e:
        print(f"1. OTP failed: {e}")
        return
    
    # Step 2: Send welcome message after verification
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text='Welcome to Sendly! Your account is now verified.',
            message_type='transactional',
            tags=['onboarding', 'welcome']
        )
        print(f"2. Welcome message sent: {response.id}")
    except Exception as e:
        print(f"2. Welcome message failed: {e}")
    
    # Step 3: Send promotional offer
    try:
        response = client.sms.send(
            to=MAGIC_NUMBERS['success']['instant'],
            text='Get 50% off your first month! Use code: WELCOME50',
            message_type='marketing',
            tags=['promotion', 'new-user']
        )
        print(f"3. Promotional offer sent: {response.id}")
    except Exception as e:
        print(f"3. Promotional offer failed: {e}")
    
    print("\nUser verification flow completed")


if __name__ == '__main__':
    main()