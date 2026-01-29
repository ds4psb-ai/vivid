"""
Run Token Service Tests

Tests for the hardened Run Token service including:
- Token lifecycle (issue, validate, deduct, refund, revoke)
- Security features (fingerprint, rate limiting, anomaly detection)
- Edge cases and error handling
"""
import asyncio
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.run_token_service import (
    RunTokenService,
    RunTokenStatus,
    RunTokenPayload,
    TokenStore,
    TokenState,
    TokenDenylist,
    RateLimiter,
    AnomalyDetector,
    FingerprintGenerator,
    RUN_TOKEN_TTL_MINUTES,
    MAX_DEDUCT_PER_MINUTE,
    MAX_TOKENS_PER_USER,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def token_store():
    """Fresh token store for each test."""
    return TokenStore()


@pytest.fixture
def service(token_store):
    """Run Token service with fresh store."""
    return RunTokenService(token_store=token_store)


@pytest.fixture
def fingerprint():
    """Sample fingerprint."""
    return FingerprintGenerator.generate(
        user_agent="Mozilla/5.0",
        client_ip="192.168.1.1",
        accept_language="en-US",
    )


# =============================================================================
# Token Lifecycle Tests (10 tests)
# =============================================================================

class TestTokenLifecycle:
    """Token lifecycle tests: issue, validate, deduct, refund, revoke."""

    @pytest.mark.asyncio
    async def test_issue_token_success(self, service, fingerprint):
        """Test successful token issuance."""
        success, token, run_id, error = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
            permissions=["read", "write"],
            fingerprint=fingerprint,
        )

        assert success is True
        assert token is not None
        assert run_id is not None
        assert run_id.startswith("run_")
        assert error is None

    @pytest.mark.asyncio
    async def test_issue_token_with_zero_credits(self, service):
        """Test token issuance with zero credits."""
        success, token, run_id, error = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=0,
        )

        assert success is True
        assert token is not None
        assert run_id is not None

    @pytest.mark.asyncio
    async def test_validate_token_success(self, service, fingerprint):
        """Test successful token validation."""
        # Issue token
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
            fingerprint=fingerprint,
        )
        assert success

        # Validate token
        valid, payload, error = await service.validate_token(token)

        assert valid is True
        assert payload is not None
        assert payload.user_id == "user-123"
        assert payload.app_id == "app-test"
        assert payload.credits_reserved == 100
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, service):
        """Test validation of invalid token."""
        valid, payload, error = await service.validate_token("invalid-token")

        assert valid is False
        assert payload is None
        assert error is not None

    @pytest.mark.asyncio
    async def test_deduct_credits_success(self, service):
        """Test successful credit deduction."""
        # Issue token with credits
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )
        assert success

        # Deduct credits
        success, used, remaining, error = await service.deduct_credits(
            run_id=run_id,
            amount=30,
            reason="usage",
        )

        assert success is True
        assert used == 30
        assert remaining == 70
        assert error is None

    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(self, service):
        """Test deduction with insufficient credits."""
        # Issue token with limited credits
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=50,
        )
        assert success

        # Try to deduct more than reserved
        success, used, remaining, error = await service.deduct_credits(
            run_id=run_id,
            amount=100,
            reason="usage",
        )

        assert success is False
        assert error == "Insufficient reserved credits"

    @pytest.mark.asyncio
    async def test_refund_credits_full(self, service):
        """Test full credit refund."""
        # Issue and partially use credits
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )
        await service.deduct_credits(run_id, 30, "usage")

        # Refund remaining
        success, refunded, error = await service.refund_credits(run_id)

        assert success is True
        assert refunded == 70  # 100 - 30 used
        assert error is None

    @pytest.mark.asyncio
    async def test_refund_credits_partial(self, service):
        """Test partial credit refund."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )

        # Partial refund
        success, refunded, error = await service.refund_credits(run_id, amount=50)

        assert success is True
        assert refunded == 50
        assert error is None

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, service):
        """Test successful token revocation."""
        # Issue token
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
        )
        assert success

        # Revoke token
        revoked = await service.revoke_token(run_id)
        assert revoked is True

        # Validate should fail
        valid, payload, error = await service.validate_token(token)
        assert valid is False
        assert "revoked" in error.lower()

    @pytest.mark.asyncio
    async def test_get_run_status(self, service):
        """Test run status retrieval."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )
        assert success

        status = await service.get_run_status(run_id)

        assert status is not None
        assert status["user_id"] == "user-123"
        assert status["app_id"] == "app-test"
        assert status["status"] == "active"
        assert status["credits_reserved"] == 100
        assert status["credits_used"] == 0


# =============================================================================
# Security Features Tests (10 tests)
# =============================================================================

