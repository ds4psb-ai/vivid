"""
Vector Service - Qdrant-based vector search for tools

Provides:
- Tool embedding and indexing
- Similarity search
- Personalized recommendations
"""

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.services.embedder import Embedder, get_embedder

logger = logging.getLogger(__name__)

COLLECTION_NAME = "vivid_tools"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2


class VectorService:
    """
    Qdrant-based vector search service for tools.
    
    Example:
        service = VectorService()
        await service.index_tool(tool)
        results = await service.search("resize image", limit=5)
    """
    
    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder or get_embedder()
        self._client: Optional[QdrantClient] = None
    
    @property
    def client(self) -> QdrantClient:
        """Lazy-initialize Qdrant client."""
        if self._client is None:
            try:
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                    timeout=10,
                )
                logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise
        return self._client
    
    def ensure_collection(self) -> bool:
        """
        Ensure the tools collection exists.
        
        Returns:
            True if collection exists or was created
        """
        try:
            collections = self.client.get_collections()
            exists = any(c.name == COLLECTION_NAME for c in collections.collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {COLLECTION_NAME}")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False
    
    def _build_tool_text(self, tool: Dict[str, Any]) -> str:
        """Build searchable text from tool data."""
        parts = [
            tool.get("display_name", ""),
            tool.get("description", ""),
            tool.get("category", ""),
        ]
        # Add input/output schema keys as context
        input_schema = tool.get("input_schema", {})
        if isinstance(input_schema, dict):
            parts.extend(input_schema.get("properties", {}).keys())
        
        return " ".join(str(p) for p in parts if p)
    
    def index_tool(self, tool: Dict[str, Any]) -> bool:
        """
        Index a tool in Qdrant.
        
        Args:
            tool: Tool dict with id, display_name, description, etc.
            
        Returns:
            True if successful
        """
        try:
            self.ensure_collection()
            
            tool_id = tool.get("id")
            if not tool_id:
                logger.warning("Tool missing id, skipping")
                return False
            
            text = self._build_tool_text(tool)
            vector = self.embedder.embed(text)
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    qdrant_models.PointStruct(
                        id=tool_id,
                        vector=vector,
                        payload={
                            "tool_key": tool.get("tool_key"),
                            "display_name": tool.get("display_name"),
                            "description": tool.get("description", "")[:500],
                            "category": tool.get("category"),
                            "tier": tool.get("tier"),
                            "usage_count": tool.get("usage_count", 0),
                            "quality_rating": tool.get("quality_rating"),
                        },
                    )
                ],
            )
            logger.debug(f"Indexed tool: {tool_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index tool {tool.get('id')}: {e}")
            return False
    
    def delete_tool(self, tool_id: str) -> bool:
        """Remove a tool from the index."""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=qdrant_models.PointIdsList(points=[tool_id]),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete tool {tool_id}: {e}")
            return False
    
    def search(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_tier: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar tools.
        
        Args:
            query: Search query text
            limit: Maximum results
            category: Filter by category
            min_tier: Minimum tier (experimental, verified, certified)
            
        Returns:
            List of matching tools with scores
        """
        try:
            self.ensure_collection()
            
            vector = self.embedder.embed(query)
            
            # Build filters
            filters = []
            if category:
                filters.append(
                    qdrant_models.FieldCondition(
                        key="category",
                        match=qdrant_models.MatchValue(value=category),
                    )
                )
            if min_tier:
                tier_order = {"experimental": 0, "verified": 1, "certified": 2}
                min_order = tier_order.get(min_tier, 0)
                allowed_tiers = [t for t, o in tier_order.items() if o >= min_order]
                filters.append(
                    qdrant_models.FieldCondition(
                        key="tier",
                        match=qdrant_models.MatchAny(any=allowed_tiers),
                    )
                )
            
            query_filter = None
            if filters:
                query_filter = qdrant_models.Filter(must=filters)
            
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
                query_filter=query_filter,
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    **r.payload,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_recommendations(
        self,
        recent_tool_ids: List[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on recent tool usage.
        
        Args:
            recent_tool_ids: List of recently used tool IDs
            limit: Maximum recommendations
            
        Returns:
            List of recommended tools
        """
        if not recent_tool_ids:
            return []
        
        try:
            # Get vectors of recent tools
            points = self.client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=recent_tool_ids[:5],  # Use up to 5 recent
                with_vectors=True,
            )
            
            if not points:
                return []
            
            # Average the vectors
            vectors = [p.vector for p in points if p.vector]
            if not vectors:
                return []
            
            avg_vector = [
                sum(v[i] for v in vectors) / len(vectors)
                for i in range(len(vectors[0]))
            ]
            
            # Search with averaged vector, excluding recent tools
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=avg_vector,
                limit=limit + len(recent_tool_ids),
                query_filter=qdrant_models.Filter(
                    must_not=[
                        qdrant_models.HasIdCondition(has_id=recent_tool_ids)
                    ]
                ),
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    **r.payload,
                }
                for r in results[:limit]
            ]
        except Exception as e:
            logger.error(f"Recommendations failed: {e}")
            return []
    
    def reindex_all(self, tools: List[Dict[str, Any]]) -> int:
        """
        Reindex all tools (admin operation).
        
        Args:
            tools: List of all tools
            
        Returns:
            Number of tools indexed
        """
        try:
            # Recreate collection
            try:
                self.client.delete_collection(COLLECTION_NAME)
            except UnexpectedResponse:
                pass  # Collection doesn't exist
            
            self.ensure_collection()
            
            # Batch index
            count = 0
            batch_size = 100
            for i in range(0, len(tools), batch_size):
                batch = tools[i:i + batch_size]
                texts = [self._build_tool_text(t) for t in batch]
                vectors = self.embedder.embed_batch(texts)
                
                points = []
                for tool, vector in zip(batch, vectors):
                    tool_id = tool.get("id")
                    if tool_id:
                        points.append(
                            qdrant_models.PointStruct(
                                id=tool_id,
                                vector=vector,
                                payload={
                                    "tool_key": tool.get("tool_key"),
                                    "display_name": tool.get("display_name"),
                                    "description": tool.get("description", "")[:500],
                                    "category": tool.get("category"),
                                    "tier": tool.get("tier"),
                                    "usage_count": tool.get("usage_count", 0),
                                    "quality_rating": tool.get("quality_rating"),
                                },
                            )
                        )
                
                if points:
                    self.client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=points,
                    )
                    count += len(points)
            
            logger.info(f"Reindexed {count} tools")
            return count
        except Exception as e:
            logger.error(f"Reindex failed: {e}")
            return 0


# Singleton
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get the singleton VectorService instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
