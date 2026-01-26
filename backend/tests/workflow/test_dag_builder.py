"""Dynamic DAG Builder Tests (P0 2026).

Tests for ToolCapabilityRegistry, DynamicDAGBuilder, IntentAnalyzer.

Coverage:
    - ToolCapabilityRegistry: register, query, dependency analysis
    - DynamicDAGBuilder: DAG construction, topological sort, edge inference
    - IntentAnalyzer: keyword-based tool recommendation
"""
from __future__ import annotations

import pytest

from app.workflow import (
    DataType,
    PortSpec,
    ToolCapability,
    DAGNode,
    DAGEdge,
    ExecutableDAG,
    ToolCapabilityRegistry,
    get_tool_registry,
    reset_tool_registry,
    DynamicDAGBuilder,
    IntentAnalyzer,
    create_dag_builder,
    DAGBuildError,
    CyclicDependencyError,
    IncompatibleToolsError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def empty_registry():
    """Empty registry for isolated tests."""
    return ToolCapabilityRegistry()


@pytest.fixture
def sample_tool_a():
    """Sample tool A: text → analysis."""
    return ToolCapability(
        tool_id="tool_a",
        display_name="Tool A",
        dimension="TEST",
        description="Test tool A",
        input_ports=[
            PortSpec(
                name="text_input",
                data_type=DataType.TEXT,
                required=True,
            ),
        ],
        output_ports=[
            PortSpec(
                name="analysis_output",
                data_type=DataType.ANALYSIS_RESULT,
            ),
        ],
        can_consume={DataType.TEXT},
        can_provide={DataType.ANALYSIS_RESULT},
        credit_cost=5,
        avg_latency_ms=1000,
        tags=["test", "analysis"],
    )


@pytest.fixture
def sample_tool_b():
    """Sample tool B: analysis → style_hint."""
    return ToolCapability(
        tool_id="tool_b",
        display_name="Tool B",
        dimension="TEST",
        description="Test tool B - consumes analysis",
        input_ports=[
            PortSpec(
                name="analysis_input",
                data_type=DataType.ANALYSIS_RESULT,
                required=True,
            ),
        ],
        output_ports=[
            PortSpec(
                name="style_output",
                data_type=DataType.STYLE_HINT,
            ),
        ],
        can_consume={DataType.ANALYSIS_RESULT},
        can_provide={DataType.STYLE_HINT},
        credit_cost=8,
        avg_latency_ms=2000,
        required_prior_tools=["tool_a"],
        tags=["test", "style"],
    )


@pytest.fixture
def sample_tool_c():
    """Sample tool C: style_hint → image_url."""
    return ToolCapability(
        tool_id="tool_c",
        display_name="Tool C",
        dimension="TEST",
        description="Test tool C - consumes style",
        input_ports=[
            PortSpec(
                name="style_input",
                data_type=DataType.STYLE_HINT,
                required=True,
            ),
        ],
        output_ports=[
            PortSpec(
                name="image_output",
                data_type=DataType.IMAGE_URL,
            ),
        ],
        can_consume={DataType.STYLE_HINT},
        can_provide={DataType.IMAGE_URL},
        credit_cost=15,
        avg_latency_ms=5000,
        requires_human_review=True,
        tags=["test", "image"],
    )


@pytest.fixture
def sample_tool_incompatible():
    """Tool that is incompatible with tool_a."""
    return ToolCapability(
        tool_id="tool_incompatible",
        display_name="Incompatible Tool",
        dimension="TEST",
        description="Incompatible with tool_a",
        can_consume={DataType.TEXT},
        can_provide={DataType.PROMPT},
        credit_cost=5,
        avg_latency_ms=1000,
        incompatible_with=["tool_a"],
    )


@pytest.fixture
def registry_with_tools(empty_registry, sample_tool_a, sample_tool_b, sample_tool_c):
    """Registry with sample tools registered."""
    empty_registry.register(sample_tool_a)
    empty_registry.register(sample_tool_b)
    empty_registry.register(sample_tool_c)
    return empty_registry


# =============================================================================
# ToolCapabilityRegistry Tests
# =============================================================================

class TestToolCapabilityRegistry:
    """ToolCapabilityRegistry tests."""

    def test_register_tool(self, empty_registry, sample_tool_a):
        """Test tool registration."""
        empty_registry.register(sample_tool_a)

        assert "tool_a" in empty_registry
        assert len(empty_registry) == 1
        assert empty_registry.get("tool_a") == sample_tool_a

    def test_register_duplicate_raises(self, empty_registry, sample_tool_a):
        """Test duplicate registration raises error."""
        empty_registry.register(sample_tool_a)

        with pytest.raises(ValueError, match="already registered"):
            empty_registry.register(sample_tool_a)

    def test_register_many(self, empty_registry, sample_tool_a, sample_tool_b):
        """Test batch registration."""
        count = empty_registry.register_many([sample_tool_a, sample_tool_b])

        assert count == 2
        assert len(empty_registry) == 2

    def test_unregister(self, empty_registry, sample_tool_a):
        """Test tool unregistration."""
        empty_registry.register(sample_tool_a)
        result = empty_registry.unregister("tool_a")

        assert result is True
        assert "tool_a" not in empty_registry

    def test_unregister_nonexistent(self, empty_registry):
        """Test unregistering nonexistent tool."""
        result = empty_registry.unregister("nonexistent")
        assert result is False

    def test_get_all(self, registry_with_tools):
        """Test getting all tools."""
        tools = registry_with_tools.get_all()
        assert len(tools) == 3

    def test_get_enabled(self, registry_with_tools, sample_tool_a):
        """Test getting enabled tools only."""
        sample_tool_a.enabled = False
        enabled = registry_with_tools.get_enabled()

        # tool_a is disabled
        assert len(enabled) == 2
        assert all(t.enabled for t in enabled)

    def test_get_by_dimension(self, registry_with_tools):
        """Test filter by dimension."""
        tools = registry_with_tools.get_by_dimension("TEST")
        assert len(tools) == 3

        tools_other = registry_with_tools.get_by_dimension("OTHER")
        assert len(tools_other) == 0

    def test_get_by_tag(self, registry_with_tools):
        """Test filter by tag."""
        analysis_tools = registry_with_tools.get_by_tag("analysis")
        assert len(analysis_tools) == 1
        assert analysis_tools[0].tool_id == "tool_a"

        test_tools = registry_with_tools.get_by_tag("test")
        assert len(test_tools) == 3

    def test_find_compatible_tools_by_input(self, registry_with_tools):
        """Test finding tools by input type."""
        tools = registry_with_tools.find_compatible_tools(
            input_types={DataType.TEXT}
        )

        assert len(tools) == 1
        assert tools[0].tool_id == "tool_a"

    def test_find_compatible_tools_by_output(self, registry_with_tools):
        """Test finding tools by output type."""
        tools = registry_with_tools.find_compatible_tools(
            output_types={DataType.IMAGE_URL}
        )

        assert len(tools) == 1
        assert tools[0].tool_id == "tool_c"

    def test_find_providers(self, registry_with_tools):
        """Test finding provider tools."""
        providers = registry_with_tools.find_providers(DataType.ANALYSIS_RESULT)

        assert len(providers) == 1
        assert providers[0].tool_id == "tool_a"

    def test_find_consumers(self, registry_with_tools):
        """Test finding consumer tools."""
        consumers = registry_with_tools.find_consumers(DataType.STYLE_HINT)

        assert len(consumers) == 1
        assert consumers[0].tool_id == "tool_c"

    def test_can_connect(self, registry_with_tools):
        """Test connection check between tools."""
        # tool_a provides ANALYSIS_RESULT, tool_b consumes ANALYSIS_RESULT
        assert registry_with_tools.can_connect("tool_a", "tool_b") is True

        # tool_a provides ANALYSIS_RESULT, tool_c consumes STYLE_HINT
        assert registry_with_tools.can_connect("tool_a", "tool_c") is False

        # tool_b provides STYLE_HINT, tool_c consumes STYLE_HINT
        assert registry_with_tools.can_connect("tool_b", "tool_c") is True

    def test_can_connect_incompatible(
        self, empty_registry, sample_tool_a, sample_tool_incompatible
    ):
        """Test connection blocked by incompatibility."""
        empty_registry.register(sample_tool_a)
        empty_registry.register(sample_tool_incompatible)

        # Both can handle TEXT but are incompatible
        assert empty_registry.can_connect("tool_a", "tool_incompatible") is False

    def test_find_connectable_types(self, registry_with_tools):
        """Test finding connectable data types."""
        types = registry_with_tools.find_connectable_types("tool_a", "tool_b")
        assert DataType.ANALYSIS_RESULT in types

        types_empty = registry_with_tools.find_connectable_types("tool_a", "tool_c")
        assert len(types_empty) == 0

    def test_get_required_prior_tools(self, registry_with_tools):
        """Test getting required prior tools."""
        priors = registry_with_tools.get_required_prior_tools("tool_b")

        assert len(priors) == 1
        assert priors[0].tool_id == "tool_a"

    def test_get_incompatible_tools(
        self, empty_registry, sample_tool_a, sample_tool_incompatible
    ):
        """Test getting incompatible tools."""
        empty_registry.register(sample_tool_a)
        empty_registry.register(sample_tool_incompatible)

        incompatibles = empty_registry.get_incompatible_tools("tool_incompatible")

        assert len(incompatibles) == 1
        assert incompatibles[0].tool_id == "tool_a"

    def test_stats(self, registry_with_tools):
        """Test registry statistics."""
        stats = registry_with_tools.stats()

        assert stats["total"] == 3
        assert stats["enabled"] == 3
        assert stats["dimensions"]["TEST"] == 3
        assert stats["total_credit_cost"] == 28  # 5 + 8 + 15
        assert stats["hitl_required_count"] == 1  # tool_c


# =============================================================================
# DynamicDAGBuilder Tests
# =============================================================================

class TestDynamicDAGBuilder:
    """DynamicDAGBuilder tests."""

    @pytest.mark.asyncio
    async def test_build_simple_dag(self, registry_with_tools):
        """Test building a simple DAG."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a"],
            initial_inputs={"text_input": "Hello"},
        )

        assert isinstance(dag, ExecutableDAG)
        assert len(dag.nodes) == 1
        assert len(dag.execution_order) == 1
        assert dag.estimated_credits == 5

    @pytest.mark.asyncio
    async def test_build_linear_dag(self, registry_with_tools):
        """Test building a linear DAG with dependencies."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b", "tool_c"],
            initial_inputs={"text_input": "Hello"},
        )

        assert len(dag.nodes) == 3
        assert len(dag.execution_order) == 3

        # Topological order: tool_a → tool_b → tool_c
        order = dag.execution_order
        node_tool_ids = [dag.nodes[nid].tool_id for nid in order]

        assert node_tool_ids.index("tool_a") < node_tool_ids.index("tool_b")
        assert node_tool_ids.index("tool_b") < node_tool_ids.index("tool_c")

    @pytest.mark.asyncio
    async def test_auto_add_dependencies(self, registry_with_tools):
        """Test automatic dependency addition."""
        builder = DynamicDAGBuilder(
            registry_with_tools,
            auto_add_dependencies=True,
        )

        # Only select tool_b, which requires tool_a
        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_b"],
            initial_inputs={"text_input": "Hello"},
        )

        # tool_a should be auto-added
        tool_ids = {node.tool_id for node in dag.nodes.values()}
        assert "tool_a" in tool_ids
        assert "tool_b" in tool_ids

    @pytest.mark.asyncio
    async def test_edge_inference(self, registry_with_tools):
        """Test automatic edge inference."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b"],
            initial_inputs={"text_input": "Hello"},
        )

        # Should have edge from tool_a to tool_b
        assert len(dag.edges) >= 1

        # Find edge connecting tool_a output to tool_b input
        found_edge = False
        for edge in dag.edges:
            from_node = dag.nodes[edge.from_node_id]
            to_node = dag.nodes[edge.to_node_id]
            if from_node.tool_id == "tool_a" and to_node.tool_id == "tool_b":
                assert edge.data_type == DataType.ANALYSIS_RESULT
                found_edge = True

        assert found_edge, "Expected edge from tool_a to tool_b not found"

    @pytest.mark.asyncio
    async def test_hitl_checkpoint_identification(self, registry_with_tools):
        """Test HITL checkpoint identification."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b", "tool_c"],
            initial_inputs={"text_input": "Hello"},
        )

        # tool_c has requires_human_review=True
        assert len(dag.human_review_points) == 1

        hitl_node = dag.nodes[dag.human_review_points[0]]
        assert hitl_node.tool_id == "tool_c"

    @pytest.mark.asyncio
    async def test_credit_estimation(self, registry_with_tools):
        """Test credit estimation."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b", "tool_c"],
            initial_inputs={"text_input": "Hello"},
        )

        # tool_a=5, tool_b=8, tool_c=15
        assert dag.estimated_credits == 28

    @pytest.mark.asyncio
    async def test_latency_estimation(self, registry_with_tools):
        """Test latency estimation."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b", "tool_c"],
            initial_inputs={"text_input": "Hello"},
        )

        # tool_a=1000, tool_b=2000, tool_c=5000
        assert dag.estimated_latency_ms == 8000

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, registry_with_tools):
        """Test unknown tool raises error."""
        builder = DynamicDAGBuilder(registry_with_tools)

        with pytest.raises(DAGBuildError, match="Unknown tools"):
            await builder.build_from_intent(
                intent="Test workflow",
                selected_tools=["nonexistent_tool"],
                initial_inputs={},
            )

    @pytest.mark.asyncio
    async def test_incompatible_tools_raises(
        self, empty_registry, sample_tool_a, sample_tool_incompatible
    ):
        """Test incompatible tools raise error."""
        empty_registry.register(sample_tool_a)
        empty_registry.register(sample_tool_incompatible)

        builder = DynamicDAGBuilder(empty_registry, auto_add_dependencies=False)

        with pytest.raises(IncompatibleToolsError):
            await builder.build_from_intent(
                intent="Test workflow",
                selected_tools=["tool_a", "tool_incompatible"],
                initial_inputs={},
            )

    @pytest.mark.asyncio
    async def test_dag_metadata(self, registry_with_tools):
        """Test DAG metadata preservation."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Create storyboard",
            selected_tools=["tool_a"],
            initial_inputs={"text_input": "Hello"},
            user_context={"auteur_key": "bong"},
        )

        assert dag.metadata["intent"] == "Create storyboard"
        assert dag.metadata["user_context"]["auteur_key"] == "bong"

    @pytest.mark.asyncio
    async def test_dag_to_dict(self, registry_with_tools):
        """Test DAG serialization."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b"],
            initial_inputs={"text_input": "Hello"},
        )

        dag_dict = dag.to_dict()

        assert "dag_id" in dag_dict
        assert "nodes" in dag_dict
        assert "edges" in dag_dict
        assert "execution_order" in dag_dict
        assert isinstance(dag_dict["nodes"], dict)

    @pytest.mark.asyncio
    async def test_dag_graph_methods(self, registry_with_tools):
        """Test DAG graph traversal methods."""
        builder = DynamicDAGBuilder(registry_with_tools)

        dag = await builder.build_from_intent(
            intent="Test workflow",
            selected_tools=["tool_a", "tool_b", "tool_c"],
            initial_inputs={"text_input": "Hello"},
        )

        # Find tool_b node
        tool_b_node_id = None
        for node_id, node in dag.nodes.items():
            if node.tool_id == "tool_b":
                tool_b_node_id = node_id
                break

        assert tool_b_node_id is not None

        # Get successors (should include tool_c)
        successors = dag.get_successors(tool_b_node_id)
        successor_tool_ids = [dag.nodes[nid].tool_id for nid in successors]
        assert "tool_c" in successor_tool_ids

        # Get predecessors (should include tool_a)
        predecessors = dag.get_predecessors(tool_b_node_id)
        predecessor_tool_ids = [dag.nodes[nid].tool_id for nid in predecessors]
        assert "tool_a" in predecessor_tool_ids


