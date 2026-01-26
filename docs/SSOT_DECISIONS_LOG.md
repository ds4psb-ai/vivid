# SSoT Decisions Log (IP-First Coordination)

> **버전**: 0.6
> **최종 업데이트**: 2026-01-26
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
| 7 | HITL Enhancement | ✅ Completed | 2026-01-20 |
| 8 | Advanced Personalization | ✅ Completed | 2026-01-20 |
| 9 | Monetization & Analytics | ✅ Completed | 2026-01-20 |
| 10 | Enterprise & Scale + IP Character Chat | ⏳ Planned | - |

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

### Decision 010 — HITL Enhancement 완료
- **ID**: SSoT-DEC-010
- **날짜**: 2026-01-20
- **상태**: **Accepted**
- **결정 요약**: 신뢰도 기반 승인 게이트 + 피드백 → RAG 파이프라인 완료
- **배경/문제**:
  - 워크플로우 결과물에 대한 품질 보증 메커니즘 부재
  - 사용자 피드백이 시스템 학습에 반영되지 않음
  - 크리에이터 성과 모니터링 도구 부재
- **2026 리서치 근거**:
  - [Parseur](https://parseur.com/blog/human-in-the-loop-ai): HITL AI Best Practices
  - [Permit.io](https://www.permit.io/blog/human-in-the-loop-for-ai-agents): HITL for AI Agents
  - [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework): 고위험 결정에 명시적 인간 감독
- **핵심 구현 항목**:
  1. **ApprovalGateService**: 신뢰도 기반 자동/수동 승인 라우팅
     - `confidence >= 0.85`: 자동 승인 (AUTO_APPROVED)
     - `confidence >= 0.50`: 수동 검토 (PENDING_REVIEW)
     - `confidence < 0.50`: 에스컬레이션 (ESCALATED)
  2. **FeedbackLoopService**: 피드백 → RAG 파이프라인
     - 긍정 피드백 (rating >= 4): Qdrant 인덱싱
     - 부정 피드백: 소스 플래깅 + 캐시 무효화 + CRAG 트리거
  3. **CreatorAnalyticsService**: 크리에이터 분석 + 이상 탐지
     - RPV (Revenue Per View) 메트릭
     - IQR 기반 이상 탐지 (평점 하락, 수정 급증, 납품 지연)
  4. **GenerationABService**: 생성 파라미터 A/B 테스트
- **구현 파일**:
  - Backend Services:
    - `backend/app/services/approval_gate.py` (승인 게이트)
    - `backend/app/services/feedback_loop.py` (피드백 루프)
    - `backend/app/services/creator_analytics.py` (크리에이터 분석)
    - `backend/app/experiments/generation_ab.py` (A/B 테스트)
  - Backend API:
    - `backend/app/routers/approval_gate.py`
    - `backend/app/routers/creator_dashboard.py`
  - Frontend:
    - `frontend/src/app/creator/dashboard/page.tsx`
    - `frontend/src/components/creator/*.tsx` (5개 컴포넌트)
  - Tests:
    - `backend/tests/services/test_approval_gate.py` (17개 테스트)
    - `backend/tests/services/test_feedback_loop.py` (12개 테스트)
    - `backend/tests/services/test_creator_analytics.py` (23개 테스트)
- **예상 효과**:
  - 품질 보증율 향상 (저신뢰도 결과물 자동 검토)
  - RAG 지식베이스 자동 학습 (피드백 기반)
  - 크리에이터 성과 가시성 확보

---

### Decision 011 — 18앱 → 3 메가앱 통합 (DNA 중심 구조)
- **ID**: SSoT-DEC-011
- **날짜**: 2026-01-26 (Updated)
- **상태**: **Accepted** ✅ 2026 트렌드 검증 완료
- **결정 요약**: 18개 산재된 Dimension 앱을 DNA 중심 3개 메가앱으로 통합
- **배경/문제**:
  - 18개 앱 중 완전 구현 7개, 부분 구현 8개, 미구현 3개
  - 2026 AI 영상 생성 모델(Veo 3.1, Sora 2 Pro, Kling 2.6) 발전으로 "공룡 API" 교체 용이성 필요
  - 거장 DNA + 영상 해석 데이터가 핵심 자산으로 분리 필요
- **대안**:
  - A) 기능 기반 5개 앱 (Video, Story, Visual, Audio, Character)
  - B) 파이프라인 기반 5개 앱 (Ideation → Visualization → Production)
  - C) 목적 기반 5개 앱 (Make Video, Write Story, etc.)
  - D) **DNA 중심 3개 앱** (DNA Lab, Story Engine, Production Bridge) — **채택**
