"""Tests for app.core.utils.rrf."""
import pytest

from app.core.utils.rrf import (
    reciprocal_rank_fusion,
    weighted_rrf,
    merge_and_dedupe,
)


class TestReciprocalRankFusion:
    """reciprocal_rank_fusion 테스트."""

    def test_basic_fusion(self):
        """기본 RRF 융합."""
        lists = [
            [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)],
            [("doc2", 0.95), ("doc1", 0.85), ("doc4", 0.6)],
        ]

        result = reciprocal_rank_fusion(lists, k=60)

        # doc1과 doc2가 두 리스트에 모두 있으므로 상위에 위치해야 함
        doc_ids = [doc_id for doc_id, _ in result]
        assert "doc1" in doc_ids[:2]
        assert "doc2" in doc_ids[:2]

    def test_single_list(self):
        """단일 리스트 RRF."""
        lists = [
            [("doc1", 0.9), ("doc2", 0.8)],
        ]

        result = reciprocal_rank_fusion(lists, k=60)

        assert result[0][0] == "doc1"
        assert result[1][0] == "doc2"

    def test_empty_lists(self):
        """빈 리스트 처리."""
        result = reciprocal_rank_fusion([], k=60)
        assert result == []

    def test_limit_parameter(self):
        """limit 파라미터."""
        lists = [
            [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7), ("doc4", 0.6)],
        ]

        result = reciprocal_rank_fusion(lists, k=60, limit=2)

        assert len(result) == 2

    def test_min_score_filter(self):
        """min_score 필터링."""
        lists = [
            [("doc1", 0.9), ("doc2", 0.8)],
        ]

        result = reciprocal_rank_fusion(lists, k=60, min_score=0.02)

        # k=60이면 rank 1의 score는 1/61 ≈ 0.0164
        # min_score=0.02보다 낮으므로 결과 없을 수 있음
        for _, score in result:
            assert score >= 0.02

    def test_rrf_formula(self):
        """RRF 수식 검증: score = 1 / (k + rank)."""
        lists = [
            [("doc1", 0.9)],  # rank 1
        ]

        result = reciprocal_rank_fusion(lists, k=60)

        expected_score = 1.0 / (60 + 1)  # = 1/61 ≈ 0.01639
        assert abs(result[0][1] - expected_score) < 0.0001


class TestWeightedRRF:
    """weighted_rrf 테스트."""

    def test_basic_weighted_fusion(self):
        """기본 가중치 RRF 융합."""
        source_results = [
            ("source1", 1.5, [{"id": "doc1", "score": 0.9}, {"id": "doc2", "score": 0.8}]),
            ("source2", 1.0, [{"id": "doc2", "score": 0.95}, {"id": "doc3", "score": 0.7}]),
        ]

        result = weighted_rrf(source_results, k=60, limit=5)

        assert len(result) > 0
        # doc2가 양쪽에 있으므로 상위에 위치해야 함
        doc_ids = [doc_id for doc_id, _, _ in result]
        assert "doc2" in doc_ids

    def test_weight_effect(self):
        """가중치 효과 검증."""
        # 높은 가중치 소스
        high_weight = [
            ("high", 2.0, [{"id": "doc_high", "score": 0.9}]),
            ("low", 0.5, [{"id": "doc_low", "score": 0.9}]),
        ]

        result = weighted_rrf(high_weight, k=60, limit=10)

        # 가중치가 높은 문서가 더 높은 점수
        scores = {doc_id: score for doc_id, score, _ in result}
        assert scores.get("doc_high", 0) > scores.get("doc_low", 0)

    def test_custom_extractors(self):
        """커스텀 추출 함수."""
        class Doc:
            def __init__(self, doc_id, score):
                self.doc_id = doc_id
                self.score = score

        source_results = [
            ("source1", 1.0, [Doc("doc1", 0.9), Doc("doc2", 0.8)]),
        ]

        def id_extractor(d):
            return d.doc_id

        def score_extractor(d):
            return d.score

        result = weighted_rrf(
            source_results,
            k=60,
            id_extractor=id_extractor,
            score_extractor=score_extractor,
        )

        assert len(result) == 2


class TestMergeAndDedupe:
    """merge_and_dedupe 테스트."""

    def test_basic_merge(self):
        """기본 병합."""
        lists = [
            [{"id": "doc1", "score": 0.9}],
            [{"id": "doc2", "score": 0.8}],
        ]

        result = merge_and_dedupe(lists)

        assert len(result) == 2

    def test_deduplication(self):
        """중복 제거."""
        lists = [
            [{"id": "doc1", "score": 0.9}],
            [{"id": "doc1", "score": 0.95}],  # 동일 ID, 더 높은 점수
        ]

        result = merge_and_dedupe(lists)

        assert len(result) == 1
        # 더 높은 점수 유지
        assert result[0]["score"] == 0.95

    def test_limit_parameter(self):
        """limit 파라미터."""
        lists = [
            [{"id": f"doc{i}", "score": 1.0 - i * 0.1} for i in range(10)],
        ]

        result = merge_and_dedupe(lists, limit=3)

        assert len(result) == 3

    def test_empty_lists(self):
        """빈 리스트 처리."""
        result = merge_and_dedupe([])
        assert result == []

        result = merge_and_dedupe([[]])
        assert result == []
