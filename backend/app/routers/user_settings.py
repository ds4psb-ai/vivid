"""
User Teaching Settings API - Manages API keys and project data for Teaching Apps.
"""
from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.database import get_db
from app.models import UserTeachingSettings
from app.utils.encryption import encrypt_api_key, decrypt_api_key


router = APIRouter(prefix="/api/user", tags=["user-settings"])


class TeachingSettingsRequest(BaseModel):
    """Request body for updating teaching settings."""
    api_key: Optional[str] = Field(None, description="Gemini API key (will be encrypted)")
    prompt_data: Optional[dict] = Field(None, description="Veo Prompt Generator state")
    storyboard_data: Optional[dict] = Field(None, description="Storyboard folders/projects")
    image_tool_data: Optional[dict] = Field(None, description="Image Tool settings")
    shot_catch_data: Optional[dict] = Field(None, description="Shot Catch settings")
    language: Optional[str] = Field(None, description="Language preference (ko/en)")
    selected_model: Optional[str] = Field(None, description="Selected Gemini model")


class TeachingSettingsResponse(BaseModel):
    """Response body for teaching settings."""
    has_api_key: bool = Field(description="Whether API key is stored (key itself not returned)")
    api_key_preview: Optional[str] = Field(None, description="First 8 chars of API key for verification")
    prompt_data: dict = Field(default_factory=dict)
    storyboard_data: dict = Field(default_factory=dict)
    image_tool_data: dict = Field(default_factory=dict)
    shot_catch_data: dict = Field(default_factory=dict)
    language: str = "ko"
    selected_model: str = "gemini-3-flash-preview"


@router.get("/teaching-settings", response_model=TeachingSettingsResponse)
async def get_teaching_settings(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingSettingsResponse:
    """Get teaching app settings for the current user."""
    user_id = user.get("email") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    result = await db.execute(
        select(UserTeachingSettings).where(UserTeachingSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        return TeachingSettingsResponse(has_api_key=False)
    
    # Decrypt API key to get preview (first 8 chars only)
    api_key_preview = None
    if settings.encrypted_api_key:
        decrypted = decrypt_api_key(settings.encrypted_api_key)
        if decrypted and len(decrypted) >= 8:
            api_key_preview = decrypted[:8] + "..."
    
    return TeachingSettingsResponse(
        has_api_key=settings.encrypted_api_key is not None,
        api_key_preview=api_key_preview,
        prompt_data=settings.prompt_data or {},
        storyboard_data=settings.storyboard_data or {},
        image_tool_data=settings.image_tool_data or {},
        shot_catch_data=settings.shot_catch_data or {},
        language=settings.language or "ko",
        selected_model=settings.selected_model or "gemini-3-flash-preview",
    )


@router.put("/teaching-settings", response_model=TeachingSettingsResponse)
async def update_teaching_settings(
    request: TeachingSettingsRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingSettingsResponse:
    """Update teaching app settings for the current user."""
    user_id = user.get("email") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    result = await db.execute(
        select(UserTeachingSettings).where(UserTeachingSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserTeachingSettings(user_id=user_id)
        db.add(settings)
    
    # Update fields if provided
    if request.api_key is not None:
        if request.api_key == "":
            settings.encrypted_api_key = None
        else:
            settings.encrypted_api_key = encrypt_api_key(request.api_key)
    
    if request.prompt_data is not None:
        settings.prompt_data = request.prompt_data
    
    if request.storyboard_data is not None:
        settings.storyboard_data = request.storyboard_data
    
    if request.image_tool_data is not None:
        settings.image_tool_data = request.image_tool_data
    
    if request.shot_catch_data is not None:
        settings.shot_catch_data = request.shot_catch_data
    
    if request.language is not None:
        settings.language = request.language
    
    if request.selected_model is not None:
        settings.selected_model = request.selected_model
    
    await db.commit()
    await db.refresh(settings)
    
    # Decrypt API key for preview
    api_key_preview = None
    if settings.encrypted_api_key:
        decrypted = decrypt_api_key(settings.encrypted_api_key)
        if decrypted and len(decrypted) >= 8:
            api_key_preview = decrypted[:8] + "..."
    
    return TeachingSettingsResponse(
        has_api_key=settings.encrypted_api_key is not None,
        api_key_preview=api_key_preview,
        prompt_data=settings.prompt_data or {},
        storyboard_data=settings.storyboard_data or {},
        image_tool_data=settings.image_tool_data or {},
        shot_catch_data=settings.shot_catch_data or {},
        language=settings.language or "ko",
        selected_model=settings.selected_model or "gemini-3-flash-preview",
    )


@router.get("/teaching-settings/api-key")
async def get_api_key(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the full decrypted API key.
    Only use this endpoint for the iframe apps that need the actual key.
    """
    user_id = user.get("email") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    result = await db.execute(
        select(UserTeachingSettings).where(UserTeachingSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.encrypted_api_key:
        return {"api_key": None}
    
    decrypted = decrypt_api_key(settings.encrypted_api_key)
    return {"api_key": decrypted}
