"""Comprehensive tests for Storyboard Sketcher router.

Test coverage:
- Sanitization functions
- Validation functions (shot type, camera movement, transitions, etc.)
- Request schema validation
- Response model validation
- Memory Bank models
- Consistency scoring
- Evidence refs format
- XSS prevention
- Edge cases
- Helper functions

2026 Best Practices:
- StoryMem Memory Bank pattern
- DINOv2 consistency scoring
- VideoMemory benchmark targets
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.storyboard import (
    # Constants
    ALLOWED_SHOT_TYPES,
    ALLOWED_CAMERA_MOVEMENTS,
    ALLOWED_CAMERA_ANGLES,
    ALLOWED_TRANSITIONS,
    ALLOWED_EXPORT_FORMATS,
    ALLOWED_LAYOUTS,
    CONSISTENCY_THRESHOLDS,
    MAX_PANELS_PER_REQUEST,
    MAX_DESCRIPTION_LENGTH,
    MAX_DIALOGUE_LENGTH,
    # Sanitization
    _sanitize_text_field,
    # Validation
    _validate_shot_type,
    _validate_camera_movement,
    _validate_camera_angle,
    _validate_transition,
    _validate_export_format,
    _validate_layout,
    # Request Models
    StoryboardSketchRequest,
    StoryboardRefineRequest,
    StoryboardExportRequest,
    ConsistencyCheckRequest,
    ShotInput,
    # Response Models
    StoryboardResponse,
    ExportResponse,
    PanelOutput,
    ConsistencyScore,
    # Memory Bank Models
    MemoryBank,
    CharacterReference,
    PropReference,
    BackgroundReference,
    # Helpers
    get_shot_type_full_name,
    get_movement_notation,
)


# ============================================================================
# Test Sanitization Functions
# ============================================================================

class TestSanitizeTextField:
    """Tests for _sanitize_text_field function."""

    def test_sanitize_empty_string(self):
        """Empty string returns default."""
        assert _sanitize_text_field("") == ""
        assert _sanitize_text_field("", default="default") == "default"

    def test_sanitize_whitespace_only(self):
        """Whitespace-only string returns default."""
        assert _sanitize_text_field("   ") == ""
        assert _sanitize_text_field("\n\t", default="fallback") == "fallback"

    def test_sanitize_normal_text(self):
        """Normal text passes through."""
        result = _sanitize_text_field("Hello World")
        assert result == "Hello World"

    def test_sanitize_removes_html_tags(self):
        """HTML tags are removed."""
        result = _sanitize_text_field("<b>Bold</b> text")
        assert "<b>" not in result
        assert "</b>" not in result
        assert "Bold" in result

    def test_sanitize_removes_script_tags(self):
        """Script tags are removed."""
        result = _sanitize_text_field("<script>alert('xss')</script>test")
        assert "<script>" not in result
        assert "test" in result

    def test_sanitize_escapes_html_entities(self):
        """HTML entities are escaped."""
        result = _sanitize_text_field("5 > 3 & 2 < 4")
        assert "&gt;" in result
        assert "&lt;" in result
        assert "&amp;" in result

    def test_sanitize_removes_javascript_protocol(self):
        """javascript: protocol is removed."""
        result = _sanitize_text_field("javascript:alert(1)")
        assert "javascript:" not in result

    def test_sanitize_removes_event_handlers(self):
        """Event handlers are removed."""
        result = _sanitize_text_field("onclick=alert(1)")
        assert "onclick=" not in result
        result2 = _sanitize_text_field("onmouseover=bad()")
        assert "onmouseover=" not in result2

    def test_sanitize_preserves_korean(self):
        """Korean text is preserved."""
        result = _sanitize_text_field("한글 텍스트 테스트")
        assert "한글" in result
        assert "텍스트" in result


# ============================================================================
# Test Validation Functions
# ============================================================================

class TestValidateShotType:
    """Tests for _validate_shot_type function."""

    def test_valid_shot_types(self):
        """All valid shot types pass validation."""
        for shot_type in ALLOWED_SHOT_TYPES:
            result = _validate_shot_type(shot_type)
            assert result == shot_type

    def test_case_insensitive(self):
        """Shot type validation is case-insensitive."""
        assert _validate_shot_type("MS") == "ms"
        assert _validate_shot_type("Cu") == "cu"
        assert _validate_shot_type("OTS") == "ots"

    def test_strips_whitespace(self):
        """Whitespace is stripped."""
        assert _validate_shot_type("  ms  ") == "ms"

    def test_invalid_shot_type_raises(self):
        """Invalid shot type raises ValueError."""
        with pytest.raises(ValueError) as exc:
            _validate_shot_type("invalid_shot")
        assert "지원하지 않는 샷 타입" in str(exc.value)


class TestValidateCameraMovement:
    """Tests for _validate_camera_movement function."""

    def test_valid_movements(self):
        """All valid camera movements pass."""
        for movement in ALLOWED_CAMERA_MOVEMENTS:
            result = _validate_camera_movement(movement)
            assert result == movement

    def test_dolly_zoom(self):
        """Special movement: dolly_zoom (Vertigo effect)."""
        assert _validate_camera_movement("dolly_zoom") == "dolly_zoom"

    def test_invalid_movement_raises(self):
        """Invalid movement raises ValueError."""
        with pytest.raises(ValueError) as exc:
            _validate_camera_movement("fly_through")
        assert "지원하지 않는 카메라 무브먼트" in str(exc.value)


class TestValidateCameraAngle:
    """Tests for _validate_camera_angle function."""

    def test_valid_angles(self):
        """All valid angles pass."""
        for angle in ALLOWED_CAMERA_ANGLES:
            result = _validate_camera_angle(angle)
            assert result == angle

    def test_dutch_angle(self):
        """Dutch angle is valid."""
        assert _validate_camera_angle("dutch_angle") == "dutch_angle"

    def test_invalid_angle_raises(self):
        """Invalid angle raises ValueError."""
        with pytest.raises(ValueError):
            _validate_camera_angle("diagonal")


class TestValidateTransition:
    """Tests for _validate_transition function."""

    def test_valid_transitions(self):
        """All valid transitions pass."""
        for trans in ALLOWED_TRANSITIONS:
            result = _validate_transition(trans)
            assert result == trans

    def test_match_cut(self):
        """match_cut is valid."""
        assert _validate_transition("match_cut") == "match_cut"

    def test_invalid_transition_raises(self):
        """Invalid transition raises ValueError."""
        with pytest.raises(ValueError):
            _validate_transition("star_wipe")


class TestValidateExportFormat:
    """Tests for _validate_export_format function."""

    def test_valid_formats(self):
        """All valid formats pass."""
        for fmt in ALLOWED_EXPORT_FORMATS:
            result = _validate_export_format(fmt)
            assert result == fmt

    def test_invalid_format_raises(self):
        """Invalid format raises ValueError."""
        with pytest.raises(ValueError):
            _validate_export_format("mp4")


class TestValidateLayout:
    """Tests for _validate_layout function."""

    def test_valid_layouts(self):
        """All valid layouts pass."""
        for layout in ALLOWED_LAYOUTS:
            result = _validate_layout(layout)
            assert result == layout

    def test_invalid_layout_raises(self):
        """Invalid layout raises ValueError."""
        with pytest.raises(ValueError):
            _validate_layout("custom_12panel")


# ============================================================================
# Test Helper Functions
# ============================================================================

class TestGetShotTypeFullName:
    """Tests for get_shot_type_full_name function."""

    def test_known_shot_types(self):
        """Known shot types return full names."""
        assert get_shot_type_full_name("ms") == "Medium Shot"
        assert get_shot_type_full_name("cu") == "Close-Up"
        assert get_shot_type_full_name("ews") == "Extreme Wide Shot"
        assert get_shot_type_full_name("ots") == "Over-the-Shoulder"

    def test_unknown_returns_uppercase(self):
        """Unknown shot type returns uppercase abbreviation."""
        result = get_shot_type_full_name("xyz")
        assert result == "XYZ"


class TestGetMovementNotation:
    """Tests for get_movement_notation function."""

    def test_static_notation(self):
        """Static movement returns simple dot."""
        assert get_movement_notation("static") == "●"

    def test_dolly_in_notation(self):
        """Dolly in shows forward movement."""
        assert get_movement_notation("dolly_in") == "→●"

    def test_pan_notations(self):
        """Pan movements show direction."""
        assert get_movement_notation("pan_left") == "←●"
        assert get_movement_notation("pan_right") == "●→"

    def test_zoom_notations(self):
        """Zoom uses special symbols."""
        assert "⊕" in get_movement_notation("zoom_in")
        assert "⊖" in get_movement_notation("zoom_out")

    def test_unknown_returns_default(self):
        """Unknown movement returns default dot."""
        assert get_movement_notation("unknown") == "●"


# ============================================================================
# Test Request Models
# ============================================================================

class TestShotInput:
    """Tests for ShotInput model."""

    def test_valid_shot_input(self):
        """Valid shot input passes validation."""
        shot = ShotInput(
            shot_number=1,
            scene_number=1,
            shot_type="ms",
            camera_angle="eye_level",
            camera_movement="static",
            description="A character enters the room.",
            duration=3.0,
        )
        assert shot.shot_number == 1
        assert shot.shot_type == "ms"

    def test_sanitizes_description(self):
        """Description is sanitized."""
        shot = ShotInput(
            shot_number=1,
            description="<script>alert('xss')</script>Normal text",
        )
        assert "<script>" not in shot.description
        assert "Normal text" in shot.description

    def test_sanitizes_dialogue(self):
        """Dialogue is sanitized."""
        shot = ShotInput(
            shot_number=1,
            description="Test",
            dialogue="<b>Bold</b> speech",
        )
        assert "<b>" not in shot.dialogue

    def test_validates_shot_type(self):
        """Invalid shot type raises error."""
        with pytest.raises(ValidationError):
            ShotInput(
                shot_number=1,
                description="Test",
                shot_type="invalid",
            )

    def test_validates_camera_movement(self):
        """Invalid camera movement raises error."""
        with pytest.raises(ValidationError):
            ShotInput(
                shot_number=1,
                description="Test",
                camera_movement="fly",
            )

    def test_validates_transition(self):
        """Invalid transition raises error."""
        with pytest.raises(ValidationError):
            ShotInput(
                shot_number=1,
                description="Test",
                transition="star_wipe",
            )

    def test_duration_bounds(self):
        """Duration has min/max bounds."""
        # Too short
        with pytest.raises(ValidationError):
            ShotInput(shot_number=1, description="Test", duration=0.1)
        # Too long
        with pytest.raises(ValidationError):
            ShotInput(shot_number=1, description="Test", duration=100)

    def test_shot_number_bounds(self):
        """Shot number has bounds."""
        with pytest.raises(ValidationError):
            ShotInput(shot_number=0, description="Test")
        with pytest.raises(ValidationError):
            ShotInput(shot_number=1000, description="Test")


class TestStoryboardSketchRequest:
    """Tests for StoryboardSketchRequest model."""

    def test_valid_request(self):
        """Valid request passes validation."""
        req = StoryboardSketchRequest(
            project_name="Test Project",
            shots=[
                ShotInput(shot_number=1, description="Shot 1"),
                ShotInput(shot_number=2, description="Shot 2"),
            ],
            style_preset="cinematic",
            aspect_ratio="16:9",
        )
        assert req.project_name == "Test Project"
        assert len(req.shots) == 2

    def test_sanitizes_project_name(self):
        """Project name is sanitized."""
        req = StoryboardSketchRequest(
            project_name="<script>bad</script>Good Name",
            shots=[ShotInput(shot_number=1, description="Test")],
        )
        assert "<script>" not in req.project_name

    def test_requires_at_least_one_shot(self):
        """At least one shot is required."""
        with pytest.raises(ValidationError):
            StoryboardSketchRequest(
                project_name="Test",
                shots=[],
            )

    def test_max_panels_limit(self):
        """Maximum panels limit is enforced."""
        shots = [ShotInput(shot_number=i, description=f"Shot {i}") for i in range(1, MAX_PANELS_PER_REQUEST + 2)]
        with pytest.raises(ValidationError):
            StoryboardSketchRequest(
                project_name="Test",
                shots=shots,
            )

    def test_validates_language(self):
        """Language is validated."""
        with pytest.raises(ValidationError):
            StoryboardSketchRequest(
                project_name="Test",
                shots=[ShotInput(shot_number=1, description="Test")],
                language="invalid",
            )

    def test_validates_model(self):
        """Model is validated."""
        with pytest.raises(ValidationError):
            StoryboardSketchRequest(
                project_name="Test",
                shots=[ShotInput(shot_number=1, description="Test")],
                model="invalid-model",
            )

    def test_consistency_threshold_bounds(self):
        """Consistency threshold has bounds."""
        with pytest.raises(ValidationError):
            StoryboardSketchRequest(
                project_name="Test",
                shots=[ShotInput(shot_number=1, description="Test")],
                consistency_threshold=1.5,
            )


class TestStoryboardRefineRequest:
    """Tests for StoryboardRefineRequest model."""

    def test_valid_refine_request(self):
        """Valid refine request passes."""
        req = StoryboardRefineRequest(
            panel_ids=[1, 2, 3],
            adjustment_notes="Make it brighter",
        )
        assert len(req.panel_ids) == 3

    def test_requires_panel_ids(self):
        """At least one panel ID required."""
        with pytest.raises(ValidationError):
            StoryboardRefineRequest(panel_ids=[])

    def test_max_panel_ids(self):
        """Maximum 10 panel IDs."""
        with pytest.raises(ValidationError):
            StoryboardRefineRequest(panel_ids=list(range(11)))

    def test_sanitizes_notes(self):
        """Notes are sanitized."""
        req = StoryboardRefineRequest(
            panel_ids=[1],
            adjustment_notes="<script>bad</script>Good notes",
        )
        assert "<script>" not in req.adjustment_notes


class TestStoryboardExportRequest:
    """Tests for StoryboardExportRequest model."""

    def test_valid_export_request(self):
        """Valid export request passes."""
        req = StoryboardExportRequest(
            session_id="abc-123",
            export_format="pdf",
            layout_template="standard_6panel",
        )
        assert req.export_format == "pdf"

    def test_validates_format(self):
        """Export format is validated."""
        with pytest.raises(ValidationError):
            StoryboardExportRequest(
                session_id="abc",
                export_format="mp4",
            )

    def test_validates_layout(self):
        """Layout is validated."""
        with pytest.raises(ValidationError):
            StoryboardExportRequest(
                session_id="abc",
                layout_template="custom",
            )

    def test_animatic_fps_bounds(self):
        """Animatic FPS has bounds."""
        with pytest.raises(ValidationError):
            StoryboardExportRequest(
                session_id="abc",
                animatic_fps=0,
            )
        with pytest.raises(ValidationError):
            StoryboardExportRequest(
                session_id="abc",
                animatic_fps=120,
            )


class TestConsistencyCheckRequest:
    """Tests for ConsistencyCheckRequest model."""

    def test_valid_request(self):
        """Valid request passes."""
        req = ConsistencyCheckRequest(
            panel_images=["img1.png", "img2.png"],
            entity_type="character",
        )
        assert len(req.panel_images) == 2

    def test_requires_minimum_images(self):
        """At least 2 images required."""
        with pytest.raises(ValidationError):
            ConsistencyCheckRequest(
                panel_images=["img1.png"],
                entity_type="character",
            )


# ============================================================================
# Test Memory Bank Models
# ============================================================================

class TestCharacterReference:
    """Tests for CharacterReference model."""

    def test_valid_character(self):
        """Valid character reference passes."""
        char = CharacterReference(
            character_id="char_001",
            character_name="John Doe",
            description="Main protagonist",
            reference_images=["img1.png", "img2.png"],
        )
        assert char.character_id == "char_001"

    def test_sanitizes_name(self):
        """Character name is sanitized."""
        char = CharacterReference(
            character_id="c1",
            character_name="<b>Bold</b> Name",
        )
        assert "<b>" not in char.character_name

    def test_reference_images_limit(self):
        """Reference images have max limit."""
        # This should work (at limit)
        char = CharacterReference(
            character_id="c1",
            character_name="Test",
            reference_images=["img"] * 10,
        )
        assert len(char.reference_images) == 10


class TestPropReference:
    """Tests for PropReference model."""

    def test_valid_prop(self):
        """Valid prop reference passes."""
        prop = PropReference(
            prop_id="prop_001",
            prop_name="Magic Wand",
            importance="key",
        )
        assert prop.importance == "key"

    def test_sanitizes_name(self):
        """Prop name is sanitized."""
        prop = PropReference(
            prop_id="p1",
            prop_name="<script>bad</script>Sword",
        )
        assert "<script>" not in prop.prop_name


class TestBackgroundReference:
    """Tests for BackgroundReference model."""

    def test_valid_background(self):
        """Valid background reference passes."""
        bg = BackgroundReference(
            location_id="loc_001",
            location_name="City Rooftop",
            time_of_day="dusk",
            weather="clear",
            lighting="dramatic",
        )
        assert bg.time_of_day == "dusk"

    def test_sanitizes_name(self):
        """Location name is sanitized."""
        bg = BackgroundReference(
            location_id="l1",
            location_name="<b>Bold</b> Location",
        )
        assert "<b>" not in bg.location_name


class TestMemoryBank:
    """Tests for MemoryBank model."""

    def test_empty_memory_bank(self):
        """Empty memory bank is valid."""
        mb = MemoryBank()
        assert len(mb.characters) == 0
        assert len(mb.props) == 0
        assert len(mb.backgrounds) == 0

    def test_memory_bank_with_data(self):
        """Memory bank with data is valid."""
        mb = MemoryBank(
            session_id="session-123",
            characters=[
                CharacterReference(character_id="c1", character_name="Char1"),
            ],
            props=[
                PropReference(prop_id="p1", prop_name="Prop1"),
            ],
            backgrounds=[
                BackgroundReference(location_id="l1", location_name="Loc1"),
            ],
            style_guide="Cinematic noir style",
        )
        assert len(mb.characters) == 1
        assert len(mb.props) == 1
        assert len(mb.backgrounds) == 1


# ============================================================================
# Test Response Models
# ============================================================================

class TestConsistencyScore:
    """Tests for ConsistencyScore model."""

    def test_valid_score(self):
        """Valid consistency score passes."""
        score = ConsistencyScore(
            entity_type="character",
            entity_id="char_001",
            panel_pair=[1, 2],
            similarity_score=0.75,
            passed=True,
        )
        assert score.similarity_score == 0.75

    def test_with_suggestion(self):
        """Score with suggestion is valid."""
        score = ConsistencyScore(
            entity_type="prop",
            entity_id="prop_001",
            panel_pair=[3, 4],
            similarity_score=0.45,
            passed=False,
            suggestion="Consider regenerating panel 4",
        )
        assert score.suggestion is not None


class TestPanelOutput:
    """Tests for PanelOutput model."""

    def test_valid_panel(self):
        """Valid panel output passes."""
        panel = PanelOutput(
            panel_number=1,
            shot_number=1,
            scene_number=1,
            shot_type="ms",
            shot_type_full="Medium Shot",
            camera_angle="eye_level",
            camera_movement="static",
            movement_notation="●",
            description="Test description",
            action="Character walks",
            duration=3.0,
            transition="cut",
        )
        assert panel.panel_number == 1

    def test_with_optional_fields(self):
        """Panel with optional fields is valid."""
        panel = PanelOutput(
            panel_number=1,
            shot_number=1,
            scene_number=1,
            shot_type="cu",
            shot_type_full="Close-Up",
            camera_angle="low_angle",
            camera_movement="dolly_in",
            movement_notation="→●",
            description="Intense close-up",
            action="",
            dialogue="Hello there.",
            duration=2.0,
            transition="dissolve",
            image_url="https://example.com/panel.png",
            thumbnail_url="https://example.com/thumb.png",
            characters_in_shot=["char_001"],
            consistency_scores=[],
            generation_metadata={"style": "noir"},
        )
        assert panel.dialogue == "Hello there."
        assert panel.image_url is not None


class TestStoryboardResponse:
    """Tests for StoryboardResponse model."""

    def test_valid_response(self):
        """Valid storyboard response passes."""
        resp = StoryboardResponse(
            success=True,
            session_id="session-123",
            project_name="Test Project",
            total_panels=5,
            total_duration=15.0,
            panels=[],
            evidence_refs=["rag:storyboard:composition_rules"],
        )
        assert resp.success is True
        assert resp.session_id == "session-123"

    def test_with_consistency_report(self):
        """Response with consistency report is valid."""
        resp = StoryboardResponse(
            success=True,
            session_id="s123",
            project_name="Test",
            total_panels=2,
            total_duration=6.0,
            panels=[],
            consistency_report={
                "enabled": True,
                "threshold": 0.6,
                "checks_performed": 4,
                "passed": 3,
                "failed": 1,
            },
            evidence_refs=[],
        )
        assert resp.consistency_report["passed"] == 3


class TestExportResponse:
    """Tests for ExportResponse model."""

    def test_valid_export_response(self):
        """Valid export response passes."""
        resp = ExportResponse(
            success=True,
            export_format="pdf",
            file_url="https://example.com/storyboard.pdf",
            file_size_bytes=1024000,
            page_count=5,
        )
        assert resp.file_url is not None


# ============================================================================
# Test Evidence Refs Format
# ============================================================================

class TestEvidenceRefs:
    """Tests for evidence_refs format."""

    def test_evidence_refs_list_str(self):
        """Evidence refs are List[str]."""
        resp = StoryboardResponse(
            success=True,
            session_id="s1",
            project_name="Test",
            total_panels=1,
            total_duration=1.0,
            panels=[],
            evidence_refs=[
                "rag:storyboard:composition_rules",
                "rag:storyboard:shot_type_visual_guide",
                "db:memory_bank:session-123",
            ],
        )
        assert isinstance(resp.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in resp.evidence_refs)

    def test_evidence_refs_prefix_patterns(self):
        """Evidence refs follow prefix patterns."""
        valid_refs = [
            "rag:storyboard:rule_id",
            "db:memory_bank:session_id",
            "db:storyboard_exports:export_id",
            "rag:dinov2:consistency_scoring",
        ]
        for ref in valid_refs:
            parts = ref.split(":")
            assert len(parts) >= 2
            assert parts[0] in ("rag", "db", "qdrant")


# ============================================================================
# Test Constants
# ============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_shot_types_not_empty(self):
        """Shot types constant is not empty."""
        assert len(ALLOWED_SHOT_TYPES) > 0
        assert "ms" in ALLOWED_SHOT_TYPES
        assert "cu" in ALLOWED_SHOT_TYPES

    def test_camera_movements_not_empty(self):
        """Camera movements constant is not empty."""
        assert len(ALLOWED_CAMERA_MOVEMENTS) > 0
        assert "static" in ALLOWED_CAMERA_MOVEMENTS
        assert "dolly_in" in ALLOWED_CAMERA_MOVEMENTS

    def test_consistency_thresholds(self):
        """Consistency thresholds match VideoMemory benchmark."""
        assert CONSISTENCY_THRESHOLDS["character"] == 0.63
        assert CONSISTENCY_THRESHOLDS["prop"] == 0.58
        assert CONSISTENCY_THRESHOLDS["background"] == 0.72

    def test_max_limits(self):
        """Max limits are reasonable."""
        assert MAX_PANELS_PER_REQUEST == 50
        assert MAX_DESCRIPTION_LENGTH == 2000
        assert MAX_DIALOGUE_LENGTH == 500


# ============================================================================
# Test XSS Prevention
# ============================================================================

class TestXSSPrevention:
    """Tests for XSS prevention in all text fields."""

    def test_project_name_xss(self):
        """XSS in project name is prevented."""
        req = StoryboardSketchRequest(
            project_name="<img src=x onerror=alert(1)>Project",
            shots=[ShotInput(shot_number=1, description="Test")],
        )
        assert "<img" not in req.project_name
        assert "onerror=" not in req.project_name

    def test_description_xss(self):
        """XSS in description is prevented."""
        shot = ShotInput(
            shot_number=1,
            description="<svg onload=alert(1)>Normal",
        )
        assert "<svg" not in shot.description
        assert "onload=" not in shot.description

    def test_dialogue_xss(self):
        """XSS in dialogue is prevented."""
        shot = ShotInput(
            shot_number=1,
            description="Test",
            dialogue="<iframe src=evil.com>",
        )
        assert "<iframe" not in shot.dialogue

    def test_action_xss(self):
        """XSS in action is prevented."""
        shot = ShotInput(
            shot_number=1,
            description="Test",
            action="<a href='javascript:alert(1)'>click</a>",
        )
        assert "javascript:" not in shot.action

    def test_style_guide_xss(self):
        """XSS in style guide is prevented."""
        mb = MemoryBank(
            style_guide="<script>document.cookie</script>Style guide",
        )
        assert "<script>" not in mb.style_guide

    def test_character_name_xss(self):
        """XSS in character name is prevented."""
        char = CharacterReference(
            character_id="c1",
            character_name="<body onload=alert(1)>Hero",
        )
        assert "onload=" not in char.character_name


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_shot_request(self):
        """Single shot request is valid."""
        req = StoryboardSketchRequest(
            shots=[ShotInput(shot_number=1, description="Only shot")],
        )
        assert len(req.shots) == 1

    def test_long_description(self):
        """Long description up to limit works."""
        long_desc = "A" * MAX_DESCRIPTION_LENGTH
        shot = ShotInput(shot_number=1, description=long_desc)
        assert len(shot.description) == MAX_DESCRIPTION_LENGTH

    def test_description_over_limit(self):
        """Description over limit raises error."""
        with pytest.raises(ValidationError):
            ShotInput(shot_number=1, description="A" * (MAX_DESCRIPTION_LENGTH + 1))

    def test_unicode_characters(self):
        """Unicode characters are preserved."""
        shot = ShotInput(
            shot_number=1,
            description="日本語テスト 🎬 한글",
        )
        assert "日本語" in shot.description
        assert "한글" in shot.description

    def test_empty_optional_fields(self):
        """Empty optional fields use defaults."""
        shot = ShotInput(shot_number=1, description="Test")
        assert shot.dialogue == ""
        assert shot.action == ""
        assert shot.characters_in_shot == []

    def test_all_shot_types(self):
        """All shot types can be used in requests."""
        for st in ALLOWED_SHOT_TYPES:
            shot = ShotInput(shot_number=1, description="Test", shot_type=st)
            assert shot.shot_type == st

    def test_all_camera_movements(self):
        """All camera movements can be used."""
        for mv in ALLOWED_CAMERA_MOVEMENTS:
            shot = ShotInput(shot_number=1, description="Test", camera_movement=mv)
            assert shot.camera_movement == mv

    def test_special_characters_in_dialogue(self):
        """Special characters in dialogue are handled."""
        shot = ShotInput(
            shot_number=1,
            description="Test",
            dialogue='"Hello," she said. "What\'s your name?"',
        )
        assert "Hello" in shot.dialogue
        assert "name" in shot.dialogue


# ============================================================================
# Test Memory Bank Features (StoryMem Pattern)
# ============================================================================

class TestMemoryBankFeatures:
    """Tests for Memory Bank StoryMem pattern features."""

    def test_memory_bank_max_characters(self):
        """Memory bank has character limit."""
        # Should work at limit (20)
        chars = [
            CharacterReference(character_id=f"c{i}", character_name=f"Char{i}")
            for i in range(20)
        ]
        mb = MemoryBank(characters=chars)
        assert len(mb.characters) == 20

    def test_memory_bank_max_props(self):
        """Memory bank has prop limit."""
        # Should work at limit (30)
        props = [
            PropReference(prop_id=f"p{i}", prop_name=f"Prop{i}")
            for i in range(30)
        ]
        mb = MemoryBank(props=props)
        assert len(mb.props) == 30

    def test_memory_bank_max_backgrounds(self):
        """Memory bank has background limit."""
        # Should work at limit (10)
        bgs = [
            BackgroundReference(location_id=f"l{i}", location_name=f"Loc{i}")
            for i in range(10)
        ]
        mb = MemoryBank(backgrounds=bgs)
        assert len(mb.backgrounds) == 10

    def test_character_reference_images_format(self):
        """Character reference images can be URLs or base64."""
        char = CharacterReference(
            character_id="c1",
            character_name="Test",
            reference_images=[
                "https://example.com/img1.png",
                "data:image/png;base64,iVBORw0KGg...",
            ],
        )
        assert len(char.reference_images) == 2

    def test_memory_bank_session_id(self):
        """Memory bank can have session ID for continuation."""
        mb = MemoryBank(session_id="session-abc-123")
        assert mb.session_id == "session-abc-123"


# ============================================================================
# Test Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Tests for realistic integration scenarios."""

    def test_full_storyboard_request(self):
        """Full storyboard request with all features."""
        req = StoryboardSketchRequest(
            project_name="My Film Project",
            shots=[
                ShotInput(
                    shot_number=1,
                    scene_number=1,
                    shot_type="ews",
                    camera_angle="high_angle",
                    camera_movement="crane_down",
                    description="Establishing shot of the city skyline at dusk",
                    duration=5.0,
                    transition="dissolve",
                    location_id="loc_city",
                ),
                ShotInput(
                    shot_number=2,
                    scene_number=1,
                    shot_type="ms",
                    camera_angle="eye_level",
                    camera_movement="dolly_in",
                    description="Hero walks through the crowded street",
                    action="Hero pushes through the crowd",
                    dialogue="(내레이션) 그날 밤, 모든 것이 바뀌었다.",
                    duration=4.0,
                    transition="cut",
                    characters_in_shot=["hero"],
                    location_id="loc_city",
                ),
                ShotInput(
                    shot_number=3,
                    scene_number=1,
                    shot_type="cu",
                    camera_angle="low_angle",
                    camera_movement="static",
                    description="Close-up on hero's determined face",
                    duration=2.0,
                    transition="cut",
                    characters_in_shot=["hero"],
                ),
            ],
            memory_bank=MemoryBank(
                characters=[
                    CharacterReference(
                        character_id="hero",
                        character_name="Jin",
                        description="Main protagonist, 30s, determined expression",
                        reference_images=["hero_ref1.png", "hero_ref2.png"],
                    ),
                ],
                backgrounds=[
                    BackgroundReference(
                        location_id="loc_city",
                        location_name="Seoul City Center",
                        time_of_day="dusk",
                        weather="clear",
                        lighting="dramatic",
                    ),
                ],
                style_guide="Cinematic noir with high contrast, inspired by Park Chan-wook",
            ),
            style_preset="cinematic_noir",
            aspect_ratio="2.39:1",
            enable_consistency_check=True,
            consistency_threshold=0.65,
            language="ko",
            model="gemini-3-pro-preview",
        )

        assert req.project_name == "My Film Project"
        assert len(req.shots) == 3
        assert req.memory_bank is not None
        assert len(req.memory_bank.characters) == 1
        assert req.memory_bank.characters[0].character_id == "hero"

    def test_export_workflow(self):
        """Export workflow request."""
        export_req = StoryboardExportRequest(
            session_id="session-full-123",
            export_format="pdf",
            layout_template="cinematic_3panel",
            include_dialogue=True,
            include_camera_notes=True,
            include_audio_notes=False,
        )
        assert export_req.layout_template == "cinematic_3panel"

    def test_consistency_check_workflow(self):
        """Consistency check between panels."""
        check_req = ConsistencyCheckRequest(
            panel_images=[
                "panel1.png",
                "panel2.png",
                "panel3.png",
            ],
            entity_type="character",
            threshold=0.63,
        )
        assert len(check_req.panel_images) == 3
        assert check_req.threshold == 0.63


