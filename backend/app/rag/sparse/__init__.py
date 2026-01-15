"""Sparse embedding module for Qdrant hybrid search.

Provides sparse vector generation using FastEmbed BM25 model
for Qdrant Native Hybrid Search with server-side IDF.
"""

from app.rag.sparse.fastembed_sparse import SparseEmbedder

__all__ = ["SparseEmbedder"]
