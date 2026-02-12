"""Tests for AD Studio — Assistant Director Dimension App.

Tests cover:
- Pydantic model validation (request/response)
- Router endpoint signatures
- Sanitization and content size validation
- Technique corpus loading and query
- Prompt engine generation
- Adapter prompt generation (Kling/Seedance)
- AD Brain building helpers
- RAG preset configuration
- Registration in dimension system
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.dimension_adapter import DimensionCapsuleId
from app.routers.dimension._base import (
    sanitize_generic_text,
    validate_content_size,
    DIMENSION_NAMES,
    CAPSULE_TO_DIMENSION,
    get_credit_cost,
    _validate_language,
    _validate_model,
)
from app.routers.dimension.ad_studio import (
    # Request models
    ADStudioScenarioRequest,
    ADStudioVideoRequest,
    # Response models
    ADStudioResponse,
    SequenceAnalysis,
    SceneAnalysis,
    SequenceContext,
    SceneTechniques,
    TechniqueTag,
    EnginePrompts,
    EmotionalBeat,
    VisualRhythm,
    ColorBeat,
    ContinuityAnchors,
    TechniqueInfo,
    # Router
    router,
    # Constants
    ALLOWED_ENGINES,
    MAX_SCENARIO_LENGTH,
)


# =============================================================================
# Registration Tests
# =============================================================================


class TestADStudioRegistration:
    """Verify AD Studio is properly registered in the dimension system."""

    def test_capsule_id_exists(self):
        assert hasattr(DimensionCapsuleId, "AD_STUDIO_ANALYZE")
        assert DimensionCapsuleId.AD_STUDIO_ANALYZE.value == "ad-studio.analyze"

    def test_dimension_names_entry(self):
        assert "ad-studio" in DIMENSION_NAMES
        assert DIMENSION_NAMES["ad-studio"] == "AD Studio"

    def test_capsule_to_dimension_mapping(self):
        assert DimensionCapsuleId.AD_STUDIO_ANALYZE in CAPSULE_TO_DIMENSION
        assert CAPSULE_TO_DIMENSION[DimensionCapsuleId.AD_STUDIO_ANALYZE] == "AD_STUDIO"

    def test_credit_cost_flash(self):
        cost = get_credit_cost(
            DimensionCapsuleId.AD_STUDIO_ANALYZE, "gemini-3-flash-preview"
        )
        assert cost == 10

    def test_credit_cost_pro(self):
        cost = get_credit_cost(
            DimensionCapsuleId.AD_STUDIO_ANALYZE, "gemini-3-pro-preview"
        )
        assert cost == 30

    def test_router_prefix(self):
        assert router.prefix == "/ad-studio"

    def test_router_tags(self):
        assert "AD Studio" in router.tags

    def test_router_has_four_routes(self):
        paths = [r.path for r in router.routes]
        assert "/ad-studio/analyze" in paths
        assert "/ad-studio/analyze/stream" in paths
        assert "/ad-studio/analyze-video" in paths
        assert "/ad-studio/techniques" in paths


# =============================================================================
# RAG Preset Tests
# =============================================================================


class TestADStudioRAGPreset:
    """Verify RAG preset for AD_STUDIO."""

    def test_preset_exists(self):
        from app.rag.rag_presets import get_rag_preset

        preset = get_rag_preset("AD_STUDIO")
        assert preset is not None

    def test_preset_rag_enabled(self):
        from app.rag.rag_presets import get_rag_preset

        preset = get_rag_preset("AD_STUDIO")
        assert preset.rag_enabled is True

    def test_preset_confidence_threshold(self):
        from app.rag.rag_presets import get_rag_preset

        preset = get_rag_preset("AD_STUDIO")
        assert preset.confidence_threshold == 0.6

    def test_preset_corpus(self):
        from app.rag.rag_presets import get_rag_preset

        preset = get_rag_preset("AD_STUDIO")
        assert preset.dimension_corpus == "cinematic_techniques"


# =============================================================================
# Request Model Tests
# =============================================================================


class TestADStudioScenarioRequest:
    """Test scenario request validation."""

    def test_valid_request(self):
        req = ADStudioScenarioRequest(
            scenario="A man walks through a rainy alley at night, neon lights reflecting off puddles.",
        )
        assert req.language == "ko"
        assert req.model == "gemini-3-pro-preview"
        assert req.generate_video is False

    def test_default_engines(self):
        req = ADStudioScenarioRequest(
            scenario="A scene of tension building in a dark room.",
        )
        assert req.target_engines == ["kling", "seedance", "veo"]

    def test_custom_engines(self):
        req = ADStudioScenarioRequest(
            scenario="A peaceful sunset scene over the ocean.",
            target_engines=["kling"],
        )
        assert req.target_engines == ["kling"]

    def test_invalid_engine_raises(self):
        with pytest.raises(ValueError, match="Unsupported engine"):
            ADStudioScenarioRequest(
                scenario="Some scene description text here.",
                target_engines=["invalid_engine"],
            )

    def test_scenario_too_short(self):
        with pytest.raises(ValueError):
            ADStudioScenarioRequest(scenario="short")

    def test_style_hint_sanitized(self):
        req = ADStudioScenarioRequest(
            scenario="A dramatic confrontation in a dimly lit warehouse.",
            style_hint="  dark and moody  ",
        )
        assert req.style_hint is not None
        assert req.style_hint == "dark and moody"

    def test_style_hint_xss_sanitized(self):
        req = ADStudioScenarioRequest(
            scenario="A scene with bright colors and dynamic movement across the city.",
            style_hint="<script>alert('xss')</script>neon",
        )
        assert "<script>" not in (req.style_hint or "")

    def test_invalid_language(self):
        with pytest.raises(ValueError, match="지원하지 않는 언어"):
            ADStudioScenarioRequest(
                scenario="A beautiful scene with rolling hills.",
                language="fr",
            )

    def test_invalid_model(self):
        with pytest.raises(ValueError, match="지원하지 않는 모델"):
            ADStudioScenarioRequest(
                scenario="A beautiful scene with rolling hills.",
                model="gpt-4-invalid",
            )


class TestADStudioVideoRequest:
    """Test video request validation."""

    def test_valid_request(self):
        req = ADStudioVideoRequest(
            video_url="https://storage.example.com/video.mp4",
            scene_timestamps=["00:00-00:05", "00:05-00:12"],
        )
        assert req.video_url == "https://storage.example.com/video.mp4"
        assert len(req.scene_timestamps) == 2

    def test_invalid_url(self):
        with pytest.raises(ValueError, match="valid HTTP"):
            ADStudioVideoRequest(
                video_url="not-a-url",
                scene_timestamps=["00:00-00:05"],
            )

    def test_empty_timestamps_allowed(self):
        req = ADStudioVideoRequest(
            video_url="https://example.com/video.mp4",
        )
        assert req.scene_timestamps == []

    def test_url_whitespace_stripped(self):
        req = ADStudioVideoRequest(
            video_url="  https://example.com/video.mp4  ",
        )
        assert req.video_url == "https://example.com/video.mp4"


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Test response model construction."""

    def test_emotional_beat(self):
        beat = EmotionalBeat(
            scene_number=1,
            emotion="긴장",
            intensity=0.8,
            description="갈등이 고조되는 순간",
        )
        assert beat.scene_number == 1
        assert beat.intensity == 0.8

    def test_emotional_beat_intensity_bounds(self):
        with pytest.raises(ValueError):
            EmotionalBeat(
                scene_number=1,
                emotion="분노",
                intensity=1.5,
                description="범위 초과",
            )

    def test_color_beat(self):
        cb = ColorBeat(
            scene_number=1,
            temperature="warm",
            palette="따뜻한 황금빛 톤",
        )
        assert cb.temperature == "warm"
        assert cb.hex_hint is None

    def test_visual_rhythm(self):
        vr = VisualRhythm(
            camera_distance_curve=["WS", "MS", "CU", "ECU"],
            edit_tempo="점점 빨라지는 편집 리듬",
        )
        assert len(vr.camera_distance_curve) == 4

    def test_continuity_anchors(self):
        ca = ContinuityAnchors(
            character_anchors=["검은 코트를 입은 남자"],
            style_anchors=["neo-noir"],
            lighting_anchors=["창문 역광"],
        )
        assert len(ca.character_anchors) == 1

    def test_scene_techniques(self):
        st = SceneTechniques(
            composition=[TechniqueTag(
                technique_id="rule_of_thirds",
                category="composition",
                name_ko="삼분법 구도",
                name_en="Rule of Thirds",
                description_ko="프레임을 삼등분하여 배치",
            )],
        )
        assert len(st.composition) == 1
        assert st.composition[0].technique_id == "rule_of_thirds"

    def test_sequence_context(self):
        ctx = SequenceContext(
            emotional_position="클라이맥스 직전",
            camera_distance_flow="이전 WS → 현재 CU → 다음 ECU",
        )
        assert ctx.previous_exit is None
        assert ctx.emotional_position == "클라이맥스 직전"

    def test_engine_prompts(self):
        ep = EnginePrompts(
            kling_3_0="A man in a dark coat, medium close-up, dim streetlight.",
            seedance_2_0="Cinematic low-angle shot of a solitary figure walking.",
        )
        assert "dark coat" in ep.kling_3_0

    def test_scene_analysis(self):
        scene = SceneAnalysis(
            scene_number=1,
            description="어두운 골목에서 남자가 걷고 있다",
            techniques=SceneTechniques(),
            sequence_context=SequenceContext(),
            prompts=EnginePrompts(),
        )
        assert scene.scene_number == 1

    def test_sequence_analysis(self):
        seq = SequenceAnalysis(
            emotional_arc=[
                EmotionalBeat(scene_number=1, emotion="평온", intensity=0.3, description="시작"),
                EmotionalBeat(scene_number=2, emotion="긴장", intensity=0.7, description="고조"),
            ],
        )
        assert len(seq.emotional_arc) == 2

    def test_ad_studio_response(self):
        resp = ADStudioResponse(
            success=True,
            sequence=SequenceAnalysis(),
            scenes=[],
            evidence_refs=["db:ad_studio:analysis:3_scenes", "model:gemini-3-pro-preview"],
        )
        assert resp.success is True
        assert len(resp.evidence_refs) == 2
        # evidence_refs must be List[str]
        assert all(isinstance(ref, str) for ref in resp.evidence_refs)

    def test_evidence_refs_type(self):
        """evidence_refs must always be List[str], never dict array."""
        resp = ADStudioResponse(
            evidence_refs=["db:ad_studio:test:1", "rag:technique:chiaroscuro"],
        )
        assert isinstance(resp.evidence_refs, list)
        assert all(isinstance(r, str) for r in resp.evidence_refs)

    def test_technique_info(self):
        info = TechniqueInfo(
            technique_id="dolly_in",
            category="camera_movement",
            name_ko="돌리 인",
            name_en="Dolly In",
            description_ko="카메라가 전진하며 긴장감을 고조",
            best_for=["emotional_climax", "revelation"],
        )
        assert info.technique_id == "dolly_in"
        assert len(info.best_for) == 2


