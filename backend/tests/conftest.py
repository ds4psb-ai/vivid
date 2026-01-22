"""Root pytest configuration for Vivid backend tests.

This conftest.py ensures the app module is importable.
"""
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# H2.1: Enable dev auth bypass for tests (before importing app.config)
# This allows X-User-Id and X-Admin-Mode headers to work in test environment
os.environ.setdefault("ENABLE_DEV_AUTH_BYPASS", "true")
os.environ.setdefault("ENVIRONMENT", "development")
