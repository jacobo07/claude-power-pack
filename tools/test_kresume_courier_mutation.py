"""V-KRC mutation drill (spec vault/specs/kresume-courier.md): proves each load-bearing gate of
tools/test_kresume_courier.py can go red. Run: python tools/test_kresume_courier_mutation.py
Exit 0 only when every mutant is killed, the live files hash identically, and no copy is left.

Mutation drill for test_kresume_courier.py. Each mutant is a COPY beside the original (so its
relative paths resolve), under a name nothing live loads; the suite is pointed at it by env.
Each mutation must apply exactly once (proved), the live files must hash identically before and
after, and every copy is removed in `finally`."""
import hashlib, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SUITE = ROOT / "tools" / "test_kresume_courier.py"
FILES = {
    "courier": ROOT / "tools" / "kresume_courier.py",
    "watchdog": ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py",
    "autotype": ROOT / "hooks" / "rollover_autotype.js",
}
ENV_KEY = {"courier": "KRC_TEST_COURIER", "watchdog": "KRC_TEST_WATCHDOG", "autotype": "KRC_TEST_AUTOTYPE"}

MUTANTS = [
    ("arms-predecessor", "courier",
     'successor = rec["sessionId"]', 'successor = predecessor', "V-KRC-ARMS-NEW-SID"),
    ("pid-reuse-accepted", "courier",
     'elif str(rec.get("procStart") or rec.get("startedAt") or "") != identity:',
     'elif False:', "V-KRC-PID-REUSE-REFUSED"),
    ("no-retry", "courier", "ARM_ATTEMPTS = 3", "ARM_ATTEMPTS = 1", "V-KRC-ARM-FAILED-RETRIED-AND-NAMED"),
    ("deadline-never-named", "courier",
     '    _ledger(predecessor, "CLEAR_NEVER_LANDED", registry_file=path.name, deadline_s=deadline_s)\n',
     '', "V-KRC-CLEAR-NEVER-LANDED"),
    ("courier-never-spawned", "watchdog",
     "        _spawn_kresume_courier(session_id, cwd, transcript)\n", "", "V-KRC-WATCHDOG-SPAWNS-COURIER"),
    ("not-resolved-at-dispatch", "watchdog",
     "    if found:\n        argv += [\"--registry-file\"",
     "    if False:\n        argv += [\"--registry-file\"", "V-KRC-WATCHDOG-RESOLVES-AT-DISPATCH"),
    ("ambiguity-not-refused", "courier",
     "    if len(matches) > 1:\n", "    if False:\n", "V-KRC-AMBIGUOUS-REFUSED"),
    # The watchdog loads the REAL courier via _load_tool, so the ancestry filter is dropped at
    # its call site, which is what KRC_TEST_WATCHDOG redirects.
    ("ancestry-filter-dropped", "watchdog",
     "kc.find_process(session_id, kc.ancestor_pids(os.getpid()))",
     "kc.find_process(session_id)", "V-KRC-WATCHDOG-PICKS-OWN-PROCESS"),
    ("starved-path-silent", "autotype",
     "    hub.note('rollover_autotype: SessionStart payload had no '",
     "    void ('rollover_autotype: SessionStart payload had no '", "V-KRC-HOOK-STARVED-IS-LOGGED"),
    ("hook-path-disabled", "autotype",
     "  arm(sid, cwd, (typeof payload.transcript_path", "  void (sid, cwd, (typeof payload.transcript_path",
     "V-KRC-HOOK-STILL-ARMS"),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


before = {k: sha(p) for k, p in FILES.items()}
killed = survived = harness = 0
made = []
try:
    for name, which, old, new, must in MUTANTS:
        src = FILES[which]
        text = src.read_text(encoding="utf-8")
        n = text.count(old)
        if n != 1:
            print(f"HARNESS {name}: anchor matched {n} times (must be 1) -- mutation not applied")
            harness += 1
            continue
        mut = src.with_name(f"_krcmut_{name.replace('-', '_')}{src.suffix}")
        mut.write_text(text.replace(old, new), encoding="utf-8", newline="")
        made.append(mut)
        env = dict(os.environ, **{ENV_KEY[which]: str(mut)}, PYTHONIOENCODING="utf-8")
        try:
            r = subprocess.run([PY, str(SUITE)], env=env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=600)
        finally:
            # Per mutant, not only at the end: a host-pressure kill skips the outer finally,
            # and on 2026-10-01 that stranded 7 copies beside the live files. Now at most one.
            mut.unlink(missing_ok=True)
        failed = [ln.split()[1].rstrip(":") for ln in r.stdout.splitlines() if ln.strip().startswith("FAIL")]
        if must in failed:
            killed += 1
            print(f"KILLED   {name}: {must} red (also red: {[f for f in failed if f != must]})")
        else:
            survived += 1
            print(f"SURVIVED {name}: expected {must} red; red={failed} tail={r.stdout[-200:]!r}")
finally:
    for m in made:
        m.unlink(missing_ok=True)
after = {k: sha(p) for k, p in FILES.items()}
left = [m for m in made if m.exists()]
print(f"\nlive files unchanged: {before == after}   copies left: {left}")
print(f"KRC_DRILL killed={killed} survived={survived} harness={harness} of {len(MUTANTS)}")
sys.exit(0 if killed == len(MUTANTS) and before == after and not left else 1)