- **결정**: **D안 채택** (DNA 중심 3-앱 구조)
  - 🧬 **DNA Lab**: AD + VPE(신규) + Mirror + QC → Logic Vector 생성
  - 📝 **Story Engine**: Story + Prompt(1D) → System Prompt 생성
  - 🎬 **Production Bridge**: VEO + Kling + Sora + Suno + Imagen → 공룡 API 래퍼
- **핵심 원칙**: "공룡 모델이 바뀌어도, 우리의 Logic Vector는 영원하다"
- **VPE (신규 모듈)**: 
  - Gemini 3 Pro 기반 마스터피스 영상 해석
  - Shot Grammar 추출: camera_grammar, lighting_physics, color_science
- **2026 트렌드 검증** (2026-01-26 웹 리서치):
  - ✅ Shot Grammar = 2026 업계 표준 프레임워크 확인
  - ✅ Logic Vector = 설계 유효, 경쟁 우위 유지
  - ✅ Provider Pattern = 추상화 필수 (모든 플랫폼 API 상이)
  - 🔄 Veo 3.1: Reference Images 3장, First/Last Frame 지원 → Phase 4.5
  - 🔄 Sora 2 Pro: Storyboard Mode, Caption Cards → 향후 통합
  - 🆕 Continuity Supervisor: Multimodal QA → Phase 6
- **근거 문서**: [MEGA_APP_ARCHITECTURE_2026.md](./MEGA_APP_ARCHITECTURE_2026.md) (v2.0)
- **Supersedes**: 
  - `unified_4layer_strategy.md` → `archive/strategic_2026_01/`
  - `story_first_architecture_roadmap.md` → `archive/strategic_2026_01/`
- **구현 로드맵**: (업데이트됨)
  - Phase 1: VPE 신규 구축 ✅ 완료
  - Phase 2: DNA Lab 통합 ✅ 완료
  - Phase 3: Story Engine 통합 ✅ 완료
  - Phase 4: Production Bridge ✅ 완료
  - **Phase 4.5: Schema Enhancement** 🔄 진행 (Reference Images, First/Last Frame)
  - Phase 5: Frontend 통합 ⏳ 대기
  - **Phase 6: Continuity Supervisor** 🆕 계획 (Multimodal QA)

---


### Phase 8 — Advanced Personalization (고급 개인화)

**목표**: 2026 Hyper-Personalization 패턴 적용 - 실시간 맞춤형 콘텐츠

**2026 리서치 근거**:
- 71% 소비자가 개인화된 상호작용 기대
- 76% 사용자가 개인화 부재 시 이탈
- Zero-Party Data + Predictive AI = 최적의 개인화

**핵심 기능**:
- **GraphRAG Integration**: 지식 그래프 기반 RAG 확장
  - 엔티티 관계 추론
  - 다중 홉 질의 지원
  - 컨텍스트 인식 검색
- **User Preference Learning**: 사용자 선호도 학습
  - 암묵적 신호 수집 (클릭, 체류시간, 스크롤)
  - Zero-Party Data 수집 (명시적 선호도)
  - 선호도 임베딩 생성
- **Predictive Content Suggestion**: 예측적 콘텐츠 제안
  - 다음 행동 예측
  - 선제적 도구 추천
  - 개인화된 RAG 힌트
- **Real-Time Adaptation**: 실시간 적응
  - 세션 내 선호도 업데이트
  - A/B 변형 실시간 선택

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `backend/app/rag/graph_rag.py` | GraphRAG 통합 |
| `backend/app/services/preference_learner.py` | 선호도 학습 |
| `backend/app/services/content_suggester.py` | 콘텐츠 제안 |
| `backend/app/models_user_preference.py` | 선호도 모델 |

---

### Phase 9 — Monetization & Analytics (수익화 및 분석)

**목표**: $205B 크리에이터 이코노미 최적화 - AI 기반 수익 분석

**2026 리서치 근거**:
- 크리에이터 이코노미 시장 $205B (2026)
- 84% 크리에이터가 AI 도구 활용
- AI 분석 도구로 평균 30% 수익 증가

