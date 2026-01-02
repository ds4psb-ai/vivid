"""
Agent Tool Executor

스펙: teaching_capsule_agent_integration_spec.md 3.1절
Agent에서 Teaching 도구 호출을 처리.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.node_builder import build_node_spec

logger = logging.getLogger(__name__)


# =========================================================================
# Tool Handler Registry
# =========================================================================

TOOL_HANDLERS = {
    # Teaching Tools
    "generate_veo_prompt": {
        "endpoint": "/api/v1/teaching/prompt/generate",
        "capsule_type": "teaching.prompt",
        "required_args": ["topic"],
        "default_args": {"style": "cinematic", "mood": "neutral"},
    },
    "create_storyboard": {
        "endpoint": "/api/v1/teaching/storyboard/create",
        "capsule_type": "teaching.storyboard",
        "required_args": ["concept"],
        "default_args": {"scene_count": 5},
    },
    "generate_image_prompt": {
        "endpoint": "/api/v1/teaching/image/generate",
        "capsule_type": "teaching.image",
        "required_args": ["description"],
        "default_args": {"style": "photorealistic", "aspect_ratio": "16:9"},
    },
    "analyze_reference": {
        "endpoint": "/api/v1/teaching/reference/analyze",
        "capsule_type": "teaching.reference",
        "required_args": ["video_description"],
        "default_args": {"focus_areas": ["composition", "lighting"]},
    },
    # Node Edit Tools
    "edit_node": {
        "endpoint": "/api/v1/intent/parse",
        "capsule_type": "node_edit.modify",
        "required_args": ["node_id", "edit_description"],
        "default_args": {},
    },
    "batch_edit_nodes": {
        "endpoint": "/api/v1/intent/batch",
        "capsule_type": "node_edit.batch",
        "required_args": ["node_ids", "edit_description"],
        "default_args": {},
    },
    "preview_changes": {
        "endpoint": "/api/v1/intent/parse",
        "capsule_type": "node_edit.modify",
        "required_args": ["node_id", "edit_description"],
        "default_args": {},
    },
    "undo_change": {
        "endpoint": None,  # Local execution
        "capsule_type": None,
        "required_args": ["node_id"],
        "default_args": {},
    },
    "connect_nodes": {
        "endpoint": None,  # Local execution
        "capsule_type": None,
        "required_args": ["source_node_id", "target_node_id"],
        "default_args": {"connection_type": "output"},
    },
}


# =========================================================================
# Tool Executor
# =========================================================================

class AgentToolExecutor:
    """
    Agent 도구 실행기
    
    Features:
    - Tool argument validation
    - Teaching endpoint 호출
    - Node Spec 생성
    - SSE 이벤트 발행
    """
    
    def __init__(self):
        self._exec_count = 0
        self._error_count = 0
        logger.info("AgentToolExecutor initialized")
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """도구 정보 조회"""
        return TOOL_HANDLERS.get(tool_name)
    
    def validate_tool_args(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> tuple[bool, str]:
        """도구 인자 검증"""
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return False, f"Unknown tool: {tool_name}"
        
        # 필수 인자 확인
        for required in handler.get("required_args", []):
            if required not in tool_args:
                return False, f"Missing required argument: {required}"
        
        return True, "OK"
    
    def merge_with_defaults(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """기본값과 병합"""
        handler = TOOL_HANDLERS.get(tool_name, {})
        defaults = handler.get("default_args", {})
        
        merged = {**defaults, **tool_args}
        return merged
    
    async def execute(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: Optional[str] = None,
        byok_key: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        도구 실행
        
        Args:
            tool_name: 도구 이름
            tool_args: 도구 인자
            user_id: 사용자 ID
            byok_key: BYOK 키
            db: 데이터베이스 세션
            
        Returns:
            {success, output, node_spec, capsule_id, error}
        """
        self._exec_count += 1
        
        # 1. 검증
        valid, error = self.validate_tool_args(tool_name, tool_args)
        if not valid:
            self._error_count += 1
            return {"success": False, "error": error}
        
        # 2. 기본값 병합
        merged_args = self.merge_with_defaults(tool_name, tool_args)
        
        handler = TOOL_HANDLERS.get(tool_name)
        
        # 3. 로컬 실행 (endpoint 없는 경우)
        if not handler.get("endpoint"):
            result = await self._execute_local(tool_name, merged_args)
            return result
        
        # 4. Teaching 도구 실행 (실제로는 HTTP 호출 또는 직접 함수 호출)
        try:
            output = await self._call_teaching_endpoint(
                handler["endpoint"],
                merged_args,
                byok_key,
            )
            
            # 5. Node Spec 생성
            node_spec = None
            if handler.get("capsule_type"):
                node_spec = build_node_spec(
                    capsule_type=handler["capsule_type"],
                    inputs=merged_args,
                    output=output,
                )
            
            logger.info(
                f"Tool executed: {tool_name}, "
                f"has_node_spec={node_spec is not None}"
            )
            
            return {
                "success": True,
                "output": output,
                "node_spec": node_spec,
                "capsule_id": handler.get("capsule_type"),
            }
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Tool execution error: {tool_name}, {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_teaching_endpoint(
        self,
        endpoint: str,
        args: Dict[str, Any],
        byok_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Teaching 엔드포인트 호출 (Mock)"""
        # TODO: 실제 HTTP 호출 또는 직접 함수 호출
        # 현재는 Mock 결과 반환
        
        if "prompt" in endpoint:
            return {
                "prompt": f"A {args.get('style', 'cinematic')} video about {args.get('topic')}",
                "negative_prompt": "blurry, dark, overexposed",
                "technical": {"duration": args.get("duration", "15s")},
            }
        elif "storyboard" in endpoint:
            return {
                "scenes": [
                    {"scene_number": i, "description": f"Scene {i}"}
                    for i in range(1, args.get("scene_count", 5) + 1)
                ],
            }
        elif "image" in endpoint:
            return {
                "prompt": f"A {args.get('style', 'photorealistic')} image of {args.get('description')}",
                "parameters": {"aspect_ratio": args.get("aspect_ratio", "16:9")},
            }
        elif "reference" in endpoint:
            return {
                "analysis": {
                    "focus_areas": args.get("focus_areas", []),
                    "summary": f"Analysis of {args.get('video_description')}",
                },
                "recommendations": ["Consider improving lighting"],
            }
        elif "intent" in endpoint:
            # Intent 파싱
            from app.services.intent_parser import intent_parser
            from app.schemas.intent_schemas import IntentParseRequest
            
            result = intent_parser.parse(IntentParseRequest(
                user_input=args.get("edit_description", ""),
                node_id=args.get("node_id"),
                include_stpf_eval=True,
            ))
            
            return {
                "success": result.success,
                "changes": result.intent.to_simple_dict() if result.intent else {},
                "stpf_score": result.stpf_score,
                "stpf_grade": result.stpf_grade,
            }
        
        return {}
    
    async def _execute_local(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """로컬 도구 실행"""
        if tool_name == "undo_change":
            from app.services.teaching_agent import teaching_agent
            result = await teaching_agent.execute_tool(tool_name, args)
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        
        if tool_name == "connect_nodes":
            from app.services.teaching_agent import teaching_agent
            result = await teaching_agent.execute_tool(tool_name, args)
            return {
                "success": result.success,
                "output": result.output,
                "node_spec": None,
            }
        
        return {"success": False, "error": f"Unknown local tool: {tool_name}"}
    
    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_executions": self._exec_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._exec_count),
            "available_tools": list(TOOL_HANDLERS.keys()),
        }


# 싱글톤 인스턴스
agent_tool_executor = AgentToolExecutor()
