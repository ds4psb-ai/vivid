# 4-D DNA Unified Architecture - Handover Document

> **Date**: 2026-01-28
> **Author**: Claude Opus 4.5
> **Status**: 🔄 2026-H2 통합 아키텍처 구현 중
> **Commit**: `f8979491` (main)

---

## 1. Executive Summary

### 기존 완료 (Phase 1-4)

**완료된 작업**: 4-D DNA Unified Architecture의 기본 인프라 구축
- DimensionChainContext 확장 (evidence_refs, sessionStorage, MegaApp 인식)
- PersonaDNA Big Five (OCEAN) 확장
- MegaApp 통합 기반 마련

### 신규 진행 (Phase 1.x-2.x)

**2026-H2 통합 아키텍처**: 독립 앱 → Saga 패턴 파이프라인 + 학습 가능한 시스템

| 컴포넌트 | 현재 → 개선 후 | Phase |
|---------|---------------|:-----:|
| **실행 방식** | 독립 호출 → Saga 패턴 | 1.2 |
| **데이터 동기화** | 즉시 Qdrant → Transactional Outbox | 1.3 |
| **Mirror 모델** | MBTI → MBTI + Big Five | 1.5.1 |
| **QC 기준** | 고정 → IP Context-aware | 1.5.2 |
| **Logic Vector** | 고정 v1 → Versioning + Drift Detection | 1.5.3 |
| **Shot Grammar** | 포맷 변환 → Transpiler (엔진별 최적화) | 1.5.4 |
| **피드백** | 알림 → HITL Dashboard + Auto-Apply | 2.3 |

---

## 2. 구현된 컴포넌트

### 2.1 Frontend - DimensionChainContext 확장

**파일**: `frontend/src/contexts/DimensionChainContext.tsx`

```typescript
// NEW: 추가된 기능들
interface DimensionChainContextValue {
  // 기존 유지...

  // Evidence refs 누적
  accumulatedEvidenceRefs: string[];
  appendEvidenceRefs: (refs: string[]) => void;

  // SessionStorage 동기화
  syncToSession: (ipSlug: string) => void;
  loadFromSession: (ipSlug: string) => boolean;
  hasSessionData: (ipSlug: string) => boolean;

  // MegaApp 인식
  currentMegaApp: MegaAppId | null;
  getMegaAppForDimension: (dimensionKey: string) => MegaAppId | null;
}
```

**사용법**:
```typescript
const {
  setChainData,
  accumulatedEvidenceRefs,
  syncToSession,
  loadFromSession,
  currentMegaApp
} = useDimensionChain();

// 데이터 저장 시 evidence_refs 포함
setChainData("reference-decoder", { logicVector }, "분석 완료", ["db:vpe:uuid123"]);

// IP 기반 세션 동기화
syncToSession("my-ip-slug");  // 저장
loadFromSession("my-ip-slug"); // 복원
```

### 2.2 Frontend - useChainDataInjection Hook

**파일**: `frontend/src/hooks/useChainDataInjection.ts`

자동으로 상위 Dimension에서 데이터를 추출하여 주입하는 hook.

```typescript
function StoryArchitectPanel() {
  const {
    logicVector,        // VPE/Reference Decoder에서 추출
    aestheticGuidelines, // AD에서 추출
    personaDNA,         // Mirror에서 추출 (OCEAN 포함)
    evidenceRefs,       // 누적된 모든 evidence refs
    isReady,            // 상위 데이터 로드 완료 여부
    hasUpstreamData,    // 상위 데이터 존재 여부
  } = useChainDataInjection("story-architect");

  if (!isReady) return <LoadingSpinner />;

  // logicVector를 활용한 스토리 생성...
}
```

**INPUT_MAP** (어떤 Dimension이 어떤 Dimension에서 데이터를 받는지):
```typescript
const INPUT_MAP = {
  "story-architect": ["reference-decoder", "aesthetic-director"],
  "prompt-alchemy": ["story-architect", "reference-decoder"],
  "system-prompt": ["story-architect", "prompt-alchemy", "reference-decoder"],
  "video-maker": ["system-prompt", "prompt-alchemy", "story-architect"],
  // ... 등
};
```

### 2.3 Frontend - Dimension-MegaApp 매핑

