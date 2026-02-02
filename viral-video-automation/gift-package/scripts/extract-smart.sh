#!/bin/bash
# extract-smart.sh v1.0 - Gemini 분석 결과에서 자동 키프레임 추출
# Usage: ./scripts/extract-smart.sh <project-name>
#
# ANALYSIS.md에 아래 형식의 JSON 블록이 필요:
# <!-- KEYFRAMES_JSON
# {"keyframes":[{"timestamp":"00:01.50","filename":"scene01","anchor":false},...]}
# -->

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_NAME=$1

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Usage: ./scripts/extract-smart.sh <project-name>${NC}"
    echo "   Example: ./scripts/extract-smart.sh dance-challenge"
    exit 1
fi

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"
ANALYSIS_FILE="$PROJECT_DIR/docs/ANALYSIS.md"
VIDEO_FILE="$PROJECT_DIR/reference/source.mp4"
OUTPUT_DIR="$PROJECT_DIR/reference/keyframes"

# 프로젝트 존재 확인
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Project not found: $PROJECT_DIR${NC}"
    exit 1
fi

# ANALYSIS.md 존재 확인
if [ ! -f "$ANALYSIS_FILE" ]; then
    echo -e "${RED}ANALYSIS.md not found: $ANALYSIS_FILE${NC}"
    echo "   Gemini로 영상 분석 후 docs/ANALYSIS.md를 생성하세요."
    exit 1
fi

# 영상 파일 존재 확인
if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}Video not found: $VIDEO_FILE${NC}"
    echo "   Copy your video: cp ~/Downloads/video.mp4 $VIDEO_FILE"
    exit 1
fi

# jq 존재 확인
if ! command -v jq &> /dev/null; then
    echo -e "${RED}jq가 설치되어 있지 않습니다.${NC}"
    echo "설치: brew install jq"
    exit 1
fi

echo -e "${BLUE}Smart Keyframe Extractor v1.0${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. ANALYSIS.md에서 JSON 블록 추출
echo -e "${YELLOW}Reading ANALYSIS.md...${NC}"
KEYFRAMES_JSON=$(sed -n '/<!-- KEYFRAMES_JSON/,/-->/p' "$ANALYSIS_FILE" | grep -v '<!--' | grep -v '-->' | tr -d '\n')

if [ -z "$KEYFRAMES_JSON" ]; then
    echo -e "${RED}KEYFRAMES_JSON not found in ANALYSIS.md${NC}"
    echo ""
    echo -e "${YELLOW}Gemini에게 다음 형식으로 JSON 블록 요청:${NC}"
    echo ""
    echo '<!-- KEYFRAMES_JSON'
    echo '{"keyframes":['
    echo '  {"timestamp":"00:01.50","filename":"scene01_arrival","anchor":false},'
    echo '  {"timestamp":"00:03.00","filename":"ANCHOR_IMG","anchor":true},'
    echo '  {"timestamp":"00:05.50","filename":"scene03_action","anchor":false}'
    echo ']}'
    echo '-->'
    echo ""
    exit 1
fi

# JSON 유효성 검사
if ! echo "$KEYFRAMES_JSON" | jq . > /dev/null 2>&1; then
    echo -e "${RED}Invalid JSON in KEYFRAMES_JSON block${NC}"
    echo "Raw content:"
    echo "$KEYFRAMES_JSON"
    exit 1
fi

# 키프레임 개수
KEYFRAME_COUNT=$(echo "$KEYFRAMES_JSON" | jq '.keyframes | length')
echo -e "${GREEN}Found $KEYFRAME_COUNT keyframes${NC}"
echo ""

# 2. 출력 폴더 생성
mkdir -p "$OUTPUT_DIR"

# 3. 각 키프레임 추출
echo -e "${BLUE}Extracting keyframes...${NC}"
echo ""

echo "$KEYFRAMES_JSON" | jq -r '.keyframes[] | "\(.timestamp)|\(.filename)|\(.anchor)|\(.description // "")"' | while IFS='|' read -r timestamp filename anchor description; do
    output_file="$OUTPUT_DIR/${filename}.png"

    if [ "$anchor" == "true" ]; then
        echo -e "${YELLOW}$timestamp${NC} ${CYAN}$filename.png${NC} ${GREEN}(ANCHOR)${NC}"
    else
        echo -e "${YELLOW}$timestamp${NC} ${CYAN}$filename.png${NC}"
    fi

    if [ -n "$description" ]; then
        echo -e "    ${CYAN}$description${NC}"
    fi

    # ffmpeg로 프레임 추출
    ffmpeg -ss "$timestamp" -i "$VIDEO_FILE" -vframes 1 -q:v 1 "$output_file" -y -loglevel error

    # 파일 검증
    if [ -f "$output_file" ]; then
        size=$(ls -lh "$output_file" | awk '{print $5}')
        dims=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$output_file" 2>/dev/null || echo "?")
        echo -e "    ${GREEN}Saved ($size, $dims)${NC}"
    else
        echo -e "    ${RED}Failed to extract${NC}"
    fi
    echo ""
done

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Keyframes extracted to: $OUTPUT_DIR/${NC}"
echo ""

# 추출된 파일 목록
echo -e "${BLUE}Extracted files:${NC}"
ls -la "$OUTPUT_DIR"/*.png 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. ANCHOR 이미지를 NanoBanana/Midjourney에서 먼저 생성"
echo "  2. ANCHOR 결과물 URL을 다른 Scene 프롬프트에 추가"
echo "  3. 나머지 Scene 순차 생성 (티키타카!)"
echo ""
