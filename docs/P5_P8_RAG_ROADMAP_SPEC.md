# P5-P8 RAG Evolution Roadmap SPEC

> **Date**: 2026-01-15
> **Author**: Claude Opus 4.5
> **Version**: 1.0
> **Status**: APPROVED FOR IMPLEMENTATION

---

## 1. Executive Summary

P5-P8은 Vivid RAG 시스템을 **정적 검색 파이프라인**에서 **자기 진화하는 지식 런타임**으로 변환하는 로드맵입니다.

### Vision
```
P4 (Reranker) → P5 (Adaptive RAG) → P6 (Feedback) → P7 (Self-Correction) → P8 (Continual Learning)
     ✅              Query Router       Data Layer    Auto-Tuning         Knowledge Evolution
```

### Key Innovations
| Phase | Innovation | Impact |
|-------|------------|--------|
| P5 | Semantic Router + Skip Retrieval | -40ms latency, -25% cost |
| P6 | Implicit/Explicit Feedback Collection | Data foundation for ML |
| P7 | A/B Testing + Auto-Tuning | +10% avg user rating |
| P8 | Synthetic Data + KG Updates | Self-improving system |

---

## 2. Current State (Post-P4)

### 2.1 Completed Phases

| Phase | Description | Key Deliverables |
|-------|-------------|------------------|
| P0 | Qdrant Native Sparse | BM25 in-engine |
| P0.5 | Hybrid Collection Migration | Dense + Sparse vectors |
| P1 | YAML Manifest | 13 app configs externalized |
| P2 | Backend ABC + Auto-discovery | 3 pluggable backends |
| P3 | Ensemble Retriever | Weighted RRF Fusion |
| P4 | Reranker Plugin | VertexReranker, LocalCrossEncoder |

### 2.2 Current Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           hybrid_query()                │
                    │      _determine_strategy()              │
                    │    (Heuristic Router, score 0-4)        │
                    └─────────────────┬───────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │  auteur_first   │     │   dimension     │     │    parallel     │
    │  (NotebookLM)   │     │  (Vertex RAG)   │     │   (Both + RRF)  │
    └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
             │                       │                       │
             └───────────────────────┼───────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │       ensemble_retrieve()       │
                    │      (P3: Weighted RRF)         │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │      Reranker Stage (P4)        │
                    │   (Vertex / LocalCrossEncoder)  │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │      CRAG (Partial)             │
                    │  confidence < 0.6 → Grounding   │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                              HybridRAGResult
```

### 2.3 Gap Analysis

| Gap | Current | Target (P5-P8) |
|-----|---------|----------------|
| Query Classification | Heuristic (규칙 기반) | Semantic + LLM Hybrid |
| Skip Retrieval | 없음 | 단순 쿼리 20-30% skip |
| Feedback Loop | 없음 | Implicit + Explicit |
| Self-Correction | 없음 | Weekly prompt tuning |
| Continual Learning | 없음 | Monthly KG updates |

---

## 3. Phase 5: Adaptive RAG

### 3.1 Goals

1. **Query Classification**: 쿼리 유형/복잡도 자동 분류
2. **Semantic Routing**: 임베딩 기반 빠른 라우팅 (15ms)
3. **Skip Retrieval**: 단순 쿼리는 LLM 직접 답변
4. **Dynamic Strategy**: 복잡도에 따른 백엔드 선택
5. **Cost Optimization**: 불필요한 검색 비용 절감

### 3.2 Architecture

```
                         ┌─────────────────────────────────────────────────┐
                         │              Adaptive RAG Router                │
                         ├─────────────────────────────────────────────────┤
                         │                                                 │