# =============================================================================
# Cinematic Techniques Corpus Tests
# =============================================================================


class TestCinematicTechniques:
    """Test the cinematic techniques RAG layer."""

    def test_corpus_loads(self):
        from app.rag.cinematic_techniques import get_all_techniques

        techniques = get_all_techniques()
        assert len(techniques) >= 30

    def test_get_by_id(self):
        from app.rag.cinematic_techniques import get_technique_by_id

        t = get_technique_by_id("chiaroscuro")
        assert t is not None
        assert t.category == "lighting"
        assert t.name_en == "Chiaroscuro"

    def test_get_by_id_not_found(self):
        from app.rag.cinematic_techniques import get_technique_by_id

        t = get_technique_by_id("nonexistent_technique_xyz")
        assert t is None

    def test_filter_by_category(self):
        from app.rag.cinematic_techniques import get_all_techniques

        composition = get_all_techniques(category="composition")
        assert len(composition) >= 5
        assert all(t.category == "composition" for t in composition)

    def test_query_mood_tension(self):
        from app.rag.cinematic_techniques import query_techniques

        results = query_techniques("tension")
        assert len(results) > 0
        ids = [r.technique.technique_id for r in results]
        assert "slow_push_in" in ids or "chiaroscuro" in ids

    def test_query_mood_serenity(self):
        from app.rag.cinematic_techniques import query_techniques

        results = query_techniques("serenity")
        assert len(results) > 0

    def test_query_with_category_filter(self):
        from app.rag.cinematic_techniques import query_techniques

        results = query_techniques("tension", category="lighting")
        assert all(r.technique.category == "lighting" for r in results)

    def test_suggest_transitions(self):
        from app.rag.cinematic_techniques import suggest_transitions

        suggestions = suggest_transitions("tension", "serenity")
        assert len(suggestions) > 0
        assert all(s.technique.category == "transition" or s.score > 0 for s in suggestions)

    def test_technique_has_prompt_keywords(self):
        from app.rag.cinematic_techniques import get_technique_by_id

        t = get_technique_by_id("rule_of_thirds")
        assert t is not None
        assert "kling" in t.prompt_keywords
        assert "seedance" in t.prompt_keywords

    def test_technique_has_combinable_with(self):
        from app.rag.cinematic_techniques import get_technique_by_id

        t = get_technique_by_id("dolly_in")
        assert t is not None
        assert len(t.combinable_with) > 0

    def test_all_categories_present(self):
        from app.rag.cinematic_techniques import get_all_techniques

        techniques = get_all_techniques()
        categories = {t.category for t in techniques}
        expected = {"composition", "camera_movement", "camera_angle", "lighting", "color", "editing_rhythm", "transition"}
        assert expected.issubset(categories)


