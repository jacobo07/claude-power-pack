"""V-SUCC-* gates for econ-succession (S2 pre-model approval receipt, S3 durable receipts, S4 succession
transactions, S5 dead-holder reconciliation). Run: python tools/test_econ_succession.py

Hermetic: every gate builds its own temp transcript, packet, capital root, state dir and ledger. Prints
SUCC_PASS=n/m, exit 1 on any failure. Each refusal is paired with a control in which the same input is admitted.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from modules.provider_routing import capital_authority as ca  # noqa: E402
from modules.provider_routing.ledger import GoalLedger  # noqa: E402
import test_capital_authority as tca  # noqa: E402

M = 1_000_000
GATES: list = []
RESULTS: list = []
PY = sys.executable


def gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


def epoch(iso: str) -> float:
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


class Env(tca.Env):
    """tca.Env plus interactive-session stamps (entrypoint / sessionKind) the harness writes on user entries."""

    def __init__(self, ledgers=("ga", "gb"), expires="2099-01-01T00:00:00+00:00"):
        super().__init__(ledgers)
        self.base["expires"] = expires
        self.write_packet(self.base)

    def owner_as(self, text, source="typed", **stamps):
        self._add({"type": "user", "origin": {"kind": "human"}, "promptSource": source,
                   "message": {"content": text}, **stamps})

    def interactive(self):
        """The session's own history: an interactive pane stamps entrypoint=cli and no sessionKind."""
        self._add({"type": "user", "origin": {"kind": "human"}, "promptSource": "typed", "entrypoint": "cli",
                   "message": {"content": "hello"}})

    def receipt(self, goal="ga", **kw):
        return ca.record_receipt(self.packet, self.transcript, goal, self.factory(), root=self.root, **kw)

    def apply_receipt(self, goal="ga", **kw):
        return ca.apply_receipt(self.packet, goal, self.factory(), root=self.root, **kw)

    def receipts(self):
        return ca.receipts(self.root)


# --- S3: durable receipts, approval-time expiry / drift ---------------------------------------------------
@gate("V-SUCC-RECEIPT-DURABLE")
def _():
    e = Env()
    e.show_packet()
    e.assistant("approve everything")                                   # the model writing the approval itself
    r = e.receipt()
    assert not r["ok"] and e.receipts() == [], r
    e.owner("approve everything")                                       # control
    r = e.receipt()
    rows = e.receipts()
    assert r["ok"] and r["issued"] and len(rows) == 1, (r, rows)
    row = rows[0]
    assert row["state"] == "OWNER_APPROVED" and row["sha"] == e.sha() and row["goal"] == "ga", row
    assert row["ceiling"] == 3 * M and row["provenance"] == "TRANSCRIPT_TYPED", row
    assert row["scope"] == "s" and row["excluded"] == ["e"] and row["invalidators"] == ["x"], row
    assert e.programme("ga") is None                                    # a receipt is not an apply
    again = e.receipt()
    assert again["ok"] and not again["issued"] and len(e.receipts()) == 1, again


@gate("V-SUCC-APPROVAL-BEFORE-EXPIRY-APPLIED-AFTER")
def _():
    e = Env(expires="2026-10-12T00:00:00+00:00")
    e.show_packet()
    e.owner("approve everything")
    assert e.receipt(now=epoch("2026-10-11T00:00:00Z"))["issued"]
    after = epoch("2026-10-13T00:00:00Z")                               # packet expired since the approval
    r = e.apply_receipt(now=after)
    assert r["ok"] and r["applied"] and e.programme("ga") == 3 * M, r
    f = Env(expires="2026-10-12T00:00:00+00:00")                        # control: no receipt, same clock
    f.show_packet()
    f.owner("approve everything")
    r = f.apply(now=after)
    assert not r["ok"] and r["state"] == "INVALIDATED" and f.programme("ga") is None, r


