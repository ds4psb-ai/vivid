"""LangGraph Nodes for Unified Orchestration.

각 노드는 순수 함수(pure function)로 구현됩니다:
- Input: UnifiedState
- Output: UnifiedState (일부 필드 업데이트)

Nodes:
- classify: 쿼리 분류 (4개 분류기 통합)
- route: 소스/도구 선택 (5개 라우터 통합)
- retrieve: 문서 검색 (MultiRAG + RRF)
- execute: 도구/워크플로우 실행
- generate: LLM 응답 생성
- hitl_wait: HITL 체크포인트 대기

Usage:
    from app.core.nodes import (
        classify_node,
        route_node,
        retrieve_node,
        execute_node,
        generate_node,
    )

    # 그래프에 노드 추가
    graph.add_node("classify", classify_node)
    graph.add_node("route", route_node)
"""
from app.core.nodes.classify import classify_node
from app.core.nodes.route import route_node
from app.core.nodes.retrieve import retrieve_node
from app.core.nodes.execute import execute_node
from app.core.nodes.generate import generate_node

__all__ = [
    "classify_node",
    "route_node",
    "retrieve_node",
    "execute_node",
    "generate_node",
]
