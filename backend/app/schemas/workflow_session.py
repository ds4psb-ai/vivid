"""
Workflow Session Schema and State Management

Defines the session state for workflow orchestration.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class WorkflowStatus(str, Enum):
    """워크플로우 세션 상태"""
    PLANNING = "planning"      # 워크플로우 계획 중
    READY = "ready"            # 실행 준비 완료
    EXECUTING = "executing"    # 실행 중
    PAUSED = "paused"          # 일시 중지 (사용자 입력 대기)
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패


class NodeConnection(BaseModel):
    """노드 간 연결 정보"""
    from_node_id: str
    from_port: str
    to_node_id: str
    to_port: str


class WorkflowNodeState(BaseModel):
    """워크플로우 내 개별 노드 상태"""
    node_id: str
    tool_id: str
    order: int
    status: str = "pending"  # pending, executing, completed, failed
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowSession(BaseModel):
    """워크플로우 세션 상태"""
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Workflow Configuration
    workflow_template_id: str
    workflow_name: str
    workflow_description: str
    
    # Execution State
    status: WorkflowStatus = WorkflowStatus.PLANNING
    current_step: int = 0
    total_steps: int = 0
    
    # Node State
    nodes: List[WorkflowNodeState] = Field(default_factory=list)
    connections: List[NodeConnection] = Field(default_factory=list)
    
    # Context
    original_request: str = ""
    extracted_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Credits
    estimated_credits: int = 0
    consumed_credits: int = 0
    
    # Canvas Integration
    canvas_session_id: Optional[str] = None
    created_node_ids: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class WorkflowSessionManager:
    """워크플로우 세션 관리자 (인메모리, 추후 DB 연동)"""
    
    def __init__(self):
        self._sessions: Dict[str, WorkflowSession] = {}
    
    def create_session(
        self,
        user_id: str,
        template_id: str,
        template_name: str,
        template_description: str,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, str]],
        original_request: str,
        extracted_params: Dict[str, Any],
        estimated_credits: int,
    ) -> WorkflowSession:
        """새 워크플로우 세션 생성"""
        
        # 노드 상태 초기화
        node_states = [
            WorkflowNodeState(
                node_id=node["id"],
                tool_id=node["tool_id"],
                order=node.get("order", i),
                inputs=node.get("data", {}).get("inputs", {}),
            )
            for i, node in enumerate(nodes)
        ]
        
        # 연결 정보 변환
        node_connections = []
        for node in nodes:
            for conn in node.get("connections", []):
                node_connections.append(NodeConnection(
                    from_node_id=conn["from_node_id"],
                    from_port=conn["from_port"],
                    to_node_id=node["id"],
                    to_port=conn["to_port"],
                ))
        
        session = WorkflowSession(
            user_id=user_id,
            workflow_template_id=template_id,
            workflow_name=template_name,
            workflow_description=template_description,
            total_steps=len(nodes),
            nodes=node_states,
            connections=node_connections,
            original_request=original_request,
            extracted_params=extracted_params,
            estimated_credits=estimated_credits,
            status=WorkflowStatus.READY,
        )
        
        self._sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        """세션 조회"""
        return self._sessions.get(session_id)
    
    def update_session(self, session: WorkflowSession) -> WorkflowSession:
        """세션 업데이트"""
        session.updated_at = datetime.utcnow()
        self._sessions[session.id] = session
        return session
    
    def advance_step(self, session_id: str) -> Optional[WorkflowSession]:
        """다음 단계로 진행"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if session.current_step < session.total_steps - 1:
            session.current_step += 1
            session.status = WorkflowStatus.EXECUTING
        else:
            session.status = WorkflowStatus.COMPLETED
        
        return self.update_session(session)
    
    def mark_node_completed(
        self,
        session_id: str,
        node_id: str,
        output: Dict[str, Any],
    ) -> Optional[WorkflowSession]:
        """노드 실행 완료 처리"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        for node in session.nodes:
            if node.node_id == node_id:
                node.status = "completed"
                node.output = output
                node.executed_at = datetime.utcnow()
                break
        
        # 다음 노드에 출력 전달
        self._propagate_outputs(session, node_id, output)
        
        return self.update_session(session)
    
    def _propagate_outputs(
        self,
        session: WorkflowSession,
        completed_node_id: str,
        output: Dict[str, Any],
    ):
        """완료된 노드의 출력을 연결된 다음 노드로 전달"""
        for conn in session.connections:
            if conn.from_node_id == completed_node_id:
                # 다음 노드 찾기
                for node in session.nodes:
                    if node.node_id == conn.to_node_id:
                        # 출력 포트에서 값 추출
                        value = self._extract_port_value(output, conn.from_port)
                        if value is not None:
                            # 입력 포트에 값 설정
                            node.inputs[conn.to_port] = value
                        break
    
    def _extract_port_value(
        self,
        output: Dict[str, Any],
        port_path: str,
    ) -> Any:
        """출력에서 포트 경로에 해당하는 값 추출
        
        예: "scenes[0].description" → output["scenes"][0]["description"]
        """
        import re
        
        current = output
        parts = re.split(r'\.|\[|\]', port_path)
        parts = [p for p in parts if p]  # 빈 문자열 제거
        
        try:
            for part in parts:
                if part.isdigit():
                    current = current[int(part)]
                else:
                    current = current[part]
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    def get_user_sessions(self, user_id: str) -> List[WorkflowSession]:
        """사용자의 모든 세션 조회"""
        return [s for s in self._sessions.values() if s.user_id == user_id]


# 전역 세션 매니저 인스턴스
workflow_session_manager = WorkflowSessionManager()
