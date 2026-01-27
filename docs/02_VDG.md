# VDG System v5.0: Unified Pipeline Architecture (Final)

**작성**: 2025-12-28
**Updated**: 2026-01-23 (v5.0.11)
**목표**: VDG v5.0 Unified Pipeline (Audio/Motion Pre-Pass + Pro 1-Pass + CV) + Director Pack + Audio Coaching 통합 문서

> [!IMPORTANT]
> **Pattern Engine SSoT**: [`26_PATTERN_CLUSTERING.md`](./26_PATTERN_CLUSTERING.md)
>
> VDG 분석 결과는 Pattern Engine의 입력 데이터입니다. 클러스터링/DNA 추출/패턴 이름 등은 위 문서 참조.

> ⚡ **v5.0.3 업데이트 (2026-01-10)**: Loop Point Detection, CV 메트릭 기반 실시간 코칭, 데이터 경로 수정 (`provenance.comment_evidence_top5`)
> ⚡ **v5.0.4 업데이트 (2026-01-12)**: irony_analysis 파이프라인 연결, 댓글 형식 호환성 강화, PropDetailLLM count 정규화
> ⚡ **v5.0.5 업데이트 (2026-01-12)**: `dopamine_radar` 5차원 바이럴 자극 지표 추가 (visual_spectacle, audio_stimulation, narrative_intrigue, emotional_resonance, comedy_shock), URL canonicalization 전 플랫폼 통합 (TikTok/YouTube/Instagram)
> ⚡ **v5.0.6 업데이트 (2026-01-21)**: Pattern Clustering 연계 강화, R-Score/DNA Extractor 연동 문서화, VDG 4축 패턴 이름 형식 명시
> ⚡ **v5.0.7 업데이트 (2026-01-21)**: **dopamine_radar 클러스터링 통합** - 5D 유사도 20% 가중치 적용, 카테고리 벤치마크 API, VDGCard 인사이트 배지
> ⚡ **v5.0.8 업데이트 (2026-01-21)**: **TikTok Self-Healing** - 쿠키 자동 재생성, comments_failed 자동 재시도, Railway 호환성 강화
> ⚡ **v5.0.9 업데이트 (2026-01-21)**: **Refresh Metadata API** - `POST /items/{id}/refresh-metadata` 수동 갱신 엔드포인트, Outliers/Lab UI 버튼
> ⚡ **v5.0.10 업데이트 (2026-01-23)**: **P0 Ops Fixes** - `trust_env=False` httpx 프록시 차단, Self-healing 30분 타임아웃 'analyzing' 복구, Railway 다운로드 안정화
> ⚡ **v5.0.11 업데이트 (2026-01-23)**: **VDG Schema Path 문서화** - v3/v4/v5 필드별 경로 매핑 테이블 추가, `implementation_layer` 구조 명시, `scenes[].time_start/time_end` 정확한 경로 문서화, `max_json_depth: 15` 수정
> ⚡ **v5.0.12 업데이트 (2026-01-27)**: **SSoT Base Class Migration** - Backend `vdg_base.py` + Frontend `vdg.ts` SSoT 확립, CANONICAL_FIELDS 22개 확장, 중복 타입 전면 제거, `Pick<Type, ...>` 파생 패턴 도입

**VDG Utilities / Backfill & Audit (2026-01-13)**
- `backend/scripts/audit_vdg_quality.py`: SSoT 기반 품질 감사 (Pass1/2/3 + 패턴 연동)
- `backend/scripts/report_comment_evidence_alignment.py`: VDG ↔ DB 정합성 리포트 (comment/viral_kicks)
- `backend/scripts/backfill_viral_kicks_and_comments.py`: ViralKick/CommentEvidence 백필
- `backend/scripts/backfill_hook_attributes.py`: Hook 3축 (format/trigger/device) 백필
- `backend/scripts/backfill_replicability_score.py`: R-Score 백필
- `backend/scripts/backfill_dopamine_radar.py`: dopamine_radar heuristic 백필
- `backend/scripts/cleanup_vdg_nodes.py`: 특정 노드 클린업 (재분석 전 정리)
- `backend/scripts/normalize_canonical_urls.py`: TikTok/YouTube/Instagram URL 정규화 백필
- `backend/scripts/refresh_materialized_views.py`: MV 최신화 (pattern_cluster_stats)
- `backend/exports/vdg_consulting/VDG_DIALECTICAL_ENGINE_SSOT.md`: 데이터 기반 고도화 로드맵 (SSoT)

> [!IMPORTANT]
> **버전 구분 (Version Clarification)**
> - **Pipeline Version**: `v5.0.x` - 아키텍처 버전 (Audio/Motion Pre-Pass + Pro LLM + CV)
> - **Schema Version**: `VDGv4` (4.0.2) - Pydantic 스키마 클래스명, DB 저장 포맷
>
> 문서에서 "v5.0"은 파이프라인 아키텍처를 의미합니다. 실제 데이터 스키마는 `VDGv4`이며, 하위 호환성을 위해 유지됩니다.

---

## 1) Overview: VDG v5.0 Unified Pipeline

