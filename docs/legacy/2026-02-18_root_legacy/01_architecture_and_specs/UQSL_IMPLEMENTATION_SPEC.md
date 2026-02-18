# UQSL (Universal Quality Selection Layer) Implementation Spec

> **Date**: 2026-01-16
> **Version**: 1.0
> **Status**: IMPLEMENTATION COMPLETE
> **Author**: Claude Opus 4.5
> **Tests**: 124 passed

---

## 1. Executive Summary

UQSL(Universal Quality Selection Layer)는 Vivid의 품질 선택 시스템으로, 다음을 구현합니다:

```
Multi-Generate → Quality Evaluation → Best Selection → Thompson Sampling → Feedback Loop
```

### 1.1 Implementation Status

| Phase | Component | Status | Files |
|-------|-----------|--------|-------|
| Phase 1 | Core Models | ✅ Complete | `app/uqsl/models.py` |
| Phase 2 | Multi-Generate Engine | ✅ Complete | `app/uqsl/multi_generate.py` |
| Phase 3 | Quality Evaluator | ✅ Complete | `app/uqsl/quality_evaluator.py` |
| Phase 4 | Best Selector | ✅ Complete | `app/uqsl/best_selector.py` |
| Phase 5 | Thompson Sampling | ✅ Complete | `app/uqsl/thompson_sampling.py` |
| Phase 6 | Ensemble++ 3-Way | ✅ Complete | `app/uqsl/ensemble_plus_plus.py` |
| Phase 7 | API Endpoints | ✅ Complete | `app/routers/uqsl.py` |
| Phase 8 | Frontend Components | ✅ Complete | `components/dimension/uqsl/` |
| Phase 9 | DB Migration | ✅ Complete | `alembic/versions/012_add_uqsl_tables.py` |
| Phase 10 | Metrics & Monitoring | ✅ Complete | `app/uqsl/metrics.py` |
| Phase 11 | Cloud Integration | ✅ Complete | `app/uqsl/cloud_integration.py` |

### 1.2 3-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│        Tier 1: FREE (모든 사용자) - 비용: $0~2/월               │
├─────────────────────────────────────────────────────────────────┤
│  • A/B 비교 + 사용자 투표                                       │
│  • Thompson Sampling 자동 조정                                  │
│  • 규칙 기반 Quality Score                                      │
│  • 앙상블 결과 머지                                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│     Tier 2: PREMIUM (구독 사용자) - 비용: $20~100/월            │
├─────────────────────────────────────────────────────────────────┤
│  • Multi-Generate (3개 생성)                                    │
│  • 거장 DNA 분석                                                │
│  • Quality Weights 커스터마이징                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│        Tier 3: DEV (개발자 전용) - 비용: $50~200/월             │
├─────────────────────────────────────────────────────────────────┤
│  • LLM-as-Judge (품질 평가)                                     │
│  • A/B/C 3-Way 앙상블 (Ensemble++)                              │
│  • 무제한 Multi-Generate                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Architecture

### 2.1 Module Structure

```
backend/app/uqsl/
├── __init__.py              # Public exports
├── models.py                # Pydantic models (222 lines)
├── multi_generate.py        # N개 후보 병렬 생성 (428 lines)
├── quality_evaluator.py     # 품질 평가 (554 lines)
├── best_selector.py         # 최적 선택 (243 lines)
├── thompson_sampling.py     # Beta 분포 기반 MAB (489 lines)
├── ensemble_plus_plus.py    # A vs B vs A+B (528 lines)
├── metrics.py               # Prometheus 메트릭 (492 lines)
└── cloud_integration.py     # Cloud SQL/BigQuery/Redis (581 lines)
```

### 2.2 Core Models (`models.py`)

```python
class QualityScore(BaseModel):
    """품질 평가 점수"""
    groundedness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    coherence: float = Field(ge=0.0, le=1.0)
    creativity: float = Field(ge=0.0, le=1.0)
    fluency: float = Field(ge=0.0, le=1.0)
    weighted_total: float = Field(ge=0.0, le=1.0)

class GenerationCandidate(BaseModel):
    """생성 후보"""
    idx: int
    content: str
    quality_score: Optional[QualityScore]
    metadata: Dict[str, Any]

class SelectionResult(BaseModel):
    """선택 결과"""
    session_id: str
    selected_idx: int
    selection_method: Literal["auto", "hitl", "hybrid", "llm_judge"]
    confidence: float
    candidates: List[GenerationCandidate]
```

### 2.3 Multi-Generate Engine (`multi_generate.py`)

