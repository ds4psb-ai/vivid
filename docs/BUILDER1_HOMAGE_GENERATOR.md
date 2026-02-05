# Builder 1: 오마주 공방 (Homage Studio)

> **Version**: 8.2
> **Last Updated**: 2026-02-05
> **Location**: `viral-video-automation/builder1-temp/`

---

## 개요

Academy에서 추출한 씬 테이블 기반으로 IMAGE + MOTION 프롬프트를 생성하는 통합 빌더.

### 지원 도구
- **IMAGE**: NanoBanana Pro (한글), Midjourney V7 (영문)
- **MOTION**: Kling 3.0, Veo 3.1

---

## 워크플로우

### 전체 흐름
```
Academy 영상 업로드 → 타임스탬프 복사 → 빌더1 → MD 다운로드 → (선택) 파싱 페이지
```

### 사전 준비 (Academy)
1. [Academy 영상 업로드](https://www.prompty.co.kr/academy?tab=upload) - 타임스탬프 추출
2. 타임스탬프 복사 → 빌더1에 붙여넣기

### 빌더1 이후 (선택)
- [파싱 페이지](https://www.prompty.co.kr/academy?tab=parse) - 빌더1에서 다운받은 MD 파일 파싱

### 빌더 5-STEP
| STEP | 내용 | 사용자 액션 |
|------|------|------------|
| **1** | 입력 정리 + 오마주 스타일 | 스타일 입력 또는 기본값(한국인) |
| **2** | IMAGE 프롬프트 (전체) | 피드백 또는 "다음" |
| **3** | MOTION 프롬프트 (전체) | 피드백 또는 "다음" |
| **4** | 통합 워크플로우 출력 | **오마주 다운로드 가능** → VariationPanel 표시 |
| **5** | 변주 생성 (선택) | **변주 다운로드 가능** |

### STEP 4 → 5 UX 흐름
```
STEP 4 완료 (오마주 워크플로우 다운로드 가능)
           ↓
    VariationPanel 표시
           ↓
┌──────────────────────┬──────────────────────┐
│ "변주 생성" 클릭      │ "변주 없이 완료" 클릭  │
│ (옵션 선택 필수)      │                      │
└──────────────────────┴──────────────────────┘
           ↓                      ↓
   STEP 5 진행               status='COMPLETE'
   (AI가 변주 생성)              (끝)
           ↓
   변주 워크플로우 다운로드 가능
   status='COMPLETE'
```

---

## 핵심 기능

### 1. 오마주 스타일 자유 입력
기존 문화권 A/B/C/D/E 선택 → **자유 텍스트 입력** 방식으로 변경

```
예시 입력:
- "한국인 20대 커플" (기본값)
- "일본 스타일로"
- "한국인인데 텍사스 사니까 인종만 바꿔"
- "동남아 느낌"
```

**자동 적용 규칙:**
| 키워드 | --no 기본값 |
|--------|------------|
| 한국/Korean | `western features, caucasian skin, blonde hair` |
| 일본/Japanese | `western features, caucasian skin, korean style` |
| 서양/Western | `asian features, black hair` |
| 동남아/Southeast | `pale skin, caucasian features` |

### 2. 별도 다운로드 (오마주/변주)
| STEP | 버튼 | 파일명 |
|------|------|--------|
| 4+ | 오마주 (.md) | `HOMAGE_WORKFLOW_YYYY-MM-DD.md` |
| 5 | 변주 (.md) | `VARIATION_WORKFLOW_YYYY-MM-DD.md` |

### 3. Step 진행 로직
- **"다음/계속/진행/next/좋습니다"** 입력 시에만 Step 증가
- 피드백/오마주 스타일 입력 시 currentStep 유지
- 통합 워크플로우 감지: `🎬 오마주 워크플로우` 또는 `## ⭐ 앵커 이미지`
- 변주 워크플로우 감지: `🎬 변주 워크플로우`

---

## 기술 스택

### Gemini 설정
```typescript
{
  model: "gemini-3-pro-preview",
  temperature: 0.2,
  maxOutputTokens: 32768,
  thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH }
}
```

### 파일 구조
```
builder1-temp/
├── App.tsx                 # 메인 앱 + Step 관리 + variationData 상태
├── constants.ts            # 시스템 프롬프트 (V8.2)
├── types.ts                # 타입 정의 (VariationOption, VariationData)
├── components/
│   ├── ResultView.tsx      # 채팅 UI + 다운로드 + VariationPanel 통합
│   ├── VariationPanel.tsx  # STEP 5 변주 UI (persona.json, 댓글, A/B/AB)
│   ├── FileUpload.tsx      # 영상 업로드
│   ├── Header.tsx          # 헤더
│   └── ProcessingOverlay.tsx
└── services/
    └── geminiService.ts    # Gemini API 연동
```

---

## 오마주 vs 변주

| 구분 | 오마주 (STEP 1-4) | 변주 (STEP 5) |
|------|------------------|---------------|
| 구도/타이밍 | 100% 유지 | 살짝 변경 가능 |
| 카메라 앵글 | 100% 유지 | 조정 가능 |
| 변경 범위 | 인종/문화/의상만 | + 구도/내용 |
| 입력 방식 | 자유 텍스트 | A/B/C 옵션 |

### 변주 옵션 (STEP 5 VariationPanel)

STEP 4 완료 후 `VariationPanel` UI가 표시됨:

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 변주 생성 (선택)                                          │
├─────────────────────────────────────────────────────────────┤
│  📄 persona.json (선택) - 드래그앤드롭 업로드                   │
│  💬 베스트 댓글 (선택) - 바이럴 포인트 강화                     │
│  🎯 변주 옵션 선택                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 🅰️ 안정형    │ │ 🅱️ 밸런스형  │ │ 🆎 과감형    │           │
│  │   (8%)     │ │   (15%)    │ │   (18%)    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  [🚀 변주 워크플로우 생성]  [변주 없이 완료]                    │
└─────────────────────────────────────────────────────────────┘
```

| 옵션 | 변경률 | 설명 |
|------|--------|------|
| 🅰️ 안정형 | 8% | 소품 디테일만 변경 |
| 🅱️ 밸런스형 | 15% | 의상/소품 + 조명 톤 |
| 🆎 과감형 | 18% | 문화권/스타일 전환 |

### 변주 입력 데이터
```typescript
interface VariationData {
  personaJson: File | null;      // persona.json 파일
  personaContent: object | null; // 파싱된 JSON 내용
  bestComment: string;           // 베스트 댓글
  variationOption: 'A' | 'B' | 'AB' | null;
}
```

---

## 시스템 프롬프트 핵심

### ANTI-LAZY GUARD
절대 금지 패턴:
- `(위와 동일)`, `(이하 생략)`
- `(같은 방식으로...)`
- `similar to Scene X`
- `...`로 내용 축약

### 범용화 원칙
- 앵커 씬: ⭐ ANCHOR 표시된 씬 자동 식별
- --no 값: 씬 상태 분석 후 동적 생성
- --stylize: Visual Rhyme Phase에 따라 자동
- 씬 수: N씬 (영상 길이에 따라)

---

## 관련 문서

- [Academy 탭 구조](https://www.prompty.co.kr/academy)
- `constants.ts` - 전체 시스템 프롬프트 V8.2
- `components/VariationPanel.tsx` - 변주 UI 컴포넌트

---

## Changelog

### V8.2 (2026-02-05)
- **VariationPanel 추가**: STEP 4 완료 후 변주 UI 표시
  - persona.json 드래그앤드롭 업로드
  - 베스트 댓글 입력
  - A/B/AB 변주 옵션 버튼
  - "변주 생성" / "변주 없이 완료" 버튼
- types.ts에 `VariationOption`, `VariationData` 타입 추가
- App.tsx에 variationData 상태 관리 추가
- ResultView.tsx에 VariationPanel 통합

### V8.1 (2026-02-05)
- 6단계 → 5단계 축소
- 문화권 버튼 → 오마주 스타일 자유 입력
- 오마주/변주 별도 다운로드 기능
- Academy 링크 연동 (upload 페이지 → 타임스탬프 복사)
- Step 증가 로직 개선 ("다음" 명령 감지)
