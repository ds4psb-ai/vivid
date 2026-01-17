"""Tool Capability Registry (P0 2026).

도구 역량 레지스트리 - 도구 등록, 조회, 의존성 분석.

Reference:
    - LangGraph Tool Registry: https://docs.langchain.com/oss/python/langchain
    - Temporal Workflow Registry: https://temporal.io/workflows

Usage:
    from app.workflow.registry import get_tool_registry, ToolCapabilityRegistry

    registry = get_tool_registry()

    # Register a tool
    registry.register(ToolCapability(
        tool_id="reference_decoder",
        ...
    ))

    # Query tools
    tools = registry.get_by_dimension("4D")
    compatible = registry.find_compatible_tools(input_types={DataType.VIDEO_URL})
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from app.workflow.types import (
    DataType,
    ToolCapability,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Capability Registry
# =============================================================================

class ToolCapabilityRegistry:
    """도구 역량 레지스트리.

    도구의 역량 정보를 관리하고, 의존성 그래프를 구축합니다.
    싱글톤 패턴으로 전역 레지스트리 제공.

    Thread-Safety:
        asyncio.Lock을 사용하여 비동기 환경에서 안전합니다.

    Example:
        >>> registry = get_tool_registry()
        >>> registry.register(ToolCapability(
        ...     tool_id="reference_decoder",
        ...     display_name="레퍼런스 해석기",
        ...     dimension="4D",
        ...     can_consume={DataType.VIDEO_URL, DataType.TEXT},
        ...     can_provide={DataType.ANALYSIS_RESULT, DataType.STYLE_HINT},
        ... ))
        >>> tools = registry.find_compatible_tools({DataType.VIDEO_URL})
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._tools: Dict[str, ToolCapability] = {}
        self._lock = asyncio.Lock()

        # Indexes for fast lookup
        self._by_dimension: Dict[str, Set[str]] = {}
        self._by_can_consume: Dict[DataType, Set[str]] = {}
        self._by_can_provide: Dict[DataType, Set[str]] = {}
        self._by_tag: Dict[str, Set[str]] = {}

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        """Check if tool is registered."""
        return tool_id in self._tools

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(self, capability: ToolCapability) -> None:
        """도구 역량 등록 (동기).

        Args:
            capability: 등록할 도구 역량

        Raises:
            ValueError: 이미 등록된 tool_id
        """
        if capability.tool_id in self._tools:
            raise ValueError(f"Tool '{capability.tool_id}' already registered")

        self._tools[capability.tool_id] = capability
        self._update_indexes(capability)

        logger.debug(f"[ToolRegistry] Registered tool: {capability.tool_id}")

    async def register_async(self, capability: ToolCapability) -> None:
        """도구 역량 등록 (비동기).

        Args:
            capability: 등록할 도구 역량
        """
        async with self._lock:
            self.register(capability)

    def register_many(self, capabilities: List[ToolCapability]) -> int:
        """여러 도구 일괄 등록.

        Args:
            capabilities: 등록할 도구 역량 목록

        Returns:
            성공적으로 등록된 도구 수
        """
        count = 0
        for cap in capabilities:
            try:
                self.register(cap)
                count += 1
            except ValueError as e:
                logger.warning(f"[ToolRegistry] Skip registration: {e}")
        return count

    def unregister(self, tool_id: str) -> bool:
        """도구 등록 해제.

        Args:
            tool_id: 해제할 도구 ID

        Returns:
            성공 여부
        """
        if tool_id not in self._tools:
            return False

        capability = self._tools.pop(tool_id)
        self._remove_from_indexes(capability)

        logger.debug(f"[ToolRegistry] Unregistered tool: {tool_id}")
        return True

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get(self, tool_id: str) -> Optional[ToolCapability]:
        """도구 조회.

        Args:
            tool_id: 도구 ID

        Returns:
            도구 역량 또는 None
        """
        return self._tools.get(tool_id)

    def get_all(self) -> List[ToolCapability]:
        """모든 도구 조회.

        Returns:
            등록된 모든 도구 역량 목록
        """
        return list(self._tools.values())

    def get_enabled(self) -> List[ToolCapability]:
        """활성화된 도구만 조회.

        Returns:
            enabled=True인 도구 목록
        """
        return [t for t in self._tools.values() if t.enabled]

    def get_by_dimension(self, dimension: str) -> List[ToolCapability]:
        """차원별 도구 조회.

        Args:
            dimension: 차원 코드 (1D, 2D, 3D, 4D, AD, STORY, etc.)

        Returns:
            해당 차원의 도구 목록
        """
        tool_ids = self._by_dimension.get(dimension, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def get_by_tag(self, tag: str) -> List[ToolCapability]:
        """태그별 도구 조회.

        Args:
            tag: 태그 문자열

        Returns:
            해당 태그를 가진 도구 목록
        """
        tool_ids = self._by_tag.get(tag, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def find_compatible_tools(
        self,
        input_types: Optional[Set[DataType]] = None,
        output_types: Optional[Set[DataType]] = None,
    ) -> List[ToolCapability]:
        """호환 가능한 도구 검색.

        입력 타입을 처리할 수 있거나, 출력 타입을 제공하는 도구 검색.

        Args:
            input_types: 필요한 입력 타입 (can_consume 매칭)
            output_types: 필요한 출력 타입 (can_provide 매칭)

        Returns:
            조건을 만족하는 도구 목록
        """
        candidates: Set[str] = set()

        if input_types:
            for dtype in input_types:
                candidates.update(self._by_can_consume.get(dtype, set()))

        if output_types:
            for dtype in output_types:
                if candidates:
                    # AND 조건: input_types도 있으면 교집합
                    candidates &= self._by_can_provide.get(dtype, set())
                else:
                    candidates.update(self._by_can_provide.get(dtype, set()))

        return [
            self._tools[tid]
            for tid in candidates
            if tid in self._tools and self._tools[tid].enabled
        ]

    def find_providers(self, data_type: DataType) -> List[ToolCapability]:
        """특정 데이터 타입을 제공하는 도구 검색.

        Args:
            data_type: 필요한 출력 데이터 타입

        Returns:
            해당 타입을 출력으로 제공하는 도구 목록
        """
        tool_ids = self._by_can_provide.get(data_type, set())
        return [
            self._tools[tid]
            for tid in tool_ids
            if tid in self._tools and self._tools[tid].enabled
        ]

    def find_consumers(self, data_type: DataType) -> List[ToolCapability]:
        """특정 데이터 타입을 소비하는 도구 검색.

        Args:
            data_type: 입력 데이터 타입

        Returns:
            해당 타입을 입력으로 받는 도구 목록
        """
        tool_ids = self._by_can_consume.get(data_type, set())
        return [
            self._tools[tid]
            for tid in tool_ids
            if tid in self._tools and self._tools[tid].enabled
        ]

    # -------------------------------------------------------------------------
    # Dependency Analysis
    # -------------------------------------------------------------------------

    def get_required_prior_tools(self, tool_id: str) -> List[ToolCapability]:
        """필수 선행 도구 조회.

        Args:
            tool_id: 도구 ID

        Returns:
            필수 선행 도구 목록
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return []

        return [
            self._tools[tid]
            for tid in tool.required_prior_tools
            if tid in self._tools
        ]

    def get_incompatible_tools(self, tool_id: str) -> List[ToolCapability]:
        """함께 사용 불가한 도구 조회.

        Args:
            tool_id: 도구 ID

        Returns:
            비호환 도구 목록
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return []

        return [
            self._tools[tid]
            for tid in tool.incompatible_with
            if tid in self._tools
        ]

    def can_connect(
        self,
        from_tool_id: str,
        to_tool_id: str,
    ) -> bool:
        """두 도구의 연결 가능 여부 확인.

        from_tool의 출력이 to_tool의 입력으로 연결 가능한지 확인.

        Args:
            from_tool_id: 출력 도구 ID
            to_tool_id: 입력 도구 ID

        Returns:
            연결 가능 여부
        """
        from_tool = self._tools.get(from_tool_id)
        to_tool = self._tools.get(to_tool_id)

        if not from_tool or not to_tool:
            return False

        # 비호환 체크
        if to_tool_id in from_tool.incompatible_with:
            return False
        if from_tool_id in to_tool.incompatible_with:
            return False

        # 타입 호환성 체크
        common_types = from_tool.can_provide & to_tool.can_consume
        return len(common_types) > 0

    def find_connectable_types(
        self,
        from_tool_id: str,
        to_tool_id: str,
    ) -> Set[DataType]:
        """두 도구 간 연결 가능한 데이터 타입 반환.

        Args:
            from_tool_id: 출력 도구 ID
            to_tool_id: 입력 도구 ID

        Returns:
            연결 가능한 데이터 타입 집합
        """
        from_tool = self._tools.get(from_tool_id)
        to_tool = self._tools.get(to_tool_id)

        if not from_tool or not to_tool:
            return set()

        return from_tool.can_provide & to_tool.can_consume

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """레지스트리 통계 반환.

        Returns:
            통계 딕셔너리
        """
        tools = list(self._tools.values())
        enabled_tools = [t for t in tools if t.enabled]

        dimensions = {}
        for dim, tool_ids in self._by_dimension.items():
            dimensions[dim] = len(tool_ids)

        return {
            "total": len(tools),
            "enabled": len(enabled_tools),
            "dimensions": dimensions,
            "total_credit_cost": sum(t.credit_cost for t in enabled_tools),
            "avg_latency_ms": (
                sum(t.avg_latency_ms for t in enabled_tools) // len(enabled_tools)
                if enabled_tools else 0
            ),
            "hitl_required_count": sum(
                1 for t in enabled_tools if t.requires_human_review
            ),
        }

    # -------------------------------------------------------------------------
    # Index Management
    # -------------------------------------------------------------------------

    def _update_indexes(self, capability: ToolCapability) -> None:
        """인덱스 업데이트."""
        tool_id = capability.tool_id

        # Dimension index
        if capability.dimension not in self._by_dimension:
            self._by_dimension[capability.dimension] = set()
        self._by_dimension[capability.dimension].add(tool_id)

        # Can consume index
        for dtype in capability.can_consume:
            if dtype not in self._by_can_consume:
                self._by_can_consume[dtype] = set()
            self._by_can_consume[dtype].add(tool_id)

        # Can provide index
        for dtype in capability.can_provide:
            if dtype not in self._by_can_provide:
                self._by_can_provide[dtype] = set()
            self._by_can_provide[dtype].add(tool_id)

        # Tag index
        for tag in capability.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = set()
            self._by_tag[tag].add(tool_id)

    def _remove_from_indexes(self, capability: ToolCapability) -> None:
        """인덱스에서 제거."""
        tool_id = capability.tool_id

        # Dimension index
        if capability.dimension in self._by_dimension:
            self._by_dimension[capability.dimension].discard(tool_id)

        # Can consume index
        for dtype in capability.can_consume:
            if dtype in self._by_can_consume:
                self._by_can_consume[dtype].discard(tool_id)

        # Can provide index
        for dtype in capability.can_provide:
            if dtype in self._by_can_provide:
                self._by_can_provide[dtype].discard(tool_id)

        # Tag index
        for tag in capability.tags:
            if tag in self._by_tag:
                self._by_tag[tag].discard(tool_id)


# =============================================================================
# Global Registry (Singleton)
# =============================================================================

_global_registry: Optional[ToolCapabilityRegistry] = None
_registry_lock = asyncio.Lock()


def get_tool_registry() -> ToolCapabilityRegistry:
    """전역 도구 레지스트리 반환 (Singleton).

    Returns:
        전역 ToolCapabilityRegistry 인스턴스
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolCapabilityRegistry()
        _register_default_tools(_global_registry)
    return _global_registry


def reset_tool_registry() -> None:
    """전역 레지스트리 초기화 (테스트용)."""
    global _global_registry
    _global_registry = None


# =============================================================================
# Default Tool Definitions
# =============================================================================

def _register_default_tools(registry: ToolCapabilityRegistry) -> None:
    """기본 도구 등록.

    Vivid 플랫폼의 핵심 도구들을 등록합니다.
    """
    from app.workflow.types import PortSpec

    default_tools = [
        # 4D - 레퍼런스 분석
        ToolCapability(
            tool_id="reference_decoder",
            display_name="레퍼런스 해석기",
            dimension="4D",
            description="동영상/이미지 레퍼런스를 분석하여 스타일, 구도, 색감 정보 추출",
            input_ports=[
                PortSpec(
                    name="video_url",
                    data_type=DataType.VIDEO_URL,
                    required=False,
                    description="분석할 동영상 URL",
                ),
                PortSpec(
                    name="image_url",
                    data_type=DataType.IMAGE_URL,
                    required=False,
                    description="분석할 이미지 URL",
                ),
                PortSpec(
                    name="description",
                    data_type=DataType.TEXT,
                    required=True,
                    description="레퍼런스 설명 또는 분석 의도",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="analysis",
                    data_type=DataType.ANALYSIS_RESULT,
                    description="분석 결과 JSON",
                ),
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    description="스타일 힌트",
                ),
                PortSpec(
                    name="color_palette",
                    data_type=DataType.COLOR_PALETTE,
                    description="색상 팔레트",
                ),
                PortSpec(
                    name="composition_guide",
                    data_type=DataType.COMPOSITION_GUIDE,
                    description="구도 가이드",
                ),
            ],
            can_consume={DataType.VIDEO_URL, DataType.IMAGE_URL, DataType.TEXT},
            can_provide={
                DataType.ANALYSIS_RESULT,
                DataType.STYLE_HINT,
                DataType.COLOR_PALETTE,
                DataType.COMPOSITION_GUIDE,
            },
            credit_cost=10,
            avg_latency_ms=5000,
            requires_human_review=True,
            tags=["analysis", "reference", "style"],
        ),

        # STORY - 스토리 구조화
        ToolCapability(
            tool_id="story_architect",
            display_name="스토리 아키텍트",
            dimension="STORY",
            description="컨셉에서 스토리 구조 생성 (3막 구조, 캐릭터 아크)",
            input_ports=[
                PortSpec(
                    name="concept",
                    data_type=DataType.TEXT,
                    required=True,
                    description="스토리 컨셉",
                ),
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    required=False,
                    description="스타일 힌트 (선택)",
                ),
                PortSpec(
                    name="rag_context",
                    data_type=DataType.RAG_CONTEXT,
                    required=False,
                    description="RAG 컨텍스트 (거장 DNA 등)",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="story_structure",
                    data_type=DataType.STORY_STRUCTURE,
                    description="스토리 구조 JSON",
                ),
                PortSpec(
                    name="scene_list",
                    data_type=DataType.SCENE_LIST,
                    description="장면 목록",
                ),
            ],
            can_consume={DataType.TEXT, DataType.STYLE_HINT, DataType.RAG_CONTEXT},
            can_provide={DataType.STORY_STRUCTURE, DataType.SCENE_LIST},
            credit_cost=8,
            avg_latency_ms=4000,
            requires_human_review=True,
            tags=["story", "creative", "structure"],
        ),

        # 2D - 스토리보드 생성
        ToolCapability(
            tool_id="storyboard_generator",
            display_name="스토리보드 생성기",
            dimension="2D",
            description="스토리 구조에서 컷별 스토리보드 생성",
            input_ports=[
                PortSpec(
                    name="story_structure",
                    data_type=DataType.STORY_STRUCTURE,
                    required=True,
                    description="스토리 구조",
                ),
                PortSpec(
                    name="scene_list",
                    data_type=DataType.SCENE_LIST,
                    required=False,
                    description="장면 목록",
                ),
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    required=False,
                    description="스타일 힌트",
                ),
                PortSpec(
                    name="composition_guide",
                    data_type=DataType.COMPOSITION_GUIDE,
                    required=False,
                    description="구도 가이드",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="storyboard",
                    data_type=DataType.STORYBOARD,
                    description="스토리보드 JSON",
                ),
            ],
            can_consume={
                DataType.STORY_STRUCTURE,
                DataType.SCENE_LIST,
                DataType.STYLE_HINT,
                DataType.COMPOSITION_GUIDE,
            },
            can_provide={DataType.STORYBOARD},
            credit_cost=12,
            avg_latency_ms=6000,
            required_prior_tools=["story_architect"],
            tags=["storyboard", "visual", "2d"],
        ),

        # 1D - 프롬프트 생성
        ToolCapability(
            tool_id="prompt_composer",
            display_name="프롬프트 작곡가",
            dimension="1D",
            description="스타일 힌트와 분석 결과를 기반으로 이미지/비디오 생성 프롬프트 작성",
            input_ports=[
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    required=False,
                    description="스타일 힌트",
                ),
                PortSpec(
                    name="analysis_result",
                    data_type=DataType.ANALYSIS_RESULT,
                    required=False,
                    description="분석 결과",
                ),
                PortSpec(
                    name="storyboard",
                    data_type=DataType.STORYBOARD,
                    required=False,
                    description="스토리보드",
                ),
                PortSpec(
                    name="user_input",
                    data_type=DataType.TEXT,
                    required=True,
                    description="사용자 입력",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="prompt",
                    data_type=DataType.PROMPT,
                    description="생성 프롬프트",
                ),
            ],
            can_consume={
                DataType.STYLE_HINT,
                DataType.ANALYSIS_RESULT,
                DataType.STORYBOARD,
                DataType.TEXT,
            },
            can_provide={DataType.PROMPT},
            credit_cost=5,
            avg_latency_ms=2000,
            tags=["prompt", "1d", "text"],
        ),

        # 3D - 이미지 생성
        ToolCapability(
            tool_id="image_generator",
            display_name="이미지 생성기",
            dimension="3D",
            description="프롬프트를 기반으로 이미지 생성",
            input_ports=[
                PortSpec(
                    name="prompt",
                    data_type=DataType.PROMPT,
                    required=True,
                    description="생성 프롬프트",
                ),
                PortSpec(
                    name="reference_image",
                    data_type=DataType.IMAGE_URL,
                    required=False,
                    description="참조 이미지 (선택)",
                ),
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    required=False,
                    description="스타일 힌트",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="image_url",
                    data_type=DataType.IMAGE_URL,
                    description="생성된 이미지 URL",
                ),
            ],
            can_consume={DataType.PROMPT, DataType.IMAGE_URL, DataType.STYLE_HINT},
            can_provide={DataType.IMAGE_URL},
            credit_cost=15,
            avg_latency_ms=8000,
            required_prior_tools=["prompt_composer"],
            tags=["image", "3d", "generation"],
        ),

        # VEO - 비디오 생성
        ToolCapability(
            tool_id="video_generator",
            display_name="비디오 생성기",
            dimension="VEO",
            description="프롬프트와 이미지를 기반으로 비디오 생성",
            input_ports=[
                PortSpec(
                    name="prompt",
                    data_type=DataType.PROMPT,
                    required=True,
                    description="생성 프롬프트",
                ),
                PortSpec(
                    name="start_image",
                    data_type=DataType.IMAGE_URL,
                    required=False,
                    description="시작 프레임 이미지",
                ),
                PortSpec(
                    name="storyboard",
                    data_type=DataType.STORYBOARD,
                    required=False,
                    description="스토리보드",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="video_url",
                    data_type=DataType.VIDEO_URL,
                    description="생성된 비디오 URL",
                ),
            ],
            can_consume={DataType.PROMPT, DataType.IMAGE_URL, DataType.STORYBOARD},
            can_provide={DataType.VIDEO_URL},
            credit_cost=50,
            avg_latency_ms=60000,
            required_prior_tools=["prompt_composer"],
            tags=["video", "veo", "generation"],
        ),

        # AD - 미학 디렉터
        ToolCapability(
            tool_id="aesthetic_director",
            display_name="미학 디렉터",
            dimension="AD",
            description="전체 프로젝트의 미학적 일관성 검토 및 가이드 제공",
            input_ports=[
                PortSpec(
                    name="style_hint",
                    data_type=DataType.STYLE_HINT,
                    required=False,
                    description="스타일 힌트",
                ),
                PortSpec(
                    name="analysis_result",
                    data_type=DataType.ANALYSIS_RESULT,
                    required=False,
                    description="분석 결과",
                ),
                PortSpec(
                    name="storyboard",
                    data_type=DataType.STORYBOARD,
                    required=False,
                    description="스토리보드",
                ),
                PortSpec(
                    name="rag_context",
                    data_type=DataType.RAG_CONTEXT,
                    required=False,
                    description="거장 DNA 컨텍스트",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="style_guide",
                    data_type=DataType.STYLE_HINT,
                    description="정제된 스타일 가이드",
                ),
                PortSpec(
                    name="color_palette",
                    data_type=DataType.COLOR_PALETTE,
                    description="통합 색상 팔레트",
                ),
            ],
            can_consume={
                DataType.STYLE_HINT,
                DataType.ANALYSIS_RESULT,
                DataType.STORYBOARD,
                DataType.RAG_CONTEXT,
            },
            can_provide={DataType.STYLE_HINT, DataType.COLOR_PALETTE},
            credit_cost=10,
            avg_latency_ms=3000,
            requires_human_review=True,
            tags=["aesthetic", "direction", "style"],
        ),

        # RAG - 컨텍스트 수집기
        ToolCapability(
            tool_id="rag_collector",
            display_name="RAG 컨텍스트 수집기",
            dimension="RAG",
            description="Multi-RAG 시스템에서 관련 컨텍스트 수집",
            input_ports=[
                PortSpec(
                    name="query",
                    data_type=DataType.TEXT,
                    required=True,
                    description="검색 쿼리",
                ),
                PortSpec(
                    name="user_context",
                    data_type=DataType.USER_CONTEXT,
                    required=False,
                    description="사용자 컨텍스트",
                ),
            ],
            output_ports=[
                PortSpec(
                    name="rag_context",
                    data_type=DataType.RAG_CONTEXT,
                    description="RAG 검색 결과",
                ),
            ],
            can_consume={DataType.TEXT, DataType.USER_CONTEXT},
            can_provide={DataType.RAG_CONTEXT},
            credit_cost=3,
            avg_latency_ms=2000,
            tags=["rag", "search", "context"],
        ),
    ]

    count = registry.register_many(default_tools)
    logger.info(f"[ToolRegistry] Registered {count} default tools")