class TestSecurityFeatures:
    """Security feature tests: fingerprint, denylist, rate limiting, anomaly."""

    def test_fingerprint_generation(self):
        """Test fingerprint generation consistency."""
        fp1 = FingerprintGenerator.generate(
            user_agent="Mozilla/5.0",
            client_ip="192.168.1.1",
            accept_language="en-US",
        )
        fp2 = FingerprintGenerator.generate(
            user_agent="Mozilla/5.0",
            client_ip="192.168.1.1",
            accept_language="en-US",
        )
        fp3 = FingerprintGenerator.generate(
            user_agent="Chrome/100",  # Different UA
            client_ip="192.168.1.1",
            accept_language="en-US",
        )

        assert fp1 == fp2  # Same input = same fingerprint
        assert fp1 != fp3  # Different input = different fingerprint
        assert len(fp1) == 32  # SHA256 truncated

    def test_fingerprint_verification(self):
        """Test fingerprint verification."""
        fp = FingerprintGenerator.generate(
            user_agent="Mozilla/5.0",
            client_ip="192.168.1.1",
            accept_language="en-US",
        )

        # Valid verification
        assert FingerprintGenerator.verify(
            fp, "Mozilla/5.0", "192.168.1.1", "en-US"
        ) is True

        # Invalid verification (different IP)
        assert FingerprintGenerator.verify(
            fp, "Mozilla/5.0", "10.0.0.1", "en-US"
        ) is False

    def test_denylist_revoke_and_check(self):
        """Test token denylist functionality."""
        denylist = TokenDenylist()

        # Token not revoked initially
        assert denylist.is_revoked("run-123") is False

        # Revoke token
        denylist.revoke("run-123")
        assert denylist.is_revoked("run-123") is True

        # Another token not affected
        assert denylist.is_revoked("run-456") is False

    def test_rate_limiter_allows_normal_usage(self):
        """Test rate limiter allows normal usage."""
        limiter = RateLimiter()

        # First few requests should pass
        for i in range(5):
            assert limiter.check_and_increment("run-123") is True

    def test_rate_limiter_blocks_excessive_usage(self):
        """Test rate limiter blocks excessive usage."""
        limiter = RateLimiter()

        # Exceed limit
        for i in range(MAX_DEDUCT_PER_MINUTE):
            limiter.check_and_increment("run-123")

        # Next request should be blocked
        assert limiter.check_and_increment("run-123") is False

    def test_anomaly_detector_normal_usage(self):
        """Test anomaly detector allows normal usage."""
        detector = AnomalyDetector()
        state = TokenState(
            user_id="user-123",
            app_id="app-test",
            status=RunTokenStatus.ACTIVE,
            credits_reserved=100,
            credits_used=0,
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
            deduct_count=0,
        )

        score, reasons = detector.calculate_score(state, amount=10)

        assert score < 0.5  # Not suspicious
        assert detector.is_suspicious(score) is False

    def test_anomaly_detector_rapid_deduct(self):
        """Test anomaly detector catches rapid deductions."""
        detector = AnomalyDetector()
        now = datetime.now(timezone.utc)
        state = TokenState(
            user_id="user-123",
            app_id="app-test",
            status=RunTokenStatus.ACTIVE,
            credits_reserved=100,
            credits_used=50,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=30)).isoformat(),
            deduct_count=5,
            last_deduct_at=(now - timedelta(seconds=1)).isoformat(),  # 1 second ago
        )

        score, reasons = detector.calculate_score(state, amount=10)

        assert "rapid_deduct" in reasons

    def test_anomaly_detector_ip_change(self):
        """Test anomaly detector catches IP changes."""
        detector = AnomalyDetector()
        state = TokenState(
            user_id="user-123",
            app_id="app-test",
            status=RunTokenStatus.ACTIVE,
            credits_reserved=100,
            credits_used=0,
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
            ip_history=["192.168.1.1", "192.168.1.1", "192.168.1.1"],
        )

        score, reasons = detector.calculate_score(
            state, amount=10, client_ip="10.0.0.1"  # New IP
        )

        assert "ip_change" in reasons

    def test_anomaly_detector_large_amount(self):
        """Test anomaly detector catches large deductions."""
        detector = AnomalyDetector()
        state = TokenState(
            user_id="user-123",
            app_id="app-test",
            status=RunTokenStatus.ACTIVE,
            credits_reserved=100,
            credits_used=0,
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
        )

        score, reasons = detector.calculate_score(state, amount=60)  # >50% of reserved

        assert "large_amount" in reasons

    @pytest.mark.asyncio
    async def test_max_tokens_per_user_limit(self, token_store):
        """Test maximum concurrent tokens per user limit."""
        service = RunTokenService(token_store=token_store)

        # Issue MAX_TOKENS_PER_USER tokens
        tokens = []
        for i in range(MAX_TOKENS_PER_USER):
            success, token, run_id, _ = await service.issue_token(
                user_id="user-123",
                app_id=f"app-{i}",
            )
            assert success
            tokens.append(run_id)

        # Issue one more - oldest should be revoked
        success, token, new_run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-new",
        )
        assert success

        # Oldest token should be revoked
        state = await token_store.get(tokens[0])
        assert state.status == RunTokenStatus.REVOKED


