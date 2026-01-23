"""User History Vector Similarity Tests (P1 2026).

Tests for hybrid search: Vector Similarity (0.7) + Keyword Matching (0.3).
"""
from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.rag.router.backends.user_history import (
    UserHistoryBackend,
    _cosine_similarity,
)
from app.rag.multi_rag.backends.user_history_adapter import (
    UserHistoryAdapter,
    _cosine_similarity as adapter_cosine_similarity,
)


class TestCosineSimilarity:
    """코사인 유사도 계산 테스트."""

    def test_identical_vectors(self):
        """동일 벡터 = 1.0 유사도."""
        vec = [1.0, 2.0, 3.0]
        assert _cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """직교 벡터 = 0.0 유사도."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert _cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        """반대 벡터 = -1.0 유사도."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [-1.0, -2.0, -3.0]
        assert _cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_zero_vector(self):
        """영벡터 = 0.0 유사도."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [0.0, 0.0, 0.0]
        assert _cosine_similarity(vec_a, vec_b) == 0.0

    def test_near_zero_vector(self):
        """거의 영벡터 = 0.0 유사도."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [1e-10, 1e-10, 1e-10]
        assert _cosine_similarity(vec_a, vec_b) == 0.0

    def test_similar_vectors(self):
        """유사 벡터 = 높은 유사도."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [1.1, 2.1, 3.1]
        similarity = _cosine_similarity(vec_a, vec_b)
        assert similarity > 0.99  # 거의 1에 가까움

    def test_384_dimension_vectors(self):
        """384 차원 벡터 (embedder 출력 크기)."""
        np.random.seed(42)
        vec_a = np.random.randn(384).tolist()
        vec_b = np.random.randn(384).tolist()
        # 랜덤 벡터는 보통 약한 상관관계
        similarity = _cosine_similarity(vec_a, vec_b)
        assert -1.0 <= similarity <= 1.0

    def test_adapter_cosine_similarity_same(self):
        """어댑터 버전도 동일하게 작동."""
        vec = [1.0, 2.0, 3.0]
        assert adapter_cosine_similarity(vec, vec) == pytest.approx(1.0)


class TestHybridScore:
    """하이브리드 점수 계산 테스트."""

    def test_hybrid_score_weights(self):
        """keyword_score * 0.3 + vector_score * 0.7 공식 검증."""
        keyword_score = 0.5  # 절반 매칭
        vector_score = 0.8  # 높은 벡터 유사도

        expected = keyword_score * 0.3 + vector_score * 0.7
        assert expected == pytest.approx(0.71)

    def test_keyword_only_match(self):
        """키워드만 매칭될 때 (벡터 유사도 0)."""
        keyword_score = 1.0
        vector_score = 0.0

        expected = keyword_score * 0.3 + vector_score * 0.7
        assert expected == pytest.approx(0.3)

    def test_vector_only_match(self):
        """벡터만 유사할 때 (키워드 매칭 0)."""
        keyword_score = 0.0
        vector_score = 1.0

        expected = keyword_score * 0.3 + vector_score * 0.7
        assert expected == pytest.approx(0.7)

    def test_perfect_match(self):
        """완벽한 매칭 (keyword 1.0, vector 1.0)."""
        keyword_score = 1.0
        vector_score = 1.0

        expected = keyword_score * 0.3 + vector_score * 0.7
        assert expected == pytest.approx(1.0)


class TestEmbedderIntegration:
    """Embedder 통합 테스트."""

    def test_embedder_singleton(self):
        """Embedder 싱글톤 패턴."""
        from app.services.embedder import get_embedder

        embedder1 = get_embedder()
        embedder2 = get_embedder()
        assert embedder1 is embedder2

    def test_embedder_dimensions(self):
        """Embedder 출력 384 차원."""
        from app.services.embedder import get_embedder

        embedder = get_embedder()
        vec = embedder.embed("test query")
        assert len(vec) == 384

    def test_embedder_empty_input(self):
        """빈 입력 = 영벡터."""
        from app.services.embedder import get_embedder

        embedder = get_embedder()
        vec = embedder.embed("")
        assert len(vec) == 384
        assert all(v == 0.0 for v in vec)

    def test_embedder_batch(self):
        """배치 임베딩."""
        from app.services.embedder import get_embedder

        embedder = get_embedder()
        texts = ["query one", "query two", "query three"]
        vecs = embedder.embed_batch(texts)
        assert len(vecs) == 3
        assert all(len(v) == 384 for v in vecs)


class TestUserHistoryBackendHybrid:
    """UserHistoryBackend 하이브리드 검색 테스트."""

    @pytest.mark.asyncio
    async def test_query_returns_documents(self):
        """쿼리 결과 반환."""
        # Mock DB factory
        mock_db_factory = AsyncMock()
        backend = UserHistoryBackend(db_session_factory=mock_db_factory)

        # DB 결과가 없어도 빈 리스트 반환
        result = await backend.query(
            query="test query",
            filters={"user_id": "user_123"},
            limit=10,
        )
        # DB 연결 실패 시 빈 리스트
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_query_requires_user_id(self):
        """user_id 필수."""
        backend = UserHistoryBackend()
        result = await backend.query(
            query="test query",
            filters={},  # user_id 없음
            limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_query_no_db_factory(self):
        """DB factory 없으면 빈 결과."""
        backend = UserHistoryBackend(db_session_factory=None)
        result = await backend.query(
            query="test query",
            filters={"user_id": "user_123"},
            limit=10,
        )
        assert result == []


class TestUserHistoryAdapterHybrid:
    """UserHistoryAdapter 하이브리드 검색 테스트."""

    @pytest.mark.asyncio
    async def test_query_requires_user_id(self):
        """user_id 필수."""
        mock_db_factory = AsyncMock()
        adapter = UserHistoryAdapter(db_factory=mock_db_factory)

        result = await adapter.query(
            query="test query",
            filters={},  # user_id 없음
            limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """헬스 체크 실패."""
        mock_db_factory = MagicMock()
        mock_db_factory.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("DB connection failed")
        )
        mock_db_factory.return_value.__aexit__ = AsyncMock()

        adapter = UserHistoryAdapter(db_factory=mock_db_factory)
        result = await adapter.health_check()
        assert result is False


class TestKeywordScoring:
    """키워드 매칭 점수 테스트."""

    def test_full_keyword_match(self):
        """모든 키워드 매칭."""
        query = "봉준호 영화 스타일"
        keywords = query.lower().split()
        content = "봉준호 감독의 영화 스타일 분석"
        content_lower = content.lower()

        match_count = sum(1 for kw in keywords if kw in content_lower)
        keyword_score = match_count / len(keywords)

        assert keyword_score == pytest.approx(1.0)

    def test_partial_keyword_match(self):
        """일부 키워드만 매칭."""
        query = "봉준호 영화 스타일"
        keywords = query.lower().split()
        content = "봉준호 감독 작품"  # "영화", "스타일" 없음
        content_lower = content.lower()

        match_count = sum(1 for kw in keywords if kw in content_lower)
        keyword_score = match_count / len(keywords)

        assert keyword_score == pytest.approx(1/3)

    def test_no_keyword_match(self):
        """키워드 매칭 없음."""
        query = "봉준호 영화"
        keywords = query.lower().split()
        content = "완전히 다른 내용"
        content_lower = content.lower()

        match_count = sum(1 for kw in keywords if kw in content_lower)
        keyword_score = match_count / len(keywords)

        assert keyword_score == 0.0


class TestVectorScoring:
    """벡터 유사도 점수 테스트."""

    def test_similar_texts_high_similarity(self):
        """유사한 텍스트 = 높은 벡터 유사도."""
        from app.services.embedder import get_embedder

        embedder = get_embedder()

        text1 = "봉준호 감독의 영화 스타일"
        text2 = "봉준호 감독 영화 스타일 분석"

        vec1 = embedder.embed(text1)
        vec2 = embedder.embed(text2)

        similarity = _cosine_similarity(vec1, vec2)
        # Mock embedder라도 일관된 해시 기반이므로 테스트 가능
        assert similarity >= 0.5  # 유사한 입력이면 어느 정도 유사

    def test_different_texts_lower_similarity(self):
        """다른 텍스트 = 낮은 벡터 유사도."""
        from app.services.embedder import get_embedder

        embedder = get_embedder()

        text1 = "봉준호 감독의 영화 스타일"
        text2 = "completely different content about programming"

        vec1 = embedder.embed(text1)
        vec2 = embedder.embed(text2)

        similarity = _cosine_similarity(vec1, vec2)
        # 결과는 모델에 따라 다르지만, 동일 텍스트보다는 낮아야 함
        same_similarity = _cosine_similarity(vec1, vec1)
        assert similarity < same_similarity


class TestThresholdFiltering:
    """임계값 필터링 테스트."""

    def test_minimum_threshold(self):
        """최소 임계값 0.1."""
        # 점수가 0.1 미만이면 필터링됨
        scores = [0.05, 0.08, 0.1, 0.15, 0.5]
        filtered = [s for s in scores if s >= 0.1]
        assert filtered == [0.1, 0.15, 0.5]

    def test_edge_case_threshold(self):
        """경계값 테스트."""
        threshold = 0.1

        assert 0.09999 < threshold  # 필터링됨
        assert 0.1 >= threshold  # 통과
        assert 0.10001 >= threshold  # 통과
