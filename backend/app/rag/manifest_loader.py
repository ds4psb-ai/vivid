"""
YAML Manifest Loader.

YAML 파일 기반 앱 RAG 설정 로딩 및 Pydantic 검증.
기존 app_manifest.py와 호환성 유지 (점진적 마이그레이션).

"앱 추가 = YAML 1개 추가" (코드 수정 0)

Usage:
    from app.rag.manifest_loader import load_manifest, get_manifest

    manifest = get_manifest("dimension.aesthetic.direct")
    print(manifest.dimensions)  # ["AD", "1D", "3D"]

Hot Reload:
    from app.rag.manifest_loader import reload_manifests
    count = reload_manifests()  # Re-scan YAML files
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# Manifest cache
_manifest_cache: Dict[str, "YAMLManifest"] = {}
_loaded = False


# ============================================================================
# Pydantic Models
# ============================================================================


class BackendConfig(BaseModel):
    """백엔드 설정 (P2 Feature).

    Attributes:
        id: 백엔드 식별자 (qdrant_hybrid, notebooklm, vertex_grounding)
        weight: RRF 융합 시 가중치 (0.0 ~ 1.0)
        enabled: 활성화 여부
        config: 백엔드별 추가 설정
    """

    id: str
    weight: float = Field(default=1.0, ge=0, le=1)
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class RerankerConfig(BaseModel):
    """리랭커 설정 (P4 Feature).

    Attributes:
        enabled: 리랭킹 활성화 여부
        backend: 리랭커 백엔드 ID (vertex, local_cross_encoder)
        config: 리랭커별 추가 설정 (model, top_k, min_score)
    """

    enabled: bool = False
    backend: str = "local_cross_encoder"
    config: Dict[str, Any] = Field(default_factory=dict)

    @property
    def model(self) -> str:
        """리랭커 모델 이름."""
        return self.config.get("model", "bge-base")

    @property
    def top_k(self) -> int:
        """리랭킹 후 반환할 문서 수."""
        return self.config.get("top_k", 5)

    @property
    def min_score(self) -> float:
        """최소 리랭크 스코어."""
        return self.config.get("min_score", 0.0)


class RoutingManifestConfig(BaseModel):
    """P5 Adaptive RAG 라우팅 설정.

    Attributes:
        enabled: P5 Adaptive RAG 활성화 여부
        semantic_threshold: SemanticRouter 최소 신뢰도 임계값
        llm_fallback: LLM Classifier 폴백 활성화 여부
        skip_retrieval_types: 검색을 생략할 쿼리 유형 목록
        cache_embeddings: Route examples 임베딩 캐싱 여부
    """

    enabled: bool = True
    semantic_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    llm_fallback: bool = True
    skip_retrieval_types: List[str] = Field(
        default_factory=lambda: ["simple_factual", "creative"]
    )
    cache_embeddings: bool = True

    def to_routing_config(self) -> "RoutingConfig":
        """query_classifier.RoutingConfig로 변환."""
        from app.rag.query_classifier import QueryType, RoutingConfig

        skip_types = []
        for type_str in self.skip_retrieval_types:
            try:
                skip_types.append(QueryType(type_str))
            except ValueError:
                pass

        return RoutingConfig(
            enabled=self.enabled,
            semantic_threshold=self.semantic_threshold,
            llm_fallback=self.llm_fallback,
            skip_retrieval_types=skip_types,
            cache_embeddings=self.cache_embeddings,
        )


# ============================================================================
# UQSL Configuration Models (2026 Best Practice)
# ============================================================================


class UQSLMultiGenerateConfig(BaseModel):
    """UQSL Multi-Generate configuration."""

    candidates: int = Field(default=3, ge=1, le=5)
    parallel: bool = True
    diversity_factor: float = Field(default=0.3, ge=0.0, le=1.0)
    timeout_per_candidate_ms: int = Field(default=30000, ge=1000, le=60000)


class UQSLQualityWeights(BaseModel):
    """Quality dimension weights (should sum to 1.0)."""

    groundedness: float = Field(default=0.30, ge=0.0, le=1.0)
    relevance: float = Field(default=0.25, ge=0.0, le=1.0)
    coherence: float = Field(default=0.20, ge=0.0, le=1.0)
    creativity: float = Field(default=0.15, ge=0.0, le=1.0)
    safety: float = Field(default=0.10, ge=0.0, le=1.0)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for use in QualityScore."""
        return {
            "groundedness": self.groundedness,
            "relevance": self.relevance,
            "coherence": self.coherence,
            "creativity": self.creativity,
            "safety": self.safety,
        }


class UQSLSelectionConfig(BaseModel):
    """Selection strategy configuration."""

    strategy: str = Field(default="auto")  # auto, hitl, hybrid, llm_judge
    auto_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    top_k_for_hitl: int = Field(default=2, ge=2, le=5)


