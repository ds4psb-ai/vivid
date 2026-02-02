# Prompty Project Package v2.0

> **AI Video Parody 프로젝트 스타터 키트**
> Bring Your Own AI - Gemini CLI + Claude Code 듀얼 워크플로우

---

## Quick Start

```bash
# 1. 패키지 압축 해제
unzip prompty-project.zip
cd prompty-project

# 2. 새 프로젝트 시작
./start.sh

# 또는 수동으로:
./scripts/init.sh my-video
```

---

## 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL ENVIRONMENT                   │
│                                                             │
│  Terminal 1 (Gemini CLI)        Terminal 2 (Claude Code)   │
│  ┌─────────────────────┐        ┌─────────────────────┐    │
│  │ gemini              │        │ claude              │    │
│  │ > @source.mp4       │   ↔    │ > STATE.md 읽고    │    │
│  │ > 이 영상 분석해줘  │        │ > 프롬프트 정제해줘│    │
│  └──────────┬──────────┘        └──────────┬──────────┘    │
│             │          공유 폴더            │               │
│             └──────────────┬───────────────┘               │
│                            ▼                               │
│              projects/my-video/                            │
│              ├── reference/source.mp4                      │
│              ├── docs/ANALYSIS.md                          │
│              ├── prompts/IMAGE_PROMPTS.md                  │
│              └── STATE.md                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 폴더 구조

```
prompty-project/
├── start.sh                 # 원클릭 시작
├── scripts/
│   ├── init.sh              # 프로젝트 초기화
│   ├── extract.sh           # 균등 키프레임 추출
│   └── extract-smart.sh     # Gemini 분석 기반 스마트 추출
├── templates/               # 핵심 템플릿 (6개)
│   ├── PROJECT_CONTEXT.md
│   ├── STATE.md
│   ├── IMAGE_PROMPTS.md
│   ├── MOTION_PROMPTS.md
│   ├── ANALYSIS.md
│   └── CRITIQUE_LOG.md
├── guides/                  # 가이드 문서 (4개)
│   ├── MODE_TIKITAKA.md
│   ├── DUAL_AI_WORKFLOW.md
│   ├── PROMPTS_NANOBANANA.md
│   └── PROMPTS_MIDJOURNEY.md
└── projects/                # 생성된 프로젝트들
    └── {project-name}/
```

---

## 스크립트 사용법

### 1. init.sh - 프로젝트 초기화

```bash
./scripts/init.sh <project-name>

# 예시:
./scripts/init.sh dance-challenge
```

**생성되는 파일:**
- `brief.md` - 프로젝트 개요
- `PROJECT_CONTEXT.md` - AI 컨텍스트
- `STATE.md` - 진행 상황 추적
- `prompts/IMAGE_PROMPTS.md` - 이미지 프롬프트
- `prompts/MOTION_PROMPTS.md` - 모션 프롬프트
- `docs/ANALYSIS.md` - 분석 결과

### 2. extract.sh - 균등 키프레임 추출

```bash
./scripts/extract.sh <project-name> [scene-count]

# 예시: 10개 씬으로 분할
./scripts/extract.sh dance-challenge 10
```

### 3. extract-smart.sh - 스마트 추출

```bash
# 먼저 Gemini로 영상 분석 후 ANALYSIS.md에 JSON 블록 추가
./scripts/extract-smart.sh <project-name>
```

**ANALYSIS.md에 필요한 JSON 형식:**
```markdown
<!-- KEYFRAMES_JSON
{"keyframes":[
  {"timestamp":"00:01.50","filename":"scene01_arrival","anchor":false},
  {"timestamp":"00:03.00","filename":"ANCHOR_IMG","anchor":true},
  {"timestamp":"00:05.50","filename":"scene03_action","anchor":false}
]}
-->
```

---

## Dual AI 워크플로우

### Step 1: Gemini - 영상 분석

```bash
gemini
> @{projects/my-video/reference/source.mp4}
> 이 영상 분석해줘. KEYFRAMES_JSON 포함해서.
```

### Step 2: 키프레임 추출

```bash
./scripts/extract-smart.sh my-video
```

### Step 3: Claude - 프롬프트 정제

```bash
claude
> docs/ANALYSIS.md 읽고 프롬프트 정제해줘
```

### Step 4: 생성 + Critique

1. IMAGE_PROMPTS.md에서 ANCHOR 프롬프트 복사
2. NanoBanana/Midjourney에서 생성
3. 결과물을 Claude에게 Critique 요청
4. STATE.md 업데이트

---

## 파일 설명

| 파일 | 역할 | 작성자 |
|------|------|--------|
| `PROJECT_CONTEXT.md` | AI가 즉시 맥락 파악 | 사람 + AI |
| `STATE.md` | 동적 진행 상황 | AI (Claude) |
| `ANALYSIS.md` | 영상 분석 결과 | AI (Gemini) |
| `IMAGE_PROMPTS.md` | 이미지 생성 프롬프트 | AI (Claude) |
| `MOTION_PROMPTS.md` | 영상 생성 프롬프트 | AI (Claude) |
| `CRITIQUE_LOG.md` | 피드백 기록 | AI (Claude) |

---

## 요구사항

- ffmpeg (키프레임 추출)
- jq (JSON 파싱, extract-smart.sh용)
- Gemini CLI
- Claude Code (Antigravity)

```bash
# macOS
brew install ffmpeg jq
```

---

## 라이선스

MIT License - 자유롭게 사용하세요!

---

> **Prompty** - AI와 함께하는 영상 파로디 제작
