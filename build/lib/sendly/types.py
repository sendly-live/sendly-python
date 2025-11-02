"""Type definitions for the Sendly Python SDK."""

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any

# Message type enumeration
MessageType = Literal['transactional', 'marketing', 'otp', 'alert', 'promotional']


@dataclass
class SMSRequest:
    """Request parameters for sending an SMS/MMS message."""
    
    to: str
    text: Optional[str] = None
    from_: Optional[str] = None  # Use from_ to avoid Python keyword
    message_type: Optional[MessageType] = None
    media_urls: Optional[List[str]] = None
    subject: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_failover_url: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class RoutingInfo:
    """Smart routing information for a message."""
    
    number_type: str
    rate_limit: int
    coverage: str
    reason: str
    country_code: str


@dataclass
class CostInfo:
    """Cost information for a message."""
    
    amount: float
    currency: str


@dataclass
class SMSResponse:
    """Response from sending an SMS/MMS message."""
    
    id: str
    status: str
    from_: str  # Use from_ to avoid Python keyword
    to: str
    text: Optional[str]
    created_at: str
    segments: int
    cost: Optional[CostInfo]
    direction: str
    routing: RoutingInfo
    message_type: Optional[str] = None
    media_type: Optional[str] = None
    media_urls: Optional[List[str]] = None
    subject: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_failover_url: Optional[str] = None
    tags: Optional[List[str]] = None
    carrier: Optional[str] = None
    line_type: Optional[str] = None
    parts: Optional[int] = None
    encoding: Optional[str] = None
    media: Optional[List[Dict[str, Any]]] = None


@dataclass
class MessageSummary:
    """Summary information for a message."""
    
    id: str
    to: str
    from_: str
    text: Optional[str]
    status: str
    provider_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    api_key_name: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class PaginationInfo:
    """Pagination information for list responses."""
    
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


@dataclass
class MessageListResponse:
    """Response from listing messages."""
    
    success: bool
    data: List[MessageSummary]
    pagination: PaginationInfo


@dataclass
class StatsResponse:
    """Response from getting usage statistics."""
    
    success: bool
    data: Dict[str, Any]


@dataclass
class LiveStatsResponse:
    """Response from getting live statistics."""
    
    success: bool
    data: Dict[str, Any]


@dataclass
class RateLimitStatusResponse:
    """Response from getting rate limit status."""
    
    success: bool
    data: Dict[str, Any]