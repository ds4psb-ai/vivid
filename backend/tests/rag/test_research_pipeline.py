"""Tests for Tavily Research Pipeline.

Tests cover:
- Content hashing and deduplication
- License detection heuristics
- Quality assessment
- Document processing
- Pipeline integration (mocked)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.research_pipeline import (
    ResearchDocument,
    ResearchPipeline,
    ResearchResult,
    PERMISSIVE_INDICATORS,
    RESTRICTED_INDICATORS,
    HIGH_QUALITY_DOMAINS,
)
from app.tavily_client import TavilySearchResult, TavilySearchResponse


class TestContentHashing:
    """Test content hash computation for deduplication."""

    def test_hash_identical_content(self):
        """Identical content should produce same hash."""
        content = "This is test content for hashing."
        hash1 = ResearchPipeline._compute_hash(content)
        hash2 = ResearchPipeline._compute_hash(content)
        assert hash1 == hash2

    def test_hash_different_content(self):
        """Different content should produce different hash."""
        hash1 = ResearchPipeline._compute_hash("Content A")
        hash2 = ResearchPipeline._compute_hash("Content B")
        assert hash1 != hash2

    def test_hash_whitespace_normalized(self):
        """Whitespace differences should be normalized."""
        hash1 = ResearchPipeline._compute_hash("test   content")
        hash2 = ResearchPipeline._compute_hash("test content")
        assert hash1 == hash2

    def test_hash_case_normalized(self):
        """Case differences should be normalized."""
        hash1 = ResearchPipeline._compute_hash("Test Content")
        hash2 = ResearchPipeline._compute_hash("test content")
        assert hash1 == hash2

    def test_hash_length(self):
        """Hash should be 16 characters."""
        hash1 = ResearchPipeline._compute_hash("any content")
        assert len(hash1) == 16


class TestLicenseDetection:
    """Test license status detection heuristics."""

    @pytest.mark.parametrize("indicator", PERMISSIVE_INDICATORS[:5])
    def test_permissive_indicators(self, indicator):
        """Content with permissive indicators should be marked permissive."""
        content = f"This content is under {indicator} license."
        result = ResearchPipeline._check_license(content, "https://example.com")
        assert result == "permissive"

    @pytest.mark.parametrize("indicator", RESTRICTED_INDICATORS[:3])
    def test_restricted_indicators(self, indicator):
        """Content with restricted indicators should be marked restricted."""
        content = f"This content has {indicator}."
        result = ResearchPipeline._check_license(content, "https://example.com")
        assert result == "restricted"

    def test_url_based_permissive(self):
        """URLs with .edu should be permissive."""
        result = ResearchPipeline._check_license(
            "Some content",
            "https://stanford.edu/research"
        )
        assert result == "permissive"

    def test_arxiv_permissive(self):
        """arxiv.org URLs should be permissive."""
        result = ResearchPipeline._check_license(
            "Some content",
            "https://arxiv.org/abs/1234.5678"
        )
        assert result == "permissive"

    def test_unknown_license(self):
        """Content without indicators should be unknown."""
        result = ResearchPipeline._check_license(
            "Generic content without any license info",
            "https://generic-site.com"
        )
        assert result == "unknown"


class TestQualityAssessment:
    """Test document quality tier assessment."""

    @pytest.mark.parametrize("domain", HIGH_QUALITY_DOMAINS[:3])
    def test_high_quality_domains(self, domain):
        """High quality domains should be marked high."""
        result = ResearchPipeline._assess_quality(f"https://{domain}/page", 0.5)
        assert result == "high"

    def test_high_score_is_high_quality(self):
        """High relevance score should be high quality."""
        result = ResearchPipeline._assess_quality("https://unknown.com", 0.85)
        assert result == "high"

    def test_medium_score_is_standard(self):
        """Medium score should be standard quality."""
        result = ResearchPipeline._assess_quality("https://unknown.com", 0.6)
        assert result == "standard"

    def test_low_score_is_low_quality(self):
        """Low score should be low quality."""
        result = ResearchPipeline._assess_quality("https://unknown.com", 0.3)
        assert result == "low"


class TestDomainExtraction:
    """Test URL domain extraction."""

    def test_simple_domain(self):
        """Extract simple domain."""
        result = ResearchPipeline._extract_domain("https://example.com/page")
        assert result == "example.com"

    def test_www_stripped(self):
        """www. prefix should be stripped."""
        result = ResearchPipeline._extract_domain("https://www.example.com/page")
        assert result == "example.com"

    def test_subdomain_preserved(self):
        """Subdomains (except www) should be preserved."""
        result = ResearchPipeline._extract_domain("https://api.example.com/v1")
        assert result == "api.example.com"

    def test_invalid_url(self):
        """Invalid URL should return 'unknown'."""
        result = ResearchPipeline._extract_domain("not a url")
        assert result == "unknown"


class TestTagExtraction:
    """Test semantic tag extraction from content."""

    def test_auteur_tag_added(self):
        """Auteur key should be added as tag."""
        tags = ResearchPipeline._extract_tags("Some content", auteur_key="bong")
        assert "bong" in tags

    def test_cinematography_keywords_detected(self):
        """Cinematography keywords should be detected."""
        content = "The cinematography uses shallow focus and dramatic lighting."
        tags = ResearchPipeline._extract_tags(content)
        assert "cinematography" in tags
        assert "lighting" in tags
        assert "focus" in tags

    def test_max_tags_limit(self):
        """Tags should be limited to 10."""
        content = " ".join([
            "cinematography", "shot", "framing", "composition",
            "lighting", "color", "camera", "lens", "focus",
            "editing", "montage", "mise-en-scene", "visual style",
        ])
        tags = ResearchPipeline._extract_tags(content)
        assert len(tags) <= 10


class TestDeduplication:
    """Test document deduplication."""

    def test_dedup_removes_duplicates(self):
        """Duplicate documents should be removed."""
        pipeline = ResearchPipeline()

        docs = [
            ResearchDocument(
                id="doc1",
                title="Test",
                url="https://example.com/1",
                content="Same content here",
                content_hash=ResearchPipeline._compute_hash("Same content here"),
                source_domain="example.com",
                query="test",
            ),
            ResearchDocument(
                id="doc2",
                title="Test 2",
                url="https://example.com/2",
                content="Same content here",
                content_hash=ResearchPipeline._compute_hash("Same content here"),
                source_domain="example.com",
                query="test",
            ),
        ]

        unique, removed = pipeline.dedup(docs)
        assert len(unique) == 1
        assert removed == 1

    def test_dedup_preserves_unique(self):
        """Unique documents should be preserved."""
        pipeline = ResearchPipeline()

        docs = [
            ResearchDocument(
                id="doc1",
                title="Test 1",
                url="https://example.com/1",
                content="Content A",
                content_hash=ResearchPipeline._compute_hash("Content A"),
                source_domain="example.com",
                query="test",
            ),
            ResearchDocument(
                id="doc2",
                title="Test 2",
                url="https://example.com/2",
                content="Content B",
                content_hash=ResearchPipeline._compute_hash("Content B"),
                source_domain="example.com",
                query="test",
            ),
        ]

        unique, removed = pipeline.dedup(docs)
        assert len(unique) == 2
        assert removed == 0


class TestLicenseFiltering:
    """Test license-based filtering."""

    def test_restricted_filtered(self):
        """Restricted license documents should be filtered."""
        pipeline = ResearchPipeline()

        docs = [
            ResearchDocument(
                id="doc1",
                title="Open",
                url="https://example.com/1",
                content="Content",
                content_hash="hash1",
                source_domain="example.com",
                query="test",
                license_status="permissive",
            ),
            ResearchDocument(
                id="doc2",
                title="Restricted",
                url="https://example.com/2",
                content="Content",
                content_hash="hash2",
                source_domain="example.com",
                query="test",
                license_status="restricted",
            ),
        ]

        filtered, count = pipeline.filter_by_license(docs)
        assert len(filtered) == 1
        assert filtered[0].id == "doc1"
        assert count == 1

    def test_unknown_allowed_by_default(self):
        """Unknown license should be allowed by default."""
        pipeline = ResearchPipeline()

        docs = [
            ResearchDocument(
                id="doc1",
                title="Unknown",
                url="https://example.com/1",
                content="Content",
                content_hash="hash1",
                source_domain="example.com",
                query="test",
                license_status="unknown",
            ),
        ]

        filtered, count = pipeline.filter_by_license(docs, allow_unknown=True)
        assert len(filtered) == 1
        assert count == 0

    def test_unknown_filtered_when_strict(self):
        """Unknown license should be filtered when strict."""
        pipeline = ResearchPipeline()

        docs = [
            ResearchDocument(
                id="doc1",
                title="Unknown",
                url="https://example.com/1",
                content="Content",
                content_hash="hash1",
                source_domain="example.com",
                query="test",
                license_status="unknown",
            ),
        ]

        filtered, count = pipeline.filter_by_license(docs, allow_unknown=False)
        assert len(filtered) == 0
        assert count == 1


class TestResearchDocument:
    """Test ResearchDocument dataclass."""

    def test_to_dict(self):
        """to_dict should return serializable dictionary."""
        doc = ResearchDocument(
            id="test_id",
            title="Test Title",
            url="https://example.com",
            content="Test content",
            content_hash="abc123",
            source_domain="example.com",
            query="test query",
            auteur_key="bong",
            dimension="4D",
            relevance_score=0.85,
            tags=["tag1", "tag2"],
        )

        result = doc.to_dict()

        assert result["id"] == "test_id"
        assert result["title"] == "Test Title"
        assert result["auteur_key"] == "bong"
        assert result["dimension"] == "4D"
        assert result["relevance_score"] == 0.85
        assert "tag1" in result["tags"]

        # Should be JSON serializable
        json.dumps(result)


class TestResearchResult:
    """Test ResearchResult dataclass."""

    def test_summary(self):
        """Summary should be human-readable."""
        result = ResearchResult(
            query="test query",
            total_found=10,
            documents=[],
            duplicates_removed=2,
            license_filtered=1,
            high_quality_count=3,
            permissive_license_count=5,
        )

        summary = result.summary()

        assert "test query" in summary
        assert "10" in summary
        assert "Duplicates: 2" in summary
        assert "License filtered: 1" in summary


class TestPipelineIntegration:
    """Integration tests with mocked Tavily client."""

    @pytest.fixture
    def mock_tavily(self):
        """Create a mock Tavily client."""
        mock = MagicMock()
        # Raw content must be > 100 chars to pass the filter
        long_content_1 = "This is a comprehensive analysis of cinematography techniques used in modern filmmaking. " * 3
        long_content_2 = "Detailed examination of visual storytelling and camera work in contemporary cinema. " * 3
        mock.search = AsyncMock(return_value=TavilySearchResponse(
            query="test query",
            results=[
                TavilySearchResult(
                    title="Test Result 1",
                    url="https://arxiv.org/paper1",
                    content="This is test content about cinematography.",
                    score=0.9,
                    raw_content=long_content_1,
                ),
                TavilySearchResult(
                    title="Test Result 2",
                    url="https://example.com/page",
                    content="Another result with content.",
                    score=0.7,
                    raw_content=long_content_2,
                ),
            ],
        ))
        return mock

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_tavily):
        """Search should return Tavily results."""
        pipeline = ResearchPipeline(tavily_client=mock_tavily)
        results = await pipeline.search("test query")

        assert len(results) == 2
        mock_tavily.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_processes_results(self, mock_tavily):
        """Extract should process search results into documents."""
        pipeline = ResearchPipeline(tavily_client=mock_tavily)

        search_results = [
            TavilySearchResult(
                title="Test",
                url="https://example.com",
                content="Short",
                score=0.8,
                raw_content="Full content that is longer than 100 characters " * 3,
            ),
        ]

        docs = await pipeline.extract(
            results=search_results,
            query="test",
            auteur_key="bong",
            dimension="4D",
        )

        assert len(docs) == 1
        assert docs[0].auteur_key == "bong"
        assert docs[0].dimension == "4D"

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_tavily, tmp_path):
        """Full pipeline should search, extract, dedup, filter, and save."""
        pipeline = ResearchPipeline(
            tavily_client=mock_tavily,
            output_dir=tmp_path,
        )

        result = await pipeline.research(
            query="cinematography techniques",
            auteur_key="nolan",
            dimension="4D",
            max_results=5,
            save_results=True,
        )

        assert result.total_found == 2
        assert result.saved_to is not None
        assert Path(result.saved_to).exists()

        # Check saved file
        saved_data = json.loads(Path(result.saved_to).read_text())
        assert len(saved_data) > 0

    @pytest.mark.asyncio
    async def test_pipeline_skips_short_content(self, mock_tavily):
        """Pipeline should skip content shorter than 100 chars."""
        mock_tavily.search = AsyncMock(return_value=TavilySearchResponse(
            query="test",
            results=[
                TavilySearchResult(
                    title="Short",
                    url="https://example.com",
                    content="Too short",
                    score=0.9,
                    raw_content="Too short",
                ),
            ],
        ))

        pipeline = ResearchPipeline(tavily_client=mock_tavily)
        result = await pipeline.research(
            query="test",
            save_results=False,
        )

        assert len(result.documents) == 0


class TestIdGeneration:
    """Test document ID generation."""

    def test_id_format(self):
        """ID should follow expected format."""
        id1 = ResearchPipeline._generate_id("query", "https://example.com/page")
        assert id1.startswith("research_")
        assert len(id1) > 20  # research_ + date + _ + hash

    def test_id_unique_for_different_urls(self):
        """Different URLs should produce different IDs."""
        id1 = ResearchPipeline._generate_id("query", "https://example.com/page1")
        id2 = ResearchPipeline._generate_id("query", "https://example.com/page2")
        assert id1 != id2

    def test_id_consistent(self):
        """Same inputs should produce same ID."""
        id1 = ResearchPipeline._generate_id("query", "https://example.com")
        id2 = ResearchPipeline._generate_id("query", "https://example.com")
        # Date part will be same if run in same day
        assert id1 == id2
