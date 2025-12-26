# NotebookLM Pattern Engine → Capsule Node Pipeline (CODEX v31)

**작성**: 2025-12-26  
**대상**: Product / Design / Engineering  
**목표**: NotebookLM 기반 “거장/수작 패턴+페르소나” 세트화 → Sealed Capsule Node 승격 파이프라인을 구현 가능한 수준으로 고정

---

## 0) 범위와 고정 원칙 (정본 요약)

- **DB = SoR(단일 진실)**, NotebookLM/Opal은 가속 레이어.  
  (상세: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`)
- **원본 영상은 NotebookLM에 직접 넣지 않는다.**  
  Gemini 구조화 → DB SoR → NotebookLM 소스. (상세: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`)
- **Derived 결과는 Sheets Bus → DB SoR 승격** 흐름을 거친다.  
  (상세: `08_SHEETS_SCHEMA_V1.md`, `11_DB_PROMOTION_RULES_V1.md`)
- **Capsule Node는 Sealed**: UI에는 입력/출력/노출 파라미터만 공개.  
  (상세: `05_CAPSULE_NODE_SPEC.md`)
- **NotebookLM 운영 단위는 `cluster_id + temporal_phase`**를 기본으로 한다.
- **Mega-Notebook은 발굴/집계/운영 전용**이며, 캡슐 승격은 **phase-locked pack**에서만 한다.
- 본 문서는 흐름/역할을 재정의하지 않는다.  
  (정본: `10_PIPELINES_AND_USER_FLOWS.md`)

---

## 1) CS(Contract/Promotion/Sealing) 3계층 모델

### 1.1 Contract Layer (계약)
목표: “무엇을 넣고 무엇이 나오는지”를 고정.

- **CapsuleNodeSpec의 계약**
  - `inputContracts` / `outputContracts`
  - `allowedTypes`, `maxUpstream`, `contextMode`
- **NotebookLM Output Contract**
  - `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md` 준수
  - Claim/Evidence 구조는 `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md` 준수

### 1.2 Promotion Layer (승격)
목표: Derived 결과를 DB SoR로 승격하기 위한 규칙/증거/추적.

- **승격 규칙**
  - `11_DB_PROMOTION_RULES_V1.md`
  - `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- **증거 요구**
  - `claim -> evidenceRefs` 매핑 필수
  - evidenceRefs는 DB SoR(shot/segment) 기반이어야 함

### 1.3 Sealing Layer (봉인)
목표: IP 보호 + 재현성 확보.

- 캡슐 내부 체인/프롬프트/룰 조합은 **서버에만 존재**
- UI에는 **입력/출력/노출 파라미터 + 버전 + 근거 요약**만 표시
- 내부 변경 시 **sealed_hash 변경 + 버전 bump**

---

## 2) MDA(Logic/Persona 2공간) 모델

### 2.1 Logic Vector (L)
“컷/구성/모티프/반복”은 정량화 가능한 신호로 묶는다.

- 컷 리듬: 샷 길이 분포, 컷 밀도, 리듬 변화율
- 구성/미장센: 프레이밍 비율, 대칭도, 색 대비
- 카메라 움직임: handheld/dolly/pan 비율
- 모티프 반복: 등장 빈도, 재등장 간격

### 2.2 Persona Vector (P)
“톤/감정곡선/호흡”을 조절 신호로 모델링한다.

- 해석 톤: 아이러니/서정/냉소/따뜻함 등
- 감정 곡선: phase별 valence/arousal 변화
- 호흡/리듬: 문장 길이, 침묵 비율
- userFitNotes (추천/적합도)와 연계

### 2.3 클러스터 거리 함수 (권장)

```
D = wL * DL(Li, Lj) + wP * DP(Pi, Pj) + wC * DC(context)
추천 가중치: wL=0.55, wP=0.35, wC=0.10
```

규칙:
- **로직 유사**가 우선, **페르소나**는 스타일 누출 방지 브레이크 역할
- `temporal_phase`는 반드시 분리(phase 혼합 금지)

---

## 3) Pipeline: NotebookLM → DB → Capsule Node

```
Raw Video
  → Gemini Video Understanding
  → DB SoR (segments/shots/motifs)
  → (Optional) Mega-Notebook (Discovery/Ops)
  → Source Pack Builder (cluster_id + temporal_phase)
  → NotebookLM Cluster Notebook
  → Derived Outputs (Sheets Bus)
  → Promotion Gate
  → DB SoR (Pattern/Persona/Trace)
  → Capsule Builder (Sealed + version pin)
  → Template Catalog → Canvas
```

핵심:
- NotebookLM은 **Pattern Engine**으로 사용하되, 결과는 **승격 전까지 Derived**
- Capsule 실행은 **DB 근거만 사용**

---

## 4) Source Pack 규칙 (NotebookLM 입력)

### 4.1 Source Pack 구성
- `cluster_id`, `temporal_phase`
- `segment_refs` (shot_id/segment_id/time_range)
- `metrics_snapshot` (리듬/구성/모티프 요약)
- `bundle_hash` (재현성)

### 4.2 Temporal Phase 가이드
숏폼 기준:
- HOOK (0~3s)
- BUILD (3~12s)
- PAYOFF (12~20s)
- CTA/LOOP (20~30s)

롱폼 기준:
- SETUP / TURN / ESCALATION / CLIMAX / RESOLUTION

---

## 5) Capsule Node 고정 규칙 (Sealed Contract)

### 5.1 공개 영역
- 입력 스키마, 출력 스키마, 노출 파라미터
- capsuleId, capsuleVersion, evidence 요약

### 5.2 비공개 영역
- 내부 체인/프롬프트/룰 조합
- sealed_hash로만 변경 추적

### 5.3 필수 노출 파라미터
최소 2개 이상이며, 범위/효과가 정의되어야 한다.
예: `style_intensity`, `pacing`, `motif_bias`, `persona_tone`

---

## 6) Observability (승격/품질용 필수 메타)

캡슐 실행/승격 판단에 반드시 기록:
- `token_usage`, `latency_ms`, `cost_usd_est`
- `eval_scores` (groundedness/relevancy/completeness)
- `trace_id` + `bundle_hash` + `model_version`

이 데이터는 Promotion Scorecard의 입력이다.

---

## 7) MVP 구현 순서 (정본 확정)

1. DB SoR 스키마 확정 (segments + claim/evidence + trace)
2. Gemini 구조화 → DB 적재 파이프라인
3. Source Pack Builder (cluster_id + temporal_phase)
4. NotebookLM Output Artifact v1 고정 + ingest
5. Promotion Gate (증거/scorecard 기반)
6. Capsule Builder v1 (sealed + version pin)
7. Template → Canvas → Run/Preview

---

## 8) Acceptance Checklist

- NotebookLM 산출물은 **claim-evidence 구조**로 저장된다.
- evidenceRefs는 **DB SoR 기반**으로 검증된다.
- Capsule Node는 **sealed_hash + version pin**을 가진다.
- cluster_id + temporal_phase 노트북 단위가 유지된다.
- Promotion Scorecard가 승격 사유를 기록한다.

---

## 9) 문서 연결

- 흐름/역할 정본: `10_PIPELINES_AND_USER_FLOWS.md`
- Video 구조화: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- NotebookLM 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`, `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- 캡슐 계약: `05_CAPSULE_NODE_SPEC.md`
