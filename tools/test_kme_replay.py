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


def sidechain_line(fx, t=40):
    """One usage-bearing inline sidechain assistant line (usage 1 / 100 / 0 / 1) in the main file."""
    return fx._w({"type": "assistant", "isSidechain": True, "timestamp": ts(t), "uuid": "u-sc", "requestId": "rsc",
                  "message": {"id": "sc", "model": "claude-opus-5-5", "role": "assistant", "content": [],
                              "usage": {"input_tokens": 1, "cache_creation_input_tokens": 100,
                                        "cache_read_input_tokens": 0, "output_tokens": 1}}})


def g_contract_e2e():
    # The tracer fixture plus ONE usage-bearing inline sidechain line (1 / 100 / 0 / 1) after call 5. Hand derivation:
    #   W = 3,879.0 (tracer) + input 1 x 1 + cache_write 100 x 2 + output 1 x 5 = 3,879 + 1 + 200 + 5 = 4,085.0 (the
    #   sidechain line is a call of the main bucket: it is IN the population).
    #   identical_rereads: t2's result (3,000 chars) is at call index 2 of 6 calls now: resident 4 ->
    #     (3000 / 3.0) x (2 + 0.1 x 4) = 1000 x 2.3 = 2,300.0.
    #   unchanged_precondition_retries: t4's 300-char result at call index 4 of 6: resident 2 ->
    #     (300 / 3.0) x (2 + 0.1 x 2) = 100 x 2.1 = 210.0 + the issuing message's output 5 / 1 x 5 = 25.0 -> 235.0.
    #   late_rollover: the only session carries an inline sidechain line, so its thread cannot be separated: observability
    #     0.0, UNMEASURED, unranked with no number.
    # Expected: exit 3, one file, ranked = identical_rereads (2,300.0) then unchanged_precondition_retries (235.0),
    # unranked = [late_rollover].
    root = scratch("ce2e")
    fx = tracer_fixture(root)
    sidechain_line(fx)
    out_dir = scratch("out")
    rc, out, err = run_cli(rank_args(root, out_dir, ["--rollover-growth", "2000"], label="FX-C"))
    files = sorted(out_dir.glob("L-FX-C-*.md"))
    if rc != 3 or len(files) != 1:
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-300:]}"
    text = files[0].read_text(encoding="utf-8")
    front, res = parse_rank(text)
    ranked, unranked = res["ranked"], res["unranked"]
    w = 4085.0
    want = {"identical_rereads": 2300.0, "unchanged_precondition_retries": 235.0}
    u = unranked[0] if unranked else {}
    table_rows = [ln for ln in text.split("## Ranking")[1].split("## Unranked")[0].splitlines()
                  if ln.startswith("| ") and not ln.startswith("| rank") and not ln.startswith("|---")]
    unranked_section = text.split("## Unranked")[1].split("## Candidate details")[0]
    last = out.strip().splitlines()[-1] if out.strip() else ""
    ok = (close(front.get("weighted_denominator"), w) and close(res["weighted_denominator"], w)
          and [e["candidate"] for e in ranked] == ["identical_rereads", "unchanged_precondition_retries"]
          and [e["rank"] for e in ranked] == [1, 2]
          and all(close(e["upper_bound_weighted"], want[e["candidate"]]) for e in ranked)
          and all(abs(e["upper_bound_share"] * w - e["upper_bound_weighted"]) <= 1e-9 * max(1.0, w) for e in ranked)
          and [x["candidate"] for x in unranked] == ["late_rollover"] and u.get("status") == "UNMEASURED"
          and "observability" in u.get("reason", "") and u.get("upper_bound_weighted") is None
          and not any("upper" in k or "weighted" in k for k in u)
          and len(table_rows) == 2 and "late_rollover" not in "".join(table_rows)
          and "late_rollover" in unranked_section and "UNMEASURED" in unranked_section
          and front.get("ranked_ids") == res["ranked_ids"] == ["identical_rereads", "unchanged_precondition_retries"]
          and front.get("unranked_ids") == res["unranked_ids"] == ["late_rollover"]
          and last.startswith("KMER ranked=identical_rereads,unchanged_precondition_retries unranked=late_rollover "
                              "denominator=FX-C"))
    return bool(ok), (f"rc={rc} unranked=late_rollover W={front.get('weighted_denominator')} "
                      f"ranked={[(e['candidate'], e['upper_bound_weighted']) for e in ranked]} rows={len(table_rows)} "
                      f"stdout_last={last[:110]}")


