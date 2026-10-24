#!/usr/bin/env python
"""V-ROT-* gates: semantic rotation is reachable before native compaction (flow-compression S1).

Defect (2026-10-24): `--autocompact 250k` compacts at ~217k, under both rotation predicates (the
250k turn-end ceiling and the 40 %-of-1M wall), so 0 rotations / 382 compactions from 10-08.
Pure for the resolver; the wall is driven through the real hooks/mission_wall.js with node.
V-ROT-REPLAY reads the real worker transcript when it exists and is INCONCLUSIVE (not PASS) when not.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="rotation-invariant-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ.pop("CPP_ROTATION_INVARIANT", None)
os.environ.pop("CPP_CE_BASELINE", None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Mutation drill: a directory holding a mutated gsd_mission.py (the env kill switch cannot drill this
# suite -- it is popped above, so a mutant set that way never reaches the code).
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402  -- FIRST: gsd_epoch's own imports would load the real one
import gsd_epoch as ge  # noqa: E402

passes = fails = inconclusive = 0
REPLAY_SID = "8ff5e205-45d5-4bd8-9623-c1f66c3ed48a"


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def wall_hook(marker_wall: dict, resident: int, used_pct: int) -> dict | None:
    """Run hooks/mission_wall.js decide() on a worker whose last model call held `resident` tokens."""
    sid = f"rotinv-{resident}-{used_pct}-{len(json.dumps(marker_wall))}"
    tr = Path(TMP) / f"{sid}.jsonl"
    row = {"type": "assistant", "message": {"model": "claude-sonnet-5-5", "usage": {
        "input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": resident - 10}}}
    tr.write_text(json.dumps({"type": "user"}) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    (Path(TMP) / f"mission-worker-{sid}.json").write_text(json.dumps(
        {"mission_id": "m-rot", "epoch": 1, "wall": marker_wall}), encoding="utf-8")
    ctx = Path(tempfile.gettempdir()) / f"claude-ctx-{sid}.json"
    ctx.write_text(json.dumps({"session_id": sid, "used_pct": used_pct}), encoding="utf-8")
    js = (f"const w=require({json.dumps(str(HERE.parent / 'hooks' / 'mission_wall.js'))});"
          f"process.stdout.write(JSON.stringify(w.decide({{session_id:{json.dumps(sid)},"
          f"transcript_path:{json.dumps(str(tr))}}})))")
    env = {**os.environ, "GSD_AUTORUN_MARKER_DIR": TMP, "GSD_LONG_RUN_STATE_DIR": TMP}
    try:
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, env=env, timeout=60)
        return json.loads(out.stdout or "null")
    finally:
        ctx.unlink(missing_ok=True)


def main() -> int:
    global inconclusive
    base = {"mission_id": "m", "epoch": 1, "resume_command": "/gsd-autonomous --ws w"}

    # V-ROT-POLICY: the policy itself now satisfies the invariant (175k under a 250k line); only the
    # absent token wall is derived on the first launch, nothing is repaired.
    r = gm.resolve_baseline(base)
    inv = r.get("rotation_invariant") or {}
    check("V-ROT-POLICY-SATISFIES", r["continue_max_tokens"] == 175_000 and not inv.get("repaired")
          and inv.get("derived") == {"wall.advisory_tokens": 175_000}, str(inv))
    # V-ROT-REPAIRS-CEILING: the defective 250k/250k shape (the pre-fix policy) is bounded at 0.70 x 250k.
    old_rec = gm.apply_rotation_invariant({"autocompact": "250k", "continue_max_tokens": 250_000})
    check("V-ROT-REPAIRS-CEILING", old_rec["continue_max_tokens"] == 175_000
          and old_rec["rotation_invariant"]["repaired"].get("continue_max_tokens") == [250_000, 175_000],
          str(old_rec.get("rotation_invariant")))
    check("V-ROT-ADDS-TOKEN-WALL", r["wall"].get("advisory_tokens") == 175_000 and r["wall"].get("advisory") == 40.0,
          str(r["wall"]))
    check("V-ROT-BASELINE-RECORDS-FINAL-VALUE", r["baseline"]["values"]["continue_max_tokens"] == 175_000,
          str(r["baseline"]["values"]))

    # V-ROT-IDEMPOTENT: resolving the resolved record changes nothing and repairs nothing new.
    again = gm.resolve_baseline(r)
    check("V-ROT-IDEMPOTENT", again["continue_max_tokens"] == 175_000 and again["wall"] == r["wall"]
          and not again.get("rotation_invariant")
          and again["baseline"]["src"]["continue_max_tokens"].startswith("policy"), str(again.get("baseline")))

    # V-ROT-EXPLICIT-BELOW-KEPT / -ABOVE-REPAIRED: an operator value below the line is respected,
    # one above it is unreachable whoever set it.
    low = gm.resolve_baseline({**base, "continue_max_tokens": 120_000})
    check("V-ROT-EXPLICIT-BELOW-KEPT", low["continue_max_tokens"] == 120_000
          and "continue_max_tokens" not in (low.get("rotation_invariant") or {}).get("repaired", {}), str(low.get("rotation_invariant")))
    big = gm.apply_rotation_invariant({"autocompact": "600k", "continue_max_tokens": 900_000})
    check("V-ROT-EXPLICIT-ABOVE-REPAIRED", big["continue_max_tokens"] == 420_000
          and big["wall"]["advisory_tokens"] == 420_000, str(big.get("rotation_invariant")))

    # V-ROT-KILL-SWITCH (the "never rotates" control): off leaves the defective ordering in place.
    os.environ["CPP_ROTATION_INVARIANT"] = "off"
    off = gm.resolve_baseline(base)
    off_old = gm.apply_rotation_invariant({"autocompact": "250k", "continue_max_tokens": 250_000})
    os.environ.pop("CPP_ROTATION_INVARIANT", None)
    check("V-ROT-KILL-SWITCH", off_old["continue_max_tokens"] == 250_000 and "wall" not in off_old
          and "advisory_tokens" not in (off.get("wall") or {}) and not off.get("rotation_invariant"),
          f"{off_old} {off.get('wall')}")

    # V-ROT-EVIDENCE: the compaction row says WHY it was not a rotation, from both poles.
    comp = {"trigger": "auto", "pre_tokens": 217_245, "post_tokens": 37_509, "duration_ms": 38_947}
    old = ge.compaction_evidence({"autocompact": "250k", "continue_max_tokens": 250_000,
                                  "wall": {"advisory": 40.0}}, comp)
    new = ge.compaction_evidence(r, comp)
    check("V-ROT-EVIDENCE-OLD-UNREACHABLE", old["rotation_verdict"] == "UNREACHABLE" and old["pre_tokens"] == 217_245, str(old))
    check("V-ROT-EVIDENCE-NEW-REACHABLE", new["rotation_verdict"] == "REACHABLE_NOT_TAKEN", str(new))
    check("V-ROT-EVIDENCE-UNMEASURED", ge.compaction_evidence(r, None)["rotation_verdict"] == "UNMEASURED")
    below = ge.compaction_evidence(r, {**comp, "pre_tokens": 150_000})   # e.g. a manual /compact
    check("V-ROT-EVIDENCE-BELOW-BOTH-NOT-REACHABLE", below["rotation_verdict"] == "UNREACHABLE", str(below))

    # V-ROT-IDEMPOTENT-SMALL-LINE (review LOW-1): under an explicit 200k line the policy 175k is bounded
    # to 140k once; the next resolution re-derives the same value and ledgers no repair.
    s1 = gm.resolve_baseline({**base, "autocompact": "200k"})
    s2 = gm.resolve_baseline(s1)
    check("V-ROT-IDEMPOTENT-SMALL-LINE", s1["continue_max_tokens"] == 140_000
          and s1["rotation_invariant"]["repaired"].get("continue_max_tokens") == [175_000, 140_000]
          and s2["continue_max_tokens"] == 140_000 and not s2.get("rotation_invariant"),
          f"{s1.get('rotation_invariant')} {s2.get('rotation_invariant')}")

    # V-ROT-WALL-*: the real hook. 180k resident = 18 % of a 1M window: the percent wall is blind.
    if shutil.which("node"):
        fired = wall_hook({"advisory": 40.0, "advisory_tokens": 175_000}, 180_000, 18)
        check("V-ROT-WALL-TOKENS-FIRES", bool(fired) and fired.get("decision") == "block"
              and "180k tokens resident" in fired.get("reason", ""), str(fired)[:160])
        check("V-ROT-WALL-UNDER-SILENT", wall_hook({"advisory": 40.0, "advisory_tokens": 175_000}, 150_000, 15) is None)
        check("V-ROT-WALL-PCT-ONLY-BLIND", wall_hook({"advisory": 40.0}, 180_000, 18) is None,
              "control: the pre-fix wall cannot see 180k")
        flag = Path(TMP) / "mission-wall-rotinv-180000-18-{}-e1.flag".format(len(json.dumps({"advisory": 40.0, "advisory_tokens": 175_000})))
        data = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
        check("V-ROT-WALL-FLAG-IS-WITNESS", data.get("tokens") == 180_000 and data.get("asked_at", 0) > 0
              and ge.wall_evidence("rotinv-180000-18-" + str(len(json.dumps({"advisory": 40.0, "advisory_tokens": 175_000}))), 1, []) is not None,
              str(data))
    else:
        inconclusive += 1
        print("INCONCLUSIVE V-ROT-WALL-* node not on PATH")

    # V-ROT-REPLAY: on the real 41-compaction worker, the token wall would have been asked before
    # every compaction (a call at >= limit precedes each boundary inside its cycle).
    path = ge._transcript(REPLAY_SID)
    if not path:
        inconclusive += 1
        print(f"INCONCLUSIVE V-ROT-REPLAY transcript {REPLAY_SID} not found")
    else:
        limit, peak, preempted, boundaries = r["wall"]["advisory_tokens"], 0, 0, 0
        for row in ge._rows(path):
            if row.get("type") == "system" and row.get("subtype") == "compact_boundary":
                boundaries += 1
                preempted += 1 if peak >= limit else 0
                peak = 0
                continue
            u = (row.get("message") or {}).get("usage") if row.get("type") == "assistant" else None
            if isinstance(u, dict):
                peak = max(peak, int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
                           + int(u.get("cache_creation_input_tokens") or 0))
        check("V-ROT-REPLAY-WALL-PRECEDES-COMPACTION", boundaries > 0 and preempted == boundaries,
              f"{preempted}/{boundaries} compactions preceded by a call >= {limit}")

    total = passes + fails
    print(f"ROT_PASS={passes}/{total}  inconclusive={inconclusive}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