**핵심 기능**:
- **Revenue Attribution**: 수익 기여도 분석
  - IP별 수익 추적
  - 도구별 ROI 분석
  - Fork 수익 분배 최적화
- **Engagement Analytics**: 참여도 분석
  - 콘텐츠 성과 대시보드
  - 오디언스 세그멘테이션
  - 트렌드 감지
- **Pricing Optimization**: 가격 최적화
  - 동적 크레딧 가격 책정
  - 수요 예측
  - 번들 추천
- **Creator Insights**: 크리에이터 인사이트
  - 경쟁 벤치마킹
  - 성장 기회 식별
  - 자동화된 보고서

**예상 파일**:
| 파일 | 목적 |
|------|------|
| `backend/app/services/revenue_attribution.py` | 수익 기여도 |
| `backend/app/services/engagement_analytics.py` | 참여도 분석 |
| `backend/app/services/pricing_optimizer.py` | 가격 최적화 |
| `frontend/src/app/analytics/page.tsx` | 분석 대시보드 |

---

### Phase 10 — Enterprise & Scale + IP Character Chat (엔터프라이즈 및 확장 + IP 캐릭터 채팅)

**목표**: 멀티테넌트 아키텍처 + IP 캐릭터 실시간 채팅 + 크리에이터 수익화

---

## 8) 경쟁사 분석: Caveduck.io (2026-01-20)

### 8.1 플랫폼 개요

**Caveduck** (caveduck.io) — Warp Space Inc. 개발, 2023년 출시

| 항목 | 상세 |
|------|------|
| 타입 | AI 캐릭터 채팅 플랫폼 |
| 태그라인 | "Create your own unique AI friend" |
| 주요 시장 | 한국, 일본, 동남아 |
| iOS 앱 | "Caveduck — Meet Your AI Friends" |

### 8.2 핵심 기능 (UI 분석)

**메인 피드**:
- 캐릭터 카드 그리드 (이미지 + 이름 + 설명 + 크리에이터)
- 필터 탭: 추천, 신작, 실시간 급상승, 인기, 태그
- 참여 메트릭: 조회수, 이미지 수, 좋아요
- #Original 배지 (오리지널 캐릭터 표시)
- 시즌 이벤트 (렛잇스노우)

**캐릭터 상세**:
- 캐릭터 프로필 + 상세 설명
- 태그 시스템 (여성, 오리지널, 힐링, 게임, 공모전 당선작 등)
- 시나리오 선택 (A/B 분기)
- 페르소나 설정 옵션
- 크리에이터 프로필 연결
- 공개일/수정일 표시
- 댓글 시스템

**채팅 인터페이스**:
- 도입 옵션 (시나리오 분기)
- 플레이 방법 가이드
- **멀티 모델 지원**:
  - 기본: Dino (자체 모델)
  - 고급: Claude 시리즈 (권장)
  - GPT-4 지원
  - Gemini 3 Pro (비권장으로 표시)
- 크리에이터 코멘트 섹션

### 8.3 수익 모델

| 티어 | 가격 | 혜택 |
|------|------|------|
| Free | 무료 | 일일 300포인트, 기본 캐릭터 접근 |
| PLUS | $11.99/월 (첫 결제 $5.99) | 무제한 기본 채팅, 음성, 고급 모델 |

**포인트 패키지**:
| 포인트 | 가격 | 보너스 |
|--------|------|--------|
| 5,000 | $4.99 | - |
| 10,000 | $9.99 | - |
| 30,900 | $29.99 | 3% |
| 52,500 | $49.99 | 5% |
| 107,000 | $99.99 | 7% |

**모델별 비용**:
- Haiku: 15포인트/응답 (저비용)
- Claude 3 Sonnet/GPT-4: 높은 비용 (창의적 응답)

**추천 시스템**: 양방향 1,000포인트 (유효기간 1년)

### 8.4 경쟁력 분석

**강점**:
1. 빠른 캐릭터 생성 (30초 이내)
2. 멀티 모델 선택권 (사용자 비용 최적화)
3. 공모전/크리에이터 인센티브
4. 이미지/음성/비디오 통합
5. 직관적 한국어 UI

**약점**:
1. 크리에이터 수익 분배 불투명
2. IP 라이선싱 체계 부재
3. 엔터프라이즈 기능 없음
4. API 미제공

