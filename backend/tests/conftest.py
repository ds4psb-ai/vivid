"""
Root Test Configuration

Sets up environment variables before any app modules are imported.
This ensures Redis-dependent modules use fallback/mock modes.
"""

import os
import sys

# Set BEFORE any app imports to ensure fallback modes are used
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("REDIS_URL", "")  # Empty = use in-memory fallback

# Common pytest fixtures and configuration
import pytest
