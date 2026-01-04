"""
Run Token Router (Hardened)

앱 실행 토큰 API
- 토큰 발급 (Fingerprint 바인딩)
- 토큰 검증 (다중 검증)
- 크레딧 차감 (Rate Limit + Anomaly Detection)
- 토큰 취소

Security Hardening:
- Fingerprint 바인딩 (User-Agent + IP)
- Client IP 추적
- Anomaly 점수 응답
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from app.auth import require_user_id
from app.services.run_token_service import (
    get_run_token_service,
    RunTokenService,
    RunTokenStatus,
    FingerprintGenerator,
)
from app.services.app_registry import get_app_registry, AppRegistryService, AppStatus


router = APIRouter(prefix="/run-token", tags=["run-token"])


# ============================================
# Request/Response Models
# ============================================

class IssueTokenRequest(BaseModel):
    app_id: str = Field(..., description="앱 ID")
    credits_to_reserve: int = Field(default=0, ge=0, description="예약할 크레딧")
    permissions: List[str] = Field(default=[], description="요청 권한")


class IssueTokenResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    run_id: Optional[str] = None
    expires_at: Optional[str] = None
    credits_reserved: int = 0
    error: Optional[str] = None


class ValidateTokenRequest(BaseModel):
    token: str = Field(..., description="검증할 토큰")


class ValidateTokenResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    app_id: Optional[str] = None
    run_id: Optional[str] = None
    credits_reserved: int = 0
    credits_used: int = 0
    credits_remaining: int = 0
    permissions: List[str] = []
    error: Optional[str] = None


class DeductCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0, description="차감할 크레딧")
    reason: str = Field(default="usage", description="차감 사유")


class DeductCreditsResponse(BaseModel):
    success: bool
    credits_used: int = 0
    credits_remaining: int = 0
    error: Optional[str] = None


class RefundCreditsRequest(BaseModel):
    amount: Optional[int] = Field(default=None, ge=0, description="환불할 금액 (None=전체)")


class RefundCreditsResponse(BaseModel):
    success: bool
    refunded: int = 0
    error: Optional[str] = None


class RunStatusResponse(BaseModel):
    run_id: str
    user_id: str
    app_id: str
    status: str
    credits_reserved: int
    credits_used: int
    credits_remaining: int
    issued_at: str
    expires_at: str
    anomaly_score: float = 0.0  # 이상 점수


# ============================================
# Helper Functions
# ============================================

def get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출 (프록시 고려)"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_fingerprint(request: Request) -> str:
    """Fingerprint 생성"""
    return FingerprintGenerator.generate(
        user_agent=request.headers.get("user-agent", ""),
        client_ip=get_client_ip(request),
        accept_language=request.headers.get("accept-language", ""),
    )


# ============================================
# Dependencies
# ============================================

def get_token_service() -> RunTokenService:
    return get_run_token_service()


def get_registry() -> AppRegistryService:
    return get_app_registry()


async def verify_run_token(
    authorization: str = Header(..., description="Bearer {token}"),
    service: RunTokenService = Depends(get_token_service),
) -> dict:
    """Run Token 검증 의존성"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]  # "Bearer " 제거
    valid, payload, error = service.validate_token(token)
    
    if not valid:
        raise HTTPException(status_code=401, detail=error or "Invalid token")
    
    return {
        "user_id": payload.user_id,
        "app_id": payload.app_id,
        "run_id": payload.run_id,
        "credits_reserved": payload.credits_reserved,
        "credits_used": payload.credits_used,
        "permissions": payload.permissions,
    }


# ============================================
# Endpoints
# ============================================

@router.post("/issue", response_model=IssueTokenResponse)
async def issue_run_token(
    request_body: IssueTokenRequest,
    request: Request,
    user_id: str = Depends(require_user_id),
    service: RunTokenService = Depends(get_token_service),
    registry: AppRegistryService = Depends(get_registry),
):
    """
    Run Token 발급 (Hardened)
    
    앱 실행 전에 호출하여 토큰을 발급받습니다.
    Fingerprint 바인딩으로 토큰 도용을 방지합니다.
    """
    # 1. 앱 존재 및 활성 상태 확인
    app = registry.get_app(request_body.app_id)
    if not app:
        return IssueTokenResponse(success=False, error="App not found")
    
    if app.status != AppStatus.ACTIVE:
        return IssueTokenResponse(success=False, error=f"App is {app.status.value}")
    
    # 2. 크레딧 예약
    credits_to_reserve = request_body.credits_to_reserve
    if credits_to_reserve == 0 and app.manifest.credits:
        credits_to_reserve = app.manifest.credits.per_run
    
    # 3. Fingerprint 생성
    fingerprint = get_fingerprint(request)
    
    # 4. 토큰 발급
    success, token, run_id, error = await service.issue_token(
        user_id=user_id,
        app_id=request_body.app_id,
        credits_to_reserve=credits_to_reserve,
        permissions=request_body.permissions or app.manifest.permissions,
        fingerprint=fingerprint,
    )
    
    if not success:
        return IssueTokenResponse(success=False, error=error)
    
    # 4. 만료 시간 조회
    run_status = await service.get_run_status(run_id)
    
    return IssueTokenResponse(
        success=True,
        token=token,
        run_id=run_id,
        expires_at=run_status.get("expires_at") if run_status else None,
        credits_reserved=credits_to_reserve,
    )