### 8.5 Vivid 차별화 전략

| Caveduck | Vivid (Phase 10) |
|----------|------------------|
| 캐릭터 채팅 중심 | **IP-First 생태계** (캐릭터 + 콘텐츠 생성) |
| 포인트 과금 | **Fork 수익 분배 (60/30/10)** |
| 크리에이터 귀속 표시 | **IP 라이선싱 마켓플레이스** |
| 단일 채팅 | **워크플로우 + 채팅 통합** |
| 소비자 중심 | **B2B + B2C 하이브리드** |

---

## 9) 2026 시장 리서치

### 9.1 AI 컴패니언 시장 규모

| 연도 | 시장 규모 | 출처 |
|------|----------|------|
| 2026 | $501B | Business Research Insights |
| 2033 | $970B | Precedence Research |
| CAGR | 36.6% | - |

### 9.2 주요 경쟁사 비교

| 플랫폼 | MAU | 특징 | 수익 모델 |
|--------|-----|------|----------|
| Character.AI | 20M+ | 8.18 페이지/세션 | $9.99/월 Plus |
| SpicyChat | 2M | 850K+ 캐릭터 | $14.95/월 True Supporter |
| JanitorAI | 5M+ | 무료 + API | OpenRouter 과금 |
| Caveduck | 1M+ | 한국 중심 | $11.99/월 PLUS |

### 9.3 NSFW vs SFW 비교

| 메트릭 | NSFW 플랫폼 | SFW 플랫폼 |
|--------|------------|-----------|
| 월 평균 지출 | $24.99 | $9.99 |
| 월간 리텐션 | 80% | 40% |
| 전환율 | 8-12% | 3-5% |

### 9.4 크리에이터 이코노미 (2026)

- 글로벌 규모: **$250B** (2027년 $500B 전망)
- AI 도구 채택률: **84%**
- 수익 증가 효과: **30%** (AI 분석 도구 사용 시)

### 9.5 멀티테넌트 AI 아키텍처 트렌드

**2026 Best Practices**:
1. **테넌트 격리**: Shared schema + tenant ID (가장 일반적)
2. **AI 모델 접근**: Hub-Spoke 패턴 (중앙 AI + 테넌트 커스텀)
3. **보안**: Zero-trust + 테넌트 컨텍스트 인젝션
4. **규제**: EU AI Act, HIPAA, SOC 2 준수 필수

### 9.6 실시간 채팅 아키텍처 (2026)

**핵심 패턴**:
1. **WebSocket + Redis Pub/Sub**: 서버 간 조정
2. **Event-Driven**: 240K 동시 연결/노드 (sub-50ms 레이턴시)
3. **Sticky Sessions**: 세션 상태 관리
4. **Microservices**: Chat/Presence/Notification 분리

### 9.7 음성 AI 기술 (2026)

**주요 기술**:
- **WebRTC Real-Time API**: OpenAI Realtime API 직접 연결
- **Voice Cloning**: 5초 샘플로 복제 (Chatterbox, ElevenLabs)
- **Zero-Shot TTS**: sub-200ms 스트리밍 레이턴시
- **Fish Audio**: 70+ 언어, 1000+ 음성

---

## 10) Phase 10 상세 설계 (Enterprise & Scale + IP Character Chat)

### 10.1 목표

1. **멀티테넌트 아키텍처**: Hub-Spoke 패턴으로 B2B 확장
2. **IP 캐릭터 채팅**: Caveduck 대비 차별화된 실시간 채팅
3. **크리에이터 마켓플레이스**: IP 라이선싱 + 수익 분배
4. **음성 채팅**: WebRTC + Voice Cloning
5. **수평 확장**: Kubernetes 오토스케일링

### 10.2 핵심 기능 설계

#### 10.2.1 IP Character Chat

```
┌─────────────────────────────────────────────────────────┐
│                    IP Character Chat                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ IP Registry  │───▶│ Character    │───▶│ Chat      │ │
│  │ (캐릭터 DB)   │    │ Personality  │    │ Session   │ │
│  │              │    │ (RAG + Prompt)│    │ (Redis)   │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
│          │                  │                  │        │
│          ▼                  ▼                  ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ Visual       │    │ Model Router │    │ WebSocket │ │
│  │ Generator    │    │ (Claude/GPT) │    │ + SSE     │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
└─────────────────────────────────────────────────────────┘
```

