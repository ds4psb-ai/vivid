# Observability 활성화 가이드

> Security Headers, Rate Limiting, OpenTelemetry 프로덕션 활성화 방법

---

## 현재 상태 요약

| 기능 | 구현 상태 | 기본값 | 활성화 필요 |
|------|----------|--------|------------|
| Security Headers | ✅ 완료 | `true` | 자동 활성화 |
| Rate Limiting | ✅ 완료 | 활성화됨 | Redis 연결만 필요 |
| OpenTelemetry | ✅ 완료 | `false` | 환경변수 설정 필요 |
| Langfuse | ✅ 완료 | `true` | API 키 설정 필요 |
| Sentry | ✅ 완료 | 비활성화 | DSN 설정 필요 |
| Prometheus | ✅ 완료 | `true` | 자동 활성화 |

---

## 1. Security Headers (자동 활성화)

`app/middleware/security.py`에서 이미 적용됨.

### 적용되는 헤더

| Header | Value |
|--------|-------|
| Strict-Transport-Security | max-age=31536000; includeSubDomains |
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| Content-Security-Policy | default-src 'self'... |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation=(), microphone=()... |

### 환경변수 (선택)

```bash
# 기본값: 모두 true
SECURITY_HEADERS_ENABLED=true
SECURITY_REQUEST_ID_ENABLED=true
SECURITY_SUSPICIOUS_DETECTION=true
```

### 검증

```bash
curl -I https://api.crebit.app/health
# Strict-Transport-Security, X-Content-Type-Options 등 확인
```

---

## 2. Rate Limiting (자동 활성화)

`app/middleware/rate_limit.py`에서 SlowAPI 기반 구현.

### 엔드포인트별 제한

| 엔드포인트 | 제한 |
|-----------|------|
| `/api/v1/auth/login` | 5/minute |
| `/api/v1/uqsl/generate` | 5/minute |
| `/api/dimension/*/generate` | 10/minute |
| `/api/v1/rag/query` | 30/minute |
| `/api/v1/batch/*` | 5/minute |
| 기본값 | 100/minute |

### 환경변수

```bash
# Redis URL (분산 rate limiting에 필수)
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

### 검증

```bash
# 6번째 요청에서 429 응답 기대
for i in {1..6}; do
  curl -w "%{http_code}\n" -o /dev/null -s -X POST \
    https://api.crebit.app/api/v1/uqsl/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"test","app_key":"1D","n_candidates":1}'
done
```

---

## 3. OpenTelemetry 활성화

### 환경변수 설정 (Railway/Production)

```bash
# 필수: OpenTelemetry 활성화
OTEL_ENABLED=true

# OTLP Collector 엔드포인트
# Jaeger: http://jaeger:4317
# Grafana Tempo: http://tempo:4317
# OTEL Collector: http://otel-collector:4317
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317

# 서비스 식별
OTEL_SERVICE_NAME=vivid-backend
OTEL_SERVICE_VERSION=2.0.0

# 샘플링 비율 (0.1 = 10%)
OTEL_SAMPLE_RATE=0.1

# gRPC 사용 (기본: true)
OTEL_USE_GRPC=true
```

### 지원되는 Instrumentation

| 라이브러리 | 자동 계측 |
|-----------|----------|
| FastAPI | ✅ |
| SQLAlchemy | ✅ |
| HTTPX | ✅ |
| aiohttp | ✅ |
| Google GenerativeAI (Gemini) | ✅ |

### Railway에서 Jaeger 배포

```bash
# Railway에서 Jaeger 서비스 추가
# Docker Image: jaegertracing/all-in-one:latest
# Port: 4317 (OTLP gRPC), 16686 (UI)

# 환경변수
COLLECTOR_OTLP_ENABLED=true
```

### 검증

```bash
# 1. 로그에서 초기화 확인
# "OpenTelemetry tracing initialized"
# "OpenLLMetry initialized with GenAI semantic conventions"

# 2. Jaeger UI에서 vivid-backend 서비스 트레이스 확인
# http://jaeger:16686
```

---

## 4. Langfuse 활성화 (LLM Observability)

### 환경변수 설정

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 키 발급

1. https://cloud.langfuse.com 접속
2. 프로젝트 생성
3. Settings → API Keys에서 발급

### 검증

```bash
# Langfuse Dashboard에서 트레이스 확인
# https://cloud.langfuse.com
```

---

## 5. Sentry 활성화 (Error Tracking)

### 환경변수 설정

```bash
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### 키 발급

1. https://sentry.io 접속
2. 프로젝트 생성 (Python)
3. DSN 복사

### 검증

```bash
# 의도적 에러 발생
curl https://api.crebit.app/debug/sentry-test

# Sentry Dashboard에서 에러 확인
```

---

## 6. Prometheus 메트릭

### 기본 활성화됨

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_METRICS_PATH=/metrics
```

### 보안 설정 (프로덕션 필수)

```bash
# IP 화이트리스트 (권장)
PROMETHEUS_ALLOWED_IPS=internal  # 내부 네트워크만

# 또는 Bearer 토큰 인증
PROMETHEUS_BEARER_TOKEN=your-secure-token
```

### 검증

```bash
# 메트릭 엔드포인트 확인
curl https://api.crebit.app/metrics
```

---

## Railway 환경변수 설정 예시

Railway Dashboard → Service → Variables:

```bash
# === Core ===
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://...@postgres.railway.internal:5432/vivid
REDIS_URL=redis://...@redis.railway.internal:6379
DB_SSL_MODE=disable

# === Security ===
SESSION_SECRET=<generated-secret>
ENABLE_DEV_AUTH_BYPASS=false

# === OpenTelemetry ===
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger.railway.internal:4317
OTEL_SERVICE_NAME=vivid-backend
OTEL_SAMPLE_RATE=0.1

# === Langfuse (Optional) ===
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# === Sentry (Optional) ===
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
```

---

## 종합 검증 스크립트

```bash
#!/bin/bash
API_URL="https://api.crebit.app"

echo "=== Security Headers ==="
curl -sI "$API_URL/health" | grep -E "Strict-Transport|X-Content-Type|X-Frame"

echo ""
echo "=== Rate Limiting ==="
for i in {1..3}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
  echo "Request $i: $STATUS"
done

echo ""
echo "=== Metrics Endpoint ==="
curl -s "$API_URL/metrics" | head -5

echo ""
echo "=== Health Check ==="
curl -s "$API_URL/health" | jq .
```

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `app/config.py` | 모든 환경변수 정의 |
| `app/monitoring.py` | Sentry, Prometheus, OTEL 초기화 |
| `app/middleware/security.py` | Security Headers 미들웨어 |
| `app/middleware/rate_limit.py` | Rate Limiting 미들웨어 |
| `app/telemetry/otel_setup.py` | OpenTelemetry 상세 설정 |
| `app/rag/observability.py` | Langfuse 통합 |
