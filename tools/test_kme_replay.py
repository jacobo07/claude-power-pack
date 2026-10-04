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
from test_kme_pillars import E_BODY, Fx, call, pdir, rd, tree_state, ts, write_frozen  # noqa: E402,F401

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
def tracer_fixture(root, project="-home-x-kme-fixture"):
    """The plan's tracer fixture: one thread, five calls, a reread, a retried Bash command."""
    fx = Fx(root, project=project)
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
          and all(abs(e["upper_bound_share"] - e["upper_bound_weighted"] / 3879.0) <= 5e-7 + 1e-12 for e in ranked)
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
          and all(abs(e["upper_bound_share"] * w - e["upper_bound_weighted"]) <= 5e-7 * w + 1e-9 for e in ranked)
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
    # output 5 / 1 tool_use x 5 = 25.0 -> 425.0. Nothing between the two runs: strict (the ranked entry carries the upper
    # bound only, WR-05; the strict class is checked by its count).
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 600)
        call(fx, 2, [("rd", "Read", {"file_path": "/x/b.py"})])
        fx.tool_result("rd", "body", ts(15))
        bash_pair(fx, 3, "b2", CMD_X, "B" * 600)
        call(fx, 4)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    ok = (rc == 0 and e is not None and close(e["upper_bound_weighted"], 425.0)
          and d.get("retries") == 1 and d.get("strict") == 1 and d.get("loose_only") == 0)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} details={ {k: d.get(k) for k in ('retries', 'strict', 'loose_only')} }"


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
    # positive case); another Bash ran between, so it is not strict: the strict count is 0.
    def build(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 600)
        bash_pair(fx, 2, "b2", {"command": "ls /x"}, "files")
        bash_pair(fx, 3, "b3", CMD_X, "B" * 600)
        call(fx, 4)
    rc, res, _ = rk(build)
    e = entry(res, "unchanged_precondition_retries")
    d = e["details"] if e else {}
    ok = (rc == 0 and e is not None and close(e["upper_bound_weighted"], 425.0)
          and d.get("strict") == 0 and d.get("loose_only") == 1 and d.get("retries") == 1)
    return ok, f"rc={rc} upper={e and e['upper_bound_weighted']} strict={d.get('strict')} loose_only={d.get('loose_only')}"


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


def sc_call(fx, n, tool_uses, agent="a1", usage=(10, 0, 1000, 5)):
    """An inline sidechain assistant call (isSidechain true, agentId) in the main transcript file."""
    i, cw, cr, o = usage
    content = [{"type": "tool_use", "id": tid, "name": name, "input": inp} for tid, name, inp in tool_uses]
    return fx._w({"type": "assistant", "isSidechain": True, "agentId": agent, "timestamp": ts(10 + 2 * n),
                  "uuid": f"u-sc{n}", "requestId": f"rsc{n}",
                  "message": {"id": f"sc{n}", "model": "claude-opus-5-5", "role": "assistant", "content": content,
                              "usage": {"input_tokens": i, "cache_creation_input_tokens": cw,
                                        "cache_read_input_tokens": cr, "output_tokens": o}}})


def sc_result(fx, tid, text, t, agent="a1"):
    return fx._w({"type": "user", "isSidechain": True, "agentId": agent, "timestamp": t,
                  "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid,
                                                             "content": text}]}})


def g_thread_keyed():
    # WR-06: retries and rereads are keyed per thread (main vs each inline sidechain), so a subagent's call never pairs
    # with the main thread's; two identical tool uses issued in ONE assistant message are not a retry (the first result
    # was not seen when the second was issued).
    def retries(build):
        rc, res, _ = rk(build)
        e = entry(res, "unchanged_precondition_retries")
        return e["details"]["retries"] if e else None

    def rereads(build):
        rc, res, _ = rk(build)
        e = entry(res, "identical_rereads")
        return (e["events"]["identical_same_segment"] + e["events"]["identical_after_compaction"]) if e else None

    def bash_main_then_side(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 300)
        sc_call(fx, 2, [("sb1", "Bash", CMD_X)])
        sc_result(fx, "sb1", "A" * 300, ts(15))
        call(fx, 3)

    def bash_side_pair(fx):
        sc_call(fx, 1, [("sb1", "Bash", CMD_X)])
        sc_result(fx, "sb1", "A" * 300, ts(13))
        sc_call(fx, 2, [("sb2", "Bash", CMD_X)])
        sc_result(fx, "sb2", "A" * 300, ts(15))
        call(fx, 3)

    def bash_two_agents(fx):
        sc_call(fx, 1, [("sb1", "Bash", CMD_X)], agent="a1")
        sc_result(fx, "sb1", "A" * 300, ts(13), agent="a1")
        sc_call(fx, 2, [("sb2", "Bash", CMD_X)], agent="a2")
        sc_result(fx, "sb2", "A" * 300, ts(15), agent="a2")
        call(fx, 3)

    def bash_main_pair(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 300)
        bash_pair(fx, 2, "b2", CMD_X, "A" * 300)
        sc_call(fx, 3, [], agent="a1")
        call(fx, 4)

    def bash_parallel(fx):
        call(fx, 1, [("b1", "Bash", CMD_X), ("b2", "Bash", CMD_X)])
        fx.tool_result("b1", "A" * 300, ts(13))
        fx.tool_result("b2", "A" * 300, ts(13))
        call(fx, 2)

    def bash_serial(fx):
        bash_pair(fx, 1, "b1", CMD_X, "A" * 300)
        bash_pair(fx, 2, "b2", CMD_X, "A" * 300)
        call(fx, 3)

    def read_main_then_side(fx):
        rd(fx, 1, "r1", "/x/a.py", E_BODY)
        sc_call(fx, 2, [("sr1", "Read", {"file_path": "/x/a.py"})])
        sc_result(fx, "sr1", E_BODY, ts(15))
        call(fx, 3)

    def read_side_pair(fx):
        sc_call(fx, 1, [("sr1", "Read", {"file_path": "/x/a.py"})])
        sc_result(fx, "sr1", E_BODY, ts(13))
        sc_call(fx, 2, [("sr2", "Read", {"file_path": "/x/a.py"})])
        sc_result(fx, "sr2", E_BODY, ts(15))
        call(fx, 3)

    def read_main_pair(fx):
        rd(fx, 1, "r1", "/x/a.py", E_BODY)
        rd(fx, 2, "r2", "/x/a.py", E_BODY)
        sc_call(fx, 3, [], agent="a1")
        call(fx, 4)
    got = {"retry main+side": retries(bash_main_then_side), "retry side pair": retries(bash_side_pair),
           "retry two agents": retries(bash_two_agents), "retry main pair": retries(bash_main_pair),
           "retry parallel": retries(bash_parallel), "retry serial": retries(bash_serial),
           "reread main+side": rereads(read_main_then_side), "reread side pair": rereads(read_side_pair),
           "reread main pair": rereads(read_main_pair)}
    want = {"retry main+side": 0, "retry side pair": 1, "retry two agents": 0, "retry main pair": 1,
            "retry parallel": 0, "retry serial": 1, "reread main+side": 0, "reread side pair": 1,
            "reread main pair": 1}
    return got == want, f"got={got} want={want}"


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
    ("V-KMER-THREAD-KEYED", g_thread_keyed),
]


# =========================================================================== task 2: contract and safety gates
CMD_C = {"command": "python3 tools/test_x.py", "description": "run"}
KR_CANARY = "sk-ant-" + "A" * 50
# The tracer fixture's population by hand: 5 calls, input 5 x 10 = 50, cache_write 1,000, cache_read 0 + 3,010 + 4,010 +
# 5,010 + 5,010 = 17,040, output 5 x 5 = 25 (weighted 3,879.0).
POP_KR = {"sessions_active": 1, "sessions_dead": 0, "calls": 5, "input": 50, "cache_write": 1000, "cache_read": 17040,
          "output": 25}


def mk(cid, upper):
    return {"candidate": cid, "upper_bound_weighted": upper, "name": cid}


def walk_keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_keys(v)


def klr_args(root, out_dir, frozen, denominator="KME-L", extra=(), project="-home-x-kme-fixture"):
    return ["rank", "--denominator", denominator, "--frozen-file", str(frozen), "--root", str(pdir(root, project)),
            "--out-dir", str(out_dir)] + list(extra)


