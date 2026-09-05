#!/usr/bin/env python3
"""Two-way gate for the question_ref PRODUCER WIRING (sealed 2026-09-04).

THE GAP THIS CLOSES. `fd_07_flywheel.Deposit` has always carried a `question_ref`
field, documented as "per-question ROI", and `run_flywheel()` reads it off every
incoming finding. But no producer could ever SET it:

    stage_finding()            -- no such parameter
    Finding                    -- no such field
    FindingsBus.publish()      -- no such parameter
    publish_session_findings() -- forwarded topic/claim/evidence/sid/anchor only

Four hops, all silent. The only way to populate it was to hand `run_flywheel()` a
findings list directly -- the path its own docstring calls hermetic testing. So the
question "which frontier question paid for which work?" was answerable only from
synthetic input and never once from a session that actually ran. Capability built,
documented, and unwired end to end.

WHY THE THIRD GATE IS THE ONE THAT MATTERS. Threading a new field into a dedup'd
ledger is exactly how a metric gets inflated: if `question_ref` leaked into
`Finding.identity`, the SAME conclusion re-reached under a second question would
mint a SECOND deposit, and FDI -- which is a ratio over deposits -- would drift
without anyone touching the flywheel. A test that only proved "the field arrives"
would pass in that world too. So V-QREF-NO-INFLATION drives the adversarial case
directly.

Run:  python tools/test_question_ref_wiring.py
Exit: 0 = all gates pass, 1 = at least one failed.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.parallel_mesh import pm_03_bus as pm            # noqa: E402
from modules.fable_distillation import fd_07_flywheel as fd  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


QREF = "KSEIP_2000#area11.frontier01"


def main() -> int:
    print("V-QREF question_ref producer wiring -- two-way gate")

    with tempfile.TemporaryDirectory(prefix="qref_") as td:
        bus_dir = Path(td, "bus")
        fd_dir = Path(td, "fd")
        bus_dir.mkdir(parents=True, exist_ok=True)
        fd_dir.mkdir(parents=True, exist_ok=True)
        repo = "qref-test-repo"
        sid = "qref-sid"

        # -- 1. GREEN: a tagged finding survives stage -> drain -> bus ---------
        pm.stage_finding(repo, sid, "via-topology",
                         "Via lives on the backends and on neither the proxy nor the lobby",
                         evidence="component_registry.json 2026-08-20",
                         question_ref=QREF, state_dir=str(bus_dir))
        drained = pm.drain_staging_findings(repo, sid, state_dir=str(bus_dir))
        if drained != 1:
            _fail("V-QREF-DRAIN", f"expected 1 finding drained, got {drained}")
            return _report()

        loaded = pm.FindingsBus(state_dir=str(bus_dir)).load(repo)
        if loaded and getattr(loaded[0], "question_ref", "") == QREF:
            _ok("V-QREF-SURVIVES-BUS", f"bus record carries question_ref={QREF!r}")
        else:
            got = getattr(loaded[0], "question_ref", "<missing>") if loaded else "<no records>"
            _fail("V-QREF-SURVIVES-BUS",
                  f"question_ref lost crossing the bus (got {got!r}) -- the producer "
                  "hop is still broken")

        # -- 2. GREEN: it reaches the DEPOSIT, which is the point --------------
        res = fd.run_flywheel(repo, sid, findings=[
            {"topic": t.topic, "claim": t.claim, "evidence": t.evidence,
             "question_ref": t.question_ref} for t in loaded
        ], state_dir=str(fd_dir))
        deps = fd._load_deposits(repo, str(fd_dir))
        tagged = [d for d in deps if d.get("question_ref") == QREF]
        if tagged:
            _ok("V-QREF-REACHES-DEPOSIT",
                f"{len(tagged)} deposit(s) attribute their cost to {QREF}")
        else:
            _fail("V-QREF-REACHES-DEPOSIT",
                  f"no deposit carries question_ref (processed={res.processed}, "
                  f"deposits={len(deps)}) -- payback is still untraceable")

        # -- 3. RED/ADVERSARIAL: question_ref must NOT create a second deposit --
        # Same topic, same claim, DIFFERENT question. If identity absorbed
        # question_ref this would mint a duplicate and silently inflate FDI.
        f_a = pm.Finding(repo=repo, topic="x", claim="one and the same conclusion",
                         question_ref="Q-AAA")
        f_b = pm.Finding(repo=repo, topic="x", claim="one and the same conclusion",
                         question_ref="Q-BBB")
        if f_a.identity == f_b.identity:
            _ok("V-QREF-NO-INFLATION",
                "identity ignores question_ref -- a re-asked question cannot mint a "
                "duplicate deposit")
        else:
            _fail("V-QREF-NO-INFLATION",
                  "identity CHANGED with question_ref -- the same conclusion under two "
                  "questions now deposits twice, inflating FDI without touching the flywheel")

        # -- 4. RED/COMPAT: an untagged finding must still work, not crash -----
        sid2 = "qref-sid-untagged"
        pm.stage_finding(repo, sid2, "untagged-topic",
                         "a conclusion reached with no question attached",
                         state_dir=str(bus_dir))
        n2 = pm.drain_staging_findings(repo, sid2, state_dir=str(bus_dir))
        recs = pm.FindingsBus(state_dir=str(bus_dir)).load(repo)
        untagged = [r for r in recs if r.topic == "untagged-topic"]
        if n2 == 1 and untagged and untagged[0].question_ref == "":
            _ok("V-QREF-BACKCOMPAT",
                "an untagged finding stages, drains and loads with question_ref=''")
        else:
            _fail("V-QREF-BACKCOMPAT",
                  f"untagged path regressed (drained={n2}, found={len(untagged)})")

        # -- 5. RED/COMPAT: a bus line written BEFORE this field must still load
        legacy = {"repo": repo, "topic": "legacy", "claim": "written before the field existed",
                  "evidence": "", "sid": "old", "anchor": {"type": "none"}, "ts": "2026-01-01"}
        try:
            f_legacy = pm.Finding.from_json(legacy)
            if f_legacy.question_ref == "":
                _ok("V-QREF-LEGACY-LINE", "a pre-existing bus line still parses, defaulting to ''")
            else:
                _fail("V-QREF-LEGACY-LINE", f"unexpected value {f_legacy.question_ref!r}")
        except Exception as exc:  # noqa: BLE001
            _fail("V-QREF-LEGACY-LINE",
                  f"a bus line written before this change no longer parses: {exc}")

    return _report()


def _report() -> int:
    total = _passes + _fails
    print(f"\nQREF_WIRING_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
