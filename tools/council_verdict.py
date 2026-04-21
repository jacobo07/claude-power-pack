#!/usr/bin/env python3
"""
Council Verdict CLI — helper for TheWarRoom (MC-U3).

Renders the 5-advisor Council prompt block with Howard's Loop context
pre-injected, to be pasted into the agent's response. Also validates
and stamps verdicts on a staged diff.

Does NOT call an LLM. The Council runs inline in the main agent's response.

Usage:
    python council_verdict.py --render                # print the Council template with Howard's Loop injected
    python council_verdict.py --render --project kobiicraft  # also inject GEX44 antipatterns
    python council_verdict.py --howard-loop-top N     # show top-N Howard's Loop entries
    python council_verdict.py --stamp A+              # validate and echo the verdict banner

Doctrine: ~/.claude/skills/claude-power-pack/modules/governance-overlay/council.md
"""

import argparse
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HOME = Path.home()
VISUAL_ANTIPATTERNS = HOME / ".claude" / "knowledge_vault" / "governance" / "visual-antipatterns.md"
GEX44_DIR = HOME / ".claude" / "knowledge_vault" / "gex44_antipatterns"
VALID_VERDICTS = ("A+", "A", "B", "REJECT")
VISUAL_PROJECTS = ("kobiicraft", "kobiisports")


def load_howard_loop_top(n: int = 3) -> list[str]:
    """Extract top-N H2/H3 headings from visual-antipatterns.md as lesson titles."""
    if not VISUAL_ANTIPATTERNS.exists():
        return []
    text = VISUAL_ANTIPATTERNS.read_text(encoding="utf-8", errors="replace")
    # Match ## or ### headings; strip leading markers and trailing whitespace
    headings = re.findall(r"^#{2,3}\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return headings[:n]


def load_gex44_entries(n: int = 3) -> list[str]:
    """Return up to N filenames (without .md) from gex44_antipatterns/."""
    if not GEX44_DIR.exists():
        return []
    entries = sorted(p.stem for p in GEX44_DIR.glob("*.md"))
    return entries[:n]


def cmd_howard_loop(args) -> int:
    entries = load_howard_loop_top(args.howard_loop_top)
    if not entries:
        print("(no entries found — visual-antipatterns.md missing or empty)")
        return 1
    for i, title in enumerate(entries, 1):
        print(f"{i}. {title}")
    return 0


def cmd_render(args) -> int:
    top = load_howard_loop_top(3)
    injected = ", ".join(top) if top else "(none registered yet)"
    extra_gex = ""
    if args.project and args.project.lower() in VISUAL_PROJECTS:
        gex = load_gex44_entries(3)
        if gex:
            extra_gex = f"\nGEX44 antipatterns (visual stack): {', '.join(gex)}"

    template = f"""[COUNCIL BLOCK]
Prior antipatterns considered: {injected}{extra_gex}

• Contrarian: <what breaks this? one failure mode the author missed, or 'no contrarian objection'>
• First Principles: <atomic operations; flag any new-and-reinvented when reusable form exists>
• Expansionist: <what unlocks next? what constraint is lifted?>
• Outsider: <would a senior engineer unfamiliar with this codebase approve? conventions flagged?>
• Executor: <ship now or more work? 30-second verification command?>

[COUNCIL_VERDICT: <A+|A|B|REJECT>]

# Grading rubric:
#   A+   — all 5 advisors approve, zero open objections. Ship.
#   A    — <=1 advisor has a minor caveat addressed in the response. Ship.
#   B    — >=2 advisors raise caveats, or any raises a major concern. BLOCK.
#   REJECT — correctness bug, security hole, or scaffold illusion. BLOCK.
"""
    print(template)
    return 0


def cmd_stamp(args) -> int:
    v = args.stamp.strip()
    if v not in VALID_VERDICTS:
        print(f"ERROR: '{v}' is not a valid verdict. Must be one of: {VALID_VERDICTS}", file=sys.stderr)
        return 1
    print(f"[COUNCIL_VERDICT: {v}]")
    if v in ("B", "REJECT"):
        print("\n⚠ BLOCKED. Route to Rejection Recovery (post-output.md § Rejection Recovery).", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Council Verdict CLI")
    parser.add_argument("--render", action="store_true", help="Print the Council prompt template with Howard's Loop injected")
    parser.add_argument("--project", default=None, help="Project id (kobiicraft, kobiisports, ...) — activates GEX44 injection for visual stacks")
    parser.add_argument("--howard-loop-top", type=int, default=0, metavar="N", help="Print top-N Howard's Loop entries and exit")
    parser.add_argument("--stamp", default=None, metavar="VERDICT", help="Validate and print a verdict banner (A+ | A | B | REJECT)")

    args = parser.parse_args()

    if args.howard_loop_top > 0:
        return cmd_howard_loop(args)
    if args.stamp:
        return cmd_stamp(args)
    if args.render:
        return cmd_render(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
