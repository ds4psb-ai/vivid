"""
Workflow Templates and Planner for Agent-driven Tool Chain Recommendation

This module defines workflow templates and provides logic for:
1. Analyzing user intent
2. Recommending tool chains (열차 워크플로우)
3. Generating connected node specifications
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class WorkflowTemplate(BaseModel):
    """사전 정의된 워크플로우 템플릿"""
    id: str
    name: str
    name_ko: str
    description: str
    description_ko: str
    tools: List[str]  # 순서대로 실행할 도구들
    connections: List[Dict[str, str]]  # 도구 간 데이터 연결
    keywords: List[str]  # 의도 매칭용 키워드
    estimated_credits: int  # 예상 크레딧 소모


# =============================================================================
# WORKFLOW TEMPLATES (열차 워크플로우)
# =============================================================================

WORKFLOW_TEMPLATES: Dict[str, WorkflowTemplate] = {
    "content_creation": WorkflowTemplate(
        id="content_creation",
        name="Content Creation Pipeline",
        name_ko="콘텐츠 제작 파이프라인",
        description="Create video/image content from scratch with prompt, storyboard, and visuals",
        description_ko="프롬프트 생성 → 스토리보드 → 이미지까지 전체 콘텐츠 제작",
        tools=["prompt_generator", "storyboard", "image_tool"],
        connections=[
            {"from": "prompt_generator.prompt", "to": "storyboard.script"},
            {"from": "storyboard.scenes[0].description", "to": "image_tool.description"},
        ],
        keywords=[
            "콘텐츠", "영상", "비디오", "만들기", "제작", "브이로그", "vlog",
            "유튜브", "숏폼", "릴스", "틱톡", "광고", "홍보",
        ],
        estimated_credits=30,
    ),
    
    "reference_to_creation": WorkflowTemplate(
        id="reference_to_creation",
        name="Reference Analysis to Creation",
        name_ko="레퍼런스 분석 → 창작",
        description="Analyze reference video then create similar content",
        description_ko="기존 영상을 분석하고 유사한 스타일로 새 콘텐츠 제작",
        tools=["reference_analyzer", "prompt_generator", "storyboard"],
        connections=[
            {"from": "reference_analyzer.style", "to": "prompt_generator.style"},
            {"from": "reference_analyzer.mood", "to": "prompt_generator.mood"},
            {"from": "prompt_generator.prompt", "to": "storyboard.script"},
        ],
        keywords=[
            "레퍼런스", "분석", "참고", "비슷하게", "스타일", "따라",
            "영감", "inspiration", "reference",
        ],
        estimated_credits=40,
    ),
    
    "quick_prompt": WorkflowTemplate(
        id="quick_prompt",
        name="Quick Prompt Generation",
        name_ko="빠른 프롬프트 생성",
        description="Generate a single video/image prompt quickly",
        description_ko="빠르게 단일 프롬프트만 생성",
        tools=["prompt_generator"],
        connections=[],
        keywords=[
            "프롬프트", "빠르게", "간단히", "하나만", "prompt",
        ],
        estimated_credits=10,
    ),
    
    "storyboard_only": WorkflowTemplate(
        id="storyboard_only",
        name="Storyboard Generation",
        name_ko="스토리보드 생성",
        description="Create a detailed storyboard from a concept",
        description_ko="컨셉으로 상세 스토리보드 생성",
        tools=["storyboard"],
        connections=[],
        keywords=[
            "스토리보드", "씬", "장면", "구성", "시나리오",
        ],
        estimated_credits=10,
    ),
    
    "image_prompt_only": WorkflowTemplate(
        id="image_prompt_only",
        name="Image Prompt Generation",
        name_ko="이미지 프롬프트 생성",
        description="Generate AI image generation prompts",
        description_ko="AI 이미지 생성용 프롬프트 제작",
        tools=["image_tool"],
        connections=[],
        keywords=[
            "이미지", "그림", "사진", "썸네일", "포스터", "image",
        ],
        estimated_credits=10,
    ),
}


# =============================================================================
# TOOL METADATA (차원문 도구 정보)
# =============================================================================

TOOL_METADATA = {
    "prompt_generator": {
        "display_name": "Veo 프롬프트 생성기",
        "display_name_ko": "Veo 프롬프트 생성기",
        "icon": "sparkles",
        "color": "violet",
        "input_ports": ["topic", "style", "mood", "duration"],
        "output_ports": ["prompt", "negative_prompt", "technical"],
        "endpoint": "/api/dimension/1d/generate",
    },
    "storyboard": {
        "display_name": "Storyboard Generator",
        "display_name_ko": "스토리보드 생성기",
        "icon": "layout-grid",
        "color": "emerald",
        "input_ports": ["script", "scene_count", "language"],
        "output_ports": ["scenes"],
        "endpoint": "/api/dimension/2d/create",
    },
    "image_tool": {
        "display_name": "Image Prompt Generator",
        "display_name_ko": "이미지 프롬프트 생성기",
        "icon": "image",
        "color": "amber",
        "input_ports": ["description", "style", "aspect_ratio"],
        "output_ports": ["prompt", "negative_prompt", "parameters"],
        "endpoint": "/api/dimension/3d/generate",
    },
    "reference_analyzer": {
        "display_name": "Reference Analyzer",
        "display_name_ko": "레퍼런스 분석기",
        "icon": "film",
        "color": "cyan",
        "input_ports": ["video_url", "focus_areas"],
        "output_ports": ["analysis", "style", "mood", "recommendations"],
        "endpoint": "/api/dimension/4d/analyze",
    },
}


# =============================================================================
# WORKFLOW PLANNER
# =============================================================================

class WorkflowPlanResult(BaseModel):
    """워크플로우 계획 결과"""
    template_id: str
    template: WorkflowTemplate
    confidence: float
    suggested_params: Dict[str, Any]
    node_chain: List[Dict[str, Any]]
    total_credits: int
    explanation: str
    explanation_ko: str


def match_workflow_template(
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[WorkflowPlanResult]:
    """
    사용자 메시지에서 의도를 분석하고 적절한 워크플로우 템플릿을 매칭
    
    Args:
        user_message: 사용자 채팅 메시지
        context: 추가 컨텍스트 (이전 대화, 세션 정보 등)
    
    Returns:
        WorkflowPlanResult or None if no match
    """
    message_lower = user_message.lower()
    
    best_match: Optional[WorkflowTemplate] = None
    best_score = 0
    
    for template_id, template in WORKFLOW_TEMPLATES.items():
        score = 0
        for keyword in template.keywords:
            if keyword.lower() in message_lower:
                score += 1
        
        # 복합 조건에 가중치 부여
        if score > best_score:
            best_score = score
            best_match = template
    
    # 기본 임계값: 최소 1개 키워드 매칭
    if best_match is None or best_score < 1:
        # 기본값으로 content_creation 제안
        best_match = WORKFLOW_TEMPLATES["content_creation"]
        confidence = 0.5
    else:
        confidence = min(best_score / 3, 1.0)  # 3개 이상 매칭 시 100%
    
    # 노드 체인 생성
    node_chain = build_node_chain(best_match)
    
    return WorkflowPlanResult(
        template_id=best_match.id,
        template=best_match,
        confidence=confidence,
        suggested_params=extract_params_from_message(user_message, best_match),
        node_chain=node_chain,
        total_credits=best_match.estimated_credits,
        explanation=f"Recommended workflow: {best_match.name}",
        explanation_ko=f"추천 워크플로우: {best_match.name_ko}",
    )


def extract_params_from_message(
    message: str,
    template: WorkflowTemplate,
) -> Dict[str, Any]:
    """
    사용자 메시지에서 파라미터 추출 (간단한 규칙 기반)
    
    실제 구현에서는 LLM을 활용하여 더 정교하게 추출
    """
    params = {}
    
    # 주제/토픽 추출 (메시지 전체를 기본값으로)
    params["topic"] = message
    
    # 시간 관련 추출
    import re
    time_match = re.search(r'(\d+)\s*(분|초|seconds?|minutes?)', message)
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        if '분' in unit or 'minute' in unit:
            params["duration"] = f"{value} minutes"
        else:
            params["duration"] = f"{value} seconds"
    
    # 스타일 감지
    style_keywords = {
        "시네마틱": "cinematic",
        "cinematic": "cinematic",
        "다큐": "documentary",
        "documentary": "documentary",
        "브이로그": "vlog",
        "vlog": "vlog",
        "광고": "commercial",
        "commercial": "commercial",
    }
    for ko, en in style_keywords.items():
        if ko in message.lower():
            params["style"] = en
            break
    
    return params


def build_node_chain(template: WorkflowTemplate) -> List[Dict[str, Any]]:
    """
    템플릿에서 연결된 노드 체인 생성
    
    Returns:
        List of node specifications ready for Canvas
    """
    import uuid
    
    nodes = []
    x_offset = 0
    
    for i, tool_id in enumerate(template.tools):
        if tool_id not in TOOL_METADATA:
            continue
        
        tool = TOOL_METADATA[tool_id]
        
        node = {
            "id": str(uuid.uuid4()),
            "tool_id": tool_id,
            "type": "teaching_capsule",
            "display_name": tool["display_name_ko"],
            "position": {"x": x_offset, "y": 100},
            "data": {
                "inputs": {},
                "output": None,
                "editable": True,
                "executed": False,
            },
            "input_ports": tool["input_ports"],
            "output_ports": tool["output_ports"],
            "icon": tool["icon"],
            "color": tool["color"],
            "order": i,
        }
        
        nodes.append(node)
        x_offset += 350  # 노드 간 간격
    
    # 연결 정보 추가
    for node in nodes:
        node["connections"] = []
        for conn in template.connections:
            from_tool = conn["from"].split(".")[0]
            to_tool = conn["to"].split(".")[0]
            
            if node["tool_id"] == to_tool:
                # 이 노드로 들어오는 연결
                from_port = conn["from"].split(".", 1)[1] if "." in conn["from"] else ""
                to_port = conn["to"].split(".", 1)[1] if "." in conn["to"] else ""
                
                # from 노드 찾기
                from_node = next((n for n in nodes if n["tool_id"] == from_tool), None)
                if from_node:
                    node["connections"].append({
                        "from_node_id": from_node["id"],
                        "from_port": from_port,
                        "to_port": to_port,
                    })
    
    return nodes


# =============================================================================
# AGENT TOOL DECLARATION (LLM Function Calling용)
# =============================================================================

WORKFLOW_PLANNER_TOOL = {
    "name": "plan_workflow",
    "description": """사용자의 콘텐츠 제작 의도를 분석하고 적절한 도구 체인(워크플로우)을 추천합니다.
    
