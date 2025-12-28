# NotebookLM Source Pack & Prompt Protocol (CODEX v33)

**작성**: 2025-12-26  
**대상**: Product / Design / Engineering  
**목표**: 통데이터셋화(Logic/Persona) + 캡슐 노드 + RL을 **하나의 프로토콜**로 고정한다.

---

## 0) Canonical Anchors

- 철학/원칙: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- 캡슐 계약: `05_CAPSULE_NODE_SPEC.md`
- 영상 구조화: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- NotebookLM 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`
- 승격 기준: `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- Claim/Evidence/Trace: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- 리서치 소스: `04_RESEARCH_SOURCES_2025-12.md`

---

## 1) Protocol Invariants (Non-negotiable)

1. **DB SoR only**: NotebookLM 산출물은 Sheets Bus를 거쳐 **DB 승격**된 것만 정본으로 사용한다.  
2. **Video → DB → NotebookLM**: 원본 영상은 NotebookLM에 직접 넣지 않는다.  
3. **Sealed Capsule**: 노드 내부 체인은 서버에만 존재하며 UI는 I/O + 노출 파라미터만 공개한다.  
4. **Evidence first**: 모든 주장(claim)은 EvidenceRef를 가진다.  
5. **cluster_id + temporal_phase** 단위 운영이 기본이다.
6. **Mega-Notebook은 발굴/집계/운영 전용**이며, 캡슐 승격은 **phase-locked pack**에서만 한다.

---

## 1.5) NotebookLM Capability Notes (2025-12 Research)

이 섹션은 **프로토콜 설계에 영향을 주는 제품 능력**만 정리한다.
상세 근거는 `04_RESEARCH_SOURCES_2025-12.md`에 기록한다.

### 1.5.1 Source 타입/제약
- Source 타입: Google Docs, Google Slides, Word/Text/Markdown/PDF, Web URL, public YouTube URL, local audio files.
- Web URL은 **텍스트만** 수집(이미지/임베드/중첩 페이지는 미포함), paywall은 미지원.
- YouTube는 **캡션/자막 텍스트만** 수집(공개 영상만).
- Audio 파일은 업로드 시 **즉시 전사**되어 텍스트 소스로 저장됨.
- Source는 **정적 스냅샷**이며 Drive 문서는 **수동 sync** 필요. 비-Drive는 재업로드 필요.
- Phase-locked pack 제한: **source 최대 50개**, source 당 **500k words 또는 200MB**.
- Mega-Notebook(Ops/Discovery)은 **Ultra 기준 최대 600 sources**까지 허용하되, 캡슐 승격에는 사용하지 않는다.

### 1.5.2 Studio 다중 출력
- Studio는 동일 타입의 출력을 **여러 개** 생성/보관 가능.
- Audio/Video/Mind Map/Report를 동시에 생성 가능(백그라운드 생성 포함).

### 1.5.3 Output Language
- Output Language 선택 지원(80+ languages).
- Chat/Studio 출력 모두 선택 언어로 생성됨.

### 1.5.4 Audio/Video Overviews
- Audio Overview: **Deep Dive / The Brief** 모드, background 재생, 인터랙티브 Join 지원.
- Video Overview: narrated slides 기반, **주제/대상/학습 목적**을 지정 가능.

### 1.5.5 Mind Map + Data Tables
- Mind Map은 **핵심 개념 관계**를 시각화.
- Data Tables는 **구조화 테이블 생성 + Google Sheets export** 지원.

### 1.6 Mega-Notebook Usage (Discovery/Ops)
- Mega-Notebook은 **다중 cluster/phase 집계**를 허용하되, **캡슐 승격에는 직접 사용하지 않는다**.
- 캡슐 승격은 반드시 `{cluster_id, temporal_phase}` **phase-locked pack**에서 파생된 출력만 사용한다.
- Mega-Notebook 결과는 **후보 발굴/운영 인사이트/드리프트 감지**에만 사용한다.
- Ultra 기준 source 상한은 **600**으로 설정하며, 결과는 `ops_only` 라벨로 분리한다.

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

### 2.4 Script Persona Priority Policy (2025-12)

> **핵심 원칙**: 시나리오 페르소나가 1차 기준, 사용자 페르소나는 2차 보정, 거장/클러스터 페르소나는 안정성 앵커.

**Persona Source 우선순위**:
1. **Primary (script)**: 텍스트 시나리오 기반 페르소나 — 검증된 톤·리듬·해석이 가장 안정적
2. **Secondary (user)**: 창작자 개인 페르소나 — 스타일 인장/개성 역할, 보정 레이어
3. **Anchor (auteur)**: 거장/클러스터 페르소나 — 품질 붕괴 방지 브레이크

**Persona Fusion Formula (EXPERIMENTAL)**:
```
P_fused = normalize(w_script * P_script + w_user * P_user + w_auteur * P_auteur)
권장 초기값: w_script=0.55, w_user=0.20, w_auteur=0.25
제약: w_auteur >= 0.15 (최소 앵커)
```

**Capsule 노출 파라미터**:
- `persona_priority: script | blended | user` (default: script)
- 결과 summary에 `persona_source` 및 `synapse_rule_ref` 포함

