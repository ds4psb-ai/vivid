# SSoT Decisions Log (IP-First Coordination)

> **버전**: 0.2  
> **최종 업데이트**: 2026-01-19  
> **범위**: IP-First 통합 로드맵(v2.1.1) 기반 SSoT 결정 기록  
> **근거 문서**: `/Users/ted/.claude/plans/ip-first-coordination-roadmap.md`  
> **목적**: 설계/구현 중 SSoT 결정을 **명시적으로 기록**하고, 변경 이력을 추적한다.

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

## 3) 오픈 질문
- `WorkflowExecution` vs `WorkflowState` 통합 경로 최종 결정은 언제 승인할지?
- Evidence 영속화 시 `evidence_records`와의 관계는 어떻게 정의할지?
- run-token 통합이 credit_service를 완전 대체하는지 여부?

---

## 4) 변경 기록

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-01-19 | 초기 SSoT 결정 로그 생성 |
| 0.2 | 2026-01-19 | 결정 1~5 Accepted 반영 |
