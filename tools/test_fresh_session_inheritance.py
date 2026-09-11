#!/usr/bin/env python3
"""Which layer actually reaches a session that nobody told about this skill?

Phases II and III proved the constitution reaches a fresh CONTEXT: a subagent,
spawned by a session that already knew the answer, sharing its host. Phase IV
crossed a real boundary instead -- `claude -p`, a separate operating-system
process with its own conversation, no parent transcript and no channel back --
and the result was not the one three phases of prose had assumed.

MEASURED 2026-09-11, two arms of one question about an I2C EEPROM write whose
HAL call returns HAL_OK, asked in a scratch directory, naming no law, no skill
and no framework. Leakage audited first: the global CLAUDE.md carries neither
law string, nor did the prompt, nor any environment variable.

    marker                     full stack      --safe-mode
    instrument-before-claim        HIT              --
    permissive substitute          HIT              --
    readback                       HIT              --
    graded / rung vocabulary       HIT              --
    LAW II / LAW IX by name        --               --

Two facts, and they point opposite ways.

The persistent doctrine layer DOES cross a genuine session boundary. Four
markers present with the stack on and absent with it off is not the model
knowing the subject; the same model answered the same question both times. The
answer named `instrument-before-claim` and reproduced its permissive-substitute
argument, which lives in ~/.claude/rules/ and reached a process that was told
nothing.

USEA's own laws did not. `SKILL.md` declaring `parts/core.md` ALWAYS READ makes
it always-read WITHIN THE SKILL -- and a skill has to be invoked. The always-on
layer is ~/.claude/CLAUDE.md plus ~/.claude/rules/, and LAW II and LAW IX are in
neither.

That is LAW II turned on USEA itself. "Declared always-read" is a cheap visible
signal; the corroborant is a session that never heard of the skill citing the
law, and that corroborant came back NEGATIVE. The laws' SUBSTANCE arrived anyway
-- the answer said HAL_OK means transmitted, not verified, and told the engineer
to read back and compare, which is the proxy/corroborant distinction reached
without the vocabulary. Substance is not the same as inheritance, and a claim
that the constitution is inherited by every session is not supported.

This suite pins the boundary so the claim cannot drift back. It READS the global
layer and never writes it: HR-001 reserves writes under ~/.claude/ to the Owner,
and a detector does not need write access to notice a gap. If the Owner ever
moves the laws into the always-on layer, V-FRESH-GLOBAL-LAYER-CARRIES-LAWS flips
to OK on its own and the recorded limitation stops being true.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()

SKILL_MD = _ROOT / "SKILL.md"
CORE_MD = _ROOT / "parts" / "core.md"
GLOBAL_MD = HOME / ".claude" / "CLAUDE.md"
GLOBAL_RULES = HOME / ".claude" / "rules"

LAW_RE = re.compile(r"LAW\s*(?:II|IX)\b")

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def main() -> int:
    skill, core, glob = _read(SKILL_MD), _read(CORE_MD), _read(GLOBAL_MD)

    # Positive control. Every assertion here is a substring or regex test, and
    # those pass silently against an unreadable file while proving nothing.
    check("V-FRESH-SOURCES-READ",
          len(skill) > 200 and len(core) > 1000,
          f"SKILL.md {len(skill)} chars, parts/core.md {len(core)} chars")

    # --- the proxy ---------------------------------------------------------
    check("V-FRESH-PROXY-DECLARED",
          "core.md" in skill,
          "the router declares parts/core.md as its always-read part")
    check("V-FRESH-LAWS-LIVE-IN-THE-SKILL",
          bool(LAW_RE.search(core)),
          "LAW II and LAW IX are carried by the skill's always-read part")

    # --- the corroborant ---------------------------------------------------
    # The always-on layer is what a session loads without invoking anything.
    rules_text = ""
    rule_files = sorted(GLOBAL_RULES.rglob("*.md")) if GLOBAL_RULES.is_dir() else []
    for rf in rule_files:
        rules_text += _read(rf)
    check("V-FRESH-GLOBAL-LAYER-READABLE",
          bool(glob) and bool(rule_files),
          f"global CLAUDE.md {len(glob)} chars + {len(rule_files)} always-on "
          f"rule file(s) — the layer a fresh session loads unprompted")

    in_global = bool(LAW_RE.search(glob)) or bool(LAW_RE.search(rules_text))
    # Deliberately NOT an assertion that the laws are absent. Asserting the
    # current gap would make the Owner's fix break the suite, which is the wrong
    # incentive: this reports, and flips to OK by itself the day the laws move.
    print(f"  {'OK  ' if in_global else 'NOTE'} "
          f"V-FRESH-GLOBAL-LAYER-CARRIES-LAWS  "
          f"{'the always-on layer carries the laws, so any session inherits them'
             if in_global else
             'the always-on layer does NOT carry LAW II/IX, so a session that '
             'never invokes this skill does not inherit them (measured: a fresh '
             'claude -p cited neither). OWNER-SIDE remedy, HR-001: only the '
             'Owner may write under ~/.claude/ outside this repo.'}")

    # --- the claim must not exceed the evidence ---------------------------
    # This is the gate that actually protects anything: no document in this
    # repository may assert universal session inheritance, because the strongest
    # boundary crossed says otherwise.
    overclaims = []
    for doc in (SKILL_MD, CORE_MD):
        text = _read(doc)
        for m in re.finditer(r"[^.\n]*inherit[^.\n]*[.\n]", text, re.IGNORECASE):
            s = m.group(0).strip()
            if re.search(r"every session|all sessions|any session", s, re.IGNORECASE) \
                    and not re.search(r"skill|invoke", s, re.IGNORECASE):
                overclaims.append(f"{doc.name}: {s[:120]}")
    check("V-FRESH-NO-UNIVERSAL-INHERITANCE-CLAIM",
          not overclaims,
          f"overstated inheritance claims: {overclaims}" if overclaims
          else "no document claims every session inherits the laws without "
               "naming skill invocation as the path")

    # --- and the substance/vocabulary distinction stays recorded ----------
    check("V-FRESH-SUBSTANCE-IS-NOT-INHERITANCE",
          "proxy" in core.lower() and "corroborant" in core.lower(),
          "the law names both halves, so reaching its conclusion by other means "
          "is never evidence that the law itself travelled")

    print(f"FRESH_INHERITANCE_PASS={PASSES}/{PASSES + FAILS}  "
          f"threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
