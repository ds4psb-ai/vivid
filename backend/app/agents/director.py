"""
Director Agent - AI 총감독

사용자의 바이브 입력을 해석하고 자동으로 워크플로우를 구성합니다.
LangGraph Supervisor 패턴을 사용하여 전문 에이전트들을 오케스트레이션합니다.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("director_agent")


# =============================================================================
# Schemas
# =============================================================================

class OutputType(str, Enum):
    SHORT_DRAMA = "short_drama"
    AD = "ad"
    ANIMATION = "animation"
    MUSIC_VIDEO = "music_video"


class VibePreset(BaseModel):
    """사전 정의된 바이브 프리셋"""
    id: str
    title: str
    tone: List[str]
    visual_style: str
    emotional_arc: str
    reference_works: List[str]


class VibeInput(BaseModel):
    """사용자 바이브 입력"""
    type: str  # 'preset' | 'custom'
    preset_id: Optional[str] = None
    custom_description: Optional[str] = None
    output_type: OutputType = OutputType.SHORT_DRAMA
    target_length_sec: int = 60
    # NotebookLM 연동: 거장 스타일 capsule
    capsule_id: Optional[str] = None  # e.g. 'auteur.bong-joon-ho'


class NodeCategory(str, Enum):
    """노드 카테고리 - 역할 분류"""
    INPUT = "input"           # 사용자 입력
    GENERATE = "generate"     # AI 생성
    REFINE = "refine"         # 다듬기/수정
    VALIDATE = "validate"     # 검증
    COMPOSE = "compose"       # 합성/편집
    OUTPUT = "output"         # 최종 출력


class HandleType(str, Enum):
    """핸들 데이터 타입 - 연결 호환성 결정"""
    TEXT = "text"             # 텍스트 데이터 (대본, 대사)
    IMAGE = "image"           # 이미지 (스토리보드, 참조 이미지)
    VIDEO = "video"           # 비디오 클립
    AUDIO = "audio"           # 오디오 (음성, BGM, SFX)
    DNA = "dna"               # NarrativeDNA 객체
    METADATA = "metadata"     # 메타데이터 (캐릭터 목록, 씬 분석)
    ANY = "any"               # 모든 타입 허용


class HandlePosition(str, Enum):
    """핸들 위치"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class NodeHandle(BaseModel):
    """노드의 입출력 핸들 정의"""
    id: str                            # "in_text", "out_video"
    type: HandleType                   # 데이터 타입
    position: HandlePosition = HandlePosition.LEFT  # 핸들 위치
    label: Optional[str] = None        # UI 표시 이름
    required: bool = True              # 필수 연결 여부
    max_connections: int = -1          # -1 = 무제한


# 연결 호환성 규칙
CONNECTION_RULES: Dict[HandleType, List[HandleType]] = {
    HandleType.TEXT: [HandleType.TEXT, HandleType.ANY],
    HandleType.IMAGE: [HandleType.IMAGE, HandleType.VIDEO, HandleType.ANY],
    HandleType.VIDEO: [HandleType.VIDEO, HandleType.ANY],
    HandleType.AUDIO: [HandleType.AUDIO, HandleType.VIDEO, HandleType.ANY],
    HandleType.DNA: [HandleType.DNA, HandleType.TEXT, HandleType.ANY],
    HandleType.METADATA: [HandleType.METADATA, HandleType.TEXT, HandleType.ANY],
    HandleType.ANY: [t for t in HandleType],
}


class NodeSpec(BaseModel):
    """캔버스 노드 스펙 (확장 버전)"""
    id: str
    type: str                          # UI 노드 타입 ('input', 'capsule', 'processing' 등)
    category: NodeCategory = NodeCategory.GENERATE  # 노드 역할 카테고리
    label: str
    description: str = ""              # 노드 설명
    position: Dict[str, float]
    
    # 핸들 정의
    input_handles: List[NodeHandle] = Field(default_factory=list)
    output_handles: List[NodeHandle] = Field(default_factory=list)
    
    # 실행 설정
    ai_model: Optional[str] = None     # 사용할 AI 모델
    
    # 데이터 (하위 호환성)
    data: Dict[str, Any] = Field(default_factory=dict)


class EdgeSpec(BaseModel):
    """캔버스 엣지 스펙"""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


class NarrativeDNA(BaseModel):
    """작품의 서사 DNA - 모든 생성물이 이를 준수"""
    core_theme: str
    secondary_themes: List[str] = Field(default_factory=list)
    overall_tone: str
    allowed_tones: List[str] = Field(default_factory=list)
    forbidden_tones: List[str] = Field(default_factory=list)
    protagonist_arc: Optional[str] = None
    visual_style: str
    color_palette: List[str] = Field(default_factory=list)
    reference_works: List[str] = Field(default_factory=list)