**파일**: `frontend/src/lib/dimension-mega-app-map.ts`

```typescript
export const DIMENSION_TO_MEGA_APP = {
  // DNA Lab
  "reference-decoder": "dna-lab",
  "aesthetic-director": "dna-lab",
  "abyss-mirror": "dna-lab",
  "quality-director": "dna-lab",

  // Story Engine
  "story-architect": "story-engine",
  "prompt-alchemy": "story-engine",
  "system-prompt": "story-engine",

  // Production
  "video-maker": "production",
  "visual-realizer": "production",
  // ...
};

// 헬퍼 함수들
getMegaAppForDimension("story-architect") // => "story-engine"
getDimensionsForMegaApp("dna-lab") // => ["reference-decoder", "aesthetic-director", ...]
getNextMegaApp("dna-lab") // => "story-engine"
```

### 2.4 Frontend - PersonaGenome OCEAN 시각화

**파일**: `frontend/src/components/dimension/PersonaGenome.tsx`

Big Five (OCEAN) 데이터가 있으면 자동으로 바 차트로 시각화:

```typescript
// PersonaGenome에 전달되는 데이터 구조
{
  persona: { ... },
  ocean: {  // 또는 big_five
    openness: 0.8,
    conscientiousness: 0.6,
    extraversion: 0.5,
    agreeableness: 0.7,
    neuroticism: 0.3,
  }
}
```

### 2.5 Backend - PersonaDNA OCEAN 확장

**파일**: `backend/app/services/dna_lab_service.py`

```python
@dataclass
class PersonaDNA:
    persona_type: str = ""
    creative_tendencies: List[str] = field(default_factory=list)
    visual_preferences: List[str] = field(default_factory=list)
    narrative_style: str = ""
    emotional_range: List[str] = field(default_factory=list)

    # NEW: Big Five (OCEAN) - 0.0 to 1.0
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
```

**OCEAN 추론 로직** (Mirror 결과에 직접 OCEAN이 없을 때):
- `_infer_openness()`: creative_tendencies, visual_preferences에서 추론
- `_infer_conscientiousness()`: narrative_style에서 추론
- `_infer_extraversion()`: emotional_range에서 추론
- `_infer_neuroticism()`: emotional_range에서 추론

### 2.6 Backend - UserPreferenceProfile OCEAN 필드

**파일**: `backend/app/models_personalization.py`

```python
class UserPreferenceProfile(Base):
    # 기존 필드들...

    # NEW: Big Five (OCEAN)
    openness: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.5)
    conscientiousness: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.5)
    extraversion: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.5)
    agreeableness: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.5)
    neuroticism: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.5)
    last_ocean_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

**마이그레이션**: `backend/alembic/versions/034_add_ocean_to_user_profiles.py`

---

## 2.5 2026-H2 신규 컴포넌트 (Phase 1.x-2.x)

### 2.5.1 Unified Schema

**신규 파일**: `backend/app/schemas/dna_lab_unified.py`

```python
class AestheticGuidelines(BaseModel):
    """AD 출력"""
    visual_style: str
    color_palette: List[str]
    mood_keywords: List[str]
    auteur_reference: Optional[str] = None

class PersonaDNA(BaseModel):
    """Mirror 출력 (MBTI + Big Five)"""
    mbti: Optional[str] = None
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    archetype: Optional[str] = None

class QualityReport(BaseModel):
    """QC 출력"""
    passed: bool
    score: float
    criteria_results: Dict[str, float]
    issues: List[str] = []
    suggestions: List[str] = []

class DNALabResult(BaseModel):
    """통합 결과"""
    success: bool
    trace_id: str
    vpe: Optional[LogicVector] = None
    ad: Optional[AestheticGuidelines] = None
    mirror: Optional[PersonaDNA] = None
    qc: Optional[QualityReport] = None
    evidence_refs: List[str] = []
    credits_used: int = 0
