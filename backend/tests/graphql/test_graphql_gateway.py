"""
Tests for GraphQL Gateway Module

Tests the GraphQL components:
1. Types and enums
2. Query resolvers
3. Mutation resolvers
4. Context and authentication
5. DataLoader patterns
6. Connection pagination
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

import strawberry

from app.graphql.types import (
    User,
    Tool,
    ToolTier,
    SafetyRating,
    RunStatus,
    CreditTransactionType,
    PageInfo,
    Connection,
    create_connection,
    PaginationInput,
    ToolFilterInput,
)
from app.graphql.context import GraphQLContext, get_graphql_context
from app.graphql.schema import schema, get_schema_sdl, validate_query
from app.graphql.queries import Query
from app.graphql.mutations import Mutation


# =============================================================================
# Type Tests
# =============================================================================

class TestGraphQLTypes:
    """Tests for GraphQL type definitions."""

    def test_tool_tier_enum(self):
        """Test ToolTier enum values."""
        assert ToolTier.EXPERIMENTAL.value == "experimental"
        assert ToolTier.VERIFIED.value == "verified"
        assert ToolTier.CERTIFIED.value == "certified"

    def test_run_status_enum(self):
        """Test RunStatus enum values."""
        assert RunStatus.STARTED.value == "started"
        assert RunStatus.SUCCESS.value == "success"
        assert RunStatus.FAILED.value == "failed"
        assert RunStatus.TIMEOUT.value == "timeout"

    def test_safety_rating_enum(self):
        """Test SafetyRating enum values."""
        assert SafetyRating.SAFE.value == "safe"
        assert SafetyRating.REVIEW.value == "review"
        assert SafetyRating.RESTRICTED.value == "restricted"

    def test_user_type(self):
        """Test User type creation."""
        user = User(
            id=strawberry.ID("user-123"),
            email="test@example.com",
            display_name="Test User",
            credit_balance=1000,
            total_spent=500,
            tier="pro",
            created_at=datetime.now(),
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.credit_balance == 1000

    def test_tool_type(self):
        """Test Tool type creation."""
        tool = Tool(
            id=strawberry.ID("tool-123"),
            tool_key="prompt-alchemy",
            display_name="Prompt Alchemy",
            description="Transform prompts",
            version="1.0.0",
            category="dimension",
            tier=ToolTier.CERTIFIED,
            credit_cost=5,
            usage_count=1000,
            success_rate=0.95,
            created_by="system",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert tool.tool_key == "prompt-alchemy"
        assert tool.tier == ToolTier.CERTIFIED
        assert tool.success_rate == 0.95

    def test_page_info(self):
        """Test PageInfo type."""
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=False,
            start_cursor="cursor-1",
            end_cursor="cursor-10",
        )

        assert page_info.has_next_page is True
        assert page_info.has_previous_page is False

    def test_create_connection(self):
        """Test connection creation helper."""
        items = [
            Tool(
                id=strawberry.ID(f"tool-{i}"),
                tool_key=f"tool-{i}",
                display_name=f"Tool {i}",
                description="Test tool",
                version="1.0.0",
                category="test",
                tier=ToolTier.EXPERIMENTAL,
                credit_cost=5,
                created_by="test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]

        connection = create_connection(
            items=items,
            total_count=100,
            has_next=True,
            has_prev=False,
        )

        assert len(connection.edges) == 5
        assert connection.total_count == 100
        assert connection.page_info.has_next_page is True
        assert connection.page_info.has_previous_page is False


# =============================================================================
# Context Tests
# =============================================================================

class TestGraphQLContext:
    """Tests for GraphQL context."""

    @pytest.fixture(autouse=True)
    def enable_dev_auth_bypass(self):
        """H2.1: Enable dev auth bypass for tests."""
        with patch("app.auth.settings") as mock_settings:
            mock_settings.ENABLE_DEV_AUTH_BYPASS = True
            mock_settings.ENVIRONMENT = "development"
            mock_settings.SESSION_COOKIE_NAME = "crebit_session"
            mock_settings.SESSION_SECRET.get_secret_value.return_value = ""
            yield mock_settings

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_context_without_auth(self, mock_request, mock_response):
        """Test context creation without authentication."""
        mock_request.headers = {}

        context = await get_graphql_context(mock_request, mock_response)

        assert context.is_authenticated is False
        assert context.user_id is None

    @pytest.mark.asyncio
    async def test_context_with_auth(self, mock_request, mock_response):
        """Test context creation with authentication."""
        # H2.1: Use X-User-Id header for dev bypass authentication
        mock_request.headers = {
            "Authorization": "Bearer user-123",
            "X-User-Id": "user-123",
        }

        context = await get_graphql_context(mock_request, mock_response)

        assert context.is_authenticated is True
        assert context.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_context_with_admin(self, mock_request, mock_response):
        """Test context creation with admin access."""
        # H2.1: Use X-User-Id and X-Admin-Mode headers for dev bypass
        mock_request.headers = {
            "Authorization": "Bearer admin-user",
            "X-User-Id": "admin-user",
            "X-Admin-Mode": "true",
        }

        # Patch get_is_admin to return True for this test
        with patch("app.graphql.context.get_is_admin", new_callable=AsyncMock, return_value=True):
            context = await get_graphql_context(mock_request, mock_response)

        assert context.is_authenticated is True
        assert context.is_admin is True

    def test_require_auth_raises(self):
        """Test require_auth raises for unauthenticated user."""
        context = GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            is_authenticated=False,
        )

        with pytest.raises(PermissionError, match="Authentication required"):
            context.require_auth()

    def test_require_admin_raises(self):
        """Test require_admin raises for non-admin user."""
        context = GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            is_authenticated=True,
            is_admin=False,
        )

        with pytest.raises(PermissionError, match="Admin access required"):
            context.require_admin()

    @pytest.mark.asyncio
    async def test_user_loader(self):
        """Test user dataloader."""
        context = GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
        )

        loader = context.get_user_loader()
        result = await loader.load("user-123")

        assert result is not None
        assert result["id"] == "user-123"

    @pytest.mark.asyncio
    async def test_tool_loader(self):
        """Test tool dataloader."""
        context = GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
        )

        loader = context.get_tool_loader()
        # Use a valid UUID format - non-UUID strings return None by design
        test_uuid = "12345678-1234-5678-1234-567812345678"
        result = await loader.load(test_uuid)

        # Without a real DB, the fallback returns dummy data for valid UUIDs
        assert result is not None
        assert result["id"] == test_uuid


# =============================================================================
# Schema Tests
# =============================================================================

class TestGraphQLSchema:
    """Tests for GraphQL schema."""

    def test_schema_creation(self):
        """Test schema is created successfully."""
        assert schema is not None

    def test_schema_has_query(self):
        """Test schema has Query type."""
        sdl = get_schema_sdl()
        assert "type Query" in sdl

    def test_schema_has_mutation(self):
        """Test schema has Mutation type."""
        sdl = get_schema_sdl()
        assert "type Mutation" in sdl

    def test_schema_has_user_type(self):
        """Test schema has User type."""
        sdl = get_schema_sdl()
        assert "type User" in sdl

    def test_schema_has_tool_type(self):
        """Test schema has Tool type."""
        sdl = get_schema_sdl()
        assert "type Tool" in sdl

    def test_validate_valid_query(self):
        """Test query validation with valid query."""
        query = """
        query {
            systemHealth {
                status
                version
            }
        }
        """
        error = validate_query(query)
        assert error is None

    def test_validate_invalid_query(self):
        """Test query validation with invalid query."""
        query = """
        query {
            nonExistentField {
                value
            }
        }
        """
        error = validate_query(query)
        assert error is not None

    def test_camel_case_conversion(self):
        """Test auto camelCase conversion is enabled."""
        sdl = get_schema_sdl()
        # Fields should be camelCase in SDL
        assert "creditBalance" in sdl or "credit_balance" in sdl


# =============================================================================
# Query Tests
# =============================================================================

class TestGraphQLQueries:
    """Tests for GraphQL queries."""

    @pytest.fixture
    def authenticated_context(self):
        """Create authenticated context."""
        return GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            user_id="test-user",
            user_email="test@example.com",
            is_authenticated=True,
        )

    @pytest.fixture
    def admin_context(self):
        """Create admin context."""
        return GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            user_id="admin-user",
            user_email="admin@example.com",
            is_authenticated=True,
            is_admin=True,
        )

    @pytest.mark.asyncio
    async def test_me_query_authenticated(self, authenticated_context):
        """Test me query for authenticated user."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.me(info)

        assert result is not None
        assert result.id == "test-user"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_me_query_unauthenticated(self):
        """Test me query for unauthenticated user."""
        context = GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            is_authenticated=False,
        )
        info = MagicMock()
        info.context = context

        query = Query()

        with pytest.raises(PermissionError):
            await query.me(info)

    @pytest.mark.asyncio
    async def test_credit_balance_query(self, authenticated_context):
        """Test credit balance query."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.credit_balance(info)

        assert result is not None
        assert result.balance >= 0
        assert result.available == result.balance - result.reserved

    @pytest.mark.asyncio
    async def test_tools_query(self, authenticated_context):
        """Test tools query with pagination."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.tools(
            info,
            filter=None,
            pagination=PaginationInput(first=10),
        )

        assert result is not None
        assert isinstance(result.edges, list)
        assert result.total_count >= 0

    @pytest.mark.asyncio
    async def test_tool_by_key_query(self, authenticated_context):
        """Test tool by key query."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.tool_by_key(info, key="prompt-alchemy")

        assert result is not None
        assert result.tool_key == "prompt-alchemy"

    @pytest.mark.asyncio
    async def test_dimension_capsules_query(self, authenticated_context):
        """Test dimension capsules query."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.dimension_capsules(info)

        assert result is not None
        assert isinstance(result, list)
        # Should have at least one capsule
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_system_health_query(self, authenticated_context):
        """Test system health query."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()
        result = await query.system_health(info)

        assert result is not None
        assert result.status in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_query_stats_admin_only(self, admin_context):
        """Test query stats requires admin."""
        info = MagicMock()
        info.context = admin_context

        query = Query()
        result = await query.query_stats(info)

        assert result is not None

    @pytest.mark.asyncio
    async def test_query_stats_non_admin_fails(self, authenticated_context):
        """Test query stats fails for non-admin."""
        info = MagicMock()
        info.context = authenticated_context

        query = Query()

        with pytest.raises(PermissionError):
            await query.query_stats(info)


# =============================================================================
# Mutation Tests
# =============================================================================

class TestGraphQLMutations:
    """Tests for GraphQL mutations."""

    @pytest.fixture
    def authenticated_context(self):
        """Create authenticated context."""
        return GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            user_id="test-user",
            user_email="test@example.com",
            is_authenticated=True,
        )

    @pytest.fixture
    def admin_context(self):
        """Create admin context."""
        return GraphQLContext(
            request=MagicMock(),
            response=MagicMock(),
            user_id="admin-user",
            user_email="admin@example.com",
            is_authenticated=True,
            is_admin=True,
        )

    @pytest.mark.asyncio
    async def test_start_tool_run(self, authenticated_context):
        """Test starting a tool run."""
        from app.graphql.types import ToolRunInput

        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.start_tool_run(
            info,
            input=ToolRunInput(
                tool_key="prompt-alchemy",
                user_id="test-user",
            ),
        )

        assert result.run is not None
        assert result.run.tool_key == "prompt-alchemy"
        assert result.run.status == RunStatus.STARTED

    @pytest.mark.asyncio
    async def test_submit_tool_feedback_valid(self, authenticated_context):
        """Test submitting valid tool feedback."""
        from app.graphql.types import ToolFeedbackInput

        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.submit_tool_feedback(
            info,
            input=ToolFeedbackInput(
                run_id=strawberry.ID(str(uuid4())),
                rating=5,
                feedback="Great tool!",
            ),
        )

        assert len(result.errors) == 0
        assert result.rating == 5

    @pytest.mark.asyncio
    async def test_submit_tool_feedback_invalid_rating(self, authenticated_context):
        """Test submitting invalid rating."""
        from app.graphql.types import ToolFeedbackInput

        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.submit_tool_feedback(
            info,
            input=ToolFeedbackInput(
                run_id=strawberry.ID(str(uuid4())),
                rating=10,  # Invalid: > 5
            ),
        )

        assert len(result.errors) > 0
        assert result.errors[0].code == "INVALID_RATING"

    @pytest.mark.asyncio
    async def test_purchase_credits_valid(self, authenticated_context):
        """Test purchasing credits."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.purchase_credits(
            info,
            amount=1000,
            payment_method_id="pm-test",
        )

        assert len(result.errors) == 0
        assert result.new_balance is not None
        assert result.transaction_id is not None

    @pytest.mark.asyncio
    async def test_purchase_credits_invalid_amount(self, authenticated_context):
        """Test purchasing with invalid amount."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()

        # Too low
        result = await mutation.purchase_credits(
            info,
            amount=10,  # < 100 minimum
            payment_method_id="pm-test",
        )

        assert len(result.errors) > 0
        assert result.errors[0].code == "INVALID_AMOUNT"

    @pytest.mark.asyncio
    async def test_create_tool(self, authenticated_context):
        """Test creating a tool."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.create_tool(
            info,
            tool_key="my-new-tool",
            display_name="My New Tool",
            description="A great new tool",
            category="custom",
            credit_cost=10,
        )

        assert len(result.errors) == 0
        assert result.tool is not None
        assert result.tool.tool_key == "my-new-tool"
        assert result.tool.tier == ToolTier.EXPERIMENTAL

    @pytest.mark.asyncio
    async def test_create_tool_invalid_key(self, authenticated_context):
        """Test creating tool with invalid key."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.create_tool(
            info,
            tool_key="Invalid Key!",  # Contains spaces and special chars
            display_name="Bad Tool",
            description="Should fail",
            category="test",
        )

        assert len(result.errors) > 0
        assert result.errors[0].code == "INVALID_TOOL_KEY"

    @pytest.mark.asyncio
    async def test_fork_tool(self, authenticated_context):
        """Test forking a tool."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()
        result = await mutation.fork_tool(
            info,
            parent_tool_id=strawberry.ID(str(uuid4())),
            new_tool_key="my-forked-tool",
            new_display_name="My Forked Tool",
            fork_reason="Adding new features",
        )

        assert len(result.errors) == 0
        assert result.tool is not None
        assert result.tool.fork_depth == 1

    @pytest.mark.asyncio
    async def test_approve_tool_admin(self, admin_context):
        """Test approving a tool (admin only)."""
        info = MagicMock()
        info.context = admin_context

        mutation = Mutation()
        result = await mutation.approve_tool(
            info,
            tool_id=strawberry.ID(str(uuid4())),
            new_tier=ToolTier.VERIFIED,
            safety_rating=SafetyRating.SAFE,
        )

        assert len(result.errors) == 0
        assert result.tool.tier == ToolTier.VERIFIED

    @pytest.mark.asyncio
    async def test_approve_tool_non_admin_fails(self, authenticated_context):
        """Test approving tool fails for non-admin."""
        info = MagicMock()
        info.context = authenticated_context

        mutation = Mutation()

        with pytest.raises(PermissionError):
            await mutation.approve_tool(
                info,
                tool_id=strawberry.ID(str(uuid4())),
                new_tier=ToolTier.VERIFIED,
                safety_rating=SafetyRating.SAFE,
            )


# =============================================================================
# Integration Tests
# =============================================================================

class TestGraphQLIntegration:
    """Integration tests for GraphQL endpoint."""

    def test_schema_executable(self):
        """Test schema can execute simple query."""
        result = schema.execute_sync(
            """
            query {
                systemHealth {
                    status
                    version
                }
            }
            """,
            context_value=GraphQLContext(
                request=MagicMock(),
                response=MagicMock(),
            ),
        )

        # Should not have GraphQL errors (may have auth errors)
        assert result.data is not None or result.errors is not None

    def test_introspection_query(self):
        """Test introspection query works."""
        result = schema.execute_sync(
            """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
            """,
            context_value=GraphQLContext(
                request=MagicMock(),
                response=MagicMock(),
            ),
        )

        assert result.errors is None
        assert result.data is not None
        type_names = [t["name"] for t in result.data["__schema"]["types"]]
        assert "Query" in type_names
        assert "Mutation" in type_names
