---
name: video-analyze
description: Gemini 3 Pro를 사용하여 비디오 파일을 직접 분석합니다. Kyle Nutt 스타일 분석, 컷 분석, 트랜지션 분석, 한국화 제안까지 지원합니다.
requirements:
  - python3
  - google-genai
---

# Video Analyze Skill

## 언제 사용하나요?
- 사용자가 비디오 파일(.mp4, .mov, .webm)을 첨부하고 분석을 요청할 때
- "이 영상 분석해줘", "비디오 Critique", "컷 분석" 등의 요청이 있을 때
- Kyle Nutt 스타일 분석, 바이럴 영상 분석 요청 시

## 사용 방법

### 1. 비디오 파일이 첨부되었을 때
```bash
python3 ~/.openclaw/skills/video-analyze/scripts/analyze_video.py "<video_path>" "<prompt>"
```

### 2. YouTube URL이 제공되었을 때
```bash
python3 ~/.openclaw/skills/video-analyze/scripts/analyze_video.py "<youtube_url>" "<prompt>"
```

## 분석 결과 형식

스크립트는 다음 형식으로 분석 결과를 반환합니다:

```
🎬 비디오 분석 결과

1. 컷 분석 (Cut-by-Cut)
   - 각 씬별 타임코드, 카메라 무빙, 조명/색감

2. 트랜지션 분석
   - 사용된 트랜지션 기법, Match Cut 포인트

3. 캐릭터 분석
   - 인물 설명, 감정 변화

4. 전체 구조
   - Hook, Build, Peak, Close

5. 한국판 오마주 제안
   - 한국 스타일 리메이크 아이디어
```

## 주의사항
- 비디오 파일은 2GB 이하여야 합니다
- 45분 이상 영상은 청크로 분할됩니다
- GEMINI_API_KEY 환경변수가 설정되어 있어야 합니다
