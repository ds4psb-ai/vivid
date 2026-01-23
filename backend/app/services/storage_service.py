"""Storage Service - GCS/Local Storage Integration.

2026 Best Practices:
- Async upload/download with streaming
- Support for both GCS (production) and local (development)
- Content-addressable storage for deduplication
- Signed URL generation for secure access

Usage:
    from app.services.storage_service import get_storage_service

    service = get_storage_service()
    url = await service.upload_image(image_data, "characters/user123/char456/image.jpg")
"""

import hashlib
import logging
import os
import re
import threading
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

import aiofiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# =============================================================================
# Security Constants
# =============================================================================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max upload size
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB max image size
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB max video size
SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')  # Safe path characters

# =============================================================================
# Configuration
# =============================================================================

class StorageConfig(BaseModel):
    """Storage configuration."""

    # GCS settings
    gcs_bucket: str = os.getenv("GCS_BUCKET", "crebit-studio-media")
    gcs_project: str = os.getenv("GCS_PROJECT", "crebit-studio")

    # Local storage settings (development fallback)
    local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "/tmp/crebit-storage")
    local_base_url: str = os.getenv("LOCAL_STORAGE_URL", "http://localhost:8100/static/uploads")

    # Use GCS in production
    use_gcs: bool = os.getenv("USE_GCS", "false").lower() == "true"

    # Public URL prefix for GCS
    gcs_public_url: str = "https://storage.googleapis.com"


# =============================================================================
# Storage Interface
# =============================================================================

class StorageBackend(ABC):
    """Abstract storage backend."""

    @abstractmethod
    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload data and return public URL."""
        pass

    @abstractmethod
    async def download(self, path: str) -> Optional[bytes]:
        """Download data by path."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete data by path."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if path exists."""
        pass

    @abstractmethod
    async def get_signed_url(
        self,
        path: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Get signed URL for temporary access."""
        pass


# =============================================================================
# Local Storage Backend (Development)
# =============================================================================

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage for development."""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.base_path = Path(config.local_storage_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path to prevent traversal attacks.

        Args:
            path: Relative path within storage

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path is invalid or attempts traversal
        """
        # Check for dangerous patterns
        if '..' in path or path.startswith('/'):
            raise ValueError(f"Invalid path: {path}")

        # Only allow safe characters
        if not SAFE_PATH_PATTERN.match(path):
            raise ValueError(f"Path contains invalid characters: {path}")

        # Resolve and verify within base_path
        full_path = (self.base_path / path).resolve()
        try:
            full_path.relative_to(self.base_path)
        except ValueError:
            raise ValueError(f"Path traversal detected: {path}")

        return full_path

    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload to local filesystem."""
        # Validate path
        full_path = self._validate_path(path)

        # Check size limit
        if len(data) > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(data)} bytes (max {MAX_FILE_SIZE})")

        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(data)
        except OSError as e:
            # Clean up partial file on failure
            if full_path.exists():
                full_path.unlink()
            raise RuntimeError(f"Storage write failed: {e}")

        logger.info(f"[STORAGE] Uploaded {len(data)} bytes to {full_path}")
        return f"{self.config.local_base_url}/{path}"

    async def download(self, path: str) -> Optional[bytes]:
        """Download from local filesystem."""
        full_path = self._validate_path(path)
        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """Delete from local filesystem."""
        full_path = self._validate_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        """Check if file exists locally."""
        try:
            full_path = self._validate_path(path)
            return full_path.exists()
        except ValueError:
            return False

    async def get_signed_url(
        self,
        path: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Return local URL (no signing for local storage)."""
        return f"{self.config.local_base_url}/{path}"


# =============================================================================
# GCS Storage Backend (Production)
# =============================================================================

class GCSStorageBackend(StorageBackend):
    """Google Cloud Storage backend for production."""

    def __init__(self, config: StorageConfig):
        self.config = config
        self._client = None
        self._bucket = None

    def _validate_path(self, path: str) -> str:
        """Validate GCS path to prevent injection.

        Args:
            path: Object path within bucket

        Returns:
            Validated path

        Raises:
            ValueError: If path is invalid
        """
        if '..' in path or path.startswith('/'):
            raise ValueError(f"Invalid path: {path}")

        if not SAFE_PATH_PATTERN.match(path):
            raise ValueError(f"Path contains invalid characters: {path}")

        return path

    @property
    def client(self):
        """Lazy-load GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=self.config.gcs_project)
                logger.info(f"[STORAGE] GCS client initialized for project {self.config.gcs_project}")
            except ImportError:
                raise RuntimeError(
                    "google-cloud-storage not installed. "
                    "Install with: pip install google-cloud-storage"
                )
            except Exception as e:
                logger.error(f"[STORAGE] Failed to initialize GCS client: {e}")
                raise
        return self._client

    @property
    def bucket(self):
        """Get bucket instance."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.config.gcs_bucket)
        return self._bucket

    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload to GCS with retry."""
        import asyncio

        # Validate path and size
        path = self._validate_path(path)
        if len(data) > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(data)} bytes (max {MAX_FILE_SIZE})")

        def _upload():
            blob = self.bucket.blob(path)
            # Retry transient errors (network issues, etc.)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    blob.upload_from_string(data, content_type=content_type)
                    return blob.public_url
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"[STORAGE] GCS upload attempt {attempt + 1} failed: {e}")
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
            return blob.public_url

        url = await asyncio.get_event_loop().run_in_executor(None, _upload)
        logger.info(f"[STORAGE] Uploaded {len(data)} bytes to GCS: {path}")
        return url

    async def download(self, path: str) -> Optional[bytes]:
        """Download from GCS."""
        import asyncio

        path = self._validate_path(path)

        def _download():
            from google.api_core.exceptions import NotFound
            try:
                blob = self.bucket.blob(path)
                return blob.download_as_bytes()
            except NotFound:
                return None

        return await asyncio.get_event_loop().run_in_executor(None, _download)

    async def delete(self, path: str) -> bool:
        """Delete from GCS."""
        import asyncio

        def _delete():
            blob = self.bucket.blob(path)
            if blob.exists():
                blob.delete()
                return True
            return False

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def exists(self, path: str) -> bool:
        """Check if blob exists in GCS."""
        import asyncio

        def _exists():
            return self.bucket.blob(path).exists()

        return await asyncio.get_event_loop().run_in_executor(None, _exists)

    async def get_signed_url(
        self,
        path: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate signed URL for temporary access."""
        import asyncio
        from datetime import timedelta

        def _sign():
            blob = self.bucket.blob(path)
            return blob.generate_signed_url(
                expiration=timedelta(seconds=expiration_seconds),
                method="GET",
            )

        return await asyncio.get_event_loop().run_in_executor(None, _sign)


