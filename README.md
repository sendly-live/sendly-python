# Sendly Python SDK

[![PyPI version](https://badge.fury.io/py/sendly.svg)](https://badge.fury.io/py/sendly)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [Sendly](https://sendly.live) - SMS for developers.

## Installation

```bash
pip install sendly
```

## Quick Start

```python
from sendly import Sendly

# Initialize the client
client = Sendly(api_key='sl_test_your_api_key_here')

# Send an SMS
response = client.sms.send(
    to='+14155552671',
    text='Hello from Sendly!'
)

print(f"Message sent! ID: {response.id}")
```

## Features

- **Instant setup** - From pip install to first SMS in under 2 minutes
- **Smart routing** - Automatic number selection for optimal delivery
- **Type hints** - Full typing support throughout
- **Auto-retry** - Exponential backoff for failed requests
- **Context managers** - Pythonic resource management
- **Error handling** - Comprehensive exception types

## Authentication

Get your API key from the [Sendly Dashboard](https://dashboard.sendly.live).

### Environment Variable (Recommended)

```bash
export SENDLY_API_KEY="sl_test_your_api_key_here"
```

```python
from sendly import Sendly

# API key automatically loaded from environment
client = Sendly()
```

### Direct Initialization

```python
client = Sendly(api_key='sl_test_your_api_key_here')
```

### Custom Configuration

```python
client = Sendly(
    api_key='sl_test_your_api_key_here',
    base_url='https://api.sendly.live',
    timeout=30.0,
    max_retries=3
)
```

## Basic Usage

### Send SMS

```python
response = client.sms.send(
    to='+14155552671',
    text='Hello from Sendly!'
)

print(f"Message ID: {response.id}")
print(f"Status: {response.status}")
print(f"From: {response.from_}")
print(f"Cost: ${response.cost.amount}")
```

### Message Types

```python
# Transactional messages
client.sms.send(
    to='+14155552671',
    text='Your order #12345 has shipped!',
    message_type='transactional'
)

# OTP/Verification messages
client.sms.send(
    to='+14155552671',
    text='Your verification code: 123456',
    message_type='otp'
)

# Marketing messages
client.sms.send(
    to='+14155552671',
    text='50% off sale this weekend!',
    message_type='marketing'
)
```

### Context Manager (Recommended)

```python
with Sendly(api_key='sl_test_your_api_key_here') as client:
    response = client.sms.send(
        to='+14155552671',
        text='Hello from Sendly!'
    )
```

## Advanced Features

### Webhooks

```python
response = client.sms.send(
    to='+14155552671',
    text='Your verification code: 789012',
    webhook_url='https://myapp.com/webhook/sms',
    webhook_failover_url='https://myapp.com/webhook/backup'
)
```

### Tags

```python
response = client.sms.send(
    to='+14155552671',
    text='Welcome to our platform!',
    tags=['onboarding', 'welcome', 'user-123']
)
```

### Batch Processing

```python
import time

recipients = [
    {'phone': '+14155552671', 'name': 'Alice'},
    {'phone': '+14155552672', 'name': 'Bob'},
    {'phone': '+14155552673', 'name': 'Charlie'}
]

for recipient in recipients:
    try:
        response = client.sms.send(
            to=recipient['phone'],
            text=f"Hello {recipient['name']}!",
            tags=['batch', f"user-{recipient['name'].lower()}"]
        )
        print(f"Sent to {recipient['name']}: {response.id}")
    except Exception as e:
        print(f"Failed to send to {recipient['name']}: {e}")
    
    time.sleep(0.1)
```

## Error Handling

```python
from sendly.errors import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError
)

try:
    response = client.sms.send(
        to='+14155552671',
        text='Hello Sendly!'
    )
except ValidationError as e:
    print(f"Validation error: {e.message}")
except AuthenticationError as e:
    print(f"Authentication error: {e.message}")
except RateLimitError as e:
    print(f"Rate limit error: {e.message}")
    if e.retry_after:
        print(f"Retry after: {e.retry_after} seconds")
except APIError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")
```

## Sandbox Testing

Use test API keys for development. The sandbox provides magic numbers for testing different scenarios:

### Success Scenarios

| Phone Number | Behavior |
|--------------|----------|
| `+15550001234` | Instant delivery |
| `+15550001010` | 10 second delay |
| `+15550001030` | 30 second delay |

### Error Scenarios

| Phone Number | Error Type | HTTP Status |
|--------------|------------|-------------|
| `+15550009999` | Invalid number | 400 |
| `+15550009998` | Carrier rejection | 400 |
| `+15550009997` | Rate limit exceeded | 429 |
| `+15550009996` | Timeout error | 500 |

Example:

```python
from sendly import Sendly
from sendly.errors import RateLimitError

# Initialize with test API key
client = Sendly(api_key='sl_test_YOUR_TEST_KEY')

# Test instant success
response = client.sms.send(
    to='+15550001234',
    text='Testing instant delivery'
)
print(f"Success: {response.status}")

# Test rate limit error
try:
    response = client.sms.send(
        to='+15550009997',
        text='Testing rate limit'
    )
except RateLimitError as e:
    print(f"Rate limit error: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
```

## API Reference

### Client Initialization

```python
Sendly(
    api_key: str = None,
    base_url: str = "https://api.sendly.live",
    timeout: float = 30.0,
    max_retries: int = 3
)
```

### SMS Methods

#### `client.sms.send()`

```python
client.sms.send(
    to: str,
    text: str,
    from_: str = None,
    message_type: str = None,
    webhook_url: str = None,
    webhook_failover_url: str = None,
    tags: List[str] = None
) -> SMSResponse
```

**Parameters:**
- `to` - Destination phone number (E.164 format)
- `text` - Message text (required)
- `from_` - Sender number (auto-selected if not provided)
- `message_type` - Message type: `transactional`, `otp`, `marketing`, `alert`
- `webhook_url` - HTTPS webhook URL for delivery notifications
- `webhook_failover_url` - HTTPS backup webhook URL
- `tags` - Message tags for analytics (max 20, 50 chars each)

### Response Objects

#### `SMSResponse`

```python
class SMSResponse:
    id: str
    status: str
    from_: str
    to: str
    text: str
    created_at: str
    segments: int
    cost: CostInfo
    routing: RoutingInfo
```

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=sendly --cov-report=html
```

## Development

```bash
# Clone the repository
git clone https://github.com/sendly-live/sendly-python.git
cd sendly-python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 sendly/
black sendly/
isort sendly/
```

## License

MIT

## Support

- Email: [support@sendly.live](mailto:support@sendly.live)
- Documentation: [https://docs.sendly.live](https://docs.sendly.live)
- Issues: [GitHub Issues](https://github.com/sendly-live/sendly-python/issues)
