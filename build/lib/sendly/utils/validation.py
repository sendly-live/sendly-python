"""Validation utilities for the Sendly Python SDK."""

import re
from typing import List, Optional
from urllib.parse import urlparse

from ..errors import ValidationError
from ..types import SMSRequest, MessageType


def is_valid_phone_number(phone: str) -> bool:
    """Validate E.164 phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if phone number is valid E.164 format
    """
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))


def is_valid_api_key(api_key: str) -> bool:
    """Validate Sendly API key format.

    Args:
        api_key: API key to validate

    Returns:
        True if API key has valid format
    """
    pattern = r'^sl_(test|live)_[a-zA-Z0-9_-]{24,50}$'
    return bool(re.match(pattern, api_key))


def is_valid_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_country_code(phone_number: str) -> str:
    """Extract country code from phone number.

    Args:
        phone_number: Phone number in E.164 format

    Returns:
        Country code as string
    """
    clean_number = re.sub(r'[^\d]', '', phone_number)

    if clean_number.startswith('1'):
        return '1'  # US/Canada
    elif clean_number.startswith('44'):
        return '44'  # UK
    elif clean_number.startswith('33'):
        return '33'  # France
    elif clean_number.startswith('86'):
        return '86'  # China

    # Common two-digit country codes
    two_digit_codes = [
        '27', '34', '39', '41', '43', '45', '46', '47', '48',
        '81', '82', '91', '92', '93', '94', '95'
    ]

    if len(clean_number) >= 10:
        two_digit = clean_number[:2]
        if two_digit in two_digit_codes:
            return two_digit

    return 'unknown'


def is_toll_free(phone_number: str) -> bool:
    """Check if phone number is toll-free.

    Args:
        phone_number: Phone number to check

    Returns:
        True if number is toll-free
    """
    clean_number = re.sub(r'[^\d]', '', phone_number)
    return bool(re.match(r'^1(800|833|844|855|866|877|888)', clean_number))


def validate_toll_free_routing(from_number: str, to_number: str) -> None:
    """Validate toll-free can send to destination.

    Args:
        from_number: Sender number
        to_number: Destination number

    Raises:
        ValidationError: If toll-free number cannot send to international destination
    """
    if is_toll_free(from_number):
        country_code = get_country_code(to_number)
        if country_code != '1':
            raise ValidationError(
                f'Toll-free number {from_number} cannot send to international '
                f'destination {to_number}. Toll-free numbers only support US/Canada.'
            )


def validate_sms_request(request: SMSRequest) -> None:
    """Validate SMS request parameters.

    Args:
        request: SMS request to validate

    Raises:
        ValidationError: If any validation fails
    """
    # Validate required fields
    if not request.to:
        raise ValidationError('to is required')

    if not request.text and not request.media_urls:
        raise ValidationError('Either text or media_urls must be provided')

    # Validate phone numbers
    if not is_valid_phone_number(request.to):
        raise ValidationError('Invalid phone number format for to')

    if request.from_ and not is_valid_phone_number(request.from_):
        raise ValidationError('Invalid phone number format for from_')

    # Validate toll-free routing if from_ is specified
    if request.from_:
        validate_toll_free_routing(request.from_, request.to)

    # Validate media URLs
    if request.media_urls:
        if len(request.media_urls) > 10:
            raise ValidationError('Maximum 10 media URLs allowed')

        for url in request.media_urls:
            if not url or not url.strip():
                raise ValidationError('Media URLs cannot be empty')

            if not is_valid_url(url):
                raise ValidationError('Invalid URL format in media_urls')

            if not url.startswith('https://'):
                raise ValidationError('Media URLs must use HTTPS')

    # Validate webhook URLs
    if request.webhook_url:
        if not is_valid_url(request.webhook_url):
            raise ValidationError('Invalid webhook URL format')

        if not request.webhook_url.startswith('https://'):
            raise ValidationError('Webhook URL must use HTTPS')

    if request.webhook_failover_url:
        if not is_valid_url(request.webhook_failover_url):
            raise ValidationError('Invalid webhook failover URL format')

        if not request.webhook_failover_url.startswith('https://'):
            raise ValidationError('Webhook failover URL must use HTTPS')

    # Validate tags
    if request.tags:
        if len(request.tags) > 20:
            raise ValidationError('Maximum 20 tags allowed')

        for tag in request.tags:
            if not tag or not tag.strip():
                raise ValidationError('Tags cannot be empty')

            if len(tag) > 50:
                raise ValidationError('Tag length cannot exceed 50 characters')

    # Validate message type
    if request.message_type:
        valid_types = ['transactional', 'marketing', 'otp', 'alert', 'promotional']
        if request.message_type not in valid_types:
            raise ValidationError(
                f'Invalid message_type. Must be one of: {", ".join(valid_types)}'
            )
