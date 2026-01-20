"""
Tests for RFC 9457 Error Handling (H3.3)

Tests:
- ProblemDetail schema
- Custom exceptions
- Exception handlers
- i18n error messages
"""
import pytest
from datetime import datetime


class TestProblemDetailSchema:
    """Tests for ProblemDetail Pydantic schema."""

    def test_create_problem_detail_minimal(self):
        """Test creating ProblemDetail with minimal fields."""
        from app.schemas.problem_details import ProblemDetail

        problem = ProblemDetail(
            title="Test Error",
            status=400,
        )

        assert problem.title == "Test Error"
        assert problem.status == 400
        assert problem.type == "about:blank"  # Default
        assert problem.detail is None

    def test_create_problem_detail_full(self):
        """Test creating ProblemDetail with all fields."""
        from app.schemas.problem_details import ProblemDetail, ProblemTypes

        problem = ProblemDetail(
            type=ProblemTypes.INSUFFICIENT_CREDITS,
            title="Insufficient Credits",
            status=402,
            detail="Need 100 credits, have 50",
            instance="/api/v1/capsules/run/abc",
            error_code="INSUFFICIENT_CREDITS",
            request_id="req-123",
        )

        assert problem.type == ProblemTypes.INSUFFICIENT_CREDITS
        assert problem.status == 402
        assert problem.error_code == "INSUFFICIENT_CREDITS"
        assert problem.request_id == "req-123"

    def test_problem_detail_to_dict(self):
        """Test ProblemDetail model_dump excludes None values."""
        from app.schemas.problem_details import ProblemDetail

        problem = ProblemDetail(
            title="Test",
            status=500,
        )

        data = problem.model_dump(exclude_none=True)

        assert "title" in data
        assert "status" in data
        assert "detail" not in data  # Should be excluded (None)

    def test_problem_types_constants(self):
        """Test ProblemTypes constant values."""
        from app.schemas.problem_details import ProblemTypes

        assert ProblemTypes.BASE == "https://vivid.crebit.io/errors"
        assert "insufficient-credits" in ProblemTypes.INSUFFICIENT_CREDITS
        assert "rate-limited" in ProblemTypes.RATE_LIMITED
        assert "validation-error" in ProblemTypes.VALIDATION_ERROR


class TestProblemDetailFactories:
    """Tests for problem detail factory functions."""

    def test_insufficient_credits_factory(self):
        """Test insufficient_credits factory."""
        from app.schemas.problem_details import insufficient_credits

        problem = insufficient_credits(required=100, available=50)

        assert problem.status == 402
        assert "100" in problem.detail
        assert "50" in problem.detail
        assert problem.error_code == "INSUFFICIENT_CREDITS"

    def test_rate_limited_factory(self):
        """Test rate_limited factory."""
        from app.schemas.problem_details import rate_limited

        problem = rate_limited(retry_after=30)

        assert problem.status == 429
        assert "30" in problem.detail
        assert problem.error_code == "RATE_LIMITED"

    def test_validation_error_factory(self):
        """Test validation_error factory."""
        from app.schemas.problem_details import validation_error

        errors = [{"loc": ["body", "name"], "msg": "required"}]
        problem = validation_error(errors=errors)

        assert problem.status == 422
        assert problem.errors == errors

    def test_resource_not_found_factory(self):
        """Test resource_not_found factory."""
        from app.schemas.problem_details import resource_not_found

        problem = resource_not_found(resource_type="Capsule", resource_id="cap-123")

        assert problem.status == 404
        assert "Capsule" in problem.detail
        assert "cap-123" in problem.detail


