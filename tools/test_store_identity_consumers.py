#!/usr/bin/env python3
"""V-SIC-* gates: every ACCOUNTING consumer of ~/.claude/projects reads a store once (plan s14 S1).

`projects/C--Users-User-Apps-mcp-video-analyzer` is a directory junction to the
PP project dir. Measured 2026-10-02 on the live store before this fix: the
tis_observed scan shape yielded 152 transcripts twice, co_12 counted 2,275
sessions for 2,123 distinct ids, sovereign_miner's recursive glob yielded 273
files twice, and budget_monitor counted 1,378 programmatic calls over 7 days
where 1,313 exist (+65, 4.95 %).

Identity is typed: per-call and per-file readers dedupe the STORE by resolved
path (tis_observed.store_dirs); co_12 counts SESSIONS, so it dedupes by session
id, the rule cognitive_os.scheduler and token_autopsy already follow.

Each gate compares a store holding an alias against the same store without it.
Hermetic; no model call. When a junction cannot be created the run is
INCONCLUSIVE (exit 2), never a pass."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "modules" / "cognitive_os"))

import tis_observed as tob  # noqa: E402
import budget_monitor  # noqa: E402
import sovereign_miner as sm  # noqa: E402
import co_12_telemetry as co12  # noqa: E402

PASS = FAIL = 0
NOW = datetime.now(timezone.utc)
S1, S2, S3 = ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222",
              "33333333-3333-3333-3333-333333333333")


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def line(mid, mins_ago, sess):
    ts = (NOW - timedelta(minutes=mins_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    o = {"type": "assistant", "timestamp": ts, "sessionId": sess, "entrypoint": "sdk-cli",
         "message": {"model": "claude-opus-5-5", "content": [],
                     "usage": {"input_tokens": 1, "cache_read_input_tokens": 100,
                               "cache_creation_input_tokens": 0, "output_tokens": 5}}}
    if mid:
        o["message"]["id"] = mid
        o["requestId"] = "r" + mid
    return json.dumps(o) + "\n"


def junction(link: Path, target: Path) -> bool:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0 and link.is_dir()


def build(proj: Path, name: str, sess: str) -> Path:
    d = proj / name
    (d / sess / "subagents").mkdir(parents=True)
    (d / f"{sess}.jsonl").write_text(line("m" + sess[:4], 60, sess) + line(None, 50, sess),
                                     encoding="utf-8")
    (d / sess / "subagents" / "agent-a.jsonl").write_text(line("s" + sess[:4], 55, sess),
                                                           encoding="utf-8")
    return d


def store(root: Path, alias: bool) -> Path | None:
    proj = root / "projects"
    proj.mkdir(parents=True)
    real = build(proj, "C--zreal", S1)
    build(proj, "C--other", S2)
    if alias:
        if not junction(proj / "C--alias", real):          # lists BEFORE C--zreal
            return None
        outside = build(root / "elsewhere", "C--ext", S3)   # junction OUT of the store
        if not junction(proj / "C--ext", outside):
            return None
    else:
        build(proj, "C--ext", S3)                           # same content, no alias
    return proj


def measure(proj: Path) -> dict:
    tob.PROJECTS_DIR = proj
    dirs = tob._project_dirs(SimpleNamespace(project_dir=None, all_projects=True))
    tis = tob.summarize(tob.scan(dirs))
    budget = budget_monitor._aggregate_observed(7, None)
    sm.PROJECTS_DIR = str(proj)
    sm.STATS.clear()
    sm.mine_transcripts()
    return {"tis_calls": tis["calls"], "tis_sub": tis["subagent_calls"],
            "tis_sessions": tis["sessions"], "budget_calls": budget.get("calls"),
            "co12_sessions": co12.loop_boundedness(proj)["sessions"],
            "miner_files": sm.STATS["files_total"]}


def main() -> int:
    saved_tis, saved_sm = tob.PROJECTS_DIR, sm.PROJECTS_DIR
    try:
        with tempfile.TemporaryDirectory() as td:
            aliased = store(Path(td) / "a", alias=True)
            if aliased is None:
                print("INCONCLUSIVE: could not create a directory junction (mklink /J)")
                return 2
            clean = store(Path(td) / "c", alias=False)

            dirs = [d for d in aliased.iterdir() if d.is_dir()]
            ok("V-SIC-FIXTURE", len(dirs) == 4, f"{len(dirs)} dirs listed: alias, real, other, ext")

            sd = tob.store_dirs(aliased) if hasattr(tob, "store_dirs") else []
            ok("V-SIC-STORE-DIRS", len(sd) == 3 and any(p.name == "C--ext" for p in sd),
               f"{len(sd)} stores; outside junction kept={any(p.name == 'C--ext' for p in sd)}")

            want, got = measure(clean), measure(aliased)
            ok("V-SIC-CONTROL", want == {"tis_calls": 6, "tis_sub": 3, "tis_sessions": 3,
                                         "budget_calls": 9, "co12_sessions": 3,
                                         "miner_files": 6}, f"clean store: {want}")
            for k, gate in (("tis_calls", "V-SIC-TIS-ALLPROJECTS"),
                            ("budget_calls", "V-SIC-BUDGET-PROGRAMMATIC"),
                            ("co12_sessions", "V-SIC-CO12-SESSIONS"),
                            ("miner_files", "V-SIC-MINER-FILES")):
                ok(gate, got[k] == want[k], f"{got[k]} vs {want[k]}")
    finally:
        tob.PROJECTS_DIR, sm.PROJECTS_DIR = saved_tis, saved_sm

    print(f"STORE_IDENTITY_CONSUMERS_PASS={PASS}/{PASS + FAIL}  threshold={PASS + FAIL}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
