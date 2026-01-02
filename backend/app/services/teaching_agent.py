"""
Teaching Agent Integration Service

Teaching 캡슐 + Node Edit 도구를 통합한 Agent 서비스.
STPF 평가 및 피드백 루프 연결.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.services.intent_parser import intent_parser
from app.services.node_manipulator import node_manipulator, VDGNode
from app.schemas.intent_schemas import IntentParseRequest, NodeEditIntent, IntentType

logger = logging.getLogger(__name__)


# =========================================================================
# Tool Declarations (Gemini Function Calling 형식)
# =========================================================================

TEACHING_TOOLS = [
    {
        "name": "generate_veo_prompt",
        "description": "영상 주제/스타일/분위기로 Veo 비디오 생성 프롬프트를 만듭니다",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "영상 주제 또는 컨셉 (필수)"},
                "style": {
                    "type": "string",
                    "enum": ["cinematic", "documentary", "commercial", "artistic", "vlog"],
                    "description": "영상 스타일",
                },
                "mood": {
                    "type": "string",
                    "enum": ["neutral", "dramatic", "calm", "energetic", "melancholic"],
                    "description": "분위기/톤",
                },
                "duration": {"type": "string", "description": "영상 길이"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "create_storyboard",
        "description": "스토리 컨셉으로 씬 단위 스토리보드를 생성합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "스토리 컨셉 또는 시나리오"},
                "scene_count": {"type": "number", "description": "생성할 씬 개수 (3~20)"},
            },
            "required": ["concept"],
        },
    },
    {
        "name": "generate_image_prompt",
        "description": "이미지 설명으로 AI 이미지 생성 프롬프트를 만듭니다",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "이미지 설명"},
                "style": {
                    "type": "string",
                    "enum": ["photorealistic", "cinematic", "anime", "illustration", "3d-render"],
                    "description": "이미지 스타일",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["16:9", "9:16", "1:1", "4:3"],
                    "description": "종횡비",
                },
            },
            "required": ["description"],
        },
    },
    {
        "name": "analyze_reference",
        "description": "영상 레퍼런스의 시네마틱 요소를 분석합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "video_description": {"type": "string", "description": "분석할 영상의 특징 설명"},
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "분석 초점: composition, lighting, color, movement, narrative",
                },
            },
            "required": ["video_description"],
        },
    },
]

NODE_EDIT_TOOLS = [
    {
        "name": "edit_node",
        "description": "VDG 노드의 속성을 편집합니다. 자연어로 편집 의도를 설명하면 자동으로 변환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "편집할 노드의 ID"},
                "edit_description": {"type": "string", "description": "편집 의도 (자연어)"},
            },
            "required": ["node_id", "edit_description"],
        },
    },
    {
        "name": "batch_edit_nodes",
        "description": "여러 노드를 동시에 편집합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "node_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "편집할 노드 ID 목록",
                },
                "edit_description": {"type": "string", "description": "편집 의도 (자연어)"},
            },
            "required": ["node_ids", "edit_description"],
        },
    },
    {
        "name": "preview_changes",
        "description": "변경을 적용하기 전에 미리보기합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "노드 ID"},
                "edit_description": {"type": "string", "description": "편집 의도 (자연어)"},
            },
            "required": ["node_id", "edit_description"],
        },
    },
    {
        "name": "undo_change",
        "description": "마지막 변경을 취소합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "노드 ID"},
                "change_id": {"type": "string", "description": "변경 ID (선택)"},
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "connect_nodes",
        "description": "두 노드를 연결합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "source_node_id": {"type": "string", "description": "소스 노드 ID"},
                "target_node_id": {"type": "string", "description": "타겟 노드 ID"},
                "connection_type": {
                    "type": "string",
                    "enum": ["output", "input", "reference"],
                    "description": "연결 유형",
                },
            },
            "required": ["source_node_id", "target_node_id"],
        },
    },
]

# 전체 통합 도구
UNIFIED_TOOLS = TEACHING_TOOLS + NODE_EDIT_TOOLS


# =========================================================================
# System Prompt
# =========================================================================

TEACHING_SYSTEM_PROMPT = """
## Teaching Tools 가이드

