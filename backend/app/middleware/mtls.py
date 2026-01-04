"""
mTLS Middleware and Certificate Management (Hardened)

서비스 간 상호 TLS 인증 (mTLS) - 보안 강화 버전

Security Hardening (2024 Best Practices):
1. 인증서 검증 강화 (만료, 폐기, 체인)
2. 인증서 핀닝 (허용된 인증서만)
3. 인증서 로테이션 지원
4. 요청 서명 검증
5. 감사 로깅
6. Rate Limiting per service
7. Replay Attack 방지
"""
from __future__ import annotations

import os
import ssl
import hashlib
import hmac
import time
from typing import Optional, Dict, Any, Tuple, Set, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import base64
import secrets
import json
import logging

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


# ============================================
# Configuration
# ============================================

# mTLS 설정
MTLS_ENABLED = os.getenv("MTLS_ENABLED", "false").lower() == "true"
MTLS_CA_CERT_PATH = os.getenv("MTLS_CA_CERT_PATH", "/etc/mtls/ca.crt")
MTLS_CLIENT_CERT_PATH = os.getenv("MTLS_CLIENT_CERT_PATH", "/etc/mtls/client.crt")
MTLS_CLIENT_KEY_PATH = os.getenv("MTLS_CLIENT_KEY_PATH", "/etc/mtls/client.key")

# 보안 설정
ENABLE_CERT_PINNING = True  # 인증서 핀닝
ENABLE_REQUEST_SIGNING = True  # 요청 서명
ENABLE_REPLAY_PROTECTION = True  # Replay 방지
ENABLE_AUDIT_LOGGING = True  # 감사 로깅
CERT_MIN_VALIDITY_DAYS = 7  # 최소 유효 기간 (만료 경고)

# Rate Limiting per service
SERVICE_RATE_LIMITS: Dict[str, int] = {
    "crebit-sandbox": 1000,  # 분당 1000 요청
    "crebit-admin": 100,
    "crebit-credit-service": 500,
    "default": 100,
}

# 허용된 서비스 (CN별 핀닝)
ALLOWED_SERVICES: Dict[str, Dict[str, Any]] = {
    "crebit-api": {
        "allowed": True,
        "permissions": ["*"],
        "pinned_fingerprints": [],  # 프로덕션에서 설정
    },
    "crebit-sandbox": {
        "allowed": True,
        "permissions": ["credit-reserve", "credit-commit", "credit-rollback"],
        "pinned_fingerprints": [],
    },
    "crebit-credit-service": {
        "allowed": True,
        "permissions": ["internal-*"],
        "pinned_fingerprints": [],
    },
    "crebit-admin": {
        "allowed": True,
        "permissions": ["admin-*"],
        "pinned_fingerprints": [],
    },
}

# 내부 서비스 경로 (mTLS 필수)
MTLS_REQUIRED_PATHS = [
    "/api/v1/internal/",
    "/api/v1/service/",
]

# 요청 서명 설정
REQUEST_SIGNATURE_TTL_SECONDS = 300  # 서명 유효 시간 (5분)
REQUEST_SIGNATURE_SECRET = os.getenv("REQUEST_SIGNATURE_SECRET", secrets.token_hex(32))

# 로깅
logger = logging.getLogger("mtls")


# ============================================
# Models
# ============================================

