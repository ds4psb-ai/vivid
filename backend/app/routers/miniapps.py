"""MiniApps Router.

Handles dimension portal submission requests from users.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/miniapps", tags=["MiniApps"])


# =============================================================================
# Schemas
# =============================================================================

class MiniAppSubmission(BaseModel):
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


# =============================================================================
# In-Memory Storage (Replace with DB model in production)
# =============================================================================

_submissions: List[dict] = []


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/submit", response_model=MiniAppSubmissionResponse)
async def submit_miniapp(
    submission: MiniAppSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a new MiniApp/Dimension Portal proposal.

    The submission will be reviewed by the internal team.
    """
    # Validate source
    if submission.source_type == "github" and not submission.github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required for github source type")
    if submission.source_type == "zip" and not submission.zip_file_uri:
        raise HTTPException(status_code=400, detail="ZIP file URI is required for zip source type")

    submission_id = uuid4()
    submitted_at = datetime.utcnow()

    # Store submission (in-memory for now)
    record = {
        "id": submission_id,
        "user_id": current_user["id"],
        "app_name": submission.app_name,
        "category": submission.category,
        "source_type": submission.source_type,
        "github_url": str(submission.github_url) if submission.github_url else None,
        "zip_file_uri": submission.zip_file_uri,
        "description": submission.description,
        "ai_tool": submission.ai_tool,
        "status": "pending_review",
        "submitted_at": submitted_at,
    }
    _submissions.append(record)

    logger.info(f"MiniApp submitted: {submission.app_name} by user {current_user['id']}")

    return MiniAppSubmissionResponse(
        id=submission_id,
        status="pending_review",
        message="Your submission has been received and is pending review.",
        submitted_at=submitted_at,
    )


@router.get("/submissions")
async def list_my_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List my MiniApp submissions."""
    user_submissions = [s for s in _submissions if s["user_id"] == current_user["id"]]
    return {"submissions": user_submissions}
