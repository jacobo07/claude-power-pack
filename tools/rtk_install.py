#!/usr/bin/env python3
"""rtk_install.py — zero-argument RTK PreToolUse activation.

Why this exists: the equivalent `settings_merger.py register-pretool
--node-script <long abs path> ...` line is long enough that pasted
terminals wrap it, splitting --node-script from its value and breaking
argparse. This wrapper hard-codes the absolute paths so the operator
runs ONE short command with no arguments to mangle:

    python tools/rtk_install.py

It is an Owner-run activation (the harness auto-mode classifier denies
the agent writing ~/.claude/settings.json directly). All it does is
call the already-verified register_pretool() with resolved absolute
paths, then print the result.
"""

from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "modules", "rtk-core", "rtk-rewrite.js")

sys.path.insert(0, os.path.join(REPO, "tools"))
from settings_merger import register_pretool, DEFAULT_SETTINGS  # noqa: E402


def main() -> int:
    if not os.path.isfile(HOOK):
        print(f"rtk_install: hook not found at {HOOK}", file=sys.stderr)
        return 5
    print(f"rtk_install: registering PreToolUse(Bash) -> {HOOK}")
    rc = register_pretool(DEFAULT_SETTINGS, HOOK, "Bash", 10)
    if rc == 0:
        print("rtk_install: DONE. Next: /restart, then run a few Bash "
              "commands and `rtk gain` to confirm live token savings.")
    else:
        print(f"rtk_install: FAILED (exit {rc}); settings.json untouched "
              f"or rolled back by settings_merger.", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
