#!/usr/bin/env python3
"""verify_claude_md_size.py - verify_spp CLAUDE_MD_SIZE probe (CLAUDE.md Router).

Gate: the GLOBAL ~/.claude/CLAUDE.md must stay under the Claude Code 40,000-char
performance-warning threshold. FAIL (rc 1) only at >= 40,000; the WARN band
(>= TARGET_MARGIN) is reported but PASSES -- the firewall + Stop linter handle
"approaching the limit", this probe is the hard backstop.

The file is GLOBAL (outside the repo) and unversioned; on a host/CI where it
does not exist the probe SKIPS (rc 0, not a failure). Reuses trim_claude_md's
thresholds (SCS C28).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.trim_claude_md import TARGET_MAX, TARGET_MARGIN, CM  # noqa: E402


def main() -> int:
    if not CM.exists():
        print("V-CLAUDE-MD-SIZE: SKIP -- no ~/.claude/CLAUDE.md on this host")
        return 0
    n = len(CM.read_text(encoding="utf-8-sig"))
    if n >= TARGET_MAX:
        print(f"V-CLAUDE-MD-SIZE: FAIL -- {n} chars >= {TARGET_MAX} "
              f"(Claude Code perf warning ACTIVE). Run "
              f"`python tools/trim_claude_md.py --dry-run` then --apply.")
        return 1
    band = "WARN" if n >= TARGET_MARGIN else "OK"
    print(f"V-CLAUDE-MD-SIZE: PASS ({band}) -- {n} chars < {TARGET_MAX} "
          f"(margin {TARGET_MARGIN}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