User Query ──────────────▶  ┌─────────────────────────────────────────┐   │
                         │  │         SemanticRouter (15ms)            │   │
                         │  │                                          │   │
                         │  │  Query → Embed → KNN Match → QueryType   │   │
                         │  │         (MiniLM-L6, 384-dim)             │   │
                         │  └──────────────────┬───────────────────────┘   │
                         │                     │                           │
                         │         ┌───────────┼───────────┐               │
                         │         │           │           │               │
                         │         ▼           ▼           ▼               │
                         │    [simple]    [domain]    [ambiguous]          │
                         │         │           │           │               │
                         │         │           │           ▼               │
                         │         │           │    ┌─────────────────┐    │
                         │         │           │    │ LLM Classifier  │    │
                         │         │           │    │   (Fallback)    │    │
                         │         │           │    └────────┬────────┘    │
                         │         │           │             │             │
                         │         ▼           ▼             ▼             │
                         │  ┌─────────────────────────────────────────┐    │
                         │  │           Strategy Selector              │    │
                         │  └──────────────────┬───────────────────────┘    │
                         │                     │                            │
                         └─────────────────────┼────────────────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────┐
               │                               │                           │
               ▼                               ▼                           ▼
      ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
      │  Direct LLM     │          │  ensemble_rrf   │          │ full_pipeline   │
      │ (Skip Retrieval)│          │  (Standard)     │          │ (Multi-hop)     │
      └─────────────────┘          └─────────────────┘          └─────────────────┘
```

### 3.3 Query Types

```python
# app/rag/query_classifier.py
from enum import Enum

class QueryType(str, Enum):
    """쿼리 유형 분류."""

    # Skip Retrieval 가능
    SIMPLE_FACTUAL = "simple_factual"
    # "Python이란?", "HTTP 상태코드 200" → LLM 파라메트릭 지식

    CREATIVE = "creative"
    # "영화 시놉시스 써줘", "캐릭터 이름 추천" → 최소 검색

    # Standard Retrieval
    DOMAIN_SPECIFIC = "domain_specific"
    # "봉준호 롱테이크", "기생충 계단 장면" → NotebookLM + Qdrant

    RECENCY_REQUIRED = "recency_required"
    # "2026년 AI 트렌드", "최신 Gemini 기능" → Google Grounding

    # Full Pipeline
    MULTI_HOP = "multi_hop"
    # "왜 기생충의 계단이 상징적인가?", "비교 분석" → 전체 파이프라인

    AMBIGUOUS = "ambiguous"
    # 분류 불확실 → LLM Classifier 폴백
```

### 3.4 Strategy Mapping

| QueryType | Strategy | Skip Retrieval | Reranker | Grounding | Cost |
|-----------|----------|----------------|----------|-----------|------|
| simple_factual | direct_llm | ✅ | ❌ | ❌ | $0.001 |
| creative | minimal_rag | ✅ (선택) | ❌ | ❌ | $0.002 |
| domain_specific | ensemble_rrf | ❌ | ✅ | ❌ | $0.005 |
| recency_required | grounding_first | ❌ | ❌ | ✅ | $0.008 |
| multi_hop | full_pipeline | ❌ | ✅ | ✅ | $0.012 |
| ambiguous | ensemble_rrf | ❌ | ✅ | ❌ | $0.006 |

### 3.5 Implementation Tasks

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| P5.1.1 | QueryType Enum + Pydantic 스키마 | `app/rag/query_classifier.py` | 1h |
| P5.1.2 | SemanticRouter 구현 (MiniLM embedding) | `app/rag/semantic_router.py` | 3h |
| P5.1.3 | Route Examples YAML 작성 | `app/rag/manifests/_routes.yaml` | 2h |
| P5.1.4 | LLM Classifier 폴백 구현 | `app/rag/query_classifier.py` | 2h |
| P5.2.1 | Strategy Selector 구현 | `app/rag/strategy_selector.py` | 2h |
| P5.2.2 | YAML Manifest routing_rules 필드 | `app/rag/manifests/_schema.yaml` | 1h |
| P5.3.1 | Skip Retrieval 로직 (`hybrid_query()` 수정) | `app/rag/hybrid_rag.py` | 2h |
| P5.3.2 | Direct LLM 경로 구현 | `app/rag/direct_llm.py` | 2h |
| P5.4.1 | 단위 테스트 | `tests/rag/test_query_classifier.py` | 3h |
| P5.4.2 | 통합 테스트 | `tests/rag/test_adaptive_rag.py` | 2h |

**Total Effort**: ~20h (3-4일)

### 3.6 SemanticRouter Implementation

```python
# app/rag/semantic_router.py
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple
import yaml

