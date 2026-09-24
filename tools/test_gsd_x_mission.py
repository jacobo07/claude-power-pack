#!/usr/bin/env python3
"""V-gates for the Mission Intelligence vertical.

The load-bearing gates here are the CONTROLS, not the recall number. Recall
against a holdout I also wrote is the weakest evidence in this file; an operator
set that fires correctly on a domain it was never written for, and stays silent
on a reality that supports nothing, is the evidence that these are rules rather
than a lookup table with a rule's name.

    python tools/test_gsd_x_mission.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.mission import closure as cl          # noqa: E402
from modules.gsd_x.mission import contract as mc         # noqa: E402
from modules.gsd_x.mission import obligation as ob       # noqa: E402
from modules.gsd_x.mission import store as st            # noqa: E402

BENCH = ROOT / "vault" / "benchmarks" / "mission_spine"
FIXTURE = BENCH / "fixture"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these

# The sealed blob ids, copied from HOLDOUT-SEALED.md. If the fixture is edited
# after sealing, these stop matching -- which is the point of sealing it.
SEALED = {
    "INTENT.txt": "65b00c071929566fc8d00a7b4739b9a4d97403c7",
    "README.md": "b85af349928ff6f7b5bb1ac1e4362e9bae1163e7",
    "probe_env.py": "35e1a7d399855143ee8176832e7713da17987b4f",
}

# The holdout's expected material obligations, by the operator that should find
# each. Written here from the SEALED file, which was committed before any
# operator existed.
EXPECTED_OPERATORS = {
    "IRREVERSIBILITY_CONSEQUENCE",
    "ABSENT_SIGNAL_CONSEQUENCE",
    "FAILURE_CONSEQUENCE",
}

# --- transfer fixture -------------------------------------------------------
# A different domain, different nouns, different verbs, written to carry the
# same STRUCTURAL facts. If the operators are rules they fire here; if they were
# fitted to the uploader they do not.
TRANSFER_INTENT = (
    "Add a command that copies each finished batch into the archive database "
    "and then drops the staging rows so staging does not grow without bound."
)
TRANSFER_REALITY = """
# nightly-etl

Runs unattended on a scheduler; nobody logs into the host.

The upstream loader is written to by a partner feed, continuously, while a batch
is in flight. It is a third-party process and emits no completion signal.

The archive database has point-in-time recovery disabled and lifecycle rules:
none. The reconciliation report lists the archive every morning and treats every
batch present as a complete batch.

Staging is capped at 50 GB and fills in about 2 days at current volume.

The link to the archive host drops: 2 to 5 outages per week by the scheduler's
own logs, most under two minutes.
"""

# A THIRD domain, written AFTER the generalisation. Domain 2 above caught the
# operators fitted to the fixture's phrasing and therefore INFORMED the fix, so
# it is no longer clean evidence for the two operators it caught. This one is
# the re-test. It is still a phrasing I wrote, so the honest claim is "these
# rules survive three independent wordings", never "these rules generalise".
THIRD_INTENT = (
    "Build a worker that publishes each completed render to the CDN and "
    "afterwards purges it from the scratch volume."
)
THIRD_REALITY = """
# render-farm publisher

No operator watches this; it is restarted by nobody.

Frames are written by the renderer, continuously, for the duration of a job.
The renderer is closed-source and sends no done marker of any kind.

The CDN origin bucket has versioning disabled and no backups.

The playlist service lists the origin hourly and treats every asset present as
a complete render.

Scratch is capped at 4 TB and fills up in about 36 hours.

Uplink failures: the egress path recorded 7 disconnects last month.
"""

# A reality supporting NOTHING. A detector that fires here detects nothing
# anywhere, and its silence is what makes its speech worth reading.
NULL_INTENT = "Add a --verbose flag to the report command."
NULL_REALITY = """
# report-tool

A small command-line report generator. It reads a CSV and prints a table.
It writes nothing and talks to no network service.
"""

# Destructive act, but the reality DOES offer recovery. DO-1 must not fire:
# the consequence it names does not exist here.
SAFE_INTENT = "Write a job that archives each file to the vault and then deletes the local copy."
SAFE_REALITY = """
# archiver

