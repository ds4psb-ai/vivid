# OpenClaw Gemini 인증 가이드

> API 키 없이 OAuth 로그인으로 Gemini 사용하기

---

## 🔐 인증 방법 요약

| 방법 | 난이도 | 추천 |
|------|--------|------|
| **OAuth 로그인 (URL)** | 쉬움 | ✅ 추천 |
| API 키 | 쉬움 | 대안 |
| ADC (gcloud) | 복잡 | 개발용 |

---

## 📋 OAuth 로그인 방법 (API 키 없이)

### Step 1: OpenClaw에서 Gemini 로그인 시도

```bash
# OpenClaw 내부에서
gemini auth login
```

### Step 2: 에러 발생해도 당황 금지!

에러 메시지 **위에** URL이 표시됨:

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...
```

### Step 3: URL 복사해서 브라우저에서 열기

1. URL 복사
2. 브라우저에서 붙여넣기
3. Google 계정 로그인
4. "허용" 클릭
5. 리다이렉트된 URL 전체 복사 (localhost:... 형태)

### Step 4: 리다이렉트 URL을 OpenClaw에 입력

```bash
# 복사한 전체 URL 붙여넣기
http://localhost:8080/callback?code=4/0AXE...
```

### Step 5: 성공!

```
✅ Loaded cached credentials.
```

---

## 🔧 Python 스크립트에서 토큰 사용

### 토큰 위치

```
/root/.openclaw/agents/main/agent/auth-profiles.json
```

### 토큰 추출

```bash
TOKEN=$(cat /root/.openclaw/agents/main/agent/auth-profiles.json | jq -r '.["google-gemini-cli"].access_token')
```

### 스크립트 실행

```bash
GEMINI_ACCESS_TOKEN="$TOKEN" python3 analyze_video.py video.mp4
```

---

## ⚠️ 주의사항

| 항목 | 설명 |
|------|------|
| **Access Token 만료** | ~1시간 후 만료됨 |
| **Refresh Token** | 자동 갱신용, 더 오래 유효 |
| **재로그인** | 만료 시 `gemini auth login` 다시 실행 |

---

## 📁 관련 파일 경로

```
~/.openclaw/agents/main/agent/auth-profiles.json  # 토큰 저장
~/.config/google-gemini-cli/                       # CLI 설정 (있으면)
```

---

## 🎯 트러블슈팅

### 문제: "OAuth 자격증명을 찾을 수 없습니다"

**해결:**
```bash
# 1. 토큰 추출
TOKEN=$(cat /root/.openclaw/agents/main/agent/auth-profiles.json | jq -r '.["google-gemini-cli"].access_token')

# 2. 환경변수로 전달
export GEMINI_ACCESS_TOKEN="$TOKEN"

# 3. 스크립트 실행
python3 analyze_video.py video.mp4
```

### 문제: "externally-managed-environment"

**해결:**
```bash
pip install google-genai --break-system-packages
```

---

## 🎬 멀티모달 비디오 분석 (Native Vision) - Single Source of Truth

> **2026-02-02 최종 검증 완료**: Ted가 직접 테스트!

---

## 🚨 정답 (이것만 따라하세요!)

### ✅ DO (해야 할 것)

```bash
# 1. SSH 접속
ssh root@158.247.230.78

# 2. Interactive 모드로 실행 (YOLO 아님!!!)
gemini

# 3. 프롬프트에서 비디오 분석 요청
> @{/root/.openclaw/media/inbound/파일명.mp4} Kyle Nutt 스타일로 분석해줘
```

### ❌ DON'T (하면 안 되는 것)

| 잘못된 방법 | 결과 |
|------------|------|
| `gemini --yolo` | ❌ API 에러 (function_response 버그) |
| One-liner 모드 | ❌ mime_type 지원 안 됨 에러 |
| FFmpeg 도구 시도 | ❌ 불필요, 네이티브로 가능 |

---

## 📋 사전 설정 (한 번만 하면 됨)

### VPS 설정 파일 (`~/.gemini/settings.json`)

```json
{
  "general": { "previewFeatures": true },
  "model": { "name": "gemini-3-pro-preview" },
  "context": { "fileName": ["GEMINI.md"] }
}
```

### 페르소나 파일 (`~/.gemini/GEMINI.md`)

영상 분석 전문가 모드 지침 저장 (컷 분해, 캐릭터 프로파일, AI 재현용 프롬프트)

---

## 💡 핵심 포인트

1. **Interactive 모드 필수**: `gemini`만 치고 들어가기
2. **YOLO 모드 OFF**: 도구 자동승인 끄기
3. **@{파일경로}** 문법으로 비디오 직접 전달
4. **previewFeatures: true** 필수

---

## 🎯 성공 출력 예시

```
✦ I will search for "Kyle Nutt video editing style"...

╭──────────────────────────────────────────────────────────────────────────────╮
│ ✓  GoogleSearch "Kyle Nutt video editing style analysis"                     │
│ ✓  ReadFile .openclaw/media/...file.mp4                                      │
╰──────────────────────────────────────────────────────────────────────────────╯

🎬 Video Analysis Report: Kyle Nutt Style

1. 컷 분해 (Cut Breakdown)
2. 캐릭터 프로파일
3. 시각 스타일 분석
4. AI 재현용 프롬프트 (English)
5. 앵커 씬 추천
```

---

## ⚠️ 트러블슈팅

| 에러 | 원인 | 해결 |
|------|------|------|
| `mime_type: video/text/timestamp` | YOLO 모드 또는 One-liner | Interactive 모드로 재시도 |
| `function_response.parts` 에러 | CLI 버그 | `gemini` Interactive 모드만 사용 |
| 응답 없음 (Silent Response) | 세션 문제 | Ctrl+C 후 `gemini` 재시작 |
| Auth 에러 | 인증 만료 | `gemini auth login` |

---

> **작성일**: 2026-02-02
> **검증 환경**: Ubuntu VPS + Gemini CLI 0.26.0 + Gemini 3 Pro Preview
> **최종 업데이트**: Interactive 모드 단일진실 확정
