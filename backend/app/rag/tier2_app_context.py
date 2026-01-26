"""Tier 2: App-specific Context Loader.

앱별 문서 및 컨텍스트 로딩.
- JSON 문서 파일 로딩
- PDF 파싱 (PyMuPDF)
- 메타데이터 필터링
- 차원별 문서 관리

Usage:
    from app.rag.tier2_app_context import get_app_context_loader

    loader = get_app_context_loader()

    # 앱별 컨텍스트 로드
    docs = await loader.load_app_context("dimension.aesthetic.direct")

    # 차원별 문서 로드
    docs = await loader.load_dimension_docs("AD")
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# 기본 문서 디렉토리 경로
DEFAULT_DOCS_DIR = Path(__file__).parent.parent.parent / "data" / "rag_docs"

# 문서 타입 정의
DOCUMENT_TYPES = {
    ".json": "json",
    ".pdf": "pdf",
    ".md": "markdown",
    ".txt": "text",
}


@dataclass
class DocumentConfig:
    """문서 설정."""
    docs_dir: Path = field(default_factory=lambda: DEFAULT_DOCS_DIR)
    max_file_size_mb: int = 10
    supported_extensions: Set[str] = field(
        default_factory=lambda: {".json", ".pdf", ".md", ".txt"}
    )
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


# ============================================================================
# Document Models
# ============================================================================

@dataclass
class AppDocument:
    """앱 문서."""
    doc_id: str
    title: str
    content: str
    doc_type: str  # json, pdf, markdown, text
    app_key: Optional[str] = None
    dimension: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type,
            "app_key": self.app_key,
            "dimension": self.dimension,
            "metadata": self.metadata,
            "file_path": self.file_path,
        }


@dataclass
class DocumentCollection:
    """문서 컬렉션."""
    collection_id: str
    documents: List[AppDocument] = field(default_factory=list)
    dimension: Optional[str] = None
    app_key: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_content_length(self) -> int:
        """총 콘텐츠 길이."""
        return sum(len(doc.content) for doc in self.documents)

    def get_combined_content(self, separator: str = "\n\n---\n\n") -> str:
        """모든 문서 콘텐츠 결합."""
        return separator.join(doc.content for doc in self.documents)


# ============================================================================
# Document Loaders
# ============================================================================

def _load_json_document(file_path: Path) -> Dict[str, Any]:
    """JSON 문서 로드."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_text_document(file_path: Path) -> str:
    """텍스트 문서 로드."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _load_pdf_document(file_path: Path) -> str:
    """PDF 문서 로드 (PyMuPDF 사용)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n\n".join(text_parts)
    except ImportError:
        logger.warning(
            "[Tier2] PyMuPDF not installed. PDF parsing disabled. "
            "Install with: pip install pymupdf"
        )
        return f"[PDF content from {file_path.name} - PyMuPDF required]"
    except Exception as e:
        logger.error(f"[Tier2] PDF loading error: {e}")
        return f"[Error loading PDF: {e}]"


# ============================================================================
# App-Dimension Mapping
# ============================================================================

# 앱 키 → 차원 매핑
APP_DIMENSION_MAP: Dict[str, str] = {
    # Teaching/Dimension capsules
    "teaching.prompt.generate": "1D",
    "teaching.storyboard.create": "2D",
    "teaching.image.generate": "3D",
    "teaching.reference.analyze": "4D",
    # Dimension-specific capsules
    "dimension.quality.check": "QC",
    "dimension.aesthetic.direct": "AD",
    "dimension.persona.analyze": "AI",
    # Veo
    "veo.video.generate": "VEO",
}

# 차원 → 문서 디렉토리 매핑
DIMENSION_DOCS_MAP: Dict[str, str] = {
    "1D": "origin",      # Veo Prompt
    "2D": "blueprint",   # Storyboard
    "3D": "ambience",    # Image
    "4D": "moment",      # Video/Analysis
    "AD": "aesthetic",   # Aesthetic Director
    "QC": "quality",     # Quality Checker
    "AI": "persona",     # Persona Analyzer
    "VEO": "veo",        # Veo templates
}


# ============================================================================
# Document Registry (어떤 문서가 어떤 앱/차원에 필요한지)
# ============================================================================

DOCUMENT_REGISTRY: Dict[str, List[str]] = {
    # Aesthetic Director 문서
    "dimension.aesthetic.direct": [
        "aesthetic/auteur_styles.json",
        "aesthetic/vdg_standards.json",
        "aesthetic/color_theory.json",
    ],
    # Quality Checker 문서
    "dimension.quality.check": [
        "quality/quality_criteria.json",
        "quality/brand_safety.json",
    ],
    # 1D Prompt 문서
    "teaching.prompt.generate": [
        "origin/veo_prompt_templates.json",
        "origin/cinematic_language.json",
    ],
    # 2D Storyboard 문서
    "teaching.storyboard.create": [
        "blueprint/storyboard_formats.json",
        "blueprint/shot_types.json",
    ],
    # 3D Image 문서
    "teaching.image.generate": [
        "ambience/image_styles.json",
        "ambience/composition_rules.json",
    ],
    # 4D Analysis 문서
    "teaching.reference.analyze": [
        "moment/analysis_frameworks.json",
        "moment/cinematic_techniques.json",
    ],
}