# =============================================================================
# Adapter Tests
# =============================================================================


class TestKlingAdapter:
    """Test Kling 3.0 prompt adapter."""

    def test_generate_from_prebuilt_prompt(self):
        from app.services.adapters.kling_adapter import generate_kling_prompt

        scene = {"prompts": {"kling_3_0": "A man in a dark coat walking."}}
        result = generate_kling_prompt(scene)
        assert result == "A man in a dark coat walking."

    def test_generate_from_techniques(self):
        from app.services.adapters.kling_adapter import generate_kling_prompt

        scene = {
            "description_en": "A solitary figure under streetlight",
            "techniques": {
                "camera_movement": ["dolly_in"],
                "lighting": ["chiaroscuro"],
            },
            "prompts": {},
        }
        result = generate_kling_prompt(scene)
        assert len(result) > 10

    def test_camera_preset_mapping(self):
        from app.services.adapters.kling_adapter import get_kling_camera_preset

        preset = get_kling_camera_preset({"camera_movement": ["dolly_in"]})
        assert preset == "dolly_in"

    def test_motion_intensity(self):
        from app.services.adapters.kling_adapter import get_kling_motion_intensity

        assert get_kling_motion_intensity(0.1) == "slow"
        assert get_kling_motion_intensity(0.5) == "normal"
        assert get_kling_motion_intensity(0.7) == "fast"
        assert get_kling_motion_intensity(0.9) == "dramatic"


