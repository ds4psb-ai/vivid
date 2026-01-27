"""
Video Downloader Service - Using yt-dlp for TikTok/Reels/Shorts
Handles video download and metadata extraction from social media platforms

Features (2026-01-20):
- TIKTOK_PROXY support for residential proxy routing
- Video integrity gate: ffprobe validation before pipeline entry
- Automatic retry with URL re-acquisition on failure

References:
- https://roundproxies.com/blog/yt-dlp/
- https://www.kindproxy.com/blog/en/blog/tiktok-static-residential-proxies-master-guide/
"""

import json
import logging
import os
import re
import tempfile
import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass, field
from typing import List

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from app.config import settings
from app.utils.http_client import (
    build_async_client,
    stream_to_file_limited,
    DownloadTooLargeError,
    InvalidContentTypeError,
)
from app.utils.security_audit import log_security_event
from app.services.download_abuse_guard import download_abuse_guard
from app.services.monitoring import send_alert
from app.services.video_integrity_gate import (
    validate_video_integrity,
    VideoIntegrityError,
    VideoMetadataResult as IntegrityMetadata,
)


class VideoTooLongError(ValueError):
    """Raised when video duration exceeds the configured maximum."""

    pass


# 2026-01: Playwright context singleton for performance (40% speedup)
_playwright_instance = None
_playwright_browser = None
_playwright_lock = asyncio.Lock()


async def get_playwright_browser():
    """Get or create a shared Playwright browser instance (singleton pattern)."""
    global _playwright_instance, _playwright_browser

    async with _playwright_lock:
        if _playwright_browser is None:
            try:
                from playwright.async_api import async_playwright

                _playwright_instance = await async_playwright().start()
                _playwright_browser = await _playwright_instance.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                logger.info("✅ Playwright browser singleton initialized")
            except ImportError:
                logger.warning("Playwright not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Playwright: {e}")
                return None

        return _playwright_browser


async def cleanup_playwright():
    """Cleanup Playwright resources (call on app shutdown)."""
    global _playwright_instance, _playwright_browser

    async with _playwright_lock:
        if _playwright_browser:
            await _playwright_browser.close()
            _playwright_browser = None
        if _playwright_instance:
            await _playwright_instance.stop()
            _playwright_instance = None
        logger.info("Playwright browser singleton cleaned up")


logger = logging.getLogger(__name__)

# Download retry configuration
MAX_DOWNLOAD_RETRIES = 2  # 최대 재시도 횟수 (URL 재획득 포함)
RETRY_DELAY_SECONDS = 2  # 재시도 간 대기 시간

VIDEO_CONTENT_TYPES = (
    "video/*",
    "application/octet-stream",
    "binary/octet-stream",
)


@dataclass
class VideoMetadata:
    """Extracted video metadata from social platforms"""

    id: str
    title: str
    duration: float
    view_count: int
    like_count: int
    uploader: str
    platform: str
    description: str
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    # v3.6 additions for metadata merge
    upload_date: Optional[str] = None  # YYYYMMDD format from yt-dlp
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    hashtags: List[str] = field(default_factory=list)


