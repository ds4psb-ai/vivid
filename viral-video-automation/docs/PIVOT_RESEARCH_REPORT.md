# 🔄 PIVOT RESEARCH REPORT: Tiki-Taka Academy Edition

> **Purpose**: Kling API → 수동 Tiki-Taka 피벗 전략 분석
> **Author**: Claude Analysis
> **Date**: 2026-02-02
> **Target**: 아카데미 교육 시작 (D-1)

---

## 📋 Executive Summary

### 현황 진단
- **Crebit/Vivid 플랫폼**: 복잡한 4-Layer 아키텍처, Kling API 의존
- **문제점**: API 비용, 불안정성, 완전자동화의 품질 한계
- **기회**: 이미 구축된 티키타카 워크플로우 문서 시스템 활용

### 피벗 방향
```
Before: [Backend API] → [Kling API] → [자동 생성]
After:  [Gemini CLI] ↔ [Claude Code] → [수동 도구] → [Human-in-the-Loop]
```

### 핵심 가치 제안
```
"AI가 대신 만들어주는 것" → "AI가 함께 만드는 것"
"완전 자동화" → "최적화된 반자동화 (Tiki-Taka)"
```

---

## 🏛️ PART 1: 기존 시스템 분석

### 1.1 Viral-Video-Automation 아키텍처 (이미 구축됨)

```
┌─────────────────────────────────────────────────────────────┐
│                    TIKI-TAKA SYSTEM v2.0                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stage 1: ANALYZE          Stage 2: IMAGE                    │
│  ┌─────────────────┐       ┌─────────────────┐              │
│  │ Gemini 3 Pro    │──────→│ NanoBanana Pro │              │
│  │ (영상 분석)      │       │ Midjourney V7  │              │
│  │ Cut Breakdown   │       │ ANCHOR System  │              │
│  └─────────────────┘       └─────────────────┘              │
│           ↓                         ↓                        │
│  Stage 3: VIDEO            Stage 4: ASSEMBLY                 │
│  ┌─────────────────┐       ┌─────────────────┐              │
│  │ Kling 2.6       │──────→│ CapCut/Premiere│              │
│  │ Sora 2 Pro      │       │ Final Edit     │              │
│  └─────────────────┘       └─────────────────┘              │
│                                                              │
│  ←←←←←←←←← TIKI-TAKA FEEDBACK LOOP →→→→→→→→→               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 이미 확보된 문서 자산 (총 40+ 문서)

| 카테고리 | 문서 | 상태 | 재활용성 |
|----------|------|------|----------|
| **Architecture** | ARCHITECTURE.md, PDR.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| **Workflow** | MODE_TIKITAKA.md, STAGE1-4.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| **Templates** | CRITIQUE_IMAGE/VIDEO.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| **Tool Guides** | TOOL_NANOBANANA/SORA2.md | ✅ 완료 | ⭐⭐⭐⭐ |
| **Quality** | GUARDRAILS.md, ERROR_RECOVERY.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| **State** | STATE.md, PROJECT_CONTEXT.md | ✅ 완료 | ⭐⭐⭐⭐⭐ |
| **Scripts** | init.sh, extract.sh, version.sh | ✅ 완료 | ⭐⭐⭐ |

### 1.3 핵심 설계 원칙 (PDR에서 채택된 것들)

| # | 결정 | 핵심 내용 |
|---|------|----------|
| PDR-001 | Dual Mode | ONE-SHOT (85%) vs TIKI-TAKA (98%) |
| PDR-002 | ANCHOR System | 캐릭터 얼굴 확정 먼저 |
| PDR-005 | Critique Self-Loop | AI 자동 평가 → Human 승인 |
| **PDR-006** | **E2E 자동화 거부** | **Human-in-the-Loop 필수** |
| PDR-010 | 4-Layer Guardrails | Data → Model → Output → Human |

---

## 🎯 PART 2: 피벗 전략

### 2.1 새로운 아키텍처: "Antigravity Tiki-Taka"

```
┌─────────────────────────────────────────────────────────────┐
│              ANTIGRAVITY TIKI-TAKA ACADEMY                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐          ┌──────────────┐                 │
│  │   GEMINI     │ ←──────→ │ CLAUDE CODE  │                 │
│  │   (분석/평가)  │  티키타카  │ (정제/생성)   │                 │
│  │              │  피드백    │ Antigravity  │                 │
│  └──────────────┘          └──────────────┘                 │
│         ↓                           ↓                        │
│  ┌──────────────┐          ┌──────────────┐                 │
│  │  NanoBanana  │          │  Kling/Sora  │                 │
│  │  Midjourney  │          │  (수동 업로드) │                 │
│  │  (이미지 생성) │          │              │                 │
│  └──────────────┘          └──────────────┘                 │
│                      ↓                                       │
│                ┌──────────────┐                              │
│                │    HUMAN     │                              │
│                │  (최종 판단)  │                              │
│                └──────────────┘                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 도구 스택 (경량화)

