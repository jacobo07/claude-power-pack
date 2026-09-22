"""Closes PR-W10-11.

W10 computed a population fingerprint and printed it. Nothing ever compared two,
so the guard that makes `control vs treatment` mean anything had never run -- the
debt register recorded it as PARTIAL for exactly that reason.

A printed fingerprint and an enforced one are indistinguishable from the report,
which is why this is driven rather than read. Both poles, on the real canonical
store as well as on fixtures, and through the CLI so the event is proven and not
only the predicate.
"""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

import ucr_cif_oracle as O  # noqa: E402

STORE = _ROOT / "vault" / "ucr_cif" / "oracle_cases.json"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate:<42} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate:<42} {diagnostic}")


def _check(gate: str, cond: bool, evidence: str, diagnostic: str = "") -> None:
    if cond:
        _ok(gate, evidence)
    else:
        _fail(gate, diagnostic or evidence)


def _real_fingerprint():
    if not STORE.is_file():
        return None
    try:
        return json.loads(STORE.read_text(encoding="utf-8")).get("fingerprint")
    except (OSError, ValueError):
        return None


def main() -> int:
    print("-- PR-W10-11  population fingerprint, driven")

    fp = _real_fingerprint()
    # A drill whose subject could not be loaded has not observed anything. This
    # is a precondition failure, never a finding about the guard.
    if not isinstance(fp, dict):
        print("  HARNESS-FAILED  the canonical store carries no readable "
              "fingerprint; nothing was measured")
        return 2

    # GREEN POLE -- the real population against itself.
    same = O.compare_fingerprints(fp, copy.deepcopy(fp))
    _check("V-W11-FP-IDENTICAL-IS-COMPARABLE",
           same["status"] == O.FP_COMPARABLE and O.paired_verdict_allowed(same),
           f"the real {fp['cases']}-case population compares to itself as "
           f"COMPARABLE, so the guard can return the licensing answer at all",
           f"the real store refuses itself: {same}")

    # RED POLE -- a second, deliberately drifted population. One case removed is
    # the smallest honest drift: the corpus id, the ledger and the window all
    # still agree, so only `case_set_sha` and `cases` may move.
    drifted = copy.deepcopy(fp)
    drifted["cases"] = fp["cases"] - 1
    drifted["case_set_sha"] = "0" * 16
    got = O.compare_fingerprints(fp, drifted)
    _check("V-W11-FP-DRIFT-IS-CAUGHT",
           got["status"] == O.FP_DRIFTED and not O.paired_verdict_allowed(got),
           f"dropping one case from the real population is refused: "
           f"{got['status']}, and no paired verdict is licensed",
           f"a drifted population was accepted: {got}")

    _check("V-W11-FP-NAMES-WHAT-MOVED",
           set(got["moved"]) == {"cases", "case_set_sha"}
           and got["detail"]["cases"] == (fp["cases"], fp["cases"] - 1),
           f"the refusal names the keys that moved -- {got['moved']} -- rather "
           f"than reporting a bare difference nobody can act on",
           f"moved set was {got['moved']}")

    # Every key is load-bearing: a guard that only watched the case set would
    # accept two arms run against different ledgers or a different cap.
    #
    # The expected set is spelled out HERE rather than read from the module. A
    # loop over `O._FP_KEYS` would shrink along with any mutation that narrows
    # it, so the drill would inherit the very assumption it exists to test and
    # report a clean green over a guard watching one field.
    EXPECT_KEYS = ("oracle_schema", "corpus_id", "ledger_rows",
                   "owner_universe_n", "owner_universe_sha", "case_set_sha",
                   "cases", "sessions_swept", "window_hours", "max_owners")
    _check("V-W11-FP-WATCHED-SET-IS-PINNED",
           tuple(O._FP_KEYS) == EXPECT_KEYS,
           f"the guard watches exactly the {len(EXPECT_KEYS)} keys this drill "
           f"names, so narrowing the watched set is a diff and not a silent "
           f"weakening",
           f"watched set drifted to {tuple(O._FP_KEYS)}")

    missed = []
    for k in EXPECT_KEYS:
        probe = copy.deepcopy(fp)
        if k not in probe:
            missed.append(k)
            continue
        probe[k] = fp[k] + 7 if isinstance(fp[k], int) else "DRIFTED-SENTINEL"
        if O.compare_fingerprints(fp, probe)["status"] != O.FP_DRIFTED:
            missed.append(k)
    _check("V-W11-FP-EVERY-KEY-IS-LOAD-BEARING",
           not missed,
           f"all {len(EXPECT_KEYS)} fingerprint keys independently trigger "
           f"refusal, including max_owners and corpus_id",
           f"these keys can move without being noticed: {missed}")

    # ABSENCE -- the one that fails open if it is got wrong.
    for label, absent in (("none", None), ("not-a-dict", "fingerprint"),
                          ("empty", {})):
        res = O.compare_fingerprints(fp, absent)
        _check(f"V-W11-FP-ABSENT-IS-REFUSAL[{label}]",
               res["status"] == O.FP_UNREADABLE
               and not O.paired_verdict_allowed(res),
               f"a {label} fingerprint is UNREADABLE, never COMPARABLE -- "
               f"absence of evidence about drift is not evidence of no drift",
               f"a {label} fingerprint returned {res['status']}")

    partial = {k: fp[k] for k in list(O._FP_KEYS)[:-1]}
    res = O.compare_fingerprints(fp, partial)
    _check("V-W11-FP-PARTIAL-KEYS-IS-REFUSAL",
           res["status"] == O.FP_UNREADABLE,
           "a fingerprint missing one required key is UNREADABLE rather than "
           "silently compared on the keys that happen to be present",
           f"a partial fingerprint returned {res['status']}")

    # The licence is a POSITIVE test. A negative one would admit every status
    # added after today without anybody revisiting this line.
    _check("V-W11-FP-LICENCE-IS-A-POSITIVE-TEST",
           not O.paired_verdict_allowed({"status": "SOME-FUTURE-STATUS"})
           and not O.paired_verdict_allowed({})
           and not O.paired_verdict_allowed(None),
           "an unnamed future status does not license a paired verdict, so the "
           "guard cannot be widened by adding a status elsewhere",
           "an unknown status licensed a paired verdict")

    # EVENT, not predicate: drive the real CLI over real files on disk.
    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / "a.json"
        b = Path(td) / "b.json"
        c = Path(td) / "c.json"
        a.write_text(json.dumps({"fingerprint": fp}), encoding="utf-8")
        b.write_text(json.dumps({"fingerprint": fp}), encoding="utf-8")
        c.write_text(json.dumps({"fingerprint": drifted}), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_same = O.main(["--compare", str(a), str(b)])
        out_same = buf.getvalue()

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_drift = O.main(["--compare", str(a), str(c)])
        out_drift = buf.getvalue()

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_missing = O.main(["--compare", str(a), str(Path(td) / "nope.json")])
        out_missing = buf.getvalue()

    _check("V-W11-FP-CLI-LICENSES-IDENTICAL",
           rc_same == 0 and "COMPARABLE" in out_same,
           "the shipped CLI exits 0 and licenses a paired verdict for two runs "
           "over one population",
           f"exit {rc_same}: {out_same.strip()[:160]}")

    _check("V-W11-FP-CLI-REFUSES-DRIFT",
           rc_drift == 1 and "REFUSED" in out_drift and "case_set_sha" in out_drift,
           "the shipped CLI exits 1 on a drifted population and prints the keys "
           "that moved -- this is the path a future wave actually calls",
           f"exit {rc_drift}: {out_drift.strip()[:160]}")

    _check("V-W11-FP-CLI-REFUSES-UNREADABLE",
           rc_missing == 1 and "UNREADABLE" in out_missing,
           "an unreadable side exits 1 as UNREADABLE, kept distinct from "
           "DRIFTED so the operator is not sent to the wrong fix",
           f"exit {rc_missing}: {out_missing.strip()[:160]}")

    total = _passes + _fails
    print(f"\nW10_FINGERPRINT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
