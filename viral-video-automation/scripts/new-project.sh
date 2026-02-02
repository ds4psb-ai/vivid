#!/bin/bash
# new-project.sh v4.0 - 새 프로젝트 자동 생성

PROJECT_NAME=$1

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Usage: ./scripts/new-project.sh <project-name>"
    echo "   Example: ./scripts/new-project.sh dance-challenge"
    exit 1
fi

BASE_DIR="/Users/ted/live/viral-video-automation/projects"
PROJECT_DIR="$BASE_DIR/$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Project already exists: $PROJECT_DIR"
    exit 1
fi

# 폴더 생성
mkdir -p "$PROJECT_DIR"/{reference,keyframes,generated}

# FINAL_PROMPTS.md 템플릿
cat > "$PROJECT_DIR/FINAL_PROMPTS.md" << 'EOF'
# 🎬 PROJECT: [PROJECT_NAME] (Korean Edition)

> **Core Concept**: [Gemini 분석 후 채우기]
> 
> ⚠️ **사용법**: 각 씬의 `[COPY THIS]` 블록 복사 → Nano Banana Pro에 붙여넣기

---

## 🔗 ANCHOR SYSTEM

### 생성 순서 (반드시 지키세요!)
```
1️⃣ SCENE [?] 먼저 생성 (ANCHOR) → anchor.png 저장
2️⃣ 나머지 씬 → anchor.png Reference
```

### Reference 관계도
| 씬 | Reference Image | Weight |
|----|-----------------|--------|
| ANCHOR | 없음 | - |
| ... | anchor.png | 0.5~0.7 |

---

## 📼 SCENE 1: [씬 이름] ([타임코드])

> **🔗 Reference**: [Gemini 분석 결과]
> **💾 저장**: `keyframes/scene01.png`

### 📐 구도 분석
(Gemini 분석 결과 붙여넣기)

### 🎨 색감/조명
(Gemini 분석 결과 붙여넣기)

```
[COPY THIS]

(Gemini가 생성한 완성 프롬프트)

--ar 9:16 --stylize [값] --v 6.0 --no text, timestamp, ...
```

### 🎬 Motion 가이드 (Kling용)
- Creativity: [값]
- Camera: [동작]
- Action: [설명]

---

(반복)

---

## 🛠️ TROUBLESHOOTING

(Gemini 분석 결과 붙여넣기)

---

## ✅ 체크리스트

| 순서 | Scene | 파일명 | Reference | 상태 |
|------|-------|--------|-----------|------|
| 1 | **ANCHOR** | `anchor.png` | 없음 | ⬜ |
| 2 | Scene 1 | `scene01.png` | anchor.png | ⬜ |
| ... | ... | ... | ... | ⬜ |
EOF

echo ""
echo "✅ Project created: $PROJECT_DIR"
echo ""
echo "📁 Structure:"
echo "   $PROJECT_DIR/"
echo "   ├── FINAL_PROMPTS.md  ← Gemini 출력 저장"
echo "   ├── reference/        ← 원본 영상"
echo "   ├── keyframes/        ← 생성 이미지"
echo "   └── output/           ← 최종 영상"
echo ""
echo "🚀 Next steps:"
echo ""
echo "   1. 레퍼런스 영상 저장:"
echo "      cp ~/Downloads/viral.mp4 $PROJECT_DIR/reference/"
echo ""
echo "   2. Gemini 분석 (ONE-SHOT):"
echo "      - templates/GEMINI_UNIFIED.md 복사"
echo "      - Gemini에 붙여넣기 + 영상 업로드"
echo "      - 출력을 FINAL_PROMPTS.md에 저장"
echo ""
echo "   3. Nano Banana Pro 이미지 생성:"
echo "      - ANCHOR 씬 먼저!"
echo "      - 각 씬의 [COPY THIS] 블록 복사/붙여넣기"
echo ""
echo "   4. Kling 영상 변환 → 편집 → 완성!"
echo ""
echo "📚 Reference project: projects/kylenutt-parody/"
echo ""
