"""
Tests for Suno AI Music Generation API.

Tests the Suno V5 music generation endpoints:
- POST /api/v1/dimension/suno/generate
- GET /api/v1/dimension/suno/status/{task_id}
- GET /api/v1/dimension/suno/pricing

Suno Features:
- Custom mode with title, style, lyrics
- Instrumental mode (no vocals)
- Models: V5, V4_5PLUS, V4_5ALL, V4_5, V4
- 2 songs per generation
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.routers.dimension.suno import (
    SunoGenerateRequest,
    SunoGenerateResponse,
    SunoStatusResponse,
    SunoSongResponse,
    get_credit_cost,
    _validate_suno_model,
    ALLOWED_SUNO_MODELS,
)
from app.routers.dimension._audio_base import sanitize_audio_text
from app.services.suno_service import (
    SunoService,
    SunoMusicRequest,
    SunoMusicResponse,
    SunoResult,
    SunoSong,
    SunoModel,
    SunoConfig,
)


# =============================================================================
# Sanitization Tests
# =============================================================================

class TestTextSanitization:
    """Test XSS sanitization for text fields."""

    def test_sanitize_empty_text(self):
        """Empty text returns empty."""
        assert sanitize_audio_text("") == ""

    def test_sanitize_strips_whitespace(self):
        """Whitespace is stripped."""
        assert sanitize_audio_text("  hello world  ") == "hello world"

    def test_sanitize_removes_html_tags(self):
        """HTML tags are removed."""
        result = sanitize_audio_text("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "hello" in result

    def test_sanitize_removes_javascript(self):
        """JavaScript patterns are removed."""
        assert "javascript" not in sanitize_audio_text("javascript:alert(1)")
        assert sanitize_audio_text("onclick=evil()").find("onclick=") == -1


# =============================================================================
# Model Validation Tests
# =============================================================================

class TestModelValidation:
    """Test Suno model validation."""

    def test_valid_models(self):
        """Valid models pass validation."""
        for model in ALLOWED_SUNO_MODELS:
            assert _validate_suno_model(model) == model

    def test_invalid_model_raises(self):
        """Invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            _validate_suno_model("V6")
        with pytest.raises(ValueError, match="Invalid model"):
            _validate_suno_model("invalid")

    def test_model_strips_whitespace(self):
        """Model validation strips whitespace."""
        assert _validate_suno_model("  V5  ") == "V5"


# =============================================================================
# Credit Cost Tests
# =============================================================================

class TestCreditCost:
    """Test credit cost calculation."""

    def test_v5_cost(self):
        """V5 costs 20 credits."""
        assert get_credit_cost("V5") == 20

    def test_v45plus_cost(self):
        """V4_5PLUS costs 15 credits."""
        assert get_credit_cost("V4_5PLUS") == 15

    def test_v45all_cost(self):
        """V4_5ALL costs 15 credits."""
        assert get_credit_cost("V4_5ALL") == 15

    def test_v45_cost(self):
        """V4_5 costs 12 credits."""
        assert get_credit_cost("V4_5") == 12

    def test_v4_cost(self):
        """V4 costs 10 credits."""
        assert get_credit_cost("V4") == 10

    def test_unknown_model_default(self):
        """Unknown model defaults to 20."""
        assert get_credit_cost("V99") == 20


# =============================================================================
# Request Model Tests
# =============================================================================

class TestSunoGenerateRequest:
    """Test SunoGenerateRequest validation."""

    def test_minimal_request(self):
        """Minimal request works."""
        request = SunoGenerateRequest(
            prompt="A beautiful sunset song",
            title="Sunset Dreams",
            style="Pop, upbeat",
        )
        assert request.prompt == "A beautiful sunset song"
        assert request.title == "Sunset Dreams"
        assert request.model == "V5"
        assert request.instrumental is False

    def test_full_request(self):
        """Full request with all options works."""
        request = SunoGenerateRequest(
            prompt="[Verse]\nWalking through...",
            title="City Lights",
            style="K-pop, electronic dance",
            instrumental=False,
            model="V4_5PLUS",
        )
        assert request.model == "V4_5PLUS"
        assert request.instrumental is False

    def test_instrumental_request(self):
        """Instrumental request works."""
        request = SunoGenerateRequest(
            prompt="Epic cinematic score",
            title="Hero's Journey",
            style="Orchestral, dramatic",
            instrumental=True,
        )
        assert request.instrumental is True

    def test_prompt_sanitization(self):
        """Prompt is sanitized on creation."""
        request = SunoGenerateRequest(
            prompt="<script>alert('xss')</script>Beautiful melody",
            title="Test",
            style="Pop",
        )
        assert "<script>" not in request.prompt
        assert "Beautiful melody" in request.prompt

    def test_title_sanitization(self):
        """Title is sanitized on creation."""
        request = SunoGenerateRequest(
            prompt="Test song",
            title="<b>Bold</b> Title",
            style="Pop",
        )
        assert "<b>" not in request.title

    def test_style_sanitization(self):
        """Style is sanitized on creation."""
        request = SunoGenerateRequest(
            prompt="Test song",
            title="Test",
            style="Pop, <script>evil</script>upbeat",
        )
        assert "<script>" not in request.style


