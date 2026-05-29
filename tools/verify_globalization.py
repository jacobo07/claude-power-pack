#!/usr/bin/env python3
"""verify_globalization.py — sub-verifier for BL-GLOB-001.

Five binary sub-checks:
  G1 agents-count   >=7 PP agents in ~/.claude/agents/
  G2 agents-schema  each PP agent has name/description/tools, no
                    forbidden YAML keys (triggers:/throttle:)
  G3 rules-common   ~/.claude/rules/common/code-review.md present + has
                    Pre-Report Gate + Zero Findings Is Valid markers
  G4 rules-python   ~/.claude/rules/python/testing.md present + has
                    AAA + TDD markers
  G5 osa-dispatcher dispatcher.should_activate returns valid tuple
                    (cross-check from BL-OSA-001)

Exit 0 iff all 5 pass. Prints GLOB_PROBE=N/5 line for verify_spp.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

HOME = Path.home()
AGENTS_DIR = HOME / ".claude" / "agents"
RULES_DIR = HOME / ".claude" / "rules"


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    # G1 agents-count
    pp_agents = sorted(
        list(AGENTS_DIR.glob("pp-*.md")) +
        list(AGENTS_DIR.glob("omni-*.md"))
    )
    if len(pp_agents) >= 7:
        checks.append(("agents-count", True,
                       f"{len(pp_agents)} PP agents present"))
    else:
        checks.append(("agents-count", False,
                       f"only {len(pp_agents)} PP agents (expected >=7)"))

    # G2 agents-schema
    schema_ok = True
    bad = []
    for p in pp_agents:
        content = p.read_text(encoding="utf-8")
        if not content.startswith("---"):
            schema_ok = False
            bad.append(p.name)
            continue
        fm_end = content.find("\n---", 3)
        fm = content[3:fm_end] if fm_end > 0 else ""
        if not ("name:" in fm and "description:" in fm and "tools:" in fm):
            schema_ok = False
            bad.append(p.name)
        elif "triggers:" in fm or "throttle:" in fm:
            schema_ok = False
            bad.append(p.name)
    if schema_ok:
        checks.append(("agents-schema", True,
                       "all agents valid"))
    else:
        checks.append(("agents-schema", False, f"bad: {bad[:3]}"))

    # G3 rules-common
    common_review = RULES_DIR / "common" / "code-review.md"
    if not common_review.is_file():
        checks.append(("rules-common", False, f"missing: {common_review}"))
    else:
        text = common_review.read_text(encoding="utf-8")
        if "Pre-Report Gate" in text and "Zero Findings Is Valid" in text:
            checks.append(("rules-common", True,
                           f"{common_review.stat().st_size} bytes"))
        else:
            checks.append(("rules-common", False,
                           "ECC doctrine markers missing"))

    # G4 rules-python
    py_testing = RULES_DIR / "python" / "testing.md"
    if not py_testing.is_file():
        checks.append(("rules-python", False, f"missing: {py_testing}"))
    else:
        text = py_testing.read_text(encoding="utf-8")
        if "AAA" in text and "TDD" in text:
            checks.append(("rules-python", True,
                           f"{py_testing.stat().st_size} bytes"))
        else:
            checks.append(("rules-python", False,
                           "AAA/TDD markers missing"))

    # G5 osa-dispatcher (cross-check from BL-OSA-001)
    try:
        from modules.osa.dispatcher import should_activate
        result = should_activate("verify-glob-probe")
        if (isinstance(result, tuple) and len(result) == 3
                and isinstance(result[2], dict)):
            checks.append(("osa-dispatcher", True,
                           f"active={result[0]} reason={result[1]}"))
        else:
            checks.append(("osa-dispatcher", False,
                           f"unexpected: {result!r}"))
    except Exception as exc:
        checks.append(("osa-dispatcher", False,
                       f"{type(exc).__name__}: {exc}"))

    passes_n = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, msg in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {name:18s} {msg}")
    print()
    print(f"GLOB_PROBE={passes_n}/{total}")
    return 0 if passes_n == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
