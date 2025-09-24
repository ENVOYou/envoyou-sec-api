# Ensure project root is importable and ignore legacy 'test' folder during collection
import os
import sys
import pytest

# Add project root to sys.path for absolute imports like 'tests.*'
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Tell pytest to ignore the old 'test' folder
collect_ignore_glob = ["test/*"]

# By default, skip legacy permit-api and unrelated integration tests.
# Set environment variable ENVOYOU_RUN_ALL_TESTS=true to run the full test suite.
SKIP_PATTERNS = [
    "test_auth",
    "test_permits",
    "test_cevs",
    "test_search",
    "test_security",
    "test_api",
    "test_free_api",
    "test_paddle",
    "test_redis",
    "test_user",       # skip legacy user stats tests
    "quick_test",      # skip ad-hoc quick test
]

RUN_ALL = os.getenv("ENVOYOU_RUN_ALL_TESTS", "false").lower() == "true"


def pytest_collection_modifyitems(config, items):
    if RUN_ALL:
        return

    skip_marker = pytest.mark.skip(reason="skipped in Envoyou-focused test run; set ENVOYOU_RUN_ALL_TESTS=true to run all tests")
    for item in items:
        path = str(item.fspath).lower()
        if any(pat in path for pat in SKIP_PATTERNS):
            item.add_marker(skip_marker)