| 역할 | Before (Crebit) | After (Academy) |
|------|-----------------|-----------------|
| **분석 AI** | Backend API + Gemini | Gemini CLI (VPS) / Gemini Web |
| **정제 AI** | Backend API + Claude | Claude Code (Antigravity) |
| **이미지 생성** | Kling API | NanoBanana Pro (웹) / MJ (Discord) |
| **비디오 생성** | Kling API | Kling Web / Sora Web (수동) |
| **상태 관리** | PostgreSQL + Redis | Markdown 파일 (STATE.md) |
| **버전 관리** | DB | 폴더 + version.sh |

### 2.3 비용 비교

| 항목 | Before (API 기반) | After (수동 기반) |
|------|-------------------|-------------------|
| Gemini API | ~$50/월 | $0 (무료 티어) |
| Kling API | ~$100/월 | $10/월 (Pro 구독) |
| 서버 비용 | ~$50/월 (Railway) | $0 (로컬) |
| **총합** | **~$200/월** | **~$10/월** |

### 2.4 Image-to-Video 중심 전략

```
WHY: Text-to-Video는 불안정, Image-to-Video가 더 제어 가능

WORKFLOW:
1. [텍스트] → [이미지 프롬프트] → [이미지 생성] ← CRITIQUE
2. [확정 이미지] → [모션 프롬프트] → [비디오 생성] ← CRITIQUE
3. [확정 비디오들] → [편집] → [최종본]

ADVANTAGES:
- 이미지 단계에서 캐릭터/구도 확정 → 비디오 안정성 ↑
- ANCHOR 시스템 적용 가능
- Critique-Refine 루프 더 효과적
```

---

## 📚 PART 3: 아카데미 커리큘럼 제안

### 3.1 3-Day Intensive Workshop

#### Day 1: Foundation (4시간)

| 시간 | 세션 | 내용 | 실습 |
|------|------|------|------|
| 1h | Intro | 티키타카 철학, SSOT 개념 | - |
| 1h | Gemini | 영상 분석, JSON 출력 | 샘플 영상 분석 |
| 1h | Claude Code | 프롬프트 정제 | CLAUDE_REFINEMENT.md 실습 |
| 1h | Tools | NanoBanana, MJ 소개 | 첫 ANCHOR 생성 |

#### Day 2: Image Generation (4시간)

| 시간 | 세션 | 내용 | 실습 |
|------|------|------|------|
| 1h | ANCHOR | ANCHOR 시스템 심화 | Scene 2 확정 |
| 1h | Multi-Entity | 의상/배경 일관성 | 레퍼런스 추출 |
| 1h | Critique | CRITIQUE_IMAGE.md | PASS/REVISE/REJECT |
| 1h | Full Scene | 전체 씬 이미지 완성 | 10컷 이미지 생성 |

#### Day 3: Video Generation (4시간)

| 시간 | 세션 | 내용 | 실습 |
|------|------|------|------|
| 1h | I2V Basics | Image-to-Video 원리 | Kling Canvas 실습 |
| 1h | Motion | Beat Timing, Motion Score | Scene 1 비디오 |
| 1h | Frame Chaining | 씬 간 연결 | 프레임 추출 |
| 1h | Assembly | CapCut 편집 | 최종본 완성 |

### 3.2 학습자 레벨별 경로

```
BEGINNER (0-3개월):
  ONE-SHOT Mode → 템플릿 복붙 → 기본 품질 달성

INTERMEDIATE (3-6개월):
  TIKI-TAKA Mode → 피드백 루프 → 98% 품질 달성

ADVANCED (6개월+):
  템플릿 커스텀 → 새 프로젝트 구조 설계 → 강사 양성
```

### 3.3 프로젝트 기반 학습 (PBL)

```
Week 1: Kyle Nutt Parody (kylenutt-parody 예제)
  - 이미 분석 완료된 프로젝트로 학습
  - 10컷, 17초, 명확한 구조

Week 2: 자유 프로젝트
  - 학습자가 선택한 영상으로 패러디
  - init.sh로 프로젝트 초기화부터

Week 3: 포트폴리오 발표
  - 완성작 공유
  - Critique 리뷰
```

---

## 🔧 PART 4: 기존 백엔드 재활용 전략

### 4.1 재활용 가능 (Lite Mode)

