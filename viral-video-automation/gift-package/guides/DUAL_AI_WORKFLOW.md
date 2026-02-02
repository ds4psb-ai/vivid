# 🔄 DUAL AI WORKFLOW: Gemini CLI + Claude Code

> **Architecture**: 같은 프로젝트 폴더를 두 AI가 공유
> **Version**: 1.0 (2026-02-02)
> **Philosophy**: 분석(Gemini) ↔ 정제(Claude) 티키타카

---

## 🎯 핵심 개념

```
같은 폴더를 두 AI가 바라본다:
  - Gemini CLI: 영상 → 분석 → 파일 저장
  - Claude Code: 파일 읽기 → 정제 → 파일 저장
  - 동기화: 파일 시스템 자체가 상태 저장소
```

---

## 📁 공유 폴더 구조

```
projects/{project-name}/
├── reference/
│   └── source.mp4          ← 원본 영상 (Gemini 분석 대상)
│
├── docs/
│   ├── ANALYSIS.md         ← Gemini 출력
│   ├── PROFILES.md         ← Gemini 출력 (캐릭터)
│   └── COLOR_KEY.md        ← Gemini 출력 (색감)
│
├── prompts/
│   ├── IMAGE_PROMPTS.md    ← Claude 정제
│   └── MOTION_PROMPTS.md   ← Claude 정제
│
├── generated/
│   ├── images/v1/, v2/, selected/
│   └── videos/selected/
│
├── PROJECT_CONTEXT.md      ← 양쪽 참조
└── STATE.md                ← 양쪽 업데이트
```

---

## 🔄 워크플로우

### Phase 1: Gemini CLI - 영상 분석

```bash
# Terminal 1: Gemini CLI
gemini

# Interactive 모드에서:
> @{projects/umbrella-parody/reference/source.mp4}

아래 형식으로 분석해줘:

## CHARACTER PROFILES
각 인물마다:
- ID: ID_[역할]
- Ethnicity: Korean
- Age, Hair, Face, Eyes, Clothing, Position

## COLOR GRADE KEY
- Tone, Grain, Contrast, Lighting, Atmosphere

## CUT-BY-CUT
각 컷마다:
- 타임코드
- [CHARACTERS IN THIS CUT]
- [SCENE DESCRIPTION]
- [NANO BANANA PRO PROMPT]
- [COLOR CONSISTENCY KEY]
- --ar 9:16

## ANCHOR 추천
얼굴이 가장 잘 보이는 컷 번호와 이유
```

**결과 저장:**
```bash
# Gemini 출력을 파일로 저장
# → projects/{name}/docs/ANALYSIS.md
```

---

### Phase 2: Claude Code - 프롬프트 정제

```bash
# Terminal 2: Claude Code (Antigravity)
cd ~/vivid/viral-video-automation
claude
```

**Claude에게 요청:**

```
projects/umbrella-parody/docs/ANALYSIS.md 파일을 읽고:

1. ANCHOR 컷 프롬프트 먼저 분리
2. IMAGE_PROMPTS.md 형식으로 정리
3. STATE.md 초기화
4. 누락된 요소 체크:
   - 모든 인물 한국인 명시?
   - --no 파라미터?
   - 의상 색깔 정확?
```

**Claude 출력:**
```
→ projects/{name}/prompts/IMAGE_PROMPTS.md
→ projects/{name}/STATE.md
```

---

### Phase 3: 이미지 생성 + Critique

```
1. IMAGE_PROMPTS.md에서 ANCHOR 프롬프트 복사
2. NanoBanana/MJ에서 생성
3. 결과물을 Claude에게 Critique 요청

Claude:
"이 이미지 평가해줘. CRITIQUE_IMAGE.md 기준으로."
→ PASS / REVISE / REJECT

4. STATE.md 업데이트
```

---

### Phase 4: Gemini - 추가 분석 (필요시)

```
Gemini CLI에서:
"Cut #2의 배경 건물 색깔 더 자세히 알려줘"
"ID_GIRL의 표정 변화를 프레임 단위로 분석해줘"
```

