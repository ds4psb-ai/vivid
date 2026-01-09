"""Context Library System.

Enables users to inject external knowledge (Wiki, articles, research)
that the AI lacks context on, following the Expert Workflow pattern.

Usage:
    from app.rag.context_library import (
        ContextLibrary,
        ContextDocument,
        get_context_library,
    )

    # Add context document
    library = get_context_library()
    doc = ContextDocument(
        title="흑백요리사 나무위키",
        content="흑백요리사는 넷플릭스 요리 서바이벌...",
        source_type="wiki",
        tags=["요리", "서바이벌", "넷플릭스"],
    )
    library.add_document(session_id, doc)

    # Retrieve context for prompt injection
    context = library.get_context_for_query(
        session_id=session_id,
        query="흑백요리사 애니메이션 오프닝",
        max_documents=3,
    )
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ContextDocument:
    """External context document for RAG injection.
    
    Represents knowledge the AI lacks (Wiki articles, columns, research)
    that users can inject to improve generation quality.
    """
    title: str
    content: str
    source_type: Literal["wiki", "article", "user_research", "style_guide", "reference_song", "character_info"]
    tags: List[str] = field(default_factory=list)
    id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            # Generate deterministic ID from content hash
            content_hash = hashlib.md5(
                f"{self.title}:{self.content[:500]}".encode()
            ).hexdigest()[:12]
            self.id = f"ctx_{content_hash}"
    
    def to_prompt_block(self) -> str:
        """Format document for prompt injection."""
        return f"""### {self.title} ({self.source_type})
{self.content}
---"""


@dataclass
class ContextRetrievalResult:
    """Result of context retrieval for a query."""
    documents: List[ContextDocument]
    total_matched: int
    query_time_ms: int
    formatted_context: str
    

# ============================================================================
# Context Library
# ============================================================================

class ContextLibrary:
    """Per-session context document library.
    
    Manages external knowledge documents that users inject to improve
    AI generation quality. Documents are scoped to sessions and can be
    retrieved based on query relevance.
    
    Pattern inspired by Expert Workflow:
    1. User identifies AI knowledge gap (e.g., 흑백요리사 context)
    2. User pastes Wiki/article content
    3. System indexes and stores document
    4. Document is injected into relevant prompts
    """
    
    def __init__(self):
        # session_id -> List[ContextDocument]
        self._sessions: Dict[str, List[ContextDocument]] = defaultdict(list)
        # session_id -> last_access_time (for cleanup)
        self._session_timestamps: Dict[str, float] = {}
        # TTL for session data (2 hours)
        self._session_ttl_seconds = 7200
    
    def add_document(
        self,
        session_id: str,
        document: ContextDocument,
    ) -> str:
        """Add a context document to a session.
        
        Args:
            session_id: User session identifier
            document: ContextDocument to add
            
        Returns:
            Document ID
        """
        self._cleanup_expired_sessions()
        self._sessions[session_id].append(document)
        self._session_timestamps[session_id] = time.time()
        
        logger.info(
            f"[ContextLibrary] Added document '{document.title}' "
            f"to session {session_id[:8]}... (type={document.source_type})"
        )
        
        return document.id
    
    def get_documents(
        self,
        session_id: str,
        source_type: Optional[str] = None,
    ) -> List[ContextDocument]:
        """Get all documents for a session.
        
        Args:
            session_id: User session identifier
            source_type: Optional filter by source type
            
        Returns:
            List of documents
        """
        self._session_timestamps[session_id] = time.time()
        docs = self._sessions.get(session_id, [])
        
        if source_type:
            docs = [d for d in docs if d.source_type == source_type]
        
        return docs
    
    def get_context_for_query(
        self,
        session_id: str,
        query: str,
        max_documents: int = 3,
        source_types: Optional[List[str]] = None,
    ) -> ContextRetrievalResult:
        """Retrieve relevant context documents for a query.
        
        Uses simple keyword matching for now. Can be upgraded to
        vector similarity search in the future.
        
        Args:
            session_id: User session identifier
            query: Search query
            max_documents: Maximum documents to return
            source_types: Optional filter by source types
            
        Returns:
            ContextRetrievalResult with matched documents
        """
        start_time = time.monotonic()
        
        docs = self.get_documents(session_id)
        
        if source_types:
            docs = [d for d in docs if d.source_type in source_types]
        
        if not docs:
            return ContextRetrievalResult(
                documents=[],
                total_matched=0,
                query_time_ms=0,
                formatted_context="",
            )
        
        # Score documents by keyword overlap
        query_tokens = set(query.lower().split())
        scored_docs = []
        
        for doc in docs:
            # Score based on title + tags + content overlap
            doc_text = f"{doc.title} {' '.join(doc.tags)} {doc.content[:500]}".lower()
            doc_tokens = set(doc_text.split())
            
            overlap = len(query_tokens & doc_tokens)
            if overlap > 0 or not query_tokens:
                scored_docs.append((overlap, doc))
        
        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N
        matched_docs = [doc for _, doc in scored_docs[:max_documents]]
        
        # Format for prompt injection
        formatted_blocks = []
        for doc in matched_docs:
            formatted_blocks.append(doc.to_prompt_block())
        
        formatted_context = ""
        if formatted_blocks:
            formatted_context = f"""## 📚 Injected Context (User-Provided Knowledge)

