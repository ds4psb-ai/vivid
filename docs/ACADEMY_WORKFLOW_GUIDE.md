# Academy 워크플로우 가이드

> **Version**: 1.1
> **Last Updated**: 2026-02-06
> **Location**: `frontend/src/app/academy/` (34개 컴포넌트)

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

### 리팩토링 전 (2026-02-05 이전)
```
frontend/src/app/academy/
└── page.tsx (2,251 lines)
```

### 리팩토링 후 (2026-02-06 ✅)
```
frontend/src/app/academy/
├── page.tsx (메인 컨테이너)
├── api/
│   └── sceneDetect.ts (씬 감지 API)
├── components/
│   ├── CreditContent.tsx
│   ├── HomeContent.tsx
│   ├── HomeworkContent.tsx
│   ├── PromptContent.tsx
│   ├── SetupContent.tsx
│   ├── VibeContent.tsx
│   ├── parse/ (5개 컴포넌트)
│   │   ├── AnchorGuidePanel.tsx
│   │   ├── ImageAttachmentGuide.tsx
│   │   ├── MDInput.tsx
│   │   ├── ParseContent.tsx
│   │   └── SceneCard.tsx
│   ├── shared/ (4개 컴포넌트)
│   │   ├── ContentCard.tsx
│   │   ├── NextStepButton.tsx
│   │   ├── PageHeader.tsx
│   │   └── WhiteButton.tsx
│   ├── tools/ (4개 컴포넌트)
│   │   ├── FAQItem.tsx
│   │   ├── ToolDetailCard.tsx
│   │   ├── ToolsContent.tsx
│   │   └── toolsData.ts
│   └── upload/ (5개 컴포넌트)
│       ├── DetectionResults.tsx
│       ├── ThresholdSelector.tsx
│       ├── UploadContent.tsx
│       ├── UploadProgressBar.tsx
│       └── VideoDropzone.tsx
├── hooks/
│   ├── useMDParse.ts (MD 파싱 로직)
│   └── useVideoUpload.ts (비디오 업로드 로직)
└── constants.ts (상수 정의)
```

### 주요 컴포넌트

#### Upload (비디오 업로드)
- `VideoDropzone.tsx`: 드래그앤드롭 UI
- `UploadProgressBar.tsx`: 업로드 진행 상태
- `ThresholdSelector.tsx`: 정밀/표준 모드 선택
- `DetectionResults.tsx`: 씬 감지 결과 표시

#### Parse (MD 파싱)
- `MDInput.tsx`: 마크다운 입력 필드
- `SceneCard.tsx`: 파싱된 씬 카드
- `AnchorGuidePanel.tsx`: 앵커 테이블 가이드
- `ImageAttachmentGuide.tsx`: 이미지 첨부 워크플로우

#### Shared (공통 컴포넌트)
- `ContentCard.tsx`: 카드 컨테이너
- `PageHeader.tsx`: 페이지 헤더
- `NextStepButton.tsx`: 다음 단계 버튼
- `WhiteButton.tsx`: 공통 버튼 스타일

#### Custom Hooks
- `useMDParse.ts`: MD → JSON 파싱 로직
- `useVideoUpload.ts`: 비디오 업로드 + 씬 감지 상태 관리

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
| 1.1 | 2026-02-06 | 2,251줄 단일 파일 → 34개 컴포넌트로 분리 (api/, components/, hooks/) |
| 1.0 | 2026-02-05 | 초기 생성, threshold 모드 선택 UI 문서화 |
