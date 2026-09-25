#!/usr/bin/env python3
"""V-LEASE-* gates for modules/lease (UWCP assimilation R2).

Each invariant is driven from both poles: the case where it must refuse and a
control where the same call must succeed, so a store that refused everything
would fail the controls. The race runs in real separate interpreters released
together by a barrier file, because a thread race would not exercise the OS lock.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.lease import (ACTIVE, CONSUMED, EXPIRED, QUEUE_WAIT_EXCEEDED, JournalCorrupt,  # noqa: E402
                           LeaseStore, UnsupportedFilesystem, filesystem_type, fs_refusal)
from modules.lease import store as store_mod  # noqa: E402

passes = fails = 0


def _ok(gate, msg):
    global passes
    passes += 1
    print(f"  PASS {gate}: {msg}")


def _fail(gate, msg):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {msg}")


def check(gate, cond, good, bad):
    (_ok if cond else _fail)(gate, good if cond else bad)


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def fresh(clock=None, min_ttl=10.0):
    d = Path(tempfile.mkdtemp(prefix="lease-"))
    return LeaseStore(d, min_ttl_s=min_ttl, clock=clock or Clock()), d


def main() -> int:
    # --- exclusivity + control ------------------------------------------------
    s, _ = fresh()
    a = s.acquire(["gpu"], "A", 30, "L1")
    b = s.acquire(["gpu"], "B", 30, "L2")
    check("V-LEASE-EXCLUSIVE", a.ok and not b.ok and b.reason == "held",
          "second holder refused while the class is held", f"a={a} b={b}")
    c = s.acquire(["dolphin"], "B", 30, "L3")
    check("V-LEASE-EXCLUSIVE-CONTROL", c.ok, "an unrelated class is still grantable", f"{c}")

    # --- all-or-nothing -------------------------------------------------------
    s, _ = fresh()
    s.acquire(["x"], "A", 30, "LA")
    r = s.acquire(["x", "y"], "B", 30, "LB")
    y_free = s.acquire(["y"], "C", 30, "LC")
    s2, _ = fresh()
    s2.acquire(["y"], "A", 30, "LA")                  # the class that sorts SECOND is held
    r2 = s2.acquire(["x", "y"], "B", 30, "LB")
    x_free = s2.acquire(["x"], "C", 30, "LC")
    check("V-LEASE-ALL-OR-NOTHING", not r.ok and y_free.ok and not r2.ok and x_free.ok,
          "a multi-class request with any member held grants none, whichever member it is",
          f"r={r} y={y_free} r2={r2} x={x_free}")

    # --- min TTL floor ----------------------------------------------------------
    s, _ = fresh(min_ttl=10)
    low, at = s.acquire(["g"], "A", 9.9, "L1"), s.acquire(["g"], "A", 10, "L2")
    check("V-LEASE-MIN-TTL", (not low.ok and low.reason == "ttl_below_floor") and at.ok,
          "ttl below the floor refused, ttl at the floor granted", f"low={low} at={at}")

    # --- TTL counts from dispatch; queue wait has its own clock ---------------
    clk = Clock()
    s, _ = fresh(clk)
    g = s.acquire(["g"], "A", 30, "L1", queue_wait_s=100)
    clk.t += 60                                   # beyond the TTL, inside queue wait
    s.check("g", g.fences["g"])                   # an op applies due expiries; snapshot() does not
    still = s.snapshot()["leases"]["L1"]["state"]
    check("V-LEASE-TTL-FROM-DISPATCH", still == "RESERVED",
          "a queued reservation does not expire by TTL", f"state={still}")
    clk.t += 50                                   # beyond queue wait
    chk = s.check("g", g.fences["g"])
    snap = s.snapshot()
    check("V-LEASE-QUEUE-WAIT-EXPIRES", snap["leases"]["L1"]["state"] == QUEUE_WAIT_EXCEEDED
          and snap["fence"]["g"] > g.fences["g"] and not chk.ok,
          "queue-wait expiry releases the class and moves the fence in the same record",
          f"snap={snap} chk={chk}")
    after = s.acquire(["g"], "B", 30, "L2")
    check("V-LEASE-QUEUE-WAIT-FREES", after.ok and after.fences["g"] > g.fences["g"],
          "the class is grantable again, with a larger fence", f"{after}")

    # --- expiry bumps the fence; the stale holder is refused by the resource ---
    clk = Clock()
    s, _ = fresh(clk)
    g = s.acquire(["g"], "A", 30, "L1")
    d = s.dispatch("L1", "A", g.fences)
    live = s.check("g", g.fences["g"])
    clk.t += 31
    dead = s.check("g", g.fences["g"])
    renew_late = s.renew("L1", "A", g.fences)
    check("V-LEASE-EXPIRY-FENCES", d.ok and live.ok and not dead.ok and not renew_late.ok,
          "live fence accepted before expiry; the same fence refused after it; no late renew",
          f"d={d} live={live} dead={dead} renew={renew_late}")
    state = s.snapshot()["leases"]["L1"]["state"]
    check("V-LEASE-EXPIRY-RECORDED", state == EXPIRED, "expiry is a journal record", state)

    # --- the Jepsen case: paused holder wakes while a NEW holder owns the class ---
    nb = s.acquire(["g"], "B", 30, "L2")
    s.dispatch("L2", "B", nb.fences)
    ghost = s.check("g", g.fences["g"])
    newer = s.check("g", nb.fences["g"])
    check("V-LEASE-STALE-VS-NEW-OWNER", not ghost.ok and ghost.reason == "stale_fence" and newer.ok,
          "the woken holder's fence is refused while the new holder's is accepted",
          f"ghost={ghost} newer={newer}")

    # --- holder-only renew, fence-matched ---------------------------------------
    clk = Clock()
    s, _ = fresh(clk)
    g = s.acquire(["g"], "A", 30, "L1")
    s.dispatch("L1", "A", g.fences)
    other = s.renew("L1", "B", g.fences)
    stale = s.renew("L1", "A", {"g": g.fences["g"] - 1})
    clk.t += 20
    mine = s.renew("L1", "A", g.fences)
    check("V-LEASE-HOLDER-ONLY", other.reason == "not_holder" and stale.reason == "stale_fence"
          and mine.ok and mine.deadline == clk.t + 30,
          "another holder and a stale fence are refused; the holder's renew moves the deadline",
          f"other={other} stale={stale} mine={mine}")

    # --- a restart never extends a deadline ------------------------------------
    clk = Clock()
    s, d = fresh(clk)
    g = s.acquire(["g"], "A", 30, "L1")
    first = s.dispatch("L1", "A", g.fences).deadline
    clk.t += 25
    s2 = LeaseStore(d, min_ttl_s=10, clock=clk)
    kept = s2.snapshot()["leases"]["L1"]["deadline"]
    clk.t += 6
    gone = s2.check("g", g.fences["g"])
    check("V-LEASE-RESTART-NO-EXTEND", kept == first and not gone.ok,
          "a reloaded store keeps the absolute deadline and expires on time",
          f"first={first} kept={kept} gone={gone}")

    # --- consume is absorbing -----------------------------------------------------
    s, _ = fresh()
    g = s.acquire(["g"], "A", 30, "L1")
    s.dispatch("L1", "A", g.fences)
    cons = s.consume("L1", "A", g.fences)
    again = s.dispatch("L1", "A", g.fences)
    check("V-LEASE-CONSUME-ABSORBING", cons.ok and cons.state == CONSUMED and not again.ok,
          "a consumed lease cannot be dispatched again", f"cons={cons} again={again}")

    # --- a replayed acquire returns the original grant, never a second one -------
    s, _ = fresh()
    one = s.acquire(["g"], "A", 30, "L1")
    two = s.acquire(["g"], "A", 30, "L1")
    snap = s.snapshot()
    check("V-LEASE-REPLAY-IDEMPOTENT", two.ok and two.fences == one.fences
          and snap["records"] == 1, "the same request replayed adds no record", f"{snap}")

    # --- torn tail: ignored, isolated, never merged with the next record ----------
    s, d = fresh()
    s.acquire(["g"], "A", 30, "L1")
    with open(d / store_mod.JOURNAL, "ab") as fh:
        fh.write(b'{"seq":2,"op":"rel')           # a write that died mid-record
    s2 = LeaseStore(d, min_ttl_s=10, clock=Clock())
    r2 = s2.acquire(["h"], "B", 30, "L2")
    s3 = LeaseStore(d, min_ttl_s=10, clock=Clock())
    snap = s3.snapshot()
    check("V-LEASE-TORN-TAIL", r2.ok and snap["records"] == 2 and snap["torn_records"] == 1,
          "a torn record is skipped and the next append lands on its own line",
          f"r2={r2} snap={snap}")

    # --- a sequence gap is corruption, not silence ---------------------------------
    s, d = fresh()
    s.acquire(["g"], "A", 30, "L1")
    with open(d / store_mod.JOURNAL, "ab") as fh:
        fh.write(json.dumps({"seq": 5, "op": "release", "lease_id": "L1"}).encode() + b"\n")
    try:
        LeaseStore(d, min_ttl_s=10).snapshot()
        _fail("V-LEASE-SEQ-GAP", "a gap in seq was accepted")
    except JournalCorrupt:
        _ok("V-LEASE-SEQ-GAP", "a gap in seq raises JournalCorrupt")

    # --- filesystem guard -----------------------------------------------------------
    here = filesystem_type(Path(tempfile.gettempdir()))
    check("V-LEASE-FS-DETECTED", bool(here) and fs_refusal(here) == "",
          f"this host's temp filesystem is detected and allowed ({here!r})",
          f"detected {here!r}")
    check("V-LEASE-FS-REFUSED", all(fs_refusal(t) for t in ("nfs", "nfs4", "overlay", "fuse.sshfs",
                                                             "cifs", ""))
          and fs_refusal("ext4") == "" and fs_refusal("ntfs") == "",
          "network/overlay/unknown filesystems refused; ext4 and ntfs allowed", "predicate wrong")
    orig = store_mod.filesystem_type
    store_mod.filesystem_type = lambda p: "nfs4"
    try:
        LeaseStore(tempfile.mkdtemp(), min_ttl_s=10)
        _fail("V-LEASE-FS-CONSTRUCT", "store opened on nfs4")
    except UnsupportedFilesystem:
        _ok("V-LEASE-FS-CONSTRUCT", "the constructor refuses an nfs4 root")
    finally:
        store_mod.filesystem_type = orig

    # --- real two-process race: exactly one grant ------------------------------------
    d = Path(tempfile.mkdtemp(prefix="lease-race-"))
    go = d / "go"
    child = (
        "import sys,time,json;sys.path.insert(0,sys.argv[1]);"
        "from pathlib import Path;from modules.lease import LeaseStore;"
        "s=LeaseStore(sys.argv[2],min_ttl_s=10);go=Path(sys.argv[2])/'go'\n"
        "while not go.exists(): time.sleep(0.001)\n"
        "r=s.acquire(['gpu'],sys.argv[3],30,sys.argv[3]);print(json.dumps({'ok':r.ok,'why':r.reason}))"
    )
    procs = [subprocess.Popen([sys.executable, "-c", child, str(ROOT), str(d), f"H{i}"],
                              stdout=subprocess.PIPE, text=True) for i in range(6)]
    time.sleep(1.5)
    go.write_text("1")
    outs = [json.loads(p.communicate(timeout=60)[0].strip().splitlines()[-1]) for p in procs]
    wins = sum(o["ok"] for o in outs)
    held = sum(o["why"] == "held" for o in outs)
    check("V-LEASE-RACE-ONE-WINNER", wins == 1 and held == 5,
          "six processes released together: one grant, five 'held'", f"outs={outs}")

    # --- the exclusive section itself: a held lock blocks a second process ------------
    # The race above can pass by luck when interpreter start-up serialises the children,
    # so the lock is also proven deterministically: a child holds it for 2 s.
    d = Path(tempfile.mkdtemp(prefix="lease-lock-"))
    LeaseStore(d, min_ttl_s=10)
    holder = (
        "import sys,time;sys.path.insert(0,sys.argv[1]);from pathlib import Path;"
        "from modules.lease import LeaseStore;s=LeaseStore(sys.argv[2],min_ttl_s=10)\n"
        "with s._lock:\n (Path(sys.argv[2])/'inside').write_text('1'); time.sleep(2.0)\n"
    )
    hp = subprocess.Popen([sys.executable, "-c", holder, str(ROOT), str(d)])
    t0 = time.monotonic()
    while not (d / "inside").exists() and time.monotonic() - t0 < 30:
        time.sleep(0.01)
    inside = (d / "inside").exists()
    t1 = time.monotonic()
    got = LeaseStore(d, min_ttl_s=10).acquire(["gpu"], "P", 30, "LP")
    waited = time.monotonic() - t1
    hp.wait(timeout=30)
    check("V-LEASE-LOCK-BLOCKS", inside and got.ok and waited >= 1.0,
          f"an acquire while another process holds the section waits for it ({waited:.2f}s)",
          f"inside={inside} got={got} waited={waited:.2f}s")

    total = passes + fails
    print(f"LEASE_PASS={passes}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
