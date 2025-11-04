"""SMS resource for the Sendly Python SDK."""

from typing import Dict, List, Optional

from ..types import SMSRequest, SMSResponse, CostInfo, RoutingInfo
from ..utils.validation import validate_sms_request
from ..utils.http_client import HttpClient


class SMS:
    """SMS resource for sending messages."""

    def __init__(self, http_client: HttpClient):
        """Initialize SMS resource.

        Args:
            http_client: HTTP client instance
        """
        self._http_client = http_client

    def send(
        self,
        to: str,
        text: Optional[str] = None,
        from_: Optional[str] = None,
        message_type: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        subject: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_failover_url: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> SMSResponse:
        """Send an SMS/MMS message.

        Args:
            to: Destination phone number in E.164 format
            text: Message text (optional for MMS-only messages)
            from_: Sender phone number (optional - auto-selected if not provided)
            message_type: Message type for routing priority
            media_urls: HTTPS URLs for MMS media (max 10)
            subject: MMS subject line
            webhook_url: HTTPS webhook URL for delivery notifications
            webhook_failover_url: HTTPS backup webhook URL
            tags: Message tags for analytics (max 20, 50 chars each)

        Returns:
            SMS response with message details and routing info

        Raises:
            ValidationError: If request validation fails
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limits are exceeded
            APIError: For other API errors
            NetworkError: For network-related errors
        """
        # Create request object
        request = SMSRequest(
            to=to,
            text=text,
            from_=from_,
            message_type=message_type,
            media_urls=media_urls,
            subject=subject,
            webhook_url=webhook_url,
            webhook_failover_url=webhook_failover_url,
            tags=tags
        )

        # Validate request
        validate_sms_request(request)

        # Prepare payload for API
        payload = self._build_payload(request)

        # Make API request
        response_data = self._http_client.post('/v1/send', payload)

        # Transform response
        return self._transform_response(response_data)

    def _build_payload(self, request: SMSRequest) -> Dict[str, any]:
        """Build API payload from request.

        Args:
            request: SMS request object

        Returns:
            Dictionary payload for API request
        """
        payload = {
            'to': request.to,
            'messageType': request.message_type or 'transactional'
        }

        if request.text:
            payload['text'] = request.text

        if request.from_:
            payload['from'] = request.from_

        if request.media_urls:
            payload['media_urls'] = request.media_urls

        if request.subject:
            payload['subject'] = request.subject

        if request.webhook_url:
            payload['webhook_url'] = request.webhook_url

        if request.webhook_failover_url:
            payload['webhook_failover_url'] = request.webhook_failover_url

        if request.tags:
            payload['tags'] = request.tags

        return payload

    def _transform_response(self, data: Dict[str, any]) -> SMSResponse:
        """Transform API response to SMSResponse object.

        Args:
            data: Raw API response data

        Returns:
            Structured SMS response object
        """
        # Extract routing info (if present)
        routing_data = data.get('routing', {})
        routing = None
        if routing_data:
            routing = RoutingInfo(
                number_type=routing_data.get('numberType', ''),
                rate_limit=routing_data.get('rateLimit', 0),
                coverage=routing_data.get('coverage', ''),
                reason=routing_data.get('reason', ''),
                country_code=routing_data.get('countryCode', '')
            )

        # Extract cost (API can return string "$0.00", number 0, or dict)
        cost_data = data.get('cost', 0)
        cost = None
        if isinstance(cost_data, str):
            # Parse cost string (e.g., "$0.00" -> 0.0)
            cost_value = float(cost_data.replace('$', '').replace(',', ''))
            cost = CostInfo(amount=cost_value, currency='USD')
        elif isinstance(cost_data, (int, float)):
            # Handle numeric cost (e.g., 0 or 0.01)
            cost = CostInfo(amount=float(cost_data), currency='USD')
        elif isinstance(cost_data, dict):
            # Handle dict format
            cost = CostInfo(
                amount=cost_data.get('amount', 0.0),
                currency=cost_data.get('currency', 'USD')
            )

        # Create response object
        return SMSResponse(
            id=data.get('id', data.get('messageId', '')),
            status=data.get('status', ''),
            from_=data.get('from', ''),
            to=data.get('to', ''),
            text=data.get('text'),
            created_at=data.get('created_at', data.get('timestamp', '')),
            segments=data.get('segments', 1),
            cost=cost,
            direction=data.get('direction', 'outbound'),
            routing=routing,
            message_type=data.get('messageType'),
            media_type=data.get('mediaType'),
            media_urls=data.get('media_urls'),
            subject=data.get('subject'),
            webhook_url=data.get('webhook_url'),
            webhook_failover_url=data.get('webhook_failover_url'),
            tags=data.get('tags'),
            carrier=data.get('carrier'),
            line_type=data.get('lineType'),
            parts=data.get('parts'),
            encoding=data.get('encoding'),
            media=data.get('media')
        )
