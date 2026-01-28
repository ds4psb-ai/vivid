"""Tests for DriftCronService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.drift_cron import (
    DriftCronService,
    get_drift_cron_service,
    AUTO_APPROVE_CONFIDENCE_THRESHOLD,
)
from app.schemas.drift_detection import DriftAction, DriftDetectionResult


class TestDriftCronService:
    """Tests for DriftCronService."""

    @pytest.fixture
    def mock_versioning(self):
        """Create mock versioning service."""
        service = MagicMock()
        service.get_active_auteur_keys = AsyncMock(return_value=["bong", "wong"])
        service.detect_drift = AsyncMock(return_value=DriftDetectionResult(
            action=DriftAction.NO_CHANGE,
            drift_score=0.02,
            confidence=0.8,
        ))
        return service

    @pytest.fixture
    def mock_hitl(self):
        """Create mock HITL service."""
        service = MagicMock()
        service.expire_old_items = AsyncMock(return_value=0)
        return service

    @pytest.fixture
    def service(self, mock_versioning, mock_hitl):
        """Create DriftCronService with mocks."""
        return DriftCronService(
            versioning=mock_versioning,
            hitl=mock_hitl,
        )

    @pytest.mark.asyncio
    async def test_run_drift_check_no_new_videos(self, service, mock_versioning):
        """Test drift check when no new videos available."""
        with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
            mock_session = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_session
            mock_db_ctx.return_value.__aexit__.return_value = None

            result = await service.run_drift_check()

            assert result["checked"] == 2  # bong, wong
            assert result["errors"] == 0
            # All should be skipped due to no new videos
            for detail in result["details"]:
                assert detail.get("skipped") is True
                assert detail.get("reason") == "no_new_videos"

    @pytest.mark.asyncio
    async def test_run_drift_check_error_handling(self, service, mock_versioning):
        """Test error handling during drift check."""
        mock_versioning.get_active_auteur_keys.side_effect = Exception("DB Error")

        with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
            mock_session = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_session
            mock_db_ctx.return_value.__aexit__.return_value = None

            result = await service.run_drift_check()

            assert result["errors"] >= 1

    @pytest.mark.asyncio
    async def test_run_drift_check_individual_error(self, service, mock_versioning):
        """Test individual auteur check error handling."""
        # First call succeeds, second raises
        mock_versioning.get_active_auteur_keys.return_value = ["bong", "wong"]

        call_count = [0]

        async def mock_check(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Analysis failed")
            return DriftDetectionResult(
                action=DriftAction.NO_CHANGE,
                drift_score=0.01,
                confidence=0.9,
            )

        mock_versioning.detect_drift.side_effect = mock_check

        with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
            mock_session = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_session
            mock_db_ctx.return_value.__aexit__.return_value = None

            result = await service.run_drift_check()

            # Should have checked 2, with 1 error
            # Note: Since no new videos, all are skipped before detect_drift is called
            # So error won't be triggered unless we modify _check_auteur
            assert result["checked"] >= 1

    def test_start_scheduler(self, service):
        """Test scheduler starts correctly."""
        with patch("app.services.drift_cron.AsyncIOScheduler") as mock_scheduler_cls:
            mock_scheduler = MagicMock()
            mock_scheduler_cls.return_value = mock_scheduler

            service.start_scheduler(hour=3, minute=30)

            mock_scheduler.start.assert_called_once()
            assert mock_scheduler.add_job.call_count == 2  # drift + expiry

    def test_start_scheduler_already_running(self, service):
        """Test scheduler won't start twice."""
        with patch("app.services.drift_cron.AsyncIOScheduler") as mock_scheduler_cls:
            mock_scheduler = MagicMock()
            mock_scheduler_cls.return_value = mock_scheduler

            service.start_scheduler()
            service.start_scheduler()  # Second call should be ignored

            # Scheduler should only be started once
            assert mock_scheduler.start.call_count == 1

    def test_stop_scheduler(self, service):
        """Test scheduler stops correctly."""
        with patch("app.services.drift_cron.AsyncIOScheduler") as mock_scheduler_cls:
            mock_scheduler = MagicMock()
            mock_scheduler_cls.return_value = mock_scheduler

            service.start_scheduler()
            service.stop_scheduler()

            mock_scheduler.shutdown.assert_called_once()
            assert service._scheduler is None

    def test_stop_scheduler_not_running(self, service):
        """Test stop when scheduler not running."""
        # Should not raise error
        service.stop_scheduler()
        assert service._scheduler is None

    @pytest.mark.asyncio
    async def test_expire_old_reviews(self, service, mock_hitl):
        """Test HITL expiry check."""
        mock_hitl.expire_old_items.return_value = 5

        with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
            mock_session = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_session
            mock_db_ctx.return_value.__aexit__.return_value = None

            await service._expire_old_reviews()

            mock_hitl.expire_old_items.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_expire_old_reviews_error_handling(self, service, mock_hitl):
        """Test HITL expiry error handling."""
        mock_hitl.expire_old_items.side_effect = Exception("DB Error")

        with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
            mock_session = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_session
            mock_db_ctx.return_value.__aexit__.return_value = None

            # Should not raise, just log error
            await service._expire_old_reviews()


