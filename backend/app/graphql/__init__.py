"""
GraphQL Gateway Module - 2026 Best Practices

Provides a GraphQL API layer with:
1. Type-safe schema using Strawberry
2. DataLoader pattern for N+1 prevention
3. Context-based authentication
4. Connection-based pagination
5. Query complexity analysis

Usage:
    from app.graphql import graphql_router
    app.include_router(graphql_router, prefix="/graphql")
"""

from app.graphql.schema import schema, graphql_router

__all__ = [
    "schema",
    "graphql_router",
]
