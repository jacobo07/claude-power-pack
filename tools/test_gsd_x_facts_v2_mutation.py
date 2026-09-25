"""Mutation drill for test_gsd_x_facts_v2.py (GSDX-M05).

Each mutant removes one semantic the v2 gate claims to protect. It is CAUGHT
only if the gate exits 1 AND the gate named for that semantic is among the
failures; a red for some other reason is scored as a survival, because a test
that goes red for the wrong reason is not evidence about the thing it names.

Two mutants here are DELIBERATELY aimed at the gate's own permissiveness rather
than at its strictness -- `relevance-filter-removed` and
`blindness-from-aggregate` make the system block MORE, and they must still be
caught. A drill that only ever loosens the subject cannot detect a gate that has
started refusing everything, and a gate that refuses everything passes every
refusal assertion in the suite it guards.

Mutation is textual and in place, inside try/finally. Every file is hashed
before and the drill fails as HARNESS if any restore does not reproduce the
original bytes. An unmutated control runs first so a broken harness cannot
manufacture catches. Anchors are translated to each file's own line-ending
convention: `core.autocrlf` is true on this host, so a file clean from checkout
is CRLF while a dirty one keeps its writer's LF, and an anchor written with \\n
would silently match 0x and report HARNESS instead of a verdict.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "test_gsd_x_facts_v2.py"
SF = REPO / "modules" / "gsd_x" / "mission" / "structured_facts.py"
CL = REPO / "modules" / "gsd_x" / "mission" / "closure.py"
CLI = REPO / "tools" / "gsd_x_mission.py"

# (name, file, exact old text, replacement, gate that must go red)
MUTANTS = [
    # The blindness never leaves the document: _blindness reports nothing.
    ("blindness-always-empty", CLI,
     "    if sf.source_of(root) != sf.SOURCE:\n",
     "    if True:\n",
     "V-FACTSV2-UNKNOWN-GATING-BLOCKS"),
    # The closure is never told: the projection falls back to UNMEASURED.
    ("blindness-not-passed-to-closure", CLI,
     "    return cl.project_closure(contract, obs, backlog_empty, pr,\n"
     "                              blindness=_blindness(root)), obs",
     "    return cl.project_closure(contract, obs, backlog_empty, pr), obs",
     "V-FACTSV2-UNKNOWN-GATING-BLOCKS"),
    # The exit code reverts to the open set alone -- the twice-burned predicate
    # this wave widened. The receipt would still SAY it, and the gate would pass.
    ("exit-code-ignores-blindness", CLI,
     '    return 1 if (payload["open_obligations"] or blind_block) else 0',
     '    return 1 if payload["open_obligations"] else 0',
     "V-FACTSV2-UNKNOWN-GATING-BLOCKS"),
    # Every read counts as gating: an enriching unknown and an orphan unknown
    # start holding waves. This mutant makes the system STRICTER and must still
    # be caught, or "blocks too much" is invisible to this drill.
    ("relevance-filter-removed", CLI,
     "    g, e = ob.GATING_FACT_NAMES, ob.ENRICHING_FACT_NAMES\n",
     "    g, e = ob.FACT_NAMES, frozenset()\n",
     "V-FACTSV2-UNKNOWN-ENRICHING-DISCLOSED-NOT-BLOCKING"),
    # Freshness read from the one-word aggregate instead of per-entry rows: an
    # empty but well-formed document answers UNKNOWN and holds every wave.
    ("blindness-from-aggregate", CLI,
     "    not_current = {r.get(\"name\") for r in rows\n"
     "                   if r.get(\"verdict\") in (sf.STALE, sf.UNKNOWN)} - unknown",
     "    not_current = (set(ob.GATING_FACT_NAMES)\n"
     "                   if sf.freshness_verdict(rows) != sf.FRESH else set()) - unknown",
     "V-FACTSV2-GREEN-EMPTY-DOCUMENT"),
    # A v2 document may omit `state`: the richer document silently means as
    # little as a v1 one, which is what the old hard refusal existed to prevent.
    ("v2-state-not-required", SF,
     "    if not isinstance(state, str) or not state.strip():\n",
     "    if False:\n",
     "V-FACTSV2-REFUSE-NO-STATE"),
    # One name in two buckets stops being a contradiction.
    ("cross-bucket-allowed", SF,
     "        prior = seen.get(name)\n",
     "        prior = None\n",
     "V-FACTSV2-REFUSE-CROSS-BUCKET"),
    # A held entry may carry state UNKNOWN: a fact that could not be measured
    # is readmitted as one that holds.
    ("held-unknown-allowed", SF,
     "        if state == UNKNOWN:\n",
     "        if False:\n",
     "V-FACTSV2-REFUSE-HELD-UNKNOWN"),
    # A receipt can no longer tell measured-empty from never-measured.
    ("unmeasured-collapses-to-measured", CL,
     '    source: str = UNMEASURED\n',
     '    source: str = "structured"\n',
     "V-FACTSV2-MEASURED-EMPTY-IS-NOT-UNMEASURED"),
    # Blindness computes correctly and then declines to act: `blocks` is the
    # single predicate the gate's exit code consults, and a receipt that still
    # PRINTS the unknown fact while never blocking on it is the most plausible
    # way this could be wrong without looking wrong.
    ("blindness-never-blocks", CL,
     "    @property\n    def blocks(self) -> bool:\n"
     "        return bool(self.gating_unknown or self.gating_stale)",
     "    @property\n    def blocks(self) -> bool:\n        return False",
     "V-FACTSV2-UNKNOWN-GATING-BLOCKS"),
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_gate() -> tuple[int, list[str]]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True,
                       encoding="utf-8", timeout=600)
    failed = [ln.split()[1].rstrip(":") for ln in r.stdout.splitlines()
              if ln.strip().startswith("FAIL ")]
    return r.returncode, failed


def main() -> int:
    files = {SF, CL, CLI}
    before = {p: _sha(p) for p in files}

    code, failed = _run_gate()
    if code != 0:
        print(f"HARNESS-FAILED: unmutated gate is not green (exit {code}, failed={failed})")
        print("GSDX_FACTSV2_MUTATIONS_CAUGHT=0/0  threshold=HARNESS")
        return 2
    print("  CONTROL unmutated: exit 0")

    caught = 0
    for name, path, old, new, must in MUTANTS:
        original = path.read_bytes()
        text = original.decode("utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        old_a, new_a = old.replace("\n", nl), new.replace("\n", nl)
        if text.count(old_a) != 1:
            print(f"HARNESS-FAILED: mutant {name!r} anchor found "
                  f"{text.count(old_a)}x in {path.name}")
            return 2
        try:
            path.write_bytes(text.replace(old_a, new_a).encode("utf-8"))
            code, failed = _run_gate()
        finally:
            path.write_bytes(original)
        hit = code == 1 and must in failed
        caught += hit
        print(f"  {'CAUGHT' if hit else 'SURVIVED':8} {name:34} expected {must}  "
              f"exit={code} failed={failed}")

    after = {p: _sha(p) for p in files}
    moved = [p.name for p in files if before[p] != after[p]]
    if moved:
        print(f"HARNESS-FAILED: restore did not reproduce original bytes for {moved}")
        return 2
    print(f"  restore verified by sha256 for {sorted(p.name for p in files)}")

    print(f"\nGSDX_FACTSV2_MUTATIONS_CAUGHT={caught}/{len(MUTANTS)}  "
          f"threshold={len(MUTANTS)}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