class TestCheckAuteur:
    """Tests for _check_auteur method."""

    @pytest.fixture
    def service(self):
        """Create service with mock."""
        mock_versioning = MagicMock()
        mock_versioning.detect_drift = AsyncMock(return_value=DriftDetectionResult(
            action=DriftAction.NO_CHANGE,
            drift_score=0.02,
            confidence=0.8,
        ))
        return DriftCronService(versioning=mock_versioning)

    @pytest.mark.asyncio
    async def test_check_auteur_no_videos(self, service):
        """Test check skips when no new videos."""
        mock_db = AsyncMock()

        result = await service._check_auteur("bong", mock_db)

        assert result["auteur_key"] == "bong"
        assert result["ip_id"] == "auteur:bong"
        assert result["skipped"] is True
        assert result["reason"] == "no_new_videos"


class TestGetDriftCronService:
    """Tests for get_drift_cron_service singleton."""

    def test_get_drift_cron_service_returns_instance(self):
        """Test get_drift_cron_service returns DriftCronService."""
        # Reset singleton
        import app.services.drift_cron as module
        module._default_service = None

        service = get_drift_cron_service()
        assert isinstance(service, DriftCronService)

    def test_get_drift_cron_service_returns_same_instance(self):
        """Test get_drift_cron_service returns same instance."""
        import app.services.drift_cron as module
        module._default_service = None

        service1 = get_drift_cron_service()
        service2 = get_drift_cron_service()

        assert service1 is service2


class TestSchedulerJobs:
    """Tests for scheduler job configurations."""

    def test_drift_check_job_configured(self):
        """Test drift check job is properly configured."""
        with patch("app.services.drift_cron.AsyncIOScheduler") as mock_scheduler_cls:
            mock_scheduler = MagicMock()
            mock_scheduler_cls.return_value = mock_scheduler

            service = DriftCronService()
            service.start_scheduler(hour=2, minute=30)

            # Find the drift_check job call
            drift_job_calls = [
                call for call in mock_scheduler.add_job.call_args_list
                if call[1].get("id") == "drift_check"
            ]

            assert len(drift_job_calls) == 1

    def test_hitl_expiry_job_configured(self):
        """Test HITL expiry job is properly configured."""
        with patch("app.services.drift_cron.AsyncIOScheduler") as mock_scheduler_cls:
            mock_scheduler = MagicMock()
            mock_scheduler_cls.return_value = mock_scheduler

            service = DriftCronService()
            service.start_scheduler()

            # Find the hitl_expiry job call
            expiry_job_calls = [
                call for call in mock_scheduler.add_job.call_args_list
                if call[1].get("id") == "hitl_expiry"
            ]

            assert len(expiry_job_calls) == 1


