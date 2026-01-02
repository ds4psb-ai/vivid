"""
Unit Tests for MCP Servers

Coverage Target: 80%+
"""
import pytest
from app.mcp_servers import MCPServerBase, mcp_tool, mcp_resource
from app.mcp_servers.pattern_truth_mcp import PatternTruthMCP, pattern_truth_mcp


class TestMCPServerBase:
    """MCP 서버 베이스 테스트"""
    
    def test_pattern_truth_initialization(self):
        """Pattern Truth MCP 초기화"""
        mcp = PatternTruthMCP()
        
        assert mcp.name == "pattern-truth"
        assert mcp.version == "1.0.0"
    
    def test_list_tools(self):
        """도구 목록 조회"""
        tools = pattern_truth_mcp.list_tools()
        
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "compute_stpf" in tool_names
        assert "update_confidence" in tool_names
        assert "calculate_kelly" in tool_names
        assert "analyze_sensitivity" in tool_names
    
    def test_list_resources(self):
        """리소스 목록 조회"""
        resources = pattern_truth_mcp.list_resources()
        
        assert len(resources) == 2
        resource_names = [r.name for r in resources]
        assert "Health Check" in resource_names
        assert "Configuration" in resource_names
    
    def test_get_server_info(self):
        """서버 정보 조회"""
        info = pattern_truth_mcp.get_server_info()
        
        assert info["name"] == "pattern-truth"
        assert info["protocol"] == "streamable-http"
        assert info["tools"] == 4
        assert info["resources"] == 2


class TestPatternTruthMCPTools:
    """Pattern Truth MCP 도구 테스트"""
    
    @pytest.mark.asyncio
    async def test_compute_stpf(self):
        """STPF 계산 도구"""
        result = await pattern_truth_mcp.compute_stpf(
            trust=7, legality=8, hygiene=6,
            essence=7, capability=6, novelty=5, proof=6,
            cost=5, risk=6, uncertainty=4,
        )
        
        assert result["status"] == "OK"
        assert result["score"] > 0
        assert result["grade"] is not None
        assert "recommendation" in result
    
    @pytest.mark.asyncio
    async def test_compute_stpf_gate_fail(self):
        """STPF 게이트 실패"""
        result = await pattern_truth_mcp.compute_stpf(
            trust=2,  # Gate fail
            legality=8, hygiene=6,
        )
        
        assert result["status"] == "GATE_FAIL"
        assert result["score"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_sensitivity(self):
        """민감도 분석 도구"""
        result = await pattern_truth_mcp.analyze_sensitivity(
            trust=7, legality=8, hygiene=6,
            essence=7, capability=6, novelty=5, proof=6,
            cost=5, risk=6, uncertainty=4,
        )
        
        assert result["status"] == "OK"
        assert result["base_score"] > 0
        assert "leverage_point" in result
        assert "action_plan" in result
    
    @pytest.mark.asyncio
    async def test_update_confidence(self):
        """베이지안 갱신 도구"""
        result = await pattern_truth_mcp.update_confidence(
            rule_id="test_rule",
            supports_rule=True,
            strength=0.9,
            prior_confidence=0.5,
        )
        
        assert result["rule_id"] == "test_rule"
        assert result["posterior"] > result["prior"]
        assert result["delta"] > 0
        assert "interpretation" in result
    
    @pytest.mark.asyncio
    async def test_update_confidence_refute(self):
        """베이지안 반박 갱신"""
        result = await pattern_truth_mcp.update_confidence(
            rule_id="test_rule",
            supports_rule=False,
            strength=0.9,
            prior_confidence=0.5,
        )
        
        assert result["posterior"] < result["prior"]
        assert result["delta"] < 0
    
    @pytest.mark.asyncio
    async def test_calculate_kelly(self):
        """Kelly 배분 도구"""
        result = await pattern_truth_mcp.calculate_kelly(
            balance=1000,
            cost_per_run=10,
            success_probability=0.7,
            reward_ratio=2.0,
        )
        
        assert result["kelly_fraction"] > 0
        assert result["max_safe_investment"] > 0
        assert result["recommended_runs"] >= 1
        assert result["should_invest"] is True
    
    @pytest.mark.asyncio
    async def test_calculate_kelly_negative_edge(self):
        """Kelly 음수 에지"""
        result = await pattern_truth_mcp.calculate_kelly(
            balance=1000,
            cost_per_run=10,
            success_probability=0.2,
            reward_ratio=1.0,
        )
        
        assert result["kelly_fraction"] == 0
        assert result["should_invest"] is False


class TestPatternTruthMCPResources:
    """Pattern Truth MCP 리소스 테스트"""
    
    @pytest.mark.asyncio
    async def test_health_resource(self):
        """Health 리소스"""
        result = await pattern_truth_mcp.read_resource("pattern://health")
        
        assert result["status"] == "healthy"
        assert result["server"] == "pattern-truth"
    
    @pytest.mark.asyncio
    async def test_config_resource(self):
        """Config 리소스"""
        result = await pattern_truth_mcp.read_resource("pattern://config")
        
        assert "stpf" in result
        assert "bayesian" in result
        assert "kelly" in result


class TestMCPToolCall:
    """MCP 도구 호출 테스트"""
    
    @pytest.mark.asyncio
    async def test_call_tool_compute_stpf(self):
        """call_tool로 compute_stpf 호출"""
        result = await pattern_truth_mcp.call_tool("compute_stpf", {
            "trust": 7, "legality": 8, "hygiene": 6,
        })
        
        assert result["status"] == "OK"
    
    @pytest.mark.asyncio
    async def test_call_tool_unknown(self):
        """존재하지 않는 도구 호출"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await pattern_truth_mcp.call_tool("nonexistent_tool", {})
    
    @pytest.mark.asyncio
    async def test_read_resource_unknown(self):
        """존재하지 않는 리소스 호출"""
        with pytest.raises(ValueError, match="Unknown resource"):
            await pattern_truth_mcp.read_resource("pattern://nonexistent")
