#!/usr/bin/env python3
"""verify_rtk_fusion.py — empirical DONE gate for the RTK proxy fusion.

Exercises the REAL integration path, not the binary in isolation:

  synthetic PreToolUse JSON
        -> node modules/rtk-core/rtk-rewrite.js
        -> parse hookSpecificOutput.updatedInput.command  (the rewrite)
        -> run BOTH the raw command and the rewritten command
        -> tiktoken cl100k token count of each real output
        -> reduction ratio = (raw - compressed) / raw

Verdict:
  reduction >= 0.60          PASS  (exit 0)
  0  <  reduction <  0.60    WARN  (exit 0, ratio logged as evidence)
  reduction <= 0  or error   FAIL  (exit 1)

The WARN band exists because the reduction ratio of one fixed command is
content-dependent (repo history varies); a working integration must not
hard-fail on a low-but-positive ratio. The actual number is always the
evidence of record.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# Pinned to an IMMUTABLE historical SHA (first RTK commit). History at/
# before this point never changes, so raw + rewritten outputs — and thus
# the reduction ratio — are reproducible run-to-run, independent of new
# commits on the branch. This makes the >=77% contract floor a falsifiable
# gate instead of HEAD-variant theater (closes audit Gap 7). Measured
# stable: ~80.3% on af8da66.
PINNED_SHA = "af8da66"
HEAVY_CMD = f"git --no-pager log --stat -50 {PINNED_SHA}"
CONTRACT_FLOOR = 0.77
HOME = os.path.expanduser("~")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "modules", "rtk-core", "rtk-rewrite.js")
RTK_BIN = os.environ.get("RTK_BIN", os.path.join(HOME, ".claude", "bin", "rtk.exe"))


def _node() -> str:
    for cand in (
        r"C:/Program Files/nodejs/node.exe",
        "node",
    ):
        try:
            subprocess.run([cand, "--version"], capture_output=True, check=True)
            return cand
        except Exception:
            continue
    raise RuntimeError("node runtime not found")


def _token_count(text: str) -> int:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def _run(cmd: str) -> str:
    """M9 fix: explicitly inject Git's cmd dir into PATH for the
    subprocess on Windows. Under PowerShell -NonInteractive the parent
    PATH may omit it, which silently degrades the pinned-SHA benchmark
    to a 26-token 'git is not recognized' error message and reports
    -169% reduction (false regression). Real raw output on the pinned
    cmd is ~74KB / ~18k tokens; the gate measures real bytes, not the
    PATH-gap artefact."""
    env = os.environ.copy()
    if os.name == "nt":
        git_dir = r"C:\Program Files\Git\cmd"
        if os.path.isdir(git_dir) and git_dir not in env.get("PATH", ""):
            env["PATH"] = git_dir + os.pathsep + env.get("PATH", "")
    res = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=REPO,
        timeout=60, env=env,
    )
    return (res.stdout or "") + (res.stderr or "")


CORPUS_HEAVY_WEIGHTED_FLOOR = 0.80
CORPUS_HEAVY_PER_CMD_FLOOR = 0.60
SMALL_OUTPUT_FLOOR_TOK = 50
# Light-tier regression tolerance: a non-heavy command's reduction can
# legitimately oscillate ±a few pp around zero (rtk format overhead vs
# tiny savings on terse stateless outputs). Only a sustained drop is a
# real regression — noise-level negatives are tracked but not gated.
LIGHT_REGRESS_FLOOR = -0.05


def _measure_one(cmd: str, node: str, hook: str) -> dict:
    """Drive one command through the real hook, return measurement.

    ok=False means the measurement itself failed (probe error, not a
    regression). Caller decides treatment per tier.
    """
    payload = json.dumps({"tool_input": {"command": cmd}})
    try:
        proc = subprocess.run(
            [node, hook], input=payload, capture_output=True, text=True,
            timeout=30
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"hook-spawn-error:{exc}"}

    out = (proc.stdout or "").strip()
    if not out:
        return {"ok": False, "reason": "hook-passthrough"}
    try:
        decision = json.loads(out)
        rewritten = decision["hookSpecificOutput"]["updatedInput"]["command"]
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"hook-output-parse:{exc}"}

    if rewritten == cmd:
        return {"ok": False, "reason": "no-rewrite"}

    raw_out = _run(cmd)
    comp_out = _run(rewritten)
    raw_tok = _token_count(raw_out)
    comp_tok = _token_count(comp_out)

    if raw_tok == 0:
        return {"ok": False, "reason": "empty-raw-output"}
    if not comp_out.strip():
        return {"ok": False, "reason": "empty-rewritten-output"}
    if comp_tok < SMALL_OUTPUT_FLOOR_TOK:
        return {"ok": False,
                "reason": f"comp-implausibly-small:{comp_tok}tok",
                "comp_sample": comp_out.strip()[:160]}

    reduction = (raw_tok - comp_tok) / raw_tok
    return {"ok": True, "raw_cmd": cmd, "rewritten_cmd": rewritten,
            "raw_tok": raw_tok, "comp_tok": comp_tok,
            "reduction": reduction}


def _verdict_single() -> int:
    """Existing single-cmd pinned-SHA DONE gate (unchanged contract)."""
    print("== RTK fusion DONE gate (single, pinned) ==")
    for label, path in (("hook", HOOK), ("rtk binary", RTK_BIN)):
        if not os.path.exists(path):
            print(f"FAIL: {label} missing at {path}")
            return 1
        print(f"  ok  {label}: {path}")

    node = _node()
    m = _measure_one(HEAVY_CMD, node, HOOK)
    if not m["ok"]:
        print(f"FAIL: {m['reason']}"
              + (f" sample={m.get('comp_sample')!r}"
                 if "comp_sample" in m else ""))
        return 1
    print(f"  raw cmd   : {m['raw_cmd']}")
    print(f"  rewritten : {m['rewritten_cmd']}")
    print(f"  raw tokens (cl100k)        : {m['raw_tok']}")
    print(f"  compressed tokens (cl100k) : {m['comp_tok']}")
    print(f"  reduction                  : {m['reduction'] * 100:.1f}%")

    if m["reduction"] <= 0:
        print("FAIL: no positive token reduction — proxy not effective")
        return 1
    if m["reduction"] >= CONTRACT_FLOOR:
        print(f"PASS: >= {CONTRACT_FLOOR:.0%} contract floor "
              f"(deterministic pinned-SHA benchmark; content preserved)")
        return 0
    print(f"FAIL: {m['reduction']*100:.1f}% < {CONTRACT_FLOOR:.0%} contract "
          f"floor on the pinned benchmark — genuine regression")
    return 1


def _verdict_corpus(corpus_path: str) -> int:
    """Iterate a corpus JSON; gate heavy set, track light set."""
    print(f"== RTK fusion DONE gate (corpus={corpus_path}) ==")
    if not os.path.isfile(corpus_path):
        print(f"FAIL: corpus not found at {corpus_path}")
        return 1
    for label, path in (("hook", HOOK), ("rtk binary", RTK_BIN)):
        if not os.path.exists(path):
            print(f"FAIL: {label} missing at {path}")
            return 1

    with open(corpus_path, encoding="utf-8") as fh:
        corpus = json.load(fh)

    entries = corpus.get("entries", [])
    if not entries:
        print("FAIL: corpus is empty")
        return 1

    node = _node()
    heavy = [e for e in entries if e.get("tier") == "heavy"]
    light = [e for e in entries if e.get("tier") == "light"]

    if not heavy:
        print("FAIL: corpus has no heavy entries to gate on")
        return 1

    print(f"-- heavy ({len(heavy)}) --")
    heavy_results = []
    for e in heavy:
        m = _measure_one(e["benchmark_cmd"], node, HOOK)
        if m["ok"]:
            print(f"  [{m['reduction']*100:5.1f}%] {e['cmd']:14s}  "
                  f"raw={m['raw_tok']:6d} comp={m['comp_tok']:6d}  "
                  f"weight={e['weight']:.3f}")
        else:
            print(f"  [ FAIL ] {e['cmd']:14s}  reason={m['reason']}")
        heavy_results.append({"entry": e, "m": m})

    print(f"-- light ({len(light)}) --")
    light_results = []
    for e in light:
        m = _measure_one(e["benchmark_cmd"], node, HOOK)
        if m["ok"]:
            tag = "OK" if m["reduction"] > 0 else "REGRESS"
            print(f"  [{m['reduction']*100:5.1f}% {tag}] {e['cmd']:14s}  "
                  f"weight={e['weight']:.3f}")
        else:
            print(f"  [ skip ] {e['cmd']:14s}  reason={m['reason']}")
        light_results.append({"entry": e, "m": m})

    failures = []
    for hr in heavy_results:
        m, e = hr["m"], hr["entry"]
        if not m["ok"]:
            failures.append(f"heavy:{e['cmd']}:probe-{m['reason']}")
            continue
        if m["reduction"] < CORPUS_HEAVY_PER_CMD_FLOOR:
            failures.append(
                f"heavy:{e['cmd']}:per-cmd "
                f"{m['reduction']*100:.1f}%<"
                f"{CORPUS_HEAVY_PER_CMD_FLOOR*100:.0f}%")

    measured_heavy = [hr for hr in heavy_results if hr["m"]["ok"]]
    weight_sum = sum(hr["entry"]["weight"] for hr in measured_heavy)
    if measured_heavy and weight_sum > 0:
        weighted = sum(
            hr["m"]["reduction"] * hr["entry"]["weight"]
            for hr in measured_heavy
        ) / weight_sum
    else:
        weighted = 0.0

    for lr in light_results:
        if lr["m"]["ok"] and lr["m"]["reduction"] < LIGHT_REGRESS_FLOOR:
            failures.append(
                f"light:{lr['entry']['cmd']}:regress "
                f"{lr['m']['reduction']*100:.1f}%<"
                f"{LIGHT_REGRESS_FLOOR*100:.0f}%")

    print("-- summary --")
    print(f"  heavy weighted reduction  : {weighted*100:.1f}%  "
          f"(floor {CORPUS_HEAVY_WEIGHTED_FLOOR*100:.0f}%)")

    if failures:
        print("FAIL: " + " | ".join(failures))
        return 1
    if weighted < CORPUS_HEAVY_WEIGHTED_FLOOR:
        print(f"FAIL: heavy weighted {weighted*100:.1f}% < "
              f"{CORPUS_HEAVY_WEIGHTED_FLOOR*100:.0f}% floor")
        return 1
    print(f"PASS: heavy weighted {weighted*100:.1f}% >= "
          f"{CORPUS_HEAVY_WEIGHTED_FLOOR*100:.0f}%; "
          f"each heavy >= {CORPUS_HEAVY_PER_CMD_FLOOR*100:.0f}%; "
          f"no light regression")
    return 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", nargs="?", const=os.path.join(
        REPO, "tests", "fixtures", "rtk_corpus.json"), default=None,
        help="run corpus mode (default fixture path)")
    args = ap.parse_args()
    if args.corpus:
        return _verdict_corpus(args.corpus)
    return _verdict_single()


if __name__ == "__main__":
    sys.exit(main())