# =========================================================================== task 2: late_rollover and identical_rereads
def rk(build, extra=(), project="-home-x-kme-fixture", label="FX-R"):
    """build(fx) writes one main-thread transcript after a human line; returns (rc, result, stdout)."""
    root = scratch("rk")
    fx = Fx(root, project=project)
    fx.human("go", ts(0))
    build(fx)
    rc, res, out, _err = run_json(rank_args(root, scratch("out"), extra, label=label, project=project))
    return rc, res, out


def seq_calls(fx, usages, start=1):
    """Plain calls (no tool use) c<start>.. with the given usage tuples."""
    for i, u in enumerate(usages):
        call(fx, start + i, usage=u)


TRACER_USAGES = [(10, 1000, 0, 5), (10, 0, 3010, 5), (10, 0, 4010, 5), (10, 0, 5010, 5), (10, 0, 5010, 5)]


def g_rollover_positive():
    # The tracer's call sequence alone, G = 2,000: floor 1,010; rollover after call 2 (growth 2,010, cut 3,020); calls 3
    # and 4 avoid 2,010 each (x 0.1 = 201.0 each); rollover after call 4 (simulated growth 2,000, cut 5,020); call 5
    # avoids 4,010 (401.0). 201 + 201 + 401 = 803.0, 2 rollovers, 1 thread.
    rc, res, _ = rk(lambda fx: seq_calls(fx, TRACER_USAGES), ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    ok = (rc == 0 and e is not None and close(e["upper_bound_weighted"], 803.0)
          and e["details"]["rollovers"] == 2 and e["details"]["threads"] == 1)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} details={e and {k: e['details'][k] for k in ('rollovers', 'threads')}}"


def g_rollover_below_threshold():
    # Same file at G = 10,000: the largest growth above the floor is 5,020 - 1,010 = 4,010 < 10,000: never a rollover,
    # a MEASURED zero that ranks (never unranked).
    rc, res, _ = rk(lambda fx: seq_calls(fx, TRACER_USAGES), ["--rollover-growth", "10000"])
    e = entry(res, "late_rollover")
    ok = (rc == 0 and e is not None and e["upper_bound_weighted"] == 0.0 and e["details"]["rollovers"] == 0
          and entry(res, "late_rollover", "unranked") is None)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} ranked={res['ranked_ids']} unranked={res['unranked_ids']}"


