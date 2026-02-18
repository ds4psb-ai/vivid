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

### 6. Alembic 마이그레이션 (핵심!)

기존 DB에 `init_db()`로 테이블이 생성되어 있으면 alembic upgrade 실패:

```dockerfile
# ❌ 실패할 수 있음
CMD alembic upgrade head && uvicorn ...

# ✅ Fallback 패턴 (권장)
CMD sh -c "alembic upgrade head 2>&1 || alembic stamp head && uvicorn ..."
```

**멱등성(Idempotency) 패턴** - 마이그레이션 파일 작성법:

```python
def upgrade() -> None:
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 테이블 존재 확인 후 생성
    if 'my_table' not in existing_tables:
        op.create_table('my_table', ...)
    
    # 컬럼 추가 시 존재 확인
    existing_columns = [c['name'] for c in inspector.get_columns('my_table')]
    if 'new_col' not in existing_columns:
        op.add_column('my_table', sa.Column('new_col', ...))
```

**FK 에러 방지** - 존재하지 않는 테이블 참조 금지:

```python
# ❌ users 테이블이 없으면 실패
sa.ForeignKeyConstraint(['user_id'], ['users.id'])

# ✅ FK 없이 (외부 ID는 FK 불필요)
sa.Column('user_id', sa.String(255), nullable=False, index=True)
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

### 방법 1: CLI (기본)

```bash
# ⚠️ 반드시 backend 폴더에서 실행 — Dockerfile이 여기 있음
cd /Users/ted/vivid/backend

railway up --service vivid --detach
```

- **빌더**: Dockerfile (railway.json에 `"builder": "DOCKERFILE"` 설정됨)
- **서비스명**: `vivid` (vivid-backend 아님)
- `--detach`: 빌드 완료 대기 없이 즉시 반환, Build Logs URL 출력

### 방법 2: GraphQL API

CLI 없이 API로 재배포 (최신 커밋 기준 재빌드):

```bash
RAILWAY_TOKEN=$(cat ~/.railway/config.json | python3 -c "import json,sys; print(json.load(sys.stdin)['user']['token'])")

curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { serviceInstanceRedeploy(environmentId: \"a9dac264-c078-4483-a5e6-6dc3acf30350\", serviceId: \"74b07bc1-f3f1-492e-af77-1e3e664572b9\") }"
  }'
# 응답: {"data":{"serviceInstanceRedeploy":true}}
```

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| environmentId | `a9dac264-c078-4483-a5e6-6dc3acf30350` | production 환경 |
| serviceId | `74b07bc1-f3f1-492e-af77-1e3e664572b9` | vivid 서비스 |

> **차이점**: CLI(`railway up`)는 로컬 파일을 업로드하여 빌드. API(`serviceInstanceRedeploy`)는 이미 배포된 설정 기준으로 재빌드 (코드 변경 없이 재시작에 적합).

### 주의사항

```bash
# ❌ 프로젝트 루트에서 실행 — Dockerfile 못 찾음
cd /Users/ted/vivid && railway up --service vivid

# ❌ GraphQL API만으로 새 코드 배포 — 로컬 변경분 반영 안 됨
# → 새 코드 배포는 반드시 CLI 방식 사용

# ✅ backend 폴더에서 CLI 실행
cd /Users/ted/vivid/backend && railway up --service vivid --detach
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

### Alembic 마이그레이션 에러

**증상**: `alembic upgrade head` 실행 시 에러 발생

| 에러 | 원인 | 해결 |
|------|------|------|
| `relation "xxx" already exists` | init_db()로 이미 생성됨 | `alembic stamp head`로 건너뛰기 |
| `relation "xxx" does not exist` | FK가 없는 테이블 참조 | FK 제거 또는 테이블 먼저 생성 |
| `null value in column "xxx"` | INSERT에 NOT NULL 컬럼 누락 | 모든 NOT NULL 컬럼 명시 |

**디버깅 방법**:

```dockerfile
# Dockerfile에 로깅 추가
CMD sh -c "echo '=== Starting ===' && \
    echo 'DATABASE_URL='$(echo $DATABASE_URL | sed 's/:.*@/:***@/') && \
    alembic upgrade head 2>&1 || { echo '=== FAILED ==='; alembic stamp head; } && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
```

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
