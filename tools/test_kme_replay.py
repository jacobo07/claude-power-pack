#!/usr/bin/env python3
"""V-KMER-* gates: the pillar L offline replay ranker (incremental-cognition phase 5, plan 05-01).

Hermetic: every fixture is a synthetic transcript tree built here under a scratch directory. A SKIP or an
INCONCLUSIVE is printed and counted apart; it is never a PASS and never part of the n/m denominator. Every expected
number below is derived by hand in a comment from the models in wiki/tools/kme_replay.py's docstring, never by calling
the module's own arithmetic.

    python3 tools/test_kme_replay.py            run every gate
    python3 tools/test_kme_replay.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import atexit
import contextlib
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for _p in (str(REPO), str(REPO / "wiki" / "tools"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import kme_pillars as kp  # noqa: E402
import kme_replay as kr  # noqa: E402
from test_kme_pillars import E_BODY, Fx, call, pdir, tree_state, ts, write_frozen  # noqa: E402,F401

SCRIPT = REPO / "wiki" / "tools" / "kme_replay.py"
TMP_ROOT = Path(tempfile.mkdtemp(prefix="kmer-test-"))
_COUNTER = [0]
RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]


def _cleanup() -> None:
    for dp, dns, fns in os.walk(TMP_ROOT):
        for n in dns + fns:
            with contextlib.suppress(OSError):
                os.chmod(os.path.join(dp, n), 0o700)
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)


def scratch(prefix: str = "t") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


# --------------------------------------------------------------------------- gate plumbing
def record(status: str, gate: str, ev: str = "") -> None:
    RESULTS.append((status, gate, str(ev)))
    if not QUIET[0]:
        print(f"{status} {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    """fn returns (True|False|'SKIP'|'INCONCLUSIVE', evidence); an exception is a FAIL naming its class."""
    try:
        res, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read red, never absent
        res, ev = False, f"{exc.__class__.__name__}: {exc}"
    if res in ("SKIP", "INCONCLUSIVE"):
        record(res, gate, ev)
    else:
        record("PASS" if res else "FAIL", gate, ev)


# --------------------------------------------------------------------------- runners
def run_cli(args, cwd=REPO):
    p = subprocess.run([sys.executable, str(SCRIPT)] + list(args), cwd=str(cwd), capture_output=True, text=True,
                       timeout=300)
    return p.returncode, p.stdout, p.stderr


FOLLOW_DEFAULTS = [True]


def run_main(args):
    """In-process kr.main() with stdout/stderr captured, so a drill's monkeypatch reaches it.

    kme_replay reads a frozen file through kp._prepare, which (WR-07) only calls the committed default a default; while
    FOLLOW_DEFAULTS is on this runner points kp.DENOMS_REL at the scratch --frozen-file the call names (same rule and
    reason as test_kme_pillars.run_main)."""
    args = list(args)
    saved = (kp.DENOMS_REL, kp.CE_LEDGER_REL)
    if FOLLOW_DEFAULTS[0] and "--frozen-file" in args:
        kp.DENOMS_REL = args[args.index("--frozen-file") + 1]
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = kr.main(args)
    finally:
        kp.DENOMS_REL, kp.CE_LEDGER_REL = saved
    return rc, out.getvalue(), err.getvalue()


def run_json(args):
    """In-process run with --json; returns (rc, result dict or None, stdout, stderr)."""
    rc, out, err = run_main(list(args) + ["--json"])
    res = None
    for line in out.splitlines():
        if line.startswith("{"):
            res = json.loads(line)
    return rc, res, out, err


def parse_rank(text):
    """(front matter dict of the `key: <json>` lines between the first two `---`, the json block)."""
    lines = text.split("\n")
    assert lines[0] == "---", "front matter missing"
    end = lines.index("---", 1)
    front = {}
    for ln in lines[1:end]:
        k, _, v = ln.partition(": ")
        front[k] = json.loads(v)
    a = text.index("<!-- kmer-json -->") + len("<!-- kmer-json -->")
    b = text.index("<!-- /kmer-json -->")
    return front, json.loads(text[a:b])


def utc_date():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def rank_args(root, out_dir, extra=(), label="FX-R", project="-home-x-kme-fixture"):
    return ["rank", "--denominator", "OTHER", "--label", label, "--select", "all", "--until", "none",
            "--root", str(pdir(root, project)), "--out-dir", str(out_dir)] + list(extra)


def entry(res, cid, key="ranked"):
    return next((e for e in res[key] if e["candidate"] == cid), None)


def close(a, b, tol=1e-6):
    return a is not None and b is not None and abs(a - b) <= tol


# =========================================================================== fixtures
def tracer_fixture(root):
    """The plan's tracer fixture: one thread, five calls, a reread, a retried Bash command."""
    fx = Fx(root)
    fx.human("go", ts(0))
    call(fx, 1, [("t1", "Read", {"file_path": "/x/a.py"})], usage=(10, 1000, 0, 5))
    fx.tool_result("t1", E_BODY, ts(13))
    call(fx, 2, [("t2", "Read", {"file_path": "/x/a.py"})], usage=(10, 0, 3010, 5))
    fx.tool_result("t2", E_BODY, ts(15))
    call(fx, 3, [("t3", "Bash", {"command": "python3 tools/test_x.py", "description": "run"})],
         usage=(10, 0, 4010, 5))
    fx.tool_result("t3", "F" * 300, ts(17))
    call(fx, 4, [("t4", "Bash", {"command": "python3 tools/test_x.py", "description": "again"})],
         usage=(10, 0, 5010, 5))
    fx.tool_result("t4", "F" * 300, ts(19))
    call(fx, 5, (), usage=(10, 0, 5010, 5))
    return fx


