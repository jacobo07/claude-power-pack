#!/usr/bin/env python3
"""V-gates for epochs, the provider contract, receipts and the retry key (C5).

The crash cases are the point. An epoch that died between intent and dispatch
must resolve to exactly one of "adopt the run that exists" or "LOST" -- never a
second dispatch, and never an open epoch nobody can close.

    python tools/test_gsd_x_goal_epoch.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import epoch as ep        # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402

REPO = "c" * 40


class FakeProvider:
    """A provider that records what it was asked to do. Stands in for a real
    executor at the CONTRACT boundary only -- it is never looser than the
    contract: it declares a wall bound and returns named outcomes."""
    name = "fake"
    wall_bound_s = 60.0

    def __init__(self, found: dict | None = None):
        self.dispatched: list[dict] = []
        self.cancelled: list[dict] = []
        self.found = found

    def dispatch(self, spec):
        self.dispatched.append(spec)
        return {"pid": 4242, "token": spec.get("token", "")}

    def observe(self, handle):
        return ep.Observation(ep.OBS_RUNNING)

    def harvest(self, handle, spec):
        return ep.Receipt(spec["epoch_id"], self.name, spec["revision"])

    def cancel(self, handle):
        self.cancelled.append(handle)

    def probe(self, identity):
        return self.found


class NoBoundProvider(FakeProvider):
    name = "nobound"
    wall_bound_s = 0.0


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    base = Path(tempfile.mkdtemp(prefix="gsdx_ep_"))
    scope_root = Path(tempfile.mkdtemp(prefix="gsdx_scope_"))
    (scope_root / "src").mkdir()
    (scope_root / "src" / "a.py").write_text("print(1)\n", encoding="utf-8")
    (scope_root / "notes.md").write_text("unrelated\n", encoding="utf-8")

    lg = gl.GoalLog(REPO, "g-ep", base=base)
    s = gc.declare(lg, "epochs", ["it runs"], [], {"paths": ["src"]})

    # --- provider contract ----------------------------------------------------
    try:
        ep.check_provider(FakeProvider())
        ok("V-EP-PROVIDER-CONTRACT", "a provider implementing the protocol is accepted")
    except ep.EpochError as exc:
        bad("V-EP-PROVIDER-CONTRACT", f"a valid provider was refused: {exc}")
    try:
        ep.check_provider(NoBoundProvider())
        bad("V-EP-PROVIDER-BOUND", "a provider with no wall bound was accepted")
    except ep.EpochError:
        ok("V-EP-PROVIDER-BOUND", "a provider declaring no wall bound refused")
    try:
        ep.check_provider(object())
        bad("V-EP-PROVIDER-SHAPE", "an object with no provider methods was accepted")
    except ep.EpochError:
        ok("V-EP-PROVIDER-SHAPE", "an object that is not a provider refused")

    # --- retry key ------------------------------------------------------------
    sc1 = ep.scope_hash(scope_root, ["src"])
    (scope_root / "notes.md").write_text("changed outside the scope\n", encoding="utf-8")
    sc2 = ep.scope_hash(scope_root, ["src"])
    check("V-EP-SCOPE-IGNORES-OUTSIDE", sc1 == sc2,
          "a change outside the declared scope does not move the scope hash", f"{sc1} != {sc2}")
    (scope_root / "src" / "a.py").write_text("print(2)\n", encoding="utf-8")
    check("V-EP-SCOPE-SEES-INSIDE", ep.scope_hash(scope_root, ["src"]) != sc1,
          "a change inside the scope moves it", "scope hash did not move")
    try:
        ep.info_key(s.revision, ["g1"], "codex", "we will try harder", sc1)
        bad("V-EP-HYPOTHESIS-CLOSED", "a free-text hypothesis was accepted")
    except ep.EpochError:
        ok("V-EP-HYPOTHESIS-CLOSED", "a free-text hypothesis refused; the vocabulary is closed")

    key = ep.info_key(s.revision, ["g1"], "fake", "initial", sc1)
    e1 = ep.begin(lg, gc.project(lg), "fake", {"epoch_id": "x", "revision": s.revision}, key,
                  "initial", "t")
    check("V-EP-INTENT-FIRST",
          ep.project_epochs(gc.project(lg))[e1.epoch_id].state == "dispatching"
          and e1.identity.get("run_token"),
          "the intent is recorded with an identity before any dispatch",
          "no dispatching record or no identity")
    check("V-EP-OPEN-BLOCKS", ep.open_epochs(gc.project(lg)) == [e1.epoch_id],
          "an epoch not yet ended is open", "epoch not reported open")

    prov = FakeProvider()
    handle = prov.dispatch({"token": e1.identity["run_token"], "epoch_id": e1.epoch_id})
    ep.mark_running(lg, gc.project(lg), e1.epoch_id, handle, "t")
    ep.end(lg, gc.project(lg), e1.epoch_id, ep.FAILED, "gate returned 1", "t")
    try:
        ep.end(lg, gc.project(lg), e1.epoch_id, ep.COMPLETED, "late claim", "t")
        bad("V-EP-ENDS-ONCE", "an ended epoch was ended a second time")
    except ep.EpochError:
        ok("V-EP-ENDS-ONCE", "an epoch ends exactly once")
    try:
        ep.end(lg, gc.project(lg), e1.epoch_id, "finished-ish", "x", "t")
        bad("V-EP-OUTCOME-NAMED", "an unnamed outcome was accepted")
    except ep.EpochError:
        ok("V-EP-OUTCOME-NAMED", "an outcome outside the named set refused")

    try:
        ep.begin(lg, gc.project(lg), "fake", {}, key, "initial", "t")
        bad("V-EP-NO-BLIND-RETRY", "the identical failed attempt was retried")
    except ep.RetryWithoutNewInformation:
        ok("V-EP-NO-BLIND-RETRY", "an attempt whose information key already failed refused")
    key2 = ep.info_key(s.revision, ["g1"], "codex", "provider_change", sc1)
    e2 = ep.begin(lg, gc.project(lg), "codex", {"epoch_id": "y", "revision": s.revision},
                  key2, "provider_change", "t")
    check("V-EP-RETRY-WITH-NEW-INFO", e2.epoch_id != e1.epoch_id,
          "changing the provider is new information and is allowed (control)", "refused")

    # --- receipts --------------------------------------------------------------
    st = gc.project(lg)
    r = ep.Receipt(e2.epoch_id, "codex", st.revision, head_before="a", head_after="b",
                   commits=["b"], narrative="I did it all myself")
    rid = ep.ingest_receipt(lg, st, r, "t")
    check("V-EP-RECEIPT-INGESTED", rid in ep.project_epochs(gc.project(lg))[e2.epoch_id].receipts,
          f"receipt {rid} stored once", "receipt not recorded")
    try:
        ep.ingest_receipt(lg, gc.project(lg), r, "t")
        bad("V-EP-RECEIPT-DUPLICATE", "the same receipt was ingested twice")
    except ep.EpochError:
        ok("V-EP-RECEIPT-DUPLICATE", "a duplicate receipt refused (content-addressed)")
    stale = ep.Receipt(e2.epoch_id, "codex", "deadbeefdeadbeef")
    try:
        ep.ingest_receipt(lg, gc.project(lg), stale, "t")
        bad("V-EP-RECEIPT-STALE-REVISION", "a receipt about another revision was ingested")
    except ep.EpochError:
        ok("V-EP-RECEIPT-STALE-REVISION", "a receipt about another revision refused")
    try:
        ep.ingest_receipt(lg, gc.project(lg), ep.Receipt("ep-nope", "codex", st.revision), "t")
        bad("V-EP-RECEIPT-UNKNOWN-EPOCH", "a receipt for an unknown epoch was ingested")
    except ep.EpochError:
        ok("V-EP-RECEIPT-UNKNOWN-EPOCH", "a receipt for an unknown epoch refused")

    # --- crash between intent and effect ---------------------------------------
    lg2 = gl.GoalLog(REPO, "g-crash", base=base)
    s2 = gc.declare(lg2, "crash")
    k = ep.info_key(s2.revision, [], "fake", "initial", "sc")
    stuck = ep.begin(lg2, gc.project(lg2), "fake", {}, k, "initial", "t")
    adopted = ep.recover(lg2, gc.project(lg2), FakeProvider(found={"pid": 99}), stuck.epoch_id, "t")
    rec = ep.project_epochs(gc.project(lg2))[stuck.epoch_id]
    check("V-EP-RECOVER-ADOPTS", adopted == "adopted" and rec.state == "running"
          and rec.handle == {"pid": 99},
          "a run found by its pre-minted identity is adopted, not re-dispatched",
          f"outcome={adopted} state={rec.state}")

    lg3 = gl.GoalLog(REPO, "g-crash2", base=base)
    s3 = gc.declare(lg3, "crash2")
    k3 = ep.info_key(s3.revision, [], "fake", "initial", "sc")
    stuck3 = ep.begin(lg3, gc.project(lg3), "fake", {}, k3, "initial", "t")
    gone = FakeProvider(found=None)
    res = ep.recover(lg3, gc.project(lg3), gone, stuck3.epoch_id, "t")
    rec3 = ep.project_epochs(gc.project(lg3))[stuck3.epoch_id]
    check("V-EP-RECOVER-LOST", res == ep.LOST and rec3.state == "ended"
          and rec3.outcome == ep.LOST and not gone.dispatched,
          "no run found -> LOST, and nothing was dispatched a second time",
          f"res={res} state={rec3.state} dispatched={gone.dispatched}")
    check("V-EP-RECOVER-CLOSES-OPEN", ep.open_epochs(gc.project(lg3)) == [],
          "a lost epoch stops blocking closure", "the lost epoch is still open")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_EPOCH_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
