---
description: Chrome CDP 디버그 모드 실행 (NotebookLM 자동화용)
---

# Chrome CDP 실행 가이드

## ⚠️ 중요: Vivid 프로젝트는 포트 9223 사용

다른 프로젝트와의 충돌 방지를 위해 **9223 포트를 사용**합니다.

## 실행 방법

### 방법 1: 스크립트 사용 (권장)
```bash
backend/scripts/run_chrome_9223.sh
```

### 방법 2: 수동 실행
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir=/tmp/chrome-debug-9223 \
  --no-first-run \
  https://notebooklm.google.com/
```

## 포트 설정 위치

| 파일 | 용도 |
|------|------|
| `backend/app/rag/tier0_notebooklm.py` | Tier0 Playwright 클라이언트 |
| `backend/app/rag/notebooklm_playwright.py` | Playwright CDP 연결 |
| `backend/scripts/upload_tarantino_notebook.py` | NotebookLM 업로드 스크립트 |

## 절대 하면 안 되는 것

❌ **9222로 변경 금지** - 다른 프로젝트가 사용 중
❌ **user-data-dir 공유 금지** - 프로필 충돌로 크래시 발생
