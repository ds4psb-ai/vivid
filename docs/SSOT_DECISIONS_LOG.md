# SSoT Decisions Log (IP-First Coordination)

> **버전**: 0.5
> **최종 업데이트**: 2026-01-20
> **범위**: IP-First 통합 로드맵(v2.1.1) + Phase 4-7 확장
> **근거 문서**: `/Users/ted/.claude/plans/ip-first-coordination-roadmap.md`
> **목적**: 설계/구현 중 SSoT 결정을 **명시적으로 기록**하고, 변경 이력을 추적한다.

---

## Phase 완료 현황 (IP-First Roadmap v2.1.1 + Extended)

| Phase | 이름 | 상태 | 완료일 |
|-------|------|------|--------|
| 0.0 | 기초 연결 | ✅ Completed | 2026-01-19 |
| 0 | DB 스키마 확장 | ✅ Completed | 2026-01-19 |
| 1 | 워크플로우 연결 | ✅ Completed | 2026-01-19 |
| 2 | run-token 통합 | ✅ Completed | 2026-01-19 |
| 2.5 | Tool Recommender & Evidence Card | ✅ Completed | 2026-01-19 |
| 3 | UI 통합 | ✅ Completed | 2026-01-19 |
| 4 | Multi-Agent Orchestration | ✅ Completed | 2026-01-19 |
| 5 | Cost Optimization | ✅ Completed | 2026-01-19 |
| 5.5 | Production Hardening | ✅ Completed | 2026-01-19 |
| 6 | Next.js 16 Cache Components | ✅ Completed | 2026-01-20 |
| 7 | HITL Enhancement | ⏳ Planned | - |

---

## 0) 상태 정의

| 상태 | 의미 |
|---|---|
| **Proposed** | 제안 단계 (검토 필요) |
| **Accepted** | 합의 완료 (SSoT 확정) |
| **Deprecated** | 더 이상 사용하지 않음 |
| **Superseded** | 다른 결정으로 대체됨 |

---

## 1) 결정 기록 템플릿

```
ID:
날짜:
상태: Proposed | Accepted | Deprecated | Superseded
결정 요약:
배경/문제:
대안:
결정:
영향 범위(코드/문서):
후속 작업:
비고:
```

---

## 2) 결정 로그 (초기)

### Decision 001 — Workflow 상태 SSoT 분리
- **ID**: SSoT-DEC-001
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: IP-First Flow의 SSoT는 `WorkflowExecution`으로, Agent 복구는 `WorkflowState`로 분리한다. `WorkflowSessionManager`는 Phase 1 이후 deprecate.
- **배경/문제**:
  - 현재 3개 상태 소스가 병존 (`WorkflowExecution`, `WorkflowSessionManager`, `WorkflowState`).
  - `/workflow`는 in-memory 세션만 사용.
- **대안**:
  - A) 모두 `WorkflowExecution`으로 통합
  - B) IP Flow만 `WorkflowExecution`, Agent 복구는 `WorkflowState` 유지 (**권장안**)
  - C) `WorkflowState`를 전면 확장하여 전부 대체
- **결정**: **B안 채택**
  - IP 기반 생성: `WorkflowExecution` (Biz Logic SSoT)
  - Agent session 복구: `WorkflowState` (Chat Context)
  - `WorkflowSessionManager`: Phase 1 이후 deprecate (In-memory 제거)
