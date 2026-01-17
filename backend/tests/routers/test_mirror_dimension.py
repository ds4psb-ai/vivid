"""
Tests for Mirror Dimension Endpoints.

Covers:
- Sanitization helpers (XSS prevention)
- Validation helpers (MBTI, blood type, gender, stage)
- Request model validation
- Edge cases
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.mirror import (
    # Constants
    ALLOWED_BLOOD_TYPES,
    ALLOWED_GENDERS,
    ALLOWED_STAGES,
    VALID_MBTI_CHARS,
    # Helpers
    _sanitize_text_field,
    _validate_mbti,
    _validate_blood_type,
    _validate_gender,
    _validate_stage,
    # Request models
    MirrorInitRequest,
    MirrorChatRequest,
)


# ============================================================================
# Sanitization Helper Tests
# ============================================================================

class TestSanitizeTextField:
    """Tests for _sanitize_text_field helper."""

    def test_empty_string_returns_default(self):
        assert _sanitize_text_field("") == ""
        assert _sanitize_text_field("", "fallback") == "fallback"

    def test_none_returns_default(self):
        # If passed None (though type hints say str)
        assert _sanitize_text_field(None) == ""
        assert _sanitize_text_field(None, "default") == "default"

    def test_whitespace_only_returns_default(self):
        assert _sanitize_text_field("   ") == ""
        assert _sanitize_text_field("\t\n", "default") == "default"

    def test_strips_whitespace(self):
        assert _sanitize_text_field("  hello  ") == "hello"

    def test_removes_html_tags(self):
        assert _sanitize_text_field("<p>hello</p>") == "hello"
        assert _sanitize_text_field("<div><span>test</span></div>") == "test"

    def test_removes_script_tags(self):
        result = _sanitize_text_field("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert" in result  # Content preserved, tags removed

    def test_escapes_html_entities(self):
        # Note: < and > are removed as HTML tag delimiters before escaping
        # Only & is escaped since it's not part of a tag
        result = _sanitize_text_field("A & B")
        assert "&amp;" in result

    def test_escapes_ampersand(self):
        result = _sanitize_text_field("Tom & Jerry")
        assert "&amp;" in result
        assert "Tom" in result
        assert "Jerry" in result

    def test_removes_javascript_protocol(self):
        assert "javascript" not in _sanitize_text_field("javascript:alert(1)")
        assert "javascript" not in _sanitize_text_field("JAVASCRIPT:void(0)")
        assert "javascript" not in _sanitize_text_field("JavaScript : alert()")

    def test_removes_event_handlers(self):
        result = _sanitize_text_field("onclick=alert(1)")
        assert "onclick=" not in result
        result = _sanitize_text_field("ONMOUSEOVER=bad()")
        assert "onmouseover=" not in result.lower()

    def test_preserves_normal_text(self):
        text = "안녕하세요, 반갑습니다. Hello World!"
        result = _sanitize_text_field(text)
        assert "안녕하세요" in result

    def test_complex_xss_attack_vector(self):
        attack = '<img src="x" onerror="alert(document.cookie)">'
        result = _sanitize_text_field(attack)
        assert "<img" not in result
        assert "onerror=" not in result

    def test_nested_html_tags(self):
        result = _sanitize_text_field("<div><p><a href='x'>link</a></p></div>")
        assert "<" not in result or "&lt;" in result


# ============================================================================
# MBTI Validation Tests
# ============================================================================

class TestValidateMbti:
    """Tests for _validate_mbti helper."""

    def test_valid_mbti_types(self):
        valid_types = ["INTJ", "ENTP", "ISFP", "ESFJ", "INFP", "ESTJ"]
        for mbti in valid_types:
            assert _validate_mbti(mbti) == mbti

    def test_lowercase_normalized_to_uppercase(self):
        assert _validate_mbti("intj") == "INTJ"
        assert _validate_mbti("entp") == "ENTP"

    def test_mixed_case_normalized(self):
        assert _validate_mbti("InTj") == "INTJ"

    def test_empty_string_returns_empty(self):
        assert _validate_mbti("") == ""

    def test_invalid_length_returns_empty(self):
        assert _validate_mbti("INT") == ""  # Too short
        assert _validate_mbti("INTJX") == ""  # Too long
        assert _validate_mbti("IN") == ""

    def test_invalid_first_char_returns_empty(self):
        assert _validate_mbti("XNTJ") == ""  # X not in {E, I}
        assert _validate_mbti("ANTJ") == ""

    def test_invalid_second_char_returns_empty(self):
        assert _validate_mbti("IXTJ") == ""  # X not in {S, N}
        assert _validate_mbti("IATJ") == ""

    def test_invalid_third_char_returns_empty(self):
        assert _validate_mbti("INXJ") == ""  # X not in {T, F}
        assert _validate_mbti("INAJ") == ""

    def test_invalid_fourth_char_returns_empty(self):
        assert _validate_mbti("INTX") == ""  # X not in {J, P}
        assert _validate_mbti("INTA") == ""

    def test_whitespace_stripped(self):
        assert _validate_mbti("  INTJ  ") == "INTJ"

    def test_all_16_types(self):
        all_types = [
            "ISTJ", "ISFJ", "INFJ", "INTJ",
            "ISTP", "ISFP", "INFP", "INTP",
            "ESTP", "ESFP", "ENFP", "ENTP",
            "ESTJ", "ESFJ", "ENFJ", "ENTJ",
        ]
        for mbti in all_types:
            assert _validate_mbti(mbti) == mbti


# ============================================================================
# Blood Type Validation Tests
# ============================================================================

class TestValidateBloodType:
    """Tests for _validate_blood_type helper."""

    def test_valid_blood_types(self):
        assert _validate_blood_type("A") == "A"
        assert _validate_blood_type("B") == "B"
        assert _validate_blood_type("O") == "O"
        assert _validate_blood_type("AB") == "AB"

    def test_lowercase_normalized_to_uppercase(self):
        assert _validate_blood_type("a") == "A"
        assert _validate_blood_type("ab") == "AB"

    def test_empty_string_returns_empty(self):
        assert _validate_blood_type("") == ""

    def test_invalid_blood_type_returns_empty(self):
        assert _validate_blood_type("C") == ""
        assert _validate_blood_type("X") == ""
        assert _validate_blood_type("ABC") == ""

    def test_whitespace_stripped(self):
        assert _validate_blood_type("  A  ") == "A"
        assert _validate_blood_type(" AB ") == "AB"


# ============================================================================
# Gender Validation Tests
# ============================================================================

class TestValidateGender:
    """Tests for _validate_gender helper."""

    def test_valid_genders(self):
        assert _validate_gender("M") == "M"
        assert _validate_gender("F") == "F"
        assert _validate_gender("Other") == "Other"

    def test_empty_string_returns_empty(self):
        assert _validate_gender("") == ""

    def test_case_insensitive(self):
        assert _validate_gender("m") == "M"
        assert _validate_gender("f") == "F"
        assert _validate_gender("other") == "Other"
        assert _validate_gender("OTHER") == "Other"

    def test_invalid_gender_returns_empty(self):
        assert _validate_gender("X") == ""
        assert _validate_gender("Male") == ""  # Only M/F/Other allowed
        assert _validate_gender("Female") == ""

    def test_whitespace_stripped(self):
        assert _validate_gender("  M  ") == "M"


# ============================================================================
# Stage Validation Tests
# ============================================================================

class TestValidateStage:
    """Tests for _validate_stage helper."""

    def test_valid_stages(self):
        for stage in ALLOWED_STAGES:
            assert _validate_stage(stage) == stage

    def test_case_insensitive(self):
        assert _validate_stage("INTRO") == "intro"
        assert _validate_stage("Birth") == "birth"
        assert _validate_stage("SYNTHESIS") == "synthesis"

    def test_whitespace_stripped(self):
        assert _validate_stage("  intro  ") == "intro"

    def test_invalid_stage_raises_error(self):
        with pytest.raises(ValueError) as exc:
            _validate_stage("invalid_stage")
        assert "지원하지 않는 단계" in str(exc.value)

    def test_empty_stage_raises_error(self):
        with pytest.raises(ValueError):
            _validate_stage("")


# ============================================================================
# MirrorInitRequest Model Tests
# ============================================================================

class TestMirrorInitRequest:
    """Tests for MirrorInitRequest model validation."""

    def test_valid_minimal_request(self):
        req = MirrorInitRequest(
            birth_year=1990,
            birth_month=5,
            birth_day=15,
        )
        assert req.birth_year == 1990
        assert req.mbti == ""  # Default empty
        assert req.blood_type == ""
        assert req.gender == ""

    def test_valid_full_request(self):
        req = MirrorInitRequest(
            mbti="INTJ",
            blood_type="A",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=14,
            gender="M",
        )
        assert req.mbti == "INTJ"
        assert req.blood_type == "A"
        assert req.gender == "M"

    def test_mbti_validation_applied(self):
        # Invalid MBTI silently becomes empty
        req = MirrorInitRequest(
            mbti="XXXX",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
        )
        assert req.mbti == ""

    def test_blood_type_validation_applied(self):
        req = MirrorInitRequest(
            blood_type="X",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
        )
        assert req.blood_type == ""

    def test_gender_validation_applied(self):
        req = MirrorInitRequest(
            gender="Invalid",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
        )
        assert req.gender == ""

    def test_birth_year_range(self):
        # Valid range
        req = MirrorInitRequest(birth_year=1950, birth_month=1, birth_day=1)
        assert req.birth_year == 1950

        # Too early
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=1800, birth_month=1, birth_day=1)

        # Too late
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=2200, birth_month=1, birth_day=1)

    def test_birth_month_range(self):
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=1990, birth_month=0, birth_day=1)
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=1990, birth_month=13, birth_day=1)

    def test_birth_day_range(self):
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=1990, birth_month=1, birth_day=0)
        with pytest.raises(ValidationError):
            MirrorInitRequest(birth_year=1990, birth_month=1, birth_day=32)

    def test_birth_hour_range(self):
        req = MirrorInitRequest(
            birth_year=1990, birth_month=1, birth_day=1, birth_hour=0
        )
        assert req.birth_hour == 0

        req = MirrorInitRequest(
            birth_year=1990, birth_month=1, birth_day=1, birth_hour=23
        )
        assert req.birth_hour == 23

        with pytest.raises(ValidationError):
            MirrorInitRequest(
                birth_year=1990, birth_month=1, birth_day=1, birth_hour=24
            )


# ============================================================================
# MirrorChatRequest Model Tests
# ============================================================================

class TestMirrorChatRequest:
    """Tests for MirrorChatRequest model validation."""

    def test_valid_request(self):
        req = MirrorChatRequest(
            session_id="test-session-123",
            user_message="Hello, this is my response.",
            current_stage="intro",
        )
        assert req.session_id == "test-session-123"
        assert "Hello" in req.user_message
        assert req.current_stage == "intro"

    def test_xss_sanitized_in_user_message(self):
        req = MirrorChatRequest(
            session_id="test",
            user_message="<script>alert('xss')</script>Hello",
            current_stage="intro",
        )
        assert "<script>" not in req.user_message
        assert "Hello" in req.user_message

    def test_javascript_protocol_removed(self):
        req = MirrorChatRequest(
            session_id="test",
            user_message="Click here: javascript:alert(1)",
            current_stage="intro",
        )
        assert "javascript" not in req.user_message.lower()

    def test_event_handlers_removed(self):
        req = MirrorChatRequest(
            session_id="test",
            user_message="Test onclick=alert(1) message",
            current_stage="intro",
        )
        assert "onclick=" not in req.user_message

    def test_stage_validation_applied(self):
        # Valid stage
        req = MirrorChatRequest(
            session_id="test",
            user_message="Hello",
            current_stage="psychology",
        )
        assert req.current_stage == "psychology"

        # Invalid stage
        with pytest.raises(ValidationError) as exc:
            MirrorChatRequest(
                session_id="test",
                user_message="Hello",
                current_stage="invalid_stage",
            )
        assert "지원하지 않는 단계" in str(exc.value)

    def test_empty_session_id_rejected(self):
        with pytest.raises(ValidationError):
            MirrorChatRequest(
                session_id="",
                user_message="Hello",
                current_stage="intro",
            )

    def test_empty_user_message_rejected(self):
        with pytest.raises(ValidationError):
            MirrorChatRequest(
                session_id="test",
                user_message="",
                current_stage="intro",
            )

    def test_message_max_length(self):
        # Should succeed at max length
        long_msg = "x" * 2000
        req = MirrorChatRequest(
            session_id="test",
            user_message=long_msg,
            current_stage="intro",
        )
        assert len(req.user_message) <= 2000

        # Should fail over max length
        too_long = "x" * 2001
        with pytest.raises(ValidationError):
            MirrorChatRequest(
                session_id="test",
                user_message=too_long,
                current_stage="intro",
            )

    def test_all_valid_stages_accepted(self):
        for stage in ALLOWED_STAGES:
            req = MirrorChatRequest(
                session_id="test",
                user_message="Hello",
                current_stage=stage,
            )
            assert req.current_stage == stage


# ============================================================================
# XSS Prevention Tests
# ============================================================================

class TestXSSPrevention:
    """Comprehensive XSS attack vector tests."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "<a href=\"javascript:alert('xss')\">click</a>",
        "<body onload=alert('xss')>",
        "<iframe src=\"javascript:alert('xss')\">",
        "<input onfocus=alert('xss') autofocus>",
        "<marquee onstart=alert('xss')>",
        "<div style=\"background:url(javascript:alert('xss'))\">",
        "&#60;script&#62;alert('xss')&#60;/script&#62;",
        "<scr<script>ipt>alert('xss')</scr</script>ipt>",
        "\"><script>alert('xss')</script>",
        "'-alert('xss')-'",
        "<IMG SRC=JaVaScRiPt:alert('XSS')>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_payloads_sanitized(self, payload):
        result = _sanitize_text_field(payload)
        # Should not contain raw script tags
        assert "<script" not in result.lower()
        # Should not contain javascript: protocol
        assert "javascript:" not in result.lower()
        # Should not contain event handlers
        assert not any(f"on{e}=" in result.lower() for e in [
            "click", "load", "error", "focus", "mouseover", "start"
        ])

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_chat_request_sanitizes_xss(self, payload):
        req = MirrorChatRequest(
            session_id="test",
            user_message=f"Normal text {payload} more text",
            current_stage="intro",
        )
        # Should not contain dangerous patterns
        assert "<script" not in req.user_message.lower()


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge case tests for mirror dimension."""

    def test_unicode_preservation(self):
        result = _sanitize_text_field("안녕하세요 Hello 你好")
        assert "안녕하세요" in result
        assert "Hello" in result

    def test_emoji_preservation(self):
        result = _sanitize_text_field("Hello 😀 World 🌍")
        assert "😀" in result
        assert "🌍" in result

    def test_newlines_preserved(self):
        result = _sanitize_text_field("Line1\nLine2\nLine3")
        assert "\n" in result

    def test_mbti_boundary_cases(self):
        # Exactly 4 valid chars
        assert _validate_mbti("INTJ") == "INTJ"
        # Empty
        assert _validate_mbti("") == ""
        # Spaces only
        assert _validate_mbti("    ") == ""

    def test_blood_type_case_sensitivity(self):
        # AB is case-insensitive
        assert _validate_blood_type("ab") == "AB"
        assert _validate_blood_type("Ab") == "AB"
        assert _validate_blood_type("aB") == "AB"

    def test_stage_all_allowed_values(self):
        expected_stages = {
            "intro", "birth", "saju", "psychology",
            "creativity", "preferences", "synthesis", "final"
        }
        assert ALLOWED_STAGES == expected_stages

    def test_request_with_optional_fields(self):
        req = MirrorInitRequest(
            birth_year=2000,
            birth_month=1,
            birth_day=1,
            session_id="existing-session",
            seed_preset={"persona": {"archetype": "Creator"}},
            prior_outputs=[{"step": 1, "data": {}}],
        )
        assert req.session_id == "existing-session"
        assert req.seed_preset is not None
        assert len(req.prior_outputs) == 1

    def test_chat_request_with_history(self):
        req = MirrorChatRequest(
            session_id="test",
            user_message="My response",
            current_stage="psychology",
            chat_history=[
                {"role": "assistant", "content": "Previous question"},
                {"role": "user", "content": "Previous answer"},
            ],
            persona_data={"saju": {"year_pillar": "甲子"}},
        )
        assert len(req.chat_history) == 2
        assert "saju" in req.persona_data


# ============================================================================
# Constants Validation Tests
# ============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_blood_types_complete(self):
        assert "A" in ALLOWED_BLOOD_TYPES
        assert "B" in ALLOWED_BLOOD_TYPES
        assert "O" in ALLOWED_BLOOD_TYPES
        assert "AB" in ALLOWED_BLOOD_TYPES
        assert "" in ALLOWED_BLOOD_TYPES  # Empty allowed

    def test_genders_complete(self):
        assert "M" in ALLOWED_GENDERS
        assert "F" in ALLOWED_GENDERS
        assert "Other" in ALLOWED_GENDERS
        assert "" in ALLOWED_GENDERS  # Empty allowed

    def test_stages_complete(self):
        expected = {"intro", "birth", "saju", "psychology", "creativity", "preferences", "synthesis", "final"}
        assert ALLOWED_STAGES == expected

    def test_mbti_chars_structure(self):
        assert len(VALID_MBTI_CHARS) == 4
        assert VALID_MBTI_CHARS[0] == frozenset({"E", "I"})
        assert VALID_MBTI_CHARS[1] == frozenset({"S", "N"})
        assert VALID_MBTI_CHARS[2] == frozenset({"T", "F"})
        assert VALID_MBTI_CHARS[3] == frozenset({"J", "P"})
