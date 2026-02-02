#!/bin/bash
# OpenClaw Video Analyze 스킬 설치 스크립트
# VPS에서 실행해주세요

set -e

SKILL_NAME="video-analyze"
OPENCLAW_SKILLS_DIR="${HOME}/.openclaw/skills"
SOURCE_DIR="$(dirname "$0")/.."

echo "🚀 OpenClaw Video Analyze 스킬 설치 시작..."

# 1. 스킬 디렉토리 생성
echo "📁 스킬 디렉토리 생성..."
mkdir -p "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/scripts"

# 2. 파일 복사
echo "📋 스킬 파일 복사..."
cp "${SOURCE_DIR}/SKILL.md" "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/"
cp "${SOURCE_DIR}/scripts/analyze_video.py" "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/scripts/"
cp "${SOURCE_DIR}/scripts/requirements.txt" "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/scripts/"

# 3. Python 의존성 설치
echo "📦 Python 의존성 설치..."
pip3 install -r "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/scripts/requirements.txt"

# 4. 실행 권한 부여
echo "🔐 실행 권한 설정..."
chmod +x "${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}/scripts/analyze_video.py"

# 5. OAuth 로그인 확인
echo "🔐 인증 확인..."
if command -v gemini &> /dev/null; then
    # Gemini CLI 설치되어 있으면 로그인 상태 확인
    if gemini auth status &> /dev/null; then
        echo "✅ Gemini CLI OAuth 로그인됨 - API 키 없이 사용 가능!"
    else
        echo ""
        echo "⚠️  Gemini CLI가 로그인되어 있지 않습니다."
        echo "   다음 명령어로 로그인하세요:"
        echo ""
        echo "   gemini auth login"
        echo ""
        echo "   또는 GEMINI_API_KEY 환경변수를 설정할 수도 있습니다."
    fi
else
    if [ -z "$GEMINI_API_KEY" ]; then
        echo ""
        echo "⚠️  Gemini CLI가 없고 GEMINI_API_KEY도 없습니다."
        echo "   다음 중 하나를 설정하세요:"
        echo ""
        echo "   옵션 1: Gemini CLI 설치 후 로그인"
        echo "   옵션 2: export GEMINI_API_KEY='your-key'"
    fi
fi

echo ""
echo "✅ 설치 완료!"
echo ""
echo "📍 스킬 위치: ${OPENCLAW_SKILLS_DIR}/${SKILL_NAME}"
echo ""
echo "🎬 사용법:"
echo "   python3 ~/.openclaw/skills/video-analyze/scripts/analyze_video.py <video_path> [prompt]"
echo ""
echo "📺 YouTube URL 분석:"
echo "   python3 ~/.openclaw/skills/video-analyze/scripts/analyze_video.py 'https://youtu.be/xxx' '분석해줘'"
echo ""
