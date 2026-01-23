"""
Tests for Mirror Dimension Endpoints.

Covers:
- Sanitization helpers (XSS prevention)
- Validation helpers (MBTI, blood type, gender, stage)
- Request model validation
- Edge cases
- 2026 Enhancements: MBTI-CI, Creative Style, Auteur Affinity, Profile Quality
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
    # 2026 Enhancements
    CreativeStyle,
    MBTI_DIMENSION_SCORES,
    MBTI_CREATIVE_STYLE_MAP,
    AUTEUR_AFFINITY_MAP,
    CREATIVE_STRENGTHS_MAP,
    calculate_mbti_creativity_index,
    get_creative_style,
    get_auteur_affinity,
    get_creative_strengths,
    assess_mirror_profile_quality,
    MirrorProfileQuality,
    MirrorInitResponse,
    MirrorChatResponse,
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
            "creativity", "preferences", "synthesis", "summary", "final"
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
        expected = {"intro", "birth", "saju", "psychology", "creativity", "preferences", "synthesis", "summary", "final"}
        assert ALLOWED_STAGES == expected

    def test_mbti_chars_structure(self):
        assert len(VALID_MBTI_CHARS) == 4
        assert VALID_MBTI_CHARS[0] == frozenset({"E", "I"})
        assert VALID_MBTI_CHARS[1] == frozenset({"S", "N"})
        assert VALID_MBTI_CHARS[2] == frozenset({"T", "F"})
        assert VALID_MBTI_CHARS[3] == frozenset({"J", "P"})


# ============================================================================
# 2026 Enhancements: MBTI Creativity Index Tests
# ============================================================================

class TestMBTICreativityIndex:
    """Tests for MBTI Creativity Index calculation (2026)."""

    def test_highest_creativity_infp(self):
        """INFP should have highest CI: 3*1 + 1 - 1 - 0.5*1 = 2.5"""
        ci = calculate_mbti_creativity_index("INFP")
        assert ci == 2.5

    def test_highest_creativity_entp(self):
        """ENTP: 3*1 + 1 - 0 - 0.5*0 = 4.0"""
        ci = calculate_mbti_creativity_index("ENTP")
        assert ci == 4.0

    def test_lowest_creativity_estj(self):
        """ESTJ: 3*0 + 0 - 0 - 0.5*0 = 0.0"""
        ci = calculate_mbti_creativity_index("ESTJ")
        assert ci == 0.0

    def test_lowest_creativity_istj(self):
        """ISTJ: 3*0 + 0 - 1 - 0.5*0 = -1.0"""
        ci = calculate_mbti_creativity_index("ISTJ")
        assert ci == -1.0

    def test_isfj_creativity(self):
        """ISFJ: 3*0 + 0 - 1 - 0.5*1 = -1.5"""
        ci = calculate_mbti_creativity_index("ISFJ")
        assert ci == -1.5

    def test_intj_creativity(self):
        """INTJ: 3*1 + 0 - 1 - 0.5*0 = 2.0"""
        ci = calculate_mbti_creativity_index("INTJ")
        assert ci == 2.0

    def test_enfp_creativity(self):
        """ENFP: 3*1 + 1 - 0 - 0.5*1 = 3.5"""
        ci = calculate_mbti_creativity_index("ENFP")
        assert ci == 3.5

    def test_empty_mbti_returns_zero(self):
        ci = calculate_mbti_creativity_index("")
        assert ci == 0.0

    def test_invalid_mbti_returns_zero(self):
        ci = calculate_mbti_creativity_index("XXXX")
        assert ci == 0.0

    def test_short_mbti_returns_zero(self):
        ci = calculate_mbti_creativity_index("INT")
        assert ci == 0.0

    def test_ci_range_boundaries(self):
        """CI should be in range -4.5 to +4.5."""
        all_types = [
            "ISTJ", "ISFJ", "INFJ", "INTJ",
            "ISTP", "ISFP", "INFP", "INTP",
            "ESTP", "ESFP", "ENFP", "ENTP",
            "ESTJ", "ESFJ", "ENFJ", "ENTJ",
        ]
        for mbti in all_types:
            ci = calculate_mbti_creativity_index(mbti)
            assert -4.5 <= ci <= 4.5, f"CI out of range for {mbti}: {ci}"

    def test_all_16_types_calculated(self):
        """All 16 MBTI types should return valid CI."""
        all_types = list(MBTI_CREATIVE_STYLE_MAP.keys())
        assert len(all_types) == 16
        for mbti in all_types:
            ci = calculate_mbti_creativity_index(mbti)
            assert isinstance(ci, float)


# ============================================================================
# 2026 Enhancements: Creative Style Tests
# ============================================================================

class TestCreativeStyle:
    """Tests for Creative Style classification (2026)."""

    def test_visionary_storyteller_types(self):
        visionary_types = ["INFP", "ENFP", "INFJ", "ENFJ", "ISFJ"]
        for mbti in visionary_types:
            style = get_creative_style(mbti)
            assert style == CreativeStyle.VISIONARY_STORYTELLER, f"{mbti} should be visionary"

    def test_logical_architect_types(self):
        architect_types = ["INTP", "INTJ", "ENTP", "ENTJ", "ISTJ"]
        for mbti in architect_types:
            style = get_creative_style(mbti)
            assert style == CreativeStyle.LOGICAL_ARCHITECT, f"{mbti} should be architect"

    def test_dramatic_director_types(self):
        dramatic_types = ["ESTJ", "ESFJ"]
        for mbti in dramatic_types:
            style = get_creative_style(mbti)
            assert style == CreativeStyle.DRAMATIC_DIRECTOR, f"{mbti} should be dramatic"

    def test_experimental_artist_types(self):
        experimental_types = ["ISTP", "ESTP", "ISFP", "ESFP"]
        for mbti in experimental_types:
            style = get_creative_style(mbti)
            assert style == CreativeStyle.EXPERIMENTAL_ARTIST, f"{mbti} should be experimental"

    def test_empty_mbti_returns_unknown(self):
        style = get_creative_style("")
        assert style == CreativeStyle.UNKNOWN

    def test_invalid_mbti_returns_unknown(self):
        style = get_creative_style("XXXX")
        assert style == CreativeStyle.UNKNOWN

    def test_all_16_types_mapped(self):
        """All 16 MBTI types should be in the mapping."""
        assert len(MBTI_CREATIVE_STYLE_MAP) == 16

    def test_creative_style_enum_values(self):
        assert CreativeStyle.VISIONARY_STORYTELLER.value == "visionary_storyteller"
        assert CreativeStyle.LOGICAL_ARCHITECT.value == "logical_architect"
        assert CreativeStyle.DRAMATIC_DIRECTOR.value == "dramatic_director"
        assert CreativeStyle.EXPERIMENTAL_ARTIST.value == "experimental_artist"
        assert CreativeStyle.UNKNOWN.value == "unknown"


# ============================================================================
# 2026 Enhancements: Auteur Affinity Tests
# ============================================================================

class TestAuteurAffinity:
    """Tests for Auteur Affinity matching (2026)."""

    def test_visionary_auteurs(self):
        auteurs = get_auteur_affinity(CreativeStyle.VISIONARY_STORYTELLER)
        assert "bong" in auteurs
        assert "wong" in auteurs
        assert "miyazaki" in auteurs

    def test_architect_auteurs(self):
        auteurs = get_auteur_affinity(CreativeStyle.LOGICAL_ARCHITECT)
        assert "nolan" in auteurs
        assert "villeneuve" in auteurs
        assert "kubrick" in auteurs

    def test_dramatic_auteurs(self):
        auteurs = get_auteur_affinity(CreativeStyle.DRAMATIC_DIRECTOR)
        assert "spielberg" in auteurs
        assert "cameron" in auteurs

    def test_experimental_auteurs(self):
        auteurs = get_auteur_affinity(CreativeStyle.EXPERIMENTAL_ARTIST)
        assert "tarantino" in auteurs
        assert "guy_ritchie" in auteurs

    def test_unknown_returns_empty(self):
        auteurs = get_auteur_affinity(CreativeStyle.UNKNOWN)
        assert auteurs == []

    def test_all_styles_have_auteurs(self):
        for style in CreativeStyle:
            if style != CreativeStyle.UNKNOWN:
                auteurs = get_auteur_affinity(style)
                assert len(auteurs) > 0, f"{style} should have auteurs"


# ============================================================================
# 2026 Enhancements: Creative Strengths Tests
# ============================================================================

class TestCreativeStrengths:
    """Tests for Creative Strengths retrieval (2026)."""

    def test_visionary_strengths(self):
        strengths = get_creative_strengths(CreativeStyle.VISIONARY_STORYTELLER)
        assert "emotional_depth" in strengths
        assert "character_psychology" in strengths

    def test_architect_strengths(self):
        strengths = get_creative_strengths(CreativeStyle.LOGICAL_ARCHITECT)
        assert "complex_plot_structure" in strengths
        assert "worldbuilding" in strengths

    def test_dramatic_strengths(self):
        strengths = get_creative_strengths(CreativeStyle.DRAMATIC_DIRECTOR)
        assert "epic_narrative" in strengths
        assert "character_growth_arc" in strengths

    def test_experimental_strengths(self):
        strengths = get_creative_strengths(CreativeStyle.EXPERIMENTAL_ARTIST)
        assert "genre_blending" in strengths
        assert "nonlinear_narrative" in strengths

    def test_unknown_returns_empty(self):
        strengths = get_creative_strengths(CreativeStyle.UNKNOWN)
        assert strengths == []

    def test_all_styles_have_strengths(self):
        for style in CreativeStyle:
            if style != CreativeStyle.UNKNOWN:
                strengths = get_creative_strengths(style)
                assert len(strengths) >= 3, f"{style} should have at least 3 strengths"


# ============================================================================
# 2026 Enhancements: Profile Quality Assessment Tests
# ============================================================================

class TestProfileQualityAssessment:
    """Tests for Profile Quality Assessment (2026)."""

    def test_basic_assessment_with_mbti(self):
        quality = assess_mirror_profile_quality(
            mbti="INFP",
            persona_data={"saju": {"year_pillar": "甲子"}},
            completion_rate=50.0,
            chat_turn_count=5,
        )
        assert quality.creativity_index == 2.5
        assert quality.creative_style == "visionary_storyteller"
        assert "bong" in quality.auteur_affinity
        assert "emotional_depth" in quality.creative_strengths

    def test_assessment_without_mbti(self):
        quality = assess_mirror_profile_quality(
            mbti="",
            persona_data={},
            completion_rate=25.0,
            chat_turn_count=2,
        )
        assert quality.creativity_index == 0.0
        assert quality.creative_style == "unknown"
        assert quality.auteur_affinity == []

    def test_completeness_score_with_full_data(self):
        quality = assess_mirror_profile_quality(
            mbti="INTJ",
            persona_data={
                "saju": {"year_pillar": "甲子"},
                "input": {"mbti": "INTJ"},
                "persona": {"archetype": "Analyst"},
                "preferences": {"genre": "sci-fi"},
            },
            completion_rate=100.0,
            chat_turn_count=15,
        )
        assert quality.completeness_score == 100  # 25+25+15+20+15

    def test_consistency_score_with_many_turns(self):
        quality = assess_mirror_profile_quality(
            mbti="ENTP",
            persona_data={},
            completion_rate=50.0,
            chat_turn_count=15,
        )
        assert quality.consistency_score == 100

    def test_consistency_score_with_few_turns(self):
        quality = assess_mirror_profile_quality(
            mbti="ENTP",
            persona_data={},
            completion_rate=50.0,
            chat_turn_count=3,
        )
        assert quality.consistency_score == 30  # 3 * 10

    def test_depth_score_from_completion_rate(self):
        quality = assess_mirror_profile_quality(
            mbti="ESTJ",
            persona_data={},
            completion_rate=75.0,
            chat_turn_count=10,
        )
        assert quality.depth_score == 75

    def test_overall_score_calculation(self):
        quality = assess_mirror_profile_quality(
            mbti="INFJ",
            persona_data={
                "saju": {"year_pillar": "甲子"},  # Non-empty to count
                "input": {"mbti": "INFJ"},  # Non-empty to count
            },
            completion_rate=60.0,
            chat_turn_count=8,
        )
        # completeness: 25 (mbti) + 25 (saju) + 15 (input) = 65
        # consistency: 60 (8 turns -> 60)
        # depth: 60
        # overall: 65*0.3 + 60*0.3 + 60*0.4 = 19.5 + 18 + 24 = 61.5 -> 61
        assert 55 <= quality.overall_score <= 65

    def test_suggestions_for_low_completion(self):
        quality = assess_mirror_profile_quality(
            mbti="",
            persona_data={},
            completion_rate=20.0,
            chat_turn_count=1,
        )
        assert len(quality.suggestions) > 0
        assert any("MBTI" in s for s in quality.suggestions)

    def test_high_creativity_suggestion(self):
        quality = assess_mirror_profile_quality(
            mbti="ENTP",  # CI = 4.0
            persona_data={},
            completion_rate=50.0,
            chat_turn_count=5,
        )
        assert any("creative potential" in s.lower() for s in quality.suggestions)

    def test_low_creativity_suggestion(self):
        # ISFJ CI = -1.5 which is <= -1.0, so structured suggestion triggers
        quality = assess_mirror_profile_quality(
            mbti="ISFJ",  # CI = -1.5 (lowest possible)
            persona_data={},
            completion_rate=50.0,
            chat_turn_count=5,
        )
        # Lowest CI (-1.5) should trigger structured suggestion
        assert any("structured" in s.lower() for s in quality.suggestions)
        # Verify the CI is indeed low
        assert quality.creativity_index == -1.5

    def test_profile_quality_model_validation(self):
        """Test MirrorProfileQuality model constraints."""
        quality = MirrorProfileQuality(
            completeness_score=100,
            consistency_score=100,
            depth_score=100,
            overall_score=100,
            creativity_index=4.5,
            creative_style="visionary_storyteller",
            auteur_affinity=["bong", "wong"],
            creative_strengths=["emotional_depth"],
            suggestions=["tip1"],
        )
        assert quality.completeness_score == 100
        assert quality.creativity_index == 4.5

    def test_profile_quality_score_bounds(self):
        """Scores should be bounded 0-100."""
        with pytest.raises(ValidationError):
            MirrorProfileQuality(
                completeness_score=150,  # Over limit
                consistency_score=50,
                depth_score=50,
                overall_score=50,
            )

    def test_empty_dicts_dont_inflate_completeness(self):
        """Empty dicts (with empty string values) should not contribute to completeness.

        Regression test for P2 issue: validate_persona_preset seeds with empty dicts.
        """
        quality = assess_mirror_profile_quality(
            mbti="INTJ",  # 25 points
            persona_data={
                "saju": {"year_pillar": "", "month_pillar": ""},  # Empty strings, 0 points
                "input": {"mbti": ""},  # Empty string, 0 points
                "persona": {},  # Empty dict, 0 points
                "preferences": {},  # Empty dict, 0 points
            },
            completion_rate=50.0,
            chat_turn_count=5,
        )
        # Only MBTI should contribute (25 points)
        assert quality.completeness_score == 25
        # Should suggest completing saju
        assert any("saju" in s.lower() for s in quality.suggestions)

    def test_meaningful_data_adds_completeness(self):
        """Only meaningful (non-empty) values should contribute to completeness."""
        quality = assess_mirror_profile_quality(
            mbti="INTJ",  # 25 points
            persona_data={
                "saju": {"year_pillar": "甲子", "month_pillar": ""},  # One meaningful value, 25 points
                "input": {"mbti": "INTJ", "blood_type": ""},  # One meaningful value, 15 points
                "persona": {"archetype": ""},  # All empty, 0 points
                "preferences": {"genre": "sci-fi"},  # One meaningful value, 15 points
            },
            completion_rate=50.0,
            chat_turn_count=5,
        )
        # MBTI + saju + input + preferences = 25+25+15+15 = 80
        assert quality.completeness_score == 80


# ============================================================================
# 2026 Enhancements: Response Model Tests
# ============================================================================

class TestMirrorInitResponse2026:
    """Tests for MirrorInitResponse with 2026 fields."""

    def test_response_with_2026_fields(self):
        response = MirrorInitResponse(
            success=True,
            session_id="test-session",
            saju={"year_pillar": "甲子"},
            initial_message="Welcome",
            persona_data={},
            completion_rate=25.0,
            trace_id="trace-123",
            evidence_refs=["rag:mirror:mbti_profile:intj"],
            profile_quality=MirrorProfileQuality(
                creativity_index=2.0,
                creative_style="logical_architect",
            ),
        )
        assert response.trace_id == "trace-123"
        assert len(response.evidence_refs) == 1
        assert response.profile_quality.creativity_index == 2.0

    def test_response_default_2026_fields(self):
        response = MirrorInitResponse(
            success=True,
            session_id="test",
            saju={},
            initial_message="msg",
            persona_data={},
            completion_rate=0.0,
        )
        assert response.trace_id == ""
        assert response.evidence_refs == []
        assert response.profile_quality is None


class TestMirrorChatResponse2026:
    """Tests for MirrorChatResponse with 2026 fields."""

    def test_response_with_profile_quality(self):
        response = MirrorChatResponse(
            success=True,
            ai_response="Hello",
            persona_data={},
            completion_rate=50.0,
            current_stage="psychology",
            is_complete=False,
            trace_id="trace-456",
            evidence_refs=["db:mirror:session:xyz"],
            confidence=0.75,
            profile_quality=MirrorProfileQuality(
                overall_score=75,
                creativity_index=3.5,
                creative_style="visionary_storyteller",
            ),
        )
        assert response.profile_quality.overall_score == 75
        assert response.confidence == 0.75

    def test_response_default_profile_quality(self):
        response = MirrorChatResponse(
            success=True,
            ai_response="msg",
            persona_data={},
            completion_rate=0.0,
            current_stage="intro",
            is_complete=False,
        )
        assert response.profile_quality is None


# ============================================================================
# 2026 Dimension Score Constants Tests
# ============================================================================

class TestMBTIDimensionScores:
    """Tests for MBTI dimension score constants."""

    def test_ei_dimension_scores(self):
        assert MBTI_DIMENSION_SCORES["E"] == 0
        assert MBTI_DIMENSION_SCORES["I"] == 1

    def test_sn_dimension_scores(self):
        assert MBTI_DIMENSION_SCORES["S"] == 0
        assert MBTI_DIMENSION_SCORES["N"] == 1

    def test_tf_dimension_scores(self):
        assert MBTI_DIMENSION_SCORES["T"] == 0
        assert MBTI_DIMENSION_SCORES["F"] == 1

    def test_jp_dimension_scores(self):
        assert MBTI_DIMENSION_SCORES["J"] == 0
        assert MBTI_DIMENSION_SCORES["P"] == 1

    def test_all_8_chars_mapped(self):
        expected = {"E", "I", "S", "N", "T", "F", "J", "P"}
        assert set(MBTI_DIMENSION_SCORES.keys()) == expected


# ============================================================================
# 2026 MBTI-CI Formula Verification Tests
# ============================================================================

class TestMBTICIFormulaVerification:
    """Comprehensive tests to verify CI formula: 3*SN + JP - EI - 0.5*TF."""

    @pytest.mark.parametrize("mbti,expected_ci", [
        # Highest creativity (N + P dominant)
        ("ENTP", 4.0),   # 3*1 + 1 - 0 - 0.5*0 = 4.0
        ("ENFP", 3.5),   # 3*1 + 1 - 0 - 0.5*1 = 3.5
        ("INTP", 3.0),   # 3*1 + 1 - 1 - 0.5*0 = 3.0
        ("INFP", 2.5),   # 3*1 + 1 - 1 - 0.5*1 = 2.5
        # High creativity (N dominant)
        ("ENTJ", 3.0),   # 3*1 + 0 - 0 - 0.5*0 = 3.0
        ("ENFJ", 2.5),   # 3*1 + 0 - 0 - 0.5*1 = 2.5
        ("INTJ", 2.0),   # 3*1 + 0 - 1 - 0.5*0 = 2.0
        ("INFJ", 1.5),   # 3*1 + 0 - 1 - 0.5*1 = 1.5
        # Medium creativity (mixed)
        ("ESTP", 1.0),   # 3*0 + 1 - 0 - 0.5*0 = 1.0
        ("ESFP", 0.5),   # 3*0 + 1 - 0 - 0.5*1 = 0.5
        ("ISTP", 0.0),   # 3*0 + 1 - 1 - 0.5*0 = 0.0
        ("ISFP", -0.5),  # 3*0 + 1 - 1 - 0.5*1 = -0.5
        # Lower creativity (S + J dominant)
        ("ESTJ", 0.0),   # 3*0 + 0 - 0 - 0.5*0 = 0.0
        ("ESFJ", -0.5),  # 3*0 + 0 - 0 - 0.5*1 = -0.5
        ("ISTJ", -1.0),  # 3*0 + 0 - 1 - 0.5*0 = -1.0
        ("ISFJ", -1.5),  # 3*0 + 0 - 1 - 0.5*1 = -1.5
    ])
    def test_ci_formula_for_all_types(self, mbti, expected_ci):
        """Verify CI calculation for all 16 MBTI types."""
        ci = calculate_mbti_creativity_index(mbti)
        assert ci == expected_ci, f"CI for {mbti} should be {expected_ci}, got {ci}"

    def test_ci_formula_max_value(self):
        """Maximum CI is 4.0 (ENTP)."""
        max_ci = max(calculate_mbti_creativity_index(mbti) for mbti in MBTI_CREATIVE_STYLE_MAP.keys())
        assert max_ci == 4.0

    def test_ci_formula_min_value(self):
        """Minimum CI is -1.5 (ISFJ)."""
        min_ci = min(calculate_mbti_creativity_index(mbti) for mbti in MBTI_CREATIVE_STYLE_MAP.keys())
        assert min_ci == -1.5
