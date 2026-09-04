#!/usr/bin/env python3
"""V-CEPS-CORRECTION-* -- gate for the Owner-correction capture loop.

Origin (2026-09-04): `from_stop_hook()` -- the only thing in this estate that
notices the OWNER correcting the agent ("no, actually", "that's wrong",
"revert", "no es asi") -- had no caller anywhere, and `vault/ceps/drafts/` did
not exist on disk, so it had provably never run. Its documented reader,
`/ceps-confirm`, did not exist either: not in the 73 PP commands and not in
~/.claude/commands. A producer with no caller writing to a sink with no reader
is two halves of nothing.

That made it the inverse of the usual failure here. The estate's documented
trap is a WRITER WITHOUT A READER; this was a reader-less sink AND a
caller-less writer, which is why no liveness gate ever fired on it -- there
were no fires to compare records against.

These gates pin the loop end to end:
  1. an Owner correction becomes a draft, and a non-correction does not;
  2. the draft is READABLE (the half that did not exist);
  3. confirming it produces a real event and empties the pending set;
  4. dismissing it also empties the pending set -- a queue whose only exit is
     "confirm" strands every false positive forever, which is the
     status-field-nobody-can-transition trap already sealed in this estate;
  5. the reader degrades to empty rather than raising when nothing has run.

Hermeticity: DRAFTS_DIR is redirected into a tmpdir, and the resolved-draft
directories are derived from it at call time precisely so this redirection is
honoured. REJECTIONS_PATH is redirected too -- `capture_liveness.py` reads the
real ledger, and a suite that writes into it has already produced one false
capture-loss alarm in this repo.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ceps  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diagnostic}")


def _isolate(tmp: Path) -> None:
    ceps.EVENTS_PATH = tmp / "events.jsonl"
    ceps.DB_PATH = tmp / "patterns.db"
    ceps.LESSONS_PATH = tmp / "session_lessons.md"
    ceps.UKDL_PATH = tmp / "ukdl.md"
    ceps.DRAFTS_DIR = tmp / "drafts"
    ceps.REJECTIONS_PATH = tmp / "rejections.jsonl"


def main() -> int:
    print("== V-CEPS-CORRECTION gates ==")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _isolate(tmp)

        # ---- V-CEPS-CORRECTION-PRODUCES ---------------------------------
        # Arrange: one genuine Owner correction among ordinary turns.
        drafts = ceps.from_stop_hook([
            "please add the index",
            "no, actually that's wrong -- revert it",
        ])
        if len(drafts) == 1:
            _ok("V-CEPS-CORRECTION-PRODUCES",
                f"1 correction turn -> 1 draft ({drafts[0]['draft_id']})")
        else:
            _fail("V-CEPS-CORRECTION-PRODUCES",
                  f"expected 1 draft, got {len(drafts)}")

        # ---- V-CEPS-CORRECTION-NEGATIVE-CONTROL --------------------------
        # Ordinary approving turns must produce NOTHING. Without this, a
        # detector that drafts on every turn would pass every gate above and
        # bury the real signal in noise.
        before = len(ceps.list_drafts())
        ceps.from_stop_hook(["ok", "perfect, ship it", "thanks"])
        if len(ceps.list_drafts()) == before:
            _ok("V-CEPS-CORRECTION-NEGATIVE-CONTROL",
                "approving turns produce no drafts")
        else:
            _fail("V-CEPS-CORRECTION-NEGATIVE-CONTROL",
                  "a non-correction turn produced a draft")

        # ---- V-CEPS-CORRECTION-READABLE ----------------------------------
        # The half that did not exist: the drafts must be enumerable.
        pending = ceps.list_drafts()
        if len(pending) == 1 and pending[0].get("needs_confirmation") is True:
            _ok("V-CEPS-CORRECTION-READABLE",
                "pending draft is reachable via list_drafts()")
        else:
            _fail("V-CEPS-CORRECTION-READABLE",
                  f"expected 1 pending draft, got {pending}")

        # ---- V-CEPS-CORRECTION-CONFIRMS ----------------------------------
        did = pending[0]["draft_id"] if pending else "missing"
        event = ceps.confirm_draft(did, "spec-violation", "owner-correction")
        # Assert the identity field by NAME. The first draft of this gate read
        # `event_id`, which record_error does not emit -- the event was being
        # created correctly the whole time while the back-link was stamped
        # None. Truthiness on the dict would have passed and hidden it.
        if event and event.get("id"):
            _ok("V-CEPS-CORRECTION-CONFIRMS", f"draft -> event {event['id']}")
        else:
            _fail("V-CEPS-CORRECTION-CONFIRMS",
                  f"confirm_draft returned {event!r}")

        # ---- V-CEPS-CORRECTION-LEAVES-PENDING ----------------------------
        if ceps.list_drafts() == []:
            _ok("V-CEPS-CORRECTION-LEAVES-PENDING",
                "confirmed draft left the pending set")
        else:
            _fail("V-CEPS-CORRECTION-LEAVES-PENDING",
                  "a confirmed draft is still pending -- it would be "
                  "re-confirmed forever")

        # ---- V-CEPS-CORRECTION-DISMISSABLE -------------------------------
        # The terminal state that is NOT promotion. Without it every false
        # positive is immortal and the queue only ever grows.
        ceps.from_stop_hook(["wait, no -- stop that"])
        pend = ceps.list_drafts()
        did2 = pend[0]["draft_id"] if pend else "missing"
        got = ceps.dismiss_draft(did2, "false positive, I was talking to someone else")
        if got and ceps.list_drafts() == []:
            _ok("V-CEPS-CORRECTION-DISMISSABLE",
                "a draft can be retired without becoming an event")
        else:
            _fail("V-CEPS-CORRECTION-DISMISSABLE",
                  f"dismiss left {len(ceps.list_drafts())} pending")

        # ---- V-CEPS-CORRECTION-PROVENANCE --------------------------------
        # A resolved draft is kept, not deleted: the confirm decision is
        # itself evidence, and deleting it would erase who judged what.
        import json as _json
        conf = list((tmp / "drafts" / "confirmed").glob("*.json"))
        dism = list((tmp / "drafts" / "dismissed").glob("*.json"))
        # The retained file must also carry a REAL back-link to the event it
        # became. Counting files alone passed while that link was None.
        linked = [
            p for p in conf
            if _json.loads(p.read_text(encoding="utf-8")).get("confirmed_event_id")
        ]
        if len(conf) == 1 and len(dism) == 1 and len(linked) == 1:
            _ok("V-CEPS-CORRECTION-PROVENANCE",
                "both resolved drafts retained; confirmed one links its event")
        else:
            _fail("V-CEPS-CORRECTION-PROVENANCE",
                  f"confirmed={len(conf)} dismissed={len(dism)} "
                  f"with-event-link={len(linked)}")

        # ---- V-CEPS-CORRECTION-UNKNOWN-ID --------------------------------
        # Fail-closed on identity, fail-open on process: an unknown id is a
        # None, never an exception and never a fabricated event.
        try:
            if ceps.confirm_draft("deadbeef") is None and \
                    ceps.dismiss_draft("deadbeef") is None:
                _ok("V-CEPS-CORRECTION-UNKNOWN-ID",
                    "unknown draft-id -> None, no exception")
            else:
                _fail("V-CEPS-CORRECTION-UNKNOWN-ID",
                      "an unknown id produced a result")
        except Exception as exc:  # noqa: BLE001 -- the gate IS "does not raise"
            _fail("V-CEPS-CORRECTION-UNKNOWN-ID", f"raised: {exc}")

    # ---- V-CEPS-CORRECTION-NO-DIR ---------------------------------------
    # Outside the fixture the drafts dir does not exist at all (it did not on
    # disk for this feature's whole life). The reader must degrade to empty.
    with tempfile.TemporaryDirectory() as td2:
        ceps.DRAFTS_DIR = Path(td2) / "never_created"
        try:
            if ceps.list_drafts() == []:
                _ok("V-CEPS-CORRECTION-NO-DIR",
                    "absent drafts dir -> [] (fail-open)")
            else:
                _fail("V-CEPS-CORRECTION-NO-DIR", "expected []")
        except Exception as exc:  # noqa: BLE001
            _fail("V-CEPS-CORRECTION-NO-DIR", f"raised instead of degrading: {exc}")

    total = _passes + _fails
    print(f"CEPS_CORRECTION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
