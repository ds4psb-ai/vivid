import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.pattern_versioning import _next_capsule_version


def test_next_capsule_version_increments_patch():
    next_version = _next_capsule_version("1.2.3", {"1.2.4"})
    assert next_version == "1.2.5"


def test_next_capsule_version_basic():
    next_version = _next_capsule_version("0.1.0", set())
    assert next_version == "0.1.1"
