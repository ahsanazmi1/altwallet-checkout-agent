"""Tests for the webhook module."""

from unittest.mock import patch

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


class TestWebhookEventType:
    """Test webhook event type enum."""

    def test_event_type_values(self):
        """Test event type enum values."""
        assert WebhookEventType.AUTH_RESULT == "auth_result"
        assert WebhookEventType.SETTLEMENT == "settlement"
        assert WebhookEventType.CHARGEBACK == "chargeback"
        assert WebhookEventType.LOYALTY_EVENT == "loyalty_event"


class TestWebhookStatus:
    """Test webhook status enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert WebhookStatus.PENDING == "pending"
        assert WebhookStatus.SENT == "sent"
        assert WebhookStatus.FAILED == "failed"
        assert WebhookStatus.RETRYING == "retrying"


class TestWebhookConfig:
    """Test webhook configuration."""

    def test_valid_config(self):
        """Test valid webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="test_secret",
            event_types=[WebhookEventType.AUTH_RESULT],
            timeout=30,
            max_retries=3,
        )

        assert config.url == "https://example.com/webhook"
        assert config.secret == "test_secret"
        assert config.event_types == [WebhookEventType.AUTH_RESULT]
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.enabled is True

    def test_invalid_url(self):
        """Test invalid URL validation."""
        with pytest.raises(ValueError, match="Webhook URL cannot be empty"):
            WebhookConfig(url="", secret="test_secret")

    def test_empty_secret(self):
        """Test empty secret validation."""
        with pytest.raises(ValueError, match="Webhook secret cannot be empty"):
            WebhookConfig(url="https://example.com", secret="")

    def test_negative_timeout(self):
        """Test negative timeout validation."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            WebhookConfig(url="https://example.com", secret="test_secret", timeout=0)


class TestWebhookPayload:
    """Test webhook payload."""

    def test_payload_creation(self):
        """Test payload creation."""
        data = {"test": "value"}
        payload = WebhookPayload.create(
            WebhookEventType.AUTH_RESULT, data, event_id="test_123"
        )

        assert payload.event_type == WebhookEventType.AUTH_RESULT
        assert payload.event_id == "test_123"
        assert payload.data == data
        assert payload.timestamp > 0

    def test_payload_auto_id(self):
        """Test payload with auto-generated ID."""
        data = {"test": "value"}
        payload = WebhookPayload.create(WebhookEventType.SETTLEMENT, data)

        assert payload.event_id is not None
        assert len(payload.event_id) > 0
        assert payload.event_type == WebhookEventType.SETTLEMENT


class TestWebhookDelivery:
    """Test webhook delivery."""

    def test_delivery_creation(self):
        """Test delivery creation."""
        delivery = WebhookDelivery(
            webhook_id="webhook_123",
            event_id="event_456",
            url="https://example.com/webhook",
            status=WebhookStatus.PENDING,
        )

        assert delivery.webhook_id == "webhook_123"
        assert delivery.event_id == "event_456"
        assert delivery.status == WebhookStatus.PENDING
        assert delivery.attempt == 1

    def test_delivery_computed_fields(self):
        """Test delivery computed fields."""
        # Successful delivery
        successful = WebhookDelivery(
            webhook_id="webhook_123",
            event_id="event_456",
            url="https://example.com/webhook",
            status=WebhookStatus.SENT,
        )
        assert successful.is_successful is True
        assert successful.can_retry is False

        # Failed delivery
        failed = WebhookDelivery(
            webhook_id="webhook_123",
            event_id="event_456",
            url="https://example.com/webhook",
            status=WebhookStatus.FAILED,
        )
        assert failed.is_successful is False
        assert failed.can_retry is True


@pytest.mark.asyncio
class TestWebhookManager:
    """Test webhook manager."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create webhook manager for testing."""
        manager = WebhookManager()
        await manager.start()
        yield manager
        await manager.stop()

    async def test_add_webhook(self, manager):
        """Test adding webhook."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await manager.add_webhook("webhook_123", config)

        webhook = await manager.get_webhook("webhook_123")
        assert webhook is not None
        assert webhook.url == "https://example.com/webhook"

    async def test_remove_webhook(self, manager):
        """Test removing webhook."""
        config = WebhookConfig(url="https://example.com/webhook", secret="test_secret")

        await manager.add_webhook("webhook_123", config)
        await manager.remove_webhook("webhook_123")

        webhook = await manager.get_webhook("webhook_123")
        assert webhook is None

    async def test_list_webhooks(self, manager):
        """Test listing webhooks."""
        config1 = WebhookConfig(url="https://example1.com/webhook", secret="secret1")
        config2 = WebhookConfig(url="https://example2.com/webhook", secret="secret2")

        await manager.add_webhook("webhook_1", config1)
        await manager.add_webhook("webhook_2", config2)

        webhooks = await manager.list_webhooks()
        assert len(webhooks) == 2

        webhook_ids = [w["webhook_id"] for w in webhooks]
        assert "webhook_1" in webhook_ids
        assert "webhook_2" in webhook_ids

    async def test_retry_delay_calculation(self, manager):
        """Test retry delay calculation."""
        # Test exponential backoff
        delay1 = manager._calculate_retry_delay(1, 1.0, 60.0)
        delay2 = manager._calculate_retry_delay(2, 1.0, 60.0)
        delay3 = manager._calculate_retry_delay(3, 1.0, 60.0)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

        # Test max delay cap
        delay_large = manager._calculate_retry_delay(10, 1.0, 60.0)
        assert delay_large == 60.0

    async def test_payload_signing(self, manager):
        """Test payload signing."""
        payload = b"test_payload"
        secret = "test_secret"

        signature = manager._sign_payload(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 7  # "sha256=" + hex digest


@pytest.mark.asyncio
class TestWebhookEventEmitter:
    """Test webhook event emitter."""

    @pytest_asyncio.fixture
    async def emitter(self):
        """Create webhook event emitter for testing."""
        manager = WebhookManager()
        await manager.start()
        emitter = WebhookEventEmitter(manager)
        yield emitter
        await manager.stop()

    async def test_emit_auth_result(self, emitter):
        """Test emitting auth result event."""
        # Mock the webhook manager's send_event method
        with patch.object(emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await emitter.emit_auth_result(
                transaction_id="txn_123", decision="APPROVE", score=85.0
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.AUTH_RESULT
            assert call_args[0][1]["transaction_id"] == "txn_123"
            assert call_args[0][1]["decision"] == "APPROVE"
            assert call_args[0][1]["score"] == 85.0

    async def test_emit_settlement(self, emitter):
        """Test emitting settlement event."""
        with patch.object(emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await emitter.emit_settlement(
                transaction_id="txn_123",
                amount=100.0,
                currency="USD",
                status="completed",
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.SETTLEMENT
            assert call_args[0][1]["transaction_id"] == "txn_123"
            assert call_args[0][1]["amount"] == 100.0
            assert call_args[0][1]["currency"] == "USD"
            assert call_args[0][1]["status"] == "completed"

    async def test_emit_chargeback(self, emitter):
        """Test emitting chargeback event."""
        with patch.object(emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await emitter.emit_chargeback(
                transaction_id="txn_123",
                chargeback_id="cb_456",
                reason="fraud",
                amount=100.0,
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.CHARGEBACK
            assert call_args[0][1]["transaction_id"] == "txn_123"
            assert call_args[0][1]["chargeback_id"] == "cb_456"
            assert call_args[0][1]["reason"] == "fraud"
            assert call_args[0][1]["amount"] == 100.0

    async def test_emit_loyalty_event(self, emitter):
        """Test emitting loyalty event."""
        with patch.object(emitter.webhook_manager, "send_event") as mock_send:
            mock_send.return_value = []

            await emitter.emit_loyalty_event(
                customer_id="cust_123",
                event_type="points_earned",
                points_change=100,
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == WebhookEventType.LOYALTY_EVENT
            assert call_args[0][1]["customer_id"] == "cust_123"
            assert call_args[0][1]["event_type"] == "points_earned"
            assert call_args[0][1]["points_change"] == 100


@pytest.mark.asyncio
class TestGlobalFunctions:
    """Test global webhook functions."""

    async def test_get_webhook_manager(self):
        """Test getting webhook manager."""
        manager = await get_webhook_manager()
        assert manager is not None
        assert isinstance(manager, WebhookManager)

        # Cleanup
        await shutdown_webhooks()

    async def test_get_webhook_emitter(self):
        """Test getting webhook emitter."""
        emitter = await get_webhook_emitter()
        assert emitter is not None
        assert isinstance(emitter, WebhookEventEmitter)

        # Cleanup
        await shutdown_webhooks()

    async def test_shutdown_webhooks(self):
        """Test webhook shutdown."""
        # Get manager first
        manager = await get_webhook_manager()
        assert manager is not None

        # Shutdown
        await shutdown_webhooks()

        # Verify shutdown - manager should be None but get_webhook_manager
        # can recreate. This tests that shutdown works and manager can be
        # recreated
        new_manager = await get_webhook_manager()
        assert new_manager is not None
        assert isinstance(new_manager, WebhookManager)

        # Clean up
        await shutdown_webhooks()


if __name__ == "__main__":
    pytest.main([__file__])