class SemanticRouter:
    """임베딩 기반 Semantic Router (15ms target)."""

    # Singleton model cache
    _model: SentenceTransformer | None = None
    _routes: dict | None = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            cls._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return cls._model

    @classmethod
    def _load_routes(cls) -> dict:
        if cls._routes is None:
            routes_path = Path(__file__).parent / "manifests" / "_routes.yaml"
            with open(routes_path) as f:
                cls._routes = yaml.safe_load(f)
        return cls._routes

    async def classify(
        self,
        query: str,
        top_k: int = 1,
        threshold: float = 0.7,
    ) -> Tuple[QueryType, float]:
        """쿼리를 QueryType으로 분류.

        Args:
            query: 입력 쿼리
            top_k: 상위 K개 매칭 고려
            threshold: 최소 유사도 임계값

        Returns:
            (QueryType, confidence_score)
            confidence < threshold이면 AMBIGUOUS 반환
        """
        model = self._get_model()
        routes = self._load_routes()

        # Query embedding
        query_emb = model.encode(query, normalize_embeddings=True)

        best_type = QueryType.AMBIGUOUS
        best_score = 0.0

        for route in routes["routes"]:
            # Route examples embedding (cached)
            examples = route["examples"]
            example_embs = model.encode(examples, normalize_embeddings=True)

            # Cosine similarity
            similarities = np.dot(example_embs, query_emb)
            max_sim = float(np.max(similarities))

            if max_sim > best_score:
                best_score = max_sim
                best_type = QueryType(route["type"])

        if best_score < threshold:
            return (QueryType.AMBIGUOUS, best_score)

        return (best_type, best_score)
```

### 3.7 Routes YAML Example

```yaml
# app/rag/manifests/_routes.yaml
routes:
  - type: simple_factual
    examples:
      - "Python이란?"
      - "HTTP 상태코드 200 의미"
      - "API란 무엇인가?"
      - "JSON 형식 설명"
      - "변수 선언 방법"

  - type: domain_specific
    examples:
      - "봉준호 감독의 롱테이크 기법"
      - "기생충 계단 장면 분석"
      - "왕가위 색감 스타일"
      - "놀란 시간 구조"
      - "타란티노 대화 스타일"

  - type: recency_required
    examples:
      - "2026년 AI 트렌드"
      - "최신 Gemini 2.0 기능"
      - "오늘 날씨"
      - "최근 영화 개봉작"
      - "현재 환율"

  - type: multi_hop
    examples:
      - "왜 기생충의 계단이 상징적인가 설명해줘"
      - "봉준호와 놀란의 시각 스타일 비교"
      - "인셉션과 테넷의 시간 구조 차이점"
      - "한국 영화가 세계 시장에서 성공한 이유 분석"

  - type: creative
    examples:
      - "영화 시놉시스 써줘"
      - "캐릭터 이름 추천해줘"
      - "로맨스 영화 아이디어"
      - "대사 작성해줘"
```

### 3.8 YAML Manifest Extension

```yaml
# dimension.aesthetic.yaml (P5 enhanced)
app_key: dimension.aesthetic.direct
version: "2.0"

# P5: Routing configuration
routing:
  enabled: true
  semantic_threshold: 0.7
  llm_fallback: true
  skip_retrieval_types:
    - simple_factual
    - creative

# P4: Reranker (existing)
reranker:
  enabled: true
  backend: local_cross_encoder
  config:
    model: bge-base
    top_k: 5

# P2-P3: Backends (existing)
backends:
  - id: qdrant_hybrid
    weight: 0.6
  - id: notebooklm
    weight: 0.3
