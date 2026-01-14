# SPEC Execute Command

입력: $ARGUMENTS (spec 파일명, e.g., "feature-name")

---

## 목적
SPEC 문서를 기반으로 정밀 구현. **새 세션에서 실행** (컨텍스트 분리).

---

## 사전 조건

- `.claude/specs/$ARGUMENTS.md` 존재
- SPEC 상태: `APPROVED`
- 인터뷰 세션과 분리된 새 세션

---

## 워크플로우

### 1. SPEC 파일 로드

```
.claude/specs/$ARGUMENTS.md 읽기
```

추출할 항목:
- 기능 요구사항 (FR-*)
- 비기능 요구사항 (NFR-*)
- 기술 설계 (파일별 변경사항)
- 테스트 계획

### 2. 태스크 분해

SPEC의 각 섹션을 개별 태스크로 변환:

```
□ Backend API 구현
  □ 라우터 생성
  □ 서비스 로직
  □ 스키마 변경
□ Frontend 구현
  □ 컴포넌트 생성
  □ API 연동
  □ 상태 관리
□ 테스트
  □ Unit tests
  □ Integration tests
□ 문서화
```

### 3. 순차 구현

각 태스크 완료 시:
1. SPEC 체크리스트 항목 ✅ 표시
2. 다음 태스크 진행

### 4. 자가 검증

구현 완료 후:
- SPEC의 모든 `[ ]` → `[x]`로 변경
- 누락된 항목 있으면 추가 구현

---

## 구현 가이드라인

### Backend
```
1. app/routers/ 에 라우터 추가
2. app/services/ 에 비즈니스 로직
3. app/models/ 에 스키마 (필요시)
4. tests/ 에 테스트 추가
```

### Frontend
```
1. src/components/ 에 컴포넌트
2. src/lib/api.ts 에 API 함수
3. src/app/ 에 페이지 (필요시)
```

---

## 완료 기준

- [ ] SPEC의 모든 FR-* 구현
- [ ] SPEC의 모든 NFR-* 충족
- [ ] 테스트 계획 완료
- [ ] SPEC 상태: `IMPLEMENTING` → `DONE`

---

## 다음 단계

```
구현 완료 후:
/spec-verify [feature-name]
```
