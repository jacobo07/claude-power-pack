"""Keep the PP-vendored raw-% statusline and the live GSD copy identical.

The context meter (RAW used % = 100 - remaining_percentage, bridge file agreeing with
the bar) is a local patch inside the GSD-owned ~/.claude/hooks/gsd-statusline.js, which
lives outside every git repo, so a `/gsd-update` can silently put the 16.5% autocompact
buffer back. The PP copy at hooks/vendor/gsd-statusline.js is the version-controlled source.

  python tools/statusline_sync.py --check     exit 1 if live differs from the vendored copy
  python tools/statusline_sync.py --install   copy vendored -> live (backs up the old live file)
  python tools/statusline_sync.py --adopt     copy live -> vendored (after a deliberate edit)
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import time
from pathlib import Path

VENDORED = Path(__file__).resolve().parent.parent / "hooks" / "vendor" / "gsd-statusline.js"
LIVE = Path.home() / ".claude" / "hooks" / "gsd-statusline.js"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--adopt", action="store_true")
    args = ap.parse_args()

    if not VENDORED.exists():
        print(f"HARNESS-FAILED: vendored copy missing at {VENDORED}")
        return 2
    if not LIVE.exists() and not args.install:
        print(f"HARNESS-FAILED: live statusline missing at {LIVE}")
        return 2

    if args.adopt:
        shutil.copyfile(LIVE, VENDORED)
        print(f"ADOPTED live -> vendored sha256={digest(VENDORED)[:12]}")
        return 0

    same = LIVE.exists() and digest(LIVE) == digest(VENDORED)
    if args.check:
        print(f"{'IN-SYNC' if same else 'DRIFT'}: vendored={digest(VENDORED)[:12]} "
              f"live={digest(LIVE)[:12]}")
        return 0 if same else 1

    if same:
        print("IN-SYNC: nothing to install")
        return 0
    if LIVE.exists():
        backup = LIVE.with_name(f"gsd-statusline.js.bak-{time.strftime('%Y%m%dT%H%M%S')}")
        shutil.copyfile(LIVE, backup)
        print(f"BACKUP {backup}")
    shutil.copyfile(VENDORED, LIVE)
    ok = digest(LIVE) == digest(VENDORED)
    print(f"{'INSTALLED' if ok else 'INSTALL-FAILED'}: live sha256={digest(LIVE)[:12]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
