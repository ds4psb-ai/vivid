# Phase 1-10 Hardening Master Plan (2026 Best Practices Edition)

> **버전**: 1.0
> **작성일**: 2026-01-20
> **기반**: 2026 최신 웹서칭 리서치 + Vivid 코드베이스 분석
> **현재 상태**: Production Readiness Score 6.1/10 → 목표 9.0/10

---

## Executive Summary

### 2026 리서치 기반 혁신 포인트

| 영역 | 기존 계획 | 2026 Best Practice 업그레이드 |
|------|----------|------------------------------|
| CSRF Protection | fastapi-csrf-protect | **Token Auth + CORS 하이브리드** (브라우저 자동 전송 방지) |
| WebSocket Auth | query param JWT | **Handshake 시점 필수 검증 + 만료 시 자동 재연결** |
| GraphQL | DataLoader 단순 구현 | **Context-based DataLoader + Cache Invalidation + Query Complexity Limit** |
| Sandbox | Docker + seccomp | **gVisor runsc 기반 커널 격리** (Google Cloud Run 수준) |
| Observability | OpenTelemetry 기본 | **OpenLLMetry + GenAI Semantic Conventions** (토큰/비용 추적) |
| RLS | 단순 tenant_id 필터 | **SET LOCAL + security_invoker View + RESTRICTIVE 정책** |
| Rate Limiting | SlowAPI 기본 | **Token Bucket + Redis Lua 원자성 + JWT 기반 차등 제한** |
| Test Coverage | 60% 목표 | **Branch Coverage 50%+ pytest-cov + Mutation Testing** |
| CI/CD Security | Bandit 단독 | **Semgrep + Bandit 하이브리드 + pip-audit + Trivy** |
| ML Feedback | 수동 피드백 | **CRAG (Corrective RAG) + 자동 threshold 조정** |
| Payment | Stripe 기본 연동 | **PCI DSS 4.0 + Webhook Signature + Idempotency Keys** |

---

## 🔴 H1: Critical Security (P0) - Week 1

### H1.1 CSRF + Auth 하이브리드 전략

**2026 Best Practice**: CSRF 토큰보다 **Token-Based Auth + Strict CORS**가 더 효과적

```python
# backend/app/middleware/security.py (신규)
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import re

class SecurityMiddleware(BaseHTTPMiddleware):
    """2026 Best Practice: Multi-layer security middleware."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    MUTATION_PATHS = re.compile(r"^/api/v1/(ip|workflow|payment|chat)/")

    async def dispatch(self, request: Request, call_next):
        # 1. Origin 검증 (CSRF 대체)
        if request.method not in self.SAFE_METHODS:
            origin = request.headers.get("origin")
            if origin and not self._is_allowed_origin(origin):
                raise HTTPException(403, "Origin not allowed")

        # 2. Content-Type 검증 (JSON hijacking 방지)
        if request.method == "POST" and self.MUTATION_PATHS.match(request.url.path):
            ct = request.headers.get("content-type", "")
            if not ct.startswith("application/json"):
                raise HTTPException(415, "Content-Type must be application/json")

        # 3. Security Headers 추가
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

    def _is_allowed_origin(self, origin: str) -> bool:
        allowed = {"https://vivid.studio", "https://app.vivid.studio"}
        if settings.DEBUG:
            allowed.add("http://localhost:3100")
        return origin in allowed

# CORS 설정 (strict)
CORS_CONFIG = {
    "allow_origins": ["https://vivid.studio", "https://app.vivid.studio"],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
    "allow_headers": ["Authorization", "Content-Type", "X-Request-ID"],
    "expose_headers": ["X-RateLimit-Remaining", "X-RateLimit-Reset"],
}
```