class WorkflowPlan(BaseModel):
    """생성된 워크플로우 계획"""
    workflow_id: str
    nodes: List[NodeSpec]
    edges: List[EdgeSpec]
    narrative_dna: NarrativeDNA
    estimated_duration_sec: int
    agent_assignments: Dict[str, str] = Field(default_factory=dict)  # node_id → agent_type
    # NotebookLM 분석 결과
    logic_vector: Optional[Dict[str, Any]] = None
    persona_vector: Optional[Dict[str, Any]] = None
    capsule_id: Optional[str] = None


# =============================================================================
# Preset Registry
# =============================================================================

VIBE_PRESETS: Dict[str, VibePreset] = {
    "noir_seoul": VibePreset(
        id="noir_seoul",
        title="80년대 서울 누아르",
        tone=["어둡고", "축축한", "고독한", "속은 뜨거운"],
        visual_style="필름 누아르, 네온 조명, 빗물에 반사되는 불빛",
        emotional_arc="냉소 → 갈등 → 희망",
        reference_works=["올드보이", "아저씨", "범죄와의 전쟁"],
    ),
    "vibrant_kpop": VibePreset(
        id="vibrant_kpop",
        title="K-POP 뮤직비디오",
        tone=["역동적", "화려한", "트렌디한", "중독성 있는"],
        visual_style="네온 컬러, 빠른 컷, 댄스 브레이크, LED 무대",
        emotional_arc="임팩트 → 빌드업 → 폭발",
        reference_works=["NewJeans MV", "aespa MV", "BLACKPINK MV"],
    ),
    "emotional_drama": VibePreset(
        id="emotional_drama",
        title="감성 멜로드라마",
        tone=["서정적", "따뜻한", "쓸쓸한", "희망적"],
        visual_style="소프트 라이팅, 파스텔 톤, 긴 테이크, 클로즈업",
        emotional_arc="일상 → 상실 → 치유 → 성장",
        reference_works=["이별의 정석", "봄날", "디어 마이 프렌즈"],
    ),
    "comedy_viral": VibePreset(
        id="comedy_viral",
        title="바이럴 코미디",
        tone=["유쾌한", "위트있는", "예상치 못한", "공감가는"],
        visual_style="밝은 조명, 빠른 편집, 리액션 컷, 자막 효과",
        emotional_arc="설정 → 빌드업 → 반전 → 펀치라인",
        reference_works=["SNL 코리아", "개그콘서트", "코미디빅리그"],
    ),
    "cinematic_ad": VibePreset(
        id="cinematic_ad",
        title="시네마틱 광고",
        tone=["프리미엄", "감각적", "스토리텔링", "브랜드 메시지"],
        visual_style="와이드 앵글, 슬로모션, 색보정, 드라마틱 조명",
        emotional_arc="호기심 → 공감 → 감동 → 액션",
        reference_works=["Apple 광고", "Nike 광고", "삼성 광고"],
    ),
    "anime_style": VibePreset(
        id="anime_style",
        title="일본 애니메이션 스타일",
        tone=["드라마틱", "감성적", "액션", "판타지"],
        visual_style="셀 애니메이션, 큰 눈, 스피드 라인, 배경 아트",
        emotional_arc="평화 → 위기 → 각성 → 승리",
        reference_works=["신카이 마코토", "지브리", "귀멸의 칼날"],
    ),
}


# =============================================================================
# Director Agent
# =============================================================================

