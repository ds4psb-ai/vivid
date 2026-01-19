"""Workflow Run-Token Integration Service.

워크플로우 실행에 run-token을 통합합니다.

SSoT Decision (SSoT-DEC-003):
- /workflow/plan → estimate only (no reservation)
- /workflow/start → run-token reserve
- /workflow/advance|execute → deduct per step
- completion/failure → refund remaining

Features:
- 크레딧 예약/차감/환불 통합
- 실패 시 자동 롤백
- 402 Insufficient Credits 처리

Usage:
    from app.services.workflow_run_token import WorkflowRunTokenService

    service = WorkflowRunTokenService()

    # 워크플로우 시작 시
    token_info = await service.reserve_for_workflow(
        user_id, execution_id, estimated_credits
    )

    # 스텝 실행 시
    await service.deduct_for_step(token_info.run_id, step_credits)

    # 완료 시
    await service.finalize_workflow(token_info.run_id, success=True)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

from app.logging_config import get_logger
from app.services.run_token_service import (
    get_run_token_service,
    RunTokenService,
    RunTokenStatus,
)

logger = get_logger("workflow_run_token")


@dataclass
class WorkflowTokenInfo:
    """워크플로우 토큰 정보."""
    run_id: str
    token: str
    credits_reserved: int
    credits_used: int = 0


class WorkflowRunTokenService:
    """워크플로우 run-token 통합 서비스."""

    def __init__(
        self,
        run_token_service: Optional[RunTokenService] = None,
    ) -> None:
        """Initialize service.

        Args:
            run_token_service: Run token 서비스 (None이면 싱글톤 사용)
        """
        self._run_token = run_token_service or get_run_token_service()

    # -------------------------------------------------------------------------
    # Reserve (workflow/start)
    # -------------------------------------------------------------------------

    async def reserve_for_workflow(
        self,
        user_id: str,
        execution_id: uuid.UUID,
        estimated_credits: int,
        fingerprint: Optional[str] = None,
    ) -> Tuple[bool, Optional[WorkflowTokenInfo], Optional[str]]:
        """워크플로우 시작 시 크레딧 예약.

        Args:
            user_id: 사용자 ID
            execution_id: 워크플로우 실행 ID
            estimated_credits: 예상 크레딧
            fingerprint: 클라이언트 fingerprint

        Returns:
            (성공 여부, 토큰 정보, 에러 메시지)
        """
        # app_id는 workflow 타입으로 설정
        app_id = f"workflow:{execution_id}"

        success, token, run_id, error = await self._run_token.issue_token(
            user_id=user_id,
            app_id=app_id,
            credits_to_reserve=estimated_credits,
            permissions=["workflow:execute"],
            fingerprint=fingerprint,
        )

        if not success:
            logger.error(
                f"[WorkflowToken] Reserve failed | user={user_id} | "
                f"execution={execution_id} | error={error}"
            )
            return False, None, error

        token_info = WorkflowTokenInfo(
            run_id=run_id,
            token=token,
            credits_reserved=estimated_credits,
        )

        logger.info(
            f"[WorkflowToken] Reserved | user={user_id} | "
            f"execution={execution_id} | credits={estimated_credits}"
        )

        return True, token_info, None

    # -------------------------------------------------------------------------
    # Deduct (workflow/advance per step)
    # -------------------------------------------------------------------------

    async def deduct_for_step(
        self,
        run_id: str,
        step_credits: int,
        step_id: str = "",
        client_ip: Optional[str] = None,
    ) -> Tuple[bool, int, Optional[str]]:
        """스텝 실행 시 크레딧 차감.

        Args:
            run_id: Run token ID
            step_credits: 스텝에 필요한 크레딧
            step_id: 스텝 식별자 (로깅용)
            client_ip: 클라이언트 IP

        Returns:
            (성공 여부, 잔여 크레딧, 에러 메시지)
        """
        success, used, remaining, error = await self._run_token.deduct_credits(
            run_id=run_id,
            amount=step_credits,
            reason=f"workflow_step:{step_id}",
            client_ip=client_ip,
        )

        if not success:
            logger.warning(
                f"[WorkflowToken] Deduct failed | run_id={run_id} | "
                f"step={step_id} | error={error}"
            )
            return False, 0, error

        logger.debug(
            f"[WorkflowToken] Deducted | run_id={run_id} | "
            f"step={step_id} | amount={step_credits} | remaining={remaining}"
        )

        return True, remaining, None

    # -------------------------------------------------------------------------
    # Finalize (workflow completion/failure)
    # -------------------------------------------------------------------------

    async def finalize_workflow(
        self,
        run_id: str,
        success: bool = True,
        refund_unused: bool = True,
    ) -> Tuple[bool, int, Optional[str]]:
        """워크플로우 완료/실패 시 토큰 정리.

        Args:
            run_id: Run token ID
            success: 성공 여부
            refund_unused: 미사용 크레딧 환불 여부

        Returns:
            (성공 여부, 환불 금액, 에러 메시지)
        """
        refunded = 0

        if refund_unused:
            ref_success, refunded, error = await self._run_token.refund_credits(
                run_id=run_id,
                amount=None,  # 전액 환불
            )

            if not ref_success:
                logger.warning(
                    f"[WorkflowToken] Refund failed | run_id={run_id} | "
                    f"error={error}"
                )
                return False, 0, error

        status_str = "completed" if success else "failed"
        logger.info(
            f"[WorkflowToken] Finalized | run_id={run_id} | "
            f"status={status_str} | refunded={refunded}"
        )

        return True, refunded, None

    # -------------------------------------------------------------------------
    # Check Balance
    # -------------------------------------------------------------------------

    async def check_balance(
        self,
        run_id: str,
        required_credits: int,
    ) -> Tuple[bool, int, Optional[str]]:
        """잔여 크레딧 확인.

        Args:
            run_id: Run token ID
            required_credits: 필요 크레딧

        Returns:
            (충분 여부, 잔여 크레딧, 에러 메시지)
        """
        status = await self._run_token.get_run_status(run_id)
        if not status:
            return False, 0, "Run not found"

        if status["status"] != RunTokenStatus.ACTIVE.value:
            return False, 0, f"Run is {status['status']}"

        remaining = status["credits_reserved"] - status["credits_used"]

        if remaining < required_credits:
            return False, remaining, f"Insufficient credits: need {required_credits}, have {remaining}"

        return True, remaining, None

    # -------------------------------------------------------------------------
    # Rollback (on step failure)
    # -------------------------------------------------------------------------

    async def rollback_step(
        self,
        run_id: str,
        step_credits: int,
        step_id: str = "",
    ) -> Tuple[bool, Optional[str]]:
        """스텝 실패 시 크레딧 롤백.

        Note: run-token은 실제 차감 전 예약 방식이므로
              실패 시 단순히 차감 안 하면 됨.
              이 함수는 명시적 롤백이 필요한 경우 사용.

        Args:
            run_id: Run token ID
            step_credits: 롤백할 크레딧
            step_id: 스텝 식별자

        Returns:
            (성공 여부, 에러 메시지)
        """
        # run-token은 예약 방식이므로 별도 롤백 불필요
        # 단, 이미 차감된 경우 refund로 처리
        logger.debug(
            f"[WorkflowToken] Step rollback (no-op) | run_id={run_id} | "
            f"step={step_id}"
        )
        return True, None


# Singleton
_workflow_run_token_service: Optional[WorkflowRunTokenService] = None


def get_workflow_run_token_service() -> WorkflowRunTokenService:
    """워크플로우 run-token 서비스 싱글톤."""
    global _workflow_run_token_service
    if _workflow_run_token_service is None:
        _workflow_run_token_service = WorkflowRunTokenService()
    return _workflow_run_token_service
