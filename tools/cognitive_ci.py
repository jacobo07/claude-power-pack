#!/usr/bin/env python3
"""cognitive_ci.py -- CDC C7: release-blocking cognitive regression gate. Design: vault/programs/cdc/C7-decision.md.

  cognitive_ci.py --measure [--root R]      print the metric table (JSON)
  cognitive_ci.py --certify [--root R]      3 runs -> vault/programs/cdc/cognitive-baseline.json
  cognitive_ci.py --check   [--root R]      exit 0 GREEN / OPEN, 1 RED (unjustified regression)

Deterministic, no model call. Kill switch CPP_COG_CI=off. Fails OPEN on its own error, never on a regression.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

PROG = Path("vault/programs/cdc")
BASELINE = PROG / "cognitive-baseline.json"
BUDGET = PROG / "cognitive-budget-changes.json"

ALWAYS_ON, PER_ROTATION, PER_SPAWN, ZERO = "ALWAYS_ON", "PER_ROTATION", "PER_SPAWN", "ZERO"
TOL = {ALWAYS_ON: (0.005, 64), PER_ROTATION: (0.05, 0), PER_SPAWN: (0.05, 0), ZERO: (0.0, 0)}
LAT_FACTOR, LAT_ABS_MS = 5.0, 50.0

STATUS_PATHS = ("tools/programme_status.py", "tools/check_hook_status.py")
WAIT_PATHS = ("tools/mission_sleep.py",)
MODEL_CALL = re.compile(r"anthropic|messages\.create|[\"']claude(?:\.exe)?[\"']\s*,\s*[\"'](?:-p|--print)|\bclaude\s+-p\b")
RESIDENT = re.compile(r"\bPopen\s*\(|DETACHED_PROCESS|CREATE_NEW_CONSOLE|while\s+True\s*:")
CTX_LINE = re.compile(r"additionalContext")
FIXED_CLAIMS = {"claims": [
    {"id": "a", "class": "deterministic"}, {"id": "b", "class": "known_transform"},
    {"id": "c", "class": "bounded_coding"}, {"id": "d", "class": "novel"}, {"id": "e", "class": "satisfied"}]}
FIXED_ROUTE = {"envelope": {"target": 1_000_000, "warn": 1_500_000, "stop": 2_000_000, "calls": 10},
               "workers": [{"name": "w", "profile": "top-level-worker", "calls": 6, "packet": 2000}]}


def _size(p: Path) -> int:
    return p.stat().st_size if p.is_file() else 0


def _tree_size(d: Path, pat: str) -> int:
    return sum(_size(p) for p in sorted(d.glob(pat))) if d.is_dir() else 0


def _fm_desc_bytes(d: Path, pat: str) -> int:
    n = 0
    for p in sorted(d.glob(pat)) if d.is_dir() else []:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
        if m:
            d_ = re.search(r"^description:\s*(.*)$", m.group(1), re.M)
            n += len(p.parent.name if p.name == "SKILL.md" else p.stem) + (len(d_.group(1)) if d_ else 0)
    return n


def _hook_ctx_bytes(root: Path) -> int:
    n = 0
    for p in sorted((root / "hooks").glob("*.js")) if (root / "hooks").is_dir() else []:
        try:
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if CTX_LINE.search(ln):
                    n += len(ln.strip())
        except OSError:
            pass
    return n


def _scan(root: Path, rels, rx) -> int:
    n = 0
    for r in rels:
        p = root / r
        if p.is_file():
            n += len(rx.findall(p.read_text(encoding="utf-8", errors="replace")))
    return n


def measure(root=ROOT, latency_n: int = 20) -> dict:
    """metric -> {"value", "class", "blast"}. Reads only declared inputs under `root` (fixed-work by construction)."""
    root = Path(root)
    m = {}

    def put(k, v, cls, blast):
        m[k] = {"value": v, "class": cls, "blast": blast}

    put("floor.claude_md_bytes", _size(root / "CLAUDE.md"), "size", ALWAYS_ON)
    put("floor.rules_bytes", _tree_size(root / "rules", "**/*.md"), "size", ALWAYS_ON)
    put("floor.hook_context_bytes", _hook_ctx_bytes(root), "size", ALWAYS_ON)
    put("floor.skill_listing_bytes", _fm_desc_bytes(root / "skills", "*/SKILL.md"), "size", ALWAYS_ON)
    put("floor.agent_listing_bytes", _fm_desc_bytes(root / "agents", "*.md"), "size", ALWAYS_ON)
    import route_admission as ra
    import cost_to_completion as ctc
    import rollover
    fl_path = root / "vault" / "config" / "route-floors.json"
    floors = ra.load_floors(fl_path)
    for name, prof in sorted(floors["profiles"].items()):
        put("admission.floor." + name, int(prof["floor"]), "size", PER_SPAWN)
    c = ctc.compile_cost(FIXED_CLAIMS, floors)
    put("ctc.candidate_tokens", c["candidate"]["tokens"], "size", PER_SPAWN)
    put("ctc.p95_tokens", c["percentiles"]["P95"], "size", PER_SPAWN)
    cap = rollover.compile_capsule("cog-ci", "C:/fx", None, goal="g", next_items=["n1"], summary="s")
    put("capsule.bytes", len(json.dumps(cap, sort_keys=True)), "size", PER_ROTATION)
    put("capsule.bootstrap_bytes", len(rollover.bootstrap(cap)), "size", PER_ROTATION)
    put("status.model_call_sites", _scan(root, STATUS_PATHS, MODEL_CALL), "count", ZERO)
    put("wait.resident_sites", _scan(root, WAIT_PATHS, RESIDENT), "count", ZERO)
    best = None
    for _ in range(latency_n):
        t = time.perf_counter()
        ra.admit(FIXED_ROUTE, floors, root=root)
        d = (time.perf_counter() - t) * 1000
        best = d if best is None or d < best else best
    put("admission.latency_ms", round(best, 3), "latency", PER_SPAWN)
    return m


def certify(root=ROOT, runs: int = 3) -> dict:
    rs = [measure(root) for _ in range(runs)]
    out = {}
    for k in rs[0]:
        vals = [r[k]["value"] for r in rs if k in r]
        out[k] = {"value": max(vals) if rs[0][k]["class"] == "latency" else vals[0], "noise": round(max(vals) - min(vals), 3),
                  "class": rs[0][k]["class"], "blast": rs[0][k]["blast"]}
    return {"schema": 1, "runs": runs, "ts": int(time.time()), "metrics": out}


def limit(b: dict) -> float:
    """Highest value that is still not a regression."""
    v, noise = b["value"], b.get("noise", 0)
    if b["blast"] == ZERO:
        return 0
    if b["class"] == "latency":
        return max(v * LAT_FACTOR, v + LAT_ABS_MS) + noise
    pct, floor = TOL[b["blast"]]
    return v + max(v * pct, floor) + noise


def evaluate(cur: dict, base: dict, budget=()) -> dict:
    """Pure. regressions = over limit; justified = covered by a budget entry (allowed_max, reason, owner)."""
    reg, just = [], []
    ent = {}
    for e in budget or ():
        if isinstance(e, dict) and e.get("metric") and str(e.get("reason", "")).strip() and str(e.get("owner", "")).strip():
            ent[e["metric"]] = e
    for k, b in sorted(base["metrics"].items()):
        if k not in cur:
            continue
        v = cur[k]["value"]
        if v <= limit(b):
            continue
        row = {"metric": k, "baseline": b["value"], "value": v, "limit": limit(b), "blast": b["blast"]}
        e = ent.get(k)
        if b["blast"] != ZERO and e and isinstance(e.get("allowed_max"), (int, float)) and v <= e["allowed_max"]:
            just.append(dict(row, reason=e["reason"], owner=e["owner"]))
        else:
            reg.append(row)
    return {"status": "RED" if reg else "GREEN", "regressions": reg, "justified": just}


def check(root=ROOT, env=None) -> dict:
    env = os.environ if env is None else env
    if env.get("CPP_COG_CI", "").lower() == "off":
        return {"status": "OFF"}
    root = Path(root)
    try:
        bp = root / BASELINE
        if not bp.is_file():
            return {"status": "OPEN", "reason": "NO_BASELINE"}
        base = json.loads(bp.read_text(encoding="utf-8-sig"))
        bud_p = root / BUDGET
        budget = json.loads(bud_p.read_text(encoding="utf-8-sig")) if bud_p.is_file() else []
        if isinstance(budget, dict):
            budget = budget.get("changes", [])
        return evaluate(measure(root), base, budget)
    except Exception as e:  # own failure never blocks a landing
        return {"status": "OPEN", "reason": "INSTRUMENT_ERROR", "detail": repr(e)[:300]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--measure", action="store_true")
    g.add_argument("--certify", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    if a.measure:
        print(json.dumps(measure(a.root), indent=1))
        return 0
    if a.certify:
        d = certify(a.root)
        p = Path(a.root) / BASELINE
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8", newline="\n")
        print("certified %d metrics -> %s" % (len(d["metrics"]), p))
        return 0
    r = check(a.root)
    print(json.dumps(r, indent=1))
    return 1 if r["status"] == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())
