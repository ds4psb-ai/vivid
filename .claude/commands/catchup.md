# Catchup Command

입력: $ARGUMENTS (브랜치명, 비어있으면 main과 비교)

---

## 목적
현재 브랜치의 변경사항을 분석하고 컨텍스트를 파악합니다.
`/clear` 후 새 세션에서 작업 컨텍스트 복원에 유용합니다.

---

## 워크플로우

### 1. Git 상태 수집

```bash
# 현재 브랜치
git branch --show-current

# main 대비 커밋 히스토리
git log main..HEAD --oneline

# 변경 파일 목록
git diff main..HEAD --stat

# 상세 diff
git diff main..HEAD
```

### 2. 변경사항 분석

#### 변경된 파일 분류
- **Backend**: `backend/app/**/*`
- **Frontend**: `frontend/src/**/*`
- **Config**: `config/**/*`, `*.yaml`, `*.json`
- **Docs**: `*.md`, `docs/**/*`
- **Tests**: `tests/**/*`, `e2e/**/*`

#### 영향 분석
- Dimension 시스템 변경 여부
- RAG 시스템 변경 여부
- 크레딧/Run-Token 변경 여부
- API 스키마 변경 여부

### 3. 관련 파일 읽기

변경된 핵심 파일들의 현재 상태를 읽어서 컨텍스트 파악

---

## 출력 형식

```markdown
# Branch Catchup: [브랜치명]

## 브랜치 정보
- 현재 브랜치: feature/xxx
- Base: main
- 커밋 수: X개
- 마지막 커밋: YYYY-MM-DD HH:MM

## 커밋 히스토리
1. `abc1234` - feat: 설명
2. `def5678` - fix: 설명

## 변경 요약

### Backend (X files)
- `app/routers/dimension.py` - 새 엔드포인트 추가
- `app/services/xxx.py` - 로직 수정

### Frontend (X files)
- `src/components/xxx.tsx` - 컴포넌트 추가

### 기타 (X files)
- `config/xxx.yaml` - 설정 변경

## 영향 분석
- [ ] Dimension 시스템: 영향 있음/없음
- [ ] RAG 시스템: 영향 있음/없음
- [ ] 크레딧/Run-Token: 영향 있음/없음
- [ ] API 스키마: Breaking change 여부

## 현재 작업 상태
- 마지막 작업: [설명]
- 다음 TODO: [설명]

## 관련 문서
- `docs/xxx.md` - 참고 문서
```

---

## 사용 시나리오

### 1. 새 세션 시작 시
```
/clear
/catchup
```

### 2. 다른 브랜치와 비교
```
/catchup develop
```

### 3. 특정 커밋 이후 변경사항
```
/catchup abc1234
```
