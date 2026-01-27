"""OCEAN (Big Five) 점수 영구 저장 서비스.

Mirror 앱에서 계산된 Big Five (OCEAN) 성격 점수를 UserPreferenceProfile에 저장.

Usage:
    from app.services.ocean_storage_service import (
        get_ocean_storage_service,
        OceanScores,
    )

    service = get_ocean_storage_service()

    # Save OCEAN scores
    result = await service.save_ocean(
        user_id="user123",
        ocean=OceanScores(
            openness=0.75,
            conscientiousness=0.60,
            extraversion=0.40,
            agreeableness=0.65,
            neuroticism=0.45,
        ),
        source="mirror",
    )

    # Get OCEAN scores
    scores = await service.get_ocean(user_id="user123")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.models_personalization import UserPreferenceProfile

logger = logging.getLogger(__name__)


@dataclass
class OceanScores:
    """OCEAN (Big Five) 점수 데이터.

    Attributes:
        openness: 개방성 (0.0-1.0)
        conscientiousness: 성실성 (0.0-1.0)
        extraversion: 외향성 (0.0-1.0)
        agreeableness: 우호성 (0.0-1.0)
        neuroticism: 신경성 (0.0-1.0)
    """
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    def __post_init__(self):
        """Validate and clamp values to 0.0-1.0 range."""
        self.openness = max(0.0, min(1.0, self.openness))
        self.conscientiousness = max(0.0, min(1.0, self.conscientiousness))
        self.extraversion = max(0.0, min(1.0, self.extraversion))
        self.agreeableness = max(0.0, min(1.0, self.agreeableness))
        self.neuroticism = max(0.0, min(1.0, self.neuroticism))

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "OceanScores":
        """Create from dictionary."""
        return cls(
            openness=data.get("openness", 0.5),
            conscientiousness=data.get("conscientiousness", 0.5),
            extraversion=data.get("extraversion", 0.5),
            agreeableness=data.get("agreeableness", 0.5),
            neuroticism=data.get("neuroticism", 0.5),
        )


@dataclass
class OceanSaveResult:
    """OCEAN 저장 결과.

    Attributes:
        success: 저장 성공 여부
        user_id: 사용자 ID
        updated_at: 업데이트 시각 (성공 시)
        previous_values: 이전 OCEAN 값 (업데이트 시)
        new_values: 새 OCEAN 값
        error: 에러 메시지 (실패 시)
        created_new_profile: 신규 프로필 생성 여부
    """
    success: bool
    user_id: str
    updated_at: Optional[datetime] = None
    previous_values: Optional[Dict[str, float]] = None
    new_values: Optional[Dict[str, float]] = None
    error: Optional[str] = None
    created_new_profile: bool = False


class OceanStorageService:
    """OCEAN 점수를 UserPreferenceProfile에 저장하는 서비스.

    Mirror 앱에서 MBTI→OCEAN 변환 후 DB에 영구 저장.
    """

    async def save_ocean(
        self,
        user_id: str,
        ocean: OceanScores,
        source: str = "mirror",
    ) -> OceanSaveResult:
        """OCEAN 점수를 DB에 저장.

        Args:
            user_id: 사용자 ID
            ocean: OCEAN 점수
            source: 점수 출처 (mirror, inference, manual)

        Returns:
            OceanSaveResult with success status and values
        """
        if not user_id or not user_id.strip():
            return OceanSaveResult(
                success=False,
                user_id=user_id or "",
                error="Invalid user_id: empty or None",
            )

        user_id = user_id.strip()

        try:
            async with get_db_context() as db:
                profile, created = await self._get_or_create_profile(db, user_id)

                # 이전 값 백업
                previous = {
                    "openness": profile.openness,
                    "conscientiousness": profile.conscientiousness,
                    "extraversion": profile.extraversion,
                    "agreeableness": profile.agreeableness,
                    "neuroticism": profile.neuroticism,
                }

                # OCEAN 업데이트
                profile.openness = ocean.openness
                profile.conscientiousness = ocean.conscientiousness
                profile.extraversion = ocean.extraversion
                profile.agreeableness = ocean.agreeableness
                profile.neuroticism = ocean.neuroticism
                profile.last_ocean_update = datetime.utcnow()

                await db.commit()

                new_values = ocean.to_dict()

                logger.info(
                    f"[OCEAN_SAVE] user={user_id} source={source} "
                    f"values={new_values} created_new={created}"
                )

                return OceanSaveResult(
                    success=True,
                    user_id=user_id,
                    updated_at=profile.last_ocean_update,
                    previous_values=previous,
                    new_values=new_values,
                    created_new_profile=created,
                )

        except Exception as e:
            logger.error(f"[OCEAN_SAVE_ERROR] user={user_id} error={e}")
            return OceanSaveResult(
                success=False,
                user_id=user_id,
                error=str(e),
            )

    async def get_ocean(self, user_id: str) -> Optional[OceanScores]:
        """사용자의 OCEAN 점수 조회.

        Args:
            user_id: 사용자 ID

        Returns:
            OceanScores if found, None if user has no profile
        """
        if not user_id or not user_id.strip():
            return None

        user_id = user_id.strip()

        try:
            async with get_db_context() as db:
                profile = await self._get_profile(db, user_id)
                if not profile:
                    return None

                return OceanScores(
                    openness=profile.openness if profile.openness is not None else 0.5,
                    conscientiousness=profile.conscientiousness if profile.conscientiousness is not None else 0.5,
                    extraversion=profile.extraversion if profile.extraversion is not None else 0.5,
                    agreeableness=profile.agreeableness if profile.agreeableness is not None else 0.5,
                    neuroticism=profile.neuroticism if profile.neuroticism is not None else 0.5,
                )
        except Exception as e:
            logger.error(f"[OCEAN_GET_ERROR] user={user_id} error={e}")
            return None

    async def has_ocean_data(self, user_id: str) -> bool:
        """사용자가 OCEAN 데이터를 가지고 있는지 확인.

        Args:
            user_id: 사용자 ID

        Returns:
            True if user has OCEAN data (last_ocean_update is not None)
        """
        if not user_id or not user_id.strip():
            return False

        user_id = user_id.strip()

        try:
            async with get_db_context() as db:
                profile = await self._get_profile(db, user_id)
                if not profile:
                    return False
                return profile.last_ocean_update is not None
        except Exception as e:
            logger.error(f"[OCEAN_HAS_DATA_ERROR] user={user_id} error={e}")
            return False

    async def _get_or_create_profile(
        self, db: AsyncSession, user_id: str
    ) -> tuple[UserPreferenceProfile, bool]:
        """프로필 조회 또는 생성.

        Returns:
            Tuple of (profile, created) where created is True if new profile
        """
        profile = await self._get_profile(db, user_id)
        if profile:
            return profile, False

        # 신규 생성
        profile = UserPreferenceProfile(user_id=user_id)
        db.add(profile)
        await db.flush()
        return profile, True

    async def _get_profile(
        self, db: AsyncSession, user_id: str
    ) -> Optional[UserPreferenceProfile]:
        """프로필 조회."""
        stmt = select(UserPreferenceProfile).where(
            UserPreferenceProfile.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# 싱글톤 인스턴스
_ocean_storage_service: Optional[OceanStorageService] = None


def get_ocean_storage_service() -> OceanStorageService:
    """OceanStorageService 싱글톤 반환."""
    global _ocean_storage_service
    if _ocean_storage_service is None:
        _ocean_storage_service = OceanStorageService()
    return _ocean_storage_service


# For testing: reset singleton
def _reset_ocean_storage_service() -> None:
    """Reset singleton for testing purposes."""
    global _ocean_storage_service
    _ocean_storage_service = None
