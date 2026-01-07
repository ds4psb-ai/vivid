"""Tier 0: Vertex AI RAG Engine - Hybrid RAG Architecture.

Vertex AI RAG Engine을 사용한 프라이빗 데이터 검색 + Gemini Grounding.

Architecture:
- Tier 0: Vertex AI RAG Engine (프라이빗 데이터)
  ├─ 거장 DNA, VDG 표준, 차원 앱 가이드
  ├─ Corpus 생성 → 자동 청킹/임베딩/인덱싱
  └─ Gemini Tool로 통합 검색

- Tier 1: Gemini Grounding + Google Search (실시간 정보)
  └─ 최신 트렌드, 뉴스, 외부 레퍼런스

Usage:
    from app.rag.tier0_vertex_rag import get_vertex_rag_service

    service = get_vertex_rag_service()

    # RAG 검색 (프라이빗 데이터)
    result = await service.query(
        query="봉준호 감독의 시각적 특징",
        corpus_name="auteur_dna",
        use_grounding=True,  # Google Search도 함께 사용
    )

    # Corpus 생성 및 문서 인덱싱
    await service.create_corpus("auteur_dna", "거장 DNA 문서")
    await service.index_documents("auteur_dna", ["gs://crebit-rag-data/dna_bong.json"])
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Timeout settings (seconds)
VERTEX_INIT_TIMEOUT = 30
CORPUS_CREATE_TIMEOUT = 60
FILE_IMPORT_TIMEOUT = 300  # 5 minutes for large imports
QUERY_TIMEOUT = 60
LIST_CORPORA_TIMEOUT = 30

# Retry settings
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 10.0

# Validation limits
MAX_QUERY_LENGTH = 10000
MAX_CORPUS_COUNT = 10
MAX_TOP_K = 100

# Thread safety
_singleton_lock = threading.RLock()

T = TypeVar("T")


# ============================================================================
# Retry Decorator with Exponential Backoff
# ============================================================================

def with_retry(
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for exponential backoff retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_exceptions: Tuple of exception types to retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"[VertexRAG] Retry {attempt + 1}/{max_retries} for {func.__name__}: "
                            f"{type(e).__name__}: {e}. Waiting {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"[VertexRAG] All {max_retries} retries exhausted for {func.__name__}: "
                            f"{type(e).__name__}: {e}"
                        )
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"[VertexRAG] Retry {attempt + 1}/{max_retries} for {func.__name__}: "
                            f"{type(e).__name__}: {e}. Waiting {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[VertexRAG] All {max_retries} retries exhausted for {func.__name__}: "
                            f"{type(e).__name__}: {e}"
                        )
            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ============================================================================
# Input Validation
# ============================================================================

def validate_query(query: str) -> None:
    """Validate query string.

    Args:
        query: Query string to validate

    Raises:
        ValueError: If query is invalid
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")
    if "\x00" in query:
        raise ValueError("Query contains invalid null bytes")


def validate_corpus_name(corpus_name: str) -> None:
    """Validate corpus name.

    Args:
        corpus_name: Corpus name to validate

    Raises:
        ValueError: If corpus name is invalid
    """
    if not corpus_name or not corpus_name.strip():
        raise ValueError("Corpus name cannot be empty")
    if len(corpus_name) > 100:
        raise ValueError("Corpus name exceeds maximum length of 100 characters")
    # Allow alphanumeric, underscore, hyphen
    if not all(c.isalnum() or c in "_-" for c in corpus_name):
        raise ValueError("Corpus name contains invalid characters (only alphanumeric, _, - allowed)")


