# Original-IP Foundry + AD Co-Director Runtime Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** OpenClaw 메모리 SSoT, Agent0 워커 분업, Rights Graph 기반 합법 창작 게이트, continuity 우선 추천 루프를 프로덕션 수준으로 구현한다.

**Architecture:** OpenClaw(세션/메모리/채널) + AD Co-Director(도메인 지능) + Qdrant(샷 검색) + Rights Graph(권리 게이트) + Agent0(백오피스 병렬 실행)으로 레이어 분리한다. 온라인 경로는 저지연 추천에 집중하고, Agent0는 배치/실험/재인덱싱을 담당한다.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, Qdrant, OpenClaw, Agent0, Playwright, pytest, React/TypeScript

---

### Task 1: Rights Graph 데이터 모델/마이그레이션

**Files:**
- Create: `backend/app/models/rights_graph.py`
- Create: `backend/tests/models/test_rights_graph.py`
- Create: `backend/alembic/versions/013_add_rights_graph_tables.py`
- Modify: `backend/app/models.py`

**Step 1: Write the failing test**

`backend/tests/models/test_rights_graph.py`에 `test_rights_asset_requires_license_type()` 작성.

**Step 2: Run test to verify it fails**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/models/test_rights_graph.py::test_rights_asset_requires_license_type`
Expected: FAIL (모델/테이블 없음)

**Step 3: Write minimal implementation**

`rights_assets`, `rights_rules`, `provenance_events` 테이블 모델 작성 + `source_license`, `allowed_actions`, `derivative_allowed` 필드 정의.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/models/test_rights_graph.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/models/rights_graph.py backend/alembic/versions/013_add_rights_graph_tables.py backend/tests/models/test_rights_graph.py
git commit -m "feat(rights): add rights graph core schema"
```

---

### Task 2: 권리 게이트 서비스 + API

**Files:**
- Create: `backend/app/services/rights_gate_service.py`
- Create: `backend/app/routers/rights_gate.py`
- Create: `backend/tests/services/test_rights_gate_service.py`
- Create: `backend/tests/routers/test_rights_gate.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing service tests**

`test_block_when_derivative_not_allowed`, `test_pass_when_action_allowed` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_rights_gate_service.py`
Expected: FAIL (서비스 없음)

**Step 3: Implement service + router**

- `POST /api/v1/rights/check-pre-gen`
- `POST /api/v1/rights/check-post-gen`
- 응답에 `decision`, `reason_codes`, `evidence_refs` 포함.

**Step 4: Run tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_rights_gate_service.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/routers/test_rights_gate.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/rights_gate_service.py backend/app/routers/rights_gate.py backend/app/main.py backend/tests/services/test_rights_gate_service.py backend/tests/routers/test_rights_gate.py
git commit -m "feat(rights): add pre/post generation policy gates"
```

---

### Task 3: OpenClaw 메모리 매핑 어댑터

**Files:**
- Create: `backend/app/adapters/openclaw_memory_adapter.py`
- Create: `backend/tests/adapters/test_openclaw_memory_adapter.py`
- Modify: `backend/app/services/adapters/inspiration_ingestion_service.py`

**Step 1: Write failing tests**

`test_parse_memory_daily_log_to_inspiration_items` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/adapters/test_openclaw_memory_adapter.py`
Expected: FAIL

**Step 3: Minimal implementation**

OpenClaw 파일(`memory/*.md`, `MEMORY.md`, `bank/*.md`, `entities/*.md`)에서 `project_id`, `scene_id`, `@character`, `mise_en_scene` 태그 파싱.