class VideoDownloader:
    """
    Downloads videos from TikTok, Instagram Reels, and YouTube Shorts
    using yt-dlp for reliable extraction.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.gettempdir()

    def _get_platform(self, url: str) -> str:
        """Detect platform from URL"""
        if "tiktok" in url:
            return "tiktok"
        elif "instagram" in url:
            return "instagram"
        elif "youtube.com/shorts" in url or "youtu.be" in url:
            return "youtube"
        else:
            return "unknown"

    def _parse_proxy_for_playwright(self, proxy_url: str) -> dict:
        """
        Parse proxy URL for Playwright format with authentication support.

        Input formats:
            - socks5://user:pass@host:port
            - http://user:pass@host:port
            - http://host:port (no auth)

        Output (Playwright proxy config):
            {"server": "socks5://host:port", "username": "user", "password": "pass"}

        Reference: https://playwright.dev/docs/api/class-browser#browser-new-context-option-proxy
        """
        from urllib.parse import urlparse

        parsed = urlparse(proxy_url)

        # Build server URL without credentials
        if parsed.port:
            server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        else:
            server = f"{parsed.scheme}://{parsed.hostname}"

        config = {"server": server}

        # Add authentication if present
        if parsed.username:
            config["username"] = parsed.username
        if parsed.password:
            config["password"] = parsed.password

        return config

    async def download(
        self,
        url: str,
        validate_integrity: bool = True,
    ) -> Tuple[str, VideoMetadata]:
        """
        Download video and extract metadata with integrity validation.

        Args:
            url: Video URL (TikTok, Reels, Shorts)
            validate_integrity: Run ffprobe validation after download (default: True)

        Returns:
            Tuple of (local_file_path, metadata)

        Raises:
            VideoIntegrityError: If video fails integrity check after all retries
            RuntimeError: If download fails after all retries
        """
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("yt-dlp not installed. Run: pip install yt-dlp")

        platform = self._get_platform(url)
        last_error = None

        # Retry loop with URL re-acquisition
        for attempt in range(MAX_DOWNLOAD_RETRIES + 1):
            if attempt > 0:
                logger.info(f"[Download] Retry {attempt}/{MAX_DOWNLOAD_RETRIES} for {url[:50]}...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

            try:
                file_path, metadata = await self._download_with_fallback(url, platform)

                # Integrity validation (P0 gate)
                if validate_integrity:
                    integrity_result = validate_video_integrity(file_path)
                    if not integrity_result.is_valid:
                        # Clean up invalid file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        raise VideoIntegrityError(f"Integrity check failed: {integrity_result.error_message}")

                    # Enrich metadata from integrity check
                    if integrity_result.metadata:
                        metadata.duration = integrity_result.metadata.duration_sec or 0

                    # 2026-01: Duration hard limit (TikTok/Shorts/Reels = max 3분)
                    max_duration = settings.VIDEO_DOWNLOAD_MAX_DURATION_SECONDS
                    if metadata.duration > max_duration:
                        # Clean up file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        log_security_event(
                            "video_too_long",
                            user_id=None,
                            reason="duration_limit_exceeded",
                            url=url[:100],
                            duration_sec=metadata.duration,
                            max_duration_sec=max_duration,
                            platform=platform,
                        )
                        raise VideoTooLongError(
                            f"영상이 너무 깁니다 ({metadata.duration:.0f}초). "
                            f"최대 {max_duration}초(3분) 이하 영상만 분석할 수 있습니다."
                        )

                    logger.info(
                        f"[Download] Success with integrity: "
                        f"{integrity_result.metadata.width}x{integrity_result.metadata.height} "
                        f"@ {integrity_result.metadata.fps}fps, {metadata.duration:.1f}s"
                    )

                return file_path, metadata

            except VideoTooLongError as e:
                # 2026-01: Don't retry for duration limit - it won't change
                logger.warning(f"[Download] Video too long, not retrying: {e}")
                raise

            except VideoIntegrityError as e:
                last_error = e
                logger.warning(f"[Download] Integrity failed (attempt {attempt + 1}): {e}")
                # Continue to retry with URL re-acquisition

            except Exception as e:
                last_error = e
                logger.warning(f"[Download] Failed (attempt {attempt + 1}): {e}")
                # Continue to retry

        # All retries exhausted
        raise last_error or RuntimeError(f"Download failed after {MAX_DOWNLOAD_RETRIES + 1} attempts")

    async def _download_with_fallback(
        self,
        url: str,
        platform: str,
    ) -> Tuple[str, VideoMetadata]:
        """
        Download video with platform-specific strategy.

        2026-01 Update:
        - TikTok: Playwright primary → yt-dlp fallback (85-90% success rate)
        - YouTube: JSON parsing primary → yt-dlp fallback (Railway 봇 감지 우회)
        - Other platforms: yt-dlp primary (no change)
        """
        import yt_dlp

        # TikTok: Playwright first (2026-01 strategy change)
        if platform == "tiktok":
            try:
                logger.info("[TikTok] Trying Playwright direct download (primary)...")
                return await self._download_tiktok_direct(url)
            except Exception as e:
                logger.warning(f"[TikTok] Playwright failed, trying yt-dlp fallback: {e}")
                # Continue to yt-dlp fallback below

        # YouTube: 3단계 폴백 전략 (2026-01)
        # 1. JSON parsing (빠른 실패)
        # 2. yt-dlp + Residential Proxy (YOUTUBE_PROXY)
        # 3. yt-dlp without proxy (최후 수단)
        if platform == "youtube":
            try:
                logger.info("[YouTube] Trying JSON parsing method (primary)...")
                return await self._download_youtube_json_parse(url)
            except Exception as e:
                logger.warning(f"[YouTube] JSON parsing failed: {e}")

            # yt-dlp with proxy (if available)
            youtube_proxy = os.getenv("YOUTUBE_PROXY")
            if youtube_proxy:
                try:
                    logger.info("[YouTube] Trying yt-dlp with proxy (residential)...")
                    return await self._download_youtube_with_ytdlp(url, proxy=youtube_proxy)
                except Exception as e:
                    logger.warning(f"[YouTube] yt-dlp with proxy failed: {e}, trying without proxy")

            # yt-dlp without proxy (fallback)
            try:
                logger.info("[YouTube] Trying yt-dlp without proxy (fallback)...")
                return await self._download_youtube_with_ytdlp(url, proxy=None)
            except Exception as e:
                raise RuntimeError(f"All YouTube download methods failed: {e}")

        # Configure yt-dlp options (TikTok/Instagram - YouTube uses dedicated method above)
        ydl_opts = {
            # Download video+audio (max 720p for faster download), merge to mp4
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",  # Ensure output is mp4
            "outtmpl": os.path.join(self.output_dir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        # Proxy support (TikTok/Instagram)
        if platform in ("tiktok", "instagram"):
            proxy_url = os.getenv("TIKTOK_PROXY") or os.getenv("YTDLP_PROXY")
            if proxy_url:
                ydl_opts["proxy"] = proxy_url
                logger.debug(f"[yt-dlp] Using proxy for {platform}: {proxy_url[:30]}...")

        # Cookie support for authenticated content
        cookie_file = os.getenv("YTDLP_COOKIE_FILE")
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts["cookiefile"] = cookie_file

        cookies_from_browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
        if cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

        # Platform-specific options
        if platform == "tiktok":
            ydl_opts.update(
                {
                    "format": "best",
                }
            )
            # TikTok: Railway 환경에서는 브라우저 쿠키 사용 불가
            # cookiefile이 있으면 사용, 없으면 쿠키 없이 시도
            if not ydl_opts.get("cookiefile"):
                # 브라우저 쿠키 사용하지 않음 (Railway 호환성)
                pass
        elif platform == "instagram":
            ydl_opts.update(
                {
                    "format": "best",
                    # Instagram may require cookies for some content
                }
            )

        # Run download in thread pool (yt-dlp is synchronous)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: self._sync_download(url, ydl_opts))
        return result

    async def _validate_video_accessible(self, url: str) -> Tuple[bool, Optional[float]]:
        """
        2026-01: TikTok oEmbed API로 영상 접근성 + duration 사전 검증.
        삭제/비공개 영상을 미리 감지하여 불필요한 Playwright 실행 방지.

        Returns:
            Tuple[accessible: bool, duration_sec: Optional[float]]
            - accessible=False → 영상 접근 불가 (삭제/비공개)
            - duration_sec=None → 알 수 없음 (다운로드 후 확인)
        """
        try:
            async with build_async_client(timeout=5.0) as client:
                resp = await client.get(
                    "https://www.tiktok.com/oembed",
                    params={"url": url},
                )
                if resp.status_code == 200:
                    # oEmbed 응답에서 duration 추출 (TikTok은 초 단위로 반환)
                    try:
                        data = resp.json()
                        duration_sec = data.get("duration")  # TikTok oEmbed: "duration" in seconds
                        if duration_sec is not None:
                            logger.debug(f"[oEmbed] Duration pre-check: {duration_sec}s")
                        return True, duration_sec
                    except Exception:
                        return True, None  # JSON 파싱 실패해도 접근 가능
                elif resp.status_code == 404:
                    logger.warning(f"[oEmbed] Video deleted or private: {url[:50]}...")
                    return False, None
                else:
                    logger.debug(f"[oEmbed] Unexpected status {resp.status_code}, proceeding anyway")
        except Exception as e:
            logger.debug(f"[oEmbed] Check failed ({e}), proceeding anyway")

        return True, None  # 불확실할 때는 진행 (duration 확인 불가)

    async def _download_tiktok_direct(self, url: str) -> Tuple[str, VideoMetadata]:
        """
        Download TikTok video directly by extracting playAddr/downloadAddr.
        Uses Playwright (cookies) via TikTokMetadataExtractor for higher success rate.

        2026-01 Improvements:
        - oEmbed pre-validation (skip deleted/private videos early)
        - Retry with exponential backoff for CDN errors
        - Playwright context reuse (singleton pattern)
        """
        from app.services.tiktok_metadata import TikTokMetadataExtractor

        # Step 1: oEmbed 사전 검증 (삭제/비공개 + duration 조기 감지)
        accessible, duration_sec = await self._validate_video_accessible(url)
        if not accessible:
            raise RuntimeError("Video not accessible (deleted/private/region-blocked)")

        # Step 1.5: Duration 사전 체크 (다운로드 전 대역폭 절약)
        max_duration = settings.VIDEO_DOWNLOAD_MAX_DURATION_SECONDS
        if duration_sec is not None and duration_sec > max_duration:
            log_security_event(
                "video_too_long_precheck",
                user_id=None,
                reason="duration_limit_exceeded_precheck",
                url=url[:100],
                duration_sec=duration_sec,
                max_duration_sec=max_duration,
            )
            raise VideoTooLongError(
                f"영상이 너무 깁니다 ({duration_sec:.0f}초). "
                f"최대 {max_duration}초(3분) 이하 영상만 분석할 수 있습니다."
            )

        video_url = await self._capture_tiktok_video_url(url)

        extractor = TikTokMetadataExtractor()
        html = None
        if not video_url:
            html = await extractor._fetch_with_playwright(url)
            if not html:
                html = await extractor._fetch_with_httpx(url)
            if not html:
                raise RuntimeError("Failed to fetch TikTok HTML")
            video_url = self._extract_tiktok_video_url(html)
        if not video_url:
            raise RuntimeError("Failed to extract TikTok video URL")

        # Prepare output path
        video_id = self._extract_tiktok_id(url) or "tiktok_video"
        temp_path = os.path.join(self.output_dir, f"{video_id}.mp4")

        guard_state = await download_abuse_guard.check_blocked(video_url, user_id=None)
        if guard_state.blocked:
            log_security_event(
                "download_blocked",
                user_id=None,
                reason="download_cooldown",
                url_host=guard_state.host,
                guard_key=guard_state.key_hash,
                guard_scope=guard_state.key_type,
                guard_cooldown_seconds=guard_state.cooldown_seconds,
            )
            try:
                await send_alert(
                    title="Video download blocked (cooldown)",
                    message=(
                        "Context: TikTok direct video\n"
                        f"Host: {guard_state.host}\n"
                        f"Key: {guard_state.key_hash}\n"
                        f"Cooldown: {guard_state.cooldown_seconds}s"
                    ),
                    severity="warning",
                )
            except Exception as alert_exc:
                logger.warning("Download cooldown alert failed: %s", alert_exc)
            raise RuntimeError("Download blocked by abuse guard")

        # Proxy support for httpx (video download)
        proxy_url = os.getenv("TIKTOK_PROXY") or os.getenv("YTDLP_PROXY")
        client_kwargs = {
            "follow_redirects": True,
            # 2026-01: Granular timeout for better error detection
            "timeout": httpx.Timeout(
                timeout=60.0,
                connect=10.0,  # 연결 10초
                read=30.0,  # 읽기 30초
                write=10.0,  # 쓰기 10초
            ),
            # 2026-01: Skip SSL verification for TikTok CDN (intermittent cert issues)
            "verify": False,
        }
        if proxy_url:
            client_kwargs["proxy"] = proxy_url
            logger.debug(f"[httpx] Using proxy for video download: {proxy_url[:30]}...")

        # 2026-01: Retry with exponential backoff for TikTok CDN errors
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True,
        )
        async def _download_with_retry():
            async with build_async_client(**client_kwargs) as client:
                await stream_to_file_limited(
                    client,
                    video_url,
                    temp_path,
                    max_bytes=settings.VIDEO_DOWNLOAD_MAX_BYTES,
                    allowed_content_types=VIDEO_CONTENT_TYPES,
                )

        try:
            await _download_with_retry()
        except DownloadTooLargeError as exc:
            guard_state = await download_abuse_guard.record_oversize(video_url, user_id=None)
            log_security_event(
                "download_too_large",
                user_id=None,
                reason="video_download_cap",
                url=video_url,
                max_bytes=settings.VIDEO_DOWNLOAD_MAX_BYTES,
                error=str(exc),
                guard_count=guard_state.count,
                guard_threshold=guard_state.threshold,
                guard_window_seconds=guard_state.window_seconds,
                guard_cooldown_seconds=guard_state.cooldown_seconds,
                guard_key=guard_state.key_hash,
                guard_scope=guard_state.key_type,
            )
            try:
                await send_alert(
                    title="Video download blocked (size cap)",
                    message=(
                        f"URL: {video_url}\n"
                        f"Cap: {settings.VIDEO_DOWNLOAD_MAX_BYTES} bytes\n"
                        f"Count: {guard_state.count}/{guard_state.threshold}\n"
                        f"Blocked: {guard_state.blocked}"
                    ),
                    severity="warning",
                )
            except Exception as alert_exc:
                logger.warning("Download size alert failed: %s", alert_exc)
            if guard_state.blocked:
                log_security_event(
                    "download_blocked",
                    user_id=None,
                    reason="oversize_threshold",
                    url_host=guard_state.host,
                    guard_key=guard_state.key_hash,
                    guard_scope=guard_state.key_type,
                    guard_count=guard_state.count,
                    guard_threshold=guard_state.threshold,
                    guard_cooldown_seconds=guard_state.cooldown_seconds,
                )
            raise
        except InvalidContentTypeError as exc:
            log_security_event(
                "download_blocked",
                user_id=None,
                reason="content_type_not_allowed",
                url=video_url,
                allowed_types=VIDEO_CONTENT_TYPES,
                error=str(exc),
            )
            try:
                await send_alert(
                    title="Video download blocked (content-type)",
                    message=(f"URL: {video_url}\n" f"Allowed: {', '.join(VIDEO_CONTENT_TYPES)}"),
                    severity="warning",
                )
            except Exception as alert_exc:
                logger.warning("Download content-type alert failed: %s", alert_exc)
            raise

        metadata = VideoMetadata(
            id=video_id,
            title=self._extract_og_title(html or "") or "TikTok Video",
            duration=0,
            view_count=0,
            like_count=0,
            uploader="unknown",
            platform="tiktok",
            description="",
            thumbnail_url=self._extract_og_thumbnail(html or ""),
            audio_url=video_url,
        )

        return temp_path, metadata

    async def _download_youtube_json_parse(self, url: str) -> Tuple[str, VideoMetadata]:
        """
        YouTube HTML에서 ytInitialPlayerResponse JSON 파싱으로 비디오 URL 추출.

        장점:
        - 로그인/쿠키/프록시 불필요
        - Railway 데이터센터 IP에서 작동
        - yt-dlp보다 빠름 (JavaScript 실행 없음)

        단점:
        - 일부 영상에서 streamingData가 없을 수 있음 (age-restricted 등)
        - YouTube가 HTML 구조를 변경하면 실패할 수 있음
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with build_async_client(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text

        # ytInitialPlayerResponse에서 streamingData 추출
        match = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.+?\});", html)
        if not match:
            raise ValueError("ytInitialPlayerResponse not found in HTML")

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse ytInitialPlayerResponse JSON: {e}")

        # playabilityStatus 체크 (봇 감지/로그인 필요 등)
        playability = data.get("playabilityStatus", {})
        status = playability.get("status")
        if status != "OK":
            reason = playability.get("reason", "Unknown reason")
            raise ValueError(f"Video not playable: {status} - {reason}")

        streaming = data.get("streamingData", {})
        if not streaming:
            raise ValueError("No streamingData found (may require login/age verification)")

        # formats 또는 adaptiveFormats에서 mp4 URL 찾기
        formats = streaming.get("formats", []) + streaming.get("adaptiveFormats", [])

        # 2026-01: SABR 스트리밍 감지 (YouTube Issue #12482)
        sabr_url = streaming.get("serverAbrStreamingUrl", "")
        has_sabr_only = bool(sabr_url) and not formats

        video_url = None
        best_quality = 0
        has_signature_cipher = False
        has_missing_url = False  # PO Token 요구 신호

        for fmt in formats:
            mime = fmt.get("mimeType", "")

            # signatureCipher가 있으면 JS 복호화 필요 (JSON 파싱으로 불가)
            if fmt.get("signatureCipher") or fmt.get("cipher"):
                has_signature_cipher = True
                continue

            # 2026-01: URL 없는 포맷 = PO Token 요구 (Issue #12482)
            if not fmt.get("url") and mime:
                has_missing_url = True
                logger.debug(f"[YouTube] Format missing URL (PO Token required): {mime[:30]}")
                continue

            # 2026-01: SABR URL 감지 (sabr=1 파라미터)
            url_str = fmt.get("url", "")
            if "sabr=1" in url_str:
                logger.debug("[YouTube] SABR format detected - skipping")
                continue

            # video/mp4 포맷 중 가장 높은 품질 선택
            if "video/mp4" in mime and fmt.get("url"):
                quality = fmt.get("height", 0) or 0
                if quality > best_quality:
                    best_quality = quality
                    video_url = fmt["url"]

        if not video_url:
            # 2026-01: 구체적인 에러 메시지
            if has_sabr_only:
                raise ValueError(
                    "SABR-only streaming (YouTube HLS protocol). "
                    "Datacenter IP likely detected. Falling back to yt-dlp..."
                )
            if has_signature_cipher:
                raise ValueError(
                    "Signature-protected URLs (JS decryption required). "
                    "Railway/datacenter: common. Falling back to yt-dlp..."
                )
            if has_missing_url:
                raise ValueError(
                    "Formats missing URL (PO Token required). "
                    "YouTube blocking datacenter IPs. Falling back to yt-dlp..."
                )
            raise ValueError("No mp4 video URL found in streamingData")

        logger.info(f"[YouTube JSON] Found video URL (quality: {best_quality}p)")

        # 비디오 ID 및 메타데이터 추출
        video_id = self._extract_youtube_id(url) or "youtube_video"
        output_path = os.path.join(self.output_dir, f"{video_id}.mp4")

        # 메타데이터 추출 (videoDetails에서)
        video_details = data.get("videoDetails", {})
        title = video_details.get("title", "YouTube Video")
        duration = int(video_details.get("lengthSeconds", 0) or 0)
        view_count = int(video_details.get("viewCount", 0) or 0)
        uploader = video_details.get("author", "Unknown")
        description = video_details.get("shortDescription", "")
        thumbnail_url = None
        thumbnails = video_details.get("thumbnail", {}).get("thumbnails", [])
        if thumbnails:
            thumbnail_url = thumbnails[-1].get("url")  # 가장 큰 썸네일

        # 직접 다운로드
        async with build_async_client(timeout=120.0) as client:
            resp = await client.get(video_url, headers=headers, follow_redirects=True)
            resp.raise_for_status()

            # 동기 파일 쓰기 (aiofiles 의존성 없이)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._write_bytes_to_file(output_path, resp.content))

        logger.info(f"[YouTube JSON] Downloaded to {output_path}")

        metadata = VideoMetadata(
            id=video_id,
            title=title,
            duration=float(duration),
            view_count=view_count,
            like_count=0,  # Not available in ytInitialPlayerResponse
            uploader=uploader,
            platform="youtube",
            description=description,
            thumbnail_url=thumbnail_url,
            audio_url=url,
        )

        return output_path, metadata

    async def _download_youtube_with_ytdlp(
        self,
        url: str,
        proxy: Optional[str] = None,
    ) -> Tuple[str, VideoMetadata]:
        """
        YouTube 전용 yt-dlp 다운로드 (2026-01 최적화).

        Args:
            url: YouTube URL
            proxy: Optional SOCKS5/HTTP proxy URL

        Returns:
            Tuple of (file_path, metadata)
        """
        import yt_dlp

        ydl_opts = {
            # 2026-01: 'best' = 미리 합쳐진 포맷 (SABR 문제 우회)
            "format": "best[ext=mp4]/best[height<=720]/best",
            "outtmpl": os.path.join(self.output_dir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "sleep_interval": 1,
            "max_sleep_interval": 3,
            "fragment_retries": 5,
            "skip_unavailable_fragments": True,
            "extractor_args": {
                "youtube": {
                    "formats": "missing_pot",
                }
            },
        }

        if proxy:
            ydl_opts["proxy"] = proxy
            logger.debug(f"[yt-dlp] YouTube: using proxy {proxy[:40]}...")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: self._sync_download(url, ydl_opts))
        return result

    async def _capture_tiktok_video_url(self, url: str) -> Optional[str]:
        """
        Capture the direct video URL from Playwright network responses.
        Supports TIKTOK_PROXY for residential proxy routing.

        2026-01: Uses singleton browser for performance (40% speedup).
        """
        import random
        from pathlib import Path

        # 2026-01: Chrome 131 required (TikTok version checking)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        ]

        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        if not cookie_file or not os.path.exists(cookie_file):
            base_dir = Path(__file__).parent.parent.parent
            auto_cookie = base_dir / "tiktok_cookies_auto.json"
            if auto_cookie.exists():
                cookie_file = str(auto_cookie)

        # Proxy support for Playwright (with authentication parsing)
        proxy_url = os.getenv("TIKTOK_PROXY") or os.getenv("YTDLP_PROXY")
        proxy_config = None
        if proxy_url:
            proxy_config = self._parse_proxy_for_playwright(proxy_url)
            logger.debug(f"[Playwright] Using proxy: {proxy_config.get('server', '')[:30]}...")

        video_url = None
        context = None

        # 2026-01: Use singleton browser for performance (context-level proxy)
        browser = await get_playwright_browser()
        if not browser:
            return None

        try:
            context = await browser.new_context(
                user_agent=random.choice(user_agents),
                viewport={"width": 1280, "height": 720},
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                proxy=proxy_config,  # Proxy at context level
                ignore_https_errors=True,  # 2026-01: Ignore HTTPS cert errors
            )

            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                window.chrome = { runtime: {} };
            """)

            if cookie_file and os.path.exists(cookie_file):
                try:
                    import json as json_module

                    with open(cookie_file, "r") as f:
                        data = json_module.load(f)
                    cookies = data.get("cookies", data) if isinstance(data, dict) else data
                    if isinstance(cookies, list) and cookies:
                        await context.add_cookies(cookies)
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"Failed to load TikTok cookies: {e}")

            page = await context.new_page()

            def handle_response(response):
                nonlocal video_url
                if video_url:
                    return
                try:
                    ctype = response.headers.get("content-type", "")
                    if response.request.resource_type == "media" or "video" in ctype:
                        if "tiktok" in response.url or "video" in response.url:
                            video_url = response.url
                except (AttributeError, KeyError) as e:
                    logger.debug(f"Response handler error: {e}")

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
                if not video_url:
                    try:
                        await page.eval_on_selector("video", "v => v.play()")
                    except (TimeoutError, Exception) as e:
                        logger.debug(f"Video play trigger failed: {e}")
                    await page.wait_for_timeout(3000)
            finally:
                # 2026-01: Close context only (browser is singleton, reused)
                if context:
                    await context.close()

        except Exception as e:
            logger.warning(f"Playwright capture failed: {e}")
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        return video_url

    def _extract_tiktok_video_url(self, html: str) -> Optional[str]:
        """
        Extract direct video URL from TikTok HTML.
        Prefers JSON payloads, falls back to regex.
        """
        import json

        def pick_video_url(video_obj: Optional[dict]) -> Optional[str]:
            if not isinstance(video_obj, dict):
                return None
            for key in ["playAddr", "downloadAddr", "playAddrByte", "downloadAddrByte"]:
                value = video_obj.get(key)
                if isinstance(value, str) and value.startswith("http"):
                    return value
            bitrate_info = video_obj.get("bitrateInfo") or []
            if isinstance(bitrate_info, list):
                for entry in bitrate_info:
                    addr = entry.get("PlayAddr") or entry.get("playAddr") or {}
                    if isinstance(addr, dict):
                        urls = addr.get("UrlList") or addr.get("url_list") or addr.get("urlList") or []
                        if isinstance(urls, list) and urls:
                            if isinstance(urls[0], str) and urls[0].startswith("http"):
                                return urls[0]
            return None

        # 1) UNIVERSAL_DATA JSON (2026-01: try new ID first, then old ID for backwards compat)
        universal_match = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)</script>', html, re.IGNORECASE
        )
        # Fallback: old script ID (pre-2026)
        if not universal_match:
            universal_match = re.search(r'<script id="UNIVERSAL_DATA"[^>]*>([\s\S]*?)</script>', html, re.IGNORECASE)
        if universal_match:
            try:
                data = json.loads(universal_match.group(1).strip())
                item = (
                    data.get("__DEFAULT_SCOPE__", {})
                    .get("webapp.video-detail", {})
                    .get("itemInfo", {})
                    .get("itemStruct", {})
                )
                url = pick_video_url(item.get("video"))
                if url:
                    return url
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"UNIVERSAL_DATA parsing failed: {e}")

        # 2) SIGI_STATE JSON
        sigi_match = re.search(r'<script id="SIGI_STATE"[^>]*>([\\s\\S]*?)</script>', html, re.IGNORECASE)
        if sigi_match:
            try:
                data = json.loads(sigi_match.group(1).strip())
                item_module = data.get("ItemModule", {}) or {}
                if item_module:
                    item = next(iter(item_module.values()))
                    url = pick_video_url(item.get("video"))
                    if url:
                        return url
            except (json.JSONDecodeError, KeyError, TypeError, StopIteration) as e:
                logger.debug(f"SIGI_STATE parsing failed: {e}")

        # 3) Fallback regex
        patterns = [
            r'"playAddr":"(.*?)"',
            r'"downloadAddr":"(.*?)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if not match:
                continue
            raw = match.group(1)
            # Decode escaped sequences
            try:
                decoded = raw.encode("utf-8").decode("unicode_escape")
            except (UnicodeDecodeError, UnicodeEncodeError, ValueError) as e:
                logger.debug(f"URL decoding failed, using raw value: {e}")
                decoded = raw
            decoded = decoded.replace("\\/", "/")
            if decoded.startswith("http"):
                return decoded
        return None

    def _write_bytes_to_file(self, path: str, content: bytes) -> None:
        """Helper to write bytes to file (used in thread pool)."""
        with open(path, "wb") as f:
            f.write(content)

    def _extract_og_title(self, html: str) -> Optional[str]:
        match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def _extract_og_thumbnail(self, html: str) -> Optional[str]:
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def _sync_download(self, url: str, ydl_opts: dict) -> Tuple[str, VideoMetadata]:
        """Synchronous download helper"""
        import yt_dlp
        import shutil

        # Verify Deno availability for YouTube (required for yt-dlp-ejs)
        if ydl_opts.get("js_runtimes") and "deno" in ydl_opts["js_runtimes"]:
            deno_path = shutil.which("deno")
            if not deno_path:
                logger.warning("⚠️ Deno not found in PATH, removing js_runtimes option")
                ydl_opts.pop("js_runtimes", None)
                ydl_opts.pop("remote_components", None)
            else:
                logger.debug(f"✅ Deno found at: {deno_path}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=True)

            # Get downloaded file path
            file_path = ydl.prepare_filename(info)

            # Handle case where extension might differ
            if not os.path.exists(file_path):
                # Try with mp4 extension
                base = os.path.splitext(file_path)[0]
                for ext in [".mp4", ".webm", ".mkv"]:
                    if os.path.exists(base + ext):
                        file_path = base + ext
                        break

            # Build metadata
            metadata = VideoMetadata(
                id=info.get("id", "unknown"),
                title=info.get("title", "Untitled"),
                duration=info.get("duration", 0) or 0,
                view_count=info.get("view_count", 0) or 0,
                like_count=info.get("like_count", 0) or 0,
                uploader=info.get("uploader", info.get("channel", "Unknown")),
                platform=self._get_platform(url),
                description=info.get("description", ""),
                thumbnail_url=info.get("thumbnail"),
                audio_url=info.get("url"),
                # v3.6 additions
                upload_date=info.get("upload_date"),  # YYYYMMDD
                comment_count=info.get("comment_count"),
                share_count=info.get("repost_count"),  # TikTok uses repost_count
                hashtags=(info.get("tags") or [])[:10],  # Max 10 hashtags
            )

            return file_path, metadata

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube Video ID from URL"""
        pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    def _extract_tiktok_id(self, url: str) -> Optional[str]:
        match = re.search(r"/video/(\d+)", url)
        return match.group(1) if match else None

    async def _fetch_youtube_metadata_api(self, video_id: str, api_key: str) -> Optional[VideoMetadata]:
        """Fetch metadata using YouTube Data API v3"""
        import httpx
        from datetime import timedelta

        # Simple ISO8601 duration parser
        def parse_duration(duration_str):
            match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
            if not match:
                return 0
            h, m, s = match.groups()
            return int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)

        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {"part": "snippet,contentDetails,statistics", "id": video_id, "key": api_key}

        async with build_async_client(timeout=15.0) as client:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"YouTube API Error: {resp.status_code}")
                    return None

                data = resp.json()
                if not data.get("items"):
                    return None

                item = data["items"][0]
                snippet = item["snippet"]
                content = item["contentDetails"]
                stats = item["statistics"]

                duration_sec = parse_duration(content["duration"])

                # Best thumbnail
                thumbs = snippet.get("thumbnails", {})
                best_thumb = (
                    thumbs.get("maxres", {}).get("url")
                    or thumbs.get("high", {}).get("url")
                    or thumbs.get("default", {}).get("url")
                )

                # Convert ISO date to YYYYMMDD format for consistency with yt-dlp
                published_at = snippet.get("publishedAt", "")  # e.g., "2009-10-25T06:57:33Z"
                upload_date = None
                if published_at:
                    upload_date = published_at[:10].replace("-", "")  # "20091025"

                return VideoMetadata(
                    id=item["id"],
                    title=snippet["title"],
                    duration=float(duration_sec),
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)),
                    uploader=snippet["channelTitle"],
                    platform="youtube",
                    description=snippet["description"],
                    thumbnail_url=best_thumb,
                    audio_url=f"https://www.youtube.com/watch?v={item['id']}",  # Not direct link, but valid for yt-dlp later
                    upload_date=upload_date,
                    comment_count=int(stats.get("commentCount", 0)) if stats.get("commentCount") else None,
                )
            except (httpx.HTTPError, KeyError, ValueError) as e:
                logger.warning(f"YouTube API Exception: {e}")
                return None

    async def extract_metadata_only(self, url: str) -> VideoMetadata:
        """
        Extract metadata without downloading.
        Prioritizes YouTube Data API for YouTube links if key is available.
        Falls back to yt-dlp.
        """

        # 1. Try YouTube API
        api_key = os.getenv("YOUTUBE_API_KEY")
        if api_key and self._get_platform(url) == "youtube":
            vid_id = self._extract_youtube_id(url)
            if vid_id:
                logger.debug(f"[YouTube API] Fetching metadata for {vid_id}")
                meta = await self._fetch_youtube_metadata_api(vid_id, api_key)
                if meta:
                    return meta
                logger.debug("[YouTube API] Failed, falling back to yt-dlp")

        # 2. Fallback to yt-dlp
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("yt-dlp not installed")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,  # Need full metadata
            "skip_download": True,
            # 'cookiefile': '...' # Needed for some Age-gated content
        }

        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # yt-dlp handles Shorts URLs automatically
                info = ydl.extract_info(url, download=False)
                return VideoMetadata(
                    id=info.get("id", "unknown"),
                    title=info.get("title", "Untitled"),
                    duration=info.get("duration", 0) or 0,
                    view_count=info.get("view_count", 0) or 0,
                    like_count=info.get("like_count", 0) or 0,
                    uploader=info.get("uploader", "Unknown"),
                    platform=self._get_platform(url),
                    description=info.get("description", ""),
                    thumbnail_url=info.get("thumbnail"),
                )

        return await loop.run_in_executor(None, _extract)


# Singleton instance
video_downloader = VideoDownloader()
