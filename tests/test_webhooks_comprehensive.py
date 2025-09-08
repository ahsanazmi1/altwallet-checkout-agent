"""Comprehensive tests for webhook module to improve coverage."""

import json
import time
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
import pytest_asyncio

from altwallet_agent.webhooks import (
    WebhookConfig,
    WebhookDelivery,
    WebhookEventEmitter,
    WebhookEventType,
    WebhookManager,
    WebhookPayload,
    WebhookStatus,
    get_webhook_emitter,
    get_webhook_manager,
    shutdown_webhooks,
)


class TestWebhookConfigValidation:
    """Test webhook configuration validation."""

    def test_webhook_config_empty_url(self):
        """Test webhook config with empty URL."""
        with pytest.raises(ValueError, match="Webhook URL cannot be empty"):
            WebhookConfig(url="", secret="test_secret")

    def test_webhook_config_invalid_url(self):
        """Test webhook config with invalid URL."""
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            WebhookConfig(url="http://[invalid-url", secret="test_secret")

    def test_webhook_config_empty_secret(self):
        """Test webhook config with empty secret."""
        with pytest.raises(ValueError, match="Webhook secret cannot be empty"):
            WebhookConfig(url="https://example.com/webhook", secret="")

    def test_webhook_config_negative_timeout(self):
        """Test webhook config with negative timeout."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            WebhookConfig(
                url="https://example.com/webhook", secret="test_secret", timeout=-1
            )

    def test_webhook_config_zero_timeout(self):
        """Test webhook config with zero timeout."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            WebhookConfig(
                url="https://example.com/webhook", secret="test_secret", timeout=0
            )

    def test_webhook_config_negative_max_retries(self):
        """Test webhook config with negative max retries."""
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            WebhookConfig(
                url="https://example.com/webhook", secret="test_secret", max_retries=-1
            )

    def test_webhook_config_negative_retry_delay_base(self):
        """Test webhook config with negative retry delay base."""
        with pytest.raises(ValueError, match="Retry delay base must be positive"):
            WebhookConfig(
                url="https://example.com/webhook",
                secret="test_secret",
                retry_delay_base=-1.0,
            )

    def test_webhook_config_zero_retry_delay_base(self):
        """Test webhook config with zero retry delay base."""
        with pytest.raises(ValueError, match="Retry delay base must be positive"):
            WebhookConfig(
                url="https://example.com/webhook",
                secret="test_secret",
                retry_delay_base=0.0,
            )

    def test_webhook_config_negative_retry_delay_max(self):
        """Test webhook config with negative retry delay max."""
        with pytest.raises(ValueError, match="Retry delay max must be positive"):
            WebhookConfig(
                url="https://example.com/webhook",
                secret="test_secret",
                retry_delay_max=-1.0,
            )

    def test_webhook_config_zero_retry_delay_max(self):
        """Test webhook config with zero retry delay max."""
        with pytest.raises(ValueError, match="Retry delay max must be positive"):
            WebhookConfig(
                url="https://example.com/webhook",
                secret="test_secret",
                retry_delay_max=0.0,
            )


class TestWebhookManagerLifecycle:
    """Test webhook manager lifecycle methods."""

    @pytest_asyncio.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_webhook_manager_start(self):
        """Test webhook manager start."""
        manager = WebhookManager()
        assert manager.session is None

        await manager.start()
        assert manager.session is not None
        assert isinstance(manager.session, aiohttp.ClientSession)

        await manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_webhook_manager_stop(self):
        """Test webhook manager stop."""
        manager = WebhookManager()
        await manager.start()
        assert manager.session is not None

        await manager.stop()
        assert manager.session is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_webhook_manager_double_start(self, webhook_manager):
        """Test webhook manager double start."""
        # Starting again should not create a new session
        original_session = webhook_manager.session
        await webhook_manager.start()
        assert webhook_manager.session is original_session

    @pytest.mark.asyncio
    async def test_webhook_manager_double_stop(self, webhook_manager):
        """Test webhook manager double stop."""
        await webhook_manager.stop()
        assert webhook_manager.session is None

        # Stopping again should not cause issues
        await webhook_manager.stop()
        assert webhook_manager.session is None


