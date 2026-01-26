"""Podcast Generation Service using Google Discovery Engine API.

Google Cloud Podcast API를 사용한 AI 팟캐스트 생성.

Endpoint: discoveryengine.googleapis.com
IAM Role: roles/discoveryengine.podcastApiUser

Supported formats:
- deep_dive: 심층 분석 (default, ~10min)
- brief: 요약 (~5min)
- debate: 토론 형식
- critique: 비평 형식
- lecture: 강의 형식 (단일 진행자, ~30min)

Usage:
    from app.rag.podcast_service import get_podcast_service, PodcastLength

    service = get_podcast_service()

    # 팟캐스트 생성
    result = await service.generate_podcast(
        sources=[{"text": "강주노 감독의 영화적 특징..."}],
        title="거장 분석",
        length=PodcastLength.STANDARD,
        language="ko",
    )

    # 다운로드
    audio_bytes = await service.download_podcast(result.operation_name)
"""
from __future__ import annotations

import asyncio
import base64
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

PODCAST_API_ENDPOINT = "https://discoveryengine.googleapis.com/v1"
PODCAST_GENERATION_TIMEOUT = 600  # 10 minutes max for generation
PODCAST_POLL_INTERVAL = 10  # seconds between status checks
PODCAST_DOWNLOAD_TIMEOUT = 300  # 5 minutes for download
HTTP_REQUEST_TIMEOUT = 60  # Default HTTP request timeout
MAX_CONTEXT_TOKENS = 100000

# Retry settings
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 10.0

# Validation limits
MAX_SOURCES_COUNT = 50  # Maximum number of sources
MAX_SOURCE_LENGTH = 100000  # Maximum length per source (chars)
MAX_TITLE_LENGTH = 500  # Maximum title length
MIN_SOURCE_LENGTH = 10  # Minimum source length

# Thread safety
_singleton_lock = threading.RLock()


# ============================================================================
# Enums
# ============================================================================

class PodcastLength(str, Enum):
    """팟캐스트 길이."""
    SHORT = "SHORT"  # 4-5 minutes
    STANDARD = "STANDARD"  # ~10 minutes


class PodcastFormat(str, Enum):
    """팟캐스트 형식."""
    DEEP_DIVE = "deep_dive"  # 심층 분석
    BRIEF = "brief"  # 요약
    DEBATE = "debate"  # 토론
    CRITIQUE = "critique"  # 비평
    LECTURE = "lecture"  # 강의 (단일 진행자)


class PodcastStatus(str, Enum):
    """팟캐스트 생성 상태."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Input Validation
# ============================================================================

def validate_sources(sources: List[Any]) -> None:
    """Validate podcast sources.

    Args:
        sources: List of source contents

    Raises:
        ValueError: If sources are invalid
    """
    if not sources:
        raise ValueError("At least one source required")
    if len(sources) > MAX_SOURCES_COUNT:
        raise ValueError(f"Too many sources: {len(sources)} > {MAX_SOURCES_COUNT}")

    for i, src in enumerate(sources):
        if isinstance(src, str):
            if len(src) < MIN_SOURCE_LENGTH:
                raise ValueError(f"Source {i} too short: {len(src)} < {MIN_SOURCE_LENGTH}")
            if len(src) > MAX_SOURCE_LENGTH:
                raise ValueError(f"Source {i} too long: {len(src)} > {MAX_SOURCE_LENGTH}")
        elif isinstance(src, dict):
            text = src.get("text", "")
            if text and len(text) > MAX_SOURCE_LENGTH:
                raise ValueError(f"Source {i} too long: {len(text)} > {MAX_SOURCE_LENGTH}")
        elif hasattr(src, "content"):
            if len(src.content) > MAX_SOURCE_LENGTH:
                raise ValueError(f"Source {i} too long: {len(src.content)} > {MAX_SOURCE_LENGTH}")


def validate_title(title: str) -> None:
    """Validate podcast title.

    Args:
        title: Podcast title

    Raises:
        ValueError: If title is invalid
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title too long: {len(title)} > {MAX_TITLE_LENGTH}")
    if "\x00" in title:
        raise ValueError("Title contains invalid null bytes")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PodcastConfig:
    """팟캐스트 설정."""
    project_id: str = field(default_factory=lambda: settings.GCP_PROJECT_ID)
    location: str = "global"
    default_language: str = "ko"
    default_length: PodcastLength = PodcastLength.STANDARD