def g_rollover_floor():
    # Floor F = 50,010 (call 1 = 10 + 50,000 + 0). Call 2: context 52,020, growth 2,010 >= 2,000 -> rollover, cut 52,020
    # (call 2's own avoided = cut(F) - F = 0). Call 3: context 53,020 -> avoided = min(52,020 - 50,010, 53,020 - 50,010)
    # = 2,010, wholly cache-read (cache_read 53,010) -> 201.0. A floor-blind model avoids the whole cut (52,020) on calls
    # 2 and 3 and reads a figure about fifty times larger.
    rc, res, _ = rk(lambda fx: seq_calls(fx, [(10, 50000, 0, 5), (10, 0, 52010, 5), (10, 0, 53010, 5)]),
                    ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    return rc == 0 and e is not None and close(e["upper_bound_weighted"], 201.0), \
        f"rc={rc} upper={e and e['upper_bound_weighted']} (floor-blind would read about 10,000)"


def g_rollover_segment():
    # Call 1 (10,1000,0,5): F 1,010. Call 2 (10,0,3010,5): context 3,020, growth 2,010 -> rollover, cut 3,020. Then a real
    # compaction; calls 3 and 4 = (10,0,1500,5), context 1,510 each. The policy restarts at the compaction (cut = F):
    # avoided 0, upper 0.0. A segment-blind model keeps cut 3,020 and avoids min(2,010, 500) = 500 x 0.1 = 50 on each of
    # calls 3 and 4 = 100.0.
    def build(fx):
        call(fx, 1, usage=(10, 1000, 0, 5))
        call(fx, 2, usage=(10, 0, 3010, 5))
        fx.compact(ts(15))
        call(fx, 3, usage=(10, 0, 1500, 5))
        call(fx, 4, usage=(10, 0, 1500, 5))
    rc, res, _ = rk(build, ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    return rc == 0 and e is not None and e["upper_bound_weighted"] == 0.0 and e["details"]["rollovers"] == 1, \
        f"rc={rc} upper={e and e['upper_bound_weighted']} rollovers={e and e['details']['rollovers']} (segment-blind reads 100.0)"


def g_rollover_synthetic_skipped():
    # A first assistant row with model <synthetic> and zero usage, then the tracer's calls: the floor is the first REAL
    # call (1,010), so the figure is the tracer's 803.0 (a synthetic floor of 0 would read a growth of 3,020 at call 2 and
    # a very different figure).
    def build(fx):
        fx.assistant("m0", "r0", (0, 0, 0, 0), ts(10), model="<synthetic>")
        seq_calls(fx, TRACER_USAGES)
    rc, res, _ = rk(build, ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    return rc == 0 and e is not None and close(e["upper_bound_weighted"], 803.0), \
        f"rc={rc} upper={e and e['upper_bound_weighted']}"


def g_rollover_subagent_thread():
    # Main thread = the tracer sequence (803.0 at G = 2,000). A subagent file is its own thread with its own floor: calls
    # (10,2000,0,5) F 2,010; (10,0,4010,5) context 4,020 growth 2,010 -> rollover, cut 4,020; (10,0,5010,5) context 5,020
    # avoids min(4,020 - 2,010, 5,020 - 2,010) = 2,010 x 0.1 = 201.0. Total 803 + 201 = 1,004.0, 3 rollovers, 2 threads.
    def build(fx):
        seq_calls(fx, TRACER_USAGES)
        sub = fx.subagent("a1", "Explore")
        sub.human("t", ts(60))
        sub.assistant("x1", "rx1", (10, 2000, 0, 5), ts(61))
        sub.assistant("x2", "rx2", (10, 0, 4010, 5), ts(62))
        sub.assistant("x3", "rx3", (10, 0, 5010, 5), ts(63))
    rc, res, _ = rk(build, ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    d = e["details"] if e else {}
    ok = rc == 0 and e is not None and close(e["upper_bound_weighted"], 1004.0) and d.get("threads") == 2 \
        and d.get("rollovers") == 3
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} threads={d.get('threads')} rollovers={d.get('rollovers')}"


def g_rollover_inline_sidechain_unmeasured():
    def build(inline):
        def b(fx):
            seq_calls(fx, TRACER_USAGES)
            if inline:
                fx._w({"type": "assistant", "isSidechain": True, "timestamp": ts(40), "uuid": "u-sc",
                       "requestId": "rsc", "message": {"id": "sc", "model": "claude-opus-5-5", "role": "assistant",
                                                       "content": [], "usage": {"input_tokens": 1,
                                                                                "cache_creation_input_tokens": 100,
                                                                                "cache_read_input_tokens": 0,
                                                                                "output_tokens": 1}}})
        return b
    rc1, r1, out1 = rk(build(True), ["--rollover-growth", "2000"])
    rc0, r0, _ = rk(build(False), ["--rollover-growth", "2000"])
    u = entry(r1, "late_rollover", "unranked")
    ok = (rc1 == 3 and u is not None and u["status"] == "UNMEASURED" and "observability" in u["reason"]
          and not any("upper" in k or "weighted" in k for k in u)
          and entry(r1, "late_rollover") is None
          and r1["ranked_ids"] == ["identical_rereads", "unchanged_precondition_retries"]
          and "late_rollover" not in "".join(l for l in out1.splitlines() if l.startswith("KMER rank="))
          and rc0 == 0 and entry(r0, "late_rollover") is not None)
    return ok, f"inline: rc={rc1} unranked={r1['unranked']} ranked={r1['ranked_ids']}; clean: rc={rc0} ranked={r0['ranked_ids']}"


def g_rollover_sensitivity():
    # G = 2,000 on the tracer sequence: 803.0 with 2 rollovers; every other G of the sensitivity set (50,000, 100,000,
    # 200,000) exceeds the largest growth (4,010): 0.0 and 0 rollovers.
    rc, res, _ = rk(lambda fx: seq_calls(fx, TRACER_USAGES), ["--rollover-growth", "2000"])
    e = entry(res, "late_rollover")
    sens = e["details"]["sensitivity"] if e else []
    by_g = {x["growth"]: x for x in sens}
    ok = (rc == 0 and sorted(by_g) == sorted(set(kr.ROLLOVER_SENSITIVITY) | {2000}) and len(sens) == len(by_g)
          and close(by_g[2000]["upper_bound_weighted"], 803.0) and by_g[2000]["rollovers"] == 2
          and all(by_g[g]["upper_bound_weighted"] == 0.0 and by_g[g]["rollovers"] == 0 for g in kr.ROLLOVER_SENSITIVITY)
          and close(e["upper_bound_weighted"], by_g[2000]["upper_bound_weighted"]))
    return ok, f"rc={rc} sensitivity={[(x['growth'], x['upper_bound_weighted'], x['rollovers']) for x in sens]}"


def reread_build(fx, second_body=None, edit_between=False):
    call(fx, 1, [("r1", "Read", {"file_path": "/w/f.py"})])
    fx.tool_result("r1", E_BODY, ts(13))
    nxt = 2
    if edit_between:
        call(fx, 2, [("ed", "Edit", {"file_path": "/w/f.py", "old_string": "x", "new_string": "y"})])
        fx.tool_result("ed", "ok", ts(15))
        nxt = 3
    call(fx, nxt, [("r2", "Read", {"file_path": "/w/f.py"})])
    fx.tool_result("r2", second_body if second_body is not None else E_BODY, ts(10 + 2 * nxt + 1))
    call(fx, nxt + 1)


def g_rereads_positive():
    # Read, Read of the same file, one more call: the second result (3,000 chars) is at call index 2 of 3 calls, resident
    # 1; upper = (3000 / 3.0) x (2 + 0.1 x 0) = 2,000.0 (one same-segment identical reread).
    rc, res, _ = rk(lambda fx: reread_build(fx))
    e = entry(res, "identical_rereads")
    ok = rc == 0 and e is not None and close(e["upper_bound_weighted"], 2000.0) \
        and e["events"]["identical_same_segment"] == 1
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} events={e and e['events']}"


def g_rereads_negative():
    changed = ("CHANGED-BODY\n" + E_BODY)[:3000]
    rc1, r1, _ = rk(lambda fx: reread_build(fx, second_body=changed))
    rc2, r2, _ = rk(lambda fx: reread_build(fx, edit_between=True))
    e1, e2 = entry(r1, "identical_rereads"), entry(r2, "identical_rereads")
    ok = (rc1 == 0 and rc2 == 0 and e1 is not None and e2 is not None and e1["upper_bound_weighted"] == 0.0
          and e2["upper_bound_weighted"] == 0.0 and entry(r1, "identical_rereads", "unranked") is None)
    return ok, (f"changed content: rc={rc1} upper={e1 and e1['upper_bound_weighted']}; after an Edit: rc={rc2} "
                f"upper={e2 and e2['upper_bound_weighted']}")


def g_rereads_equals_e():
    # One file read, reread in the same segment, a real compaction, reread again: kme_pillars' E reports an interval
    # whose low bound keeps only the same-segment reread and whose high bound adds the after-compaction one. The rank's
    # identical_rereads upper bound is that high bound (6 decimals), not the low one.
    root = scratch("eq")
    fx = Fx(root)
    fx.human("go", ts(0))
    call(fx, 1, [("r1", "Read", {"file_path": "/w/f.py"})])
    fx.tool_result("r1", E_BODY, ts(13))
    call(fx, 2, [("r2", "Read", {"file_path": "/w/f.py"})])
    fx.tool_result("r2", E_BODY, ts(15))
    call(fx, 3)
    fx.compact(ts(17))
    call(fx, 4, [("r3", "Read", {"file_path": "/w/f.py"})])
    fx.tool_result("r3", E_BODY, ts(19))
    call(fx, 5)
    common = ["--denominator", "OTHER", "--label", "FX-E", "--select", "all", "--until", "none", "--root",
              str(pdir(root)), "--json"]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc_e = kp.main(["e"] + common + ["--out-dir", str(scratch("oute"))])
    e_json = [json.loads(l) for l in out.getvalue().splitlines() if l.startswith("{")]
    rc_r, res, _o, _e = run_json(["rank"] + common[:-1] + ["--out-dir", str(scratch("outr"))])
    if rc_e != 0 or not e_json or rc_r != 0:
        return False, f"rc_e={rc_e} rc_r={rc_r} err={err.getvalue()[-200:]}"
    lo, hi = e_json[0]["numerator"]["weighted_interval"]
    e = entry(res, "identical_rereads")
    ok = e is not None and e["upper_bound_weighted"] == round(hi, 6) and e["upper_bound_weighted"] != round(lo, 6) \
        and hi > lo
    return ok, f"E interval=[{lo}, {hi}] rank upper={e and e['upper_bound_weighted']}"


GATES_ROLLOVER = [
    ("V-KMER-ROLLOVER-POSITIVE", g_rollover_positive),
    ("V-KMER-ROLLOVER-BELOW-THRESHOLD", g_rollover_below_threshold),
    ("V-KMER-ROLLOVER-FLOOR", g_rollover_floor),
    ("V-KMER-ROLLOVER-SEGMENT", g_rollover_segment),
    ("V-KMER-ROLLOVER-SYNTHETIC-SKIPPED", g_rollover_synthetic_skipped),
    ("V-KMER-ROLLOVER-SUBAGENT-THREAD", g_rollover_subagent_thread),
    ("V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED", g_rollover_inline_sidechain_unmeasured),
    ("V-KMER-ROLLOVER-SENSITIVITY", g_rollover_sensitivity),
    ("V-KMER-REREADS-POSITIVE", g_rereads_positive),
    ("V-KMER-REREADS-NEGATIVE", g_rereads_negative),
    ("V-KMER-REREADS-EQUALS-E", g_rereads_equals_e),
]


# =========================================================================== task 3: unchanged_precondition_retries
CMD_X = {"command": "python3 tools/test_x.py", "description": "run"}


def bash_pair(fx, n, tid, inp, text, usage=(10, 0, 1000, 5)):
    """Assistant call n carrying one Bash use, followed by its tool_result."""
    call(fx, n, [(tid, "Bash", inp)], usage=usage)
    fx.tool_result(tid, text, ts(10 + 2 * n + 1))


def g_retry_positive():
    # c1 Bash X (600-char result), c2 Read of another file, c3 Bash X again (600-char result), c4 plain. The retry's result
    # sits at call index 3 of 4 calls: resident 1. Upper = (600 / 3.0) x (2 + 0.1 x 0) = 400.0 + the issuing message's
    # output 5 / 1 tool_use x 5 = 25.0 -> 425.0. Strict lower = (600 / 4.5) x 2 = 266.667 (nothing between the two runs).
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 600)
        call(fx, 2, [("rd", "Read", {"file_path": "/x/b.py"})])
        fx.tool_result("rd", "body", ts(15))
        bash_pair(fx, 3, "b2", CMD_X, "B" * 600)
        call(fx, 4)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    lo = e["numerator"]["weighted_interval"][0] if e else None
    ok = (rc == 0 and e is not None and close(e["upper_bound_weighted"], 425.0) and close(lo, 266.666667)
          and d.get("retries") == 1 and d.get("strict") == 1 and d.get("loose_only") == 0)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} strict_lo={lo} details={ {k: d.get(k) for k in ('retries', 'strict', 'loose_only')} }"


