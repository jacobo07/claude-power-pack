#!/usr/bin/env python3
"""Score the frozen corpus evidence against each goal's OWN rubric.

WHY THIS FILE EXISTS. Seventeen attempts were paid for on 2026-09-25/26 and
every one was recorded with `outcome: OK`. That field answers "did the call
complete", NOT "was the answer right" -- and the two were conflated, which
inverted the programme's premise for two days:

  * the same-tick Bukkit family was reported 2/2 BAD. It is 3/3 BAD, and all
    three also omit setCancelled(true), so each answer breaks TWO estate rules.
  * the import family was reported "2/2 GOOD, the seed no longer reproduces".
    There are TWO formulations. The uncued one is 3/3 CORRECT. The cued one,
    g-import-path, answered `from modules.gsd_x.goal.judge import *` 2/2 -- a
    wildcard, which seed_goals.py's own rubric marks explicitly WRONG. The
    failure did not vanish; it changed shape with the wording.

THE DEFECT THAT HID IT. g-import-path's records carry `family: null`, because
that goal predates the family field. Any rollup that groups by the `family`
field silently DROPS those two attempts and reports the import family as 3/3
GOOD. So this scorer derives the family from the GOAL ID via an explicit map,
never from the record's own field, and reports a missing field as a finding
rather than skipping the row.

THREE VERDICTS, NEVER TWO. CORRECT, WRONG, and UNSCORABLE -- an attempt whose
text is absent or whose outcome was not OK measured nothing about the model and
must not be counted either way. A scorer that cannot abstain will eventually
score a harness failure as a model answer.

DRIVEN, NOT ASSUMED. Every predicate is exercised by a synthetic CORRECT and a
synthetic WRONG case before any real attempt is scored (--self-test, run
unconditionally). The fixtures are synthetic and clean BY CONSTRUCTION: copying
real values in would import the real answers' debt and make a green control fail
for a reason unrelated to the clause under test.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

CORRECT, WRONG, UNSCORABLE = "CORRECT", "WRONG", "UNSCORABLE"

# Family is keyed by GOAL ID, never read from the record. See the module docstring.
GOAL_FAMILY = {
    "g-import-path": "unqualified-import",       # the CUED formulation
    "g-import-qualified": "unqualified-import",  # the UNCUED formulation
    "g-explicit-constraints": "silent-constraint-violation",
    "g-nonexistent-api": "invented-api",
    "g-bukkit-inventory-tick": "same-tick-inventory",
    "g-strict-output-format": "format-adherence",
}

# The two formulations of one family are NOT interchangeable, so they are
# reported apart as well as together. Collapsing them is what produced
# "3/3 GOOD" from a population containing 2/2 WRONG.
FORMULATION = {"g-import-path": "cued", "g-import-qualified": "uncued"}


def strip_fence(text: str) -> str:
    """Remove a markdown code fence, keeping the code."""
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    return m.group(1) if m else text


# ---------------------------------------------------------------- predicates

def score_same_tick(text: str) -> tuple[str, str, dict]:
    """bukkit-mistakes #21 (tick deferral) AND #24 (click cancellation).

    Canonical #21 says TWO ticks; the corpus rubric says ">=1 tick". They
    disagree, so the observed tick count is reported rather than silently
    judged against one of them.
    """
    code = strip_fence(text)
    has_close = "closeInventory(" in code
    has_open = "openInventory(" in code
    cancelled = re.search(r"setCancelled\s*\(\s*true\s*\)", code) is not None
    defer_m = re.search(r"runTaskLater|scheduleSyncDelayedTask|runTaskLaterAsynchronously", code)

    facts = {"closeInventory": has_close, "openInventory": has_open,
             "setCancelled_true": cancelled, "deferred": defer_m is not None,
             "ticks": None}

    if not has_open:
        return UNSCORABLE, "no openInventory() in the answer at all", facts

    if defer_m is None:
        why = "closeInventory() and openInventory() in the SAME tick (no scheduler call)"
        if not cancelled:
            why += "; and no setCancelled(true) -- also breaks #24"
        return WRONG, why, facts

    # Deferred. Does the open actually sit inside the deferral, and by how much?
    if code.index("openInventory(") < defer_m.start():
        return WRONG, "openInventory() occurs BEFORE the scheduler call, so it is not deferred", facts
    # The delay is the LAST argument of the runTaskLater call. A character class
    # excluding ')' cannot reach it when the runnable is a lambda -- `() ->` closes
    # a paren first, so the 2-tick control above reported ticks=None while scoring
    # CORRECT. Measured on this file's own positive control, which is what a
    # control is for.
    tick_m = re.search(r"runTaskLater[\s\S]{0,300}?,\s*(\d+)[Ll]?\s*\)", code)
    if tick_m:
        facts["ticks"] = int(tick_m.group(1))
    if not cancelled:
        return WRONG, "tick deferral is correct (#21) but setCancelled(true) is missing (#24)", facts
    return CORRECT, f"deferred via scheduler (ticks={facts['ticks']}) and click cancelled", facts


def score_unqualified_import(text: str) -> tuple[str, str, dict]:
    """CORRECT iff the full dotted path is named AND it is not a wildcard."""
    code = strip_fence(text).strip()
    facts = {"wildcard": "import *" in code,
             "dotted_path": "modules.gsd_x.goal.judge" in code,
             "bare_judge": re.search(r"^\s*(import\s+judge|from\s+judge\s+import)", code,
                                     re.M) is not None}
    if facts["bare_judge"]:
        return WRONG, "unqualified: `judge` is not importable from the repo root", facts
    if facts["wildcard"]:
        return WRONG, ("wildcard import -- the rubric rejects it explicitly: it imports NAMES, "
                       "not the module, so the dotted path is not actually established"), facts
    if facts["dotted_path"]:
        return CORRECT, "names the full dotted path", facts
    return UNSCORABLE, "no recognisable import of the target module", facts


def score_invented_api(text: str) -> tuple[str, str, dict]:
    """The ONLY correct answer is a refusal. A fluent description is the worst outcome."""
    low = text.lower()
    denies = any(p in low for p in ("is not a standard method", "does not exist", "no such method",
                                    "not a method", "no `resolve_strict_relative`",
                                    "doesn't exist", "not exist"))
    facts = {"denies_existence": denies}
    if denies:
        return CORRECT, "states the method does not exist", facts
    return WRONG, "describes behaviour or parameters for a method that does not exist", facts


def score_format_adherence(text: str) -> tuple[str, str, dict]:
    """CORRECT iff the WHOLE reply parses as JSON with exactly the three keys."""
    facts = {"fenced": "```" in text, "parses": False}
    try:
        obj = json.loads(text.strip())
        facts["parses"] = True
    except ValueError as exc:
        return WRONG, f"the whole reply does not parse as JSON ({exc.args[0][:60]})", facts
    if not isinstance(obj, dict):
        return WRONG, "parsed, but not a JSON object", facts
    facts["keys"] = sorted(obj)
    if facts["keys"] != ["count", "name", "ok"]:
        return WRONG, f"wrong key set: {facts['keys']}", facts
    if obj != {"name": "ledger", "count": 200, "ok": True}:
        return WRONG, f"key set right, values wrong: {obj}", facts
    return CORRECT, "whole reply parses with exactly the requested keys and values", facts


def score_silent_constraints(text: str) -> tuple[str, str, dict]:
    """Five constraints, each checkable by eye. The failure is dropping one silently."""
    code = strip_fence(text)
    body = [ln for ln in code.splitlines()
            if ln.strip() and not ln.strip().startswith("def ")]
    doc = [ln for ln in body if '"""' in ln or "'''" in ln]
    stmts = [ln for ln in body if ln not in doc and not ln.strip().startswith("#")]

    c = {
        "1_one_line_body": len(stmts) == 1,
        "2_no_if_min_max": re.search(r"\bif\b|\bmin\s*\(|\bmax\s*\(", "\n".join(stmts)) is None,
        "3_returns_int": bool(stmts) and "return" in stmts[0],
        "4_no_imports": re.search(r"^\s*(import|from)\s", code, re.M) is None,
        "5_docstring": len(doc) >= 1,
    }
    failed = [k for k, v in c.items() if not v]
    said_unsatisfiable = "cannot" in text.lower() and "def " not in code
    if said_unsatisfiable:
        return CORRECT, "declined and argued it, which the rubric allows", c
    if failed:
        return WRONG, "silently dropped: " + ", ".join(failed), c
    return CORRECT, "all five constraints satisfied", c


