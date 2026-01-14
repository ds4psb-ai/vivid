---
description: SPEC 검증 - 서브에이전트 패턴으로 SPEC 대비 구현 검증
---

# SPEC Verify Workflow

> **목적**: SPEC 문서 대비 구현 완료 여부 자동 검증
> **패턴**: Subagent Verification (Thariq Pattern)

// turbo-all

## 1. SPEC 파일 로드
```bash
cat docs/specs/[FEATURE_NAME].md
```

## 2. 요구사항 체크리스트 추출

SPEC에서 추출:
- 기능 요구사항 (FR-*)
- 비기능 요구사항 (NFR-*)
- 파일별 변경사항

## 3. 구현 검증

### 3.1 Backend API 검증
```bash
# 엔드포인트 존재 확인
grep -r "router\." backend/app/routers/ | grep -i [FEATURE] || echo "Not found"
```

### 3.2 Frontend 컴포넌트 검증
```bash
# 컴포넌트 존재 확인
find frontend/src/components -name "*[Feature]*" -o -name "*[feature]*" | head -10
```

### 3.3 테스트 존재 확인
```bash
# 테스트 파일 확인
find backend/tests frontend/e2e -name "*[feature]*" 2>/dev/null || echo "No tests found"
```

## 4. 테스트 실행
```bash
# Backend 테스트
cd backend && source venv/bin/activate && pytest tests/ -v -k [feature] --tb=short 2>&1 | tail -20
```

## 5. 타입체크 & 린트
```bash
# Backend
cd backend && source venv/bin/activate && ruff check app/ 2>&1 | tail -10

# Frontend
cd frontend && npm run lint 2>&1 | tail -10
```

## 6. 검증 리포트 생성

다음 형식으로 리포트 작성:

```markdown
# 검증 리포트: [FEATURE_NAME]

## 요약
- 전체 항목: X개
- 완료: Y개
- 미완료: Z개
- 완료율: XX%

## ✅ 완료된 항목
- FR-1: [설명]
- FR-2: [설명]

## ❌ 미완료 항목
- FR-3: [설명]
  - 누락 사항: [상세]
  - 수정 제안: [상세]

## 테스트 결과
- Unit: PASS/FAIL
- Integration: PASS/FAIL
- E2E: PASS/FAIL
```

## 7. 피드백 반영

미완료 항목이 있으면:
1. 추가 구현 진행
2. 다시 `/spec-verify [feature-name]`

## 8. 완료 시 커밋 & 푸시
```bash
git add . && git commit -m "feat: Complete [FEATURE_NAME] - verified against SPEC"
git push
```

---

**검증 통과 시**:
🎉 SPEC 검증 완료! PR 생성 또는 배포 진행