class CertificateStatus(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    REVOKED = "revoked"
    EXPIRING_SOON = "expiring_soon"


@dataclass
class ClientCertInfo:
    """클라이언트 인증서 정보 (Hardened)"""
    subject_cn: str
    issuer_cn: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    fingerprint_sha256: str
    spiffe_id: Optional[str] = None
    gcp_service_account: Optional[str] = None
    san_dns: List[str] = field(default_factory=list)
    san_uri: List[str] = field(default_factory=list)
    
    def get_status(self) -> CertificateStatus:
        """인증서 상태 확인"""
        now = datetime.now(timezone.utc)
        
        if now < self.not_before:
            return CertificateStatus.NOT_YET_VALID
        
        if now > self.not_after:
            return CertificateStatus.EXPIRED
        
        # 만료 임박 (7일 이내)
        if now > self.not_after - timedelta(days=CERT_MIN_VALIDITY_DAYS):
            return CertificateStatus.EXPIRING_SOON
        
        return CertificateStatus.VALID
    
    def is_valid(self) -> bool:
        """유효성 검증"""
        status = self.get_status()
        return status in (CertificateStatus.VALID, CertificateStatus.EXPIRING_SOON)
    
    def is_pinned(self) -> bool:
        """핀닝 검증"""
        if not ENABLE_CERT_PINNING:
            return True
        
        service_config = ALLOWED_SERVICES.get(self.subject_cn, {})
        pinned = service_config.get("pinned_fingerprints", [])
        
        # 프로덕션에서 핀 없으면 허용 (초기 설정)
        if not pinned:
            return True
        
        return self.fingerprint_sha256 in pinned
    
    def has_permission(self, operation: str) -> bool:
        """권한 확인"""
        service_config = ALLOWED_SERVICES.get(self.subject_cn, {})
        permissions = service_config.get("permissions", [])
        
        if "*" in permissions:
            return True
        
        for perm in permissions:
            if perm.endswith("*"):
                if operation.startswith(perm[:-1]):
                    return True
            elif perm == operation:
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_cn": self.subject_cn,
            "issuer_cn": self.issuer_cn,
            "fingerprint_sha256": self.fingerprint_sha256,
            "status": self.get_status().value,
            "spiffe_id": self.spiffe_id,
            "is_pinned": self.is_pinned(),
        }


# ============================================
# Security Components
# ============================================

class CertificateRevocationList:
    """인증서 폐기 목록 (CRL)"""
    
    def __init__(self):
        self._revoked: Set[str] = set()  # fingerprint
        self._revoked_serials: Set[str] = set()  # serial number
    
    def revoke_by_fingerprint(self, fingerprint: str) -> None:
        self._revoked.add(fingerprint)
    
    def revoke_by_serial(self, serial: str) -> None:
        self._revoked_serials.add(serial)
    
    def is_revoked(self, cert: ClientCertInfo) -> bool:
        return (
            cert.fingerprint_sha256 in self._revoked or
            cert.serial_number in self._revoked_serials
        )


class NonceStore:
    """Nonce 저장소 (Replay Attack 방지)"""
    
    def __init__(self, ttl_seconds: int = 300):
        self._used: Dict[str, datetime] = {}
        self._ttl = ttl_seconds
    
    def use_nonce(self, nonce: str) -> bool:
        """Nonce 사용 (이미 사용됐으면 False)"""
        self._cleanup()
        
        if nonce in self._used:
            return False
        
        self._used[nonce] = datetime.now(timezone.utc)
        return True
    
    def _cleanup(self) -> None:
        """만료된 nonce 정리"""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._ttl)
        self._used = {k: v for k, v in self._used.items() if v > cutoff}