# =============================================================================
# IntentAnalyzer Tests
# =============================================================================

class TestIntentAnalyzer:
    """IntentAnalyzer tests."""

    @pytest.mark.asyncio
    async def test_analyze_storyboard_intent(self):
        """Test storyboard intent analysis."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("스토리보드 만들기")

        assert "story_architect" in tools or "storyboard_generator" in tools

    @pytest.mark.asyncio
    async def test_analyze_reference_intent(self):
        """Test reference analysis intent."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("레퍼런스 분석")

        assert "reference_decoder" in tools

    @pytest.mark.asyncio
    async def test_analyze_image_intent(self):
        """Test image generation intent."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("이미지 생성")

        assert "prompt_composer" in tools or "image_generator" in tools

    @pytest.mark.asyncio
    async def test_analyze_video_intent(self):
        """Test video generation intent."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("video generation")

        assert "video_generator" in tools

    @pytest.mark.asyncio
    async def test_analyze_default_fallback(self):
        """Test default fallback for unknown intent."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("xyz123 completely random")

        # Should fallback to prompt_composer
        assert "prompt_composer" in tools

    @pytest.mark.asyncio
    async def test_analyze_multiple_keywords(self):
        """Test intent with multiple matching keywords."""
        reset_tool_registry()
        registry = get_tool_registry()
        analyzer = IntentAnalyzer(registry)

        tools = await analyzer.analyze("레퍼런스 분석 후 이미지 생성")

        # Should match both reference and image
        assert "reference_decoder" in tools
        assert "prompt_composer" in tools or "image_generator" in tools


# =============================================================================
# Global Registry Tests
# =============================================================================

class TestGlobalRegistry:
    """Global tool registry tests."""

    def test_get_tool_registry_singleton(self):
        """Test global registry is singleton."""
        reset_tool_registry()
        reg1 = get_tool_registry()
        reg2 = get_tool_registry()

        assert reg1 is reg2

    def test_global_registry_has_default_tools(self):
        """Test global registry has default tools."""
        reset_tool_registry()
        registry = get_tool_registry()

        # Default tools should be registered
        assert "reference_decoder" in registry
        assert "story_architect" in registry
        assert "storyboard_generator" in registry
        assert "prompt_composer" in registry
        assert "image_generator" in registry
        assert "video_generator" in registry

    def test_reset_tool_registry(self):
        """Test registry reset."""
        reset_tool_registry()
        reg1 = get_tool_registry()

        reset_tool_registry()
        reg2 = get_tool_registry()

        # After reset, should be new instance
        assert reg1 is not reg2


# =============================================================================
# Integration Tests
# =============================================================================

class TestWorkflowIntegration:
    """Integration tests for the full workflow system."""

    @pytest.mark.asyncio
    async def test_full_pipeline_storyboard(self):
        """Test full pipeline: analyze → build → verify."""
        reset_tool_registry()
        registry = get_tool_registry()

        # 1. Analyze intent
        analyzer = IntentAnalyzer(registry)
        recommended_tools = await analyzer.analyze("SF 영화 스토리보드 생성")

        assert len(recommended_tools) > 0

        # 2. Build DAG
        builder = DynamicDAGBuilder(registry)
        dag = await builder.build_from_intent(
            intent="SF 영화 스토리보드 생성",
            selected_tools=["story_architect", "storyboard_generator"],
            initial_inputs={"concept": "우주 탐험"},
            user_context={"auteur_key": "epoch"},
        )

        # 3. Verify DAG structure
        assert dag.dag_id.startswith("dag_")
        assert len(dag.nodes) >= 2
        assert len(dag.execution_order) >= 2

        # story_architect should come before storyboard_generator
        order = dag.execution_order
        node_tool_ids = [dag.nodes[nid].tool_id for nid in order]
        assert node_tool_ids.index("story_architect") < node_tool_ids.index("storyboard_generator")

    @pytest.mark.asyncio
    async def test_full_pipeline_reference_analysis(self):
        """Test full pipeline for reference analysis."""
        reset_tool_registry()
        registry = get_tool_registry()

        builder = DynamicDAGBuilder(registry)
        dag = await builder.build_from_intent(
            intent="레퍼런스 분석",
            selected_tools=["reference_decoder"],
            initial_inputs={
                "description": "강주노 기생충 계단 씬",
            },
        )

        assert len(dag.nodes) == 1
        assert dag.human_review_points  # reference_decoder requires HITL

    @pytest.mark.asyncio
    async def test_create_dag_builder_factory(self):
        """Test factory function."""
        reset_tool_registry()

        builder = create_dag_builder()

        assert isinstance(builder, DynamicDAGBuilder)

        dag = await builder.build_from_intent(
            intent="Test",
            selected_tools=["prompt_composer"],
            initial_inputs={"user_input": "test"},
        )

        assert dag is not None
