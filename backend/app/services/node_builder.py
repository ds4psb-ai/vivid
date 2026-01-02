"""
Node Builder Service

Teaching 도구 결과를 Canvas Node Spec으로 변환.
스펙: teaching_capsule_agent_integration_spec.md 3.2절
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# =========================================================================
# Capsule Configurations
# =========================================================================

CAPSULE_CONFIGS = {
    "teaching.prompt": {
        "display_name": "Veo 프롬프트 생성기",
        "node_type": "capsule",
        "input_ports": ["topic", "style", "mood", "duration"],
        "output_ports": ["prompt", "negative_prompt", "technical"],
        "icon": "wand",
        "color": "#8B5CF6",
    },
    "teaching.storyboard": {
        "display_name": "스토리보드 생성기",
        "node_type": "capsule",
        "input_ports": ["concept", "scene_count"],
        "output_ports": ["scenes"],
        "icon": "film",
        "color": "#3B82F6",
    },
    "teaching.image": {
        "display_name": "이미지 프롬프트 생성기",
        "node_type": "capsule",
        "input_ports": ["description", "style", "aspect_ratio"],
        "output_ports": ["prompt", "parameters"],
        "icon": "image",
        "color": "#10B981",
    },
    "teaching.reference": {
        "display_name": "레퍼런스 분석기",
        "node_type": "capsule",
        "input_ports": ["video_description", "focus_areas"],
        "output_ports": ["analysis", "recommendations"],
        "icon": "search",
        "color": "#F59E0B",
    },
    # Node Edit 관련
    "node_edit.modify": {
        "display_name": "노드 편집기",
        "node_type": "action",
        "input_ports": ["changes"],
        "output_ports": ["result"],
        "icon": "edit",
        "color": "#EC4899",
    },
    "node_edit.batch": {
        "display_name": "배치 편집기",
        "node_type": "action",
        "input_ports": ["node_ids", "changes"],
        "output_ports": ["results"],
        "icon": "layers",
        "color": "#6366F1",
    },
}


# =========================================================================
# Node Spec Builder
# =========================================================================

def build_node_spec(
    capsule_type: str,
    inputs: Dict[str, Any],
    output: Dict[str, Any],
    position: Optional[Dict[str, float]] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Teaching 도구 결과를 Canvas Node Spec으로 변환
    
    Args:
        capsule_type: 캡슐 타입 (예: "teaching.prompt")
        inputs: 입력 파라미터
        output: 출력 결과
        position: 캔버스 위치 (없으면 자동 배치)
        node_id: 노드 ID (없으면 자동 생성)
        
    Returns:
        Canvas Node Spec 딕셔너리
    """
    config = CAPSULE_CONFIGS.get(capsule_type, {
        "display_name": capsule_type.split(".")[-1].title(),
        "node_type": "generic",
        "input_ports": list(inputs.keys()),
        "output_ports": list(output.keys()) if output else ["output"],
        "icon": "box",
        "color": "#64748B",
    })
    
    return {
        "id": node_id or str(uuid4()),
        "capsule_id": capsule_type,
        "type": config["node_type"],
        "display_name": config["display_name"],
        "position": position or {"x": 0, "y": 0},
        "data": {
            "inputs": inputs,
            "locked_inputs": list(inputs.keys()),  # 채팅에서 채운 값 고정
            "output": output,
            "editable": True,
        },
        "input_ports": config["input_ports"],
        "output_ports": config["output_ports"],
        "icon": config["icon"],
        "color": config["color"],
        "executed": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def build_pipeline_spec(
    nodes: List[Dict[str, Any]],
    connections: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    여러 노드를 파이프라인으로 구성
    
    Args:
        nodes: 노드 스펙 목록
        connections: 연결 목록 [{"source": "node1", "target": "node2"}]
        
    Returns:
        Pipeline Spec
    """
    # 자동 배치
    for i, node in enumerate(nodes):
        if node["position"] == {"x": 0, "y": 0}:
            node["position"] = {"x": i * 300, "y": i * 100}
    
    # 연결 생성
    edges = []
    if connections:
        for conn in connections:
            edges.append({
                "id": f"{conn['source']}-{conn['target']}",
                "source": conn["source"],
                "target": conn["target"],
                "sourceHandle": conn.get("sourceHandle", "output"),
                "targetHandle": conn.get("targetHandle", "input"),
            })
    else:
        # 순차 연결
        for i in range(len(nodes) - 1):
            edges.append({
                "id": f"{nodes[i]['id']}-{nodes[i+1]['id']}",
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"],
                "sourceHandle": "output",
                "targetHandle": "input",
            })
    
    return {
        "pipeline_id": str(uuid4()),
        "nodes": nodes,
        "edges": edges,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


# =========================================================================
# SSE Event Builders
# =========================================================================

def build_node_created_event(
    session_id: str,
    node_spec: Dict[str, Any],
    seq: int,
) -> Dict[str, Any]:
    """Teaching 도구 실행 후 노드 생성 SSE 이벤트"""
    return {
        "event_id": f"{session_id}:{seq}",
        "session_id": session_id,
        "type": "agent.node_created",
        "seq": seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "node_type": "teaching_capsule",
            "node_spec": node_spec,
            "action": "add_to_canvas",
        },
    }


def build_node_updated_event(
    session_id: str,
    node_id: str,
    changes: Dict[str, Any],
    seq: int,
) -> Dict[str, Any]:
    """노드 업데이트 SSE 이벤트"""
    return {
        "event_id": f"{session_id}:{seq}",
        "session_id": session_id,
        "type": "agent.node_updated",
        "seq": seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "node_id": node_id,
            "changes": changes,
            "action": "update_node",
        },
    }


def build_pipeline_created_event(
    session_id: str,
    pipeline_spec: Dict[str, Any],
    seq: int,
) -> Dict[str, Any]:
    """파이프라인 생성 SSE 이벤트"""
    return {
        "event_id": f"{session_id}:{seq}",
        "session_id": session_id,
        "type": "agent.pipeline_created",
        "seq": seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "pipeline_spec": pipeline_spec,
            "action": "create_pipeline",
        },
    }


# =========================================================================
# Utility Functions
# =========================================================================

def get_available_capsule_types() -> List[str]:
    """사용 가능한 캡슐 타입 목록"""
    return list(CAPSULE_CONFIGS.keys())


def get_capsule_config(capsule_type: str) -> Optional[Dict[str, Any]]:
    """캡슐 설정 조회"""
    return CAPSULE_CONFIGS.get(capsule_type)


def validate_capsule_inputs(
    capsule_type: str,
    inputs: Dict[str, Any],
) -> tuple[bool, List[str]]:
    """캡슐 입력 검증"""
    config = CAPSULE_CONFIGS.get(capsule_type)
    if not config:
        return False, [f"Unknown capsule type: {capsule_type}"]
    
    errors = []
    required_ports = config.get("input_ports", [])
    
    # 필수 포트 확인 (첫 번째 포트는 필수)
    if required_ports and required_ports[0] not in inputs:
        errors.append(f"Required input missing: {required_ports[0]}")
    
    return len(errors) == 0, errors


logger.info("NodeBuilder service loaded")
