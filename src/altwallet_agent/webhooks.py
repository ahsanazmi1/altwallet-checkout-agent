"""Webhook support for AltWallet Checkout Agent downstream events.

This module provides an async event emitter that can send JSON payloads to
configurable webhook URLs with retry logic, exponential backoff, and signed
payloads for verification.
"""

import asyncio
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel, Field, computed_field

from .logger import get_logger


class WebhookEventType(str, Enum):
    """Supported webhook event types."""

    AUTH_RESULT = "auth_result"
    SETTLEMENT = "settlement"
    CHARGEBACK = "chargeback"
    LOYALTY_EVENT = "loyalty_event"


class WebhookStatus(str, Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    url: str
    secret: str
    event_types: list[WebhookEventType] = field(default_factory=list)
    timeout: int = 30
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 60.0
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate webhook configuration."""
        if not self.url:
            raise ValueError("Webhook URL cannot be empty")

        try:
            urlparse(self.url)
        except Exception as e:
            raise ValueError(f"Invalid webhook URL: {e}")

        if not self.secret:
            raise ValueError("Webhook secret cannot be empty")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

        if self.retry_delay_base <= 0:
            raise ValueError("Retry delay base must be positive")

        if self.retry_delay_max <= 0:
            raise ValueError("Retry delay max must be positive")


class WebhookPayload(BaseModel):
    """Standard webhook payload structure."""

    event_type: WebhookEventType = Field(..., description="Type of event")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: float = Field(..., description="Event timestamp (Unix epoch)")
    data: dict[str, Any] = Field(..., description="Event-specific data")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def create(
        cls,
        event_type: WebhookEventType,
        data: dict[str, Any],
        event_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "WebhookPayload":
        """Create a webhook payload with auto-generated fields."""
        if event_id is None:
            import uuid

            event_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        return cls(
            event_type=event_type,
            event_id=event_id,
            timestamp=float(time.time()),
            data=data,
            metadata=metadata,
        )


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt record."""

    webhook_id: str = Field(..., description="Webhook endpoint identifier")
    event_id: str = Field(..., description="Event identifier")
    url: str = Field(..., description="Webhook URL")
    status: WebhookStatus = Field(..., description="Delivery status")
    attempt: int = Field(default=1, description="Attempt number")
    sent_at: float | None = Field(None, description="When sent")
    response_code: int | None = Field(None, description="HTTP response code")
    response_body: str | None = Field(None, description="Response body")
    error_message: str | None = Field(None, description="Error message")
    retry_after: float | None = Field(None, description="Next retry time")

    @computed_field
    def is_successful(self) -> bool:
        """Check if delivery was successful."""
        return self.status == WebhookStatus.SENT

    @computed_field
    def can_retry(self) -> bool:
        """Check if delivery can be retried."""
        return self.status in [WebhookStatus.FAILED, WebhookStatus.RETRYING]


class WebhookManager:
    """Manages webhook configurations and delivery."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.webhooks: dict[str, WebhookConfig] = {}
        self.delivery_history: list[WebhookDelivery] = []
        self.session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    async def add_webhook(self, webhook_id: str, config: WebhookConfig) -> None:
        """Add a webhook configuration."""
        async with self._lock:
            self.webhooks[webhook_id] = config
            self.logger.info(
                "Webhook added",
                webhook_id=webhook_id,
                url=config.url,
                event_types=[et.value for et in config.event_types],
            )

    async def remove_webhook(self, webhook_id: str) -> None:
        """Remove a webhook configuration."""
        async with self._lock:
            if webhook_id in self.webhooks:
                del self.webhooks[webhook_id]
                self.logger.info("Webhook removed", webhook_id=webhook_id)

    async def get_webhook(self, webhook_id: str) -> WebhookConfig | None:
        """Get webhook configuration by ID."""
        async with self._lock:
            return self.webhooks.get(webhook_id)

    async def list_webhooks(self) -> list[dict[str, Any]]:
        """List all webhook configurations."""
        async with self._lock:
            return [
                {
                    "webhook_id": wid,
                    "url": config.url,
                    "event_types": [et.value for et in config.event_types],
                    "enabled": config.enabled,
                    "max_retries": config.max_retries,
                }
                for wid, config in self.webhooks.items()
            ]

    async def start(self) -> None:
        """Start the webhook manager."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self.logger.info("Webhook manager started")

    async def stop(self) -> None:
        """Stop the webhook manager."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Webhook manager stopped")

    def _sign_payload(self, payload: bytes, secret: str) -> str:
        """Sign payload using HMAC-SHA256."""
        signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def _calculate_retry_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate retry delay with exponential backoff."""
        delay: float = base_delay * (2 ** (attempt - 1))
        return min(delay, max_delay)

    async def _send_webhook(
        self,
        webhook_id: str,
        config: WebhookConfig,
        payload: WebhookPayload,
        attempt: int = 1,
    ) -> WebhookDelivery:
        """Send webhook to a specific endpoint."""
        if not config.enabled:
            return WebhookDelivery(
                webhook_id=webhook_id,
                event_id=payload.event_id,
                url=config.url,
                status=WebhookStatus.FAILED,
                attempt=attempt,
                error_message="Webhook disabled",
                sent_at=float(time.time()),
                response_code=None,
                response_body=None,
                retry_after=None,
            )

        # Prepare payload
        payload_json = payload.model_dump_json()
        payload_bytes = payload_json.encode("utf-8")

        # Sign payload
        signature = self._sign_payload(payload_bytes, config.secret)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event-Type": payload.event_type.value,
            "X-Webhook-Event-ID": payload.event_id,
            "User-Agent": "AltWallet-Checkout-Agent/1.0",
        }

        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=payload.event_id,
            url=config.url,
            status=WebhookStatus.PENDING,
            attempt=attempt,
            sent_at=None,
            response_code=None,
            response_body=None,
            error_message=None,
            retry_after=None,
        )

        try:
            if self.session is None:
                raise RuntimeError("Webhook manager not started")

            # Send webhook
            async with self.session.post(
                config.url,
                data=payload_bytes,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config.timeout),
            ) as response:
                delivery.sent_at = float(time.time())
                delivery.response_code = response.status
                delivery.response_body = await response.text()

                if 200 <= response.status < 300:
                    delivery.status = WebhookStatus.SENT
                    self.logger.info(
                        "Webhook sent successfully",
                        webhook_id=webhook_id,
                        event_id=payload.event_id,
                        response_code=response.status,
                    )
                else:
                    delivery.status = WebhookStatus.FAILED
                    delivery.error_message = (
                        f"HTTP {response.status}: {delivery.response_body}"
                    )
                    self.logger.warning(
                        "Webhook failed",
                        webhook_id=webhook_id,
                        event_id=payload.event_id,
                        response_code=response.status,
                        response_body=delivery.response_body,
                    )

        except TimeoutError:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Request timeout"
            self.logger.warning(
                "Webhook timeout",
                webhook_id=webhook_id,
                event_id=payload.event_id,
                timeout=config.timeout,
            )

        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            self.logger.error(
                "Webhook error",
                webhook_id=webhook_id,
                event_id=payload.event_id,
                error=str(e),
                exc_info=True,
            )

        # Record delivery
        self.delivery_history.append(delivery)

        return delivery

    async def send_event(
        self,
        event_type: WebhookEventType,
        data: dict[str, Any],
        event_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[WebhookDelivery]:
        """Send event to all configured webhooks."""
        if self.session is None:
            raise RuntimeError("Webhook manager not started")

        # Create payload
        payload = WebhookPayload.create(
            event_type=event_type,
            data=data,
            event_id=event_id,
            metadata=metadata,
        )

        # Find webhooks for this event type
        target_webhooks = [
            (wid, config)
            for wid, config in self.webhooks.items()
            if not config.event_types or event_type in config.event_types
        ]

        if not target_webhooks:
            self.logger.info(
                "No webhooks configured for event type",
                event_type=event_type.value,
                event_id=payload.event_id,
            )
            return []

        # Send to all target webhooks
        deliveries = []
        for webhook_id, config in target_webhooks:
            delivery = await self._send_webhook(webhook_id, config, payload)
            deliveries.append(delivery)

            # Handle retries if needed
            if (
                delivery.status == WebhookStatus.FAILED
                and delivery.attempt < config.max_retries
            ):
                await self._schedule_retry(webhook_id, config, payload, delivery)

        return deliveries

    async def _schedule_retry(
        self,
        webhook_id: str,
        config: WebhookConfig,
        payload: WebhookPayload,
        failed_delivery: WebhookDelivery,
    ) -> None:
        """Schedule a retry for failed webhook delivery."""
        next_attempt = failed_delivery.attempt + 1
        delay = self._calculate_retry_delay(
            next_attempt, config.retry_delay_base, config.retry_delay_max
        )

        retry_delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=payload.event_id,
            url=config.url,
            status=WebhookStatus.RETRYING,
            attempt=next_attempt,
            sent_at=None,
            response_code=None,
            response_body=None,
            error_message=None,
            retry_after=float(time.time()) + delay,
        )

        self.delivery_history.append(retry_delivery)

        # Schedule retry
        asyncio.create_task(
            self._retry_webhook(webhook_id, config, payload, retry_delivery, delay)
        )

        self.logger.info(
            "Webhook retry scheduled",
            webhook_id=webhook_id,
            event_id=payload.event_id,
            attempt=next_attempt,
            delay=delay,
        )

    async def _retry_webhook(
        self,
        webhook_id: str,
        config: WebhookConfig,
        payload: WebhookPayload,
        retry_delivery: WebhookDelivery,
        delay: float,
    ) -> None:
        """Retry webhook delivery after delay."""
        await asyncio.sleep(delay)

        # Update retry delivery status
        retry_delivery.status = WebhookStatus.PENDING

        # Attempt delivery
        delivery = await self._send_webhook(
            webhook_id, config, payload, retry_delivery.attempt
        )

        # If still failed and more retries available, schedule another
        if (
            delivery.status == WebhookStatus.FAILED
            and retry_delivery.attempt < config.max_retries
        ):
            await self._schedule_retry(webhook_id, config, payload, delivery)

    async def get_delivery_history(
        self,
        webhook_id: str | None = None,
        event_id: str | None = None,
        status: WebhookStatus | None = None,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """Get webhook delivery history with optional filtering."""
        filtered = self.delivery_history

        if webhook_id:
            filtered = [d for d in filtered if d.webhook_id == webhook_id]

        if event_id:
            filtered = [d for d in filtered if d.event_id == event_id]

        if status:
            filtered = [d for d in filtered if d.status == status]

        # Sort by sent_at (most recent first) and limit results
        filtered.sort(key=lambda x: x.sent_at or 0, reverse=True)
        return filtered[:limit]

    async def clear_delivery_history(self, older_than_days: int = 30) -> int:
        """Clear old delivery history entries."""
        cutoff_time = float(time.time()) - (older_than_days * 24 * 60 * 60)

        async with self._lock:
            original_count = len(self.delivery_history)
            self.delivery_history = [
                d
                for d in self.delivery_history
                if d.sent_at and d.sent_at > cutoff_time
            ]
            removed_count = original_count - len(self.delivery_history)

        if removed_count > 0:
            self.logger.info(
                "Cleared old delivery history",
                removed_count=removed_count,
                older_than_days=older_than_days,
            )

        return removed_count


class WebhookEventEmitter:
    """High-level webhook event emitter for common use cases."""

    def __init__(self, webhook_manager: WebhookManager) -> None:
        self.webhook_manager = webhook_manager
        self.logger = get_logger(__name__)

    async def emit_auth_result(
        self,
        transaction_id: str,
        decision: str,
        score: float,
        metadata: dict[str, Any] | None = None,
    ) -> list[WebhookDelivery]:
        """Emit authentication result event."""
        data = {
            "transaction_id": transaction_id,
            "decision": decision,
            "score": score,
            "timestamp": float(time.time()),
        }

        if metadata:
            data.update(metadata)

        return await self.webhook_manager.send_event(WebhookEventType.AUTH_RESULT, data)

    async def emit_settlement(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[WebhookDelivery]:
        """Emit settlement event."""
        data = {
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "timestamp": float(time.time()),
        }

        if metadata:
            data.update(metadata)

        return await self.webhook_manager.send_event(WebhookEventType.SETTLEMENT, data)

    async def emit_chargeback(
        self,
        transaction_id: str,
        chargeback_id: str,
        reason: str,
        amount: float,
        metadata: dict[str, Any] | None = None,
    ) -> list[WebhookDelivery]:
        """Emit chargeback event."""
        data = {
            "transaction_id": transaction_id,
            "chargeback_id": chargeback_id,
            "reason": reason,
            "amount": amount,
            "timestamp": float(time.time()),
        }

        if metadata:
            data.update(metadata)

        return await self.webhook_manager.send_event(WebhookEventType.CHARGEBACK, data)

    async def emit_loyalty_event(
        self,
        customer_id: str,
        event_type: str,
        points_change: int,
        metadata: dict[str, Any] | None = None,
    ) -> list[WebhookDelivery]:
        """Emit loyalty event."""
        data = {
            "customer_id": customer_id,
            "event_type": event_type,
            "points_change": points_change,
            "timestamp": float(time.time()),
        }

        if metadata:
            data.update(metadata)

        return await self.webhook_manager.send_event(
            WebhookEventType.LOYALTY_EVENT, data
        )


# Global webhook manager instance
_webhook_manager: WebhookManager | None = None
_webhook_emitter: WebhookEventEmitter | None = None


async def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager instance."""
    global _webhook_manager

    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
        await _webhook_manager.start()

    return _webhook_manager


async def get_webhook_emitter() -> WebhookEventEmitter:
    """Get the global webhook event emitter instance."""
    global _webhook_emitter

    if _webhook_emitter is None:
        webhook_manager = await get_webhook_manager()
        _webhook_emitter = WebhookEventEmitter(webhook_manager)

    return _webhook_emitter


async def shutdown_webhooks() -> None:
    """Shutdown the global webhook manager."""
    global _webhook_manager, _webhook_emitter

    if _webhook_manager:
        await _webhook_manager.stop()
        _webhook_manager = None

    _webhook_emitter = None