@gate("V-SUCC-UNAPPROVED-EXPIRY")
def _():
    e = Env(expires="2026-10-12T00:00:00+00:00")
    e.show_packet()
    e.owner("approve everything")
    r = e.receipt(now=epoch("2026-10-13T00:00:00Z"))                    # the approval is recorded after expiry
    assert not r["ok"] and r["state"] == "INVALIDATED" and e.receipts() == [], r
    assert not e.apply_receipt()["ok"] and e.programme("ga") is None
    f = Env(expires="2026-10-12T00:00:00+00:00")                        # control: recorded in time
    f.show_packet()
    f.owner("approve everything")
    assert f.receipt(now=epoch("2026-10-11T00:00:00Z"))["issued"]


@gate("V-SUCC-DRIFT-AT-APPROVAL")
def _():
    e = Env()
    e.show_packet()
    e.owner("approve everything")
    e.factory()("ga").renew("s1", 600_000, 1_000)                       # moved 600k > 500k before the approval
    r = e.receipt()
    assert not r["ok"] and r["state"] == "INVALIDATED" and e.receipts() == [], r
    f = Env()
    f.show_packet()
    f.owner("approve everything")
    assert f.receipt()["issued"]                                        # control: receipted at the packet's spend
    f.factory()("ga").renew("s1", 600_000, 1_000)                       # drift AFTER the approval is not a veto
    r = f.apply_receipt()
    assert r["ok"] and r["applied"] and f.programme("ga") == 3 * M, r
    g = Env()
    g.show_packet()
    g.owner("approve everything")
    assert g.receipt()["issued"]
    g.factory()("ga").renew("s1", 3 * M + 1, 4 * M)                     # ceiling no longer above spend: refused
    r = g.apply_receipt()
    assert not r["ok"] and g.programme("ga") is None, r


@gate("V-SUCC-AMOUNT-TAMPER")
def _():
    e = Env()
    e.show_packet()
    e.owner("approve everything")
    assert e.receipt()["issued"]
    edited = json.loads(e.packet.read_text(encoding="utf-8"))
    edited["programmes"][0]["ceilings"]["P80"] = 99 * M
    e.write_packet(edited)
    r = e.apply_receipt()
    assert not r["ok"] and "sha" in r["reason"] and e.programme("ga") is None, r
    e.write_packet(e.base)                                              # control: the approved bytes
    assert e.apply_receipt()["applied"] and e.programme("ga") == 3 * M


@gate("V-SUCC-GOAL-MISMATCH")
def _():
    e = Env()
    e.show_packet()
    e.owner("approve ga only")
    assert not e.receipt("gb")["ok"] and e.receipts() == []
    assert e.receipt("ga")["issued"]                                    # control
    r = e.apply_receipt("gb")
    assert not r["ok"] and e.programme("gb") is None, r
    assert e.apply_receipt("ga")["applied"]


@gate("V-SUCC-DUPLICATE-APPROVAL")
def _():
    e = Env()
    e.show_packet()
    e.owner("approve everything")
    e.owner("approve everything")
    r1, r2 = e.receipt(), e.receipt()
    assert r1["issued"] and not r2["issued"] and len(e.receipts()) == 1 and r1["id"] == r2["id"], (r1, r2)
    a1, a2 = e.apply_receipt(), e.apply_receipt()
    rows = [r for r in e.ledger("ga")._read() if r["op"] == "programme"]
    assert a1["applied"] and not a2["applied"] and len(rows) == 1, (a1, a2, rows)


@gate("V-SUCC-HEADLESS-FORGERY")
def _():
    # Measured 2026-10-11 (plan 5.1): a --bg worker's launch prompt is stamped origin=human, promptSource=typed.
    e = Env()
    e.show_packet()
    e.owner_as("approve everything", sessionKind="bg", entrypoint="cli")
    assert not e.receipt()["ok"] and not e.apply()["ok"] and e.programme("ga") is None
    e.owner_as("approve everything", entrypoint="sdk-cli")
    assert not e.receipt()["ok"] and not e.apply()["ok"]
    e.owner_as("approve everything", entrypoint="cli")                  # control: an interactive pane
    r = e.receipt()
    assert r["issued"] and e.receipts()[0]["approval"] != "", r
    f = Env()
    f.show_packet()
    f.interactive()
    assert ca.session_provenance(f.transcript) == "INTERACTIVE"
    f._add({"type": "user", "origin": {"kind": "human"}, "promptSource": "typed", "sessionKind": "bg",
            "entrypoint": "cli", "message": {"content": "work"}})
    assert ca.session_provenance(f.transcript) == "BG"
    g = Env()
    g._add({"type": "assistant", "message": {"content": [{"type": "text", "text": "x"}]}})
    assert ca.session_provenance(g.transcript) == "UNKNOWN"             # no stamp at all is not interactive