The following context was provided by the user to help you understand the topic better:

{chr(10).join(formatted_blocks)}

Use this context to inform your response. Do not hallucinate beyond this information.
"""
        
        query_time_ms = int((time.monotonic() - start_time) * 1000)
        
        logger.info(
            f"[ContextLibrary] Retrieved {len(matched_docs)}/{len(docs)} docs "
            f"for query '{query[:30]}...' in {query_time_ms}ms"
        )
        
        return ContextRetrievalResult(
            documents=matched_docs,
            total_matched=len(matched_docs),
            query_time_ms=query_time_ms,
            formatted_context=formatted_context,
        )
    
    def remove_document(
        self,
        session_id: str,
        document_id: str,
    ) -> bool:
        """Remove a document from a session.
        
        Args:
            session_id: User session identifier
            document_id: Document ID to remove
            
        Returns:
            True if removed, False if not found
        """
        docs = self._sessions.get(session_id, [])
        for i, doc in enumerate(docs):
            if doc.id == document_id:
                docs.pop(i)
                logger.info(f"[ContextLibrary] Removed document {document_id}")
                return True
        return False
    
    def clear_session(self, session_id: str) -> int:
        """Clear all documents for a session.
        
        Args:
            session_id: User session identifier
            
        Returns:
            Number of documents removed
        """
        count = len(self._sessions.get(session_id, []))
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._session_timestamps:
            del self._session_timestamps[session_id]
        
        logger.info(f"[ContextLibrary] Cleared session {session_id[:8]}... ({count} docs)")
        return count
    
    def _cleanup_expired_sessions(self):
        """Remove expired session data."""
        current_time = time.time()
        expired = [
            sid for sid, ts in self._session_timestamps.items()
            if current_time - ts > self._session_ttl_seconds
        ]
        for sid in expired:
            self.clear_session(sid)
        
        if expired:
            logger.debug(f"[ContextLibrary] Cleaned up {len(expired)} expired sessions")


# ============================================================================
# Singleton & Factory
# ============================================================================

_context_library: Optional[ContextLibrary] = None


def get_context_library() -> ContextLibrary:
    """Get the global context library instance."""
    global _context_library
    if _context_library is None:
        _context_library = ContextLibrary()
    return _context_library


def reset_context_library() -> None:
    """Reset the context library (for testing)."""
    global _context_library
    _context_library = None


# ============================================================================
# Integration Helpers
# ============================================================================

def inject_context_into_prompt(
    session_id: str,
    query: str,
    base_prompt: str,
    max_documents: int = 3,
    position: Literal["prepend", "append"] = "prepend",
) -> str:
    """Convenience function to inject context into a prompt.
    
    Args:
        session_id: User session identifier
        query: Search query for context retrieval
        base_prompt: Original prompt
        max_documents: Max context documents to include
        position: Where to inject context
        
    Returns:
        Enhanced prompt with injected context
    """
    library = get_context_library()
    result = library.get_context_for_query(
        session_id=session_id,
        query=query,
        max_documents=max_documents,
    )
    
    if not result.formatted_context:
        return base_prompt
    
    if position == "prepend":
        return f"{result.formatted_context}\n\n{base_prompt}"
    else:
        return f"{base_prompt}\n\n{result.formatted_context}"


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ContextDocument",
    "ContextRetrievalResult",
    "ContextLibrary",
    "get_context_library",
    "reset_context_library",
    "inject_context_into_prompt",
]
