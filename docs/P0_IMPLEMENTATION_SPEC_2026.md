# P0 Implementation Specification 2026

> Dynamic DAG Orchestration + HITL Checkpoint + Multi-RAG Router

---

## Executive Summary

P0 구현은 Vivid를 **2026 Composable AI 표준**에 맞추기 위한 핵심 업그레이드입니다.

### P0 범위

| Component | 목적 | 예상 기간 |
|-----------|------|----------|
| **Multi-RAG Router** | 5-10개 RAG 소스 지능형 라우팅 | 1-2주 |
| **Dynamic DAG Planner** | 의도 기반 동적 워크플로우 생성 | 2주 |
| **HITL Checkpoint System** | 인간 개입 지점 일시정지/재개 | 2주 |

**총 예상: 5-6주**

---

## Part 1: Multi-RAG Router

### 1.1 현재 상태

```python
# backend/app/rag/hybrid_rag.py - 현재 2개 소스만
class HybridRAGResult:
    notebooklm_sources: List[NotebookSource]  # Tier 0: 거장 DNA
    vertex_sources: List[RAGSource]           # Tier 1: Qdrant
```

### 1.2 목표 아키텍처 (5-10개 RAG)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Multi-RAG Router Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Query → [RAG Router Agent] → [Knowledge Source Selection]              │
│                      ↓                                                       │
│              ┌──────────────────────────────────────────────────┐           │
│              │           RAG Source Registry                     │           │
│              ├──────────────────────────────────────────────────┤           │
│              │                                                   │           │
│              │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │           │
│              │  │ NotebookLM  │  │   Qdrant    │  │ User DB  │  │           │
│              │  │ (거장 DNA)  │  │ (차원 지식) │  │(히스토리)│  │           │
│              │  └─────────────┘  └─────────────┘  └──────────┘  │           │
│              │                                                   │           │
│              │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │           │
│              │  │ Template KB │  │  Industry   │  │ Project  │  │           │
│              │  │ (워크플로우)│  │  (업종별)   │  │ Context  │  │           │
│              │  └─────────────┘  └─────────────┘  └──────────┘  │           │
│              │                                                   │           │
│              │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │           │
│              │  │   Trends    │  │   Legal/    │  │  Custom  │  │           │
│              │  │  (2026 트렌드)│  │  Compliance │  │  (확장)  │  │           │
│              │  └─────────────┘  └─────────────┘  └──────────┘  │           │
│              └──────────────────────────────────────────────────┘           │
│                      ↓                                                       │
│              [Parallel Query Execution] → [RRF Fusion] → [Reranker]         │
│                      ↓                                                       │
│              [Enriched Context for LLM]                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 RAG Source Registry 설계