**Sources**:
- [FastAPI Security Best Practices](https://davidmuraya.com/blog/fastapi-security-guide/)
- [StackHawk CSRF Protection](https://www.stackhawk.com/blog/csrf-protection-in-fastapi/)

---

### H1.2 WebSocket Authentication (JWT + Handshake)

**2026 Best Practice**: Handshake 시점 필수 검증 + Dependency Injection

```python
# backend/app/routers/ip_chat.py (수정)
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError
from datetime import datetime, timezone
import asyncio

class WebSocketAuthManager:
    """2026 Pattern: Handshake 시점 JWT 검증 + 자동 재연결."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.active_connections: dict[str, WebSocket] = {}

    async def authenticate(
        self,
        websocket: WebSocket,
        token: str = Query(..., description="JWT access token"),
    ) -> dict:
        """Handshake 시점 인증 (연결 전 검증)."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 만료 검증
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                await websocket.close(code=4001, reason="Token expired")
                return None

            # Origin 검증
            origin = websocket.headers.get("origin", "")
            if not self._validate_origin(origin):
                await websocket.close(code=4003, reason="Invalid origin")
                return None

            return payload

        except JWTError as e:
            await websocket.close(code=4002, reason=f"Invalid token: {e}")
            return None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # 토큰 만료 감시 태스크 시작
        asyncio.create_task(self._token_expiry_watcher(websocket, user_id))

    async def _token_expiry_watcher(self, websocket: WebSocket, user_id: str):
        """토큰 만료 시 자동 연결 종료."""
        # 구현: 주기적으로 토큰 유효성 확인
        pass

    def _validate_origin(self, origin: str) -> bool:
        allowed = {"https://vivid.studio", "https://app.vivid.studio"}
        if settings.DEBUG:
            allowed.add("http://localhost:3100")
        return origin in allowed


# WebSocket 엔드포인트
@router.websocket("/ws/chat/{character_id}")
async def websocket_chat(
    websocket: WebSocket,
    character_id: str,
    auth: dict = Depends(ws_auth_manager.authenticate),
):
    if not auth:
        return  # 인증 실패 시 이미 close됨

    user_id = auth.get("sub")
    await ws_auth_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            # 메시지 처리...
    except WebSocketDisconnect:
        ws_auth_manager.disconnect(user_id)
```

**Sources**:
- [FastAPI JWT Auth - WebSocket Protecting](https://indominusbyte.github.io/fastapi-jwt-auth/advanced-usage/websocket/)
- [Authenticating WebSocket Clients](https://hexshift.medium.com/authenticating-websocket-clients-in-fastapi-with-jwt-and-dependency-injection-d636d48fdf48)

---

### H1.3 Secrets Management (Pydantic SecretStr + Vault)

**2026 Best Practice**: SecretStr + 로깅 자동 마스킹 + Runtime Injection

```python
# backend/app/config.py (수정)
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import re

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Secrets (SecretStr로 자동 마스킹) ===
    DATABASE_URL: SecretStr
    REDIS_URL: SecretStr
    GEMINI_API_KEY: SecretStr
    STRIPE_SECRET_KEY: SecretStr
    STRIPE_WEBHOOK_SECRET: SecretStr
    JWT_SECRET_KEY: SecretStr
    QDRANT_API_KEY: SecretStr | None = None

    # === Non-Secrets ===
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    @field_validator("DATABASE_URL", "REDIS_URL", mode="before")
    @classmethod
    def mask_url_password(cls, v: str) -> str:
        """URL 내 패스워드 검증."""
        if v and "@" in v and ":" in v:
            return v  # SecretStr이 자동으로 마스킹
        return v

    def get_db_url(self) -> str:
        """DB URL 안전 반환 (로깅에 노출 금지)."""
        return self.DATABASE_URL.get_secret_value()


# 로깅 자동 마스킹
class SecretMaskingFilter(logging.Filter):
    """로그에서 민감 정보 자동 마스킹."""

    PATTERNS = [
        (re.compile(r'(api[_-]?key["\s:=]+)["\']?[\w-]+', re.I), r'\1***MASKED***'),
        (re.compile(r'(password["\s:=]+)["\']?[\w-]+', re.I), r'\1***MASKED***'),
        (re.compile(r'(secret["\s:=]+)["\']?[\w-]+', re.I), r'\1***MASKED***'),
        (re.compile(r'(token["\s:=]+)["\']?[\w-]+', re.I), r'\1***MASKED***'),
        (re.compile(r'(Bearer\s+)[\w.-]+', re.I), r'\1***MASKED***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True
```

---

### H1.4 PostgreSQL Row Level Security (RLS)

**2026 Best Practice**: SET LOCAL + RESTRICTIVE 정책 + security_invoker View

```sql
-- backend/alembic/versions/029_add_rls_policies.py

-- 1. RLS 활성화
ALTER TABLE ip_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_marketplace_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- 2. 테넌트 격리 정책 (RESTRICTIVE)
CREATE POLICY tenant_isolation_policy ON ip_chat_sessions
    AS RESTRICTIVE  -- 다른 정책과 AND 조합
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_isolation_messages ON ip_chat_messages
    AS RESTRICTIVE
    FOR ALL
    USING (
        session_id IN (
            SELECT id FROM ip_chat_sessions
            WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
        )
    );

-- 3. 사용자 격리 정책 (PERMISSIVE)
CREATE POLICY user_own_sessions ON ip_chat_sessions
    AS PERMISSIVE
    FOR ALL
    USING (user_id = current_setting('app.current_user', true));

-- 4. 관리자 우회 정책 (선택적)
CREATE POLICY admin_bypass ON ip_chat_sessions
    AS PERMISSIVE
    FOR SELECT
    USING (current_setting('app.is_admin', true)::boolean = true);

-- 5. FORCE RLS for owner (보안 강화)
ALTER TABLE ip_chat_sessions FORCE ROW LEVEL SECURITY;
```

```python
# backend/app/middleware/tenant.py (신규)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends
from contextlib import asynccontextmanager

class TenantContextMiddleware:
    """2026 Pattern: SET LOCAL로 요청 스코프 테넌트 컨텍스트."""

    @asynccontextmanager
    async def set_tenant_context(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        is_admin: bool = False,
    ):
        """트랜잭션 내 테넌트 컨텍스트 설정."""
        try:
            # SET LOCAL은 트랜잭션 종료 시 자동 롤백
            await db.execute(text(f"SET LOCAL app.current_tenant = '{tenant_id}'"))
            await db.execute(text(f"SET LOCAL app.current_user = '{user_id}'"))
            await db.execute(text(f"SET LOCAL app.is_admin = '{str(is_admin).lower()}'"))
            yield
        finally:
            # 명시적 정리 (선택적)
            pass


async def get_tenant_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """요청별 테넌트 컨텍스트가 설정된 DB 세션."""
    tenant_id = request.state.tenant_id
    user_id = request.state.user_id

    async with tenant_middleware.set_tenant_context(db, tenant_id, user_id):
        yield db
```

**Sources**:
- [AWS RLS Best Practices](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [Permit.io RLS Implementation Guide](https://www.permit.io/blog/postgres-rls-implementation-guide)
- [Crunchy Data RLS for Tenants](https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres)

---

## 🟠 H2: Core Feature Completion (P1) - Week 2-3

### H2.1 GraphQL DataLoader (Context-based + Cache Invalidation)

**2026 Best Practice**: Context-based 인스턴스화 + 캐시 무효화 + Query Complexity

```python
# backend/app/graphql/dataloaders.py (신규)
from strawberry.dataloader import DataLoader
from collections import defaultdict
from typing import TypeVar, Generic
from uuid import UUID

T = TypeVar("T")

class CacheableDataLoader(Generic[T]):
    """2026 Pattern: Context-scoped DataLoader with invalidation."""

    def __init__(self, load_fn, cache_key_fn=None):
        self._load_fn = load_fn
        self._cache_key_fn = cache_key_fn or str
        self._cache: dict[str, T] = {}
        self._loader: DataLoader | None = None

    @property
    def loader(self) -> DataLoader:
        if self._loader is None:
            self._loader = DataLoader(load_fn=self._batch_load)
        return self._loader

    async def _batch_load(self, keys: list) -> list[T | None]:
        """N+1 방지 배치 로딩."""
        results = await self._load_fn(keys)

        # 결과를 딕셔너리로 변환
        result_map = {self._cache_key_fn(r): r for r in results if r}

        # 키 순서대로 반환 (DataLoader 요구사항)
        return [result_map.get(self._cache_key_fn(k)) for k in keys]

    def invalidate(self, key) -> None:
        """캐시 무효화 (mutation 후 호출)."""
        cache_key = self._cache_key_fn(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
        if self._loader:
            self._loader.clear(key)

    def invalidate_all(self) -> None:
        """전체 캐시 무효화."""
        self._cache.clear()
        self._loader = None


# Context에서 DataLoader 생성
@strawberry.type
class Query:
    @strawberry.field
    async def ip_catalog(
        self,
        info: strawberry.Info,
        slug: str,
    ) -> IPCatalogType | None:
        # Context-scoped DataLoader
        loader = info.context["ip_loader"]
        return await loader.load(slug)


def get_graphql_context(request: Request, db: AsyncSession):
    """요청별 DataLoader 인스턴스 생성."""
    return {
        "request": request,
        "db": db,
        "ip_loader": create_ip_dataloader(db),
        "user_loader": create_user_dataloader(db),
    }


# Query Complexity Limit
from strawberry.extensions import QueryDepthLimiter
from strawberry.extensions.query_complexity import QueryComplexityLimiter

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),
        QueryComplexityLimiter(max_complexity=1000),
    ],
)
```

**Sources**:
- [Strawberry DataLoaders](https://strawberry.rocks/docs/guides/dataloaders)
- [Avoiding N+1 queries in Strawberry GraphQL](https://blog.separateconcerns.com/2024-05-28-graphql-dataloaders.html)

---

### H2.2 Sandbox (gVisor + seccomp Defense-in-Depth)

**2026 Best Practice**: gVisor runsc 기반 커널 격리 (Google Cloud Run 수준)

```python
# backend/app/services/sandbox_executor.py (수정)
import docker
import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class SandboxRuntime(Enum):
    RUNC = "runc"           # 기본 (seccomp만)
    RUNSC = "runsc"         # gVisor (권장)
    KATA = "kata-runtime"   # Kata Containers

@dataclass
class SandboxConfig:
    runtime: SandboxRuntime = SandboxRuntime.RUNSC
    memory_limit: str = "512m"
    cpu_limit: float = 0.5
    timeout_seconds: int = 30
    network_disabled: bool = True
    read_only_rootfs: bool = True

    # gVisor 특화 옵션
    gvisor_platform: str = "systrap"  # systrap (빠름) or ptrace (호환성)
    gvisor_overlay: bool = True


class SandboxExecutor:
    """2026 Pattern: gVisor 기반 방어 심층 샌드박스."""

    SECCOMP_PROFILE = {
        "defaultAction": "SCMP_ACT_ERRNO",
        "architectures": ["SCMP_ARCH_X86_64"],
        "syscalls": [
            # 최소 허용 syscall (gVisor 기본보다 더 제한적)
            {"names": ["read", "write", "close", "fstat", "lseek"], "action": "SCMP_ACT_ALLOW"},
            {"names": ["mmap", "mprotect", "munmap", "brk"], "action": "SCMP_ACT_ALLOW"},
            {"names": ["exit", "exit_group"], "action": "SCMP_ACT_ALLOW"},
            # 금지: execve, socket, open (상위 디렉토리)
        ],
    }

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.client = docker.from_env()

    async def execute_code(
        self,
        code: str,
        language: str,
        inputs: dict | None = None,
    ) -> SandboxResult:
        """샌드박스 내 코드 실행."""

        # 1. 임시 작업 디렉토리
        with tempfile.TemporaryDirectory() as workdir:
            code_path = Path(workdir) / f"code.{self._get_extension(language)}"
            code_path.write_text(code)

            # 2. 컨테이너 설정
            container_config = {
                "image": f"vivid-sandbox-{language}:latest",
                "command": self._get_run_command(language, code_path.name),
                "volumes": {
                    workdir: {"bind": "/workspace", "mode": "ro"},
                },
                "mem_limit": self.config.memory_limit,
                "nano_cpus": int(self.config.cpu_limit * 1e9),
                "network_disabled": self.config.network_disabled,
                "read_only": self.config.read_only_rootfs,
                "user": "nobody:nogroup",
                "security_opt": [
                    f"seccomp={json.dumps(self.SECCOMP_PROFILE)}",
                    "no-new-privileges:true",
                ],
                "cap_drop": ["ALL"],
                "pids_limit": 50,
                "tmpfs": {"/tmp": "size=64m,noexec,nosuid"},
            }

            # 3. gVisor 런타임 사용
            if self.config.runtime == SandboxRuntime.RUNSC:
                container_config["runtime"] = "runsc"
                container_config["environment"] = {
                    "GVISOR_PLATFORM": self.config.gvisor_platform,
                }

            # 4. 실행 with timeout
            try:
                container = self.client.containers.run(
                    **container_config,
                    detach=True,
                )

                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait),
                    timeout=self.config.timeout_seconds,
                )

                logs = container.logs(stdout=True, stderr=True).decode()

                return SandboxResult(
                    success=result["StatusCode"] == 0,
                    output=logs,
                    exit_code=result["StatusCode"],
                )

            except asyncio.TimeoutError:
                container.kill()
                return SandboxResult(
                    success=False,
                    error="Execution timeout",
                    exit_code=-1,
                )
            finally:
                container.remove(force=True)
```

```dockerfile
# docker/vivid-sandbox/Dockerfile
FROM python:3.11-slim-bookworm AS base

# 보안: non-root 사용자
RUN useradd -m -s /bin/false sandbox && \
    mkdir /workspace && \
    chown sandbox:sandbox /workspace

# 최소 패키지만 설치
RUN pip install --no-cache-dir numpy pandas pillow

# 보안: 쓰기 불가
USER sandbox
WORKDIR /workspace

# 기본 명령어 없음 (docker run에서 지정)
CMD ["python", "-c", "print('ready')"]
```

**Sources**:
- [gVisor Security Model](https://gvisor.dev/docs/architecture_guide/security/)
- [Docker Seccomp Security Profiles](https://docs.docker.com/engine/security/seccomp/)
- [Safe Ride into the Dangerzone](https://gvisor.dev/blog/2024/09/23/safe-ride-into-the-dangerzone/)

---

### H2.3 Stripe Payment Integration (PCI DSS 4.0)

**2026 Best Practice**: Webhook Signature + Idempotency + Tokenization

```python
# backend/app/services/payment_service.py (신규)
import stripe
from fastapi import HTTPException
import hashlib
import hmac

class StripePaymentService:
    """2026 Pattern: PCI DSS 4.0 준수 결제 서비스."""

    def __init__(self, secret_key: str, webhook_secret: str):
        stripe.api_key = secret_key
        self.webhook_secret = webhook_secret
        self._idempotency_cache: dict[str, str] = {}

    async def create_checkout_session(
        self,
        user_id: str,
        credits: int,
        price_cents: int,
    ) -> stripe.checkout.Session:
        """Stripe Checkout 세션 생성 (카드 데이터 서버 미통과)."""

        # Idempotency Key 생성 (중복 결제 방지)
        idempotency_key = self._generate_idempotency_key(
            user_id, credits, "checkout"
        )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": price_cents,
                        "product_data": {
                            "name": f"{credits:,} Credits",
                            "description": "Vivid Studio Credits",
                        },
                    },
                    "quantity": 1,
                }],
                metadata={
                    "user_id": user_id,
                    "credits": str(credits),
                },
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
                idempotency_key=idempotency_key,
            )

            return session

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e.user_message}")
            raise HTTPException(400, str(e.user_message))

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> stripe.Event:
        """Webhook 서명 검증 (필수)."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return event
        except stripe.error.SignatureVerificationError:
            raise HTTPException(400, "Invalid webhook signature")

    async def process_payment_success(
        self,
        session: stripe.checkout.Session,
        db: AsyncSession,
    ) -> CreditTransaction:
        """결제 성공 처리 (크레딧 충전)."""
        user_id = session.metadata["user_id"]
        credits = int(session.metadata["credits"])

        # 중복 처리 방지
        existing = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.stripe_session_id == session.id
            )
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one()

        # 크레딧 추가
        transaction = CreditTransaction(
            user_id=user_id,
            amount=credits,
            type="purchase",
            stripe_session_id=session.id,
            stripe_payment_intent=session.payment_intent,
        )
        db.add(transaction)

        # 잔액 업데이트
        await self._update_balance(db, user_id, credits)

        await db.commit()
        return transaction

    def _generate_idempotency_key(self, *args) -> str:
        """결정적 idempotency key 생성."""
        data = ":".join(str(a) for a in args)
        return hashlib.sha256(data.encode()).hexdigest()[:32]


# Webhook Router
@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    event = payment_service.verify_webhook_signature(payload, signature)

    match event.type:
        case "checkout.session.completed":
            await payment_service.process_payment_success(event.data.object, db)
        case "payment_intent.payment_failed":
            await payment_service.handle_payment_failure(event.data.object, db)
        case "charge.refunded":
            await payment_service.process_refund(event.data.object, db)

    return {"received": True}
```

**Sources**:
- [Stripe Integration Security Guide](https://docs.stripe.com/security/guide)
- [PCI DSS Checklist](https://stripe.com/resources/more/pci-dss-checklist-for-businesses)

---

## 🟡 H3: Observability & Testing (P1) - Week 3-4

### H3.1 OpenTelemetry + OpenLLMetry (LLM Observability)

**2026 Best Practice**: GenAI Semantic Conventions + 토큰/비용 추적

```python
# backend/app/telemetry/otel_setup.py (수정)
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from traceloop.sdk import Traceloop  # OpenLLMetry

# GenAI Semantic Conventions (2026 표준)
GEN_AI_ATTRIBUTES = {
    "gen_ai.system": "gemini",
    "gen_ai.request.model": "gemini-2.0-flash",
    "gen_ai.request.max_tokens": 4096,
    "gen_ai.response.finish_reason": "stop",
    "gen_ai.usage.input_tokens": 0,
    "gen_ai.usage.output_tokens": 0,
    "gen_ai.usage.total_tokens": 0,
}


def setup_observability(app: FastAPI):
    """2026 Pattern: Full-stack observability with LLM tracing."""

    # 1. OpenTelemetry 기본 설정
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # 2. FastAPI 자동 계측
    FastAPIInstrumentor.instrument_app(app)

    # 3. SQLAlchemy 자동 계측
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
        enable_commenter=True,
    )

    # 4. OpenLLMetry (LLM 전용 계측)
    Traceloop.init(
        app_name="vivid-studio",
        disable_batch=settings.DEBUG,
        api_key=settings.TRACELOOP_API_KEY,  # 선택적
    )


# LLM 호출 래퍼 with 메트릭
class LLMObservabilityWrapper:
    """LLM 호출 관측성 래퍼."""

    def __init__(self):
        self.tracer = trace.get_tracer("vivid.llm")
        self.meter = metrics.get_meter("vivid.llm")

        # 메트릭 정의
        self.token_counter = self.meter.create_counter(
            "llm.tokens.total",
            description="Total tokens used",
        )
        self.cost_counter = self.meter.create_counter(
            "llm.cost.total",
            unit="usd",
            description="Total LLM cost",
        )
        self.latency_histogram = self.meter.create_histogram(
            "llm.request.duration",
            unit="ms",
            description="LLM request latency",
        )

    async def call_with_observability(
        self,
        model: str,
        prompt: str,
        **kwargs,
    ) -> tuple[str, dict]:
        """LLM 호출 + 자동 메트릭 수집."""

        with self.tracer.start_as_current_span(
            "llm.generate",
            attributes={
                "gen_ai.system": "gemini",
                "gen_ai.request.model": model,
                "gen_ai.request.max_tokens": kwargs.get("max_tokens", 4096),
            },
        ) as span:
            start_time = time.time()

            try:
                response = await generate_content(model, prompt, **kwargs)

                # 토큰 사용량 기록
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                total_tokens = input_tokens + output_tokens

                span.set_attributes({
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "gen_ai.response.finish_reason": response.candidates[0].finish_reason.name,
                })

                # 메트릭 업데이트
                self.token_counter.add(total_tokens, {"model": model})

                cost = self._calculate_cost(model, input_tokens, output_tokens)
                self.cost_counter.add(cost, {"model": model})

                latency = (time.time() - start_time) * 1000
                self.latency_histogram.record(latency, {"model": model})

                return response.text, {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost,
                    "latency_ms": latency,
                }

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                raise

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """모델별 비용 계산."""
        PRICING = {
            "gemini-2.0-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
            "gemini-2.0-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
        }
        pricing = PRICING.get(model, PRICING["gemini-2.0-flash"])
        return input_tokens * pricing["input"] + output_tokens * pricing["output"]
```

**Sources**:
- [OpenTelemetry for Generative AI](https://opentelemetry.io/blog/2024/otel-generative-ai/)
- [OpenLLMetry GitHub](https://github.com/traceloop/openllmetry)
- [AI Agents Observability with OpenTelemetry](https://victoriametrics.com/blog/ai-agents-observability/)

---

### H3.2 Test Coverage 60%+ (Branch Coverage + Mutation Testing)

**2026 Best Practice**: pytest-cov + pytest-asyncio + Mutation Testing

```python
# pytest.ini (설정)
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts =
    --cov=app
    --cov-branch
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=60
    -v
    --tb=short

# 커버리지 제외
[coverage:run]
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */conftest.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    @abstractmethod
```

```python
# tests/conftest.py (개선)
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Fixture: 테스트 DB (롤백 기반)
@pytest.fixture(scope="function")
async def db_session():
    """트랜잭션 기반 테스트 DB (자동 롤백)."""
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            # 자동 롤백
            await session.rollback()


# Fixture: 테스트 클라이언트
@pytest.fixture(scope="function")
async def client(db_session):
    """테스트용 AsyncClient."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Fixture: 인증된 클라이언트
@pytest.fixture
async def auth_client(client, test_user):
    """JWT 인증된 테스트 클라이언트."""
    token = create_access_token({"sub": test_user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    yield client


# Fixture: Mock LLM 응답
@pytest.fixture
def mock_llm_response():
    """LLM 응답 Mock."""
    with patch("app.generation_client.generate_content") as mock:
        mock.return_value = MockLLMResponse(
            text="Generated content",
            usage_metadata=MockUsage(
                prompt_token_count=100,
                candidates_token_count=50,
            ),
        )
        yield mock
```

```python
# tests/middleware/test_security_middleware.py (신규)
import pytest
from httpx import AsyncClient

class TestSecurityMiddleware:
    """보안 미들웨어 테스트 (현재 0% → 목표 100%)."""

    @pytest.mark.asyncio
    async def test_cors_blocked_origin(self, client):
        """허용되지 않은 Origin 차단."""
        response = await client.post(
            "/api/v1/ip/test/generate",
            headers={"Origin": "https://evil.com"},
            json={},
        )
        assert response.status_code == 403
        assert "Origin not allowed" in response.text

    @pytest.mark.asyncio
    async def test_content_type_validation(self, client):
        """Content-Type 검증."""
        response = await client.post(
            "/api/v1/workflow/start",
            headers={"Content-Type": "text/plain"},
            content="invalid",
        )
        assert response.status_code == 415

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """보안 헤더 존재 확인."""
        response = await client.get("/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "max-age" in response.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, client):
        """Rate Limit 적용 확인."""
        # 100회 요청
        for _ in range(101):
            response = await client.get("/api/v1/ip")

        assert response.status_code == 429
        assert "Retry-After" in response.headers
```

**Sources**:
- [Python Testing Best Practices 2025](https://danielsarney.com/blog/python-testing-best-practices-2025-building-reliable-applications/)
- [Maximizing Test Coverage with Pytest](https://www.graphapp.ai/blog/maximizing-test-coverage-with-pytest)
- [PyTest Code Coverage Explained](https://enodeas.com/pytest-code-coverage-explained/)

---

### H3.3 Error Response 표준화 (RFC 7807)

**2026 Best Practice**: RFC 7807 Problem Details + i18n

```python
# backend/app/schemas/error.py (신규)
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any

class ErrorCode(str, Enum):
    """표준 에러 코드."""

    # 인증/인가
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"

    # 리소스
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"

    # 비즈니스 로직
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    WORKFLOW_INVALID_STATE = "WORKFLOW_INVALID_STATE"

    # 결제
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_REFUND_FAILED = "PAYMENT_REFUND_FAILED"

    # 일반
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """RFC 7807 Problem Details 기반 에러 응답."""

    type: str = Field(
        description="에러 타입 URI",
        examples=["https://vivid.studio/errors/AUTH_TOKEN_EXPIRED"],
    )
    title: str = Field(description="사람이 읽을 수 있는 제목")
    status: int = Field(description="HTTP 상태 코드")
    detail: str = Field(description="상세 설명")
    instance: str | None = Field(
        default=None,
        description="에러 발생 URI",
    )

    # 확장 필드
    code: ErrorCode = Field(description="머신 리더블 에러 코드")
    trace_id: str | None = Field(default=None, description="추적 ID")
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="필드별 에러 목록",
    )

    # i18n
    title_ko: str | None = Field(default=None, description="한국어 제목")
    detail_ko: str | None = Field(default=None, description="한국어 상세")


# 에러 메시지 i18n
ERROR_MESSAGES = {
    ErrorCode.AUTH_TOKEN_EXPIRED: {
        "title": "Token Expired",
        "title_ko": "토큰 만료",
        "detail": "Your access token has expired. Please sign in again.",
        "detail_ko": "액세스 토큰이 만료되었습니다. 다시 로그인해 주세요.",
    },
    ErrorCode.INSUFFICIENT_CREDITS: {
        "title": "Insufficient Credits",
        "title_ko": "크레딧 부족",
        "detail": "You don't have enough credits for this operation.",
        "detail_ko": "이 작업을 수행하기 위한 크레딧이 부족합니다.",
    },
    # ... 더 많은 에러 코드
}


def create_error_response(
    code: ErrorCode,
    status: int,
    detail: str | None = None,
    instance: str | None = None,
    errors: list[dict] | None = None,
    trace_id: str | None = None,
) -> ErrorResponse:
    """표준 에러 응답 생성."""
    messages = ERROR_MESSAGES.get(code, {})

    return ErrorResponse(
        type=f"https://vivid.studio/errors/{code.value}",
        title=messages.get("title", code.value),
        status=status,
        detail=detail or messages.get("detail", "An error occurred"),
        instance=instance,
        code=code,
        trace_id=trace_id or get_current_trace_id(),
        errors=errors,
        title_ko=messages.get("title_ko"),
        detail_ko=messages.get("detail_ko"),
    )


# Exception Handler
@app.exception_handler(VividException)
async def vivid_exception_handler(request: Request, exc: VividException):
    """통합 예외 핸들러."""
    response = create_error_response(
        code=exc.code,
        status=exc.status_code,
        detail=exc.detail,
        instance=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True),
    )
```

---

## 🟢 H4: Automation & ML (P2) - Week 4-5

### H4.1 ML Feedback Loop (CRAG + Auto-Threshold)

**2026 Best Practice**: Corrective RAG + 피드백 기반 자동 threshold 조정

```python
# backend/app/services/ml_feedback_service.py (신규)
from dataclasses import dataclass
from enum import Enum
import numpy as np

class FeedbackAction(Enum):
    """피드백 기반 액션."""
    INDEX_TO_RAG = "index"          # RAG에 인덱싱
    FLAG_SOURCE = "flag"            # 소스 플래깅
    TRIGGER_CRAG = "crag"           # Corrective RAG 트리거
    INVALIDATE_CACHE = "cache"      # 캐시 무효화
    UPDATE_THRESHOLD = "threshold"  # Threshold 조정


@dataclass
class FeedbackSignal:
    """피드백 신호."""
    generation_id: str
    rating: int  # 1-5
    comment: str | None
    source_helpful: bool | None
    retrieval_relevant: bool | None


class MLFeedbackService:
    """2026 Pattern: CRAG + 자동 threshold 조정 피드백 루프."""

    def __init__(
        self,
        rag_service: HybridRAGService,
        qdrant_client: QdrantClient,
    ):
        self.rag_service = rag_service
        self.qdrant = qdrant_client

        # 동적 threshold (학습 가능)
        self.confidence_thresholds = {
            "auto_approve": 0.85,
            "manual_review": 0.50,
            "escalate": 0.30,
        }

        # EMA (지수 이동 평균) for threshold 조정
        self.ema_alpha = 0.1
        self.feedback_history: list[FeedbackSignal] = []

    async def process_feedback(
        self,
        signal: FeedbackSignal,
        db: AsyncSession,
    ) -> list[FeedbackAction]:
        """피드백 처리 + 액션 결정."""
        actions = []

        # 1. 긍정 피드백 → RAG 인덱싱
        if signal.rating >= 4 and signal.source_helpful:
            await self._index_positive_feedback(signal, db)
            actions.append(FeedbackAction.INDEX_TO_RAG)

        # 2. 부정 피드백 → CRAG + 소스 플래깅
        if signal.rating <= 2:
            await self._flag_poor_source(signal, db)
            actions.append(FeedbackAction.FLAG_SOURCE)

            if signal.retrieval_relevant is False:
                await self._trigger_crag(signal)
                actions.append(FeedbackAction.TRIGGER_CRAG)

            # 캐시 무효화
            await self._invalidate_related_cache(signal)
            actions.append(FeedbackAction.INVALIDATE_CACHE)

        # 3. Threshold 자동 조정
        self.feedback_history.append(signal)
        if len(self.feedback_history) >= 100:
            await self._auto_adjust_thresholds()
            actions.append(FeedbackAction.UPDATE_THRESHOLD)

        return actions

    async def _trigger_crag(self, signal: FeedbackSignal):
        """Corrective RAG: 검색 결과 품질 검증 후 재검색."""
        # 원본 쿼리 가져오기
        generation = await self._get_generation(signal.generation_id)
        original_query = generation.input_context.get("query")

        # 재검색 with stricter filters
        results = await self.rag_service.hybrid_query(
            query=original_query,
            dimension=generation.dimension,
            min_confidence=0.8,  # 더 엄격한 threshold
            rerank=True,
        )

        # 검색 결과 품질 검증
        quality_score = await self._evaluate_retrieval_quality(results)

        if quality_score < 0.7:
            # 웹 검색 fallback 또는 다른 전략
            await self._fallback_retrieval(original_query)

    async def _auto_adjust_thresholds(self):
        """EMA 기반 threshold 자동 조정."""
        recent = self.feedback_history[-100:]

        # 긍정 피드백 비율 계산
        positive_rate = sum(1 for f in recent if f.rating >= 4) / len(recent)

        # EMA 업데이트
        current_auto = self.confidence_thresholds["auto_approve"]

        if positive_rate < 0.7:
            # 품질 저하 → threshold 상향
            new_threshold = current_auto + (0.95 - current_auto) * self.ema_alpha
        else:
            # 품질 양호 → threshold 하향 (더 많은 자동 승인)
            new_threshold = current_auto - (current_auto - 0.75) * self.ema_alpha

        self.confidence_thresholds["auto_approve"] = max(0.75, min(0.95, new_threshold))

        # 로깅
        logger.info(
            f"Threshold auto-adjusted: {current_auto:.2f} → "
            f"{self.confidence_thresholds['auto_approve']:.2f} "
            f"(positive_rate={positive_rate:.2%})"
        )

        # 히스토리 정리
        self.feedback_history = recent[-50:]
```

**Sources**:
- [RAGOps: Operating and Managing RAG Pipelines](https://arxiv.org/html/2506.03401v1)
- [Top 5 RAG Evaluation Platforms in 2026](https://www.getmaxim.ai/articles/top-5-rag-evaluation-platforms-in-2026/)
- [Advanced RAG Techniques](https://neo4j.com/blog/genai/advanced-rag-techniques/)

---

### H4.2 Recommendation Engine (Hybrid Collaborative + Content)

**2026 Best Practice**: Matrix Factorization + Content-Based Hybrid

```python
# backend/app/services/recommendation_service.py (신규)
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import NamedTuple

class Recommendation(NamedTuple):
    item_id: str
    score: float
    reason: str  # "similar_users", "similar_content", "trending"


class HybridRecommendationEngine:
    """2026 Pattern: Collaborative + Content-Based 하이브리드 추천."""

    def __init__(
        self,
        n_factors: int = 50,
        alpha: float = 0.5,  # Collaborative vs Content 가중치
    ):
        self.n_factors = n_factors
        self.alpha = alpha
        self.svd = TruncatedSVD(n_components=n_factors)

        self._user_factors: np.ndarray | None = None
        self._item_factors: np.ndarray | None = None
        self._content_embeddings: dict[str, np.ndarray] = {}

    async def fit(
        self,
        interaction_matrix: np.ndarray,
        item_features: dict[str, np.ndarray],
    ):
        """모델 학습."""
        # 1. Matrix Factorization (Collaborative)
        self._user_factors = self.svd.fit_transform(interaction_matrix)
        self._item_factors = self.svd.components_.T

        # 2. Content Embeddings 저장
        self._content_embeddings = item_features

    async def recommend(
        self,
        user_id: str,
        user_history: list[str],
        n_recommendations: int = 10,
    ) -> list[Recommendation]:
        """하이브리드 추천."""

        # 1. Collaborative Filtering Score
        user_idx = self._get_user_index(user_id)
        if user_idx is not None and self._user_factors is not None:
            cf_scores = self._user_factors[user_idx] @ self._item_factors.T
        else:
            cf_scores = np.zeros(len(self._item_factors))

        # 2. Content-Based Score
        cb_scores = await self._content_based_scores(user_history)

        # 3. Hybrid Score
        hybrid_scores = self.alpha * cf_scores + (1 - self.alpha) * cb_scores

        # 4. 이미 본 아이템 제외
        for item_id in user_history:
            item_idx = self._get_item_index(item_id)
            if item_idx is not None:
                hybrid_scores[item_idx] = -np.inf

        # 5. Top-N 추천
        top_indices = np.argsort(hybrid_scores)[::-1][:n_recommendations]

        recommendations = []
        for idx in top_indices:
            item_id = self._get_item_id(idx)
            score = hybrid_scores[idx]

            # 추천 이유 결정
            reason = self._determine_reason(
                cf_score=cf_scores[idx],
                cb_score=cb_scores[idx],
            )

            recommendations.append(Recommendation(
                item_id=item_id,
                score=float(score),
                reason=reason,
            ))

        return recommendations

    async def _content_based_scores(
        self,
        user_history: list[str],
    ) -> np.ndarray:
        """Content-Based 점수 계산."""
        if not user_history:
            return np.zeros(len(self._item_factors))

        # 사용자 선호도 프로필 구축
        history_embeddings = [
            self._content_embeddings[item_id]
            for item_id in user_history
            if item_id in self._content_embeddings
        ]

        if not history_embeddings:
            return np.zeros(len(self._item_factors))

        user_profile = np.mean(history_embeddings, axis=0)

        # 모든 아이템과의 유사도
        all_embeddings = np.array(list(self._content_embeddings.values()))
        similarities = cosine_similarity([user_profile], all_embeddings)[0]

        return similarities

    def _determine_reason(self, cf_score: float, cb_score: float) -> str:
        """추천 이유 결정."""
        if cf_score > cb_score * 1.2:
            return "similar_users"
        elif cb_score > cf_score * 1.2:
            return "similar_content"
        else:
            return "hybrid_match"


# 콜드 스타트 처리
class ColdStartHandler:
    """신규 사용자/아이템 콜드 스타트 처리."""

    async def get_popular_items(self, n: int = 10) -> list[str]:
        """인기 아이템 반환 (콜드 스타트 fallback)."""
        pass

    async def get_similar_by_content(
        self,
        item_id: str,
        n: int = 10,
    ) -> list[str]:
        """Content 기반 유사 아이템 (신규 아이템용)."""
        pass
```

**Sources**:
- [Build a Recommendation Engine With Collaborative Filtering](https://realpython.com/build-recommendation-engine-collaborative-filtering/)
- [Practical Guide to Building Scalable Recommender Systems](https://medium.com/@anilcogalan/practical-guide-to-building-scalable-recommender-systems-in-python-b175547e6fce)

---

### H4.3 Distributed Rate Limiting (Token Bucket + Redis)

**2026 Best Practice**: Token Bucket + Redis Lua 원자성 + JWT 기반 차등

```python
# backend/app/middleware/rate_limit.py (신규)
import redis.asyncio as redis
from fastapi import Request, HTTPException
from datetime import datetime
import hashlib

# Redis Lua 스크립트 (원자성 보장)
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- 토큰 리필
local elapsed = now - last_refill
local refill = math.floor(elapsed * refill_rate)
tokens = math.min(capacity, tokens + refill)

-- 토큰 소비
if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)
    return {1, tokens}  -- 허용
else
    return {0, tokens}  -- 거부
end
"""


class DistributedRateLimiter:
    """2026 Pattern: Token Bucket + Redis + 플랜별 차등 제한."""

    PLAN_LIMITS = {
        "free": {"capacity": 100, "refill_rate": 1.0},      # 100 req, 1/sec 리필
        "starter": {"capacity": 500, "refill_rate": 5.0},
        "pro": {"capacity": 2000, "refill_rate": 20.0},
        "enterprise": {"capacity": 10000, "refill_rate": 100.0},
    }

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self._script_sha: str | None = None

    async def init(self):
        """Lua 스크립트 등록."""
        self._script_sha = await self.redis.script_load(TOKEN_BUCKET_SCRIPT)

    async def check_rate_limit(
        self,
        request: Request,
        user_id: str | None = None,
        plan: str = "free",
    ) -> tuple[bool, int, int]:
        """
        Rate limit 체크.

        Returns:
            (allowed, remaining_tokens, reset_seconds)
        """
        # 키 결정 (사용자 > IP)
        if user_id:
            key = f"rate_limit:user:{user_id}"
        else:
            client_ip = request.client.host
            key = f"rate_limit:ip:{client_ip}"

        # 플랜별 제한
        limits = self.PLAN_LIMITS.get(plan, self.PLAN_LIMITS["free"])

        # Token Bucket 체크 (Lua 스크립트)
        now = datetime.now().timestamp()
        result = await self.redis.evalsha(
            self._script_sha,
            1,
            key,
            limits["capacity"],
            limits["refill_rate"],
            now,
            1,  # 요청 1개
        )

        allowed = bool(result[0])
        remaining = int(result[1])

        # Reset 시간 계산
        if not allowed:
            reset_seconds = int((limits["capacity"] - remaining) / limits["refill_rate"])
        else:
            reset_seconds = int(limits["capacity"] / limits["refill_rate"])

        return allowed, remaining, reset_seconds

    async def apply_rate_limit(self, request: Request):
        """미들웨어에서 호출."""
        # JWT에서 사용자 정보 추출
        user_id, plan = await self._extract_user_info(request)

        allowed, remaining, reset = await self.check_rate_limit(
            request, user_id, plan
        )

        # 헤더 설정
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(reset),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                },
            )


# FastAPI 미들웨어
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 제외 경로
    if request.url.path in ["/health", "/metrics", "/docs"]:
        return await call_next(request)

    await rate_limiter.apply_rate_limit(request)

    response = await call_next(request)

    # 응답 헤더 추가
    response.headers["X-RateLimit-Remaining"] = str(
        request.state.rate_limit_remaining
    )
    response.headers["X-RateLimit-Reset"] = str(
        request.state.rate_limit_reset
    )

    return response
```

**Sources**:
- [Implementing a Rate Limiter with FastAPI and Redis](https://bryananthonio.com/blog/implementing-rate-limiter-fastapi-redis/)
- [RateLimit Python SlowAPI Token Bucket](https://johal.in/ratelimit-python-slowapi-token-bucket-async-throttling-2025/)
- [API Rate Limiting and Abuse Prevention at Scale](https://python.plainenglish.io/api-rate-limiting-and-abuse-prevention-at-scale-best-practices-with-fastapi-b5d31d690208)

---

## 🔵 H5: Production Readiness (P2) - Week 5-6

### H5.1 CI/CD Security Scanning (Semgrep + Bandit Hybrid)

**2026 Best Practice**: Semgrep (커스텀 룰) + Bandit (Python 특화) + pip-audit

```yaml
# .github/workflows/security.yml (신규)
name: Security Scanning

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  sast:
    name: SAST Scanning
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # 1. Semgrep (AST 기반, 커스텀 룰)
      - name: Run Semgrep
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/python
            p/security-audit
            p/owasp-top-ten
            p/secrets
            .semgrep/vivid-rules.yml
        env:
          SEMGREP_RULES_FROM_GITHUB: true

      # 2. Bandit (Python 특화)
      - name: Run Bandit
        run: |
          pip install bandit[toml]
          bandit -r backend/app -c pyproject.toml -f json -o bandit-report.json || true

          # Critical/High 발견 시 실패
          bandit -r backend/app -c pyproject.toml -ll -ii

      # 3. pip-audit (의존성 취약점)
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit -r backend/requirements.txt --strict

      # 4. Trivy (컨테이너 스캔)
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      # 5. Secret Detection
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
```

```yaml
# .semgrep/vivid-rules.yml (커스텀 룰)
rules:
  - id: vivid-no-raw-sql
    patterns:
      - pattern: $DB.execute($SQL)
      - pattern-not: $DB.execute(text($SQL))
    message: "Use SQLAlchemy text() for raw SQL to prevent injection"
    severity: ERROR
    languages: [python]

  - id: vivid-no-hardcoded-secrets
    patterns:
      - pattern-regex: (api[_-]?key|secret|password)\s*=\s*["'][^"']+["']
    message: "Don't hardcode secrets. Use environment variables."
    severity: ERROR
    languages: [python]

  - id: vivid-jwt-verify-signature
    patterns:
      - pattern: jwt.decode($TOKEN, ...)
      - pattern-not: jwt.decode($TOKEN, $KEY, algorithms=[...])
    message: "JWT decode must specify algorithms to prevent algorithm confusion"
    severity: ERROR
    languages: [python]
```

**Sources**:
- [DevSecOps Pipelines: Semgrep Python SAST Scans 2026](https://www.johal.in/devsecops-pipelines-semgrep-python-sast-scans-2026/)
- [Python static analysis comparison: Bandit vs Semgrep](https://semgrep.dev/blog/2021/python-static-analysis-comparison-bandit-semgrep/)
- [GitHub - Bandit](https://github.com/PyCQA/bandit)

---

## 검증 계획

### 보안 테스트 스크립트

```bash
#!/bin/bash
# scripts/security_test.sh

echo "=== Vivid Security Test Suite ==="

# 1. SAST
echo "\n[1/5] Running SAST..."
semgrep --config .semgrep/ backend/app
bandit -r backend/app -ll

# 2. 의존성 취약점
echo "\n[2/5] Checking dependencies..."
pip-audit -r backend/requirements.txt

# 3. CSRF/CORS 테스트
echo "\n[3/5] Testing CSRF/CORS..."
pytest tests/security/test_csrf_cors.py -v

# 4. RLS 테스트
echo "\n[4/5] Testing tenant isolation..."
pytest tests/security/test_tenant_isolation.py -v

# 5. Rate Limiting 테스트
echo "\n[5/5] Testing rate limiting..."
pytest tests/middleware/test_rate_limit.py -v

echo "\n=== Security tests complete ==="
```

### 성능 테스트 (locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class VividUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 로그인 및 토큰 획득
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@vivid.studio",
            "password": "testpass123",
        })
        self.token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(3)
    def browse_ip_catalog(self):
        self.client.get("/api/v1/ip")

    @task(2)
    def view_ip_detail(self):
        self.client.get("/api/v1/ip/dokabi")

    @task(1)
    def start_generation(self):
        self.client.post("/api/v1/ip/dokabi/generate", json={
            "preset_id": "default",
            "inputs": {"prompt": "test"},
        })
```

---

## 완료 기준 (Updated)

### Phase 완성도 목표 (2026 Best Practices 적용)

| Phase | 현재 | 목표 | 2026 혁신 포인트 |
|-------|------|------|------------------|
| 1 | 65% | 95% | OpenLLMetry + GenAI Semantic Conventions |
| 2 | 70% | 95% | PCI DSS 4.0 + Idempotency |
| 3 | 45% | 95% | Context-based DataLoader + Complexity Limit |
| 4 | 50% | 95% | gVisor runsc + Defense-in-Depth |
| 5 | 75% | 95% | Run-token 완전 흐름 |
| 6 | 85% | 95% | CRAG + Auto-threshold |
| 7 | 70% | 95% | WebSocket JWT Handshake |
| 8 | 75% | 95% | Hybrid Recommendation |
| 9 | 80% | 95% | Background Jobs + Scheduler |
| 10 | 65% | 95% | Multi-tenant RLS + Voice Chat |

### 인프라 목표 (2026 Standards)

| 영역 | 현재 | 목표 | 방법 |
|------|------|------|------|
| Test Coverage | 28% | 65%+ | pytest-cov + Branch Coverage |
| CSRF/Auth | Missing | 100% | Token Auth + Strict CORS |
| Secrets | Hardcoded | SecretStr | Pydantic SecretStr + Vault |
| Rate Limiting | Not wired | Token Bucket | Redis Lua + JWT 차등 |
| Error Response | 비표준 | RFC 7807 | ErrorResponse + i18n |
| SAST | 없음 | Semgrep+Bandit | GitHub Actions |
| Production Score | 6.1/10 | 9.0/10 | 종합 |

---

## Research Sources

### Security
- [FastAPI Security Best Practices](https://davidmuraya.com/blog/fastapi-security-guide/)
- [StackHawk CSRF Protection](https://www.stackhawk.com/blog/csrf-protection-in-fastapi/)
- [FastAPI JWT Auth - WebSocket](https://indominusbyte.github.io/fastapi-jwt-auth/advanced-usage/websocket/)
- [Stripe Integration Security Guide](https://docs.stripe.com/security/guide)

### Observability
- [OpenTelemetry for Generative AI](https://opentelemetry.io/blog/2024/otel-generative-ai/)
- [OpenLLMetry GitHub](https://github.com/traceloop/openllmetry)
- [AI Agents Observability](https://victoriametrics.com/blog/ai-agents-observability/)

### Database
- [AWS RLS Best Practices](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [Permit.io RLS Guide](https://www.permit.io/blog/postgres-rls-implementation-guide/)
- [Crunchy Data RLS](https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres)

### Sandbox
- [gVisor Security Model](https://gvisor.dev/docs/architecture_guide/security/)
- [Docker Seccomp](https://docs.docker.com/engine/security/seccomp/)

### GraphQL
- [Strawberry DataLoaders](https://strawberry.rocks/docs/guides/dataloaders)
- [N+1 in Strawberry GraphQL](https://blog.separateconcerns.com/2024-05-28-graphql-dataloaders.html)

### Testing
- [Python Testing Best Practices 2025](https://danielsarney.com/blog/python-testing-best-practices-2025-building-reliable-applications/)
- [PyTest Code Coverage Explained](https://enodeas.com/pytest-code-coverage-explained/)

### CI/CD
- [DevSecOps Semgrep 2026](https://www.johal.in/devsecops-pipelines-semgrep-python-sast-scans-2026/)
- [Bandit vs Semgrep](https://semgrep.dev/blog/2021/python-static-analysis-comparison-bandit-semgrep/)

### ML/RAG
- [RAGOps](https://arxiv.org/html/2506.03401v1)
- [Top 5 RAG Evaluation Platforms 2026](https://www.getmaxim.ai/articles/top-5-rag-evaluation-platforms-in-2026/)

### Rate Limiting
- [Rate Limiter FastAPI Redis](https://bryananthonio.com/blog/implementing-rate-limiter-fastapi-redis/)
- [Token Bucket SlowAPI](https://johal.in/ratelimit-python-slowapi-token-bucket-async-throttling-2025/)

---

> **이 문서는 2026년 1월 최신 웹서칭 리서치를 기반으로 작성되었습니다.**