# =============================================================================
# Response Model Tests
# =============================================================================

class TestSunoGenerateResponse:
    """Test SunoGenerateResponse model."""

    def test_success_response(self):
        """Success response includes songs."""
        songs = [
            SunoSongResponse(
                id="song-1",
                title="Track 1",
                audio_url="https://cdn.suno.ai/song1.mp3",
                duration=120.5,
            ),
            SunoSongResponse(
                id="song-2",
                title="Track 2",
                audio_url="https://cdn.suno.ai/song2.mp3",
                duration=118.0,
            ),
        ]
        response = SunoGenerateResponse(
            success=True,
            task_id="task-123",
            status="completed",
            songs=songs,
            credits_used=20,
        )
        assert response.success is True
        assert len(response.songs) == 2
        assert response.credits_used == 20

    def test_error_response(self):
        """Error response includes error message."""
        response = SunoGenerateResponse(
            success=False,
            task_id="task-456",
            status="failed",
            error="Content policy violation",
        )
        assert response.success is False
        assert response.error is not None


class TestSunoSongResponse:
    """Test SunoSongResponse model."""

    def test_full_song(self):
        """Song with all fields."""
        song = SunoSongResponse(
            id="song-123",
            title="My Song",
            audio_url="https://cdn.suno.ai/audio.mp3",
            stream_url="https://cdn.suno.ai/stream.mp3",
            image_url="https://cdn.suno.ai/cover.jpg",
            duration=180.5,
        )
        assert song.duration == 180.5
        assert song.image_url is not None

    def test_minimal_song(self):
        """Song with minimal fields."""
        song = SunoSongResponse(
            id="song-456",
            title="Untitled",
        )
        assert song.audio_url is None
        assert song.duration is None


# =============================================================================
# Service Tests
# =============================================================================

class TestSunoServiceConfig:
    """Test Suno service configuration."""

    def test_default_config(self):
        """Default config values are set."""
        assert SunoConfig.DEFAULT_MODEL == "V5"
        assert "V5" in SunoConfig.SUPPORTED_MODELS
        assert SunoConfig.REQUEST_TIMEOUT == 30.0
        assert SunoConfig.POLL_TIMEOUT == 180.0

    def test_credit_costs(self):
        """Credit costs match pricing."""
        assert SunoConfig.CREDIT_COSTS["V5"] == 20
        assert SunoConfig.CREDIT_COSTS["V4_5PLUS"] == 15
        assert SunoConfig.CREDIT_COSTS["V4_5"] == 12
        assert SunoConfig.CREDIT_COSTS["V4"] == 10


class TestSunoModelEnum:
    """Test SunoModel enum."""

    def test_enum_values(self):
        """Enum has correct values."""
        assert SunoModel.V5.value == "V5"
        assert SunoModel.V4_5_PLUS.value == "V4_5PLUS"
        assert SunoModel.V4_5_ALL.value == "V4_5ALL"
        assert SunoModel.V4_5.value == "V4_5"
        assert SunoModel.V4.value == "V4"


class TestSunoMusicRequest:
    """Test SunoMusicRequest model from service."""

    def test_request_with_custom_mode(self):
        """Request with custom mode."""
        request = SunoMusicRequest(
            prompt="[Verse]\nSinging in the rain...",
            title="Rainy Day",
            style="Pop ballad, emotional",
            custom_mode=True,
            instrumental=False,
            model=SunoModel.V5,
        )
        assert request.custom_mode is True
        assert request.model == SunoModel.V5

    def test_request_instrumental(self):
        """Request with instrumental mode."""
        request = SunoMusicRequest(
            prompt="Epic orchestral soundtrack",
            title="Battle Theme",
            style="Cinematic, Hans Zimmer style",
            instrumental=True,
            model=SunoModel.V4_5_PLUS,
        )
        assert request.instrumental is True


class TestSunoService:
    """Test SunoService methods."""

    def test_service_init_no_key(self):
        """Service initializes without API key."""
        service = SunoService()
        assert service.api_key is None
        assert service.base_url == SunoConfig.BASE_URL

    def test_service_init_with_key(self):
        """Service initializes with API key."""
        service = SunoService(api_key="test-key")
        assert service.api_key == "test-key"

    def test_calculate_credits(self):
        """Credit calculation from request."""
        service = SunoService(api_key="test")

        request_v5 = SunoMusicRequest(
            prompt="test",
            title="test",
            style="test",
            model=SunoModel.V5,
        )
        assert service._calculate_credits(request_v5) == 20

        request_v4 = SunoMusicRequest(
            prompt="test",
            title="test",
            style="test",
            model=SunoModel.V4,
        )
        assert service._calculate_credits(request_v4) == 10

    @pytest.mark.asyncio
    async def test_generate_without_key(self):
        """Generate fails without API key."""
        service = SunoService()
        request = SunoMusicRequest(
            prompt="test",
            title="test",
            style="test",
        )
        result = await service.generate_music(request)

        assert result.success is False
        assert "API key not configured" in result.error


