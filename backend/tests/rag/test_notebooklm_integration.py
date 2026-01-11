"""NotebookLM Integration Tests.

P4 Commit 4: Tests for NotebookLM service, registry, and health endpoint.

NOTE: These tests require the full backend environment with qdrant_client.
      Run from project root with full dependencies installed.

Run with:
    cd backend && pytest tests/rag/test_notebooklm_integration.py -v
"""
import pytest

# Skip all tests if rag modules can't be imported (missing dependencies)
try:
    from app.rag.tier0_notebooklm import (
        NOTEBOOK_REGISTRY,
        get_notebooklm_health,
        get_notebooklm_service,
        reset_notebooklm_service,
        query_auteur_dna,
        query_dimension_guide,
    )
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define placeholders so the file parses
    NOTEBOOK_REGISTRY = {}
    get_notebooklm_health = None
    get_notebooklm_service = None
    reset_notebooklm_service = None
    query_auteur_dna = None
    query_dimension_guide = None


pytestmark = pytest.mark.skipif(
    not RAG_AVAILABLE,
    reason=f"RAG modules not available: {IMPORT_ERROR if not RAG_AVAILABLE else ''}"
)


class TestNotebookRegistry:
    """Tests for NOTEBOOK_REGISTRY structure and content."""
    
    def test_registry_has_minimum_real_notebooks(self):
        """At least 5 notebooks should have real IDs (not SIMULATION)."""
        real_notebooks = [
            key for key, info in NOTEBOOK_REGISTRY.items()
            if info.get("notebook_id") not in ("SIMULATION", "PENDING")
            and not info.get("notebook_id", "").startswith("notebooklm://")
        ]
        
        assert len(real_notebooks) >= 5, f"Expected ≥5 real notebooks, got {len(real_notebooks)}: {real_notebooks}"
    
    def test_registry_entries_have_required_fields(self):
        """All registry entries must have required fields."""
        required_fields = ["notebook_id", "display_name", "dimension", "category"]
        
        for key, info in NOTEBOOK_REGISTRY.items():
            for field in required_fields:
                assert field in info, f"Registry entry '{key}' missing required field: {field}"
    
    def test_registry_categories_are_valid(self):
        """All categories should be one of: auteur, meta, dimension."""
        valid_categories = {"auteur", "meta", "dimension"}
        
        for key, info in NOTEBOOK_REGISTRY.items():
            category = info.get("category")
            assert category in valid_categories, f"Invalid category '{category}' for entry '{key}'"
    
    def test_auteur_notebooks_have_description(self):
        """Auteur notebooks should have descriptions."""
        for key, info in NOTEBOOK_REGISTRY.items():
            if info.get("category") == "auteur":
                assert info.get("description"), f"Auteur entry '{key}' missing description"


class TestNotebookLMHealth:
    """Tests for get_notebooklm_health() function."""
    
    def test_health_returns_expected_structure(self):
        """Health response should have required top-level keys."""
        health = get_notebooklm_health()
        
        assert "status" in health
        assert "circuit_breaker" in health
        assert "registry" in health
        assert "clients" in health
        assert "cache" in health
    
    def test_health_circuit_breaker_fields(self):
        """Circuit breaker section should have state info."""
        health = get_notebooklm_health()
        cb = health["circuit_breaker"]
        
        assert "state" in cb
        assert cb["state"] in ("closed", "open", "half_open", "degraded")
        assert "failure_count" in cb
        assert "threshold" in cb
    
    def test_health_registry_counts(self):
        """Registry section should have accurate counts."""
        health = get_notebooklm_health()
        reg = health["registry"]
        
        assert reg["total"] == len(NOTEBOOK_REGISTRY)
        assert reg["real"] + reg["simulation"] <= reg["total"]
        assert isinstance(reg["real_notebooks"], list)
        assert isinstance(reg["simulation_notebooks"], list)
    
    def test_health_clients_availability(self):
        """Clients section should report availability."""
        health = get_notebooklm_health()
        clients = health["clients"]
        
        assert "playwright_available" in clients
        assert "mcp_available" in clients
        assert isinstance(clients["playwright_available"], bool)
        assert isinstance(clients["mcp_available"], bool)


class TestNotebookLMService:
    """Tests for NotebookLMService class."""
    
    def test_service_singleton(self):
        """get_notebooklm_service should return singleton."""
        reset_notebooklm_service()
        
        service1 = get_notebooklm_service()
        service2 = get_notebooklm_service()
        
        assert service1 is service2
        
        reset_notebooklm_service()
    
    def test_resolve_notebook_id_with_valid_key(self):
        """_resolve_notebook_id should return real ID for valid key."""
        service = get_notebooklm_service()
        
        # Pick a real notebook from registry
        real_key = None
        real_id = None
        for key, info in NOTEBOOK_REGISTRY.items():
            if info.get("notebook_id") not in ("SIMULATION", "PENDING"):
                real_key = key
                real_id = info["notebook_id"]
                break
        
        if real_key:
            resolved = service._resolve_notebook_id(real_key)
            assert resolved == real_id
    
    def test_resolve_notebook_id_passthrough(self):
        """_resolve_notebook_id should passthrough unknown keys."""
        service = get_notebooklm_service()
        
        unknown_key = "some-random-uuid-12345"
        resolved = service._resolve_notebook_id(unknown_key)
        
        assert resolved == unknown_key
    
    def test_get_cache_stats(self):
        """get_cache_stats should return size and ttl."""
        service = get_notebooklm_service()
        stats = service.get_cache_stats()
        
        assert "size" in stats
        assert "ttl_seconds" in stats
        assert isinstance(stats["size"], int)
        assert stats["size"] >= 0


class TestSimulationFallback:
    """Tests for SIMULATION mode notebooks."""
    
    @pytest.mark.asyncio
    async def test_simulation_notebook_returns_result(self):
        """SIMULATION notebooks should return valid mock response."""
        # Find a SIMULATION notebook
        sim_key = None
        for key, info in NOTEBOOK_REGISTRY.items():
            if info.get("notebook_id") == "SIMULATION":
                sim_key = key
                break
        
        if not sim_key:
            pytest.skip("No SIMULATION notebooks in registry")
        
        service = get_notebooklm_service()
        result = await service.query_notebook(sim_key, "test query")
        
        # Should return simulation result with reasonable defaults
        assert result.answer or result.confidence == 0.0
        assert hasattr(result, "grounded")
        assert hasattr(result, "sources")


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    @pytest.mark.asyncio
    async def test_query_auteur_dna_unknown_auteur(self):
        """query_auteur_dna should handle unknown auteur gracefully."""
        result = await query_auteur_dna("nonexistent", "test query")
        
        assert "Unknown auteur" in result.answer
        assert result.confidence == 0.0
        assert result.grounded is False
    
    @pytest.mark.asyncio
    async def test_query_dimension_guide_unknown_dimension(self):
        """query_dimension_guide should handle unknown dimension gracefully."""
        result = await query_dimension_guide("9D", "test query")
        
        assert "Unknown dimension" in result.answer
        assert result.confidence == 0.0
        assert result.grounded is False