class UQSLBanditConfig(BaseModel):
    """Thompson Sampling bandit configuration."""

    enabled: bool = True
    arms: List[str] = Field(
        default_factory=lambda: ["backend:qdrant_hybrid", "backend:notebooklm"]
    )
    min_exploration_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    decay_factor: float = Field(default=0.99, ge=0.9, le=1.0)


class UQSLEnsemblePlusPlusConfig(BaseModel):
    """Ensemble++ 3-way comparison configuration."""

    enabled: bool = False
    backend_a: str = "qdrant_hybrid"
    backend_b: str = "notebooklm"
    merge_strategy: str = "concat"  # concat, interleave, weighted, llm_fuse


class UQSLFeedbackConfig(BaseModel):
    """Feedback collection configuration."""

    enabled: bool = True
    implicit: bool = True
    explicit: bool = True
    bigquery_sync: bool = False
    sync_interval_seconds: int = Field(default=300, ge=60, le=3600)


class UQSLConfig(BaseModel):
    """UQSL (Universal Quality Selection Layer) configuration.

    2026 Best Practice: Full UQSL configuration from _uqsl_schema.yaml.

    Attributes:
        enabled: Enable UQSL quality selection
        tier: UQSL tier (free, premium, dev)
        multi_generate: Multi-candidate generation config
        quality_weights: Quality dimension weights
        selection: Selection strategy config
        bandit: Thompson Sampling config
        ensemble_plus_plus: Ensemble++ 3-way config
        feedback: Feedback collection config
    """

    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    tier: str = Field(default="free")  # free, premium, dev

    multi_generate: Optional[UQSLMultiGenerateConfig] = None
    quality_weights: Optional[UQSLQualityWeights] = None
    selection: Optional[UQSLSelectionConfig] = None
    bandit: Optional[UQSLBanditConfig] = None
    ensemble_plus_plus: Optional[UQSLEnsemblePlusPlusConfig] = None
    feedback: Optional[UQSLFeedbackConfig] = None

    def model_post_init(self, __context: Any) -> None:
        """Set defaults for nested configs."""
        if self.enabled:
            if self.multi_generate is None:
                self.multi_generate = UQSLMultiGenerateConfig()
            if self.quality_weights is None:
                self.quality_weights = UQSLQualityWeights()
            if self.selection is None:
                self.selection = UQSLSelectionConfig()
            if self.bandit is None:
                self.bandit = UQSLBanditConfig()
            if self.feedback is None:
                self.feedback = UQSLFeedbackConfig()


class DatasetRoutingRule(BaseModel):
    """Dataset 라우팅 규칙."""

    pattern: str
    datasets: List[str]


class DatasetRouting(BaseModel):
    """Dataset 라우팅 설정 (P1 Feature)."""

    model_config = ConfigDict(extra="allow")

    candidates: List[str] = Field(default_factory=list)
    rules: List[DatasetRoutingRule] = Field(default_factory=list)
    default: str = ""
    max_select: int = 2
    labels: Dict[str, str] = Field(default_factory=dict)
    cross_template: str = ""

    def select_datasets(self, query: str) -> List[str]:
        """쿼리 기반 dataset 선택.

        Args:
            query: 검색 쿼리

        Returns:
            선택된 dataset_id 목록 (최대 max_select개)
        """
        if not self.candidates:
            return []

        selected = []
        query_lower = query.lower()

        # 규칙 기반 매칭
        for rule in self.rules:
            try:
                if re.search(rule.pattern, query_lower, re.IGNORECASE):
                    selected.extend(rule.datasets)
            except re.error as e:
                logger.warning(f"[DatasetRouting] Invalid regex '{rule.pattern}': {e}")

        # 중복 제거 + 제한
        selected = list(dict.fromkeys(selected))[: self.max_select]

        # Fallback: 매칭 없으면 기본값
        if not selected:
            fallback = self.default or (self.candidates[0] if self.candidates else None)
            if fallback:
                selected = [fallback]
                logger.debug(f"[DatasetRouting] No rules matched, using fallback: {fallback}")

        return selected