**특징**:
- IP 기반 캐릭터 페르소나 (RAG에서 월드빌딩 컨텍스트 주입)
- 시나리오 분기 (A/B 선택지)
- 다중 모델 선택 (비용/품질 트레이드오프)
- 이미지/음성/비디오 응답 통합
- 대화 기록 영속화 (세션 복구)

#### 10.2.2 Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                          │
├─────────────────────────────────────────────────────────┤
│                   Tenant Middleware                      │
│   ┌──────────────────────────────────────────────────┐  │
│   │ - X-Tenant-Id 헤더 검증                           │  │
│   │ - JWT 테넌트 클레임 추출                          │  │
│   │ - Rate Limiting (테넌트별)                        │  │
│   │ - Usage Metering                                 │  │
│   └──────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│   ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │
│   │ Tenant A  │  │ Tenant B  │  │ Shared AI Hub     │  │
│   │ (Data)    │  │ (Data)    │  │ (LLM + RAG)       │  │
│   └───────────┘  └───────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**격리 전략**:
- **Database**: Schema-per-tenant (PostgreSQL schemas)
- **Redis**: Key prefix (`tenant:{id}:*`)
- **Qdrant**: Collection-per-tenant
- **S3**: Bucket prefix (`s3://vivid/{tenant_id}/`)

#### 10.2.3 Voice Chat (Phase 10.5)

```
┌─────────────────────────────────────────────────────────┐
│                    Voice Chat Flow                       │
├─────────────────────────────────────────────────────────┤
│  User Mic ──▶ WebRTC ──▶ STT ──▶ LLM ──▶ TTS ──▶ Speaker│
│              (Opus)     (Whisper) (Claude) (Voice Clone)│
│                                                         │
│  Voice Clone Options:                                   │
│  - ElevenLabs (상용)                                    │
│  - Chatterbox (오픈소스, sub-200ms)                     │
│  - Fish Audio (70+ 언어)                                │
└─────────────────────────────────────────────────────────┘
```

#### 10.2.4 Creator Marketplace

| 기능 | 설명 |
|------|------|
| IP 등록 | 캐릭터 + 월드빌딩 + 스토리 |
| 라이선스 티어 | Free / Commercial / Exclusive |
| 수익 분배 | 크리에이터 60% / 플랫폼 30% / Fork 원작자 10% |
| 어트리뷰션 | 사용 추적 + 로열티 정산 |
| 공모전 | 주기적 테마 공모 + 상금 |

### 10.3 예상 파일 구조

**Backend (신규)**:

| 파일 | 목적 |
|------|------|
| `app/middleware/tenant_middleware.py` | 테넌트 격리 미들웨어 |
| `app/services/tenant_service.py` | 테넌트 CRUD + 프로비저닝 |
| `app/services/ip_chat_service.py` | IP 캐릭터 채팅 서비스 |
| `app/services/character_personality.py` | 캐릭터 페르소나 + RAG 주입 |
| `app/services/voice_chat_service.py` | WebRTC 음성 채팅 |
| `app/services/ip_marketplace_service.py` | IP 마켓플레이스 서비스 |
| `app/routers/tenant.py` | 테넌트 관리 API |
| `app/routers/ip_chat.py` | IP 채팅 API + WebSocket |
| `app/routers/voice.py` | 음성 채팅 API |
| `app/routers/marketplace.py` | 마켓플레이스 API |
| `app/models_tenant.py` | 테넌트 모델 |
| `app/models_ip_chat.py` | 채팅 세션/메시지 모델 |

**Frontend (신규)**:

| 파일 | 목적 |
|------|------|
| `src/app/chat/[characterId]/page.tsx` | IP 캐릭터 채팅 페이지 |
| `src/app/marketplace/page.tsx` | IP 마켓플레이스 |
| `src/components/chat/ChatInterface.tsx` | 채팅 인터페이스 |
| `src/components/chat/VoiceControl.tsx` | 음성 채팅 컨트롤 |
| `src/components/marketplace/IPCard.tsx` | IP 카드 컴포넌트 |
| `src/hooks/useChat.ts` | 채팅 WebSocket 훅 |
| `src/hooks/useVoiceChat.ts` | 음성 채팅 훅 |

**Infrastructure**:

