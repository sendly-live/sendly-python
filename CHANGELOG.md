# Changelog

All notable changes to the Sendly Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2023-10-01

### Added
- Initial release of Sendly Python SDK
- Core SMS sending functionality with `client.sms.send()`
- MMS support with media attachments (up to 10 HTTPS URLs)
- Smart routing with message types (transactional, otp, marketing, alert, promotional)
- Comprehensive error handling with specific exception types:
  - `ValidationError` for request validation failures
  - `AuthenticationError` for invalid API keys
  - `RateLimitError` for rate limit exceeded
  - `APIError` for general API errors
  - `NetworkError` for network connectivity issues
- Automatic retry logic with exponential backoff for retryable errors
- Webhook support for delivery notifications with signature verification
- International messaging support with country-specific routing
- Tag-based analytics and message organization
- Context manager support for automatic resource cleanup
- Comprehensive type definitions with dataclasses
- Phone number validation and E.164 format enforcement
- Configurable HTTP client with custom timeouts and retry limits
- Thread-safe client implementation
- Extensive test coverage (90%+ coverage target)
- Detailed documentation and usage examples
- Support for Python 3.7+

### Features
- **SMS/MMS Sending**: Send text messages and multimedia messages
- **Smart Routing**: Automatic routing optimization based on message type and destination
- **Error Handling**: Robust error handling with automatic retries
- **Webhooks**: Real-time delivery notifications with security verification
- **International**: Global coverage with country-specific optimizations
- **Analytics**: Message tracking and organization with custom tags
- **Validation**: Client-side validation to prevent API errors
- **Performance**: HTTP connection pooling and automatic retry logic
- **Security**: API key validation and webhook signature verification

### Dependencies
- `requests` >= 2.25.0 for HTTP communication
- `typing_extensions` for Python 3.7 compatibility (if needed)

### Supported Message Types
- `transactional` - High-priority transactional messages
- `otp` - One-time passwords and verification codes  
- `marketing` - Marketing and promotional content
- `alert` - System alerts and notifications
- `promotional` - Sales and promotional announcements

### Supported Countries
- United States & Canada (toll-free and local numbers)
- United Kingdom (local routing)
- China (China-specific routing and compliance)
- 200+ additional countries with international routing

### Configuration Options
- Custom API endpoints for development/testing
- Configurable request timeouts (default: 30s)
- Adjustable retry limits (default: 3 attempts)
- Custom user agent strings
- Environment variable support for API keys

### Examples Included
- Basic SMS sending
- MMS with media attachments
- Advanced configuration options
- Error handling patterns
- Webhook integration
- Batch processing
- Performance monitoring
- International messaging

### Testing
- Comprehensive unit test suite
- Integration tests with mock API responses
- Error scenario testing
- Performance and concurrency testing
- 90%+ code coverage achieved

---

## Future Releases

### Planned for 0.2.0
- Async/await support with `asyncio`
- Message scheduling and delayed sending
- Bulk messaging APIs
- Enhanced analytics and reporting
- Message templates and personalization
- Two-way messaging support
- Number lookup and validation APIs

### Planned for 0.3.0
- WhatsApp Business API integration
- Rich messaging with interactive elements
- Advanced webhook management
- Message history and conversation tracking
- Enhanced international compliance features