def g_rank_order():
    unit = kr.rank_candidates([mk("late_rollover", 5.0), mk("identical_rereads", 9.0),
                               mk("unchanged_precondition_retries", 1.0)])
    unit_order = [e["candidate"] for e in unit]
    # CLI: the tracer sequence at G = 2,000: identical_rereads 2,200.0 > late_rollover 803.0 > retries 225.0
    root = scratch("ord")
    tracer_fixture(root)
    rc, res, _o, _e = run_json(rank_args(root, scratch("out"), ["--rollover-growth", "2000"]))
    cli = [(e["rank"], e["candidate"], e["upper_bound_weighted"]) for e in res["ranked"]]
    ok = (unit_order == ["identical_rereads", "late_rollover", "unchanged_precondition_retries"]
          and [e["upper_bound_weighted"] for e in unit] == [9.0, 5.0, 1.0] and rc == 0
          and cli == [(1, "identical_rereads", 2200.0), (2, "late_rollover", 803.0),
                      (3, "unchanged_precondition_retries", 225.0)])
    return ok, f"unit={unit_order} cli={cli}"


def g_rank_tie_deterministic():
    entries = [mk("late_rollover", 4.0), mk("identical_rereads", 4.0), mk("unchanged_precondition_retries", 4.0)]
    fwd = [e["candidate"] for e in kr.rank_candidates(list(entries))]
    rev = [e["candidate"] for e in kr.rank_candidates(list(reversed(entries)))]
    want = ["late_rollover", "identical_rereads", "unchanged_precondition_retries"]

    def build(fx):      # three measured zeros: distinct reads, no repeated call, growth below G -> a three-way tie
        call(fx, 1, [("r1", "Read", {"file_path": "/x/a.py"})])
        fx.tool_result("r1", E_BODY, ts(13))
        call(fx, 2, [("r2", "Read", {"file_path": "/x/b.py"})])
        fx.tool_result("r2", "B" + E_BODY[1:], ts(15))
        call(fx, 3)
    rc1, r1, out1 = rk(build)
    rc2, r2, _ = rk(build)
    # IN-01: equal figures share a rank (dense ranking: 4,4,4 -> 1,1,1; 9,4,4 -> 1,2,2; 9,5,1 -> 1,2,3), the order inside a
    # tie stays the fixed candidate order, and stdout labels the share as the bound it is
    def ranks(figs):
        es = kr.rank_candidates([mk(c, f) for c, f in zip(kr.CANDIDATES, figs)])
        return [(e["candidate"], r) for e, r in zip(es, kr.dense_ranks(es))]
    dense = [[r for _c, r in ranks(f)] for f in ((4.0, 4.0, 4.0), (4.0, 9.0, 4.0), (1.0, 5.0, 9.0), (0.0, 0.0, 0.0))]
    lines = [ln for ln in out1.splitlines() if ln.startswith("KMER rank=")]
    tie_ok = (dense == [[1, 1, 1], [1, 2, 2], [1, 2, 3], [1, 1, 1]] and [e["rank"] for e in r1["ranked"]] == [1, 1, 1]
              and len(lines) == 3 and all(" upper_bound_share=" in ln and " share=" not in ln for ln in lines))
    ok = (fwd == want and rev == want and rc1 == rc2 == 0 and r1["ranked_ids"] == r2["ranked_ids"] == want
          and r1["ranked"] == r2["ranked"] and all(e["upper_bound_weighted"] == 0.0 for e in r1["ranked"]) and tie_ok)
    return ok, (f"unit fwd={fwd} rev={rev}; cli ids={r1['ranked_ids']} same_json={r1['ranked'] == r2['ranked']} "
                f"dense={dense} cli ranks={[e['rank'] for e in r1['ranked']]} stdout={lines[:1]}")


def g_unmeasured_never_zero():
    results = {"late_rollover": mk("late_rollover", 5.0),
               "identical_rereads": None,
               "unchanged_precondition_retries": mk("unchanged_precondition_retries", 1.0)}
    ranked, unranked = kr.split_ranking(results)
    u = unranked[0] if unranked else {}
    unit_ok = ([e["candidate"] for e in ranked] == ["late_rollover", "unchanged_precondition_retries"]
               and [x["candidate"] for x in unranked] == ["identical_rereads"] and u.get("status") == "UNMEASURED"
               and u.get("reason") == "input missing: no observer result"
               and not any("upper" in k or "weighted" in k for k in u))
    # through the renderer: a real result with the identical_rereads entry removed
    root = scratch("unz")
    tracer_fixture(root)
    rc, res, _o, _e = run_json(rank_args(root, scratch("out"), ["--rollover-growth", "2000"]))
    by = {e["candidate"]: e for e in res["ranked"]}
    by["identical_rereads"] = None
    rk2, un2 = kr.split_ranking(by)
    for i, e in enumerate(rk2, 1):
        e["rank"] = i
    res2 = dict(res, ranked=rk2, unranked=un2, ranked_ids=[e["candidate"] for e in rk2],
                unranked_ids=[x["candidate"] for x in un2])
    text = kr.render_rank(res2)
    front, js = parse_rank(text)
    rows = [ln for ln in text.split("## Ranking")[1].split("## Unranked")[0].splitlines()
            if ln.startswith("| ") and not ln.startswith("| rank") and not ln.startswith("|---")]
    sect = text.split("## Unranked")[1].split("## Candidate details")[0]
    render_ok = (len(rows) == 2 and "identical_rereads" not in "".join(rows) and "identical_rereads" in sect
                 and "UNMEASURED" in sect and js["unranked"][0].get("upper_bound_weighted") is None
                 and front["unranked_ids"] == ["identical_rereads"])
    # the CLI path: a session with an inline sidechain line leaves late_rollover unobserved
    root2 = scratch("unz2")
    fx = tracer_fixture(root2)
    sidechain_line(fx)
    rc3, r3, _o3, _e3 = run_json(rank_args(root2, scratch("out"), ["--rollover-growth", "2000"]))
    cli_ok = (rc3 == 3 and r3["unranked_ids"] == ["late_rollover"] and "late_rollover" not in r3["ranked_ids"]
              and all(e["upper_bound_weighted"] != 0.0 for e in r3["ranked"]))
    return bool(unit_ok and render_ok and cli_ok), (f"unit={unit_ok} render={render_ok} cli={cli_ok} "
                                                     f"(rows={len(rows)} unranked={[x['candidate'] for x in unranked]})")


def g_measured_zero_ranked():
    def build(fx):
        call(fx, 1, [("r1", "Read", {"file_path": "/x/a.py"})])
        fx.tool_result("r1", E_BODY, ts(13))
        call(fx, 2, [("r2", "Read", {"file_path": "/x/b.py"})])
        fx.tool_result("r2", "B" + E_BODY[1:], ts(15))
        call(fx, 3)
    rc, res, _ = rk(build)
    ok = (rc == 0 and sorted(res["ranked_ids"]) == sorted(["late_rollover", "identical_rereads",
                                                           "unchanged_precondition_retries"])
          and res["unranked"] == [] and all(e["upper_bound_weighted"] == 0.0 for e in res["ranked"])
          and all(e["bound_vs_threshold"] == "< 3 %" for e in res["ranked"]))
    return bool(ok), f"rc={rc} ranked={[(e['candidate'], e['upper_bound_weighted'], e['bound_vs_threshold']) for e in res['ranked']]}"


