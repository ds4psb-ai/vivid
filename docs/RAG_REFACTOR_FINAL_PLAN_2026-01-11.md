# 최종 RAG 리팩토링 플랜 (Codex 분석 + 보완 통합)

> **Type**: Technical Design Document (Reference)
> **Status**: Finalized
> **Created**: 2026-01-11
> **Related**: [RAG Execution Plan](./RAG_NEXT_PHASE_PLAN_2026-01-11.md) | [RAG Reliability](./RAG_RELIABILITY.md)

**Scope**: Hybrid RAG 경량화, 관측성 보강, 레거시 정리
**Principle**: 모놀리식 유지 + 모듈 경계 강화 (분리 최소화)

---

## 1) 합의된 핵심 결론 (최종 권고)

| 항목 | 최종 결정 | 이유 |
| --- | --- | --- |
| Microservices | 구조 철학만 반영, 실제 분리는 보류 | 현재 규모에선 모듈 경계가 ROI가 높음 |
| Router 위치 | `hybrid_rag.py` 내 inline | 별도 `router.py`는 오버엔지니어링 |
| 전략 결정 | score 기반 heuristic | LangGraph 없이도 충분 |
| circuit open | Vertex 직행 | 이미 구현됨, 안정성 확보 |
| rag_cache | 3줄 shim로 단순화 | 책임 축소, 제거 용이 |
| 전역 기본값 | `rag_presets.py` 확장 | 별도 YAML 로딩 복잡도 방지 |
| Metrics | 데코레이터 패턴 | 경로 누락 방지 |

---

## 2) 최종 설계 방향 (코드 위치 확정)

### 2.1 Router는 `hybrid_rag.py` 상단에 inline
- 파일: `backend/app/rag/hybrid_rag.py`
- 추가 함수:
  - `_determine_strategy(query, auteur_key, dimension, use_google_search) -> (strategy, use_reranker, force_grounding)`
- 기본 규칙 (최소한의 분기):
  - 길이 > 120 → score +1
  - 최신성 키워드 포함 → score +1
  - dimension이 story/4d → score +1
  - auteur_key 존재 → `auteur_first`
  - score >= 2 → `hybrid + rerank`
  - score >= 3 → grounding 강제

### 2.2 Metrics는 데코레이터로 통일
- 파일: `backend/app/rag/metrics.py`
- 추가 데코레이터:
  - `@track_rag_operation("notebooklm_query")`
  - `@track_rag_operation("vertex_query")`
- 적용 위치:
  - `_query_auteur_first`, `_query_dimension`, `_query_parallel`

### 2.3 rag_cache는 shim으로 최소화
- 파일: `backend/app/rag/rag_cache.py`
- 기존 클래스 제거, 3줄 함수로 교체:
  - `get_or_query()` → `hybrid_query()`로 direct proxy

### 2.4 전역 기본값은 `rag_presets.py`에서 관리
- 파일: `backend/app/rag/rag_presets.py`
- 추가:
  - `DEFAULT_RAG_CONFIG = {...}`
  - `get_preset(app_key, yaml_config) -> merged config`
- YAML override는 이 기본값을 덮어쓰기

### 2.5 Semantic Cache 메트릭 연동
- 파일: `backend/app/rag/semantic_cache.py`
- `get/set` 흐름에 `record_semantic_cache_op()` 호출 추가

---

## 3) 변경 사항 상세 (파일별)

### A. `backend/app/rag/hybrid_rag.py`
- [추가] `_determine_strategy()`
- [변경] `hybrid_query()`에서 strategy/grounding/rerank 결정
- [유지] CRAG logic (confidence < 0.5) 유지

### B. `backend/app/rag/metrics.py`
- [추가] 데코레이터 `track_rag_operation()`
- [효과] 실패율 기록 누락 방지 (record_rag_error 자동 호출)

### C. `backend/app/rag/rag_cache.py`
- [변경] shim 함수 1개만 유지
- [효과] 레거시 유지 비용 최소화

### D. `backend/app/rag/rag_presets.py`
- [추가] DEFAULT_RAG_CONFIG
- [추가] `get_preset(app_key, yaml_config)`
- [효과] 전역 기본값 + YAML override 통합

### E. `backend/app/rag/semantic_cache.py`
- [변경] `record_semantic_cache_op()` 연결
- [효과] hit/miss/latency 실측 가능

---

## 4) 실행 순서 (ROI 기준)

| 순서 | 작업 | 예상 시간 | ROI |
| --- | --- | --- | --- |
| 1 | `_determine_strategy()` 추가 | 30분 | ★★★★★ |
| 2 | `rag_cache.py` shim 전환 | 15분 | ★★★★☆ |
| 3 | `@track_rag_operation` 데코레이터 | 45분 | ★★★★☆ |
| 4 | `DEFAULT_RAG_CONFIG` 추가 | 20분 | ★★★☆☆ |
| 5 | Semantic Cache 메트릭 호출 | 15분 | ★★★☆☆ |

---

## 5) 검증/테스트 체크리스트

- Backend 테스트 (RAG 안정성 스모크)
  - `cd backend && pytest -v tests/e2e/test_rag_reliability.py`
- Dimension RAG 동작 스모크
  - `cd backend && pytest -v tests/routers/test_dimension_sse.py`

---

## 6) 리스크 & 가드레일

- NotebookLM 실 ID 미완료
  - `backend/app/rag/tier0_notebooklm.py`
  - Tarantino PENDING, Park/Shinkai SIMULATION
- rag_cache 경로 여전히 사용 중
  - `backend/app/routers/dimension/_base.py`
  - `backend/app/agents/notebooklm_tools.py`
  - `backend/app/agents/dimension_tools.py`
  - `backend/app/routers/health.py`

---

## 7) 완료 기준 (Exit Criteria)

- `_determine_strategy()`로 전략 결정이 일원화됨
- rag_cache 호출이 shim으로만 남음
- semantic_cache hit/miss/latency가 Prometheus로 수집됨
- 오류 메트릭(record_rag_error)이 누락 없이 기록됨

---

## 8) 다음 단계 (필요 시)

- Router 복잡도 증가 시 `router.py` 분리
- YAML 전역 config 도입 여부 재검토
- NotebookLM notebook ID 업로드 완료 후 실호출률 재측정