def g_retry_intervening_write():
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 600)
        call(fx, 2, [("ed", "Edit", {"file_path": "/x/a.py", "old_string": "x", "new_string": "y"})])
        fx.tool_result("ed", "ok", ts(15))
        bash_pair(fx, 3, "b2", CMD_X, "B" * 600)
        call(fx, 4)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    ok = rc == 0 and e is not None and e["upper_bound_weighted"] == 0.0 and e["details"]["retries"] == 0
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} ranked={res['ranked_ids']}"


def g_retry_intervening_bash():
    # Bash X, Bash Y, Bash X: no write tool between, so it is a loose retry (counted in the upper bound, 425.0 as in the
    # positive case); another Bash ran between, so it is not strict: the strict lower bound is 0.0.
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 600)
        bash_pair(fx, 2, "b2", {"command": "ls /x"}, "files")
        bash_pair(fx, 3, "b3", CMD_X, "B" * 600)
        call(fx, 4)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    lo = e["numerator"]["weighted_interval"][0] if e else None
    ok = (rc == 0 and e is not None and close(e["upper_bound_weighted"], 425.0) and lo == 0.0
          and d.get("strict") == 0 and d.get("loose_only") == 1 and d.get("retries") == 1)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} strict_lo={lo} strict={d.get('strict')} loose_only={d.get('loose_only')}"