```
영상 + 댓글
     ↓
┌─────────────────────────────────────┐
│  Audio Pass (P1): librosa             │  ← v5.0 NEW
│  - BPM, beat_timestamps, onsets        │
├─────────────────────────────────────┤
│  Motion Pass (P2): OpenCV Optical Flow │  ← v5.0 NEW
│  - dominant_movement, segments         │
├────────────────┴────────────────────┤
                 ↓  (ENGINEERING_CONTEXT)
┌─────────────────────────────────────┐
│  Pass 1: Pro LLM (의미/인과/Plan)       │  ← Gemini 3.0 Pro 1회
│  - 10fps hook + 1fps full             │
│  - JSON output (manual validation)    │
│  - Entity Hints → CV 전달             │
│  - 댓글 기반 Mise-en-Scène 신호         │
└────────────────┬────────────────────┘
                 ↓  (UnifiedPassLLMOutput)
┌─────────────────────────────────────┐
│  Pass 2: CV (결정론적 측정)              │  ← ffmpeg + OpenCV
│  - 3 MVP 메트릭 (100% 재현 가능)        │
│  - Plan 기반 프레임 추출                │
│  - Metric Registry 검증               │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  VDG Merger / Orchestrator            │
│  - Semantic-Visual 정합성 검증          │
│  - Contract Candidates 생성           │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Director Pack Compiler               │
│  - Contract-First + heuristic 보강   │
│  - Metric Validation                  │
│  → DirectorPack v1.0.2                │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Audio Coach (Gemini 2.5 Flash)       │
│  - Pack 기반 실시간 코칭                  │
│  - One-Command 정책                    │
└─────────────────────────────────────┘
```

---

## 2) 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **1차는 의미** | "무엇을, 왜" - 구조/의도/댓글 미장센 |
| **2차는 시각** | "어떻게, 어디에" - 프레임/객체/구도 |
| **Metric Registry** | 단위/좌표계 명확 → 검출기 교체 가능 |
| **Entity 검증** | 후보 + 폴백 → multi-person 안정화 |
| **Analysis Plan** | 예산/병합/클램프 → 비용 통제 |
| **분포 저장** | 평균 + 분산 → 미래 재사용 |
| **Evidence 통합** | URI/해시/타임코드 → 규칙 근거 추적 |
| **Contract-First** | VDG → Pack 연결고리 고정 (heuristic 보강/폴백 포함) |

---

## 3) Core Schemas

### 3.1 VDG Main Structure (schema field: vdg_version=4.0.2)
```python
class VDGv4(BaseModel):
    # Core identifiers
    vdg_version: str = "4.0.2"
    content_id: str
    duration_sec: float

    # Pass 1: Semantic
    semantic: SemanticPassResult

    # Bridge: Analysis Plan
    analysis_plan: AnalysisPlan

    # Pass 2: Visual
    visual: VisualPassResult

    # Quality check
    merger_quality: MergerQuality

    # Pack input
    contract_candidates: ContractCandidates

    # Evidence
    evidence_items: List[EvidenceItem]

    # Flywheel
    distill_runs: List[DistillRun]
```
> Note: 파이프라인은 v5.0 기준이지만, 현재 스키마의 `vdg_version` 기본값은 호환성 유지를 위해 4.0.2로 유지 중입니다.

### 3.2 Schema Normalization (SSoT) ⭐ UPDATED 2026-01-27

> **중요**: VDG 스키마(v3/v4/v5)에 직접 접근 금지. 반드시 정규화 유틸 사용.

```python
# ❌ 금지 - 버전별 구조 차이로 실패 가능
hook = vdg_data.get("hook_genome", {})  # v4에서 실패 (semantic 경로)

# ✅ 필수 - 정규화 유틸 사용
from app.services.vdg_schema_normalizer import normalize_vdg_schema
normalized = normalize_vdg_schema(vdg_data)
hook = normalized.get("hook_genome") or {}
```

**핵심 함수:**
| 함수 | 용도 |
|------|------|
| `normalize_vdg_schema(raw)` | v3/v4/v5 → flat canonical 구조 |
| `get_schema_version(raw)` | 버전 자동 감지 |
| `is_empty_schema(normalized)` | 빈 스키마 체크 |

**Data Contract:** `docs/contracts/vdg_canonical_v1.yaml`

### 3.2.0 SSoT Base Class Architecture ⭐ NEW 2026-01-27

> **Phase 2.5 SSoT Migration 완료**: Backend/Frontend 타입 이중화 제거, 단일 진실 공급원 확립

**SSoT 파일 구조:**

| Layer | SSoT File | 역할 |
|-------|-----------|------|
| **Backend** | `app/schemas/vdg_base.py` | Python 기본 클래스 (MicrobeatBase, HookGenomeBase, SceneBase 등) |
| **Frontend** | `src/lib/types/vdg.ts` | TypeScript SSoT (22+ types) |
| **Contract** | `docs/contracts/vdg_time_format.md` | 시간 포맷 계약 (ms vs sec) |

**CANONICAL_FIELDS (22개):**
```typescript
// frontend/src/utils/normalizeVDG.ts
export const CANONICAL_FIELDS = [
  "hook_genome", "scenes", "intent_layer", "implementation_layer",
  "provenance", "mise_en_scene_signals", "content_id", "duration_sec",
  "vdg_version", "platform", "title", "upload_date", "meta", "media",
  "asr_transcript", "ocr_content", "entity_hints", "commerce",
  "capsule_brief", "summary", "audience_reaction", "visual"
] as const;
```

**Backend 상속 구조:**
```python
# app/schemas/vdg_base.py
class MicrobeatBase(BaseModel): ...      # t_ms, role, cue, note
class HookGenomeBase(BaseModel): ...     # pattern, delivery, strength
class SceneBase(BaseModel): ...          # scene_number, role, summary
class IntentLayerBase(BaseModel): ...    # dopamine_radar, irony_analysis
class DopamineRadarBase(BaseModel): ...  # 5D radar (0-10)
class ViralKickBase(BaseModel): ...      # kick_index, mechanism
class ViralKickKeyframeBase(BaseModel): ... # uri, type, t_ms

# app/schemas/vdg.py - 상속
class Microbeat(MicrobeatBase): ...
class HookGenome(HookGenomeBase): ...
```