@gate("V-SUCC-FD25EFD1-INVALIDATED")
def _():
    e = Env()
    e.show_packet()
    e.owner("approve everything")
    r = ca.invalidate(e.packet, "ga", "stale before approval (RC4)", root=e.root)
    assert r["ok"] and r["state"] == "INVALIDATED", r
    assert ca.invalidate(e.packet, "ga", "again", root=e.root)["reason"].startswith("already")
    rows = [x for x in ca._rows(e.root) if x["state"] == "INVALIDATED"]
    assert len(rows) == 1 and rows[0]["final"] and rows[0]["sha"] == e.sha(), rows
    assert not e.apply()["ok"] and not e.receipt()["ok"] and e.programme("ga") is None
    f = Env()                                                           # control: no row, same input
    f.show_packet()
    f.owner("approve everything")
    assert f.apply()["ok"]


# --- S2: pre-model approval verb in the registered hook ---------------------------------------------------
class HookEnv(Env):
    def __init__(self, goal="ga", ledgers=("ga",), bind=True):
        super().__init__(ledgers)
        self.state = self.tmp / "state"
        self.sid = "11111111-2222-3333-4444-555555555555"
        self.goal = goal
        (self.state / "goal-binding").mkdir(parents=True)
        if bind:
            (self.state / "goal-binding" / f"{self.sid}.json").write_text(
                json.dumps({"goal": goal, "since_ts": "2026-10-11T00:00:00", "source": "explicit", "pid": 0}),
                encoding="utf-8")
        GoalLedger(self.state / "goal-budget" / goal, goal).declare_cap(5 * M, "test")
        (self.root).mkdir(parents=True, exist_ok=True)
        (self.root / "pending.json").write_text(json.dumps([{"packet": str(self.packet), "goals": [goal]}]),
                                                encoding="utf-8")

    def fire(self, prompt, flush=True, **env):
        if flush:                                                       # the harness flushes the typed entry first
            self._add({"type": "user", "origin": {"kind": "human"}, "promptSource": "typed", "entrypoint": "cli",
                       "message": {"content": prompt}})
        ev ={"session_id": self.sid, "transcript_path": str(self.transcript), "prompt": prompt}
        e = {**os.environ, "CPP_CAPITAL_ROOT": str(self.root), "GSD_LONG_RUN_STATE_DIR": str(self.state),
             "CPP_OCA_NO_SPAWN": "1", "CLAUDE_PY_EXE": PY, "PYTHON_BIN": PY, **env}
        p = subprocess.run(["node", str(REPO / "hooks" / "econ_admission.js")], input=json.dumps(ev),
                           capture_output=True, text=True, env=e, timeout=60)
        assert p.returncode == 0, (p.returncode, p.stderr[:300])
        return json.loads(p.stdout)


@gate("V-SUCC-HOOK-APPROVE-PREMODEL")
def _():
    h = HookEnv()
    h.interactive()
    h.show_packet()
    out = h.fire("approve")
    assert out.get("decision") == "block" and "OWNER_APPROVED" in out["reason"], out   # 0 model tokens
    rows = h.receipts()
    assert len(rows) == 1 and rows[0]["provenance"] == "HOOK_ATTESTED_INTERACTIVE" and rows[0]["goal"] == "ga", rows
    assert rows[0]["sha"] == h.sha() and rows[0]["ceiling"] == 3 * M, rows
    out2 = h.fire("approve")                                            # duplicate: still one receipt
    assert out2.get("decision") == "block" and len(h.receipts()) == 1, out2
    assert h.fire("fix the bug please") == {} and len(h.receipts()) == 1  # control: ordinary text passes through