```

### 2.5.2 Saga Orchestrator

**신규 파일**: `backend/app/services/dna_lab_orchestrator.py`

```python
class DNALabOrchestrator:
    """Saga 패턴으로 VPE → AD → Mirror → QC 순차 실행"""

    async def run_pipeline(
        self, video_uri: str, user_id: str, db: AsyncSession
    ) -> DNALabResult:
        trace_id = str(uuid.uuid4())
        completed = []

        try:
            vpe_result = await self._run_vpe(video_uri)
            completed.append("vpe")

            ad_result = await self._run_ad(vpe_result)
            completed.append("ad")

            mirror_result = await self._run_mirror()
            completed.append("mirror")

            qc_result = await self._run_qc(ad_result)
            completed.append("qc")

            await self._write_to_outbox(trace_id, result, db)

            return DNALabResult(success=True, trace_id=trace_id, ...)

        except Exception as e:
            await self._compensate(completed, trace_id, db)
            raise
```

### 2.5.3 Transactional Outbox

**신규 파일**: `backend/app/models_outbox.py`

```python
class Outbox(Base):
    __tablename__ = "outbox"
    id = Column(UUID, primary_key=True)
    event_type = Column(String(50), nullable=False)  # "dna_lab_result"
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
```

**신규 파일**: `backend/app/services/outbox_publisher.py`
- 폴링 방식으로 pending 이벤트 → Qdrant 동기화
- 최대 3회 재시도 후 failed 상태 전환

### 2.5.4 Logic Vector Versioning + Drift Detection

**신규 파일**: `backend/app/services/logic_vector_versioning.py`

```python
class LogicVectorVersioning:
    DRIFT_THRESHOLD = 0.15  # cosine distance > 15% = drift

    async def detect_drift(
        self, ip_id: str, new_videos: List[str], db: AsyncSession
    ) -> DriftDetectionResult:
        # 1. 새 영상 Logic Vector 추출
        # 2. 현재 active version 로드
        # 3. Cosine distance + KS-test
        # 4. drift 감지 시 HITL 검토 요청
```

**DB 테이블**: `logic_vector_versions`
- `ip_id`, `version_number`, `embedding`, `logic_vector`
- `is_active`, `valid_from`, `valid_until`
- `drift_score_from_prev`, `drift_reason`

### 2.5.5 Shot Grammar Transpiler

**신규 파일**: `backend/app/routers/production/providers/adapters/transpiler.py`

```python
class ShotGrammarTranspiler:
    """공통 Shot Grammar → 엔진별 최적 포맷 변환"""

    async def transpile(
        self, prompt_cards: PromptCards, target_engine: str,
        logic_vector: Optional[LogicVector] = None
    ) -> Dict[str, Any]:
        if target_engine == "veo":
            return self._to_veo_optimal(prompt_cards, logic_vector)
        elif target_engine == "kling":
            return self._to_kling_optimal(prompt_cards, logic_vector)
        elif target_engine == "sora":
            return self._to_sora_optimal(prompt_cards, logic_vector)
```

**엔진별 최적화**:
- **Veo 3.1**: `[Cinematography] + [Subject] + [Action] + [Context] + [Style]` + first/last frame
- **Kling 2.6**: Subject-first + motion_intensity + beat_markers
- **Sora 2**: Timeline/Storyboard cards + physics hints

### 2.5.6 HITL Dashboard + Auto-Apply

**신규 파일**: `backend/app/services/hitl_workflow.py`

```python
class HITLWorkflowService:
    async def create_review_item(
        self, review_type: str, payload: Dict, severity: str = "medium"
    ) -> HITLReviewItem:
        # 검토 항목 생성 + 알림 발송

    async def approve_and_apply(
        self, item_id: str, decision_by: str, modified_action: Optional[Dict]
    ) -> HITLReviewItem:
        # 승인 + 자동 적용 (vector_drift → upgrade, qc_failure → 기준 조정)
