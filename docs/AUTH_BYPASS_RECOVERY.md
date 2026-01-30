# Auth Bypass 복구 가이드

> 디자이너 프리뷰용 임시 인증 비활성화 복구 절차

---

## 변경된 파일 (2개)

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/middleware.ts` | 미들웨어 auth 체크 비활성화 |
| `frontend/src/lib/api.ts` | 401 로그인 리다이렉트 비활성화 |

---

## 🚀 원클릭 복구 (권장)

```bash
# 프로젝트 루트에서 실행
cd /Users/ted/vivid

# 1. sed로 TEMP 블록 삭제 (middleware.ts)
sed -i '' '/⚠️ TEMP: Auth disabled/,/^    }/d' frontend/src/middleware.ts

# 2. sed로 TEMP 블록 삭제 (api.ts)
sed -i '' '/⚠️ TEMP: 디자이너 프리뷰용/,/^        }/d' frontend/src/lib/api.ts

# 3. 커밋 & 푸시
git add -A && git commit -m "revert: auth bypass 복구 - 로그인 정상화" && git push origin main

# 4. Vercel 배포
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token') && \
curl -s -X POST "https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crebit",
    "project": "crebit",
    "gitSource": {"type": "github", "org": "ds4psb-ai", "repo": "vivid", "ref": "main"},
    "target": "production"
  }' | jq '{id: .id, readyState: .readyState}'
```

---

## 복구 절차 (상세)

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

## Git Revert 방법 (대안)

```bash
# 변경 전 커밋으로 확인
git log --oneline -5

# 특정 커밋 되돌리기 (최신 순서대로)
git revert ac33bdf6 --no-commit  # 401 리다이렉트 비활성화
git revert 1767f99e --no-commit  # 미들웨어 auth 비활성화
git commit -m "revert: auth bypass 복구"
git push origin main
```

### ⚠️ Revert 충돌 발생 시

```bash
# 충돌 파일 확인
git status

# 충돌 해결 후
git add <충돌파일>
git revert --continue

# 또는 revert 취소하고 수동 편집으로 전환
git revert --abort
```

**충돌이 복잡하면**: 원클릭 복구(sed) 방법 사용 권장

---

## 배포 상태 확인

### Vercel 배포 상태 확인

```bash
# 배포 ID로 상태 확인 (배포 시 반환된 ID 사용)
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')
DEPLOY_ID="<배포ID>"

curl -s "https://api.vercel.com/v13/deployments/$DEPLOY_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | jq '{readyState: .readyState, url: .url}'
```

**상태값**:
- `INITIALIZING` - 시작
- `BUILDING` - 빌드 중
- `READY` - ✅ 완료
- `ERROR` - ❌ 실패

### 최신 프로덕션 배포 확인

```bash
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')

curl -s "https://api.vercel.com/v6/deployments?projectId=crebit&target=production&limit=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | jq '.deployments[0] | {id: .uid, state: .state, url: .url}'
```

---

## 복구 확인 체크리스트

- [ ] `middleware.ts`에서 `AUTH_DISABLED` 블록 삭제됨
- [ ] `api.ts`에서 `SKIP_AUTH_REDIRECT` 블록 삭제됨
- [ ] `git push origin main` 완료
- [ ] Vercel 배포 완료 (`readyState: READY`)
- [ ] 시크릿 창에서 https://prompty.co.kr/dna-lab 접속
- [ ] 로그인 페이지로 리다이렉트 확인
- [ ] Google 로그인 후 정상 작동 확인

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
4. **sed 명령어 실행 전 git status로 변경사항 없는지 확인**

---

## 문제 발생 시

### sed가 안 먹힐 때

macOS sed와 GNU sed 차이로 인한 문제:

```bash
# macOS (기본)
sed -i '' 's/pattern/replacement/' file

# Linux/GNU
sed -i 's/pattern/replacement/' file
```

### 빌드 에러 발생 시

```bash
# 로컬에서 빌드 테스트
cd frontend && npm run build

# 에러 확인 후 수동 수정
```

### 완전 초기화 (최후의 수단)

```bash
# auth bypass 이전 커밋으로 하드 리셋
git log --oneline -10  # 커밋 확인
git reset --hard <auth_bypass_이전_커밋>
git push origin main --force  # ⚠️ 주의: 강제 푸시

# 이후 Vercel 배포
```
