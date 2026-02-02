#!/bin/bash
# init.sh v1.0 - 티키타카 프로젝트 초기화
# Usage: ./scripts/init.sh <project-name>

set -e

PROJECT_NAME=$1

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Usage: ./scripts/init.sh <project-name>"
    echo "   Example: ./scripts/init.sh dance-challenge"
    exit 1
fi

BASE_DIR="/Users/ted/live/viral-video-automation"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Project already exists: $PROJECT_DIR"
    exit 1
fi

echo "🚀 Creating project: $PROJECT_NAME"
echo ""

# ====== 디렉토리 구조 생성 ======
mkdir -p "$PROJECT_DIR"/{reference/keyframes,generated/{images/{v1,v2,selected},videos/{kling,sora,selected}},prompts,docs}

# ====== brief.md 생성 ======
cat > "$PROJECT_DIR/brief.md" << EOF
# 📋 Project Brief: $PROJECT_NAME

> **Created**: $(date +%Y-%m-%d)
> **Status**: 🔴 Not Started

---

## 🎯 Concept

(프로젝트 컨셉 설명)

---

## 📹 Reference

- **Source**: \`reference/source.mp4\`
- **Duration**: 
- **Cut Count**: 

---

## 📊 Progress

| Stage | Status |
|-------|--------|
| 1. Analysis | ⬜ |
| 2. Image | ⬜ |
| 3. Video | ⬜ |
| 4. Assembly | ⬜ |

---

## 📝 Notes

(작업 노트)
EOF

# ====== PROJECT_CONTEXT.md 생성 ======
cat > "$PROJECT_DIR/PROJECT_CONTEXT.md" << EOF
# Project Context: $PROJECT_NAME

> **Purpose**: AI가 읽고 즉시 프로젝트 맥락 파악
> **Updated**: $(date +%Y-%m-%d)

---

## 🎯 Goal

(한 줄 프로젝트 목표)

---

## 📹 Source

| 항목 | 값 |
|------|-----|
| **File** | reference/source.mp4 |
| **Duration** | (초)s |
| **Cuts** | (컷 수) |

---

## 👥 Characters

| ID | Role | Description |
|----|------|-------------|
| CHAR_A | 주인공 | Korean, 나이, 특징 |

---

## 🎨 Visual Style

| 항목 | 값 |
|------|-----|
| **Color Grade** | |
| **Lighting** | |
| **Era** | |

---

## 📋 Current Status

| Stage | Status |
|-------|--------|
| 1. Analysis | ⬜ |
| 2. Image | ⬜ |
| 3. Video | ⬜ |
| 4. Assembly | ⬜ |

---

## ✅ Completed

- [ ] 아직 없음

---

## 🚧 In Progress

- [ ] 프로젝트 시작

---

## 📌 Key Decisions

| 결정 | 내용 |
|------|------|
| ANCHOR | (미정) |
| Image Tool | NanoBanana / Midjourney |
| Video Tool | Kling / Sora |

---

## 🤖 AI Instructions

### Role
티키타카 방식 AI Video Parody 전문가

### Allowed
- 프롬프트 생성/수정
- CRITIQUE 수행
- 개선 제안
- STATE.md 업데이트

### Constraints
- API 호출 금지 (사용자 수동 복붙)
- 한 번에 1씬씩 진행
- ANCHOR 기준 일관성 유지
EOF

# ====== STATE.md 생성 ======
cat > "$PROJECT_DIR/STATE.md" << EOF
# State: $PROJECT_NAME

> **Purpose**: 동적 진행 상황 추적 (AI가 업데이트)
> **Last Updated**: $(date +"%Y-%m-%d %H:%M")

---

## 📊 Scene Progress

| Scene | Description | Image | Video | Status |
|-------|-------------|-------|-------|--------|
| 1 | - | - | - | ⬜ |
| 2 | - | - | - | ⬜ |
| 3 | - | - | - | ⬜ |

---

## 📈 Overall Progress

\`\`\`
Stage 1 (Analysis):  ░░░░░░░░░░░░░░░░░░░░   0%
Stage 2 (Image):     ░░░░░░░░░░░░░░░░░░░░   0%
Stage 3 (Video):     ░░░░░░░░░░░░░░░░░░░░   0%
Stage 4 (Assembly):  ░░░░░░░░░░░░░░░░░░░░   0%
\`\`\`

---

## 🚧 Current Task

(현재 작업)

---

## 💬 Last Conversation Summary

\`\`\`
아직 대화 없음
\`\`\`

---

## 📝 Session Notes

### $(date +%Y-%m-%d)
- 프로젝트 생성

---

## 📌 Quick Resume Prompt

\`\`\`
"지난 작업 이어서 하자. STATE.md 보고 다음 할 일 알려줘."
\`\`\`
EOF

# ====== prompts/IMAGE_PROMPTS.md 생성 ======
cat > "$PROJECT_DIR/prompts/IMAGE_PROMPTS.md" << 'EOF'
# 🎨 Image Prompts

> **Project**: [NAME]
> **Tool**: NanoBanana / Midjourney

---

## 🔗 ANCHOR 시스템

| 순서 | Scene | Reference | Status |
|------|-------|-----------|--------|
| 1 | **ANCHOR** | 없음 | ⬜ |
| 2 | Scene 1 | anchor.png | ⬜ |

---

## 📼 ANCHOR Scene

### [📋 COPY]
```
(프롬프트)
```

---

## 📼 Scene 1: [이름]

### [📋 COPY]
```
(프롬프트)
```

---

(반복)
EOF

# ====== prompts/MOTION_PROMPTS.md 생성 ======
cat > "$PROJECT_DIR/prompts/MOTION_PROMPTS.md" << 'EOF'
# 🎬 Motion Prompts

> **Project**: [NAME]
> **Tool**: Kling 2.0 / Sora 2 Pro

---

## ⚙️ Global Settings

| 항목 | 값 |
|------|-----|
| **Model** | Kling 2.0 High Quality |
| **Duration** | 5s (trim to use) |
| **Aspect** | 9:16 |

---

## 📼 Scene 1: [이름]

> **Use**: 0~Xs

### [📋 COPY] Positive
```
(프롬프트)
```

### [📋 COPY] Negative
```
(네거티브)
```

| Camera | Motion Score |
|--------|-------------|
| Static | **4** |

---

(반복)
EOF

# ====== docs/ANALYSIS.md 생성 ======
cat > "$PROJECT_DIR/docs/ANALYSIS.md" << 'EOF'
# 📊 Video Analysis

> **Analyzed by**: Gemini
> **Date**: 

---

## 📹 Source Video

- **File**: `reference/source.mp4`
- **Duration**: 
- **Resolution**: 

---

## 🎬 Cut Breakdown

| Scene | Timecode | Duration | Description |
|-------|----------|----------|-------------|
| 1 | 00:00~00:XX | Xs | |

---

## 👤 Character Profiles

(캐릭터 분석)

---

## 🎨 Visual Style

(시각 스타일 분석)

---

## 📝 Notes

(분석 노트)
EOF

# ====== docs/CRITIQUE_LOG.md 생성 ======
cat > "$PROJECT_DIR/docs/CRITIQUE_LOG.md" << 'EOF'
# 📝 Critique Log

> **Project**: [NAME]
> **Purpose**: 티키타카 피드백 기록

---

## 🎨 Image Critiques

### Scene 1

**v1 (날짜)**
- ✅ 강점: 
- ❌ 약점: 
- 💡 개선: 

**v2 (날짜)**
- 결과: 

---

## 🎬 Video Critiques

### Scene 1

**v1 (날짜)**
- ✅ 강점: 
- ❌ 약점: 
- 💡 개선: 

---
EOF

# ====== docs/PROFILES.md 생성 ======
cat > "$PROJECT_DIR/docs/PROFILES.md" << 'EOF'
# 👥 Character Profiles

> **Purpose**: 캐릭터 일관성 유지

---

## 👤 Main Character

| 속성 | 값 |
|------|-----|
| **나이** | |
| **성별** | |
| **인종** | Korean |
| **헤어** | |
| **의상** | |
| **특징** | |

### Reference Keywords
```
(프롬프트에 사용할 키워드)
```

---

## 👤 Supporting Characters

(반복)
EOF

echo "✅ Project created: $PROJECT_DIR"
echo ""
echo "📁 Structure:"
echo "   $PROJECT_DIR/"
echo "   ├── brief.md               ← 프로젝트 개요"
echo "   ├── reference/"
echo "   │   ├── source.mp4         ← 원본 영상"
echo "   │   └── keyframes/         ← 키프레임"
echo "   ├── generated/"
echo "   │   ├── images/{v1,v2,selected}"
echo "   │   └── videos/{kling,sora,selected}"
echo "   ├── prompts/"
echo "   │   ├── IMAGE_PROMPTS.md"
echo "   │   └── MOTION_PROMPTS.md"
echo "   └── docs/"
echo "       ├── ANALYSIS.md"
echo "       ├── PROFILES.md"
echo "       └── CRITIQUE_LOG.md"
echo ""
echo "🚀 Next steps:"
echo ""
echo "   1. 레퍼런스 영상 저장:"
echo "      cp ~/Downloads/video.mp4 $PROJECT_DIR/reference/source.mp4"
echo ""
echo "   2. Stage 1 - 영상 분석:"
echo "      Gemini에 영상 업로드 → docs/ANALYSIS.md 작성"
echo ""
echo "   3. 키프레임 추출:"
echo "      ./scripts/extract.sh $PROJECT_NAME"
echo ""
echo "   4. 티키타카 시작! 🎾"
echo ""
