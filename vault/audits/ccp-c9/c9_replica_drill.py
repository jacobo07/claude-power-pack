"""c9 replica drill: tools/ + modules/ copied with repo layout, mutant written in the copy,
the copy's test run, live SHA asserted. Control first: each test must be all-PASS unmutated
in the same replica (otherwise a KILLED could be a replica artefact)."""
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules")

M = [
 ("1 listing order picks identity", "tools/usage_index.py", "tools/test_usage_index_identity.py",
  "V-UXID-NO-ALIAS-PATH",
  "        canon = real[0] if real else min(subs, key=lambda s: str(s).lower())",
  "        canon = subs[0]"),
 ("2 blocked spawn charged as executed", "tools/fanout_ledger.py", "tools/test_spawn_outcomes.py",
  "V-SPOUT-SUMMARY", '        return "HOOK_BLOCKED"', '        return "RETURNED"'),
 ("3 protected deferred", "modules/cognitive_os/scheduler.py", "tools/test_estate_shadow.py",
  "V-SHADOW-PROTECTED",
  "    v = SpawnVerdict(SPAWN_ALLOW, priority)\n    if priority in PROTECTED:",
  "    v = SpawnVerdict(SPAWN_ALLOW, priority)\n    if False:"),
 ("4 UNKNOWN treated as BACKGROUND", "modules/cognitive_os/scheduler.py", "tools/test_spawn_policy_v2.py",
  "V-SPV2-PRIORITY-UNKNOWN",
  '    return PRIO_UNKNOWN if p == PRIO_BACKGROUND and root_class == "UNKNOWN" else p',
  "    return p"),
 ("5 bands tuned on judged window", "tools/estate_shadow.py", "tools/test_estate_shadow.py",
  "V-SHADOW-BANDS-BEFORE-WINDOW",
  "    if not b1 <= start:     # here, not only in the CLI",
  "    if False:     # here, not only in the CLI"),
 ("6 shape sums diverge", "tools/fanout_ledger.py", "tools/test_execution_shape.py",
  "V-SHAPE-SUMS",
  '    calls = sum(s["area"] for s in roots) + len(unrooted)',
  '    calls = sum(s["area"] for s in roots)'),
 ("7 UNSETTLED reported as WASTE (producer)", "tools/root_progress.py", "tools/test_root_progress.py",
  "V-PROG-UNSETTLED", '"ADVANCED_LATER" if later else "UNSETTLED")', '"ADVANCED_LATER" if later else "WASTE")'),
 ("8 receipt without deopt", "modules/cognitive_os/scheduler.py", "tools/test_spawn_policy_v2.py",
  "V-SPV2-DEOPT", '{"kind": "UNMEASURED"}, "deopt": deopt}', '{"kind": "UNMEASURED"}, "deopt": ""}'),
 ("9 optimizer writes ledger (CREATE escapes the verb regex)", "tools/estate_shadow.py",
  "tools/test_spawn_policy_v2.py", "V-SPV2-LEDGER-UNTOUCHED",
  "    eq = Equivalents(con)\n    spend = RootSpend(con, start, end)",
  "    eq = Equivalents(con)\n    con.execute('CREATE TABLE IF NOT EXISTS shadow_cache(x)'); con.commit()\n"
  "    spend = RootSpend(con, start, end)"),
 ("9b same mutant, static gate widened", "tools/estate_shadow.py",
  "tools/test_spawn_policy_v2.py", "V-SPV2-NO-WRITE-SQL",
  "    eq = Equivalents(con)\n    spend = RootSpend(con, start, end)",
  "    eq = Equivalents(con)\n    con.execute('CREATE TABLE IF NOT EXISTS shadow_cache(x)'); con.commit()\n"
  "    spend = RootSpend(con, start, end)"),
 ("10 UNSETTLED counted as WASTE (journey consumer)", "tools/root_progress.py", "tools/test_goal_journey.py",
  "V-JRNY-SHAPE-PROGRESS",
  '"progress": {k: prog.get(k) for k in',
  '"progress": {k: ("WASTE" if prog.get(k) == "UNSETTLED" else prog.get(k)) for k in'),
]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def run(test_rel, mutate=None):
    root = Path(tempfile.mkdtemp(prefix="c9rep-"))
    try:
        for d in ("tools", "modules", "vault/pricing", "vault/config"):
            shutil.copytree(REPO / d, root / d, ignore=SKIP)
        if mutate:
            f_rel, old, new = mutate
            p = root / f_rel
            t = p.read_text(encoding="utf-8")
            if t.count(old) != 1:
                return "HARNESS", f"anchor {t.count(old)}x"
            p.write_text(t.replace(old, new), encoding="utf-8")
        r = subprocess.run([sys.executable, str(root / test_rel)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900,
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
                           cwd=str(root))
        return "RAN", r.stdout + r.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    out = {"controls": {}, "mutants": []}
    for test in sorted({m[2] for m in M}):
        _, o = run(test)
        lines = o.splitlines()
        summ = [l for l in lines if "_PASS=" in l]
        fails = [l.strip() for l in lines if l.strip().startswith("FAIL")]
        out["controls"][test] = {"summary": summ, "fails": fails,
                                 "clean": bool(summ) and not fails}
        print("CONTROL", test, summ, "fails:", fails, flush=True)
    for name, f, test, gate, old, new in M:
        live = REPO / f
        before = sha(live)
        st, o = run(test, (f, old, new))
        if sha(live) != before:
            v = "HARNESS(live changed)"
        elif st == "HARNESS":
            v = "HARNESS(" + o + ")"
        elif not any("_PASS=" in l for l in o.splitlines()):
            v = "UNJUDGED"
        elif f"FAIL {gate}" in o:
            v = "KILLED"
        else:
            v = "SURVIVED"
        fails = [l.strip().split(":")[0] for l in o.splitlines() if l.strip().startswith("FAIL")]
        summ = [l for l in o.splitlines() if "_PASS=" in l]
        rec = {"mutant": name, "file": f, "test": test, "gate": gate, "verdict": v,
               "all_failing_gates": fails, "summary": summ}
        if v == "UNJUDGED":
            rec["tail"] = o.splitlines()[-8:]
        out["mutants"].append(rec)
        print("MUTANT", v, "|", name, "| gate", gate, "| failing:", fails, flush=True)
    Path(__file__).with_name("c9_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    ctrl_ok = all(c["clean"] for c in out["controls"].values())
    killed = sum(m["verdict"] == "KILLED" for m in out["mutants"])
    print(f"C9_DRILL controls_clean={ctrl_ok} killed={killed}/{len(M)}")


if __name__ == "__main__":
    main()
