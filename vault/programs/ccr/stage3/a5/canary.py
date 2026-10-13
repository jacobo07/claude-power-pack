"""A5 canary: CARRY (fork of a copied Lobby transcript cut at call 40) vs ROT (fresh session from the M1 capsule
under CCR_WORK_UNIT with the CCR mod). Haiku, subscription `claude -p`. 3 runs per arm, interleaved.
The source transcript and the Lobby repo are only read; every run works on copies under ccr-s3-data/a5-work.

    python3 vault/programs/ccr/stage3/a5/canary.py --out vault/programs/ccr/stage3/a5/canary.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "tools"))
import ccr_continuation as cc  # noqa: E402
from ccr_epoch_econ import W_INPUT, W_OUT, W_READ, W_WRITE  # noqa: E402

CLAUDE = str(Path.home() / ".local/bin/claude")          # host 2.1.296 (/usr/local/bin/claude is 2.1.113)
WORK = Path("/home/kobii/missions/ccr-s3-data/a5-work")
SRC_CUT = WORK / "transcript-copies/cb70bd86-e909-470f-b1df-f4f14a9e5706.at40.jsonl"  # copy cut at call 40
REPO = WORK / "canary-repo"
PROJ = Path.home() / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", str(REPO))
MOD = ROOT / "mods/cpp-cognitive-runtime"
OBLIGATION = "continue Ralph epoch m-1d270cd85220-e5 (luckyarena-lobby) at call 40"
TASK = ("Continue this luckyarena-lobby epoch with ONE bounded step and do not edit any file. "
        "From measurement M9 (s_spawn's DECK footprint, per-row outline span in blocks, in "
        "vault/kme/intake/luckyarena-lobby/MEASUREMENTS.md), give the span at row v 55.8 and the maximum span "
        "over all rows. End your reply with exactly one line: ANSWER: <span at v 55.8> <maximum span>")
CHECK = re.compile(r"^ANSWER:\s*18\.9\s+25\.5\s*$", re.M)
RUNAWAY = 1_500_000
MIN_MEM_KB = 4 * 1024 * 1024


def mem_kb() -> int:
    for ln in Path("/proc/meminfo").read_text().splitlines():
        if ln.startswith("MemAvailable:"):
            return int(ln.split()[1])
    return 0


def usage_of(transcript: Path, skip: set[str]) -> tuple[list[dict], set[str]]:
    per, order = {}, []
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            msg = o.get("message") or {}
            mid, u = msg.get("id"), msg.get("usage")
            if o.get("type") != "assistant" or not mid or not u or mid in skip:
                continue
            row = {"inp": u.get("input_tokens") or 0, "cr": u.get("cache_read_input_tokens") or 0,
                   "cw": u.get("cache_creation_input_tokens") or 0, "out": u.get("output_tokens") or 0,
                   "model": msg.get("model")}
            if mid not in per:
                order.append(mid)
                per[mid] = row
            else:
                per[mid] = {k: (max(per[mid][k], row[k]) if k != "model" else row[k]) for k in row}
    return [per[m] for m in order], set(order)


def summarize(calls: list[dict]) -> dict:
    inp, cr, cw, out = (sum(c[k] for c in calls) for k in ("inp", "cr", "cw", "out"))
    return {"calls": len(calls), "inp": inp, "cr": cr, "cw": cw, "out": out, "processed": inp + cr + cw + out,
            "weighted": round(W_INPUT * inp + W_READ * cr + W_WRITE * cw + W_OUT * out, 1),
            "first_ctx": (calls[0]["inp"] + calls[0]["cr"] + calls[0]["cw"]) if calls else 0,
            "models": sorted({c["model"] for c in calls if c.get("model")})}


def run(cmd: list[str], env_extra: dict, prompt: str) -> tuple[dict, float]:
    import os
    env = {**os.environ, **env_extra}
    env.pop("ANTHROPIC_API_KEY", None)                    # subscription only
    t0 = time.time()
    p = subprocess.run(cmd + [prompt], cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    try:
        res = json.loads(p.stdout)
    except ValueError:
        res = {"is_error": True, "result": (p.stdout + p.stderr)[-2000:]}
    return res, round(time.time() - t0, 1)


COMMON = ["--model", "haiku", "--output-format", "json", "--strict-mcp-config", "--max-turns", "6",
          "--allowedTools", "Read,Grep,Glob", "--disallowedTools", "Edit,Write,Bash,NotebookEdit,Agent", "-p"]


def carry(i: int) -> dict:
    cid = str(uuid.uuid4())
    PROJ.mkdir(parents=True, exist_ok=True)
    src = SRC_CUT.read_text(encoding="utf-8")
    old = SRC_CUT.name.split(".")[0]
    lines = [ln for ln in src.splitlines(keepends=True) if not ln.startswith('{"type":"last-prompt"')]
    (PROJ / f"{cid}.jsonl").write_text("".join(lines).replace(old, cid), encoding="utf-8")
    _, prior = usage_of(PROJ / f"{cid}.jsonl", set())
    res, secs = run([CLAUDE, "--resume", cid, "--fork-session"] + COMMON, {}, TASK)
    sid = res.get("session_id")
    calls, _ = usage_of(PROJ / f"{sid}.jsonl", prior) if sid and (PROJ / f"{sid}.jsonl").exists() else ([], set())
    return {"arm": "CARRY", "run": i, "copy_id": cid, "sid": sid, "secs": secs, "res": res, "calls": calls}


def rot(i: int, capsule: str, unit: Path) -> dict:
    res, secs = run([CLAUDE, "--plugin-dir", str(MOD)] + COMMON, {"CCR_WORK_UNIT": str(unit)},
                    capsule + "\n" + TASK)
    sid = res.get("session_id")
    calls, _ = usage_of(PROJ / f"{sid}.jsonl", set()) if sid and (PROJ / f"{sid}.jsonl").exists() else ([], set())
    return {"arm": "ROT", "run": i, "sid": sid, "secs": secs, "res": res, "calls": calls}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", type=int, required=True, help="one interleaved CARRY+ROT round; appends to --out")
    a = ap.parse_args(argv)
    capsule = cc.build(REPO, OBLIGATION, [], SRC_CUT)
    unit = WORK / "unit-a5.json"
    unit.write_text(json.dumps({"class": "read-only-reviewer", "id": "WU-A5-canary"}))
    if Path(a.out).exists():
        out = json.loads(Path(a.out).read_text())
        if out.get("stopped"):
            print("stopped earlier:", out["stopped"])
            return 1
    else:
        out = {"task": TASK, "check": CHECK.pattern, "capsule": capsule, "capsule_rent": cc.rent(capsule),
               "claude": subprocess.run([CLAUDE, "--version"], capture_output=True, text=True).stdout.strip(),
               "runs": []}
    stop = None
    for i in (a.round,):
        for arm in ("CARRY", "ROT"):
            mem = mem_kb()
            if mem < MIN_MEM_KB:
                out["runs"].append({"arm": arm, "run": i, "verdict": f"RAM_HOLD:{mem}kB"})
                continue
            r = carry(i) if arm == "CARRY" else rot(i, capsule, unit)
            s = summarize(r.pop("calls"))
            res = r.pop("res")
            text = res.get("result") or ""
            r.update(s, mem_kb_before=mem, answer_ok=bool(CHECK.search(text)), is_error=bool(res.get("is_error")),
                     subtype=res.get("subtype"), num_turns=res.get("num_turns"), result_tail=text[-400:],
                     cli_usage=res.get("usage"), cli_cost_usd=res.get("total_cost_usd"))
            r["verdict"] = "FAIL:runaway" if s["processed"] > RUNAWAY else ("PASS" if r["answer_ok"] else "FAIL:answer")
            out["runs"].append(r)
            Path(a.out).write_text(json.dumps(out, indent=1))
            print(json.dumps({k: r.get(k) for k in ("arm", "run", "verdict", "calls", "processed", "weighted",
                                                     "first_ctx", "secs", "subtype", "models")}), flush=True)
            if r["verdict"] == "FAIL:runaway":
                stop = f"{arm} run {i} processed {s['processed']}"
                break
        if stop:
            break
    out["stopped"] = stop
    Path(a.out).write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
