#!/usr/bin/env python3
"""Break each property the goal spine claims, and require the suite to go red.

    python tools/test_gsd_x_goal_mutation.py

Same contract as test_gsd_x_mission_mutation: anchors matched in the file's own
line endings, bytecode disabled, every restore verified by SHA-256, and outcomes
that are never collapsed -- a mutant whose anchor is missing is not a verdict.

Each mutant also names the gate that is SUPPOSED to catch it; the suite that owns
that gate is chosen from the gate's prefix. A mutant caught only by some other
gate is reported CAUGHT-ELSEWHERE and is not counted: a red for the wrong reason
says nothing about the property the mutant removed.

NOT a mutant here: removing the sequence-gap clause in `log.read()` is
EQUIVALENT. Any real gap also breaks the hash chain (the next event's
prev_digest names the missing event), so the chain clause raises anyway.
Measured 2026-09-22: that mutant SURVIVED with rc=0. The clause stays for its
clearer message and is not counted as a guarantee.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOAL = ROOT / "modules" / "gsd_x" / "goal"
LOG, CONTRACT, CONV = GOAL / "log.py", GOAL / "contract.py", GOAL / "convergence.py"
EPOCH = GOAL / "epoch.py"
GATEP = GOAL / "providers" / "gate.py"
LRP = GOAL / "providers" / "long_run.py"
CXP = GOAL / "providers" / "codex.py"
GITST = GOAL / "git_state.py"
STORE = ROOT / "modules" / "gsd_x" / "mission" / "store.py"
SUITES = {
    "V-GOAL-": ROOT / "tools" / "test_gsd_x_goal.py",
    "V-CONV-": ROOT / "tools" / "test_gsd_x_goal_convergence.py",
    "V-EP-": ROOT / "tools" / "test_gsd_x_goal_epoch.py",
    "V-GATE-": ROOT / "tools" / "test_gsd_x_goal_gate_provider.py",
    "V-LR-": ROOT / "tools" / "test_gsd_x_goal_long_run_provider.py",
    "V-CX-": ROOT / "tools" / "test_gsd_x_goal_codex_provider.py",
}

# name -> (file, old, new, property removed, gate that must go red)
MUTATIONS: dict[str, tuple[Path, str, str, str, str]] = {
    "link-becomes-overwrite": (
        LOG, "os.link(tmp, target)            # atomic",
        "os.replace(tmp, target)            # atomic",
        "two writers must not both publish the same sequence number",
        # Attributed to the DETERMINISTIC gate. The two-process race also goes
        # red under this mutant, but only when the two overlap; keying the drill
        # on it reported "caught" by luck (measured 2026-09-22).
        "V-GOAL-CAS-PUBLISH-ONCE"),
    "digest-unchecked": (
        LOG, 'if raw.get("digest") != event_digest(raw):', "if False:",
        "an edited past event must be detected", "V-GOAL-LOG-CHAIN"),
    "permission-is-a-win": (
        LOG, 'raise Inconclusive(f"{target}: sharing violation: {exc}") from exc', "pass",
        "a sharing violation must not be reported as a published event",
        "V-GOAL-CAS-PERMISSION"),
    "budget-moves-revision": (
        CONTRACT, "            st.budget = dict(ev.data)\n",
        "            st.budget = dict(ev.data)\n            st.revision = st.revision + 'b'\n",
        "a budget change must not mint a new revision", "V-GOAL-REV-BUDGET-NEUTRAL"),
    "store-ignores-binding": (
        STORE,
        "def save(root: Path, obligations: list[Obligation]) -> Path:\n    refuse_if_bound(root)\n",
        "def save(root: Path, obligations: list[Obligation]) -> Path:\n",
        "a goal-bound root must refuse per-root obligation writes", "V-GOAL-SINGLE-OWNER"),
    # --- convergence (C2/C3) ---
    "unknown-plane-passes": (
        CONV, "        if pstate == CANDIDATE:", "        if False:",
        "a plane nobody judged must block closure", "V-CONV-UNKNOWN-BLOCKS"),
    "reality-accepts-unit-test": (
        CONV, "if ob.plane in REALITY_PLANES and verdict.gate_class not in RUNTIME_GATE_CLASSES:",
        "if False:",
        "a unit test must not prove a REALITY obligation", "V-CONV-REALITY-NEEDS-RUNTIME"),
    "verdict-revision-ignored": (
        CONV, "    if verdict.revision != state.revision:", "    if False:",
        "a verdict about another revision must be refused", "V-CONV-VERDICT-REVISION"),
    "gate-pin-ignored": (
        CONV, "    if _pin(verdict.gate_pin) != _pin(ob.gate_pin):", "    if False:",
        "a gate changed since acceptance must not prove the pinned one", "V-CONV-GATE-PIN"),
    "obligation-revision-ignored": (
        CONV, "    if ob.revision != state.revision:", "    if False:",
        "an old-revision obligation must be carried before it is re-proven",
        "V-CONV-REVISION-NEEDS-CARRY"),
    "closure-tree-ignored": (
        CONV, '            if v.get("tree_hash") != tree_hash:', "            if False:",
        "evidence about another tree must not close this one", "V-CONV-CLOSE-AT-OTHER-TREE"),
    "open-epoch-ignored": (
        CONV, "    for ep in open_epochs or []:", "    for ep in []:",
        "an open epoch must block closure", "V-CONV-OPEN-EPOCH"),
    "failure-ignored": (
        CONV, '        if not f["disposition"]:', "        if False:",
        "an undispositioned failure must block closure", "V-CONV-FAILURE-BLOCKS"),
    "carry-keeps-old-proof": (
        CONV, "                if o.disposition == SATISFIED:      # its proof was about the old meaning\n"
              "                    o.disposition, o.verdict = ACCEPTED, None\n",
        "",
        "a carried obligation must be proven again under the new revision",
        "V-CONV-REVISION-CARRIED"),
    # --- epochs (C5) ---
    "retry-key-ignored": (
        EPOCH, "        if e.info_key == key and e.outcome in UNSUCCESSFUL:",
        "        if False:",
        "an attempt whose information key already failed must be refused",
        "V-EP-NO-BLIND-RETRY"),
    "recover-redispatches": (
        EPOCH, "    handle = provider.probe(e.identity)",
        "    handle = provider.dispatch(e.spec)",
        "recovery must probe the pre-minted identity, never dispatch again",
        "V-EP-RECOVER-LOST"),
    "receipt-duplicate-allowed": (
        EPOCH, "    if any(rid in x.receipts for x in eps.values()):", "    if False:",
        "a receipt must be ingested once", "V-EP-RECEIPT-DUPLICATE"),
    "receipt-revision-ignored": (
        EPOCH, "    if receipt.revision != e.revision:", "    if False:",
        "a receipt about another revision must be refused", "V-EP-RECEIPT-STALE-REVISION"),
    "scope-hash-whole-tree": (
        EPOCH, "        p = root / rel", "        p = root",
        "the scope hash must ignore changes outside the declared scope",
        "V-EP-SCOPE-IGNORES-OUTSIDE"),
    "provider-bound-unchecked": (
        EPOCH, "    if not (isinstance(p.wall_bound_s, (int, float)) and p.wall_bound_s > 0):",
        "    if False:",
        "a provider with no wall bound must be refused", "V-EP-PROVIDER-BOUND"),
    # --- gate provider (C6) ---
    "cancelled-gate-gets-a-verdict": (
        GATEP, "        if self._was_cancelled(handle):\n            rc = None\n", "",
        "a cancelled gate must not produce a verdict from its killer's exit code",
        "V-GATE-CANCELLED-NO-VERDICT"),
    "gate-class-inferred": (
        GATEP, 'if g.get("class") not in GATE_CLASSES:', "if False:",
        "the gate class must be declared, never guessed", "V-GATE-CLASS-DECLARED"),
    "dirty-tree-reads-as-commit": (
        GITST, "    if not _dirty(root, paths):\n        return f\"git:{oid}\"",
        "    if True:\n        return f\"git:{oid}\"",
        "an uncommitted scope must not borrow the commit's tree name",
        "V-GATE-TREE-DIRTY"),
    # --- long-run provider (C7) ---
    "halted-kind-collapsed": (
        LRP, 'outcome = STALE_REVISION if kind == "mission" else EXPIRED',
        "outcome = EXPIRED",
        "a stale mission and a spent budget are different endings",
        "V-LR-HALTED-MISSION"),
    "no-rows-is-lost": (
        LRP, 'return Observation(OBS_UNKNOWN, "", "no ledger rows for this session")',
        'return Observation(OBS_LOST, LOST, "no ledger rows for this session")',
        "a ledger we could not read must not end a live run",
        "V-LR-NO-ROWS-UNKNOWN"),
    "longrun-emits-verdict": (
        LRP, "                       failures=failures,",
        "                       failures=failures,\n"
        "                       verdicts=[{'gate': 'cpp-gsd-long', 'exit_status': 0,\n"
        "                                  'observed': 'the run ended'}],",
        "a run ending must not be evidence that anything was proven",
        "V-LR-HARVEST-NO-VERDICT"),
    # --- codex provider (C8), a SHARED account ---
    "codex-ignores-kill-switch": (
        CXP, "        why = self.disabled_reason()\n        if why:\n"
             "            raise EpochError(f\"codex is disabled: {why}\")\n", "",
        "the shared kill switch must stop a dispatch", "V-CX-KILL-FLAG"),
    "codex-ignores-daily-cap": (
        CXP, "        if used >= self.max_per_day:", "        if False:",
        "the Owner's daily cap must stop a dispatch", "V-CX-BUDGET-STOPS"),
    "codex-ignores-lock": (
        CXP, "        if not stale:", "        if False:",
        "two local epochs must not hold one account at once", "V-CX-LOCK"),
    "codex-ignores-rate-limit": (
        CXP, "            self.trip_cooldown()", "            pass",
        "a rate limit must write the shared cooldown", "V-CX-RATELIMIT-TRIPS-COOLDOWN"),
    "codex-emits-verdict": (
        CXP, "                       commits=commits, failures=failures,",
        "                       commits=commits, failures=failures,\n"
        "                       verdicts=[{'gate': 'codex', 'exit_status': 0,\n"
        "                                  'observed': 'codex said it worked'}],",
        "codex writing code must not be evidence that the work is right",
        "V-CX-NO-VERDICT"),
}


def suite_for(gate: str) -> Path:
    for prefix, suite in SUITES.items():
        if gate.startswith(prefix):
            return suite
    raise KeyError(f"no suite owns gate {gate}")


def main() -> int:
    targets = {m[0] for m in MUTATIONS.values()}
    for p in targets | set(SUITES.values()):
        if not p.is_file():
            print(f"INSTRUMENT_FAILED: missing {p}")
            return 2
    originals = {p: p.read_bytes() for p in targets}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in originals.items()}
    outcomes: dict[str, object] = {}
    try:
        for name, (path, old, new, prop, gate) in MUTATIONS.items():
            text = originals[path].decode("utf-8")
            if "\r\n" in text:
                old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
            if old not in text:
                outcomes[name] = ("ANCHOR NOT FOUND -- drill invalid, not a verdict", prop, gate)
                continue
            path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
            try:
                proc = subprocess.run([sys.executable, "-B", str(suite_for(gate))],
                                      capture_output=True, text=True, cwd=str(ROOT),
                                      timeout=300,
                                      env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                           "PYTHONDONTWRITEBYTECODE": "1"})
            finally:
                path.write_bytes(originals[path])
            failed = [ln.strip() for ln in proc.stdout.splitlines()
                      if ln.strip().startswith("FAIL")]
            outcomes[name] = ((proc.returncode, failed), prop, gate)
    finally:
        for p, b in originals.items():
            p.write_bytes(b)

    restored = all(hashlib.sha256(p.read_bytes()).hexdigest() == digests[p] for p in targets)
    print(f"restored (sha256, {len(targets)} file(s)): {restored}\n")
    if not restored:
        print("INSTRUMENT_FAILED: a mutated module was not restored")
        return 2
    caught = 0
    for name, (outcome, prop, gate) in outcomes.items():
        if isinstance(outcome, str):
            print(f"  INVALID   {name}: {outcome}")
            continue
        rc, failed = outcome
        names = [f.split(":")[0].replace("FAIL ", "") for f in failed]
        if rc != 0 and not failed:
            print(f"  CRASHED   {name}  rc={rc} with no failing gate -- mutant malformed")
        elif gate in names:
            caught += 1
            print(f"  CAUGHT  {name} by {gate}")
        elif failed:
            print(f"  CAUGHT-ELSEWHERE  {name}: expected {gate}, red: {names}")
        else:
            print(f"  SURVIVED  {name}  rc={rc}\n            property: {prop}")
    print(f"\nGSDX_GOAL_MUTATIONS_CAUGHT={caught}/{len(MUTATIONS)}  "
          f"threshold={len(MUTATIONS)}/{len(MUTATIONS)}")
    return 0 if caught == len(MUTATIONS) else 2


if __name__ == "__main__":
    sys.exit(main())
