# Code Review Command

입력: $ARGUMENTS (PR 번호 또는 브랜치명, 비어있으면 현재 브랜치)

---

## 목적
현재 변경사항 또는 지정된 PR을 Vivid 규칙 기준으로 리뷰합니다.

---

## 워크플로우

### 1. 변경사항 수집

```bash
# 현재 브랜치 변경사항
git diff main...HEAD --stat
git diff main...HEAD

# PR인 경우
gh pr view $ARGUMENTS --json files,additions,deletions
gh pr diff $ARGUMENTS
```

### 2. Vivid 핵심 규칙 검사

#### P0 체크 (즉시 수정 필요)
- [ ] `evidence_refs` 타입이 `List[str]`인가?
- [ ] Run-Token 흐름 준수 (issue → execute → deduct/refund)?
- [ ] Sealed Capsule 원칙 (프론트에서 LLM 직접 호출 없음)?
- [ ] 보안/권한/PII 노출 없음?

#### P1 체크 (권장 수정)
- [ ] IntentFactory/AestheticHints 오용 → ShotContract 사용?
- [ ] shot_type enum 정규화?
- [ ] 성능 병목 (N^2, 풀스캔, 불필요한 LLM 호출)?

### 3. 코드 품질 검사

```bash
# Backend
cd backend && source venv/bin/activate
ruff check .
pyright

# Frontend
cd frontend
npm run lint
npm run build
```

### 4. 테스트 실행

```bash
# Backend
cd backend && pytest --tb=short -q

# Frontend (변경 영역에 따라)
cd frontend && npm run test:e2e
```

---

## 출력 형식

```markdown
# 코드 리뷰: [브랜치/PR 정보]

## 요약
- 변경 파일: X개
- 추가: +X줄, 삭제: -X줄
- P0 이슈: X개
- P1 이슈: X개

## P0 이슈 (즉시 수정)
1. `파일:라인` - 설명
   ```diff
   - 문제 코드
   + 수정 제안
   ```

## P1 이슈 (권장 수정)
1. `파일:라인` - 설명

## P2 이슈 (향후 개선)
1. 설명

## 테스트 결과
- Backend: ✅/❌
- Frontend Build: ✅/❌

## 잘된 점
- 설명

## 결론
- [ ] Approve / Request Changes / Comment
```

---

## 자동화 옵션

리뷰 후 자동 수정 적용:
```
/review --fix
```

PR에 코멘트 남기기:
```
/review PR_NUMBER --comment
```
