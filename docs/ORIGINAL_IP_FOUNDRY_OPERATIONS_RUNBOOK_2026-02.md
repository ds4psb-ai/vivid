# Original-IP Foundry Operations Runbook (2026-02) — v2.0 (Ambient Canvas)

> 목적: A-Prime 운영 규약 기반으로 Foundry를 빠르게 배포하되, 장애/오용 시 10분 내 차단·복구한다.
> **v2.0 변경**: Ambient Creative Canvas OS 패러다임 반영 — Blueprint Canvas, Fragment Ingestion, Auto-Placement, Sora deprecation.
> **참조**: `AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md` (Vision Document — 용어 정의 및 전체 비전)
> **갱신일**: 2026-02-23

---

## 1) 즉시 전환 가능한 운영 플래그

```bash
AD_FOUNDRY_ENABLED=true|false
AD_FOUNDRY_WRITE_ENABLED=true|false
AD_FOUNDRY_ACCESS_SCOPE=internal|authenticated|public
AD_FOUNDRY_ALLOWLIST=comma,separated,emails
AD_FOUNDRY_READONLY_SAFE_PATHS=/api/v1/foundry/...,/api/v1/foundry/provenance/export-c2pa,/api/v1/foundry/workers/dispatch,/api/v1/foundry/workers/jobs
AD_THEORY_KB_ENABLED=true|false
AD_CANVAS_ENABLED=true|false          # Blueprint Canvas 전체 활성화
AD_FRAGMENT_INGESTION_ENABLED=true|false  # Fragment Ingestion Pipeline 활성화
AD_AUTO_PLACEMENT_ENABLED=true|false   # Auto-Placement AI 활성화
AD_SORA_DEPRECATED=true               # Sora 어댑터 비활성화 (hard deprecation)
```

- **긴급 차단(권장 1순위)**: `AD_FOUNDRY_ENABLED=false`
- **쓰기 차단(2순위)**: `AD_FOUNDRY_WRITE_ENABLED=false`
- **접근 축소(3순위)**: `AD_FOUNDRY_ACCESS_SCOPE=internal` + allowlist 최소화
- **KB 비활성화(4순위)**: `AD_THEORY_KB_ENABLED=false` → Council이 Empirical-only로 graceful degrade (§SSOT 2-H)
- **Canvas 비활성화**: `AD_CANVAS_ENABLED=false` → Fragment 수집은 계속하되 Canvas 배치 비활성
- **Fragment 비활성화**: `AD_FRAGMENT_INGESTION_ENABLED=false` → 채널 수집 중단, 기존 Canvas 유지
- **Placement 비활성화**: `AD_AUTO_PLACEMENT_ENABLED=false` → 수동 배치만 허용 (Auto-Placement 비활성)
- **Sora deprecated**: `AD_SORA_DEPRECATED=true` → Prompt Compiler에서 Sora adapter 호출 차단

---

## 2) 단계적 공개 규약

1. **Stage F (Fragment)**
   - `FRAGMENT_INGESTION_ENABLED=true`, `CANVAS_ENABLED=false`
   - Fragment 수집만 시작, Canvas 미공개
   - 채널 어댑터 검증 + Fragment 분류 품질 확인 단계

2. **Stage C (Canvas)**
   - `CANVAS_ENABLED=true`, `AUTO_PLACEMENT_ENABLED=false`
   - Canvas 공개, 수동 배치만
   - 감독이 직접 Fragment를 셀에 배치하며 UX 검증

3. **Stage M (Materialization)**
   - `AUTO_PLACEMENT_ENABLED=true`
   - Auto-Placement 활성화 + Progressive Materialization 전체 경로 오픈
   - `auto_placement_accuracy` >= 0.70 확인 후 진입

4. **Stage R (Read-only)**
   - `WRITE_ENABLED=false`
   - 읽기/추천/평가용 POST만 허용 (safe path whitelist)

5. **Stage W (Limited write)**
   - 운영 KPI 통과 시 `WRITE_ENABLED=true`
   - 내부 승인 플로우 유지

6. **Stage GA (Authenticated public)**
   - `ACCESS_SCOPE=authenticated`
   - 로그인 사용자에게 공개

---

## 2.1 Qdrant 동시성 제어 규약

Foundry 패턴/전이 룰 업서트는 아래 규약을 따른다.

1. payload에 `revision` 필드 유지 (optimistic concurrency)
2. 요청에 `expected_revision`을 포함해 충돌 감지
3. Qdrant write는 `wait=true`, `ordering=strong` 사용
4. 충돌 시 즉시 실패 처리(`status=conflict`) 후 재시도 큐 전송

