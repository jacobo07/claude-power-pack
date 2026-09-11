#!/usr/bin/env python3
"""Suite entry point for the foreign-hunk guard.

The guard carries its own self-test because the fixture it needs is a real git
repository with two writers in one file, and that is cheaper to build inside
the tool than to describe to one. This wrapper exists so the mutation probe and
the verify_spp row have a conventional, argument-free suite to run: a probe
that cannot invoke a suite reports nothing caught, which is indistinguishable
from a suite that catches nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.foreign_hunk_guard import _self_test  # noqa: E402

if __name__ == "__main__":
    sys.exit(_self_test())