# ============================================================================
# Test Model Serialization
# ============================================================================

class TestModelSerialization:
    """Tests for model JSON serialization."""

    def test_shot_input_to_dict(self):
        """ShotInput can be serialized to dict."""
        shot = ShotInput(shot_number=1, description="Test")
        data = shot.model_dump()
        assert data["shot_number"] == 1
        assert "description" in data

    def test_memory_bank_to_dict(self):
        """MemoryBank can be serialized to dict."""
        mb = MemoryBank(
            session_id="s1",
            characters=[CharacterReference(character_id="c1", character_name="Test")],
        )
        data = mb.model_dump()
        assert data["session_id"] == "s1"
        assert len(data["characters"]) == 1

    def test_panel_output_to_dict(self):
        """PanelOutput can be serialized to dict."""
        panel = PanelOutput(
            panel_number=1,
            shot_number=1,
            scene_number=1,
            shot_type="ms",
            shot_type_full="Medium Shot",
            camera_angle="eye_level",
            camera_movement="static",
            movement_notation="●",
            description="Test",
            action="",
            duration=3.0,
            transition="cut",
        )
        data = panel.model_dump()
        assert data["panel_number"] == 1
        assert data["movement_notation"] == "●"

    def test_response_to_dict(self):
        """StoryboardResponse can be serialized to dict."""
        resp = StoryboardResponse(
            success=True,
            session_id="s1",
            project_name="Test",
            total_panels=1,
            total_duration=3.0,
            panels=[],
            evidence_refs=["rag:test"],
        )
        data = resp.model_dump()
        assert data["success"] is True
        assert "evidence_refs" in data
