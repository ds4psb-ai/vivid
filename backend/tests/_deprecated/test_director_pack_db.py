"""
Unit Tests for DirectorPack DB Service

Coverage Target: 80%+
"""
import pytest
from app.services.director_pack_db_service import (
    DirectorPackDBService,
    director_pack_db_service,
)
from app.models_director_pack import (
    DirectorPackDB,
    DNAInvariantConfidence,
    DirectorPackUsageLog,
)


class TestDirectorPackDBModels:
    """DB 모델 테스트"""
    
    def test_director_pack_db_model(self):
        """DirectorPackDB 모델"""
        pack = DirectorPackDB(
            pack_id="test_pack",
            pattern_id="test.pattern",
            version="1.0.0",
        )
        assert pack.pack_id == "test_pack"
        assert pack.pattern_id == "test.pattern"
    
    def test_dna_invariant_confidence_model(self):
        """DNAInvariantConfidence 모델"""
        conf = DNAInvariantConfidence(
            pack_id="test_pack",
            rule_id="rule_001",
            confidence=0.8,
            evidence_count=5,
        )
        assert conf.confidence == 0.8
        assert conf.evidence_count == 5
    
    def test_usage_log_model(self):
        """DirectorPackUsageLog 모델"""
        log = DirectorPackUsageLog(
            pack_id="test_pack",
            user_id="user_123",
            outcome="success",
            score=85.0,
        )
        assert log.outcome == "success"
        assert log.score == 85.0


class TestDirectorPackDBService:
    """DirectorPack DB 서비스 테스트"""
    
    @pytest.fixture
    def service(self):
        return DirectorPackDBService()
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert director_pack_db_service is not None
        assert isinstance(director_pack_db_service, DirectorPackDBService)


class TestDirectorPackIntegration:
    """통합 테스트"""
    
    def test_service_methods_exist(self):
        """서비스 메서드 존재 확인"""
        service = DirectorPackDBService()
        
        assert hasattr(service, 'save_pack')
        assert hasattr(service, 'load_pack')
        assert hasattr(service, 'list_packs')
        assert hasattr(service, 'update_invariant_confidence')
        assert hasattr(service, 'get_invariant_confidences')
        assert hasattr(service, 'log_usage')
        assert hasattr(service, 'get_pack_stats')