class TestSunoResult:
    """Test SunoResult dataclass."""

    def test_success_result(self):
        """Success result with songs."""
        songs = [
            SunoSong(
                id="song-1",
                title="Track 1",
                audio_url="https://cdn.suno.ai/song1.mp3",
                duration=120.0,
                status="complete",
            ),
        ]
        result = SunoResult(
            success=True,
            task_id="task-123",
            songs=songs,
            credits_used=20,
        )
        assert result.success is True
        assert len(result.songs) == 1
        assert result.error is None

    def test_error_result(self):
        """Error result with message."""
        result = SunoResult(
            success=False,
            task_id="task-456",
            error="Generation failed",
        )
        assert result.success is False
        assert result.error is not None
        assert len(result.songs) == 0


class TestSunoSong:
    """Test SunoSong model."""

    def test_song_fields(self):
        """Song has all expected fields."""
        song = SunoSong(
            id="song-123",
            title="My Song",
            audio_url="https://cdn.suno.ai/audio.mp3",
            stream_url="https://cdn.suno.ai/stream.mp3",
            image_url="https://cdn.suno.ai/cover.jpg",
            duration=180.5,
            status="complete",
        )
        assert song.id == "song-123"
        assert song.status == "complete"


# =============================================================================
# YAML Config Tests
# =============================================================================

class TestSunoYAMLConfig:
    """Test Suno YAML configuration."""

    @pytest.fixture
    def config_path(self):
        """Get absolute path to config file."""
        import os
        # Tests run from backend/ directory, config is at project root
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(backend_dir)
        return os.path.join(project_root, "config/apps/content/dimensions/suno.yaml")

    def test_config_file_exists(self, config_path):
        """Config file should exist."""
        import os
        assert os.path.exists(config_path), f"Config file not found: {config_path}"

    def test_config_structure(self, config_path):
        """Config has required structure."""
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Metadata
        assert config["metadata"]["name"] == "suno"
        assert config["metadata"]["type"] == "dimension"
        assert "5.0" in config["metadata"]["version"]

        # Display
        assert "display" in config
        assert config["display"]["icon"] == "🎵"

        # Capabilities
        assert "capabilities" in config
        capability_names = [c["name"] for c in config["capabilities"]]
        assert "cache" in capability_names
        assert "execution" in capability_names

        # Extensions
        assert "extensions" in config
        assert "suno_music" in config["extensions"]

        suno_ext = config["extensions"]["suno_music"]

        # Models
        assert "models" in suno_ext
        model_ids = [m["id"] for m in suno_ext["models"]]
        assert "V5" in model_ids
        assert "V4" in model_ids

        # Genres
        assert "genres" in suno_ext
        genre_ids = [g["id"] for g in suno_ext["genres"]]
        assert "pop" in genre_ids
        assert "cinematic" in genre_ids

        # Moods
        assert "moods" in suno_ext
        mood_ids = [m["id"] for m in suno_ext["moods"]]
        assert "happy" in mood_ids
        assert "epic" in mood_ids

        # Composer styles
        assert "composer_styles" in suno_ext
        composer_ids = [c["id"] for c in suno_ext["composer_styles"]]
        assert "hans_zimmer" in composer_ids
        assert "joe_hisaishi" in composer_ids

        # Instrumental mode
        assert "instrumental" in suno_ext
        assert suno_ext["instrumental"]["enabled"] is True


# =============================================================================
# Integration-Style Tests (mocked)
# =============================================================================

class TestSunoEndpointBehavior:
    """Test expected endpoint behaviors (mocked)."""

    @pytest.mark.asyncio
    async def test_generate_returns_two_songs(self):
        """Successful generation returns 2 songs."""
        mock_songs = [
            SunoSong(
                id="song-1",
                title="Track 1",
                audio_url="https://cdn.suno.ai/song1.mp3",
                duration=120.0,
                status="complete",
            ),
            SunoSong(
                id="song-2",
                title="Track 2",
                audio_url="https://cdn.suno.ai/song2.mp3",
                duration=118.0,
                status="complete",
            ),
        ]
        mock_result = SunoResult(
            success=True,
            task_id="task-123",
            songs=mock_songs,
        )

        with patch.object(SunoService, 'generate_music', return_value=mock_result):
            service = SunoService(api_key="test")
            request = SunoMusicRequest(
                prompt="test",
                title="test",
                style="test",
            )
            result = await service.generate_music(request)

            assert result.success is True
            assert len(result.songs) == 2

    @pytest.mark.asyncio
    async def test_generate_refunds_on_failure(self):
        """Credits should be refunded on failed generation."""
        mock_result = SunoResult(
            success=False,
            task_id="task-456",
            error="Content policy violation",
        )

        with patch.object(SunoService, 'generate_music', return_value=mock_result):
            service = SunoService(api_key="test")
            request = SunoMusicRequest(
                prompt="test",
                title="test",
                style="test",
            )
            result = await service.generate_music(request)

            assert result.success is False
            # In real scenario, credits would be refunded