**Step 4: Run tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/adapters/test_openclaw_memory_adapter.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/adapters/openclaw_memory_adapter.py backend/app/services/adapters/inspiration_ingestion_service.py backend/tests/adapters/test_openclaw_memory_adapter.py
git commit -m "feat(memory): map openclaw workspace files to inspiration schema"
```

---

### Task 4: Retrieval 이중 경로 (Memory vs Shot Corpus)

**Files:**
- Create: `backend/app/services/ad_retrieval_service.py`
- Create: `backend/tests/services/test_ad_retrieval_service.py`
- Modify: `backend/app/rag/backends/qdrant_backend.py`

**Step 1: Write failing tests**

`test_routes_to_memory_first_for_director_context`, `test_routes_to_qdrant_for_shot_search` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_retrieval_service.py`
Expected: FAIL

**Step 3: Implement service**

- Query type `director_context` → OpenClaw memory adapter
- Query type `shot_reference` → Qdrant backend
- 결과 통합 시 정규 스키마로 normalize

**Step 4: Run tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_retrieval_service.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/ad_retrieval_service.py backend/app/rag/backends/qdrant_backend.py backend/tests/services/test_ad_retrieval_service.py
git commit -m "feat(retrieval): add dual-path memory and shot corpus retrieval"
```

---

### Task 5: Continuity-first 랭킹 + 실험 이벤트 수집

**Files:**
- Create: `backend/app/services/ad_ranking_service.py`
- Create: `backend/tests/services/test_ad_ranking_service.py`
- Modify: `backend/app/uqsl/thompson_sampling.py`
- Modify: `backend/app/routers/dimension/_base.py`

**Step 1: Write failing ranking tests**

`test_drop_candidate_when_continuity_below_threshold`, `test_reward_update_on_variant_selected` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_ranking_service.py`
Expected: FAIL

**Step 3: Implement minimal scoring**

`final_score = 0.45*continuity + 0.20*mise_en_scene + 0.15*story_intent_fit + 0.10*director_style_fit + 0.10*execution_feasibility`
및 `continuity < 0.60` 하드 탈락 적용.

**Step 4: Run tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_ranking_service.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/uqsl`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/ad_ranking_service.py backend/app/uqsl/thompson_sampling.py backend/app/routers/dimension/_base.py backend/tests/services/test_ad_ranking_service.py
git commit -m "feat(ranking): enforce continuity-first scoring and reward updates"
```

---

### Task 6: Prompt Compiler 4-Engine 표준 계약

**Files:**
- Create: `backend/app/services/prompt_compiler_service.py`
- Create: `backend/tests/services/test_prompt_compiler_service.py`
- Modify: `backend/app/schemas/agent.py`
- Modify: `frontend/src/lib/api.ts`

**Step 1: Write failing tests**

`test_compile_returns_common_contract_fields` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_prompt_compiler_service.py`
Expected: FAIL

**Step 3: Implement minimal compiler**

엔진별 출력에 공통 필드(`shot_id`, `camera_intent`, `motion_intent`, `continuity_anchor_refs`, `audio_intent`) 포함.

**Step 4: Run tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_prompt_compiler_service.py`
- `cd /Users/ted/vivid/frontend && npm run lint`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/prompt_compiler_service.py backend/app/schemas/agent.py backend/tests/services/test_prompt_compiler_service.py frontend/src/lib/api.ts
git commit -m "feat(prompt): add unified multi-engine prompt compiler contract"
```

---

### Task 7: Agent0 워커 스웜 연동 (배치 작업 전용)

**Files:**
- Create: `backend/app/jobs/agent0_dispatcher.py`
- Create: `backend/tests/jobs/test_agent0_dispatcher.py`
- Create: `backend/scripts/run_agent0_batch_jobs.py`
- Modify: `docs/27_MCP_INTEGRATION_SPEC_V1.md`

**Step 1: Write failing tests**

`test_dispatch_index_rebuild_job`, `test_dispatch_experiment_rollup_job` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/jobs/test_agent0_dispatcher.py`
Expected: FAIL

**Step 3: Implement dispatcher**

Agent0로 전달할 작업 타입(`index_rebuild`, `eval_rollup`, `quality_regression`)과 payload 스키마 정의.