class DirectorAgent:
    """
    AI 총감독 에이전트
    
    사용자의 바이브 입력을 해석하고 적절한 워크플로우를 자동으로 구성합니다.
    """
    
    def __init__(self):
        self.presets = VIBE_PRESETS
    
    async def interpret_vibe(self, vibe_input: VibeInput) -> WorkflowPlan:
        """
        바이브 입력을 해석하여 워크플로우 계획을 생성합니다.
        """
        logger.info(
            "Interpreting vibe input",
            extra={"type": vibe_input.type, "output_type": vibe_input.output_type}
        )
        
        # 1. 바이브 해석
        if vibe_input.type == "preset" and vibe_input.preset_id:
            preset = self.presets.get(vibe_input.preset_id)
            if not preset:
                raise ValueError(f"Unknown preset: {vibe_input.preset_id}")
            narrative_dna = self._preset_to_dna(preset, vibe_input.output_type)
        else:
            # 커스텀 입력은 LLM으로 해석 (추후 구현)
            narrative_dna = await self._interpret_custom_vibe(
                vibe_input.custom_description or "",
                vibe_input.output_type
            )
        # 2. NotebookLM 분석 (capsule_id가 있는 경우)
        logic_vector = None
        persona_vector = None
        
        if vibe_input.capsule_id:
            try:
                from app.notebooklm_client import run_notebooklm_analysis
                source_pack = self._build_source_pack_from_dna(narrative_dna, vibe_input.output_type)
                analysis, _ = run_notebooklm_analysis(source_pack, vibe_input.capsule_id)
                logic_vector = analysis.get("logic_vector")
                persona_vector = analysis.get("persona_vector")
                logger.info(
                    "NotebookLM analysis completed",
                    extra={"capsule_id": vibe_input.capsule_id, "has_logic": bool(logic_vector)}
                )
            except Exception as e:
                logger.warning(f"NotebookLM analysis failed, using defaults: {e}")
        
        # 3. 워크플로우 노드 생성 (Logic Vector 기반 순서 결정)
        nodes, edges = self._generate_workflow_nodes(
            vibe_input.output_type,
            vibe_input.target_length_sec,
            narrative_dna,
            logic_vector=logic_vector,
            capsule_id=vibe_input.capsule_id,
        )
        
        # 4. Persona Vector 기반 노드 파라미터 적용
        if persona_vector:
            nodes = self._apply_persona_to_nodes(nodes, persona_vector, vibe_input.capsule_id)
        
        # 5. 에이전트 할당
        agent_assignments = self._assign_agents(nodes)
        
        workflow = WorkflowPlan(
            workflow_id=f"wf_{uuid4().hex[:8]}",
            nodes=nodes,
            edges=edges,
            narrative_dna=narrative_dna,
            estimated_duration_sec=vibe_input.target_length_sec,
            agent_assignments=agent_assignments,
            logic_vector=logic_vector,
            persona_vector=persona_vector,
            capsule_id=vibe_input.capsule_id,
        )
        
        logger.info(
            "Workflow plan generated",
            extra={
                "workflow_id": workflow.workflow_id,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "capsule_id": vibe_input.capsule_id,
            }
        )
        
        return workflow
    
    def _preset_to_dna(self, preset: VibePreset, output_type: OutputType) -> NarrativeDNA:
        """프리셋을 서사 DNA로 변환"""
        return NarrativeDNA(
            core_theme=preset.emotional_arc.split("→")[0].strip(),
            secondary_themes=[arc.strip() for arc in preset.emotional_arc.split("→")[1:]],
            overall_tone=preset.tone[0] if preset.tone else "중립",
            allowed_tones=preset.tone,
            forbidden_tones=self._get_conflicting_tones(preset.tone),
            visual_style=preset.visual_style,
            reference_works=preset.reference_works,
        )
    
    def _build_source_pack_from_dna(
        self, 
        dna: NarrativeDNA, 
        output_type: OutputType
    ) -> Dict[str, Any]:
        """NarrativeDNA로부터 NotebookLM용 source_pack 생성"""
        return {
            "pack_id": f"dna_{uuid4().hex[:8]}",
            "cluster_id": f"vibe_{dna.core_theme[:20].replace(' ', '_').lower()}",
            "temporal_phase": output_type.value,
            "source_ids": [f"dna_{output_type.value}"],
            "source_count": 1,
            "segment_refs": [
                {"segment_id": f"seg_{i}", "content": theme}
                for i, theme in enumerate([dna.core_theme] + dna.secondary_themes[:4])
            ],
            "metrics_snapshot": {
                "tone": dna.overall_tone,
                "visual_style": dna.visual_style,
                "themes": dna.secondary_themes[:3],
            },
        }
    
    def _apply_persona_to_nodes(
        self,
        nodes: List[NodeSpec],
        persona_vector: Dict[str, Any],
        capsule_id: Optional[str]
    ) -> List[NodeSpec]:
        """Persona Vector를 기반으로 노드 파라미터 조정"""
        
        # Persona 시그니처 추출
        tone = persona_vector.get("tone", ["neutral"])
        interpretation_frame = persona_vector.get("interpretation_frame", ["aesthetics"])
        sentence_rhythm = persona_vector.get("sentence_rhythm", {})
        
        # 거장별 특화 파라미터
        auteur_params = {
            "auteur.bong-joon-ho": {
                "tension_bias": 0.8,
                "class_critique": True,
                "irony_level": 0.7,
            },
            "auteur.park-chan-wook": {
                "symmetry_bias": 0.9,
                "violence_stylization": 0.8,
                "baroque_level": 0.7,
            },
            "auteur.shinkai": {
                "light_diffusion": 0.9,
                "nostalgia_level": 0.8,
                "romanticism": 0.85,
            },
        }
        
        params = auteur_params.get(capsule_id, {})
        
        for node in nodes:
            # 모든 AI 노드에 persona 파라미터 적용
            if node.ai_model:
                node.data["persona_tone"] = tone
                node.data["interpretation_frame"] = interpretation_frame
                node.data["sentence_rhythm"] = sentence_rhythm
                node.data["auteur_params"] = params
                node.data["capsule_id"] = capsule_id
        
        logger.info(f"Applied persona to {len([n for n in nodes if n.ai_model])} AI nodes")
        return nodes
    
    def _get_conflicting_tones(self, tones: List[str]) -> List[str]:
        """톤과 충돌하는 톤 목록 반환"""
        conflicts = {
            "어둡고": ["밝은", "경쾌한"],
            "따뜻한": ["차가운", "냉소적인"],
            "유쾌한": ["우울한", "어두운"],
            "프리미엄": ["저가형", "싸구려"],
        }
        result = []
        for tone in tones:
            if tone in conflicts:
                result.extend(conflicts[tone])
        return list(set(result))
    
    async def _interpret_custom_vibe(
        self, 
        description: str, 
        output_type: OutputType
    ) -> NarrativeDNA:
        """
        자연어 설명을 Gemini API로 해석하여 서사 DNA로 변환
        """
        import google.generativeai as genai
        
        if not description or len(description.strip()) < 3:
            return NarrativeDNA(
                core_theme="사용자 정의 테마",
                overall_tone="중립",
                visual_style="기본 스타일",
            )
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            output_type_kr = {
                OutputType.SHORT_DRAMA: "숏드라마",
                OutputType.AD: "광고",
                OutputType.ANIMATION: "애니메이션",
                OutputType.MUSIC_VIDEO: "뮤직비디오",
            }.get(output_type, "영상 콘텐츠")
            
            prompt = f"""당신은 영상 콘텐츠 전문 AI 감독입니다. 
사용자의 자연어 설명을 분석하여 콘텐츠의 서사 DNA를 정의해주세요.

## 사용자 입력
"{description}"

## 결과물 유형
{output_type_kr}

## 출력 형식 (JSON)
다음 형식으로 정확히 출력해주세요:
{{
    "core_theme": "핵심 테마 (한 문장)",
    "secondary_themes": ["보조 테마1", "보조 테마2"],
    "overall_tone": "전체 톤 (예: 어둡고 서정적인, 유쾌하고 활기찬)",
    "allowed_tones": ["허용 톤1", "허용 톤2", "허용 톤3"],
    "forbidden_tones": ["금지 톤1", "금지 톤2"],
    "visual_style": "비주얼 스타일 설명 (조명, 색감, 카메라워크 등)",
    "color_palette": ["주요 색상1", "주요 색상2"],
    "reference_works": ["참고 작품1", "참고 작품2"]
}}

JSON만 출력하세요. 다른 설명 없이 순수 JSON만."""

            response = await model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            
            import json
            result = json.loads(response.text)
            
            logger.info(
                "Custom vibe interpreted",
                extra={"description": description[:50], "core_theme": result.get("core_theme")}
            )
            
            return NarrativeDNA(
                core_theme=result.get("core_theme", "사용자 정의 테마"),
                secondary_themes=result.get("secondary_themes", []),
                overall_tone=result.get("overall_tone", "중립"),
                allowed_tones=result.get("allowed_tones", []),
                forbidden_tones=result.get("forbidden_tones", []),
                visual_style=result.get("visual_style", description[:100]),
                color_palette=result.get("color_palette", []),
                reference_works=result.get("reference_works", []),
            )
            
        except Exception as e:
            logger.error(f"Failed to interpret custom vibe: {e}")
            # 폴백: 기본 DNA 반환
            return NarrativeDNA(
                core_theme=description[:50] if description else "사용자 정의 테마",
                overall_tone="중립",
                visual_style=description[:100] if description else "기본 스타일",
            )
    
    def _generate_workflow_nodes(
        self,
        output_type: OutputType,
        duration_sec: int,
        dna: NarrativeDNA,
        logic_vector: Optional[Dict[str, Any]] = None,
        capsule_id: Optional[str] = None,
    ) -> tuple[List[NodeSpec], List[EdgeSpec]]:
        """출력 유형과 DNA/Logic Vector에 따른 동적 워크플로우 노드 생성
        
        Logic Vector 기반 순서 결정:
        - cut_density 높음 → 스토리보드 우선 (시각 중심 워크플로우)
        - cut_density 낮음 → 대본 우선 (서사 중심 워크플로우)
        """
        
        nodes: List[NodeSpec] = []
        edges: List[EdgeSpec] = []
        
        # 공통 시작 노드
        source_node = NodeSpec(
            id="source_1",
            type="source",
            category=NodeCategory.INPUT,  # Opal Yellow
            label="📝 스토리 입력",
            position={"x": 100, "y": 200},
            data={
                "hint": "시놉시스 또는 컨셉을 입력하세요",
                "dna_reference": dna.core_theme,
            }
        )
        nodes.append(source_node)
        
        # DNA 검증 노드 (항상 포함)
        dna_node = NodeSpec(
            id="dna_validator",
            type="processing",
            category=NodeCategory.VALIDATE,  # Opal Teal
            label="🧬 서사 DNA 검증",
            position={"x": 350, "y": 200},
            data={
                "narrative_dna": dna.model_dump(),
                "auto_validate": True,
            }
        )
        nodes.append(dna_node)
        edges.append(EdgeSpec(id="e_s1_dna", source="source_1", target="dna_validator"))
        
        # ========== 장르 감지 및 특화 노드 추가 ==========
        genre_nodes, genre_edges = self._detect_and_create_genre_nodes(dna, output_type)
        nodes.extend(genre_nodes)
        edges.extend(genre_edges)

        # ========== 거장 스타일 특화 노드 추가 ==========
        if capsule_id:
            auteur_nodes, auteur_edges = self._create_auteur_nodes(capsule_id, dna)
            nodes.extend(auteur_nodes)
            edges.extend(auteur_edges)
        
        # 출력 유형별 기본 노드
        if output_type == OutputType.SHORT_DRAMA:
            nodes.extend(self._create_drama_nodes(dna))
            edges.extend(self._create_drama_edges())
        elif output_type == OutputType.AD:
            nodes.extend(self._create_ad_nodes(dna))
            edges.extend(self._create_ad_edges())
        elif output_type == OutputType.MUSIC_VIDEO:
            nodes.extend(self._create_mv_nodes(dna))
            edges.extend(self._create_mv_edges())
        else:  # ANIMATION
            nodes.extend(self._create_animation_nodes(dna))
            edges.extend(self._create_animation_edges())
        
        # 최종 출력 노드
        output_node = NodeSpec(
            id="output_1",
            type="output",
            category=NodeCategory.OUTPUT,  # Opal Green
            label="🎬 최종 결과물",
            position={"x": 1100, "y": 200},
            data={
                "target_duration": duration_sec,
                "dna_compliance_required": True,
            }
        )
        nodes.append(output_node)
        
        return nodes, edges
    
    def _detect_and_create_genre_nodes(
        self, 
        dna: NarrativeDNA, 
        output_type: OutputType
    ) -> tuple[List[NodeSpec], List[EdgeSpec]]:
        """장르별 특화 노드 생성 - Dual Capsule System으로 대체 예정
        
        현재: 빈 리스트 반환 (Mock 노드 제거됨)
        향후: Teaching Capsule + NotebookLM RAG 노드로 대체
        """
        # DNA에서 장르 감지 (로깅용)
        all_text = f"{dna.core_theme} {' '.join(dna.secondary_themes)} {dna.overall_tone}".lower()
        genre_keywords = {
            "horror": ["공포", "스릴러", "호러"],
            "romance": ["로맨스", "멜로", "사랑"],
            "action": ["액션", "추격", "전투"],
            "comedy": ["코미디", "유쾌", "반전"],
        }
        detected = [g for g, kws in genre_keywords.items() if any(k in all_text for k in kws)]
        
        if detected:
            logger.info(f"Detected genres: {detected} - awaiting Dual Capsule integration")
        
        # Mock 노드 대신 빈 리스트 반환
        return [], []
    
    def _create_drama_nodes(self, dna: NarrativeDNA) -> List[NodeSpec]:
        """숏드라마용 노드 생성 (핸들 시스템 적용)"""
        return [
            # Layer 1: 콘텐츠 기획
            NodeSpec(
                id="concept_input",
                type="input",
                category=NodeCategory.INPUT,
                label="💡 컨셉 입력",
                description="드라마의 핵심 컨셉과 로그라인을 입력",
                position={"x": 550, "y": 50},
                input_handles=[],  # 입력 노드는 입력 핸들 없음
                output_handles=[
                    NodeHandle(id="out_text", type=HandleType.TEXT, position=HandlePosition.RIGHT, label="텍스트"),
                ],
                data={"placeholder": "예: 평범한 직장인이 어느 날 우연히...", "max_length": 500},
            ),
            NodeSpec(
                id="reference_upload",
                type="input",
                category=NodeCategory.INPUT,
                label="📂 레퍼런스 업로드",
                description="참고 이미지나 영상 업로드",
                position={"x": 250, "y": 50},
                input_handles=[],
                output_handles=[
                    NodeHandle(id="out_image", type=HandleType.IMAGE, position=HandlePosition.RIGHT, label="이미지"),
                    NodeHandle(id="out_video", type=HandleType.VIDEO, position=HandlePosition.RIGHT, label="영상", required=False),
                ],
                data={"accept": ["image/*", "video/*"]},
            ),
            # Layer 2: AI 생성
            NodeSpec(
                id="script_gen",
                type="capsule",
                category=NodeCategory.GENERATE,
                label="📖 대본 생성",
                description="AI가 시놉시스를 기반으로 대본 생성",
                position={"x": 550, "y": 200},
                ai_model="gemini-3-flash-preview",
                input_handles=[
                    NodeHandle(id="in_text", type=HandleType.TEXT, position=HandlePosition.LEFT, label="컨셉"),
                    NodeHandle(id="in_dna", type=HandleType.DNA, position=HandlePosition.TOP, label="DNA", required=False),
                ],
                output_handles=[
                    NodeHandle(id="out_script", type=HandleType.TEXT, position=HandlePosition.RIGHT, label="대본"),
                    NodeHandle(id="out_meta", type=HandleType.METADATA, position=HandlePosition.BOTTOM, label="캐릭터"),
                ],
                data={"tone": dna.overall_tone, "parameters": {"temperature": 0.8, "max_tokens": 4000}},
            ),
            NodeSpec(
                id="storyboard",
                type="capsule",
                category=NodeCategory.GENERATE,
                label="🎨 스토리보드",
                description="씬별 비주얼 스토리보드 생성",
                position={"x": 250, "y": 350},
                ai_model="imagen-3",
                input_handles=[
                    NodeHandle(id="in_script", type=HandleType.TEXT, position=HandlePosition.LEFT, label="대본"),
                    NodeHandle(id="in_ref", type=HandleType.IMAGE, position=HandlePosition.TOP, label="레퍼런스", required=False),
                ],
                output_handles=[
                    NodeHandle(id="out_images", type=HandleType.IMAGE, position=HandlePosition.RIGHT, label="스토리보드"),
                ],
                data={"visual_style": dna.visual_style, "aspect_ratio": "16:9"},
            ),
            NodeSpec(
                id="dialogue_gen",
                type="capsule",
                category=NodeCategory.REFINE,
                label="💬 대사 다듬기",
                description="대사를 자연스럽게 다듬기",
                position={"x": 850, "y": 200},
                ai_model="gemini-pro",
                input_handles=[
                    NodeHandle(id="in_script", type=HandleType.TEXT, position=HandlePosition.LEFT, label="대본"),
                ],
                output_handles=[
                    NodeHandle(id="out_dialogue", type=HandleType.TEXT, position=HandlePosition.RIGHT, label="대사"),
                ],
                data={"tone_adherence": dna.overall_tone},
            ),
            # Layer 3: 검증
            NodeSpec(
                id="dna_check",
                type="processing",
                category=NodeCategory.VALIDATE,
                label="🧬 DNA 컴플라이언스",
                description="서사 DNA 준수 여부 검증",
                position={"x": 550, "y": 480},
                input_handles=[
                    NodeHandle(id="in_text", type=HandleType.TEXT, position=HandlePosition.LEFT, label="대본/대사"),
                    NodeHandle(id="in_images", type=HandleType.IMAGE, position=HandlePosition.TOP, label="스토리보드"),
                    NodeHandle(id="in_dna", type=HandleType.DNA, position=HandlePosition.LEFT, label="DNA"),
                ],
                output_handles=[
                    NodeHandle(id="out_validated", type=HandleType.DNA, position=HandlePosition.RIGHT, label="검증된 DNA"),
                    NodeHandle(id="out_issues", type=HandleType.METADATA, position=HandlePosition.BOTTOM, label="이슈"),
                ],
                data={"narrative_dna": dna.model_dump(), "auto_validate": True},
            ),
            # Layer 4: 영상 생성
            NodeSpec(
                id="video_gen",
                type="capsule",
                category=NodeCategory.GENERATE,
                label="🎬 영상 생성",
                description="스토리보드 기반 비디오 클립 생성",
                position={"x": 550, "y": 630},
                ai_model="veo-2",
                input_handles=[
                    NodeHandle(id="in_storyboard", type=HandleType.IMAGE, position=HandlePosition.LEFT, label="스토리보드"),
                    NodeHandle(id="in_dna", type=HandleType.DNA, position=HandlePosition.TOP, label="DNA"),
                ],
                output_handles=[
                    NodeHandle(id="out_video", type=HandleType.VIDEO, position=HandlePosition.RIGHT, label="영상"),
                ],
                data={"fps": 24, "resolution": "1080p", "motion_strength": 0.6},
            ),
            NodeSpec(
                id="audio_mix",
                type="capsule",
                category=NodeCategory.GENERATE,
                label="🔊 오디오 믹싱",
                description="음향 효과와 배경음악 생성",
                position={"x": 250, "y": 730},
                ai_model="audiocraft",
                input_handles=[
                    NodeHandle(id="in_video", type=HandleType.VIDEO, position=HandlePosition.LEFT, label="영상"),
                    NodeHandle(id="in_dialogue", type=HandleType.TEXT, position=HandlePosition.TOP, label="대사"),
                ],
                output_handles=[
                    NodeHandle(id="out_audio", type=HandleType.AUDIO, position=HandlePosition.RIGHT, label="오디오"),
                ],
                data={"bgm_style": dna.overall_tone, "voice_synthesis": True},
            ),
            # Layer 5: 편집
            NodeSpec(
                id="edit_compose",
                type="processing",
                category=NodeCategory.COMPOSE,
                label="✂️ 편집/합성",
                description="영상, 오디오, 자막 최종 편집",
                position={"x": 550, "y": 830},
                input_handles=[
                    NodeHandle(id="in_video", type=HandleType.VIDEO, position=HandlePosition.LEFT, label="영상"),
                    NodeHandle(id="in_audio", type=HandleType.AUDIO, position=HandlePosition.LEFT, label="오디오"),
                ],
                output_handles=[
                    NodeHandle(id="out_final", type=HandleType.VIDEO, position=HandlePosition.RIGHT, label="최종 영상"),
                ],
                data={"auto_cut": True, "transition_style": "smooth", "subtitle_enabled": True},
            ),
        ]
    
    def _create_drama_edges(self) -> List[EdgeSpec]:
        return [
            # Input to Generation
            EdgeSpec(id="e_concept_script", source="concept_input", target="script_gen"),
            EdgeSpec(id="e_ref_storyboard", source="reference_upload", target="storyboard"),
            # DNA validation input
            EdgeSpec(id="e_dna_src", source="dna_validator", target="concept_input"),
            # Generation flow
            EdgeSpec(id="e_script_sb", source="script_gen", target="storyboard"),
            EdgeSpec(id="e_script_dialogue", source="script_gen", target="dialogue_gen"),
            # To DNA check
            EdgeSpec(id="e_sb_dna", source="storyboard", target="dna_check"),
            EdgeSpec(id="e_dialogue_dna", source="dialogue_gen", target="dna_check"),
            # To video generation
            EdgeSpec(id="e_dna_video", source="dna_check", target="video_gen"),
            EdgeSpec(id="e_video_audio", source="video_gen", target="audio_mix"),
            # Final composition
            EdgeSpec(id="e_video_edit", source="video_gen", target="edit_compose"),
            EdgeSpec(id="e_audio_edit", source="audio_mix", target="edit_compose"),
            # Output
            EdgeSpec(id="e_edit_out", source="edit_compose", target="output_1"),
        ]
    
    def _create_ad_nodes(self, dna: NarrativeDNA) -> List[NodeSpec]:
        """광고용 노드 생성"""
        return [
            NodeSpec(
                id="hook_gen",
                type="capsule",
                label="🎯 훅 생성",
                position={"x": 600, "y": 100},
                data={"capsule_type": "hook_generator"}
            ),
            NodeSpec(
                id="visual_gen",
                type="capsule",
                label="🖼️ 비주얼 생성",
                position={"x": 600, "y": 300},
                data={"style": dna.visual_style}
            ),
            NodeSpec(
                id="cta_gen",
                type="processing",
                label="📢 CTA 최적화",
                position={"x": 850, "y": 200},
                data={}
            ),
        ]
    
    def _create_ad_edges(self) -> List[EdgeSpec]:
        return [
            EdgeSpec(id="e_dna_hook", source="dna_validator", target="hook_gen"),
            EdgeSpec(id="e_dna_visual", source="dna_validator", target="visual_gen"),
            EdgeSpec(id="e_hook_cta", source="hook_gen", target="cta_gen"),
            EdgeSpec(id="e_visual_cta", source="visual_gen", target="cta_gen"),
            EdgeSpec(id="e_cta_out", source="cta_gen", target="output_1"),
        ]
    
    def _create_mv_nodes(self, dna: NarrativeDNA) -> List[NodeSpec]:
        """뮤직비디오용 노드 생성"""
        return [
            NodeSpec(
                id="beat_sync",
                type="processing",
                label="🎵 비트 싱크",
                position={"x": 600, "y": 100},
                data={}
            ),
            NodeSpec(
                id="choreo_gen",
                type="capsule",
                label="💃 안무 생성",
                position={"x": 600, "y": 300},
                data={}
            ),
            NodeSpec(
                id="visual_effects",
                type="capsule",
                label="✨ 비주얼 이펙트",
                position={"x": 850, "y": 200},
                data={"style": dna.visual_style}
            ),
        ]
    
    def _create_mv_edges(self) -> List[EdgeSpec]:
        return [
            EdgeSpec(id="e_dna_beat", source="dna_validator", target="beat_sync"),
            EdgeSpec(id="e_dna_choreo", source="dna_validator", target="choreo_gen"),
            EdgeSpec(id="e_beat_vfx", source="beat_sync", target="visual_effects"),
            EdgeSpec(id="e_choreo_vfx", source="choreo_gen", target="visual_effects"),
            EdgeSpec(id="e_vfx_out", source="visual_effects", target="output_1"),
        ]
    
    def _create_animation_nodes(self, dna: NarrativeDNA) -> List[NodeSpec]:
        """애니메이션용 노드 생성"""
        return [
            NodeSpec(
                id="keyframe_gen",
                type="capsule",
                label="🖼️ 키프레임 생성",
                position={"x": 600, "y": 100},
                data={"style": dna.visual_style}
            ),
            NodeSpec(
                id="motion_gen",
                type="capsule",
                label="🎬 모션 생성",
                position={"x": 600, "y": 300},
                data={}
            ),
            NodeSpec(
                id="composit",
                type="processing",
                label="🎨 합성",
                position={"x": 850, "y": 200},
                data={}
            ),
        ]
    
    def _create_animation_edges(self) -> List[EdgeSpec]:
        return [
            EdgeSpec(id="e_dna_kf", source="dna_validator", target="keyframe_gen"),
            EdgeSpec(id="e_dna_motion", source="dna_validator", target="motion_gen"),
            EdgeSpec(id="e_kf_comp", source="keyframe_gen", target="composit"),
            EdgeSpec(id="e_motion_comp", source="motion_gen", target="composit"),
            EdgeSpec(id="e_comp_out", source="composit", target="output_1"),
        ]
    
    def _assign_agents(self, nodes: List[NodeSpec]) -> Dict[str, str]:
        """노드에 전문 에이전트 할당"""
        agent_map = {
            "source": "user_input",
            "script_gen": "script_agent",
            "storyboard": "visual_agent",
            "character_design": "visual_agent",
            "hook_gen": "script_agent",
            "visual_gen": "visual_agent",
            "cta_gen": "script_agent",
            "beat_sync": "audio_agent",
            "choreo_gen": "visual_agent",
            "visual_effects": "visual_agent",
            "keyframe_gen": "visual_agent",
            "motion_gen": "visual_agent",
            "composit": "visual_agent",
            "dna_validator": "director_agent",
            "output": "director_agent",
        }
        
        assignments = {}
        for node in nodes:
            agent = agent_map.get(node.id) or agent_map.get(node.type, "director_agent")
            assignments[node.id] = agent
            
        return assignments

    def _create_auteur_nodes(self, capsule_id: str, dna: NarrativeDNA) -> tuple[List[NodeSpec], List[EdgeSpec]]:
        """거장(Auteur)별 시그니처 노드 생성 - Dual Capsule System으로 대체 예정
        
        현재: 빈 리스트 반환 (Mock 노드 제거됨)
        향후: Teaching Capsule + NotebookLM RAG 노드로 대체
        """
        if capsule_id:
            logger.info(f"Auteur style requested: {capsule_id} - awaiting Dual Capsule integration")
        
        # Mock 노드 대신 빈 리스트 반환
        return [], []


# Singleton instance
director_agent = DirectorAgent()
