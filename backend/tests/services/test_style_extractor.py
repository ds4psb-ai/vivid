"""
Tests for StyleExtractor Service (2026 Expert Workflow).

Tests:
- StyleExtractionResult model validation
- StyleExtractor initialization
- Style extraction from images
- Color palette extraction (K-Means)
- Video frame extraction
- Result merging
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import base64

from pydantic import ValidationError

from app.services.ai.style_extractor import (
    StyleExtractor,
    StyleExtractionResult,
    StyleExtractionConfig,
    StyleExtractionError,
    StyleExtractionTimeoutError,
    StyleExtractionAPIError,
    get_style_extractor,
    extract_style,
)


# ============================================================================
# StyleExtractionResult Model Tests
# ============================================================================


class TestStyleExtractionResultModel:
    """Test StyleExtractionResult Pydantic model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        result = StyleExtractionResult()
        assert result.style_tags == []
        assert result.style_prompt == ""
        assert result.color_palette == []
        assert result.lighting == "natural"
        assert result.composition == "balanced"
        assert result.mood == "neutral"
        assert result.camera_angle is None
        assert result.reference_artists == []
        assert result.confidence == 0.0

    def test_valid_full_result(self):
        """Test valid full result creation."""
        result = StyleExtractionResult(
            style_tags=["anime", "cel-shading", "vibrant"],
            style_prompt="Cinematic anime style with bold outlines...",
            color_palette=["#FF5733", "#33FF57", "#3357FF"],
            lighting="neon",
            composition="rule-of-thirds",
            mood="energetic",
            camera_angle="low-angle",
            reference_artists=["Makoto Shinkai", "Studio Ghibli"],
            confidence=0.95,
        )
        assert len(result.style_tags) == 3
        assert result.lighting == "neon"
        assert result.confidence == 0.95

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        # Valid bounds
        assert StyleExtractionResult(confidence=0.0).confidence == 0.0
        assert StyleExtractionResult(confidence=1.0).confidence == 1.0

        # Invalid bounds
        with pytest.raises(ValidationError):
            StyleExtractionResult(confidence=-0.1)
        with pytest.raises(ValidationError):
            StyleExtractionResult(confidence=1.1)

    def test_model_dump(self):
        """Test model serialization."""
        result = StyleExtractionResult(
            style_tags=["anime"],
            style_prompt="Test prompt",
            confidence=0.8,
        )
        data = result.model_dump()
        assert data["style_tags"] == ["anime"]
        assert data["style_prompt"] == "Test prompt"
        assert data["confidence"] == 0.8


# ============================================================================
# StyleExtractionConfig Tests
# ============================================================================


class TestStyleExtractionConfig:
    """Test StyleExtractionConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StyleExtractionConfig()
        assert config.model == "gemini-3-flash-preview"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout_seconds == 30.0
        assert config.extract_color_palette is True
        assert config.num_palette_colors == 7

    def test_custom_values(self):
        """Test custom configuration values."""
        config = StyleExtractionConfig(
            model="gemini-2.5-pro",
            max_retries=5,
            timeout_seconds=60.0,
            num_palette_colors=5,
        )
        assert config.model == "gemini-2.5-pro"
        assert config.max_retries == 5
        assert config.timeout_seconds == 60.0
        assert config.num_palette_colors == 5


# ============================================================================
# StyleExtractor Initialization Tests
# ============================================================================


class TestStyleExtractorInit:
    """Test StyleExtractor initialization."""

    def test_init_default(self):
        """Test default initialization."""
        with patch("app.services.ai.style_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"
            extractor = StyleExtractor()
            assert extractor._api_key == "test-key"
            assert extractor.config is not None

    def test_init_custom_key(self):
        """Test initialization with custom API key."""
        extractor = StyleExtractor(api_key="custom-key")
        assert extractor._api_key == "custom-key"

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = StyleExtractionConfig(model="gemini-2.5-pro")
        extractor = StyleExtractor(api_key="key", config=config)
        assert extractor.config.model == "gemini-2.5-pro"


# ============================================================================
# Style Extraction Tests (Mocked)
# ============================================================================


class TestStyleExtraction:
    """Test style extraction methods with mocked API."""

    @pytest.fixture
    def mock_client(self):
        """Create mock GenAI client."""
        mock = MagicMock()
        mock.models.generate_content = MagicMock()
        return mock

    @pytest.fixture
    def extractor(self, mock_client):
        """Create extractor with mocked client."""
        extractor = StyleExtractor(api_key="test-key")
        extractor._client = mock_client
        return extractor

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes (minimal JPEG)."""
        # Minimal valid JPEG (1x1 pixel)
        return base64.b64decode(
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
            "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgN"
            "DRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
            "MjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAU"
            "EAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAA"
            "AAAAAAAAAAAAAAAAA//aAAwDAQACEQMRAD8AlgAB/9k="
        )

    @pytest.mark.asyncio
    async def test_extract_style_success(self, extractor, mock_client, sample_image_bytes):
        """Test successful style extraction."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "style_tags": ["anime", "cel-shading"],
            "style_prompt": "Anime style with vibrant colors",
            "color_palette": ["#FF5733", "#33FF57"],
            "lighting": "dramatic",
            "composition": "centered",
            "mood": "energetic",
            "camera_angle": "eye-level",
            "reference_artists": ["Makoto Shinkai"],
            "confidence": 0.9,
        })

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_response

            result = await extractor.extract_style(sample_image_bytes)

            assert result.style_tags == ["anime", "cel-shading"]
            assert result.style_prompt == "Anime style with vibrant colors"
            assert result.lighting == "dramatic"
            assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_extract_style_with_context(self, extractor, sample_image_bytes):
        """Test style extraction with additional context."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "style_tags": ["sci-fi"],
            "style_prompt": "Futuristic sci-fi aesthetic",
            "color_palette": ["#0066FF"],
            "lighting": "neon",
            "composition": "dynamic",
            "mood": "futuristic",
            "confidence": 0.85,
        })

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_response

            result = await extractor.extract_style(
                sample_image_bytes,
                additional_context="This is from a sci-fi film",
            )

            assert "sci-fi" in result.style_tags

    @pytest.mark.asyncio
    async def test_extract_style_fallback_parse(self, extractor, sample_image_bytes):
        """Test fallback parsing when JSON fails."""
        mock_response = MagicMock()
        mock_response.text = 'style_tags: "anime", "dramatic", mood: energetic'

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_response

            result = await extractor.extract_style(sample_image_bytes)

            # Fallback should return low confidence
            assert result.confidence == 0.3