**Step 4: Run tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/jobs/test_agent0_dispatcher.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/jobs/agent0_dispatcher.py backend/tests/jobs/test_agent0_dispatcher.py backend/scripts/run_agent0_batch_jobs.py docs/27_MCP_INTEGRATION_SPEC_V1.md
git commit -m "feat(agent0): add batch worker dispatch integration"
```

---

### Task 8: SSoT/문서/검증 동기화

**Files:**
- Modify: `docs/AD_CO_DIRECTOR_OS_SSOT_2026_H2.md`
- Modify: `00_DOCS_INDEX.md`
- Modify: `docs/00_DOCS_INDEX.md`
- Create: `docs/contracts/AD_RUNTIME_EVENT_SCHEMA.md`

**Step 1: Write docs validation checklist**

SSoT 항목과 구현 파일 매핑표 작성.

**Step 2: Run backend smoke tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/routers/test_dimension_sse.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/agents/test_vivid_agent_integration.py tests/routers/test_agent_streaming.py`
Expected: PASS

**Step 3: Run frontend smoke tests**

Run:
- `cd /Users/ted/vivid/frontend && npm run test:e2e -- e2e/dimension.spec.ts`
- `cd /Users/ted/vivid/frontend && npm run test:e2e -- e2e/agent-chat.spec.ts e2e/flow.spec.ts`
Expected: PASS

**Step 4: Update changelog/docs index**

문서 인덱스와 릴리즈 노트 동기화.

**Step 5: Commit**

```bash
git add docs/AD_CO_DIRECTOR_OS_SSOT_2026_H2.md docs/00_DOCS_INDEX.md 00_DOCS_INDEX.md docs/contracts/AD_RUNTIME_EVENT_SCHEMA.md
git commit -m "docs(ssot): sync original-ip foundry runtime and verification matrix"
```

---

### Task 9: B2C 채널 어댑터 계층 (Telegram/Kakao/WebChat)

**Files:**
- Create: `backend/app/channels/channel_port.py`
- Create: `backend/app/channels/adapters/telegram_adapter.py`
- Create: `backend/app/channels/adapters/kakao_adapter.py`
- Create: `backend/app/channels/adapters/webchat_adapter.py`
- Create: `backend/tests/channels/test_channel_contract.py`

**Step 1: Write failing contract tests**

`test_all_adapters_emit_channelevent_v1`, `test_send_reply_contract` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/channels/test_channel_contract.py`
Expected: FAIL

**Step 3: Implement minimal adapters**

공통 `ChannelEvent v1` 매퍼를 구현하고 Telegram/Kakao/WebChat adapter가 동일 schema를 반환하도록 구현.

**Step 4: Run tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/channels/test_channel_contract.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/channels backend/tests/channels/test_channel_contract.py
git commit -m "feat(channel): add channel adapter contract for telegram kakao webchat"
```

---

### Task 10: Provider Port + Switch Drill 자동 검증

**Files:**
- Create: `backend/app/providers/memory_port.py`
- Create: `backend/app/providers/worker_port.py`
- Create: `backend/tests/providers/test_memory_port_contract.py`
- Create: `backend/tests/providers/test_worker_port_contract.py`
- Create: `backend/scripts/run_vendor_switch_drill.py`

**Step 1: Write failing contract tests**

