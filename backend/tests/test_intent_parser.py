"""
Unit Tests for Intent Parser

Coverage Target: 80%+
"""
import pytest
from app.services.intent_parser import IntentParser, intent_parser
from app.schemas.intent_schemas import (
    NodeEditIntent, IntentType, PropertyChange, PropertyCategory,
    IntentParseRequest, IntentParseResult, IntentMapping,
)


class TestIntentSchemas:
    """Intent 스키마 테스트"""
    
    def test_node_edit_intent_creation(self):
        """NodeEditIntent 생성"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="밝게 해줘",
            simple_changes={"lighting": 8},
        )
        
        assert intent.intent_type == IntentType.MODIFY
        assert intent.simple_changes["lighting"] == 8
        assert intent.intent_id is not None
    
    def test_property_change(self):
        """PropertyChange 생성"""
        change = PropertyChange(
            property_name="mood",
            category=PropertyCategory.MOOD,
            new_value="dramatic",
            confidence=0.9,
        )
        
        assert change.property_name == "mood"
        assert change.new_value == "dramatic"
    
    def test_intent_to_simple_dict(self):
        """to_simple_dict 변환"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"a": 1},
            property_changes=[
                PropertyChange(
                    property_name="b",
                    category=PropertyCategory.LIGHTING,
                    new_value=2,
                )
            ],
        )
        
        result = intent.to_simple_dict()
        assert result["a"] == 1
        assert result["b"] == 2