class YAMLManifest(BaseModel):
    """YAML 기반 앱 RAG 매니페스트.

    기존 AppRAGManifest와 호환되는 필드 구조.

    Attributes:
        app_key: 고유 앱 식별자
        version: 매니페스트 버전
        description: 앱 설명
        dimensions: 검색할 차원 목록
        search_limit: 각 차원에서 검색할 최대 문서 수
        min_score: 최소 유사도 점수
        amplify_with_history: 이전 단계 이력 포함 여부
        prompt_injection_template: RAG 결과 프롬프트 주입 템플릿
        fallback_enabled: RAG 실패 시 폴백 동작 활성화
        metadata_filters: 추가 메타데이터 필터 조건
        dataset_routing: P1 Dataset 라우팅 설정
    """

    model_config = ConfigDict(
        extra="allow",  # 추가 필드 허용 (확장성)
        str_strip_whitespace=True,
    )

    app_key: str
    version: str = "1.0"
    description: str = ""
    dimensions: List[str] = Field(default_factory=lambda: ["1D"])
    search_limit: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.5, ge=0, le=1)
    amplify_with_history: bool = True
    prompt_injection_template: str = ""
    fallback_enabled: bool = True
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    dataset_routing: Optional[DatasetRouting] = None

    # P2: Backend 설정
    backends: List[BackendConfig] = Field(default_factory=list)

    # P4: Reranker 설정
    reranker: Optional[RerankerConfig] = None

    # P5: Routing 설정 (Adaptive RAG)
    routing: Optional["RoutingManifestConfig"] = None

    # UQSL: Universal Quality Selection Layer (2026)
    quality_selection: Optional[UQSLConfig] = None

    # Legacy compatibility fields (from AppRAGManifest)
    dataset_candidates: List[str] = Field(default_factory=list)
    dataset_selection_rules: Dict[str, List[str]] = Field(default_factory=dict)
    max_datasets: int = 2
    default_dataset: str = ""
    cross_dataset_template: str = ""
    dataset_labels: Dict[str, str] = Field(default_factory=dict)

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: List[str]) -> List[str]:
        """차원 값 검증."""
        valid = {"1D", "2D", "3D", "4D", "5D", "6D", "QC", "AD", "AI", "VEO"}
        for dim in v:
            if dim.upper() not in valid:
                raise ValueError(f"Invalid dimension: {dim}. Valid: {valid}")
        return [d.upper() for d in v]

    @field_validator("app_key")
    @classmethod
    def validate_app_key(cls, v: str) -> str:
        """앱 키 형식 검증."""
        parts = v.split(".")
        if len(parts) < 2:
            raise ValueError(f"app_key must have at least 2 parts: {v}")
        return v

    def model_post_init(self, __context: Any) -> None:
        """기본 프롬프트 템플릿 설정 및 호환성 변환."""
        if not self.prompt_injection_template:
            self.prompt_injection_template = """
## Reference Context (Retrieved from Knowledge Base)
{rag_results}

Use the above context to enhance your response quality and consistency.
"""

        # dataset_routing -> legacy fields 호환성 변환
        if self.dataset_routing:
            if not self.dataset_candidates:
                self.dataset_candidates = self.dataset_routing.candidates
            if not self.dataset_selection_rules and self.dataset_routing.rules:
                self.dataset_selection_rules = {
                    rule.pattern: rule.datasets for rule in self.dataset_routing.rules
                }
            if not self.default_dataset:
                self.default_dataset = self.dataset_routing.default
            if not self.max_datasets:
                self.max_datasets = self.dataset_routing.max_select
            if not self.dataset_labels:
                self.dataset_labels = self.dataset_routing.labels
            if not self.cross_dataset_template:
                self.cross_dataset_template = self.dataset_routing.cross_template

    def select_datasets(self, query: str) -> List[str]:
        """쿼리 기반 dataset 선택 (convenience method).

        Args:
            query: 검색 쿼리

        Returns:
            선택된 dataset_id 목록
        """
        if self.dataset_routing:
            return self.dataset_routing.select_datasets(query)

        # Legacy fallback
        if not self.dataset_candidates:
            return []

        selected = []
        query_lower = query.lower()

        for pattern, datasets in self.dataset_selection_rules.items():
            try:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    selected.extend(datasets)
            except re.error:
                pass

        selected = list(dict.fromkeys(selected))[: self.max_datasets]

        if not selected:
            fallback = self.default_dataset or (
                self.dataset_candidates[0] if self.dataset_candidates else None
            )
            if fallback:
                selected = [fallback]

        return selected


# ============================================================================
# Loader Functions
# ============================================================================


def _get_manifests_dir() -> Path:
    """매니페스트 디렉토리 경로 반환."""
    return Path(__file__).parent / "manifests"


def _load_all_manifests() -> None:
    """모든 YAML 매니페스트 로드 (캐시)."""
    global _loaded, _manifest_cache

    if _loaded:
        return

    manifest_dir = _get_manifests_dir()
    if not manifest_dir.exists():
        logger.warning(f"[ManifestLoader] Directory not found: {manifest_dir}")
        _loaded = True
        return

    for yaml_file in manifest_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue  # _schema.yaml 등 스킵

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "app_key" not in data:
                logger.warning(f"[ManifestLoader] Invalid manifest: {yaml_file}")
                continue

            manifest = YAMLManifest.model_validate(data)
            _manifest_cache[manifest.app_key] = manifest
            logger.debug(f"[ManifestLoader] Loaded: {manifest.app_key}")

        except Exception as e:
            logger.error(f"[ManifestLoader] Failed to load {yaml_file}: {e}")

    logger.info(f"[ManifestLoader] Loaded {len(_manifest_cache)} YAML manifests")
    _loaded = True