# =============================================================================
# Storage Service (High-level API)
# =============================================================================

class StorageService:
    """High-level storage service with content-addressable uploads."""

    def __init__(self, backend: StorageBackend):
        self.backend = backend

    def _content_hash(self, data: bytes) -> str:
        """Generate content hash for deduplication."""
        return hashlib.sha256(data).hexdigest()[:16]

    async def upload_image(
        self,
        image_data: bytes,
        path: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload image with content-type detection and validation.

        Args:
            image_data: Image bytes
            path: Storage path (e.g., "characters/user123/char456/image.jpg")
            content_type: MIME type (default: image/jpeg)

        Returns:
            Public URL of uploaded image

        Raises:
            ValueError: If image is too large or invalid
        """
        # Check size limit
        if len(image_data) > MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large: {len(image_data)} bytes (max {MAX_IMAGE_SIZE})")

        # Validate magic bytes - must be a known image format
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            content_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            content_type = "image/jpeg"
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            content_type = "image/gif"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            content_type = "image/webp"
        else:
            raise ValueError("Invalid image format: unknown magic bytes")

        return await self.backend.upload(image_data, path, content_type)

    async def upload_video(
        self,
        video_data: bytes,
        path: str,
        content_type: str = "video/mp4",
    ) -> str:
        """Upload video with content-type detection."""
        # Auto-detect common video formats
        if video_data[4:8] == b'ftyp':
            content_type = "video/mp4"
        elif video_data[:4] == b'\x1a\x45\xdf\xa3':
            content_type = "video/webm"

        return await self.backend.upload(video_data, path, content_type)

    async def upload_audio(
        self,
        audio_data: bytes,
        path: str,
        content_type: str = "audio/mpeg",
    ) -> str:
        """Upload audio with content-type detection."""
        # Auto-detect audio formats
        if audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
            content_type = "audio/mpeg"
        elif audio_data[:4] == b'fLaC':
            content_type = "audio/flac"
        elif audio_data[:4] == b'RIFF':
            content_type = "audio/wav"

        return await self.backend.upload(audio_data, path, content_type)

    async def upload_with_hash(
        self,
        data: bytes,
        prefix: str,
        extension: str = ".bin",
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload with content-addressable naming.

        Generates a deterministic filename from content hash for deduplication.

        Args:
            data: File data
            prefix: Path prefix (e.g., "characters/user123")
            extension: File extension (e.g., ".jpg")
            content_type: MIME type

        Returns:
            Public URL
        """
        content_hash = self._content_hash(data)
        path = f"{prefix}/{content_hash}{extension}"
        return await self.backend.upload(data, path, content_type)

    async def download(self, path: str) -> Optional[bytes]:
        """Download file by path."""
        return await self.backend.download(path)

    async def delete(self, path: str) -> bool:
        """Delete file by path."""
        return await self.backend.delete(path)

    async def get_signed_url(
        self,
        path: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Get signed URL for temporary access."""
        return await self.backend.get_signed_url(path, expiration_seconds)


# =============================================================================
# Singleton Instance (Thread-safe)
# =============================================================================

_service: Optional[StorageService] = None
_config: Optional[StorageConfig] = None
_lock = threading.Lock()


def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    global _config
    if _config is None:
        with _lock:
            if _config is None:  # Double-check locking
                _config = StorageConfig()
    return _config


def get_storage_service() -> StorageService:
    """Get or create StorageService instance (thread-safe).

    Returns:
        StorageService with appropriate backend (GCS or local)
    """
    global _service

    if _service is None:
        with _lock:
            if _service is None:  # Double-check locking
                config = get_storage_config()

                if config.use_gcs:
                    backend = GCSStorageBackend(config)
                    logger.info("[STORAGE] Using GCS storage backend")
                else:
                    backend = LocalStorageBackend(config)
                    logger.info("[STORAGE] Using local storage backend")

                _service = StorageService(backend)

    return _service


def reset_storage_service():
    """Reset singleton for testing."""
    global _service, _config
    with _lock:
        _service = None
        _config = None