# =============================================================================
# Edge Cases Tests (10 tests)
# =============================================================================

class TestEdgeCases:
    """Edge case tests for error handling and boundary conditions."""

    @pytest.mark.asyncio
    async def test_deduct_from_nonexistent_run(self, service):
        """Test deduction from non-existent run."""
        success, used, remaining, error = await service.deduct_credits(
            run_id="nonexistent-run",
            amount=10,
        )

        assert success is False
        assert error == "Run not found"

    @pytest.mark.asyncio
    async def test_refund_from_nonexistent_run(self, service):
        """Test refund from non-existent run."""
        success, refunded, error = await service.refund_credits("nonexistent-run")

        assert success is False
        assert error == "Run not found"

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token(self, service):
        """Test revoking non-existent token."""
        revoked = await service.revoke_token("nonexistent-run")
        assert revoked is False

    @pytest.mark.asyncio
    async def test_get_status_nonexistent_run(self, service):
        """Test status of non-existent run."""
        status = await service.get_run_status("nonexistent-run")
        assert status is None

    @pytest.mark.asyncio
    async def test_deduct_from_revoked_token(self, service):
        """Test deduction from revoked token."""
        # Issue and revoke
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )
        await service.revoke_token(run_id)

        # Try to deduct
        success, used, remaining, error = await service.deduct_credits(
            run_id=run_id,
            amount=10,
        )

        assert success is False
        assert "revoked" in error.lower()

    @pytest.mark.asyncio
    async def test_deduct_zero_amount(self, service):
        """Test deduction of zero amount (should technically work but no change)."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )

        # Note: Deduct 0 should work (no-op)
        success, used, remaining, error = await service.deduct_credits(
            run_id=run_id,
            amount=0,
        )

        # This depends on implementation - could be True or False
        # Current implementation should allow it
        assert remaining == 100  # No change

    @pytest.mark.asyncio
    async def test_multiple_deductions(self, service):
        """Test multiple sequential deductions."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )

        # Multiple deductions
        await service.deduct_credits(run_id, 20, "step-1")
        await service.deduct_credits(run_id, 30, "step-2")
        success, used, remaining, _ = await service.deduct_credits(run_id, 25, "step-3")

        assert success is True
        assert used == 75  # 20 + 30 + 25
        assert remaining == 25

    @pytest.mark.asyncio
    async def test_deduct_exact_remaining(self, service):
        """Test deduction of exact remaining credits."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=100,
        )

        # Deduct exactly all credits
        success, used, remaining, error = await service.deduct_credits(
            run_id=run_id,
            amount=100,
        )

        assert success is True
        assert used == 100
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_token_payload_serialization(self, service):
        """Test token payload serialization/deserialization."""
        now = datetime.now(timezone.utc)
        payload = RunTokenPayload(
            user_id="user-123",
            app_id="app-test",
            run_id="run-test",
            credits_reserved=100,
            credits_used=50,
            permissions=["read", "write"],
            cert_hash=None,
            fingerprint="abc123",
            nonce="nonce-123",
            issued_at=now,
            expires_at=now + timedelta(minutes=30),
        )

        # Convert to JWT claims and back
        claims = payload.to_jwt_claims()
        restored = RunTokenPayload.from_jwt_claims(claims)

        assert restored.user_id == payload.user_id
        assert restored.app_id == payload.app_id
        assert restored.run_id == payload.run_id
        assert restored.credits_reserved == payload.credits_reserved
        assert restored.credits_used == payload.credits_used
        assert restored.permissions == payload.permissions
        assert restored.fingerprint == payload.fingerprint
        assert restored.nonce == payload.nonce

    @pytest.mark.asyncio
    async def test_concurrent_deductions(self, service):
        """Test concurrent deductions don't cause race conditions."""
        success, token, run_id, _ = await service.issue_token(
            user_id="user-123",
            app_id="app-test",
            credits_to_reserve=1000,
        )

        # Concurrent deductions
        async def deduct():
            return await service.deduct_credits(run_id, 10, "concurrent")

        results = await asyncio.gather(*[deduct() for _ in range(10)])

        # Count successful deductions
        successful = sum(1 for r in results if r[0] is True)

        # All should succeed (with rate limit, might be less)
        assert successful >= 1
        assert successful <= 10

        # Total used should match
        status = await service.get_run_status(run_id)
        assert status["credits_used"] == successful * 10
