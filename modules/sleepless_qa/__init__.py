"""
Sleepless QA — Universal Empirical Verification Pipeline

Closed-loop runtime verification: launch headless target → capture evidence
(screenshot/log/HTTP) → emit PASS/FAIL/UNCERTAIN verdict via Claude Vision
or pattern match → dispatch healing via `claude -p` on FAIL → re-verify until
empirical PASS or retry budget exhausted.

Enforces Ley 25 (Empirical Evidence Law). The VPS is the arbiter of truth.
"""

__version__ = "0.1.0"

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
STATE_DIR_DEFAULT = Path.home() / ".claude" / "sleepless-qa"

__all__ = ["__version__", "PACKAGE_ROOT", "STATE_DIR_DEFAULT"]