class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_insufficient_credits_exception(self):
        """Test InsufficientCreditsError."""
        from app.exceptions import InsufficientCreditsError

        exc = InsufficientCreditsError(required=100, available=50)

        assert exc.status_code == 402
        assert exc.required == 100
        assert exc.available == 50
        assert exc.problem.error_code == "INSUFFICIENT_CREDITS"

    def test_token_expired_exception(self):
        """Test TokenExpiredError."""
        from app.exceptions import TokenExpiredError

        exc = TokenExpiredError(token_id="tok-abc")

        assert exc.status_code == 400
        assert exc.token_id == "tok-abc"

    def test_rate_limited_exception(self):
        """Test RateLimitedError."""
        from app.exceptions import RateLimitedError

        exc = RateLimitedError(retry_after=60)

        assert exc.status_code == 429
        assert exc.retry_after == 60

    def test_authentication_required_exception(self):
        """Test AuthenticationRequiredError."""
        from app.exceptions import AuthenticationRequiredError

        exc = AuthenticationRequiredError()

        assert exc.status_code == 401
        assert exc.problem.error_code == "AUTHENTICATION_REQUIRED"

    def test_permission_denied_exception(self):
        """Test PermissionDeniedError."""
        from app.exceptions import PermissionDeniedError

        exc = PermissionDeniedError(resource="capsule", action="delete")

        assert exc.status_code == 403
        assert exc.resource == "capsule"
        assert exc.action == "delete"

    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundError."""
        from app.exceptions import ResourceNotFoundError

        exc = ResourceNotFoundError(resource_type="User", resource_id="usr-123")

        assert exc.status_code == 404
        assert exc.resource_type == "User"
        assert exc.resource_id == "usr-123"

    def test_capsule_execution_exception(self):
        """Test CapsuleExecutionError."""
        from app.exceptions import CapsuleExecutionError

        exc = CapsuleExecutionError(capsule_id="cap-123", reason="API timeout")

        assert exc.status_code == 500
        assert exc.capsule_id == "cap-123"
        assert "API timeout" in exc.problem.detail

    def test_service_unavailable_exception(self):
        """Test ServiceUnavailableError."""
        from app.exceptions import ServiceUnavailableError

        exc = ServiceUnavailableError(service="Gemini", retry_after=30)

        assert exc.status_code == 503
        assert exc.service == "Gemini"
        assert exc.retry_after == 30

    def test_timeout_exception(self):
        """Test TimeoutError."""
        from app.exceptions import TimeoutError

        exc = TimeoutError(operation="generation", timeout_seconds=120)

        assert exc.status_code == 504
        assert exc.operation == "generation"


class TestI18nErrorMessages:
    """Tests for i18n error message localization."""

    def test_get_localized_message_english(self):
        """Test getting English message."""
        from app.i18n.errors import get_localized_message

        title = get_localized_message("INSUFFICIENT_CREDITS", "title", "en")
        detail = get_localized_message("INSUFFICIENT_CREDITS", "detail", "en")

        assert title == "Insufficient Credits"
        assert "credits" in detail.lower()

    def test_get_localized_message_korean(self):
        """Test getting Korean message."""
        from app.i18n.errors import get_localized_message

        title = get_localized_message("INSUFFICIENT_CREDITS", "title", "ko")
        detail = get_localized_message("INSUFFICIENT_CREDITS", "detail", "ko")

        assert title == "크레딧 부족"
        assert "크레딧" in detail

    def test_get_localized_message_japanese(self):
        """Test getting Japanese message."""
        from app.i18n.errors import get_localized_message

        title = get_localized_message("RATE_LIMITED", "title", "ja")

        assert title == "レート制限超過"

    def test_get_localized_message_fallback(self):
        """Test fallback to English for unsupported language."""
        from app.i18n.errors import get_localized_message

        # Unsupported language should fall back to English
        title = get_localized_message("VALIDATION_ERROR", "title", "fr")

        assert title == "Validation Error"

    def test_get_localized_message_unknown_code(self):
        """Test handling of unknown error code."""
        from app.i18n.errors import get_localized_message

        result = get_localized_message("UNKNOWN_ERROR", "title", "en")

        # Should return error code as fallback
        assert result == "UNKNOWN_ERROR"

    def test_get_localized_error(self):
        """Test getting both title and detail."""
        from app.i18n.errors import get_localized_error

        error = get_localized_error("TOKEN_EXPIRED", "ko")

        assert "title" in error
        assert "detail" in error
        assert error["title"] == "토큰 만료"

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        from app.i18n.errors import get_supported_languages

        languages = get_supported_languages()

        assert "en" in languages
        assert "ko" in languages
        assert "ja" in languages

    def test_detect_language_from_header(self):
        """Test language detection from Accept-Language header."""
        from app.i18n.errors import detect_language_from_header

        # Korean preference
        assert detect_language_from_header("ko-KR,ko;q=0.9,en;q=0.8") == "ko"

        # Japanese preference
        assert detect_language_from_header("ja;q=0.9,en;q=0.8") == "ja"

        # English fallback for unsupported
        assert detect_language_from_header("fr-FR,fr;q=0.9") == "en"

        # None header
        assert detect_language_from_header(None) == "en"

        # Empty header
        assert detect_language_from_header("") == "en"


class TestVividExceptionBase:
    """Tests for VividException base class."""

    def test_vivid_exception_has_problem_detail(self):
        """Test that VividException creates ProblemDetail."""
        from app.exceptions import VividException
        from app.schemas.problem_details import ProblemTypes

        exc = VividException(
            status_code=400,
            problem_type=ProblemTypes.VALIDATION_ERROR,
            title="Test Error",
            detail="Test detail",
            error_code="TEST_ERROR",
        )

        assert hasattr(exc, "problem")
        assert exc.problem.title == "Test Error"
        assert exc.problem.status == 400

    def test_vivid_exception_detail_is_dict(self):
        """Test that exception detail is serializable dict."""
        from app.exceptions import VividException
        from app.schemas.problem_details import ProblemTypes

        exc = VividException(
            status_code=500,
            problem_type=ProblemTypes.INTERNAL_ERROR,
            title="Error",
        )

        # detail should be dict for JSON serialization
        assert isinstance(exc.detail, dict)
        assert "title" in exc.detail
        assert "status" in exc.detail
