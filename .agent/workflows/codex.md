---
description: Codex 전용 워크플로우 (Validator + Executor) - Vivid 전용
---

# Codex 워크플로우 (Vivid 전용)

> 목적: **오버코딩 방지 + 리스크 최소화 + 빠른 품질 검증**

---

## 0. Always-On 모드 (기본값)

- **항상 시니어 개발자 시각**으로 판단한다.
- **ultrathink / think harder**를 기본으로 적용한다.
- 필요한 경우에만 추가 질문, 그렇지 않으면 바로 분석/리뷰를 제공한다.

---

## 1. Vivid 핵심 체크리스트 (P0)

### evidence_refs 타입
```python
# ✅ 올바름 - List[str]
evidence_refs = ["db:json_generator:shot_001", "db:rag_docs:AI:dataset:doc"]

# ❌ 틀림 - dict 배열
evidence_refs = [{"source": "...", "ref_id": "..."}]
```
**근거**: `backend/app/services/capsule_executor.py` L42

### Run-Token 흐름
```
issue() → 캡슐 실행 → deduct()/refund()
```
- `reserve_credits()`/`commit_credits()` 직접 호출 금지
**근거**: `backend/app/routers/run_token.py`

### ShotContract 매핑
- `IntentFactory`/`AestheticHints`로 상세 필드 매핑 금지
- 카메라/조명/캐릭터 → `ShotContract` 레벨에서 처리
**근거**: `backend/app/generation_client.py`

---

## 2. 기본 원칙

- **최소 변경**이 원칙 (필수 수정만)
- **기존 코드 재활용 우선**
- **DB 변경은 신중** (마이그레이션/백필/인덱스는 근거 필수)
- **리스크 먼저 보고** (P0/P1 우선순위)
- **검증 가능한 상태**로 마무리

---

## 3. 코드 리뷰 체크리스트

### P0 (즉시 수정)
- 데이터 무결성 깨짐 (FK/중복/덮어쓰기)
- `evidence_refs` 타입 불일치 (`List[str]` 아님)
- Run-Token 흐름 위반
- Sealed Capsule 원칙 위반 (프론트에서 LLM 직접 호출)
- 보안/권한/PII 노출

### P1 (권장 수정)
- `IntentFactory`/`AestheticHints` 오용 (→ ShotContract 사용)
- shot_type enum 정규화 누락
- 성능 병목 (N^2, 풀스캔, 불필요한 LLM 호출)
- 중복 로직/중앙화 누락

### P2 (향후 개선)
- 네이밍/표기 일관성
- 문서/테스트 보강
- 경량 리팩토링

---

## 4. Vivid 파이프라인 체크

### Generation Pipeline
```
Storyboard Cards → ShotContract → PromptContract → Gen Run (Veo/Kling)
```

### Dimension Tools 등록
```python
# TOOL_TO_DIMENSION 매핑 확인
TOOL_TO_DIMENSION: Dict[str, str] = {
    "generate_veo_prompt": "1D",
    "create_storyboard": "2D",
    ...
}
```

### RAG Suggestion 규칙
- `dataset_id` 필수
- `evidence_refs: List[str]` 형식
- confidence threshold 확인

---

## 5. 실행 워크플로우

### Step A. 상황 파악 (Read-only)
1. 관련 파일/경로 확인
2. 기존 로직/계약/스크립트 확인
3. 영향 범위 정리

### Step B. 스코프 확정
1. 반드시 고칠 것 (P0/P1)
2. 하면 좋은 것 (P2)
3. 이번 스프린트에서 **제외할 것**

### Step C. 수정 계획
- 변경 파일 목록
- 변경 요약 (왜/무엇)
- 리스크/롤백 방법

### Step D. 구현
- 작은 단위로 커밋 가능한 변경
- DB/스크립트는 **dry-run 우선**

### Step E. 검증
- 테스트/스크립트 실행 결과 요약
- 실패 시 원인/대안

---

## 6. DB/마이그레이션 가이드

- `alembic upgrade` 실패 시 **stamp 금지** (드리프트 위험)
- 테이블 존재 시: **원인 추적 → 마이그레이션 재작성 권장**
- 인덱스/확장은 `CREATE IF NOT EXISTS` 선호
- pgvector/HNSW는 **파라미터 근거** 명시

---

## 7. 웹 리서치 사용 원칙

다음 케이스는 웹 리서치 필수:
- DB/런타임 정책 변경 (PostgreSQL, Alembic)
- pgvector/embedding 베스트 프랙티스
- RAG/LLM 베스트 프랙티스 (RAGAS, TruLens)
- 보안/취약점/버전 이슈
- MCP/Copilot 최신 가이드

---

## 8. Codex 빠른 프롬프트

| 목적 | 프롬프트 |
|------|----------|
| 최소 패치 검토 | `필수 수정만 리스트업 해줘` |
| 에러 분석 | `원인-수정-재현 순서로 정리해줘` |
| 오버코딩 체크 | `기존 코드로 가능한지 먼저 봐줘` |
| 풀 감사 | `P0/P1/P2로 정렬해서 전수조사` |
| Vivid 규칙 체크 | `evidence_refs, run-token, ShotContract 규칙 위반 확인` |

기본값:
- 위 프롬프트를 쓰지 않아도 **항상 ultrathink/think harder 모드**로 동작한다.

---

## 9. 완료 기준

- P0 문제 모두 해결
- P1 리스크 명시
- 변경 파일/테스트 결과 요약
- 다음 단계 제시
- Vivid 핵심 규칙 (evidence_refs, run-token, ShotContract) 준수 확인

---

## 10. Vivid 핵심 파일 Quick Reference

| 영역 | 파일 |
|------|------|
| Shot/Prompt Contract | `backend/app/generation_client.py` |
| Dimension Tools | `backend/app/agents/dimension_tools.py` |
| Run Token | `backend/app/routers/run_token.py` |
| Capsule Executor | `backend/app/services/capsule_executor.py` |
| RAG Suggestion | `backend/app/rag/rag_suggestion_service.py` |
| Creative Intent | `backend/app/schemas/creative_intent.py` |
| Evidence Trace Spec | `docs/archive/24_CLAIM_EVIDENCE_TRACE_SPEC_V1.md` |
| Architecture | `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` |
