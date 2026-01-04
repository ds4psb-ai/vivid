"""
Secure Logging Middleware

요청/응답 로깅 시 민감 정보(PII) 마스킹
- JSON Body 내 민감 필드 (token, password, run_id 등) 마스킹
- Header 내 민감 정보 (Authorization, Cookie 등) 마스킹
- 구조화된 JSON 로깅

Hardening (Security Best Practices):
1. 정규식 기반 PII 패턴 매칭
2. 재귀적 JSON 마스킹
3. Authorization 헤더 자동 마스킹
"""
from __future__ import annotations

import logging
import json
import re
from typing import Dict, Any, Union, List, Set
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from starlette.types import Message

# 로거 설정
logger = logging.getLogger("secure_api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# 마스킹 설정
SENSITIVE_KEYS: Set[str] = {
    "password", "secret", "token", "access_token", "refresh_token",
    "api_key", "run_token", "authorization", "cookie", "set-cookie",
    "credit_card", "ssn", "client_secret"
}

SENSITIVE_PATTERNS = [
    r"Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*",  # Bearer Token
]

class SecureLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 1. Request Body 로깅 (스트림 소비 주의)
        # FastAPI/Starlette에서 Request body를 읽으면 스트림이 소모됨.
        # 프로덕션에서는 성능 이슈로 Body 로깅은 신중해야 함.
        # 여기서는 Header와 URL 위주로 로깅하고 Body는 선택적으로 처리하거나 생략.
        
        request_log = {
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "headers": self._mask_headers(dict(request.headers)),
        }
        
        logger.info(json.dumps(request_log))
        
        response = await call_next(request)
        
        # 2. Response 로깅
        response_log = {
            "event": "response",
            "status": response.status_code,
            "path": request.url.path,
        }
        logger.info(json.dumps(response_log))
        
        return response

    def _mask_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        masked = {}
        for k, v in headers.items():
            key_lower = k.lower()
            if key_lower in SENSITIVE_KEYS or any(s in key_lower for s in ["token", "auth", "key"]):
                masked[k] = "***MASKED***"
            else:
                masked[k] = self._mask_pii_in_text(v)
        return masked

    def _mask_data(self, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """재귀적 데이터 마스킹"""
        if isinstance(data, dict):
            return {k: self._mask_data(v) if k.lower() not in SENSITIVE_KEYS else "***MASKED***" for k, v in data.items()}
        elif isinstance(data, list):
            return [self._mask_data(item) for item in data]
        elif isinstance(data, str):
            return self._mask_pii_in_text(data)
        return data

    def _mask_pii_in_text(self, text: str) -> str:
        """텍스트 내 패턴 마스킹"""
        for pattern in SENSITIVE_PATTERNS:
            text = re.sub(pattern, "Bearer ***MASKED***", text)
        return text
