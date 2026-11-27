"""inherit_check.py - phase-local instrument for PERF-06 (Phase 6, plan 06-01).

Question it answers: which of the Phase 2-5 proofs does a future run inherit through a
STANDING gate, and which only by convention? It measures; it does not assert.

Subcommands (run with `python3 -I`, from anywhere inside the repo checkout):
  selftest                       drives every verdict shape and a mutant control against the checker itself
  manifest [--only ID,..] [--include-slow]
                                 runs each standing gate with its recorded expected marker
  matrix [--verify-record FILE]  plants five mutants in a scratch copy and runs the standing gate
                                 (tools/test_bench_gate.py) and the owning suite on each

Closed verdict set for a manifest row: PASS FAIL TIMED_OUT NOT_RUN UNPARSED BASELINE_MATCH
SKIPPED_BY_POLICY. A row is PASS only with exit 0, a marker whose numerator equals its
denominator and a denominator equal to the recorded expected count. A skipped, timed-out,
unparsed or not-run row is never a pass and never lets the footer say everything passed.

Stdlib only. Registered nowhere. Never imported from tools/ or modules/ (D6-01). Every path it
prints is repo-relative; absolute home, repo and scratch paths are scrubbed from printed text.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

VERDICTS = ("PASS", "FAIL", "TIMED_OUT", "NOT_RUN", "UNPARSED", "BASELINE_MATCH", "SKIPPED_BY_POLICY")
GREEN = ("PASS", "BASELINE_MATCH")
NOT_JUDGED = ("UNPARSED", "NOT_RUN", "TIMED_OUT")
JUDGED = ("PASS", "FAIL", "BASELINE_MATCH")
HERE = os.path.dirname(os.path.abspath(__file__))
PH_REL = ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back"
HOOKS_BASE = "4fa606d7"


def repo_root():
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit("inherit_check: not inside a git checkout")
    return r.stdout.strip()


ROOT = None


def scrub(text, extra=()):
    """Remove absolute host paths from anything printed (records are read on another host)."""
    global ROOT
    if ROOT is None:
        ROOT = repo_root()
    for path, repl in list(extra) + [(ROOT, "."), (os.path.expanduser("~"), "~")]:
        if path and path not in ("/", ""):
            text = text.replace(path, repl)
    return text


def spawn(argv, timeout, cwd=None, env=None, merge=True):
    """Run argv (list, no shell) in its own session; on timeout kill the whole process group.
    Returns (rc, out, err, timed_out, not_run). rc is None on timeout / not run."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    try:
        p = subprocess.Popen(argv, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT if merge else subprocess.PIPE,
                             cwd=cwd, env=full_env, start_new_session=True,
                             text=True, encoding="utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return None, "spawn failed: %s: %s\n" % (type(exc).__name__, exc), "", False, True
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out or "", err or "", False, False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            out, err = p.communicate(timeout=10)
        except Exception:  # noqa: BLE001
            out, err = "", ""
        return None, out or "", err or "", True, False


class Row:
    def __init__(self, rid, argv, marker=None, expected=None, timeout=120, env=None,
                 mode="count", expected_exit=0, baseline=None, fn=None, skip_reason=None, note=""):
        self.id, self.argv, self.marker, self.expected = rid, argv, marker, expected
        self.timeout, self.env, self.mode = timeout, env, mode
        self.expected_exit, self.baseline, self.fn = expected_exit, baseline, fn
        self.skip_reason, self.note = skip_reason, note


def parse_marker(pattern, output):
    """Last match of pattern in output -> (numerator, denominator) or None.
    One capture group means n/n (a 'N passed, 0 failed' style line); two groups mean n/d."""
    last = None
    for m in re.finditer(pattern, output, flags=re.M):
        last = m
    if last is None:
        return None
    g = last.groups()
    try:
        if len(g) >= 2:
            return int(g[0]), int(g[1])
        return int(g[0]), int(g[0])
    except (TypeError, ValueError):
        return None


def judge(rc, timed_out, not_run, output, row, compare_counts=True):
    """Pure verdict function. compare_counts=False exists only for the selftest mutant control."""
    if not_run:
        return "NOT_RUN", "executable missing or unspawnable"
    if timed_out:
        return "TIMED_OUT", "killed after %ss" % row.timeout
    m = parse_marker(row.marker, output) if row.marker else None
    if m is None:
        return "UNPARSED", "exit=%s, marker %r not found" % (rc, row.marker)
    num, den = m
    shown = "%d/%d" % (num, den)
    if row.mode == "baseline":
        if rc == row.expected_exit and (num, den) == tuple(row.baseline):
            return "BASELINE_MATCH", "observed %s equals recorded baseline %d/%d (pre-existing debt, never PASS)" % (
                shown, row.baseline[0], row.baseline[1])
        return "FAIL", "observed %s exit=%s differs from recorded baseline %d/%d exit=%s" % (
            shown, rc, row.baseline[0], row.baseline[1], row.expected_exit)
    if rc != 0:
        return "FAIL", "exit=%s with marker %s" % (rc, shown)
    if num != den:
        return "FAIL", "marker %s: numerator differs from denominator" % shown
    if compare_counts and den != row.expected:
        return "FAIL", "marker %s: count differs from expected %s" % (shown, row.expected)
    return "PASS", "marker %s (expected %s)" % (shown, row.expected)


def run_row(row, cwd, compare_counts=True):
    """Run one row, return (verdict, detail, seconds, tail_of_output_on_failure)."""
    t0 = time.time()
    if row.skip_reason is not None:
        return "SKIPPED_BY_POLICY", row.skip_reason, 0.0, ""
    if row.fn is not None:
        verdict, detail = row.fn(row, cwd)
        assert verdict in VERDICTS, verdict
        return verdict, detail, time.time() - t0, ""
    env = dict(row.env or {})
    tmp_home = None
    for k, v in list(env.items()):
        if v == "{TMPHOME}":
            tmp_home = tempfile.mkdtemp(prefix="p6-home-")
            env[k] = tmp_home
    try:
        rc, out, _err, timed_out, not_run = spawn(row.argv, row.timeout, cwd=cwd, env=env)
    finally:
        if tmp_home and os.path.basename(tmp_home).startswith("p6-home-") and \
                os.path.dirname(tmp_home) == tempfile.gettempdir():
            shutil.rmtree(tmp_home, ignore_errors=True)
    verdict, detail = judge(rc, timed_out, not_run, out, row, compare_counts)
    tail = ""
    if verdict in ("FAIL", "UNPARSED", "TIMED_OUT"):
        lines = [ln for ln in out.splitlines() if ln.strip()]
        tail = "\n".join("      | " + scrub(ln)[:240] for ln in lines[-4:])
    return verdict, detail, time.time() - t0, tail


def sha256_file(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def footer_for(results):
    """results: list of verdict strings. Returns (lines, exit_code)."""
    total = len(results)
    skipped = sum(1 for v in results if v == "SKIPPED_BY_POLICY")
    ran = total - skipped
    passed = sum(1 for v in results if v in GREEN)
    not_judged = sum(1 for v in results if v in NOT_JUDGED)
    judged = sum(1 for v in results if v in JUDGED)
    lines = ["INHERIT_JUDGED=%d/%d judged (total rows %d, skipped %d, not judged %d)" % (
        judged, total, total, skipped, not_judged),
        "INHERIT_PASS=%d/%d" % (passed, ran),
        "SKIPPED=%d" % skipped,
        "NOT_JUDGED=%d" % not_judged]
    return lines, (0 if passed == ran else 1)


def run_manifest(rows, cwd, out=print, hashes=None):
    results = []
    for row in rows:
        verdict, detail, secs, tail = run_row(row, cwd)
        results.append(verdict)
        out("ROW %-22s %-17s %5.1fs  %s" % (row.id, verdict, secs, scrub(detail)))
        if tail:
            out(tail)
        if row.note:
            out("      note: " + row.note)
    lines, code = footer_for(results)
    if hashes:
        after = {p: sha256_file(os.path.join(cwd, p)) for p in hashes[0]}
        for p in hashes[0]:
            same = "SAME" if after[p] == hashes[0][p] else "CHANGED"
            out("HASH_AFTER %s %s %s" % (p, after[p], same))
            if same == "CHANGED":
                code = 1
    for ln in lines:
        out(ln)
    return code


# ---------------------------------------------------------------- special rows

def fn_hooks_unchanged(row, cwd):
    rc, out, _e, to, nr = spawn(["git", "diff", "--stat", HOOKS_BASE, "--", "hooks/"], 60, cwd=cwd)
    if nr or to or rc != 0:
        return "NOT_RUN", "git diff %s did not complete (rc=%s)" % (HOOKS_BASE, rc)
    if out.strip():
        return "FAIL", "hooks/ differs from %s: %s" % (HOOKS_BASE, out.strip().splitlines()[-1][:160])
    return "PASS", "hooks/ empty diff against %s" % HOOKS_BASE


def fn_tree_clean(row, cwd):
    rc, out, _e, to, nr = spawn(["git", "status", "--porcelain", "--", "tools", "modules", "hooks", "vault/config"],
                                60, cwd=cwd)
    if nr or to or rc != 0:
        return "NOT_RUN", "git status did not complete (rc=%s)" % rc
    if out.strip():
        return "FAIL", "tracked/untracked change outside PH: %s" % " | ".join(out.strip().splitlines()[:5])
    return "PASS", "tools modules hooks vault/config: empty porcelain"


def reach_offender_units(text):
    """Offender unit names from a JSON document (reachability --json)."""
    doc = json.loads(text)
    return sorted(o["unit"] for o in doc.get("offenders", []))


def reach_record_units(path):
    """Parse a record_run record: JSON from the first opening brace to the line before '# exit='."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("{"))
    end = next(i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("# exit="))
    return reach_offender_units("\n".join(lines[start:end]))


def fn_reachability(row, cwd):
    rc, out, _e, to, nr = spawn(["python3", "-I", "modules/liveness/reachability.py", "--json"], 300,
                                cwd=cwd, merge=False)
    if nr or to:
        return ("NOT_RUN" if nr else "TIMED_OUT"), "reachability did not complete"
    try:
        now = reach_offender_units(out)
        rec = reach_record_units(os.path.join(
            cwd, ".planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-reach-pre.txt"))
    except (ValueError, StopIteration, OSError, KeyError) as exc:
        return "UNPARSED", "could not read offender names: %s: %s" % (type(exc).__name__, exc)
    new, gone = sorted(set(now) - set(rec)), sorted(set(rec) - set(now))
    if not new and not gone:
        return "BASELINE_MATCH", "%d offenders (rc=%s), names equal 05-01-reach-pre.txt by unit; pre-existing debt" % (
            len(now), rc)
    return "FAIL", "offenders differ by name: new=%s gone=%s" % (new[:6], gone[:6])


def build_rows(include_slow=False):
    py = "python3"
    rows = [
        Row("a5_u6", [py, "tools/test_a5_u6.py"], r"^A5_U6_PASS=(\d+)/(\d+)", 13, 120),
        Row("arm_preflight", [py, "tools/test_arm_preflight.py"], r"^PRE_PASS=(\d+)/(\d+)", 23, 120),
        Row("bench_integrity", [py, "tools/test_bench_integrity.py"], r"^BENCHINT_PASS=(\d+)/(\d+)", 53, 180),
        Row("bench_gate", [py, "tools/test_bench_gate.py"], r"^BENCH_GATE_PASS=(\d+)/(\d+)", 24, 180),
        Row("resource_pressure", [py, "tools/test_resource_pressure.py"], r"^PRESSURE_PASS=(\d+)/(\d+)", 17, 120),
        Row("gsd_mission_resources", [py, "tools/test_gsd_mission_resources.py"], r"^RES_PASS=(\d+)/(\d+)", 17, 120),
        Row("gsd_mission_baseline", [py, "tools/test_gsd_mission_baseline.py"], r"^(\d+) passed, 0 failed", 21, 120),
        Row("metrology", [py, "tools/test_construction_metrology.py"], r"^METRO_PASS=(\d+)/(\d+)", 38, 180),
        Row("critical_path", [py, "-I", "tools/test_hook_critical_path.py"], r"^CRITPATH_PASS=(\d+)/(\d+)", 134, 180),
        Row("hook_boundary", [py, "tools/test_hook_boundary.py"], r"^HOOK_PASS=(\d+)/(\d+)", 7, 180,
            env={"HOME": "{TMPHOME}"},
            note="HOME is a fresh temp dir; the duplicate-invocation sub-check stays UNEVALUATED (LAPTOP-ONLY LP-12)"),
        Row("git_invocation", [py, "tools/test_git_invocation.py"], r"^GIT_INVOCATION_PASS=(\d+)/(\d+)", None, 180,
            mode="baseline", expected_exit=1, baseline=(6, 7),
            note="pre-existing debt 6/7; BASELINE_MATCH is not PASS"),
        Row("hooks_unchanged", None, fn=fn_hooks_unchanged),
        Row("reachability", None, fn=fn_reachability, note="pre-existing 56 offenders; compared by unit name"),
        Row("phase6_tree_clean", None, fn=fn_tree_clean),
    ]
    if include_slow:
        rows.append(Row("s9_redteam", [py, "tools/test_s9_redteam.py"], r"^(\d+)/(\d+)", None, 1800))
    else:
        rows.append(Row("s9_redteam", None, skip_reason=(
            "814 s; last recorded 111/114 in 04-02-s9-redteam.after.txt; UNJUDGED, no clean control run exists "
            "(Phase 4 caveat)")))
    return rows


HASHED = ("vault/benchmarks/ledger.json", "vault/config/resource-floors.json")


def cmd_manifest(args):
    cwd = repo_root()
    rows = build_rows(args.include_slow)
    if args.only:
        wanted = set(args.only.split(","))
        unknown = wanted - {r.id for r in rows}
        if unknown:
            print("manifest: unknown row id(s): %s" % ", ".join(sorted(unknown)))
            return 2
        rows = [r for r in rows if r.id in wanted]
    before = {p: sha256_file(os.path.join(cwd, p)) for p in HASHED}
    for p in HASHED:
        print("HASH_BEFORE %s %s" % (p, before[p]))
    return run_manifest(rows, cwd, hashes=(before,))


# ---------------------------------------------------------------- selftest

def selftest():
    gates = []

    def gate(name, ok, detail):
        gates.append(ok)
        print("%s %s: %s" % ("OK  " if ok else "FAIL", name, detail))

    py = sys.executable
    cwd = repo_root()

    def mk(code, expected=3, timeout=20, marker=r"X_PASS=(\d+)/(\d+)", **kw):
        return Row("t", [py, "-c", code], marker, expected, timeout, **kw)

    v, d, _s, _t = run_row(mk("print('X_PASS=3/3')"), cwd)
    gate("V-INH-PASS", v == "PASS", "good row -> %s (%s)" % (v, d))
    v, d, _s, _t = run_row(mk("print('X_PASS=3/3'); raise SystemExit(1)"), cwd)
    gate("V-INH-EXIT", v == "FAIL", "marker 3/3 with exit 1 -> %s" % v)
    v, d, _s, _t = run_row(mk("pass"), cwd)
    gate("V-INH-SILENT", v == "UNPARSED", "exit 0 and no marker -> %s" % v)
    pidfile = os.path.join(tempfile.mkdtemp(prefix="p6-self-"), "gpid")
    code = ("import subprocess,sys,time;"
            "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "open(%r,'w').write(str(p.pid));time.sleep(60)" % pidfile)
    t0 = time.time()
    v, d, _s, _t = run_row(mk(code, timeout=2), cwd)
    gone = False
    try:
        gpid = int(open(pidfile).read())
        for _ in range(40):
            try:
                os.kill(gpid, 0)
                try:
                    with open("/proc/%d/stat" % gpid) as fh:
                        if fh.read().rsplit(")", 1)[1].split()[0] == "Z":
                            gone = True
                            break
                except OSError:
                    gone = True
                    break
            except ProcessLookupError:
                gone = True
                break
            time.sleep(0.1)
    except (OSError, ValueError):
        gone = False
    shutil.rmtree(os.path.dirname(pidfile), ignore_errors=True)
    gate("V-INH-TIMEOUT", v == "TIMED_OUT" and gone and (time.time() - t0) < 15,
         "over-timeout row -> %s, grandchild process gone=%s" % (v, gone))
    lo1, _d1, _s1, _t1 = run_row(mk("print('X_PASS=2/3')"), cwd)
    lo2, _d2, _s2, _t2 = run_row(mk("print('X_PASS=3/4')"), cwd)
    lo3, _d3, _s3, _t3 = run_row(mk("print('X_PASS=4/4')"), cwd)
    gate("V-INH-LOWER", (lo1, lo2, lo3) == ("FAIL", "FAIL", "FAIL"),
         "2/3, 3/4 and 4/4 against expected 3/3 -> %s %s %s" % (lo1, lo2, lo3))
    v, d, _s, _t = run_row(Row("t", ["definitely-not-a-real-executable-p6"], "x", 1, 5), cwd)
    gate("V-INH-NOT-RUN", v == "NOT_RUN", "missing executable -> %s" % v)
    base = Row("b", [py, "-c", "print('G_PASS=6/7'); raise SystemExit(1)"], r"G_PASS=(\d+)/(\d+)", None, 20,
               mode="baseline", expected_exit=1, baseline=(6, 7))
    base_low = Row("b", [py, "-c", "print('G_PASS=5/7'); raise SystemExit(1)"], r"G_PASS=(\d+)/(\d+)", None, 20,
                   mode="baseline", expected_exit=1, baseline=(6, 7))
    vb, _d, _s, _t = run_row(base, cwd)
    vl, _d, _s, _t = run_row(base_low, cwd)
    gate("V-INH-BASELINE", vb == "BASELINE_MATCH" and vl == "FAIL",
         "recorded 6/7 -> %s, lower 5/7 -> %s (baseline is never PASS)" % (vb, vl))
    # footer: one PASS + one SKIPPED -> exit 0 and '1/2 judged'; one PASS + one UNPARSED -> exit 1
    lines_a = []
    code_a = run_manifest([mk("print('X_PASS=3/3')"),
                           Row("s", None, skip_reason="policy")], cwd, out=lines_a.append)
    lines_b = []
    code_b = run_manifest([mk("print('X_PASS=3/3')"), mk("pass")], cwd, out=lines_b.append)
    ok_a = code_a == 0 and any("1/2 judged" in ln for ln in lines_a) and "SKIPPED=1" in lines_a
    ok_b = code_b == 1 and "NOT_JUDGED=1" in lines_b and not any(ln.startswith("INHERIT_PASS=2/") for ln in lines_b)
    gate("V-INH-FOOTER", ok_a and ok_b,
         "PASS+SKIPPED -> exit %s '1/2 judged'; PASS+UNPARSED -> exit %s, NOT_JUDGED=1" % (code_a, code_b))
    # mutant control: with the count comparison disabled in memory, the lower-count shape must stop failing,
    # which proves V-INH-LOWER can fail (a test that cannot go red is not a test).
    v, _d, _s, _t = run_row(mk("print('X_PASS=2/2')"), cwd, compare_counts=False)
    v_real, _d, _s, _t = run_row(mk("print('X_PASS=2/2')"), cwd)
    gate("V-INH-MUTANT-CONTROL", v == "PASS" and v_real == "FAIL",
         "2/2 against expected 3: real judge -> %s, judge with count comparison disabled -> %s" % (v_real, v))
    n, total = sum(gates), len(gates)
    print("INHERIT_SELFTEST=%d/%d" % (n, total))
    return 0 if n == total else 1


# ---------------------------------------------------------------- matrix

SCRATCH_PREFIX = "p6-inherit-"
# Paths copied into the scratch tree. The first five are the plan's set; hooks, tests, vault/specs and the Phase 5
# inventory baseline were ADDED after the first control run failed without them (F2): the integrity suite needs
# tests/ and hooks/, the metrology suite needs its contract document, the critical-path suite needs the dispatcher
# and the recorded baseline. They are read-only inputs of the scratch copy; no mutant is ever written to them.
ARCHIVE_PATHS = ["tools", "modules", "vault/config", "vault/benchmarks", "vault/liveness",
                 "hooks", "tests", "vault/specs",
                 ".planning/workstreams/perf-construction/phases/05-critical-path-audit/records/"
                 "05-01-inventory-baseline.json"]
ADDED_PATHS = ARCHIVE_PATHS[5:]
STANDING = ["python3", "tools/test_bench_gate.py"]

# (id, phase, owner file, target text, replacement text, owning suite argv, owning suite timeout)
MUTANTS = [
    ("MX1", "4 pressure judge", "tools/bench_all.py",
     "elif pressure is not None and pressure[0] != PRESSURE_GREEN:", "elif False:",
     ["python3", "tools/test_bench_integrity.py"], 180),
    ("MX2", "4 pressure reader", "tools/resource_admission.py",
     "count > ceiling", "count >= ceiling",
     ["python3", "tools/test_resource_pressure.py"], 180),
    # MX3: the exit-code rule of the absolute-target judgement (Phase 2): a missed target must exit non-zero.
    ("MX3", "2 benchmark integrity", "tools/bench_all.py",
     '               or v.get("met_target") is False\n', "               or False\n",
     ["python3", "tools/test_bench_integrity.py"], 180),
    # MX4: censoring set (Phase 3): FAILED turns must stay censored samples, never silently measured or dropped.
    ("MX4", "3 metrology censoring", "modules/capability_runtime/construction_metrology.py",
     'CENSORED_STATES = frozenset({"TIMED_OUT", "UNOBSERVED", "FAILED"})',
     'CENSORED_STATES = frozenset({"TIMED_OUT", "UNOBSERVED"})',
     ["python3", "tools/test_construction_metrology.py"], 180),
    # MX5: the weakened-flag detection of the hook critical-path guard (Phase 5).
    ("MX5", "5 critical-path guard", "tools/hook_critical_path_audit.py",
     "if b.get(flag) and not c.get(flag):", "if b.get(flag) and c.get(flag):",
     ["python3", "-I", "tools/test_hook_critical_path.py"], 180),
]

FAIL_RE = re.compile(r"\bFAIL\b")


def first_fail(out):
    lines = out.splitlines()
    for ln in lines:  # a line that is itself a FAIL result ("FAIL x", "[FAIL] x")
        if re.match(r"^\s*\[?FAIL\b", ln):
            return scrub(ln.strip())[:220]
    for ln in lines:  # otherwise any non-PASS line that carries the word
        if FAIL_RE.search(ln) and not re.match(r"^\s*(\[)?(PASS|OK)\b", ln):
            return scrub(ln.strip())[:220]
    return "-"


def make_scratch():
    scratch = tempfile.mkdtemp(prefix=SCRATCH_PREFIX)
    prefix = os.path.join(tempfile.gettempdir(), SCRATCH_PREFIX)
    assert scratch.startswith(prefix), scratch
    root = repo_root()
    ar = subprocess.Popen(["git", "archive", "HEAD", "--"] + ARCHIVE_PATHS, cwd=root, stdout=subprocess.PIPE)
    tar = subprocess.run(["tar", "-x", "-C", scratch], stdin=ar.stdout, capture_output=True)
    ar.stdout.close()
    ar.wait()
    if ar.returncode != 0 or tar.returncode != 0:
        raise SystemExit("matrix: git archive | tar failed (%s, %s)" % (ar.returncode, tar.returncode))
    return scratch


def drop_scratch(scratch):
    prefix = os.path.join(tempfile.gettempdir(), SCRATCH_PREFIX)
    if scratch.startswith(prefix):
        shutil.rmtree(scratch, ignore_errors=True)
        return True
    return False


def run_cmd(argv, timeout, cwd):
    env = {"PYTHONDONTWRITEBYTECODE": "1"}
    rc, out, _e, to, nr = spawn(argv, timeout, cwd=cwd, env=env)
    return rc, out, to, nr


def classify(standing, own):
    """standing/own: (rc, first_fail_line, timed_out_or_not_run). Returns the closed verdict."""
    s_rc, s_ff, s_bad = standing
    o_rc, o_ff, o_bad = own
    if s_bad or o_bad:
        return "NOT_DISCRIMINATING"
    if s_rc not in (0, None) and s_ff != "-":
        return "ENFORCED"
    if s_rc not in (0, None):
        return "NOT_DISCRIMINATING"
    if o_rc not in (0, None) and o_ff != "-":
        return "OWN_SUITE_ONLY"
    if o_rc not in (0, None):
        return "NOT_DISCRIMINATING"
    return "SURVIVED_ALL"


def cmd_matrix(args):
    if args.verify_record:
        return verify_record(args.verify_record)
    scratch = make_scratch()
    counts = {k: 0 for k in ("ENFORCED", "OWN_SUITE_ONLY", "SURVIVED_ALL", "NOT_DISCRIMINATING")}
    try:
        print("SCRATCH copy of: %s (git archive HEAD, read-only source; mutants exist only in the scratch copy)" %
              " ".join(ARCHIVE_PATHS))
        suites = []
        for m in MUTANTS:
            if m[5] not in suites:
                suites.append(m[5])
        rc, out, to, nr = run_cmd(STANDING, 180, scratch)
        c_standing_ok = rc == 0 and not to and not nr
        print("ADDED_PATHS (F2, control needed them): %s" % " ".join(ADDED_PATHS))
        print("CONTROL standing_gate %s exit=%s %s" % (" ".join(STANDING), rc, "PASS" if c_standing_ok else "NOT_PASS"))
        if not c_standing_ok:
            print("  control_first_fail=%s" % first_fail(out))
        control_ok = c_standing_ok
        for s in suites:
            tmo = next(m[6] for m in MUTANTS if m[5] == s)
            rc, out, to, nr = run_cmd(s, tmo, scratch)
            ok = rc == 0 and not to and not nr
            control_ok = control_ok and ok
            print("CONTROL owning_suite %s exit=%s %s" % (" ".join(s[1:] if s[0] == "python3" else s), rc,
                                                           "PASS" if ok else "NOT_PASS"))
            if not ok:
                print("  control_first_fail=%s" % first_fail(out))
        print("CONTROL_RESULT %s" % ("PASS" if control_ok else "NOT_PASS"))
        for mid, phase, relfile, target, repl, own_argv, own_tmo in MUTANTS:
            path = os.path.join(scratch, relfile)
            print("%s owner=%s phase=%s" % (mid, relfile, phase))
            print("  target=%r" % target)
            print("  replacement=%r" % repl)
            with open(path, encoding="utf-8") as fh:
                original = fh.read()
            occ = original.count(target)
            print("  occurrences=%d" % occ)
            verdict, standing, own = "NOT_DISCRIMINATING", (None, "-", True), (None, "-", True)
            compiled = "SKIPPED"
            if occ == 1 and control_ok:
                mutated = original.replace(target, repl)
                try:
                    compile(mutated, path, "exec")
                    compiled = "OK"
                except SyntaxError as exc:
                    compiled = "SyntaxError: %s" % exc
                print("  compile=%s" % compiled)
                if compiled == "OK":
                    try:
                        with open(path, "w", encoding="utf-8") as fh:
                            fh.write(mutated)
                        rc, out, to, nr = run_cmd(STANDING, 180, scratch)
                        standing = (rc, first_fail(out), to or nr)
                        rc2, out2, to2, nr2 = run_cmd(own_argv, own_tmo, scratch)
                        own = (rc2, first_fail(out2), to2 or nr2)
                    finally:
                        with open(path, "w", encoding="utf-8") as fh:
                            fh.write(original)
                    verdict = classify(standing, own)
            else:
                print("  compile=%s" % compiled)
            print("  standing_gate exit=%s first_fail=%s" % (standing[0], standing[1]))
            print("  own_suite %s exit=%s first_fail=%s" % (" ".join(own_argv[1:]), own[0], own[1]))
            print("VERDICT %s %s" % (mid, verdict))
            counts[verdict] += 1
        print("MATRIX: ENFORCED=%d OWN_SUITE_ONLY=%d SURVIVED_ALL=%d NOT_DISCRIMINATING=%d" % (
            counts["ENFORCED"], counts["OWN_SUITE_ONLY"], counts["SURVIVED_ALL"], counts["NOT_DISCRIMINATING"]))
        print("SCRATCH removed=%s" % drop_scratch(scratch))
        return 0
    finally:
        drop_scratch(scratch)


def verify_record(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    problems = []
    if "CONTROL_RESULT PASS" not in text:
        problems.append("control did not pass")
    verdicts = re.findall(r"^VERDICT (MX\d) (\w+)$", text, flags=re.M)
    if len(verdicts) != 5:
        problems.append("expected 5 VERDICT lines, found %d" % len(verdicts))
    closed = {"ENFORCED", "OWN_SUITE_ONLY", "SURVIVED_ALL", "NOT_DISCRIMINATING"}
    for mid, v in verdicts:
        if v not in closed:
            problems.append("%s verdict %r outside the closed set" % (mid, v))
    occ = re.findall(r"^  occurrences=(\d+)$", text, flags=re.M)
    if len(occ) != 5 or any(o != "1" for o in occ):
        problems.append("occurrence counts %s (want five 1s)" % occ)
    comp = re.findall(r"^  compile=(.*)$", text, flags=re.M)
    if len(comp) != 5 or any(c != "OK" for c in comp):
        problems.append("compile results %s" % comp)
    m = re.search(r"^MATRIX: ENFORCED=(\d+) OWN_SUITE_ONLY=(\d+) SURVIVED_ALL=(\d+) NOT_DISCRIMINATING=(\d+)$",
                  text, flags=re.M)
    if not m:
        problems.append("no MATRIX footer")
    else:
        tally = {k: sum(1 for _i, v in verdicts if v == k) for k in closed}
        foot = dict(zip(("ENFORCED", "OWN_SUITE_ONLY", "SURVIVED_ALL", "NOT_DISCRIMINATING"), map(int, m.groups())))
        if sum(foot.values()) != 5 or foot != {k: tally[k] for k in foot}:
            problems.append("footer %s does not match verdict lines %s" % (foot, tally))
    if not re.search(r"^# exit=\d+$", text, flags=re.M):
        problems.append("no record_run exit footer")
    for bad in ("/home/", "/Users/", "C:\\Users", os.path.join(tempfile.gettempdir(), SCRATCH_PREFIX)):
        if bad in text:
            problems.append("record contains host path %r" % bad)
    if problems:
        for p in problems:
            print("MATRIX_RECORD_PROBLEM " + p)
        return 1
    print("MATRIX_RECORD_OK verdicts=%s" % ",".join("%s:%s" % t for t in verdicts))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    mp = sub.add_parser("manifest")
    mp.add_argument("--only", default="")
    mp.add_argument("--include-slow", action="store_true")
    xp = sub.add_parser("matrix")
    xp.add_argument("--verify-record", default="")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "manifest":
        return cmd_manifest(a)
    return cmd_matrix(a)


if __name__ == "__main__":
    sys.exit(main())
