# SPEC Interview Command

입력: $ARGUMENTS (기능 설명)

---

## 목적
Thariq 방법론 기반 심층 인터뷰로 상세 SPEC 문서 작성.
**뻔한 질문 금지** - 엣지 케이스와 트레이드오프에 집중.

---

## 워크플로우

### 1. 초기 컨텍스트 수집
```
관련 파일 탐색:
- backend/app/routers/ (API)
- backend/app/services/ (비즈니스 로직)
- frontend/src/components/ (UI)
- 기존 유사 기능 패턴 파악
```

### 2. 심층 인터뷰 진행

**질문 영역** (각 영역 3-5개 질문):

#### 기술 구현
- API 엔드포인트 설계 (REST? GraphQL?)
- 데이터 모델/스키마 변경사항
- 기존 RAG/Dimension 시스템 연동
- 비동기 처리 필요성

#### UI/UX
- 화면 흐름과 사용자 시나리오
- 로딩/에러 상태 처리
- 반응형 디자인 요구사항
- 접근성 고려사항

#### 트레이드오프
- 성능 vs 단순성
- 재사용성 vs 특화
- 즉시 구현 vs 확장성

#### 엣지 케이스
- 동시성/경쟁 조건
- 네트워크 실패 복구
- 권한 부족 상황
- 대용량 데이터 처리

#### 기존 시스템 연동
- VDG v4 스키마 호환성
- 패턴 엔진 활용
- Credit 시스템 영향
- NotebookLM RAG 연동

**금지 질문 예시**:
- ❌ "이 기능이 필요한가요?"
- ❌ "테스트가 필요한가요?"
- ❌ "성능이 중요한가요?"

**좋은 질문 예시**:
- ✅ "VEO 3.1과 Kling 둘 다 지원할 때 비디오 길이 제한이 다른데 어떻게 처리?"
- ✅ "실시간 업데이트가 필요하면 WebSocket vs SSE 중 어느 것?"
- ✅ "크레딧 부족 시 부분 결과라도 보여줄까, 아니면 완전 차단?"

### 3. SPEC 문서 작성

인터뷰 완료 후 → `.claude/specs/$FEATURE_NAME.md` 작성

```bash
# 파일 생성
.claude/specs/[feature-kebab-case].md
```

템플릿: `.claude/templates/spec-template.md` 사용

---

## 완료 기준

- [ ] 15개 이상 비-자명한 질문 완료
- [ ] 모든 트레이드오프 결정 문서화
- [ ] 엣지 케이스 5개 이상 식별
- [ ] SPEC 파일 작성 완료
- [ ] 상태: DRAFT → APPROVED 변경 대기

---

## 다음 단계

```
인터뷰 완료 후:
1. /clear (컨텍스트 초기화)
2. 새 세션에서 /spec-execute [feature-name]
```