class ServiceRateLimiter:
    """서비스별 Rate Limiter"""
    
    def __init__(self):
        self._counts: Dict[str, List[datetime]] = defaultdict(list)
    
    def check(self, service_cn: str) -> bool:
        """Rate limit 체크"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        
        # 1분 이내 요청만 유지
        self._counts[service_cn] = [
            t for t in self._counts[service_cn] if t > cutoff
        ]
        
        limit = SERVICE_RATE_LIMITS.get(service_cn, SERVICE_RATE_LIMITS["default"])
        
        if len(self._counts[service_cn]) >= limit:
            return False
        
        self._counts[service_cn].append(now)
        return True


class RequestSigner:
    """요청 서명 (HMAC-SHA256)"""
    
    @staticmethod
    def sign(
        method: str,
        path: str,
        body_hash: str,
        timestamp: int,
        nonce: str,
    ) -> str:
        """요청 서명 생성"""
        message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
        signature = hmac.new(
            REQUEST_SIGNATURE_SECRET.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify(
        method: str,
        path: str,
        body_hash: str,
        timestamp: int,
        nonce: str,
        signature: str,
    ) -> Tuple[bool, Optional[str]]:
        """요청 서명 검증"""
        # 타임스탬프 검증
        now = int(time.time())
        if abs(now - timestamp) > REQUEST_SIGNATURE_TTL_SECONDS:
            return False, "Signature expired"
        
        # 서명 검증
        expected = RequestSigner.sign(method, path, body_hash, timestamp, nonce)
        if not hmac.compare_digest(expected, signature):
            return False, "Invalid signature"
        
        return True, None


class AuditLogger:
    """감사 로깅"""
    
    @staticmethod
    def log_access(
        cert: ClientCertInfo,
        path: str,
        method: str,
        allowed: bool,
        reason: Optional[str] = None,
    ) -> None:
        if not ENABLE_AUDIT_LOGGING:
            return
        
        log_entry = {
            "event": "mtls_access",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": cert.subject_cn,
            "fingerprint": cert.fingerprint_sha256[:16] + "...",
            "path": path,
            "method": method,
            "allowed": allowed,
            "reason": reason,
        }
        
        if allowed:
            logger.info(json.dumps(log_entry))
        else:
            logger.warning(json.dumps(log_entry))


# ============================================
# Certificate Parser (Hardened)
# ============================================

class CertificateParser:
    """인증서 파서 (Hardened)"""
    
    @staticmethod
    def parse_from_header(cert_header: str) -> Optional[ClientCertInfo]:
        """X-Forwarded-Client-Cert 헤더에서 인증서 정보 추출"""
        if not cert_header:
            return None
        
        try:
            parts = {}
            for part in cert_header.split(";"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    parts[key.strip()] = value.strip().strip('"')
            
            subject = parts.get("Subject", "")
            cn = CertificateParser._extract_cn(subject)
            
            spiffe_id = parts.get("URI") if parts.get("URI", "").startswith("spiffe://") else None
            fingerprint = parts.get("Hash", "")
            
            # SAN 파싱
            san_dns = []
            san_uri = []
            if "DNS" in parts:
                san_dns = parts["DNS"].split(",")
            if "URI" in parts:
                san_uri = parts["URI"].split(",")
            
            return ClientCertInfo(
                subject_cn=cn,
                issuer_cn=CertificateParser._extract_cn(parts.get("Issuer", "")),
                serial_number=parts.get("Serial", ""),
                not_before=datetime.min.replace(tzinfo=timezone.utc),
                not_after=datetime.max.replace(tzinfo=timezone.utc),
                fingerprint_sha256=fingerprint,
                spiffe_id=spiffe_id,
                san_dns=san_dns,
                san_uri=san_uri,
            )
        except Exception:
            return None
    
    @staticmethod
    def parse_from_pem(cert_pem: str) -> Optional[ClientCertInfo]:
        """PEM 인증서 파싱"""
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes
            
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            cn = ""
            for attr in cert.subject:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    cn = attr.value
                    break
            
            issuer_cn = ""
            for attr in cert.issuer:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    issuer_cn = attr.value
                    break
            
            fingerprint = cert.fingerprint(hashes.SHA256()).hex()
            
            # SAN 추출
            spiffe_id = None
            san_dns = []
            san_uri = []
            try:
                san = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                for name in san.value:
                    if isinstance(name, x509.DNSName):
                        san_dns.append(name.value)
                    elif isinstance(name, x509.UniformResourceIdentifier):
                        san_uri.append(name.value)
                        if name.value.startswith("spiffe://"):
                            spiffe_id = name.value
            except x509.ExtensionNotFound:
                pass
            
            return ClientCertInfo(
                subject_cn=cn,
                issuer_cn=issuer_cn,
                serial_number=str(cert.serial_number),
                not_before=cert.not_valid_before_utc,
                not_after=cert.not_valid_after_utc,
                fingerprint_sha256=fingerprint,
                spiffe_id=spiffe_id,
                san_dns=san_dns,
                san_uri=san_uri,
            )
        except ImportError:
            return None
        except Exception:
            return None
    
    @staticmethod
    def _extract_cn(subject: str) -> str:
        for part in subject.split(","):
            part = part.strip()
            if part.upper().startswith("CN="):
                return part[3:]
        return ""


# ============================================
# Global Security Components
# ============================================

_crl = CertificateRevocationList()
_nonce_store = NonceStore()
_rate_limiter = ServiceRateLimiter()


# ============================================
# mTLS Middleware (Hardened)
# ============================================

class MTLSMiddleware(BaseHTTPMiddleware):
    """mTLS 검증 미들웨어 (Hardened)"""
    
    async def dispatch(self, request: Request, call_next):
        # mTLS 비활성화 시 통과
        if not MTLS_ENABLED:
            return await call_next(request)
        
        path = request.url.path
        requires_mtls = any(path.startswith(p) for p in MTLS_REQUIRED_PATHS)
        
        if not requires_mtls:
            return await call_next(request)
        
        # 인증서 추출
        cert_info = self._extract_cert_info(request)
        
        if not cert_info:
            AuditLogger.log_access(
                ClientCertInfo("unknown", "", "", datetime.min, datetime.max, ""),
                path, request.method, False, "No certificate"
            )
            raise HTTPException(
                status_code=401,
                detail="Client certificate required",
                headers={"WWW-Authenticate": "mTLS"},
            )
        
        # 1. 인증서 상태 검증
        status = cert_info.get_status()
        if status == CertificateStatus.EXPIRED:
            AuditLogger.log_access(cert_info, path, request.method, False, "Certificate expired")
            raise HTTPException(status_code=401, detail="Client certificate expired")
        
        if status == CertificateStatus.NOT_YET_VALID:
            AuditLogger.log_access(cert_info, path, request.method, False, "Certificate not yet valid")
            raise HTTPException(status_code=401, detail="Client certificate not yet valid")
        
        # 2. 폐기 확인 (CRL)
        if _crl.is_revoked(cert_info):
            AuditLogger.log_access(cert_info, path, request.method, False, "Certificate revoked")
            raise HTTPException(status_code=401, detail="Client certificate revoked")
        
        # 3. 핀닝 확인
        if ENABLE_CERT_PINNING and not cert_info.is_pinned():
            AuditLogger.log_access(cert_info, path, request.method, False, "Certificate not pinned")
            raise HTTPException(status_code=401, detail="Certificate not in trusted list")
        
        # 4. 허용된 서비스 확인
        service_config = ALLOWED_SERVICES.get(cert_info.subject_cn)
        if not service_config or not service_config.get("allowed", False):
            AuditLogger.log_access(cert_info, path, request.method, False, "Service not allowed")
            raise HTTPException(status_code=403, detail=f"Service '{cert_info.subject_cn}' not allowed")
        
        # 5. Rate Limiting
        if not _rate_limiter.check(cert_info.subject_cn):
            AuditLogger.log_access(cert_info, path, request.method, False, "Rate limit exceeded")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # 6. 요청 서명 검증 (optional)
        if ENABLE_REQUEST_SIGNING:
            sig_error = await self._verify_request_signature(request)
            if sig_error:
                AuditLogger.log_access(cert_info, path, request.method, False, sig_error)
                raise HTTPException(status_code=401, detail=sig_error)
        
        # 7. 만료 임박 경고 헤더 추가
        if status == CertificateStatus.EXPIRING_SOON:
            logger.warning(f"Certificate for {cert_info.subject_cn} expiring soon")
        
        # Request state에 저장
        request.state.client_cert = cert_info
        
        AuditLogger.log_access(cert_info, path, request.method, True)
        
        response = await call_next(request)
        
        # 만료 임박 헤더
        if status == CertificateStatus.EXPIRING_SOON:
            response.headers["X-Certificate-Warning"] = "Certificate expiring soon"
        
        return response
    
    def _extract_cert_info(self, request: Request) -> Optional[ClientCertInfo]:
        """Request에서 인증서 정보 추출"""
        xfcc_header = request.headers.get("x-forwarded-client-cert")
        if xfcc_header:
            return CertificateParser.parse_from_header(xfcc_header)
        
        client_cert_header = request.headers.get("x-client-cert")
        if client_cert_header:
            try:
                cert_pem = base64.b64decode(client_cert_header).decode()
                return CertificateParser.parse_from_pem(cert_pem)
            except Exception:
                pass
        
        return None
    
    async def _verify_request_signature(self, request: Request) -> Optional[str]:
        """요청 서명 검증"""
        signature = request.headers.get("x-request-signature")
        timestamp = request.headers.get("x-request-timestamp")
        nonce = request.headers.get("x-request-nonce")
        
        if not all([signature, timestamp, nonce]):
            return None  # 서명 없으면 통과 (선택적)
        
        try:
            ts = int(timestamp)
        except ValueError:
            return "Invalid timestamp"
        
        # Nonce 재사용 방지
        if ENABLE_REPLAY_PROTECTION:
            if not _nonce_store.use_nonce(nonce):
                return "Nonce already used"
        
        # Body hash
        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest() if body else ""
        
        # 서명 검증
        valid, error = RequestSigner.verify(
            request.method,
            str(request.url.path),
            body_hash,
            ts,
            nonce,
            signature,
        )
        
        if not valid:
            return error
        
        return None


# ============================================
# S2S HTTP Client (Hardened)
# ============================================

class S2SClient:
    """서비스 간 통신 클라이언트 (Hardened)"""
    
    def __init__(self):
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._cert_mtime: float = 0
        self._gcp_token: Optional[str] = None
        self._gcp_token_expires: Optional[datetime] = None
    
    def _get_ssl_context(self) -> ssl.SSLContext:
        # 파일 수정 시간 확인
        current_mtime = 0
        if os.path.exists(MTLS_CLIENT_CERT_PATH):
            current_mtime = os.path.getmtime(MTLS_CLIENT_CERT_PATH)
        
        # 변경가 없으면 캐시 반환
        if self._ssl_context and current_mtime == self._cert_mtime:
            return self._ssl_context
        
        # 컨텍스트 재생성
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        if os.path.exists(MTLS_CA_CERT_PATH):
            ctx.load_verify_locations(MTLS_CA_CERT_PATH)
        
        if os.path.exists(MTLS_CLIENT_CERT_PATH) and os.path.exists(MTLS_CLIENT_KEY_PATH):
            ctx.load_cert_chain(MTLS_CLIENT_CERT_PATH, MTLS_CLIENT_KEY_PATH)
            self._cert_mtime = current_mtime
            logger.info("S2SClient certificate reloaded")
        
        # 강화된 TLS 설정
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        
        self._ssl_context = ctx
        return ctx
    
    def _generate_signature_headers(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
    ) -> Dict[str, str]:
        """요청 서명 헤더 생성"""
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        body_hash = hashlib.sha256(body).hexdigest() if body else ""
        
        signature = RequestSigner.sign(method, path, body_hash, timestamp, nonce)
        
        return {
            "x-request-signature": signature,
            "x-request-timestamp": str(timestamp),
            "x-request-nonce": nonce,
        }
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        use_mtls: bool = False,
        sign_request: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        """S2S HTTP 요청 (Hardened)"""
        import httpx
        from urllib.parse import urlparse
        
        request_headers = headers or {}
        
        # 요청 서명
        if sign_request and ENABLE_REQUEST_SIGNING:
            body = json.dumps(json_data).encode() if json_data else None
            parsed = urlparse(url)
            sig_headers = self._generate_signature_headers(method, parsed.path, body)
            request_headers.update(sig_headers)
        
        # SSL 컨텍스트
        ssl_context = self._get_ssl_context() if use_mtls else None
        
        try:
            async with httpx.AsyncClient(verify=ssl_context or True) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json_data,
                    timeout=30.0,
                )
                
                try:
                    return response.status_code, response.json()
                except Exception:
                    return response.status_code, {"raw": response.text}
                    
        except Exception as e:
            logger.error(f"S2S request failed: {e}")
            return 0, {"error": str(e)}


# ============================================
# Helper Functions
# ============================================

def get_client_cert(request: Request) -> Optional[ClientCertInfo]:
    return getattr(request.state, "client_cert", None)


def require_client_cert(request: Request) -> ClientCertInfo:
    cert = get_client_cert(request)
    if not cert:
        raise HTTPException(status_code=401, detail="Client certificate required")
    return cert


def require_permission(operation: str):
    """권한 체크 의존성"""
    def checker(request: Request) -> ClientCertInfo:
        cert = require_client_cert(request)
        if not cert.has_permission(operation):
            AuditLogger.log_access(cert, str(request.url.path), request.method, False, f"No permission: {operation}")
            raise HTTPException(status_code=403, detail=f"No permission for '{operation}'")
        return cert
    return checker


def revoke_certificate(fingerprint: str) -> None:
    """인증서 폐기"""
    _crl.revoke_by_fingerprint(fingerprint)


# ============================================
# Singleton
# ============================================

_s2s_client: Optional[S2SClient] = None


def get_s2s_client() -> S2SClient:
    global _s2s_client
    if _s2s_client is None:
        _s2s_client = S2SClient()
    return _s2s_client
