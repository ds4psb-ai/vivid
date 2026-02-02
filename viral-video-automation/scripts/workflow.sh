#!/bin/bash
# 🎬 Viral Video Parody Workflow v1.0
# 반자동화 워크플로우 오케스트레이터
#
# Usage: ./workflow.sh <project_name> <video_file>
# Example: ./workflow.sh kylenutt-parody videos/original.mp4

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Banner
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}🎬 VIRAL VIDEO PARODY WORKFLOW v1.0${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Arguments
PROJECT_NAME="$1"
VIDEO_FILE="$2"

if [ -z "$PROJECT_NAME" ] || [ -z "$VIDEO_FILE" ]; then
    echo -e "${RED}Usage: $0 <project_name> <video_file>${NC}"
    echo "Example: $0 kylenutt-parody videos/original.mp4"
    exit 1
fi

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$ROOT_DIR/projects/$PROJECT_NAME"
KEYFRAMES_DIR="$PROJECT_DIR/keyframes"
TEMPLATES_DIR="$ROOT_DIR/templates"

# Validate
if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}❌ Video file not found: $VIDEO_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Project:${NC} $PROJECT_NAME"
echo -e "${BLUE}📹 Video:${NC} $VIDEO_FILE"
echo ""

# Phase indicator
phase() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ============================================================
# PHASE 1: PROJECT SETUP
# ============================================================
phase "📂 PHASE 1: PROJECT SETUP"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${GREEN}Creating project directory...${NC}"
    mkdir -p "$PROJECT_DIR"
fi

# ============================================================
# PHASE 2: KEYFRAME EXTRACTION
# ============================================================
phase "📸 PHASE 2: KEYFRAME EXTRACTION"

if [ -d "$KEYFRAMES_DIR" ] && [ "$(ls -A "$KEYFRAMES_DIR"/*.png 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠️  Keyframes already exist. Skipping extraction.${NC}"
    echo "   Delete $KEYFRAMES_DIR to re-extract."
else
    echo -e "${GREEN}Extracting precision keyframes...${NC}"
    "$SCRIPT_DIR/extract-keyframes.sh" "$VIDEO_FILE" "$KEYFRAMES_DIR"
fi

echo ""
echo -e "${GREEN}✅ Keyframes ready:${NC}"
ls -la "$KEYFRAMES_DIR"/*.png 2>/dev/null | awk '{print "   📄 " $NF " (" $5 ")"}'

# ============================================================
# PHASE 3: GEMINI ANALYSIS (MANUAL)
# ============================================================
phase "🤖 PHASE 3: GEMINI VIDEO ANALYSIS"

echo -e "${CYAN}📋 MANUAL STEP REQUIRED${NC}"
echo ""
echo "1. Open Gemini: ${BLUE}https://gemini.google.com${NC}"
echo ""
echo "2. Upload the video: ${YELLOW}$VIDEO_FILE${NC}"
echo ""
echo "3. Copy and paste this template:"
echo "   ${GREEN}$TEMPLATES_DIR/GEMINI_VIDEO_ANALYSIS.md${NC}"
echo ""
echo "4. Get JSON response from Gemini"
echo ""
echo "5. Save response to: ${YELLOW}$PROJECT_DIR/gemini_analysis.json${NC}"
echo ""

# Check if analysis exists
if [ -f "$PROJECT_DIR/gemini_analysis.json" ]; then
    echo -e "${GREEN}✅ Gemini analysis found!${NC}"
    echo ""
    echo -e "${CYAN}Preview:${NC}"
    head -20 "$PROJECT_DIR/gemini_analysis.json"
else
    echo -e "${YELLOW}⏳ Waiting for Gemini analysis...${NC}"
    echo ""
    echo -e "Press ${GREEN}[Enter]${NC} after saving gemini_analysis.json, or ${RED}[Ctrl+C]${NC} to exit"
    read -r
    
    if [ ! -f "$PROJECT_DIR/gemini_analysis.json" ]; then
        echo -e "${RED}❌ gemini_analysis.json not found. Please save it and re-run.${NC}"
        exit 1
    fi
fi

# ============================================================
# PHASE 4: PROMPT GENERATION
# ============================================================
phase "✍️ PHASE 4: PROMPT GENERATION"

echo -e "${CYAN}📋 MANUAL STEP REQUIRED${NC}"
echo ""
echo "Pass the Gemini JSON to Claude with this request:"
echo ""
echo -e "${GREEN}────────────────────────────────────────${NC}"
cat << 'EOF'
이 Gemini 분석 결과를 바탕으로 FINAL_PROMPTS_MINIMAL.md를 업데이트해줘:

```json
[PASTE gemini_analysis.json HERE]
```

keyframes 폴더에 추출된 이미지들:
- ANCHOR_IMG.png
- scene01_arrival.png
- scene03_clapping.png
- scene04_blowout.png
- scene05a_cake_past.png
- scene05b_cake_present.png
- scene06_lonely.png
- scene07_selfie.png
EOF
echo -e "${GREEN}────────────────────────────────────────${NC}"
echo ""

# ============================================================
# PHASE 5: MIDJOURNEY GENERATION
# ============================================================
phase "🎨 PHASE 5: MIDJOURNEY GENERATION"

echo "Reference prompts:"
echo -e "   ${GREEN}$PROJECT_DIR/FINAL_PROMPTS_MINIMAL.md${NC}"
echo ""
echo "Workflow:"
echo "1. Upload keyframes to Discord"
echo "2. Copy image URLs"
echo "3. Generate ANCHOR first (Scene 2)"
echo "4. Use ANCHOR result for Scene 1, 3, 4"
echo "5. Generate remaining scenes"
echo ""

# ============================================================
# SUMMARY
# ============================================================
phase "📊 WORKFLOW SUMMARY"

echo -e "${GREEN}Project Files:${NC}"
echo "   📁 $PROJECT_DIR/"
echo "   ├── keyframes/          (extracted frames)"
echo "   ├── gemini_analysis.json (Gemini output)"
echo "   ├── FINAL_PROMPTS.md    (detailed version)"
echo "   └── FINAL_PROMPTS_MINIMAL.md (balanced version)"
echo ""
echo -e "${CYAN}Templates:${NC}"
echo "   📄 $TEMPLATES_DIR/GEMINI_VIDEO_ANALYSIS.md"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Workflow setup complete!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