**Frontend 파생 패턴:**
```typescript
// ✅ 권장: Pick으로 SSoT에서 파생
import type { HookGenome } from "@/lib/types/vdg";

export type HookGenomeData = Pick<
  HookGenome,
  "pattern" | "delivery" | "strength" | "hook_summary" | "start_sec" | "end_sec"
>;

// ❌ 금지: 로컬 인터페이스 중복 정의
interface HookGenomeData {
  pattern?: string;  // vdg.ts와 동기화 필요 → 실패 위험
  // ...
}
```

**마이그레이션된 컴포넌트:**
| 파일 | 변경 내용 |
|------|----------|
| `HookPatternCard.tsx` | `HookGenomeData` → `Pick<HookGenome, ...>` |
| `StoryboardPanel.tsx` | `AudioEvent`, `CameraInfo`, `SceneData`, `RawVDG` 별칭 제거 |
| `VDGFilmingGuide.tsx` | `VDGSceneData`, `VDGCameraInfo` SSoT 직접 import |
| `DopamineRadarChart.tsx` | `DopamineRadar` SSoT 직접 import |
| `session.ts` | 중복 타입 제거, `vdg.ts` re-export |
| `videoStore.ts` | 중복 타입 제거 |

**검증 함수:**
```typescript
// frontend/src/utils/normalizeVDG.ts
export function validateVDGCompleteness(vdg: Record<string, unknown>): {
  present: string[];
  missing: string[];
  completeness: number;
}
```

### 3.2.1 VDG 필드별 경로 매핑 ⭐ UPDATED 2026-01-23

> ⚠️ **Critical**: 버전별 경로가 다릅니다. 반드시 `normalize_vdg_schema()` 사용!

| 필드 | v3.3 (Legacy) | v4.0.2+ (Current) | 정규화 후 |
|------|---------------|-------------------|-----------|
| `hook_genome` | `root.hook_genome` | `semantic.hook_genome` | `hook_genome` |
| `scenes` | `root.scenes` | `semantic.scenes` | `scenes` |
| `dopamine_radar` | `root.intent_layer.dopamine_radar` | `semantic.intent_layer.dopamine_radar` | `intent_layer.dopamine_radar` |
| `movement_vectors` | N/A | `root.implementation_layer.camera_physics.movement_vectors[]` | 동일 |
| `sync_points` | N/A | `root.implementation_layer.audio_engineering.sync_points[]` | 동일 |
| **timing** | `scenes[].shots[].start/end` | **`scenes[].time_start/time_end`** | 동일 |

> 🚨 **경고**: `scenes[].window.start_ms/end_ms`는 **존재하지 않습니다!**
> 실제 필드: `time_start`, `time_end`, `duration_sec` (모두 초 단위)

> [!CAUTION]
> **implementation_layer는 루트 레벨!** semantic 안에서 찾으면 실패합니다.
> ```python
> # ❌ 잘못됨 - semantic.implementation_layer 없음!
> impl = normalized.get("implementation_layer")  # None 반환
>
> # ✅ 올바름 - 원본 payload에서 직접 접근
> impl = payload.get("implementation_layer")
> ```

**루트 vs semantic 키 구조 (v4.0.2+):**

| 위치 | 키 목록 |
|------|---------|
| **루트에만** (23개) | `implementation_layer`, `camera_metadata`, `feature_vectors`, `scene_transitions`, `multi_shot_analysis`, `evidence_items`, `distill_runs`, `metric_definitions`, `contract_candidates`, `legacy_flat_view`, `feature_store_version`, `metric_registry_version`, `merger_quality`, `analysis_plan`, `meta`, `media`, `title`, `visual`, `platform`, `content_id`, `upload_date`, `vdg_version`, `duration_sec` |
| **semantic에만** (10개) | `scenes`, `summary`, `commerce`, `hook_genome`, `ocr_content`, `entity_hints`, `intent_layer`, `capsule_brief`, `asr_transcript`, `audience_reaction` |
| **둘 다** (2개, 루트 우선) | `provenance`, `mise_en_scene_signals` |

**implementation_layer 구조 (루트 레벨, v4/v5 only):**
```python
# payload["implementation_layer"] - 루트 레벨!
implementation_layer = {
    "camera_physics": {
        "movement_vectors": [
            {"technique": "static", "speed": "slow", "direction": "none",
             "t_start_ms": 83, "t_end_ms": 7917}
        ]
    },
    "audio_engineering": {
        "bpm": 120.0,
        "sync_points": [
            {"event": "static_start", "t_ms": 93, "beat_aligned": True}
        ]
    }
}
```

### 3.2.2 Retry 패턴 ⭐ NEW 2026-01-11


```python
# app/utils/retry.py 사용
from app.utils.retry import retry_gemini_call, retry_gemini_call_sync

# async 함수용
response = await retry_gemini_call(lambda: gemini_api_call())

# sync 함수용
response = retry_gemini_call_sync(lambda: gemini_api_call())
```

**재시도 조건:** 429, 5xx, timeout, connection 오류만 (4xx는 즉시 실패)

### 3.3 Metric Registry (SSoT)
```python
# app/schemas/metric_registry.py
class MetricDefinition(BaseModel):
    metric_id: str  # "cmp.center_offset_xy.v1"
    description: str
    unit: str  # "norm_0_1", "ratio", "bool"
    coordinate_frame: str
    aggregation_allowed: List[str]
```

### 3.3 Director Pack
```python
class DirectorPack(BaseModel):
    pack_version: str = "1.0.2"
    pattern_id: str
    goal: str

    # Rules
    dna_invariants: List[DNAInvariant]
    mutation_slots: List[MutationSlot]
    forbidden_mutations: List[ForbiddenMutation]

    # Coaching
    checkpoints: List[Checkpoint]
    policy: Policy
```

---

## 4) Hardenings (완료)