@gate("V-SUCC-HOOK-REFUSES-FORGED-AND-AMBIGUOUS")
def _():
    bg = HookEnv()
    bg.owner_as("work", sessionKind="bg", entrypoint="cli")
    bg.show_packet()
    assert bg.fire("approve") == {} and bg.receipts() == []             # a bg worker cannot approve itself
    sdk = HookEnv()
    sdk._add({"type": "user", "promptSource": "sdk", "entrypoint": "sdk-cli", "message": {"content": "work"}})
    sdk.show_packet()
    assert sdk.fire("approve") == {} and sdk.receipts() == []
    unseen = HookEnv()                                                  # packet never displayed in this session
    unseen.interactive()
    assert unseen.fire("approve") == {} and unseen.receipts() == []
    unbound = HookEnv(bind=False)
    unbound.interactive()
    unbound.show_packet()
    assert unbound.fire("approve") == {} and unbound.receipts() == []
    neg = HookEnv()
    neg.interactive()
    neg.show_packet()
    assert neg.fire("don't approve") == {} and neg.receipts() == []
    two = HookEnv()
    two.interactive()
    two.show_packet()
    other = two.tmp / "other.json"
    other.write_text(json.dumps({**two.base, "packet": "other"}), encoding="utf-8")
    two._add({"type": "assistant", "message": {"content": [{"type": "text",
              "text": f"Packet sha256 {ca.packet_sha(other)} ready"}]}})
    (two.root / "pending.json").write_text(json.dumps([{"packet": str(two.packet), "goals": ["ga"]},
                                                       {"packet": str(other), "goals": ["ga"]}]), encoding="utf-8")
    assert two.fire("approve") == {} and two.receipts() == []           # two displayed packets: no guess
    ok = HookEnv()                                                      # control: interactive, displayed, bound
    ok.interactive()
    ok.show_packet()
    assert ok.fire("approve").get("decision") == "block" and len(ok.receipts()) == 1
    off = HookEnv()
    off.interactive()
    off.show_packet()
    assert off.fire("approve", CPP_ECON_APPROVE="off") == {} and off.receipts() == []   # kill switch


