"""Root pytest configuration for Vivid backend tests.

This conftest.py ensures the app module is importable.
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