사용자가 영상/이미지 콘텐츠 제작을 요청하면 Teaching 도구를 활용하세요.

### 도구 선택 기준

| 사용자 요청 | 추천 도구 |
|-------------|-----------| 
| "영상 프롬프트", "비디오 만들기" | generate_veo_prompt |
| "스토리보드", "씬 구성" | create_storyboard |
| "이미지 프롬프트", "그림 만들기" | generate_image_prompt |
| "레퍼런스 분석", "영상 분석" | analyze_reference |

## Node Edit Tools 가이드

사용자가 노드 변형을 요청하면:

1. edit_node로 변경 적용
2. preview_changes로 미리보기
3. undo_change로 취소

### 변형 예시
| 사용자 요청 | 변환 |
|-------------|------|
| "더 극적으로" | mood=dramatic, contrast=high |
| "밝게 해줘" | lighting=8 |
| "카메라 줌인" | camera_motion=zoom_in |
| "연결해줘" | connect_nodes(a, b) |

### 주의사항
- STPF 점수가 250 미만이면 변경이 거부됩니다
- 보호된 속성 (node_id, created_at 등)은 변경 불가
"""


# =========================================================================
# Tool Execution Result
# =========================================================================

@dataclass
class ToolExecutionResult:
    """도구 실행 결과"""
    success: bool
    tool_name: str
    output: Dict[str, Any]
    node_spec: Optional[Dict[str, Any]] = None  # Canvas 노드 생성용
    error: Optional[str] = None


# =========================================================================
# Node Store (메모리 기반, 실제로는 DB 사용)
# =========================================================================

class NodeStore:
    """노드 저장소 (메모리 기반)"""
    
    def __init__(self):
        self._nodes: Dict[str, VDGNode] = {}
    
    def get(self, node_id: str) -> Optional[VDGNode]:
        return self._nodes.get(node_id)
    
    def put(self, node: VDGNode) -> None:
        self._nodes[node.node_id] = node
    
    def create(self, node_type: str, properties: Dict[str, Any] = None) -> VDGNode:
        node = VDGNode(
            node_id=str(uuid4())[:8],
            node_type=node_type,
            properties=properties or {},
        )
        self._nodes[node.node_id] = node
        return node
    
    def list_all(self) -> List[VDGNode]:
        return list(self._nodes.values())


# =========================================================================
# Teaching Agent Service
# =========================================================================

class TeachingAgent:
    """
    Teaching + Node Edit 통합 Agent
    
    Features:
    - Teaching 캡슐 호출
    - 노드 편집 (Intent Parser + Node Manipulator)
    - STPF 평가 통합
    - 피드백 루프 연결
    """
    
    def __init__(self):
        self.node_store = NodeStore()
        self._tool_count = 0
        self._error_count = 0
        logger.info("TeachingAgent initialized")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록"""
        return UNIFIED_TOOLS
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return TEACHING_SYSTEM_PROMPT
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> ToolExecutionResult:
        """도구 실행"""
        self._tool_count += 1
        logger.info(f"Executing tool: {tool_name}, args={list(tool_args.keys())}")
        
        try:
            # Teaching Tools
            if tool_name == "generate_veo_prompt":
                return await self._execute_teaching_tool(tool_name, tool_args)
            elif tool_name == "create_storyboard":
                return await self._execute_teaching_tool(tool_name, tool_args)
            elif tool_name == "generate_image_prompt":
                return await self._execute_teaching_tool(tool_name, tool_args)
            elif tool_name == "analyze_reference":
                return await self._execute_teaching_tool(tool_name, tool_args)
            
            # Node Edit Tools
            elif tool_name == "edit_node":
                return await self._execute_edit_node(tool_args)
            elif tool_name == "batch_edit_nodes":
                return await self._execute_batch_edit(tool_args)
            elif tool_name == "preview_changes":
                return await self._execute_preview(tool_args)
            elif tool_name == "undo_change":
                return await self._execute_undo(tool_args)
            elif tool_name == "connect_nodes":
                return await self._execute_connect(tool_args)
            
            else:
                return ToolExecutionResult(
                    success=False,
                    tool_name=tool_name,
                    output={},
                    error=f"Unknown tool: {tool_name}",
                )
                
        except Exception as e:
            self._error_count += 1
            logger.error(f"Tool execution error: {tool_name}, {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                output={},
                error=str(e),
            )
    
    async def _execute_teaching_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """Teaching 도구 실행 (실제로는 teaching.py 라우터 호출)"""
        # 현재는 Mock 응답
        # TODO: teaching.py의 실제 함수 호출
        
        if tool_name == "generate_veo_prompt":
            output = {
                "prompt": f"A {tool_args.get('style', 'cinematic')} video about {tool_args.get('topic')}",
                "negative_prompt": "blurry, dark, overexposed",
                "technical": {"duration": tool_args.get("duration", "15s")},
            }
        elif tool_name == "create_storyboard":
            output = {
                "scenes": [
                    {"scene_number": i, "description": f"Scene {i} for {tool_args.get('concept')}"}
                    for i in range(1, min(tool_args.get("scene_count", 5) + 1, 21))
                ],
            }
        elif tool_name == "generate_image_prompt":
            output = {
                "prompt": f"A {tool_args.get('style', 'photorealistic')} image of {tool_args.get('description')}",
                "parameters": {"aspect_ratio": tool_args.get("aspect_ratio", "16:9")},
            }
        elif tool_name == "analyze_reference":
            output = {
                "analysis": {
                    "focus_areas": tool_args.get("focus_areas", ["composition"]),
                    "description": tool_args.get("video_description"),
                },
                "recommendations": ["Consider improving lighting"],
            }
        else:
            output = {}
        
        # Node Spec 생성
        node_spec = self._build_node_spec(tool_name, tool_args, output)
        
        return ToolExecutionResult(
            success=True,
            tool_name=tool_name,
            output=output,
            node_spec=node_spec,
        )
    
    async def _execute_edit_node(
        self,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """노드 편집 실행"""
        node_id = tool_args.get("node_id")
        edit_description = tool_args.get("edit_description", "")
        
        # 노드 조회 또는 생성
        node = self.node_store.get(node_id)
        if not node:
            node = self.node_store.create("scene", {"name": f"Node {node_id}"})
            node.node_id = node_id
            self.node_store.put(node)
        
        # Intent 파싱
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=edit_description,
            node_id=node_id,
            include_stpf_eval=True,
        ))
        
        if not parse_result.success:
            return ToolExecutionResult(
                success=False,
                tool_name="edit_node",
                output={"parse_error": parse_result.error},
                error=parse_result.error,
            )
        
        # 노드에 적용
        result = await node_manipulator.apply_intent(
            parse_result.intent,
            node,
            send_feedback=True,
        )
        
        return ToolExecutionResult(
            success=result.success,
            tool_name="edit_node",
            output={
                "node_id": result.node_id,
                "changes_applied": result.changes_applied,
                "previous_values": result.previous_values,
                "stpf_score": result.stpf_score,
                "stpf_grade": result.stpf_grade,
                "warnings": result.warnings,
                "change_id": result.change_id,
            },
            error=result.error,
        )
    
    async def _execute_batch_edit(
        self,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """배치 편집 실행"""
        node_ids = tool_args.get("node_ids", [])
        edit_description = tool_args.get("edit_description", "")
        
        # Intent 파싱
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=edit_description,
            include_stpf_eval=True,
        ))
        
        if not parse_result.success:
            return ToolExecutionResult(
                success=False,
                tool_name="batch_edit_nodes",
                output={},
                error=parse_result.error,
            )
        
        # 노드들 조회/생성
        nodes = []
        for nid in node_ids:
            node = self.node_store.get(nid)
            if not node:
                node = self.node_store.create("scene")
                node.node_id = nid
                self.node_store.put(node)
            nodes.append(node)
        
        # 배치 적용
        results = await node_manipulator.batch_apply(parse_result.intent, nodes)
        
        success_count = sum(1 for r in results if r.success)
        
        return ToolExecutionResult(
            success=success_count == len(results),
            tool_name="batch_edit_nodes",
            output={
                "success_count": success_count,
                "total_count": len(results),
                "results": [
                    {
                        "node_id": r.node_id,
                        "success": r.success,
                        "error": r.error,
                        "stpf_score": r.stpf_score,
                    }
                    for r in results
                ],
            },
        )
    
    async def _execute_preview(
        self,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """미리보기 실행"""
        node_id = tool_args.get("node_id")
        edit_description = tool_args.get("edit_description", "")
        
        # 노드 조회
        node = self.node_store.get(node_id)
        if not node:
            node = self.node_store.create("scene")
        
        # Intent 파싱
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=edit_description,
            include_stpf_eval=True,
        ))
        
        if not parse_result.success:
            return ToolExecutionResult(
                success=False,
                tool_name="preview_changes",
                output={},
                error=parse_result.error,
            )
        
        # 미리보기
        preview = node_manipulator.preview_changes(parse_result.intent, node)
        
        return ToolExecutionResult(
            success=True,
            tool_name="preview_changes",
            output=preview,
        )
    
    async def _execute_undo(
        self,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """Undo 실행"""
        node_id = tool_args.get("node_id")
        change_id = tool_args.get("change_id")
        
        node = self.node_store.get(node_id)
        if not node:
            return ToolExecutionResult(
                success=False,
                tool_name="undo_change",
                output={},
                error=f"Node not found: {node_id}",
            )
        
        if change_id:
            result = node_manipulator.undo_by_change_id(node, change_id)
        else:
            # 히스토리에서 마지막 변경 찾기
            history = node_manipulator.get_history(node_id, limit=1)
            if history:
                result = node_manipulator.undo_by_change_id(node, history[0]["change_id"])
            else:
                return ToolExecutionResult(
                    success=False,
                    tool_name="undo_change",
                    output={},
                    error="No changes to undo",
                )
        
        return ToolExecutionResult(
            success=result.success,
            tool_name="undo_change",
            output={
                "node_id": result.node_id,
                "changes_reverted": result.changes_applied,
            },
            error=result.error,
        )
    
    async def _execute_connect(
        self,
        tool_args: Dict[str, Any],
    ) -> ToolExecutionResult:
        """노드 연결 실행"""
        source_id = tool_args.get("source_node_id")
        target_id = tool_args.get("target_node_id")
        connection_type = tool_args.get("connection_type", "output")
        
        # 노드 조회
        source = self.node_store.get(source_id)
        target = self.node_store.get(target_id)
        
        if not source or not target:
            return ToolExecutionResult(
                success=False,
                tool_name="connect_nodes",
                output={},
                error=f"Nodes not found: {source_id}, {target_id}",
            )
        
        # 연결 정보 저장 (실제로는 엣지 DB에 저장)
        connection_id = str(uuid4())[:8]
        
        return ToolExecutionResult(
            success=True,
            tool_name="connect_nodes",
            output={
                "connection_id": connection_id,
                "source_node_id": source_id,
                "target_node_id": target_id,
                "connection_type": connection_type,
            },
        )
    
    def _build_node_spec(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Node Spec 생성 (Canvas용)"""
        configs = {
            "generate_veo_prompt": {
                "display_name": "Veo 프롬프트 생성기",
                "node_type": "capsule",
                "icon": "wand",
            },
            "create_storyboard": {
                "display_name": "스토리보드 생성기",
                "node_type": "capsule",
                "icon": "film",
            },
            "generate_image_prompt": {
                "display_name": "이미지 프롬프트 생성기",
                "node_type": "capsule",
                "icon": "image",
            },
            "analyze_reference": {
                "display_name": "레퍼런스 분석기",
                "node_type": "capsule",
                "icon": "search",
            },
        }
        
        config = configs.get(tool_name, {
            "display_name": tool_name,
            "node_type": "generic",
            "icon": "box",
        })
        
        return {
            "id": str(uuid4()),
            "capsule_id": f"teaching.{tool_name}",
            "type": config["node_type"],
            "display_name": config["display_name"],
            "position": {"x": 0, "y": 0},
            "data": {
                "inputs": inputs,
                "output": output,
                "editable": True,
            },
            "icon": config["icon"],
            "executed": True,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_tools_executed": self._tool_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._tool_count),
            "nodes_in_store": len(self.node_store.list_all()),
        }


# 싱글톤 인스턴스
teaching_agent = TeachingAgent()