# ============================================================================
# App Context Loader
# ============================================================================

class AppContextLoader:
    """앱별 컨텍스트 로더.

    Tier 2: 메타데이터 필터링 기반 문서 로딩.
    """

    def __init__(self, config: Optional[DocumentConfig] = None):
        """Initialize loader.

        Args:
            config: 문서 설정
        """
        self.config = config or DocumentConfig()
        self._cache: Dict[str, DocumentCollection] = {}
        self._ensure_docs_dir()

    def _ensure_docs_dir(self) -> None:
        """문서 디렉토리 확인 및 생성."""
        if not self.config.docs_dir.exists():
            logger.info(f"[Tier2] Creating docs directory: {self.config.docs_dir}")
            self.config.docs_dir.mkdir(parents=True, exist_ok=True)

            # 하위 디렉토리 생성
            for dim_dir in DIMENSION_DOCS_MAP.values():
                (self.config.docs_dir / dim_dir).mkdir(exist_ok=True)

    def _get_cache_key(self, identifier: str) -> str:
        """캐시 키 생성."""
        return f"ctx:{identifier}"

    def _is_cache_valid(self, key: str) -> bool:
        """캐시 유효성 확인."""
        if not self.config.cache_enabled:
            return False
        if key not in self._cache:
            return False
        collection = self._cache[key]
        age = (datetime.utcnow() - collection.loaded_at).total_seconds()
        return age < self.config.cache_ttl_seconds

    async def load_app_context(
        self,
        app_key: str,
        force_reload: bool = False,
    ) -> DocumentCollection:
        """앱별 컨텍스트 로드.

        Args:
            app_key: 앱 식별자
            force_reload: 캐시 무시

        Returns:
            DocumentCollection with loaded documents
        """
        cache_key = self._get_cache_key(app_key)

        # 캐시 확인
        if not force_reload and self._is_cache_valid(cache_key):
            logger.debug(f"[Tier2] Cache hit for app: {app_key}")
            return self._cache[cache_key]

        # 문서 목록 조회
        doc_paths = DOCUMENT_REGISTRY.get(app_key, [])
        dimension = APP_DIMENSION_MAP.get(app_key)

        documents: List[AppDocument] = []

        for rel_path in doc_paths:
            full_path = self.config.docs_dir / rel_path
            if not full_path.exists():
                logger.warning(f"[Tier2] Document not found: {full_path}")
                continue

            try:
                doc = await self._load_document(full_path, app_key, dimension)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"[Tier2] Error loading {full_path}: {e}")

        collection = DocumentCollection(
            collection_id=f"app:{app_key}",
            documents=documents,
            dimension=dimension,
            app_key=app_key,
        )

        # 캐시 저장
        if self.config.cache_enabled:
            self._cache[cache_key] = collection

        logger.info(
            f"[Tier2] Loaded {len(documents)} documents for app: {app_key}"
        )

        return collection

    async def load_dimension_docs(
        self,
        dimension: str,
        force_reload: bool = False,
    ) -> DocumentCollection:
        """차원별 문서 로드.

        Args:
            dimension: 차원 코드
            force_reload: 캐시 무시

        Returns:
            DocumentCollection
        """
        cache_key = self._get_cache_key(f"dim:{dimension}")

        if not force_reload and self._is_cache_valid(cache_key):
            logger.debug(f"[Tier2] Cache hit for dimension: {dimension}")
            return self._cache[cache_key]

        # 차원 디렉토리 확인
        dim_dir_name = DIMENSION_DOCS_MAP.get(dimension)
        if not dim_dir_name:
            logger.warning(f"[Tier2] Unknown dimension: {dimension}")
            return DocumentCollection(
                collection_id=f"dim:{dimension}",
                dimension=dimension,
            )

        dim_dir = self.config.docs_dir / dim_dir_name
        if not dim_dir.exists():
            logger.warning(f"[Tier2] Dimension directory not found: {dim_dir}")
            return DocumentCollection(
                collection_id=f"dim:{dimension}",
                dimension=dimension,
            )

        # 디렉토리 내 모든 문서 로드
        documents: List[AppDocument] = []
        for file_path in dim_dir.iterdir():
            if file_path.suffix not in self.config.supported_extensions:
                continue
            try:
                doc = await self._load_document(file_path, None, dimension)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"[Tier2] Error loading {file_path}: {e}")

        collection = DocumentCollection(
            collection_id=f"dim:{dimension}",
            documents=documents,
            dimension=dimension,
        )

        if self.config.cache_enabled:
            self._cache[cache_key] = collection

        logger.info(
            f"[Tier2] Loaded {len(documents)} documents for dimension: {dimension}"
        )

        return collection

    async def _load_document(
        self,
        file_path: Path,
        app_key: Optional[str],
        dimension: Optional[str],
    ) -> Optional[AppDocument]:
        """단일 문서 로드.

        Args:
            file_path: 파일 경로
            app_key: 앱 키
            dimension: 차원

        Returns:
            AppDocument or None
        """
        # 파일 크기 확인
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            logger.warning(
                f"[Tier2] File too large ({file_size_mb:.1f}MB): {file_path}"
            )
            return None

        suffix = file_path.suffix.lower()
        doc_type = DOCUMENT_TYPES.get(suffix, "text")

        # 파일 타입별 로딩
        if doc_type == "json":
            data = _load_json_document(file_path)
            content = json.dumps(data, ensure_ascii=False, indent=2)
            metadata = data if isinstance(data, dict) else {"data": data}
            title = metadata.get("title", file_path.stem)
        elif doc_type == "pdf":
            content = _load_pdf_document(file_path)
            metadata = {}
            title = file_path.stem
        else:
            content = _load_text_document(file_path)
            metadata = {}
            title = file_path.stem

        return AppDocument(
            doc_id=f"{app_key or dimension or 'doc'}:{file_path.stem}",
            title=title,
            content=content,
            doc_type=doc_type,
            app_key=app_key,
            dimension=dimension,
            metadata=metadata,
            file_path=str(file_path),
        )

    async def load_auteur_styles(self) -> Dict[str, Any]:
        """Auteur 스타일 문서 로드.

        Returns:
            Auteur 스타일 딕셔너리
        """
        file_path = self.config.docs_dir / "aesthetic" / "auteur_styles.json"
        if not file_path.exists():
            logger.warning(f"[Tier2] Auteur styles not found: {file_path}")
            return self._get_default_auteur_styles()

        try:
            return _load_json_document(file_path)
        except Exception as e:
            logger.error(f"[Tier2] Error loading auteur styles: {e}")
            return self._get_default_auteur_styles()

    def _get_default_auteur_styles(self) -> Dict[str, Any]:
        """기본 Auteur 스타일."""
        return {
            "bong": {
                "name": "강주노 (Bong Joon-ho)",
                "signature": "Structural tension, genre mixing, controlled camera",
                "palette_bias": "cool",
                "techniques": ["deep focus", "tracking shots", "visual metaphor"],
            },
            "park": {
                "name": "박찬욱 (Park Chan-wook)",
                "signature": "Symmetry, high contrast, precise framing",
                "palette_bias": "warm",
                "techniques": ["split screen", "extreme close-up", "slow motion"],
            },
            "shinkai": {
                "name": "신카이 마코토 (Shinkai Makoto)",
                "signature": "Light diffusion, lyrical colors, emotional atmosphere",
                "palette_bias": "warm",
                "techniques": ["lens flare", "sky gradients", "detailed backgrounds"],
            },
            "lee": {
                "name": "이준호 (Lee Jun-ho)",
                "signature": "Music sync, rhythmic editing, dynamic camera",
                "palette_bias": "neutral",
                "techniques": ["match cuts", "montage", "handheld"],
            },
            "na": {
                "name": "나홍진 (Na Hong-jin)",
                "signature": "Raw realism, suspense, chaotic camera",
                "palette_bias": "cool",
                "techniques": ["long takes", "natural lighting", "documentary style"],
            },
            "hong": {
                "name": "홍상수 (Hong Sang-soo)",
                "signature": "Static camera, dialogue-driven, minimalist",
                "palette_bias": "neutral",
                "techniques": ["zoom", "static shots", "natural sound"],
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """로더 통계."""
        return {
            "docs_dir": str(self.config.docs_dir),
            "cache_size": len(self._cache),
            "cache_enabled": self.config.cache_enabled,
            "registered_apps": list(DOCUMENT_REGISTRY.keys()),
            "dimensions": list(DIMENSION_DOCS_MAP.keys()),
        }

    def clear_cache(self) -> None:
        """캐시 클리어."""
        self._cache.clear()


# ============================================================================
# Singleton
# ============================================================================

_app_context_loader: Optional[AppContextLoader] = None


def get_app_context_loader(
    config: Optional[DocumentConfig] = None,
) -> AppContextLoader:
    """앱 컨텍스트 로더 싱글톤 반환.

    Args:
        config: 설정 (최초 호출 시에만 적용)

    Returns:
        AppContextLoader instance
    """
    global _app_context_loader
    if _app_context_loader is None:
        _app_context_loader = AppContextLoader(config)
    return _app_context_loader


def reset_app_context_loader() -> None:
    """로더 리셋 (테스트용)."""
    global _app_context_loader
    _app_context_loader = None