def g_retry_command_key():
    def count(build):
        rc, res, _ = rk(build)
        e = entry(res, "unchanged_precondition_retries")
        return rc, (e["details"]["retries"] if e else None)

    def bash_desc(fx):
        bash_pair(fx, 1, "b1", {"command": "make test", "description": "a"}, "A" * 100)
        bash_pair(fx, 2, "b2", {"command": "make test", "description": "b"}, "A" * 100)
        call(fx, 3)

    def bash_other(fx):
        bash_pair(fx, 1, "b1", {"command": "make test"}, "A" * 100)
        bash_pair(fx, 2, "b2", {"command": "make lint"}, "A" * 100)
        call(fx, 3)

    def grep_same(fx):
        for n, tid in ((1, "g1"), (2, "g2")):
            call(fx, n, [(tid, "Grep", {"pattern": "foo", "path": "/x"})])
            fx.tool_result(tid, "hits", ts(10 + 2 * n + 1))
        call(fx, 3)

    def grep_other(fx):
        for n, tid, path in ((1, "g1", "/x"), (2, "g2", "/y")):
            call(fx, n, [(tid, "Grep", {"pattern": "foo", "path": path})])
            fx.tool_result(tid, "hits", ts(10 + 2 * n + 1))
        call(fx, 3)
    got = [count(b) for b in (bash_desc, bash_other, grep_same, grep_other)]
    ok = [n for _, n in got] == [1, 0, 1, 0] and all(rc == 0 for rc, _ in got)
    return ok, f"retries (desc differs, other command, grep identical, grep other path) = {[n for _, n in got]}"


