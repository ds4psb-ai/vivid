#!/usr/bin/env python3
"""
OpenClaw Video Analyze Skill
Gemini 3 Pro를 사용하여 비디오를 직접 분석합니다.

Usage:
    python3 analyze_video.py <video_path_or_url> [prompt]
    
Examples:
    python3 analyze_video.py /path/to/video.mp4 "이 영상을 Kyle Nutt 스타일로 분석해줘"
    python3 analyze_video.py "https://youtube.com/watch?v=xxx" "컷 분석해줘"
"""

import os
import sys
import time
import json
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai 패키지가 필요합니다.")
    print("설치: pip install google-genai")
    sys.exit(1)


# Gemini API 설정
try:
    from google.oauth2.credentials import Credentials
except ImportError:
    Credentials = None

API_KEY = os.environ.get("GEMINI_API_KEY")
ACCESS_TOKEN = os.environ.get("GEMINI_ACCESS_TOKEN")

if API_KEY:
    # API 키로 인증
    client = genai.Client(api_key=API_KEY)
    print("🔑 API Key 인증 사용")
elif ACCESS_TOKEN:
    # Access Token으로 직접 인증 (OpenClaw 내부용)
    if Credentials is None:
        print("Error: google-auth 패키지가 필요합니다.")
        print("설치: pip install google-auth")
        sys.exit(1)
    creds = Credentials(token=ACCESS_TOKEN)
    # google-genai Client에 credentials 전달
    client = genai.Client(credentials=creds)
    print("🔓 Access Token 인증 사용 (OpenClaw)")
else:
    # OAuth/ADC 자격증명 사용 (기본값)
    try:
        client = genai.Client()
        print("🔐 OAuth/ADC 자격증명 사용 (캐시된 로그인)")
    except Exception as e:
        print(f"Error: OAuth 자격증명을 찾을 수 없습니다.")
        print(f"       GEMINI_API_KEY 또는 GEMINI_ACCESS_TOKEN 환경변수를 설정해주세요.")
        print(f"       상세: {e}")
        sys.exit(1)


# 기본 분석 프롬프트 (Kyle Nutt 스타일)
DEFAULT_PROMPT = """
이 영상을 상세히 분석해주세요.

📋 분석 항목:

1. 컷 분석 (Cut-by-Cut)
   - 각 씬별 시작~끝 타임코드
   - 각 씬의 카메라 무빙 (Pan, Tilt, Dolly, Zoom 등)
   - 각 씬의 조명/색감 (색온도, 명암비, 필터)

2. 트랜지션 분석
   - 어떤 트랜지션 기법 사용? (Match Cut, Whip Pan, Dissolve 등)
   - Match Cut 포인트 있으면 타임코드와 함께 표시

3. 캐릭터 분석
   - 인물 설명 (외모, 의상, 연령대)
   - 감정 변화 흐름

4. 전체 구조
   - Hook (도입부): 어떻게 시선을 끄는가?
   - Build (전개): 어떻게 긴장감을 쌓는가?
   - Peak (절정): 가장 임팩트 있는 순간
   - Close (마무리): 어떻게 여운을 남기는가?

5. 한국인 버전 오마주 제안
   - 한국적 맥락으로 리메이크한다면 어떻게?
   - 소품, 장소, 문화적 요소 제안

영상의 분위기와 기법을 최대한 자세히 분석해주세요.
"""


def is_youtube_url(path: str) -> bool:
    """YouTube URL인지 확인"""
    youtube_patterns = [
        "youtube.com/watch",
        "youtu.be/",
        "youtube.com/shorts/",
        "youtube.com/embed/"
    ]
    return any(pattern in path.lower() for pattern in youtube_patterns)


def analyze_with_youtube_url(url: str, prompt: str) -> str:
    """YouTube URL로 직접 분석"""
    print(f"📺 YouTube URL 분석 중: {url}")
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[
            types.Content(
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        file_data=types.FileData(
                            file_uri=url,
                            mime_type="video/mp4"
                        )
                    )
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )
    )
    
    return response.text


def upload_video_file(video_path: str) -> str:
    """비디오 파일을 Gemini Files API로 업로드"""
    print(f"📤 비디오 업로드 중: {video_path}")
    
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {video_path}")
    
    # MIME 타입 결정
    mime_types = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska"
    }
    mime_type = mime_types.get(path.suffix.lower(), "video/mp4")
    
    # 파일 업로드
    with open(video_path, "rb") as f:
        file_data = f.read()
    
    # Files API로 업로드
    uploaded_file = client.files.upload(
        file=video_path,
        config=types.UploadFileConfig(
            display_name=path.name,
            mime_type=mime_type
        )
    )
    
    print(f"✅ 업로드 완료: {uploaded_file.name}")
    
    # 처리 완료 대기
    print("⏳ 비디오 처리 중...")
    while uploaded_file.state == "PROCESSING":
        time.sleep(5)
        uploaded_file = client.files.get(name=uploaded_file.name)
    
    if uploaded_file.state == "FAILED":
        raise Exception(f"비디오 처리 실패: {uploaded_file.state}")
    
    print("✅ 비디오 처리 완료!")
    return uploaded_file.uri


def analyze_with_file(file_uri: str, prompt: str) -> str:
    """업로드된 파일로 분석"""
    print("🔍 영상 분석 중...")
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[
            types.Content(
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        file_data=types.FileData(
                            file_uri=file_uri,
                            mime_type="video/mp4"
                        )
                    )
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )
    )
    
    return response.text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    video_input = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROMPT
    
    try:
        if is_youtube_url(video_input):
            # YouTube URL 직접 분석
            result = analyze_with_youtube_url(video_input, prompt)
        else:
            # 로컬 파일 업로드 후 분석
            file_uri = upload_video_file(video_input)
            result = analyze_with_file(file_uri, prompt)
        
        print("\n" + "="*60)
        print("🎬 비디오 분석 결과")
        print("="*60 + "\n")
        print(result)
        
    except FileNotFoundError as e:
        print(f"❌ 파일 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 분석 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