| 파일 | 목적 |
|------|------|
| `infrastructure/k8s/deployment.yaml` | K8s 배포 설정 |
| `infrastructure/k8s/hpa.yaml` | 수평 오토스케일링 |
| `infrastructure/k8s/ingress.yaml` | 인그레스 설정 |
| `infrastructure/terraform/` | IaC 설정 |

### 10.4 DB 스키마 (마이그레이션 028)

```sql
-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    plan VARCHAR(32) DEFAULT 'free',  -- free, starter, pro, enterprise
    settings JSONB DEFAULT '{}',
    api_key_hash VARCHAR(256),
    usage_limits JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- IP Characters (확장)
ALTER TABLE ip_registry ADD COLUMN chat_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE ip_registry ADD COLUMN persona_prompt TEXT;
ALTER TABLE ip_registry ADD COLUMN voice_id VARCHAR(64);  -- ElevenLabs/Chatterbox voice ID
ALTER TABLE ip_registry ADD COLUMN scenario_branches JSONB DEFAULT '[]';

-- Chat Sessions
CREATE TABLE ip_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(160) NOT NULL,
    ip_id UUID REFERENCES ip_registry(id),
    character_state JSONB DEFAULT '{}',  -- 캐릭터 상태
    scenario_branch VARCHAR(64),  -- 현재 시나리오
    model_preference VARCHAR(32) DEFAULT 'flash',  -- flash, pro, opus
    total_messages INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    last_message_at TIMESTAMP
);
CREATE INDEX ix_chat_session_user ON ip_chat_sessions(user_id, last_message_at DESC);

-- Chat Messages
CREATE TABLE ip_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ip_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    media_urls JSONB DEFAULT '[]',  -- 이미지/음성/비디오 URL
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER,
    model_used VARCHAR(32),
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX ix_chat_message_session ON ip_chat_messages(session_id, created_at);

-- IP Marketplace Listings
CREATE TABLE ip_marketplace_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID REFERENCES ip_registry(id),
    creator_id VARCHAR(160) NOT NULL,
    license_type VARCHAR(32) NOT NULL,  -- free, commercial, exclusive
    price_credits INTEGER DEFAULT 0,
    royalty_percent FLOAT DEFAULT 0.1,  -- Fork 시 로열티
    downloads INTEGER DEFAULT 0,
    revenue_total INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT FALSE,
    contest_winner BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX ix_marketplace_featured ON ip_marketplace_listings(featured, downloads DESC);
```

### 10.5 구현 순서

| 순서 | 작업 | 의존성 | 우선순위 |
|------|------|--------|----------|
| 1 | DB Migration (028) | - | P0 |
| 2 | IP Chat Session/Message 모델 | 1 | P0 |
| 3 | IP Chat Service (텍스트) | 2 | P0 |
| 4 | Chat WebSocket Router | 3 | P0 |
| 5 | Frontend Chat UI | 4 | P0 |
| 6 | Marketplace Listings 모델 | 1 | P1 |
| 7 | Marketplace Service | 6 | P1 |
| 8 | Frontend Marketplace | 7 | P1 |
| 9 | Tenant Middleware | - | P1 |
| 10 | Tenant Service | 9 | P1 |
| 11 | Voice Chat Integration | 4 | P2 |
| 12 | K8s 배포 설정 | All | P2 |

### 10.6 성능 목표

| 메트릭 | 목표 |
|--------|------|
| Chat 첫 토큰 지연 | < 500ms |
| WebSocket 연결 | < 100ms |
| 동시 채팅 세션 | 10K/노드 |
| 음성 응답 지연 | < 2s (E2E) |
| Marketplace 검색 | < 200ms |

### 10.7 Caveduck 대비 차별화 포인트

| 기능 | Caveduck | Vivid Phase 10 |
|------|----------|----------------|
| 채팅 | 단순 텍스트 | **IP 컨텍스트 + RAG 기반** |
| 크리에이터 수익 | 불투명 | **60/30/10 투명 분배** |
| 콘텐츠 생성 | 채팅만 | **채팅 + 이미지/비디오/오디오 생성** |
| B2B | 없음 | **멀티테넌트 화이트라벨** |
| API | 미제공 | **Public API + SDK** |
| 음성 | 기본 TTS | **Voice Cloning + WebRTC** |

---

## 11) Decision 011 — Phase 10 전략 채택