| 컴포넌트 | 용도 | 재활용 방법 |
|----------|------|-------------|
| **RAG 시스템** | 거장 스타일 힌트 | NotebookLM만 사용 |
| **Gemini Client** | 분석/평가 | CLI로 대체 가능 |
| **환경변수** | API 키 | GEMINI_API_KEY 유지 |

### 4.2 재활용 불필요 (Academy에서 제외)

| 컴포넌트 | 이유 |
|----------|------|
| Kling API 통합 | 수동 웹 UI로 대체 |
| Run-Token 시스템 | 과금 체계 불필요 |
| Capsule Executor | 자동화 불필요 |
| PostgreSQL | Markdown으로 대체 |
| Redis | 세션 관리 불필요 |

### 4.3 OpenClaw Skill 활용

```bash
# VPS에 이미 설정된 Gemini CLI
ssh root@158.247.230.78

# Interactive 모드로 비디오 분석
gemini
> @{/root/.openclaw/media/inbound/video.mp4} Kyle Nutt 스타일로 분석해줘
```

**장점**:
- API 키 없이 OAuth로 무료 사용
- Native Vision으로 비디오 직접 분석
- ~/.gemini/GEMINI.md로 페르소나 설정

---

## 📊 PART 5: 새로운 워크플로우 (Antigravity Edition)

### 5.1 Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Project Setup                                        │
├─────────────────────────────────────────────────────────────┤
│ $ ./scripts/init.sh my-project                               │
│ $ cp ~/Downloads/source.mp4 projects/my-project/reference/   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Gemini Analysis (VPS or Web)                         │
├─────────────────────────────────────────────────────────────┤
│ [영상 업로드] + [GEMINI_ONESHOT.md 프롬프트]                   │
│ → JSON 출력 (씬 분해, 캐릭터, 도구 추천)                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Claude Code Refinement                               │
├─────────────────────────────────────────────────────────────┤
│ [JSON 붙여넣기] + "도구별 프롬프트로 변환해줘"                  │
│ → IMAGE_PROMPTS.md, MOTION_PROMPTS.md 생성                   │
│ → STATE.md 업데이트                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Image Generation (NanoBanana/MJ)                     │
├─────────────────────────────────────────────────────────────┤
│ ANCHOR 먼저 → 나머지 씬                                       │
│ [결과 첨부] → Claude: "Critique 해줘"                         │
│ PASS → 확정 / REVISE → 수정 / REJECT → 재시작                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Video Generation (Kling/Sora Web)                    │
├─────────────────────────────────────────────────────────────┤
│ [확정 이미지] + [Motion Prompt] → 도구 웹 업로드               │
│ [결과 첨부] → Claude: "Critique 해줘"                         │
│ Frame Chaining: 마지막 프레임 → 다음 씬 첫 프레임              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Assembly (CapCut)                                    │
├─────────────────────────────────────────────────────────────┤
│ 타임라인 구성 → 트랜지션 → 오디오 → 렌더링                     │
│ 최종본: generated/videos/selected/FINAL.mp4                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Tiki-Taka Loop Detail

```
┌──────────────────────────────────────────────────────────┐
│                    TIKI-TAKA LOOP                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│    USER              GEMINI              CLAUDE           │
│      │                  │                   │             │
│      │──[영상]─────────→│                   │             │
│      │                  │──[분석 JSON]─────→│             │
│      │                  │                   │             │
│      │←─────────────────│←─[정제 프롬프트]──│             │
│      │                                      │             │
│      │──[도구에서 생성]─────────────────────→│             │
│      │                                      │             │
│      │──[결과 이미지]───────────────────────→│             │
│      │                                      │             │
│      │←─────────────────[Critique]─────────│             │
│      │                                      │             │
│      │  PASS → 다음 씬                       │             │
│      │  REVISE → 수정 후 재생성              │             │
│      │  REJECT → 프롬프트 재검토             │             │
│      │                                      │             │
│      │──[다음 씬]───────────────────────────→│             │
│      │                  ...반복...           │             │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Quick Start Template (Claude Code용)

```markdown
# 🎾 Tiki-Taka Session

## Context
- Project: [PROJECT_NAME]
- Stage: [1-4]
- Current Scene: [N]

## 이전 대화 요약
- [요약]

## 현재 작업
- [작업 내용]

## 첨부 파일
- [이미지/영상 경로]