```

**DB 테이블**: `hitl_review_items`
- `review_type`: vector_drift, qc_failure, prompt_pattern
- `severity`: low, medium, high, critical
- `status`: pending, in_review, approved, rejected
- `suggested_action`, `decision`, `auto_applied`

**프론트엔드**: `frontend/src/app/admin/hitl/page.tsx`
- 3가지 유형 탭: Vector Drift | QC Failure | Prompt Pattern
- KPI Cards, Severity 기반 정렬, 승인/거부 버튼

---

## 3. 다음 작업 (TODO)

### 3.1 Priority 1: Panel에서 useChainDataInjection 활용

각 Panel에서 실제로 hook을 사용하도록 수정 필요:

| Panel | 파일 | 작업 |
|-------|------|------|
| StoryArchitectPanel | `components/dimension/StoryArchitectPanel.tsx` | logicVector 자동 주입 |
| PromptGeneratorPanel | `components/dimension/PromptGeneratorPanel.tsx` | story 데이터 자동 주입 |
| SystemPromptPanel | `components/dimension/SystemPromptPanel.tsx` | logicVector → System Prompt 변환 |
| VeoVideoPanel | `components/dimension/VeoVideoPanel.tsx` | System Prompt 자동 적용 |
| KlingPanel | `components/dimension/KlingPanel.tsx` | System Prompt 자동 적용 |

**예시 마이그레이션**:
```typescript
// Before (수동)
function StoryArchitectPanel() {
  const [logicVector, setLogicVector] = useState(null);
  // 사용자가 수동으로 입력...
}

// After (자동 주입)
function StoryArchitectPanel() {
  const { logicVector, isReady } = useChainDataInjection("story-architect");

  // logicVector가 있으면 자동으로 폼에 프리필
  useEffect(() => {
    if (logicVector) {
      // 폼 필드에 자동 적용
    }
  }, [logicVector]);
}
```

### 3.2 Priority 2: setChainData 호출 추가

각 Panel에서 결과 생성 후 `setChainData` 호출 필요:

```typescript
// VPEPanel에서 분석 완료 후
const handleAnalysisComplete = (result) => {
  setChainData(
    "reference-decoder",
    { logicVector: result.logic_vector, ...result },
    `${result.auteur_id} 스타일 분석 완료`,
    result.evidence_refs  // evidence_refs 포함!
  );
};
```

### 3.3 Priority 3: Mirror에서 OCEAN 직접 추출

현재 Mirror 캡슐이 OCEAN을 직접 반환하지 않음. 프롬프트 수정 필요:

**파일**: `backend/app/dimension_adapter.py` 또는 관련 캡슐 정의

```python
# Mirror 캡슐 출력에 OCEAN 추가
{
  "persona_type": "...",
  "creative_tendencies": [...],
  "big_five": {
    "openness": 0.8,
    "conscientiousness": 0.6,
    "extraversion": 0.5,
    "agreeableness": 0.7,
    "neuroticism": 0.3
  }
}
```

### 3.4 Priority 4: UserPreferenceProfile OCEAN 업데이트 서비스

Mirror 분석 결과를 UserPreferenceProfile에 저장하는 서비스 필요:

```python
# backend/app/services/preference_service.py (신규 또는 기존 확장)
async def update_user_ocean(
    db: AsyncSession,
    user_id: str,
    persona_dna: PersonaDNA,
):
    profile = await get_or_create_profile(db, user_id)
    profile.openness = persona_dna.openness
    profile.conscientiousness = persona_dna.conscientiousness
    profile.extraversion = persona_dna.extraversion
    profile.agreeableness = persona_dna.agreeableness
    profile.neuroticism = persona_dna.neuroticism
    profile.last_ocean_update = datetime.utcnow()
    await db.commit()
