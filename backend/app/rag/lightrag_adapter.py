"""LightRAG Adapter: Graph-based RAG with Entity/Relation Extraction.

EMNLP 2025 SOTA RAG 프레임워크 어댑터.
- 듀얼 레벨 검색 (Low-level: 엔티티+관계, High-level: 테마)
- 엔티티/관계 추출
- 증분 업데이트
- GraphRAG 대비 효율적

Usage:
    from app.rag.lightrag_adapter import get_lightrag_adapter

    adapter = get_lightrag_adapter()

    # 문서 인덱싱 (엔티티/관계 추출)
    await adapter.index_document(
        doc_id="doc_001",
        content="봉준호 감독의 기생충은 계급 갈등을 다룬다...",
        dimension="AD"
    )

    # 듀얼 레벨 검색
    result = await adapter.search(
        query="봉준호 감독의 시각적 특징",
        search_level="hybrid"  # low, high, hybrid
    )
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LightRAGConfig:
    """LightRAG 설정."""
    # 엔티티 추출 설정
    max_entities_per_doc: int = 50
    min_entity_mentions: int = 1
    # 관계 추출 설정
    max_relations_per_doc: int = 100
    relation_confidence_threshold: float = 0.5
    # 검색 설정
    top_k_entities: int = 10
    top_k_relations: int = 20
    # 스토리지 (현재 인메모리, 추후 Qdrant/Neo4j)
    use_qdrant: bool = False
    qdrant_collection: str = "lightrag_entities"


# ============================================================================
# Entity & Relation Types
# ============================================================================

# Crebit 도메인 특화 엔티티 타입
ENTITY_TYPES = {
    "PERSON": ["감독", "director", "auteur", "cinematographer", "actor"],
    "FILM": ["영화", "movie", "film", "작품"],
    "TECHNIQUE": ["기법", "technique", "shot", "angle", "movement"],
    "STYLE": ["스타일", "style", "aesthetic", "visual"],
    "CONCEPT": ["개념", "concept", "theme", "motif"],
    "COLOR": ["색상", "color", "palette", "tone"],
    "COMPOSITION": ["구도", "composition", "framing", "frame"],
}

# 관계 타입
RELATION_TYPES = {
    "USES": "uses technique",
    "CREATES": "creates style",
    "INFLUENCES": "influences",
    "INSPIRED_BY": "inspired by",
    "CONTRASTS": "contrasts with",
    "SIMILAR_TO": "similar to",
    "PART_OF": "part of",
    "EVOKES": "evokes mood",
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Entity:
    """LightRAG 엔티티."""
    entity_id: str
    name: str
    entity_type: str
    description: str = ""
    mentions: int = 1
    attributes: Dict[str, Any] = field(default_factory=dict)
    source_docs: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "mentions": self.mentions,
            "attributes": self.attributes,
        }


@dataclass
class Relation:
    """LightRAG 관계."""
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    description: str = ""
    weight: float = 1.0
    confidence: float = 1.0
    source_docs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "relation_id": self.relation_id,
            "source": self.source_entity_id,
            "target": self.target_entity_id,
            "type": self.relation_type,
            "description": self.description,
            "weight": self.weight,
        }


@dataclass
class LightRAGSearchResult:
    """LightRAG 검색 결과."""
    # Low-level 결과
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    # High-level 결과
    themes: List[str] = field(default_factory=list)
    summary: str = ""
    # 메타
    query: str = ""
    search_level: str = "hybrid"
    confidence: float = 0.0
    query_time_ms: int = 0

    def get_formatted_context(self) -> str:
        """프롬프트 주입용 컨텍스트 생성."""
        parts = []

        # 엔티티 요약
        if self.entities:
            parts.append("### Related Entities")
            for e in self.entities[:5]:
                parts.append(f"- **{e.name}** ({e.entity_type}): {e.description}")

        # 관계 요약
        if self.relations:
            parts.append("\n### Key Relationships")
            for r in self.relations[:5]:
                parts.append(f"- {r.source_entity_id} → {r.relation_type} → {r.target_entity_id}")

        # 테마
        if self.themes:
            parts.append(f"\n### Themes: {', '.join(self.themes)}")

        # 요약
        if self.summary:
            parts.append(f"\n### Summary\n{self.summary}")

        return "\n".join(parts)


# ============================================================================
# Entity/Relation Extraction (Simple Rule-based)
# ============================================================================

class EntityExtractor:
    """간단한 규칙 기반 엔티티 추출기.

    실제 프로덕션에서는 LLM 기반 추출 또는 spaCy NER 사용.
    """

    # 알려진 엔티티 (사전 정의)
    KNOWN_ENTITIES = {
        # Auteurs
        "봉준호": ("PERSON", "Korean film director known for Parasite"),
        "bong joon-ho": ("PERSON", "Korean film director known for Parasite"),
        "박찬욱": ("PERSON", "Korean director known for Oldboy"),
        "park chan-wook": ("PERSON", "Korean director known for Oldboy"),
        "신카이 마코토": ("PERSON", "Japanese animator known for Your Name"),
        "shinkai makoto": ("PERSON", "Japanese animator known for Your Name"),
        # Techniques
        "deep focus": ("TECHNIQUE", "Camera technique keeping all planes in focus"),
        "tracking shot": ("TECHNIQUE", "Camera movement following subject"),
        "slow motion": ("TECHNIQUE", "Reduced playback speed effect"),
        "split screen": ("TECHNIQUE", "Multiple images shown simultaneously"),
        "match cut": ("TECHNIQUE", "Edit connecting similar visual elements"),
        # Styles
        "minimalist": ("STYLE", "Sparse, essential visual approach"),
        "expressionist": ("STYLE", "Distorted reality for emotional effect"),
        "noir": ("STYLE", "Dark, shadowy visual style"),
        "naturalistic": ("STYLE", "Realistic, documentary-like approach"),
        # Colors
        "warm palette": ("COLOR", "Orange, red, yellow dominant colors"),
        "cool palette": ("COLOR", "Blue, green, purple dominant colors"),
        "desaturated": ("COLOR", "Reduced color intensity"),
        "high contrast": ("COLOR", "Strong difference between lights and darks"),
    }

    def extract_entities(
        self,
        content: str,
        max_entities: int = 50,
    ) -> List[Entity]:
        """텍스트에서 엔티티 추출.

        Args:
            content: 텍스트 콘텐츠
            max_entities: 최대 엔티티 수

        Returns:
            추출된 엔티티 목록
        """
        content_lower = content.lower()
        entities: Dict[str, Entity] = {}

        # 알려진 엔티티 매칭
        for name, (entity_type, description) in self.KNOWN_ENTITIES.items():
            if name.lower() in content_lower:
                entity_id = self._make_entity_id(name)
                if entity_id not in entities:
                    entities[entity_id] = Entity(
                        entity_id=entity_id,
                        name=name,
                        entity_type=entity_type,
                        description=description,
                        mentions=1,
                    )
                else:
                    entities[entity_id].mentions += 1

        # 패턴 기반 추출 (간단한 예시)
        # "감독 이름" 패턴
        director_pattern = r"(\w+)\s*감독"
        for match in re.finditer(director_pattern, content):
            name = match.group(1)
            entity_id = self._make_entity_id(name)
            if entity_id not in entities and len(name) > 1:
                entities[entity_id] = Entity(
                    entity_id=entity_id,
                    name=name,
                    entity_type="PERSON",
                    description=f"Director mentioned in context",
                )

        # 정렬 (언급 횟수 기준)
        sorted_entities = sorted(
            entities.values(),
            key=lambda e: e.mentions,
            reverse=True,
        )

        return sorted_entities[:max_entities]

    def _make_entity_id(self, name: str) -> str:
        """엔티티 ID 생성."""
        return hashlib.md5(name.lower().encode()).hexdigest()[:12]


class RelationExtractor:
    """간단한 관계 추출기."""

    # 관계 패턴
    RELATION_PATTERNS = [
        (r"(\w+)(?:는|은|가|이)\s*(\w+)(?:를|을)\s*사용", "USES"),
        (r"(\w+)(?:의|가)\s*(\w+)\s*스타일", "CREATES"),
        (r"(\w+)(?:에게|한테)\s*영향", "INFLUENCES"),
        (r"(\w+)(?:와|과)\s*유사", "SIMILAR_TO"),
        (r"(\w+)(?:와|과)\s*대조", "CONTRASTS"),
    ]

    def extract_relations(
        self,
        content: str,
        entities: List[Entity],
        max_relations: int = 100,
    ) -> List[Relation]:
        """텍스트에서 관계 추출.

        Args:
            content: 텍스트 콘텐츠
            entities: 추출된 엔티티 목록
            max_relations: 최대 관계 수

        Returns:
            추출된 관계 목록
        """
        relations: List[Relation] = []
        entity_names = {e.name.lower(): e.entity_id for e in entities}

        # 패턴 기반 추출
        for pattern, rel_type in self.RELATION_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                source_name = match.group(1).lower()
                target_name = match.group(2).lower() if match.lastindex >= 2 else ""

                source_id = entity_names.get(source_name)
                target_id = entity_names.get(target_name)

                if source_id and target_id:
                    relations.append(Relation(
                        relation_id=f"rel_{len(relations)}",
                        source_entity_id=source_id,
                        target_entity_id=target_id,
                        relation_type=rel_type,
                        description=match.group(0),
                    ))

        # 엔티티 co-occurrence 기반 암묵적 관계
        # 같은 문장에 등장하는 엔티티는 관련있다고 가정
        sentences = re.split(r'[.!?。]', content)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            present_entities = [
                (name, eid) for name, eid in entity_names.items()
                if name in sentence_lower
            ]

            for i, (name1, eid1) in enumerate(present_entities):
                for name2, eid2 in present_entities[i+1:]:
                    relations.append(Relation(
                        relation_id=f"rel_cooc_{len(relations)}",
                        source_entity_id=eid1,
                        target_entity_id=eid2,
                        relation_type="RELATED_TO",
                        description="Co-occurrence in same sentence",
                        confidence=0.6,
                    ))

        return relations[:max_relations]


# ============================================================================
# LightRAG Adapter
# ============================================================================

class LightRAGAdapter:
    """LightRAG 어댑터.

    EMNLP 2025 SOTA 그래프 기반 RAG.
    듀얼 레벨 검색: Low-level (엔티티+관계) + High-level (테마)
    """

    def __init__(self, config: Optional[LightRAGConfig] = None):
        """Initialize adapter.

        Args:
            config: LightRAG 설정
        """
        self.config = config or LightRAGConfig()
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()

        # 인메모리 스토리지 (추후 Qdrant/Neo4j로 교체)
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}
        self._doc_index: Dict[str, Set[str]] = {}  # doc_id → entity_ids
        self._dimension_index: Dict[str, Set[str]] = {}  # dimension → entity_ids

    async def index_document(
        self,
        doc_id: str,
        content: str,
        dimension: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """문서 인덱싱 (엔티티/관계 추출 및 저장).

        Args:
            doc_id: 문서 ID
            content: 문서 내용
            dimension: 차원 코드
            metadata: 추가 메타데이터

        Returns:
            인덱싱 결과 (엔티티 수, 관계 수)
        """
        import time
        start_time = time.monotonic()

        # 엔티티 추출
        entities = self.entity_extractor.extract_entities(
            content,
            max_entities=self.config.max_entities_per_doc,
        )

        # 관계 추출
        relations = self.relation_extractor.extract_relations(
            content,
            entities,
            max_relations=self.config.max_relations_per_doc,
        )

        # 저장
        entity_ids = set()
        for entity in entities:
            entity.source_docs.append(doc_id)
            if entity.entity_id in self._entities:
                # 기존 엔티티 업데이트
                existing = self._entities[entity.entity_id]
                existing.mentions += entity.mentions
                if doc_id not in existing.source_docs:
                    existing.source_docs.append(doc_id)
            else:
                self._entities[entity.entity_id] = entity
            entity_ids.add(entity.entity_id)

        for relation in relations:
            relation.source_docs.append(doc_id)
            if relation.confidence >= self.config.relation_confidence_threshold:
                self._relations[relation.relation_id] = relation

        # 인덱스 업데이트
        self._doc_index[doc_id] = entity_ids
        if dimension:
            if dimension not in self._dimension_index:
                self._dimension_index[dimension] = set()
            self._dimension_index[dimension].update(entity_ids)

        duration_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            f"[LightRAG] Indexed doc {doc_id}: "
            f"{len(entities)} entities, {len(relations)} relations ({duration_ms}ms)"
        )

        return {
            "doc_id": doc_id,
            "entities_count": len(entities),
            "relations_count": len(relations),
            "duration_ms": duration_ms,
        }

    async def search(
        self,
        query: str,
        search_level: str = "hybrid",
        dimension: Optional[str] = None,
        top_k: int = 10,
    ) -> LightRAGSearchResult:
        """듀얼 레벨 검색.

        Args:
            query: 검색 쿼리
            search_level: 검색 레벨 (low, high, hybrid)
            dimension: 차원 필터
            top_k: 상위 결과 수

        Returns:
            LightRAGSearchResult
        """
        import time
        start_time = time.monotonic()

        result = LightRAGSearchResult(
            query=query,
            search_level=search_level,
        )

        # Low-level: 엔티티 검색
        if search_level in ("low", "hybrid"):
            query_entities = self.entity_extractor.extract_entities(query, max_entities=5)
            query_entity_names = {e.name.lower() for e in query_entities}

            # 매칭되는 엔티티 찾기
            matched_entities = []
            for entity in self._entities.values():
                # 이름 매칭
                if entity.name.lower() in query_entity_names:
                    matched_entities.append((entity, 1.0))
                # 부분 매칭
                elif any(qe in entity.name.lower() for qe in query.lower().split()):
                    matched_entities.append((entity, 0.5))
                # 설명 매칭
                elif query.lower() in entity.description.lower():
                    matched_entities.append((entity, 0.3))

            # 차원 필터
            if dimension and dimension in self._dimension_index:
                dim_entities = self._dimension_index[dimension]
                matched_entities = [
                    (e, s) for e, s in matched_entities
                    if e.entity_id in dim_entities
                ]

            # 정렬 및 상위 K
            matched_entities.sort(key=lambda x: x[1], reverse=True)
            result.entities = [e for e, _ in matched_entities[:top_k]]

            # 관련 관계 찾기
            entity_ids = {e.entity_id for e in result.entities}
            for relation in self._relations.values():
                if (relation.source_entity_id in entity_ids or
                    relation.target_entity_id in entity_ids):
                    result.relations.append(relation)

        # High-level: 테마 추출
        if search_level in ("high", "hybrid"):
            # 간단한 테마 추출 (키워드 기반)
            theme_keywords = {
                "visual": ["시각적", "visual", "aesthetic", "look"],
                "narrative": ["서사", "narrative", "story", "plot"],
                "technical": ["기술", "technical", "camera", "lighting"],
                "emotional": ["감정", "emotional", "mood", "tone"],
                "style": ["스타일", "style", "genre", "auteur"],
            }

            query_lower = query.lower()
            for theme, keywords in theme_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    result.themes.append(theme)

            # 요약 생성 (간단한 버전)
            if result.entities:
                entity_names = [e.name for e in result.entities[:3]]
                result.summary = (
                    f"Query relates to: {', '.join(entity_names)}. "
                    f"Themes: {', '.join(result.themes) if result.themes else 'general'}."
                )

        # 신뢰도 계산
        if result.entities or result.relations:
            result.confidence = min(1.0, (len(result.entities) + len(result.relations)) / 10)

        result.query_time_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            f"[LightRAG] Search completed: {len(result.entities)} entities, "
            f"{len(result.relations)} relations ({result.query_time_ms}ms)"
        )

        return result

    async def get_entity_graph(
        self,
        entity_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """엔티티 중심 그래프 조회.

        Args:
            entity_id: 시작 엔티티 ID
            depth: 탐색 깊이

        Returns:
            그래프 구조 (nodes, edges)
        """
        nodes: Dict[str, Entity] = {}
        edges: List[Relation] = []
        visited: Set[str] = set()

        def traverse(eid: str, current_depth: int):
            if eid in visited or current_depth > depth:
                return
            visited.add(eid)

            if eid in self._entities:
                nodes[eid] = self._entities[eid]

                for relation in self._relations.values():
                    if relation.source_entity_id == eid:
                        edges.append(relation)
                        traverse(relation.target_entity_id, current_depth + 1)
                    elif relation.target_entity_id == eid:
                        edges.append(relation)
                        traverse(relation.source_entity_id, current_depth + 1)

        traverse(entity_id, 0)

        return {
            "nodes": [n.to_dict() for n in nodes.values()],
            "edges": [e.to_dict() for e in edges],
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회."""
        return {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "indexed_documents": len(self._doc_index),
            "dimensions": list(self._dimension_index.keys()),
            "entity_types": self._count_entity_types(),
            "relation_types": self._count_relation_types(),
        }

    def _count_entity_types(self) -> Dict[str, int]:
        """엔티티 타입별 카운트."""
        counts: Dict[str, int] = {}
        for entity in self._entities.values():
            counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
        return counts

    def _count_relation_types(self) -> Dict[str, int]:
        """관계 타입별 카운트."""
        counts: Dict[str, int] = {}
        for relation in self._relations.values():
            counts[relation.relation_type] = counts.get(relation.relation_type, 0) + 1
        return counts

    def clear(self) -> None:
        """모든 데이터 클리어."""
        self._entities.clear()
        self._relations.clear()
        self._doc_index.clear()
        self._dimension_index.clear()


# ============================================================================
# Singleton
# ============================================================================

_lightrag_adapter: Optional[LightRAGAdapter] = None


def get_lightrag_adapter(
    config: Optional[LightRAGConfig] = None,
) -> LightRAGAdapter:
    """LightRAG 어댑터 싱글톤 반환.

    Args:
        config: 설정 (최초 호출 시에만 적용)

    Returns:
        LightRAGAdapter instance
    """
    global _lightrag_adapter
    if _lightrag_adapter is None:
        _lightrag_adapter = LightRAGAdapter(config)
    return _lightrag_adapter


def reset_lightrag_adapter() -> None:
    """어댑터 리셋 (테스트용)."""
    global _lightrag_adapter
    _lightrag_adapter = None
