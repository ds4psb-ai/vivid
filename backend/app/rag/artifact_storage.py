"""NotebookLM Studio Artifact Storage.

NotebookLM Studio 산출물 (Audio Overview, Infographic, Slide Deck 등)을 
GCS/S3에 저장하고 CDN을 통해 제공.

한 번 생성 → 무제한 제공 전략으로 API 쿼터 절감.

Usage:
    from app.rag.artifact_storage import get_artifact_storage
    
    storage = get_artifact_storage()
    
    # Audio Overview 저장/조회
    artifact = await storage.store_audio_overview(
        auteur_key="bong",
        audio_bytes=audio_data,
        focus_topic="시각적 스타일 분석",
    )
    
    # 캐시된 산출물 조회
    artifact = await storage.get_artifact(
        auteur_key="bong",
        artifact_type="audio",
        focus_topic="시각적 스타일",
    )
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Storage settings
ARTIFACTS_BASE_PATH = Path("/tmp/vivid_artifacts")  # Local fallback
GCS_BUCKET = settings.GCS_BUCKET  # crebit-rag-data

# TTL settings (days)
TTL_AUDIO = 90      # Audio overviews: 3 months
TTL_INFOGRAPHIC = 30  # Infographics: 1 month
TTL_SLIDE_DECK = 30   # Slide decks: 1 month
TTL_MIND_MAP = 90     # Mind maps: 3 months
TTL_REPORT = 30       # Reports: 1 month


# =============================================================================
# Enums & Data Classes
# =============================================================================

class ArtifactType(str, Enum):
    """Studio 산출물 유형."""
    AUDIO = "audio"
    INFOGRAPHIC = "infographic"
    SLIDE_DECK = "slide_deck"
    MIND_MAP = "mind_map"
    REPORT = "report"
    VIDEO = "video"


class ArtifactStatus(str, Enum):
    """산출물 상태."""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class StudioArtifact:
    """Studio 산출물 메타데이터."""
    artifact_id: str
    artifact_type: ArtifactType
    auteur_key: Optional[str]
    focus_topic: str  # 생성 시 사용한 프롬프트/주제
    status: ArtifactStatus
    
    # Storage
    storage_path: str  # GCS/S3 path or local path
    storage_url: Optional[str] = None  # Public URL if available
    file_size_bytes: int = 0
    mime_type: str = ""
    
    # Metadata
    notebook_id: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)
    generation_params: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_ready(self) -> bool:
        return self.status == ArtifactStatus.READY and not self.is_expired
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "auteur_key": self.auteur_key,
            "focus_topic": self.focus_topic,
            "status": self.status.value,
            "storage_url": self.storage_url,
            "file_size_bytes": self.file_size_bytes,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
        }


@dataclass
class ArtifactStats:
    """Storage 통계."""
    total_artifacts: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_auteur: Dict[str, int] = field(default_factory=dict)
    total_size_bytes: int = 0
    total_accesses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_artifacts": self.total_artifacts,
            "by_type": self.by_type,
            "by_auteur": self.by_auteur,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "total_accesses": self.total_accesses,
        }


# =============================================================================
# Artifact Storage Service
# =============================================================================

class ArtifactStorage:
    """NotebookLM Studio 산출물 저장 서비스.
    
    Features:
    - Local filesystem storage (fallback)
    - GCS integration (production)
    - Artifact caching and retrieval
    - Automatic expiration
    """
    
    def __init__(self, use_gcs: bool = True):
        self.use_gcs = use_gcs
        self._gcs_available = False
        self._gcs_client = None
        
        # L1 Cache (Memory)
        self._artifacts: Dict[str, StudioArtifact] = {}
        self._stats = ArtifactStats()
        
        # Ensure local storage directory exists
        ARTIFACTS_BASE_PATH.mkdir(parents=True, exist_ok=True)
    
    async def _ensure_gcs_initialized(self) -> bool:
        """Initialize GCS client if available."""
        if self._gcs_client is not None:
            return self._gcs_available
        
        if not self.use_gcs:
            return False
        
        try:
            from google.cloud import storage
            # GCS calls will fail if no auth is present
            self._gcs_client = storage.Client()
            self._gcs_available = True
            logger.info(f"[ArtifactStorage] GCS available: {GCS_BUCKET}")
            return True
        except Exception as e:
            logger.warning(f"[ArtifactStorage] GCS not available (fallback to local): {e}")
            self._gcs_available = False
            return False
    
    def _generate_artifact_id(
        self,
        artifact_type: ArtifactType,
        auteur_key: Optional[str],
        focus_topic: str,
    ) -> str:
        """Generate deterministic artifact ID for deduplication."""
        key_data = {
            "type": artifact_type.value,
            "auteur": auteur_key,
            "topic": focus_topic.strip().lower()[:200],
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _get_storage_path(
        self,
        artifact_type: ArtifactType,
        auteur_key: Optional[str],
        artifact_id: str,
        extension: str = "",
    ) -> str:
        """Generate storage path."""
        auteur_part = auteur_key or "general"
        date_str = datetime.now().strftime("%Y%m")
        
        return f"studio/{artifact_type.value}/{auteur_part}/{date_str}/{artifact_id}{extension}"
    
    def _get_ttl_days(self, artifact_type: ArtifactType) -> int:
        """Get TTL in days for artifact type."""
        ttl_map = {
            ArtifactType.AUDIO: TTL_AUDIO,
            ArtifactType.INFOGRAPHIC: TTL_INFOGRAPHIC,
            ArtifactType.SLIDE_DECK: TTL_SLIDE_DECK,
            ArtifactType.MIND_MAP: TTL_MIND_MAP,
            ArtifactType.REPORT: TTL_REPORT,
            ArtifactType.VIDEO: TTL_AUDIO,
        }
        return ttl_map.get(artifact_type, 30)
    
    def _get_mime_type(self, artifact_type: ArtifactType) -> str:
        """Get MIME type for artifact."""
        mime_map = {
            ArtifactType.AUDIO: "audio/wav",
            ArtifactType.INFOGRAPHIC: "image/png",
            ArtifactType.SLIDE_DECK: "application/pdf",
            ArtifactType.MIND_MAP: "application/json",
            ArtifactType.REPORT: "text/markdown",
            ArtifactType.VIDEO: "video/mp4",
        }
        return mime_map.get(artifact_type, "application/octet-stream")
    
    def _get_extension(self, artifact_type: ArtifactType) -> str:
        """Get file extension for artifact type."""
        ext_map = {
            ArtifactType.AUDIO: ".wav",
            ArtifactType.INFOGRAPHIC: ".png",
            ArtifactType.SLIDE_DECK: ".pdf",
            ArtifactType.MIND_MAP: ".json",
            ArtifactType.REPORT: ".md",
            ArtifactType.VIDEO: ".mp4",
        }
        return ext_map.get(artifact_type, "")
    
    async def get_artifact(
        self,
        auteur_key: Optional[str],
        artifact_type: ArtifactType,
        focus_topic: str,
    ) -> Optional[StudioArtifact]:
        """Get existing artifact if available.
        
        Checks Memory -> DB -> Return
        """
        artifact_id = self._generate_artifact_id(artifact_type, auteur_key, focus_topic)
        
        # 1. Memory Check
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            if artifact.is_expired:
                del self._artifacts[artifact_id]
                return None
            
            if artifact.is_ready:
                artifact.access_count += 1
                artifact.last_accessed_at = datetime.now()
                self._stats.total_accesses += 1
                logger.debug(f"[ArtifactStorage] MEM HIT: {artifact_id[:8]}...")
                return artifact
        
        # 2. DB Check
        try:
            from app.database import get_db_context
            from app.models import StudioArtifactModel
            from sqlalchemy import select, update
            
            async with get_db_context() as session:
                stmt = select(StudioArtifactModel).where(
                    StudioArtifactModel.id == artifact_id,
                    StudioArtifactModel.expires_at > datetime.now()
                )
                result = await session.execute(stmt)
                db_entry = result.scalar_one_or_none()
                
                if db_entry:
                    # Update access stats
                    await session.execute(
                        update(StudioArtifactModel)
                        .where(StudioArtifactModel.id == artifact_id)
                        .values(
                            access_count=StudioArtifactModel.access_count + 1,
                            last_accessed_at=datetime.now()
                        )
                    )
                    
                    # Convert to domain object
                    artifact = self._model_to_domain(db_entry)
                    if artifact.is_expired:
                         return None

                    # Hydrate memory
                    self._artifacts[artifact_id] = artifact
                    self._update_stats(artifact)
                    
                    logger.debug(f"[ArtifactStorage] DB HIT: {artifact_id[:8]}...")
                    return artifact
                    
        except Exception as e:
            logger.warning(f"[ArtifactStorage] DB Lookup failed: {e}")
            
        return None
    
    async def store_artifact(
        self,
        artifact_type: ArtifactType,
        data: bytes,
        auteur_key: Optional[str] = None,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        generation_params: Optional[Dict[str, Any]] = None,
    ) -> StudioArtifact:
        """Store a new artifact to Storage and Metadata DB."""
        artifact_id = self._generate_artifact_id(artifact_type, auteur_key, focus_topic)
        extension = self._get_extension(artifact_type)
        storage_path = self._get_storage_path(artifact_type, auteur_key, artifact_id, extension)
        
        # Check if already exists (Mem/DB) by calling get_artifact
        existing = await self.get_artifact(auteur_key, artifact_type, focus_topic)
        if existing and existing.is_ready:
            logger.info(f"[ArtifactStorage] Already exists: {artifact_id[:8]}...")
            return existing
        
        # Store to GCS or local
        storage_url = None
        await self._ensure_gcs_initialized()
        
        if self._gcs_available:
            try:
                bucket = self._gcs_client.bucket(GCS_BUCKET)
                blob = bucket.blob(storage_path)
                blob.upload_from_string(data, content_type=self._get_mime_type(artifact_type))
                storage_url = f"gs://{GCS_BUCKET}/{storage_path}"
                logger.info(f"[ArtifactStorage] Stored to GCS: {storage_path}")
            except Exception as e:
                logger.warning(f"[ArtifactStorage] GCS upload failed: {e}")
        
        # Local fallback
        if not storage_url:
            local_path = ARTIFACTS_BASE_PATH / storage_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
            storage_url = f"file://{local_path}"
            logger.info(f"[ArtifactStorage] Stored locally: {local_path}")
        
        # Calculate expiration
        ttl_days = self._get_ttl_days(artifact_type)
        expires_at = datetime.now() + timedelta(days=ttl_days)
        
        # Create artifact metadata domain object
        artifact = StudioArtifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            status=ArtifactStatus.READY,
            storage_path=storage_path,
            storage_url=storage_url,
            file_size_bytes=len(data),
            mime_type=self._get_mime_type(artifact_type),
            notebook_id=notebook_id,
            source_ids=source_ids or [],
            generation_params=generation_params or {},
            created_at=datetime.now(),
            expires_at=expires_at,
        )
        
        # Update Memory
        self._artifacts[artifact_id] = artifact
        self._update_stats(artifact)
        
        # Update DB
        try:
            from app.database import get_db_context
            from app.models import StudioArtifactModel
            from sqlalchemy.dialects.postgresql import insert
            
            async with get_db_context() as session:
                # Upsert to DB
                stmt = insert(StudioArtifactModel).values(
                    id=artifact.artifact_id,
                    artifact_type=artifact.artifact_type.value,
                    auteur_key=artifact.auteur_key,
                    focus_topic=artifact.focus_topic,
                    status=artifact.status.value,
                    storage_path=artifact.storage_path,
                    storage_url=artifact.storage_url,
                    file_size_bytes=artifact.file_size_bytes,
                    mime_type=artifact.mime_type,
                    notebook_id=artifact.notebook_id,
                    source_ids=artifact.source_ids,
                    generation_params=artifact.generation_params,
                    access_count=0,
                    expires_at=artifact.expires_at,
                    created_at=artifact.created_at,
                    updated_at=datetime.now()
                ).on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "storage_url": artifact.storage_url,
                        "updated_at": datetime.now(),
                        "expires_at": artifact.expires_at
                    }
                )
                await session.execute(stmt)
                logger.debug(f"[ArtifactStorage] Persisted: {artifact_id[:8]}")
        except Exception as e:
            logger.error(f"[ArtifactStorage] DB Write failed: {e}")
        
        return artifact
    
    async def store_audio_overview(
        self,
        auteur_key: str,
        audio_bytes: bytes,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
        format_code: int = 1,
        language: str = "ko",
    ) -> StudioArtifact:
        """Store Audio Overview artifact.
        
        NotebookLM Audio Overview를 저장.
        """
        return await self.store_artifact(
            artifact_type=ArtifactType.AUDIO,
            data=audio_bytes,
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            notebook_id=notebook_id,
            generation_params={
                "format_code": format_code,
                "language": language,
            },
        )
    
    async def store_infographic(
        self,
        auteur_key: str,
        image_bytes: bytes,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
        orientation_code: int = 1,
        detail_level_code: int = 2,
    ) -> StudioArtifact:
        """Store Infographic artifact.
        
        NotebookLM Infographic (PNG)를 저장.
        """
        return await self.store_artifact(
            artifact_type=ArtifactType.INFOGRAPHIC,
            data=image_bytes,
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            notebook_id=notebook_id,
            generation_params={
                "orientation_code": orientation_code,
                "detail_level_code": detail_level_code,
            },
        )
    
    async def store_slide_deck(
        self,
        auteur_key: str,
        pdf_bytes: bytes,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
        format_code: int = 1,
        length_code: int = 3,
    ) -> StudioArtifact:
        """Store Slide Deck artifact.
        
        NotebookLM Slide Deck (PDF)를 저장.
        """
        return await self.store_artifact(
            artifact_type=ArtifactType.SLIDE_DECK,
            data=pdf_bytes,
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            notebook_id=notebook_id,
            generation_params={
                "format_code": format_code,
                "length_code": length_code,
            },
        )
    
    async def store_mind_map(
        self,
        auteur_key: str,
        mind_map_json: str,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
    ) -> StudioArtifact:
        """Store Mind Map artifact.
        
        NotebookLM Mind Map (JSON)를 저장.
        """
        return await self.store_artifact(
            artifact_type=ArtifactType.MIND_MAP,
            data=mind_map_json.encode("utf-8"),
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            notebook_id=notebook_id,
        )
    
    async def store_report(
        self,
        auteur_key: str,
        report_markdown: str,
        focus_topic: str = "",
        notebook_id: Optional[str] = None,
        report_format: str = "Briefing Doc",
    ) -> StudioArtifact:
        """Store Report artifact.
        
        NotebookLM Report (Markdown)를 저장.
        """
        return await self.store_artifact(
            artifact_type=ArtifactType.REPORT,
            data=report_markdown.encode("utf-8"),
            auteur_key=auteur_key,
            focus_topic=focus_topic,
            notebook_id=notebook_id,
            generation_params={
                "report_format": report_format,
            },
        )
    
    async def download_artifact(self, artifact_id: str) -> Optional[bytes]:
        """Download artifact data."""
        # Check Memory
        artifact = self._artifacts.get(artifact_id)
        
        # If not in Memory, check DB and hydrate
        if not artifact:
             try:
                from app.database import get_db_context
                from app.models import StudioArtifactModel
                from sqlalchemy import select
                async with get_db_context() as session:
                    stmt = select(StudioArtifactModel).where(StudioArtifactModel.id == artifact_id)
                    result = await session.execute(stmt)
                    db_entry = result.scalar_one_or_none()
                    if db_entry:
                        artifact = self._model_to_domain(db_entry)
                        self._artifacts[artifact_id] = artifact
             except Exception as e:
                logger.warning(f"[ArtifactStorage] DL Metadata lookup failed: {e}")
                
        if not artifact or not artifact.is_ready:
            return None
        
        storage_url = artifact.storage_url
        
        # GCS
        if storage_url and storage_url.startswith("gs://"):
            await self._ensure_gcs_initialized()
            if self._gcs_available:
                try:
                    bucket = self._gcs_client.bucket(GCS_BUCKET)
                    blob = bucket.blob(artifact.storage_path)
                    return blob.download_as_bytes()
                except Exception as e:
                    logger.error(f"[ArtifactStorage] GCS download failed: {e}")
        
        # Local
        if storage_url and storage_url.startswith("file://"):
            local_path = Path(storage_url.replace("file://", ""))
            if local_path.exists():
                return local_path.read_bytes()
        
        return None
    
    def _model_to_domain(self, model: Any) -> StudioArtifact:
        """Convert DB model to Domain object."""
        return StudioArtifact(
            artifact_id=model.id,
            artifact_type=ArtifactType(model.artifact_type),
            auteur_key=model.auteur_key,
            focus_topic=model.focus_topic,
            status=ArtifactStatus(model.status),
            storage_path=model.storage_path,
            storage_url=model.storage_url,
            file_size_bytes=model.file_size_bytes,
            mime_type=model.mime_type,
            notebook_id=model.notebook_id,
            source_ids=model.source_ids,
            generation_params=model.generation_params,
            created_at=model.created_at,
            expires_at=model.expires_at,
            access_count=model.access_count,
            last_accessed_at=model.last_accessed_at,
        )
    
    def _update_stats(self, artifact: StudioArtifact) -> None:
        """Update storage statistics."""
        self._stats.total_artifacts = len(self._artifacts)
        self._stats.total_size_bytes += artifact.file_size_bytes
        
        # By type
        type_key = artifact.artifact_type.value
        self._stats.by_type[type_key] = self._stats.by_type.get(type_key, 0) + 1
        
        # By auteur
        if artifact.auteur_key:
            self._stats.by_auteur[artifact.auteur_key] = (
                self._stats.by_auteur.get(artifact.auteur_key, 0) + 1
            )
    
    def list_artifacts(
        self,
        auteur_key: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        limit: int = 50,
    ) -> List[StudioArtifact]:
        """List artifacts with optional filters."""
        artifacts = list(self._artifacts.values())
        
        if auteur_key:
            artifacts = [a for a in artifacts if a.auteur_key == auteur_key]
        if artifact_type:
            artifacts = [a for a in artifacts if a.artifact_type == artifact_type]
        
        # Sort by created_at descending
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        
        return artifacts[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self._stats.to_dict()
    
    def cleanup_expired(self) -> int:
        """Remove expired artifacts.
        
        Returns:
            Number of artifacts removed
        """
        expired_ids = [
            aid for aid, artifact in self._artifacts.items()
            if artifact.is_expired
        ]
        
        for aid in expired_ids:
            del self._artifacts[aid]
        
        logger.info(f"[ArtifactStorage] Cleaned up {len(expired_ids)} expired artifacts")
        return len(expired_ids)


# =============================================================================
# Singleton
# =============================================================================

_artifact_storage: Optional[ArtifactStorage] = None


def get_artifact_storage() -> ArtifactStorage:
    """Get artifact storage singleton."""
    global _artifact_storage
    if _artifact_storage is None:
        _artifact_storage = ArtifactStorage()
    return _artifact_storage


def reset_artifact_storage() -> None:
    """Reset storage singleton (for testing)."""
    global _artifact_storage
    _artifact_storage = None
