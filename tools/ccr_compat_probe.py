"""CCR compat probe driver: runs the ccr-uz-probe plugin headless on the host under test and judges each CCR surface.

    python -I tools/ccr_compat_probe.py --selftest     # pure evaluator checks, no model call
    python -I tools/ccr_compat_probe.py                # the real run (haiku, per-case budget, cumulative guard)
    options: --cases S1a,S1b (resumable), --fresh (discard saved cases), --results PATH

Surfaces are the ones the CPP Cognitive Runtime actually rewrites (mods/cpp-cognitive-runtime/hooks/register.ts):
subagent attachments (drop and replace), the Bash tool.call seam, tool deferral, the memory prompt section.
Verdict per case: PASS, FAIL, or INCONCLUSIVE (the surface never fired, so absence proves nothing).
Results are written after every case to vault/programs/ccr/compat/probe-results.json (or --results).
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
PROBE = REPO / "mods" / "ccr-uz-probe"
OUT = pathlib.Path(os.path.expanduser("~")) / ".claude" / "state" / "ccr" / "uz-probe-out"   # the plugin writes here (register.ts OUT)
RESULTS = REPO / "vault" / "programs" / "ccr" / "compat" / "probe-results.json"
if "--results" in sys.argv:
    RESULTS = pathlib.Path(sys.argv[sys.argv.index("--results") + 1])
GUARD = 1_500_000          # cumulative processed tokens for the whole probe (V1 lesson)
CASE_BUDGET_USD = "0.40"   # per-case hard stop in the CLI
REQUIRED = ("S1b", "S2", "S3", "S4")
REPLACED_LEN = len("UZ-REPLACED-INSTRUCTIONS")
LEAN_DROP_MAX_RATIO = 0.60  # a >= 40 % subagent drop; measured 2.1.296: -67 % (M1), -40..-50 % (S1)

SUB_PROMPT = ("Use the Agent tool exactly once with subagent_type 'general-purpose' and the prompt "
              "'What is 2+2? Answer with just the digit.' Then reply with only the digit the subagent returned.")
TRIVIAL = "Reply with the single word OK."


def seam_prompt(counter: pathlib.Path) -> str:
    cmd = f"echo UZ_REAL >> {counter.as_posix()} && echo UZ_REAL"
    return f"Run this exact Bash command, then tell me its exact stdout and nothing else: {cmd}"


def processed(usage) -> int | None:
    """Input side of provider usage (input + cache creation + cache read); None when the shape is not a flat dict."""
    if not isinstance(usage, dict):
        return None
    vals = [v for k, v in usage.items() if isinstance(v, int) and ("input" in k.lower() or "cache" in k.lower())]
    return sum(vals) if vals else None


def sub_processed(rows) -> int | None:
    parts = [processed(r.get("usage")) for r in rows if r.get("ev") == "turn.complete" and r.get("agent")]
    parts = [p for p in parts if p is not None]
    return sum(parts) if parts else None


def judge(case_id: str, rows: list, answer: str, base_sub: int | None, counter_lines: int | None) -> tuple[str, str]:
    att = [r for r in rows if r.get("ev") == "prompt.attachment" and r.get("agent")]
    sub = sub_processed(rows)
    spawned = any(r.get("ev") == "agent.spawn" for r in rows)
    if case_id == "S1a":
        if not spawned or sub is None:
            return "INCONCLUSIVE", "no subagent ran or its usage was unreadable: no baseline"
        return ("PASS", f"baseline subagent processed={sub}") if "4" in answer else ("FAIL", "baseline answer lost")
    if case_id == "S1b":
        tgt = [r for r in att if r.get("type") in ("instructions", "skill_listing")]
        if not spawned or not tgt:
            return "INCONCLUSIVE", "no subagent instructions/skill_listing attachment fired"
        if any(r.get("out") is not None for r in tgt):
            return "FAIL", "an attachment was not dropped: " + json.dumps([[r.get("type"), r.get("out")] for r in tgt])
        if "4" not in answer:
            return "FAIL", "answer lost under the drop"
        if base_sub is None or sub is None:
            return "INCONCLUSIVE", "dropped, but a usage figure is missing, so the saving is unmeasured"
        ratio = sub / base_sub
        return ("PASS" if ratio <= LEAN_DROP_MAX_RATIO else "FAIL"), f"subagent processed {sub} vs baseline {base_sub} (ratio {ratio:.2f}, max {LEAN_DROP_MAX_RATIO})"
    if case_id == "S2":
        tgt = [r for r in att if r.get("type") == "instructions"]
        if not spawned or not tgt:
            return "INCONCLUSIVE", "no subagent instructions attachment fired"
        if any(r.get("out") != REPLACED_LEN for r in tgt):
            return "FAIL", "replacement text not applied: " + json.dumps([r.get("out") for r in tgt])
        return ("PASS", "instructions replaced by the marker") if "4" in answer else ("FAIL", "answer lost under the replace")
    if case_id == "S3":
        calls = [r for r in rows if r.get("ev") == "tool.call"]
        if not calls:
            return "INCONCLUSIVE", "the Bash tool.call hook never fired"
        if not any(r.get("applied") for r in calls):
            return "FAIL", "tool.call fired but did not apply the rewrite"
        if counter_lines != 1:
            return "FAIL", f"tool ran {counter_lines} times (must be exactly 1: the seam must not replay the command)"
        return ("PASS", "result rewritten through next(e), command ran once") if "UZ-PROJECTED" in answer else ("FAIL", "model did not see the rewritten stdout")
    if case_id == "S4":
        d = [r for r in rows if r.get("ev") == "tool.describe" and r.get("tool") not in
             ("Read", "Edit", "Write", "Glob", "Grep", "Bash", "PowerShell", "Agent", "ToolSearch", "Skill")]
        if not d:
            return "INCONCLUSIVE", "no non-core tool was described"
        if not any(r.get("deferred") for r in d):
            return "FAIL", "no non-core tool was deferred"
        return ("PASS", f"{sum(1 for r in d if r.get('deferred'))} tools deferred") if "OK" in answer else ("FAIL", "session broke under deferral")
    if case_id == "S5":
        s = [r for r in rows if r.get("ev") == "prompt.section" and r.get("name") == "memory"]
        if not s:
            return "INCONCLUSIVE", "no memory section in this cwd (limit to name, does not block widening)"
        return ("PASS", "memory section dropped") if any(r.get("applied") for r in s) else ("FAIL", "memory section present but not dropped")
    return "FAIL", "unknown case"


def selftest() -> int:
    ok = True

    def check(name, got, want):
        nonlocal ok
        if got != want:
            ok = False
        print(("PASS " if got == want else "FAIL ") + name + f": {got} (want {want})")

    mk = lambda out, use: [{"ev": "agent.spawn"}, {"ev": "prompt.attachment", "agent": True, "type": "instructions", "out": out},
                           {"ev": "turn.complete", "agent": "a1", "usage": {"input_tokens": 10, "cache_read_input_tokens": use, "output_tokens": 5}}]
    check("processed-ignores-output", processed({"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 500}), 100)
    check("S1b-pass", judge("S1b", mk(None, 30), "4", 100, None)[0], "PASS")
    check("S1b-fail-not-dropped", judge("S1b", mk(500, 30), "4", 100, None)[0], "FAIL")
    check("S1b-fail-no-saving", judge("S1b", mk(None, 90), "4", 100, None)[0], "FAIL")
    check("S1b-inconclusive-no-attachment", judge("S1b", [{"ev": "agent.spawn"}], "4", 100, None)[0], "INCONCLUSIVE")
    check("S2-fail-wrong-len", judge("S2", mk(7, 30), "4", 100, None)[0], "FAIL")
    check("S2-pass", judge("S2", mk(REPLACED_LEN, 30), "4", 100, None)[0], "PASS")
    seam = [{"ev": "tool.call", "applied": True}]
    check("S3-pass", judge("S3", seam, "UZ-PROJECTED", None, 1)[0], "PASS")
    check("S3-fail-replayed", judge("S3", seam, "UZ-PROJECTED", None, 2)[0], "FAIL")
    check("S3-fail-not-seen", judge("S3", seam, "UZ_REAL", None, 1)[0], "FAIL")
    check("S3-inconclusive-never-fired", judge("S3", [], "x", None, 0)[0], "INCONCLUSIVE")
    check("S4-fail-none-deferred", judge("S4", [{"ev": "tool.describe", "tool": "WebFetch", "deferred": None}], "OK", None, None)[0], "FAIL")
    check("S5-inconclusive-absent", judge("S5", [], "OK", None, None)[0], "INCONCLUSIVE")
    print("UZ_SELFTEST=" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def run_case(claude: str, case: dict, tmp: pathlib.Path) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mode.json").write_text(json.dumps({"mode": case["mode"]}), encoding="ascii")
    t0 = time.time()
    p = subprocess.run([claude, "-p", "--plugin-dir", str(PROBE), "--model", "haiku", "--output-format", "json",
                        "--max-budget-usd", CASE_BUDGET_USD, "--allowedTools", "Bash,Agent"],
                       input=case["prompt"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=tmp, timeout=400)
    try:
        j = json.loads(p.stdout)
    except ValueError:
        return {"id": case["id"], "verdict": "FAIL", "why": "claude -p gave no JSON: rc=%s err=%s" % (p.returncode, p.stderr[:200])}
    sid = j.get("session_id")
    f = OUT / f"{sid}.jsonl"
    if not f.exists():   # fall back to the newest file written during this case
        fresh = [x for x in OUT.glob("*.jsonl") if x.stat().st_mtime >= t0 - 1]
        f = max(fresh, key=lambda x: x.stat().st_mtime) if fresh else f
    rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()] if f.exists() else []
    tot = sum(x for x in (processed(r.get("usage")) for r in rows if r.get("ev") == "turn.complete") if x)
    return {"id": case["id"], "mode": case["mode"], "session": sid, "answer": str(j.get("result", ""))[:400], "rows": rows,
            "total_processed": tot, "sub_processed": sub_processed(rows), "cost_usd": j.get("total_cost_usd")}


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    claude = shutil.which("claude")
    ver = subprocess.run([claude, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip() if claude else ""
    if not claude or not PROBE.exists():
        print(json.dumps({"verdict": "ABORT", "why": "claude or the uz-probe plugin is missing", "claude": claude, "probe": str(PROBE)}))
        return 2
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uzprobe_"))   # outside any repo: a clean floor
    counter = tmp / "counter.txt"
    cases = [dict(id="S1a", mode="observe", prompt=SUB_PROMPT), dict(id="S1b", mode="subagent-lean", prompt=SUB_PROMPT),
             dict(id="S2", mode="subagent-replace", prompt=SUB_PROMPT), dict(id="S3", mode="seam", prompt=seam_prompt(counter)),
             dict(id="S4", mode="defer", prompt=TRIVIAL), dict(id="S5", mode="section-drop", prompt=TRIVIAL)]
    # Resumable: --cases S1a,S1b runs only those; finished cases in probe-results.json are kept (--fresh starts over).
    want = None
    if "--cases" in sys.argv:
        want = set(sys.argv[sys.argv.index("--cases") + 1].split(","))
    res = {"host": ver, "guard": GUARD, "cases": [], "spent": 0}
    if RESULTS.exists() and "--fresh" not in sys.argv:
        old = json.loads(RESULTS.read_text(encoding="utf-8"))
        if old.get("host") == ver:
            res = {k: old[k] for k in ("host", "guard", "cases", "spent")}
    done = {c["id"]: c for c in res["cases"]}
    base_sub = (done.get("S1a") or {}).get("sub_processed")
    res["cases"] = [c for c in res["cases"] if want is not None and c["id"] not in want]
    for c in cases:
        if want is not None and c["id"] not in want:
            if c["id"] in done and done[c["id"]] not in res["cases"]:
                res["cases"].append(done[c["id"]])
            continue
        if want is None and c["id"] in done and "--fresh" not in sys.argv:
            res["cases"].append(done[c["id"]])
            continue
        if res["spent"] >= GUARD:
            res["cases"].append({"id": c["id"], "verdict": "INCONCLUSIVE", "why": f"cumulative guard {GUARD} reached before this case"})
            continue
        if counter.exists():
            counter.unlink()
        r = run_case(claude, c, tmp)
        if "verdict" not in r:
            lines = len(counter.read_text().splitlines()) if counter.exists() else 0
            r["verdict"], r["why"] = judge(c["id"], r["rows"], r["answer"], base_sub, lines)
            if c["id"] == "S1a":
                base_sub = r["sub_processed"]
            res["spent"] += r["total_processed"]
            r["rows"] = len(r["rows"])      # the rows stay in OUT; the result keeps the count
        res["cases"].append(r)
        RESULTS.write_text(json.dumps(res, indent=1), encoding="utf-8")   # write as you go
    v = {c["id"]: c["verdict"] for c in res["cases"]}
    res["verdicts"] = v
    res["all_required_pass"] = all(v.get(k) == "PASS" for k in REQUIRED)
    res["named_limits"] = [f"{k}={x}" for k, x in v.items() if x != "PASS"]
    RESULTS.write_text(json.dumps(res, indent=1), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"host": ver, "verdicts": v, "all_required_pass": res["all_required_pass"], "spent": res["spent"], "results": str(RESULTS)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
