"""MiniApps Router.

Handles dimension portal submission requests from users.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_miniapps import MiniAppSubmission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/miniapps", tags=["MiniApps"])


# =============================================================================
# Schemas
# =============================================================================

class MiniAppSubmissionRequest(BaseModel):
    """MiniApp submission request."""
    app_name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    source_type: str = Field(..., pattern="^(github|zip)$")
    github_url: Optional[HttpUrl] = None
    zip_file_uri: Optional[str] = None
    description: str = Field(..., max_length=2000)
    ai_tool: Optional[str] = None


class MiniAppSubmissionResponse(BaseModel):
    """MiniApp submission response."""
    id: UUID
    status: str
    message: str
    submitted_at: datetime


class MiniAppSubmissionListItem(BaseModel):
    """MiniApp submission list item."""
    id: UUID
    app_name: str
    category: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/submit", response_model=MiniAppSubmissionResponse)
async def submit_miniapp(
    request: MiniAppSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a new MiniApp/Dimension Portal proposal.

    The submission will be reviewed by the internal team.
    """
    # Validate source
    if request.source_type == "github" and not request.github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required for github source type")
    if request.source_type == "zip" and not request.zip_file_uri:
        raise HTTPException(status_code=400, detail="ZIP file URI is required for zip source type")

    # Create submission record
    submission = MiniAppSubmission(
        user_id=current_user["id"],
        app_name=request.app_name,
        category=request.category,
        source_type=request.source_type,
        github_url=str(request.github_url) if request.github_url else None,
        zip_file_uri=request.zip_file_uri,
        description=request.description,
        ai_tool=request.ai_tool,
        status="pending_review",
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    logger.info(f"MiniApp submitted: {request.app_name} by user {current_user['id']}")

    return MiniAppSubmissionResponse(
        id=submission.id,
        status="pending_review",
        message="Your submission has been received and is pending review.",
        submitted_at=submission.created_at,
    )


@router.get("/submissions", response_model=List[MiniAppSubmissionListItem])
async def list_my_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List my MiniApp submissions."""
    result = await db.execute(
        select(MiniAppSubmission)
        .where(MiniAppSubmission.user_id == current_user["id"])
        .order_by(MiniAppSubmission.created_at.desc())
    )
    submissions = result.scalars().all()
    return submissions