### P0 Foundation (10/10)
1. ✅ 2-Pass 구조 (Semantic → Visual)
2. ✅ Metric Registry SSoT
3. ✅ Plan-based frame extraction
4. ✅ AP ID deterministic (`ap.{domain}.{idx}.{hash}`)
5. ✅ Evidence ID structural (`ev.frame.{id}.{ap_id}.{t_ms}`)
6. ✅ Contract-first compiler
7. ✅ Pack fallback rules (silent director 방지)
8. ✅ Compiler metric validation
9. ✅ Compiler fallback warnings
10. ✅ VisualPass metric validation

### Flywheel Hardenings
- ✅ `DistillRun` schema (NotebookLM-ready)
- ✅ `SignalPerformance` tracking
- ✅ `InvariantCandidate` intermediate state
- ✅ A→B Migration (Signal → Invariant 자동 승격)

### Cluster SoR
- ✅ `ContentCluster` (parent-kids)
- ✅ `ClusterSignature` for similarity

### RL Data Schema
- ✅ `CoachingIntervention` (rule_id, ap_id, evidence_id)
- ✅ `CoachingOutcome` (compliance, metric_before/after)
- ✅ `SessionContext` (persona, environment, device)

### Normalized Evidence Tables (Added 2026-01-01)
- ✅ `viral_kicks` (23 columns): 바이럴 킥 정규화 테이블
- ✅ `keyframe_evidences` (14 columns): 프레임 증거 테이블
- ✅ `comment_evidences` (8 columns): 댓글 증거 테이블

### Coaching System Phase 1-5+ (Added 2026-01-03) ⭐ NEW
- ✅ 출력 모드 4종: graphic | text | audio | graphic_audio
- ✅ 페르소나 4종: drill_sergeant | bestie | chill_guide | hype_coach (aliases: strict_pd | close_friend | calm_mentor | energetic)
- ✅ LLM 기반 적응형 코칭 (`AdaptiveCoachingService`)
- ✅ VDG 데이터 활용 (shotlist, kicks, mise_en_scene)
- ✅ 고급 자동학습 (`AdvancedSessionAnalyzer`, `WeightedSignal`, `LiveAxisMetrics`)

### Visual Detail Extraction (Added 2026-01-05)
- ✅ `VisualDetailLLM` 스키마 (`background`, `foreground_props`, `text_overlays`, `subject_*`)
- ✅ `unified_prompt.py`: Task G) Scene segmentation에 `visual_detail` JSON 예시 추가
- ✅ `maxOutputTokens`: 8192 → **65535** (Gemini 2.5 Pro 최대값, JSON 트렁케이션 방지)
- ✅ `_extract_scenes()`: VDG v3/v4/v5 모든 경로 호환 (`analysis.scenes`, `semantic.scenes`)
- ✅ API `/outliers/items/{id}`: `response.analysis.scenes` 필드 추가

### Loop Point Detection (Added 2026-01-10) ⭐ NEW
- ✅ `unified_prompt.py`: 영상 구조 기반 루프 가능성 추론 지시 추가
- ✅ `unified_pass.py`: `"loop"` signal_type 추가
- ✅ `vdg_extractor.py`: `extract_loop_point()` 함수
- ✅ `director_compiler.py`: `_extract_loop_point_from_vdg()` 메서드
- ✅ API 노출: `/outliers/items/{id}` → `response.loop_point`
- ✅ WebSocket 노출: `vdg_coaching_data.loop_point`
- ✅ Frontend: `ShotlistTimeline.tsx` 청록색 루프 마커 표시
- ✅ **Data Path 수정**: `provenance.comment_evidence_top5` (primary) + `semantic.audience_reaction.best_comments` (fallback)

### CV 메트릭 기반 실시간 코칭 (Added 2026-01-10) ⭐ NEW
- ✅ `frame_analyzer.py`: 7개 Visual Rule 스펙 (`VISUAL_RULE_SPECS`)
  - `framing_center`, `framing_thirds`, `brightness_underexposed`, `brightness_overexposed`
  - `stability_shake`, `subject_size`, `headroom`
- ✅ `CoachingFeedback` 데이터클래스 + `to_dict()` 변환
- ✅ `coaching_ws.py`: `frame_analysis_result` WebSocket 메시지 타입
- ✅ Frontend: `FrameAnalysisResult` 인터페이스 + 실시간 위반 알림 UI

### VDG Quality Validation v3.7 (Added 2026-01-13) ⭐ NEW

> **Duration 기반 최소 요구사항**: 짧은 영상에는 엄격한 기준 대신 완화된 기준 적용

**파일**: `app/validators/vdg_quality_validator.py`

**Duration 기반 remix_suggestions 최소값:**

| 영상 길이 | remix_suggestions 최소 | 비고 |
|----------|----------------------|------|
| ≤15초 | 0개 OK | 초단편은 변주 제안 과잉 |
| 15-30초 | 1개 | 표준 숏폼 |
| >30초 | 2개 | 일반 기준 |

**Duration 기반 richness 요구사항:**

| 영상 길이 | microbeats | keyframes | focus_windows |
|----------|-----------|----------|---------------|
| ≤15초 | 2 | 2 | 2 |
| 15-30초 | 3 | 2 | 3 |
| 30-60초 | 3 | 3 | 4 |
| >60초 | 2 | 2 | 3 |

**CRITICAL → WARNING 변경:**
- v3.6 이전: remix_suggestions 미달 시 `CRITICAL` → `vdg_quality_valid = False`
- v3.7: `WARNING` 으로 변경 → valid 차단 안 함 (score 감점만)

**검증 흐름:**
```python
from app.validators.vdg_quality_validator import vdg_validator

result = vdg_validator.validate_vdg(vdg_data, duration_sec=15.0)
# QualityResult(is_valid=True, score=0.82, issues=[], suggestions=[])
```

### dopamine_radar (5D) (Added 2026-01-12) ⭐ NEW