@dataclass
class PodcastSource:
    """팟캐스트 소스 콘텐츠."""
    content: str
    media_type: str = "text"  # text, blob
    mime_type: Optional[str] = None  # for blob: audio/mp3, video/mp4, image/png


@dataclass
class PodcastRequest:
    """팟캐스트 생성 요청."""
    title: str
    sources: List[PodcastSource]
    description: str = ""
    focus: str = ""  # Custom prompt for podcast direction
    length: PodcastLength = PodcastLength.STANDARD
    language: str = "ko"
    format: PodcastFormat = PodcastFormat.DEEP_DIVE


@dataclass
class PodcastResult:
    """팟캐스트 생성 결과."""
    operation_name: str
    status: PodcastStatus
    title: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audio_url: Optional[str] = None
    duration_seconds: int = 0
    error_message: Optional[str] = None


# ============================================================================
# Podcast Service
# ============================================================================

class PodcastService:
    """Google Discovery Engine Podcast API 서비스.

    Thread-safe singleton with async HTTP client and retry logic.
    """

    def __init__(self, config: Optional[PodcastConfig] = None):
        """Initialize service.

        Args:
            config: Podcast 설정 (None이면 기본값)
        """
        self.config = config or PodcastConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = threading.RLock()
        self._token_lock = threading.RLock()
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client (thread-safe)."""
        if self._client is not None and not self._client.is_closed:
            return self._client

        with self._client_lock:
            # Double-check pattern
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=HTTP_REQUEST_TIMEOUT,
                    limits=httpx.Limits(
                        max_keepalive_connections=5,
                        max_connections=10,
                    ),
                )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """HTTP request with exponential backoff retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        client = await self._get_client()
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.request(method, url, **kwargs)
                # Retry on 5xx errors
                if response.status_code >= 500 and attempt < MAX_RETRIES:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                return response
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(
                        f"[Podcast] Retry {attempt + 1}/{MAX_RETRIES} for {method} {url}: "
                        f"{type(e).__name__}: {e}. Waiting {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[Podcast] All {MAX_RETRIES} retries exhausted for {method} {url}"
                    )
            except Exception as e:
                # Non-retryable error
                logger.error(f"[Podcast] Non-retryable error: {e}")
                raise

        if last_error:
            raise last_error
        raise RuntimeError("Request failed with unknown error")

    async def _get_access_token(self) -> str:
        """Get GCP access token using ADC (thread-safe with caching).

        Returns:
            Access token string

        Raises:
            RuntimeError: If token acquisition fails
        """
        from datetime import timedelta

        # Fast path: token is still valid (with 5 minute buffer)
        with self._token_lock:
            if (
                self._access_token
                and self._token_expiry
                and datetime.now(timezone.utc) < self._token_expiry
            ):
                return self._access_token

        # Slow path: need to refresh token
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                # Use gcloud to get access token
                proc = await asyncio.create_subprocess_exec(
                    "gcloud", "auth", "print-access-token",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    error_msg = stderr.decode().strip()
                    raise RuntimeError(f"gcloud auth failed: {error_msg}")

                token = stdout.decode().strip()
                if not token:
                    raise RuntimeError("Empty access token received")

                with self._token_lock:
                    self._access_token = token
                    # Token typically valid for 1 hour, set expiry to 55 minutes
                    self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=55)
                    return self._access_token

            except FileNotFoundError:
                logger.error("[Podcast] gcloud CLI not found")
                raise RuntimeError("gcloud CLI not installed or not in PATH")
            except RuntimeError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"[Podcast] Token retry {attempt + 1}/{MAX_RETRIES}: {e}")
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.exception("[Podcast] Failed to get access token")
                raise

        raise last_error or RuntimeError("Failed to get access token")

    def _build_focus_prompt(self, format: PodcastFormat, custom_focus: str = "") -> str:
        """Build focus prompt based on format.

        Args:
            format: Podcast format
            custom_focus: Custom focus instructions

        Returns:
            Focus prompt string
        """
        format_prompts = {
            PodcastFormat.DEEP_DIVE: "심층적으로 분석하고 인사이트를 제공해주세요. 배경, 맥락, 세부사항을 깊이있게 다뤄주세요.",
            PodcastFormat.BRIEF: "핵심 내용만 간결하게 요약해주세요. 주요 포인트 위주로 빠르게 전달해주세요.",
            PodcastFormat.DEBATE: "두 진행자가 서로 다른 관점에서 토론하는 형식으로 진행해주세요. 찬반 의견을 균형있게 다뤄주세요.",
            PodcastFormat.CRITIQUE: "비평적 시각으로 장단점을 분석해주세요. 개선점과 대안도 제시해주세요.",
            PodcastFormat.LECTURE: "교육적인 강의 형식으로 체계적으로 설명해주세요. 예시와 함께 이해하기 쉽게 전달해주세요.",
        }

        base_prompt = format_prompts.get(format, format_prompts[PodcastFormat.DEEP_DIVE])

        if custom_focus:
            return f"{base_prompt}\n\n추가 지시사항: {custom_focus}"
        return base_prompt

    async def generate_podcast(
        self,
        sources: List[Union[PodcastSource, Dict[str, str], str]],
        title: str,
        description: str = "",
        focus: str = "",
        length: PodcastLength = PodcastLength.STANDARD,
        language: str = "ko",
        format: PodcastFormat = PodcastFormat.DEEP_DIVE,
    ) -> PodcastResult:
        """팟캐스트 생성 요청 (with validation and retry).

        Args:
            sources: 소스 콘텐츠 목록 (텍스트 또는 PodcastSource)
            title: 팟캐스트 제목
            description: 설명
            focus: 커스텀 포커스 프롬프트
            length: 길이 (SHORT, STANDARD)
            language: BCP47 언어 코드
            format: 팟캐스트 형식

        Returns:
            PodcastResult with operation_name for status tracking

        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        validate_sources(sources)
        validate_title(title)

        # Validate language code (basic BCP47 check)
        if not language or len(language) < 2:
            raise ValueError("Invalid language code")

        # Normalize sources
        normalized_sources = []
        for src in sources:
            if isinstance(src, str):
                normalized_sources.append({"text": src})
            elif isinstance(src, PodcastSource):
                if src.media_type == "text":
                    normalized_sources.append({"text": src.content})
                else:
                    # Blob source
                    content = src.content
                    if isinstance(content, str):
                        content = content.encode()
                    normalized_sources.append({
                        "blob": {
                            "mimeType": src.mime_type or "application/octet-stream",
                            "data": base64.b64encode(content).decode(),
                        }
                    })
            elif isinstance(src, dict):
                normalized_sources.append(src)

        # Build request body
        focus_prompt = self._build_focus_prompt(format, focus)

        request_body = {
            "podcastConfig": {
                "focus": focus_prompt,
                "length": length.value,
                "languageCode": language,
            },
            "contexts": normalized_sources,
            "title": title,
            "description": description or f"{format.value} 형식 팟캐스트",
        }

        try:
            token = await self._get_access_token()
            url = f"{PODCAST_API_ENDPOINT}/projects/{self.config.project_id}/locations/{self.config.location}/podcasts"

            logger.info(f"[Podcast] Generating podcast: {title} ({format.value}, {length.value})")

            response = await self._request_with_retry(
                "POST",
                url,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text[:500]}"
                logger.error(f"[Podcast] {error_msg}")
                return PodcastResult(
                    operation_name="",
                    status=PodcastStatus.FAILED,
                    title=title,
                    error_message=error_msg,
                )

            result = response.json()
            operation_name = result.get("name", "")

            if not operation_name:
                logger.warning("[Podcast] No operation_name in response")
                return PodcastResult(
                    operation_name="",
                    status=PodcastStatus.FAILED,
                    title=title,
                    error_message="No operation name returned from API",
                )

            logger.info(f"[Podcast] Generation started: {operation_name}")

            return PodcastResult(
                operation_name=operation_name,
                status=PodcastStatus.PROCESSING,
                title=title,
            )

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.exception(f"[Podcast] Failed to generate podcast: {e}")
            return PodcastResult(
                operation_name="",
                status=PodcastStatus.FAILED,
                title=title,
                error_message=str(e),
            )

    async def check_status(self, operation_name: str) -> PodcastResult:
        """팟캐스트 생성 상태 확인 (with validation and retry).

        Args:
            operation_name: Operation name from generate_podcast

        Returns:
            PodcastResult with current status
        """
        # Input validation
        if not operation_name or not operation_name.strip():
            return PodcastResult(
                operation_name="",
                status=PodcastStatus.FAILED,
                title="",
                error_message="No operation name provided",
            )

        if len(operation_name) < 10:
            return PodcastResult(
                operation_name=operation_name,
                status=PodcastStatus.FAILED,
                title="",
                error_message="Invalid operation name format",
            )

        try:
            token = await self._get_access_token()
            url = f"{PODCAST_API_ENDPOINT}/{operation_name}"

            response = await self._request_with_retry(
                "GET",
                url,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                return PodcastResult(
                    operation_name=operation_name,
                    status=PodcastStatus.FAILED,
                    title="",
                    error_message=f"Status check failed: {response.status_code}",
                )

            result = response.json()
            done = result.get("done", False)

            if done:
                if "error" in result:
                    error_info = result["error"]
                    return PodcastResult(
                        operation_name=operation_name,
                        status=PodcastStatus.FAILED,
                        title="",
                        error_message=error_info.get("message", "Unknown error"),
                    )
                response_data = result.get("response", {})
                return PodcastResult(
                    operation_name=operation_name,
                    status=PodcastStatus.COMPLETED,
                    title=response_data.get("title", ""),
                    duration_seconds=response_data.get("durationSeconds", 0),
                    audio_url=response_data.get("audioUri"),
                )
            else:
                # Still processing
                metadata = result.get("metadata", {})
                return PodcastResult(
                    operation_name=operation_name,
                    status=PodcastStatus.PROCESSING,
                    title=metadata.get("title", ""),
                )

        except Exception as e:
            logger.exception(f"[Podcast] Status check failed: {e}")
            return PodcastResult(
                operation_name=operation_name,
                status=PodcastStatus.FAILED,
                title="",
                error_message=str(e),
            )

    async def wait_for_completion(
        self,
        operation_name: str,
        timeout: int = PODCAST_GENERATION_TIMEOUT,
        poll_interval: int = PODCAST_POLL_INTERVAL,
    ) -> PodcastResult:
        """팟캐스트 생성 완료 대기.

        Args:
            operation_name: Operation name from generate_podcast
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between status checks

        Returns:
            PodcastResult with final status
        """
        import time
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout:
            result = await self.check_status(operation_name)

            if result.status == PodcastStatus.COMPLETED:
                logger.info(f"[Podcast] Generation completed: {operation_name}")
                return result
            elif result.status == PodcastStatus.FAILED:
                logger.error(f"[Podcast] Generation failed: {result.error_message}")
                return result

            logger.info(f"[Podcast] Still processing... (elapsed: {int(time.monotonic() - start_time)}s)")
            await asyncio.sleep(poll_interval)

        return PodcastResult(
            operation_name=operation_name,
            status=PodcastStatus.FAILED,
            title="",
            error_message=f"Generation timed out after {timeout}s",
        )

    async def download_podcast(
        self,
        operation_name: str,
        output_path: Optional[str] = None,
    ) -> Union[bytes, str]:
        """팟캐스트 오디오 다운로드 (with validation and retry).

        Args:
            operation_name: Completed operation name
            output_path: Optional file path to save MP3

        Returns:
            Audio bytes if no output_path, else file path

        Raises:
            ValueError: If operation_name is invalid
            RuntimeError: If download fails
        """
        # Input validation
        if not operation_name or not operation_name.strip():
            raise ValueError("No operation name provided")
        if len(operation_name) < 10:
            raise ValueError("Invalid operation name format")

        # Validate output path if provided
        if output_path:
            import os
            parent_dir = os.path.dirname(output_path)
            if parent_dir and not os.path.exists(parent_dir):
                raise ValueError(f"Output directory does not exist: {parent_dir}")
            if ".." in output_path:
                raise ValueError("Path traversal not allowed")

        try:
            token = await self._get_access_token()
            url = f"{PODCAST_API_ENDPOINT}/{operation_name}:download?alt=media"

            # Use longer timeout for download
            client = await self._get_client()
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                follow_redirects=True,
                timeout=PODCAST_DOWNLOAD_TIMEOUT,
            )

            if response.status_code != 200:
                raise RuntimeError(f"Download failed: {response.status_code} - {response.text[:200]}")

            audio_bytes = response.content

            if not audio_bytes or len(audio_bytes) < 1000:
                raise RuntimeError("Downloaded audio is too small or empty")

            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"[Podcast] Downloaded to: {output_path} ({len(audio_bytes)} bytes)")
                return output_path
            else:
                logger.info(f"[Podcast] Downloaded {len(audio_bytes)} bytes")
                return audio_bytes

        except ValueError:
            raise
        except Exception as e:
            logger.exception(f"[Podcast] Download failed: {e}")
            raise RuntimeError(f"Download failed: {e}") from e

    async def generate_and_download(
        self,
        sources: List[Union[PodcastSource, Dict[str, str], str]],
        title: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """팟캐스트 생성 및 다운로드 (end-to-end).

        Args:
            sources: 소스 콘텐츠
            title: 제목
            output_path: 저장 경로 (선택)
            **kwargs: generate_podcast 추가 인자

        Returns:
            {
                "status": PodcastStatus,
                "audio": bytes or path,
                "operation_name": str,
                "error": str or None,
            }
        """
        # Generate
        gen_result = await self.generate_podcast(sources, title, **kwargs)

        if gen_result.status == PodcastStatus.FAILED:
            return {
                "status": gen_result.status,
                "audio": None,
                "operation_name": gen_result.operation_name,
                "error": gen_result.error_message,
            }

        # Wait for completion
        final_result = await self.wait_for_completion(gen_result.operation_name)

        if final_result.status != PodcastStatus.COMPLETED:
            return {
                "status": final_result.status,
                "audio": None,
                "operation_name": final_result.operation_name,
                "error": final_result.error_message,
            }

        # Download
        try:
            audio = await self.download_podcast(final_result.operation_name, output_path)
            return {
                "status": PodcastStatus.COMPLETED,
                "audio": audio,
                "operation_name": final_result.operation_name,
                "error": None,
            }
        except Exception as e:
            return {
                "status": PodcastStatus.FAILED,
                "audio": None,
                "operation_name": final_result.operation_name,
                "error": str(e),
            }

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "project_id": self.config.project_id,
            "location": self.config.location,
            "default_language": self.config.default_language,
            "default_length": self.config.default_length.value,
            "api_endpoint": PODCAST_API_ENDPOINT,
        }


# ============================================================================
# Singleton
# ============================================================================

_podcast_service: Optional[PodcastService] = None


def get_podcast_service(config: Optional[PodcastConfig] = None) -> PodcastService:
    """Podcast 서비스 싱글톤 반환 (thread-safe).

    Args:
        config: 설정 (최초 호출 시에만 적용)

    Returns:
        PodcastService instance
    """
    global _podcast_service

    if _podcast_service is not None:
        return _podcast_service

    with _singleton_lock:
        if _podcast_service is None:
            _podcast_service = PodcastService(config)
    return _podcast_service


def reset_podcast_service() -> None:
    """서비스 리셋 (테스트용, thread-safe)."""
    global _podcast_service
    with _singleton_lock:
        _podcast_service = None


# ============================================================================
# Convenience Functions
# ============================================================================

async def generate_deep_dive_podcast(
    sources: List[str],
    title: str,
    language: str = "ko",
) -> PodcastResult:
    """Deep Dive 팟캐스트 생성.

    Args:
        sources: 텍스트 소스 목록
        title: 제목
        language: 언어 코드

    Returns:
        PodcastResult
    """
    service = get_podcast_service()
    return await service.generate_podcast(
        sources=sources,
        title=title,
        format=PodcastFormat.DEEP_DIVE,
        length=PodcastLength.STANDARD,
        language=language,
    )


async def generate_debate_podcast(
    sources: List[str],
    title: str,
    language: str = "ko",
) -> PodcastResult:
    """Debate 토론 팟캐스트 생성.

    Args:
        sources: 텍스트 소스 목록
        title: 제목
        language: 언어 코드

    Returns:
        PodcastResult
    """
    service = get_podcast_service()
    return await service.generate_podcast(
        sources=sources,
        title=title,
        format=PodcastFormat.DEBATE,
        length=PodcastLength.STANDARD,
        language=language,
    )
