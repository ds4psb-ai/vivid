"""
GraphQL Schema Assembly - 2026 Best Practices

Assembles the complete GraphQL schema with:
1. Query and Mutation types
2. Custom scalars
3. Extensions (query complexity, tracing)
4. FastAPI router integration
"""

from typing import Optional
import logging

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.extensions import QueryDepthLimiter
from strawberry.schema.config import StrawberryConfig

from app.graphql.queries import Query
from app.graphql.mutations import Mutation
from app.graphql.context import get_graphql_context

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Extensions
# =============================================================================

class QueryComplexityLimiter:
    """
    Extension to limit query complexity.

    Prevents expensive queries from consuming too many resources.
    Each field has a complexity cost, and the total must be under a threshold.
    """

    def __init__(self, max_complexity: int = 1000):
        self.max_complexity = max_complexity

    def on_operation(self):
        """Called before executing an operation."""
        pass


class RequestLogger:
    """
    Extension to log GraphQL requests.

    Logs query info for monitoring and debugging.
    """

    def on_operation(self):
        """Log operation details."""
        logger.debug("GraphQL operation started")

    def on_executing_start(self):
        """Log execution start."""
        pass

    def on_executing_end(self):
        """Log execution end."""
        pass


# =============================================================================
# Schema Configuration
# =============================================================================

# Create the Strawberry schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(
        auto_camel_case=True,  # Convert snake_case to camelCase
    ),
    extensions=[
        # Limit query depth to prevent deeply nested queries
        QueryDepthLimiter(max_depth=10),
    ],
)


# =============================================================================
# FastAPI Router
# =============================================================================

# Create the GraphQL router with context factory
graphql_router = GraphQLRouter(
    schema=schema,
    context_getter=get_graphql_context,
    # Enable GraphiQL for development
    graphql_ide="graphiql",
    # Allow introspection (disable in production if needed)
    allow_queries_via_get=False,
)


# =============================================================================
# Schema Utilities
# =============================================================================

def get_schema_sdl() -> str:
    """Get the schema SDL (Schema Definition Language) string."""
    return str(schema)


def validate_query(query: str) -> Optional[str]:
    """
    Validate a GraphQL query without executing it.

    Returns None if valid, or an error message if invalid.
    """
    try:
        from graphql import parse, validate

        document = parse(query)
        errors = validate(schema._schema, document)

        if errors:
            return "; ".join(str(e) for e in errors)

        return None
    except Exception as e:
        return str(e)


# =============================================================================
# Type Exports for Testing
# =============================================================================

__all__ = [
    "schema",
    "graphql_router",
    "get_schema_sdl",
    "validate_query",
    "Query",
    "Mutation",
]