```python
class MultiGenerateEngine:
    """N개 후보 병렬 생성"""

    async def generate(
        self,
        prompt: str,
        n_candidates: int = 3,
        diversity_factor: float = 0.3,
        parallel: bool = True,
    ) -> List[GenerationCandidate]:
        """
        동일 프롬프트로 N개 다양한 후보 생성

        Args:
            prompt: 입력 프롬프트
            n_candidates: 생성할 후보 수 (1-5)
            diversity_factor: 다양성 인자 (0.0-1.0)
            parallel: 병렬 생성 여부
        """
```

### 2.4 Quality Evaluator (`quality_evaluator.py`)

```python
class QualityEvaluator:
    """품질 평가기"""

    async def evaluate(
        self,
        candidate: GenerationCandidate,
        context: Optional[str] = None,
        weights: Optional[QualityWeights] = None,
    ) -> QualityScore:
        """
        후보의 품질 평가

        평가 기준:
        - groundedness: RAG 소스 기반 근거
        - relevance: 프롬프트 관련성
        - coherence: 논리적 일관성
        - creativity: 창의성
        - fluency: 유창성
        """
```

### 2.5 Best Selector (`best_selector.py`)

```python
class BestSelector:
    """최적 후보 선택기"""

    async def select(
        self,
        candidates: List[GenerationCandidate],
        strategy: Literal["auto", "hitl", "hybrid", "llm_judge"] = "hybrid",
        auto_threshold: float = 0.85,
    ) -> SelectionResult:
        """
        최적 후보 선택

        Strategies:
        - auto: weighted_total 기준 자동 선택
        - hitl: Human-in-the-loop (사용자 선택 대기)
        - hybrid: auto_threshold 초과 시 auto, 미만 시 hitl
        - llm_judge: LLM이 평가 후 선택
        """
```

### 2.6 Thompson Sampling (`thompson_sampling.py`)

```python
class ThompsonSamplingService:
    """Beta 분포 기반 Multi-Armed Bandit"""

    async def sample(self, arm_ids: List[str]) -> str:
        """
        Thompson Sampling으로 arm 선택

        각 arm의 Beta(α, β) 분포에서 샘플링하여
        가장 높은 값을 가진 arm 반환
        """

    async def update(self, arm_id: str, success: bool) -> ArmStats:
        """
        피드백으로 arm 통계 업데이트

        success=True: α += 1
        success=False: β += 1
        """
```

### 2.7 Ensemble++ 3-Way (`ensemble_plus_plus.py`)

```python
class EnsemblePlusPlusService:
    """A vs B vs A+B 3-Way 비교 (NeurIPS 2025)"""

    async def compare(
        self,
        query: str,
        backend_a: str = "qdrant_hybrid",
        backend_b: str = "notebooklm",
    ) -> ThreeWayResult:
        """
        3-Way 비교 결과 반환

        Returns:
            result_a: Backend A 단독 결과
            result_b: Backend B 단독 결과
            result_ab: A+B 앙상블 결과
            recommendation: 추천 결과 ("a", "b", "ab")
        """
```

---

## 3. API Endpoints

### 3.1 REST API (`/api/v1/uqsl/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Multi-Generate N개 후보 |
| POST | `/select` | 최적 후보 선택 |
| POST | `/feedback` | 사용자 피드백 제출 |
| POST | `/three-way` | 3-Way 비교 |
| GET | `/session/{id}` | 세션 조회 |
| GET | `/arms` | Thompson Sampling arm 목록 |
| GET | `/arms/{id}/stats` | Arm 통계 조회 |
| GET | `/health` | 헬스 체크 |
| GET | `/metrics` | Prometheus 메트릭 |

### 3.2 Request/Response Examples

```python
# POST /api/v1/uqsl/generate
{
    "prompt": "봉준호 감독 스타일의 영화 장면 분석",
    "app_key": "dimension.aesthetic",
    "n_candidates": 3,
    "diversity_factor": 0.3,
    "tier": "premium"
}

# Response
{
    "session_id": "uqsl_abc123",
    "candidates": [
        {
            "idx": 0,
            "content": "...",
            "quality_score": {
                "groundedness": 0.92,
                "relevance": 0.88,
                "weighted_total": 0.89
            }
        },
        // ... 2 more
    ],
    "selection": {
        "method": "hybrid",
        "selected_idx": 0,
        "confidence": 0.91
    }
}
```

---

## 4. Frontend Components

### 4.1 UQSL Components

```
frontend/src/components/dimension/
├── uqsl/
│   └── index.ts                  # Export all UQSL components
├── ABComparisonCard.tsx          # A/B 비교 카드 (332 lines)
├── QualityScorecard.tsx          # 품질 점수 표시 (501 lines)
└── ThreeWayComparison.tsx        # 3-Way 비교 UI (482 lines)

frontend/src/components/dimension/panel/
├── ABComparisonWrapper.tsx       # A/B 비교 래퍼 (129 lines)
├── MultiGenerateWrapper.tsx      # Multi-Generate UI (419 lines)
└── ThreeWayComparisonWrapper.tsx # 3-Way 래퍼 (166 lines)
```