**Reference**: [RAGRouter 논문](https://arxiv.org/abs/2505.23052) - 3.61% 성능 향상

```python
# backend/app/rag/multi_rag_router.py

from typing import List, Dict, Any, Optional, Protocol
from pydantic import BaseModel
from enum import Enum
from abc import ABC, abstractmethod


class RAGSourceType(str, Enum):
    """RAG 소스 유형"""
    AUTEUR_DNA = "auteur_dna"           # 거장 DNA (NotebookLM)
    DIMENSION_KNOWLEDGE = "dimension"    # 차원별 지식 (Qdrant)
    USER_HISTORY = "user_history"        # 사용자 작업 히스토리
    TEMPLATE_WORKFLOW = "template"       # 워크플로우 템플릿
    INDUSTRY_VERTICAL = "industry"       # 업종별 지식 (광고, 영화, 유튜브)
    PROJECT_CONTEXT = "project"          # 현재 프로젝트 컨텍스트
    TREND_DATA = "trend"                 # 2026 트렌드 데이터
    COMPLIANCE = "compliance"            # 법적/규정 가이드
    CUSTOM = "custom"                    # 사용자 정의


class RAGSourceSpec(BaseModel):
    """RAG 소스 명세"""
    source_id: str
    source_type: RAGSourceType
    display_name: str
    description: str
    # 라우팅 메타데이터
    keywords: List[str]                  # 라우팅 키워드
    priority: int = 5                    # 1-10, 높을수록 우선
    latency_ms_avg: int = 500           # 평균 응답 시간
    cost_per_query: float = 0.0         # 쿼리당 비용
    # 연결 설정
    backend_type: str                    # "notebooklm", "qdrant", "postgres", "api"
    connection_config: Dict[str, Any]    # 백엔드별 연결 설정
    # 제약 조건
    max_results: int = 10
    requires_auth: bool = False
    enabled: bool = True


class RAGSourceBackend(Protocol):
    """RAG 소스 백엔드 프로토콜 (Duck Typing)"""

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """쿼리 실행"""
        ...

    async def health_check(self) -> bool:
        """헬스 체크"""
        ...


class RAGSourceRegistry:
    """RAG 소스 레지스트리 - Composable Pattern"""

    def __init__(self):
        self._sources: Dict[str, RAGSourceSpec] = {}
        self._backends: Dict[str, RAGSourceBackend] = {}

    def register(
        self,
        spec: RAGSourceSpec,
        backend: RAGSourceBackend,
    ) -> None:
        """새 RAG 소스 등록 (런타임 가능)"""
        self._sources[spec.source_id] = spec
        self._backends[spec.source_id] = backend

    def unregister(self, source_id: str) -> None:
        """RAG 소스 제거"""
        self._sources.pop(source_id, None)
        self._backends.pop(source_id, None)

    def get_enabled_sources(self) -> List[RAGSourceSpec]:
        """활성화된 소스 목록"""
        return [s for s in self._sources.values() if s.enabled]

    def get_backend(self, source_id: str) -> Optional[RAGSourceBackend]:
        """백엔드 인스턴스 조회"""
        return self._backends.get(source_id)
```

### 1.4 Intelligent Router Agent

**Reference**: [LlamaIndex Router](https://docs.llamaindex.ai/en/stable/examples/low_level/router/)

```python
# backend/app/rag/intelligent_router.py

from typing import List, Dict, Any, Tuple
import asyncio
from dataclasses import dataclass


@dataclass
class RouteDecision:
    """라우팅 결정 결과"""
    selected_sources: List[str]
    reasoning: str
    confidence: float
    estimated_latency_ms: int


class IntelligentRAGRouter:
    """지능형 RAG 라우터 - LLM 기반 소스 선택"""

    def __init__(
        self,
        registry: RAGSourceRegistry,
        llm_client: Any,  # Gemini client
    ):
        self.registry = registry
        self.llm = llm_client

    async def route(
        self,
        query: str,
        context: Dict[str, Any],
        max_sources: int = 3,
    ) -> RouteDecision:
        """
        쿼리를 분석하고 최적의 RAG 소스 선택

        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트 (dimension, auteur_key, user_id 등)
            max_sources: 최대 선택 소스 수

        Returns:
            RouteDecision with selected sources
        """
        sources = self.registry.get_enabled_sources()

        # 1. Rule-based Pre-filtering
        candidates = self._prefilter(query, context, sources)

        # 2. LLM-based Selection (for complex queries)
        if len(candidates) > max_sources:
            candidates = await self._llm_select(
                query, context, candidates, max_sources
            )

        # 3. Build decision
        return RouteDecision(
            selected_sources=[c.source_id for c in candidates],
            reasoning=self._build_reasoning(candidates),
            confidence=self._calculate_confidence(candidates),
            estimated_latency_ms=max(c.latency_ms_avg for c in candidates),
        )

    def _prefilter(
        self,
        query: str,
        context: Dict[str, Any],
        sources: List[RAGSourceSpec],
    ) -> List[RAGSourceSpec]:
        """규칙 기반 사전 필터링"""
        candidates = []
        query_lower = query.lower()

        for source in sources:
            score = 0

            # 키워드 매칭
            for kw in source.keywords:
                if kw.lower() in query_lower:
                    score += 1

            # 컨텍스트 기반 부스트
            if context.get("auteur_key") and source.source_type == RAGSourceType.AUTEUR_DNA:
                score += 3
            if context.get("dimension") and source.source_type == RAGSourceType.DIMENSION_KNOWLEDGE:
                score += 2
            if context.get("user_id") and source.source_type == RAGSourceType.USER_HISTORY:
                score += 1

            if score > 0:
                candidates.append((source, score))

        # 점수순 정렬
        candidates.sort(key=lambda x: (-x[1], -x[0].priority))
        return [c[0] for c in candidates]

    async def _llm_select(
        self,
        query: str,
        context: Dict[str, Any],
        candidates: List[RAGSourceSpec],
        max_sources: int,
    ) -> List[RAGSourceSpec]:
        """LLM 기반 소스 선택 (복잡한 쿼리용)"""
        prompt = f"""
        사용자 쿼리: {query}

        컨텍스트:
        - Dimension: {context.get('dimension', 'N/A')}
        - Auteur: {context.get('auteur_key', 'N/A')}
        - User ID: {context.get('user_id', 'N/A')}

        사용 가능한 지식 소스:
        {self._format_sources(candidates)}

        이 쿼리에 가장 적합한 지식 소스를 {max_sources}개 선택하세요.
        JSON 형식으로 source_id 목록만 반환: ["source_1", "source_2"]
        """

        response = await self.llm.generate(prompt)
        selected_ids = self._parse_selection(response)

        return [c for c in candidates if c.source_id in selected_ids]


class MultiRAGOrchestrator:
    """Multi-RAG 오케스트레이터 - 병렬 실행 및 융합"""

    def __init__(
        self,
        registry: RAGSourceRegistry,
        router: IntelligentRAGRouter,
        reranker: Any,  # Reranker instance
    ):
        self.registry = registry
        self.router = router
        self.reranker = reranker

    async def query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> "MultiRAGResult":
        """
        Multi-RAG 쿼리 실행

        1. Router가 최적 소스 선택
        2. 선택된 소스에 병렬 쿼리
        3. RRF (Reciprocal Rank Fusion)로 결과 융합
        4. Reranker로 최종 정렬
        """
        # 1. Route
        decision = await self.router.route(query, context)

        # 2. Parallel Query
        tasks = []
        for source_id in decision.selected_sources:
            backend = self.registry.get_backend(source_id)
            if backend:
                tasks.append(self._query_source(source_id, backend, query))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. RRF Fusion
        fused = self._rrf_fusion(results)

        # 4. Rerank
        reranked = await self.reranker.rerank(query, fused)

        return MultiRAGResult(
            documents=reranked,
            sources_used=decision.selected_sources,
            routing_decision=decision,
        )

    def _rrf_fusion(
        self,
        results: List[List[Dict[str, Any]]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion

        Score = Σ 1 / (k + rank_i)
        """
        scores: Dict[str, float] = {}
        docs: Dict[str, Dict[str, Any]] = {}

        for source_results in results:
            if isinstance(source_results, Exception):
                continue
            for rank, doc in enumerate(source_results):
                doc_id = doc.get("id") or hash(doc.get("content", ""))
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
                docs[doc_id] = doc

        # 점수순 정렬
        sorted_ids = sorted(scores.keys(), key=lambda x: -scores[x])
        return [docs[doc_id] for doc_id in sorted_ids]
```

### 1.5 RAG 소스 구현 예시

```python
# backend/app/rag/backends/user_history.py

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class UserHistoryRAGBackend:
    """사용자 히스토리 RAG 백엔드"""

    def __init__(self, db_session_factory):
        self.db_factory = db_session_factory

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """사용자 과거 작업에서 유사 컨텍스트 검색"""
        user_id = filters.get("user_id") if filters else None
        if not user_id:
            return []

        async with self.db_factory() as db:
            # 사용자의 최근 성공 결과 검색
            # TODO: Vector similarity 추가
            results = await db.execute(
                select(CapsuleRun)
                .where(CapsuleRun.user_id == user_id)
                .where(CapsuleRun.success == True)
                .order_by(CapsuleRun.created_at.desc())
                .limit(limit)
            )

            runs = results.scalars().all()

            return [
                {
                    "id": str(run.id),
                    "content": run.output.get("summary", ""),
                    "metadata": {
                        "dimension": run.dimension,
                        "created_at": run.created_at.isoformat(),
                    },
                }
                for run in runs
            ]

    async def health_check(self) -> bool:
        try:
            async with self.db_factory() as db:
                await db.execute(select(1))
            return True
        except Exception:
            return False
```

---

## Part 2: Dynamic DAG Planner

### 2.1 현재 상태

```python
# backend/app/services/workflow_planner.py - 현재 하드코딩
WORKFLOW_TEMPLATES: Dict[str, WorkflowTemplate] = {
    "content_creation": WorkflowTemplate(
        tools=["prompt_generator", "storyboard", "image_tool"],  # 순서 고정!
        connections=[...],
    ),
}
```

### 2.2 목표 아키텍처

**Reference**: [Temporal DAG](https://temporal.io/code-exchange/temporalgraph-graph-based-orchestration), [LangGraph](https://context7.com/langchain-ai/langgraph/llms.txt)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Dynamic DAG Planner Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Intent → [Intent Analyzer] → [Tool Capability Matcher]                 │
│                      ↓                                                       │
│              [Dependency Graph Builder]                                      │
│                      ↓                                                       │
│              [Topological Sort]                                              │
│                      ↓                                                       │
│              [Executable DAG]                                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Tool Capability Registry                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  Tool: "reference_decoder"                                          │    │
│  │  ├── Input Schema: { video_url: string, focus_areas: string[] }     │    │
│  │  ├── Output Schema: { composition, lighting, color, recommendations }│    │
│  │  └── Can Provide: ["style_hint", "mood", "color_palette"]           │    │
│  │                                                                      │    │
│  │  Tool: "story_architect"                                            │    │
│  │  ├── Input Schema: { concept: string, style_hint?: string }         │    │
│  │  ├── Output Schema: { synopsis, characters, scenes }                │    │
│  │  ├── Can Consume: ["style_hint", "reference_analysis"]              │    │
│  │  └── Can Provide: ["story_structure", "character_profiles"]         │    │
│  │                                                                      │    │
│  │  ... (10개 도구)                                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Tool Capability Registry

```python
# backend/app/workflow/tool_capability_registry.py

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel
from enum import Enum


class DataType(str, Enum):
    """데이터 타입 (도구 간 호환성 체크용)"""
    TEXT = "text"
    STRUCTURED_JSON = "structured_json"
    IMAGE_URL = "image_url"
    VIDEO_URL = "video_url"
    AUDIO_URL = "audio_url"
    STYLE_HINT = "style_hint"
    STORY_STRUCTURE = "story_structure"
    SCENE_LIST = "scene_list"
    PROMPT = "prompt"
    ANALYSIS_RESULT = "analysis_result"


class PortSpec(BaseModel):
    """입출력 포트 명세"""
    name: str
    data_type: DataType
    required: bool = True
    description: str = ""


class ToolCapability(BaseModel):
    """도구 역량 명세"""
    tool_id: str
    display_name: str
    dimension: str  # "1D", "2D", "3D", "4D", "AD", "SC", etc.

    # I/O Schemas
    input_ports: List[PortSpec]
    output_ports: List[PortSpec]

    # Semantic Capabilities
    can_consume: Set[DataType]  # 입력으로 받을 수 있는 데이터 타입
    can_provide: Set[DataType]  # 출력으로 제공할 수 있는 데이터 타입

    # Execution Properties
    credit_cost: int
    avg_latency_ms: int
    requires_human_review: bool = False

    # Dependencies (optional hard constraints)
    required_prior_tools: List[str] = []
    incompatible_with: List[str] = []


class ToolCapabilityRegistry:
    """도구 역량 레지스트리"""

    def __init__(self):
        self._tools: Dict[str, ToolCapability] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}

    def register(self, capability: ToolCapability) -> None:
        """도구 등록"""
        self._tools[capability.tool_id] = capability
        self._rebuild_dependency_graph()

    def get_compatible_predecessors(self, tool_id: str) -> List[str]:
        """
        특정 도구의 입력을 제공할 수 있는 모든 도구 반환

        Returns:
            List of tool_ids that can provide input for this tool
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return []

        predecessors = []
        for other_id, other_tool in self._tools.items():
            if other_id == tool_id:
                continue
            # 출력이 입력과 호환되는지 체크
            if other_tool.can_provide & tool.can_consume:
                predecessors.append(other_id)

        return predecessors

    def get_compatible_successors(self, tool_id: str) -> List[str]:
        """
        특정 도구의 출력을 받을 수 있는 모든 도구 반환
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return []

        successors = []
        for other_id, other_tool in self._tools.items():
            if other_id == tool_id:
                continue
            if tool.can_provide & other_tool.can_consume:
                successors.append(other_id)

        return successors

    def _rebuild_dependency_graph(self) -> None:
        """의존성 그래프 재구축"""
        self._dependency_graph.clear()
        for tool_id, tool in self._tools.items():
            self._dependency_graph[tool_id] = set()
            for req in tool.required_prior_tools:
                if req in self._tools:
                    self._dependency_graph[tool_id].add(req)


# 초기 도구 정의 (SSoT)
TOOL_CAPABILITIES: List[ToolCapability] = [
    ToolCapability(
        tool_id="reference_decoder",
        display_name="레퍼런스 해석기",
        dimension="4D",
        input_ports=[
            PortSpec(name="video_url", data_type=DataType.VIDEO_URL, required=False),
            PortSpec(name="video_description", data_type=DataType.TEXT, required=True),
        ],
        output_ports=[
            PortSpec(name="composition", data_type=DataType.ANALYSIS_RESULT),
            PortSpec(name="lighting", data_type=DataType.ANALYSIS_RESULT),
            PortSpec(name="color", data_type=DataType.ANALYSIS_RESULT),
            PortSpec(name="recommendations", data_type=DataType.STYLE_HINT),
        ],
        can_consume={DataType.VIDEO_URL, DataType.TEXT},
        can_provide={DataType.ANALYSIS_RESULT, DataType.STYLE_HINT},
        credit_cost=10,
        avg_latency_ms=5000,
        requires_human_review=True,  # P0: HITL 지점
    ),
    ToolCapability(
        tool_id="story_architect",
        display_name="시나리오 생성기",
        dimension="STORY",
        input_ports=[
            PortSpec(name="concept", data_type=DataType.TEXT, required=True),
            PortSpec(name="style_hint", data_type=DataType.STYLE_HINT, required=False),
        ],
        output_ports=[
            PortSpec(name="synopsis", data_type=DataType.TEXT),
            PortSpec(name="scenes", data_type=DataType.SCENE_LIST),
        ],
        can_consume={DataType.TEXT, DataType.STYLE_HINT, DataType.ANALYSIS_RESULT},
        can_provide={DataType.STORY_STRUCTURE, DataType.SCENE_LIST, DataType.TEXT},
        credit_cost=10,
        avg_latency_ms=8000,
    ),
    # ... 나머지 도구들
]
```

### 2.4 Dynamic DAG Builder

```python
# backend/app/workflow/dag_builder.py

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import uuid


@dataclass
class DAGNode:
    """DAG 노드"""
    node_id: str
    tool_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)  # node_ids
    requires_human_review: bool = False


@dataclass
class DAGEdge:
    """DAG 엣지 (데이터 흐름)"""
    from_node_id: str
    from_port: str
    to_node_id: str
    to_port: str


@dataclass
class ExecutableDAG:
    """실행 가능한 DAG"""
    dag_id: str
    nodes: Dict[str, DAGNode]
    edges: List[DAGEdge]
    execution_order: List[str]  # Topological sorted node_ids
    human_review_points: List[str]  # HITL checkpoint node_ids
    estimated_credits: int
    estimated_latency_ms: int


class DynamicDAGBuilder:
    """동적 DAG 빌더"""

    def __init__(self, registry: ToolCapabilityRegistry):
        self.registry = registry

    async def build_from_intent(
        self,
        intent: str,
        selected_tools: List[str],
        initial_inputs: Dict[str, Any],
        llm_client: Any,
    ) -> ExecutableDAG:
        """
        의도와 선택된 도구로부터 DAG 구축

        Args:
            intent: 사용자 의도 (자연어)
            selected_tools: 사용할 도구 목록
            initial_inputs: 초기 입력 데이터
            llm_client: LLM 클라이언트 (연결 추론용)

        Returns:
            ExecutableDAG ready for execution
        """
        # 1. 도구 역량 조회
        tools = [self.registry._tools[t] for t in selected_tools if t in self.registry._tools]

        # 2. 의존성 분석
        dependencies = self._analyze_dependencies(tools)

        # 3. 노드 생성
        nodes = self._create_nodes(tools, initial_inputs)

        # 4. 엣지 생성 (데이터 흐름)
        edges = await self._infer_edges(nodes, tools, intent, llm_client)

        # 5. 위상 정렬
        execution_order = self._topological_sort(nodes, dependencies)

        # 6. HITL 지점 식별
        hitl_points = [
            node_id for node_id, node in nodes.items()
            if node.requires_human_review
        ]

        return ExecutableDAG(
            dag_id=str(uuid.uuid4()),
            nodes=nodes,
            edges=edges,
            execution_order=execution_order,
            human_review_points=hitl_points,
            estimated_credits=sum(t.credit_cost for t in tools),
            estimated_latency_ms=sum(t.avg_latency_ms for t in tools),
        )

    def _analyze_dependencies(
        self,
        tools: List[ToolCapability],
    ) -> Dict[str, Set[str]]:
        """도구 간 의존성 분석 (can_consume/can_provide 기반)"""
        dependencies: Dict[str, Set[str]] = {t.tool_id: set() for t in tools}

        tool_map = {t.tool_id: t for t in tools}

        for tool in tools:
            for other_id, other_tool in tool_map.items():
                if other_id == tool.tool_id:
                    continue
                # other가 제공하는 것을 tool이 소비할 수 있으면 의존성
                if other_tool.can_provide & tool.can_consume:
                    dependencies[tool.tool_id].add(other_id)

        return dependencies

    def _topological_sort(
        self,
        nodes: Dict[str, DAGNode],
        dependencies: Dict[str, Set[str]],
    ) -> List[str]:
        """위상 정렬 (Kahn's algorithm)"""
        # In-degree 계산
        in_degree = {node_id: 0 for node_id in nodes}
        for node_id, deps in dependencies.items():
            for dep in deps:
                if dep in nodes:
                    in_degree[node_id] += 1

        # 큐 초기화 (in-degree 0인 노드들)
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # 이 노드에 의존하는 노드들의 in-degree 감소
            for other_id, deps in dependencies.items():
                if node_id in deps:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        return result
```

### 2.5 Intent-based Tool Selection

```python
# backend/app/workflow/intent_analyzer.py

from typing import List, Dict, Any, Tuple


class IntentAnalyzer:
    """의도 분석기 - LLM 기반 도구 선택"""

    def __init__(
        self,
        registry: ToolCapabilityRegistry,
        llm_client: Any,
    ):
        self.registry = registry
        self.llm = llm_client

    async def analyze_and_select(
        self,
        user_intent: str,
        context: Dict[str, Any],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        사용자 의도 분석 및 도구 선택

        Args:
            user_intent: 사용자 요청 (자연어)
            context: 추가 컨텍스트

        Returns:
            (selected_tool_ids, extracted_params)
        """
        tools = list(self.registry._tools.values())

        prompt = f"""
        사용자 요청: {user_intent}

        사용 가능한 도구:
        {self._format_tools(tools)}

        이 요청을 처리하기 위해 필요한 도구를 선택하고,
        요청에서 추출 가능한 파라미터를 식별하세요.

        JSON 형식으로 응답:
        {{
            "selected_tools": ["tool_id_1", "tool_id_2"],
            "extracted_params": {{
                "topic": "추출된 주제",
                "style": "추출된 스타일"
            }},
            "reasoning": "선택 이유"
        }}
        """

        response = await self.llm.generate(prompt)
        parsed = self._parse_response(response)

        return parsed["selected_tools"], parsed["extracted_params"]
```

---

## Part 3: HITL Checkpoint System

### 3.1 현재 상태

```python
# backend/app/schemas/workflow_session.py - PAUSED 상태는 있으나 미사용
class WorkflowStatus(str, Enum):
    PAUSED = "paused"  # 일시 중지 (사용자 입력 대기)
```

### 3.2 목표 아키텍처

**Reference**: [LangGraph interrupt()](https://docs.langchain.com/oss/python/langchain/human-in-the-loop), [Microsoft Checkpointing](https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/checkpointing-and-resuming)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HITL Checkpoint System Architecture                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Workflow Execution:                                                         │
│                                                                              │
│  [Tool 1] → [Tool 2] → [CHECKPOINT] → [Tool 3] → [Tool 4] → [END]           │
│                             ↓                                                │
│                      [Pause & Save State]                                    │
│                             ↓                                                │
│                      [Notify Frontend]                                       │
│                             ↓                                                │
│                      [Wait for Human Input]                                  │
│                             ↓                                                │
│                      [Resume with Decision]                                  │
│                             ↓                                                │
│                      [Continue Execution]                                    │
│                                                                              │
│  Human Actions at Checkpoint:                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   APPROVE   │  │    EDIT     │  │   REJECT    │  │ REGENERATE  │        │
│  │  (as-is)    │  │ (with mods) │  │ (stop flow) │  │ (retry node)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Checkpoint 데이터 모델

```python
# backend/app/models_checkpoint.py

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class CheckpointStatus(str, enum.Enum):
    """체크포인트 상태"""
    PENDING = "pending"          # 인간 입력 대기
    APPROVED = "approved"        # 승인됨
    EDITED = "edited"            # 수정 후 승인
    REJECTED = "rejected"        # 거부됨
    REGENERATED = "regenerated"  # 재생성 요청
    EXPIRED = "expired"          # 타임아웃


class WorkflowCheckpoint(Base):
    """워크플로우 체크포인트 (HITL 지점)"""
    __tablename__ = "workflow_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_session_id = Column(String, nullable=False, index=True)
    node_id = Column(String, nullable=False)
    tool_id = Column(String, nullable=False)

    # 상태
    status = Column(SQLEnum(CheckpointStatus), default=CheckpointStatus.PENDING)

    # 체크포인트 데이터
    node_output = Column(JSON, nullable=False)           # 노드 실행 결과
    workflow_state_snapshot = Column(JSON, nullable=False)  # 전체 상태 스냅샷

    # 인간 입력
    human_decision = Column(String, nullable=True)       # approve/edit/reject/regenerate
    human_edits = Column(JSON, nullable=True)            # 수정 내용
    human_feedback = Column(String, nullable=True)       # 피드백 메시지

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)         # 타임아웃
    resolved_at = Column(DateTime, nullable=True)        # 해결 시점


class CheckpointNotification(Base):
    """체크포인트 알림"""
    __tablename__ = "checkpoint_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkpoint_id = Column(UUID(as_uuid=True), ForeignKey("workflow_checkpoints.id"))
    user_id = Column(String, nullable=False, index=True)

    # 알림 상태
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # 알림 채널
    channel = Column(String, default="in_app")  # in_app, email, websocket
```

### 3.4 Checkpoint Service

```python
# backend/app/services/checkpoint_service.py

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import asyncio

from app.models_checkpoint import WorkflowCheckpoint, CheckpointStatus, CheckpointNotification


class CheckpointService:
    """HITL 체크포인트 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._pending_checkpoints: Dict[str, asyncio.Event] = {}

    async def create_checkpoint(
        self,
        workflow_session_id: str,
        node_id: str,
        tool_id: str,
        node_output: Dict[str, Any],
        workflow_state: Dict[str, Any],
        timeout_hours: int = 24,
    ) -> WorkflowCheckpoint:
        """
        체크포인트 생성 (워크플로우 일시정지)

        Args:
            workflow_session_id: 워크플로우 세션 ID
            node_id: 현재 노드 ID
            tool_id: 도구 ID
            node_output: 노드 실행 결과
            workflow_state: 전체 워크플로우 상태 스냅샷
            timeout_hours: 타임아웃 (시간)

        Returns:
            생성된 체크포인트
        """
        checkpoint = WorkflowCheckpoint(
            workflow_session_id=workflow_session_id,
            node_id=node_id,
            tool_id=tool_id,
            node_output=node_output,
            workflow_state_snapshot=workflow_state,
            expires_at=datetime.utcnow() + timedelta(hours=timeout_hours),
        )

        self.db.add(checkpoint)
        await self.db.commit()
        await self.db.refresh(checkpoint)

        # 대기 이벤트 생성
        self._pending_checkpoints[str(checkpoint.id)] = asyncio.Event()

        return checkpoint

    async def wait_for_human_input(
        self,
        checkpoint_id: str,
        timeout_seconds: Optional[int] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """
        인간 입력 대기 (블로킹)

        Args:
            checkpoint_id: 체크포인트 ID
            timeout_seconds: 타임아웃 (초), None이면 무제한

        Returns:
            해결된 체크포인트 또는 None (타임아웃)
        """
        event = self._pending_checkpoints.get(checkpoint_id)
        if not event:
            return None

        try:
            if timeout_seconds:
                await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            else:
                await event.wait()
        except asyncio.TimeoutError:
            # 타임아웃 처리
            await self._mark_expired(checkpoint_id)
            return None

        # 해결된 체크포인트 반환
        return await self.get_checkpoint(checkpoint_id)

    async def resolve_checkpoint(
        self,
        checkpoint_id: str,
        decision: str,  # "approve", "edit", "reject", "regenerate"
        edits: Optional[Dict[str, Any]] = None,
        feedback: Optional[str] = None,
    ) -> WorkflowCheckpoint:
        """
        체크포인트 해결 (인간 결정)

        Args:
            checkpoint_id: 체크포인트 ID
            decision: 결정 유형
            edits: 수정 내용 (decision="edit"일 때)
            feedback: 피드백 메시지

        Returns:
            해결된 체크포인트
        """
        status_map = {
            "approve": CheckpointStatus.APPROVED,
            "edit": CheckpointStatus.EDITED,
            "reject": CheckpointStatus.REJECTED,
            "regenerate": CheckpointStatus.REGENERATED,
        }

        await self.db.execute(
            update(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.id == checkpoint_id)
            .values(
                status=status_map.get(decision, CheckpointStatus.APPROVED),
                human_decision=decision,
                human_edits=edits,
                human_feedback=feedback,
                resolved_at=datetime.utcnow(),
            )
        )
        await self.db.commit()

        # 대기 중인 워크플로우 깨우기
        event = self._pending_checkpoints.get(checkpoint_id)
        if event:
            event.set()

        return await self.get_checkpoint(checkpoint_id)

    async def get_pending_checkpoints(
        self,
        user_id: str,
    ) -> list[WorkflowCheckpoint]:
        """사용자의 대기 중인 체크포인트 목록"""
        result = await self.db.execute(
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.status == CheckpointStatus.PENDING)
            # TODO: user_id 필터링 (workflow_session과 조인)
            .order_by(WorkflowCheckpoint.created_at.desc())
        )
        return result.scalars().all()
```

### 3.5 Workflow Executor with HITL

```python
# backend/app/services/hitl_workflow_executor.py

from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.services.checkpoint_service import CheckpointService
from app.workflow.dag_builder import ExecutableDAG, DAGNode


@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    output: Dict[str, Any]
    checkpoint_id: Optional[str] = None  # HITL 일시정지 시
    error: Optional[str] = None


class HITLWorkflowExecutor:
    """Human-in-the-Loop 워크플로우 실행기"""

    def __init__(
        self,
        checkpoint_service: CheckpointService,
        tool_executor: Any,  # 기존 execute_step 함수
    ):
        self.checkpoint_service = checkpoint_service
        self.tool_executor = tool_executor

    async def execute_dag(
        self,
        dag: ExecutableDAG,
        initial_inputs: Dict[str, Any],
        user: Dict[str, Any],
        db: Any,
        byok_key: Optional[str] = None,
    ) -> ExecutionResult:
        """
        DAG 실행 (HITL 체크포인트 지원)

        HITL 노드에서 일시정지하고 인간 입력 대기
        """
        outputs: Dict[str, Dict[str, Any]] = {}
        current_inputs = initial_inputs.copy()

        for node_id in dag.execution_order:
            node = dag.nodes[node_id]

            # 1. 노드 입력 준비 (이전 노드 출력 + 초기 입력)
            node_inputs = self._prepare_inputs(node, outputs, current_inputs, dag.edges)

            # 2. 노드 실행
            result = await self.tool_executor(
                tool_id=node.tool_id,
                inputs=node_inputs,
                user=user,
                db=db,
                byok_key=byok_key,
            )

            if not result.success:
                return ExecutionResult(
                    success=False,
                    output=outputs,
                    error=result.error,
                )

            outputs[node_id] = result.output

            # 3. HITL 체크포인트 확인
            if node.requires_human_review:
                checkpoint = await self.checkpoint_service.create_checkpoint(
                    workflow_session_id=dag.dag_id,
                    node_id=node_id,
                    tool_id=node.tool_id,
                    node_output=result.output,
                    workflow_state={"outputs": outputs, "current_node": node_id},
                )

                # 일시정지 및 인간 입력 대기
                resolved = await self.checkpoint_service.wait_for_human_input(
                    str(checkpoint.id),
                    timeout_seconds=3600 * 24,  # 24시간
                )

                if not resolved or resolved.status.value == "rejected":
                    return ExecutionResult(
                        success=False,
                        output=outputs,
                        checkpoint_id=str(checkpoint.id),
                        error="Workflow rejected by human reviewer",
                    )

                # 수정 사항 반영
                if resolved.human_edits:
                    outputs[node_id] = {**outputs[node_id], **resolved.human_edits}

                # 재생성 요청 시
                if resolved.status.value == "regenerated":
                    # TODO: 노드 재실행 로직
                    pass

        return ExecutionResult(
            success=True,
            output=outputs,
        )

    def _prepare_inputs(
        self,
        node: DAGNode,
        outputs: Dict[str, Dict[str, Any]],
        initial_inputs: Dict[str, Any],
        edges: list,
    ) -> Dict[str, Any]:
        """노드 입력 준비 (데이터 흐름 추적)"""
        inputs = initial_inputs.copy()

        for edge in edges:
            if edge.to_node_id == node.node_id:
                source_output = outputs.get(edge.from_node_id, {})
                if edge.from_port in source_output:
                    inputs[edge.to_port] = source_output[edge.from_port]

        return inputs
```

### 3.6 Frontend Integration (API)

```python
# backend/app/routers/checkpoint.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/checkpoints", tags=["HITL Checkpoints"])


class CheckpointResponse(BaseModel):
    id: str
    workflow_session_id: str
    node_id: str
    tool_id: str
    status: str
    node_output: Dict[str, Any]
    created_at: str
    expires_at: Optional[str]


class ResolveCheckpointRequest(BaseModel):
    decision: str  # "approve", "edit", "reject", "regenerate"
    edits: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None


@router.get("/pending", response_model=List[CheckpointResponse])
async def get_pending_checkpoints(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """대기 중인 체크포인트 목록 조회"""
    service = CheckpointService(db)
    checkpoints = await service.get_pending_checkpoints(current_user["id"])
    return [_to_response(cp) for cp in checkpoints]


@router.post("/{checkpoint_id}/resolve", response_model=CheckpointResponse)
async def resolve_checkpoint(
    checkpoint_id: str,
    request: ResolveCheckpointRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """체크포인트 해결 (인간 결정)"""
    service = CheckpointService(db)

    checkpoint = await service.resolve_checkpoint(
        checkpoint_id=checkpoint_id,
        decision=request.decision,
        edits=request.edits,
        feedback=request.feedback,
    )

    return _to_response(checkpoint)


@router.get("/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_id: str,
    db: AsyncSession = Depends(get_db),
):
    """체크포인트 상세 조회"""
    service = CheckpointService(db)
    checkpoint = await service.get_checkpoint(checkpoint_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return _to_response(checkpoint)
```

---

## Part 4: Implementation Roadmap

### Phase 1: Multi-RAG Router (Week 1-2)

```
Week 1:
├── [ ] RAGSourceSpec, RAGSourceBackend 인터페이스 정의
├── [ ] RAGSourceRegistry 구현
├── [ ] 기존 NotebookLM 백엔드 어댑터
├── [ ] 기존 Qdrant 백엔드 어댑터
└── [ ] UserHistoryRAGBackend 구현

Week 2:
├── [ ] IntelligentRAGRouter 구현 (규칙 기반)
├── [ ] LLM 기반 소스 선택 (복잡 쿼리용)
├── [ ] MultiRAGOrchestrator 구현
├── [ ] RRF Fusion 구현
└── [ ] 통합 테스트
```

### Phase 2: Dynamic DAG Planner (Week 3-4)

```
Week 3:
├── [ ] ToolCapability 모델 정의
├── [ ] ToolCapabilityRegistry 구현
├── [ ] 10개 도구 역량 정의 (SSoT)
├── [ ] 의존성 분석 로직
└── [ ] Topological Sort 구현

Week 4:
├── [ ] DynamicDAGBuilder 구현
├── [ ] IntentAnalyzer 구현 (LLM 기반)
├── [ ] 엣지 추론 로직
├── [ ] 기존 WorkflowExecutor 통합
└── [ ] 통합 테스트
```

### Phase 3: HITL Checkpoint System (Week 5-6)

```
Week 5:
├── [ ] WorkflowCheckpoint 모델 정의
├── [ ] Alembic 마이그레이션
├── [ ] CheckpointService 구현
├── [ ] 체크포인트 생성/대기/해결 로직
└── [ ] WebSocket 알림 (선택)

Week 6:
├── [ ] HITLWorkflowExecutor 구현
├── [ ] Checkpoint API 엔드포인트
├── [ ] Frontend Checkpoint UI 컴포넌트
├── [ ] E2E 테스트
└── [ ] 문서화
```

---

## Part 5: Code Quality Standards (2026)

### 5.1 Python/FastAPI Best Practices

**Reference**: [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

```python
# ✅ 올바른 async 패턴
async def query_rag(query: str) -> RAGResult:
    """Non-blocking I/O with async"""
    async with aiohttp.ClientSession() as session:
        result = await session.get(...)
    return result

# ❌ 잘못된 패턴 - async 내 blocking
async def bad_query(query: str):
    result = requests.get(...)  # BLOCKING!
    return result

# ✅ 의존성 주입 패턴
def get_rag_service(
    db: AsyncSession = Depends(get_db),
    registry: RAGSourceRegistry = Depends(get_registry),
) -> MultiRAGOrchestrator:
    return MultiRAGOrchestrator(registry, db)

# ✅ Pydantic Settings (타입 안전)
class RAGSettings(BaseSettings):
    notebooklm_timeout: int = 30
    qdrant_url: str = "http://localhost:6333"
    max_parallel_queries: int = 5

    model_config = SettingsConfigDict(env_prefix="RAG_")
```

### 5.2 Type Safety

```python
# ✅ 완전한 타입 힌트
from typing import TypeVar, Generic, Protocol

T = TypeVar("T")

class Repository(Protocol[T]):
    async def get(self, id: str) -> Optional[T]: ...
    async def save(self, entity: T) -> T: ...

# ✅ Literal types for exhaustive checks
from typing import Literal

Decision = Literal["approve", "edit", "reject", "regenerate"]

def handle_decision(decision: Decision) -> None:
    match decision:
        case "approve":
            ...
        case "edit":
            ...
        case "reject":
            ...
        case "regenerate":
            ...
```

### 5.3 Testing Strategy

```python
# tests/services/test_multi_rag_router.py

import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_registry():
    registry = RAGSourceRegistry()
    registry.register(
        RAGSourceSpec(
            source_id="test_notebooklm",
            source_type=RAGSourceType.AUTEUR_DNA,
            ...
        ),
        AsyncMock(spec=RAGSourceBackend),
    )
    return registry

@pytest.mark.asyncio
async def test_router_selects_auteur_source_for_auteur_query(mock_registry):
    """거장 관련 쿼리 시 NotebookLM 소스 선택"""
    router = IntelligentRAGRouter(mock_registry, AsyncMock())

    decision = await router.route(
        query="봉준호 감독의 계단 상징",
        context={"auteur_key": "bong"},
    )

    assert "test_notebooklm" in decision.selected_sources
    assert decision.confidence > 0.7
```

---

## Part 6: File Structure

```
backend/app/
├── rag/
│   ├── multi_rag_router.py        # NEW: Multi-RAG Router
│   ├── intelligent_router.py      # NEW: LLM-based routing
│   ├── backends/
│   │   ├── user_history.py        # NEW: User history backend
│   │   ├── template_kb.py         # NEW: Template KB backend
│   │   └── ...
│   └── ...
├── workflow/
│   ├── tool_capability_registry.py  # NEW: Tool capabilities
│   ├── dag_builder.py               # NEW: Dynamic DAG builder
│   ├── intent_analyzer.py           # NEW: Intent analysis
│   └── ...
├── services/
│   ├── checkpoint_service.py        # NEW: HITL checkpoints
│   ├── hitl_workflow_executor.py    # NEW: HITL executor
│   └── ...
├── models_checkpoint.py             # NEW: Checkpoint models
└── routers/
    └── checkpoint.py                # NEW: Checkpoint API
```

---

## References

### Research Papers
- [RAGRouter: Learning to Route Queries](https://arxiv.org/abs/2505.23052)
- [Multi-Agent RAG Framework](https://www.mdpi.com/2073-431X/14/12/525)

### Framework Documentation
- [Temporal Python SDK](https://context7.com/temporalio/sdk-python)
- [LangGraph Human-in-the-Loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Microsoft Agent Framework Checkpointing](https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/checkpointing-and-resuming)

### Best Practices
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [LlamaIndex Router](https://docs.llamaindex.ai/en/stable/examples/low_level/router/)
- [XState for React Workflows](https://stately.ai/docs/xstate-react)

---

*Generated with ultrathink analysis based on 2026 MCP research*

*Last Updated: 2026-01-16*