```

### 3.5 Priority 5: E2E 테스트

```typescript
// e2e/mega-app-flow.spec.ts
test("DNA Lab → Story Engine 데이터 흐름", async ({ page }) => {
  // 1. DNA Lab에서 VPE 분석
  await page.goto("/dna-lab?tab=vpe&ip=test-ip");
  await page.click('[data-testid="analyze-button"]');
  await expect(page.locator('[data-testid="logic-vector"]')).toBeVisible();

  // 2. Story Engine으로 이동
  await page.goto("/story-engine?tab=story&ip=test-ip");

  // 3. LogicVector 자동 로드 확인
  await expect(page.locator('[data-testid="injected-logic-vector"]')).toBeVisible();
});
```

---

## 4. 데이터 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                         DNA Lab                                  │
├─────────────────────────────────────────────────────────────────┤
│  VPEPanel ──────► setChainData("reference-decoder", {           │
│     │              logicVector, evidence_refs                    │
│     │            })                                              │
│     │                                                            │
│  ADPanel ───────► setChainData("aesthetic-director", {          │
│     │              aestheticGuidelines, evidence_refs            │
│     │            })                                              │
│     │                                                            │
│  MirrorPanel ───► setChainData("abyss-mirror", {                │
│                    personaDNA (with OCEAN), evidence_refs        │
│                  })                                              │
│                                                                  │
│  ──────────────► syncToSession("ip-slug") ◄─────────────────    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ sessionStorage
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Story Engine                               │
├─────────────────────────────────────────────────────────────────┤
│  loadFromSession("ip-slug") ◄────────────────────────────────   │
│                                                                  │
│  StoryArchitectPanel                                             │
│     │  const { logicVector, aestheticGuidelines } =              │
│     │    useChainDataInjection("story-architect")                │
│     │                                                            │
│     └──► setChainData("story-architect", { storyStructure })    │
│                                                                  │
│  SystemPromptPanel                                               │
│     │  const { logicVector, storyStructure } =                   │
│     │    useChainDataInjection("system-prompt")                  │
│     │                                                            │
│     └──► setChainData("system-prompt", { systemPrompt })        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Production                                 │
├─────────────────────────────────────────────────────────────────┤
│  VeoVideoPanel                                                   │
│     │  const { systemPrompt } =                                  │
│     │    useChainDataInjection("veo")                            │
│     │                                                            │
│     └──► API 호출 시 systemPrompt + accumulatedEvidenceRefs     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 파일 위치 요약

### Frontend

| 파일 | 역할 |
|------|------|
| `contexts/DimensionChainContext.tsx` | 체인 상태 관리 (확장됨) |
| `hooks/useChainDataInjection.ts` | 자동 데이터 주입 hook (신규) |
| `lib/dimension-mega-app-map.ts` | Dimension ↔ MegaApp 매핑 (신규) |
| `components/dimension/PersonaGenome.tsx` | OCEAN 시각화 (확장됨) |
| `components/mega-app/MegaAppShell.tsx` | 세션 자동 로드/동기화 (확장됨) |
| `app/dna-lab/page.tsx` | Aurora 활성화, tabParamName 통일 |
| `app/story-engine/page.tsx` | Aurora 활성화, tabParamName 통일 |
| `app/production/page.tsx` | tabParamName 통일 |

### Backend

| 파일 | 역할 |
|------|------|
| `services/dna_lab_service.py` | PersonaDNA OCEAN 확장 + 추론 로직 |
| `models_personalization.py` | UserPreferenceProfile OCEAN 필드 |
| `alembic/versions/034_add_ocean_to_user_profiles.py` | DB 마이그레이션 |

---

## 6. 테스트 명령어

```bash
# Backend 테스트
cd backend && source venv/bin/activate && pytest --tb=short -q

# Frontend 빌드
cd frontend && npm run build

# PersonaDNA OCEAN 테스트
cd backend && source venv/bin/activate
python -c "
from app.services.dna_lab_service import PersonaDNA
p = PersonaDNA(openness=0.8, conscientiousness=0.6)
print(p)
"

# DB 마이그레이션 상태 확인
cd backend && source venv/bin/activate && alembic current
```

---

## 7. 주의사항

1. **sessionStorage 용량 제한**: 5MB까지만 저장 가능. 대용량 데이터(이미지 등)는 요약만 저장하고 상세는 백엔드에서 가져오도록.

2. **evidence_refs 타입**: 반드시 `List[str]` 형태 유지. dict 배열 사용 금지.
   ```python
   # ✅ 올바름
   evidence_refs = ["db:vpe:uuid123", "db:rag:4D:doc456"]

   # ❌ 틀림
   evidence_refs = [{"source": "vpe", "id": "uuid123"}]
   ```

3. **URL 파라미터**: 모든 MegaApp에서 `?tab=` 사용 (production도 `?provider=`에서 변경됨)

4. **OCEAN 값 범위**: 항상 0.0 ~ 1.0. 프론트엔드에서 퍼센트로 표시 시 x100.

---

## 8. 관련 문서

- `docs/MEGA_APP_ARCHITECTURE_2026.md` - MegaApp 전체 아키텍처
- `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` - Dimension 앱 개발 가이드
- `docs/15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` - 아키텍처 철학

---

**Questions?** 이 문서에 없는 내용은 코드를 직접 확인하거나, 위 관련 문서 참조.