## 요청
- [분석 / Critique / 프롬프트 생성 / 수정]
```

---

## 🚀 PART 6: 실행 로드맵

### 6.1 D-Day 체크리스트 (아카데미 시작 전)

| # | 항목 | 상태 | 담당 |
|---|------|------|------|
| 1 | viral-video-automation 폴더 구조 확인 | ✅ | - |
| 2 | kylenutt-parody 예제 프로젝트 확인 | ✅ | - |
| 3 | VPS Gemini CLI 접속 테스트 | ⬜ | Ted |
| 4 | Claude Code (Antigravity) 설정 | ⬜ | Ted |
| 5 | NanoBanana Pro 계정 준비 | ⬜ | Ted |
| 6 | Kling Web 계정 준비 | ⬜ | Ted |
| 7 | 학습자 가이드 문서 정리 | ⬜ | Claude |

### 6.2 Week 1 목표

```
Day 1: 시스템 소개 + Gemini 분석 실습
Day 2: 이미지 생성 + Critique 실습
Day 3: 비디오 생성 + 편집 실습
Day 4-5: 개인 프로젝트 시작
Day 6-7: 피드백 + 수정
```

### 6.3 성공 지표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 프로젝트 완성률 | 80%+ | 최종본 제출 수 |
| 품질 점수 | 85%+ | Critique Self-Loop 점수 |
| 학습자 만족도 | 4.0+/5.0 | 설문조사 |
| 재수강률 | 50%+ | 다음 기수 등록 |

---

## 💡 PART 7: 핵심 인사이트

### 7.1 왜 이 피벗이 가능한가?

```
1. 이미 문서화 완료
   - 40+ 템플릿/가이드 존재
   - kylenutt-parody 예제 프로젝트 완성
   - SSOT 아키텍처 확립

2. Human-in-the-Loop이 오히려 강점
   - PDR-006에서 E2E 자동화 거부 결정
   - 품질은 사람의 판단이 핵심
   - 티키타카 = 반복 정제 > 한 번에 완벽

3. 도구 접근성 향상
   - Gemini CLI: OAuth로 무료
   - NanoBanana: 대화형 무료
   - Kling Web: $10/월 저렴
```

### 7.2 Crebit 플랫폼과의 관계

```
SHORT TERM (아카데미):
  - Crebit과 독립적으로 운영
  - viral-video-automation 폴더만 사용
  - 학습자 교육에 집중

MID TERM (검증 후):
  - 학습자 프로젝트 결과물 축적
  - 베스트 프랙티스 고도화
  - 커뮤니티 형성

LONG TERM (플랫폼 복귀):
  - 검증된 워크플로우를 Crebit에 통합
  - 반자동화 → 부분 자동화
  - Human Cloud 연계 가능
```

### 7.3 경쟁 우위

```
vs 완전 자동화 도구:
  ✅ 품질 제어 가능 (98% vs 60-70%)
  ✅ 캐릭터 일관성 (ANCHOR 시스템)
  ✅ 창작자 의도 반영

vs 수동 작업:
  ✅ 체계화된 워크플로우
  ✅ AI Critique로 품질 보장
  ✅ 반복 가능한 프로세스

vs 타 교육 프로그램:
  ✅ 실전 프로젝트 중심
  ✅ 문서화된 노하우 제공
  ✅ 즉시 적용 가능한 템플릿
```

---

## 📎 부록

### A. 핵심 파일 경로

```
viral-video-automation/
├── docs/
│   ├── ARCHITECTURE.md          # 시스템 아키텍처
│   ├── PDR.md                   # 설계 결정 기록
│   └── OPENCLAW_GEMINI_AUTH.md  # VPS Gemini 설정
├── templates/
│   ├── MODE_TIKITAKA.md         # 핵심 워크플로우
│   ├── STAGE1-4_*.md            # 단계별 가이드
│   ├── CRITIQUE_*.md            # 품질 평가
│   └── TOOL_*.md                # 도구별 가이드
├── scripts/
│   ├── init.sh                  # 프로젝트 초기화
│   ├── extract.sh               # 키프레임 추출
│   └── version.sh               # 버전 관리
└── projects/
    └── kylenutt-parody/         # 예제 프로젝트
```

### B. Quick Reference

```bash
# 새 프로젝트 시작
./scripts/init.sh my-project

# 키프레임 추출
./scripts/extract.sh my-project 10

# 버전 롤백
./scripts/version.sh rollback images v1

# VPS Gemini 접속
ssh root@158.247.230.78
gemini
```

### C. 추가 연구 필요 사항

1. **Gemini CLI 안정성 테스트**
   - YOLO 모드 버그 확인
   - Interactive 모드 세션 유지

2. **Claude Code 통합**
   - Antigravity 세션 관리
   - STATE.md 자동 업데이트

3. **학습자 피드백 수집 체계**
   - Critique 점수 기록
   - 프로젝트별 시간 측정

---

> **Prepared by**: Claude Code Analysis
> **For**: Ted / Crebit Academy
> **Status**: READY FOR REVIEW
> **Next Step**: D-Day 체크리스트 실행
