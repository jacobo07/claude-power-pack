"""V-QA-HINTPROP: the stand-in marker stays banned; the hint-text prop name is allowed."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quality_audit  # noqa: E402

# Assembled at runtime so this detector test does not trip the gate it tests.
UP = "PLACE" + "HOLDER"
LO = UP.lower()
RULE = next(r for r in quality_audit.SLOP_RULES if UP in r[2])[0]

BANNED = [
    f"// {UP} until the API lands",
    f"return '{LO}'",
    f"const value = {UP}",
    f"# {LO} body",
]
ALLOWED = [
    f'<TextInput {LO}="Search worktrees" />',
    f"{LO}={{t('search')}}",
    f"{LO}?: string",
    f"  {LO}: 'Search',",
    f"props.{LO}",
    f"{LO}TextColor={{colors.muted}}",
    f'aria-{LO}="x"',
]


def main() -> int:
    passes = fails = 0
    for line in BANNED:
        if RULE.search(line):
            passes += 1
        else:
            fails += 1
            print(f"FAIL banned not caught: {line!r}")
    for line in ALLOWED:
        if RULE.search(line):
            fails += 1
            print(f"FAIL allowed flagged: {line!r}")
        else:
            passes += 1
    print(f"V-QA-HINTPROP-PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