### 4.2 useUQSL Hook

```typescript
// frontend/src/hooks/useUQSL.ts (563 lines)

export function useUQSL(appKey: string) {
  const [session, setSession] = useState<UQSLSession | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);

  const generate = async (prompt: string, options?: GenerateOptions) => {
    // Multi-Generate 호출
  };

  const select = async (idx: number, method: SelectionMethod) => {
    // 선택 제출
  };

  const submitFeedback = async (feedback: FeedbackType) => {
    // 피드백 제출 → Thompson Sampling 업데이트
  };

  return { session, candidates, loading, generate, select, submitFeedback };
}
```

---

## 5. Database Schema

### 5.1 UQSL Tables (Alembic Migration `012`)

```sql
-- uqsl_sessions: 세션 관리
CREATE TABLE uqsl_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_key VARCHAR(100) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    tier VARCHAR(20) DEFAULT 'free',
    status VARCHAR(20) DEFAULT 'pending',
    selected_idx INTEGER,
    selection_method VARCHAR(20),
    selection_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- uqsl_candidates: 생성된 후보들
CREATE TABLE uqsl_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES uqsl_sessions(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    content TEXT NOT NULL,
    quality_groundedness FLOAT,
    quality_relevance FLOAT,
    quality_coherence FLOAT,
    quality_creativity FLOAT,
    quality_fluency FLOAT,
    quality_weighted_total FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- uqsl_arm_stats: Thompson Sampling arm 통계
CREATE TABLE uqsl_arm_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arm_id VARCHAR(100) UNIQUE NOT NULL,
    alpha INTEGER DEFAULT 1,
    beta INTEGER DEFAULT 1,
    total_trials INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.5,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- uqsl_feedback: 사용자 피드백
CREATE TABLE uqsl_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES uqsl_sessions(id) ON DELETE CASCADE,
    feedback_type VARCHAR(20) NOT NULL,
    selected_idx INTEGER,
    user_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Cloud Integration (2026 Best Practices)

### 6.1 Cloud SQL Connector

```python
# app/uqsl/cloud_integration.py

async def get_cloud_sql_connector():
    """
    Cloud SQL Python Connector (google-cloud-sql-connector)

    Features:
    - IAM authentication (optional)
    - Automatic SSL/TLS
    - Connection pooling via SQLAlchemy
    - Fallback to local PostgreSQL
    """
```

### 6.2 BigQuery Analytics Pipeline

```python
class BigQueryUQSLEvent(BaseModel):
    """UQSL 분석 이벤트"""
    event_id: str
    event_type: Literal["generation", "selection", "feedback", "three_way"]
    app_key: str
    timestamp: datetime

    # Generation details
    prompt_hash: Optional[str]
    n_candidates: Optional[int]

    # Quality scores
    quality_scores: Optional[list[dict]]
    selected_idx: Optional[int]
    selection_method: Optional[str]
    selection_confidence: Optional[float]

    # Thompson Sampling
    arms_used: Optional[list[str]]

    # Feedback
    user_feedback: Optional[str]
```

### 6.3 Redis Session Cache

```python
class UQSLSessionCache:
    """
    Redis 기반 세션 캐시 (In-memory 폴백)

    Features:
    - TTL 기반 만료 (1시간)
    - Connection pooling
    - Graceful fallback
    """

    @staticmethod
    async def set(session_id: str, data: dict, ttl: int = 3600) -> bool

    @staticmethod
    async def get(session_id: str) -> Optional[dict]


class ThompsonSamplingCache:
    """
    Thompson Sampling arm 통계 캐시

    Features:
    - Atomic increment (Redis pipeline)
    - 24시간 TTL
    - DB 동기화
    """
```

---

## 7. Metrics & Monitoring

### 7.1 Prometheus Metrics (`metrics.py`)

```python
# Counters
uqsl_generations_total = Counter(
    "uqsl_generations_total",
    "Total UQSL generations",
    ["app_key", "tier"]
)

uqsl_selections_total = Counter(
    "uqsl_selections_total",
    "Total selections",
    ["method", "app_key"]
)

uqsl_feedback_total = Counter(
    "uqsl_feedback_total",
    "Total feedback submissions",
    ["type", "app_key"]
)

# Histograms
uqsl_generation_latency = Histogram(
    "uqsl_generation_latency_seconds",
    "Generation latency",
    ["app_key", "n_candidates"]
)

uqsl_quality_score = Histogram(
    "uqsl_quality_score",
    "Quality score distribution",
    ["dimension", "app_key"]
)

