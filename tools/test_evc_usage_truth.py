#!/usr/bin/env python
"""V-EVC-* gates for the usage-truth reader (EVC phase 1, plan 01).

Purpose: pin mission_spend.usage_truth, the one canonical reader of a mission's spend (last copy per
(message.id, requestId) per transcript, per-column maximum across transcripts), and the int projection
processed_tokens. Each later plan of the phase appends its own section and REQUIRED names.

Hermetic: every state directory is pointed at a fresh temp dir BEFORE any project import. Final line:
    EVC_USAGE_TRUTH_PASS=p/t threshold=t/t NOT_OBSERVED=k

Mutation drill: GSD_MISSION_DRILL_DIR holding mutated copies is imported first (position 0 of sys.path).
Use isolated copies only; the live files are never edited to prove a gate can go red.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REAL_STATE = os.environ.get("GSD_LONG_RUN_STATE_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "state")

TMP = tempfile.mkdtemp(prefix="evc-usage-truth-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_USAGE_INDEX"] = str(Path(TMP) / "usage_index.sqlite")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ.pop("CPP_MISSION_RENEW", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
# Order matters: plan 02 appends mission_surface and gsd_mission AFTER these (gsd_mission resets sys.path[0]).
import tis_observed  # noqa: E402,F401
import usage_index  # noqa: E402,F401
import mission_spend as ms  # noqa: E402

passes = fails = notobs_n = 0
SEEN: list[str] = []
REQUIRED = ["V-EVC-STREAM-LAST", "V-EVC-STREAM-LAST-CONTROL"]
CREATED = 1_800_000_000.0          # 2027-01-15T08:00:00Z
WORK_DIR = "/home/kobii/missions/evc-fix"


def check(gate, cond, ev=""):
    global passes, fails
    SEEN.append(gate)
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def notobs(gate, ev=""):
    global notobs_n
    notobs_n += 1
    print(f"NOT_OBSERVED {gate} {ev}")


def ts(minute=0, sec=0):
    return f"2027-01-15T08:{minute:02d}:{sec:02d}Z"


def aline(mid, req, t, inp=0, cw=0, cr=0, out=0, cc=None, model="claude-sonnet-5-5"):
    u = {"input_tokens": inp, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr,
         "output_tokens": out}
    if cc:
        u["cache_creation"] = cc
    o = {"type": "assistant", "timestamp": t, "message": {"id": mid, "model": model, "usage": u}}
    if req is not None:
        o["requestId"] = req
    if mid is None:
        del o["message"]["id"]
    return json.dumps(o) + "\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def mission_rec():
    return {"mission_id": "m-evcfix", "work_dir": WORK_DIR, "created_at": CREATED}


def build_fixs(root: Path):
    d = root / ms.encode_cwd(WORK_DIR)
    f = write(d / "s1.jsonl",
              aline("m1", "r1", ts(0, 10), inp=1, cr=100, out=5)
              + aline("m1", "r1", ts(0, 11), inp=1, cr=100, out=50))
    return f


def section_reader():
    root = Path(TMP) / "projects_fixs"
    f = build_fixs(root)
    rec = mission_rec()
    sess = ({"s1"}, set())
    pt = ms.processed_tokens(rec, root, None, sess)
    ut = ms.usage_truth(rec, root, None, sess) if hasattr(ms, "usage_truth") else None
    tree_p = (ut or {}).get("tree", {}).get("processed")
    check("V-EVC-STREAM-LAST", pt == 151 and tree_p == 151, f"processed_tokens={pt} tree.processed={tree_p}")
    first = ms._file_tokens(f, None)
    check("V-EVC-STREAM-LAST-CONTROL", first == 106 and first < 151 and 151 - first == 45,
          f"_file_tokens={first} diff={151 - first}")


def main() -> int:
    section_reader()
    missing = [g for g in REQUIRED if g not in SEEN]
    check("V-EVC-ALL-GATES-RAN", not missing, f"missing={missing}")
    print(f"EVC_USAGE_TRUTH_PASS={passes}/{passes + fails} threshold={len(REQUIRED) + 1}/{len(REQUIRED) + 1} "
          f"NOT_OBSERVED={notobs_n}")
    return 0 if fails == 0 and passes >= len(REQUIRED) + 1 else 1


if __name__ == "__main__":
    sys.exit(main())
