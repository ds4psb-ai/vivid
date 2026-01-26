"""Tests for Story Engine Router and Service.

Comprehensive test suite covering:
- Story Engine service orchestration
- System Prompt Generator
- Component integration (Story, Prompt, Shot List)
- Credit calculation
- Error handling
"""
from __future__ import annotations

import pytest
from dataclasses import asdict
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from app.schemas.vpe import LogicVector, Cadence, Composition, CameraGrammar, LightingPhysics, ColorScience
from app.services.story_engine_service import (
    StoryEngineService,
    StoryEngineResult,
    StoryScenario,
    TranslatedPrompt,
    ShotListItem,
    StoryEngineComponent,
    STORY_ENGINE_CREDITS,
)
from app.routers.story_engine.system_prompt import (
    SystemPromptGenerator,
    SystemPromptResult,
    StoryStructure,
    TargetPlatform,
    AUTEUR_STYLE_HINTS,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_logic_vector() -> LogicVector:
    """Create a mock Logic Vector."""
    return LogicVector(
        auteur_id="bong",
        confidence=0.85,
        cadence=Cadence(
            avg_shot_length=4.5,
            tempo="moderate",
            rhythm_pattern="building_tension",
        ),
        composition=Composition(
            primary_strategy="vertical_blocking",
            symmetry_score=0.74,
            depth_staging="foreground_focus",
        ),
        camera_grammar=CameraGrammar(
            dolly=0.35,
            handheld=0.15,
            push_in=0.20,
            static=0.25,
            orbit=0.05,
        ),
        lighting_physics=LightingPhysics(
            key_light="low_key",
            color_temp_range=(3200, 4500),
            shadow_quality="hard",
        ),
        color_science=ColorScience(
            lut_reference="parasite_basement",
            palette=["desaturated", "green_tint", "yellow_accent"],
            saturation_level="muted",
        ),
    )


@pytest.fixture
def mock_scenario() -> StoryScenario:
    """Create a mock story scenario."""
    return StoryScenario(
        title="지하실의 비밀",
        logline="부잣집 지하실에서 발견된 충격적인 진실",
        genre="thriller",
        structure="3-act",
        duration_seconds=60,
        scenes=[
            {
                "scene_number": 1,
                "duration_seconds": 20,
                "description": "주인공이 지하실 문을 발견한다",
            },
            {
                "scene_number": 2,
                "duration_seconds": 25,
                "description": "지하실로 내려가는 계단",
            },
            {
                "scene_number": 3,
                "duration_seconds": 15,
                "description": "충격적인 발견",
            },
        ],
        visual_style="dark cinematic",
        mood="tension",
        setting="modern luxury house",
        raw_content="Full scenario text here...",
    )


# =============================================================================
# System Prompt Generator Tests
# =============================================================================

class TestSystemPromptGenerator:
    """Tests for System Prompt Generator."""

    def test_generate_basic(self, mock_logic_vector: LogicVector):
        """Test basic system prompt generation."""
        generator = SystemPromptGenerator()
        result = generator.generate(
            logic_vector=mock_logic_vector,
            target_platform="veo",
        )

        assert result.system_prompt
        assert result.platform == "veo"
        assert result.character_count > 0
        assert "bong" in result.system_prompt.lower() or "joon-ho" in result.system_prompt.lower()

    def test_generate_with_story_structure(self, mock_logic_vector: LogicVector):
        """Test system prompt with story structure."""
        generator = SystemPromptGenerator()
        story = StoryStructure(
            title="Test Story",
            genre="thriller",
            mood="dark",
            setting="urban",
            shot_description="A man walks through dark alley",
        )

        result = generator.generate(
            logic_vector=mock_logic_vector,
            story_structure=story,
            target_platform="veo",
        )

        assert "Scene:" in result.system_prompt or "Genre:" in result.system_prompt
        assert result.character_count > 100

    def test_generate_for_different_platforms(self, mock_logic_vector: LogicVector):
        """Test generation for different platforms."""
        generator = SystemPromptGenerator()

        for platform in ["veo", "kling", "runway", "generic"]:
            result = generator.generate(
                logic_vector=mock_logic_vector,
                target_platform=platform,
            )

            assert result.platform == platform
            assert result.system_prompt

    def test_generate_with_negative_prompt(self, mock_logic_vector: LogicVector):
        """Test negative prompt generation."""
        generator = SystemPromptGenerator()
        result = generator.generate(
            logic_vector=mock_logic_vector,
            target_platform="veo",
            include_negative=True,
        )

        assert result.negative_prompt
        assert "Avoid:" in result.negative_prompt or len(result.negative_prompt) > 0

    def test_generate_truncation(self, mock_logic_vector: LogicVector):
        """Test prompt truncation for long content."""
        generator = SystemPromptGenerator()
        long_story = StoryStructure(
            shot_description="A" * 2000,  # Very long description
        )

        result = generator.generate(
            logic_vector=mock_logic_vector,
            story_structure=long_story,
            target_platform="kling",  # Has 1000 char limit
        )

        # Kling has 1000 max length
        assert result.character_count <= 1000 or result.truncated

    def test_generate_for_shot(self, mock_logic_vector: LogicVector):
        """Test shot-specific prompt generation."""
        generator = SystemPromptGenerator()
        result = generator.generate_for_shot(
            logic_vector=mock_logic_vector,
            shot_description="Close-up of character's face showing fear",
            shot_number=3,
            target_platform="veo",
        )

        assert "Shot 3" in result.system_prompt
        assert result.platform == "veo"

    def test_auteur_style_hints(self):
        """Test auteur style hints are available."""
        assert "bong" in AUTEUR_STYLE_HINTS
        assert "nolan" in AUTEUR_STYLE_HINTS
        assert "kubrick" in AUTEUR_STYLE_HINTS

        hint = AUTEUR_STYLE_HINTS["bong"]
        assert "vertical" in hint.lower() or "contrast" in hint.lower()

    def test_target_platform_enum(self):
        """Test TargetPlatform enum values."""
        assert TargetPlatform.VEO.value == "veo"
        assert TargetPlatform.KLING.value == "kling"
        assert TargetPlatform.RUNWAY.value == "runway"


# =============================================================================
# Story Engine Service Tests
# =============================================================================

class TestStoryEngineService:
    """Tests for Story Engine service."""

    def test_calculate_total_credits(self):
        """Test credit calculation for components."""
        service = StoryEngineService()

        # Single component
        assert service.calculate_total_credits(["story"]) == STORY_ENGINE_CREDITS[StoryEngineComponent.STORY]

        # Multiple components
        expected = (
            STORY_ENGINE_CREDITS[StoryEngineComponent.STORY] +
            STORY_ENGINE_CREDITS[StoryEngineComponent.PROMPT]
        )
        assert service.calculate_total_credits(["story", "prompt"]) == expected

        # All components
        all_cost = sum(STORY_ENGINE_CREDITS.values())
        assert service.calculate_total_credits(["story", "prompt", "system_prompt", "shot_list"]) == all_cost

        # Invalid component
        assert service.calculate_total_credits(["invalid"]) == 0

    @pytest.mark.asyncio
    async def test_generate_story_basic(self, mock_scenario: StoryScenario):
        """Test basic story generation."""
        with patch.object(StoryEngineService, "_run_story_architect", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = mock_scenario

            service = StoryEngineService()
            result = await service.generate_story(
                concept="thriller in basement",
                genre="thriller",
            )

            assert result.success is True
            assert "story" in result.components_run
            assert result.scenario is not None
            assert result.scenario.title == "지하실의 비밀"

    @pytest.mark.asyncio
    async def test_generate_story_with_logic_vector(
        self,
        mock_scenario: StoryScenario,
        mock_logic_vector: LogicVector,
    ):
        """Test story generation with Logic Vector."""
        with patch.object(StoryEngineService, "_run_story_architect", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = mock_scenario

            service = StoryEngineService()
            result = await service.generate_story(
                concept="thriller in basement",
                logic_vector=mock_logic_vector,
            )

            assert result.success is True
            assert "story" in result.components_run
            assert "system_prompt" in result.components_run
            assert result.system_prompt is not None
            assert result.logic_vector_used is True

    @pytest.mark.asyncio
    async def test_generate_story_with_platforms(self, mock_scenario: StoryScenario):
        """Test story generation with platform-specific prompts."""
        with patch.object(StoryEngineService, "_run_story_architect", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = mock_scenario

            with patch.object(StoryEngineService, "_run_prompt_alchemy", new_callable=AsyncMock) as mock_prompt:
                mock_prompt.return_value = [
                    TranslatedPrompt(platform="veo", prompt="VEO prompt", quality_score=0.8),
                    TranslatedPrompt(platform="kling", prompt="Kling prompt", quality_score=0.85),
                ]

                service = StoryEngineService()
                result = await service.generate_story(
                    concept="thriller in basement",
                    target_platforms=["veo", "kling"],
                )

                assert result.success is True
                assert "prompt" in result.components_run
                assert len(result.translated_prompts) == 2

    @pytest.mark.asyncio
    async def test_generate_story_with_shot_list(self, mock_scenario: StoryScenario):
        """Test story generation with shot list."""
        mock_shots = [
            ShotListItem(shot_number=1, time_range="0:00-0:03", duration=3, recommended_tool="veo"),
            ShotListItem(shot_number=2, time_range="0:04-0:08", duration=4, recommended_tool="kling"),
        ]

        with patch.object(StoryEngineService, "_run_story_architect", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = mock_scenario

            with patch.object(StoryEngineService, "_generate_shot_list", new_callable=AsyncMock) as mock_shots_gen:
                mock_shots_gen.return_value = mock_shots

                service = StoryEngineService()
                result = await service.generate_story(
                    concept="thriller in basement",
                    generate_shot_list=True,
                )

                assert result.success is True
                assert "shot_list" in result.components_run
                assert len(result.shot_list) == 2

    @pytest.mark.asyncio
    async def test_generate_system_prompt_only(self, mock_logic_vector: LogicVector):
        """Test system prompt only generation."""
        service = StoryEngineService()
        prompt = await service.generate_system_prompt_only(
            logic_vector=mock_logic_vector,
            story_description="Dark scene in basement",
            target_platform="veo",
        )

        assert prompt
        assert len(prompt) > 50

    @pytest.mark.asyncio
    async def test_generate_shot_list_only(self):
        """Test shot list only generation."""
        mock_shots = [
            ShotListItem(shot_number=1, duration=5, recommended_tool="veo"),
        ]

        with patch.object(StoryEngineService, "_generate_shot_list", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_shots

            service = StoryEngineService()
            shots = await service.generate_shot_list_only(
                scenario_text="A man enters a dark room",
                duration_seconds=30,
            )

            assert len(shots) == 1

    def test_scenario_to_description(self, mock_scenario: StoryScenario):
        """Test scenario to description conversion."""
        service = StoryEngineService()
        description = service._scenario_to_description(mock_scenario)

        assert "지하실의 비밀" in description
        assert "thriller" in description.lower() or "dark" in description.lower()

    def test_calculate_confidence(self, mock_scenario: StoryScenario):
        """Test confidence calculation."""
        service = StoryEngineService()

        result = StoryEngineResult(
            success=True,
            scenario=mock_scenario,
            logic_vector_used=True,
            translated_prompts=[
                TranslatedPrompt(platform="veo", prompt="test", quality_score=0.8),
            ],
        )

        confidence = service._calculate_confidence(result)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high with all components


# =============================================================================
# Router Tests
# =============================================================================

class TestStoryEngineRouter:
    """Tests for Story Engine API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_endpoint_success(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/story-engine/generate endpoint success."""
        with patch("app.routers.story_engine.router.get_story_engine_service") as mock_service:
            mock_svc = MagicMock()
            mock_svc.calculate_total_credits.return_value = 15
            mock_svc.generate_story = AsyncMock(return_value=StoryEngineResult(
                success=True,
                trace_id="test-trace",
                components_run=["story"],
                scenario=StoryScenario(title="Test", genre="drama"),
                confidence=0.8,
                credits_used=15,
            ))
            mock_service.return_value = mock_svc

            with patch("app.routers.story_engine.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.story_engine.router.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/story-engine/generate",
                        json={
                            "concept": "A thriller story",
                            "genre": "thriller",
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "story" in data["components_run"]

    @pytest.mark.asyncio
    async def test_generate_endpoint_insufficient_credits(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/story-engine/generate returns 402 when credits insufficient."""
        with patch("app.routers.story_engine.router.get_story_engine_service") as mock_service:
            mock_svc = MagicMock()
            mock_svc.calculate_total_credits.return_value = 100
            mock_service.return_value = mock_svc

            with patch("app.routers.story_engine.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=10)

                response = await async_client.post(
                    "/api/story-engine/generate",
                    json={
                        "concept": "A thriller story",
                        "generate_shot_list": True,
                        "target_platforms": ["veo", "kling"],
                    },
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    @pytest.mark.asyncio
    async def test_system_prompt_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        mock_logic_vector: LogicVector,
    ):
        """Test /api/story-engine/system-prompt endpoint."""
        response = await async_client.post(
            "/api/story-engine/system-prompt",
            json={
                "logic_vector": mock_logic_vector.model_dump(),
                "target_platform": "veo",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["system_prompt"]
        assert data["platform"] == "veo"

    @pytest.mark.asyncio
    async def test_get_credit_costs(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/story-engine/credits endpoint."""
        response = await async_client.get(
            "/api/story-engine/credits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "components" in data
        assert "story" in data["components"]
        assert "prompt" in data["components"]

    @pytest.mark.asyncio
    async def test_get_platforms(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/story-engine/platforms endpoint."""
        response = await async_client.get(
            "/api/story-engine/platforms",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "platforms" in data
        assert "veo" in data["platforms"]

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test /api/story-engine/health endpoint."""
        response = await async_client.get("/api/story-engine/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "story_engine"
        assert "components" in data


# =============================================================================
# Data Classes Tests
# =============================================================================

class TestStoryEngineDataClasses:
    """Tests for Story Engine data classes."""

    def test_story_scenario_defaults(self):
        """Test StoryScenario default values."""
        scenario = StoryScenario()
        assert scenario.title == ""
        assert scenario.scenes == []

    def test_translated_prompt_defaults(self):
        """Test TranslatedPrompt default values."""
        prompt = TranslatedPrompt()
        assert prompt.platform == ""
        assert prompt.quality_score == 0.0

    def test_shot_list_item_defaults(self):
        """Test ShotListItem default values."""
        shot = ShotListItem()
        assert shot.shot_number == 0
        assert shot.recommended_tool == "veo"

    def test_story_engine_result_to_dict(self):
        """Test StoryEngineResult can be serialized."""
        result = StoryEngineResult(
            success=True,
            trace_id="test",
            scenario=StoryScenario(title="Test Story"),
        )

        if result.scenario:
            data = asdict(result.scenario)
            assert data["title"] == "Test Story"


# =============================================================================
# Integration Tests
# =============================================================================

class TestStoryEngineIntegration:
    """Integration tests for Story Engine."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_logic_vector(
        self,
        mock_logic_vector: LogicVector,
        mock_scenario: StoryScenario,
    ):
        """Test complete pipeline with Logic Vector."""
        mock_shots = [
            ShotListItem(shot_number=1, duration=5, recommended_tool="veo"),
            ShotListItem(shot_number=2, duration=5, recommended_tool="kling"),
        ]

        with patch.object(StoryEngineService, "_run_story_architect", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = mock_scenario

            with patch.object(StoryEngineService, "_run_prompt_alchemy", new_callable=AsyncMock) as mock_prompt:
                mock_prompt.return_value = [
                    TranslatedPrompt(platform="veo", prompt="VEO prompt", quality_score=0.8),
                ]

                with patch.object(StoryEngineService, "_generate_shot_list", new_callable=AsyncMock) as mock_shots_gen:
                    mock_shots_gen.return_value = mock_shots

                    service = StoryEngineService()
                    result = await service.generate_story(
                        concept="thriller story",
                        logic_vector=mock_logic_vector,
                        target_platforms=["veo"],
                        generate_shot_list=True,
                    )

                    assert result.success is True
                    assert result.logic_vector_used is True
                    assert len(result.components_run) >= 3
                    assert result.system_prompt is not None
                    assert len(result.translated_prompts) == 1
                    assert len(result.shot_list) == 2

    def test_component_enum_values(self):
        """Test StoryEngineComponent enum values."""
        assert StoryEngineComponent.STORY.value == "story"
        assert StoryEngineComponent.PROMPT.value == "prompt"
        assert StoryEngineComponent.SYSTEM_PROMPT.value == "system_prompt"
        assert StoryEngineComponent.SHOT_LIST.value == "shot_list"

    def test_component_credits_coverage(self):
        """Test all components have credit costs defined."""
        for component in StoryEngineComponent:
            assert component in STORY_ENGINE_CREDITS
            assert STORY_ENGINE_CREDITS[component] > 0

    def test_system_prompt_with_all_auteurs(self, mock_logic_vector: LogicVector):
        """Test system prompt generation with different auteurs."""
        generator = SystemPromptGenerator()

        for auteur_id in ["bong", "nolan", "kubrick", "wong", "tarantino"]:
            mock_logic_vector.auteur_id = auteur_id
            result = generator.generate(
                logic_vector=mock_logic_vector,
                target_platform="veo",
            )

            assert result.system_prompt
            # Check auteur reference is included
            assert auteur_id in result.system_prompt.lower() or len(result.system_prompt) > 100