def _convert_legacy_manifest(legacy: "AppRAGManifest") -> YAMLManifest:
    """기존 AppRAGManifest를 YAMLManifest로 변환.

    Args:
        legacy: 기존 dataclass 매니페스트

    Returns:
        YAMLManifest 인스턴스
    """
    # DatasetRouting 변환
    dataset_routing = None
    if legacy.dataset_candidates:
        rules = [
            DatasetRoutingRule(pattern=pattern, datasets=datasets)
            for pattern, datasets in legacy.dataset_selection_rules.items()
        ]
        dataset_routing = DatasetRouting(
            candidates=legacy.dataset_candidates,
            rules=rules,
            default=legacy.default_dataset,
            max_select=legacy.max_datasets,
            labels=legacy.dataset_labels,
            cross_template=legacy.cross_dataset_template,
        )

    return YAMLManifest(
        app_key=legacy.app_key,
        dimensions=legacy.dimensions,
        search_limit=legacy.search_limit,
        min_score=legacy.min_score,
        amplify_with_history=legacy.amplify_with_history,
        prompt_injection_template=legacy.prompt_injection_template,
        fallback_enabled=legacy.fallback_enabled,
        metadata_filters=legacy.metadata_filters,
        dataset_routing=dataset_routing,
        # Legacy fields (직접 복사)
        dataset_candidates=legacy.dataset_candidates,
        dataset_selection_rules=legacy.dataset_selection_rules,
        max_datasets=legacy.max_datasets,
        default_dataset=legacy.default_dataset,
        cross_dataset_template=legacy.cross_dataset_template,
        dataset_labels=legacy.dataset_labels,
    )


def get_manifest(app_key: str) -> Optional[YAMLManifest]:
    """앱 키로 매니페스트 조회.

    YAML 캐시에서 먼저 조회하고, 없으면 기존 APP_MANIFESTS에서 조회 (호환성).

    Args:
        app_key: 앱 식별자

    Returns:
        YAMLManifest or None if not found
    """
    _load_all_manifests()

    # 1. YAML 캐시에서 조회
    if app_key in _manifest_cache:
        return _manifest_cache[app_key]

    # 2. 기존 APP_MANIFESTS 폴백 (호환성)
    try:
        from app.rag.app_manifest import APP_MANIFESTS

        old_manifest = APP_MANIFESTS.get(app_key)
        if old_manifest:
            return _convert_legacy_manifest(old_manifest)
    except ImportError:
        pass

    return None


def list_manifests() -> List[str]:
    """등록된 모든 매니페스트 app_key 목록.

    Returns:
        정렬된 app_key 목록 (YAML + legacy 통합)
    """
    _load_all_manifests()

    # YAML + 기존 APP_MANIFESTS 통합
    all_keys = set(_manifest_cache.keys())

    try:
        from app.rag.app_manifest import APP_MANIFESTS

        all_keys |= set(APP_MANIFESTS.keys())
    except ImportError:
        pass

    return sorted(all_keys)


def reload_manifests() -> int:
    """매니페스트 캐시 리로드 (hot-reload용).

    Returns:
        로드된 YAML 매니페스트 수
    """
    global _loaded, _manifest_cache
    _loaded = False
    _manifest_cache.clear()
    _load_all_manifests()
    return len(_manifest_cache)


def get_dimensions_for_app(app_key: str) -> List[str]:
    """앱에서 사용하는 차원 목록 반환.

    Args:
        app_key: 앱 식별자

    Returns:
        차원 목록 (기본: ["1D"])
    """
    manifest = get_manifest(app_key)
    return manifest.dimensions if manifest else ["1D"]


def list_apps_by_dimension(dimension: str) -> List[str]:
    """특정 차원을 사용하는 모든 앱 목록 반환.

    Args:
        dimension: 차원 ID (예: "AD", "VEO")

    Returns:
        해당 차원을 사용하는 앱 키 목록
    """
    _load_all_manifests()

    apps = []
    dim_upper = dimension.upper()

    # YAML manifests
    for app_key, manifest in _manifest_cache.items():
        if dim_upper in manifest.dimensions:
            apps.append(app_key)

    # Legacy manifests
    try:
        from app.rag.app_manifest import APP_MANIFESTS

        for app_key, manifest in APP_MANIFESTS.items():
            if app_key not in apps and dim_upper in manifest.dimensions:
                apps.append(app_key)
    except ImportError:
        pass

    return sorted(apps)


# ============================================================================
# Type alias for backward compatibility
# ============================================================================

# Allow importing AppRAGManifest-like type from this module
AppManifest = YAMLManifest
