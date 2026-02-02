#!/bin/bash
# extract.sh v2.0 - 키프레임 추출 (티키타카 버전)
# Usage: ./scripts/extract.sh <project-name> [scene-count]

set -e

PROJECT_NAME=$1
SCENE_COUNT=${2:-10}  # 기본값 10개 씬

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Usage: ./scripts/extract.sh <project-name> [scene-count]"
    echo "   Example: ./scripts/extract.sh kylenutt-parody 10"
    exit 1
fi

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"
VIDEO_FILE="$PROJECT_DIR/reference/source.mp4"
OUTPUT_DIR="$PROJECT_DIR/reference/keyframes"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project not found: $PROJECT_DIR"
    echo "   Run: ./scripts/init.sh $PROJECT_NAME"
    exit 1
fi

if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ Video not found: $VIDEO_FILE"
    echo "   Copy your video: cp ~/Downloads/video.mp4 $VIDEO_FILE"
    exit 1
fi

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

echo "🎬 Extracting keyframes from: $VIDEO_FILE"
echo "   Output: $OUTPUT_DIR"
echo "   Scenes: $SCENE_COUNT"
echo ""

# 영상 길이 가져오기
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE" 2>/dev/null)
INTERVAL=$(echo "$DURATION / $SCENE_COUNT" | bc -l)

echo "   Duration: ${DURATION}s"
echo "   Interval: ${INTERVAL}s per scene"
echo ""

# 균등 간격으로 프레임 추출
for i in $(seq 1 $SCENE_COUNT); do
    TIMESTAMP=$(echo "($i - 1) * $INTERVAL + ($INTERVAL / 2)" | bc -l)
    FORMATTED_TS=$(printf "%05.2f" $TIMESTAMP)
    OUTPUT_FILE="$OUTPUT_DIR/scene$(printf '%02d' $i)_${FORMATTED_TS}s.png"
    
    echo "   📸 Scene $i: ${FORMATTED_TS}s"
    ffmpeg -ss $TIMESTAMP -i "$VIDEO_FILE" -vframes 1 -q:v 2 "$OUTPUT_FILE" -y 2>/dev/null
done

echo ""
echo "✅ Extracted $SCENE_COUNT keyframes"
echo ""
echo "📁 Files:"
ls -la "$OUTPUT_DIR"
echo ""
echo "🚀 Next: Gemini로 각 키프레임 분석 → prompts/IMAGE_PROMPTS.md 작성"
echo ""
