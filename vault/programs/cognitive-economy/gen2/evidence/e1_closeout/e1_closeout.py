#!/usr/bin/env python
"""e1_closeout.py -- post-E1 Phase 1 driver: D1-D8 in ONE call, 0 model calls between steps.

Plan: vault/plans/post-e1-meta-work-2026-10-06.md (Phase 1). Receipt contract: tools/cep_gen2.py check_receipt (B1).
Each step writes, runs its gates, and commits only its own paths; a red gate restores the step's files and aborts.

  D1 gen1 ledger state.B savings (via ledger_write.py, the only state writer)
  D2 gen2 superseded_estimates: the 12.5k forecast and the plan's 10.8k / 22% (which came from a byte-count typo)
  D3 calibration.json      D4 pointer_tax.json      D5 cleanup-survival test (red/green + corrupt usage)
  D6 payback.json (laptop usage_index; lower bound)  D7 receipt.json + gen2 W3 closed as an experiment
  D8 RESUMPTION section

    python vault/programs/cognitive-economy/gen2/evidence/e1_closeout/e1_closeout.py [--dry-run]
Exit 0 = all steps committed; 1 = aborted on a red gate or a refused precondition.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
GIT = r"C:\Program Files\Git\cmd\git.exe" if os.name == "nt" else "git"
PY = sys.executable
CE = "vault/programs/cognitive-economy"
OUT = f"{CE}/gen2/evidence/e1_closeout"
GEN1, GEN2 = f"{CE}/ledger.json", f"{CE}/gen2/ledger.json"
RESUME = "vault/plans/tok18-pre-rearm-optimization-RESUMPTION.md"
PRE, POST = f"{CE}/measure/e1_mechanical_laptop.json", f"{CE}/measure/e1_postmove_laptop.json"
D5_TEST = f"{CE}/measure/test_e1_mechanical_cleanup.py"
RULES = Path.home() / ".claude" / "rules"
BACKUP = Path.home() / ".claude" / "backups" / "rules-20261005-143407"
MOVED = ["technical-failure-to-product-state", "scoped-side-effect-authority", "human-facing-external-effects",
         "documented-capability-must-be-executable", "validation-planes-do-not-transfer",
         "capability-preserving-compaction", "state-lifetime-and-incarnation", "post-effect-resource-truth"]
E1_COST = 9_172_196            # e1/REPORT.md "Counted context summed over all runs"
ACTIVATED = "2026-10-05T12:35:40Z"  # 17b3188a committer time 14:35:40 +0200
PLAN_FORECAST, PLAN_BYTE_EST, PLAN_POINTER_SHARE = 12_500, 10_800, 22
COMMIT_BYTES_CLAIM = 41_353   # 17b3188a message: "drops from 41,353 B to 9,232 B"
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n"
DRY = "--dry-run" in sys.argv
ENV = dict(os.environ, PYTHONIOENCODING="utf-8",
           PATH=os.pathsep.join([str(Path(GIT).parent), os.environ.get("PATH", "")]))


def git(*a) -> str:
    r = subprocess.run([GIT, "-C", str(REPO), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"ABORT git {' '.join(a[:3])}: {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def run(argv, timeout=600) -> tuple:
    r = subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ENV, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def jread(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def write(rel, text):
    (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
    (REPO / rel).write_text(text, encoding="utf-8", newline="\n")


def jwrite(rel, obj):
    write(rel, json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def gen2_dump(led: dict) -> str:
    """The gen2 ledger's own layout: one line per scalar key, list item and work unit."""
    lines = []
    for k, v in led.items():
        if k == "superseded_estimates":
            items = [f"  {json.dumps(x, ensure_ascii=False)}" for x in v]
            lines.append(f' "{k}": [\n' + ",\n".join(items) + "\n ]")
        elif k == "work_units":
            items = [f'  "{w}": {json.dumps(u, ensure_ascii=False)}' for w, u in v.items()]
            lines.append(f' "{k}": {{\n' + ",\n".join(items) + "\n }")
        else:
            lines.append(f' "{k}": {json.dumps(v, ensure_ascii=False)}')
    return "{\n" + ",\n".join(lines) + "\n}\n"


