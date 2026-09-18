#!/usr/bin/env python
"""V-CXT-* -- a continuation reaches the session that owns it, or nobody.

Spec: vault/specs/exact-target-continuation.md (C2, C3, C5).

The Orca CLI is replaced by a fake that keeps real per-terminal transcripts: a
send appends the command ONLY to the transcript of the terminal it addressed.
So "B did not receive it" is observed in B's own transcript, not inferred from
which handle we meant to use. Terminal B is marked `active` in the fake: a CLI
call that omitted `--terminal` would resolve to it, which is the exact
foreground trap from 2026-09-18 re-created at the provider layer.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="cxt-state-")
os.environ.pop("CPP_CONTINUATION_TRANSPORT", None)

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
TMP = Path(tempfile.mkdtemp(prefix="cxt-"))

FAKE_ORCA = r'''
import json, os, sys, time
state_path = os.environ["FAKE_ORCA_STATE"]
st = json.load(open(state_path, encoding="utf-8"))
argv = sys.argv[1:]
with open(st["log"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(argv) + "\n")
def flag(name):
    return argv[argv.index(name) + 1] if name in argv else None
def out(obj):
    print(json.dumps(obj)); sys.exit(0 if obj.get("ok") else 1)
if st.get("down"):
    out({"ok": False, "error": {"code": "runtime_unavailable"}})
verb = argv[1] if len(argv) > 1 else ""
handle = flag("--terminal")
if handle is None and verb in ("wait", "send"):
    handle = next(t["handle"] for t in st["terminals"] if t.get("active"))
if verb == "list":
    out({"ok": True, "result": {"terminals": st["terminals"], "totalCount": len(st["terminals"])}})
if verb == "wait":
    for t in st["terminals"]:
        if t["handle"] == handle and st.get("replace_after_wait"):
            t["incarnationId"] = "replaced-" + t["incarnationId"]
    json.dump(st, open(state_path, "w", encoding="utf-8"))
    out({"ok": True, "result": {"wait": {"handle": handle, "condition": "tui-idle",
                                          "satisfied": st.get("idle", True), "status": "running"}}})
if verb == "send":
    t = next((t for t in st["terminals"] if t["handle"] == handle), None)
    if t is None:
        out({"ok": False, "error": {"code": "terminal_handle_stale"}})
    if st.get("refuse"):
        out({"ok": True, "result": {"send": {"handle": handle, "accepted": False, "bytesWritten": 0,
                                              "refusedReason": st["refuse"]}}})
    text = flag("--text") or ""
    if st.get("consume", True) and t.get("transcript"):
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 1)) + ".000Z"
        row = {"type": "user", "timestamp": iso,
               "message": {"role": "user", "content": "<command-name>" + text.split()[0] + "</command-name>"}}
        with open(t["transcript"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    out({"ok": True, "result": {"send": {"handle": handle, "accepted": True,
                                          "bytesWritten": len(text) + 1}}})
out({"ok": False, "error": {"code": "unknown_verb"}})
'''

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ct = load(TOOLS / "continuation_transport.py", "continuation_transport")
lr = sys.modules["gsd_long_run"]

FAKE = TMP / "fake_orca.py"
FAKE.write_text(FAKE_ORCA, encoding="utf-8")
os.environ["CPP_ORCA_CLI"] = json.dumps([sys.executable, str(FAKE)])


def uid() -> str:
    return str(uuid.uuid4())


def terminal(tab: str, leaf: str, tx: Path, **kw) -> dict:
    t = {"handle": f"term_{uid()}", "ptyId": str(len(tab)), "incarnationId": uid(), "orphaned": False,
         "tabId": tab, "leafId": leaf, "connected": True, "writable": True, "title": "x",
         "transcript": str(tx)}
    t.update(kw)
    return t


def transcript_file(rows=()) -> Path:
    p = TMP / f"tx-{uid()}.jsonl"
    lines = [{"type": "system", "cwd": str(ROOT)}] + list(rows)
    p.write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    return p


def asst(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def world(terminals, **flags) -> Path:
    log = TMP / f"log-{uid()}.jsonl"
    log.write_text("", encoding="utf-8")
    state = {"terminals": terminals, "log": str(log), **flags}
    sp = TMP / f"state-{uid()}.json"
    sp.write_text(json.dumps(state), encoding="utf-8")
    os.environ["FAKE_ORCA_STATE"] = str(sp)
    return log


def calls(log: Path) -> list[list[str]]:
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]


def sends(log: Path) -> list[list[str]]:
    return [c for c in calls(log) if c[:2] == ["terminal", "send"]]


def cmd_rows(tx: Path) -> int:
    return sum(1 for l in tx.read_text(encoding="utf-8").splitlines() if "<command-name>" in l)


class Clock:
    def __init__(self):
        self.t = time.time()

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


def pane(tab: str, leaf: str) -> str:
    return f"{tab}:{leaf}"


def bind(session: str, key: str | None) -> None:
    ct.capture_endpoint(session, env={"ORCA_PANE_KEY": key} if key else {})


def run(session: str, tx: Path, kind="resume", text="/d1-continue", cid=None, **kw) -> dict:
    c = Clock()
    return ct.deliver(session, kind, text, kw.get("expect_prefix"), str(tx), cid=cid or f"{session}:c1",
                      requested_at=time.time() - 1, sleep=c.sleep, now=c.now)


# ------------------------------------------------------------------ pure
def gates_pure() -> None:
    tab, leaf = uid(), uid()
    a = terminal(tab, leaf, TMP / "a")
    ok, t = ct.resolve(pane(tab, leaf), [a, terminal(uid(), uid(), TMP / "b")])
    check("V-CXT-RESOLVE-EXACT", ok == "OK" and t is a, ok)
    check("V-CXT-RESOLVE-NOT-FOUND", ct.resolve(pane(tab, uid()), [a])[0] == ct.NOT_FOUND, "missing leaf")
    check("V-CXT-RESOLVE-AMBIGUOUS", ct.resolve(pane(tab, leaf), [a, dict(a, handle="term_x")])[0] == ct.AMBIGUOUS,
          "two terminals claim one pane key")
    check("V-CXT-RESOLVE-ORPHAN-STALE", ct.resolve(pane(tab, leaf), [dict(a, orphaned=True)])[0] == ct.STALE,
          "orphaned")
    check("V-CXT-RESOLVE-UNWRITABLE", ct.resolve(pane(tab, leaf), [dict(a, writable=False)])[0] == ct.NOT_WRITABLE,
          "not writable")
    check("V-CXT-RESOLVE-MALFORMED-KEY", ct.resolve("not-a-key", [a])[0] == ct.NO_ENDPOINT, "malformed key")
    s = f"cxt-{uid()[:8]}"
    bind(s, pane(tab, leaf))
    ep = ct.read_endpoint(s)
    check("V-CXT-CAPTURE-ORCA", ep and ep["host"] == "orca" and ep["pane_key"] == pane(tab, leaf), f"{ep}")
    bind(s, None)
    ep = ct.read_endpoint(s)
    check("V-CXT-CAPTURE-UNSUPPORTED", ep and ep["host"] == "unsupported" and ep["pane_key"] is None, f"{ep}")


# ------------------------------------------------------------------ delivery
def gates_delivery() -> None:
    # Two panes; B is the ACTIVE one. The continuation belongs to A.
    ta, tb = transcript_file(), transcript_file()
    tab_a, leaf_a, tab_b, leaf_b = uid(), uid(), uid(), uid()
    A, B = terminal(tab_a, leaf_a, ta), terminal(tab_b, leaf_b, tb, active=True)
    log = world([A, B])
    s = f"cxt-{uid()[:8]}"
    bind(s, pane(tab_a, leaf_a))
    out = run(s, ta)
    check("V-CXT-TWO-PANE-DELIVERED-TO-OWNER",
          out.get("outcome") == ct.DELIVERED and cmd_rows(ta) == 1, f"{out} rowsA={cmd_rows(ta)}")
    check("V-CXT-TWO-PANE-FOREGROUND-UNTOUCHED", cmd_rows(tb) == 0, f"rowsB={cmd_rows(tb)}")
    addressed = [c for c in calls(log) if c[:2] in (["terminal", "send"], ["terminal", "wait"])]
    check("V-CXT-EVERY-EFFECT-NAMES-ITS-TERMINAL",
          addressed and all("--terminal" in c and c[c.index("--terminal") + 1] == A["handle"] for c in addressed),
          f"{len(addressed)} addressed calls")
    ev = [e["event"] for e in lr.ledger_events(s)]
    check("V-CXT-RECEIPT-STAGES",
          ev[:1] == ["delivery_requested"] and "target_resolved" in ev and "transport_accepted" in ev
          and ev[-1] == "resume_confirmed", f"{ev}")
    # Same continuation again: reconciled, not resent.
    before = len(sends(log))
    out = run(s, ta)
    check("V-CXT-DUPLICATE-NOT-RESENT", out.get("outcome") == ct.ALREADY and len(sends(log)) == before, f"{out}")

    # Worker replacement: the session re-captured a NEW pane key; the old one must not receive.
    tab_c, leaf_c = uid(), uid()
    tc = transcript_file()
    C = terminal(tab_c, leaf_c, tc)
    world([A, B, C])
    s2 = f"cxt-{uid()[:8]}"
    bind(s2, pane(tab_a, leaf_a))
    bind(s2, pane(tab_c, leaf_c))
    rows_a = cmd_rows(ta)
    out = run(s2, tc)
    check("V-CXT-MIGRATED-ENDPOINT-WINS",
          out.get("outcome") == ct.DELIVERED and cmd_rows(tc) == 1 and cmd_rows(ta) == rows_a, f"{out}")

    # Unsupported host (a Cursor terminal): no provider call at all.
    s3 = f"cxt-{uid()[:8]}"
    bind(s3, None)
    log = world([A, B])
    out = run(s3, transcript_file())
    check("V-CXT-UNSUPPORTED-NO-FALLBACK", out.get("outcome") == ct.UNSUPPORTED and not calls(log), f"{out}")

    # No endpoint ever captured.
    out = run(f"cxt-{uid()[:8]}", transcript_file())
    check("V-CXT-NO-ENDPOINT-BLOCKS", out.get("outcome") == ct.NO_ENDPOINT, f"{out}")

    # Provider down (the state measured on 2026-09-18: runtime_unavailable).
    s4 = f"cxt-{uid()[:8]}"
    bind(s4, pane(tab_a, leaf_a))
    log = world([A, B], down=True)
    out = run(s4, ta)
    check("V-CXT-PROVIDER-DOWN-BLOCKS", out.get("outcome") == ct.PROVIDER_DOWN and not sends(log), f"{out}")

    # Terminal replaced while we waited for idle.
    log = world([dict(A), B], replace_after_wait=True)
    out = run(s4, ta)
    check("V-CXT-REPLACED-DURING-WAIT-REFUSED", out.get("outcome") == ct.STALE and not sends(log), f"{out}")

    # Agent busy.
    log = world([A, B], idle=False)
    out = run(s4, ta, cid=f"{s4}:busy")
    check("V-CXT-BUSY-NOT-SENT", out.get("outcome") == ct.BUSY and not sends(log), f"{out}")

    # Runtime refuses (no agent in that pane).
    log = world([A, B], refuse="no-agent")
    out = run(s4, ta, cid=f"{s4}:refused")
    check("V-CXT-REFUSAL-REPORTED", out.get("outcome") == ct.REJECTED and out.get("refused") == "no-agent", f"{out}")

    # Already consumed before we send (the Owner typed it): reconcile, do not send.
    s5 = f"cxt-{uid()[:8]}"
    tx5 = transcript_file([{"type": "user", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
                            + ".000Z", "message": {"role": "user",
                                                   "content": "<command-name>/d1-continue</command-name>"}}])
    A5 = terminal(tab_a, leaf_a, tx5)
    bind(s5, pane(tab_a, leaf_a))
    log = world([A5, B])
    out = run(s5, tx5)
    check("V-CXT-ALREADY-CONSUMED-NOT-SENT", out.get("outcome") == ct.ALREADY and not sends(log), f"{out}")

    # Accepted but never consumed: bounded attempts, then exhausted.
    s6 = f"cxt-{uid()[:8]}"
    tx6 = transcript_file()
    bind(s6, pane(tab_a, leaf_a))
    log = world([terminal(tab_a, leaf_a, tx6), B], consume=False)
    o1, o2, o3 = (run(s6, tx6, cid=f"{s6}:c1") for _ in range(3))
    check("V-CXT-UNCONFIRMED-IS-NOT-DELIVERED",
          o1.get("outcome") == ct.ACCEPTED_UNCONFIRMED and "delivery_unconfirmed" in
          [e["event"] for e in lr.ledger_events(s6)], f"{o1}")
    check("V-CXT-ATTEMPTS-BOUNDED",
          o2.get("outcome") == ct.ACCEPTED_UNCONFIRMED and o3.get("outcome") == ct.EXHAUSTED
          and len(sends(log)) == ct.MAX_ATTEMPTS, f"{o2} {o3} sends={len(sends(log))}")

    # Kill switch.
    os.environ["CPP_CONTINUATION_TRANSPORT"] = "off"
    log = world([A, B])
    out = run(s4, ta, cid=f"{s4}:off")
    os.environ.pop("CPP_CONTINUATION_TRANSPORT", None)
    check("V-CXT-KILL-SWITCH", out.get("outcome") == ct.DISABLED and not calls(log), f"{out}")

    # /compact: the model's own validated last line is what gets sent.
    s7 = f"cxt-{uid()[:8]}"
    tx7 = transcript_file([asst("done for now\n/compact focus on phase 7 invariants")])
    bind(s7, pane(tab_a, leaf_a))
    log = world([terminal(tab_a, leaf_a, tx7), B])
    out = run(s7, tx7, kind="compact", text=None, expect_prefix="/compact", cid=f"{s7}:k1")
    sent = sends(log)
    check("V-CXT-COMPACT-SENDS-VALIDATED-LINE",
          out.get("outcome") == ct.DELIVERED and sent
          and sent[0][sent[0].index("--text") + 1] == "/compact focus on phase 7 invariants", f"{out}")
    tx8 = transcript_file([asst("I think we should compact soon.")])
    log = world([terminal(tab_a, leaf_a, tx8), B])
    out = run(s7, tx8, kind="compact", text=None, expect_prefix="/compact", cid=f"{s7}:k2")
    check("V-CXT-COMPACT-WITHOUT-LINE-REFUSED", out.get("outcome") == ct.NO_LINE and not sends(log), f"{out}")

    # Durable job: written before the worker exists, removed once resolved.
    s9 = f"cxt-{uid()[:8]}"
    tx9 = transcript_file()
    bind(s9, pane(tab_a, leaf_a))
    world([terminal(tab_a, leaf_a, tx9), B])
    os.environ["GSD_LONG_RUN_NO_SPAWN"] = "1"
    spawned = ct.spawn_delivery(s9, "resume", "/d1-continue", None, str(tx9), f"{s9}:j1")
    os.environ.pop("GSD_LONG_RUN_NO_SPAWN", None)
    jp = ct.job_path(f"{s9}:j1")
    check("V-CXT-JOB-PERSISTED-BEFORE-WORKER", not spawned and jp.is_file(), f"{jp}")
    out = ct.run_job(jp)
    check("V-CXT-JOB-RUNS-AND-CLEARS", out.get("outcome") == ct.DELIVERED and not jp.exists(), f"{out}")


def main() -> int:
    print("V-CXT -- exact-target continuation transport")
    gates_pure()
    gates_delivery()
    total = passes + fails
    print(f"CXT_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
