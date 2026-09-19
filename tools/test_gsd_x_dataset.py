#!/usr/bin/env python3
"""V-GSDX-DATASET-* -- the dataset cannot quietly become prose.

A corpus of claims is only worth more than a transcript if the epistemic state
is enforced. Left unchecked, every entry drifts toward OBSERVED, because that
is the state that needs no companion field and reads most confidently.

So each state owes a companion, and the companion is the falsifiable half:

    OBSERVED              evidence      -- the instrument, not just the verdict
    CONTRADICTED          contradicted_by
    DECISION              rationale
    NOT_BUILT_BY_DECISION revisit_when  -- decided against != forgotten
    UNPROVEN              resolved_by   -- names what would close it

Three outcomes, never two (instrument-before-claim): a gate that dies while
parsing must not be legible as a gate that found a bad dataset.

    python tools/test_gsd_x_dataset.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_DEFAULT = Path(__file__).resolve().parents[1] / "vault" / "datasets" / "gsd_x" / "claims.jsonl"
# The drill points this at a SYNTHETIC dataset. Pinning a red-branch drill to a
# real defect gives the drill an interest in that defect surviving, and it decays
# the day the defect is fixed.
DATASET = Path(os.environ.get("GSDX_DATASET") or _DEFAULT)

REQUIRED_COMPANION = {
    "OBSERVED": "evidence",
    "CONTRADICTED": "contradicted_by",
    "DECISION": "rationale",
    "NOT_BUILT_BY_DECISION": "revisit_when",
    "UNPROVEN": "resolved_by",
}
ALWAYS = ("id", "state", "claim", "date")

# Floor + positive control. An empty dataset must not pass as a clean one, and a
# reader that stopped reading must not pass as a dataset with nothing wrong.
MIN_CLAIMS = 20
POSITIVE_CONTROL = "GSDX-R08"   # the CONTRADICTED entry; if this is gone the
                                # corpus has started deleting its own mistakes

# V7-V10 need the real repository: blob SHAs, a commit range, git itself. The
# drill redirects DATASET at a synthetic corpus in a temp dir, which has none of
# those. Running them there would sweep the real repo's history while judging a
# fabricated claim set -- a verdict that is a function of whichever pane commits
# next. So they SKIP when the subject is not the real ledger, and the drill
# asserts exactly how many skipped, so the skip cannot silently become permanent.
SYNTHETIC = DATASET.resolve() != _DEFAULT.resolve()
REPO_GATES = ("V-GSDX-DATASET-DEPENDENCY", "V-GSDX-DATASET-COVERAGE")

# The one pre-existing supersedes edge points outside the claim id space, at a
# planning artifact that predates the corpus. It is grandfathered BY NAME so a
# new row cannot reuse the escape; a count would be satisfied by any single row.
LEGACY_SUPERSEDE_ESCAPE = {"GSDX-R03"}

# Shrink-only ratchet, frozen 2026-09-19 at 56 of 82 claims. New claims must pin
# their surfaces; these are the debt. The list may only get shorter, and an entry
# that has since been pinned must be DELETED from it -- a ratchet whose inventory
# can outlive its debts stops turning and becomes a permanent exemption.
UNPINNED_INVENTORY = frozenset({
    'GSDX-B05', 'GSDX-B06', 'GSDX-C01', 'GSDX-C02', 'GSDX-C05', 'GSDX-C06',
    'GSDX-C07', 'GSDX-C08', 'GSDX-C09', 'GSDX-C10', 'GSDX-C11', 'GSDX-C15',
    'GSDX-C16', 'GSDX-C18', 'GSDX-C19', 'GSDX-D01', 'GSDX-D02', 'GSDX-D03',
    'GSDX-D05', 'GSDX-D07', 'GSDX-D08', 'GSDX-F03', 'GSDX-F06', 'GSDX-I02',
    'GSDX-I03', 'GSDX-I05', 'GSDX-I06', 'GSDX-I07', 'GSDX-I08', 'GSDX-I09',
    'GSDX-I10', 'GSDX-I11', 'GSDX-N01', 'GSDX-N02', 'GSDX-N03', 'GSDX-N04',
    'GSDX-N05', 'GSDX-O01', 'GSDX-R01', 'GSDX-R02', 'GSDX-R03', 'GSDX-R06',
    'GSDX-R07', 'GSDX-R08', 'GSDX-R11', 'GSDX-R12', 'GSDX-R13', 'GSDX-R14',
    'GSDX-R15', 'GSDX-R16', 'GSDX-U01', 'GSDX-U02', 'GSDX-U04', 'GSDX-U05',
    'GSDX-U06', 'GSDX-U07',
})


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(gate: str, ev: str) -> None:
        passes.append(gate)
        print(f"  PASS {gate}: {ev}")

    def bad(gate: str, why: str) -> None:
        fails.append(gate)
        print(f"  FAIL {gate}: {why}")

    if not DATASET.is_file():
        print(f"INSTRUMENT_FAILED: no dataset at {DATASET}")
        return 2

    rows: list[dict] = []
    for n, line in enumerate(
        DATASET.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"INSTRUMENT_FAILED: line {n} is not JSON: {exc}")
            return 2

    print(f"# V-GSDX-DATASET  ({len(rows)} claims)\n")

    if len(rows) < MIN_CLAIMS:
        print(f"INSTRUMENT_FAILED: {len(rows)} claims, floor is {MIN_CLAIMS}")
        return 2
    ids = {r.get("id") for r in rows}
    if POSITIVE_CONTROL not in ids:
        print(
            f"INSTRUMENT_FAILED: positive control {POSITIVE_CONTROL} absent. "
            "That entry is the corpus's record of its own falsified claim; if it "
            "was deleted rather than marked, this gate is measuring a corpus that "
            "has started tidying away its mistakes."
        )
        return 2

    # V1 -- every claim carries the always-required fields
    missing = [
        f"{r.get('id', '?')}:{f}" for r in rows for f in ALWAYS if not r.get(f)
    ]
    if missing:
        bad("V-GSDX-DATASET-FIELDS", f"missing {missing[:6]}")
    else:
        ok("V-GSDX-DATASET-FIELDS", f"{len(rows)} claims carry {list(ALWAYS)}")

    # V2 -- the state vocabulary is closed
    unknown = sorted({r["state"] for r in rows if r["state"] not in REQUIRED_COMPANION})
    if unknown:
        bad("V-GSDX-DATASET-VOCAB", f"states outside the vocabulary: {unknown}")
    else:
        ok("V-GSDX-DATASET-VOCAB", f"states used: {sorted({r['state'] for r in rows})}")

    # V3 -- each state owes its companion field
    orphaned = [
        f"{r['id']} ({r['state']} needs {REQUIRED_COMPANION[r['state']]})"
        for r in rows
        if r["state"] in REQUIRED_COMPANION and not r.get(REQUIRED_COMPANION[r["state"]])
    ]
    if orphaned:
        bad("V-GSDX-DATASET-COMPANION", f"{orphaned}")
    else:
        ok("V-GSDX-DATASET-COMPANION", "every state carries its falsifiable half")

    # V4 -- zero inline code
    fenced = [r["id"] for r in rows if any("```" in str(v) for v in r.values())]
    if fenced:
        bad("V-GSDX-DATASET-NOCODE", f"code fence in {fenced}")
    else:
        ok("V-GSDX-DATASET-NOCODE", "no code fences; code lives in the repo")

    # V5 -- cross-references resolve, so a supersession cannot point at nothing
    dangling = [
        f"{r['id']}->{r[k]}"
        for r in rows
        for k in ("contradicted_by", "supersedes")
        if r.get(k) and r[k] not in ids and not str(r[k]).startswith("DATASET-")
    ]
    if dangling:
        bad("V-GSDX-DATASET-XREF", f"unresolved: {dangling}")
    else:
        ok("V-GSDX-DATASET-XREF", "every cross-reference resolves")

    # V6 -- the corpus still admits at least one thing it got wrong and one it
    # has not earned. A dataset with no CONTRADICTED and no UNPROVEN is not a
    # clean dataset, it is an unfalsifiable one.
    states = [r["state"] for r in rows]
    if "CONTRADICTED" not in states or "UNPROVEN" not in states:
        bad(
            "V-GSDX-DATASET-HONESTY",
            "no CONTRADICTED and/or no UNPROVEN entry -- a corpus that claims "
            "only successes has stopped recording",
        )
    else:
        ok(
            "V-GSDX-DATASET-HONESTY",
            f"{states.count('CONTRADICTED')} contradicted, "
            f"{states.count('UNPROVEN')} unproven",
        )

    skipped: list[str] = []

    def skip(gate: str, why: str) -> None:
        skipped.append(gate)
        print(f"  SKIP {gate}: {why}")

    # V7 -- a supersession names a claim that exists. The legacy escape is by
    # name, so it cannot be inherited.
    bad_target = [
        f"{r['id']}->{r['supersedes']}"
        for r in rows
        if r.get("supersedes")
        and r["supersedes"] not in ids
        and r["id"] not in LEGACY_SUPERSEDE_ESCAPE
    ]
    if bad_target:
        bad("V-GSDX-DATASET-SUPERSEDE-TARGET", f"points at nothing: {bad_target}")
    else:
        edges = sum(1 for r in rows if r.get("supersedes"))
        ok("V-GSDX-DATASET-SUPERSEDE-TARGET",
           f"{edges} supersedes edge(s), each resolving or grandfathered by name")

    # V8 -- supersession is a history, so it must not close into a loop. A cycle
    # makes "which claim is current" unanswerable, which is the whole question.
    succ = {r["id"]: r["supersedes"] for r in rows if r.get("supersedes")}
    cycles = []
    for start in succ:
        seen, cur = [], start
        while cur in succ and cur not in seen:
            seen.append(cur)
            cur = succ[cur]
        if cur in seen:
            cycles.append(" -> ".join(seen[seen.index(cur):] + [cur]))
    if cycles:
        bad("V-GSDX-DATASET-SUPERSEDE-CYCLE", f"{cycles}")
    else:
        ok("V-GSDX-DATASET-SUPERSEDE-CYCLE", "supersession is acyclic")

    # V9 -- the dependency ratchet. Two directions: new debt fails, and an
    # inventory entry that has since been pinned must be removed.
    if SYNTHETIC:
        skip("V-GSDX-DATASET-DEPENDENCY", "synthetic subject carries no repo surfaces")
    else:
        new_debt = sorted(
            r["id"] for r in rows
            if not r.get("depends_on") and r["id"] not in UNPINNED_INVENTORY
        )
        stale_entries = sorted(
            r["id"] for r in rows
            if r.get("depends_on") and r["id"] in UNPINNED_INVENTORY
        )
        if new_debt:
            bad("V-GSDX-DATASET-DEPENDENCY",
                f"new claims with no depends_on: {new_debt}")
        elif stale_entries:
            bad("V-GSDX-DATASET-DEPENDENCY",
                f"pinned but still in the frozen inventory, delete them: {stale_entries}")
        else:
            pinned = sum(1 for r in rows if r.get("depends_on"))
            ok("V-GSDX-DATASET-DEPENDENCY",
               f"{pinned} pinned, {len(UNPINNED_INVENTORY)} frozen, 0 new debt")

    # V10 -- material evidence exists that no claim covers. This is the class the
    # other six gates are structurally blind to: it fails by OMISSION, so nothing
    # is contradicted and every other clause stays green.
    if SYNTHETIC:
        skip("V-GSDX-DATASET-COVERAGE", "synthetic subject has no commit range")
    else:
        recon = Path(__file__).resolve().parent / "gsd_x_claim_reconcile.py"
        proc = subprocess.run(
            [sys.executable, str(recon)],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if proc.returncode == 2:
            print(f"INSTRUMENT_FAILED: reconciler could not judge: "
                  f"{proc.stdout.strip()[:200]}")
            return 2
        n = None
        for line in proc.stdout.splitlines():
            if "UNCOVERED_EVIDENCE" in line and ":" in line:
                n = int(line.rsplit(":", 1)[1].strip())
        if n is None:
            print("INSTRUMENT_FAILED: reconciler produced no UNCOVERED_EVIDENCE line")
            return 2
        if n:
            bad("V-GSDX-DATASET-COVERAGE",
                f"{n} material evidence event(s) no claim speaks about")
        else:
            ok("V-GSDX-DATASET-COVERAGE", "every material event is covered")

    for g in REPO_GATES:
        if g in skipped and not SYNTHETIC:
            print(f"INSTRUMENT_FAILED: {g} skipped against the real ledger")
            return 2

    total = len(passes) + len(fails)
    print(f"\nGSDX_DATASET_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


# --- Red-branch drill -------------------------------------------------------
# Both poles, against a synthetic subject. The green half matters as much as the
# red: a gate that flagged EVERYTHING would pass the red branch and look like a
# working detector.
_GOOD = [
    {"id": "SYN-1", "state": "OBSERVED", "claim": "x", "date": "2026-01-01",
     "evidence": "file:1"},
    {"id": "SYN-2", "state": "CONTRADICTED", "claim": "y", "date": "2026-01-01",
     "contradicted_by": "SYN-1"},
    {"id": "SYN-3", "state": "UNPROVEN", "claim": "z", "date": "2026-01-01",
     "resolved_by": "a run"},
]
# Each mutation removes exactly one thing the gate claims to require.
_MUTATIONS = {
    "companion-missing": lambda rs: [{k: v for k, v in r.items() if k != "evidence"}
                                     if r["state"] == "OBSERVED" else r for r in rs],
    "vocab-escape": lambda rs: [{**r, "state": "PROBABLY_FINE"}
                                if r["id"] == "SYN-1" else r for r in rs],
    "inline-code": lambda rs: [{**r, "claim": "see ```def f(): pass```"}
                               if r["id"] == "SYN-1" else r for r in rs],
    "dangling-xref": lambda rs: [{**r, "contradicted_by": "SYN-404"}
                                 if r["state"] == "CONTRADICTED" else r for r in rs],
    # Strip ONLY the two honesty states. Removing every non-OBSERVED row also
    # removes the positive control, and the run then dies as INSTRUMENT_FAILED
    # (2) before it ever reaches the honesty predicate -- scored here as a miss,
    # correctly: a gate that could not judge has not judged.
    "honesty-stripped": lambda rs: [
        r for r in rs if r["state"] not in ("CONTRADICTED", "UNPROVEN")
    ],
    # A supersession pointing at a claim that does not exist. SYN-1 is not in
    # LEGACY_SUPERSEDE_ESCAPE, so the grandfather clause cannot absorb it.
    "supersede-nowhere": lambda rs: [{**r, "supersedes": "SYN-404"}
                                     if r["id"] == "SYN-1" else r for r in rs],
    # The escape is by NAME, so a synthetic row must not inherit it.
    "supersede-escape-inherited": lambda rs: [
        {**r, "supersedes": "DATASET-ANYTHING"} if r["id"] == "SYN-1" else r
        for r in rs
    ],
    # Two rows superseding each other: "which is current" becomes unanswerable.
    "supersede-cycle": lambda rs: [
        {**r, "supersedes": "SYN-2"} if r["id"] == "SYN-1"
        else {**r, "supersedes": "SYN-1"} if r["id"] == "SYN-2"
        else r for r in rs
    ],
}


def _run_against(rows: list[dict], tmp: Path) -> int:
    tmp.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    env = {**os.environ, "GSDX_DATASET": str(tmp), "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env=env, capture_output=True, text=True,
    )
    return proc.returncode


def drill() -> int:
    # The floor and the positive control are instrument assertions, not subject
    # assertions, so the synthetic corpus must satisfy them or every drill run
    # would return INSTRUMENT_FAILED and prove nothing about the predicates.
    pad = [
        {"id": f"SYN-PAD-{i}", "state": "DECISION", "claim": "pad",
         "date": "2026-01-01", "rationale": "corpus floor"}
        for i in range(MIN_CLAIMS)
    ]
    control = [{"id": POSITIVE_CONTROL, "state": "DECISION", "claim": "control",
                "date": "2026-01-01", "rationale": "positive control"}]
    base = _GOOD + control + pad

    failures: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "synthetic.jsonl"

        rc = _run_against(base, tmp)
        if rc == 0:
            print("  PASS drill/green: an intact synthetic corpus is accepted")
        else:
            failures.append(f"green pole returned {rc}, expected 0")
            print(f"  FAIL drill/green: intact corpus rejected (rc={rc}) -- the "
                  "gate flags everything, so its red branch proves nothing")

        for name, mutate in _MUTATIONS.items():
            rc = _run_against(mutate(list(base)), tmp)
            if rc == 1:
                print(f"  PASS drill/{name}: caught")
            else:
                failures.append(f"{name} survived (rc={rc})")
                print(f"  FAIL drill/{name}: NOT caught (rc={rc})")

        # The two repo-backed gates MUST have skipped against the synthetic
        # subject. If they ran, the drill's verdict is a function of the real
        # repo's history and of whichever pane commits next, not of the mutation.
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve())],
            env={**os.environ, "GSDX_DATASET": str(tmp), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True,
        )
        n_skipped = proc.stdout.count("  SKIP ")
        if n_skipped == len(REPO_GATES):
            print(f"  PASS drill/skip-accounting: {n_skipped} repo gates skipped")
        else:
            failures.append(f"skip accounting: {n_skipped} skipped, "
                            f"expected {len(REPO_GATES)}")
            print(f"  FAIL drill/skip-accounting: {n_skipped} skipped, expected "
                  f"{len(REPO_GATES)} -- a repo gate is judging a synthetic corpus")

    total = len(_MUTATIONS) + 2
    print(f"\nGSDX_DATASET_DRILL={total - len(failures)}/{total}  "
          f"threshold={total}/{total}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(drill() if "--drill" in sys.argv[1:] else main())