class TestWebhookManagerSendEvent:
    """Test webhook manager send event functionality."""

    @pytest_asyncio.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_send_event_manager_not_started(self):
        """Test send event when manager not started."""
        manager = WebhookManager()

        with pytest.raises(RuntimeError, match="Webhook manager not started"):
            await manager.send_event(WebhookEventType.AUTH_RESULT, {"test": "data"})

    @pytest.mark.asyncio
    async def test_send_event_no_webhooks_configured(self, webhook_manager):
        """Test send event with no webhooks configured."""
        deliveries = await webhook_manager.send_event(
            WebhookEventType.AUTH_RESULT, {"test": "data"}
        )

        assert deliveries == []

    @pytest.mark.asyncio
    async def test_send_event_webhook_disabled(self, webhook_manager):
        """Test send event to disabled webhook."""
        config = WebhookConfig(
            url="https://example.com/webhook", secret="test_secret", enabled=False
        )

        await webhook_manager.add_webhook("test_webhook", config)

        deliveries = await webhook_manager.send_event(
            WebhookEventType.AUTH_RESULT, {"test": "data"}
        )

        assert len(deliveries) == 1
        assert deliveries[0].status == WebhookStatus.FAILED
        assert deliveries[0].error_message == "Webhook disabled"

    @pytest.mark.asyncio
    async def test_send_event_webhook_event_type_filter(self, webhook_manager):
        """Test send event with event type filtering."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="test_secret",
            event_types=[WebhookEventType.SETTLEMENT],
        )

        await webhook_manager.add_webhook("test_webhook", config)

        # Send AUTH_RESULT event - should not be sent
        deliveries = await webhook_manager.send_event(
            WebhookEventType.AUTH_RESULT, {"test": "data"}
        )

        assert deliveries == []

        # Send SETTLEMENT event - should be sent
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            mock_post.return_value.__aenter__.return_value = mock_response

            deliveries = await webhook_manager.send_event(
                WebhookEventType.SETTLEMENT, {"test": "data"}
            )

            assert len(deliveries) == 1
            assert deliveries[0].status == WebhookStatus.SENT

    @pytest.mark.asyncio
    async def test_send_event_webhook_success(self, webhook_manager):
        """Test successful webhook send."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await webhook_manager.add_webhook("test_webhook", config)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            mock_post.return_value.__aenter__.return_value = mock_response

            deliveries = await webhook_manager.send_event(
                WebhookEventType.AUTH_RESULT, {"test": "data"}
            )

            assert len(deliveries) == 1
            delivery = deliveries[0]
            assert delivery.status == WebhookStatus.SENT
            assert delivery.response_code == 200
            assert delivery.response_body == "OK"
            assert delivery.sent_at is not None

    @pytest.mark.asyncio
    async def test_send_event_webhook_http_error(self, webhook_manager):
        """Test webhook send with HTTP error."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await webhook_manager.add_webhook("test_webhook", config)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response

            deliveries = await webhook_manager.send_event(
                WebhookEventType.AUTH_RESULT, {"test": "data"}
            )

            assert len(deliveries) == 1
            delivery = deliveries[0]
            assert delivery.status == WebhookStatus.FAILED
            assert delivery.response_code == 500
            assert delivery.response_body == "Internal Server Error"
            assert "HTTP 500" in delivery.error_message

    @pytest.mark.asyncio
    async def test_send_event_webhook_timeout(self, webhook_manager):
        """Test webhook send with timeout."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await webhook_manager.add_webhook("test_webhook", config)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = TimeoutError()

            deliveries = await webhook_manager.send_event(
                WebhookEventType.AUTH_RESULT, {"test": "data"}
            )

            assert len(deliveries) == 1
            delivery = deliveries[0]
            assert delivery.status == WebhookStatus.FAILED
            assert delivery.error_message == "Request timeout"

    @pytest.mark.asyncio
    async def test_send_event_webhook_general_exception(self, webhook_manager):
        """Test webhook send with general exception."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await webhook_manager.add_webhook("test_webhook", config)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")

            deliveries = await webhook_manager.send_event(
                WebhookEventType.AUTH_RESULT, {"test": "data"}
            )

            assert len(deliveries) == 1
            delivery = deliveries[0]
            assert delivery.status == WebhookStatus.FAILED
            assert delivery.error_message == "Connection error"


class TestWebhookManagerRetryLogic:
    """Test webhook manager retry logic."""

    @pytest_asyncio.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_retry_delay_calculation(self, webhook_manager):
        """Test retry delay calculation."""
        # Test exponential backoff
        delay1 = webhook_manager._calculate_retry_delay(1, 1.0, 60.0)
        delay2 = webhook_manager._calculate_retry_delay(2, 1.0, 60.0)
        delay3 = webhook_manager._calculate_retry_delay(3, 1.0, 60.0)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    @pytest.mark.asyncio
    async def test_retry_delay_max_limit(self, webhook_manager):
        """Test retry delay respects max limit."""
        delay = webhook_manager._calculate_retry_delay(10, 1.0, 60.0)
        assert delay == 60.0

    @pytest.mark.asyncio
    async def test_retry_scheduling(self, webhook_manager):
        """Test retry scheduling."""
        config = WebhookConfig(
            url="https://example.com/webhook", secret="test_secret", max_retries=2
        )

        await webhook_manager.add_webhook("test_webhook", config)

        # Create a failed delivery
        payload = WebhookPayload.create(WebhookEventType.AUTH_RESULT, {"test": "data"})
        failed_delivery = WebhookDelivery(
            webhook_id="test_webhook",
            event_id=payload.event_id,
            url=config.url,
            status=WebhookStatus.FAILED,
            attempt=1,
            sent_at=time.time(),
            response_code=500,
            response_body="Error",
            error_message="HTTP 500: Error",
        )

        # Schedule retry
        await webhook_manager._schedule_retry(
            "test_webhook", config, payload, failed_delivery
        )

        # Check that retry delivery was added to history
        assert len(webhook_manager.delivery_history) == 1
        retry_delivery = webhook_manager.delivery_history[0]
        assert retry_delivery.status == WebhookStatus.RETRYING
        assert retry_delivery.attempt == 2
        assert retry_delivery.retry_after is not None

    @pytest.mark.asyncio
    async def test_retry_webhook_success(self, webhook_manager):
        """Test retry webhook with success."""
        config = WebhookConfig(
            url="https://example.com/webhook", secret="test_secret", max_retries=2
        )

        await webhook_manager.add_webhook("test_webhook", config)

        payload = WebhookPayload.create(WebhookEventType.AUTH_RESULT, {"test": "data"})
        retry_delivery = WebhookDelivery(
            webhook_id="test_webhook",
            event_id=payload.event_id,
            url=config.url,
            status=WebhookStatus.RETRYING,
            attempt=2,
            retry_after=time.time() + 1.0,
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            mock_post.return_value.__aenter__.return_value = mock_response

            await webhook_manager._retry_webhook(
                "test_webhook", config, payload, retry_delivery, 0.0
            )

            # Check that retry delivery status was updated
            assert retry_delivery.status == WebhookStatus.PENDING

    @pytest.mark.asyncio
    async def test_retry_webhook_max_retries_exceeded(self, webhook_manager):
        """Test retry webhook when max retries exceeded."""
        config = WebhookConfig(
            url="https://example.com/webhook", secret="test_secret", max_retries=2
        )

        await webhook_manager.add_webhook("test_webhook", config)

        payload = WebhookPayload.create(WebhookEventType.AUTH_RESULT, {"test": "data"})
        retry_delivery = WebhookDelivery(
            webhook_id="test_webhook",
            event_id=payload.event_id,
            url=config.url,
            status=WebhookStatus.RETRYING,
            attempt=2,  # This is the max retry
            retry_after=time.time() + 1.0,
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Error")
            mock_post.return_value.__aenter__.return_value = mock_response

            await webhook_manager._retry_webhook(
                "test_webhook", config, payload, retry_delivery, 0.0
            )

            # Should have one delivery record (the failed retry)
            assert len(webhook_manager.delivery_history) == 1


class TestWebhookManagerDeliveryHistory:
    """Test webhook manager delivery history functionality."""

    @pytest_asyncio.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_delivery_history_all(self, webhook_manager):
        """Test get delivery history without filters."""
        # Add some test deliveries
        delivery1 = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time() - 100,
        )

        delivery2 = WebhookDelivery(
            webhook_id="webhook2",
            event_id="event2",
            url="https://example.com/webhook2",
            status=WebhookStatus.FAILED,
            attempt=1,
            sent_at=time.time() - 50,
        )

        webhook_manager.delivery_history = [delivery1, delivery2]

        history = await webhook_manager.get_delivery_history()

        assert len(history) == 2
        # Should be sorted by sent_at (most recent first)
        assert history[0].event_id == "event2"
        assert history[1].event_id == "event1"

    @pytest.mark.asyncio
    async def test_get_delivery_history_filter_by_webhook_id(self, webhook_manager):
        """Test get delivery history filtered by webhook ID."""
        delivery1 = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time(),
        )

        delivery2 = WebhookDelivery(
            webhook_id="webhook2",
            event_id="event2",
            url="https://example.com/webhook2",
            status=WebhookStatus.FAILED,
            attempt=1,
            sent_at=time.time(),
        )

        webhook_manager.delivery_history = [delivery1, delivery2]

        history = await webhook_manager.get_delivery_history(webhook_id="webhook1")

        assert len(history) == 1
        assert history[0].webhook_id == "webhook1"

    @pytest.mark.asyncio
    async def test_get_delivery_history_filter_by_event_id(self, webhook_manager):
        """Test get delivery history filtered by event ID."""
        delivery1 = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time(),
        )

        delivery2 = WebhookDelivery(
            webhook_id="webhook2",
            event_id="event2",
            url="https://example.com/webhook2",
            status=WebhookStatus.FAILED,
            attempt=1,
            sent_at=time.time(),
        )

        webhook_manager.delivery_history = [delivery1, delivery2]

        history = await webhook_manager.get_delivery_history(event_id="event2")

        assert len(history) == 1
        assert history[0].event_id == "event2"

    @pytest.mark.asyncio
    async def test_get_delivery_history_filter_by_status(self, webhook_manager):
        """Test get delivery history filtered by status."""
        delivery1 = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time(),
        )

        delivery2 = WebhookDelivery(
            webhook_id="webhook2",
            event_id="event2",
            url="https://example.com/webhook2",
            status=WebhookStatus.FAILED,
            attempt=1,
            sent_at=time.time(),
        )

        webhook_manager.delivery_history = [delivery1, delivery2]

        history = await webhook_manager.get_delivery_history(
            status=WebhookStatus.FAILED
        )

        assert len(history) == 1
        assert history[0].status == WebhookStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_delivery_history_limit(self, webhook_manager):
        """Test get delivery history with limit."""
        # Add multiple deliveries
        deliveries = []
        for i in range(5):
            delivery = WebhookDelivery(
                webhook_id=f"webhook{i}",
                event_id=f"event{i}",
                url=f"https://example.com/webhook{i}",
                status=WebhookStatus.SENT,
                attempt=1,
                sent_at=time.time() - i,
            )
            deliveries.append(delivery)

        webhook_manager.delivery_history = deliveries

        history = await webhook_manager.get_delivery_history(limit=3)

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_clear_delivery_history(self, webhook_manager):
        """Test clear delivery history."""
        # Add old and recent deliveries
        old_delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time() - (35 * 24 * 60 * 60),  # 35 days ago
        )

        recent_delivery = WebhookDelivery(
            webhook_id="webhook2",
            event_id="event2",
            url="https://example.com/webhook2",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time() - (5 * 24 * 60 * 60),  # 5 days ago
        )

        webhook_manager.delivery_history = [old_delivery, recent_delivery]

        removed_count = await webhook_manager.clear_delivery_history(older_than_days=30)

        assert removed_count == 1
        assert len(webhook_manager.delivery_history) == 1
        assert webhook_manager.delivery_history[0].event_id == "event2"

    @pytest.mark.asyncio
    async def test_clear_delivery_history_no_removals(self, webhook_manager):
        """Test clear delivery history with no removals."""
        recent_delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook1",
            status=WebhookStatus.SENT,
            attempt=1,
            sent_at=time.time() - (5 * 24 * 60 * 60),  # 5 days ago
        )

        webhook_manager.delivery_history = [recent_delivery]

        removed_count = await webhook_manager.clear_delivery_history(older_than_days=30)

        assert removed_count == 0
        assert len(webhook_manager.delivery_history) == 1


class TestWebhookEventEmitterComprehensive:
    """Test webhook event emitter comprehensive functionality."""

    @pytest_asyncio.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    @pytest_asyncio.fixture
    def webhook_emitter(self, webhook_manager):
        """Create a webhook event emitter for testing."""
        return WebhookEventEmitter(webhook_manager)

    @pytest.mark.asyncio
    async def test_emit_auth_result_with_metadata(self, webhook_emitter):
        """Test emit auth result with metadata."""
        with patch.object(webhook_emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await webhook_emitter.emit_auth_result(
                transaction_id="txn_123",
                decision="APPROVE",
                score=0.85,
                metadata={"custom_field": "custom_value"},
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.AUTH_RESULT
            data = call_args[0][1]
            assert data["transaction_id"] == "txn_123"
            assert data["decision"] == "APPROVE"
            assert data["score"] == 0.85
            assert data["custom_field"] == "custom_value"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_emit_settlement_with_metadata(self, webhook_emitter):
        """Test emit settlement with metadata."""
        with patch.object(webhook_emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await webhook_emitter.emit_settlement(
                transaction_id="txn_123",
                amount=100.50,
                currency="USD",
                status="COMPLETED",
                metadata={"settlement_id": "settle_456"},
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.SETTLEMENT
            data = call_args[0][1]
            assert data["transaction_id"] == "txn_123"
            assert data["amount"] == 100.50
            assert data["currency"] == "USD"
            assert data["status"] == "COMPLETED"
            assert data["settlement_id"] == "settle_456"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_emit_chargeback_with_metadata(self, webhook_emitter):
        """Test emit chargeback with metadata."""
        with patch.object(webhook_emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await webhook_emitter.emit_chargeback(
                transaction_id="txn_123",
                chargeback_id="cb_789",
                reason="FRAUD",
                amount=100.50,
                metadata={"dispute_id": "dispute_123"},
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.CHARGEBACK
            data = call_args[0][1]
            assert data["transaction_id"] == "txn_123"
            assert data["chargeback_id"] == "cb_789"
            assert data["reason"] == "FRAUD"
            assert data["amount"] == 100.50
            assert data["dispute_id"] == "dispute_123"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_emit_loyalty_event_with_metadata(self, webhook_emitter):
        """Test emit loyalty event with metadata."""
        with patch.object(webhook_emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await webhook_emitter.emit_loyalty_event(
                customer_id="cust_123",
                event_type="POINTS_EARNED",
                points_change=100,
                metadata={"campaign_id": "campaign_456"},
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.LOYALTY_EVENT
            data = call_args[0][1]
            assert data["customer_id"] == "cust_123"
            assert data["event_type"] == "POINTS_EARNED"
            assert data["points_change"] == 100
            assert data["campaign_id"] == "campaign_456"
            assert "timestamp" in data


class TestWebhookPayloadComprehensive:
    """Test webhook payload comprehensive functionality."""

    def test_webhook_payload_create_with_custom_id(self):
        """Test webhook payload creation with custom event ID."""
        payload = WebhookPayload.create(
            event_type=WebhookEventType.AUTH_RESULT,
            data={"test": "data"},
            event_id="custom_event_123",
            metadata={"custom": "metadata"},
        )

        assert payload.event_type == WebhookEventType.AUTH_RESULT
        assert payload.event_id == "custom_event_123"
        assert payload.data == {"test": "data"}
        assert payload.metadata == {"custom": "metadata"}
        assert payload.timestamp > 0

    def test_webhook_payload_create_with_none_metadata(self):
        """Test webhook payload creation with None metadata."""
        payload = WebhookPayload.create(
            event_type=WebhookEventType.AUTH_RESULT,
            data={"test": "data"},
            metadata=None,
        )

        assert payload.metadata == {}

    def test_webhook_payload_model_dump_json(self):
        """Test webhook payload JSON serialization."""
        payload = WebhookPayload.create(
            event_type=WebhookEventType.AUTH_RESULT, data={"test": "data"}
        )

        json_str = payload.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "auth_result"
        assert data["data"] == {"test": "data"}
        assert "event_id" in data
        assert "timestamp" in data
        assert "metadata" in data


class TestWebhookDeliveryComprehensive:
    """Test webhook delivery comprehensive functionality."""

    def test_webhook_delivery_computed_fields_success(self):
        """Test webhook delivery computed fields for success."""
        delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook",
            status=WebhookStatus.SENT,
            attempt=1,
        )

        assert delivery.is_successful is True
        assert delivery.can_retry is False

    def test_webhook_delivery_computed_fields_failed(self):
        """Test webhook delivery computed fields for failed."""
        delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook",
            status=WebhookStatus.FAILED,
            attempt=1,
        )

        assert delivery.is_successful is False
        assert delivery.can_retry is True

    def test_webhook_delivery_computed_fields_retrying(self):
        """Test webhook delivery computed fields for retrying."""
        delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook",
            status=WebhookStatus.RETRYING,
            attempt=2,
        )

        assert delivery.is_successful is False
        assert delivery.can_retry is True

    def test_webhook_delivery_computed_fields_pending(self):
        """Test webhook delivery computed fields for pending."""
        delivery = WebhookDelivery(
            webhook_id="webhook1",
            event_id="event1",
            url="https://example.com/webhook",
            status=WebhookStatus.PENDING,
            attempt=1,
        )

        assert delivery.is_successful is False
        assert delivery.can_retry is False


class TestGlobalWebhookFunctions:
    """Test global webhook functions."""

    @pytest.mark.asyncio
    async def test_get_webhook_manager_singleton(self):
        """Test get webhook manager returns singleton."""
        manager1 = await get_webhook_manager()
        manager2 = await get_webhook_manager()

        assert manager1 is manager2

        await shutdown_webhooks()

    @pytest.mark.asyncio
    async def test_get_webhook_emitter_singleton(self):
        """Test get webhook emitter returns singleton."""
        emitter1 = await get_webhook_emitter()
        emitter2 = await get_webhook_emitter()

        assert emitter1 is emitter2

        await shutdown_webhooks()

    @pytest.mark.asyncio
    async def test_shutdown_webhooks_resets_singletons(self):
        """Test shutdown webhooks resets singletons."""
        manager1 = await get_webhook_manager()
        emitter1 = await get_webhook_emitter()

        await shutdown_webhooks()

        manager2 = await get_webhook_manager()
        emitter2 = await get_webhook_emitter()

        # Should be new instances
        assert manager1 is not manager2
        assert emitter1 is not emitter2

        await shutdown_webhooks()