### 2.5 Script Quality Gate (Gap 6)

Script Persona를 사용하기 위한 최소 품질 기준:

| 항목 | 최소 요건 | 검증 시점 |
|------|----------|----------|
| `min_length` | 500자 이상 | Source Pack 생성 |
| `min_scenes` | 3개 이상 | Segment 분할 후 |
| `required_fields` | `scene_summary`, `characters` 존재 | Ingest 시점 |
| `segment_type` | `script` 또는 `text` | DB 저장 시점 |

**검증 실패 시**:
- `segment_type=script`로 저장 불가
- `persona_source=script` 사용 불가, 자동으로 `auteur`로 fallback

## 3) Tong Datasetization Protocol (A/B/C/D)

> **정본**: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` §3.4

통 데이터셋 A/B/C/D 정의와 Synapse Rule은 정본 문서를 따른다.
이 문서는 **Logic/Persona 추출 프로토콜**에 집중한다.

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

### 6.1 Distance Function (EXPERIMENTAL)

> [!WARNING]
> 아래 가중치는 **실험값**이며 학습/검증 후 조정 예정

```
D = 0.55*D_logic + 0.35*D_persona + 0.10*D_context
```

**정의**:
- `D_logic`: Logic Vector 간 코사인 거리
- `D_persona`: Persona Vector 간 코사인 거리
- `D_context`: 장르/시대/지역 메타데이터 불일치 페널티 (0 또는 1)

### 6.2 Thresholds (MVP, EXPERIMENTAL)

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

### 8.1.1 Pack Sharding (NotebookLM 제한 대응)
- **Phase-locked pack source 제한(50개)**을 초과하면 pack을 분할한다.
- 규칙: `bundle_id` 뒤에 `p01/p02` shard suffix 추가.
- 예: `sp_CL_A12_hook_20251226_p01`
- shard는 동일 `{cluster_id, temporal_phase}`를 공유한다.

### 8.2 Pack Fields (Required)
- `bundle_id`, `cluster_id`, `temporal_phase`
- `segment_refs[]` (shot_id/time range)
- `metrics_snapshot` (cadence/compose/motion summary)
- `motif_refs[]` (object/action/visual motif)
- `evidence_refs[]` (db only)
- `source_hash`

### 8.2.1 Source Snapshot (Recommended)
- `source_snapshot_at`: 소스 스냅샷 시각(정적 copy 기준).
- `source_sync_at`: Drive source 재동기화 시각.
- `source_count`: shard당 source 수(<=50).
- `source_manifest[]`: source id + type + title + url + rights_status.

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

### 8.4 Source Discovery (Optional)
- NotebookLM의 **Fast Research / Deep Research**로 web/Drive source 후보를 수집할 수 있다.
- 단, **SoR 규칙**을 위해 수집 결과는 반드시 `raw_assets`에 기록하고 rights check를 통과해야 한다.
- Deep Research 결과는 **cited source list**를 함께 저장하고, 미선택 소스는 폐기한다.

---

## 9) NotebookLM Prompt Protocol (Guide Extraction)

NotebookLM은 **가이드/변주/요약 레이어**다. 출력은 항상 **Claim + Evidence** 구조를 따른다.

### 9.1 Guide Tasks
- Logic Extraction (규칙화)
- Persona Summary (톤/감정/해석 프레임)
- Variation Guide (변주 규칙/노브 제안)
- Template Fit (추천 대상/부적합 조건)
- New Genre Delta (장르 변주 차이 설명)
- Mind Map (모티프/관계)
- Data Table (구조화 테이블 → Sheets export)

### 9.2 기능 활용 규칙
- **Citations**: 모든 핵심 주장에 근거 링크 필수
- **Source filter**: 변주 목적별 소스 포함/제외
- **Mind Map**: 패턴/모티프 관계 구조화
- **Audio/Video Overview**: 빠른 감독 브리핑용
- **Video Overview (narrated slides)**: 시각 요약/설명용
- **Output language**: 다국어 가이드 생성
- **Multiple outputs**: 동일 타입 출력은 `studio_output_id + output_language + guide_type` 조합으로 구분

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
  "claims": [{ "claim_id": "c1", "evidence_refs": ["db:shot_102"] }],
  "output_type": "report",
  "output_language": "ko",
  "studio_output_id": "studio-output-001"
}
```

---

## 10) Optimal Variation Recommendation Protocol

1. NotebookLM이 **Top-K 변주 후보**를 생성 (Guide 레이어)
2. Evidence/Trace 점수로 **Quality Gate** 통과 여부 판단
3. GA/RL이 **파라미터 최적화** (Evidence reward 기준)
4. 승격된 변주만 캡슐 버전으로 고정

---

## 11) Evaluation + Promotion

> **정본**: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md` §3.4, `11_DB_PROMOTION_RULES_V1.md` §4

평가/승격 규칙은 정본 문서를 따른다. 이 문서에서는 중복 기술하지 않는다.

---

## 12) Minimal Rollout (MVP)

- **1개 cluster + 1개 temporal_phase**로 시작
- Source Pack → NotebookLM Guide → Sheets Bus → DB 승격까지 완주
- 캡슐 1개 버전 고정 후 템플릿 카드로 노출