class TestSeedanceAdapter:
    """Test Seedance 2.0 prompt adapter."""

    def test_generate_from_prebuilt_prompt(self):
        from app.services.adapters.seedance_adapter import generate_seedance_prompt

        scene = {"prompts": {"seedance_2_0": "Cinematic wide shot of a forest."}}
        result = generate_seedance_prompt(scene)
        assert result == "Cinematic wide shot of a forest."

    def test_generate_from_techniques(self):
        from app.services.adapters.seedance_adapter import generate_seedance_prompt

        scene = {
            "description_en": "A couple walking on a beach",
            "techniques": {
                "camera_angle": ["eye_level"],
                "camera_movement": ["lateral_tracking"],
                "lighting": ["natural_golden_hour"],
            },
            "prompts": {},
        }
        result = generate_seedance_prompt(scene)
        assert "Cinematic" in result
        assert len(result) > 20


# =============================================================================
# Prompt Engine Tests
# =============================================================================


class TestADPromptEngine:
    """Test the prompt engine."""

    def test_generate_all_basic(self):
        from app.services.ad_prompt_engine import ADPromptEngine

        engine = ADPromptEngine()
        scenes = [
            {
                "scene_number": 1,
                "description_en": "A man enters a dark room",
                "techniques": {},
                "prompts": {
                    "kling_3_0": "Man enters dark room, medium shot, dim lighting.",
                    "seedance_2_0": "Cinematic entry into shadowy interior space.",
                },
            },
            {
                "scene_number": 2,
                "description_en": "Tension builds as he sees something",
                "techniques": {},
                "prompts": {
                    "kling_3_0": "Close-up reaction shot, slow push in.",
                    "seedance_2_0": "Cinematic close-up with subtle forward movement.",
                },
            },
        ]

        results = engine.generate_all(scenes)
        assert len(results) == 2
        assert results[0]["scene_number"] == 1
        assert "kling_3_0" in results[0]
        assert "seedance_2_0" in results[0]

    def test_generate_with_sequence(self):
        from app.services.ad_prompt_engine import ADPromptEngine

        engine = ADPromptEngine()
        scenes = [
            {
                "scene_number": 1,
                "description_en": "Peaceful morning",
                "techniques": {},
                "prompts": {"kling_3_0": "test", "seedance_2_0": "test"},
            },
        ]
        sequence = {
            "emotional_arc": [
                {"scene_number": 1, "intensity": 0.2},
            ],
            "continuity_anchors": {
                "style_anchors": ["cinematic"],
                "character_anchors": ["young woman"],
            },
        }

        results = engine.generate_all(scenes, sequence)
        assert len(results) == 1
        assert results[0]["kling_metadata"]["motion_intensity"] == "slow"


