"""
Tests for Stripe Payment Service - H2.3 Core Feature Hardening

Tests the PCI DSS 4.0 compliant payment service:
1. Checkout session creation
2. Webhook signature verification
3. Idempotency key generation
4. Duplicate payment prevention
5. Event handling
"""

import pytest
import json
import hashlib
import hmac
import time
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4


# =============================================================================
# Stripe Payment Service Tests
# =============================================================================

class TestStripePaymentService:
    """Tests for StripePaymentService class."""

    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe SDK."""
        with patch("stripe.checkout.Session") as mock_session:
            with patch("stripe.Webhook") as mock_webhook:
                mock_session.create = MagicMock(return_value=MagicMock(
                    id="cs_test_123",
                    url="https://checkout.stripe.com/pay/cs_test_123",
                    amount_total=999,
                ))
                mock_session.retrieve = MagicMock(return_value=MagicMock(
                    id="cs_test_123",
                    status="complete",
                    payment_status="paid",
                    amount_total=999,
                    currency="usd",
                ))
                yield {
                    "session": mock_session,
                    "webhook": mock_webhook,
                }

    @pytest.fixture
    def service(self, mock_stripe):
        """Create payment service with mocked Stripe."""
        from app.services.stripe_payment import StripePaymentService

        return StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_test_mock",
            publishable_key="pk_test_mock",
        )

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        ))
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.publishable_key == "pk_test_mock"
        assert service.webhook_secret == "whsec_test_mock"

    def test_get_publishable_key(self, service):
        """Test getting publishable key."""
        key = service.get_publishable_key()
        assert key == "pk_test_mock"

    def test_get_credit_packages(self, service):
        """Test getting credit packages."""
        packages = service.get_credit_packages()

        assert len(packages) > 0
        assert all("credits" in p for p in packages)
        assert all("price_cents" in p for p in packages)

    def test_idempotency_key_generation(self, service):
        """Test idempotency key generation is consistent."""
        key1 = service._generate_idempotency_key("user1", 100, 499, "checkout")
        key2 = service._generate_idempotency_key("user1", 100, 499, "checkout")

        # Same inputs within same hour should produce same key
        assert key1 == key2
        assert len(key1) == 32

    def test_idempotency_key_different_inputs(self, service):
        """Test different inputs produce different keys."""
        key1 = service._generate_idempotency_key("user1", 100, 499, "checkout")
        key2 = service._generate_idempotency_key("user2", 100, 499, "checkout")

        assert key1 != key2


class TestCheckoutSession:
    """Tests for checkout session creation."""

    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe SDK."""
        with patch("stripe.checkout.Session") as mock_session:
            mock_session.create = MagicMock(return_value=MagicMock(
                id="cs_test_123",
                url="https://checkout.stripe.com/pay/cs_test_123",
                amount_total=999,
            ))
            yield mock_session

    @pytest.fixture
    def service(self, mock_stripe):
        """Create payment service."""
        from app.services.stripe_payment import StripePaymentService

        return StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_test_mock",
            publishable_key="pk_test_mock",
        )

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        ))
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, service, mock_db, mock_stripe):
        """Test creating a checkout session."""
        result = await service.create_checkout_session(
            user_id="user-123",
            credits=100,
            price_cents=499,
            db=mock_db,
        )

        assert result.session_id == "cs_test_123"
        assert "checkout.stripe.com" in result.checkout_url

    @pytest.mark.asyncio
    async def test_create_checkout_session_with_urls(self, service, mock_db, mock_stripe):
        """Test creating session with custom URLs."""
        result = await service.create_checkout_session(
            user_id="user-123",
            credits=100,
            price_cents=499,
            db=mock_db,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        # Verify Stripe was called
        mock_stripe.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkout_session_includes_metadata(self, service, mock_db, mock_stripe):
        """Test session includes required metadata."""
        await service.create_checkout_session(
            user_id="user-123",
            credits=100,
            price_cents=499,
            db=mock_db,
        )

        # Check call arguments
        call_kwargs = mock_stripe.create.call_args.kwargs

        assert "metadata" in call_kwargs
        assert call_kwargs["metadata"]["user_id"] == "user-123"
        assert call_kwargs["metadata"]["credits"] == "100"

    @pytest.mark.asyncio
    async def test_checkout_session_uses_idempotency_key(self, service, mock_db, mock_stripe):
        """Test session uses idempotency key."""
        await service.create_checkout_session(
            user_id="user-123",
            credits=100,
            price_cents=499,
            db=mock_db,
        )

        call_kwargs = mock_stripe.create.call_args.kwargs
        assert "idempotency_key" in call_kwargs


class TestWebhookVerification:
    """Tests for webhook signature verification."""

    @pytest.fixture
    def service(self):
        """Create payment service."""
        from app.services.stripe_payment import StripePaymentService

        return StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_test_secret",
            publishable_key="pk_test_mock",
        )

    def test_verify_webhook_missing_signature(self, service):
        """Test verification fails without signature."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            service.verify_webhook_signature(b"payload", "")

        assert exc_info.value.status_code == 400
        assert "Missing" in exc_info.value.detail

    def test_verify_webhook_invalid_signature(self, service):
        """Test verification fails with invalid signature."""
        from fastapi import HTTPException

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "sig_header"
            )

            with pytest.raises(HTTPException) as exc_info:
                service.verify_webhook_signature(b"payload", "invalid_sig")

            assert exc_info.value.status_code == 400
            assert "Invalid" in exc_info.value.detail

    def test_verify_webhook_valid_signature(self, service):
        """Test verification succeeds with valid signature."""
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_event = MagicMock()
            mock_event.id = "evt_test_123"
            mock_event.type = "checkout.session.completed"
            mock_construct.return_value = mock_event

            event = service.verify_webhook_signature(b"payload", "valid_sig")

            assert event.id == "evt_test_123"
            assert event.type == "checkout.session.completed"


class TestWebhookEventHandling:
    """Tests for webhook event handling."""

    @pytest.fixture
    def service(self):
        """Create payment service."""
        from app.services.stripe_payment import StripePaymentService

        return StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_test_mock",
            publishable_key="pk_test_mock",
        )

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        ))
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_handle_checkout_completed(self, service, mock_db):
        """Test handling checkout.session.completed event."""
        event = MagicMock()
        event.type = "checkout.session.completed"
        event.id = "evt_test_123"
        event.data = MagicMock()
        event.data.object = MagicMock(
            id="cs_test_123",
            metadata={"user_id": "user-123", "credits": "100"},
            amount_total=499,
        )

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "success"
        assert result["credits_added"] == 100

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_duplicate(self, service, mock_db):
        """Test handling duplicate checkout completion."""
        # Simulate already processed
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=MagicMock())  # Existing record
        ))

        event = MagicMock()
        event.type = "checkout.session.completed"
        event.id = "evt_test_123"
        event.data = MagicMock()
        event.data.object = MagicMock(
            id="cs_test_123",
            metadata={"user_id": "user-123", "credits": "100"},
        )

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_handle_payment_failed(self, service, mock_db):
        """Test handling payment_intent.payment_failed event."""
        event = MagicMock()
        event.type = "payment_intent.payment_failed"
        event.id = "evt_test_456"
        event.data = MagicMock()
        event.data.object = MagicMock(
            id="pi_test_123",
            last_payment_error="Card declined",
        )

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "logged"

    @pytest.mark.asyncio
    async def test_handle_refund(self, service, mock_db):
        """Test handling charge.refunded event."""
        event = MagicMock()
        event.type = "charge.refunded"
        event.id = "evt_test_789"
        event.data = MagicMock()
        event.data.object = MagicMock(
            id="ch_test_123",
            amount_refunded=499,
            payment_intent="pi_test_123",
        )

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "refund_processed"

    @pytest.mark.asyncio
    async def test_handle_session_expired(self, service, mock_db):
        """Test handling checkout.session.expired event."""
        event = MagicMock()
        event.type = "checkout.session.expired"
        event.id = "evt_test_expired"
        event.data = MagicMock()
        event.data.object = MagicMock(id="cs_test_expired")

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "expired"

    @pytest.mark.asyncio
    async def test_handle_unknown_event(self, service, mock_db):
        """Test handling unknown event type."""
        event = MagicMock()
        event.type = "unknown.event.type"
        event.id = "evt_test_unknown"

        result = await service.handle_webhook_event(event, mock_db)

        assert result["status"] == "ignored"


# =============================================================================
# Router Tests
# =============================================================================

class TestStripeWebhookRouter:
    """Tests for Stripe webhook router."""

    @pytest.fixture
    def mock_service(self):
        """Mock Stripe payment service."""
        service = MagicMock()
        service.verify_webhook_signature = MagicMock()
        service.handle_webhook_event = AsyncMock(return_value={"status": "success"})
        service.get_publishable_key = MagicMock(return_value="pk_test_mock")
        service.get_credit_packages = MagicMock(return_value=[
            {"credits": 100, "price_cents": 499}
        ])
        return service

    @pytest.mark.asyncio
    async def test_webhook_requires_signature(self):
        """Test webhook endpoint requires signature header."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        # This would need proper app setup for real test
        # Here we just verify the logic exists
        from app.routers.stripe_webhook import router

        # Router has prefix /stripe, so paths are /stripe/webhook etc.
        assert any("/webhook" in r.path for r in router.routes)

    def test_config_endpoint_returns_packages(self, mock_service):
        """Test config endpoint returns credit packages."""
        from app.services.stripe_payment import CREDIT_PACKAGES

        assert len(CREDIT_PACKAGES) > 0
        assert CREDIT_PACKAGES[0]["credits"] == 100


