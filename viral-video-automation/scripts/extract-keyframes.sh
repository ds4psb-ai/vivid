#!/bin/bash
# 🎬 Keyframe Extractor v2.0 (Precision Capture)
# Usage: ./extract-keyframes.sh <video_file> [output_dir]
# 
# 전문가 분석 기반 1/100초 정밀 타임스탬프로 Keyframe 추출
# Motion Blur/Transition 없는 최적의 프레임만 캡처

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ ffmpeg가 설치되어 있지 않습니다.${NC}"
    echo "설치: brew install ffmpeg"
    exit 1
fi

# Arguments
VIDEO_FILE="$1"
OUTPUT_DIR="${2:-./keyframes}"

if [ -z "$VIDEO_FILE" ]; then
    echo -e "${RED}Usage: $0 <video_file> [output_dir]${NC}"
    echo "Example: $0 reference/123.mp4 keyframes/"
    exit 1
fi

if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}❌ 파일을 찾을 수 없습니다: $VIDEO_FILE${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}🎬 Keyframe Extractor v2.0 (Precision Capture)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📹 Video: $VIDEO_FILE"
echo -e "📁 Output: $OUTPUT_DIR"
echo ""
echo -e "${YELLOW}💡 전문가 분석 기반 1/100초 정밀 타임스탬프 사용${NC}"
echo ""

# Define PRECISION keyframe timestamps (SS.CC format = seconds.centiseconds)
# Format: "timestamp|filename|description|reason"
# 10-CUT VERSION (v3.0) - 전문가 검증 타임코드
KEYFRAMES=(
    "00:00.50|scene01_arrival|Scene 1 - Arrival|엄마 케이크 들고 등장"
    "00:01.50|ANCHOR_IMG|Scene 2 - Anchor ⭐|아이 단독 클로즈업 정면"
    "00:03.00|scene03_sideview|Scene 3 - Side View|측면 앵글 가족 반응"
    "00:05.00|scene04_clapping_a|Scene 4 - Clapping A|박수 초반 노래 시작"
    "00:07.00|scene05_clapping_b|Scene 5 - Clapping B|박수 클라이맥스"
    "00:08.30|scene06_pre_blow|Scene 6 - Pre-Blow|숨 들이마시기 직전"
    "00:09.00|scene07_blowout|Scene 7 - Blowout|촛불 끄는 순간"
    "00:10.00|scene08_glitch|Scene 8 - Glitch|케이크 모핑 전환 중간"
    "00:12.00|scene09_isolation|Scene 9 - Isolation|플래시 세례"
    "00:15.00|scene10_selfie|Scene 10 - Selfie|셀카 엔딩"
)

echo -e "${GREEN}📸 Extracting precision keyframes (8 frames)...${NC}"
echo ""

for keyframe in "${KEYFRAMES[@]}"; do
    IFS='|' read -r timestamp filename description reason <<< "$keyframe"
    
    output_file="$OUTPUT_DIR/${filename}.png"
    
    echo -e "${YELLOW}⏱️  $timestamp${NC} → ${BLUE}$filename.png${NC}"
    echo -e "    📝 $description"
    echo -e "    ${CYAN}💡 $reason${NC}"
    
    # Extract frame with HIGHEST quality
    # -ss: seek to timestamp (supports SS.CC format)
    # -vframes 1: extract 1 frame
    # -q:v 1: highest quality (1-31, lower is better)
    # -pix_fmt rgb24: full color
    ffmpeg -ss "$timestamp" -i "$VIDEO_FILE" -vframes 1 -q:v 1 "$output_file" -y -loglevel error
    
    if [ -f "$output_file" ]; then
        # Get file size and dimensions
        size=$(ls -lh "$output_file" | awk '{print $5}')
        dims=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$output_file" 2>/dev/null || echo "?")
        echo -e "    ${GREEN}✅ Saved ($size, $dims)${NC}"
    else
        echo -e "    ${RED}❌ Failed${NC}"
    fi
    echo ""
done

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 완료! 추출된 키프레임:${NC}"
echo ""

# Show extracted files with details
for f in "$OUTPUT_DIR"/scene*.png "$OUTPUT_DIR"/ANCHOR_IMG.png; do
    if [ -f "$f" ]; then
        basename "$f"
    fi
done 2>/dev/null | sort | while read fname; do
    filepath="$OUTPUT_DIR/$fname"
    if [ -f "$filepath" ]; then
        size=$(ls -lh "$filepath" | awk '{print $5}')
        echo -e "   📄 $fname ($size)"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📋 PRODUCTION WORKFLOW:${NC}"
echo ""
echo -e "  ${GREEN}1.${NC} Discord에 이미지들을 업로드"
echo -e "  ${GREEN}2.${NC} 각 이미지 URL 복사"
echo -e "  ${GREEN}3.${NC} FINAL_PROMPTS.md의 [Insert URL] 부분에 붙여넣기"
echo ""
echo -e "${RED}⚠️  ANCHOR FIRST RULE:${NC}"
echo -e "   ANCHOR_IMG.png를 먼저 Midjourney에서 생성하고,"
echo -e "   그 ${YELLOW}결과물 URL${NC}을 Scene 1, 3, 4에 추가하세요!"
echo ""
echo -e "${CYAN}🪞 VISUAL RHYME CHECK:${NC}"
echo -e "   Scene 3 (박수) ↔ Scene 6 (플래시) 구도 일치 확인!"