def g_retry_exclusions():
    # An identical Read pair is E's identical reread, an identical Write pair is a write: neither is a retry. An identical
    # Agent pair is outside the candidate (counted beside only).
    def build(fx):
        n = 0
        for tid in ("r1", "r2"):
            n += 1
            call(fx, n, [(tid, "Read", {"file_path": "/x/a.py"})])
            fx.tool_result(tid, "body", ts(10 + 2 * n + 1))
        for tid in ("w1", "w2"):
            n += 1
            call(fx, n, [(tid, "Write", {"file_path": "/x/n.py", "content": "a"})])
            fx.tool_result(tid, "ok", ts(10 + 2 * n + 1))
        for tid in ("a1", "a2"):
            n += 1
            call(fx, n, [(tid, "Agent", {"description": "d", "prompt": "p", "subagent_type": "Explore"})])
            fx.tool_result(tid, "done", ts(10 + 2 * n + 1))
        call(fx, n + 1)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    ok = rc == 0 and e is not None and d.get("retries") == 0 and d.get("agent_redispatches") == 1 \
        and e["upper_bound_weighted"] == 0.0
    return ok, f"rc={rc} retries={d.get('retries')} agent_redispatches={d.get('agent_redispatches')} upper={e and e['upper_bound_weighted']}"