```

---

## 4. Phase 6: Feedback Collection

### 4.1 Goals

1. **Explicit Feedback**: 사용자 평점, 좋아요/싫어요, 신고
2. **Implicit Feedback**: 클릭률, 세션 시간, 재검색
3. **Classification Metrics**: P5 분류 정확도 추적
4. **Data Foundation**: P7/P8을 위한 데이터 축적

### 4.2 Database Schema

```python
# app/models_feedback.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class RAGResponse(Base):
    """RAG 응답 저장 (피드백 연결용)."""
    __tablename__ = "rag_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    query_hash = Column(String(64), index=True)  # SHA256 for grouping
    answer = Column(Text)

    # P5 Classification
    query_type = Column(String(50))  # simple_factual, domain_specific, etc.
    retrieval_skipped = Column(Boolean, default=False)
    strategy_used = Column(String(50))

    # Metrics
    confidence = Column(Float)
    latency_ms = Column(Integer)
    retrieval_count = Column(Integer)
    reranked = Column(Boolean, default=False)
    crag_triggered = Column(Boolean, default=False)

    # Sources
    sources = Column(JSONB)  # [{source_id, type, score}, ...]

    # Context
    app_key = Column(String(100), index=True)
    dimension = Column(String(10))
    auteur_key = Column(String(50))
    user_id = Column(UUID(as_uuid=True), index=True)

    created_at = Column(DateTime, server_default=func.now())


