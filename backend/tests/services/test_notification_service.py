"""Tests for NotificationService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.notification_service import (
    NotificationService,
    AdminAlert,
    get_notification_service,
)


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def service(self):
        """Create service with mock URL."""
        return NotificationService(slack_webhook_url="https://hooks.slack.com/test")

    @pytest.fixture
    def service_no_slack(self):
        """Create service without Slack configured."""
        with patch("app.services.notification_service.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = ""
            return NotificationService(slack_webhook_url="")

    @pytest.mark.asyncio
    async def test_send_admin_alert_success(self, service):
        """Test successful Slack alert."""
        with patch("app.services.notification_service.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await service.send_admin_alert(
                title="Test Alert",
                message="Test message",
                severity="warning",
            )

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_admin_alert_no_slack(self, service_no_slack):
        """Test alert when Slack not configured."""
        result = await service_no_slack.send_admin_alert(
            title="Test Alert",
            message="Test message",
        )
        # Should return False (not sent because disabled)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_admin_alert_with_data(self, service):
        """Test alert with extra data fields."""
        with patch("app.services.notification_service.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await service.send_admin_alert(
                title="HITL Review",
                message="New drift detected",
                severity="critical",
                data={
                    "item_id": "abc123",
                    "review_type": "vector_drift",
                    "severity": "high",
                    "ip_id": "auteur:bong",
                    "drift_score": 0.25,
                },
                trace_id="trace-xyz",
            )

            assert result is True
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]

            # Check blocks structure
            assert "blocks" in payload
            assert len(payload["blocks"]) >= 2  # header + message + potentially more

            # Check attachment color (critical = #f44336)
            assert "attachments" in payload
            assert payload["attachments"][0]["color"] == "#f44336"

    @pytest.mark.asyncio
    async def test_send_admin_alert_with_alert_object(self, service):
        """Test alert using AdminAlert object."""
        with patch("app.services.notification_service.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            alert = AdminAlert(
                title="Test Alert",
                message="Test message",
                severity="info",
                data={"key": "value"},
                trace_id="trace-123",
            )

            result = await service.send_admin_alert(alert=alert)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_admin_alert_missing_fields(self, service):
        """Test alert with missing required fields."""
        result = await service.send_admin_alert(title="Only title")
        # Should return False due to missing message
        assert result is False

    @pytest.mark.asyncio
    async def test_send_admin_alert_slack_timeout(self, service):
        """Test handling of Slack timeout."""
        import httpx

        with patch("app.services.notification_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await service.send_admin_alert(
                title="Test Alert",
                message="Test message",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_admin_alert_slack_http_error(self, service):
        """Test handling of Slack HTTP error."""
        import httpx

        with patch("app.services.notification_service.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await service.send_admin_alert(
                title="Test Alert",
                message="Test message",
            )

            assert result is False


class TestAdminAlert:
    """Tests for AdminAlert dataclass."""

    def test_admin_alert_defaults(self):
        """Test AdminAlert default values."""
        alert = AdminAlert(title="Test", message="Message")

        assert alert.title == "Test"
        assert alert.message == "Message"
        assert alert.severity == "info"
        assert alert.data == {}
        assert alert.trace_id is None

    def test_admin_alert_with_all_fields(self):
        """Test AdminAlert with all fields."""
        alert = AdminAlert(
            title="Test",
            message="Message",
            severity="critical",
            data={"key": "value"},
            trace_id="trace-123",
        )

        assert alert.title == "Test"
        assert alert.message == "Message"
        assert alert.severity == "critical"
        assert alert.data == {"key": "value"}
        assert alert.trace_id == "trace-123"


class TestGetNotificationService:
    """Tests for get_notification_service singleton."""

    def test_get_notification_service_returns_instance(self):
        """Test get_notification_service returns NotificationService."""
        # Reset singleton
        import app.services.notification_service as module
        module._default_service = None

        service = get_notification_service()
        assert isinstance(service, NotificationService)

    def test_get_notification_service_returns_same_instance(self):
        """Test get_notification_service returns same instance."""
        import app.services.notification_service as module
        module._default_service = None

        service1 = get_notification_service()
        service2 = get_notification_service()

        assert service1 is service2