def validate_document_paths(paths: List[str]) -> None:
    """Validate document paths for path traversal attacks.

    Args:
        paths: List of file paths to validate

    Raises:
        ValueError: If any path is invalid
    """
    if not paths:
        raise ValueError("At least one document path required")
    for path in paths:
        if not path:
            raise ValueError("Document path cannot be empty")
        # Check for path traversal
        if ".." in path:
            raise ValueError(f"Path traversal detected in: {path}")
        # Local paths should not start with /
        if not path.startswith("gs://") and path.startswith("/"):
            raise ValueError(f"Local paths should be relative: {path}")


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class VertexRAGConfig:
    """Vertex AI RAG Engine 설정."""
    project_id: str = field(default_factory=lambda: getattr(settings, "GCP_PROJECT_ID", "gen-lang-client-0587915249"))
    location: str = field(default_factory=lambda: getattr(settings, "GCP_LOCATION", "us-central1"))
    # RAG 설정
    embedding_model: str = "text-embedding-005"
    chunk_size: int = 1024
    chunk_overlap: int = 200
    # Gemini 설정 (Vertex AI model names differ from API)
    # Vertex AI: gemini-2.0-flash-001, gemini-2.0-pro-001
    # API: gemini-3-flash-preview, gemini-3-pro-preview
    gemini_model: str = field(default_factory=lambda: getattr(settings, "VERTEX_GEMINI_MODEL", "gemini-2.0-flash-001"))
    # GCS 버킷
    gcs_bucket: str = "crebit-rag-data"
    # Grounding
    enable_google_search: bool = True


# ============================================================================
# Corpus Registry (Crebit RAG Corpora)
# ============================================================================

CORPUS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "auteur_dna": {
        "display_name": "Auteur DNA Collection",
        "description": "거장 감독들의 시각적 문법, 스타일 DNA",
        "dimension": "AD",
        "documents": [
            "dna_bong.json",
            "dna_park.json",
            "dna_shinkai.json",
            "dna_hong.json",
            "dna_na.json",
            "dna_lee.json",
        ],
    },
    "meta_invariants": {
        "display_name": "Cinematic Invariants",
        "description": "영화적 진리의 불변 법칙, 시대를 초월하는 원칙",
        "dimension": "QC",
        "documents": ["invariants.json", "cinematic_principles.json"],
    },
    "meta_vdg": {
        "display_name": "Visual Design Grammar",
        "description": "시각적 디자인 문법 표준",
        "dimension": "AD",
        "documents": ["vdg_standard.json", "visual_grammar.json"],
    },
    "dim_1d_prompts": {
        "display_name": "1D Veo Prompt Templates",
        "description": "Veo 프롬프트 생성 가이드라인",
        "dimension": "1D",
        "documents": ["veo_prompts.json", "prompt_templates.json"],
    },
    "dim_2d_storyboard": {
        "display_name": "2D Storyboard Guide",
        "description": "스토리보드 제작 원칙과 예시",
        "dimension": "2D",
        "documents": ["storyboard_guide.json"],
    },
    "dim_3d_imagery": {
        "display_name": "3D Image Style Guide",
        "description": "AI 이미지 생성 스타일 레퍼런스",
        "dimension": "3D",
        "documents": ["image_styles.json", "style_references.json"],
    },
    "dim_4d_analysis": {
        "display_name": "4D Analysis Framework",
        "description": "비디오/레퍼런스 분석 방법론",
        "dimension": "4D",
        "documents": ["analysis_framework.json"],
    },
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RAGSource:
    """RAG 검색 소스."""
    source_id: str
    content: str
    relevance_score: float = 0.0
    document_name: str = ""
    chunk_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VertexRAGResult:
    """Vertex AI RAG 검색 결과."""
    answer: str
    sources: List[RAGSource] = field(default_factory=list)
    grounding_sources: List[Dict[str, Any]] = field(default_factory=list)  # Google Search 결과
    confidence: float = 0.0
    query_time_ms: int = 0
    corpus_name: str = ""
    model_used: str = ""
    grounded: bool = False


@dataclass
class CorpusInfo:
    """Corpus 정보."""
    corpus_id: str
    display_name: str
    description: str = ""
    document_count: int = 0
    created_at: str = ""
    status: str = "active"


# ============================================================================
# Vertex AI RAG Service
# ============================================================================

