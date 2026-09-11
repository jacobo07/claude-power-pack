"""V-LIVEWRAP-* -- is the OWNER'S hook registry currently infected, right now.

tools/test_conhost_hook_leak.py proves repair() works, and proves it on
SYNTHETIC fixtures on purpose: a drill pinned to the Owner's real settings.json
has an interest in that file staying broken, and would go green the moment it
was fixed. That reasoning is correct and this file does not touch it.

It answers the OTHER question, which nothing was asking.

MEASURED 2026-09-11. The wrappers were removed at 21:37 and were back by 22:27
-- eleven entries across eleven events, the same `%USERPROFILE%\\.orca\\
agent-hooks\\claude-hook.cmd`. The installer reinstates them on launch, so the
repair is not a one-time fix and never was. The whole suite stayed green
through the re-infection, because every subject in it was a fixture. A gate
that proves the FIXER works is not a gate that proves the ESTATE is fixed, and
the difference is invisible for exactly as long as nobody looks.

ADVISORY BY CONTRACT. This repo cannot repair ~/.claude -- HR-001 reserves that
to the Owner -- so a red here is not a defect in this changeset and must never
block a sweep. A gate that is red on arrival and blocks gets disabled within a
week, which would cost more than it saves. It reports, loudly, every run.

Three outcomes, because "clean" and "could not look" are different facts:
    0  no wrapped entries found
    1  wrapped entries found -- the screen-clear is live
    3  the registry could not be read; nothing was judged
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.fix_conhost_hook_leak import scan  # noqa: E402

LIVE_SETTINGS = Path.home() / ".claude" / "settings.json"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    target = Path(argv[argv.index("--settings") + 1]) if "--settings" in argv \
        else LIVE_SETTINGS

    print("=" * 72)
    print("check_live_hook_wrappers -- V-LIVEWRAP (subject: the LIVE registry)")
    print(f"  target : {target}")

    if not target.exists():
        # Not a pass. An absent registry means the question was not answered,
        # and a clean bill from a file that is not there is worth nothing.
        print("  [??  ] V-LIVEWRAP-READABLE   registry absent -- nothing judged")
        print("LIVEWRAP=UNKNOWN")
        return 3
    try:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        print(f"  [??  ] V-LIVEWRAP-READABLE   unreadable: "
              f"{type(exc).__name__}: {exc}")
        print("LIVEWRAP=UNKNOWN")
        return 3

    wrapped = scan(data)
    if not wrapped:
        print("  [OK  ] V-LIVEWRAP-CLEAN      0 conhost-wrapped hook entries")
        print("LIVEWRAP=CLEAN")
        return 0

    events: dict[str, int] = {}
    commands = set()
    for event, _mi, _hi, cmd in wrapped:
        events[event] = events.get(event, 0) + 1
        commands.add(cmd)
    print(f"  [WARN] V-LIVEWRAP-INFECTED  {len(wrapped)} wrapped entr(ies) "
          f"across {len(events)} event(s)")
    for ev in sorted(events):
        print(f"           {ev:<22s} {events[ev]}")
    for c in sorted(commands):
        print(f"         wrapped command: {c}")
    print()
    print("  Every event above clears the Owner's terminal when it fires, and")
    print("  discards the wrapped hook's output. On PreToolUse with matcher")
    print("  '*' that is every tool call in every repository.")
    print()
    print("  OWNER-SIDE FIX (HR-001 -- this repo may not write ~/.claude):")
    print("    python tools/fix_conhost_hook_leak.py --apply")
    print("  A backup is written first. It is idempotent, and it does NOT")
    print("  stop the installer from reinstating them on its next launch.")
    print("LIVEWRAP=INFECTED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
