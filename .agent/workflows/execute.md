---
description: SPEC 실행 - 명세서 기반 정밀 구현 (새 세션에서 실행)
---

# SPEC Execute Workflow

> **목적**: SPEC 문서 기반 정밀 구현
> **전제조건**: 새 세션에서 실행 (컨텍스트 분리)

// turbo-all

## 1. SPEC 파일 로드
```bash
cat docs/specs/[FEATURE_NAME].md
```

## 2. 요구사항 추출

SPEC에서 체크리스트 추출:
- 기능 요구사항 (FR-*)
- 비기능 요구사항 (NFR-*)
- 파일별 변경사항
- 테스트 계획

## 3. Backend 구현

### 3.1 라우터 생성/수정
```bash
# 관련 라우터 확인
ls -la backend/app/routers/
```

### 3.2 서비스 로직
```bash
# 관련 서비스 확인
ls -la backend/app/services/
```

### 3.3 스키마/모델
```bash
# 스키마 파일 확인
ls -la backend/app/schemas/ backend/app/models/
```

## 4. Frontend 구현

### 4.1 컴포넌트 생성
```bash
# 관련 컴포넌트 확인
ls -la frontend/src/components/
```

### 4.2 API 연동
```bash
# API 파일 확인
cat frontend/src/lib/api.ts | head -50
```

## 5. 테스트 작성
```bash
# 테스트 파일 위치
ls -la backend/tests/ frontend/e2e/
```

## 6. 린트 & 타입체크
```bash
cd backend && source venv/bin/activate && ruff check app/ --fix
cd ../frontend && npm run lint
```

## 7. SPEC 체크리스트 업데이트

구현 완료 후 SPEC 파일의 체크박스 업데이트:
- `[ ]` → `[x]` 변경
- 상태: `IMPLEMENTING` → `DONE`

## 8. 커밋
```bash
git add . && git status
git commit -m "feat: Implement [FEATURE_NAME] per SPEC"
```

---

**다음 단계**:
`/spec-verify [feature-name]` 로 검증 진행