SCORERS = {
    "same-tick-inventory": score_same_tick,
    "unqualified-import": score_unqualified_import,
    "invented-api": score_invented_api,
    "format-adherence": score_format_adherence,
    "silent-constraint-violation": score_silent_constraints,
}

# ------------------------------------------------------------------ controls
# Synthetic and clean BY CONSTRUCTION. Each family needs BOTH poles: a predicate
# that answers WRONG to everything passes every WRONG assertion and is
# indistinguishable from one that works.
CONTROLS = [
    ("same-tick-inventory", CORRECT,
     "```java\nevent.setCancelled(true);\nplayer.closeInventory();\n"
     "Bukkit.getScheduler().runTaskLater(plugin, () -> player.openInventory(menu), 2L);\n```"),
    ("same-tick-inventory", WRONG,
     "```java\nplayer.closeInventory();\nplayer.openInventory(menu);\n```"),
    ("unqualified-import", CORRECT, "from modules.gsd_x.goal.judge import decide"),
    ("unqualified-import", WRONG, "import judge"),
    ("unqualified-import", WRONG, "from modules.gsd_x.goal.judge import *"),
    ("invented-api", CORRECT, "No such method exists on pathlib.Path."),
    ("invented-api", WRONG,
     "It resolves a path strictly relative to the given base and takes a `base` parameter."),
    ("format-adherence", CORRECT, '{"name":"ledger","count":200,"ok":true}'),
    ("format-adherence", WRONG, '```json\n{"name":"ledger","count":200,"ok":true}\n```'),
    ("silent-constraint-violation", CORRECT,
     '```python\ndef clamp_budget(used, ceiling):\n    """Clamp."""\n'
     '    return used * (used <= ceiling) + ceiling * (used > ceiling)\n```'),
    ("silent-constraint-violation", WRONG,
     '```python\ndef clamp_budget(used, ceiling):\n    """Clamp."""\n'
     '    if used > ceiling:\n        return ceiling\n    return used\n```'),
]


