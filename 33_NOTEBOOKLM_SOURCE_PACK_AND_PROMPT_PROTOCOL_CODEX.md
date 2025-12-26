# NotebookLM Source Pack & Prompt Protocol (CODEX v33)

**작성**: 2025-12-26  
**대상**: Product / Design / Engineering  
**목표**: 통데이터셋화(Logic/Persona) + 캡슐 노드 + RL을 **하나의 프로토콜**로 고정한다.

---

## 0) Canonical Anchors

- 철학/원칙: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- 캡슐 계약: `05_CAPSULE_NODE_SPEC.md`
- 영상 구조화: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- NotebookLM 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`
- 승격 기준: `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- Claim/Evidence/Trace: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`

---

## 1) Protocol Invariants (Non-negotiable)

1. **DB SoR only**: NotebookLM 산출물은 Sheets Bus를 거쳐 **DB 승격**된 것만 정본으로 사용한다.  
2. **Video → DB → NotebookLM**: 원본 영상은 NotebookLM에 직접 넣지 않는다.  
3. **Sealed Capsule**: 노드 내부 체인은 서버에만 존재하며 UI는 I/O + 노출 파라미터만 공개한다.  
4. **Evidence first**: 모든 주장(claim)은 EvidenceRef를 가진다.  
5. **cluster_id + temporal_phase** 단위 운영이 기본이다.

---

## 2) Core Concepts (Logic / Persona / Fusion)

### 2.1 Logic Vector (수학적 로직)
- 컷 리듬/길이 분포, 컷 밀도, 전환 타입 비율
- 구도/대칭/프레이밍 분포
- 카메라 모션 타입/빈도
- 모티프 재등장 패턴(타이밍/빈도)

### 2.2 Persona Vector (거장 페르소나)
- 해석 톤(냉소/서정/건조/유머 등)
- 감정 곡선(Valence/Arousal)
- 문장 리듬/호흡(짧은 문장/긴 여백)
- 해석 프레임(사회/심리/미학/장르 중심)

### 2.3 Fusion Rule (Logic × Persona)
- **Logic 우선, Persona 필터**가 기본.
- 로직 유사도 높으나 페르소나가 다르면 **분리 클러스터** 생성.
- 결합 결과는 Capsule Policy로 동결한다.

---

## 3) Tong Datasetization Protocol (A/B/C/D)

통 데이터셋은 **A/B/C/D**를 분리 저장하고 **Synapse Rule**로 결합한다.

- **A (Origin Visual)**: 영상 구조화 결과(샷/구도/리듬/모티프)
- **B (Origin Persona)**: 거장/명작의 해석 톤/감정 곡선
- **D (Filter Persona)**: 변주/오마주를 위한 필터 페르소나
- **C (Result Visual)**: 캡슐 실행 결과(생성/프리뷰 산출물)

**Synapse Rule**
- A + B → D → C 변환 규칙이 캡슐 스펙의 핵심이다.
- B/D는 NotebookLM 가이드 레이어에서 요약/라벨링한다.
- Synapse Rule은 **DB SoR**에 구조화해 재현성을 확보한다.

---

## 4) Logic Extraction Protocol

### 4.1 입력
- `video_segments[]` (shot_id, time range, visual/audio schema)
- `metrics_snapshot` (컷 길이 통계, 모션 비율, 색/광량 분포)
- `motif_stats` (모티프 빈도, 재등장 간격)

### 4.2 출력 (Logic Vector)
```json
{
  "logic_id": "logic_CL_A12_hook_v1",
  "temporal_phase": "HOOK",
  "cadence": {
    "shot_length_ms": { "median": 280, "p25": 140, "p75": 420 },
    "cut_density": 3.4,
    "transition_types": { "cut": 0.92, "dissolve": 0.06, "match": 0.02 }
  },
  "composition": {
    "symmetry_score": 0.74,
    "framing_ratio": { "WS": 0.2, "MS": 0.5, "CU": 0.3 }
  },
  "camera_motion": { "handheld": 0.15, "dolly": 0.4, "static": 0.45 },
  "motif_rules": { "recurrence_interval": "every_6_shots" }
}
```

---

## 5) Persona Extraction Protocol

### 5.1 입력
- NotebookLM 소스(구조화 segment + 감정/톤 태그)
- 오마주/변주 가이드 후보

### 5.2 출력 (Persona Vector)
```json
{
  "persona_id": "persona_CL_A12_v1",
  "tone": ["dry", "observational"],
  "emotion_arc": [
    { "t": 0.0, "valence": 0.1, "arousal": 0.2 },
    { "t": 1.0, "valence": -0.1, "arousal": 0.7 }
  ],
  "sentence_rhythm": { "avg_len": 9.2, "pause_bias": 0.7 },
  "interpretation_frame": ["psychology", "society"]
}
```

---

## 6) Fusion + Clustering Protocol

### 6.1 Distance Function

```
D = 0.55*D_logic + 0.35*D_persona + 0.10*D_context
```

### 6.2 Thresholds (MVP)

- join: `D <= 0.22`
- split: `D >= 0.35`
- logic similar but persona diverged → new cluster_id

### 6.3 Temporal Phase Buckets

숏폼 기본:
- HOOK (0~3s), BUILD (3~12s), PAYOFF (12~24s), CTA (24~30s)

롱폼 기본:
- SETUP, TURN, ESCALATION, CLIMAX, RESOLUTION

---

## 7) New Genre Migration Protocol

1. **신규 장르 입력** → Logic/Persona 벡터 생성
2. 기존 cluster와 거리 계산
3. 아래 중 하나:
   - **흡수**: 거리 임계치 통과 + 동일 phase → 기존 cluster 확장
   - **분기**: logic 유사 but persona 차이 → sibling cluster 생성
   - **신규**: 로직/페르소나 모두 상이 → 신규 cluster_id 생성
4. 신규 장르에 필요한 파라미터는 **exposed_params 추가**로 반영  
   - 의미 변화 시 **capsule version bump** 필수

---

## 8) NotebookLM Source Pack Protocol

### 8.1 Pack Unit
- `{cluster_id, temporal_phase}` 단위로 1 pack
- 동일 pack은 `bundle_hash`로 재현성 고정

### 8.2 Pack Fields (Required)
- `bundle_id`, `cluster_id`, `temporal_phase`
- `segment_refs[]` (shot_id/time range)
- `metrics_snapshot` (cadence/compose/motion summary)
- `motif_refs[]` (object/action/visual motif)
- `evidence_refs[]` (db only)
- `source_hash`

### 8.3 Pack Example
```json
{
  "bundle_id": "sp_CL_A12_hook_20251226",
  "cluster_id": "CL_A12",
  "temporal_phase": "HOOK",
  "segment_refs": ["shot_102", "shot_108"],
  "metrics_snapshot": { "cut_density": 3.4, "symmetry_score": 0.74 },
  "motif_refs": ["motif:doorway", "motif:backlight"],
  "evidence_refs": ["db:shot_102", "db:shot_108"],
  "source_hash": "sha256:..."
}
```

---

## 9) NotebookLM Prompt Protocol (Guide Extraction)

NotebookLM은 **가이드/변주/요약 레이어**다. 출력은 항상 **Claim + Evidence** 구조를 따른다.

### 9.1 Guide Tasks
- Logic Extraction (규칙화)
- Persona Summary (톤/감정/해석 프레임)
- Variation Guide (변주 규칙/노브 제안)
- Template Fit (추천 대상/부적합 조건)
- New Genre Delta (장르 변주 차이 설명)

### 9.2 기능 활용 규칙
- **Citations**: 모든 핵심 주장에 근거 링크 필수
- **Source filter**: 변주 목적별 소스 포함/제외
- **Mind Map**: 패턴/모티프 관계 구조화
- **Audio/Video Overview**: 빠른 감독 브리핑용
- **Slide/Infographic**: 템플릿 카드 요약용
- **Output language**: 다국어 가이드 생성

### 9.3 Output Contract (V1)
```json
{
  "output_spec": "NOTEBOOKLM_GUIDE_V1",
  "cluster_id": "CL_A12",
  "temporal_phase": "HOOK",
  "logic_summary": "...",
  "persona_summary": "...",
  "variation_rules": ["..."],
  "params_proposal": [{ "key": "pace", "range": [0,1] }],
  "template_fit_notes": ["..."],
  "claims": [{ "claim_id": "c1", "evidence_refs": ["db:shot_102"] }]
}
```

---

## 10) Optimal Variation Recommendation Protocol

1. NotebookLM이 **Top-K 변주 후보**를 생성 (Guide 레이어)
2. Evidence/Trace 점수로 **Quality Gate** 통과 여부 판단
3. GA/RL이 **파라미터 최적화** (Evidence reward 기준)
4. 승격된 변주만 캡슐 버전으로 고정

---

## 11) Evaluation + Promotion (RAGAS-style)

RAGAS 계열 평가지표(groundedness/faithfulness/answer_relevancy 등)를
`Trace.eval_scores`에 기록하여 승격 자동화를 보조한다.

연동 규칙:
- 평가 점수가 기준 이하이면 `candidate` 상태 유지
- 기준 이상 + Evidence Gate 통과 시 `promoted`

상세 규칙:
- `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- `11_DB_PROMOTION_RULES_V1.md`

---

## 12) Minimal Rollout (MVP)

- **1개 cluster + 1개 temporal_phase**로 시작
- Source Pack → NotebookLM Guide → Sheets Bus → DB 승격까지 완주
- 캡슐 1개 버전 고정 후 템플릿 카드로 노출
