---
description: SPEC 인터뷰 - 심층 Q&A로 상세 명세서 작성 (Thariq 패턴)
---

# SPEC Interview Workflow

> **목적**: 40+ 비-자명한 질문으로 상세 SPEC 문서 작성
> **기반**: Anthropic Thariq's Interview-First Pattern (2026)

// turbo

## 1. 초기 SPEC 파일 생성
```bash
# 템플릿 복사
cp docs/specs/TEMPLATE_SPEC.md docs/specs/[FEATURE_NAME].md
```

## 2. 관련 코드 탐색
```bash
# Backend 관련 파일
ls -la backend/app/routers/ backend/app/services/

# Frontend 관련 파일
ls -la frontend/src/components/ frontend/src/lib/
```

## 3. 심층 인터뷰 프롬프트

지금부터 심층 인터뷰를 진행합니다. 다음 영역에서 **비-자명한** 질문을 던지세요:

### 질문 영역

**기술 구현**:
- 기존 RAG/Dimension 시스템과 어떻게 연동?
- API 엔드포인트 설계 (REST? GraphQL? SSE?)
- 데이터 모델/스키마 변경 필요?

**UI/UX**:
- 화면 흐름과 사용자 시나리오
- 로딩/에러/빈 상태 처리
- 모바일 반응형 필요?

**트레이드오프**:
- 성능 vs 단순성
- 재사용성 vs 특화
- 즉시 구현 vs 확장성

**엣지 케이스**:
- 동시성/경쟁 조건
- 네트워크 실패 복구
- 권한/크레딧 부족 상황

**금지 질문**:
- ❌ "이 기능이 필요한가요?"
- ❌ "테스트가 필요한가요?"
- ❌ "성능이 중요한가요?"

**좋은 질문 예시**:
- ✅ "VEO 3.1과 Kling 둘 다 지원할 때 비디오 길이 제한이 다른데 어떻게?"
- ✅ "실시간 업데이트가 필요하면 WebSocket vs SSE?"
- ✅ "크레딧 부족 시 부분 결과라도 보여줄까?"

## 4. SPEC 문서 작성

인터뷰 완료 후 `docs/specs/[FEATURE_NAME].md` 에 작성:
- 기능/비기능 요구사항
- 기술 설계 (파일별 변경사항)
- 엣지 케이스 & 에러 처리
- 트레이드오프 결정
- 테스트 계획

## 5. 완료 확인
```bash
cat docs/specs/[FEATURE_NAME].md | head -50
```

---

**다음 단계**:
1. 세션 종료 또는 새 대화 시작
2. `/spec-execute [feature-name]` 로 구현 시작
