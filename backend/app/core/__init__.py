"""Vivid Core Module.

통합 오케스트레이션 및 앱 관리 시스템.

Submodules:
- app_schema: 앱 설정 스키마 (YAML)
- app_registry: 앱 레지스트리 (Microkernel)
- unified_schemas: 통합 타입 정의
- unified_state: LangGraph 상태
- graph: StateGraph 정의
- entrypoint: 통합 쿼리 진입점
- nodes: 그래프 노드 함수들
- utils: 유틸리티 함수 (RRF 등)
- service_registry: 서비스 싱글톤 관리

Usage:
    # 통합 쿼리 실행
    from app.core import unified_query

    result = await unified_query("강주노 롱테이크 분석")

    # 앱 레지스트리 조회
    from app.core import AppRegistry

    apps = AppRegistry.get_by_type(AppType.AUTEUR)
"""
from app.core.app_registry import AppRegistry, init_registry
from app.core.app_schema import AppConfig, AppType, BoundedContext

# Unified orchestration exports
from app.core.entrypoint import (
    unified_query,
    unified_query_from_request,
    unified_query_compat,
)
from app.core.graph import (
    get_unified_graph,
    build_unified_graph,
    reset_graph,
)
from app.core.unified_schemas import (
    QueryType,
    Intent,
    Dimension,
    DataType,
    CheckpointAction,
    OrchestrationPattern,
)
from app.core.unified_state import (
    UnifiedState,
    create_initial_state,
)
from app.core.service_registry import (
    ServiceRegistry,
    setup_default_services,
)

__all__ = [
    # App Registry
    "AppRegistry",
    "init_registry",
    "AppConfig",
    "AppType",
    "BoundedContext",
    # Unified Orchestration
    "unified_query",
    "unified_query_from_request",
    "unified_query_compat",
    # Graph
    "get_unified_graph",
    "build_unified_graph",
    "reset_graph",
    # Types
    "QueryType",
    "Intent",
    "Dimension",
    "DataType",
    "CheckpointAction",
    "OrchestrationPattern",
    # State
    "UnifiedState",
    "create_initial_state",
    # Service Registry
    "ServiceRegistry",
    "setup_default_services",
]
