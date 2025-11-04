"""Sendly Python SDK - Send SMS with ease.

The official Python SDK for the Sendly SMS API.
"""

from .client import Sendly
from .errors import (
    SendlyError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NetworkError,
)
from .types import (
    MessageType,
    SMSRequest,
    SMSResponse,
    RoutingInfo,
    CostInfo,
    MessageSummary,
    PaginationInfo,
    MessageListResponse,
    StatsResponse,
    LiveStatsResponse,
    RateLimitStatusResponse,
)
from .constants import (
    MAGIC_NUMBERS,
    MAGIC_NUMBER_INFO,
    is_magic_number,
    get_magic_number_info,
    get_magic_numbers_by_category,
    get_error_magic_numbers,
    get_success_magic_numbers,
)

__version__ = "0.1.2"
__author__ = "Sendly Team"
__email__ = "support@sendly.live"

__all__ = [
    # Main client
    'Sendly',

    # Exceptions
    'SendlyError',
    'ValidationError',
    'AuthenticationError',
    'RateLimitError',
    'APIError',
    'NetworkError',

    # Types
    'MessageType',
    'SMSRequest',
    'SMSResponse',
    'RoutingInfo',
    'CostInfo',
    'MessageSummary',
    'PaginationInfo',
    'MessageListResponse',
    'StatsResponse',
    'LiveStatsResponse',
    'RateLimitStatusResponse',

    # Sandbox constants and utilities
    'MAGIC_NUMBERS',
    'MAGIC_NUMBER_INFO',
    'is_magic_number',
    'get_magic_number_info',
    'get_magic_numbers_by_category',
    'get_error_magic_numbers',
    'get_success_magic_numbers',
]
