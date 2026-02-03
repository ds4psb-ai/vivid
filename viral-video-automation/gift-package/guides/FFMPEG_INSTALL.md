# 🔧 FFmpeg 설치 가이드

## macOS

```bash
# Homebrew로 설치
brew install ffmpeg

# 확인
ffmpeg -version
```

## Windows

```powershell
# PowerShell 관리자 권한
winget install ffmpeg

# 또는 Chocolatey
choco install ffmpeg
```

## Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ffmpeg
```

---

## 자주 쓰는 명령어

### 10개 균등 키프레임 추출

```bash
ffmpeg -i source.mp4 -vf "select='eq(n,0)+lt(mod(t,2),0.1)'" \
  -vsync vfr -q:v 2 keyframes/scene%02d.png
```

### 특정 시간 1프레임 추출

```bash
ffmpeg -ss 00:01.27 -i source.mp4 -frames:v 1 ANCHOR_IMG.png
```

### 영상 길이 확인

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 source.mp4
```

---

## 문제 해결

### "ffmpeg: command not found"

```bash
# macOS: PATH 추가
export PATH="/opt/homebrew/bin:$PATH"

# 터미널 재시작
```

### 권한 오류

```bash
# macOS: Homebrew 재링크
brew link ffmpeg
```