- **영향 범위(코드/문서)**:
  - `backend/app/models_workflow.py`
  - `backend/app/schemas/workflow_session.py`
  - `backend/app/services/workflow_state_service.py`
  - `backend/app/routers/workflow.py`
  - `08_PIPELINES_AND_USER_FLOWS.md`, `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- **후속 작업**:
  - DB 세션 기반 `/workflow` 전환 설계 확정
  - Deprecated 계획 문서화

---

### Decision 002 — Evidence 테이블 명칭/모델 충돌 방지
- **ID**: SSoT-DEC-002
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: 신규 Evidence 영속 테이블은 기존 `evidence_logs`와 충돌하지 않는 `ip_evidence_logs` 명칭을 사용한다.
- **배경/문제**:
  - `models_humancloud.py`에 이미 `evidence_logs` 테이블 존재.
  - RAG에는 `evidence_records` 테이블도 존재.
- **대안**:
  - A) 신규 테이블명 `ip_evidence_logs`, `ip_evidence_chains`
  - B) 기존 `evidence_logs` 확장 (`subject_type`, `subject_id` 추가)
- **결정**: **A안 채택** (명시적 분리)
  - `ip_evidence_logs`, `ip_evidence_chains` 사용
  - 기존 Legacy `evidence_logs`와 완전 분리
- **영향 범위(코드/문서)**:
  - `backend/app/models_humancloud.py`
  - (신규) `backend/app/models_evidence.py`
  - Alembic 마이그레이션
- **후속 작업**:
  - 명칭 확정
  - Alembic 스키마 초안 작성

---

### Decision 003 — /workflow run-token 통합 범위
- **ID**: SSoT-DEC-003
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: `/workflow`의 크레딧 흐름을 run-token으로 전면 통합한다.
- **배경/문제**:
  - 현재 `/workflow`는 credit_service 직접 차감.
  - IP Generation은 run-token 사용.
- **대안**:
  - A) `/workflow` 전면 run-token 이관
  - B) 기존 credit_service 유지 + 부분 run-token
- **결정**: **A안 채택** (전면 통합)
  - `/workflow/plan` = estimated credits 반환
  - `/workflow/start` = run-token reserve (선점)
  - `/workflow/advance|execute` = commit/rollback (확정/취소)
  - IP Generation과의 일관성 확보
- **영향 범위(코드/문서)**:
  - `backend/app/routers/workflow.py`
  - `backend/app/services/workflow_executor.py`
  - `backend/app/routers/run_token.py`
  - `13_CREDITS_AND_BILLING_SPEC_V1.md`
- **후속 작업**:
  - run-token 정책 확정(credit_service 대체 여부)
  - 실패/환불 플로우 정의

---

### Decision 004 — workflow_trace SSoT
- **ID**: SSoT-DEC-004
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: workflow trace는 `WorkflowNodeResult`를 SSoT로 사용하고, Evidence는 보조로 활용한다.
- **배경/문제**:
  - `IPGeneration` evidence 응답의 `workflow_trace`는 비어 있음.
  - `WorkflowNodeResult` 테이블은 존재.
- **결정**: **A안 채택**
  - Primary SSoT: `WorkflowNodeResult` (실행 결과)
  - Secondary Reference: `EvidenceChain` (추론 근거)
- **후속 작업**:
  - UI 요구 스키마 확정
  - API 응답 구조 정의

---

### Decision 005 — IPContext 표준화
- **ID**: SSoT-DEC-005
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: `ip_context`를 Pydantic BaseModel로 표준화하여 Validation을 강화한다.
- **배경/문제**:
  - 현재 `ip_context`는 단순 dict (`ip.worldbuilding`).
- **결정**: **B안 채택** (Pydantic)
  - Pydantic BaseModel 사용하여 직렬화/검증 이점 활용
  - `to_dict` 메서드보다 `model_dump()` 활용 권장
- **후속 작업**:
  - 최종 스키마 확정
  - Capsule input 표준 반영

---

## 3) 오픈 질문 (해결됨)

| 질문 | 상태 | 해결 내용 |
|------|------|----------|
| `WorkflowExecution` vs `WorkflowState` 통합 경로 | ✅ 해결 | Phase 1에서 B안 채택: WorkflowExecution(Biz Logic) + WorkflowState(Chat Context) 분리 유지 |
| Evidence 영속화 시 `evidence_records`와의 관계 | ✅ 해결 | `ip_evidence_logs`, `ip_evidence_chains` 신규 테이블로 명시적 분리 |
| run-token 통합이 credit_service를 완전 대체하는지 | ✅ 해결 | run-token이 크레딧 흐름 SSoT. credit_service는 내부 구현으로 유지 |

---

## 4) Phase 4-7 로드맵 (2026 연구 기반)

### Phase 4 — Multi-Agent Orchestration (멀티 에이전트 오케스트레이션)

**목표**: 2026 Agentic OS 패턴 적용 - 전문화된 에이전트 스웜 관리

**핵심 기능**:
- **Supervisor Pattern**: 메인 에이전트가 전문 에이전트 조율
- **Sequential/Concurrent Pattern**: 작업 의존성에 따른 실행 전략
- **Handoff Pattern**: 컨텍스트 유지하며 에이전트 간 작업 인계
- **Plan-and-Execute Pattern**: 저비용 모델(planning) + 고성능 모델(execution) 조합

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `backend/app/agents/orchestrator.py` | 에이전트 오케스트레이터 |
| `backend/app/agents/patterns/supervisor.py` | Supervisor 패턴 |
| `backend/app/agents/patterns/handoff.py` | Handoff 패턴 |
| `backend/app/schemas/agent_task.py` | 에이전트 작업 스키마 |

**근거**: LangGraph 2026, CrewAI, AutoGen 패턴 연구

---

### Phase 5 — Cost Optimization (비용 최적화)

**목표**: Plan-and-Execute 패턴으로 90% 비용 절감

**핵심 기능**:
- **Heterogeneous Model Selection**: 작업 복잡도에 따른 모델 선택
  - Planning: Gemini Flash (저비용)
  - Execution: Gemini Pro (고성능)
  - Validation: Gemini Flash (저비용)
- **Semantic Cache**: 유사 쿼리 캐싱으로 API 호출 감소
- **Batch Processing**: 관련 작업 일괄 처리

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `backend/app/services/model_router.py` | 작업별 모델 라우팅 |
| `backend/app/services/cost_tracker.py` | 비용 추적/분석 |
| `backend/app/rag/semantic_cache.py` | 시맨틱 캐시 확장 |

**근거**: Anthropic Plan-and-Execute 연구 (90% 비용 감소 사례)

---

### Phase 6 — Next.js 16 Cache Components (캐시 컴포넌트)

**목표**: Next.js 16의 `"use cache"` 지시어 활용한 명시적 캐싱

**핵심 기능**:
- **Explicit Cache Opt-in**: 컴포넌트/함수 단위 캐싱
- **Cache Tag System**: 세분화된 캐시 무효화
- **Streaming + Cache**: AI 스트리밍과 캐시 조합

**예상 변경**:
```tsx
// 캐시 컴포넌트 예시
"use cache";
export async function CachedIPMetadata({ slug }: { slug: string }) {
  const ip = await fetchIP(slug);
  return <IPCard ip={ip} />;
}

