# Evidence Command

입력: $ARGUMENTS (옵션: --fix, --report)

---

## 목적
evidence_refs 사용 현황을 검증하고 위반 사항을 리포트합니다.

---

## evidence_refs 규칙 (P0)

### 올바른 형식

```python
# 올바름 - List[str]
evidence_refs: List[str] = [
    "db:capsule_runs:uuid-1234",
    "db:rag_docs:4D:video_ref:doc_001",
    "db:rag_docs:3D:image_grid:doc_002"
]
```

### 잘못된 형식

```python
# 틀림 - dict 배열
evidence_refs = [{"source": "...", "ref_id": "..."}]

# 틀림 - 단일 문자열
evidence_refs = "db:capsule_runs:uuid"

# 틀림 - prefix 누락
evidence_refs = ["capsule_runs:uuid"]  # "db:" 필요
```

---

## 워크플로우

### 1. 위반 검색

```bash
cd backend

# dict 패턴 (위반)
grep -rn "evidence_refs.*\[{" app/ --include="*.py"

# 올바른 패턴 확인
grep -rn "evidence_refs.*List\[str\]" app/ --include="*.py"

# evidence_refs 사용 위치 전체
grep -rn "evidence_refs" app/ --include="*.py"
```

### 2. 타입 검증

```bash
cd backend && source venv/bin/activate
pyright app/ --outputjson | jq '.generalDiagnostics[] | select(.message | contains("evidence_refs"))'
```

### 3. 테스트 실행

```bash
pytest tests/ -k "evidence" -v
```

---

## ref_id 형식

| 형식 | 설명 | 예시 |
|------|------|------|
| `db:capsule_runs:{uuid}` | CapsuleRun 기반 | `db:capsule_runs:abc-123` |
| `db:rag_docs:{dim}:{dataset}:{id}` | RAG 문서 | `db:rag_docs:4D:video_ref:doc_001` |

---

## 검증 체크리스트

1. **타입 검사**: `isinstance(evidence_refs, list)`
2. **요소 타입**: `all(isinstance(r, str) for r in evidence_refs)`
3. **Prefix 검사**: 모든 요소가 `db:` 또는 허용된 prefix로 시작
4. **형식 검사**: 콜론으로 구분된 올바른 세그먼트

---

## 출력 형식

```markdown
# evidence_refs 검증 리포트

## 요약
- 검사 파일: X개
- 올바른 사용: Y개
- 위반: Z개

## 위반 목록

### 파일: path/to/file.py:123
- **문제**: dict 배열 사용
- **현재**: `[{"source": "..."}]`
- **수정**: `["db:rag_docs:4D:video_ref:doc_001"]`

## 권장 조치
1. [ ] 위반 코드 수정
2. [ ] 테스트 실행
```

---

## UI 동작 규칙

| 조건 | UI 동작 |
|------|--------|
| `evidence_refs` 있음 | "AI 근거" 섹션 표시 |
| `evidence_refs` 없음 | 섹션 숨김 |
| `confidence < 0.5` | 섹션 기본 접힘 |
| refs > 3개 | "더보기" 버튼 |

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `app/rag/rag_suggestion_service.py` | evidence_refs 생성 |
| `app/services/capsule_executor.py` | CapsuleRun 기록 |
| `frontend/src/components/dimension/EvidenceDisplay.tsx` | UI 표시 |
| `docs/EVIDENCE_DISPLAY_UX.md` | UX 가이드 |
| `.claude/agents/evidence-checker.md` | 검증 서브에이전트 |
