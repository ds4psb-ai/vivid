# 🚀 대대적 보충 로드맵: Story-First + DNA 아키텍처

**작성일**: 2025-12-30  
**목적**: 외부 컨설턴트 분석을 바탕으로 DirectorPack 시스템을 Story/Narrative/Viral 레이어로 확장

---

## 📋 핵심 전략 전환

```
[현재]                          [목표]
DNA(How) → Shot Contract     →  Story(What) → DNA(How) → Viral(Impact)
     ↓                                ↓            ↓            ↓
   품질 검증                      서사 검증    스타일 검증   바이럴 예측
```

> [!IMPORTANT]
> **컨설턴트 핵심 결론**: "DNA가 틀렸다"가 아니라, "DNA만으로는 바이럴을 결정하지 못한다"
> 기존 DirectorPack/Validator는 **그대로 엔진**으로 활용하고, 위에 레이어를 얹는다.

---

## 🎯 Hook 컨텍스트 인식 (중요 보정)

### 컨설턴트 피드백 반영: "모든 씬에 Hook이 필요한 것은 아니다"

```python
# Hook 적용 컨텍스트
HOOK_CRITICAL_CONTEXTS = [
    "sequence_start",      # 시퀀스 시작
    "shortform_start",     # 숏폼 시작 (1.5초 승부)
    "episode_cold_open",   # 에피소드 콜드 오픈
    "act_transition",      # 막 전환점
]

HOOK_OPTIONAL_CONTEXTS = [
    "mid_sequence",        # 시퀀스 중간
    "dialogue_scene",      # 대화 씬
    "transition_shot",     # 전환 샷
    "montage_middle",      # 몽타주 중간
]
```

### 구현 방향

1. `NarrativeRole` 필드에 `hook_required: bool` 추가
2. Hook 규칙을 **조건부 적용**으로 변경
3. 시퀀스 시작/숏폼 첫 샷에만 `hook_timing_1_5s` CRITICAL 적용

---

## 🏗️ 목표 아키텍처 (Capsule Node 그래프)

```
┌─────────────────────────────────────────────────────────┐
│                    Template Catalog                      │
│  (캡슐 노드들의 조합 = 재사용 가능한 제작 파이프라인)       │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  StoryArc     │  │ DirectorPack  │  │ Viral Analyzer│
│  Capsule      │  │ Capsule       │  │ Capsule       │
│  (NEW)        │  │ (기존 강화)    │  │ (NEW)         │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ story_pitch   │  │ pack_id       │  │ shots[]       │
│ target_emotion│  │ narrative_arc │  │ pack          │
│ platform      │  │ style_intensity│ │ arc           │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ NarrativeArc  │  │ ShotContracts │  │ DNACompliance │
│ HookVariants[]│  │ (with DNA)    │  │ ArcCompliance │
│ DissonanceMap │  │               │  │ ViralPredict  │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## 📦 Phase 1: Hook 1.5초 규칙 (즉시 반영)

### 1.1 기존 규칙 수정 + 조건부 적용

```python
DNAInvariant(
    rule_id="hook_timing_1_5s",
    rule_type="timing",
    name="황금 1.5초 훅",
    description="시퀀스/숏폼 시작 시 1.5초 이내 시선 잡기",
    condition="hook_punch_time",
    spec=RuleSpec(
        operator="<=", 
        value=1.5, 
        unit="sec",
        context_filter=["sequence_start", "shortform_start"],
    ),
    priority="critical",
    coach_line_ko="1.5초! 시작부터 치고 나가세요!",
),
```

### 1.2 10초 기대감 충족 규칙 추가

```python
DNAInvariant(
    rule_id="expectation_fulfillment_10s",
    rule_type="engagement",
    name="10초 기대감 충족",
    condition="expectation_gap_closed",
    spec=RuleSpec(operator=">=", value=0.7),
    priority="high",
    coach_line_ko="10초까지 뭔가 보여줘야 해요!",
),
```

---

## 📖 Phase 2: 서사 구조 레이어 (1주)

### 2.1 새 스키마: NarrativeArc

```python
# backend/app/schemas/narrative.py [NEW]

class NarrativePhase(str, Enum):
    HOOK = "hook"
    SETUP = "setup"
    BUILD = "build"
    TURN = "turn"
    PAYOFF = "payoff"

class ShotNarrativeRole(BaseModel):
    shot_id: str
    phase: NarrativePhase
    hook_required: bool = False
    expectation_created: Optional[str] = None
    dissonance_element: Optional[str] = None

class NarrativeArc(BaseModel):
    arc_id: str
    arc_type: Literal["3-act", "5-act", "hook-payoff"]
    phases: List[ShotNarrativeRole]
    emotion_start: str
    emotion_peak: str
    emotion_end: str
    dissonance_type: Optional[str] = None
```

---

## 📊 Phase 3: 바이럴 메트릭 (2주)

```python
# backend/app/schemas/viral_metrics.py [NEW]

class HookRetentionScore(BaseModel):
    t_1_5s: float
    t_10s: float
    drop_off_reason: Optional[str] = None

class DissonanceScore(BaseModel):
    familiar_element: str
    unexpected_element: str
    tension_level: float

class ViralAnalysisReport(BaseModel):
    hook_retention: HookRetentionScore
    dissonance: DissonanceScore
    viral_potential: Literal["low", "moderate", "high", "viral"]
```

---

## 📋 MVP 구현 순서 (7단계)

| # | 항목 | 기간 |
|---|------|------|
| 1 | Hook 1.5초 + context_filter | 1일 |
| 2 | /validate에 Hook 요약 추가 | 1일 |
| 3 | NarrativeArc 스키마 | 3일 |
| 4 | 10초 기대감 규칙 | 1일 |
| 5 | DissonanceScore MVP | 4일 |
| 6 | HookVariants 슬롯 | 5일 |
| 7 | 실측 메트릭 파이프라인 | 7일 |

---

## 🗂️ 파일 구조 변경

```
backend/app/
├── schemas/
│   ├── narrative.py            # [NEW]
│   ├── viral_metrics.py        # [NEW]
│   └── metrics_collection.py   # [NEW]
├── services/
│   ├── arc_validator.py        # [NEW]
│   ├── viral_analyzer.py       # [NEW]
│   └── story_analyzer.py       # [NEW]
```

---

## 🎯 성공 지표

| 지표 | 현재 | 목표 (3개월) |
|------|------|-------------|
| DNA 규칙 수 | 15 | 25+ |
| 서사 검증 커버리지 | 0% | 80% |
| Hook 1.5초 준수율 | N/A | 90%+ |
| 바이럴 예측 정확도 | N/A | 65%+ |
