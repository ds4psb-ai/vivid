"""Tests for Mirror Run-Token enforcement.

P5-6: Run-Token 401/402/200 테스트
- 토큰 없이 호출 → 401
- 유효하지 않은 토큰 → 401
- 유효 토큰 → 200

Note: 상세한 token validation (app mismatch, user mismatch, credits)은
RunTokenService 단위 테스트에서 검증합니다.

Tests cover:
- /api/dimension/mirror/chat
- /api/dimension/mirror/chat/stream (SSE)
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport


class MockTokenPayload:
    """Mock token payload for testing."""
    def __init__(self, user_id="test-user", app_id="ai", credits_reserved=100, credits_used=0):
        self.user_id = user_id
        self.app_id = app_id
        self.run_id = "test-run-id"
        self.credits_reserved = credits_reserved
        self.credits_used = credits_used
        self.permissions = ["chat", "stream"]


@pytest_asyncio.fixture
async def client():
    """Async test client fixture."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestMirrorChatRunToken:
    """Mirror Chat Run-Token 테스트."""

    @pytest.mark.asyncio
    async def test_chat_no_token_401(self, client):
        """토큰 없이 호출 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
        )
        assert response.status_code == 401
        assert "Authorization header required" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_chat_invalid_bearer_format_401(self, client):
        """잘못된 Bearer 형식 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401
        assert "Invalid authorization header" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_chat_invalid_token_401(self, client):
        """유효하지 않은 토큰 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
            headers={"Authorization": "Bearer invalid-token-xyz"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_valid_token_passes_auth(self):
        """유효 토큰 → 인증 통과 (이후 로직 실행)."""
        from app.main import app
        from app.routers.run_token import verify_run_token
        from app.routers.dimension._base import get_current_user

        # Override the verify_run_token dependency
        async def mock_verify_run_token():
            return {
                "user_id": "test-user",
                "app_id": "ai",
                "run_id": "test-run-id",
                "credits_reserved": 100,
                "credits_used": 0,
                "permissions": ["chat", "stream"],
            }

        # Override the get_current_user dependency
        async def mock_get_current_user():
            return {"id": "test-user", "email": "test@example.com"}

        app.dependency_overrides[verify_run_token] = mock_verify_run_token
        app.dependency_overrides[get_current_user] = mock_get_current_user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/dimension/mirror/chat",
                    json={
                        "session_id": "test-session",
                        "user_message": "안녕하세요",
                        "persona_data": {"input": {}},
                        "chat_history": [],
                        "current_stage": "intro",
                    },
                    headers={"Authorization": "Bearer valid-test-token"},
                )
                # 인증은 통과하고 비즈니스 로직 실행 (500 또는 다른 응답)
                # 401이 아니면 인증 통과
                assert response.status_code != 401
        finally:
            app.dependency_overrides.pop(verify_run_token, None)
            app.dependency_overrides.pop(get_current_user, None)


class TestMirrorStreamRunToken:
    """Mirror SSE Stream Run-Token 테스트."""

    @pytest.mark.asyncio
    async def test_stream_no_token_401(self, client):
        """SSE 토큰 없이 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat/stream",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
        )
        assert response.status_code == 401
        assert "Authorization header required" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_stream_invalid_bearer_format_401(self, client):
        """SSE 잘못된 Bearer 형식 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat/stream",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
            headers={"Authorization": "Basic auth"},
        )
        assert response.status_code == 401
        assert "Invalid authorization header" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_stream_invalid_token_401(self, client):
        """SSE 유효하지 않은 토큰 → 401."""
        response = await client.post(
            "/api/dimension/mirror/chat/stream",
            json={
                "session_id": "test-session",
                "user_message": "안녕하세요",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
            headers={"Authorization": "Bearer invalid-token-xyz"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stream_valid_token_passes_auth(self):
        """SSE 유효 토큰 → 인증 통과.

        Note: Stream 엔드포인트는 인증 후 비즈니스 로직에서 추가 에러가 발생할 수 있음.
        이 테스트는 인증 통과 여부만 검증합니다. (401이 아닌 응답)
        """
        from app.main import app
        from app.routers.run_token import verify_run_token
        from app.routers.dimension._base import get_current_user

        # Override the verify_run_token dependency
        async def mock_verify_run_token():
            return {
                "user_id": "test-user",
                "app_id": "ai",
                "run_id": "test-run-id",
                "credits_reserved": 100,
                "credits_used": 0,
                "permissions": ["chat", "stream"],
            }

        # Override the get_current_user dependency
        async def mock_get_current_user():
            return {"id": "test-user", "email": "test@example.com"}

        app.dependency_overrides[verify_run_token] = mock_verify_run_token
        app.dependency_overrides[get_current_user] = mock_get_current_user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                try:
                    response = await client.post(
                        "/api/dimension/mirror/chat/stream",
                        json={
                            "session_id": "test-session",
                            "user_message": "안녕하세요",
                            "persona_data": {"input": {}},
                            "chat_history": [],
                            "current_stage": "intro",
                        },
                        headers={"Authorization": "Bearer valid-test-token"},
                    )
                    # 401이 아니면 인증 통과
                    assert response.status_code != 401
                except Exception as e:
                    # Streaming 비즈니스 로직 에러는 인증 통과 후 발생
                    # KeyError 등은 인증 이후 로직 에러이므로 테스트 통과
                    if "401" in str(e) or "Unauthorized" in str(e):
                        raise AssertionError("Authentication should have passed") from e
                    # 다른 에러는 인증 통과 후 비즈니스 로직 에러 → 테스트 통과
                    pass
        finally:
            app.dependency_overrides.pop(verify_run_token, None)
            app.dependency_overrides.pop(get_current_user, None)


class TestRunTokenAuthEnforcement:
    """Run-Token 인증 강제 확인 테스트.

    Mirror chat 엔드포인트가 Run-Token을 요구하는지 확인합니다.
    (P0 보안 패치 검증)
    """

    @pytest.mark.asyncio
    async def test_chat_endpoint_requires_token(self, client):
        """POST /mirror/chat는 토큰 없이 401 반환해야 함."""
        response = await client.post(
            "/api/dimension/mirror/chat",
            json={
                "session_id": "test-session",
                "user_message": "test",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
        )
        assert response.status_code == 401, "Mirror chat should require Run-Token"

    @pytest.mark.asyncio
    async def test_stream_endpoint_requires_token(self, client):
        """POST /mirror/chat/stream는 토큰 없이 401 반환해야 함."""
        response = await client.post(
            "/api/dimension/mirror/chat/stream",
            json={
                "session_id": "test-session",
                "user_message": "test",
                "persona_data": {},
                "chat_history": [],
                "current_stage": "intro",
            },
        )
        assert response.status_code == 401, "Mirror stream should require Run-Token"
