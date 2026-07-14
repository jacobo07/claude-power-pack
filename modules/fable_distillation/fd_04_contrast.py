#!/usr/bin/env python3
"""fd_04_contrast.py -- the cross-model contrast instrument (FD-04's missing half).

fd_04_prover can prove that a deposited claim is FACTUALLY TRUE (a file exists, a
pattern matches). It cannot prove that the claim is PORTABLE -- that a cheaper
model, given the same evidence, reaches the same judgment. Those are different
questions and only the second one measures frontier residue.

This module runs the second one. It poses a deposited judgment as a cold question
to a cheaper substrate (`claude -p --model <m>`, no tools, hooks disabled), scores
the answer against a deterministic rubric of required elements, and hands the
verdict to fd_04_prover.record_cross_model -- the single ledger authority. The
instrument spawns; the prover records. Neither does the other's job.

Rubric discipline (absolute, never a ratio): an element is HIT when any of its
patterns matches the answer; the model REPRODUCED the judgment only when EVERY
element is hit. A case with zero required elements is an ERROR, not a vacuous
pass -- an empty conjunction is the classic silent-true.

Both poles must be reachable or the rubric is not measuring anything, so every run
is bookended by two controls: the deposit's own claim MUST score REPRODUCED
(positive -- else the rubric is impossible and a model failure means nothing) and
an empty answer MUST score FAILED (negative -- else the rubric is vacuous). A run
whose controls do not hold is discarded before any model is judged.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_04_prover import (  # noqa: E402
    _load_deposits, record_cross_model)

# Substrate ladder, cheapest first. The cheapest model that reproduces a judgment
# is the one the capability retires to -- so the order here IS the retirement
# preference, not a display detail.
_LADDER = (("sonnet", "small-model"), ("opus", "mid-model"))

_CLI_TIMEOUT_S = 240
_ANSWER_CAP = 60_000            # chars of a model answer the rubric will scan
_NO_TOOLS = ("Bash", "Read", "Write", "Edit", "Glob", "Grep", "Agent",
             "WebFetch", "WebSearch", "Task", "NotebookEdit")


# --------------------------------------------------------------------------- #
# Rubric -- deterministic, no model judges another model.
# --------------------------------------------------------------------------- #
def score(answer: str, required_elements: list) -> dict:
    """Score one answer. REPRODUCED requires every element hit (absolute).

    Returns verdict + the exact elements missing, so a FAILED verdict names what
    the cheaper model did not reach -- that residue is the deliverable.
    """
    if not isinstance(required_elements, list) or not required_elements:
        return {"verdict": "ERROR", "hits": 0, "total": 0, "missing": [],
                "note": "case has no required_elements -- an empty conjunction "
                        "would score any answer as reproduced"}
    text = (answer or "")[:_ANSWER_CAP]
    hit_ids, missing = [], []
    for el in required_elements:
        eid = str(el.get("id", "?"))
        pats = el.get("patterns") or []
        found = any(re.search(p, text, re.IGNORECASE | re.DOTALL)
                    for p in pats if isinstance(p, str) and p)
        (hit_ids if found else missing).append(eid)
    total = len(required_elements)
    hits = len(hit_ids)
    if hits == total:
        verdict = "REPRODUCED"
    elif hits == 0:
        verdict = "FAILED"
    else:
        verdict = "PARTIAL"
    return {"verdict": verdict, "hits": hits, "total": total,
            "hit_ids": hit_ids, "missing": missing}


def controls_hold(case: dict) -> dict:
    """Both poles reachable? Positive: the deposit's own claim must REPRODUCE.
    Negative: an empty answer must FAIL. A rubric failing either is not a rubric.
    """
    els = case.get("required_elements") or []
    pos = score(case.get("gold_answer") or "", els)
    neg = score("", els)
    ok = (pos.get("verdict") == "REPRODUCED" and neg.get("verdict") == "FAILED")
    return {"ok": ok, "positive": pos, "negative": neg}


# --------------------------------------------------------------------------- #
# Substrate runner -- an isolated child: no tools, no hooks, outside the repo.
# --------------------------------------------------------------------------- #
def ask_model(prompt: str, model: str, *, timeout: int = _CLI_TIMEOUT_S) -> dict:
    """Run one cold question on one substrate. Never raises: a dead child is a
    recorded failure, never a silent pass."""
    settings = None
    try:
        tmp = Path(tempfile.mkdtemp(prefix="fd04_contrast_"))
        settings = tmp / "settings.json"
        settings.write_text(json.dumps({"hooks": {}, "disableAllHooks": True}),
                            encoding="utf-8")
        env = {**os.environ, "PP_FRONTIER_SESSION": "0"}
        cmd = ["claude", "-p", prompt, "--model", model,
               "--settings", str(settings),
               "--disallowedTools", *_NO_TOOLS]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, cwd=str(tmp),
                              env=env, stdin=subprocess.DEVNULL, check=False)
        if proc.returncode != 0:
            return {"ok": False, "answer": "",
                    "note": f"exit {proc.returncode}: {(proc.stderr or '')[:300]}"}
        return {"ok": True, "answer": proc.stdout or ""}
    except subprocess.TimeoutExpired:
        return {"ok": False, "answer": "", "note": f"timeout after {timeout}s"}
    except Exception as e:  # noqa: BLE001 -- a broken child proves nothing
        return {"ok": False, "answer": "", "note": f"{type(e).__name__}: {e}"}


# --------------------------------------------------------------------------- #
# The contrast run.
# --------------------------------------------------------------------------- #
def contrast_case(case: dict, *, models=None, timeout: int = _CLI_TIMEOUT_S) -> dict:
    """Pose one case to each substrate (cheapest first) and score every answer.

    Every substrate is always asked: a full row is what makes the residual map a
    measurement instead of an early exit.
    """
    ctrl = controls_hold(case)
    if not ctrl["ok"]:
        return {"fingerprint": case.get("fingerprint"), "verdict": "ERROR",
                "controls": ctrl, "results": [],
                "note": "controls did not hold -- rubric discarded before judging "
                        "any model (impossible or vacuous)"}
    ladder = [(m, t) for m, t in _LADDER
              if models is None or m in models]
    results = []
    for model, target in ladder:
        run = ask_model(case.get("prompt", ""), model, timeout=timeout)
        sc = score(run["answer"], case.get("required_elements") or [])
        results.append({"model": model, "substrate": target,
                        "verdict": sc["verdict"] if run["ok"] else "FAILED",
                        "hits": sc.get("hits", 0), "total": sc.get("total", 0),
                        "missing": sc.get("missing", []),
                        "answer_chars": len(run["answer"] or ""),
                        "note": run.get("note", "")})
    return {"fingerprint": case.get("fingerprint"), "verdict": "OK",
            "controls": ctrl, "results": results}


def load_cases(path: str) -> list:
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    data = json.loads(raw.lstrip("﻿"))
    return data if isinstance(data, list) else []


def run(repo: str, cases_path: str, *, models=None, sid: str = "",
        state_dir=None, record: bool = True, timeout: int = _CLI_TIMEOUT_S) -> dict:
    """Contrast every case, record each verdict through the prover, and return the
    residual map: which judgments a cheaper substrate reproduced, and which did not.
    """
    deposited = {d.get("fingerprint") for d in _load_deposits(repo, state_dir)}
    rows, residue, retired = [], [], []
    for case in load_cases(cases_path):
        fp = case.get("fingerprint")
        if fp not in deposited:
            rows.append({"fingerprint": fp, "verdict": "ERROR",
                         "note": "not in the deposits ledger -- contrast only "
                                 "covers deposited claims"})
            continue
        out = contrast_case(case, models=models, timeout=timeout)
        if out["verdict"] == "OK" and record:
            out["recorded"] = record_cross_model(
                repo, fp, results=out["results"], sid=sid, state_dir=state_dir)
        reproduced = [r for r in out.get("results", [])
                      if r["verdict"] == "REPRODUCED"]
        (retired if reproduced else residue).append(fp)
        rows.append(out)
    return {"cases": len(rows), "rows": rows,
            "retired_to_cheaper": retired, "frontier_residue": residue}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="FD-04 cross-model contrast harness")
    ap.add_argument("--repo", default=str(_PP_ROOT))
    ap.add_argument("--cases", default=str(_PP_ROOT / "vault" / "fd04" /
                                           "contrast_cases.json"))
    ap.add_argument("--state-dir", default=None)
    ap.add_argument("--models", nargs="*", default=None,
                    help="subset of the ladder (default: all)")
    ap.add_argument("--sid", default="")
    ap.add_argument("--timeout", type=int, default=_CLI_TIMEOUT_S)
    ap.add_argument("--controls-only", action="store_true",
                    help="validate every rubric without spending a model call")
    ap.add_argument("--no-record", action="store_true")
    args = ap.parse_args(argv)

    if args.controls_only:
        out = [{"fingerprint": c.get("fingerprint"), **controls_hold(c)}
               for c in load_cases(args.cases)]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if all(o["ok"] for o in out) else 1

    out = run(args.repo, args.cases, models=args.models, sid=args.sid,
              state_dir=args.state_dir, record=not args.no_record,
              timeout=args.timeout)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
