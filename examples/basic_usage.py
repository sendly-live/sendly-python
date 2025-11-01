#!/usr/bin/env python3
"""
Basic Usage Examples for Sendly Python SDK

This example demonstrates the fundamental features of the Sendly Python SDK:
- Sending basic SMS messages
- Sending MMS with media
- Error handling
- Using different message types for smart routing
"""

import os
from sendly import Sendly
from sendly.errors import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NetworkError
)

def basic_sms_example():
    """Send a basic SMS message."""
    print("📱 Basic SMS Example")
    print("-" * 30)
    
    # Initialize the client
    client = Sendly(
        api_key=os.environ.get('SENDLY_API_KEY'),  # or pass directly: 'sl_test_...'
        # base_url='https://api.sendly.dev'  # Optional: use for testing
    )
    
    try:
        # Send a simple SMS
        response = client.sms.send(
            to='+14155552671',  # Destination phone number (E.164 format)
            text='Hello from Sendly Python SDK! 🚀'
        )
        
        print(f"✅ Message sent successfully!")
        print(f"   Message ID: {response.id}")
        print(f"   Status: {response.status}")
        print(f"   From: {response.from_}")
        print(f"   To: {response.to}")
        print(f"   Segments: {response.segments}")
        
        # Routing information
        if response.routing:
            print(f"   Routing: {response.routing.number_type} ({response.routing.coverage} coverage)")
        
        # Cost information
        if response.cost:
            print(f"   Cost: ${response.cost.amount} {response.cost.currency}")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
    except AuthenticationError as e:
        print(f"❌ Authentication Error: {e.message}")
    except RateLimitError as e:
        print(f"❌ Rate Limit Error: {e.message}")
        if e.retry_after:
            print(f"   Retry after: {e.retry_after} seconds")
    except APIError as e:
        print(f"❌ API Error: {e.message}")
        if e.status_code:
            print(f"   Status Code: {e.status_code}")
    except NetworkError as e:
        print(f"❌ Network Error: {e.message}")
    finally:
        client.close()
    
    print()

def mms_example():
    """Send an MMS message with media."""
    print("🖼️  MMS with Media Example")
    print("-" * 30)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    try:
        response = client.sms.send(
            to='+14155552671',
            text='Check out this awesome image! 📸',
            media_urls=[
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
                'https://images.unsplash.com/photo-1511593358241-7eea1f3c84e5?w=800'
            ],
            subject='Beautiful Landscapes'  # MMS subject line
        )
        
        print(f"✅ MMS sent successfully!")
        print(f"   Message ID: {response.id}")
        print(f"   Media Type: {response.media_type}")
        print(f"   Media URLs: {len(response.media_urls or [])} attachments")
        print(f"   Subject: {response.subject}")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
        # Common MMS validation errors:
        # - Invalid media URLs (must be HTTPS)
        # - Too many media files (max 10)
        # - Invalid URL format
    finally:
        client.close()
    
    print()

def advanced_sms_example():
    """Send SMS with advanced options."""
    print("⚙️  Advanced SMS Example")
    print("-" * 30)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    try:
        response = client.sms.send(
            to='+14155552671',
            text='Your verification code is: 123456',
            from_='+18005551234',  # Specific sender number
            message_type='otp',  # Message type for routing priority
            webhook_url='https://myapp.com/webhook/sms',  # Delivery notifications
            webhook_failover_url='https://myapp.com/webhook/backup',  # Backup webhook
            tags=['auth', 'verification', 'user-123']  # Analytics tags
        )
        
        print(f"✅ Advanced SMS sent successfully!")
        print(f"   Message ID: {response.id}")
        print(f"   Message Type: {response.message_type}")
        print(f"   Tags: {response.tags}")
        print(f"   Webhook URL: {response.webhook_url}")
        
        # Smart routing information
        if response.routing:
            print(f"   Routing Reason: {response.routing.reason}")
            print(f"   Country Code: {response.routing.country_code}")
            print(f"   Rate Limit: {response.routing.rate_limit}/minute")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
    finally:
        client.close()
    
    print()

