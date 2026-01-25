# Railway 배포 가이드

> Vivid Backend를 Railway Pro에 배포하는 방법

---

## 아키텍처

```
prompty.co.kr (Vercel)
    ↓ API 호출
api.prompty.co.kr (Railway)
    ├── PostgreSQL (postgres.railway.internal)
    └── Redis (redis.railway.internal)
```

---

## 핵심 교훈 (Lessons Learned)

### 1. $PORT 변수 처리

Railway는 동적으로 `$PORT` 환경변수를 할당함. **Shell expansion** 필요:

```dockerfile
# ❌ 작동 안 함 - exec form은 shell expansion 안 함
CMD ["uvicorn", "app.main:app", "--port", "$PORT"]

# ✅ 작동함 - shell form 사용
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
```

### 2. railway.json vs Dockerfile CMD

**둘 중 하나만 사용** - 충돌 방지:

```json
// railway.json - startCommand 사용 시
{
  "deploy": {
    "startCommand": "sh -c 'uvicorn app.main:app --port ${PORT}'"
  }
}

// 또는 Dockerfile CMD만 사용 (권장)
{
  "deploy": {
    "healthcheckPath": "/health"
    // startCommand 없음
  }
}
```

### 3. Private Networking

같은 Railway 프로젝트 내 서비스 연결:

```bash
# ❌ Public URL (egress 요금 발생)
DATABASE_URL=postgresql://...@interchange.proxy.rlwy.net:44853/...

# ✅ Private Domain (무료, 빠름)
DATABASE_URL=postgresql+asyncpg://...@postgres.railway.internal:5432/...
REDIS_URL=redis://...@redis.railway.internal:6379
```

### 4. SQLAlchemy Async

async SQLAlchemy 사용 시 `+asyncpg` 드라이버 명시:

```bash
# ❌ 동기 드라이버
DATABASE_URL=postgresql://...

# ✅ 비동기 드라이버
DATABASE_URL=postgresql+asyncpg://...
```

### 5. Private Networking SSL

Railway private networking은 SSL을 사용하지 않음:

```bash
# ❌ SSL 연결 시도 (ConnectionRefusedError)
DB_SSL_MODE=prefer  # 기본값

# ✅ SSL 비활성화
DB_SSL_MODE=disable
```

### 5. 변수 참조 vs 하드코딩

Railway 변수 참조 (`${{Service.VAR}}`)가 안 될 때 하드코딩:

```bash
# 변수 참조 (가끔 안 됨)
DATABASE_URL=postgresql://...@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/...

# 하드코딩 (확실함)
DATABASE_URL=postgresql://...@postgres.railway.internal:5432/...
```

---

## 필수 환경변수 (Railway Variables)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:{PASSWORD}@postgres.railway.internal:5432/railway
DB_SSL_MODE=disable  # ⚠️ Private networking은 SSL 없음

# Redis
REDIS_URL=redis://default:{PASSWORD}@redis.railway.internal:6379

# API Keys
GEMINI_API_KEY=AIzaSy...

# App Config
ENVIRONMENT=production
CORS_ORIGINS=https://prompty.co.kr
SECRET_KEY=your-secret-key-min-32-chars
```

---

## 배포 명령어

```bash
# 프로젝트 루트에서 실행 (중요!)
cd /Users/ted/vivid

# Railway 프로젝트 연결
railway link --project prompty-backend

# backend 폴더에서 배포
cd backend && railway up --service vivid --detach
```

**주의**: Root Directory 설정이 있으면 해당 폴더에서 `railway up` 실행 시 경로 충돌!

```bash
# ❌ Root Directory = "backend" 설정 + backend 폴더에서 실행
# → backend/backend 찾음 → 실패

# ✅ 프로젝트 루트에서 실행하거나 Root Directory 설정 제거
```

---

## 트러블슈팅

### ModuleNotFoundError

requirements.txt에 패키지 누락:
```bash
# 자주 누락되는 패키지
cachetools>=5.3.0
cryptography>=41.0.0
sse-starlette>=1.8.0
pydantic-settings>=2.0.0
PyJWT>=2.8.0
PyYAML>=6.0.0
```

### ConnectionRefusedError

1. DATABASE_URL에 `+asyncpg` 드라이버 확인
2. Private domain 사용 확인 (`*.railway.internal`)
3. 서비스 이름 일치 확인 (`postgres`, `redis`)
4. **DB_SSL_MODE=disable** 설정 확인 (private networking은 SSL 미사용)

### Production Validation Error

`config.py`의 `validate_production_config()` 오류 시:
- 필요한 환경변수 설정
- 또는 validation 임시 비활성화

---

## 파일 구조

```
backend/
├── Dockerfile          # Shell form CMD with $PORT
├── railway.json        # Build/deploy 설정
├── requirements.txt    # 모든 의존성 포함
└── app/
    └── main.py
```

---

## Custom Domain 설정

### Railway (api.prompty.co.kr)

1. Service → Settings → Networking → Custom Domain
2. `api.prompty.co.kr` 입력
3. CNAME 값 복사 (예: `2t4p6mna.up.railway.app`)

### DNS (호스팅케이알)

```
Type: CNAME
Name: api
Value: 2t4p6mna.up.railway.app
TTL: 300
```

---

## 검증

```bash
# Health check
curl https://api.prompty.co.kr/health

# 또는 Railway 도메인
curl https://vivid-production-6499.up.railway.app/health
```
