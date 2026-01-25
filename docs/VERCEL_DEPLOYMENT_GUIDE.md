# Vercel Deployment Guide

> Frontend (Next.js) 배포 가이드

---

## 프로젝트 정보

| 항목 | 값 |
|------|-----|
| 프로젝트명 | `crebit` |
| 도메인 | `prompty.co.kr`, `www.prompty.co.kr` |
| GitHub Repo | `ds4psb-ai/vivid` |
| Root Directory | `frontend` |
| Framework | Next.js 16 |

---

## 자동 배포 (Git Push)

현재 webhook 이슈로 **수동 배포** 필요. 아래 API 방식 사용.

---

## 수동 배포 (API)

### 1. 간단 명령어

```bash
# 배포 트리거
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')
curl -s -X POST "https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crebit",
    "project": "crebit",
    "gitSource": {
      "type": "github",
      "org": "ds4psb-ai",
      "repo": "vivid",
      "ref": "main"
    },
    "target": "production"
  }'
```

### 2. 배포 상태 확인

```bash
# 배포 ID로 상태 확인
curl -s "https://api.vercel.com/v13/deployments/<DEPLOYMENT_ID>" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | grep -oE '"readyState":"[^"]*"'
```

상태값:
- `INITIALIZING` - 시작
- `BUILDING` - 빌드 중
- `READY` - 완료
- `ERROR` - 실패

---

## 환경 변수

| 변수 | 값 | 용도 |
|------|-----|------|
| `NEXT_PUBLIC_API_URL` | `https://vivid-production.up.railway.app` | Backend API |

### 환경 변수 설정/변경

```bash
# 조회
curl -s "https://api.vercel.com/v9/projects/crebit/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | jq '.envs'

# 추가
curl -s -X POST "https://api.vercel.com/v10/projects/crebit/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "key": "NEXT_PUBLIC_API_URL",
    "value": "https://vivid-production.up.railway.app",
    "target": ["production", "preview", "development"],
    "type": "plain"
  }]'
```

---

## 트러블슈팅

### 1. CLI 업로드 실패 (Socket closed unexpectedly)

**원인**: VPN(NordVPN 등)이 대용량 업로드 연결을 끊음

```bash
# 증상
Uploading [--------------------] (0.0B/89.8MB)
Error: FetchError: request to https://api.vercel.com/v2/files failed,
reason: The socket connection was closed unexpectedly.
```

**해결**:
1. VPN 완전 종료 (백그라운드 포함)
2. 또는 **API 방식 배포 사용** (권장)

### 2. Git author 권한 에러

```bash
# 증상
Error: Git author ds4psbravo@gmail.com must have access to the team
```

**해결**:
- CLI 대신 **API 방식 배포** 사용 (Git author 체크 우회)
- 또는 Vercel 대시보드에서 팀 멤버 초대

### 3. `env_secret_missing` 에러

`vercel.json`에서 `@secret_name` 참조 제거:

```json
// 잘못된 설정
"env": {
  "NEXT_PUBLIC_API_URL": "@api_url"  // ❌ 삭제
}
```

### 4. Root Directory 에러

```bash
# Root Directory 설정
curl -X PATCH "https://api.vercel.com/v9/projects/crebit" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rootDirectory": "frontend"}'
```

### 5. Git webhook 안 됨

Vercel 대시보드에서:
1. Settings > Git
2. Disconnect
3. 다시 Connect Git Repository
4. `ds4psb-ai/vivid` 선택, Root: `frontend`

---

## CLI vs API 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **CLI** (`vercel deploy`) | 간단 | VPN 간섭, Git author 체크, 대용량 업로드 실패 |
| **API** (curl) | 안정적, Git author 우회 | 명령어 복잡 |

**권장**: API 방식 사용

---

## 도메인 관리

```bash
# 도메인 목록
curl -s "https://api.vercel.com/v9/projects/crebit/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN"

# 도메인 추가
curl -s -X POST "https://api.vercel.com/v10/projects/crebit/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com"}'
```

---

## 관련 문서

- [Railway 배포 가이드](./RAILWAY_DEPLOYMENT_GUIDE.md) - Backend 배포
- [Vercel 공식 API 문서](https://vercel.com/docs/rest-api)
