"""
GraphQL Schema Assembly - 2026 Best Practices (H2.1 Hardening)

Assembles the complete GraphQL schema with:
1. Query and Mutation types
2. Custom scalars
3. Extensions (query complexity, depth limiting, tracing)
4. FastAPI router integration
5. DoS protection via complexity analysis
"""

from typing import Optional, Any, Dict, Callable
import logging
import time

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.extensions import QueryDepthLimiter
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.schema.config import StrawberryConfig
from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    OperationDefinitionNode,
    FieldNode,
    InlineFragmentNode,
    FragmentSpreadNode,
)

from app.graphql.queries import Query
from app.graphql.mutations import Mutation
from app.graphql.context import get_graphql_context
from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Extensions (H2.1)
# =============================================================================

class QueryComplexityLimiter(SchemaExtension):
    """
    Extension to limit query complexity (H2.1 Production Implementation).

    Prevents expensive queries from consuming too many resources through:
    1. Field complexity scoring (connections cost more)
    2. Depth-based multipliers
    3. List size estimation
    4. Configurable complexity limits

    Complexity Scoring:
    - Scalar fields: 1 point
    - Object fields: 2 points
    - List fields: 5 points * estimated_size
    - Connection fields: 10 points
    - Nested multiplier: depth * 1.5
    """

    # Field complexity costs
    FIELD_COSTS: Dict[str, int] = {
        # High-cost connection fields
        "tools": 10,
        "creditTransactions": 10,
        "myToolRuns": 10,
        "myTools": 10,
        # Medium-cost object fields
        "tool": 5,
        "user": 5,
        "toolAnalytics": 5,
        "systemHealth": 3,
        # Low-cost scalar fields
        "me": 2,
        "creditBalance": 2,
        # Default for unlisted fields
    }

    DEFAULT_FIELD_COST = 1
    LIST_MULTIPLIER = 5
    DEPTH_MULTIPLIER = 1.5

    def __init__(
        self,
        max_complexity: int = 500,
        *,
        execution_context: Optional[Any] = None,
    ):
        """
        Initialize complexity limiter.

        Args:
            max_complexity: Maximum allowed query complexity (default: 500)
        """
        self.max_complexity = max_complexity
        super().__init__(execution_context=execution_context)

    def on_operation(self) -> None:
        """Calculate and validate query complexity before execution."""
        execution_context = self.execution_context

        if execution_context is None:
            return

        try:
            # Get the operation definition
            operation = execution_context.graphql_document
            if operation is None:
                return

            total_complexity = 0

            for definition in operation.definitions:
                if isinstance(definition, OperationDefinitionNode):
                    complexity = self._calculate_complexity(
                        definition.selection_set.selections,
                        depth=1,
                    )
                    total_complexity += complexity

            # Reject if over limit
            if total_complexity > self.max_complexity:
                logger.warning(
                    f"GraphQL query rejected: complexity {total_complexity} "
                    f"exceeds limit {self.max_complexity}"
                )
                raise ValueError(
                    f"Query complexity ({total_complexity}) exceeds maximum allowed ({self.max_complexity}). "
                    "Please reduce the number of fields or use pagination."
                )

            logger.debug(f"GraphQL query complexity: {total_complexity}/{self.max_complexity}")

        except ValueError:
            raise
        except Exception as e:
            # Don't block queries on complexity calculation errors
            logger.warning(f"Failed to calculate query complexity: {e}")

    def _calculate_complexity(
        self,
        selections: Any,
        depth: int,
    ) -> int:
        """Recursively calculate complexity for selection set."""
        complexity = 0

        for selection in selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value

                # Get base cost for this field
                base_cost = self.FIELD_COSTS.get(field_name, self.DEFAULT_FIELD_COST)

                # Apply depth multiplier
                field_complexity = int(base_cost * (self.DEPTH_MULTIPLIER ** (depth - 1)))

                # Check for pagination arguments (first, last, limit)
                list_size = 20  # Default assumed size
                if selection.arguments:
                    for arg in selection.arguments:
                        if arg.name.value in ("first", "last", "limit"):
                            try:
                                list_size = int(arg.value.value)  # type: ignore
                            except (AttributeError, ValueError):
                                pass

                # Apply list multiplier for connection/list fields
                if field_name in ("tools", "creditTransactions", "myToolRuns", "myTools", "edges"):
                    field_complexity *= min(list_size, 100)  # Cap at 100

                complexity += field_complexity

                # Recurse into nested selections
                if selection.selection_set:
                    complexity += self._calculate_complexity(
                        selection.selection_set.selections,
                        depth=depth + 1,
                    )

            elif isinstance(selection, InlineFragmentNode):
                if selection.selection_set:
                    complexity += self._calculate_complexity(
                        selection.selection_set.selections,
                        depth=depth,
                    )

            elif isinstance(selection, FragmentSpreadNode):
                # Fragment spreads add complexity but we can't fully analyze them here
                complexity += 5

        return complexity


class RequestLogger(SchemaExtension):
    """
    Extension to log GraphQL requests with timing.

    Logs query info for monitoring, debugging, and performance tracking.
    """

    def __init__(self, *, execution_context: Optional[Any] = None):
        super().__init__(execution_context=execution_context)
        self._start_time: Optional[float] = None

    def on_operation(self) -> None:
        """Log operation start."""
        self._start_time = time.time()

        execution_context = self.execution_context
        if execution_context and execution_context.graphql_document:
            for definition in execution_context.graphql_document.definitions:
                if isinstance(definition, OperationDefinitionNode):
                    op_name = definition.name.value if definition.name else "anonymous"
                    op_type = definition.operation.value
                    logger.debug(f"GraphQL {op_type} started: {op_name}")
                    break

    def on_executing_end(self) -> None:
        """Log execution completion with timing."""
        if self._start_time:
            duration_ms = (time.time() - self._start_time) * 1000
            logger.debug(f"GraphQL execution completed in {duration_ms:.2f}ms")


# =============================================================================
# Schema Configuration (H2.1 Hardening)
# =============================================================================

# Default complexity limits
MAX_QUERY_DEPTH = 10  # Prevent deeply nested queries
MAX_QUERY_COMPLEXITY = 500  # Prevent expensive queries

# Create the Strawberry schema with security extensions
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(
        auto_camel_case=True,  # Convert snake_case to camelCase
    ),
    extensions=[
        # H2.1: Limit query depth to prevent deeply nested queries
        QueryDepthLimiter(max_depth=MAX_QUERY_DEPTH),
        # H2.1: Limit query complexity to prevent DoS attacks
        QueryComplexityLimiter(max_complexity=MAX_QUERY_COMPLEXITY),
        # Request logging for monitoring
        RequestLogger,
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
    graphql_ide="graphiql" if settings.ENVIRONMENT.lower() in {"development", "dev", "local"} else None,
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