> **5차원 바이럴 자극 지표** (0-10 scale): 콘텐츠의 바이럴 잠재력을 다각도로 측정

**스키마 위치:** `semantic.intent_layer.dopamine_radar`

| 차원 | 설명 | 측정 기준 |
|-----|------|----------|
| `visual_spectacle` | 시각적 스펙터클 | 장면 수, 카메라 움직임 강도 |
| `audio_stimulation` | 청각 자극 | BPM, 음악 에너지 |
| `narrative_intrigue` | 서사적 흥미 | microbeats 수, 스토리 복잡도 |
| `emotional_resonance` | 감정 공명 | irony gap 유무, 감정 변화폭 |
| `comedy_shock` | 코미디/충격 | expectation_subversion 존재 |

**데이터 예시:**
```json
{
  "dopamine_radar": {
    "visual_spectacle": 7,
    "audio_stimulation": 8,
    "narrative_intrigue": 6,
    "emotional_resonance": 9,
    "comedy_shock": 8
  }
}
```

**백필 스크립트:** `scripts/backfill_dopamine_radar.py` (heuristic 기반)

---

## 4.5) VDG → Pattern Engine 연계 ⭐ NEW 2026-01-21

> **SSoT**: Pattern Engine 상세는 [`26_PATTERN_CLUSTERING.md`](./26_PATTERN_CLUSTERING.md) 참조

### 4.5.1 VDG 4축 패턴 이름 형식

VDG 분석 결과에서 추출된 4개 축을 기반으로 패턴 이름을 생성합니다:

```
"[카테고리]•[훅타입] [딜리버리] ([오디오])"

예시:
- "뷰티•POV 빠른컷 (트렌딩음악)"
- "먹방•질문형 스토리텔링 (오리지널)"
- "일상•충격 반전 (ASMR)"
```

**4축 매핑:**

| 축 | VDG 소스 경로 | 예시 |
|----|---------------|------|
| 카테고리 | `semantic.content_category` | beauty, food, daily |
| 훅타입 | `semantic.hook_genome.type` | pov, question, shock |
| 딜리버리 | `semantic.hook_genome.delivery` | fast_cut, storytelling |
| 오디오 | `semantic.audio_patterns[0]` | trending, original, asmr |

**구현:** `app/services/pattern_naming_service.py`

### 4.5.2 DNA 추출 (VDG → PatternDNA)

VDG 분석 결과에서 패턴의 DNA(불변 규칙/변형 슬롯)를 추출합니다:

```python
# ✅ 정규화 유틸 사용 필수
from app.services.vdg_schema_normalizer import normalize_vdg_schema
from app.services.dna_extractor import DNAExtractor

# VDG → 정규화 → DNA 추출
normalized = normalize_vdg_schema(vdg_data)
dna = DNAExtractor.extract(vdg_data)  # 내부적으로 normalize_vdg_schema 사용

# DNA 구조
# {
#   "invariant_rules": ["3초 이내 훅", "시각적 반전 필수", ...],
#   "mutation_slots": ["배경음악 선택", "말투 변형", ...],
#   "quality_score": 0.85,
#   "quality_grade": "A"
# }
```

**구현:** `app/services/dna_extractor.py`

### 4.5.3 R-Score (Replicability Score)

패턴의 **재현 가능성**을 0.0~1.0 점수로 평가합니다:

```
R-Score = 0.25 × quality_score       (VDG 완성도)
        + 0.25 × mutation_factor     (변형 슬롯 수 / 5)
        + 0.20 × invariant_factor    (규칙 적을수록 쉬움)
        + 0.15 × member_factor       (검증된 성공 사례)
        + 0.15 × performance_factor  (평균 Outlier 성과)
```

**Tier 분류:**

| Tier | R-Score 범위 | 의미 |
|------|-------------|------|
| EASY | ≥ 0.70 | 초보자도 쉽게 재현 가능 |
| MODERATE | 0.40 ~ 0.69 | 약간의 기술 필요 |
| HARD | 0.20 ~ 0.39 | 상당한 숙련도 필요 |
| EXPERT | < 0.20 | 전문가만 재현 가능 |
| UNKNOWN | - | 데이터 부족 (member < 2) |

**구현:** `app/services/replicability_scorer.py`
**백필:** `scripts/backfill_replicability_score.py`

### 4.5.4 dopamine_radar 클러스터링 통합 ✅ (v5.0.7)

> ✅ **완료** (2026-01-21): 클러스터링 유사도에 5D dopamine_radar 20% 가중치 적용

**구현 내용:**

1. **클러스터링 유사도 계산** (`app/services/clustering.py`)
   ```python
   WEIGHTS = {
       "microbeat_sequence": 0.25,  # 30→25 (-5%)
       "hook": 0.20,                # 25→20 (-5%)
       "visual_pattern": 0.15,      # 20→15 (-5%)
       "audio_pattern": 0.10,       # 15→10 (-5%)
       "timing": 0.10,              # 유지
       "dopamine_radar": 0.20,      # NEW +20%
   }
   ```

2. **코사인 유사도 비교** (`_compare_dopamine_radar()`)
   - 5축 벡터 비교: visual_spectacle, audio_stimulation, narrative_intrigue, emotional_resonance, comedy_shock
   - 누락 시 graceful degradation (weight 제외)

3. **카테고리 벤치마크 API** (`GET /api/v1/patterns/dopamine-benchmark/{category}`)
   - 카테고리별 dopamine_radar 평균값 반환
   - 5분 TTL + 10분 stale-while-revalidate 캐싱

4. **UI 인사이트 배지** (`VDGCard.tsx`)
   - 카테고리 평균 대비 above/below 표시
   - 사용자에게 자극 프로필 인사이트 제공

**효과:**
- 같은 "훅타입"이라도 자극 강도가 다른 패턴 분리 가능
- "감정적으로 유사한" 콘텐츠 클러스터링 품질 향상