The vault keeps every version forever and restores on request; backups run
hourly and are verified. Nothing else is notable about this host.
"""


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    print("# V-GSDX-MISSION\n")

    intent = (FIXTURE / "INTENT.txt").read_text(encoding="utf-8-sig")
    reality = (FIXTURE / "README.md").read_text(encoding="utf-8-sig")

    # --- V1 the seal ---------------------------------------------------------
    drift = []
    for name, want in SEALED.items():
        p = subprocess.run([GIT, "-C", str(ROOT), "hash-object",
                            str((FIXTURE / name).relative_to(ROOT)).replace("\\", "/")],
                           capture_output=True, text=True)
        got = p.stdout.strip()
        if got != want:
            drift.append(f"{name}: {got[:7]} != sealed {want[:7]}")
    if not drift:
        ok("V-MISSION-SEAL-INTACT",
           f"{len(SEALED)} fixture file(s) match the ids sealed before any operator existed")
    else:
        bad("V-MISSION-SEAL-INTACT",
            f"the holdout fixture changed after sealing: {drift} -- recall measured "
            "against an edited fixture is not recall")

    # --- V2 recall against the sealed holdout --------------------------------
    cands, facts = ob.derive(intent, reality)
    judged = [ob.judge(c) for c in cands]
    got_ops = {o.operator for o in judged if o.is_accepted}
    missing = EXPECTED_OPERATORS - got_ops
    if not missing:
        ok("V-MISSION-RECALL",
           f"{len(got_ops)}/{len(EXPECTED_OPERATORS)} expected material obligations derived "
           f"from {len(facts)} extracted facts")
    else:
        bad("V-MISSION-RECALL", f"not derived: {sorted(missing)}")

    # --- V3 NEGATIVE CONTROL -------------------------------------------------
    null_c, null_f = ob.derive(NULL_INTENT, NULL_REALITY)
    if not null_c:
        ok("V-MISSION-NEGATIVE-CONTROL",
           f"a reality supporting nothing produced 0 obligations ({len(null_f)} facts)")
    else:
        bad("V-MISSION-NEGATIVE-CONTROL",
            f"fired on a null reality: {[c.operator for c in null_c]} -- a detector "
            "that speaks everywhere says nothing anywhere")

    # --- V4 TRANSFER ---------------------------------------------------------
    # The decisive one. Different domain, never seen by the operators.
    t_c, t_f = ob.derive(TRANSFER_INTENT, TRANSFER_REALITY)
    t_ops = {ob.judge(c).operator for c in t_c}
    t_missing = EXPECTED_OPERATORS - t_ops
    if not t_missing:
        ok("V-MISSION-TRANSFER",
           f"all {len(EXPECTED_OPERATORS)} operators fired on an unseen domain "
           f"({len(t_f)} facts). This domain FAILED on its first run and is what "
           "caught the patterns fitted to the fixture's phrasing, so it informed "
           "the fix and is no longer clean evidence -- V-MISSION-TRANSFER-THIRD "
           "is the re-test")
    else:
        bad("V-MISSION-TRANSFER",
            f"did not transfer: {sorted(t_missing)} -- these operators are fitted to "
            "the fixture they were written against")

    # --- V4b TRANSFER to a domain written after the fix ----------------------
    u_c, u_f = ob.derive(THIRD_INTENT, THIRD_REALITY)
    u_ops = {ob.judge(c).operator for c in u_c}
    u_missing = EXPECTED_OPERATORS - u_ops
    if not u_missing:
        ok("V-MISSION-TRANSFER-THIRD",
           f"all {len(EXPECTED_OPERATORS)} operators fired on a third wording "
           f"({len(u_f)} facts) -- but domain 2 cost two pattern corrections and "
           "domain 3 cost one more verb, so the demonstrated property is 'survives "
           "three wordings after three corrections', NOT 'generalises'")
    else:
        bad("V-MISSION-TRANSFER-THIRD",
            f"did not transfer to the third domain: {sorted(u_missing)}")

    # --- V5 PARTIAL TRANSFER -------------------------------------------------
    # A destructive act whose consequence does not exist here. Firing anyway is
    # a false positive, and a false positive is what a feature-inflation engine
    # is made of.
    s_c, _ = ob.derive(SAFE_INTENT, SAFE_REALITY)
    s_ops = {c.operator for c in s_c}
    if "IRREVERSIBILITY_CONSEQUENCE" not in s_ops:
        ok("V-MISSION-NO-FALSE-POSITIVE",
           "a destructive act with a recovery path did not raise an irreversibility "
           f"obligation (fired: {sorted(s_ops) or 'nothing'})")
    else:
        bad("V-MISSION-NO-FALSE-POSITIVE",
            "raised an irreversibility obligation against a reality that recovers")

    # --- V6 candidate is not authority ---------------------------------------
    red = {
        "no consequence": ob.Obligation("X1", "t", "OP", ["p"], "",
                                        evidence=["e"], closure_condition="c"),
        "no evidence": ob.Obligation("X2", "t", "OP", ["p"], "c",
                                     evidence=[], closure_condition="c"),
        "no closure": ob.Obligation("X3", "t", "OP", ["p"], "c",
                                    evidence=["e"], closure_condition=""),
    }
    wrong = [k for k, o in red.items() if ob.judge(o).disposition == ob.ACCEPTED]
    distinct = {ob.judge(o).disposition for o in red.values()}
    if not wrong and len(distinct) >= 2:
        ok("V-MISSION-CANDIDATE-NOT-AUTHORITY",
           f"three deficient candidates refused, in {len(distinct)} distinct "
           f"dispositions: {sorted(distinct)}")
    else:
        bad("V-MISSION-CANDIDATE-NOT-AUTHORITY",
            f"accepted: {wrong}; dispositions collapsed to {sorted(distinct)}")

    # --- V7 narrative is not authority ---------------------------------------
    # The parent carries the `fact:` prefix deliberately: that prefix IS the
    # invalidation contract, and the first version of this test used a bare name,
    # so V-MISSION-STALE-PARENT failed against correct code. A test that cannot
    # reach the branch it names is measuring nothing.
    live = ob.judge(ob.Obligation("N1", "t", "OP", ["fact:p"], "c", evidence=["e"],
                                  closure_condition="c", done_gate="a real gate"))
    r_narr = cl.evaluate_transition(
        live, None, narrative="I have completed this work and verified it thoroughly.")
    if r_narr.outcome == cl.REFUSED and "not evidence" in r_narr.reason:
        ok("V-MISSION-NARRATIVE-REFUSED",
           "an executor's own account of completion did not move the obligation")
    else:
        bad("V-MISSION-NARRATIVE-REFUSED",
            f"narrative produced {r_narr.outcome}: {r_narr.reason}")

    # --- V8 a failed gate refuses, for a DIFFERENT reason --------------------
    r_fail = cl.evaluate_transition(live, cl.Verdict("pytest", 1, "2 failed"))
    if r_fail.outcome == cl.REFUSED and r_fail.reason != r_narr.reason:
        ok("V-MISSION-FAILED-GATE-REFUSED",
           "a gate that ran and failed refuses with its own reason, not the "
           "no-evidence one")
    else:
        bad("V-MISSION-FAILED-GATE-REFUSED",
            f"{r_fail.outcome}; reason indistinguishable from missing evidence")

    # --- V9 no done gate is UNJUDGEABLE, a third outcome ---------------------
    nogate = ob.judge(ob.Obligation("N2", "t", "OP", ["p"], "c", evidence=["e"],
                                    closure_condition="c", done_gate=""))
    r_uj = cl.evaluate_transition(nogate, cl.Verdict("pytest", 0, "ok"))
    if r_uj.outcome == cl.UNJUDGEABLE:
        ok("V-MISSION-THREE-OUTCOMES",
           "an obligation naming no gate is UNJUDGEABLE, never a pass or a refusal")
    else:
        bad("V-MISSION-THREE-OUTCOMES", f"got {r_uj.outcome}")

    # --- V10 valid proof allows ----------------------------------------------
    sat, r_ok = cl.satisfy(live, cl.Verdict("pytest", 0, "12 passed"))
    if r_ok.allowed and sat.disposition == ob.SATISFIED:
        ok("V-MISSION-VALID-PROOF-ALLOWED", f"{r_ok.reason[:70]}")
    else:
        bad("V-MISSION-VALID-PROOF-ALLOWED", f"{r_ok.outcome}: {r_ok.reason}")

    # --- V11 a stale parent invalidates, even from SATISFIED -----------------
    aged = ob.invalidate_if_parent_gone(sat, [])          # no facts hold any more
    if aged.disposition == ob.STALE:
        ok("V-MISSION-STALE-PARENT",
           "a satisfied obligation whose causal parent stopped holding went STALE")
    else:
        bad("V-MISSION-STALE-PARENT",
            f"stayed {aged.disposition} by inertia after its parent went away")

    # --- V12 false DONE: backlog empty, mission denied ------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "INTENT.txt").write_text(intent, encoding="utf-8")
        (root / "README.md").write_text(reality, encoding="utf-8")
        fresh = [ob.judge(c) for c in ob.derive(intent, reality)[0]]
        st.save(root, fresh)
        contract = mc.project(root, intent=intent.strip(), obligations=fresh)
        denied = cl.project_closure(contract, fresh, explicit_backlog_empty=True)
        if not denied.may_close and denied.blocking:
            ok("V-MISSION-FALSE-DONE",
               f"explicit backlog empty and closure DENIED on {len(denied.blocking)} "
               "derived obligation(s)")
        else:
            bad("V-MISSION-FALSE-DONE",
                "an empty explicit backlog closed a mission with open derived work")

        # --- V13 and it closes once they are honestly resolved ---------------
        for o in fresh:
            cl.satisfy(o, cl.Verdict("bench", 0, "observed"))
        allowed = cl.project_closure(contract, fresh, explicit_backlog_empty=True,
                                     production_reality="FIRST_VERTICAL_SLICE")
        if allowed.may_close:
            ok("V-MISSION-CLOSURE-REACHABLE",
               "with every derived obligation proven, closure proceeds -- the gate "
               "refuses, it does not merely never pass")
        else:
            bad("V-MISSION-CLOSURE-REACHABLE",
                f"still blocked with everything satisfied: {allowed.blocking}")

        # --- V14 the receipt separates explicit from derived ------------------
        verbatim = " ".join(intent.split())
        if (allowed.explicit_requirements == [verbatim]
                and allowed.derived_accepted
                and verbatim not in json.dumps(allowed.derived_accepted)):
            ok("V-MISSION-EXPLICIT-VS-DERIVED",
               "the human's sentence is carried verbatim and is not mixed into the "
               "derived set")
        else:
            bad("V-MISSION-EXPLICIT-VS-DERIVED",
                "the receipt cannot distinguish what was asked for from what was derived")

        # --- V15 the store is mission-scoped, and nothing global appeared -----
        p = st.store_path(root)
        stray = [q for q in root.rglob("*") if q.is_file()
                 and q not in {p, root / "INTENT.txt", root / "README.md"}]
        if p.is_file() and not stray:
            ok("V-MISSION-NO-NEW-STORE",
               f"one file under the mission root ({p.name}); no database, no registry")
        else:
            bad("V-MISSION-NO-NEW-STORE", f"unexpected artifacts: {[s.name for s in stray]}")

    # --- V16 the derivation path cannot read the holdout ---------------------
    srcs = list((ROOT / "modules" / "gsd_x" / "mission").glob("*.py"))
    srcs.append(ROOT / "tools" / "gsd_x_mission.py")
    leaks = [s.name for s in srcs
             if "HOLDOUT" in s.read_text(encoding="utf-8-sig", errors="replace")]
    if not leaks:
        ok("V-MISSION-HOLDOUT-UNREAD",
           f"{len(srcs)} derivation source(s) contain no reference to the sealed "
           "label set")
    else:
        bad("V-MISSION-HOLDOUT-UNREAD", f"the derivation path names the holdout: {leaks}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_MISSION_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
