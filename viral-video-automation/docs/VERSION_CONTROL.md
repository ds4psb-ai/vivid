# 📦 Version Control Guide

> **Purpose**: 생성물 버전 관리 및 롤백
> **Version**: 2026-02
> **Last Updated**: 2026-02-02

---

## 🎯 왜 필요한가?

```
❌ Before: "어제 버전이 더 나았는데..."
✅ After:  "./version.sh rollback v1" (즉시 복원)
```

---

## 📁 디렉토리 구조

```
projects/{project}/generated/
├── images/
│   ├── v1/
│   │   ├── scene01.png
│   │   ├── scene02.png
│   │   └── _metadata.json  ← 버전 메타데이터
│   ├── v2/
│   │   └── _metadata.json
│   └── selected/
│       ├── scene01.png     ← 최종 선택
│       └── _version.json   ← 출처 버전 기록
└── videos/
    └── (동일 구조)
```

---

## 📋 메타데이터 형식

### _metadata.json (버전별)

```json
{
  "version": "v1",
  "created": "2026-02-02T00:45:00+09:00",
  "tool": "NanoBanana Pro",
  "prompt_file": "prompts/IMAGE_PROMPTS.md",
  "status": "active",
  "notes": "ANCHOR 확정, Scene 1-3 완료",
  "files": [
    "scene01.png",
    "scene02.png",
    "scene03.png"
  ]
}
```

### _version.json (selected/)

```json
{
  "scene01.png": {"from": "v2", "selected_at": "2026-02-02T01:00:00"},
  "scene02.png": {"from": "v1", "selected_at": "2026-02-02T01:00:00"}
}
```

---

## 🔧 스크립트 사용법

### 새 버전 생성

```bash
./scripts/version.sh new images
# → generated/images/v3/ 생성
```

### 버전 목록 확인

```bash
./scripts/version.sh list images
# v1 (2026-02-02) - ANCHOR 확정
# v2 (2026-02-02) - Scene 4-7 추가
# v3 (2026-02-02) - 현재 작업 중
```

### 롤백

```bash
./scripts/version.sh rollback images v1
# v1 → selected/ 복사
# 기존 selected/ → _backup/ 이동
```

### 버전 비교

```bash
./scripts/version.sh compare images v1 v2
# 차이점 출력
```

### 파일 선택

```bash
./scripts/version.sh select images v2/scene01.png
# v2/scene01.png → selected/scene01.png
```

---

## 📋 워크플로우

### 일반 작업

```
1. 새 버전 생성: ./version.sh new images
2. 해당 버전에 생성물 저장
3. 만족 시: ./version.sh select images v3/scene01.png
4. 불만족 시: 새 버전 생성 후 재시도
```

### 롤백 필요 시

```
1. 이전 버전 확인: ./version.sh list images
2. 롤백: ./version.sh rollback images v1
3. 해당 버전부터 재작업
```

---

## ✅ 베스트 프랙티스

1. **Stage 완료 시 메타데이터 저장**
   - notes에 진행 상황 기록

2. **major 변경 시 새 버전**
   - ANCHOR 변경, 스타일 변경

3. **minor 수정은 같은 버전**
   - 파라미터 조정, 미세 수정

4. **selected/에 최종본만**
   - 혼동 방지

5. **정기 정리**
   - 오래된 버전 archive

---

## 🚨 주의사항

- `_metadata.json` 수동 편집 시 JSON 유효성 확인
- 롤백 전 현재 작업 백업
- selected/ 직접 수정 지양

---

> **Related**: [ERROR_RECOVERY.md](./ERROR_RECOVERY.md)