---

## 5) File Structure (Updated 2026-01-21)

```
backend/app/
├── schemas/
│   ├── vdg_v4.py             # VDG v4.0.2 schema (1125 lines)
│   ├── vdg_unified_pass.py   # Unified Pass output (540 lines) + pattern/delivery/hook_summary
│   ├── director_pack.py      # Director Pack (427 lines)
│   └── metric_registry.py    # Metric SSoT (274 lines)
│
├── services/
│   ├── gemini_pipeline.py    # [WRAPPER] → vdg_pipeline/ 패키지로 위임
│   ├── vdg_extractor.py      # VDG 헬퍼 함수 (extract_*, translate_*)
│   ├── vdg_schema_normalizer.py  # ⭐ VDG v3/v4/v5 정규화 (SSoT)
│   ├── dna_extractor.py      # ⭐ VDG → Pattern DNA 추출
│   ├── replicability_scorer.py   # ⭐ R-Score 계산 (Tier 분류)
│   ├── pattern_naming_service.py # ⭐ VDG 4축 패턴 이름 생성
│   ├── genai_client.py       # google-genai SDK client
│   ├── audio_coach.py        # Gemini 2.5 Flash Live
│   └── evidence_updater.py   # RL weight adjustment
│
├── services/vdg_pipeline/    # Phase 2 리팩토링 (2026-01-01)
│   ├── __init__.py           # 공개 API (GeminiPipeline, gemini_pipeline)
│   ├── constants.py          # VDG_PROMPT (7771 chars)
│   ├── prompt_builder.py     # 영상 길이별 프롬프트 빌더
│   ├── sanitizer.py          # 페이로드 정제, 레거시 필드
│   ├── converter.py          # UnifiedResult → VDGv4 변환
│   └── analyzer.py           # GeminiPipeline 클래스 (main entry)
│
├── services/vdg_2pass/
│   ├── unified_pass.py       # Pass 1: Pro LLM + "loop" signal_type
│   ├── cv_measurement_pass.py # Pass 2: CV
│   ├── vdg_unified_pipeline.py # 오케스트레이터
│   ├── audio_analyzer.py      # ⭐ P1: librosa BPM/Onset [v5.0]
│   ├── motion_analyzer.py     # ⭐ P2: OpenCV Optical Flow [v5.0]
│   ├── director_compiler.py   # Pack 컴파일러 + loop_point 추출
│   ├── quality_gate.py        # Proof Grade validation
│   ├── frame_extractor.py     # Plan-based frames
│   └── prompts/
│       ├── unified_prompt.py     # Pro 1-Pass 프롬프트 + ENGINEERING_CONTEXT
│       └── semantic_prompt.py    # pattern/delivery/hook_summary 지시
│
├── services/clustering/       # ⭐ Pattern Engine (26_PATTERN_CLUSTERING.md 참조)
│   └── clustering.py          # 6D 유사도 (microbeat, hook, visual, audio, timing, dopamine_radar)
│
└── validators/
    └── vdg_quality_validator.py  # VDG 품질 검증 (v3.7)
```

---

## 6) Data Flywheel (A→B Migration)

**핵심**: 코드 변경 없이 데이터만 쌓이면 자동 승격되는 메커니즘

### 6.1 Signal → Invariant 승격 임계값 (Configurable)

| 승격 단계 | 조건 | 설명 |
|-----------|------|------|
| **Slot → Candidate** | 10 sessions + 70% success | 초기 신호 포착. `InvariantCandidate` 생성 |
| **Candidate → DNA** | 50 sessions + 80% success | 강력한 패턴 증명. `DNAInvariant` 승격 (Distill 검증 필수) |

**용어 정의**
- **Sessions**: 해당 Slot/Signal이 제안된 코칭 세션 수
- **Success**: 사용자가 가이드를 따랐고(Outcome.compliance=True), 메트릭이 개선됨

### 6.2 Cluster SoR & Distill

**ContentCluster (Parent-Kids)**
- **Parent**: 원본 영상 (VDG Source)
- **Kids**: 해당 Parent를 보고 만든 변주들 (VDG Variants)
- **Cluster Signature**: 훅/오디오/인텐트 유사도로 묶임

**Distill Pipeline**
1. Cluster 내 Parent + Kids의 VDG 모음
2. NotebookLM에 투입
3. **공통 성공 요인** 추출 → `DistillRun` 결과로 저장
4. Candidate의 `distill_validated=True` 마킹 → DNA 승격

---

## 7) Evidence 계산

### 7.1 R_ES Score (Rule Execution Score)
```python
R_ES = (checked_rules / total_rules) × 100
```

### 7.2 Pattern Lift
```python
Lift = (Variant_metric - Parent_metric) / Parent_metric
```

---

## 8) Integration Points

### 8.1 Frontend Flow
```
[Card Detail] → [촬영 시작] → [Mode Select] → [CoachingSession]
```

### 8.2 API Endpoints
- `POST /api/v1/coaching/sessions` - 세션 생성
- `GET /api/v1/coaching/sessions` - 세션 목록 (Admin)
- `GET /api/v1/coaching/sessions/{session_id}` - 상태 조회
- `POST /api/v1/coaching/sessions/{session_id}/feedback` - 피드백 제출
- `POST /api/v1/coaching/sessions/{session_id}/events/rule-evaluated` - 규칙 평가 로깅
- `POST /api/v1/coaching/sessions/{session_id}/events/intervention` - 개입 로깅
- `POST /api/v1/coaching/sessions/{session_id}/events/outcome` - 결과 로깅
- `GET /api/v1/coaching/sessions/{session_id}/events` - 이벤트 조회
- `GET /api/v1/coaching/sessions/{session_id}/summary` - 세션 요약
- `POST /api/v1/coaching/sessions/{session_id}/end` - 세션 종료 (JSON body 지원)
- `DELETE /api/v1/coaching/sessions/{session_id}` - 세션 종료