@gate("V-SUCC-CAPTURE-MERGED")
def _():
    assert not (REPO / "hooks" / "owner_capital_capture.js").exists(), "retired: merged into econ_admission.js"
    src = (REPO / "hooks" / "econ_admission.js").read_text(encoding="utf-8")
    assert "isCapitalIntent" in src and "outstanding" in src and "approvals.jsonl" in src
    h = HookEnv()
    h.show_packet()                                                     # no interactive stamp: receipt refused,
    assert h.fire("approve", flush=False) == {}                         # but the capture row is still written
    rows = [json.loads(x) for x in (h.root / "approvals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows and rows[-1]["kind"] == "approval" and rows[-1]["prompt"] == "approve", rows


@gate("V-SUCC-CLI-CLAIM-NOT-EVIDENCE")
def _():
    h = HookEnv()
    h.interactive()
    h.show_packet()
    r = ca.record_receipt_from_prompt("approve", h.transcript, h.sid, "ga", h.factory(), root=h.root,
                                      wait=0.3, sleep=lambda s: None)
    assert not r["ok"] and h.receipts() == [], r                        # a claim with no typed entry is not evidence
    assert h.fire("approve", flush=False) == {} and h.receipts() == []
    out = h.fire("approve")                                             # control: the typed entry is flushed
    assert out.get("decision") == "block" and len(h.receipts()) == 1, out


# --- S4: the receipt-gated succession transaction ---------------------------------------------------------
class Crash(Exception):
    pass


class Tx:
    """An approved packet plus an injectable launcher that records every launch."""

    def __init__(self):
        self.e = Env()
        self.e.show_packet()
        self.e.owner("approve everything")
        assert self.e.receipt()["issued"]
        self.launches: list = []

    def launcher(self, goal, lease, continuation, key):
        self.launches.append((goal, lease, key))
        return {"ok": True, "key": key}

    def run(self, after=None, **kw):
        from modules.provider_routing import succession as sx
        return sx.run(self.e.packet, "ga", self.e.factory(), self.launcher, "pred-sid", root=self.e.root,
                      after_step=after, **kw)

    def crash_at(self, step):
        def hook(s):
            if s == step:
                raise Crash(s)
        return hook

    def leases(self):
        return self.e.ledger("ga")._gfold(self.e.ledger("ga")._read())["leases"]


@gate("V-SUCC-TX-FULL")
def _():
    t = Tx()
    r = t.run()
    ls = t.leases()
    assert r["ok"] and r["state"] == "RELEASED", r
    assert [x["id"] for x in ls] == ["L1", "L2"] and ls[0]["closed"] and not ls[1]["closed"], ls
    assert ls[1]["succession_id"] == t.e.receipts()[0]["id"], ls
    assert len(t.launches) == 1 and t.launches[0][1] == "L2", t.launches
    assert "pred-sid" in t.e.ledger("ga")._gfold(t.e.ledger("ga")._read())["tombs"]
    cont = json.loads((t.e.root / "succession" / t.e.receipts()[0]["id"] / "continuation.json").read_text("utf-8"))
    assert cont["goal"] == "ga" and cont["lease"] == "L2", cont


@gate("V-SUCC-TX-CRASH-REPLAY")
def _():
    from modules.provider_routing import succession as sx
    for step in sx.STEPS[:-1]:
        t = Tx()
        try:
            t.run(after=t.crash_at(step))
            raise AssertionError(f"crash hook did not fire at {step}")
        except Crash:
            pass
        r = t.run()                                                     # rerun replays from the journal
        ls = t.leases()
        assert r["ok"] and r["state"] == "RELEASED", (step, r)
        assert [x["id"] for x in ls] == ["L1", "L2"] and ls[0]["closed"] and not ls[1]["closed"], (step, ls)
        assert len(t.launches) == 1, (step, t.launches)                 # one L2, one successor, whatever the crash


@gate("V-SUCC-TX-DUPLICATE")
def _():
    t = Tx()
    a, b = t.run(), t.run()
    assert a["state"] == b["state"] == "RELEASED" and len(t.leases()) == 2 and len(t.launches) == 1, (a, b)


@gate("V-SUCC-TX-REFUSES-WITHOUT-RECEIPT-OR-AFTER-REVOKE")
def _():
    from modules.provider_routing import succession as sx
    e = Env()
    e.show_packet()                                                     # displayed, never approved: no receipt
    launches: list = []
    r = sx.run(e.packet, "ga", e.factory(), lambda *a: launches.append(a), "pred-sid", root=e.root)
    assert not r["ok"] and r["state"] == "REJECTED" and launches == [] and len(e.ledger("ga")._gfold(
        e.ledger("ga")._read())["leases"]) == 1, r
    t = Tx()
    assert ca.invalidate(t.e.packet, "ga", "stale", root=t.e.root)["ok"]
    r = t.run()
    assert not r["ok"] and t.launches == [] and len(t.leases()) == 1, r  # control above: the approved packet ran


@gate("V-SUCC-TX-LAUNCH-FAILURE-IS-FAILED-SAFE")
def _():
    t = Tx()
    t.launcher = lambda goal, lease, continuation, key: {"ok": False, "reason": "no slot"}
    r = t.run()
    assert not r["ok"] and r["state"] == "FAILED_SAFE" and "no slot" in r["reason"], r
    t.launcher = Tx.launcher.__get__(t)                                 # control: a later rerun launches once
    r = t.run()
    assert r["ok"] and r["state"] == "RELEASED" and len(t.launches) == 1 and len(t.leases()) == 2, r


def main() -> int:
    for name, fn in GATES:
        try:
            fn()
            RESULTS.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001 - a gate reports, never raises
            RESULTS.append((name, False, "".join(traceback.format_exception_only(type(exc), exc)).strip()
                            + " @ " + traceback.format_exc().splitlines()[-3].strip()))
    for name, ok, why in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'} {name} {why}")
    n = sum(1 for _, ok, _w in RESULTS if ok)
    print(f"SUCC_PASS={n}/{len(RESULTS)}")
    return 0 if n == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