`test_openclaw_and_fallback_memory_provider_share_same_contract`, `test_agent0_and_temporal_worker_provider_share_same_contract` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/providers`
Expected: FAIL

**Step 3: Implement provider ports**

Memory/Worker provider interface와 OpenClaw/Agent0 + fallback 구현체 바인딩 추가.

**Step 4: Run tests + switch drill**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/providers`
- `cd /Users/ted/vivid/backend && python scripts/run_vendor_switch_drill.py --dry-run`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/providers backend/tests/providers backend/scripts/run_vendor_switch_drill.py
git commit -m "feat(provider): add swap-safe provider ports and switch drill script"
```

---

### Task 11: Masterpiece Pattern Atom 파이프라인 구축

**Files:**
- Create: `backend/app/services/masterpiece_pattern_extraction_service.py`
- Create: `backend/app/schemas/masterpiece_pattern.py`
- Create: `backend/tests/services/test_masterpiece_pattern_extraction_service.py`
- Create: `backend/scripts/ingest_masterpiece_patterns.py`

**Step 1: Write failing tests**

`test_extract_pattern_atom_from_shot_sequence`, `test_emit_preconditions_and_expected_effect` 작성.

**Step 2: Run failing tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_masterpiece_pattern_extraction_service.py`
Expected: FAIL

**Step 3: Implement minimal extraction service**

scene/shot/beat 입력에서 Pattern Atom(`pattern_type`, `preconditions`, `execution_template`, `expected_effect`, `anti_pattern`)을 생성하고 `source_license` 필드를 강제.

**Step 4: Run tests**

Run: `cd /Users/ted/vivid/backend && pytest -v tests/services/test_masterpiece_pattern_extraction_service.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/masterpiece_pattern_extraction_service.py backend/app/schemas/masterpiece_pattern.py backend/tests/services/test_masterpiece_pattern_extraction_service.py backend/scripts/ingest_masterpiece_patterns.py
git commit -m "feat(pattern): add masterpiece pattern atom extraction pipeline"
```

---

### Task 12: Qdrant 다중 컬렉션 + 4-pass 검색 구현

**Files:**
- Create: `backend/app/rag/pattern_collections.py`
- Modify: `backend/app/rag/backends/qdrant_backend.py`
- Create: `backend/tests/rag/test_pattern_collections.py`
- Create: `backend/tests/services/test_pattern_aware_retrieval.py`

**Step 1: Write failing tests**

`test_create_pattern_collections`, `test_four_pass_query_plan_returns_filtered_results` 작성.

**Step 2: Run failing tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/rag/test_pattern_collections.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_pattern_aware_retrieval.py`
Expected: FAIL

**Step 3: Implement collection layout + retrieval**

`shot_corpus`, `pattern_atoms`, `transition_rules`, `rights_constraints` 컬렉션 생성 및 4-pass 검색(semantic → rights filter → pattern rerank → transition rerank) 구현.

**Step 4: Run tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/rag/test_pattern_collections.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_pattern_aware_retrieval.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/rag/pattern_collections.py backend/app/rag/backends/qdrant_backend.py backend/tests/rag/test_pattern_collections.py backend/tests/services/test_pattern_aware_retrieval.py
git commit -m "feat(retrieval): add pattern-aware multi-collection qdrant query plan"
```

---

### Task 13: Pattern-aware 랭킹(v2) + clone_risk 게이트

**Files:**
- Modify: `backend/app/services/ad_ranking_service.py`
- Create: `backend/tests/services/test_ad_ranking_v2.py`
- Create: `backend/app/services/clone_risk_service.py`
- Create: `backend/tests/services/test_clone_risk_service.py`

**Step 1: Write failing tests**

`test_score_includes_pattern_affinity`, `test_block_when_clone_risk_exceeds_threshold` 작성.

**Step 2: Run failing tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_ranking_v2.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_clone_risk_service.py`
Expected: FAIL

**Step 3: Implement v2 scoring**

`final_score_v2` 수식(`pattern_affinity`, `clone_risk` 포함) 적용 + clone risk 임계치 초과 시 추천 제외.

**Step 4: Run tests**

Run:
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_ad_ranking_v2.py`
- `cd /Users/ted/vivid/backend && pytest -v tests/services/test_clone_risk_service.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/ad_ranking_service.py backend/app/services/clone_risk_service.py backend/tests/services/test_ad_ranking_v2.py backend/tests/services/test_clone_risk_service.py
git commit -m "feat(ranking): add pattern-affinity scoring and clone-risk guard"
```

---

