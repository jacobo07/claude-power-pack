"""Red-branch drills for the three gates added to test_two_pane_exactness.py.

A green nobody has falsified could have every clause removed and read the same,
so each gate here is driven to FAIL on a subject built for the purpose, and
PAIRED with a green control on an otherwise identical subject. Without the
control, a predicate that refused everything would satisfy every red assertion
and look like a working detector.

Every subject is SYNTHETIC and hermetic: temp ledgers, a temp extension source,
a temp inbox directory. Nothing under ~/.claude is read or written, so there is
no mutation to restore and no window in which the real ledger is wrong. It also
means these drills cannot decay the day the real residue is cleaned up -- a
drill pinned to a real defect has an interest in that defect surviving.

  0  every drill landed on its own assertion
  1  a drill did not fire, or a control went red
  2  HARNESS-FAILED -- the gate module could not be loaded or driven

Usage:  python tools/test_two_pane_gate_drills.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OWNER_ROW = {"ts": "2026-09-20T22:03:23+00:00", "session_id": "syn-owner",
             "event": "refused", "detail": "terminal inbox refused: session-mismatch"}
NOOWNER_ROW = {"ts": "2026-09-19T02:21:13+00:00", "session_id": "syn-noowner",
               "event": "refused",
               "detail": "no exact-session delivery: no terminal-inbox provider "
                         "answered or the session is not resolvable"}

passes = fails = 0


def _ok(drill: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {drill}: {evidence}")


def _bad(drill: str, evidence: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {drill}: {evidence}")


def _load_gate():
    path = REPO / "tools" / "test_two_pane_exactness.py"
    spec = importlib.util.spec_from_file_location("_gate_under_drill", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_gate_under_drill"] = mod
    spec.loader.exec_module(mod)
    return mod


def _ledger(tmp: Path, rows: list[dict], name: str) -> Path:
    p = tmp / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def _run(g, fn) -> tuple[int, int, int | None]:
    """Drive one gate call with the counters zeroed. -> (passes, fails, rc)."""
    g.passes = g.fails = 0
    rc = fn()
    return g.passes, g.fails, rc


def main() -> int:
    try:
        g = _load_gate()
    except Exception as exc:                                   # noqa: BLE001
        print(f"HARNESS-FAILED: cannot load the gate module: {exc!r}")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="twopane-drills-"))
    real_ledger, real_repo, real_runs, real_inbox = (
        g.REAL_LEDGER, g.REPO, g.RUNS, g.INBOX_DIR)
    try:
        # ---- control for drills 1-2: both legs present and correct -----------
        g.REAL_LEDGER = _ledger(tmp, [OWNER_ROW, NOOWNER_ROW], "good.jsonl")
        p, f, rc = _run(g, lambda: g.gates_refusal(None))
        if rc is None and p == 2 and f == 0:
            _ok("D0-CONTROL-BOTH-LEGS-PASS",
                "an untouched ledger passes both refusal gates, so the reds below "
                "are attributable to the mutation and not to a gate that refuses "
                "everything")
        else:
            _bad("D0-CONTROL-BOTH-LEGS-PASS", f"passes={p} fails={f} rc={rc}")

        # ---- drill 1 (plan mutation 4): the two rows are NOT interchangeable --
        # Replace the OWNER row's detail with Refuse-NoExact's string. If the two
        # gates were substitutable -- a test asserting only "both rows exist" --
        # this would still pass. It must not.
        swapped = dict(OWNER_ROW, detail=NOOWNER_ROW["detail"])
        g.REAL_LEDGER = _ledger(tmp, [swapped, NOOWNER_ROW], "swapped.jsonl")
        p, f, rc = _run(g, lambda: g.gates_refusal(None))
        if rc is None and f == 1 and p == 1:
            _ok("D1-OWNER-LEG-NOT-SUBSTITUTABLE",
                "with the owner row wearing the no-owner string, OWNER-REFUSED "
                "reds and NOOWNER-NOT-TYPED still passes -- the weak leg cannot "
                "stand in for the strong one")
        else:
            _bad("D1-OWNER-LEG-NOT-SUBSTITUTABLE",
                 f"expected 1 pass + 1 fail, got passes={p} fails={f} rc={rc}")

        # ---- drill 2: a reason OUTSIDE decide()'s vocabulary is not a judgement
        # The prefix alone must not earn the gate: anything can write that string.
        # What makes it owner-only is that the reason is one decide() can return.
        bogus = dict(OWNER_ROW, detail="terminal inbox refused: vibes")
        g.REAL_LEDGER = _ledger(tmp, [bogus, NOOWNER_ROW], "bogus.jsonl")
        p, f, rc = _run(g, lambda: g.gates_refusal(None))
        if rc is None and f == 1:
            _ok("D2-REASON-MUST-BE-IN-VOCABULARY",
                "'terminal inbox refused: vibes' reds -- the gate reads the prefix "
                "AND the reason, so a row nothing in decide() could have produced "
                "cannot pass as an owner judgement")
        else:
            _bad("D2-REASON-MUST-BE-IN-VOCABULARY",
                 f"a reason outside the vocabulary was accepted: passes={p} fails={f}")

        # ---- drill 3: the vocabulary FLOOR -----------------------------------
        # A regex that stopped matching yields an empty set, against which no
        # ledger reason can match -- and the gate would FAIL, blaming the
        # transport for a broken parser. That must be HARNESS-FAILED instead.
        blind = tmp / "blind-repo"
        (blind / "extension" / "src").mkdir(parents=True, exist_ok=True)
        (blind / "extension" / "src" / "terminal_inbox.js").write_text(
            'function decide() { return { action: "refuse", reason: "expired" }; }\n',
            encoding="utf-8")
        g.REPO = blind
        g.REAL_LEDGER = _ledger(tmp, [OWNER_ROW, NOOWNER_ROW], "good2.jsonl")
        p, f, rc = _run(g, lambda: g.gates_refusal(None))
        g.REPO = real_repo
        if rc == 2 and p == 0 and f == 0:
            _ok("D3-VOCABULARY-FLOOR-IS-HARNESS-NOT-VERDICT",
                "a source exposing 1 refusal reason exits 2 with no PASS/FAIL "
                "lines -- a blind extractor reports as an instrument failure, "
                "never as a verdict about the transport")
        else:
            _bad("D3-VOCABULARY-FLOOR-IS-HARNESS-NOT-VERDICT",
                 f"expected rc=2 and no verdicts, got passes={p} fails={f} rc={rc}")

        # ---- drill 4 (plan mutation 5): a planted REQUEST reds the inbox gate -
        runs = tmp / "runs"
        (runs / "synrun").mkdir(parents=True, exist_ok=True)
        (runs / "synrun" / "manifest.json").write_text(json.dumps(
            {"panes": {"A": {"session_id": "syn-sid-aaaa"},
                       "B": {"session_id": "syn-sid-bbbb"}}}), encoding="utf-8")
        g.RUNS = runs
        inbox = tmp / "inbox"
        inbox.mkdir(exist_ok=True)
        g.INBOX_DIR = inbox

        (inbox / "syn-sid-aaaa.req.json").write_text("{}", encoding="utf-8")
        p, f, rc = _run(g, g.gate_inbox_drained)
        if rc is None and f == 1:
            _ok("D4-PLANTED-REQUEST-REDS-THE-GATE",
                "one <drill-sid>.req.json in the inbox fails V-TWOPANE-INBOX-DRAINED")
        else:
            _bad("D4-PLANTED-REQUEST-REDS-THE-GATE",
                 f"a planted request did not red the gate: passes={p} fails={f} rc={rc}")

        # ---- drill 5: removing it restores the green (the paired control) -----
        (inbox / "syn-sid-aaaa.req.json").unlink()
        (inbox / "unrelated-session.req.json").write_text("{}", encoding="utf-8")
        p, f, rc = _run(g, g.gate_inbox_drained)
        if rc is None and p == 1 and f == 0:
            _ok("D5-CONTROL-FOREIGN-REQUEST-IS-NOT-OURS",
                "with the drill file gone the gate passes even though the inbox is "
                "NOT empty -- it judges drill residue, not tidiness, so it cannot "
                "red on the Owner's own live traffic")
        else:
            _bad("D5-CONTROL-FOREIGN-REQUEST-IS-NOT-OURS",
                 f"expected 1 pass, got passes={p} fails={f} rc={rc}")

        # ---- drill 6: an empty needle set is HARNESS, never a pass -----------
        empty_runs = tmp / "empty-runs"
        empty_runs.mkdir(exist_ok=True)
        g.RUNS = empty_runs
        p, f, rc = _run(g, g.gate_inbox_drained)
        if rc == 2 and p == 0 and f == 0:
            _ok("D6-EMPTY-SID-SET-IS-HARNESS",
                "with no drill sids to look for, the gate exits 2 rather than "
                "reporting a clean inbox it never actually interrogated")
        else:
            _bad("D6-EMPTY-SID-SET-IS-HARNESS",
                 f"an empty needle set produced passes={p} fails={f} rc={rc}")

        # ---- drill 7: a missing inbox directory is HARNESS, never a pass ------
        g.RUNS = runs
        g.INBOX_DIR = tmp / "no-such-inbox"
        p, f, rc = _run(g, g.gate_inbox_drained)
        if rc == 2 and p == 0 and f == 0:
            _ok("D7-MISSING-INBOX-DIR-IS-HARNESS",
                "'no drill file is present' is not claimed of a directory that "
                "cannot hold one")
        else:
            _bad("D7-MISSING-INBOX-DIR-IS-HARNESS",
                 f"a missing inbox produced passes={p} fails={f} rc={rc}")

        # ---- drill 8: an unreadable ledger is HARNESS, never a FAIL ----------
        g.REAL_LEDGER = tmp / "no-such-ledger.jsonl"
        p, f, rc = _run(g, lambda: g.gates_refusal(None))
        if rc == 2 and p == 0 and f == 0:
            _ok("D8-ABSENT-LEDGER-IS-HARNESS",
                "with no ledger readable the refusal gates exit 2 -- an absence "
                "here is a statement about the filesystem, not about the transport")
        else:
            _bad("D8-ABSENT-LEDGER-IS-HARNESS",
                 f"an absent ledger produced passes={p} fails={f} rc={rc}")
    finally:
        g.REAL_LEDGER, g.REPO, g.RUNS, g.INBOX_DIR = (
            real_ledger, real_repo, real_runs, real_inbox)
        shutil.rmtree(tmp, ignore_errors=True)

    total = passes + fails
    print(f"TWOPANE_DRILL_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
