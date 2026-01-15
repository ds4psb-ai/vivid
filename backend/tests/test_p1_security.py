"""
P1.3 Security Hardening Tests
============================

Tests for security middleware following 2026 OWASP best practices.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    SuspiciousActivityMiddleware,
    get_client_ip,
    get_request_fingerprint,
    setup_security_middleware,
)


class TestSecurityHeadersMiddleware:
    """Test security headers are properly added to responses."""

    @pytest.fixture
    def app_with_security_headers(self):
        """Create FastAPI app with security headers middleware."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    def test_hsts_header(self, app_with_security_headers):
        """Test Strict-Transport-Security header is present."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    def test_content_type_options_header(self, app_with_security_headers):
        """Test X-Content-Type-Options header is nosniff."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_frame_options_header(self, app_with_security_headers):
        """Test X-Frame-Options header is DENY."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_header(self, app_with_security_headers):
        """Test Content-Security-Policy header is present."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    def test_xss_protection_header(self, app_with_security_headers):
        """Test X-XSS-Protection header is set."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy_header(self, app_with_security_headers):
        """Test Referrer-Policy header is set."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self, app_with_security_headers):
        """Test Permissions-Policy header is set."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert "Permissions-Policy" in response.headers
        assert "geolocation=()" in response.headers["Permissions-Policy"]


class TestRequestIDMiddleware:
    """Test request ID tracking middleware."""

    @pytest.fixture
    def app_with_request_id(self):
        """Create FastAPI app with request ID middleware."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}

        return app

    def test_request_id_generated(self, app_with_request_id):
        """Test request ID is generated when not provided."""
        client = TestClient(app_with_request_id)
        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_request_id_preserved(self, app_with_request_id):
        """Test provided request ID is preserved."""
        client = TestClient(app_with_request_id)
        custom_id = "my-custom-request-id-123"
        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["X-Request-ID"] == custom_id

    def test_request_id_in_response_body(self, app_with_request_id):
        """Test request ID is accessible in endpoint."""
        client = TestClient(app_with_request_id)
        response = client.get("/test")

        data = response.json()
        assert "request_id" in data
        assert data["request_id"] == response.headers["X-Request-ID"]


class TestRequestTimingMiddleware:
    """Test request timing middleware."""

    @pytest.fixture
    def app_with_timing(self):
        """Create FastAPI app with timing middleware."""
        app = FastAPI()
        app.add_middleware(RequestTimingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    def test_process_time_header(self, app_with_timing):
        """Test X-Process-Time header is added."""
        client = TestClient(app_with_timing)
        response = client.get("/test")

        assert "X-Process-Time" in response.headers
        assert "ms" in response.headers["X-Process-Time"]


class TestSuspiciousActivityMiddleware:
    """Test suspicious activity detection middleware."""

    @pytest.fixture
    def app_with_suspicious_detection(self):
        """Create FastAPI app with suspicious detection middleware."""
        app = FastAPI()
        app.add_middleware(SuspiciousActivityMiddleware, block_suspicious=False)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    def test_normal_request_passes(self, app_with_suspicious_detection):
        """Test normal requests are not flagged."""
        client = TestClient(app_with_suspicious_detection)
        response = client.get("/test")

        assert response.status_code == 200

    def test_middleware_allows_normal_request(self, app_with_suspicious_detection):
        """Test middleware allows normal requests through."""
        client = TestClient(app_with_suspicious_detection)
        response = client.get("/test", params={"id": "123", "name": "test"})

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_suspicious_patterns_exist(self):
        """Test suspicious patterns are defined."""
        assert len(SuspiciousActivityMiddleware.SUSPICIOUS_PATTERNS) > 0
        assert "../" in SuspiciousActivityMiddleware.SUSPICIOUS_PATTERNS
        assert "union select" in SuspiciousActivityMiddleware.SUSPICIOUS_PATTERNS
        assert "<script" in SuspiciousActivityMiddleware.SUSPICIOUS_PATTERNS

    def test_suspicious_user_agents_exist(self):
        """Test suspicious user agents are defined."""
        assert len(SuspiciousActivityMiddleware.SUSPICIOUS_USER_AGENTS) > 0
        assert "sqlmap" in SuspiciousActivityMiddleware.SUSPICIOUS_USER_AGENTS
        assert "nikto" in SuspiciousActivityMiddleware.SUSPICIOUS_USER_AGENTS

    def test_max_body_size_configurable(self):
        """Test max body size can be configured."""
        app = FastAPI()
        middleware = SuspiciousActivityMiddleware(app.router, max_body_size=5000)

        assert middleware.max_body_size == 5000


class TestGetClientIP:
    """Test client IP extraction from various headers."""

    def test_cloudflare_header(self):
        """Test CF-Connecting-IP header is prioritized."""
        request = Mock()
        request.headers = {"CF-Connecting-IP": "1.2.3.4"}
        request.client = Mock(host="10.0.0.1")

        assert get_client_ip(request) == "1.2.3.4"

    def test_real_ip_header(self):
        """Test X-Real-IP header is used when CF header absent."""
        request = Mock()
        request.headers = {"X-Real-IP": "5.6.7.8"}
        request.client = Mock(host="10.0.0.1")

        assert get_client_ip(request) == "5.6.7.8"

    def test_forwarded_for_header(self):
        """Test X-Forwarded-For header is used (first IP)."""
        request = Mock()
        request.headers = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3"}
        request.client = Mock(host="10.0.0.1")

        assert get_client_ip(request) == "1.1.1.1"

    def test_direct_client(self):
        """Test direct client IP when no proxy headers."""
        request = Mock()
        request.headers = {}
        request.client = Mock(host="192.168.1.1")

        assert get_client_ip(request) == "192.168.1.1"


class TestGetRequestFingerprint:
    """Test request fingerprint generation."""

    def test_fingerprint_consistency(self):
        """Test same request data produces same fingerprint."""
        request = Mock()
        request.headers = {
            "user-agent": "Mozilla/5.0",
            "accept-language": "en-US",
        }
        request.client = Mock(host="1.2.3.4")

        fp1 = get_request_fingerprint(request)
        fp2 = get_request_fingerprint(request)

        assert fp1 == fp2
        assert len(fp1) == 16

    def test_fingerprint_varies_with_ip(self):
        """Test different IPs produce different fingerprints."""
        request1 = Mock()
        request1.headers = {"user-agent": "Mozilla/5.0", "accept-language": "en-US"}
        request1.client = Mock(host="1.2.3.4")

        request2 = Mock()
        request2.headers = {"user-agent": "Mozilla/5.0", "accept-language": "en-US"}
        request2.client = Mock(host="5.6.7.8")

        assert get_request_fingerprint(request1) != get_request_fingerprint(request2)


class TestSetupSecurityMiddleware:
    """Test security middleware setup function."""

    def test_setup_all_middleware(self):
        """Test all middleware can be enabled."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        setup_security_middleware(
            app,
            enable_security_headers=True,
            enable_request_id=True,
            enable_timing=True,
            enable_suspicious_detection=True,
        )

        client = TestClient(app)
        response = client.get("/test")

        # Check all headers are present
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert response.status_code == 200

    def test_setup_selective_middleware(self):
        """Test selective middleware enabling."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        setup_security_middleware(
            app,
            enable_security_headers=True,
            enable_request_id=False,
            enable_timing=False,
            enable_suspicious_detection=False,
        )

        client = TestClient(app)
        response = client.get("/test")

        # Only security headers should be present
        assert "Strict-Transport-Security" in response.headers
        assert "X-Request-ID" not in response.headers
