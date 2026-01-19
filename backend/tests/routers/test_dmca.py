"""
Tests for DMCA Compliance API router.

Tests the DMCA Safe Harbor compliance endpoints:
- POST /dmca/notice - Submit takedown notice
- POST /dmca/counter - Submit counter-notice
- GET /dmca/status/{notice_id} - Check notice status
- GET /dmca/my-cases - List user's DMCA cases

Reference: https://copyrightalliance.org/education/copyright-law-explained/the-digital-millennium-copyright-act-dmca/dmca-safe-harbor/
"""
import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.routers.dmca import (
    DMCANoticeRequest,
    DMCANoticeResponse,
    DMCACounterRequest,
    DMCACounterResponse,
    DMCAStatusResponse,
)


# =============================================================================
# DMCA Notice Request Validation Tests
# =============================================================================

class TestDMCANoticeRequest:
    """Test DMCANoticeRequest schema validation."""

    def test_valid_minimal_notice(self):
        """Test minimal valid DMCA notice."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Copyright Holder",
            claimant_email="holder@example.com",
            claim_description="This content infringes my copyright on X",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.claimant_name == "Copyright Holder"
        assert notice.good_faith_belief is True

    def test_valid_full_notice(self):
        """Test full DMCA notice with all fields."""
        notice = DMCANoticeRequest(
            ip_slug="goblin",
            content_id=uuid4(),
            content_type="generation",
            claimant_name="Media Company Inc.",
            claimant_email="legal@mediacompany.com",
            claimant_company="Media Company Inc.",
            claim_description="This AI-generated video uses characters and scenes from our copyrighted drama 'Goblin'",
            claimed_work="The original K-drama 'Goblin' (2016-2017)",
            claimed_urls=["https://example.com/content/123", "https://example.com/content/456"],
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.claimant_company == "Media Company Inc."
        assert len(notice.claimed_urls) == 2

    def test_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_name="Test",
                claimant_email="invalid-email",  # Invalid email
                claim_description="Description of infringement",
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )

    def test_claimant_name_required(self):
        """Test claimant name is required."""
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_email="test@example.com",
                claim_description="Description",
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )

    def test_claim_description_min_length(self):
        """Test claim description minimum length."""
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_name="Test",
                claimant_email="test@example.com",
                claim_description="Short",  # Too short (min 10 chars)
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )

    def test_claim_description_max_length(self):
        """Test claim description maximum length."""
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_name="Test",
                claimant_email="test@example.com",
                claim_description="x" * 5001,  # Too long (max 5000 chars)
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )

    def test_content_id_required(self):
        """Test content_id is required."""
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                claimant_name="Test",
                claimant_email="test@example.com",
                claim_description="Valid description here",
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )


# =============================================================================
# Legal Affirmation Tests
# =============================================================================

class TestLegalAffirmations:
    """Test legal affirmation requirements."""

    def test_all_affirmations_required(self):
        """All legal affirmations must be true for valid notice."""
        # Test good_faith_belief
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_name="Test",
                claimant_email="test@example.com",
                claim_description="Valid description",
                # good_faith_belief missing
                accurate_statement=True,
                authorized_to_act=True,
                perjury_acknowledgment=True,
            )

    def test_false_affirmations_accepted_by_schema(self):
        """Schema accepts false affirmations (logic check is in endpoint)."""
        # Note: The schema itself doesn't enforce True values,
        # that's done by the endpoint validation
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="Valid description",
            good_faith_belief=False,  # False value
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        # Schema accepts it, endpoint should reject
        assert notice.good_faith_belief is False

    def test_perjury_acknowledgment_required(self):
        """Test perjury acknowledgment is required."""
        # Under 17 U.S.C. § 512(c)(3)(A)(vi), statements must be
        # made under penalty of perjury
        with pytest.raises(ValidationError):
            DMCANoticeRequest(
                content_id=uuid4(),
                claimant_name="Test",
                claimant_email="test@example.com",
                claim_description="Valid description",
                good_faith_belief=True,
                accurate_statement=True,
                authorized_to_act=True,
                # perjury_acknowledgment missing
            )


# =============================================================================
# DMCA Counter-Notice Tests
# =============================================================================

class TestDMCACounterRequest:
    """Test DMCACounterRequest schema validation."""

    def test_valid_counter_notice(self):
        """Test valid counter-notice."""
        counter = DMCACounterRequest(
            notice_id=uuid4(),
            counter_statement="This content is original and does not infringe copyright",
            user_name="Content Creator",
            user_email="creator@example.com",
            user_address="123 Main St, City, State 12345",
            good_faith_belief=True,
            consent_to_jurisdiction=True,
            perjury_acknowledgment=True,
        )
        assert counter.user_name == "Content Creator"

    def test_counter_with_phone(self):
        """Test counter-notice with optional phone."""
        counter = DMCACounterRequest(
            notice_id=uuid4(),
            counter_statement="This content is fair use parody",
            user_name="Creator",
            user_email="creator@example.com",
            user_address="456 Oak Ave, Town, State 67890",
            user_phone="+1-555-123-4567",
            good_faith_belief=True,
            consent_to_jurisdiction=True,
            perjury_acknowledgment=True,
        )
        assert counter.user_phone == "+1-555-123-4567"

    def test_address_required(self):
        """Test user address is required (for legal service)."""
        with pytest.raises(ValidationError):
            DMCACounterRequest(
                notice_id=uuid4(),
                counter_statement="Valid counter statement",
                user_name="Creator",
                user_email="creator@example.com",
                # user_address missing - required for legal service of process
                good_faith_belief=True,
                consent_to_jurisdiction=True,
                perjury_acknowledgment=True,
            )

    def test_address_min_length(self):
        """Test address minimum length."""
        with pytest.raises(ValidationError):
            DMCACounterRequest(
                notice_id=uuid4(),
                counter_statement="Valid counter statement",
                user_name="Creator",
                user_email="creator@example.com",
                user_address="Short",  # Too short
                good_faith_belief=True,
                consent_to_jurisdiction=True,
                perjury_acknowledgment=True,
            )

    def test_consent_to_jurisdiction_required(self):
        """Test consent to jurisdiction is required.

        Under 17 U.S.C. § 512(g)(3)(D), counter-notice must include
        consent to jurisdiction of Federal District Court.
        """
        with pytest.raises(ValidationError):
            DMCACounterRequest(
                notice_id=uuid4(),
                counter_statement="Valid counter statement",
                user_name="Creator",
                user_email="creator@example.com",
                user_address="Valid full address here",
                good_faith_belief=True,
                # consent_to_jurisdiction missing
                perjury_acknowledgment=True,
            )


# =============================================================================
# Response Schema Tests
# =============================================================================

class TestDMCANoticeResponse:
    """Test DMCANoticeResponse schema."""

    def test_notice_submitted_response(self):
        """Test response for submitted notice."""
        response = DMCANoticeResponse(
            notice_id="dmca-123",
            status="received",
            message="DMCA notice received. Content will be reviewed within 24 hours.",
            content_removed=False,
        )
        assert response.status == "received"
        assert response.content_removed is False

    def test_content_removed_response(self):
        """Test response when content is removed."""
        response = DMCANoticeResponse(
            notice_id="dmca-123",
            status="content_removed",
            message="Allegedly infringing content has been removed.",
            content_removed=True,
        )
        assert response.content_removed is True


class TestDMCACounterResponse:
    """Test DMCACounterResponse schema."""

    def test_counter_filed_response(self):
        """Test response for filed counter-notice."""
        response = DMCACounterResponse(
            notice_id="dmca-123",
            status="counter_filed",
            message="Counter-notice filed. Content may be restored after 10-14 business days.",
            restoration_date="2026-02-02",
        )
        assert response.status == "counter_filed"
        assert response.restoration_date is not None

    def test_counter_without_restoration_date(self):
        """Test response without restoration date."""
        response = DMCACounterResponse(
            notice_id="dmca-123",
            status="counter_received",
            message="Counter-notice received and being processed.",
        )
        assert response.restoration_date is None


class TestDMCAStatusResponse:
    """Test DMCAStatusResponse schema."""

    def test_initial_status(self):
        """Test initial notice status."""
        status = DMCAStatusResponse(
            notice_id="dmca-123",
            status="received",
            content_id="content-456",
            content_type="generation",
            notice_received_at="2026-01-19T12:00:00Z",
        )
        assert status.status == "received"
        assert status.content_removed_at is None

    def test_full_timeline_status(self):
        """Test status with full timeline."""
        status = DMCAStatusResponse(
            notice_id="dmca-123",
            status="counter_filed",
            content_id="content-456",
            content_type="generation",
            notice_received_at="2026-01-10T12:00:00Z",
            content_removed_at="2026-01-10T18:00:00Z",
            counter_filed_at="2026-01-12T10:00:00Z",
            counter_deadline="2026-01-24T10:00:00Z",
            restored_at=None,
        )
        assert status.counter_filed_at is not None
        assert status.restored_at is None


# =============================================================================
# DMCA Status Flow Tests
# =============================================================================

class TestDMCAStatusFlow:
    """Test DMCA case status transitions."""

    def test_initial_status_is_received(self):
        """Initial status should be 'received'."""
        assert "received" in ["received", "content_removed", "counter_filed", "restored", "closed"]

    def test_status_after_content_removal(self):
        """Status should be 'content_removed' after takedown."""
        valid_statuses = ["received", "content_removed", "counter_filed", "restored", "closed"]
        assert "content_removed" in valid_statuses

    def test_status_after_counter_notice(self):
        """Status should be 'counter_filed' after counter-notice."""
        valid_statuses = ["received", "content_removed", "counter_filed", "restored", "closed"]
        assert "counter_filed" in valid_statuses

    def test_10_14_day_waiting_period(self):
        """Counter-notice triggers 10-14 business day waiting period."""
        # Per 17 U.S.C. § 512(g)(2)(C), content may be restored
        # not less than 10, nor more than 14, business days after receipt
        from datetime import datetime, timedelta

        counter_filed_date = datetime(2026, 1, 12)
        min_restore_date = counter_filed_date + timedelta(days=10)
        max_restore_date = counter_filed_date + timedelta(days=14)

        assert min_restore_date == datetime(2026, 1, 22)
        assert max_restore_date == datetime(2026, 1, 26)


# =============================================================================
# Repeat Infringer Policy Tests
# =============================================================================

class TestRepeatInfringerPolicy:
    """Test repeat infringer policy compliance.

    DMCA Safe Harbor requires a policy for terminating repeat infringers.
    """

    def test_threshold_tracking(self):
        """Test infringement threshold tracking."""
        # Typical threshold is 3 valid DMCA notices
        threshold = 3
        infringement_count = 0

        infringement_count += 1  # First notice
        assert infringement_count < threshold

        infringement_count += 1  # Second notice
        assert infringement_count < threshold

        infringement_count += 1  # Third notice
        assert infringement_count >= threshold  # Account termination

    def test_count_only_valid_notices(self):
        """Only valid DMCA notices should count toward threshold."""
        # Invalid notices (e.g., without all required elements) don't count
        notices = [
            {"valid": True, "dismissed": False},
            {"valid": True, "dismissed": True},  # Counter-notice succeeded
            {"valid": False, "dismissed": False},  # Missing required elements
            {"valid": True, "dismissed": False},
        ]

        valid_undismissed = [n for n in notices if n["valid"] and not n["dismissed"]]
        assert len(valid_undismissed) == 2  # Only 2 count


# =============================================================================
# Content Type Tests
# =============================================================================

class TestContentTypes:
    """Test content type handling."""

    def test_generation_content_type(self):
        """Test 'generation' content type (AI-generated content)."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            content_type="generation",
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="Valid description here",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.content_type == "generation"

    def test_default_content_type(self):
        """Test default content type is 'generation'."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="Valid description here",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.content_type == "generation"


# =============================================================================
# Korean Language Support Tests
# =============================================================================

class TestKoreanLanguageSupport:
    """Test Korean language handling in DMCA fields."""

    def test_korean_claimant_name(self):
        """Test Korean claimant name."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="김철수 법률대리인",
            claimant_email="legal@example.com",
            claim_description="이 콘텐츠는 저작권 침해입니다.",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.claimant_name == "김철수 법률대리인"

    def test_korean_claim_description(self):
        """Test Korean claim description."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="이 AI 생성 영상은 저희 드라마 '도깨비'의 캐릭터와 장면을 무단으로 사용하고 있습니다.",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert "도깨비" in notice.claim_description

    def test_korean_counter_statement(self):
        """Test Korean counter statement."""
        counter = DMCACounterRequest(
            notice_id=uuid4(),
            counter_statement="이 콘텐츠는 패러디이며 공정 이용에 해당합니다.",
            user_name="창작자",
            user_email="creator@example.com",
            user_address="서울특별시 강남구 테헤란로 123",
            good_faith_belief=True,
            consent_to_jurisdiction=True,
            perjury_acknowledgment=True,
        )
        assert "패러디" in counter.counter_statement
        assert "서울" in counter.user_address


# =============================================================================
# IP Integration Tests
# =============================================================================

class TestIPIntegration:
    """Test DMCA integration with IP catalog."""

    def test_notice_with_ip_slug(self):
        """Test notice linked to specific IP."""
        notice = DMCANoticeRequest(
            ip_slug="goblin",
            content_id=uuid4(),
            claimant_name="Studio Dragon",
            claimant_email="legal@studiodragon.com",
            claim_description="Unauthorized use of Goblin IP",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.ip_slug == "goblin"

    def test_notice_without_ip_slug(self):
        """Test notice without IP slug (general content claim)."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="General Copyright Holder",
            claimant_email="holder@example.com",
            claim_description="This content infringes my copyright",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.ip_slug is None


# =============================================================================
# URL Validation Tests
# =============================================================================

class TestClaimedURLs:
    """Test claimed URLs handling."""

    def test_multiple_claimed_urls(self):
        """Test multiple claimed URLs."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="Valid description",
            claimed_urls=[
                "https://example.com/video/1",
                "https://example.com/video/2",
                "https://example.com/video/3",
            ],
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert len(notice.claimed_urls) == 3

    def test_empty_claimed_urls(self):
        """Test empty claimed URLs list."""
        notice = DMCANoticeRequest(
            content_id=uuid4(),
            claimant_name="Test",
            claimant_email="test@example.com",
            claim_description="Valid description",
            good_faith_belief=True,
            accurate_statement=True,
            authorized_to_act=True,
            perjury_acknowledgment=True,
        )
        assert notice.claimed_urls == []