class TestIntentParser:
    """Intent Parser 테스트"""
    
    @pytest.fixture
    def parser(self):
        return IntentParser()
    
    # 기본 파싱 테스트
    def test_parse_dramatic(self, parser):
        """극적으로 파싱"""
        request = IntentParseRequest(
            user_input="이 장면 좀 더 극적으로 해줘",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert "mood" in result.intent.simple_changes
        assert result.intent.simple_changes["mood"] == "dramatic"
    
    def test_parse_bright(self, parser):
        """밝게 파싱"""
        request = IntentParseRequest(
            user_input="밝게 해줘",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert result.intent.simple_changes.get("lighting") == 8
    
    def test_parse_zoom_in(self, parser):
        """줌인 파싱"""
        request = IntentParseRequest(
            user_input="카메라 줌인 해줘",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert result.intent.simple_changes.get("camera_motion") == "zoom_in"
    
    def test_parse_warm_color(self, parser):
        """따뜻하게 파싱"""
        request = IntentParseRequest(
            user_input="색감을 따뜻하게",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert result.intent.simple_changes.get("color_temp") == "warm"
    
    def test_parse_slow(self, parser):
        """천천히 파싱"""
        request = IntentParseRequest(
            user_input="천천히 움직여",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert result.intent.simple_changes.get("speed") == 0.7
    
    # STPF 평가 테스트
    def test_parse_with_stpf(self, parser):
        """STPF 평가 포함 파싱"""
        request = IntentParseRequest(
            user_input="밝게 해줘",
            include_stpf_eval=True,
        )
        result = parser.parse(request)
        
        assert result.success is True
        assert result.stpf_score is not None
        assert result.stpf_score > 0
        assert result.stpf_grade is not None
    
    def test_parse_with_kelly(self, parser):
        """Kelly 권장 포함"""
        request = IntentParseRequest(
            user_input="극적으로 해줘",
            include_stpf_eval=True,
        )
        result = parser.parse(request)
        
        assert result.kelly_recommendation is not None
    
    # 복잡한 의도 테스트
    def test_detect_complex_intent(self, parser):
        """복잡한 의도 감지"""
        is_complex, desc = parser._detect_complex_intent("전체 스토리보드를 바꿔줘")
        assert is_complex is True
    
    def test_simple_intent_not_complex(self, parser):
        """단순 의도는 복잡하지 않음"""
        is_complex, _ = parser._detect_complex_intent("밝게 해줘")
        assert is_complex is False
    
    # 의도 유형 테스트
    def test_intent_type_delete(self, parser):
        """삭제 의도"""
        intent_type = parser._determine_intent_type("이 장면 삭제해줘", [])
        assert intent_type == IntentType.DELETE
    
    def test_intent_type_connect(self, parser):
        """연결 의도"""
        intent_type = parser._determine_intent_type("두 장면 연결해줘", [])
        assert intent_type == IntentType.CONNECT
    
    def test_intent_type_create(self, parser):
        """생성 의도"""
        intent_type = parser._determine_intent_type("새로운 장면 추가해줘", [])
        assert intent_type == IntentType.CREATE
    
    # 에러 케이스
    def test_parse_unknown_intent(self, parser):
        """알 수 없는 의도"""
        request = IntentParseRequest(
            user_input="zzzxxx",
            include_stpf_eval=False,
        )
        result = parser.parse(request)
        
        assert result.success is False
        assert result.error is not None
    
    # 유틸리티 테스트
    def test_quick_parse(self, parser):
        """빠른 파싱"""
        changes = parser.quick_parse("극적으로 밝게")
        
        assert "mood" in changes or "lighting" in changes
    
    def test_get_available_mappings(self, parser):
        """매핑 목록 조회"""
        mappings = parser.get_available_mappings()
        
        assert len(mappings) > 0
        assert "keywords" in mappings[0]


class TestIntentIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert intent_parser is not None
        assert isinstance(intent_parser, IntentParser)
    
    def test_full_parse_cycle(self):
        """전체 파싱 사이클"""
        request = IntentParseRequest(
            user_input="이 장면을 더 극적이고 밝게 해줘",
            node_id="node_123",
            include_stpf_eval=True,
        )
        
        result = intent_parser.parse(request)
        
        # 성공 확인
        assert result.success is True
        
        # 의도 확인
        assert result.intent is not None
        assert result.intent.target_node_id == "node_123"
        
        # 변경 확인
        changes = result.intent.to_simple_dict()
        assert len(changes) >= 1
        
        # STPF 확인
        assert result.stpf_score is not None
        assert result.stpf_grade is not None  # Grade exists


class TestIntentParserHardening:
    """Intent Parser 하드닝 테스트"""
    
    @pytest.fixture
    def parser(self):
        from app.services.intent_parser import IntentParser
        return IntentParser()
    
    # 입력 검증 테스트
    def test_empty_input_validation_error(self, parser):
        """빈 입력 - Pydantic에서 검증"""
        import pytest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            IntentParseRequest(user_input="", include_stpf_eval=False)
    
    def test_short_input(self, parser):
        """너무 짧은 입력"""
        request = IntentParseRequest(user_input="ab", include_stpf_eval=False)
        result = parser.parse(request)
        # 짧아도 파싱 시도
        assert result is not None
    
    def test_long_input_validation_error(self, parser):
        """긴 입력 - Pydantic에서 검증"""
        import pytest
        from pydantic import ValidationError
        
        long_input = "밝게 " * 500  # 2500자 초과
        with pytest.raises(ValidationError):
            IntentParseRequest(user_input=long_input, include_stpf_eval=False)
    
    def test_max_length_input(self, parser):
        """최대 길이 입력"""
        max_input = "밝게 " * 200  # 약 600자
        request = IntentParseRequest(user_input=max_input[:1000], include_stpf_eval=False)
        result = parser.parse(request)
        assert result.success is True
    
    # 통계 테스트
    def test_parser_stats(self, parser):
        """파서 통계"""
        # 몇 번 파싱
        parser.parse(IntentParseRequest(user_input="밝게", include_stpf_eval=False))
        parser.parse(IntentParseRequest(user_input="어둡게", include_stpf_eval=False))
        
        stats = parser.get_stats()
        assert stats["total_parses"] >= 2
        assert stats["mapping_count"] > 0
    
    # 의도 유형 테스트
    def test_intent_type_with_variations(self, parser):
        """다양한 키워드 변형"""
        # 삭제 변형
        assert parser._determine_intent_type("지워주세요", []) == IntentType.DELETE
        
        # 연결 변형
        assert parser._determine_intent_type("붙여주세요", []) == IntentType.CONNECT
        
        # 생성 변형
        assert parser._determine_intent_type("생성해줘", []) == IntentType.CREATE
        
        # 취소 변형
        assert parser._determine_intent_type("원래대로 해줘", []) == IntentType.UNDO
    
    # 중복 키워드 테스트
    def test_duplicate_keywords_handled(self, parser):
        """중복 키워드 처리"""
        request = IntentParseRequest(
            user_input="밝게 밝게 밝게",  # 같은 키워드 반복
            include_stpf_eval=False
        )
        result = parser.parse(request)
        assert result.success is True
        # 중복이 아닌 하나만 적용
    
    # STPF 리스크 조정 테스트
    def test_delete_intent_higher_risk(self, parser):
        """삭제 의도는 높은 리스크"""
        # DELETE는 risk_modifier = 3
        request = IntentParseRequest(
            user_input="밝게 하고 삭제해줘",
            include_stpf_eval=True
        )
        result = parser.parse(request)
        assert result.success is True
        # 삭제 의도
        assert result.intent.intent_type == IntentType.DELETE
    
    # 매핑 추가 테스트
    def test_add_custom_mapping(self, parser):
        """커스텀 매핑 추가"""
        from app.schemas.intent_schemas import IntentMapping, PropertyCategory
        
        custom = IntentMapping(
            keywords=["커스텀테스트"],
            property_changes={"custom": "value"},
            category=PropertyCategory.TECHNICAL,
        )
        
        parser.add_mapping(custom)
        
        request = IntentParseRequest(
            user_input="커스텀테스트 해줘",
            include_stpf_eval=False
        )
        result = parser.parse(request)
        assert result.success is True
        assert result.intent.simple_changes.get("custom") == "value"

