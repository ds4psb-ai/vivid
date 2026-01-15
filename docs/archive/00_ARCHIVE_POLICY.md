# Archive Policy

> **Created**: 2026-01-15
> **Status**: Active

---

## 목적

`/docs/archive/` 디렉토리는 더 이상 활성화되지 않은 문서를 보관합니다.
삭제하지 않고 아카이빙하는 이유:
- 과거 결정의 맥락 보존
- 레거시 시스템 참조 지원
- 감사(audit) 추적 가능

---

## 아카이빙 기준

### 1. Deprecated (삭제 예정)

**파일명 규칙**: `*_deprecated.md`

| 조건 | 설명 |
|------|------|
| 신규 문서로 대체됨 | 예: 3-Layer → 4-Layer 전환 |
| 코드가 제거됨 | 해당 기능 코드 삭제 완료 |
| 오래된 전략 | 전략 방향 변경 후 구 전략 |

**보존 기간**: 2주 (삭제 전 검토 기간)

### 2. Archived (장기 보관)

**파일명 규칙**: 숫자 prefix 유지 (예: `08_PIPELINES_AND_USER_FLOWS.md`)

| 조건 | 설명 |
|------|------|
| 6개월 이상 미수정 | 마지막 수정일 기준 |
| 참조용으로만 사용 | 활성 개발에 직접 사용 안 함 |
| 역사적 가치 | 아키텍처 진화 기록 |

**보존 기간**: 무기한 (분기별 검토)

---

## 아카이빙 절차

### 활성 → Archive 이동

```bash
# 1. 파일 이동
mv docs/MY_DOC.md docs/archive/MY_DOC.md

# 2. 참조 문서 업데이트
# - 00_DOCS_INDEX.md에서 링크 수정
# - 관련 문서의 "Related" 섹션 업데이트

# 3. Git 커밋
git add -A && git commit -m "docs: archive MY_DOC.md"
```

### Archive → 삭제

```bash
# 1. deprecated 문서 확인 (2주 경과)
ls docs/archive/*_deprecated.md

# 2. 최종 검토 후 삭제
rm docs/archive/OLD_DOC_deprecated.md

# 3. Git 커밋
git add -A && git commit -m "docs: remove deprecated OLD_DOC"
```

---

## 현재 아카이브 현황

### Deprecated (삭제 예정)

| 파일 | 대체 문서 | 아카이브 일자 | 삭제 예정 |
|------|----------|--------------|----------|
| `crebit_teaching_apps_spec_v3_deprecated.md` | `unified_4layer_strategy.md` | 2026-01-15 | 2026-01-29 |
| `teaching_capsule_agent_integration_spec_deprecated.md` | 4-Layer 통합 | 2026-01-15 | 2026-01-29 |

### Archived (장기 보관)

| 범주 | 파일 수 | 설명 |
|------|--------|------|
| Architecture (00-15) | 16 | 아키텍처 진화 기록 |
| Codex (16-26) | 11 | 코딩 표준 및 규칙 |
| Plans (RAG, Phase) | 8 | 과거 계획 문서 |
| Misc | 4 | 기타 |

---

## 분기별 검토 체크리스트

- [ ] Deprecated 파일 삭제 기한 확인
- [ ] 6개월 미수정 문서 식별
- [ ] Archive 파일 중 재활성화 후보 검토
- [ ] 문서 인덱스(00_DOCS_INDEX.md) 동기화

---

## 관련 문서

- [문서 인덱스](../00_DOCS_INDEX.md)
- [CLAUDE.md](../../CLAUDE.md) - 프로젝트 개요
