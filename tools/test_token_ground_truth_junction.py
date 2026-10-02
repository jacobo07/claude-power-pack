#!/usr/bin/env python3
"""V-TGTJX-* gates: token_ground_truth reads each transcript store once.

`projects/C--Users-User-Apps-mcp-video-analyzer` is a directory junction to the
PP project dir (RCA s16). Measured 2026-10-02 on this host: the two iterators
yielded 152 top-level and 258 total transcripts twice. analyze() and
today_output_tokens() have no call dedup, so every alias doubled them;
window_usage() keys id-less calls by path, so those doubled too. usage_index
fixed the same defect in f234580; this pins the sibling reader.

Each gate compares a store holding an alias against the same store without it.
Hermetic; no model call. When the junction cannot be created the run is
INCONCLUSIVE (exit 2), never a pass."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import token_ground_truth as tgt  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
NOW = datetime.fromtimestamp(T0 + 2 * 3600, timezone.utc)


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(mid, h, sess):
    o = {"type": "assistant", "timestamp": iso(h), "sessionId": sess,
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
    # one call with an id, one without (the id-less key embeds the file path)
    (d / f"{sess}.jsonl").write_text(asst("m" + sess, 1.1, sess) + asst(None, 1.2, sess),
                                     encoding="utf-8")
    (d / sess / "subagents" / "agent-a.jsonl").write_text(asst("s" + sess, 1.15, sess),
                                                           encoding="utf-8")
    return d


def store(root: Path, alias: bool) -> Path | None:
    proj = root / "projects"
    proj.mkdir(parents=True)
    real = build(proj, "C--zreal", "S1")
    build(proj, "C--other", "S2")             # a distinct dir must stay distinct
    if alias and not junction(proj / "C--alias", real):   # lists BEFORE C--zreal
        return None
    return proj


def snapshot(proj: Path) -> dict:
    a = tgt.analyze(proj, now=NOW.replace(tzinfo=None))
    return {"top": sorted(p.name for p in tgt.iter_transcripts(proj)),
            "all": sorted((p.name, s) for p, s in tgt.iter_transcripts_with_subagents(proj)),
            "analyze_out": a["lifetime"]["output_tokens"], "files_total": a["files_total"],
            "window": tgt.window_usage(24, proj, now=NOW)}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        aliased = store(Path(td) / "a", alias=True)
        if aliased is None:
            print("INCONCLUSIVE: could not create a directory junction (mklink /J)")
            return 2
        clean = store(Path(td) / "c", alias=False)

        # Control: the fixture really holds an alias the naive walk can see.
        dirs = [d for d in aliased.iterdir() if d.is_dir()]
        ok("V-TGTJX-FIXTURE", len(dirs) == 3,
           f"{len(dirs)} dirs listed, 2 distinct stores (alias + real + other)")

        want, got = snapshot(clean), snapshot(aliased)
        ok("V-TGTJX-CONTROL", want["top"] == ["S1.jsonl", "S2.jsonl"]
           and want["window"] and want["window"]["calls"] == 6,
           f"no-alias store: top={want['top']} calls={want['window'] and want['window']['calls']}")
        ok("V-TGTJX-TOP", got["top"] == want["top"], f"{got['top']} vs {want['top']}")
        ok("V-TGTJX-SUB", got["all"] == want["all"], f"{len(got['all'])} vs {len(want['all'])}")
        ok("V-TGTJX-ANALYZE", (got["analyze_out"], got["files_total"])
           == (want["analyze_out"], want["files_total"]),
           f"output {got['analyze_out']} vs {want['analyze_out']}, "
           f"files {got['files_total']} vs {want['files_total']}")
        ok("V-TGTJX-WINDOW-IDLESS", got["window"] == want["window"],
           f"calls {got['window'] and got['window']['calls']} vs {want['window']['calls']}")

        # A junction to a dir OUTSIDE the store is a distinct store: still read once.
        outside = build(Path(td) / "elsewhere", "C--ext", "S3")
        if junction(aliased / "C--ext", outside):
            names = [p.name for p in tgt.iter_transcripts(aliased)]
            ok("V-TGTJX-OUTSIDE", names.count("S3.jsonl") == 1, f"S3 seen {names.count('S3.jsonl')}x")
        else:
            ok("V-TGTJX-OUTSIDE", False, "could not create the outside junction")

    print(f"TGT_JUNCTION_PASS={PASS}/{PASS + FAIL}  threshold={PASS + FAIL}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
