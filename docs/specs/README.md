# Specs Directory

> **Purpose**: Feature specification documents created via `/spec-interview`

---

## 파일 설명

| 파일 | 역할 | 상태 |
|------|------|------|
| `TEMPLATE_SPEC.md` | SPEC 문서 작성 템플릿 | 템플릿 (편집 금지) |
| `abyss-mirror.md` | 심연의 거울 기능 SPEC | ✅ DONE |

---

## SPEC 작성 워크플로우

### 1. 인터뷰 세션 시작

```bash
/spec-interview
```

Claude가 기능 요구사항에 대해 질문합니다:
- 핵심 가치
- 입력/출력 형태
- 비기능 요구사항
- 엣지 케이스

### 2. SPEC 문서 생성

인터뷰 완료 후 `TEMPLATE_SPEC.md`를 기반으로 새 SPEC 파일 생성:

```bash
# 예: feature-name.md
cp TEMPLATE_SPEC.md feature-name.md
```

### 3. 구현 실행

```bash
/spec-execute feature-name.md
```

### 4. 검증

```bash
/spec-verify feature-name.md
```

---

## SPEC 문서 구조

```markdown
# SPEC: [기능명]

> **생성일**: YYYY-MM-DD
> **상태**: DRAFT | APPROVED | IMPLEMENTING | DONE

## 1. 개요
## 2. 요구사항 (FR/NFR)
## 3. 기술 설계
## 4. UI/UX 설계
## 5. 엣지 케이스
## 6. 트레이드오프 결정
## 7. 테스트 계획
## 8. 인터뷰 Q&A 로그
## 9. 최종 체크리스트
```

---

## 상태 정의

| 상태 | 설명 |
|------|------|
| `DRAFT` | 인터뷰 진행 중 / 검토 대기 |
| `APPROVED` | 구현 승인됨 |
| `IMPLEMENTING` | 구현 진행 중 |
| `DONE` | 구현 및 검증 완료 |

---

## 관련 문서

- [DIMENSION_APP_DEVELOPER_GUIDE.md](../DIMENSION_APP_DEVELOPER_GUIDE.md) - 앱 개발 가이드
- [CLAUDE.md](../../CLAUDE.md) - 프로젝트 개요