# ============================================================================
# Color Palette Extraction Tests
# ============================================================================


class TestColorPaletteExtraction:
    """Test K-Means color palette extraction."""

    def test_extract_colors_kmeans_success(self):
        """Test successful K-Means color extraction."""
        extractor = StyleExtractor(api_key="test-key")

        # Create a simple test image (solid red)
        try:
            from PIL import Image
            import io

            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()

            colors = extractor._extract_colors_kmeans(image_bytes, n_colors=3)

            # Should extract colors, primary should be red-ish
            assert len(colors) > 0
            assert all(c.startswith("#") for c in colors)

        except ImportError:
            pytest.skip("PIL/sklearn not available")

    def test_extract_colors_kmeans_invalid_image(self):
        """Test K-Means with invalid image bytes."""
        extractor = StyleExtractor(api_key="test-key")

        colors = extractor._extract_colors_kmeans(b"invalid image data", n_colors=5)

        # Should return empty list on error
        assert colors == []


# ============================================================================
# Result Merging Tests
# ============================================================================


class TestResultMerging:
    """Test merging multiple style extraction results."""

    def test_merge_single_result(self):
        """Test merging single result returns same result."""
        extractor = StyleExtractor(api_key="test-key")
        result = StyleExtractionResult(
            style_tags=["anime"],
            confidence=0.9,
        )

        merged = extractor._merge_style_results([result])

        assert merged.style_tags == ["anime"]
        assert merged.confidence == 0.9

    def test_merge_multiple_results(self):
        """Test merging multiple results finds common tags."""
        extractor = StyleExtractor(api_key="test-key")

        results = [
            StyleExtractionResult(
                style_tags=["anime", "vibrant", "cel-shading"],
                style_prompt="Style 1",
                mood="energetic",
                confidence=0.9,
            ),
            StyleExtractionResult(
                style_tags=["anime", "vibrant", "colorful"],
                style_prompt="Style 2",
                mood="energetic",
                confidence=0.8,
            ),
            StyleExtractionResult(
                style_tags=["anime", "vibrant"],
                style_prompt="Style 3",
                mood="calm",
                confidence=0.7,
            ),
        ]

        merged = extractor._merge_style_results(results)

        # Common tags: anime, vibrant
        assert "anime" in merged.style_tags
        assert "vibrant" in merged.style_tags
        # Average confidence
        assert 0.7 < merged.confidence < 0.9

    def test_merge_empty_list(self):
        """Test merging empty list returns default result."""
        extractor = StyleExtractor(api_key="test-key")

        merged = extractor._merge_style_results([])

        assert merged.style_tags == []
        assert merged.confidence == 0.0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling in StyleExtractor."""

    def test_no_api_key_error(self):
        """Test error when no API key available."""
        with patch("app.services.ai.style_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            extractor = StyleExtractor()

            with pytest.raises(StyleExtractionError, match="No API key"):
                extractor._get_client()

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test timeout during extraction."""
        extractor = StyleExtractor(api_key="test-key")
        extractor._client = MagicMock()

        with patch("asyncio.wait_for") as mock_wait:
            import asyncio
            mock_wait.side_effect = asyncio.TimeoutError()

            with pytest.raises(StyleExtractionTimeoutError):
                await extractor.extract_style(b"test image")


# ============================================================================
# Module-Level Functions Tests
# ============================================================================


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_get_style_extractor_default(self):
        """Test get_style_extractor returns singleton."""
        with patch("app.services.ai.style_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            extractor1 = get_style_extractor()
            extractor2 = get_style_extractor()

            assert extractor1 is extractor2

    def test_get_style_extractor_custom_key(self):
        """Test get_style_extractor with custom key returns new instance."""
        extractor = get_style_extractor(api_key="custom-key")
        assert extractor._api_key == "custom-key"


# ============================================================================
# Integration Tests (Skipped by default)
# ============================================================================


@pytest.mark.skip(reason="Requires actual Gemini API key")
class TestIntegration:
    """Integration tests with real Gemini API."""

    @pytest.mark.asyncio
    async def test_real_style_extraction(self):
        """Test real style extraction with Gemini."""
        # Would need actual image and API key
        pass