def g_same_denominator():
    # main: c1 Read f (10,1000,0,5), c2 Read f again (10,0,3010,5), c3 plain (10,0,3010,5)
    #   input 30, cache_write 1,000, cache_read 6,020, output 15 -> 30 + 2,000 + 602 + 75 = 2,707.0
    # subagent a1: s1 Bash X (10,2000,0,5), s2 Bash X again (10,0,4010,5), s3 plain (10,0,4010,5)
    #   input 30, cache_write 2,000, cache_read 8,020, output 15 -> 30 + 4,000 + 802 + 75 = 4,907.0
    # W = 7,614.0 over 6 calls, the subagent calls included; one W divides every share.
    root = scratch("sd")
    fx = Fx(root)
    fx.human("go", ts(0))
    call(fx, 1, [("r1", "Read", {"file_path": "/w/f.py"})], usage=(10, 1000, 0, 5))
    fx.tool_result("r1", E_BODY, ts(13))
    call(fx, 2, [("r2", "Read", {"file_path": "/w/f.py"})], usage=(10, 0, 3010, 5))
    fx.tool_result("r2", E_BODY, ts(15))
    call(fx, 3, usage=(10, 0, 3010, 5))
    sub = fx.subagent("a1", "Explore")
    sub.human("t", ts(60))
    sub.assistant("x1", "rx1", (10, 2000, 0, 5), ts(61), tool_uses=[("sb1", "Bash", CMD_C)])
    sub.tool_result("sb1", "A" * 300, ts(62))
    sub.assistant("x2", "rx2", (10, 0, 4010, 5), ts(63), tool_uses=[("sb2", "Bash", CMD_C)])
    sub.tool_result("sb2", "A" * 300, ts(64))
    sub.assistant("x3", "rx3", (10, 0, 4010, 5), ts(65))
    rc, res, _o, _e = run_json(rank_args(root, scratch("out"), ["--rollover-growth", "2000"]))
    w = 7614.0
    ranked = res["ranked"]
    shares_ok = all(abs(e["upper_bound_share"] * w - e["upper_bound_weighted"]) <= 5e-7 * w + 1e-9 for e in ranked)
    nonzero = sorted(e["candidate"] for e in ranked if e["upper_bound_weighted"] > 0)
    ok = (rc == 0 and res["population"]["calls"] == 6 and close(res["weighted_denominator"], w, 1e-9)
          and len(ranked) == 3 and shares_ok and len(nonzero) == 3)
    fake = {"measured": {"weighted": 100.0}}
    unit = [kr.denominator_for(c, fake) for c in kr.CANDIDATES]
    return bool(ok and unit == [100.0, 100.0, 100.0]), (f"rc={rc} W={res['weighted_denominator']} calls="
                                                        f"{res['population']['calls']} shares_ok={shares_ok} "
                                                        f"nonzero={nonzero} unit={unit}")


def g_selected_only():
    root = scratch("sel")
    tracer_fixture(root)
    tracer_fixture(root, project="-home-x-other")
    # the other project's cwd is /home/x/work and its name carries no kme / mapengine: not selected under `kme`
    out1 = scratch("out")
    rc1, r1, _o1, _e1 = run_json(["rank", "--denominator", "OTHER", "--label", "FX-S", "--until", "none", "--expand",
                                  "--root", str(root / "projects"), "--out-dir", str(out1),
                                  "--rollover-growth", "2000"])
    rc0, r0, _o0, _e0 = run_json(rank_args(root, scratch("out"), ["--rollover-growth", "2000"], label="FX-S0"))
    up1 = {e["candidate"]: e["upper_bound_weighted"] for e in r1["ranked"]}
    up0 = {e["candidate"]: e["upper_bound_weighted"] for e in r0["ranked"]}
    ok = (rc1 == 0 and rc0 == 0 and up1 == up0 and len(up0) == 3 and all(v > 0 for v in up0.values())
          and r1["corpus"]["sessions_scanned"] == 2 and r1["corpus"]["sessions_selected_active"] == 1
          and close(r1["weighted_denominator"], r0["weighted_denominator"], 1e-9))
    return bool(ok), (f"rc={rc1}/{rc0} scanned={r1['corpus']['sessions_scanned']} selected="
                      f"{r1['corpus']['sessions_selected_active']} uppers expand={up1} alone={up0}")


def g_drift_all_unmeasured():
    root = scratch("dr")
    tracer_fixture(root)
    exact = write_frozen(root / "f_exact.json", **{"KME-L": POP_KR})
    off = write_frozen(root / "f_off.json", **{"KME-L": dict(POP_KR, calls=POP_KR["calls"] + 1)})
    out_off, out_ok = scratch("out"), scratch("out")
    rc, res, _o, _e = run_json(klr_args(root, out_off, off, extra=["--rollover-growth", "2000"]))
    rc_ok, r_ok, _o2, _e2 = run_json(klr_args(root, out_ok, exact, extra=["--rollover-growth", "2000"]))
    ok = (rc == 3 and res["population_match"] == "drifted" and res["ranked"] == [] and res["ranked_ids"] == []
          and sorted(res["unranked_ids"]) == sorted(kr.CANDIDATES) and len(res["unranked"]) == 3
          and all("population_not_reproduced" in u["reason"] and u["status"] == "UNMEASURED"
                  and not any("upper" in k for k in u) for u in res["unranked"])
          and res["terminal_evidence"] is False and len(list(out_off.glob("L-KME-L-*.md"))) == 1
          and rc_ok == 0 and r_ok["population_match"] == "exact" and len(r_ok["ranked"]) == 3)
    return bool(ok), (f"drift: rc={rc} match={res['population_match']} unranked={res['unranked_ids']} "
                      f"deltas={res['population_deltas']}; control: rc={rc_ok} match={r_ok['population_match']} "
                      f"ranked={len(r_ok['ranked'])}")


def g_upper_bound_labels():
    hi, lo = kr.bound_label(30.0, 1000.0), kr.bound_label(29.999, 1000.0)
    root = scratch("lab")
    tracer_fixture(root)
    rc, res, _o, _e = run_json(rank_args(root, scratch("out"), ["--rollover-growth", "2000"]))
    bad_keys = sorted({k for k in walk_keys(res) if k in ("saving", "realized", "realized_saving")})
    ok = (hi == ">= 3 %" and lo == "< 3 %" and rc == 0 and len(res["ranked"]) == 3
          and "saving_status" in set(walk_keys(res))      # positive control: the walker does see keys
          and all(e["saving_status"] == "upper_bound" and e["displacement"] == "unknown" for e in res["ranked"])
          and all(e["bound_vs_threshold"] == (">= 3 %" if e["upper_bound_share"] >= 0.03 else "< 3 %")
                  for e in res["ranked"]) and not bad_keys)
    return bool(ok), f"30/1000 -> {hi}; 29.999/1000 -> {lo}; cli rc={rc} forbidden keys={bad_keys}"


