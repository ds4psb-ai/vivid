# Auth Bypass 복구 가이드

> 디자이너 프리뷰용 임시 인증 비활성화 복구 절차

---

## 변경된 파일 (2개)

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/middleware.ts` | 미들웨어 auth 체크 비활성화 |
| `frontend/src/lib/api.ts` | 401 로그인 리다이렉트 비활성화 |

---

## 복구 절차

### 1. middleware.ts 복구

**파일**: `frontend/src/middleware.ts`

**삭제할 코드** (Line 63-72 근처):
```typescript
// ⚠️ TEMP: Auth disabled for designer preview - REMOVE AFTER REVIEW
const AUTH_DISABLED = true;
if (AUTH_DISABLED) {
    // Only handle legacy redirects, skip all auth
    const redirectTarget = LEGACY_REDIRECTS[pathname];
    if (redirectTarget) {
        return NextResponse.redirect(new URL(redirectTarget, request.url), { status: 301 });
    }
    return NextResponse.next();
}
```

**복구 후 코드** (해당 블록 전체 삭제, 아래만 남김):
```typescript
export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Check for legacy redirects first (2026 Mega Apps)
    const redirectTarget = LEGACY_REDIRECTS[pathname];
    // ... 나머지 원래 코드
```

---

### 2. api.ts 복구

**파일**: `frontend/src/lib/api.ts`

**삭제할 코드** (Line 896-901 근처):
```typescript
// ⚠️ TEMP: 디자이너 프리뷰용 - 401에서 로그인 리다이렉트 비활성화
// TODO: 리뷰 후 제거
const SKIP_AUTH_REDIRECT = true;
if (SKIP_AUTH_REDIRECT) {
  throw new Error("인증이 필요합니다.");
}
```

**복구 후 코드** (해당 블록 전체 삭제):
```typescript
// Handle authentication errors (JWT expired or invalid)
if (response.status === 401) {
  // Clear any cached session and redirect to login
  if (typeof window !== "undefined") {
    // ... 원래 코드 그대로
```

---

## 빠른 복구 명령어

### 방법 1: Git revert (권장)

```bash
# 변경 전 커밋으로 확인
git log --oneline -5

# 특정 커밋 되돌리기 (2개 커밋)
git revert ac33bdf6 --no-commit  # 401 리다이렉트 비활성화
git revert 1767f99e --no-commit  # 미들웨어 auth 비활성화
git commit -m "revert: auth bypass 복구"
git push origin main
```

### 방법 2: 수동 편집

```bash
# 1. middleware.ts에서 AUTH_DISABLED 블록 삭제
# 2. api.ts에서 SKIP_AUTH_REDIRECT 블록 삭제
# 3. 커밋 & 배포

git add -A
git commit -m "revert: auth bypass 복구 - 로그인 정상화"
git push origin main

# Vercel 배포
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')
curl -s -X POST "https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crebit",
    "project": "crebit",
    "gitSource": {"type": "github", "org": "ds4psb-ai", "repo": "vivid", "ref": "main"},
    "target": "production"
  }'
```

---

## 복구 확인 체크리스트

- [ ] `middleware.ts`에서 `AUTH_DISABLED` 블록 삭제됨
- [ ] `api.ts`에서 `SKIP_AUTH_REDIRECT` 블록 삭제됨
- [ ] `git push origin main` 완료
- [ ] Vercel 배포 완료 (readyState: READY)
- [ ] https://prompty.co.kr/dna-lab 접속 시 로그인 페이지로 리다이렉트 확인
- [ ] 로그인 후 정상 작동 확인

---

## 관련 커밋

| 커밋 | 메시지 | 작업 |
|------|--------|------|
| `1767f99e` | temp: 디자이너 프리뷰용 auth 임시 비활성화 | middleware.ts |
| `ac33bdf6` | temp: 401 로그인 리다이렉트 비활성화 | api.ts |

---

## 주의사항

1. **복구 전 디자이너 리뷰 완료 확인**
2. **복구 후 반드시 Vercel 배포** (git push만으로 자동 배포 안 됨)
3. **배포 후 시크릿 창에서 테스트** (캐시 문제 방지)