> Legacy alias: `/coaching/*` (non-versioned)도 노출되어 있으나, 문서/연동은 `/api/v1/coaching/*` 사용을 권장합니다.

---

## 9) 현재 상태 (2026-01-27)

| 항목 | 상태 |
|------|------|
| VDG v5.0.2 visual_detail | ✅ 완료 |
| Gemini maxOutputTokens 65535 | ✅ 완료 |
| API scenes 반환 | ✅ 완료 |
| VDG Quality Validator (5개 컴포넌트) | ✅ 완료 |
| Curation Learning 시스템 | ✅ 완료 |
| **Loop Point Detection** | ✅ 완료 (v5.0.3) |
| **CV 메트릭 기반 실시간 코칭** | ✅ 완료 (v5.0.3) |
| **데이터 경로 수정** (provenance.comment_evidence_top5) | ✅ 완료 |
| **irony_analysis 파이프라인** | ✅ LLM → Converter → VDGv4 연결 완료 |
| **댓글 형식 호환성** | ✅ str/dict 혼합 입력 처리 |
| **PropDetailLLM count 정규화** | ✅ "many/several" → None 처리 |
| **DNA 이식 E2E (A/B/C)** | ✅ expectation_subversion 검증 완료 |
| **VDG 4축 패턴 이름** | ✅ 완료 (v5.0.6) - `"[카테고리]•[훅타입] [딜리버리] ([오디오])"` |
| **R-Score Tier 분류** | ✅ 완료 - EASY/MODERATE/HARD/EXPERT |
| **DNA Extractor 연동** | ✅ 완료 - `normalize_vdg_schema()` 기반 |
| **Pattern Clustering SSoT 문서화** | ✅ 완료 - `26_PATTERN_CLUSTERING.md` |
| **dopamine_radar 클러스터링 통합** | ✅ 완료 (v5.0.7) - 5D 유사도 20% 가중치, 벤치마크 API, UI 인사이트 |
| **SSoT Base Class Migration** | ✅ 완료 (v5.0.12) - Backend/Frontend 타입 통합, 22 CANONICAL_FIELDS |

### 향후 개발 (우선순위)

| 항목 | 예상 시기 | 비고 |
|------|----------|------|
| **R-Score Tier UI 필터링** | Q1 2026 | 사용자 레벨 기반 패턴 추천 |
| VDG Observability (Drift 감지) | Q1 2026 | 분석 품질 모니터링 |
| Kids Prediction (Neo4j GDS) | Q2 2026 | 바이럴 원본 예측 자동화 |
| Curation Reward Model (RLHF) | Q2 2026 | 큐레이션 품질 자동 개선 |

### Known Issues / TODO

| 항목 | 상태 | 설명 |
|------|------|------|
| **viral_kicks.confidence 하드코딩** | 🟡 숨김 | LLM 프롬프트(`unified_prompt.py`)에 confidence 필드 미요청 → `vdg_db_saver.py:476`에서 기본값 **0.7** 적용 → 모든 킥이 70%로 표시됨. 현재 UI에서 숨김 처리. 향후 프롬프트 수정 필요 시 `ViralKickTimeline.tsx` 주석 해제 |

---

## 10) VDG Pipeline Runbook (2026-01-21)

### 10.1 분석 상태 흐름 (OutlierItem.analysis_status)
```
pending → promoted → approved → analyzing → completed
                               ↳ comments_pending_review (S/A tier) → 자동 재시도 (Self-healing)
                               ↳ comments_failed (B/C tier) → 자동 재시도 (Self-healing)
```

### 10.2 실행 경로 (E2E)
1. **Outlier 등록**
   - `POST /api/v1/outliers/items/manual`
   - TikTok/YouTube/Instagram 메타데이터 + 썸네일 자동 추출
2. **승격 + 승인**
   - `POST /api/v1/outliers/items/{id}/promote`
   - `POST /api/v1/outliers/items/{id}/approve`
3. **VDG 분석**
   - `vdg_pipeline/analyzer.py` (댓글 정규화 + fallback 추출)
   - `vdg_2pass/unified_prompt.py` (LLM output)
   - `vdg_pipeline/converter.py` (LLM → VDGv4 매핑)
4. **DB 저장**
   - `remix_nodes.gemini_analysis` 저장
   - NotebookLibraryEntry 생성 (클러스터 경로 존재 시)

### 10.3 최근 핵심 패치
- **irony_analysis 연결**
  - `vdg_unified_pass.py` → `converter.py` → `vdg_v4.py`
- **댓글 형식 호환성**
  - `analyzer.py`에서 `List[str]` + `List[dict]` 모두 처리
- **Pydantic 안정화**
  - `PropDetailLLM.count` 정규화 (문자열 수량 → None)

### 10.4 검증 쿼리 (핵심 4개)
```sql
-- 1) Outlier 상태
SELECT id, video_url, analysis_status, promoted_to_node_id
FROM outlier_items
WHERE analysis_status IN ('analyzing','completed')
ORDER BY updated_at DESC;

-- 2) RemixNode VDG 존재 확인
SELECT rn.node_id,
       rn.gemini_analysis->'semantic'->'hook_genome' AS hook_genome,
       rn.gemini_analysis->'semantic'->'intent_layer'->'irony_analysis' AS irony
FROM remix_nodes rn
ORDER BY rn.created_at DESC
LIMIT 20;

-- 3) NotebookLibraryEntry 생성 확인
SELECT id, source_url, cluster_id
FROM notebook_library
ORDER BY created_at DESC
LIMIT 20;

-- 4) PatternCluster 연결 확인
SELECT nle.id, nle.cluster_id, pc.cluster_name
FROM notebook_library nle
LEFT JOIN pattern_clusters pc ON pc.cluster_id = nle.cluster_id
ORDER BY nle.created_at DESC
LIMIT 20;
```