def message_types_example():
    """Demonstrate different message types for smart routing."""
    print("🎯 Message Types & Smart Routing Example")
    print("-" * 45)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    message_types = [
        ('transactional', 'Your order #12345 has been shipped!'),
        ('otp', 'Your verification code: 567890'),
        ('marketing', 'Special offer: 50% off this weekend only! 🛍️'),
        ('alert', 'System maintenance scheduled for tonight at 2 AM'),
        ('promotional', 'New product launch - be the first to try it!')
    ]
    
    for msg_type, text in message_types:
        try:
            response = client.sms.send(
                to='+14155552671',
                text=text,
                message_type=msg_type
            )
            
            print(f"✅ {msg_type.title()} message sent")
            print(f"   ID: {response.id}")
            if response.routing:
                print(f"   Routing: {response.routing.reason} ({response.routing.number_type})")
            print()
            
        except Exception as e:
            print(f"❌ Failed to send {msg_type} message: {e}")
            print()
    
    client.close()

def error_handling_example():
    """Comprehensive error handling demonstration."""
    print("🚨 Error Handling Example")
    print("-" * 30)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    # Example 1: Validation Error
    print("1. Testing validation error...")
    try:
        client.sms.send(
            to='invalid-phone-number',  # Invalid format
            text='This will fail validation'
        )
    except ValidationError as e:
        print(f"   ✅ Caught validation error: {e.message}")
    
    # Example 2: Missing content
    print("2. Testing missing content...")
    try:
        client.sms.send(
            to='+14155552671'
            # Missing both text and media_urls
        )
    except ValidationError as e:
        print(f"   ✅ Caught validation error: {e.message}")
    
    # Example 3: Too many media URLs
    print("3. Testing too many media URLs...")
    try:
        client.sms.send(
            to='+14155552671',
            media_urls=['https://example.com/image.jpg'] * 11  # Max is 10
        )
    except ValidationError as e:
        print(f"   ✅ Caught validation error: {e.message}")
    
    # Example 4: Invalid webhook URL
    print("4. Testing invalid webhook URL...")
    try:
        client.sms.send(
            to='+14155552671',
            text='Test message',
            webhook_url='http://insecure-webhook.com'  # Must be HTTPS
        )
    except ValidationError as e:
        print(f"   ✅ Caught validation error: {e.message}")
    
    client.close()
    print()

def context_manager_example():
    """Demonstrate using the client as a context manager."""
    print("🔒 Context Manager Example")
    print("-" * 30)
    
    # Using context manager ensures proper cleanup
    with Sendly(api_key=os.environ.get('SENDLY_API_KEY')) as client:
        try:
            response = client.sms.send(
                to='+14155552671',
                text='Message sent using context manager! 🔄'
            )
            print(f"✅ Message sent: {response.id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Client is automatically closed here
    print("   🔒 Client automatically closed")
    print()

def international_example():
    """Send international messages."""
    print("🌍 International Messages Example")
    print("-" * 35)
    
    client = Sendly(api_key=os.environ.get('SENDLY_API_KEY'))
    
    international_numbers = [
        ('+447700900123', '🇬🇧 UK'),
        ('+33123456789', '🇫🇷 France'),
        ('+8613800138000', '🇨🇳 China'),
        ('+81312345678', '🇯🇵 Japan')
    ]
    
    for number, country in international_numbers:
        try:
            response = client.sms.send(
                to=number,
                text=f'Hello from Sendly Python SDK! Sent to {country}',
                message_type='transactional'
            )
            
            print(f"✅ Message sent to {country}")
            print(f"   Message ID: {response.id}")
            if response.routing:
                print(f"   Country Code: {response.routing.country_code}")
                print(f"   Coverage: {response.routing.coverage}")
            if response.cost:
                print(f"   Cost: ${response.cost.amount} {response.cost.currency}")
            print()
            
        except Exception as e:
            print(f"❌ Failed to send to {country}: {e}")
            print()
    
    client.close()

def main():
    """Run all examples."""
    print("🚀 Sendly Python SDK Examples")
    print("=" * 50)
    print()
    
    # Check for API key
    if not os.environ.get('SENDLY_API_KEY'):
        print("❌ Please set SENDLY_API_KEY environment variable")
        print("   export SENDLY_API_KEY='sl_test_your_api_key_here'")
        return
    
    # Run examples
    basic_sms_example()
    mms_example()
    advanced_sms_example()
    message_types_example()
    error_handling_example()
    context_manager_example()
    international_example()
    
    print("✨ All examples completed!")

if __name__ == '__main__':
    main()