class RAGFeedback(Base):
    """RAG 피드백 수집."""
    __tablename__ = "rag_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id = Column(UUID(as_uuid=True), ForeignKey("rag_responses.id"))

    # Explicit Feedback
    rating = Column(Integer)  # 1-5 stars (nullable)
    feedback_type = Column(Enum("thumbs_up", "thumbs_down", "report", name="feedback_type_enum"))
    user_comment = Column(Text)

    # Implicit Feedback
    source_clicked = Column(Boolean, default=False)
    clicked_source_id = Column(String(100))
    session_duration_ms = Column(Integer)
    query_reformulated = Column(Boolean, default=False)
    reformulated_query = Column(Text)
    text_copied = Column(Boolean, default=False)
    copied_length = Column(Integer)

    # Metadata
    user_id = Column(UUID(as_uuid=True), index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    response = relationship("RAGResponse", backref="feedbacks")
```

### 4.3 Collection API

```python
# app/routers/rag_feedback.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/rag/feedback", tags=["rag-feedback"])

class ExplicitFeedbackCreate(BaseModel):
    response_id: UUID
    rating: Optional[int] = None  # 1-5
    feedback_type: Optional[str] = None  # thumbs_up, thumbs_down, report
    comment: Optional[str] = None

class ImplicitFeedbackCreate(BaseModel):
    response_id: UUID
    event_type: str  # click, copy, reformulate
    source_id: Optional[str] = None
    duration_ms: Optional[int] = None
    new_query: Optional[str] = None
    copied_length: Optional[int] = None

@router.post("/explicit")
async def submit_explicit_feedback(
    feedback: ExplicitFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """명시적 피드백 제출 (평점, 좋아요/싫어요)."""
    ...

@router.post("/implicit")
async def track_implicit_feedback(
    feedback: ImplicitFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """암시적 피드백 추적 (클릭, 복사, 재검색)."""
    ...

@router.get("/metrics/{app_key}")
async def get_feedback_metrics(
    app_key: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """앱별 피드백 메트릭 조회."""
    ...
```

### 4.4 Implementation Tasks

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| P6.1.1 | RAGResponse/RAGFeedback 모델 | `app/models_feedback.py` | 2h |
| P6.1.2 | Alembic 마이그레이션 | `alembic/versions/xxx_add_feedback.py` | 1h |
| P6.2.1 | Feedback Router | `app/routers/rag_feedback.py` | 3h |
| P6.2.2 | FeedbackService | `app/services/feedback_service.py` | 2h |
| P6.3.1 | FeedbackAnalytics | `app/services/feedback_analytics.py` | 3h |
| P6.3.2 | Prometheus 메트릭 추가 | `app/rag/metrics.py` | 1h |
| P6.4.1 | hybrid_query() 응답 저장 연동 | `app/rag/hybrid_rag.py` | 2h |
| P6.4.2 | 테스트 | `tests/test_rag_feedback.py` | 2h |

**Total Effort**: ~16h (2-3일)

---

## 5. Phase 7: Self-Correction

### 5.1 Goals

1. **Prompt Auto-Tuning**: P5 분류 프롬프트 자동 개선
2. **A/B Testing**: 백엔드 weight, threshold 실험
3. **Drift Detection**: 분류 성능 저하 감지
4. **Automated Rollback**: 실험 실패 시 자동 롤백

### 5.2 Architecture

```
                    ┌────────────────────────────────────────┐
                    │      Weekly Self-Correction Loop       │
                    ├────────────────────────────────────────┤
                    │                                        │
                    │  1. Collect P6 Feedback (7 days)       │
                    │            │                           │
                    │            ▼                           │
                    │  2. Analyze Misclassifications         │
                    │     - Skip했는데 rating < 3            │
                    │     - CRAG 트리거율 분석               │
                    │            │                           │
                    │            ▼                           │
                    │  3. Generate Improved Prompt           │
                    │     (LLM-based refinement)             │
                    │            │                           │
                    │            ▼                           │
                    │  4. Deploy A/B Test (10%)              │
                    │     - New prompt variant               │
                    │     - New backend weights              │
                    │            │                           │
                    │            ▼                           │
                    │  5. Monitor & Compare (7 days)         │
                    │     - avg_rating                       │
                    │     - skip_accuracy                    │
                    │            │                           │
                    │            ▼                           │
                    │  6. Adopt or Rollback                  │
                    │     - +5% improvement → adopt          │
                    │     - else → rollback                  │
                    │                                        │
                    └────────────────────────────────────────┘
```

### 5.3 A/B Testing Framework

```python
# app/services/ab_testing.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

@dataclass
class Experiment:
    id: str
    name: str
    control: Dict[str, Any]
    variant: Dict[str, Any]
    traffic_ratio: float  # 0.0 ~ 1.0 (variant 비율)
    metric: str  # "avg_rating", "skip_accuracy"
    start_date: datetime
    end_date: datetime
    status: str  # "running", "completed", "rolled_back"

class ABTestingService:
    """A/B 테스트 서비스."""

    _experiments: Dict[str, Experiment] = {}

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
    ) -> str:
        """사용자를 control/variant에 할당 (deterministic)."""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != "running":
            return "control"

        # Deterministic assignment via hash
        hash_input = f"{experiment_id}:{user_id}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        ratio = (hash_val % 100) / 100.0

        return "variant" if ratio < exp.traffic_ratio else "control"

    async def get_variant_config(
        self,
        experiment_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """사용자에게 적용할 설정 반환."""
        variant = self.assign_variant(experiment_id, user_id)
        exp = self._experiments[experiment_id]
        return exp.variant if variant == "variant" else exp.control

    async def evaluate_experiment(
        self,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """실험 결과 평가."""
        # P6 피드백 데이터에서 control/variant 그룹 비교
        ...
```

### 5.4 YAML Manifest A/B Extension

```yaml
# dimension.aesthetic.yaml (P7 enhanced)
ab_testing:
  enabled: true
  experiments:
    - id: "exp_2026_01_backend_weights"
      control:
        qdrant_weight: 0.6
        notebooklm_weight: 0.3
      variant:
        qdrant_weight: 0.5
        notebooklm_weight: 0.4
      traffic_ratio: 0.1
      metric: "avg_rating"

    - id: "exp_2026_01_reranker_threshold"
      control:
        min_score: 0.3
      variant:
        min_score: 0.4
      traffic_ratio: 0.1
      metric: "skip_accuracy"
```

### 5.5 Implementation Tasks

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| P7.1.1 | MisclassificationAnalyzer | `app/services/misclassification_analyzer.py` | 3h |
| P7.1.2 | PromptTuner (LLM-based) | `app/services/prompt_tuner.py` | 4h |
| P7.2.1 | ABTestingService | `app/services/ab_testing.py` | 4h |
| P7.2.2 | Experiment DB 모델 | `app/models_experiments.py` | 2h |
| P7.3.1 | ThresholdTuner | `app/services/threshold_tuner.py` | 3h |
| P7.4.1 | Weekly Cron Job | `app/tasks/weekly_self_correction.py` | 3h |
| P7.4.2 | Rollback Logic | `app/services/experiment_manager.py` | 2h |
| P7.5.1 | Admin Dashboard API | `app/routers/admin_experiments.py` | 3h |
| P7.5.2 | 테스트 | `tests/test_ab_testing.py` | 3h |

**Total Effort**: ~27h (5-7일)

---

## 6. Phase 8: Continual Learning

### 6.1 Goals

1. **Synthetic Data Generation**: 고품질 QA 쌍에서 학습 데이터 생성
2. **Self-RAG Adapter**: 자체 검증 기반 생성 (Optional)
3. **Knowledge Graph Updates**: 동적 엔티티/관계 업데이트
4. **Domain Adaptation**: Vivid 도메인 특화 개선

### 6.2 Synthetic Data Pipeline

```
    ┌─────────────────────────────────────────────────────────────┐
    │               Monthly Synthetic Data Pipeline               │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  1. Extract High-Quality Pairs                              │
    │     - rating >= 4                                           │
    │     - confidence >= 0.8                                     │
    │     - no CRAG trigger                                       │
    │              │                                              │
    │              ▼                                              │
    │  2. Generate Variations (LLM Paraphrasing)                  │
    │     "봉준호 롱테이크" → ["봉 감독 긴 촬영", "장면 전환"]    │
    │              │                                              │
    │  3. Quality Filter (Self-Validation)                        │
    │     - 변형이 원본 의도 유지하는지 검증                      │
    │              │                                              │
    │              ▼                                              │
    │  4. Export Training Format                                  │
    │     → JSONL / Parquet                                       │
    │              │                                              │
    │              ▼                                              │
    │  5. Update Knowledge Graph                                  │
    │     - 새 엔티티 추출                                        │
    │     - 관계 업데이트                                         │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

### 6.3 Knowledge Graph Updater

```python
# app/rag/knowledge_graph_updater.py
from typing import List
from dataclasses import dataclass

@dataclass
class ExtractedEntity:
    name: str
    type: str  # "AUTEUR", "FILM", "TECHNIQUE", "CONCEPT"
    source_response_id: str
    confidence: float

@dataclass
class ExtractedRelation:
    source: str
    relation: str  # "USES_TECHNIQUE", "DIRECTED", "INFLUENCED_BY"
    target: str
    confidence: float

class KnowledgeGraphUpdater:
    """Knowledge Graph 동적 업데이트."""

    async def extract_entities_from_responses(
        self,
        responses: List[RAGResponse],
    ) -> List[ExtractedEntity]:
        """고품질 응답에서 엔티티 추출 (NER)."""
        # Gemini로 엔티티 추출
        prompt = """
        Extract named entities from the following text.
        Categories: AUTEUR (감독), FILM (영화), TECHNIQUE (기법), CONCEPT (개념)

        Text: {text}

        Output JSON format:
        [{"name": "...", "type": "...", "confidence": 0.9}]
        """
        ...

    async def extract_relations(
        self,
        entities: List[ExtractedEntity],
        context: str,
    ) -> List[ExtractedRelation]:
        """엔티티 간 관계 추출."""
        ...

    async def update_lightrag(
        self,
        entities: List[ExtractedEntity],
        relations: List[ExtractedRelation],
    ):
        """LightRAG 그래프 업데이트."""
        from app.rag.lightrag_adapter import get_lightrag_adapter

        adapter = get_lightrag_adapter()
        await adapter.add_entities(entities)
        await adapter.add_relations(relations)

    async def detect_entity_drift(
        self,
        entity_name: str,
        period_days: int = 30,
    ) -> bool:
        """엔티티 드리프트 감지 (관계 변화)."""
        # 지난 30일간 엔티티 관계 변화 추적
        ...
```

### 6.4 Implementation Tasks

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| P8.1.1 | SyntheticDataGenerator | `app/services/synthetic_data_generator.py` | 4h |
| P8.1.2 | Quality Filter | `app/services/synthetic_data_generator.py` | 2h |
| P8.1.3 | Export Formats | `app/services/data_exporter.py` | 2h |
| P8.2.1 | SelfRAGAdapter (Optional) | `app/rag/self_rag.py` | 6h |
| P8.3.1 | KnowledgeGraphUpdater | `app/rag/knowledge_graph_updater.py` | 4h |
| P8.3.2 | LightRAG 통합 | `app/rag/lightrag_adapter.py` | 3h |
| P8.4.1 | Monthly Pipeline Task | `app/tasks/monthly_learning.py` | 3h |
| P8.4.2 | 테스트 | `tests/test_continual_learning.py` | 3h |

**Total Effort**: ~27h (5-7일)

---

## 7. Timeline & Dependencies

### 7.1 Dependency Graph

```
P4 ✅ ──────────────────────────────────────────────────────────────────────┐
                                                                             │
P5.1 QueryClassifier ◄──────────────────────────────────────────────────────┤
         │                                                                   │
         ▼                                                                   │
P5.2 Strategy Selector                                                       │
         │                                                                   │
         ▼                                                                   │
P5.3 Skip Retrieval                                                          │
         │                                                                   │
         ├──────────────────────────────┬───────────────────────────────────┘
         │                              │
         ▼                              ▼
P6.1 Feedback Schema ◄─────────────── (병렬 가능)
         │
         ▼
P6.2 Collection API
         │
         ▼
P6.3 Analytics
         │
         │ ← 최소 2주 데이터 축적 필요
         ▼
P7.1 MisclassificationAnalyzer
         │
         ▼
P7.2 A/B Testing
         │
         ▼
P7.3 Threshold Tuning
         │
         │ ← 최소 1달 데이터 + A/B 결과 필요
         ▼
P8.1 Synthetic Data
         │
         ▼
P8.3 KG Updates
```

### 7.2 Timeline

| Phase | Start | End | Duration | Prerequisites |
|-------|-------|-----|----------|---------------|
| **P5** | Week 1 | Week 2 | 2주 | P4 완료 ✅ |
| **P6** | Week 2 | Week 3 | 1.5주 | P5 시작 후 병렬 가능 |
| **P7** | Week 5 | Week 7 | 2주 | P6 완료 + 2주 데이터 |
| **P8** | Week 9 | Week 11 | 2주 | P7 완료 + 1달 데이터 |

**Total Duration**: ~11주 (데이터 축적 기간 포함)

---

## 8. Success Criteria (KPIs)

### 8.1 P5 Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Skip Retrieval Rate | 0% | 20-30% | `skip_count / total_queries` |
| Avg Latency (simple) | ~200ms | ~50ms | Prometheus `rag_query_latency` |
| Cost per Query | $0.008 | $0.006 | `-25%` |
| Classification Accuracy | N/A | >85% | P6 피드백 기반 |

### 8.2 P6 Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Feedback Collection Rate | >5% | `feedback_count / response_count` |
| Explicit Feedback Rate | >1% | Rating/thumbs 제출률 |
| Implicit Tracking Coverage | >90% | Click/copy/reformulate 추적률 |

### 8.3 P7 Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| A/B Test Improvement | +10% | avg_rating variant vs control |
| Prompt Iteration Success | >50% | 채택된 개선안 비율 |
| Auto-Rollback Trigger | <20% | 자동 롤백 비율 |

### 8.4 P8 Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Synthetic Data Quality | >90% | 변형-원본 의미 유지율 |
| KG Entity Addition | +100/month | 새 엔티티 수 |
| Domain Drift Detection | <1% | 드리프트 감지된 엔티티 비율 |

---

## 9. Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Skip Retrieval 오판 | 환각 증가 | Medium | Conservative threshold + CRAG 폴백 |
| LLM Classifier 지연 | +200-500ms | High | SemanticRouter 우선, LLM 폴백 |
| Feedback 수집 저조 | P7/P8 불가 | Medium | Implicit feedback 강화, 인센티브 |
| A/B 테스트 UX 불일치 | 사용자 혼란 | Low | 10% 이하, 롤백 자동화 |
| KG 업데이트 오염 | 검색 품질 저하 | Low | Confidence threshold, 수동 검토 |

---

## 10. Files Summary

### P5 Files

| File | Description |
|------|-------------|
| `app/rag/query_classifier.py` | QueryType + SemanticRouter + LLM Classifier |
| `app/rag/semantic_router.py` | MiniLM 기반 Semantic Routing |
| `app/rag/strategy_selector.py` | QueryType → Strategy 매핑 |
| `app/rag/direct_llm.py` | Skip Retrieval 직접 LLM 경로 |
| `app/rag/manifests/_routes.yaml` | Route examples |
| `app/rag/manifests/_schema.yaml` | routing 필드 추가 |
| `tests/rag/test_query_classifier.py` | 단위 테스트 |
| `tests/rag/test_adaptive_rag.py` | 통합 테스트 |

### P6 Files

| File | Description |
|------|-------------|
| `app/models_feedback.py` | RAGResponse, RAGFeedback 모델 |
| `alembic/versions/xxx_add_feedback.py` | DB 마이그레이션 |
| `app/routers/rag_feedback.py` | Feedback API |
| `app/services/feedback_service.py` | Feedback CRUD |
| `app/services/feedback_analytics.py` | 메트릭 분석 |
| `tests/test_rag_feedback.py` | 테스트 |

### P7 Files

| File | Description |
|------|-------------|
| `app/models_experiments.py` | Experiment 모델 |
| `app/services/ab_testing.py` | A/B Testing 서비스 |
| `app/services/misclassification_analyzer.py` | 오분류 분석 |
| `app/services/prompt_tuner.py` | 프롬프트 자동 튜닝 |
| `app/services/threshold_tuner.py` | Threshold 튜닝 |
| `app/services/experiment_manager.py` | 실험 관리 |
| `app/tasks/weekly_self_correction.py` | Weekly Cron Job |
| `app/routers/admin_experiments.py` | Admin API |
| `tests/test_ab_testing.py` | 테스트 |

### P8 Files

| File | Description |
|------|-------------|
| `app/services/synthetic_data_generator.py` | 합성 데이터 생성 |
| `app/services/data_exporter.py` | 데이터 내보내기 |
| `app/rag/self_rag.py` | Self-RAG Adapter (Optional) |
| `app/rag/knowledge_graph_updater.py` | KG 업데이터 |
| `app/tasks/monthly_learning.py` | Monthly Pipeline |
| `tests/test_continual_learning.py` | 테스트 |

---

## 11. Appendix

### A. References

1. **Adaptive RAG (2025)**: https://www.meilisearch.com/blog/adaptive-rag
2. **Self-RAG Paper**: Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
3. **CRAG Paper**: Yan et al., "Corrective Retrieval Augmented Generation"
4. **LangGraph**: https://langchain-ai.github.io/langgraph/
5. **RAGAS Evaluation**: https://docs.ragas.io/
6. **Semantic Router**: https://github.com/aurelio-labs/semantic-router
7. **RAG Evolution 2026-2030**: https://nstarxinc.com/blog/the-next-frontier-of-rag/

### B. Glossary

| Term | Definition |
|------|------------|
| **Adaptive RAG** | 쿼리 복잡도에 따라 검색 전략을 동적으로 조정하는 RAG |
| **Self-RAG** | 자체 검증(reflection tokens)을 통해 생성 품질을 개선하는 RAG |
| **CRAG** | 검색 결과 품질이 낮을 때 자동으로 보정하는 RAG |
| **Skip Retrieval** | 단순 쿼리에서 검색을 생략하고 LLM 파라메트릭 지식 사용 |
| **Semantic Router** | 임베딩 유사도 기반 빠른 쿼리 라우팅 |
| **RRF** | Reciprocal Rank Fusion - 다중 검색 결과 통합 알고리즘 |

---

## 12. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Author | Claude Opus 4.5 | 2026-01-15 | ✅ |
| Reviewer | TBD | | |
| Approver | TBD | | |

---

*End of Document*