def walk_floats(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from walk_floats(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_floats(v)
    elif isinstance(x, float):
        yield x


def g_upper_only():
    # WR-05: a ranked entry carries ONE figure, the upper bound. No `weighted_lo` / `weighted_hi` / `weighted_interval`
    # (a "lower" side that is the gross cost of the avoided tokens, not a lower bound on any saving), and every float is
    # rounded to 6 decimals (float noise is not a measurement). Read from the result, the file front matter's json block
    # and the rendered text.
    root = scratch("uo")
    tracer_fixture(root)
    outd = scratch("out")
    rc, res, _o, _e = run_json(rank_args(root, outd, ["--rollover-growth", "2000"]))
    f = next(iter(outd.glob("L-FX-R-*.md")), None)
    if rc != 0 or f is None:
        return False, f"rc={rc}"
    text = f.read_text(encoding="utf-8")
    _front, block = parse_rank(text)
    forbidden = ("weighted_lo", "weighted_hi", "weighted_interval")
    seen = {}
    for name, doc in (("result", res), ("file json", block)):
        keys = set(walk_keys(doc["ranked"]))
        floats = list(walk_floats(doc["ranked"]))
        seen[name] = (sorted(k for k in keys if k in forbidden), [x for x in floats if round(x, 6) != x],
                      "upper_bound_weighted" in keys, len(floats))
    control = all(v[2] and v[3] > 0 for v in seen.values())          # the walkers do see keys and floats
    noise_free = all(not v[0] and not v[1] for v in seen.values())
    shares = [e["upper_bound_share"] for e in res["ranked"]]
    return bool(control and noise_free and not any(w in text.split("<!-- kmer-json -->")[0] for w in forbidden)), (
        f"forbidden/noisy per source = { {k: v[:2] for k, v in seen.items()} } control={control} shares={shares}")


def g_terminal_evidence():
    # unit truth table of the seam
    d, nd = {"all_default": True}, {"all_default": False}
    unit = [kr.terminal_ok("primary", "exact", d, []), kr.terminal_ok("primary", "exact", d, [{"candidate": "x"}]),
            kr.terminal_ok("primary", "exact", nd, []), kr.terminal_ok("smoke", "exact", d, []),
            kr.terminal_ok("primary", "drifted", d, []), kr.terminal_ok("primary", "exact", None, [])]
    unit_ok = unit == [True, False, False, False, False, False]
    root = scratch("te")
    tracer_fixture(root)
    exact = write_frozen(root / "f_exact.json", **{"KME-L": POP_KR, "KME-G": POP_KR})
    rc1, a, _o, _e = run_json(klr_args(root, scratch("out"), exact))
    primary_ok = (rc1 == 0 and a["evidence_role"] == "primary" and a["terminal_evidence"] is True)
    # the same fixture plus an inline sidechain line (frozen file regenerated to match): late_rollover unranked
    root2 = scratch("te2")
    fx = tracer_fixture(root2)
    sidechain_line(fx)
    pop_sc = dict(POP_KR, calls=6, input=51, cache_write=1100, output=26)
    frozen_sc = write_frozen(root2 / "f_sc.json", **{"KME-L": pop_sc})
    rc2, b, _o2, _e2 = run_json(klr_args(root2, scratch("out"), frozen_sc))
    unranked_ok = (rc2 == 3 and b["population_match"] == "exact" and b["terminal_evidence"] is False
                   and b["unranked_ids"] == ["late_rollover"] and "late_rollover" in b["terminal_evidence_reason"])
    rc3, g, _o3, _e3 = run_json(klr_args(root, scratch("out"), exact, denominator="KME-G"))
    rc4, o, _o4, _e4 = run_json(rank_args(root, scratch("out")))
    smoke_ok = (g["evidence_role"] == "smoke" and g["terminal_evidence"] is False and o["evidence_role"] == "smoke"
                and o["terminal_evidence"] is False and rc3 == 0 and rc4 == 0)
    FOLLOW_DEFAULTS[0] = False
    try:
        rc5, h, _o5, _e5 = run_json(klr_args(root, scratch("out"), exact))
    finally:
        FOLLOW_DEFAULTS[0] = True
    src_ok = (rc5 == 0 and h["evidence_role"] == "primary" and h["terminal_evidence"] is False
              and "NOT the committed frozen source" in h["terminal_evidence_reason"] and h["frozen_source"]["all_default"] is False)
    return bool(unit_ok and primary_ok and unranked_ok and smoke_ok and src_ok), (
        f"unit={unit} primary={primary_ok} unranked={unranked_ok} smoke={smoke_ok} src={src_ok}")


def g_rollover_growth_pinned():
    # WR-04: a primary ranking is terminal only at the frozen default G (100,000). Any other G is sensitivity / smoke,
    # whatever the population, the frozen source and the measured candidates say.
    d = {"all_default": True}
    unit = [kr.terminal_ok("primary", "exact", d, [], growth=kr.ROLLOVER_GROWTH),
            kr.terminal_ok("primary", "exact", d, [], growth=1000000000),
            kr.terminal_ok("primary", "exact", d, [], growth=50000),
            kr.terminal_ok("primary", "exact", d, [], growth=True)]
    root = scratch("gp")
    tracer_fixture(root)
    exact = write_frozen(root / "f_exact.json", **{"KME-L": POP_KR})
    rc0, r0, _o0, _e0 = run_json(klr_args(root, scratch("out"), exact))
    rc1, r1, _o1, _e1 = run_json(klr_args(root, scratch("out"), exact, extra=["--rollover-growth", "1000000000"]))
    rc2, r2, _o2, _e2 = run_json(klr_args(root, scratch("out"), exact, extra=["--rollover-growth", "2000"]))
    ok = (unit == [True, False, False, False]
          and rc0 == 0 and r0["terminal_evidence"] is True and r0["rollover_growth"] == kr.ROLLOVER_GROWTH
          and rc1 == 0 and r1["evidence_role"] == "primary" and r1["terminal_evidence"] is False
          and "rollover_growth" in r1["terminal_evidence_reason"] and r1["rollover_growth"] == 1000000000
          and r1["ranked_ids"] and rc2 == 0 and r2["terminal_evidence"] is False)
    return bool(ok), (f"unit={unit} default: rc={rc0} terminal={r0['terminal_evidence']}; G=1e9: rc={rc1} "
                      f"terminal={r1['terminal_evidence']} reason={r1['terminal_evidence_reason'][-120:]}; G=2000 "
                      f"terminal={r2['terminal_evidence']}")


def g_no_raw_paths():
    # IN-02: a ranking file never carries the absolute paths the transcripts read. top_paths is sha256[:12] digests plus the
    # extension (enough to tell two files apart and what kind they are), with the count and chars kept. The path is
    # something a redactor's regex cannot know is sensitive (a customer name, an .env.production).
    import hashlib
    secret = "/home/u/customer-acme/.env.production"
    plain = "/home/u/work/notes.md"

    def build(fx):
        rd(fx, 1, "r1", secret, E_BODY)
        rd(fx, 2, "r2", secret, E_BODY)
        rd(fx, 3, "r3", plain, "N" * 400)
        rd(fx, 4, "r4", plain, "N" * 400)
        call(fx, 5)
    root = scratch("np")
    fx = Fx(root)
    fx.human("go", ts(0))
    build(fx)
    outd = scratch("out")
    rc, res, out, _e = run_json(rank_args(root, outd))
    f = next(iter(outd.glob("L-FX-R-*.md")), None)
    text = f.read_text(encoding="utf-8") if f else ""
    e = entry(res, "identical_rereads")
    tp = e["details"]["top_paths"] if e else []
    dig = lambda p_: hashlib.sha256(p_.encode("utf-8")).hexdigest()[:12]
    want = {dig(secret): ".production", dig(plain): ".md"}
    got = {t.get("path_sha256_12"): t.get("ext") for t in tp}
    leaked = [x for x in ("customer-acme", ".env.production", "/home/u", "notes.md") if x in text or x in out]
    ok = (rc == 0 and len(tp) == 2 and got == want and all(set(t) == {"path_sha256_12", "ext", "count", "chars"}
                                                           for t in tp)
          and all(t["count"] == 1 for t in tp) and not leaked and "path_sha256_12" in text)
    return bool(ok), f"rc={rc} top_paths={tp} want={want} leaked={leaked}"


def secret_fixture(root):
    fx = Fx(root)
    fx.human("go " + KR_CANARY, ts(0))
    fx.attachment("hook_additional_context", ts(1), content=["ctx " + KR_CANARY], hookName="PreToolUse:Bash",
                  hookEvent="PreToolUse")
    call(fx, 1, [("b1", "Bash", {"command": "echo " + KR_CANARY, "description": "d"})], usage=(10, 1000, 0, 5))
    fx.tool_result("b1", "out " + KR_CANARY * 3, ts(13))
    call(fx, 2, [("b2", "Bash", {"command": "echo " + KR_CANARY, "description": "d"})], usage=(10, 0, 3010, 5))
    fx.tool_result("b2", "out " + KR_CANARY * 3, ts(15))
    call(fx, 3, [("r1", "Read", {"file_path": "/x/" + KR_CANARY + ".py"})], usage=(10, 0, 4010, 5))
    fx.tool_result("r1", KR_CANARY + E_BODY, ts(17))
    call(fx, 4, [("r2", "Read", {"file_path": "/x/" + KR_CANARY + ".py"})], usage=(10, 0, 5010, 5))
    fx.tool_result("r2", KR_CANARY + E_BODY, ts(19))
    fx.assistant("m5", "r5", (10, 0, 5010, 5), ts(21), text="said " + KR_CANARY)
    return fx


def g_no_secret():
    root = scratch("sec")
    fx = secret_fixture(root)
    raw = fx.path.read_text()
    out_dir = scratch("out")
    rc, out, err = run_main(rank_args(root, out_dir, ["--json", "--rollover-growth", "2000"]))
    written = "".join(p.read_text(encoding="utf-8") for p in out_dir.glob("*.md"))
    present = [n for n, t in (("file", written), ("stdout", out), ("stderr", err)) if KR_CANARY in t]
    exercised = '"signature"' in written and "unchanged_precondition_retries" in written   # the retried command reached the file as a signature
    return (KR_CANARY in raw and written != "" and out != "" and exercised and not present and rc in (0, 3)), \
        f"fixture holds canary={KR_CANARY in raw}; leaked into {present}; rc={rc}; file bytes={len(written)}; command signature path exercised={exercised}"


def g_read_only():
    if os.name == "nt":
        return "SKIP", "chmod a-w is not a read-only fence on nt"
    root = scratch("ro")
    tracer_fixture(root)
    tree = root / "projects"
    for dp, dns, fns in os.walk(tree):
        for n in fns:
            os.chmod(os.path.join(dp, n), 0o444)
    for dp, dns, fns in os.walk(tree, topdown=False):
        os.chmod(dp, 0o555)
    before = tree_state(tree)
    rc, _o, err = run_main(rank_args(root, scratch("out")))
    after = tree_state(tree)
    return rc == 0 and before == after and len(before) >= 2, f"rc={rc} entries={len(before)} unchanged={before == after} err={err[-120:]}"


def g_out_dir_inside_root():
    root = scratch("oir")
    tracer_fixture(root)
    pd = pdir(root)
    before = tree_state(root / "projects")
    inside = pd / "out"
    rc_in, _o, err_in = run_main(rank_args(root, inside))
    link = scratch("oir-link") / "lnk"
    try:
        link.symlink_to(pd, target_is_directory=True)
    except OSError as exc:  # Windows without the symlink privilege: a junction resolves the same way
        if os.name != "nt" or getattr(exc, "winerror", None) != 1314:
            raise
        import _winapi
        _winapi.CreateJunction(str(pd), str(link))
    rc_ln, _o2, _e2 = run_main(rank_args(root, link / "viasym"))
    rc_ex, _o3, _e3 = run_main(["rank", "--denominator", "OTHER", "--label", "FX-R", "--until", "none", "--expand",
                                "--root", str(root / "projects"), "--out-dir", str(root / "projects" / "deeper" / "out")])
    rc_eq, _o4, _e4 = run_main(rank_args(root, pd))
    after = tree_state(root / "projects")
    out_ok = scratch("oir-ok")
    rc_ok, _o5, _e5 = run_main(rank_args(root, out_ok))
    wrote = len(list(out_ok.glob("*.md")))
    refused = rc_in == rc_ln == rc_ex == rc_eq == 2
    return refused and before == after and not inside.exists() and "inside --root" in err_in and rc_ok in (0, 3) \
        and wrote == 1, f"inside={rc_in} symlink={rc_ln} expand={rc_ex} equal={rc_eq} unchanged={before == after} control_rc={rc_ok} files={wrote}"


def g_no_overwrite():
    root = scratch("noov")
    tracer_fixture(root)
    out_dir = scratch("out")
    args = rank_args(root, out_dir, label="FX-N")
    rc1, _o1, _e1 = run_main(args)
    first = sorted(out_dir.glob("L-FX-N-*.md"))
    h1 = first[0].read_bytes() if first else b""
    rc2, _o2, _e2 = run_main(args)
    names = sorted(x.name for x in out_dir.glob("L-FX-N-*.md"))
    ok = (rc1 == rc2 == 0 and len(first) == 1 and len(names) == 2 and first[0].read_bytes() == h1
          and sum(1 for n in names if n.endswith("-2.md")) == 1)
    return bool(ok), f"rc={rc1}/{rc2} files={names}"


def g_until_auto():
    # The tracer fixture (5 calls, last line at ts(20)) plus one later call 6 at ts(22) that REPEATS the Bash command: a
    # third identical run, so counted it would be a second retry. The frozen population is the 5-call one, the freeze
    # instant lies after the last line: the locator must find a cutoff between ts(20) and ts(22) by bisect, and the late
    # call's retry is not in the result (retries stays 1, the 300-char t4 retry: 225.0).
    root = scratch("ua")
    fx = tracer_fixture(root)
    call(fx, 6, [("t6", "Bash", CMD_C)], usage=(10, 0, 5010, 5))
    fx.tool_result("t6", "F" * 300, ts(23))
    frozen = write_frozen(root / "f.json", **{"KME-L": POP_KR})
    out_dir = scratch("out")
    rc, res, _o, _e = run_json(klr_args(root, out_dir, frozen, extra=["--until", "auto", "--freeze-instant", ts(30),
                                                                      "--rollover-growth", "2000"]))
    ul = res.get("until_located") or {}
    until = kp.parse_instant(res["until"]) if res else None
    e = entry(res, "unchanged_precondition_retries") if res else None
    ok = (rc == 0 and res["population_match"] == "exact" and ul.get("method") == "bisect"
          and until is not None and kp.parse_instant(ts(20)) <= until < kp.parse_instant(ts(22))
          and res["population"]["calls"] == 5 and e is not None and e["events"]["retries"] == 1
          and close(e["upper_bound_weighted"], 225.0))
    return bool(ok), (f"rc={rc} match={res['population_match']} until={res['until']} located={ul} "
                      f"retries={e and e['events']['retries']} upper={e and e['upper_bound_weighted']}")


def g_cli_usage():
    root = scratch("cu")
    tracer_fixture(root)
    out_dir = scratch("out")
    pd = pdir(root)
    frozen = write_frozen(root / "f.json", **{"KME-L": POP_KR})
    base = ["--root", str(pd), "--out-dir", str(out_dir)]
    cases = {
        "growth 0": ["rank", "--denominator", "OTHER", "--label", "FX-U", "--select", "all", "--until", "none",
                     "--rollover-growth", "0"] + base,
        "CPP-D-W7": ["rank", "--denominator", "CPP-D-W7"] + base,
        "select all with KME-L": ["rank", "--denominator", "KME-L", "--select", "all", "--frozen-file", frozen] + base,
        "OTHER without label": ["rank", "--denominator", "OTHER", "--select", "all", "--until", "none"] + base,
        "root not a directory": ["rank", "--denominator", "OTHER", "--label", "FX-U", "--select", "all", "--until",
                                 "none", "--root", str(root / "nope"), "--out-dir", str(out_dir)],
    }
    rcs = {k: run_main(v)[0] for k, v in cases.items()}
    wrote = list(out_dir.glob("*.md"))
    rc_ok, _o, _e = run_main(rank_args(root, out_dir, label="FX-U"))
    return all(v == 2 for v in rcs.values()) and not wrote and rc_ok == 0 and len(list(out_dir.glob("*.md"))) == 1, \
        f"rcs={rcs} wrote_on_refusal={len(wrote)} control_rc={rc_ok}"


GATES_CONTRACT = [
    ("V-KMER-RANK-ORDER", g_rank_order),
    ("V-KMER-RANK-TIE-DETERMINISTIC", g_rank_tie_deterministic),
    ("V-KMER-UNMEASURED-NEVER-ZERO", g_unmeasured_never_zero),
    ("V-KMER-MEASURED-ZERO-RANKED", g_measured_zero_ranked),
    ("V-KMER-SAME-DENOMINATOR", g_same_denominator),
    ("V-KMER-SELECTED-ONLY", g_selected_only),
    ("V-KMER-DRIFT-ALL-UNMEASURED", g_drift_all_unmeasured),
    ("V-KMER-UPPER-BOUND-LABELS", g_upper_bound_labels),
    ("V-KMER-UPPER-ONLY", g_upper_only),
    ("V-KMER-TERMINAL-EVIDENCE", g_terminal_evidence),
    ("V-KMER-ROLLOVER-GROWTH-PINNED", g_rollover_growth_pinned),
    ("V-KMER-NO-SECRET", g_no_secret),
    ("V-KMER-NO-RAW-PATHS", g_no_raw_paths),
    ("V-KMER-READ-ONLY", g_read_only),
    ("V-KMER-OUT-DIR-INSIDE-ROOT", g_out_dir_inside_root),
    ("V-KMER-NO-OVERWRITE", g_no_overwrite),
    ("V-KMER-UNTIL-AUTO", g_until_auto),
    ("V-KMER-CLI-USAGE", g_cli_usage),
]


# --------------------------------------------------------------------------- plan 05-03: the owner bundle's [L] lines
BUNDLE_REL = "vault/programs/incremental-cognition/owner-bundle.md"
REPLAY_TOKEN = "wiki/tools/kme_replay.py"


def bundle_replay_commands(text):
    """(item tag or None, the line, argv after the script token, placeholder tokens) for every indented kme_replay line.

    Same grammar as test_kme_pillars.bundle_commands: an item tag is the nearest preceding `- **[X]**`, a `#` / `##`
    header resets it, tokens come from shlex posix=False with quotes stripped."""
    import re
    import shlex
    tag, rows = None, []
    for ln in text.split("\n"):
        m = re.match(r"^- \*\*\[([A-Z])\]\*\*", ln)
        if m:
            tag = m.group(1)
        elif re.match(r"^(## |# )", ln):
            tag = None
        if not re.match(r"^ {4,}\S", ln) or REPLAY_TOKEN not in ln:
            continue
        toks = [t.strip("\"'") for t in shlex.split(ln.strip(), posix=False)]
        i = next((k for k, t in enumerate(toks) if t.endswith(REPLAY_TOKEN)), None)
        if i is None:
            continue
        rows.append((tag, ln.strip(), toks[i + 1:], [t for t in toks if "<" in t or ">" in t]))
    return rows


def bundle_replay_check(text):
    """(problems, parsed rows [(tag, namespace, line)]) of a bundle text through kme_replay's own parser."""
    ap = kr.build_parser()
    problems, parsed = [], []
    for tag, line, argv, placeholders in bundle_replay_commands(text):
        if placeholders:
            problems.append(f"placeholder {placeholders} in: {line[:80]}")
            continue
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                parsed.append((tag, ap.parse_args(argv), line))
        except SystemExit:
            problems.append(f"unparsable: {line[:80]}")
    return problems, parsed


def g_bundle_argv_parses():
    import re
    text = (REPO / BUNDLE_REL).read_text(encoding="utf-8")
    problems, parsed = bundle_replay_check(text)
    rank_l = [a for t, a, _l in parsed if t == "L" and a.cmd == "rank" and a.denominator == "KME-L"
              and a.until == "auto" and a.expand is True]
    l_items = len(re.findall(r"^- \*\*\[L\]\*\*", text, re.M))
    head = text.split("## Phase 5", 1)
    sec = head[1].split("\n## ", 1)[0] if len(head) == 2 else ""
    status_ok = "NOT RUNNABLE HERE" in sec
    # controls inside the gate: an unknown flag and a placeholder are both refused, a good line is not
    bad_text = ("- **[L]** x\n\n    python wiki/tools/kme_replay.py rank --denominator KME-L --no-such-flag --root R\n"
                "    python wiki/tools/kme_replay.py rank --denominator KME-L --root <projects-dir>\n")
    good_text = ("- **[L]** x\n\n    python wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand "
                 "--root C:\\Users\\User\\.claude\\projects\n")
    ctl_bad, _p = bundle_replay_check(bad_text)
    ctl_good, ctl_rows = bundle_replay_check(good_text)
    controls = len(ctl_bad) == 2 and ctl_good == [] and len(ctl_rows) == 1
    ok = not problems and len(rank_l) >= 1 and l_items >= 2 and status_ok and controls
    return ok, (f"{len(parsed)} replay line(s) parsed, problems={problems}, rank lines tagged L (KME-L, until auto, "
                f"expand)={len(rank_l)} (>= 1), [L] items={l_items} (>= 2), Phase 5 NOT RUNNABLE HERE={status_ok}, "
                f"controls(bad={len(ctl_bad)}/2, good={len(ctl_good)}/0)={controls}")


GATES_BUNDLE = [("V-KMER-BUNDLE-ARGV-PARSES", g_bundle_argv_parses)]


# --------------------------------------------------------------------------- plan 05-04: the owner bundle's summary table
SUMMARY_HEAD = "## Summary (every Owner item, phases 1-5)"
PHASES_REL = ".planning/workstreams/incremental-cognition/phases"
CMD_STARTS = ("python", "python3", "git", "bash", "cp")


def split_summary(text):
    """(the summary section's text or '', the file text with that section removed)."""
    import re
    m = re.search(r"^" + re.escape(SUMMARY_HEAD) + r"[ \t]*$", text, re.M)
    if not m:
        return "", text
    end = text.find("\n## ", m.end())
    end = len(text) if end < 0 else end + 1
    return text[m.start():end], text[:m.start()] + text[end:]


def bundle_items(text):
    """Keys of every Owner item, DISCOVERED from the file: `[X]#k "<first three words>"` for each `- **[X]**` line
    outside the summary (k = ordinal among that tag's items), plus `sync` when the `## Laptop code sync` header exists."""
    import re
    _s, body = split_summary(text)
    n, keys = {}, []
    for ln in body.split("\n"):
        m = re.match(r"^- \*\*\[([A-Z])\]\*\*\s+(.*)", ln)
        if m:
            n[m.group(1)] = n.get(m.group(1), 0) + 1
            keys.append(f'[{m.group(1)}]#{n[m.group(1)]} "{" ".join(m.group(2).split()[:3])}"')
    if re.search(r"^## Laptop code sync", body, re.M):
        keys.append("sync")
    return keys


def summary_rows(text):
    """Data rows of the first table of the summary section, each as its list of stripped cells."""
    import re
    sec, _b = split_summary(text)
    rows = [ln for ln in sec.split("\n") if ln.startswith("|")]
    out = []
    for ln in rows[1:]:
        if re.match(r"^\|[\s:\-|]+$", ln):
            continue
        out.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return out


def source_tokens(cell):
    return [t.strip() for t in cell.split(";") if t.strip()]


def check_items(text):
    """Problems of the summary table against the items of the same file; [] when it covers them exactly."""
    import re
    sec, body = split_summary(text)
    if not sec:
        return ["no summary section"]
    rows = summary_rows(text)
    if not rows:
        return ["summary section holds no table rows"]
    probs = []
    for i, r in enumerate(rows, 1):
        if len(r) != 6:
            probs.append(f"row {i} has {len(r)} cells, not 6")
            continue
        for name, idx in (("pillar", 1), ("source", 2), ("action", 3), ("command", 4), ("closes", 5)):
            if not r[idx]:
                probs.append(f"row {i} has an empty {name} cell")
    rows = [r for r in rows if len(r) == 6]
    items = bundle_items(text)
    toks = [t for r in rows for t in source_tokens(r[2])]
    for k in items:
        if k not in toks:
            probs.append(f"missing row for {k}")
    for t in toks:
        if re.match(r"^(UAT|VER) \d{2}#\d+$", t):
            continue
        if t not in items:
            probs.append(f"stale or unknown source {t}")
    lines = {ln.strip() for ln in body.split("\n") if re.match(r"^ {4,}\S", ln)}
    for i, r in enumerate(rows, 1):
        for span in re.findall(r"`([^`]+)`", r[4]):
            if span.split()[0] in CMD_STARTS and span.strip() not in lines:
                probs.append(f"unknown command in row {i}: {span[:70]}")
    return probs


def g_summary_items():
    text = (REPO / BUNDLE_REL).read_text(encoding="utf-8")
    probs = check_items(text)
    items = bundle_items(text)
    lines = text.split("\n")
    # controls: each check must be able to go red on the real text
    sep = next((i for i, ln in enumerate(lines) if ln.startswith("|") and set(ln) <= set("|-: ")), None)
    e_row = next((i for i, ln in enumerate(lines) if ln.startswith("|") and '[E]#1 ' in ln), None)
    ctl = {}
    if e_row is not None:
        ctl["removed row"] = any(p.startswith("missing row for [E]#1") for p in check_items("\n".join(lines[:e_row] + lines[e_row + 1:])))
    if sep is not None:
        row = '| 99 | Z | [Z]#9 "no such item" | do it | none -- nothing | nothing |'
        ctl["stale row"] = any(p.startswith("stale or unknown source [Z]#9") for p in check_items("\n".join(lines[:sep + 1] + [row] + lines[sep + 1:])))
    cmd = "`python wiki/tools/kme_replay.py rank"
    mutated = text.replace(cmd, cmd.replace("rank", "rankx"), 1)
    ctl["unknown command"] = mutated != text and any(p.startswith("unknown command") for p in check_items(mutated))
    ctl["removed header"] = check_items(text.replace(SUMMARY_HEAD, "## Not the summary")) == ["no summary section"]
    ctl_ok = len(ctl) == 4 and all(ctl.values())
    ok = not probs and len(items) >= 19 and ctl_ok
    return ok, (f"{len(items)} item key(s) incl. sync (>= 19), {len(summary_rows(text))} row(s), problems={probs[:4]}, "
                f"controls report: {ctl}")


def uat_pending(text, nn):
    """`UAT <NN>#<n>` for every `### <n>.` block under `## Tests` whose result is [pending]."""
    import re
    m = re.search(r"^## Tests[ \t]*$", text, re.M)
    if not m:
        return []
    end = text.find("\n## ", m.end())
    sec = text[m.end():end if end >= 0 else len(text)]
    out = []
    for blk in re.split(r"^(?=### \d+\. )", sec, flags=re.M):
        h = re.match(r"^### (\d+)\. ", blk)
        if h and re.search(r"^result:[ \t]*\[pending\][ \t]*$", blk, re.M):
            out.append(f"UAT {nn}#{h.group(1)}")
    return out


def ver_entries(text, nn):
    """`VER <NN>#<k>` for each human_verification entry of a human_needed VERIFICATION front matter."""
    import re
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not fm or not re.search(r"^status:[ \t]*human_needed[ \t]*$", fm.group(1), re.M):
        return []
    out, inside, base = [], False, None
    for ln in fm.group(1).split("\n"):
        if re.match(r"^human_verification:[ \t]*$", ln):
            inside = True
        elif inside:
            item = re.match(r"^([ \t]*)-(?:[ \t]|$)", ln)
            if item:
                if base is None:
                    base = len(item.group(1))
                if len(item.group(1)) == base:       # one list entry, whatever its shape (a string, or `test:`/`expected:` keys)
                    out.append(f"VER {nn}#{len(out) + 1}")
            elif ln.strip() and not ln[0].isspace():  # an unindented non-item line ends the list; indented lines continue an entry
                break
    return out


def uat_keys(phases_dir):
    """Pending human checks DISCOVERED from every phase directory NN-*; {NN: has any UAT/VERIFICATION file} beside them."""
    keys, have = [], {}
    for d in sorted(Path(phases_dir).glob("[0-9][0-9]-*")):
        if not d.is_dir():
            continue
        nn = d.name[:2]
        uats, vers = sorted(d.glob("*-UAT.md")), sorted(d.glob("*-VERIFICATION.md"))
        have[nn] = have.get(nn, False) or bool(uats or vers)
        for f in uats:
            keys += uat_pending(f.read_text(encoding="utf-8"), nn)
        if not uats:
            for f in vers:
                keys += ver_entries(f.read_text(encoding="utf-8"), nn)
    return keys, have


def check_uat(text, phases_dir):
    """(status, problems): status is 'SKIP' when a cited phase has no files here, else 'OK'."""
    import re
    rows = [r for r in summary_rows(text) if len(r) == 6]
    cited = [t for r in rows for t in source_tokens(r[2]) if re.match(r"^(UAT|VER) \d{2}#\d+$", t)]
    keys, have = uat_keys(phases_dir)
    absent = sorted({t.split()[1][:2] for t in cited if not have.get(t.split()[1][:2])})
    if absent:
        return "SKIP", [f"phase(s) {absent} cited by a row have no UAT or VERIFICATION file on this checkout"]
    probs = [f"missing row for {k}" for k in keys if k not in cited]
    probs += [f"stale row cites {t}" for t in cited if t not in keys]
    return "OK", probs


def g_summary_uat():
    import re
    # controls on synthetic trees, run before anything is judged from the real files
    uat_txt = ("---\nstatus: testing\n---\n\n## Current Test\n\nnumber: 1\n\n## Tests\n\n### 1. a\nexpected: x\nresult: [pending]\n\n"
               "### 2. b\nexpected: x\nresult: pass\n\n### 3. c\nexpected: x\nresult: [pending]\n\n## Summary\n\ntotal: 3\n")
    got_uat = uat_pending(uat_txt, "05")
    ver_txt = "---\nphase: x\nstatus: human_needed\nhuman_verification:\n  - \"one thing\"\nscore: 1/1\n---\n\n# body\n"
    got_ver = ver_entries(ver_txt, "05")
    got_none = ver_entries(ver_txt.replace("human_needed", "passed"), "05")
    ctl = {"two pending of three": got_uat == ["UAT 05#1", "UAT 05#3"], "one human_verification entry": got_ver == ["VER 05#1"],
           "passed verification yields none": got_none == []}
    multi_txt = ("---\nphase: x\nstatus: human_needed\nhuman_verification:\n"
                 "  - test: \"first\"\n    expected: \"e1\"\n    why_human: \"w1\"\n"
                 "  - test: \"second\"\n    expected: \"e2\"\n    why_human: \"w2\"\n"
                 "  - test: \"third\"\n    expected: \"e3\"\n    why_human: \"w3\"\nscore: 1/1\n---\n\n# body\n")
    flat_txt = ("---\nstatus: human_needed\nhuman_verification:\n- \"a\"\n- \"b\"\n- \"c\"\nscore: 1/1\n---\n")
    ctl["three multi-key entries count three"] = ver_entries(multi_txt, "05") == ["VER 05#1", "VER 05#2", "VER 05#3"]
    ctl["three unindented one-string entries count three"] = ver_entries(flat_txt, "05") == ["VER 05#1", "VER 05#2", "VER 05#3"]
    pd = scratch("ph")
    (pd / "05-x").mkdir()
    (pd / "05-x" / "05-UAT.md").write_text(uat_txt, encoding="utf-8")
    (pd / "01-y").mkdir()
    (pd / "01-y" / "01-VERIFICATION.md").write_text(ver_txt, encoding="utf-8")
    head = f"{SUMMARY_HEAD}\n\n| # | pillar | source | action | exact command | what closes when it lands |\n|---|---|---|---|---|---|\n"
    full = head + "| 1 | P | UAT 05#1 ; UAT 05#3 ; VER 01#1 | a | none -- x | y |\n"
    lacking = head + "| 1 | P | UAT 05#1 ; VER 01#1 | a | none -- x | y |\n"
    extra = full + "| 2 | P | UAT 05#2 | a | none -- x | y |\n"
    gone = full.replace("VER 01#1", "VER 04#1")
    ctl["complete synthetic table is clean"] = check_uat(full, pd) == ("OK", [])
    ctl["removed row is reported"] = check_uat(lacking, pd)[1] == ["missing row for UAT 05#3"]
    ctl["row for an answered check is stale"] = check_uat(extra, pd)[1] == ["stale row cites UAT 05#2"]
    ctl["a cited phase without files is a SKIP"] = check_uat(gone, pd)[0] == "SKIP"
    pd6 = scratch("ph6")                     # its own tree: phase 6 (and any later NN-*) is discovered, never listed
    (pd6 / "06-z").mkdir()
    (pd6 / "06-z" / "06-UAT.md").write_text("---\nstatus: testing\n---\n\n## Tests\n\n### 1. a\nexpected: x\nresult: [pending]\n",
                                            encoding="utf-8")
    ctl["a phase 06 directory is discovered"] = uat_keys(pd6)[0] == ["UAT 06#1"]
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    text = (REPO / BUNDLE_REL).read_text(encoding="utf-8")
    real = REPO / PHASES_REL
    status, probs = check_uat(text, real)
    if status == "SKIP":
        return "SKIP", probs[0]
    keys, _have = uat_keys(real)
    n_uat = sum(1 for k in keys if k.startswith("UAT"))
    n_ver = sum(1 for k in keys if k.startswith("VER"))
    ok = not probs and n_uat >= 11 and n_ver >= 1
    return ok, (f"{n_uat} pending UAT key(s) (>= 11) and {n_ver} VER key(s) (>= 1) each have a row, problems={probs[:4]}, "
                f"{len(ctl)} controls report")


GATES_SUMMARY = [("V-KMER-BUNDLE-SUMMARY-ITEMS", g_summary_items), ("V-KMER-BUNDLE-SUMMARY-UAT", g_summary_uat)]


# --------------------------------------------------------------------------- plan 05-03: the program done-gate reads the ranking
def _icp_pair_tools():
    """test_kme_pillars' own helpers for the done-gate pair gate (imported lazily: the wrapper rebinds CE globals)."""
    import test_kme_pillars as tkp
    return tkp._icp(), tkp.icp_sources, tkp.r3_led


def g_r3_pair():
    """The instrument's own KME-L primary, its KME-G smoke, and the pillar fences, through the wrapper's R3."""
    icp, icp_sources, r3_led = _icp_pair_tools()
    root = scratch("r3l")
    tracer_fixture(root)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": POP_KR, "KME-G": POP_KR})
    outd = scratch("r3lo")
    rc1, o1, e1 = run_main(klr_args(root, outd, frozen))
    rc2, o2, e2 = run_main(klr_args(root, outd, frozen, denominator="KME-G"))
    prim, smoke = (next(iter(outd.glob(f"L-{d}-*.md")), None) for d in ("KME-L", "KME-G"))
    if rc1 != 0 or rc2 != 0 or not (prim and smoke):
        return False, f"rc={rc1},{rc2} files={sorted(f.name for f in outd.glob('*.md'))} err={(e1 + e2)[-200:]}"
    fp, fk = (icp.front_matter_fields(f.read_text(encoding="utf-8")) for f in (prim, smoke))
    shaped = (fp["evidence_role"] == "primary" and fp["terminal_evidence"] is True and fp["pillar"] == "L"
              and fk["evidence_role"] == "smoke" and fk["terminal_evidence"] is False and fp["unranked_ids"] == [])
    res = icp.ce.Resolver()

    def fails(pillar, refs, terminal=None):
        led = r3_led(pillar, *refs)
        if terminal:
            led["state"][pillar]["terminal"] = terminal
        with icp_sources(icp, frozen_file=frozen):
            return icp.check_measurement_scope(led, res, only=[pillar])
    meas = "RESEARCH_INSUFFICIENT_EVIDENCE"
    accepted = fails("L", [prim], meas)
    smk = fails("L", [smoke])
    smk_term = fails("L", [smoke], meas)
    none = fails("L", [], meas)
    wrong = fails("E", [prim])
    ok = (shaped and accepted == [] and len(smk) == 1 and smk[0].startswith("R3 L:") and "smoke" in smk[0]
          and any("cites no kme_replay primary" in x for x in smk_term)
          and len(none) == 1 and "cites no kme_replay primary" in none[0]
          and len(wrong) == 1 and wrong[0].startswith("R3 E:") and "measures pillar L" in wrong[0])
    return ok, (f"front shaped={shaped} primary accepted={accepted == []} smoke={smk} smoke-as-terminal={len(smk_term)} "
                f"line(s) no-primary={none} L-file-cited-by-E={wrong}")


def g_r3_table_pinned():
    """The wrapper's copy of the instrument's marks and rule table equals the instrument's own (no silent drift)."""
    icp, _s, _r = _icp_pair_tools()
    pairs = {"REPLAY_RULE_DENOMINATORS": (icp.REPLAY_RULE_DENOMINATORS, {kr.PILLAR: list(kr.RULE_DENOMINATORS)}),
             "KMER_INSTRUMENT": (icp.KMER_INSTRUMENT, kr.INSTRUMENT),
             "KMER_BODY_MARKER": (icp.KMER_BODY_MARKER, kr.KMER_BODY_MARKER),
             "KMER_BODY_END": (icp.KMER_BODY_END, kr.KMER_BODY_END),
             "KMER_ROLLOVER_GROWTH": (icp.KMER_ROLLOVER_GROWTH, kr.ROLLOVER_GROWTH),
             "KMER_CANDIDATES": (tuple(icp.KMER_CANDIDATES), tuple(kr.CANDIDATES)),
             "REPLAY_PILLARS": (tuple(icp.REPLAY_PILLARS), (kr.PILLAR,))}
    off = [k for k, (a, b) in pairs.items() if a != b]
    return not off, f"equal: {sorted(k for k in pairs if k not in off)}; differ: {off}"


GATES_R3 = [("V-KMER-R3-PAIR", g_r3_pair), ("V-KMER-R3-TABLE-PINNED", g_r3_table_pinned)]


GATES_TRACER = [("V-KMER-TRACER-E2E", g_tracer_e2e), ("V-KMER-CONTRACT-E2E", g_contract_e2e)]
GATES = list(GATES_TRACER) + GATES_ROLLOVER + GATES_RETRY + GATES_CONTRACT + GATES_BUNDLE + GATES_R3 + GATES_SUMMARY


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
DRILL_GATES = [n for n, _ in GATES if n not in ("V-KMER-TRACER-E2E", "V-KMER-CONTRACT-E2E", "V-KMER-BUNDLE-SUMMARY-UAT")]    # the subprocess tracer is excluded (patches cannot reach it)


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


def _m_ascending():
    def mutant(entries):
        have = [e for e in entries if e.get("upper_bound_weighted") is not None]
        return sorted(have, key=lambda e: (e["upper_bound_weighted"], kr.CANDIDATES.index(e["candidate"])))
    return _patch(kr, "rank_candidates", mutant)


def _m_unmeasured_as_zero():
    def mutant(entries):
        have = [dict(e, upper_bound_weighted=0.0 if e.get("upper_bound_weighted") is None
                     else e["upper_bound_weighted"]) for e in entries]
        return sorted(have, key=lambda e: (-e["upper_bound_weighted"], kr.CANDIDATES.index(e["candidate"])))
    return _patch(kr, "rank_candidates", mutant)


def _m_tie_reversed():
    def mutant(entries):
        have = [e for e in entries if e.get("upper_bound_weighted") is not None]
        return sorted(have, key=lambda e: (-e["upper_bound_weighted"], -kr.CANDIDATES.index(e["candidate"])))
    return _patch(kr, "rank_candidates", mutant)


def _m_raw_paths():
    return _patch(kr, "scrub_details", lambda cid, details: details)


def _m_distinct_ranks():
    return _patch(kr, "dense_ranks", lambda entries: list(range(1, len(entries) + 1)))


def _m_half_denominator():
    return _patch(kr, "denominator_for", lambda cid, scan: scan["measured"]["weighted"]
                  / (2 if cid == "unchanged_precondition_retries" else 1))


def _m_select_all():
    return _patch(kr, "in_selection", lambda sid, selected: True)


def _m_compare_always_exact():
    return _patch(kp, "compare_population", lambda measured, frozen: ("exact", {}))


def _m_terminal_ignores_unranked():
    return _patch(kr, "terminal_ok", lambda role, match, frozen_source, unranked, growth=kr.ROLLOVER_GROWTH:
                  role == "primary" and match == "exact" and bool(frozen_source)
                  and bool(frozen_source.get("all_default")) and growth == kr.ROLLOVER_GROWTH)


def _m_terminal_ignores_growth():
    return _patch(kr, "terminal_ok", lambda role, match, frozen_source, unranked, growth=kr.ROLLOVER_GROWTH:
                  role == "primary" and match == "exact" and bool(frozen_source)
                  and bool(frozen_source.get("all_default")) and not unranked)


def _m_interval_back():
    """The pre-fix entry: unrounded share and the observer's full numerator (weighted_lo / weighted_interval)."""
    return _patch(kr, "entry_figures", lambda pres, upper, share: {
        "upper_bound_weighted": kr._r(upper), "upper_bound_share": share, "numerator": pres["numerator"]})


def _m_one_thread():
    return _patch(kr, "thread_of", lambda o: "main")


def _m_parallel_is_retry():
    return _patch(kr, "same_message", lambda prev, mid: False)


MUTANTS = [
    ("M1 rollover_avoided ignores the thread floor (avoids the whole cut)", _m_floor_ignored,
     ["V-KMER-ROLLOVER-FLOOR"]),
    ("M2 rollover_segments ignores actual compactions (one segment)", _m_one_segment, ["V-KMER-ROLLOVER-SEGMENT"]),
    ("M3 retry_kind ignores the write epoch (a rerun after an Edit is a retry)", _m_write_epoch_ignored,
     ["V-KMER-RETRY-INTERVENING-WRITE"]),
    ("M4 retry_key keys a Bash call by its full input JSON (a changed description hides the retry)",
     _m_bash_full_json_key, ["V-KMER-RETRY-COMMAND-KEY"]),
    ("M5 upper_bound_of returns weighted_interval[0]", _m_upper_is_lower, ["V-KMER-REREADS-EQUALS-E"]),
    ("M6 rank_candidates sorts ascending (lowest upper bound first)", _m_ascending, ["V-KMER-RANK-ORDER"]),
    ("M7 rank_candidates ranks an UNMEASURED candidate as 0.0", _m_unmeasured_as_zero,
     ["V-KMER-UNMEASURED-NEVER-ZERO"]),
    ("M8 rank_candidates breaks a tie in reverse candidate order", _m_tie_reversed,
     ["V-KMER-RANK-TIE-DETERMINISTIC"]),
    ("M9 candidate_status ignores observability (a partly observed candidate is ranked)",
     _m_status_ignores_observability,
     ["V-KMER-RETRY-UNPAIRED-UNMEASURED", "V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED"]),
    ("M10 denominator_for halves the weighted for unchanged_precondition_retries", _m_half_denominator,
     ["V-KMER-SAME-DENOMINATOR"]),
    ("M11 in_selection selects every session (an unselected project enters the figures)", _m_select_all,
     ["V-KMER-SELECTED-ONLY"]),
    ("M12 kp.compare_population always answers exact (a drifted population ranks)", _m_compare_always_exact,
     ["V-KMER-DRIFT-ALL-UNMEASURED"]),
    ("M13 terminal_ok ignores unranked candidates", _m_terminal_ignores_unranked, ["V-KMER-TERMINAL-EVIDENCE"]),
    ("M14 terminal_ok ignores the rollover growth (a ranking at any G is terminal)", _m_terminal_ignores_growth,
     ["V-KMER-ROLLOVER-GROWTH-PINNED"]),
    ("M15 a ranked entry carries the observer's weighted_lo / weighted_interval and an unrounded share",
     _m_interval_back, ["V-KMER-UPPER-ONLY"]),
    ("M19 scrub_details keeps the raw read paths in a ranking file", _m_raw_paths, ["V-KMER-NO-RAW-PATHS"]),
    ("M18 dense_ranks gives equal figures distinct ranks", _m_distinct_ranks, ["V-KMER-RANK-TIE-DETERMINISTIC"]),
    ("M16 thread_of keys every line to the main thread (a subagent's call pairs with the main thread's)",
     _m_one_thread, ["V-KMER-THREAD-KEYED"]),
    ("M17 same_message never matches (parallel identical tool uses in one message count as a retry)",
     _m_parallel_is_retry, ["V-KMER-THREAD-KEYED"]),
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