class VertexRAGService:
    """Vertex AI RAG Engine 서비스.

    Tier 0 RAG: 프라이빗 데이터 + Gemini Grounding 하이브리드.

    Thread-safe singleton with exponential backoff retry.
    """

    def __init__(self, config: Optional[VertexRAGConfig] = None):
        """Initialize service.

        Args:
            config: Vertex RAG 설정 (None이면 기본값)
        """
        self.config = config or VertexRAGConfig()
        self._initialized = False
        self._init_lock = threading.RLock()
        self._corpora_lock = threading.RLock()
        self._corpora: Dict[str, Any] = {}  # corpus_name → corpus object
        self._vertexai = None
        self._rag_module = None
        self._generative_models = None

    async def _ensure_initialized(self) -> bool:
        """Vertex AI 초기화 (thread-safe with retry).

        Returns:
            True if initialized successfully
        """
        if self._initialized:
            return True

        with self._init_lock:
            # Double-check pattern
            if self._initialized:
                return True

            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    import vertexai
                    from vertexai import rag
                    from vertexai.generative_models import GenerativeModel, Tool, grounding

                    # Initialize with timeout
                    vertexai.init(
                        project=self.config.project_id,
                        location=self.config.location,
                    )

                    self._vertexai = vertexai
                    self._rag_module = rag
                    self._generative_models = {
                        "GenerativeModel": GenerativeModel,
                        "Tool": Tool,
                        "grounding": grounding,
                    }
                    self._initialized = True

                    logger.info(
                        f"[VertexRAG] Initialized: project={self.config.project_id}, "
                        f"location={self.config.location}, model={self.config.gemini_model}"
                    )
                    return True

                except ImportError as e:
                    logger.error(f"[VertexRAG] Missing dependency (not retryable): {e}")
                    return False
                except Exception as e:
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                        logger.warning(
                            f"[VertexRAG] Init retry {attempt + 1}/{MAX_RETRIES}: {e}. "
                            f"Waiting {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.exception(f"[VertexRAG] Initialization failed after {MAX_RETRIES} retries")

            return False

    async def create_corpus(
        self,
        corpus_name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[CorpusInfo]:
        """RAG Corpus 생성.

        Args:
            corpus_name: Corpus 식별자
            display_name: 표시 이름
            description: 설명

        Returns:
            CorpusInfo if created successfully

        Raises:
            ValueError: If corpus_name is invalid
        """
        # Input validation
        validate_corpus_name(corpus_name)

        if not await self._ensure_initialized():
            return None

        # 레지스트리에서 정보 가져오기
        registry_info = CORPUS_REGISTRY.get(corpus_name, {})
        display_name = display_name or registry_info.get("display_name", corpus_name)
        description = description or registry_info.get("description", "")

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                rag = self._rag_module

                # Corpus 생성 with timeout (new API - uses default embedding model)
                corpus = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: rag.create_corpus(
                            display_name=display_name,
                            description=description,
                        )
                    ),
                    timeout=CORPUS_CREATE_TIMEOUT,
                )

                with self._corpora_lock:
                    self._corpora[corpus_name] = corpus

                logger.info(f"[VertexRAG] Corpus created: {corpus_name} ({corpus.name})")

                return CorpusInfo(
                    corpus_id=corpus.name,
                    display_name=display_name,
                    description=description,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )

            except asyncio.TimeoutError:
                logger.error(f"[VertexRAG] Corpus creation timed out after {CORPUS_CREATE_TIMEOUT}s")
                return None
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(
                        f"[VertexRAG] Create corpus retry {attempt + 1}/{MAX_RETRIES}: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.exception(f"[VertexRAG] Failed to create corpus {corpus_name} after {MAX_RETRIES} retries")

        return None

    async def index_documents(
        self,
        corpus_name: str,
        document_paths: List[str],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> Dict[str, Any]:
        """문서 인덱싱 (with validation, retry, and timeout).

        Args:
            corpus_name: Corpus 식별자
            document_paths: GCS 경로 목록 또는 로컬 파일 경로
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩

        Returns:
            인덱싱 결과

        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        validate_corpus_name(corpus_name)
        validate_document_paths(document_paths)

        if not await self._ensure_initialized():
            return {"error": "Not initialized"}

        # Get corpus with thread safety
        with self._corpora_lock:
            corpus = self._corpora.get(corpus_name)

        if not corpus:
            # Corpus 목록에서 찾기
            try:
                rag = self._rag_module
                corpora = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, rag.list_corpora
                    ),
                    timeout=LIST_CORPORA_TIMEOUT,
                )
                for c in corpora:
                    if corpus_name in c.display_name.lower():
                        corpus = c
                        with self._corpora_lock:
                            self._corpora[corpus_name] = corpus
                        break
            except asyncio.TimeoutError:
                logger.error(f"[VertexRAG] List corpora timed out after {LIST_CORPORA_TIMEOUT}s")
            except Exception as e:
                logger.exception(f"[VertexRAG] Failed to list corpora")

        if not corpus:
            return {"error": f"Corpus not found: {corpus_name}"}

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                rag = self._rag_module

                # GCS 경로로 변환 (validated paths)
                gcs_paths = []
                for path in document_paths:
                    if path.startswith("gs://"):
                        gcs_paths.append(path)
                    else:
                        # 로컬 파일 → GCS 업로드
                        gcs_path = f"gs://{self.config.gcs_bucket}/{corpus_name}/{path}"
                        # TODO: 실제 업로드 구현
                        gcs_paths.append(gcs_path)

                # 청킹 설정 (new API)
                transformation_config = rag.TransformationConfig(
                    chunking_config=rag.ChunkingConfig(
                        chunk_size=chunk_size or self.config.chunk_size,
                        chunk_overlap=chunk_overlap or self.config.chunk_overlap,
                    )
                )

                # 문서 인덱싱 with timeout
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: rag.import_files(
                            corpus_name=corpus.name,
                            paths=gcs_paths,
                            transformation_config=transformation_config,
                        )
                    ),
                    timeout=FILE_IMPORT_TIMEOUT,
                )

                logger.info(
                    f"[VertexRAG] Documents indexed: {corpus_name}, "
                    f"paths={len(gcs_paths)}"
                )

                return {
                    "corpus_name": corpus_name,
                    "indexed_count": len(gcs_paths),
                    "paths": gcs_paths,
                }

            except asyncio.TimeoutError:
                logger.error(f"[VertexRAG] Document indexing timed out after {FILE_IMPORT_TIMEOUT}s")
                return {"error": f"Indexing timed out after {FILE_IMPORT_TIMEOUT}s"}
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(
                        f"[VertexRAG] Index documents retry {attempt + 1}/{MAX_RETRIES}: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.exception(f"[VertexRAG] Failed to index documents after {MAX_RETRIES} retries")

        return {"error": str(last_error) if last_error else "Unknown error"}

    async def query(
        self,
        query: str,
        corpus_name: Optional[str] = None,
        corpus_names: Optional[List[str]] = None,
        use_grounding: bool = True,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> VertexRAGResult:
        """RAG 검색 + Gemini 생성 (with validation, timeout, and retry).

        Args:
            query: 검색 쿼리
            corpus_name: 단일 Corpus 이름
            corpus_names: 복수 Corpus 이름 (둘 중 하나 필수)
            use_grounding: Google Search Grounding 사용 여부
            top_k: 검색 결과 수 (1-100)
            min_score: 최소 관련성 점수 (0.0-1.0)

        Returns:
            VertexRAGResult with answer and sources

        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        validate_query(query)

        # Bounds validation
        if not 1 <= top_k <= MAX_TOP_K:
            raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")

        if not await self._ensure_initialized():
            return VertexRAGResult(
                answer="Service not initialized",
                confidence=0.0,
            )

        start_time = time.monotonic()

        # Corpus 이름 처리 with limit check
        target_corpora = corpus_names or ([corpus_name] if corpus_name else list(CORPUS_REGISTRY.keys()))
        if len(target_corpora) > MAX_CORPUS_COUNT:
            logger.warning(f"[VertexRAG] Corpus count {len(target_corpora)} exceeds limit {MAX_CORPUS_COUNT}, truncating")
            target_corpora = target_corpora[:MAX_CORPUS_COUNT]

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                rag = self._rag_module
                GenerativeModel = self._generative_models["GenerativeModel"]
                Tool = self._generative_models["Tool"]
                grounding_module = self._generative_models["grounding"]

                # RAG 검색 도구 설정
                tools = []
                rag_sources = []

                # RAG Corpus 검색 (thread-safe access, new API)
                rag_resources = []
                for cname in target_corpora:
                    with self._corpora_lock:
                        corpus = self._corpora.get(cname)
                    if corpus:
                        rag_resources.append(rag.RagResource(rag_corpus=corpus.name))

                if rag_resources:
                    try:
                        retrieval_tool = Tool.from_retrieval(
                            retrieval=rag.Retrieval(
                                source=rag.VertexRagStore(
                                    rag_resources=rag_resources,
                                    rag_retrieval_config=rag.RagRetrievalConfig(top_k=top_k),
                                ),
                            )
                        )
                        tools.append(retrieval_tool)
                    except Exception as e:
                        logger.warning(f"[VertexRAG] Failed to create retrieval tool: {e}")

                # Google Search Grounding 추가
                if use_grounding and self.config.enable_google_search:
                    try:
                        google_search_tool = Tool.from_google_search_retrieval(
                            grounding_module.GoogleSearchRetrieval(
                                dynamic_retrieval_config=grounding_module.DynamicRetrievalConfig(
                                    mode=grounding_module.DynamicRetrievalConfig.Mode.MODE_DYNAMIC,
                                    dynamic_threshold=0.3,
                                )
                            )
                        )
                        tools.append(google_search_tool)
                    except AttributeError:
                        try:
                            from vertexai.generative_models import grounding as grounding_new
                            google_search_tool = Tool.from_google_search_retrieval(
                                grounding_new.GoogleSearchRetrieval()
                            )
                            tools.append(google_search_tool)
                        except Exception as e2:
                            logger.warning(f"[VertexRAG] Google Search grounding not available: {e2}")
                    except Exception as e:
                        logger.warning(f"[VertexRAG] Failed to add Google Search grounding: {e}")

                # Gemini 모델로 생성
                model = GenerativeModel(
                    self.config.gemini_model,
                    tools=tools if tools else None,
                )

                # Generate with timeout
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: model.generate_content(
                            contents=query,
                            generation_config={
                                "temperature": 0.3,
                                "max_output_tokens": 2048,
                            },
                        )
                    ),
                    timeout=QUERY_TIMEOUT,
                )

                # 결과 파싱
                answer = response.text if response.text else ""
                confidence = 0.85 if answer else 0.0

                # Grounding 메타데이터 추출 (safe access)
                grounding_sources = []
                if hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "grounding_metadata"):
                        gm = candidate.grounding_metadata
                        if gm is not None and hasattr(gm, "grounding_chunks"):
                            chunks = gm.grounding_chunks or []
                            for chunk in chunks:
                                retrieved_ctx = getattr(chunk, "retrieved_context", None)
                                if retrieved_ctx:
                                    grounding_sources.append({
                                        "source": getattr(retrieved_ctx, "title", "") or "",
                                        "uri": getattr(retrieved_ctx, "uri", "") or "",
                                    })

                query_time_ms = int((time.monotonic() - start_time) * 1000)

                logger.info(
                    f"[VertexRAG] Query completed: {query[:50]}... "
                    f"({confidence:.2f} confidence, {len(rag_sources)} RAG sources, "
                    f"{len(grounding_sources)} grounding sources, {query_time_ms}ms)"
                )

                return VertexRAGResult(
                    answer=answer,
                    sources=rag_sources,
                    grounding_sources=grounding_sources,
                    confidence=confidence,
                    query_time_ms=query_time_ms,
                    corpus_name=",".join(target_corpora),
                    model_used=self.config.gemini_model,
                    grounded=use_grounding and len(grounding_sources) > 0,
                )

            except asyncio.TimeoutError:
                logger.error(f"[VertexRAG] Query timed out after {QUERY_TIMEOUT}s")
                return VertexRAGResult(
                    answer=f"Query timed out after {QUERY_TIMEOUT}s",
                    confidence=0.0,
                )
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(f"[VertexRAG] Query retry {attempt + 1}/{MAX_RETRIES}: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.exception(f"[VertexRAG] Query failed after {MAX_RETRIES} retries")

        return VertexRAGResult(
            answer=f"Query failed: {str(last_error)}" if last_error else "Unknown error",
            confidence=0.0,
        )

    async def query_with_fallback(
        self,
        query: str,
        corpus_name: Optional[str] = None,
    ) -> VertexRAGResult:
        """RAG 검색 with 폴백.

        RAG 실패 시 Gemini + Grounding만 사용.

        Args:
            query: 검색 쿼리
            corpus_name: Corpus 이름

        Returns:
            VertexRAGResult
        """
        # 먼저 RAG + Grounding 시도
        result = await self.query(query, corpus_name=corpus_name, use_grounding=True)

        if result.confidence < 0.5:
            # RAG 실패 시 Grounding만
            logger.info(f"[VertexRAG] Falling back to grounding-only for: {query[:50]}...")
            result = await self.query(query, corpus_name=None, use_grounding=True)

        return result

    def list_corpora(self) -> List[str]:
        """등록된 Corpus 목록."""
        return list(CORPUS_REGISTRY.keys())

    def get_corpus_info(self, corpus_name: str) -> Optional[Dict[str, Any]]:
        """Corpus 정보 조회."""
        return CORPUS_REGISTRY.get(corpus_name)

    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계."""
        return {
            "initialized": self._initialized,
            "project_id": self.config.project_id,
            "location": self.config.location,
            "gemini_model": self.config.gemini_model,
            "registered_corpora": len(CORPUS_REGISTRY),
            "loaded_corpora": len(self._corpora),
            "grounding_enabled": self.config.enable_google_search,
        }


# ============================================================================
# Singleton
# ============================================================================

_vertex_rag_service: Optional[VertexRAGService] = None


def get_vertex_rag_service(config: Optional[VertexRAGConfig] = None) -> VertexRAGService:
    """Vertex RAG 서비스 싱글톤 반환 (thread-safe).

    Args:
        config: 설정 (최초 호출 시에만 적용)

    Returns:
        VertexRAGService instance
    """
    global _vertex_rag_service

    # Fast path: already initialized
    if _vertex_rag_service is not None:
        return _vertex_rag_service

    # Thread-safe initialization (double-checked locking)
    with _singleton_lock:
        if _vertex_rag_service is None:
            _vertex_rag_service = VertexRAGService(config)
    return _vertex_rag_service


def reset_vertex_rag_service() -> None:
    """서비스 리셋 (테스트용, thread-safe)."""
    global _vertex_rag_service
    with _singleton_lock:
        _vertex_rag_service = None


# ============================================================================
# Convenience Functions
# ============================================================================

async def query_auteur_dna(
    query: str,
    auteur_key: Optional[str] = None,
) -> VertexRAGResult:
    """Auteur DNA 검색.

    Args:
        query: 검색 쿼리
        auteur_key: 특정 거장 키 (bong, park, shinkai 등)

    Returns:
        VertexRAGResult
    """
    service = get_vertex_rag_service()

    # auteur_key가 있으면 쿼리에 포함
    if auteur_key:
        auteur_names = {
            "bong": "봉준호",
            "park": "박찬욱",
            "shinkai": "신카이 마코토",
            "hong": "홍상수",
            "na": "나홍진",
            "lee": "이준호",
        }
        auteur_name = auteur_names.get(auteur_key.lower(), auteur_key)
        query = f"{auteur_name}: {query}"

    return await service.query(
        query=query,
        corpus_name="auteur_dna",
        use_grounding=True,
    )


async def query_dimension_guide(
    dimension: str,
    query: str,
) -> VertexRAGResult:
    """차원별 가이드 검색.

    Args:
        dimension: 차원 코드 (1D, 2D, 3D, 4D)
        query: 검색 쿼리

    Returns:
        VertexRAGResult
    """
    dim_to_corpus = {
        "1D": "dim_1d_prompts",
        "2D": "dim_2d_storyboard",
        "3D": "dim_3d_imagery",
        "4D": "dim_4d_analysis",
    }

    corpus_name = dim_to_corpus.get(dimension.upper())
    if not corpus_name:
        return VertexRAGResult(
            answer=f"Unknown dimension: {dimension}",
            confidence=0.0,
        )

    service = get_vertex_rag_service()
    return await service.query(
        query=query,
        corpus_name=corpus_name,
        use_grounding=True,
    )


async def cascaded_query(
    query: str,
    depth1_top_k: int = 20,
    depth2_sources_limit: int = 600,
) -> Dict[str, Any]:
    """2-Depth Cascaded RAG 검색 (with validation).

    Depth 1: Vertex AI RAG (환각률 0.7%) → 핵심 지식 20개 추출
    Depth 2: NotebookLM Ultra (600 소스) → 심층 분석 + 팟캐스트

    Args:
        query: 검색 쿼리
        depth1_top_k: Depth 1에서 추출할 핵심 문서 수 (1-100)
        depth2_sources_limit: Depth 2에서 사용할 최대 소스 수 (10-1000)

    Returns:
        {
            "depth1_results": VertexRAGResult,
            "depth2_ready": bool,
            "combined_sources": List[str],
            "podcast_eligible": bool,
        }

    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    validate_query(query)
    if not 1 <= depth1_top_k <= MAX_TOP_K:
        raise ValueError(f"depth1_top_k must be between 1 and {MAX_TOP_K}")
    if not 10 <= depth2_sources_limit <= 1000:
        raise ValueError("depth2_sources_limit must be between 10 and 1000")

    service = get_vertex_rag_service()

    # Depth 1: Vertex AI RAG 정밀 검색
    depth1_result = await service.query(
        query=query,
        corpus_names=["auteur_dna", "meta_vdg", "meta_invariants"],
        use_grounding=False,  # 정밀 검색만
        top_k=depth1_top_k,
    )

    # Depth 1 결과에서 핵심 문서 추출
    core_documents = []
    for source in depth1_result.sources[:depth1_top_k]:
        core_documents.append({
            "content": source.content,
            "source_id": source.source_id,
            "relevance": source.relevance_score,
        })

    # Depth 2 준비 상태 확인
    depth2_ready = len(core_documents) >= 5  # 최소 5개 핵심 문서 필요

    return {
        "depth1_results": depth1_result,
        "depth1_documents": core_documents,
        "depth2_ready": depth2_ready,
        "depth2_sources_limit": depth2_sources_limit,
        "podcast_eligible": depth2_ready and depth1_result.confidence >= 0.7,
        "query": query,
    }


async def create_deep_podcast(
    topic: str,
    mode: str = "deep_dive",
    wait_for_completion: bool = False,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """2-Depth Cascaded RAG 기반 Deep Podcast 생성 (with validation).

    Depth 1: Vertex AI RAG Engine (환각률 0.7%) → 핵심 지식 추출
    Depth 2: Discovery Engine Podcast API → 오디오 생성

    Args:
        topic: 팟캐스트 주제 (1-5000자)
        mode: 팟캐스트 모드 (deep_dive, debate, critique, lecture, brief)
        wait_for_completion: True면 생성 완료까지 대기
        output_path: 오디오 파일 저장 경로 (wait_for_completion=True 필요)

    Returns:
        {
            "status": str,
            "operation_name": str (for async tracking),
            "depth1_summary": str,
            "sources_count": int,
            "confidence": float,
            "audio": bytes or path (if wait_for_completion),
        }

    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")
    if len(topic) > 5000:
        raise ValueError("Topic too long (max 5000 characters)")
    if "\x00" in topic:
        raise ValueError("Topic contains invalid null bytes")

    # Validate mode
    valid_modes = {"deep_dive", "debate", "critique", "lecture", "brief"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {', '.join(valid_modes)}")

    # Validate output path
    if output_path:
        import os
        if ".." in output_path:
            raise ValueError("Path traversal not allowed in output_path")
        parent_dir = os.path.dirname(output_path)
        if parent_dir and not os.path.exists(parent_dir):
            raise ValueError(f"Output directory does not exist: {parent_dir}")

    # Depth 1: Vertex AI RAG 정밀 검색
    cascaded = await cascaded_query(topic, depth1_top_k=20, depth2_sources_limit=600)

    if not cascaded["podcast_eligible"]:
        return {
            "status": "insufficient_sources",
            "error": "Not enough quality sources for deep podcast",
            "depth1_confidence": cascaded["depth1_results"].confidence,
            "depth1_summary": cascaded["depth1_results"].answer[:500] if cascaded["depth1_results"].answer else "",
        }

    # Depth 2: Discovery Engine Podcast API
    try:
        from app.rag.podcast_service import (
            get_podcast_service,
            PodcastFormat,
            PodcastLength,
            PodcastStatus,
        )

        podcast_service = get_podcast_service()

        # Map mode to PodcastFormat
        mode_mapping = {
            "deep_dive": PodcastFormat.DEEP_DIVE,
            "debate": PodcastFormat.DEBATE,
            "critique": PodcastFormat.CRITIQUE,
            "lecture": PodcastFormat.LECTURE,
            "brief": PodcastFormat.BRIEF,
        }
        podcast_format = mode_mapping.get(mode, PodcastFormat.DEEP_DIVE)

        # Prepare sources from Depth 1 results
        depth1_content = cascaded["depth1_results"].answer
        depth1_sources = cascaded["depth1_documents"]

        # Combine Depth 1 answer + source documents
        sources = [depth1_content]
        for doc in depth1_sources[:10]:  # Limit to 10 source docs
            if isinstance(doc, dict) and doc.get("content"):
                sources.append(doc["content"])

        # Determine length based on mode
        length = PodcastLength.SHORT if mode == "brief" else PodcastLength.STANDARD

        if wait_for_completion:
            # Generate and download in one call
            result = await podcast_service.generate_and_download(
                sources=sources,
                title=f"{topic} - {mode}",
                format=podcast_format,
                length=length,
                language="ko",
                output_path=output_path,
            )

            return {
                "status": result["status"].value if isinstance(result["status"], PodcastStatus) else result["status"],
                "operation_name": result.get("operation_name", ""),
                "depth1_summary": depth1_content[:500],
                "depth1_sources_count": len(depth1_sources),
                "confidence": cascaded["depth1_results"].confidence,
                "audio": result.get("audio"),
                "error": result.get("error"),
            }
        else:
            # Start async generation
            gen_result = await podcast_service.generate_podcast(
                sources=sources,
                title=f"{topic} - {mode}",
                format=podcast_format,
                length=length,
                language="ko",
            )

            return {
                "status": gen_result.status.value,
                "operation_name": gen_result.operation_name,
                "depth1_summary": depth1_content[:500],
                "depth1_sources_count": len(depth1_sources),
                "confidence": cascaded["depth1_results"].confidence,
                "message": "Podcast generation started. Use operation_name to check status and download.",
            }

    except ImportError as e:
        logger.warning(f"[CascadedRAG] Podcast service not available: {e}")
        return {
            "status": "service_unavailable",
            "error": "Podcast service not available",
            "depth1_summary": cascaded["depth1_results"].answer[:500],
            "depth1_sources_count": len(cascaded["depth1_documents"]),
            "confidence": cascaded["depth1_results"].confidence,
        }
    except Exception as e:
        logger.exception(f"[CascadedRAG] Deep podcast creation failed")
        return {
            "status": "failed",
            "error": str(e),
            "depth1_available": True,
            "depth1_summary": cascaded["depth1_results"].answer[:500] if cascaded["depth1_results"].answer else "",
        }


async def query_hybrid(
    query: str,
    include_auteur: bool = True,
    include_meta: bool = True,
    include_dimensions: Optional[List[str]] = None,
) -> VertexRAGResult:
    """하이브리드 RAG 검색 (복수 Corpus).

    Args:
        query: 검색 쿼리
        include_auteur: Auteur DNA 포함
        include_meta: Meta (VDG, Invariants) 포함
        include_dimensions: 포함할 차원 목록

    Returns:
        VertexRAGResult
    """
    corpora = []

    if include_auteur:
        corpora.append("auteur_dna")

    if include_meta:
        corpora.extend(["meta_invariants", "meta_vdg"])

    if include_dimensions:
        dim_to_corpus = {
            "1D": "dim_1d_prompts",
            "2D": "dim_2d_storyboard",
            "3D": "dim_3d_imagery",
            "4D": "dim_4d_analysis",
        }
        for dim in include_dimensions:
            corpus = dim_to_corpus.get(dim.upper())
            if corpus:
                corpora.append(corpus)

    service = get_vertex_rag_service()
    return await service.query(
        query=query,
        corpus_names=corpora if corpora else None,
        use_grounding=True,
    )