### 10.5 실패 모드 & 대응
| 실패 유형 | 증상 | 대응 |
|-----------|------|------|
| TikTok 쿠키 만료 | comments_failed | **Self-Healing 자동 복구** (v5.0.8) |
| 댓글 추출 실패 | comments_failed | **Celery Beat 자동 재시도** (5/15/45분 backoff) |
| 댓글 형식 불일치 | Pydantic 에러 | `analyzer.py` 정규화 유지 |
| LLM 스키마 불일치 | VDG 저장 실패 | `vdg_unified_pass.py` + converter 매핑 확인 |
| count="many" | PropDetailLLM 검증 실패 | count 정규화 유지 |

### 10.6 TikTok Self-Healing 시스템 ⭐ NEW v5.0.8

> **2026-01-21 추가**: Railway 환경에서 TikTok 쿠키 자동 복구 및 댓글 추출 재시도 시스템

**문제 상황:**
- Railway 서버에 로컬 브라우저 없음 → `browser_cookie3` 실패
- `TIKTOK_COOKIE_BASE64` 환경변수의 쿠키가 파일로 bootstrap 되지 않거나 만료

**Self-Healing 흐름:**
```
TikTok 추출 시도 (메타데이터/댓글)
           ↓
    실패? (view_count=0 또는 comments=[])
           ↓ Yes
[Self-Healing] force_bootstrap_from_env() 호출
           ↓
   TIKTOK_COOKIE_BASE64 → /app/data/tiktok_cookies.json
           ↓
        재시도 1회
           ↓
    성공 → 정상 진행
    실패 → comments_failed 상태 → Celery Beat 자동 재시도
```

**구현 파일:**

| 파일 | 역할 |
|------|------|
| `cookie_admin.py` | `force_bootstrap_from_env()` - 쿠키 강제 재생성 |
| `tiktok_extractor.py` | 메타데이터 추출 + Self-healing |
| `comment_extractor.py` | 댓글 추출 + Self-healing |
| `vdg_reanalysis_queue.py` | `comments_failed` 자동 재시도 |

**Celery Beat 일정:**
- `run_reanalysis_queue_task`: 30분마다 실행
- `comments_failed`, `comments_pending_review` 상태 아이템 자동 재시도
- Exponential backoff: 5분 → 15분 → 45분 (최대 3회)

**수동 쿠키 갱신 (Admin):**
```bash
POST /api/v1/admin/cookies/force-bootstrap
```

### 10.7 Refresh Metadata API ⭐ NEW v5.0.9

> **2026-01-21 추가**: Self-Healing 배포 전 등록된 아이템의 메타데이터 수동 갱신

**문제 상황:**
- Self-Healing 배포 전 등록된 아이템 → view_count=0, 댓글=0 상태
- 사용자가 직접 수정할 방법 없음

**해결책 - 수동 Refresh API:**

| 엔드포인트 | 대상 |
|-----------|------|
| `POST /api/v1/outliers/items/{id}/refresh-metadata` | Outliers 아이템 |
| `POST /api/v1/lab/items/{id}/refresh-metadata` | Lab 아이템 |

**흐름:**
```
🔄 버튼 클릭 (모달)
       ↓
refresh-metadata API 호출
       ↓
extract_tiktok_complete() (Self-Healing 적용)
       ↓
DB 업데이트 (view_count, like_count, title, comments)
       ↓
캐시 무효화
       ↓
✅ UI 갱신
```

**UI 위치:**
- Outliers: `/ops/outliers` 상세 모달 → "원본 보기" 버튼 위
- Lab: `/my/lab` 상세 모달 (TikTok 아이템만)

**테스트 결과:**
```
Before: 0 views, 0 likes, 0 comments
After:  1,300,000 views, 175,800 likes, 10 comments ✅
```

---

## Appendix A: 실제 데이터 구조 (video_3 샘플)

```json
{
  "outlier_item": {
    "hook_type": "contrast",
    "vdg_quality_score": 0.64,
    "vdg_quality_valid": false,
    "vdg_quality_issues": [
      "CRITICAL: remix_suggestions 0개 < 최소 2개",
      "product_placement_guide 누락",
      "WARNING: keyframes 총 0개 < 권장 4개"
    ]
  },
  "vdg_analysis": {
    "semantic": {
      "hook_genome": {
        "pattern": "expectation_vs_reality",
        "delivery": "visual_gag",
        "strength": 0.85
      },
      "intent_layer": {
        "hook_trigger": "curiosity_gap",
        "dopamine_radar": {},
        "irony_analysis": {
          "setup": "욕쟁이 할머니 식당...",
          "twist": "손님이 '신고할게요'로 응수",
          "gap_type": "expectation_subversion"
        }
      },
      "audio_engineering": null
    },
    "implementation_layer": {
      "audio_engineering": {
        "bpm": 135.99,
        "beat_timestamps_ms": [116, 557]
      }
    }
  }
}
```

---

## 11) Reference

### 상위/관련 문서
- [**26_PATTERN_CLUSTERING.md**](./26_PATTERN_CLUSTERING.md) - **Pattern Engine SSoT** (VDG → 클러스터링 → DNA 추출)
- [09_NOTEBOOKLM_INTEGRATION.md](./09_NOTEBOOKLM_INTEGRATION.md) - NotebookLM 연동 세부

### 아키텍처/로드맵
- [00_ARCHITECTURE.md](./00_ARCHITECTURE.md) - 최종 아키텍처 (2026 완료)
- [03_ROADMAP.md](./03_ROADMAP.md) - 통합 로드맵
- [CHANGELOG.md](./CHANGELOG.md) - 개발 이력
