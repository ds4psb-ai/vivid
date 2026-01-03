"""
Embedder Service - Text to Vector conversion using SentenceTransformers

Uses all-MiniLM-L6-v2 for fast, lightweight embeddings (384 dimensions).
For higher quality, consider switching to all-mpnet-base-v2 (768 dimensions).
"""

import logging
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

# Lazy loading to avoid slow startup
_model = None


def _get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock embeddings")
            _model = "mock"
    return _model


class Embedder:
    """
    Text embedding service using SentenceTransformers.
    
    Example:
        embedder = Embedder()
        vector = embedder.embed("image resizing tool")
        # Returns: [0.123, -0.456, ...]  (384 dimensions)
    """
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSIONS = 384
    
    def __init__(self):
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            self._model = _get_model()
        return self._model
    
    def embed(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats (384 dimensions)
        """
        if not text or not text.strip():
            return [0.0] * self.DIMENSIONS
        
        model = self.model
        if model == "mock":
            # Mock embedding for testing without sentence-transformers
            import hashlib
            h = hashlib.md5(text.encode()).hexdigest()
            return [int(h[i:i+2], 16) / 255.0 - 0.5 for i in range(0, 64, 2)] + [0.0] * (self.DIMENSIONS - 32)
        
        try:
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * self.DIMENSIONS
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch (more efficient).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        model = self.model
        if model == "mock":
            return [self.embed(t) for t in texts]
        
        try:
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return [[0.0] * self.DIMENSIONS for _ in texts]


# Singleton instance
@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Get the singleton Embedder instance."""
    return Embedder()