# =========================================================================== gate: tracer
def g_tracer_e2e():
    # Hand derivation (never the module's arithmetic):
    #   W = input 50 x 1 + cache_write 1000 x 2 + cache_read (0+3010+4010+5010+5010 = 17,040) x 0.1 + output 25 x 5
    #     = 50 + 2000 + 1704 + 125 = 3,879.0
    #   identical_rereads upper = E hi: t2's result (3,000 chars) sits at call index 2 of 5 calls, resident 3 calls:
    #     (3000 / 3.0) x (2 + 0.1 x 2) = 1000 x 2.2 = 2,200.0
    #   late_rollover upper at G = 2,000: floor F = 10 + 1000 + 0 = 1,010. After call 2 the context is 3,020, growth
    #     2,010 >= 2,000 -> rollover, cut 3,020. Calls 3 and 4 (contexts 4,020 / 5,020) each avoid min(3020 - 1010,
    #     ctx - 1010) = 2,010, entirely cache-read (2,010 < their cache_read) = 201.0 each. Simulated growth after
    #     call 4 = 3,010 - 1,010 = 2,000 -> second rollover, cut 5,020. Call 5 (context 5,020) avoids 4,010 -> 401.0.
    #     201 + 201 + 401 = 803.0, rollovers 2.
    #   unchanged_precondition_retries upper: t4 repeats t3's command with no write between. Its 300-char result is at
    #     call index 4 of 5: resident 1: (300 / 3.0) x 2 = 200.0, plus the issuing message's output 5 / 1 tool_use x 5
    #     = 25.0 -> 225.0.
    root = scratch("tr")
    tracer_fixture(root)
    out_dir = scratch("out")
    rc, out, err = run_cli(rank_args(root, out_dir, ["--rollover-growth", "2000"]))
    files = sorted(out_dir.glob("L-FX-R-*.md"))
    if rc != 0 or len(files) != 1 or files[0].name != f"L-FX-R-{utc_date()}.md":
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-300:]}"
    text = files[0].read_text(encoding="utf-8")
    front, res = parse_rank(text)
    ranked = res["ranked"]
    order = [e["candidate"] for e in ranked]
    want = {"identical_rereads": 2200.0, "late_rollover": 803.0, "unchanged_precondition_retries": 225.0}
    ok = (front.get("instrument") == "wiki/tools/kme_replay.py" and front.get("pillar") == "L"
          and front.get("denominator") == "FX-R" and front.get("evidence_role") == "smoke"
          and front.get("terminal_evidence") is False and front.get("population_match") == "not_frozen"
          and close(front.get("weighted_denominator"), 3879.0) and str(front.get("command", "")).strip() != ""
          and order == ["identical_rereads", "late_rollover", "unchanged_precondition_retries"]
          and [e["rank"] for e in ranked] == [1, 2, 3] and res["unranked"] == []
          and all(close(e["upper_bound_weighted"], want[e["candidate"]]) for e in ranked)
          and all(e["saving_status"] == "upper_bound" for e in ranked)
          and all(abs(e["upper_bound_share"] - e["upper_bound_weighted"] / 3879.0) <= 1e-9 for e in ranked)
          and "KMER ranked=identical_rereads,late_rollover,unchanged_precondition_retries unranked=none" in out)
    return ok, (f"rc={rc} file={files[0].name} order={order} uppers={[e['upper_bound_weighted'] for e in ranked]} "
                f"W={front.get('weighted_denominator')} role={front.get('evidence_role')} "
                f"stdout_last={out.strip().splitlines()[-1][:120] if out.strip() else ''}")


GATES_TRACER = [("V-KMER-TRACER-E2E", g_tracer_e2e)]
GATES = list(GATES_TRACER)


def summary_line() -> str:
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    n = sum(1 for r in counted if r[0] == "PASS")
    m = len(counted)
    sk = sum(1 for r in RESULTS if r[0] == "SKIP")
    inc = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"KMER_PASS={n}/{m}  threshold={m}/{m}  skipped={sk}  inconclusive={inc}"


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    return 0 if counted and all(r[0] == "PASS" for r in counted) else 1


if __name__ == "__main__":
    sys.exit(run_all())
