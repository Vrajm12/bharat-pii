#!/usr/bin/env python3
"""Standalone test runner for BharatPII Demo, Offsets, and Redaction.

Can be run directly via:
    python examples/test_demo.py
or via pytest:
    python -m pytest examples/test_demo.py
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Forward all tests from tests/test_demo_redaction.py
from tests.test_demo_redaction import (  # noqa: F401
    TestDemoCLI,
    TestModelInferenceAndOffsets,
    TestRedactionUnit,
    TestSyntheticCatalog,
    TestWebDemoServer,
    model,
)

if __name__ == "__main__":
    exit_code = pytest.main([str(Path(__file__).resolve()), "-v"])
    sys.exit(exit_code)
