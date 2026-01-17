"""Default MCP Server Configurations (P0 Phase 4 - 2026).

사전 등록된 외부 MCP 서버 설정.

2026 Best Practices:
    - Streamable HTTP transport (MCP Spec 2025-06-18)
    - Environment-based configuration
    - Graceful degradation when servers unavailable
    - Tiered server organization (Core, Premium, Internal)

Tier Structure:
    - Tier 1 (Core): Tavily, Qdrant - 기본 제공
    - Tier 2 (Premium): Playwright, GitHub - 옵션
    - Tier 3 (Internal): Dimension Tools MCP - 내부

Reference:
    - MCP Registry: https://registry.modelcontextprotocol.io
    - Tavily MCP: https://github.com/tavily-ai/tavily-mcp
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.config import settings
from app.mcp.types import MCPServerConfig, MCPTransport

logger = logging.getLogger(__name__)


# =============================================================================
# Server Configurations
# =============================================================================

def get_tavily_config() -> Optional[MCPServerConfig]:
    """Tavily AI Search MCP 서버 설정.

    AI-optimized 웹 검색 및 콘텐츠 추출.

    Features:
        - tavily-search: 웹 검색 (AI 최적화)
        - tavily-extract: URL에서 콘텐츠 추출
        - tavily-crawl: 웹 크롤링
        - tavily-map: 사이트 구조 매핑

    Pricing:
        - Free: 1,000 searches/month
        - Starter: $50/month, 10,000 searches
        - Pro: $200/month, 50,000 searches

    Returns:
        MCPServerConfig if API key configured, else None
    """
    if not settings.TAVILY_API_KEY:
        logger.debug("Tavily MCP disabled: TAVILY_API_KEY not set")
        return None

    return MCPServerConfig(
        server_id="tavily",
        name="Tavily AI Search",
        description="AI-optimized web search, extract, crawl, and site mapping",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.tavily.com/mcp",
        auth_type="api_key",
        auth_config={
            "api_key": settings.TAVILY_API_KEY,
            "header": "Authorization",
            "prefix": "Bearer",
        },
        timeout_seconds=30,
        max_retries=3,
        retry_delay_ms=1000,
        rate_limit_rpm=50,  # Free tier safe limit
        circuit_breaker_threshold=5,
        enabled=True,
        tags=("search", "web", "tier1", "rag"),
    )


def get_qdrant_config() -> Optional[MCPServerConfig]:
    """Qdrant Vector Database MCP 서버 설정.

    시맨틱 검색 및 RAG 파이프라인 지원.

    Features:
        - search: 벡터 유사도 검색
        - upsert: 벡터 삽입/업데이트
        - delete: 벡터 삭제
        - scroll: 벡터 스크롤 조회

    Note:
        Qdrant는 기본적으로 REST API를 제공하므로
        MCP 래퍼를 통해 접근합니다.

    Returns:
        MCPServerConfig for local Qdrant
    """
    # Qdrant MCP는 내부 구현 사용 (외부 MCP 서버 아님)
    # 여기서는 설정만 정의하고, 실제 연결은 QdrantAdapter에서 처리
    qdrant_url = settings.QDRANT_URL

    return MCPServerConfig(
        server_id="qdrant",
        name="Qdrant Vector Search",
        description="Semantic vector search for RAG pipeline",
        transport=MCPTransport.STREAMABLE_HTTP,
        url=f"{qdrant_url}/mcp",  # Qdrant MCP endpoint
        auth_type="api_key" if settings.QDRANT_API_KEY else "none",
        auth_config={
            "api_key": settings.QDRANT_API_KEY,
            "header": "api-key",
        } if settings.QDRANT_API_KEY else {},
        timeout_seconds=15,
        max_retries=2,
        retry_delay_ms=500,
        rate_limit_rpm=200,  # Internal, higher limit
        circuit_breaker_threshold=3,
        enabled=True,
        tags=("vector", "search", "tier1", "rag", "internal"),
    )


def get_playwright_config() -> Optional[MCPServerConfig]:
    """Playwright Browser MCP 서버 설정.

    브라우저 자동화 및 스크린샷 캡처.

    Features:
        - navigate: URL 이동
        - screenshot: 스크린샷 캡처
        - click: 요소 클릭
        - fill: 폼 입력
        - evaluate: JavaScript 실행

    Warning:
        리소스 집약적이므로 기본 비활성화.
        운영 환경에서는 별도 컨테이너 권장.

    Returns:
        MCPServerConfig if enabled, else None
    """
    if not settings.MCP_PLAYWRIGHT_ENABLED:
        logger.debug("Playwright MCP disabled: MCP_PLAYWRIGHT_ENABLED=False")
        return None

    return MCPServerConfig(
        server_id="playwright",
        name="Playwright Browser Automation",
        description="Browser automation, screenshots, and E2E testing",
        transport=MCPTransport.STDIO,
        command="npx",
        args=(
            "-y",
            "@anthropic-ai/mcp-server-puppeteer",
        ),
        env={
            "PUPPETEER_HEADLESS": str(settings.MCP_PLAYWRIGHT_HEADLESS).lower(),
        },
        timeout_seconds=60,  # Browser ops can be slow
        max_retries=2,
        retry_delay_ms=2000,
        rate_limit_rpm=20,  # Resource-heavy
        circuit_breaker_threshold=3,
        enabled=True,
        tags=("browser", "automation", "tier2", "e2e"),
    )


def get_filesystem_config() -> Optional[MCPServerConfig]:
    """Filesystem MCP 서버 설정.

    로컬 파일 시스템 접근.

    Features:
        - read_file: 파일 읽기
        - write_file: 파일 쓰기
        - list_directory: 디렉토리 목록
        - search_files: 파일 검색

    Security:
        - 허용된 경로만 접근 가능
        - 기본 비활성화 (보안 민감)

    Returns:
        MCPServerConfig if enabled, else None
    """
    if not settings.MCP_FILESYSTEM_ENABLED:
        logger.debug("Filesystem MCP disabled: MCP_FILESYSTEM_ENABLED=False")
        return None

    allowed_paths = settings.MCP_FILESYSTEM_ALLOWED_PATHS.split(",")

    return MCPServerConfig(
        server_id="filesystem",
        name="Filesystem Access",
        description="Local filesystem read/write operations",
        transport=MCPTransport.STDIO,
        command="npx",
        args=(
            "-y",
            "@modelcontextprotocol/server-filesystem",
            *[p.strip() for p in allowed_paths],
        ),
        timeout_seconds=30,
        max_retries=2,
        retry_delay_ms=500,
        rate_limit_rpm=100,
        circuit_breaker_threshold=5,
        enabled=True,
        tags=("filesystem", "tier2", "local"),
    )


def get_github_config() -> Optional[MCPServerConfig]:
    """GitHub MCP 서버 설정.

    GitHub API 접근.

    Features:
        - search_repositories: 리포지토리 검색
        - get_file_contents: 파일 내용 조회
        - create_issue: 이슈 생성
        - create_pull_request: PR 생성

    Returns:
        MCPServerConfig if token configured, else None
    """
    if not settings.MCP_GITHUB_ENABLED or not settings.MCP_GITHUB_TOKEN:
        logger.debug("GitHub MCP disabled: MCP_GITHUB_ENABLED=False or no token")
        return None

    return MCPServerConfig(
        server_id="github",
        name="GitHub API",
        description="GitHub repository and issue management",
        transport=MCPTransport.STDIO,
        command="npx",
        args=(
            "-y",
            "@modelcontextprotocol/server-github",
        ),
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": settings.MCP_GITHUB_TOKEN,
        },
        timeout_seconds=30,
        max_retries=3,
        retry_delay_ms=1000,
        rate_limit_rpm=60,  # GitHub rate limit aware
        circuit_breaker_threshold=5,
        enabled=True,
        tags=("github", "vcs", "tier2"),
    )


def get_dimension_tools_config() -> Optional[MCPServerConfig]:
    """Dimension Tools Internal MCP 서버 설정.

    Vivid Dimension Tools를 MCP 프로토콜로 노출.

    Features:
        - reference_decode: 레퍼런스 영상 분석
        - storyboard_generate: 스토리보드 생성
        - image_generate: 이미지 생성
        - aesthetic_direct: 미학 디렉션
        - rag_collect: RAG 지식 수집

    Note:
        내부 HTTP 서버로 동작 (FastMCP).

    Returns:
        MCPServerConfig for internal dimension tools
    """
    if not settings.MCP_INTERNAL_SERVER_ENABLED:
        logger.debug("Dimension Tools MCP disabled: MCP_INTERNAL_SERVER_ENABLED=False")
        return None

    return MCPServerConfig(
        server_id="dimension_tools",
        name="Vivid Dimension Tools",
        description="Crebit Studio internal AI tools for content creation",
        transport=MCPTransport.STREAMABLE_HTTP,
        url=f"http://localhost:{settings.MCP_INTERNAL_SERVER_PORT}/mcp",
        auth_type="none",  # Internal, no external auth needed
        timeout_seconds=120,  # LLM calls can be slow
        max_retries=2,
        retry_delay_ms=1000,
        rate_limit_rpm=100,
        circuit_breaker_threshold=5,
        enabled=True,
        tags=("dimension", "internal", "tier3", "llm"),
    )


# =============================================================================
# Registration Functions
# =============================================================================

def get_core_server_configs() -> List[MCPServerConfig]:
    """Tier 1 Core 서버 설정 목록.

    기본 제공되는 필수 MCP 서버들.

    Returns:
        List of core MCPServerConfig
    """
    configs = []

    # Tavily (if configured)
    tavily = get_tavily_config()
    if tavily:
        configs.append(tavily)

    # Qdrant (always available for RAG)
    qdrant = get_qdrant_config()
    if qdrant:
        configs.append(qdrant)

    return configs


def get_premium_server_configs() -> List[MCPServerConfig]:
    """Tier 2 Premium 서버 설정 목록.

    옵션으로 활성화 가능한 MCP 서버들.

    Returns:
        List of premium MCPServerConfig
    """
    configs = []

    playwright = get_playwright_config()
    if playwright:
        configs.append(playwright)

    filesystem = get_filesystem_config()
    if filesystem:
        configs.append(filesystem)

    github = get_github_config()
    if github:
        configs.append(github)

    return configs


def get_internal_server_configs() -> List[MCPServerConfig]:
    """Tier 3 Internal 서버 설정 목록.

    내부 도구를 MCP로 노출하는 서버들.

    Returns:
        List of internal MCPServerConfig
    """
    configs = []

    dimension = get_dimension_tools_config()
    if dimension:
        configs.append(dimension)

    return configs


def get_all_server_configs() -> List[MCPServerConfig]:
    """모든 MCP 서버 설정 목록.

    Returns:
        List of all configured MCPServerConfig
    """
    return (
        get_core_server_configs()
        + get_premium_server_configs()
        + get_internal_server_configs()
    )


async def register_default_servers(
    manager: "MCPClientManager",  # noqa: F821
    *,
    include_core: bool = True,
    include_premium: bool = True,
    include_internal: bool = True,
) -> List[str]:
    """기본 MCP 서버들을 매니저에 등록.

    Args:
        manager: MCP Client Manager 인스턴스
        include_core: Core 서버 포함 여부
        include_premium: Premium 서버 포함 여부
        include_internal: Internal 서버 포함 여부

    Returns:
        등록된 서버 ID 목록
    """
    registered = []

    configs = []
    if include_core:
        configs.extend(get_core_server_configs())
    if include_premium:
        configs.extend(get_premium_server_configs())
    if include_internal:
        configs.extend(get_internal_server_configs())

    for config in configs:
        try:
            await manager.register_server(config)
            registered.append(config.server_id)
            logger.info(
                f"MCP server registered: {config.server_id} "
                f"({config.transport.value})"
            )
        except Exception as e:
            logger.error(f"Failed to register MCP server {config.server_id}: {e}")

    return registered


# =============================================================================
# Tool Mappings (Vivid Tool ID → MCP Server/Tool)
# =============================================================================

# Vivid 내부 도구 ID와 MCP 서버/도구 매핑
DEFAULT_TOOL_MAPPINGS = {
    # Tavily Search Tools
    "web_search": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-search",
        "description": "AI-optimized web search",
        "credit_cost": 2,
    },
    "web_extract": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-extract",
        "description": "Extract content from URLs",
        "credit_cost": 2,
    },
    "web_crawl": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-crawl",
        "description": "Crawl website structure",
        "credit_cost": 3,
    },
    "site_map": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-map",
        "description": "Map website URL structure",
        "credit_cost": 2,
    },

    # Qdrant Vector Tools
    "semantic_search": {
        "server_id": "qdrant",
        "mcp_tool_name": "search",
        "description": "Semantic vector search",
        "credit_cost": 1,
    },
    "vector_upsert": {
        "server_id": "qdrant",
        "mcp_tool_name": "upsert",
        "description": "Upsert vectors",
        "credit_cost": 1,
    },

    # Playwright Browser Tools
    "browser_navigate": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_navigate",
        "description": "Navigate browser to URL",
        "credit_cost": 5,
    },
    "browser_screenshot": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_screenshot",
        "description": "Capture browser screenshot",
        "credit_cost": 5,
    },
    "browser_click": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_click",
        "description": "Click element in browser",
        "credit_cost": 3,
    },
    "browser_fill": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_fill",
        "description": "Fill form input",
        "credit_cost": 3,
    },

    # Filesystem Tools
    "file_read": {
        "server_id": "filesystem",
        "mcp_tool_name": "read_file",
        "description": "Read file content",
        "credit_cost": 1,
    },
    "file_write": {
        "server_id": "filesystem",
        "mcp_tool_name": "write_file",
        "description": "Write file content",
        "credit_cost": 1,
    },
    "file_list": {
        "server_id": "filesystem",
        "mcp_tool_name": "list_directory",
        "description": "List directory contents",
        "credit_cost": 1,
    },

    # GitHub Tools
    "github_search": {
        "server_id": "github",
        "mcp_tool_name": "search_repositories",
        "description": "Search GitHub repositories",
        "credit_cost": 2,
    },
    "github_file": {
        "server_id": "github",
        "mcp_tool_name": "get_file_contents",
        "description": "Get file from GitHub repo",
        "credit_cost": 1,
    },

    # Dimension Tools (Internal)
    "reference_analyze": {
        "server_id": "dimension_tools",
        "mcp_tool_name": "reference_decode",
        "description": "Analyze video reference",
        "credit_cost": 10,
    },
    "storyboard_create": {
        "server_id": "dimension_tools",
        "mcp_tool_name": "storyboard_generate",
        "description": "Generate storyboard",
        "credit_cost": 15,
    },
    "image_create": {
        "server_id": "dimension_tools",
        "mcp_tool_name": "image_generate",
        "description": "Generate image",
        "credit_cost": 20,
    },
    "aesthetic_feedback": {
        "server_id": "dimension_tools",
        "mcp_tool_name": "aesthetic_direct",
        "description": "Get aesthetic direction",
        "credit_cost": 5,
    },
    "rag_knowledge": {
        "server_id": "dimension_tools",
        "mcp_tool_name": "rag_collect",
        "description": "Collect RAG knowledge",
        "credit_cost": 3,
    },
}


def get_tool_mapping(tool_id: str) -> Optional[dict]:
    """도구 ID로 MCP 매핑 조회.

    Args:
        tool_id: Vivid 내부 도구 ID

    Returns:
        MCP 매핑 정보 또는 None
    """
    return DEFAULT_TOOL_MAPPINGS.get(tool_id)


def get_server_tools(server_id: str) -> List[dict]:
    """서버 ID로 매핑된 도구 목록 조회.

    Args:
        server_id: MCP 서버 ID

    Returns:
        해당 서버의 도구 매핑 목록
    """
    return [
        {"tool_id": tool_id, **mapping}
        for tool_id, mapping in DEFAULT_TOOL_MAPPINGS.items()
        if mapping["server_id"] == server_id
    ]