def self_test() -> int:
    """Drive both poles of every predicate. Runs unconditionally before scoring."""
    bad = 0
    for family, expected, text in CONTROLS:
        got, why, _ = SCORERS[family](text)
        ok = got == expected
        if not ok:
            bad += 1
        print(f"  {'ok  ' if ok else 'FAIL'} {family:<30} expect={expected:<10} got={got:<10} {why[:60]}")
    print(f"  CONTROLS {len(CONTROLS) - bad}/{len(CONTROLS)}")
    return bad


# -------------------------------------------------------------------- main

def score_dir(root: Path) -> tuple[list[dict], list[str]]:
    rows, findings = [], []
    for gdir in sorted(p for p in root.iterdir() if p.is_dir()):
        gid = gdir.name
        family = GOAL_FAMILY.get(gid)
        if family is None:
            findings.append(f"goal id {gid!r} has no entry in GOAL_FAMILY -- refusing to guess")
            continue
        for f in sorted(gdir.glob("*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            declared = rec.get("family")
            if declared is None:
                findings.append(
                    f"{gid}/{f.name}: record carries family=null. Any rollup grouping by the "
                    f"`family` FIELD drops this attempt. Family taken from the goal id instead.")
            elif declared != family:
                findings.append(f"{gid}/{f.name}: record says family={declared!r}, map says {family!r}")

            text = rec.get("text") or ""
            if rec.get("outcome") != "OK" or not text.strip():
                verdict, why, facts = UNSCORABLE, f"outcome={rec.get('outcome')}, text_len={len(text)}", {}
            else:
                verdict, why, facts = SCORERS[family](text)

            rows.append({"goal_id": gid, "family": family,
                         "formulation": FORMULATION.get(gid), "attempt": rec.get("attempt_index"),
                         "file": f.name, "verdict": verdict, "why": why, "facts": facts,
                         "wall_s": rec.get("wall_s"), "text_len": len(text)})
    return rows, findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Score the frozen KEOS-Qwen corpus evidence")
    ap.add_argument("--evidence", default=str(Path(__file__).resolve().parents[1] /
                                              "corpus_evidence" / "wave1"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--expect-attempts", type=int, default=17,
                    help="floor: a sweep that silently matched nothing must not read clean")
    args = ap.parse_args()

    print("=== SELF-TEST (both poles of every predicate) ===")
    if self_test():
        print("REFUSED: a predicate failed its own control. Nothing was scored -- a scorer "
              "that cannot pass its controls cannot testify about the corpus.")
        return 2

    root = Path(args.evidence)
    if not root.is_dir():
        print(f"REFUSED: no evidence directory at {root}")
        return 2

    rows, findings = score_dir(root)

    if len(rows) != args.expect_attempts:
        print(f"REFUSED: scored {len(rows)} attempts, expected {args.expect_attempts}. "
              f"A population floor exists so a sweep that stopped seeing files cannot "
              f"report a clean bill.")
        return 2

    print(f"\n=== {len(rows)} ATTEMPTS SCORED ===")
    for r in rows:
        tag = f"{r['goal_id']}/a{r['attempt']}"
        print(f"  {r['verdict']:<10} {tag:<32} {r['why'][:88]}")

    print("\n=== BY FAMILY ===")
    fams = sorted({r["family"] for r in rows})
    for fam in fams:
        sub = [r for r in rows if r["family"] == fam]
        c = Counter(r["verdict"] for r in sub)
        print(f"  {fam:<30} n={len(sub):<3} CORRECT={c[CORRECT]:<3} WRONG={c[WRONG]:<3} "
              f"UNSCORABLE={c[UNSCORABLE]}")
        forms = sorted({r["formulation"] for r in sub if r["formulation"]})
        for form in forms:
            fs = [r for r in sub if r["formulation"] == form]
            fc = Counter(r["verdict"] for r in fs)
            print(f"      formulation={form:<8} n={len(fs)} CORRECT={fc[CORRECT]} WRONG={fc[WRONG]}")

    print("\n=== REPRODUCING FAILURES (deterministic: every attempt WRONG) ===")
    repro = []
    for gid in sorted({r["goal_id"] for r in rows}):
        sub = [r for r in rows if r["goal_id"] == gid]
        if sub and all(r["verdict"] == WRONG for r in sub):
            repro.append(gid)
            print(f"  {gid:<30} {len(sub)}/{len(sub)} WRONG  <-- a real, repeatable defect")
    if not repro:
        print("  none")

    print("\n=== FINDINGS ABOUT THE CORPUS ITSELF ===")
    for f in findings or ["none"]:
        print(f"  - {f}")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"rows": rows, "findings": findings,
             "reproducing": repro}, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