---

## 📋 역할 분담

| AI | 역할 | 강점 |
|----|------|------|
| **Gemini CLI** | 영상 → 텍스트 분석 | Native Vision, 멀티모달 |
| **Claude Code** | 텍스트 → 구조화/정제 | 파일 편집, 코드 생성, 일관성 |

---

## 🔁 Tiki-Taka Loop

```
GEMINI                          CLAUDE
   │                               │
   │──[영상 분석]─────────────────→│
   │                               │──[정제]──→ IMAGE_PROMPTS.md
   │                               │
   │                               │──[Critique 요청]
   │                               │
   │←─[추가 분석 요청]──────────────│
   │                               │
   │──[상세 분석]─────────────────→│
   │                               │──[프롬프트 수정]
   │                               │
                    ...반복...
```

---

## 📝 템플릿: Gemini 분석 요청 (개선판)

```
아래 영상을 VIDEO REPLICATION SYSTEM v2.0 기준으로 분석해주세요.

## 필수 출력

### 1. CHARACTER PROFILES
각 인물별로:
- ID: ID_[역할] (예: ID_BOY, ID_GIRL)
- Ethnicity: Korean (필수)
- Apparent Age:
- Hair: 색, 스타일, 길이
- Face: 형태, 피부톤, 표정
- Eyes: 특징
- Clothing: 색깔 명시 필수!
- Position: 프레임 내 위치

### 2. COLOR GRADE KEY
- Key Name: [씬 분위기]_KEY (예: DAYTIME_RAIN_DRAMA_KEY)
- Tone:
- Grain:
- Contrast:
- Lighting:
- Atmosphere:

### 3. CUT-BY-CUT PROMPTS
각 컷별로:
===== CUT #N | 00:00 - 00:00 =====
[CHARACTERS IN THIS CUT]
[SCENE DESCRIPTION]
[NANO BANANA PRO PROMPT]
[COLOR CONSISTENCY KEY]
--ar 9:16

### 4. ANCHOR 추천
- 추천 컷: #N
- 이유: 얼굴 선명도, 조명, 표정

### 5. 도구 추천
- 이미지: NanoBanana Pro / Midjourney V7
- 영상: Kling 2.6 / Sora 2 Pro
- 이유:
```

---

## 📝 템플릿: Claude 정제 요청

```
docs/ANALYSIS.md 파일을 읽고 아래 작업 수행:

1. ANCHOR 프롬프트 분리
   - Cut #[N]을 ANCHOR로 지정
   - prompts/IMAGE_PROMPTS.md 맨 앞에 배치

2. 프롬프트 검증
   - 모든 인물 "Korean" 명시 확인
   - 의상 색깔 원본과 일치 확인
   - --no 파라미터 추가 (western features 등)

3. STATE.md 초기화
   - Scene Progress 테이블
   - Current Task
   - Quick Resume Prompt

4. 누락 사항 리포트
   - 불명확한 부분 목록
   - Gemini에게 추가 질문할 내용
```

---

## ✅ 장점

| 기존 (OpenClaw Skill) | 새 방식 (Dual AI Folder) |
|-----------------------|--------------------------|
| VPS 의존 | 로컬 + VPS 유연 |
| 단방향 | **양방향 티키타카** |
| 스크립트 필요 | 대화형 인터랙션 |
| 상태 분리 | **파일 시스템 = 상태** |

---

## 🚀 Quick Start

```bash
# 1. 프로젝트 생성
./scripts/init.sh umbrella-parody

# 2. 영상 복사
cp ~/Downloads/umbrella.mp4 projects/umbrella-parody/reference/source.mp4

# 3. Terminal 분할
# - Left: Gemini CLI (gemini)
# - Right: Claude Code (claude)

# 4. 같은 폴더 바라보기
# Gemini: @{projects/umbrella-parody/reference/source.mp4} 분석해줘
# Claude: projects/umbrella-parody/docs/ANALYSIS.md 정제해줘
```

---

> **핵심**: 파일 시스템이 두 AI의 공유 메모리 역할
