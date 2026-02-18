# Auth System Documentation

> Vivid/Crebit 인증 시스템 가이드

---

## 개요

Google OAuth 2.0 기반 인증 + 세션 쿠키 관리 + CSRF 보호

---

## 인증 흐름

```
1. 프론트엔드: /api/v1/auth/google/login 리다이렉트
2. Google OAuth 로그인
3. 콜백: /api/v1/auth/google/callback
4. 세션 쿠키 설정 (crebit_session)
5. CSRF 토큰 쿠키 설정 (csrf_token)
6. AUTH_SUCCESS_REDIRECT로 리다이렉트
```

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `backend/app/routers/auth.py` | 인증 엔드포인트 |
| `backend/app/dependencies.py` | `require_authenticated_user` 의존성 |
| `backend/app/auth.py` | 세션 토큰 생성/검증 |
| `backend/app/middleware/csrf.py` | CSRF 미들웨어 |
| `backend/app/config.py` | 인증 관련 설정 |

---

## 환경변수 (Railway)

### 필수

| 변수 | 설명 | 예시 |
|------|------|------|
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | `915052...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | OAuth 콜백 URL | `https://api.prompty.co.kr/api/v1/auth/google/callback` |
| `AUTH_SUCCESS_REDIRECT` | 로그인 성공 후 리다이렉트 | `https://www.prompty.co.kr` |
| `AUTH_ERROR_REDIRECT` | 로그인 실패 시 리다이렉트 | `https://www.prompty.co.kr/login?error=auth_failed` |
| `COOKIE_DOMAIN` | 쿠키 도메인 (서브도메인 공유) | `.prompty.co.kr` |

### 관리자 설정

| 변수 | 설명 | 예시 |
|------|------|------|
| `MASTER_ADMIN_EMAILS` | 마스터 관리자 이메일 (쉼표 구분) | `ted.taeeun.kim@gmail.com` |

**중요**: 이 환경변수가 없으면 관리자 기능이 작동하지 않음!

---

## Academy 접근 권한

### 체크 로직 (`/api/v1/auth/academy/access`)

```python
# 1. 관리자 체크
is_admin = user_email in settings.MASTER_ADMIN_EMAIL_SET

# 2. 수강생 체크 (crebit_applications 테이블)
application = await db.execute(
    select(CrebitApplication)
    .where(CrebitApplication.owner_id == user_id)
    .where(CrebitApplication.status == "paid")
)

# 3. 둘 중 하나라도 true면 접근 가능
can_access = is_admin or application is not None
```

### 접근 가능 조건

| 조건 | 설명 |
|------|------|
| **관리자** | `MASTER_ADMIN_EMAILS` 환경변수에 이메일 포함 |
| **수강생** | `crebit_applications` 테이블에 `status='paid'` 레코드 존재 |

---

## 세션 구조

`require_authenticated_user` 반환값:

```python
{
    "id": "google:123456789",
    "user_id": "google:123456789",
    "is_admin": True,
    "email": "ted.taeeun.kim@gmail.com",
    "name": "Ted Kim",
    "role": "master"
}
```

**주의**: `email`이 빈 문자열이면 관리자 체크 실패!

---

## CSRF 보호

### 패턴: Double Submit Cookie

1. 서버가 `csrf_token` 쿠키 설정
2. 클라이언트가 `X-CSRF-Token` 헤더에 동일 값 전송
3. 미들웨어가 쿠키 == 헤더 검증

### 예외 (CSRF 체크 안 함)

- `GET`, `HEAD`, `OPTIONS` 요청
- API Key 인증 (`X-API-Key` 헤더)
- Bearer 토큰 인증 (`Authorization` 헤더)
- `/health`, `/webhooks/*` 등 특정 경로

### 프론트엔드 사용법

```typescript
// CSRF 토큰 가져오기
function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

// API 호출 시 헤더에 포함
const response = await fetch('/api/v1/some-endpoint', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfToken() || '',
  },
  credentials: 'include',
  body: JSON.stringify(data),
});
```

---

## 로그아웃

```python
# /api/v1/auth/logout (POST)
# 쿠키 삭제 시 set_cookie()와 동일한 파라미터 필요!
response.delete_cookie(
    settings.SESSION_COOKIE_NAME,
    domain=settings.COOKIE_DOMAIN or None,
    path="/",
    secure=settings.COOKIE_SECURE,
    samesite="lax",
)
```

---

## 수강생 자동 연결

로그인 시 `crebit_applications` 테이블과 자동 연결:

```python
# owner_id가 null인 레코드 중 email이 일치하면 연결
app_result = await db.execute(
    select(CrebitApplication)
    .where(CrebitApplication.email == email.lower())
    .where(CrebitApplication.owner_id.is_(None))
)
if pending_application:
    pending_application.owner_id = account.user_id
```

---

## 접근 요청 시스템 (Academy)

### 수강생 플로우

1. Academy 페이지 접속 → "접근 요청하기" 버튼 클릭
2. `POST /api/v1/access-request` → DB에 요청 저장
3. "대기 중" 상태 표시

### 관리자 플로우

1. `/admin/academy` 페이지 접속
2. 요청 목록 확인
3. 승인/거절 버튼 클릭

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/v1/access-request` | 접근 요청 생성 |
| `GET` | `/api/v1/access-request/status` | 요청 상태 확인 |
| `GET` | `/api/v1/access-request/admin/list` | 관리자: 요청 목록 |
| `PATCH` | `/api/v1/access-request/admin/{id}/approve` | 관리자: 승인 |
| `PATCH` | `/api/v1/access-request/admin/{id}/reject` | 관리자: 거절 |

---

## 트러블슈팅

### 403 Forbidden (Academy 접근)

1. **환경변수 확인**: Railway에 `MASTER_ADMIN_EMAILS` 설정되어 있는지
2. **세션 이메일 확인**: `require_authenticated_user`가 `email` 반환하는지
3. **DB 확인**: `crebit_applications`에 `status='paid'` 레코드 있는지

### CSRF 토큰 오류

1. 쿠키에 `csrf_token` 있는지 확인
2. 요청 헤더에 `X-CSRF-Token` 포함되어 있는지 확인
3. GET 요청은 CSRF 체크 안 함

### 로그아웃 안 됨

- `delete_cookie()` 파라미터가 `set_cookie()`와 동일한지 확인
- 특히 `domain`, `path`, `secure`, `samesite`

---

## 디버깅 팁

### 1. Health 엔드포인트로 환경변수 확인

```bash
curl https://api.prompty.co.kr/health | jq .
```

### 2. DB에서 사용자 확인

```sql
-- user_accounts
SELECT user_id, email, role FROM user_accounts WHERE email ILIKE '%ted%';

-- crebit_applications
SELECT email, owner_id, status FROM crebit_applications;
```

### 3. 세션 정보 확인 (브라우저 콘솔)

```javascript
fetch('/api/v1/auth/me', {credentials: 'include'}).then(r => r.json()).then(console.log)
```

---

## 2026-02-06 핫픽스 기록

| 문제 | 원인 | 해결 |
|------|------|------|
| 로그아웃 안 됨 | `delete_cookie()`에 domain 파라미터 누락 | 파라미터 추가 |
| 관리자 접근 403 | `MASTER_ADMIN_EMAILS` 환경변수 누락 | Railway에 추가 |
| 관리자 접근 403 | `require_authenticated_user`가 email 미반환 | `dependencies.py` 수정 |
| 접근 요청 403 | CSRF 토큰 헤더 누락 | 프론트엔드에 헤더 추가 |
