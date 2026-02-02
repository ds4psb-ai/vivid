# 🏛️ Viral Video Automation - Architecture (SSOT)

> **Single Source of Truth** for the AI Video Parody System
> **Version**: 2.0 (Tiki-Taka Edition)
> **Last Updated**: 2026-02-02

---

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIRAL VIDEO AUTOMATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   ANALYZE   │ → │   GENERATE  │ → │   ASSEMBLE  │         │
│  │  (Gemini)   │    │ (NB/MJ/K/S) │    │  (CapCut)   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         ↑                  ↑                  ↑                │
│         └──────── TIKI-TAKA FEEDBACK LOOP ───┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Core Philosophy

### Tiki-Taka Workflow

```
"반복 정제 > 한 번에 완벽"
```

| 원칙 | 설명 |
|------|------|
| **Iterative Refinement** | 5-6회 왕복으로 98% 품질 달성 |
| **AI Self-Critique** | Gemini → Claude 교차 검증 |
| **Human-in-the-Loop** | 최종 결정은 항상 사람 |
| **Feedback Loop** | 발견 → 개선 → 템플릿 고도화 |

---

## 🔧 Tool Stack

### Image Generation

| Tool | Strength | Use Case |
|------|----------|----------|
| **NanoBanana Pro** | 14 refs, 4K, conversation | 복합 구도, 다인물 |
| **Midjourney v7** | --oref, 얼굴 일관성 | ANCHOR, 클로즈업 |

### Video Generation

| Tool | Strength | Use Case |
|------|----------|----------|
| **Kling 2.6** | Elements 4, Motion Control | 대사 없음, 동작 |
| **Sora 2 Pro** | Physics, 25초, Cinematic | 고퀄리티 시네마틱 |

### Analysis & Orchestration

| Tool | Role |
|------|------|
| **Gemini** | 영상 분석, Success Brief, Critique |
| **Claude/Antigravity** | 프롬프트 생성, 정제, 대화형 피드백 |

---

## 📁 Directory Structure

```
viral-video-automation/
├── docs/                      # ← YOU ARE HERE
│   ├── ARCHITECTURE.md        # SSOT 아키텍처
│   └── PDR.md                 # 설계 결정 기록
│
├── templates/                 # 워크플로우 템플릿
│   ├── MODE_TIKITAKA.md       # 핵심 워크플로우
│   ├── STAGE1_ANALYSIS.md     # 분석 단계
│   ├── STAGE2_IMAGE.md        # 이미지 생성
│   ├── STAGE3_VIDEO.md        # 영상 생성
│   ├── STAGE4_ASSEMBLY.md     # 조립
│   ├── CRITIQUE_*.md          # 품질 평가
│   ├── TOOL_*.md              # 도구별 가이드
│   ├── MULTI_ENTITY.md        # 다중 엔티티 일관성
│   ├── FRAME_CHAINING.md      # 프레임 연결
│   └── CRITIQUE_SELFLOOP.md   # AI 자동 평가
│
├── scripts/                   # 자동화 스크립트
│   ├── init.sh                # 프로젝트 생성
│   ├── extract.sh             # 키프레임 추출
│   └── version.sh             # 버전 관리
│
├── projects/                  # 프로젝트별 폴더
│   └── {project-name}/
│       ├── reference/         # 원본 영상, 키프레임
│       ├── generated/         # 생성물
│       ├── prompts/           # 프롬프트
│       ├── docs/              # 프로젝트 문서
│       └── legacy/            # 이전 버전
│
└── SYSTEM_GUIDE.md            # 마스터 가이드
```

---

## 🔄 Workflow Stages

### Stage 1: Analysis (Gemini)
```
Input:  원본 영상
Output: Cut Breakdown, Character Profiles, Style Guide
Tool:   Gemini (영상 업로드)
```

### Stage 2: Image Generation (NanoBanana/MJ)
```
Input:  분석 결과, 키프레임
Output: 씬별 이미지
Tool:   NanoBanana Pro / Midjourney v7
Loop:   Generate → Critique → Revise
```

### Stage 3: Video Generation (Kling/Sora)
```
Input:  확정 이미지
Output: 씬별 영상 클립
Tool:   Kling 2.6 / Sora 2 Pro
Loop:   Generate → Critique → Revise
```

### Stage 4: Assembly (CapCut)
```
Input:  확정 영상 클립
Output: 최종 편집본
Tool:   CapCut / Premiere
```

---

## 🔗 Key Concepts

### ANCHOR System
```
1. ANCHOR 씬 먼저 생성 (캐릭터 얼굴 확정)
2. 나머지 씬에서 ANCHOR를 레퍼런스로 사용
3. 캐릭터 일관성 유지
```

### Multi-Entity Consistency
```
캐릭터 + 의상 + 소품 + 배경 모두 일관성 유지
Kling Elements 4슬롯 / NanoBanana 14레퍼런스 활용
```

### Frame Chaining
```
Scene N 마지막 프레임 → Scene N+1 첫 프레임
끊김 없는 영상 연결
```

### Critique Self-Loop
```
Generate → AI Self-Critique → Improvement → Human Approval
PASS / REVISE / REJECT 판정
```

---

## 📊 Quality Metrics

| Mode | Iterations | Time | Quality |
|------|------------|------|---------|
| ONE-SHOT | 2회 | 10분 | 85% |
| TIKI-TAKA | 5-6회 | 30분 | 98% |

---

## 📚 References

| Document | Purpose |
|----------|---------|
| [SYSTEM_GUIDE.md](../SYSTEM_GUIDE.md) | 마스터 가이드 |
| [MODE_TIKITAKA.md](../templates/MODE_TIKITAKA.md) | 티키타카 워크플로우 |
| [PDR.md](./PDR.md) | 설계 결정 기록 |

---

> **Maintainer**: Ted
> **Contact**: viral-video-automation
