"""
Internal Service Router

내부 S2S 통신용 API 엔드포인트
- mTLS 인증 필수
- 크레딧 2-Phase Commit
- 서비스 간 통신
"""
from typing import Optional
import logging
import json
from datetime import datetime, timezone
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.middleware.mtls import (
    get_client_cert, 
    require_client_cert, 
    require_permission, 
    ClientCertInfo
)

router = APIRouter(prefix="/internal", tags=["internal"])
logger = logging.getLogger("internal")


# ============================================
# Request/Response Models
# ============================================

class CreditReserveRequest(BaseModel):
    """크레딧 예약 요청"""
    user_id: str = Field(..., description="사용자 ID")
    amount: int = Field(..., gt=0, description="예약할 금액")
    run_id: str = Field(..., description="실행 ID")
    ttl_seconds: int = Field(default=300, description="예약 유효 시간 (초)")


class CreditReserveResponse(BaseModel):
    """크레딧 예약 응답"""
    success: bool
    reservation_id: Optional[str] = None
    reserved_amount: int = 0
    error: Optional[str] = None


class CreditCommitRequest(BaseModel):
    """크레딧 확정 요청"""
    reservation_id: str = Field(..., description="예약 ID")
    actual_amount: int = Field(..., ge=0, description="실제 사용량")


class CreditCommitResponse(BaseModel):
    """크레딧 확정 응답"""
    success: bool
    committed_amount: int = 0
    refunded_amount: int = 0
    error: Optional[str] = None


class CreditRollbackRequest(BaseModel):
    """크레딧 롤백 요청"""
    reservation_id: str = Field(..., description="예약 ID")
    reason: str = Field(default="cancelled", description="롤백 사유")


class CreditRollbackResponse(BaseModel):
    """크레딧 롤백 응답"""
    success: bool
    refunded_amount: int = 0
    error: Optional[str] = None


class ServiceHealthResponse(BaseModel):
    """서비스 헬스 응답"""
    service: str
    status: str
    version: str
    mtls_verified: bool
    client_cn: Optional[str] = None


# ============================================
# In-Memory Reservation Store (Production: Redis)
# ============================================

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict
import secrets


@dataclass
class CreditReservation:
    """크레딧 예약"""
    reservation_id: str
    user_id: str
    run_id: str
    amount: int
    expires_at: datetime
    status: str = "reserved"  # reserved, committed, rolled_back


_reservations: Dict[str, CreditReservation] = {}
_reservations_lock = asyncio.Lock()  # 동시성 제어


def generate_reservation_id() -> str:
    return f"rsv_{secrets.token_hex(16)}"


# ============================================
# Endpoints
# ============================================

@router.post("/credit-reserve", response_model=CreditReserveResponse)
async def reserve_credits(
    request: CreditReserveRequest,
    client_cert: ClientCertInfo = Depends(require_permission("credit-reserve")),
):
    """
    크레딧 예약 (2-Phase Commit - Phase 1)
    """
    reservation_id = generate_reservation_id()
    
    # 로깅
    logger.info(json.dumps({
        "event": "credit_reserve",
        "reservation_id": reservation_id,
        "run_id": request.run_id,
        "amount": request.amount,
        "service": client_cert.subject_cn
    }))
    
    reservation = CreditReservation(
        reservation_id=reservation_id,
        user_id=request.user_id,
        run_id=request.run_id,
        amount=request.amount,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=request.ttl_seconds),
    )
    
    # Thread-safe write
    async with _reservations_lock:
        _reservations[reservation_id] = reservation
    
    return CreditReserveResponse(
        success=True,
        reservation_id=reservation_id,
        reserved_amount=request.amount,
    )


@router.post("/credit-commit", response_model=CreditCommitResponse)
async def commit_credits(
    request: CreditCommitRequest,
    client_cert: ClientCertInfo = Depends(require_permission("credit-commit")),
):
    """
    크레딧 확정 (2-Phase Commit - Phase 2)
    """
    async with _reservations_lock:
        reservation = _reservations.get(request.reservation_id)
        
        # Idempotency: 이미 commit된 경우 성공 처리
        if reservation and reservation.status == "committed":
            return CreditCommitResponse(
                success=True,
                committed_amount=reservation.amount, # 단순화
                refunded_amount=0,
            )

        if not reservation:
            return CreditCommitResponse(success=False, error="Reservation not found")
        
        if reservation.status != "reserved":
            return CreditCommitResponse(success=False, error=f"Reservation is {reservation.status}")
        
        if datetime.now(timezone.utc) > reservation.expires_at:
            reservation.status = "expired"
            return CreditCommitResponse(success=False, error="Reservation expired")
        
        # 실제 사용량 vs 예약량
        actual = min(request.actual_amount, reservation.amount)
        refund = reservation.amount - actual
        
        reservation.status = "committed"
    
    # 로깅
    logger.info(json.dumps({
        "event": "credit_commit",
        "reservation_id": request.reservation_id,
        "requested": request.actual_amount,
        "committed": actual,
        "refunded": refund,
        "service": client_cert.subject_cn
    }))
    
    return CreditCommitResponse(
        success=True,
        committed_amount=actual,
        refunded_amount=refund,
    )


@router.post("/credit-rollback", response_model=CreditRollbackResponse)
async def rollback_credits(
    request: CreditRollbackRequest,
    client_cert: ClientCertInfo = Depends(require_permission("credit-rollback")),
):
    """
    크레딧 롤백
    """
    async with _reservations_lock:
        reservation = _reservations.get(request.reservation_id)
        
        # Idempotency
        if reservation and reservation.status == "rolled_back":
            return CreditRollbackResponse(
                success=True,
                refunded_amount=reservation.amount,
            )
        
        if not reservation:
            return CreditRollbackResponse(success=False, error="Reservation not found")
        
        if reservation.status == "committed":
            return CreditRollbackResponse(success=False, error="Already committed")
        
        refund_amount = reservation.amount
        reservation.status = "rolled_back"
    
    # 로깅
    logger.info(json.dumps({
        "event": "credit_rollback",
        "reservation_id": request.reservation_id,
        "reason": request.reason,
        "refunded": refund_amount,
        "service": client_cert.subject_cn
    }))
    
    return CreditRollbackResponse(
        success=True,
        refunded_amount=refund_amount,
    )


@router.get("/health", response_model=ServiceHealthResponse)
async def internal_health(
    request: Request,
):
    """
    내부 헬스 체크
    
    mTLS 연결 상태를 포함한 서비스 상태 반환.
    """
    client_cert = get_client_cert(request)
    
    return ServiceHealthResponse(
        service="crebit-api",
        status="healthy",
        version="1.0.0",
        mtls_verified=client_cert is not None,
        client_cn=client_cert.subject_cn if client_cert else None,
    )


@router.post("/validate-service")
async def validate_service(
    client_cert: ClientCertInfo = Depends(require_client_cert),
):
    """
    서비스 인증 검증
    
    mTLS 클라이언트 인증서 정보 반환.
    """
    return {
        "valid": True,
        "service": client_cert.subject_cn,
        "issuer": client_cert.issuer_cn,
        "fingerprint": client_cert.fingerprint_sha256,
        "spiffe_id": client_cert.spiffe_id,
        "is_allowed": client_cert.is_allowed_service(),
    }
