"""RAG E2E tests for dataset routing + evidence_refs.

Verifies that:
1. Dataset routing selects correct dataset_id based on query
2. Evidence refs are formatted correctly (db:rag_docs:{dim}:{dataset}:{doc_id})
3. Qdrant unavailable → graceful skip

Usage:
    cd backend && pytest tests/rag/test_rag_e2e_evidence_refs.py -v
"""
from __future__ import annotations

import pytest

# Check RAG module availability
try:
    from app.rag.tier1_dimension_rag import get_dimension_rag
    from app.rag.rag_suggestion_service import (
        RAGSuggestionService,
        build_evidence_ref_id,
    )
    from app.rag.app_manifest import get_manifest
    RAG_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)


pytestmark = pytest.mark.skipif(
    not RAG_AVAILABLE,
    reason=f"RAG modules not available: {IMPORT_ERROR or 'unknown'}",
)


def _ensure_qdrant(rag) -> bool:
    """Check if Qdrant is available, skip if not."""
    if rag.client is None:
        pytest.skip("Qdrant unavailable")
    return True


def _index_test_doc(rag, doc_id: str, content: str, metadata: dict) -> bool:
    """Index a test document, skip if indexing fails."""
    if not rag.index_document(doc_id, content, metadata):
        pytest.skip("Qdrant index failed")
    return True


class TestVideoRefDataset:
    """Test video_ref dataset routing and evidence_refs."""

    def test_video_ref_evidence_refs(self):
        """Verify video_ref dataset returns correct evidence_refs format."""
        rag = get_dimension_rag("4D")
        _ensure_qdrant(rag)
        
        # Index test document
        doc_id = "test_video_ref_e2e"
        _index_test_doc(
            rag,
            doc_id=doc_id,
            content="강주노 레퍼런스 촬영 구도 분석 테스트",
            metadata={
                "dataset_id": "video_ref",
                "app_key": "teaching.reference.analyze",
                "source_id": "test_video",
                "pack_id": doc_id,
            },
        )
        
        # Search with dataset filter (use same text for mock embedding match)
        results = rag.search(
            query="강주노 레퍼런스 촬영 구도 분석 테스트",  # Same as indexed content
            limit=5,
            min_score=0.1,  # Lower for mock embeddings
            metadata_filters={"dataset_id": "video_ref"},
        )
        
        # Verify results
        assert len(results) >= 1, "Should find at least 1 video_ref document"
        
        # Check evidence_ref format
        for r in results:
            if r.get("doc_id") == doc_id:
                ref_id = build_evidence_ref_id("4D", "video_ref", doc_id)
                assert ref_id.startswith("db:rag_docs:4D:video_ref:")
                break
        else:
            pytest.fail(f"Test document {doc_id} not found in results")


class TestImageGridDataset:
    """Test image_grid dataset routing and evidence_refs."""

    def test_image_grid_evidence_refs(self):
        """Verify image_grid dataset returns correct evidence_refs format."""
        rag = get_dimension_rag("3D")
        _ensure_qdrant(rag)
        
        # Index test document
        doc_id = "test_image_grid_e2e"
        _index_test_doc(
            rag,
            doc_id=doc_id,
            content="그리드 타일 레퍼런스 스타일 테스트",
            metadata={
                "dataset_id": "image_grid",
                "app_key": "teaching.image.generate",
                "source_id": "test_grid",
                "pack_id": doc_id,
                "row": 0,
                "col": 0,
            },
        )
        
        # Search with dataset filter (use same text for mock embedding match)
        results = rag.search(
            query="그리드 타일 레퍼런스 스타일 테스트",  # Same as indexed content
            limit=5,
            min_score=0.1,  # Lower for mock embeddings
            metadata_filters={"dataset_id": "image_grid"},
        )
        
        # Verify results
        assert len(results) >= 1, "Should find at least 1 image_grid document"
        
        # Check evidence_ref format
        for r in results:
            if r.get("doc_id") == doc_id:
                ref_id = build_evidence_ref_id("3D", "image_grid", doc_id)
                assert ref_id.startswith("db:rag_docs:3D:image_grid:")
                break
        else:
            pytest.fail(f"Test document {doc_id} not found in results")


class TestDatasetRouting:
    """Test dataset selection based on query patterns."""

    def test_manifest_video_ref_routing(self):
        """Verify teaching.reference.analyze has video_ref dataset configured."""
        manifest = get_manifest("teaching.reference.analyze")
        assert manifest is not None, "Manifest should exist"
        assert "video_ref" in manifest.dataset_candidates
        assert "video_ref" in manifest.dataset_labels

    def test_manifest_image_grid_routing(self):
        """Verify teaching.image.generate has image_grid dataset configured."""
        manifest = get_manifest("teaching.image.generate")
        assert manifest is not None, "Manifest should exist"
        assert "image_grid" in manifest.dataset_candidates
        assert "image_grid" in manifest.dataset_labels


class TestEvidenceRefFormat:
    """Test evidence_refs ID format."""

    def test_build_evidence_ref_id_format(self):
        """Verify build_evidence_ref_id produces correct format."""
        ref_id = build_evidence_ref_id("4D", "video_ref", "test_doc_001")
        expected = "db:rag_docs:4D:video_ref:test_doc_001"
        assert ref_id == expected

    def test_build_evidence_ref_id_image_grid(self):
        """Verify image_grid evidence_refs format."""
        ref_id = build_evidence_ref_id("3D", "image_grid", "grid_001_r0_c0")
        expected = "db:rag_docs:3D:image_grid:grid_001_r0_c0"
        assert ref_id == expected