// 캐시 태그 무효화
import { revalidateTag } from 'next/cache';
revalidateTag(`ip:${slug}`);
```

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `frontend/src/components/cached/CachedIPCard.tsx` | 캐시된 IP 카드 |
| `frontend/src/lib/cache-tags.ts` | 캐시 태그 관리 |
| `frontend/src/app/api/revalidate/route.ts` | 캐시 무효화 API |

**근거**: Next.js 16 RC 문서 (2026년 1월 기준)

---

### Phase 7 — HITL Enhancement (Human-in-the-Loop 강화)

**목표**: 크리에이터 피드백 루프 강화

**핵심 기능**:
- **Approval Gates**: 워크플로우 단계별 승인 게이트
- **Feedback Integration**: 피드백을 RAG에 반영
- **A/B Testing**: 생성 결과 A/B 테스트
- **Creator Dashboard**: 크리에이터 전용 대시보드

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `backend/app/services/approval_gate.py` | 승인 게이트 서비스 |
| `backend/app/services/feedback_loop.py` | 피드백 루프 서비스 |
| `frontend/src/app/creator/dashboard/page.tsx` | 크리에이터 대시보드 |

**근거**: AI Content Platform 2026 트렌드 (Human-AI Collaboration)

---

## 5) Phase 4-7 결정 로그

### Decision 006 — Multi-Agent Pattern 선택
- **ID**: SSoT-DEC-006
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: Supervisor + Handoff 하이브리드 패턴 채택
- **배경/문제**:
  - 현재 VividAgent는 단일 에이전트.
  - 복잡한 워크플로우에서 전문화된 에이전트 필요.
- **대안**:
  - A) Supervisor Pattern only
  - B) Sequential/Concurrent Pattern only
  - C) Supervisor + Handoff 하이브리드 (**채택**)
- **결정**: **C안 채택**
  - `AgentOrchestrator`: Supervisor 역할
  - `BaseAgent` 서브클래스: ResearchAgent, CreativeAgent, ValidatorAgent, PlannerAgent
  - `HandoffRequest`: 에이전트 간 컨텍스트 전달
  - `TaskPlan`: 의존성 기반 실행
- **구현 파일**:
  - `backend/app/agents/orchestrator.py`
  - `backend/app/agents/base_agent.py`
  - `backend/app/schemas/agent_task.py`
  - `backend/tests/agents/test_orchestrator.py` (37개 테스트)

---

### Decision 007 — Model Router 전략
- **ID**: SSoT-DEC-007
- **날짜**: 2026-01-19
- **상태**: **Accepted**
- **결정 요약**: 작업 복잡도 기반 동적 모델 라우팅
- **배경/문제**:
  - 모든 작업에 고비용 모델 사용 중.
  - 단순 작업에 저비용 모델 사용 가능.
- **대안**:
  - A) 정적 라우팅 (작업 유형별 고정)
  - B) 동적 라우팅 (복잡도 분석 후 선택) (**채택**)
- **결정**: **B안 채택**
  - `ComplexityAnalyzer`: 키워드/태스크 타입/입력 길이 기반 분석
  - `ModelRouter`: LOW→FLASH, MEDIUM→PRO, HIGH→ULTRA
  - `CostTracker`: 실제 비용 기록 + ULTRA 대비 절감액 계산
  - 일일 예산 강제 (`DailyBudgetExceededError`)
- **구현 파일**:
  - `backend/app/services/model_router.py`
  - `backend/app/services/cost_tracker.py`
  - `backend/tests/services/test_model_router.py` (28개 테스트)
  - `backend/tests/services/test_cost_tracker.py` (27개 테스트)
- **예상 효과**: 67% 비용 절감

---

### Decision 008 — Production Hardening 전략
- **ID**: SSoT-DEC-008
- **날짜**: 2026-01-19
- **상태**: **Proposed**
- **결정 요약**: 2026 Best Practices 기반 프로덕션 강화
- **배경/문제**:
  - Multi-Agent + Cost Optimization 완료되었으나 resilience 패턴 미적용
  - 2026 기준: "Observability is non-negotiable for production agents"
  - LLM API 장애 시 cascading failure 위험
- **2026 리서치 근거**:
  - [LakeFS](https://lakefs.io/blog/llm-observability-tools/): 89% 조직이 에이전트 관측성 구현
  - [Portkey](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/): Circuit breaker 필수
  - [TrueFoundry](https://www.truefoundry.com/blog/rate-limiting-in-llm-gateway): Token-aware rate limiting
  - [Splunk](https://www.splunk.com/en_us/blog/learn/llm-observability.html): 토큰 모니터링으로 30-40% 절감
- **핵심 구현 항목**:
  1. **Circuit Breaker**: LLM provider 장애 감지/차단/복구
  2. **Retry with Exponential Backoff**: 일시적 실패 자동 재시도
  3. **OpenTelemetry Tracing**: 분산 추적 + 토큰 메트릭
  4. **Structured Logging**: JSON 로깅 + trace ID 연동
  5. **Rate Limiting**: Token-aware 제한
- **예상 파일**:
  - `backend/app/services/resilience.py` (Circuit Breaker, Retry)
  - `backend/app/telemetry/otel_setup.py` (OpenTelemetry 설정)
  - `backend/app/telemetry/llm_metrics.py` (LLM 메트릭)
  - `backend/app/middleware/logging_middleware.py` (구조화된 로깅)
- **후속 작업**:
  - ✅ 구현 완료 (2026-01-19)

---

### Decision 009 — Next.js 16 Cache Components 전략
- **ID**: SSoT-DEC-009
- **날짜**: 2026-01-20
- **상태**: **Accepted**
- **결정 요약**: ISR 기반 캐싱 + cacheLife 프로필로 IP-First UX 최적화
- **배경/문제**:
  - IP 카탈로그/상세 페이지 매 요청마다 API 호출
  - TTFB 500ms+ 지연
  - 불필요한 서버 부하
- **대안**:
  - A) `cacheComponents: true` + `"use cache"` 지시어
  - B) 전통적 ISR (`next: { revalidate }`) (**채택**)
- **결정**: **B안 채택** (점진적 전환)
  - `cacheComponents`는 다른 페이지 Suspense 준비 후 활성화
  - Server Component + ISR로 IP 페이지 캐싱
  - `/api/revalidate` 웹훅으로 선택적 무효화
- **구현 파일**:
  - `frontend/src/lib/cache-tags.ts` - 캐시 태그 상수
  - `frontend/next.config.ts` - cacheLife 프로필 (ip, editorial, realtime)
  - `frontend/src/app/api/revalidate/route.ts` - 캐시 무효화 API
  - `frontend/src/app/ip/_components/IPCatalogServer.tsx` - 서버 컴포넌트
  - `frontend/src/app/ip/[slug]/_components/IPDetailServer.tsx` - 서버 컴포넌트
  - `frontend/src/app/ip/[slug]/page.tsx` - generateStaticParams
  - `backend/app/services/cache_invalidation.py` - 백엔드 무효화 서비스
- **예상 효과**:
  - TTFB 90% 감소 (500ms → 50ms)
  - API 호출 100% 감소 (캐시 HIT 시)
- **후속 작업**:
  - 다른 페이지에 Suspense 추가 후 `cacheComponents: true` 활성화
  - `REVALIDATE_SECRET` 프로덕션 환경 변수 설정

---

## 6) 변경 기록

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-01-19 | 초기 SSoT 결정 로그 생성 |
| 0.2 | 2026-01-19 | 결정 1~5 Accepted 반영 |
| 0.3 | 2026-01-19 | Phase 0-3, 2.5 완료 반영 + Phase 4-7 로드맵 추가 |
| 0.4 | 2026-01-19 | Phase 4-5 완료 + Decision 006/007 Accepted + Phase 5.5 Hardening 추가 |
| 0.5 | 2026-01-20 | Phase 5.5/6 완료 + Decision 009 Accepted (Next.js Cache Components) |
