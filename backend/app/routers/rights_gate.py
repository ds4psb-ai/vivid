"""Rights gate API endpoints for Original-IP Foundry."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.rights_gate_service import RightsGateService


router = APIRouter()
_service = RightsGateService()


class RightsAssetPayload(BaseModel):
    derivative_allowed: bool = True
    allowed_actions: List[str] = Field(default_factory=list)


class PreGenRequest(BaseModel):
    action: str
    rights_asset: RightsAssetPayload
    evidence_refs: List[str] = Field(default_factory=list)


class PostGenRequest(BaseModel):
    clone_risk: float = 0.0
    threshold: float = 0.6
    evidence_refs: List[str] = Field(default_factory=list)


class GateResponse(BaseModel):
    decision: str
    reason_codes: List[str]
    evidence_refs: List[str]


@router.post("/check-pre-gen", response_model=GateResponse)
async def check_pre_gen(payload: PreGenRequest) -> GateResponse:
    result = _service.check_pre_generation(payload.model_dump())
    return GateResponse(**result)


@router.post("/check-post-gen", response_model=GateResponse)
async def check_post_gen(payload: PostGenRequest) -> GateResponse:
    result = _service.check_post_generation(payload.model_dump())
    return GateResponse(**result)