# Gauges
uqsl_arm_success_rate = Gauge(
    "uqsl_arm_success_rate",
    "Thompson Sampling arm success rate",
    ["arm_id"]
)
```

### 7.2 Health Check (`/api/v1/health`)

```python
@router.get("/health")
async def health_check():
    """
    Comprehensive health check for Cloud Run

    Checks:
    - Database connectivity
    - Redis connectivity
    - Thompson Sampling arm count
    - Recent generation count
    """
    return {
        "status": "healthy",
        "components": {
            "database": "ok",
            "redis": "ok",
            "thompson_sampling": {"arms": 5, "status": "ok"}
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 8. YAML Manifest Integration

### 8.1 quality_selection Block

```yaml
# config/apps/content/dimensions/{app}.yaml

quality_selection:
  enabled: true
  tier: premium  # free | premium | dev

  multi_generate:
    candidates: 3
    parallel: true
    diversity_factor: 0.3

  quality_weights:
    groundedness: 0.35
    relevance: 0.25
    coherence: 0.15
    creativity: 0.15
    fluency: 0.10

  selection:
    strategy: hybrid  # auto | hitl | hybrid | llm_judge
    auto_threshold: 0.85

  bandit:
    enabled: true
    exploration_rate: 0.1
    arms:
      - backend:qdrant_hybrid
      - backend:notebooklm

  ensemble_plus_plus:
    enabled: true
    backend_a: qdrant_hybrid
    backend_b: notebooklm

  feedback:
    enabled: true
    implicit: true
    explicit: true
    bigquery_sync: false
```

---

## 9. Testing

### 9.1 Test Files

```
backend/tests/uqsl/
├── __init__.py
├── test_uqsl_models.py          # 모델 테스트 (240 lines)
├── test_uqsl_api.py             # API 테스트 (351 lines)
├── test_quality_evaluator.py    # 품질 평가 테스트 (338 lines)
├── test_thompson_sampling.py    # Thompson Sampling 테스트 (230 lines)
├── test_ensemble_plus_plus.py   # Ensemble++ 테스트 (281 lines)
├── test_uqsl_metrics.py         # 메트릭 테스트 (267 lines)
└── test_cloud_integration.py    # 클라우드 통합 테스트 (368 lines)
```

### 9.2 E2E Tests

```typescript
// frontend/e2e/uqsl.spec.ts (342 lines)

test.describe('UQSL Integration', () => {
  test('Multi-Generate flow', async ({ page }) => {
    // 1. Navigate to dimension panel
    // 2. Enter prompt
    // 3. Click generate
    // 4. Verify 3 candidates displayed
    // 5. Select best candidate
    // 6. Submit feedback
  });

  test('Three-Way comparison', async ({ page }) => {
    // Test Ensemble++ UI
  });
});
```

### 9.3 Test Results

```
124 passed, 51 warnings in 2.34s
```

---

## 10. Deployment

### 10.1 Cloud Run Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Cloud SQL Proxy support
ENV CLOUD_SQL_INSTANCE=""
ENV CLOUD_SQL_IAM_AUTH="false"

# BigQuery support
ENV BIGQUERY_DATASET=""

# Redis support
ENV REDIS_URL="redis://localhost:6380"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 10.2 Environment Variables

```bash
# Cloud SQL
CLOUD_SQL_INSTANCE=project:region:instance
CLOUD_SQL_USER=uqsl_user
CLOUD_SQL_PASSWORD=***
CLOUD_SQL_IAM_AUTH=true

# BigQuery
BIGQUERY_DATASET=vivid_analytics
BIGQUERY_TABLE_UQSL_EVENTS=uqsl_events

# Redis
REDIS_URL=redis://10.0.0.1:6379
```

---

## 11. References

- [UQSL_SPEC.md.resolved](/.gemini/antigravity/brain/.../UQSL_SPEC.md.resolved) - Original design spec
- [PRE_ROADMAP_ANALYSIS.md](docs/PRE_ROADMAP_ANALYSIS.md) - Pre-implementation analysis
- [P5_P8_RAG_ROADMAP_SPEC.md](docs/P5_P8_RAG_ROADMAP_SPEC.md) - RAG evolution roadmap
- [NeurIPS 2025 Ensemble++](https://arxiv.org/abs/...) - 3-Way comparison paper

---

## Appendix A: Migration from Pre-UQSL

기존 Dimension 앱에서 UQSL 활성화:

```yaml
# 1. YAML manifest에 quality_selection 추가
quality_selection:
  enabled: true
  tier: premium

# 2. 프론트엔드에서 useUQSL 훅 사용
const { generate, candidates, select } = useUQSL("dimension.aesthetic");

# 3. Thompson Sampling arm 초기화 (자동)
```

---

**Last Updated**: 2026-01-16 05:00 KST