@router.post("/validate", response_model=ValidateTokenResponse)
async def validate_run_token(
    request: ValidateTokenRequest,
    service: RunTokenService = Depends(get_token_service),
):
    """
    Run Token 검증
    
    토큰의 유효성을 확인하고 페이로드를 반환합니다.
    """
    valid, payload, error = service.validate_token(request.token)
    
    if not valid:
        return ValidateTokenResponse(valid=False, error=error)
    
    return ValidateTokenResponse(
        valid=True,
        user_id=payload.user_id,
        app_id=payload.app_id,
        run_id=payload.run_id,
        credits_reserved=payload.credits_reserved,
        credits_used=payload.credits_used,
        credits_remaining=payload.credits_reserved - payload.credits_used,
        permissions=payload.permissions,
    )


@router.post("/{run_id}/deduct", response_model=DeductCreditsResponse)
async def deduct_credits(
    run_id: str,
    request_body: DeductCreditsRequest,
    request: Request,
    token_data: dict = Depends(verify_run_token),
    service: RunTokenService = Depends(get_token_service),
):
    """
    크레딧 차감 (Hardened)
    
    Rate Limiting + Anomaly Detection 적용.
    의심스러운 활동 감지 시 토큰이 일시 중지됩니다.
    """
    # Run ID 일치 확인
    if token_data["run_id"] != run_id:
        return DeductCreditsResponse(success=False, error="Run ID mismatch")
    
    # 클라이언트 IP 추출
    client_ip = get_client_ip(request)
    
    success, used, remaining, error = await service.deduct_credits(
        run_id=run_id,
        amount=request_body.amount,
        reason=request_body.reason,
        client_ip=client_ip,
    )
    
    return DeductCreditsResponse(
        success=success,
        credits_used=used,
        credits_remaining=remaining,
        error=error,
    )


@router.post("/{run_id}/refund", response_model=RefundCreditsResponse)
async def refund_credits(
    run_id: str,
    request: RefundCreditsRequest,
    token_data: dict = Depends(verify_run_token),
    service: RunTokenService = Depends(get_token_service),
):
    """
    크레딧 환불
    
    미사용 크레딧을 환불합니다.
    앱 실행 완료 후 호출합니다.
    """
    # Run ID 일치 확인
    if token_data["run_id"] != run_id:
        return RefundCreditsResponse(success=False, error="Run ID mismatch")
    
    success, refunded, error = await service.refund_credits(
        run_id=run_id,
        amount=request.amount,
    )
    
    return RefundCreditsResponse(
        success=success,
        refunded=refunded,
        error=error,
    )


@router.delete("/{run_id}")
async def revoke_token(
    run_id: str,
    token_data: dict = Depends(verify_run_token),
    service: RunTokenService = Depends(get_token_service),
):
    """
    토큰 취소
    
    실행 중인 토큰을 취소합니다.
    """
    # Run ID 일치 확인
    if token_data["run_id"] != run_id:
        raise HTTPException(status_code=403, detail="Run ID mismatch")
    
    success = await service.revoke_token(run_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"success": True, "message": "Token revoked"}


@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str,
    token_data: dict = Depends(verify_run_token),
    service: RunTokenService = Depends(get_token_service),
):
    """
    실행 상태 조회
    """
    # Run ID 일치 확인
    if token_data["run_id"] != run_id:
        raise HTTPException(status_code=403, detail="Run ID mismatch")
    
    status = await service.get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return RunStatusResponse(
        run_id=run_id,
        user_id=status["user_id"],
        app_id=status["app_id"],
        status=status["status"],
        credits_reserved=status["credits_reserved"],
        credits_used=status["credits_used"],
        credits_remaining=status["credits_reserved"] - status["credits_used"],
        issued_at=status["issued_at"],
        expires_at=status["expires_at"],
        anomaly_score=status.get("anomaly_score", 0.0),
    )
