"""NotebookLM Authentication Service.

쿠키 유효성 검사 및 자동 갱신 관리.
상용 환경에서 NotebookLM API 호출의 안정성을 보장.

Usage:
    from app.rag.notebooklm_auth import get_auth_service, AuthStatus
    
    auth = get_auth_service()
    status = await auth.check_status()
    
    if status == AuthStatus.EXPIRED:
        # 알림 또는 자동 갱신
        await auth.refresh()
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Auth file path (notebooklm-mcp stores cookies here)
AUTH_FILE_PATH = Path.home() / ".notebooklm-mcp" / "auth.json"


class AuthStatus(Enum):
    """인증 상태."""
    VALID = "valid"
    EXPIRED = "expired"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class AuthInfo:
    """인증 정보."""
    status: AuthStatus
    last_validated: Optional[datetime] = None
    last_success: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class NotebookLMAuthService:
    """NotebookLM 인증 관리 서비스.
    
    - 쿠키 유효성 검사
    - 만료 예상 시간 추적
    - 성공/실패 기록
    """
    
    # Class-level tracking
    _last_success: Optional[datetime] = None
    _consecutive_failures: int = 0
    _last_error: Optional[str] = None
    
    def __init__(self):
        self._auth_file = AUTH_FILE_PATH
    
    async def check_status(self) -> AuthInfo:
        """현재 인증 상태 확인.
        
        Returns:
            AuthInfo with current status
        """
        if not self._auth_file.exists():
            return AuthInfo(
                status=AuthStatus.MISSING,
                error_message="Auth file not found. Run: notebooklm-mcp-auth"
            )
        
        try:
            with open(self._auth_file) as f:
                auth_data = json.load(f)
            
            cookies = auth_data.get("cookies", {})
            if not cookies:
                return AuthInfo(
                    status=AuthStatus.MISSING,
                    error_message="No cookies in auth file"
                )
            
            # Check required cookies
            required = ["SID", "HSID", "SSID"]
            if not all(k in cookies for k in required):
                return AuthInfo(
                    status=AuthStatus.EXPIRED,
                    error_message="Missing required cookies (SID, HSID, SSID)"
                )
            
            # Estimate expiry (Google cookies typically last 2 weeks)
            file_mtime = datetime.fromtimestamp(self._auth_file.stat().st_mtime)
            estimated_expiry = file_mtime + timedelta(days=14)
            
            if datetime.now() > estimated_expiry:
                return AuthInfo(
                    status=AuthStatus.EXPIRED,
                    expires_at=estimated_expiry,
                    last_success=self._last_success,
                    error_message="Cookies likely expired (>14 days old)"
                )
            
            # Check if we've had recent failures
            if self._consecutive_failures >= 3:
                return AuthInfo(
                    status=AuthStatus.EXPIRED,
                    last_success=self._last_success,
                    error_message=f"Consecutive failures: {self._consecutive_failures}. Last: {self._last_error}"
                )
            
            return AuthInfo(
                status=AuthStatus.VALID,
                last_validated=datetime.now(),
                last_success=self._last_success,
                expires_at=estimated_expiry,
            )
            
        except Exception as e:
            logger.error(f"[NotebookLM-Auth] Error checking status: {e}")
            return AuthInfo(
                status=AuthStatus.UNKNOWN,
                error_message=str(e)
            )
    
    def record_success(self) -> None:
        """성공적인 API 호출 기록."""
        self._last_success = datetime.now()
        self._consecutive_failures = 0
        self._last_error = None
        logger.debug("[NotebookLM-Auth] Recorded successful query")
    
    def record_failure(self, error: str) -> None:
        """실패한 API 호출 기록."""
        self._consecutive_failures += 1
        self._last_error = error
        logger.warning(f"[NotebookLM-Auth] Failure #{self._consecutive_failures}: {error}")
    
    def should_fallback(self) -> bool:
        """폴백 모드로 전환해야 하는지 확인.
        
        3회 연속 실패 시 True 반환.
        """
        return self._consecutive_failures >= 3
    
    def get_health_dict(self) -> dict:
        """헬스체크용 딕셔너리 반환."""
        # Use sync fallback - async in sync context is complex
        info = self._sync_check_status()
        
        return {
            "status": "healthy" if info.status == AuthStatus.VALID else "degraded",
            "auth_status": info.status.value,
            "last_success": self._last_success.isoformat() if self._last_success else None,
            "consecutive_failures": self._consecutive_failures,
            "expires_at": info.expires_at.isoformat() if info.expires_at else None,
            "error": info.error_message,
        }
    
    def _sync_check_status(self) -> AuthInfo:
        """동기 버전의 상태 체크 (완전 버전)."""
        if not self._auth_file.exists():
            return AuthInfo(
                status=AuthStatus.MISSING,
                error_message="Auth file not found"
            )
        
        if self._consecutive_failures >= 3:
            return AuthInfo(
                status=AuthStatus.EXPIRED,
                error_message=f"Consecutive failures: {self._consecutive_failures}"
            )
        
        # Calculate expiry from file modification time
        try:
            file_mtime = datetime.fromtimestamp(self._auth_file.stat().st_mtime)
            estimated_expiry = file_mtime + timedelta(days=14)
            
            if datetime.now() > estimated_expiry:
                return AuthInfo(
                    status=AuthStatus.EXPIRED,
                    expires_at=estimated_expiry,
                    error_message="Cookies likely expired (>14 days old)"
                )
            
            return AuthInfo(
                status=AuthStatus.VALID,
                expires_at=estimated_expiry,
                last_success=self._last_success,
            )
        except Exception:
            return AuthInfo(status=AuthStatus.VALID)
    
    async def refresh(self) -> bool:
        """쿠키 갱신 시도 (Playwright 사용).
        
        Returns:
            True if refresh successful
        """
        try:
            from app.rag.notebooklm_playwright import PlaywrightNotebookLMClient
            
            async with PlaywrightNotebookLMClient() as client:
                logged_in = await client.ensure_logged_in()
                if logged_in:
                    self.record_success()
                    logger.info("[NotebookLM-Auth] Session refreshed successfully")
                    return True
                else:
                    self.record_failure("Session refresh failed - login required")
                    return False
                    
        except ImportError:
            logger.error("[NotebookLM-Auth] Playwright not available for refresh")
            return False
        except Exception as e:
            self.record_failure(str(e))
            return False


# Singleton
_auth_service: Optional[NotebookLMAuthService] = None


def get_auth_service() -> NotebookLMAuthService:
    """인증 서비스 싱글톤 반환."""
    global _auth_service
    if _auth_service is None:
        _auth_service = NotebookLMAuthService()
    return _auth_service