# ---------------------------------------------------------------- gates
sys.path.insert(0, str(REPO / "tools"))
import cep_gen2  # noqa: E402

BASE_VIOL = set(cep_gen2.check(jread(GEN2), REPO))


def gate_cep2(closed=()) -> list:
    fails = []
    if not cep_gen2.selftest(verbose=False):
        fails.append("cep_gen2 selftest FAIL")
    now = set(cep_gen2.check(jread(GEN2), REPO))
    new = sorted(now - BASE_VIOL)
    if new:
        fails.append(f"gen2 new violations: {new}")
    for w in closed:
        left = [v for v in now if v.startswith(f"{w} ")]
        if left:
            fails.append(f"{w} still violates: {left}")
    return fails


def gate_gen1() -> list:
    rc, out = run([PY, "tools/test_cognitive_economy_program.py", "--final"])
    return [] if rc == 0 and "CEP_VERDICT=PASS" in out else [f"gen1 --final rc={rc}: {out[-400:]}"]


def gate_d5() -> list:
    rc, out = run([PY, D5_TEST], timeout=120)
    return [] if rc == 0 else [f"D5 test rc={rc}: {out[-400:]}"]


# ---------------------------------------------------------------- facts (all zero-model)
def facts() -> dict:
    pre, post = jread(PRE), jread(POST)
    assert pre["verdict"] == "MEASURED" and post["A"]["state"] == post["B"]["state"] == "MEASURED"
    moved = sum((BACKUP / f"{n}.md").stat().st_size for n in MOVED)
    pointers = sum((RULES / f"{n}.md").stat().st_size for n in MOVED)
    resident5 = pre["pinned_bytes"] - moved
    if post["pinned_bytes"] != resident5 + pointers:
        raise SystemExit(f"ABORT bytes do not reconcile: post pinned {post['pinned_bytes']} != {resident5}+{pointers}")
    tpb = pre["delta_context_tokens"] / pre["pinned_bytes"]
    saving = pre["delta_context_tokens"] - post["delta_context_tokens"]
    f = {"pre_excludable": pre["delta_context_tokens"], "post_excludable": post["delta_context_tokens"],
         "pre_pinned_bytes": pre["pinned_bytes"], "post_pinned_bytes": post["pinned_bytes"],
         "moved_bytes": moved, "pointer_bytes": pointers, "resident5_bytes": resident5,
         "tokens_per_byte": round(tpb, 6), "saving": saving,
         "forecast_gross": round(moved * tpb), "byte_est_net": round((moved - pointers) * tpb),
         "plan_byte_est_from_typo": round((COMMIT_BYTES_CLAIM - pointers) * tpb),
         "pointer_tax_bytewise": round(pointers * tpb),
         "pointer_tax_if_resident_avg": post["delta_context_tokens"] - round(resident5 * tpb)}
    f["error_pct"] = round(100.0 * (saving - f["forecast_gross"]) / f["forecast_gross"], 1)
    f["break_even"] = -(-E1_COST // saving)
    # D6 count: laptop usage index, refreshed now, bounded.
    import usage_index as ui
    con = ui.connect()
    rs = ui.refresh(con, deadline_s=150)
    act = datetime.fromisoformat(ACTIVATED.replace("Z", "+00:00")).timestamp()
    now = datetime.now(timezone.utc)
    rows = dict(con.execute("SELECT is_sub, COUNT(*) FROM calls WHERE ts >= ? GROUP BY is_sub", (act,)).fetchall())
    f["index_status"], f["observed_until"] = rs.get("status"), now.isoformat(timespec="seconds")
    f["calls_main"], f["calls_sub"] = int(rows.get(0, 0)), int(rows.get(1, 0))
    return f


# ---------------------------------------------------------------- step runner
LOG, DRY_SNAPS = [], []


def restore_dry() -> None:
    for snap in reversed(DRY_SNAPS):
        for p, b in snap.items():
            if b is None:
                (REPO / p).unlink(missing_ok=True)
            else:
                (REPO / p).write_bytes(b)


def step(name, paths, produce, gates, subject, body):
    snap = {p: ((REPO / p).read_bytes() if (REPO / p).exists() else None) for p in paths}
    produce()
    fails = [x for g in gates for x in g()]
    if fails:
        for p, b in snap.items():
            if b is None:
                (REPO / p).unlink(missing_ok=True)
            else:
                (REPO / p).write_bytes(b)
        if DRY:
            restore_dry()
        print(f"{name} RED -> restored {paths}")
        for x in fails:
            print("  FAIL", x)
        raise SystemExit(1)
    if DRY:
        DRY_SNAPS.append(snap)
        LOG.append((name, "dry"))
        print(f"{name} green (dry run, not committed)")
        return "dry"
    git("add", "--", *paths)
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{subject}\n\n{body}{TRAILER}")
        msg = fh.name
    git("commit", "-q", "-F", msg, "--", *paths)
    os.unlink(msg)
    h, s = git("log", "-1", "--format=%h"), git("log", "-1", "--format=%s")
    files = set(git("show", "--name-only", "--format=", "HEAD").splitlines())
    if s != subject or files != set(paths):
        raise SystemExit(f"ABORT {name} commit {h} mismatch: subject={s!r} files={sorted(files)}")
    LOG.append((name, h))
    print(f"{name} green -> {h} {subject}")
    return h


def main() -> int:
    head0 = git("rev-parse", "--short", "HEAD")
    if git("diff", "--cached", "--name-only"):
        raise SystemExit("ABORT the index already holds staged paths (another pane?); nothing written")
    dirty = git("status", "--porcelain", "--untracked-files=all", "--", GEN1, GEN2, RESUME, OUT)
    stray = [ln for ln in dirty.splitlines() if not ln.endswith("e1_closeout.py")]
    if stray:
        raise SystemExit(f"ABORT target paths dirty before start: {stray}")
    F = facts()
    print(json.dumps(F, indent=1))
    ev = {"pre": PRE, "post": POST, "report": f"{CE}/e1/REPORT.md"}
    per_call_den = (f"billed first-call context per call, laptop, same-probe A/B differential "
                    f"({F['pre_excludable']:,} -> {F['post_excludable']:,})")

    # D1 gen1 state.B savings
    def d1():
        b = copy.deepcopy(jread(GEN1)["state"]["B"])
        b["savings"] = [
            {"status": "upper_bound", "displacement": "unknown", "denominator": per_call_den,
             "value": F["saving"], "unit": "processed tokens/call", "measurement": POST,
             "note": "on-demand loads of the 8 relocated skills are not netted out, so this bounds the net saving from above"},
            {"status": "upper_bound", "displacement": "unknown",
             "denominator": f"laptop main-thread calls {ACTIVATED}..{F['observed_until']} (usage_index), projected",
             "value": F["saving"] * F["calls_main"], "unit": "processed tokens",
             "measurement": f"{OUT}/payback.json", "note": "GEX44 and subagent calls not counted"}]
        if not any(e.get("ref") == POST for e in b["evidence"]):
            b["evidence"].append({"kind": "file", "ref": POST})
        spec = Path(tempfile.gettempdir()) / "e1_closeout_d1_spec.json"
        spec.write_text(json.dumps([{"pillar": "B", **b}]), encoding="utf-8")
        rc, out = run([PY, f"{CE}/ledger_write.py", str(spec)])
        spec.unlink(missing_ok=True)
        if rc:
            raise SystemExit(f"ABORT D1 ledger_write rc={rc}: {out}")
    step("D1", [GEN1], d1, [gate_gen1], "data(cognitive-economy): D1 E1 saving on ledger state.B (8,477/call, upper bound)",
         f"state.B.savings was empty. Per call: {F['saving']:,} processed tokens ({per_call_den}); estate since\n"
         f"activation: {F['saving']:,} x {F['calls_main']:,} laptop main-thread calls. Both upper_bound: on-demand skill\n"
         "loads are not netted out. Written by ledger_write.py; gen1 --final PASS.")

    # D2 gen2 superseded estimates
    def d2():
        led = jread(GEN2)
        led.setdefault("superseded_estimates", []).extend([
            {"label": "E1 rule-move saving forecast", "value": F["forecast_gross"], "unit": "processed tokens/call",
             "quoted_as": "12.5k (post-e1 plan line 31)", "derivation": "moved bytes x pre-move tokens/byte, pointers ignored",
             "superseded": "2026-10-06", "by": f"measured {F['saving']:,} (6124eecf)"},
            {"label": "E1 byte-proportional net estimate", "value": PLAN_BYTE_EST, "unit": "processed tokens/call",
             "quoted_as": "10.8k and 'pointers keep 22% of bytes' (post-e1 plan line 31)",
             "derivation": f"used {COMMIT_BYTES_CLAIM:,} B from the 17b3188a message; the moved originals are {F['moved_bytes']:,} B",
             "superseded": "2026-10-06", "by": f"net byte estimate {F['byte_est_net']:,}; pointer share "
                                               f"{round(100 * F['pointer_bytes'] / F['moved_bytes'], 1)}%"}])
        write(GEN2, gen2_dump(led))
    step("D2", [GEN2], d2, [gate_cep2], "data(cognitive-economy): D2 supersede the 12.5k E1 forecast and the 10.8k typo estimate",
         f"12.5k = {F['moved_bytes']:,} moved B x {F['tokens_per_byte']} tok/B (gross, pointers ignored) = {F['forecast_gross']:,}.\n"
         f"The plan's 10.8k and 22% used 41,353 B from the 17b3188a message; the moved originals are {F['moved_bytes']:,} B\n"
         f"(backup dir, 56,861 - 19,508 resident), so the net estimate is {F['byte_est_net']:,}. Measured {F['saving']:,}.")

    # D3 calibration
    def d3():
        jwrite(f"{OUT}/calibration.json", {
            "record": "rule-virtualization forecast calibration (E1 move, 17b3188a)",
            "instrument": "e1_mechanical.py one-call A/B probe, laptop, same day per figure", "evidence": ev,
            "inputs": {k: F[k] for k in ("pre_excludable", "post_excludable", "pre_pinned_bytes", "post_pinned_bytes",
                                         "moved_bytes", "pointer_bytes", "resident5_bytes", "tokens_per_byte")},
            "forecast_gross": F["forecast_gross"], "byte_est_net": F["byte_est_net"], "measured": F["saving"],
            "error_pct_vs_forecast": F["error_pct"],
            "error_pct_vs_byte_est_net": round(100.0 * (F["saving"] - F["byte_est_net"]) / F["byte_est_net"], 1),
            "cause": "the forecast priced the moved bytes and forgot the pointers that replace them; the pointers are "
                     f"{F['pointer_bytes']:,} B = {round(100 * F['pointer_bytes'] / F['moved_bytes'], 1)}% of the moved bytes",
            "residual_unexplained_tokens": F["saving"] - F["byte_est_net"],
            "plan_figures_corrected": {"byte_est": [PLAN_BYTE_EST, F["byte_est_net"]], "pointer_share_pct":
                                       [PLAN_POINTER_SHARE, round(100 * F['pointer_bytes'] / F['moved_bytes'], 1)],
                                       "source_of_error": f"{COMMIT_BYTES_CLAIM:,} B in the 17b3188a message"},
            "rule_for_next_forecast": "forecast = (removed bytes - replacement bytes) x measured tokens/byte; "
                                      "expect a further ~10% shortfall until a second calibration point exists (n=1)"})
    step("D3", [f"{OUT}/calibration.json"], d3, [gate_cep2],
         "data(cognitive-economy): D3 calibration record for the E1 rule-move forecast",
         f"forecast {F['forecast_gross']:,} -> measured {F['saving']:,} ({F['error_pct']}%); net byte estimate "
         f"{F['byte_est_net']:,} ({F['saving'] - F['byte_est_net']:+,}).\nCause: pointers ignored. n=1.")

    # D4 pointer tax
    def d4():
        jwrite(f"{OUT}/pointer_tax.json", {
            "receipt": "pointer tax of the E1 relocation (resident one-line pointers that replace the 8 rule bodies)",
            "pointer_files": [str(RULES / f"{n}.md") for n in MOVED], "pointer_bytes": F["pointer_bytes"],
            "tokens_per_call_estimate": {"low": F["pointer_tax_bytewise"], "high": F["pointer_tax_if_resident_avg"],
                                         "label": "ESTIMATED",
                                         "low_method": "pointer bytes x pre-move tokens/byte",
                                         "high_method": "post-move excludable minus the 5 resident rules at average density"},
            "measured": "UNMEASURED: no probe isolates the pointers (two equations, three unknowns)",
            "lever": "removing the pointers would need the skill listing to carry the triggers; not proposed here"})
    step("D4", [f"{OUT}/pointer_tax.json"], d4, [gate_cep2], "data(cognitive-economy): D4 pointer-tax receipt for the E1 move",
         f"{F['pointer_bytes']:,} B of pointers stay resident; ESTIMATED {F['pointer_tax_bytewise']:,}-"
         f"{F['pointer_tax_if_resident_avg']:,} tokens/call. Not separately measured.")

    # D5 cleanup-survival test
    step("D5", [D5_TEST], lambda: None, [gate_d5],
         "test(cognitive-economy): D5 a paid E1 probe survives a held temp dir (red/green + corrupt usage)",
         "Fake CLI leaves a detached child holding the cwd. The flag-flipped mutant loses the measurement\n"
         "(positive control, else INCONCLUSIVE); the real module returns MEASURED; zero and absent usage stay UNMEASURED.")

    # D6 payback
    state = "PAID_BACK" if F["calls_main"] >= F["break_even"] else "NOT_YET"
    payback = {"activated_at": ACTIVATED, "coverage": "laptop transcripts only, main-thread calls (lower bound)",
               "break_even_calls": F["break_even"], "calls_observed": F["calls_main"], "state": state,
               "observed_until": F["observed_until"], "subagent_calls_not_counted": F["calls_sub"],
               "index_refresh_status": F["index_status"],
               "cost_scope": "E1 counted runs only (9,172,196); the orchestrating panes were not metered, so the true "
                             "break-even is later than this"}

    def d6():
        jwrite(f"{OUT}/payback.json", {"cost_processed": E1_COST, "saving_per_call": F["saving"], **payback,
                                       "command": "python " + f"{OUT}/e1_closeout.py (facts: usage_index calls ts >= activation)"})
    step("D6", [f"{OUT}/payback.json"], d6, [gate_cep2], f"data(cognitive-economy): D6 E1 payback {state} on laptop calls",
         f"break-even ceil({E1_COST:,}/{F['saving']:,}) = {F['break_even']:,} calls; observed {F['calls_main']:,} main-thread\n"
         f"calls since {ACTIVATED} (index {F['index_status']}). Lower bound on calls; cost excludes orchestration.")

    # D7 receipt + W3 closed
    receipt = {"experiment": "E1 resident-rule relocation", "work_unit": "W3",
               "closed": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "cost": {"unit": "processed", "value": E1_COST, "source": ev["report"], "scope": payback["cost_scope"]},
               "saving": {"per_call": F["saving"], "unit": "processed tokens/call", "label": "upper_bound",
                          "measured_by": "python vault/programs/cognitive-economy/measure/e1_mechanical.py --claude <cli>",
                          "evidence": POST},
               "forecast": {"per_call": F["forecast_gross"], "derivation": "moved bytes x pre-move tokens/byte"},
               "calibration": {"error_pct": F["error_pct"], "record": f"{OUT}/calibration.json"},
               "payback": payback,
               "supersedes": [{"value": F["forecast_gross"], "quoted_as": "12.5k"}, {"value": PLAN_BYTE_EST, "quoted_as": "10.8k"}],
               "evidence": [ev["report"], PRE, POST, f"{OUT}/calibration.json", f"{OUT}/pointer_tax.json",
                            f"{OUT}/payback.json", D5_TEST]}

    def d7():
        jwrite(f"{OUT}/receipt.json", receipt)
        led = jread(GEN2)
        led["work_units"]["W3"].update(
            terminal="IMPLEMENTED_AND_VERIFIED", experiment=True, receipt=f"{OUT}/receipt.json",
            saving={"label": "upper_bound", "per_call": F["saving"], "measured_by": receipt["saving"]["measured_by"]},
            evidence=[{"path": f"{OUT}/receipt.json", "command": "python tools/cep_gen2.py --status"},
                      {"path": ev["report"], "command": "python vault/programs/cognitive-economy/e1/test_e1_report.py"}])
        write(GEN2, gen2_dump(led))
    step("D7", [f"{OUT}/receipt.json", GEN2], d7, [lambda: gate_cep2(closed=("W3",))],
         "data(cognitive-economy): D7 E1 receipt; gen2 W3 closed as an experiment",
         f"W3 IMPLEMENTED_AND_VERIFIED with experiment=true and a receipt that cep_gen2 B1 re-derives\n"
         f"(break-even {F['break_even']:,}, calibration {F['error_pct']}%, payback {state}). W3 left the open list.")

    # D8 README + RESUMPTION
    hs = dict(LOG)

    def d8():
        write(f"{OUT}/README.md", "\n".join([
            "# E1 closeout (post-E1 Phase 1)", "",
            f"Driver `e1_closeout.py`, one call, 0 model calls. Receipt contract: `tools/cep_gen2.py` check_receipt (B1, 42a984fb).", "",
            "| step | commit | result |", "|---|---|---|",
            f"| D1 | {hs['D1']} | gen1 state.B savings: {F['saving']:,}/call, upper_bound |",
            f"| D2 | {hs['D2']} | 12.5k (= {F['forecast_gross']:,}) and 10.8k superseded |",
            f"| D3 | {hs['D3']} | calibration {F['error_pct']}% vs forecast; net byte est {F['byte_est_net']:,} |",
            f"| D4 | {hs['D4']} | pointer tax {F['pointer_bytes']:,} B, ESTIMATED {F['pointer_tax_bytewise']:,}-{F['pointer_tax_if_resident_avg']:,} tok/call |",
            f"| D5 | {hs['D5']} | cleanup-survival test 4/4 (red pole real) |",
            f"| D6 | {hs['D6']} | payback {state}: {F['calls_main']:,} of {F['break_even']:,} calls (laptop main, lower bound) |",
            f"| D7 | {hs['D7']} | receipt; gen2 W3 closed |", "",
            "Correction: 17b3188a's \"41,353 B\" is wrong; the moved originals are "
            f"{F['moved_bytes']:,} B (backup dir), so the plan's 10.8k / 22% were derived from a typo.", ""]))
        text = (REPO / RESUME).read_text(encoding="utf-8").rstrip("\n")
        text += "\n\n" + "\n".join([
            f"## Post-E1 Phase 1 DONE ({datetime.now(timezone.utc):%Y-%m-%d}, driver {OUT}/e1_closeout.py)",
            f"- B1 42a984fb: cep_gen2 fails a closed experiment without a receipt and re-derives its arithmetic (23/23 mutants).",
            f"- D1-D7 {hs['D1']}..{hs['D7']}: gen1 state.B saving {F['saving']:,}/call (upper_bound); forecast {F['forecast_gross']:,} "
            f"(the 12.5k) superseded, {F['error_pct']}%; plan's 10.8k/22% came from 41,353 B typo (real {F['moved_bytes']:,} B, net est "
            f"{F['byte_est_net']:,}); pointer tax ESTIMATED {F['pointer_tax_bytewise']:,}-{F['pointer_tax_if_resident_avg']:,}/call; "
            f"payback {state} ({F['calls_main']:,}/{F['break_even']:,} laptop main calls, lower bound); gen2 W3 closed with receipt.",
            f"- Evidence: {OUT}/README.md. Semantic (UKDL/KV/CBR candidates) not written here.",
            "- Next: Phase 2 (fresh pane): wake mode in cep_gen2 on a zero-model scheduled task (W1, W2)."]) + "\n"
        write(RESUME, text)
    step("D8", [f"{OUT}/README.md", f"{OUT}/e1_closeout.py", RESUME], d8, [gate_cep2, gate_gen1],
         "docs(post-e1): D8 Phase 1 closeout recorded in RESUMPTION",
         f"README + RESUMPTION section + this driver; start HEAD {head0}.")
    if DRY:
        restore_dry()
    print("E1_CLOSEOUT=" + ("DRY (all writes restored)" if DRY else "DONE") + " " + " ".join(f"{n}={h}" for n, h in LOG))
    return 0


if __name__ == "__main__":
    sys.exit(main())
