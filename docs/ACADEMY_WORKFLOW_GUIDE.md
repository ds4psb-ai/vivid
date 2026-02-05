# Academy 워크플로우 가이드

> **Version**: 1.0
> **Last Updated**: 2026-02-05
> **Location**: `frontend/src/app/academy/page.tsx`

---

## 개요

AI 영상 제작 워크플로우 가이드 페이지. 레퍼런스 영상 분석 → 프롬프트 생성 → 외부 도구 연동까지 전 과정을 안내합니다.

### URL
- **Production**: https://www.prompty.co.kr/academy
- **Dev**: http://localhost:3100/academy

---

## 탭 구조

| 탭 | URL Param | 설명 |
|----|-----------|------|
| 홈 대시보드 | `?tab=home` | 전체 워크플로우 개요 |
| 환경 설정 | `?tab=setup` | Gemini CLI, API 키 설정 |
| $300 무료 크레딧 | `?tab=credit` | Google AI Studio 크레딧 안내 |
| **영상 업로드** | `?tab=upload` | 씬 감지 + 타임스탬프 추출 |
| 프롬프트 생성 | `?tab=prompt` | Builder1 연동 |
| 파싱 + 복사 | `?tab=parse` | MD 파일 파싱 |
| 외부 툴 | `?tab=tools` | Builder1, Antigravity 링크 |
| 바이브 철학관 | `?tab=vibe` | 바이브 코딩 철학 |
| 과제 | `?tab=homework` | 실습 과제 |

---

## 핵심 기능: 자동 씬 감지

### 위치
`?tab=upload` → STEP 1. 자동 씬 감지

### Threshold 모드 선택 (2026-02-05 추가)

씬 감지 민감도를 선택할 수 있습니다:

| 모드 | Threshold | 특성 | 적합한 영상 |
|------|-----------|------|------------|
| **⚡ 정밀 모드** | 0.19 | 빠른 컷도 놓치지 않고 감지 | 빠른 편집, 많은 장면 전환 |
| **🎯 표준 모드** | 0.25 | 트랜지션 효과(페이드/디졸브) 무시 | 일반 영상, 효과 있는 영상 |

### UX 흐름

```
1. 모드 선택 (기본: 정밀 모드)
   ↓
2. 영상 드래그 & 드롭 (또는 클릭)
   ↓
3. 업로드 + FFmpeg 분석
   ↓
4. 결과: N개 씬 감지 완료!
   - 타임스탬프 목록 표시
   - "Builder1 입력용 복사" 버튼
   - "프레임 이미지 다운로드" 버튼
   - "다른 모드로 재분석" 버튼
```

### API 연동

```typescript
// Frontend → Backend
POST /api/v1/scene-detect/?threshold=0.19  // 정밀 모드
POST /api/v1/scene-detect/?threshold=0.25  // 표준 모드

// Response
{
  "timestamps": ["0:00.00", "0:03.45", "0:07.12", ...]
}
```

### 기술 스택
- **Frontend**: React useState로 threshold 모드 관리
- **Backend**: FastAPI + FFmpeg scene detection
- **Threshold 범위**: 0.05 ~ 0.5 (낮을수록 민감)

---

## 워크플로우 연동

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  1. 레퍼런스 영상 다운로드                                    │
│     YouTube/TikTok/Instagram → savefrom.net, snaptik.app    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 씬 감지 (Academy ?tab=upload)                            │
│     정밀/표준 모드 선택 → 영상 업로드 → 타임스탬프 복사        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Builder1 프롬프트 생성 (외부 도구)                        │
│     타임스탬프 붙여넣기 → IMAGE/MOTION 프롬프트 생성          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 파싱 + 이미지 생성 (Academy ?tab=parse)                  │
│     MD 파일 업로드 → 프롬프트 파싱 → 외부 도구로 생성         │
└─────────────────────────────────────────────────────────────┘
```

### 외부 도구 연동

| 도구 | 용도 | 링크 |
|------|------|------|
| **Builder1 (통합빌더)** | IMAGE + MOTION 프롬프트 생성 | Google AI Studio |
| **바이브 철학관** | 바이브 코딩 관련 | Google AI Studio |
| **Antigravity** | Gemini 파일 관리 | antigravity.google |

---

## 파일 구조

```
frontend/src/app/academy/
└── page.tsx          # 전체 Academy 페이지 (1,400+ lines)
    ├── UploadContent()   # 씬 감지 UI
    ├── PromptContent()   # 프롬프트 생성
    ├── ParseContent()    # 파싱 기능
    ├── ToolsContent()    # 외부 도구 링크
    └── ...
```

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [BUILDER1_HOMAGE_GENERATOR.md](./BUILDER1_HOMAGE_GENERATOR.md) | Builder1 상세 스펙 |
| [API_REFERENCE.md](./API_REFERENCE.md) | `/api/v1/scene-detect/` API 스펙 |

---

## Changelog

| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.0 | 2026-02-05 | 초기 생성, threshold 모드 선택 UI 문서화 |
