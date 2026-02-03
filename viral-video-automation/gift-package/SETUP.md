# 📦 패키지 자동 설치 가이드

> **Claude가 이 파일을 읽으면 자동으로 설치를 진행합니다**

---

## 🔧 설치 단계

### 1. FFmpeg 확인/설치
```bash
# 설치 확인
which ffmpeg

# 없으면 설치 (macOS)
brew install ffmpeg

# Windows
winget install ffmpeg
```

### 2. jq 확인/설치 (선택)
```bash
# 설치 확인
which jq

# 없으면 설치
brew install jq
```

### 3. 작업 폴더 생성
```bash
# 프로젝트 폴더 생성
mkdir -p ~/video-parody-project/{reference,keyframes,prompts,generated}
```

### 4. 패키지 내용 복사
```bash
# 템플릿들을 프로젝트로 복사
cp templates/*.md ~/video-parody-project/prompts/
```

---

## ✅ 설치 완료 후 안내

설치가 완료되면 사용자에게 다음을 알려주세요:

```
✅ 패키지 설치가 완료되었습니다!

📂 작업 폴더: ~/video-parody-project/

🚀 다음 단계:
1. AI 빌더 링크를 클릭하세요: [링크]
2. 영상을 업로드하고 분석하세요
3. IMAGE_PROMPTS.md를 다운로드 받으세요
4. 저에게 "모션 프롬프트 만들어줘"라고 말씀하세요

🔗 AI 빌더: https://aistudio.google.com/app/prompts?state=...
```

---

## 📋 Claude 자동 실행 체크리스트

- [ ] FFmpeg 설치 확인
- [ ] 작업 폴더 생성
- [ ] 사용자에게 다음 단계 안내
- [ ] AI 빌더 링크 제공

---

## 💬 대화 템플릿

### 사용자가 "패키지 설치해줘"라고 하면:

```
네! 패키지를 설치하고 있습니다.

1️⃣ FFmpeg 확인 중...
   → [설치됨/설치 필요]

2️⃣ 작업 폴더 생성 중...
   → ~/video-parody-project/ 생성 완료

3️⃣ 설치 완료! 🎉

👉 다음 단계:
   AI 빌더 링크를 클릭해서 영상을 분석하세요:
   https://aistudio.google.com/app/prompts?state=...

   분석이 끝나면 IMAGE_PROMPTS.md를 다운로드해서
   저에게 "모션 프롬프트 만들어줘"라고 말씀하세요!
```

---

## 🎬 대사가 있는 영상

사용자가 대사가 있다고 하면 MOTION_PROMPTS.md에 포함:

```markdown
### [📋 COPY] Positive
[동작 설명...]
**Lip-sync**: "[대사]" mouthed clearly at [타이밍].
```

예시:
```markdown
### [📋 COPY] Positive
A Korean family gathered around the table. 
Mouths IMMEDIATELY open singing "HAPPY BIRTHDAY TO YOU" from beat one.
**Lip-sync**: "생일 축하합니다" synced naturally, lips forming 'ㅎ' and 'ㅊ' clearly.
```

---

## ⚙️ 키프레임 추출 명령어

사용자가 "키프레임 추출해줘"라고 하면:

```bash
# 타임코드 기반 추출
ffmpeg -ss 00:01.27 -i source.mp4 -frames:v 1 keyframes/scene01.png
ffmpeg -ss 00:02.28 -i source.mp4 -frames:v 1 keyframes/ANCHOR_IMG.png
# ... (각 씬마다)
```

---

## 🔗 핵심 링크

- **AI 빌더**: https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221AAcse-ic6mNRbtgjy6jWYThp8qwZL31m%22%5D,%22action%22:%22open%22,%22userId%22:%22114876486829819877093%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing
