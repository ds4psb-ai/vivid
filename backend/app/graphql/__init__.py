"""
GraphQL Gateway Module - 2026 Best Practices (H2.1 Hardening)

Provides a GraphQL API layer with:
1. Type-safe schema using Strawberry
2. DataLoader pattern for N+1 prevention (production-grade)
3. Context-based authentication
4. Connection-based pagination
5. Query complexity analysis (DoS protection)
6. Query depth limiting

Usage:
    from app.graphql import graphql_router
    app.include_router(graphql_router, prefix="/graphql")
"""

from app.graphql.schema import schema, graphql_router
from app.graphql.dataloaders import (
    DataLoaderRegistry,
    TypedDataLoader,
    IPCatalogDataLoader,
    UserDataLoader,
    UserCreditsDataLoader,
    ToolManifestDataLoader,
    ToolByKeyDataLoader,
    ToolAnalyticsDataLoader,
)

__all__ = [
    # Schema
    "schema",
    "graphql_router",
    # DataLoaders (H2.1)
    "DataLoaderRegistry",
    "TypedDataLoader",
    "IPCatalogDataLoader",
    "UserDataLoader",
    "UserCreditsDataLoader",
    "ToolManifestDataLoader",
    "ToolByKeyDataLoader",
    "ToolAnalyticsDataLoader",
]
