#!/bin/bash
# Prompty Quick Start v2.0
# 원클릭 프로젝트 시작

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}"
echo "  ____                       _         "
echo " |  _ \ _ __ ___  _ __ ___ | |_ _   _ "
echo " | |_) | '__/ _ \| '_ \` _ \| __| | | |"
echo " |  __/| | | (_) | | | | | | |_| |_| |"
echo " |_|   |_|  \___/|_| |_| |_|\__|\__, |"
echo "                                |___/ "
echo -e "${NC}"
echo -e "${CYAN}AI Video Parody Project Starter v2.0${NC}"
echo ""

# 프로젝트 이름 입력
read -p "$(echo -e ${YELLOW}Project name: ${NC})" PROJECT_NAME

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Project name is required${NC}"
    exit 1
fi

# 영상 경로 입력 (선택)
echo ""
read -p "$(echo -e ${YELLOW}Video path \(Enter to skip\): ${NC})" VIDEO_PATH

# 프로젝트 생성
echo ""
echo -e "${BLUE}Creating project...${NC}"
"$BASE_DIR/scripts/init.sh" "$PROJECT_NAME"

PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"

# 영상 복사 (입력된 경우)
if [ -n "$VIDEO_PATH" ] && [ -f "$VIDEO_PATH" ]; then
    cp "$VIDEO_PATH" "$PROJECT_DIR/reference/source.mp4"
    echo -e "${GREEN}Video copied to reference/source.mp4${NC}"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Project created: $PROJECT_DIR${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "${BLUE}1. Terminal 1 - Gemini CLI:${NC}"
echo "   gemini"
echo "   > @{projects/$PROJECT_NAME/reference/source.mp4}"
echo "   > 이 영상 분석해줘 (KEYFRAMES_JSON 포함)"
echo ""
echo -e "${BLUE}2. Extract keyframes:${NC}"
echo "   ./scripts/extract-smart.sh $PROJECT_NAME"
echo ""
echo -e "${BLUE}3. Terminal 2 - Claude/Antigravity:${NC}"
echo "   cd projects/$PROJECT_NAME"
echo "   claude"
echo "   > docs/ANALYSIS.md 읽고 프롬프트 정제해줘"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Gemini JSON 요청 템플릿:${NC}"
echo ""
cat << 'TEMPLATE'
이 영상을 분석해줘. 아래 형식으로 출력:

## CUT-BY-CUT
| Cut | Timecode | Description |
|-----|----------|-------------|
| 1 | 00:00~00:02 | ... |

## ANCHOR 추천
- Cut #:
- 이유:

## KEYFRAMES_JSON (필수!)
<!-- KEYFRAMES_JSON
{"keyframes":[
  {"timestamp":"00:01.50","filename":"scene01","anchor":false},
  {"timestamp":"00:03.00","filename":"ANCHOR_IMG","anchor":true}
]}
-->
TEMPLATE
echo ""