- **ID**: SSoT-DEC-011
- **날짜**: 2026-01-20
- **상태**: **Proposed**
- **결정 요약**: IP Character Chat + Multi-Tenant + Marketplace 통합 전략 채택
- **배경/문제**:
  - Caveduck 등 AI 캐릭터 채팅 시장 급성장 ($501B, 2026)
  - 현재 Vivid는 콘텐츠 생성 중심, 채팅 기능 부재
  - B2B 확장을 위한 멀티테넌트 아키텍처 필요
- **대안**:
  - A) 채팅만 추가 (Caveduck 클론)
  - B) 엔터프라이즈만 추가 (B2B 집중)
  - C) **IP Chat + Marketplace + Enterprise 통합** (채택)
- **결정**: **C안 채택**
  - IP-First 전략과 일관성 유지
  - 크리에이터 수익화 강화 (마켓플레이스)
  - B2B 확장 기반 마련 (멀티테넌트)
- **리스크**:
  - 구현 복잡도 높음 → 단계별 출시 (P0/P1/P2)
  - 경쟁 심화 → IP 컨텍스트 차별화
- **후속 작업**:
  - Phase 10 구현 시작
  - Caveduck 지속 모니터링

---

## 12) 리서치 출처

### 경쟁사 분석
- [Caveduck Review - FindMyAITool](https://findmyaitool.io/tool/caveduck/)
- [Caveduck AI Review 2025 - Skywork](https://skywork.ai/blog/caveduck-ai-review-2025-features-safety-cost/)
- [Character.AI Statistics - Business of Apps](https://www.businessofapps.com/data/character-ai-statistics/)

### 시장 리서치
- [AI Companion Market 2026 - Companion Guide](https://companionguide.ai/news/ai-companion-market-120m-revenue)
- [Creator Economy 2026 - Digiday](https://digiday.com/marketing/in-graphic-detail-heres-what-the-creator-economy-is-expected-to-look-like-in-2026/)
- [AI Companion Market Size - Precedence Research](https://www.precedenceresearch.com/ai-companion-market)

### 기술 아키텍처
- [Multi-Tenant AI on AWS](https://aws.amazon.com/blogs/machine-learning/build-a-multi-tenant-generative-ai-environment-for-your-enterprise-on-aws/)
- [Agentic AI Multi-Tenant - AWS](https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/agentic-ai-multitenant/agentic-ai-multitenant.pdf)
- [Real-Time AI Chat Infrastructure - Render](https://render.com/articles/real-time-ai-chat-websockets-infrastructure)
- [WebSocket Architecture - Ably](https://ably.com/topic/websocket-architecture-best-practices)

### IP/마켓플레이스
- [Kamoto.AI - Create & Monetize AI Characters](https://www.kamoto.ai/)
- [IP Licensing Legal Guide - Promise Legal](https://blog.promise.legal/startup-central/licensing-your-characters-to-generative-ai-platforms-a-legal-governance-checklist-for-studios-and-ai-companies/)

### 음성 기술
- [Voice Chat AI - GitHub](https://github.com/bigsk1/voice-chat-ai)
- [Chatterbox AI](https://chatterboxai.net/)
- [ElevenLabs Voice Cloning](https://elevenlabs.io/voice-cloning)

---

## 7) 변경 기록

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-01-19 | 초기 SSoT 결정 로그 생성 |
| 0.2 | 2026-01-19 | 결정 1~5 Accepted 반영 |
| 0.3 | 2026-01-19 | Phase 0-3, 2.5 완료 반영 + Phase 4-7 로드맵 추가 |
| 0.4 | 2026-01-19 | Phase 4-5 완료 + Decision 006/007 Accepted + Phase 5.5 Hardening 추가 |
| 0.5 | 2026-01-20 | Phase 5.5/6 완료 + Decision 009 Accepted (Next.js Cache Components) |
| 0.6 | 2026-01-20 | Phase 7 완료 + Decision 010 Accepted (HITL Enhancement) + Phase 8-10 로드맵 추가 |
| 0.7 | 2026-01-20 | Phase 8 완료 (Advanced Personalization) |
| 0.8 | 2026-01-20 | Phase 9 완료 (Monetization & Analytics) |
| 0.9 | 2026-01-20 | Phase 10 상세 계획 + 경쟁사 분석 + 2026 리서치 추가 |