사용자가 다음과 같은 요청을 할 때 이 도구를 사용하세요:
- 영상/이미지 콘텐츠를 만들고 싶다고 할 때
- 여러 단계의 작업이 필요해 보일 때
- "처음부터 끝까지", "전체 과정", "파이프라인" 등의 표현을 사용할 때

이 도구는 연결된 노드 체인을 Canvas에 생성합니다.""",
    "parameters": {
        "type": "object",
        "properties": {
            "user_request": {
                "type": "string",
                "description": "사용자의 원래 요청 메시지",
            },
            "preferred_template": {
                "type": "string",
                "enum": list(WORKFLOW_TEMPLATES.keys()),
                "description": "선호하는 워크플로우 템플릿 (선택사항)",
            },
        },
        "required": ["user_request"],
    },
}


# =============================================================================
# SYSTEM PROMPT INJECTION
# =============================================================================

WORKFLOW_PLANNER_SYSTEM_PROMPT = """
## 워크플로우 플래너 가이드

사용자가 콘텐츠 제작을 요청하면 `plan_workflow` 도구를 사용하여 
적절한 도구 체인(열차 워크플로우)을 추천하세요.

### 워크플로우 템플릿

| 템플릿 | 설명 | 포함 도구 |
|--------|------|-----------|
| content_creation | 처음부터 콘텐츠 제작 | 프롬프트 → 스토리보드 → 이미지 |
| reference_to_creation | 레퍼런스 분석 후 창작 | 분석 → 프롬프트 → 스토리보드 |
| quick_prompt | 빠른 프롬프트 생성 | 프롬프트만 |
| storyboard_only | 스토리보드만 | 스토리보드만 |
| image_prompt_only | 이미지 프롬프트만 | 이미지 도구만 |

### 사용 시점

1. 사용자가 "영상 만들기", "콘텐츠 제작" 등 복합 작업을 요청할 때
2. 여러 도구를 순차적으로 사용해야 할 때
3. 사용자가 전체 워크플로우를 원할 때

### 응답 형식

워크플로우를 추천한 후:
1. 추천 이유를 간략히 설명
2. 포함된 도구들과 순서 안내
3. 예상 크레딧 소모량 안내
4. 사용자가 시작하면 Canvas에 연결된 노드들이 생성됨을 안내
"""
