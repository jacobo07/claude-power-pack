#!/usr/bin/env python
"""gate_compound78.py -- pillar L gate: compound steps 7+8 (`compound/steps78.py`) proven on a TEMP copy.

Never writes the live `~/.claude/state/compound-learnings.json`: its sha256 is taken before and after,
and a difference fails the gate. Every case runs on a fresh copy of the live bytes in a temp dir.

Cases (each must hold):
  advance      cursor merged for one project: last_run_iso set, directive_count 0, every other key of that
               entry kept, every other project kept byte-for-byte in value (case-variant ids included),
               marker gone, lock released, backup == original bytes
  no_marker    absent marker is not a failure
  rollback     marker unlink fails (the marker is a non-empty directory): state restored BYTE-IDENTICAL to the
               original, marker still there, lock released
  busy         a fresh lock held by someone else: nothing written, state byte-identical
  stale        a lock older than STALE_S is recovered and the advance succeeds
  live_intact  live state sha256 identical before and after the gate

`--break-rollback` makes the rollback case skip restoring (by patching `write_atomic` to a no-op on its
second call); it exists only to drive the red branch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "compound"))
LIVE = Path.home() / ".claude" / "state" / "compound-learnings.json"
PP_MAIN = Path.home() / ".claude" / "skills" / "claude-power-pack"   # the checkout the learnings belong to


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--break-rollback", action="store_true")
    a = ap.parse_args(argv)
    import steps78

    if not LIVE.is_file():
        print(f"GATE_COMPOUND78=FAIL live state missing: {LIVE}")
        return 1
    live_before = sha(LIVE)
    original = LIVE.read_bytes()
    doc = json.loads(original.decode("utf-8-sig"))
    pids = list(doc.get("projects", {}))
    if len(pids) < 2:
        print("GATE_COMPOUND78=FAIL live state has < 2 projects; the merge case cannot be judged")
        return 1
    folded = {}
    for p in pids:
        folded.setdefault(p.lower(), []).append(p)
    case_pairs = [v for v in folded.values() if len(v) > 1]
    target = case_pairs[0][0] if case_pairs else pids[0]
    results, fails = {}, []

    # Real learning files and the real marker of the main checkout (read only, copied into the temp dir).
    # The marker is transient: a successful /cpp-compound deletes it and the sentinel recreates it later.
    # finalize() only unlinks it and never reads its content, so when it is absent a synthetic marker
    # tests the same transaction. The source is reported so a reader knows which one was judged.
    learn = sorted(PP_MAIN.glob(".claude/cache/learnings/*.md"))
    real_marker = PP_MAIN / "LEARNINGS_PENDING.md"
    if real_marker.is_file():
        marker_bytes, marker_src = real_marker.read_bytes(), "live"
    else:
        marker_bytes, marker_src = b"# Compound Learnings -- Pending Consolidation (synthetic, gate_compound78)\n", "synthetic"
    if not learn:
        print("GATE_COMPOUND78=FAIL real inputs missing: learnings=0")
        return 1
    print(f"  real inputs: {len(learn)} learning files, marker {len(marker_bytes)} bytes (source={marker_src})")

    def fresh(tmp: Path, marker: bool = True):
        st = tmp / "compound-learnings.json"
        st.write_bytes(original)
        mk = tmp / "LEARNINGS_PENDING.md"
        if marker:
            mk.write_bytes(marker_bytes)
        return st, mk

    with tempfile.TemporaryDirectory() as td:
        # advance (cursor = now, as the command does)
        t = Path(td) / "advance"; t.mkdir()
        st, mk = fresh(t)
        r = steps78.finalize(st, target, mk)
        new = json.loads(st.read_text(encoding="utf-8"))
        old_entry = doc["projects"][target]
        e = new["projects"][target]
        cursor = datetime.fromisoformat(e["last_run_iso"].replace("Z", "+00:00")).timestamp()
        regathered = sum(f.stat().st_mtime > cursor for f in learn)
        print(f"  learning files newer than the advanced cursor (would be re-gathered): {regathered}")
        ok = (r["ok"] and regathered == 0 and e["directive_count"] == 0
              and all(e.get(k) == v for k, v in old_entry.items() if k not in ("last_run_iso", "directive_count"))
              and all(new["projects"].get(p) == doc["projects"][p] for p in pids if p != target)
              and set(new["projects"]) == set(pids)
              and {k: v for k, v in new.items() if k != "projects"} == {k: v for k, v in doc.items() if k != "projects"}
              and not mk.exists() and not (t / "compound-learnings.json.lock").exists()
              and (t / "compound-learnings.json.bak").read_bytes() == original)
        results["advance"] = ok
        # no_marker
        t = Path(td) / "nomarker"; t.mkdir()
        st, mk = fresh(t, marker=False)
        results["no_marker"] = steps78.finalize(st, target, mk)["ok"]
        # rollback
        t = Path(td) / "rollback"; t.mkdir()
        st, mk = fresh(t, marker=False)
        mk.mkdir()
        (mk / "x").write_text("x", encoding="utf-8")
        real = steps78.write_atomic
        if a.break_rollback:
            calls = {"n": 0}

            def broken(path, data):
                calls["n"] += 1
                if calls["n"] == 1:
                    real(path, data)
            steps78.write_atomic = broken
            print("  perturbed: rollback restore disabled")
        try:
            r = steps78.finalize(st, target, mk)
        finally:
            steps78.write_atomic = real
        results["rollback"] = (not r["ok"] and r["action"] == "rolled_back" and st.read_bytes() == original
                               and mk.exists() and not (t / "compound-learnings.json.lock").exists())
        # busy
        t = Path(td) / "busy"; t.mkdir()
        st, mk = fresh(t)
        (t / "compound-learnings.json.lock").mkdir()
        r = steps78.finalize(st, target, mk, timeout=0.5)
        results["busy"] = (not r["ok"] and r["action"] == "busy" and st.read_bytes() == original and mk.exists())
        # stale
        t = Path(td) / "stale"; t.mkdir()
        st, mk = fresh(t)
        lk = t / "compound-learnings.json.lock"
        lk.mkdir()
        old = time.time() - steps78.STALE_S - 5
        os.utime(lk, (old, old))
        results["stale"] = steps78.finalize(st, target, mk, timeout=1.0)["ok"] and not mk.exists()

    results["live_intact"] = sha(LIVE) == live_before
    for k, v in results.items():
        print(f"  {'ok  ' if v else 'FAIL'} {k}")
        if not v:
            fails.append(k)
    print(f"  target project {target!r}; case-variant id pairs in live state: {len(case_pairs)}")
    print(f"GATE_COMPOUND78={'PASS' if not fails else 'FAIL'} failures={len(fails)} marker={marker_src}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
