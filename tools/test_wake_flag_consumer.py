#!/usr/bin/env python3
"""V-WAKE-* gates for the WAKE_FLAG consumer (tranche context-runtime-3, unit S3).

Drives the REAL producer (`wake_check.evaluate`, gate overridden by PP_WAKE_GATE_CMD) into the
REAL consumer (`wake_check.consume`) against a real gsd_x GoalLog in a temp goals root.
Red poles: flag absent -> goal unchanged; flag or goal state unreadable -> refusal receipt, goal unchanged.

    python tools/test_wake_flag_consumer.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import wake_check as wc                              # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402

REPO_ID = "3a" * 20


def gate_cmd(code: int) -> str:
    return json.dumps([sys.executable, "-c", "import sys; sys.exit(%d)" % code])


def make_goal(base: Path, gid: str) -> gl.GoalLog:
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, "wake goal %s" % gid, ["the wake is acted on"], [], {"paths": ["."]})
    return lg


def snapshot(lg: gl.GoalLog) -> dict:
    return {p.name: p.read_bytes() for p in sorted(lg.dir.iterdir())}


def main() -> int:
    for k in ("PP_WAKE_FLAG", "PP_WAKE_RECEIPTS"):
        os.environ.pop(k, None)
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print("  %s %s: %s" % ("PASS" if cond else "FAIL", g, ev if cond else why))

    tmp = Path(tempfile.mkdtemp(prefix="wake_consumer_"))
    base, rdir, flag = tmp / "goals", tmp / "receipts", tmp / "WAKE_FLAG.json"

    # Red pole 1: producer decides DORMANT -> no flag -> goal unchanged, no receipt.
    lg = make_goal(base, "wake-e2e")
    before = snapshot(lg)
    os.environ["PP_WAKE_GATE_CMD"] = gate_cmd(0)
    prod = wc.evaluate(flag)
    r = wc.consume(lg, flag, rdir)
    check("V-WAKE-ABSENT", prod["wake"] is False and not flag.exists() and r["outcome"] == "NO_FLAG"
          and snapshot(lg) == before and not rdir.exists(),
          "dormant producer wrote no flag; consumer NO_FLAG; goal bytes unchanged; no receipt",
          "prod=%s r=%s" % (prod, r))

    # Green path: producer decides WAKE -> flag -> consumer appends a wake event -> receipt.
    os.environ["PP_WAKE_GATE_CMD"] = gate_cmd(1)
    prod = wc.evaluate(flag)
    n0 = len(lg.read())
    r = wc.consume(lg, flag, rdir)
    evs = lg.read()
    last = evs[-1]
    rec = json.loads(Path(r.get("receipt", tmp / "none")).read_text(encoding="utf-8")) if r.get("receipt") else {}
    check("V-WAKE-E2E", prod["wake"] and r["outcome"] == "MOVED" and len(evs) == n0 + 1
          and last.type == "wake" and last.data.get("reason") == "MATERIAL_RISE" and last.seq == r.get("seq")
          and rec.get("outcome") == "MOVED" and rec.get("event_digest") == last.digest,
          "flag -> wake event seq %s (MATERIAL_RISE) -> receipt %s" % (last.seq, Path(r.get("receipt", "")).name),
          "prod=%s r=%s last=%s" % (prod, r, last))
    check("V-WAKE-FLAG-RETIRED", not flag.exists() and flag.with_name("WAKE_FLAG.consumed.json").is_file(),
          "consumed flag renamed aside", "flag still present or not retired")
    try:
        gc.project(lg)
        ok, why = True, ""
    except Exception as exc:                          # the owner's projection must tolerate the event
        ok, why = False, "%s: %s" % (type(exc).__name__, exc)
    check("V-WAKE-PROJECT", ok, "contract.project reads the goal with the wake event", why)

    # Idempotency: the same flag again is DUPLICATE, goal unchanged.
    flag.write_bytes(flag.with_name("WAKE_FLAG.consumed.json").read_bytes())
    before = snapshot(lg)
    r = wc.consume(lg, flag, rdir)
    check("V-WAKE-IDEMPOTENT", r["outcome"] == "DUPLICATE" and snapshot(lg) == before,
          "re-delivered flag -> DUPLICATE, goal bytes unchanged", "r=%s" % r)

    # Red pole 2a: flag present but unreadable -> refusal recorded, goal unchanged.
    flag.write_text("{not json", encoding="utf-8")
    before = snapshot(lg)
    r = wc.consume(lg, flag, rdir)
    rec = json.loads(Path(r["receipt"]).read_text(encoding="utf-8")) if r.get("receipt") else {}
    check("V-WAKE-REFUSE-FLAG", r["outcome"] == "REFUSED" and rec.get("outcome") == "REFUSED"
          and snapshot(lg) == before and flag.exists(),
          "unreadable flag -> REFUSED receipt (%s), goal unchanged, flag kept" % rec.get("cause", "")[:40],
          "r=%s" % r)

    # Red pole 2b: real producer flag, goal state unreadable -> refusal recorded, goal unchanged.
    flag.unlink()
    lg2 = make_goal(base, "wake-corrupt")
    (lg2.dir / "000001.json").write_text("{", encoding="utf-8")
    before = snapshot(lg2)
    prod = wc.evaluate(flag)
    r = wc.consume(lg2, flag, rdir)
    rec = json.loads(Path(r["receipt"]).read_text(encoding="utf-8")) if r.get("receipt") else {}
    check("V-WAKE-REFUSE-STATE", prod["wake"] and r["outcome"] == "REFUSED"
          and "GoalLogCorrupt" in rec.get("cause", "") and snapshot(lg2) == before and flag.exists(),
          "corrupt goal log -> REFUSED receipt (GoalLogCorrupt), goal bytes unchanged, flag kept",
          "r=%s" % r)

    check("V-WAKE-CHAIN", len(lg.read()) == n0 + 1, "goal log still verifies as one chain",
          "chain length changed")
    os.environ.pop("PP_WAKE_GATE_CMD", None)
    print("WAKE_CONSUMER_PASS=%d/%d" % (len(passes), len(passes) + len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
