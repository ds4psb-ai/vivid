# AI 숏폼 마스터피스 스튜디오

> 퀄리티 중심의 30초 AI 영상 제작 워크플로우

## 🎯 핵심 철학

**자동화 < 퀄리티**  
복잡한 파이프라인 대신, 각 단계에서 최고 품질을 만드는 데 집중

## 📁 프로젝트 구조

```
viral-video-automation/
├── assets/              # 소스 자료
│   ├── references/      # 영감 이미지/영상
│   ├── mixboard/        # Mixboard 생성 이미지
│   └── elements/        # 캐릭터/배경 에셋
│
├── projects/            # 프로젝트별 폴더
│   └── [project-name]/
│       ├── brief.md     # 콘셉트 & 스크립트
│       ├── storyboard/  # Mixboard 장면들
│       └── output/      # 최종 영상
│
├── prompts/             # 마스터 프롬프트
│   ├── gemini-video.md  # Gemini 영상 생성용
│   ├── kling-image.md   # Kling 이미지용
│   └── mixboard.md      # Mixboard 스타일용
│
└── workflow.md          # 워크플로우 가이드
```

## 🎬 워크플로우

```
1. 아이디어 스케치
   ↓
2. Google Mixboard로 무드보드/장면 생성
   ↓
3. Gemini 채팅에 이미지 + 마스터 프롬프트 입력
   ↓
4. 30초 숏폼 영상 생성 & 리파인
   ↓
5. 완성작 저장
```

## 🚀 빠른 시작

1. `workflow.md` 읽고 단계별 따라하기
2. `prompts/` 폴더의 마스터 프롬프트 활용
3. 각 프로젝트는 `projects/` 아래 폴더로 관리