def g_retry_output_share():
    # c2 issues two tool uses (Bash X again and Bash Z) in one message with output_tokens 10: the retry's output share is
    # 10 / 2 = 5 (not 10). Its 300-char result sits at call index 2 of 3: resident 1. Upper = (300 / 3.0) x 2 = 200.0 +
    # 5 x 5 = 25.0 -> 225.0 (an undivided output would read 250.0).
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 300)
        call(fx, 2, [("b2", "Bash", CMD_X), ("bz", "Bash", {"command": "ls /z"})], usage=(10, 0, 1000, 10))
        fx.tool_result("b2", "A" * 300, ts(15))
        fx.tool_result("bz", "Z", ts(15))
        call(fx, 3)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    return rc == 0 and e is not None and close(e["upper_bound_weighted"], 225.0), \
        f"rc={rc} upper={e and e['upper_bound_weighted']} (undivided output would read 250.0)"


def g_retry_after_error():
    # The first run errored (is_error): the identical rerun still counts, flagged after_error. 100-char result at index 2
    # of 3 calls, resident 1: (100 / 3.0) x 2 = 66.667 + 25.0 = 91.667.
    def build(fx):
        call(fx, 1, [("b1", "Bash", CMD_X)])
        fx.tool_result("b1", "boom", ts(13), is_error=True)
        bash_pair(fx, 2, "b2", CMD_X, "O" * 100)
        call(fx, 3)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    ok = rc == 0 and e is not None and close(e["upper_bound_weighted"], 91.666667) and d.get("after_error") == 1 \
        and d.get("retries") == 1
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} after_error={d.get('after_error')}"


def g_retry_unpaired_unmeasured():
    def build(with_result):
        def b(fx):
            bash_pair(fx, 1, "b1", CMD_X, "A" * 300)
            call(fx, 2, [("b2", "Bash", CMD_X)])
            if with_result:
                fx.tool_result("b2", "A" * 300, ts(15))
            call(fx, 3)
        return b
    rc1, r1, _ = rk(build(False))
    rc0, r0, _ = rk(build(True))
    u = entry(r1, "unchanged_precondition_retries", "unranked")
    ok = (rc1 == 3 and u is not None and u["status"] == "UNMEASURED" and "no tool_result" in u["reason"]
          and not any("upper" in k or "weighted" in k for k in u)
          and entry(r1, "unchanged_precondition_retries") is None
          and sorted(r1["ranked_ids"]) == ["identical_rereads", "late_rollover"]
          and rc0 == 0 and entry(r0, "unchanged_precondition_retries") is not None)
    return bool(ok), f"unpaired: rc={rc1} unranked={r1['unranked']} ranked={r1['ranked_ids']}; paired: rc={rc0} ranked={r0['ranked_ids']}"


