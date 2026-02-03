# ⚙️ 환경 설정

> 시작하기 전에 필요한 것들을 준비해요

---

## Google AI Studio 접속

> 모든 도구는 **AI Studio**에서 실행됩니다

### 접속 방법

☐ **Step 1**: 브라우저에서 [aistudio.google.com](https://aistudio.google.com) 접속

☐ **Step 2**: Google 계정으로 로그인

---

## 캔버스 앱 사용법

> Builder 도구는 "캔버스 앱"이라는 기능을 사용해요

☐ **Step 1**: 좌측 패널 → **"+ 새 앱"** 클릭

☐ **Step 2**: **"Canvas App"** 선택

☐ **Step 3**: ZIP 파일 업로드

| ZIP 파일 | 용도 |
|----------|------|
| `builder1-hardened.zip` | 영상 분석기 |
| `builder2-hardened.zip` | 변주 엔진 |
| `vibe-philosophy.zip` | 바이브 철학관 |

☐ **Step 4**: 자동으로 앱 로드 완료!

> ⚠️ **주의**: ZIP 파일은 최대 10개 파일, 100MB 이하여야 해요

---

## FFmpeg 설치

> 영상에서 기준 프레임을 추출할 때 필요해요

### macOS 사용자

```bash
# 1. Homebrew 업데이트
brew update

# 2. FFmpeg 설치
brew install ffmpeg

# 3. 설치 확인
ffmpeg -version
```

> 💡 **팁**: Homebrew가 없다면 [brew.sh](https://brew.sh)에서 먼저 설치하세요

---

### Windows 사용자

☐ [ffmpeg.org/download.html](https://ffmpeg.org/download.html) 접속

☐ Windows 빌드 다운로드 & 압축 해제

☐ 환경변수 PATH에 `ffmpeg/bin` 폴더 추가

---

<details>
<summary>▶ PATH 설정이 처음이라면 (클릭)</summary>

1. 시작 → "환경 변수" 검색
2. "시스템 환경 변수 편집" 클릭
3. "환경 변수" 버튼 클릭
4. "Path" 선택 → "편집"
5. "새로 만들기" → ffmpeg 폴더 경로 입력
   - 예: `C:\ffmpeg\bin`
6. 확인 → 확인 → 확인

</details>

---

## 설치 완료 체크리스트

☐ Google AI Studio 로그인 완료

☐ FFmpeg 설치 완료 (`ffmpeg -version` 동작 확인)

☐ ZIP 파일 3개 다운로드 완료

---

> **다음**: [🎬 기준 프레임 추출](./02-anchor-frame.md)