### `blueprint_fragments` 컬렉션

Fragment 임베딩 + 배치 메타데이터를 저장하는 전용 컬렉션.

- **payload index**: `project_id`, `fragment_type`, `suggested_cell`, `materialization_level`, `placement_confidence`
- **optimistic revision 동시성 제어**: 기존 규약과 동일 (`revision` 필드 + `expected_revision` 충돌 감지)
- **write 설정**: `wait=true`, `ordering=strong`

---

## 2.2 Worker Port 전환 규약 (Agent0 ↔ Taskiq ↔ Temporal)

1. 기본 실행체는 `Agent0WorkerProvider`
2. 병목/장애 시 `TaskiqWorkerProvider` 또는 `TemporalWorkerProvider`로 전환 가능해야 함
3. 분기별 1회 스위치 드릴에서 아래 3개 검증:
   - dispatch_job 성공
   - status 조회 가능
   - cancel 흐름 정상
4. status/cancel은 `tenant_id + project_id` 스코프 파라미터를 필수로 전달한다.
5. 스코프 불일치 시 API는 403(`tenant scope mismatch` 또는 `project scope mismatch`)를 반환해야 한다.

---

## 2.3 Cinema Grammar KB 운영 규약 (§SSOT 2-H)

Cinema Grammar KB 3종(EditingGrammarKB, NarrativeTheoryKB, StylePatternKB)은 VPS 1-3의 OpenClaw 인스턴스에서 운영한다.

1. **KB 검색 SLO**: p95 < 500ms (VPS당 OpenClaw 하이브리드 검색)
2. **KB 인덱싱**: Agent0 → Codex 5.3 xhigh dispatch로 배치 처리
3. **Fallback**: `AD_THEORY_KB_ENABLED=false` 시 Council은 Empirical-only로 동작 (theory_layer 없이 enrichment 진행)
4. **KB 업데이트 주기**: 주간 1회 증분 인덱싱, 월간 1회 전체 재인덱싱
5. **KB 품질 감사**: Meta-Council 주간 감사 시 theory_alignment_avg / power_mutation_ratio / dead_rule_prune_count 확인

---

## 2.4 Fragment Ingestion SLO

Fragment Ingestion Pipeline 각 단계의 성능 목표.

| Stage | p95 Target |
|-------|-----------|
| Fragment Classification (type + metadata) | < 1s |
| Auto-Placement (Canvas context → cell suggestion) | < 3s |
| End-to-end (channel receive → Canvas update) | < 5s |
| Rights Pre-screen (Fragment-level IP check) | < 2s |

---

## 2.5 Engine Deprecation Protocol (Sora)

Sora 제거 절차:

1. `AD_SORA_DEPRECATED=true` 설정 → Prompt Compiler가 Sora adapter 호출 건너뜀
2. 기존 Sora 생성 결과는 보존 (삭제하지 않음)
3. `prompt_compiler.py` DEFAULT_ENGINES에서 `"sora"` 제거
4. `SoraEngineAdapter` 코드는 deprecated 마킹 후 60일 유예 기간 유지
5. 60일 후 코드 제거 (clean removal)
6. 제거 사유 문서화: API 프로덕션 부적합(Sora 2는 2025-09-30 출시되었으나, Plus/Pro 전용 + rate limit 5-50 RPM) + 권리 정책 충돌(IP 생성 차단) + 수동 멀티샷 한계(vs Kling Smart Storyboard) + commodity 상황 차별 가치 부재

> **코드 참조**: `backend/app/features/original_ip_foundry/prompt_compiler.py`
> **사유 상세**: `AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md` §11 Engine Strategy

---

## 3) 관측성 스키마 (필수)

`foundry.audit` 로그에 아래 필드를 고정한다.

- `path`
- `method`
- `user`
- `model`
- `input_type`
- `latency_ms`
- `status_code`
- `failure_code`
- `block_reason`
- `theory_alignment` (Council Theory Validation 결과, §SSOT 2-H)
- `kb_source` (참조된 KB: editing_grammar / narrative_theory / style_pattern)
- `classification` (3단 분류: invariant / power_mutation / dead_rule)
- `fragment_type` (text_memo / voice_memo / photo / video_clip / url_bookmark / sketch / prompt_draft)
- `placement_confidence` (0.0 ~ 1.0, Auto-Placement 신뢰도)
- `materialization_level` (0~4, Progressive Materialization 단계)
- `canvas_fill_rate` (0.0 ~ 1.0, 현재 프로젝트 Canvas 채움율)

오류/차단 시 `failure_code`, `block_reason` 누락 금지.
권장: C2PA export 호출은 `input_type=provenance`로 고정해 추적한다.
Council enrichment 호출은 `theory_alignment`, `kb_source`, `classification` 필드를 포함해 이론 검증 추적성을 확보한다.
Fragment 관련 호출은 `fragment_type`, `placement_confidence`, `materialization_level`, `canvas_fill_rate` 필드를 포함해 Canvas 상태 추적성을 확보한다.

---

## 4) 사고 대응 10분 플레이북

### 0~2분
- 증상 확인: 5xx 급증, 403 급증, 권리 게이트 오판, 지연 p95 급등
- 즉시 `AD_FOUNDRY_ENABLED=false` 적용

### 2~5분
- `foundry.audit` 최근 100건 확인
- 차단 사유 상위 3개, 실패 코드 상위 3개 추출

### 5~10분
- 원인 분류: 권리정책/데이터/모델/라우팅/인증/**KB 검색**/**Fragment 파이프라인**/**Canvas 상태**
- 임시 조치:
  - 정책 오판: `ACCESS_SCOPE=internal`로 축소
  - 품질 저하: 추천 endpoint hold 강제
  - 과부하: 배치 큐/실시간 분리 확인
  - **KB 검색 장애**: `AD_THEORY_KB_ENABLED=false` → Empirical-only fallback (Council 기능 유지, theory_layer만 비활성)
  - **KB 인덱싱 오류**: Agent0 배치 큐 일시 중지 + VPS OpenClaw 인스턴스 재시작
  - **Fragment 폭주**: 단일 프로젝트에서 분당 100+ Fragment 수신 → `FRAGMENT_INGESTION_ENABLED=false` for project + rate limit 적용
  - **Placement 드리프트**: `auto_placement_accuracy` < 0.30 (30% 미만 수락률) → `AUTO_PLACEMENT_ENABLED=false` → manual placement fallback + 알고리즘 재검토
  - **Canvas 상태 불일치**: OpenClaw Memory와 Qdrant `blueprint_fragments` 간 데이터 불일치 → reconciliation job 즉시 실행 + 불일치 셀 목록 추출 + 수동 복구

---

## 5) GA 직전 체크리스트

- [ ] `/api/v1/foundry/health` 정상
- [ ] `/api/v1/foundry/status`에서 접근/쓰기 플래그 기대값 확인
- [ ] `/api/v1/foundry/workers/providers`에서 active provider 확인
- [ ] `/api/v1/foundry/workers/jobs/{job_id}` status 조회 시 tenant/project 스코프 강제 확인
- [ ] 권리 평가 응답에 `decision/reason_codes/per_asset` 포함
- [ ] 추천 응답에 `continuity_score/rights_decision/recommendation_rationale` 포함
- [ ] A/B 이벤트 집계에서 variant별 accept/edit/reject rate 노출
- [ ] `/api/v1/foundry/provenance/export-c2pa` 응답에 `spec_version/manifest/compliance` 포함
- [ ] 장애 롤백 리허설 1회 완료
- [ ] Cinema Grammar KB 검색 p95 < 500ms (VPS 1-3 각각)
- [ ] `AD_THEORY_KB_ENABLED=false` fallback 동작 확인 (Empirical-only graceful degrade)
- [ ] theory_layer 포함 Pattern Atom 500+ 확인
- [ ] KB 인덱싱 커버리지: EditingGrammar 100+, Narrative 50+, Style 30+
- [ ] Council enrichment 응답에 `theory_alignment`, `classification` 필드 포함
- [ ] Blueprint Canvas API (`/api/v1/foundry/canvas/*`) 정상
- [ ] Fragment Ingestion Pipeline end-to-end p95 < 5s
- [ ] Auto-Placement accuracy >= 0.70 (파일럿 기준)
- [ ] `creative_fill_rate` 30%+ (파일럿 프로젝트 기준)
- [ ] Qdrant `blueprint_fragments` 컬렉션 정상 + payload index 확인
- [ ] `AD_SORA_DEPRECATED=true` 확인 + Prompt Compiler에서 Sora 호출 0건
- [ ] 3-engine (Kling 3.0/Seedance 2.0/Veo 3.1) Prompt Compiler 정상 동작 확인
- [ ] Fragment 폭주 시나리오 대응 리허설 1회 완료
- [ ] Canvas 상태 불일치 reconciliation job 테스트 완료