GATES_RETRY = [
    ("V-KMER-RETRY-POSITIVE", g_retry_positive),
    ("V-KMER-RETRY-INTERVENING-WRITE", g_retry_intervening_write),
    ("V-KMER-RETRY-INTERVENING-BASH", g_retry_intervening_bash),
    ("V-KMER-RETRY-COMMAND-KEY", g_retry_command_key),
    ("V-KMER-RETRY-EXCLUSIONS", g_retry_exclusions),
    ("V-KMER-RETRY-OUTPUT-SHARE", g_retry_output_share),
    ("V-KMER-RETRY-AFTER-ERROR", g_retry_after_error),
    ("V-KMER-RETRY-UNPAIRED-UNMEASURED", g_retry_unpaired_unmeasured),
]


GATES_TRACER = [("V-KMER-TRACER-E2E", g_tracer_e2e), ("V-KMER-CONTRACT-E2E", g_contract_e2e)]
GATES = list(GATES_TRACER) + GATES_ROLLOVER + GATES_RETRY


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


# --------------------------------------------------------------------------- mutation drill
GATE_FN = dict(GATES)
DRILL_GATES = [n for n, _ in GATES if n not in ("V-KMER-TRACER-E2E", "V-KMER-CONTRACT-E2E")]    # the subprocess tracer is excluded (patches cannot reach it)


def _quiet(names) -> dict:
    """Run the named gates with printing off; {gate: passed} for the ones that ran to PASS/FAIL."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for n in names:
            run_gate(n, GATE_FN[n])
    finally:
        QUIET[0] = False
    return {g: st == "PASS" for st, g, _ in RESULTS[start:] if st in ("PASS", "FAIL")}


def _patch(module, attr, value):
    saved = getattr(module, attr)
    setattr(module, attr, value)
    return lambda: setattr(module, attr, saved)


def _m_floor_ignored():
    return _patch(kr, "rollover_avoided", lambda cut, ctx, floor: cut)


def _m_one_segment():
    return _patch(kr, "rollover_segments", lambda n_order, compact_points: [(0, n_order)])


def _m_upper_is_lower():
    return _patch(kr, "upper_bound_of", lambda result: result["numerator"]["weighted_interval"][0])


def _m_write_epoch_ignored():
    def mutant(prev, now):
        if prev is None:
            return None
        return "strict" if now[1] == prev[1] else "loose"
    return _patch(kr, "retry_kind", mutant)


def _m_bash_full_json_key():
    import hashlib

    def mutant(name, inp):
        return (name, hashlib.sha256(json.dumps(inp, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
    return _patch(kr, "retry_key", mutant)


def _m_status_ignores_observability():
    return _patch(kr, "candidate_status", lambda denominator_ok, observability: "MEASURED" if denominator_ok
                  else "UNMEASURED")


MUTANTS = [
    ("M1 rollover_avoided ignores the thread floor (avoids the whole cut)", _m_floor_ignored,
     ["V-KMER-ROLLOVER-FLOOR"]),
    ("M2 rollover_segments ignores actual compactions (one segment)", _m_one_segment, ["V-KMER-ROLLOVER-SEGMENT"]),
    ("M3 retry_kind ignores the write epoch (a rerun after an Edit is a retry)", _m_write_epoch_ignored,
     ["V-KMER-RETRY-INTERVENING-WRITE"]),
    ("M4 retry_key keys a Bash call by its full input JSON (a changed description hides the retry)",
     _m_bash_full_json_key, ["V-KMER-RETRY-COMMAND-KEY"]),
    ("M5 upper_bound_of returns weighted_interval[0]", _m_upper_is_lower, ["V-KMER-REREADS-EQUALS-E"]),
    ("M9 candidate_status ignores observability (a partly observed candidate is ranked)",
     _m_status_ignores_observability,
     ["V-KMER-RETRY-UNPAIRED-UNMEASURED", "V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED"]),
]


def run_drill() -> int:
    """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""
    control = _quiet(DRILL_GATES)
    control_ok = len(control) == len(DRILL_GATES) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(targets)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            print(f"SURVIVED {label} (still green or absent: {', '.join(t for t in targets if seen.get(t) is not False)})")
    after = _quiet(DRILL_GATES)
    clean = len(after) == len(DRILL_GATES) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