## Delivery Definition of Done

- 권리 게이트 API가 pre/post 모두 동작
- OpenClaw 메모리 기반 문맥 검색 + Qdrant 샷 검색이 분리 동작
- continuity 하드 게이트가 실제 추천 결과에 반영
- Pattern Atom 추출/저장/검색/근거출력이 동작
- pattern_affinity와 clone_risk가 추천 랭킹에 반영
- Prompt Compiler 공통 계약이 엔진별 출력에 적용
- Agent0는 배치 작업 전용으로 안정 운영
- Telegram/Kakao/WebChat이 동일 ChannelEvent 계약으로 동작
- OpenClaw/Agent0 교체 리허설이 자동 점검 스크립트로 검증됨
- SSoT/인덱스/테스트 증거가 커밋에 포함

---

## Immediate Execution Checklist (30-Day Compression Plan)

### Day 0-2 (War-Room 세팅)

- [ ] Tiger Team 24/7 운영체계 확정 (Owner, 대체 담당, 승인권자)
- [ ] Codex 5.3 Terminal lane / Opus 4.6 review lane 분리
- [ ] PR 규칙: “하루 2회 통합, 기능 플래그 기본 ON/OFF”
- [ ] 핵심 대시보드: continuity/pattern_reuse/clone_risk/p95

**Exit Criteria**
- [ ] 첫 48시간 내 Task 1~3 머지 완료
- [ ] 계약 테스트(채널/메모리/워커) 파이프라인 동작

---

### Day 3-9 (Foundation Sprint)

- [ ] Rights Graph + Pre/Post Gate 운영 API 배포
- [ ] Qdrant 4-컬렉션 생성 및 인덱스 정책 고정
- [ ] OpenClawMemoryProvider + Agent0WorkerProvider 연결
- [ ] Masterpiece ingestion v0: 1,000클립 분절/태깅
- [ ] Pattern Atom 최소 스키마 + 저장 파이프라인

**Exit Criteria**
- [ ] pattern_atoms 2,000+ 적재
- [ ] Gate false-negative 0건 (테스트셋 기준)

---

### Day 10-16 (Intelligence Sprint)

- [ ] Pattern-aware ranking(v2) 활성화
- [ ] clone_risk 계산/차단 규칙 연결
- [ ] A/B + Thompson 실험 엔진 실트래픽 연결
- [ ] Prompt Compiler 4엔진 계약 고정
- [ ] 근거 출력(`evidence_refs`) 누락 차단

**Exit Criteria**
- [ ] continuity >= 0.80 추천 비율 55%+
- [ ] pattern_reuse_rate 20%+

---

### Day 17-23 (B2C Channel Sprint)

- [ ] Telegram + WebChat 안정화 (retry/dedupe/dead-letter)
- [ ] Kakao Adapter 베타 연결
- [ ] ChannelEvent v1 통합 검증
- [ ] 감독 피드백 루프(승인/수정/기각) 실시간 반영

**Exit Criteria**
- [ ] 파일럿 10팀 주 2회 이상 사용
- [ ] 채널별 이벤트 유실률 < 0.5%

---

### Day 24-30 (Launch Sprint)

- [ ] Vendor Switch Drill 1회 (OpenClaw/Agent0 대체 리허설)
- [ ] near-duplicate 차단 자동화 + 감사로그 검증
- [ ] 운영 런북/장애대응/권리분쟁 플레이북 완료
- [ ] Launch Candidate 승인 및 유료 파일럿 온보딩

**Exit Criteria**
- [ ] “2주 내 벤더 대체 가능” 증빙 리포트 완료
- [ ] 추천 API p95 < 2.5s, 검색 p95 < 900ms
- [ ] pattern 적용군 continuity uplift +0.08 달성
- [ ] 유료 전환 또는 LOI 확보

---

Plan complete and saved to `/Users/ted/vivid/docs/plans/2026-02-18-original-ip-foundry-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
