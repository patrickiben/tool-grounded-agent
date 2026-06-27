import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import selftest  # noqa: E402


def test_selftest_returns_zero():
    assert selftest.main() == 0