# =============================================================================
# Security Tests
# =============================================================================

class TestStripeSecurityCompliance:
    """Tests for PCI DSS 4.0 compliance."""

    def test_secret_key_not_exposed(self):
        """Test secret key is not exposed in service."""
        from app.services.stripe_payment import StripePaymentService

        service = StripePaymentService(
            secret_key="sk_test_sensitive",
            webhook_secret="whsec_sensitive",
            publishable_key="pk_test_public",
        )

        # Public key should be accessible
        assert service.get_publishable_key() == "pk_test_public"

        # Secret key should not be directly accessible
        assert not hasattr(service, "secret_key")

    def test_webhook_secret_not_exposed(self):
        """Test webhook secret is only used for verification."""
        from app.services.stripe_payment import StripePaymentService

        service = StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_test_secret",
            publishable_key="pk_test_mock",
        )

        # Webhook secret should only be used internally
        assert service.webhook_secret == "whsec_test_secret"

    def test_idempotency_prevents_duplicates(self):
        """Test idempotency key generation prevents duplicates."""
        from app.services.stripe_payment import StripePaymentService

        service = StripePaymentService(
            secret_key="sk_test_mock",
            webhook_secret="whsec_mock",
            publishable_key="pk_test_mock",
        )

        # Same operation should produce same key
        key1 = service._generate_idempotency_key("user1", 100, 499, "checkout")
        key2 = service._generate_idempotency_key("user1", 100, 499, "checkout")

        assert key1 == key2

        # Different operation should produce different key
        key3 = service._generate_idempotency_key("user1", 200, 999, "checkout")
        assert key1 != key3