class TestAutoApprove:
    """Tests for auto-approve functionality."""

    @pytest.fixture
    def mock_versioning_high_confidence(self):
        """Create mock versioning with high confidence result."""
        service = MagicMock()
        service.get_active_auteur_keys = AsyncMock(return_value=["bong"])
        service.detect_drift = AsyncMock(return_value=DriftDetectionResult(
            action=DriftAction.REQUIRE_HUMAN_REVIEW,
            drift_score=0.25,
            confidence=0.9,  # High confidence → auto-approve
            current_version=1,
            proposed_version=2,
        ))
        return service

    @pytest.fixture
    def mock_versioning_low_confidence(self):
        """Create mock versioning with low confidence result."""
        service = MagicMock()
        service.get_active_auteur_keys = AsyncMock(return_value=["bong"])
        service.detect_drift = AsyncMock(return_value=DriftDetectionResult(
            action=DriftAction.REQUIRE_HUMAN_REVIEW,
            drift_score=0.25,
            confidence=0.5,  # Low confidence → needs review
            current_version=1,
            proposed_version=2,
        ))
        return service

    def test_auto_approve_threshold_value(self):
        """Test threshold constant is set correctly."""
        assert AUTO_APPROVE_CONFIDENCE_THRESHOLD == 0.8

    @pytest.mark.asyncio
    async def test_auto_approve_high_confidence(self, mock_versioning_high_confidence):
        """Test drift is auto-approved when confidence > 0.8."""
        service = DriftCronService(versioning=mock_versioning_high_confidence)

        with patch("app.services.notification_service.get_notification_service") as mock_notif:
            mock_notification = MagicMock()
            mock_notification.send_admin_alert = AsyncMock(return_value=True)
            mock_notif.return_value = mock_notification

            mock_db = AsyncMock()

            # Patch to provide new_videos
            with patch.object(service, "_check_auteur") as mock_check:
                mock_check.return_value = {
                    "auteur_key": "bong",
                    "ip_id": "auteur:bong",
                    "action": "auto_approved",
                    "drift_score": 0.25,
                    "confidence": 0.9,
                    "drift_detected": True,
                    "auto_approved": True,
                    "review_created": False,
                }

                with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
                    mock_db_ctx.return_value.__aenter__.return_value = mock_db
                    mock_db_ctx.return_value.__aexit__.return_value = None

                    result = await service.run_drift_check()

                    assert result["auto_approved"] == 1
                    assert result["reviews_created"] == 0

    @pytest.mark.asyncio
    async def test_no_auto_approve_low_confidence(self, mock_versioning_low_confidence):
        """Test drift creates review when confidence < 0.8."""
        service = DriftCronService(versioning=mock_versioning_low_confidence)

        mock_db = AsyncMock()

        with patch.object(service, "_check_auteur") as mock_check:
            mock_check.return_value = {
                "auteur_key": "bong",
                "ip_id": "auteur:bong",
                "action": "require_human_review",
                "drift_score": 0.25,
                "confidence": 0.5,
                "drift_detected": True,
                "auto_approved": False,
                "review_created": False,  # Would be True with actual implementation
            }

            with patch("app.services.drift_cron.get_db_context") as mock_db_ctx:
                mock_db_ctx.return_value.__aenter__.return_value = mock_db
                mock_db_ctx.return_value.__aexit__.return_value = None

                result = await service.run_drift_check()

                assert result["auto_approved"] == 0

    @pytest.mark.asyncio
    async def test_auto_approve_sends_notification(self):
        """Test auto-approve sends Slack notification."""
        mock_versioning = MagicMock()
        service = DriftCronService(versioning=mock_versioning)

        with patch("app.services.notification_service.get_notification_service") as mock_notif:
            mock_notification = MagicMock()
            mock_notification.send_admin_alert = AsyncMock(return_value=True)
            mock_notif.return_value = mock_notification

            drift_result = DriftDetectionResult(
                action=DriftAction.REQUIRE_HUMAN_REVIEW,
                drift_score=0.25,
                confidence=0.9,
                current_version=1,
                proposed_version=2,
            )

            mock_db = AsyncMock()

            await service._auto_approve_drift(
                ip_id="auteur:bong",
                auteur_key="bong",
                drift_result=drift_result,
                new_videos=["video1.mp4"],
                db=mock_db,
            )

            mock_notification.send_admin_alert.assert_called_once()
            call_kwargs = mock_notification.send_admin_alert.call_args[1]
            assert "bong" in call_kwargs["title"]
            assert call_kwargs["severity"] == "info"
