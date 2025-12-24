"""Spec and optimization endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.spec_engine import generate_spec_from_canvas, compute_graph
from app.ga_optimizer import optimize_canvas_params

router = APIRouter()


class SpecRequest(BaseModel):
    nodes: list
    edges: list


class SpecResponse(BaseModel):
    spec: dict
    generated: bool


class OptimizeRequest(BaseModel):
    nodes: list
    edges: list
    target_profile: str = "balanced"


class RecommendationResponse(BaseModel):
    params: dict
    fitness_score: float
    profile: str


class OptimizeResponse(BaseModel):
    recommendations: List[RecommendationResponse]


@router.post("/compute", response_model=SpecResponse)
async def compute_spec(data: SpecRequest) -> SpecResponse:
    """Compute spec from canvas graph."""
    spec = compute_graph(data.nodes, data.edges)
    return SpecResponse(spec=spec, generated=True)


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_params(data: OptimizeRequest) -> OptimizeResponse:
    """Run GA optimization on canvas parameters."""
    canvas_data = {"nodes": data.nodes, "edges": data.edges}
    recommendations = optimize_canvas_params(canvas_data, data.target_profile)
    
    return OptimizeResponse(
        recommendations=[
            RecommendationResponse(**rec) for rec in recommendations
        ]
    )