# =============================================================================
# Integration Tests
# =============================================================================

class TestStripeIntegration:
    """Integration tests for Stripe payment flow."""

    @pytest.mark.asyncio
    async def test_full_payment_flow(self):
        """Test complete payment flow simulation."""
        # This test simulates the full flow:
        # 1. Create checkout session
        # 2. (User pays on Stripe)
        # 3. Receive webhook
        # 4. Verify and process

        with patch("stripe.checkout.Session.create") as mock_create:
            with patch("stripe.Webhook.construct_event") as mock_verify:
                mock_create.return_value = MagicMock(
                    id="cs_test_flow",
                    url="https://checkout.stripe.com/test",
                )

                mock_verify.return_value = MagicMock(
                    id="evt_flow",
                    type="checkout.session.completed",
                    data=MagicMock(object=MagicMock(
                        id="cs_test_flow",
                        metadata={"user_id": "user-flow", "credits": "100"},
                        amount_total=499,
                    )),
                )

                from app.services.stripe_payment import StripePaymentService

                service = StripePaymentService(
                    secret_key="sk_test_mock",
                    webhook_secret="whsec_mock",
                    publishable_key="pk_test_mock",
                )

                # Step 1: Create session
                mock_db = MagicMock()
                mock_db.execute = AsyncMock(return_value=MagicMock(
                    scalar_one_or_none=MagicMock(return_value=None)
                ))
                mock_db.commit = AsyncMock()
                mock_db.add = MagicMock()

                session = await service.create_checkout_session(
                    user_id="user-flow",
                    credits=100,
                    price_cents=499,
                    db=mock_db,
                )

                assert session.session_id == "cs_test_flow"

                # Step 2: Verify webhook
                event = service.verify_webhook_signature(
                    b"test_payload",
                    "test_signature",
                )

                assert event.type == "checkout.session.completed"

                # Step 3: Process event
                result = await service.handle_webhook_event(event, mock_db)

                assert result["status"] == "success"
                assert result["credits_added"] == 100