# =============================================================================
# AD Brain Tests
# =============================================================================


class TestADBrain:
    """Test AD Brain service helpers (no Gemini calls)."""

    def test_build_scene_analysis(self):
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain()
        scene_raw = {
            "scene_number": 1,
            "description": "어두운 방에서 남자가 서 있다",
            "description_en": "A man standing in a dark room",
            "techniques": {
                "composition": ["rule_of_thirds"],
                "camera_movement": ["dolly_in"],
                "camera_angle": ["eye_level"],
                "lighting": ["chiaroscuro"],
                "color": ["cool_blue"],
            },
            "sequence_context": {
                "emotional_position": "도입부",
                "camera_distance_flow": "WS → MS",
            },
            "prompts": {
                "kling_3_0": "A man in a dark room, rule of thirds.",
                "seedance_2_0": "Cinematic shot of man in dark room.",
            },
        }

        scene = brain._build_scene_analysis(scene_raw)
        assert scene.scene_number == 1
        assert scene.description == "어두운 방에서 남자가 서 있다"
        assert scene.prompts.kling_3_0 != ""

    def test_build_sequence_analysis(self):
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain()
        sequence_raw = {
            "emotional_arc": [
                {"scene_number": 1, "emotion": "평온", "intensity": 0.3, "description": "시작"},
                {"scene_number": 2, "emotion": "긴장", "intensity": 0.7, "description": "고조"},
            ],
            "visual_rhythm": {
                "camera_distance_curve": ["WS", "MS", "CU"],
                "edit_tempo": "점진적 가속",
            },
            "color_progression": [
                {"scene_number": 1, "temperature": "warm", "palette": "골든아워"},
            ],
            "continuity_anchors": {
                "character_anchors": ["검은 코트"],
                "style_anchors": ["neo-noir"],
                "lighting_anchors": ["역광"],
            },
        }

        seq = brain._build_sequence_analysis(sequence_raw, [])
        assert len(seq.emotional_arc) == 2
        assert seq.visual_rhythm is not None
        assert len(seq.color_progression) == 1
        assert seq.continuity_anchors is not None

    def test_enrich_techniques_with_corpus(self):
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain()
        techniques_raw = {
            "composition": ["rule_of_thirds"],
            "lighting": ["chiaroscuro"],
        }

        result = brain._enrich_techniques(techniques_raw)
        # Should have enriched composition
        assert len(result.composition) == 1
        assert result.composition[0].technique_id == "rule_of_thirds"
        assert result.composition[0].name_ko != ""
        # Should have enriched lighting
        assert len(result.lighting) == 1
        assert result.lighting[0].technique_id == "chiaroscuro"

    def test_enrich_techniques_unknown_id_fallback(self):
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain()
        techniques_raw = {
            "composition": ["unknown_technique_xyz"],
        }

        result = brain._enrich_techniques(techniques_raw)
        assert len(result.composition) == 1
        assert result.composition[0].technique_id == "unknown_technique_xyz"


# =============================================================================
# Sanitization Tests
# =============================================================================


class TestSanitization:
    """Test input sanitization for AD Studio."""

    def test_scenario_xss_stripped(self):
        req = ADStudioScenarioRequest(
            scenario="A scene with <script>alert('xss')</script> dramatic lighting and tension building throughout.",
        )
        assert "<script>" not in req.scenario

    def test_scenario_javascript_stripped(self):
        req = ADStudioScenarioRequest(
            scenario="A scene with javascript:void(0) and other normal cinematic description elements here.",
        )
        assert "javascript:" not in req.scenario

    def test_scenario_whitespace_stripped(self):
        req = ADStudioScenarioRequest(
            scenario="  A scene with leading/trailing whitespace here for testing.  ",
        )
        # strip is applied
        assert not req.scenario.startswith(" ")

    def test_content_size_validation(self):
        with pytest.raises(ValueError, match="크기가 너무 큽니다"):
            validate_content_size("x" * 60000, max_size=50000, field_name="test")


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Test AD Studio constants."""

    def test_allowed_engines(self):
        assert "kling" in ALLOWED_ENGINES
        assert "seedance" in ALLOWED_ENGINES
        assert len(ALLOWED_ENGINES) == 3
        assert "veo" in ALLOWED_ENGINES

    def test_max_scenario_length(self):
        assert MAX_SCENARIO_LENGTH == 10000
