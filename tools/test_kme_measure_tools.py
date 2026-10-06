#!/usr/bin/env python3
"""V-KMEC-* gates for the two KME-L challenger measuring tools (incremental-cognition phase 2, plan 02-02):
tools/strace_io_sum.py (open-set summer + query runner) and tools/kme_equivalence.py (normalised comparator).

Hermetic: every corpus, log and candidate directory is built here under a scratch directory; the committed
measurement files are only read. A SKIP or an INCONCLUSIVE is printed and counted apart; it is never a PASS and
never part of the n/m denominator.

    python3 tools/test_kme_measure_tools.py            run every gate
    python3 tools/test_kme_measure_tools.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import atexit
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import strace_io_sum as ssum  # noqa: E402

MEASUREMENTS = REPO / "vault" / "programs" / "incremental-cognition" / "measurements"
TMP_ROOT = Path(os.path.realpath(tempfile.mkdtemp(prefix="kmet-test-")))
_COUNTER = [0]
RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]
HAVE_STRACE = os.path.exists("/usr/bin/strace")


def _cleanup() -> None:
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


def summary_line() -> str:
    n_pass = sum(1 for s, _, _ in RESULTS if s == "PASS")
    n_fail = sum(1 for s, _, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _, _ in RESULTS if s == "SKIP")
    inconc = sum(1 for s, _, _ in RESULTS if s == "INCONCLUSIVE")
    m = n_pass + n_fail
    return f"KMET_PASS={n_pass}/{m}  threshold={m}/{m}  skipped={skipped}  inconclusive={inconc}"


# --------------------------------------------------------------------------- strace fixtures
def write_file(path: Path, size: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


class Corpus:
    """A tmp corpus under <root>/projects with real files of known sizes, an index DB and a non-corpus file."""

    def __init__(self):
        self.base = scratch("corp")
        self.root = self.base / "projects"
        self.s1 = write_file(self.root / "projA" / "s1.jsonl", 1000)
        self.s2 = write_file(self.root / "projA" / "s2.jsonl", 2000)
        self.s3 = write_file(self.root / "projB" / "s3.jsonl", 3000)
        self.cl_dir = self.root / "-home-Cursor-Projects-CostaLuz-Lawyers"
        self.c1 = write_file(self.cl_dir / "c1.jsonl", 4500)
        self.idx = write_file(self.base / "idx" / "cold.sqlite", 5000)
        self.wal = write_file(self.base / "idx" / "cold.sqlite-wal", 904)
        self.other = write_file(self.base / "other" / "notes.txt", 77)


def op(pid, path, ret_fd, flags="O_RDONLY|O_CLOEXEC"):
    return f'{pid} openat(AT_FDCWD</work>, "{path}", {flags}) = {ret_fd}<{path}>'


def rd(pid, fd, path, ret, name="read"):
    if name == "pread64":
        return f'{pid} pread64({fd}<{path}>, "abc"..., 4096, 0) = {ret}'
    if name == "preadv":
        return f'{pid} preadv({fd}<{path}>, [{{iov_base="abc", iov_len=500}}], 1, 1500) = {ret}'
    if name == "readv":
        return f'{pid} readv({fd}<{path}>, [{{iov_base="abc", iov_len=500}}], 1) = {ret}'
    return f'{pid} read({fd}<{path}>, "abc"..., 65536) = {ret}'


def exact_log(c: Corpus, with_forbidden=True) -> list[str]:
    L = [
        op(100, c.s1, 3),
        rd(100, 3, c.s1, 600),
        f'100 read(3<{c.s1}>,  <unfinished ...>',
        op(101, c.s2, 4),
        f'100 <... read resumed>"abc"..., 65536) = 400',
        rd(101, 4, c.s2, 1500, "pread64"),
        rd(101, 4, c.s2, 0),
        rd(101, 4, c.s2, 500, "preadv"),
        op(100, c.s3, 5),
        rd(100, 5, c.s3, 3000),
    ]
    if with_forbidden:
        L += [op(100, str(c.cl_dir), 6, "O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY"),
              op(100, c.c1, 7),
              rd(100, 7, c.c1, 4000)]
    L += [
        op(100, c.idx, 8), rd(100, 8, c.idx, 4096),
        op(100, c.wal, 9), rd(100, 9, c.wal, 904),
        op(100, c.other, 10), rd(100, 10, c.other, 77),
        '100 openat(AT_FDCWD</work>, "/nonexistent", O_RDONLY) = -1 ENOENT (No such file or directory)',
        '100 read(3<' + str(c.s1) + '>, 0x7ffd, 65536) = -1 EAGAIN (Resource temporarily unavailable)',
        '101 --- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=101} ---',
        '101 +++ exited with 0 +++',
    ]
    return L


def write_log(lines, name="x.strace") -> Path:
    p = scratch("log") / name
    p.write_text("\n".join(lines) + ("\n" if lines else ""))
    return p


def sum_json(argv):
    """Run ssum.main in process; (exit code, parsed JSON or None)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ssum.main(argv)
    out = buf.getvalue()
    try:
        return rc, json.loads(out)
    except ValueError:
        return rc, None


def sum_of(lines, c: Corpus, *extra):
    log = write_log(lines)
    return sum_json(["sum", str(log), "--corpus-root", str(c.root), "--scope-regex", "^projA$",
                     "--index-path", str(c.idx), *extra])


# --------------------------------------------------------------------------- Task 1 gates
def g_sum_exact():
    c = Corpus()
    rc, j = sum_of(exact_log(c), c)
    want = {
        "verdict": "MEASURED", "syscalls_parsed": 20, "lines_unparsed": 0,
        "raw_bytes": 10000, "raw_files_opened": 4, "unique_bytes": 1000 + 2000 + 3000 + 4500,
        "cross_project_bytes": 7000, "forbidden_bytes": 4000, "forbidden_opens": 2,
        "index_bytes": 5000, "other_bytes": 77, "unstattable": [],
        "by_project": {"-home-Cursor-Projects-CostaLuz-Lawyers": {"bytes": 4000, "files": 1},
                       "projA": {"bytes": 3000, "files": 2}, "projB": {"bytes": 3000, "files": 1}},
    }
    bad = {k: (j or {}).get(k) for k, v in want.items() if (j or {}).get(k) != v}
    leaked = "abc" in json.dumps(j)   # the log payload strings must never reach the output
    return rc == 0 and j is not None and not bad and not leaked, f"rc={rc} mismatches={bad} cross={j and j['cross_project_bytes']}"


def g_forbid_fires():
    c = Corpus()
    rc1, with_cl = sum_of(exact_log(c, True), c)
    rc2, without = sum_of(exact_log(c, False), c)
    ctl = (without["forbidden_bytes"], without["forbidden_opens"])
    low = write_file(c.root / "-home-x-costaluz-companion" / "k.jsonl", 100)
    spaced = write_file(c.root / "-home-Cursor Projects-CostaLuz Lawyers" / "k2.jsonl", 50)
    rc3, lo = sum_of([op(1, low, 3), rd(1, 3, low, 100), op(1, spaced, 4), rd(1, 4, spaced, 50)], c)
    ok = (with_cl["forbidden_bytes"] > 0 and with_cl["forbidden_opens"] > 0 and ctl == (0, 0)
          and lo["forbidden_bytes"] == 150 and lo["forbidden_opens"] == 2 and lo["raw_files_opened"] == 2)
    return ok, (f"positive control bytes={with_cl['forbidden_bytes']} opens={with_cl['forbidden_opens']}; "
                f"paired control without the lines={ctl}; lowercase+spaced path bytes={lo['forbidden_bytes']} "
                f"opens={lo['forbidden_opens']}")


def g_unique_inode():
    c = Corpus()
    link = c.root / "projAlias"
    os.symlink("projA", link)
    a, b = c.root / "projA" / "s1.jsonl", link / "s1.jsonl"
    rc, j = sum_of([op(1, a, 3), rd(1, 3, a, 100), op(1, b, 4), rd(1, 4, b, 100)], c)
    ok = j["raw_bytes"] == 200 and j["unique_bytes"] == 1000 and j["raw_files_opened"] == 2
    gone = c.root / "projA" / "gone.jsonl"
    rc2, j2 = sum_of([op(1, gone, 3), rd(1, 3, gone, 10)], c)
    ok2 = j2["unstattable"] == [str(gone)] and j2["unique_bytes"] == 0 and j2["raw_bytes"] == 10
    return ok and ok2, (f"alias pair raw={j['raw_bytes']} unique={j['unique_bytes']} files={j['raw_files_opened']}; "
                        f"vanished file listed unstattable={j2['unstattable'] == [str(gone)]}")


def g_sum_empty_unmeasured():
    c = Corpus()
    rows = []
    for label, lines in (("empty", []), ("garbage", ["hello", "not a syscall", "+++ exited with 0 +++"])):
        rc, j = sum_of(lines, c)
        rows.append((label, rc, j and j["verdict"], j and j["syscalls_parsed"]))
    cp = subprocess.run([sys.executable, "-I", str(HERE / "strace_io_sum.py"), "sum", "/dev/null",
                         "--corpus-root", str(c.root)], capture_output=True, text=True)
    cli_ok = cp.returncode == 3 and '"verdict": "UNMEASURED"' in cp.stdout
    ok = all(r[1] == 3 and r[2] == "UNMEASURED" and r[3] == 0 for r in rows) and cli_ok
    return ok, f"{rows} cli /dev/null rc={cp.returncode}"


def _run_json(argv):
    return sum_json(["run", *argv])


def g_run_real_strace():
    if not HAVE_STRACE:
        return "SKIP", "/usr/bin/strace absent"
    c = Corpus()
    f = write_file(c.root / "projR" / "r.jsonl", 12345)
    code = "import sys; open(sys.argv[1],'rb').read()"
    step = " ".join(shlex.quote(x) for x in (sys.executable, "-I", "-c", code, str(f)))
    td = scratch("trace")
    rc, j = _run_json(["--label", "real", "--repeat", "1", "--trace-repeat", "1", "--trace-dir", str(td),
                       "--step", step, "--corpus-root", str(c.root)])
    t = (j or {}).get("traced", [{}])[0]
    rc2, j2 = _run_json(["--label", "two", "--repeat", "0", "--trace-repeat", "2", "--trace-dir", str(td),
                         "--step", step, "--corpus-root", str(c.root)])
    ok = (rc == 0 and t.get("raw_bytes") == 12345 and t.get("raw_files_opened") == 1
          and t.get("verdict") == "MEASURED" and (j or {}).get("wall_median_s") is not None
          and rc2 == 0 and j2["open_set_identical"] is True and j2["wall_median_s"] is None)
    return ok, (f"rc={rc} raw_bytes={t.get('raw_bytes')} files={t.get('raw_files_opened')} "
                f"index_bytes={t.get('index_bytes')} identical(K=2)={j2 and j2['open_set_identical']} "
                f"median(N=0)={j2 and j2['wall_median_s']}")


def g_run_median():
    c = Corpus()
    td = scratch("trace")
    triv = " ".join(shlex.quote(x) for x in (sys.executable, "-c", "pass"))
    ev = write_file(c.base / "evict" / "e.jsonl", 100)
    rc, j = _run_json(["--label", "med", "--repeat", "3", "--trace-dir", str(td), "--step", triv,
                       "--evict", str(c.base / "evict"), "--corpus-root", str(c.root)])
    walls = [r["wall_s"] for r in j["wall_runs"]]
    med_ok = len(walls) == 3 and j["wall_median_s"] == round(statistics.median(walls), 6) and not j["failed"]
    cache_ok = j["cache"].get("mode") == ssum.CACHE_LABEL and j["cache"]["evicted"] == 3 and ev.exists()
    marker = c.base / "marker"
    flaky = " ".join(shlex.quote(x) for x in (
        sys.executable, "-c",
        "import os,sys; p=sys.argv[1]; ok=os.path.exists(p); open(p,'a').close(); sys.exit(0 if ok else 3)",
        str(marker)))
    rc2, j2 = _run_json(["--label", "flaky", "--repeat", "3", "--trace-dir", str(td), "--step", flaky,
                         "--corpus-root", str(c.root)])
    good = [r["wall_s"] for r in j2["wall_runs"] if not r["failed"]]
    fail_ok = (rc2 == 1 and [r["failed"] for r in j2["wall_runs"]] == [True, False, False]
               and j2["wall_median_s"] == round(statistics.median(good), 6) and len(j2["failed"]) == 1
               and j2["failed"][0]["exit"] == 3)
    allbad = " ".join(shlex.quote(x) for x in (sys.executable, "-c", "import sys; sys.exit(3)"))
    rc3, j3 = _run_json(["--label", "bad", "--repeat", "2", "--trace-dir", str(td), "--step", allbad,
                         "--corpus-root", str(c.root)])
    none_ok = j3["wall_median_s"] is None and len(j3["failed"]) == 2
    return med_ok and cache_ok and fail_ok and none_ok, (
        f"walls={walls} median={j['wall_median_s']} cache={j['cache']}; flaky failed={[r['failed'] for r in j2['wall_runs']]} "
        f"median over good={j2['wall_median_s']}; all-failed median={j3['wall_median_s']}")


# --------------------------------------------------------------------------- Task 2 gates (comparator)
PILLARS = "DEFGHIL"
DATE = "2026-10-05"
MEAS_SHA = {}


def keq():
    """The comparator, imported lazily so a missing tool reads as a FAIL naming ModuleNotFoundError."""
    import importlib
    return importlib.import_module("kme_equivalence")


def committed_text(p):
    return (MEASUREMENTS / f"{p}-KME-L-{DATE}.md").read_text(encoding="utf-8")


def measurement_hashes():
    import hashlib
    return {p: hashlib.sha256((MEASUREMENTS / f"{p}-KME-L-{DATE}.md").read_bytes()).hexdigest() for p in PILLARS}


def volatilise(text):
    """Change exactly the volatile fields, independently of the comparator's own VOLATILE list."""
    text = re.sub(r'(?m)^(measured_at: )".*"$', r'\1"2026-10-09T01:02:03Z"', text)
    text = re.sub(r'(?m)^( "measured_at": )".*"(,?)$', r'\1"2026-10-09T01:02:03Z"\2', text)
    text = re.sub(r'(?m)^(command: )".*"$', r'\1"python3 elsewhere --probe"', text)
    text = re.sub(r'(?m)^( "command": )".*"(,?)$', r'\1"python3 elsewhere --probe"\2', text)
    return re.sub(r'("commit": ")[0-9a-f]{40}(")', r"\g<1>" + "f" * 40 + r"\2", text)


def perturb_population(text):
    """One digit of the JSON population.calls changed."""
    m = re.search(r'("population": \{.*?"calls": )(\d+)', text, re.S)
    assert m, "population.calls not found"
    n = m.group(2)
    return text[:m.end(1)] + n[:-1] + str((int(n[-1]) + 1) % 10) + text[m.end(2):]


def cand_dir(mutate=None, only=None, drop=(), rename_date=None):
    """A candidate directory of copies of the committed files; mutate(pillar, text) -> text."""
    d = scratch("cand")
    for p in PILLARS:
        if p in drop:
            continue
        t = committed_text(p)
        if mutate and (only is None or p in only):
            t = mutate(p, t)
        (d / f"{p}-KME-L-{rename_date or DATE}.md").write_text(t, encoding="utf-8")
    return d


def run_compare(cand, extra=()):
    """(rc, raw output, {pillar: fields}) of `compare` on a candidate dir against the committed measurements."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = keq().main(["compare", "--candidate", str(cand), "--committed", str(MEASUREMENTS), *extra])
    out = buf.getvalue()
    rows = {}
    for line in out.splitlines():
        if line.startswith("KMEQ pillar="):
            f = dict(re.findall(r"(\w+)=(\S+)", line))
            rows[f["pillar"]] = f
    return rc, out, rows


def verdicts(rows):
    return "".join({"SAME": "S", "DIFFERENT": "D", "MISSING": "M"}.get(rows.get(p, {}).get("verdict"), "?") for p in PILLARS)


def g_equiv_self():
    before = measurement_hashes()
    rc, out, rows = run_compare(cand_dir())
    rc2, out2, rows2 = run_compare(MEASUREMENTS)
    ok = (rc == 0 and verdicts(rows) == "SSSSSSS" and "KMEQ_VERDICT=SAME same=7/7" in out
          and rc2 == 0 and verdicts(rows2) == "SSSSSSS" and measurement_hashes() == before)
    return ok, f"copies {verdicts(rows)} rc={rc}; committed-vs-itself {verdicts(rows2)} rc={rc2}; committed unchanged={measurement_hashes() == before}"


def g_equiv_volatile_masked():
    d = cand_dir(lambda p, t: volatilise(t), rename_date="2026-10-09")
    changed = sum(1 for p in PILLARS if volatilise(committed_text(p)) != committed_text(p))
    rc, out, rows = run_compare(d, ["--date", DATE])
    return rc == 0 and verdicts(rows) == "SSSSSSS" and changed == 7, (
        f"{changed}/7 files changed in measured_at/command (+H commit) and renamed 2026-10-09: {verdicts(rows)} rc={rc}")


def g_equiv_perturb():
    seen = {}
    for p in PILLARS:
        rc, out, rows = run_compare(cand_dir(lambda q, t: perturb_population(t), only=p))
        want = "".join("D" if x == p else "S" for x in PILLARS)
        seen[p] = (verdicts(rows) == want and rc == 1 and "KMEQ_VERDICT=DIFFERENT same=6/7" in out)
    return all(seen.values()), f"one population digit per file, DIFFERENT and exit 1: {seen}"


def g_equiv_sessions():
    def mut(p, t):
        assert '"sessions_scanned": 568' in t
        return t.replace('"sessions_scanned": 568', '"sessions_scanned": 552')
    rc, out, rows = run_compare(cand_dir(mut, only="D"))
    r = rows.get("D", {})
    ok = (rc == 1 and r.get("verdict") == "DIFFERENT" and r.get("sessions_scanned") == "552/568"
          and "sessions_scanned" in r.get("key", "") and verdicts(rows) == "DSSSSSS")
    return ok, f"D with sessions_scanned 552: {verdicts(rows)} fields={ {k: r.get(k) for k in ('sessions_scanned', 'key', 'first_diff_line')} }"


def g_equiv_h_verdicts():
    def mut(p, t):
        t = volatilise(t)   # commit is masked, so only the verdict map can differ
        n = t.count('"P": "FALSIFIED_OR_REJECTED_BY_EVIDENCE"')
        assert n >= 2, n
        return t.replace('"P": "FALSIFIED_OR_REJECTED_BY_EVIDENCE"', '"P": "OPEN"')
    rc, out, rows = run_compare(cand_dir(mut, only="H"))
    r = rows.get("H", {})
    ok = rc == 1 and verdicts(rows) == "SSSSDSS" and r.get("verdict_map") == "DIFFERENT"
    return ok, f"H copy with one owner terminal changed and commit changed: {verdicts(rows)} verdict_map={r.get('verdict_map')}"


def g_equiv_missing():
    rc, out, rows = run_compare(cand_dir(drop="I"))
    miss_ok = rc == 1 and verdicts(rows) == "SSSSSMS" and "KMEQ_VERDICT=DIFFERENT same=6/7" in out
    d = cand_dir()
    (d / f"D-KME-L-2026-10-06.md").write_text(committed_text("D"), encoding="utf-8")
    rc2, out2, rows2 = run_compare(d)
    amb_ok = rc2 == 1 and rows2["D"]["verdict"] == "MISSING" and "ambiguous" in out2
    rc3, out3, rows3 = run_compare(cand_dir(), ["--pillars", "DEFGHIX"])
    return miss_ok and amb_ok and rc3 == 2, (
        f"I absent: {verdicts(rows)} rc={rc}; two D files: {rows2['D']['verdict']} rc={rc2}; unknown pillar X rc={rc3}")


def g_equiv_no_content():
    canary = "CANARY_ZQXJ_TRANSCRIPT_TEXT"

    def mut(p, t):
        lines = t.split("\n")
        i = next(i for i, ln in enumerate(lines) if ln.startswith("- ") and i > 30)
        lines[i] = lines[i] + " " + canary
        return "\n".join(lines)
    rc, out, rows = run_compare(cand_dir(mut, only="D"))
    ok = rc == 1 and rows["D"]["verdict"] == "DIFFERENT" and canary not in out and "CANARY" not in out
    return ok, f"D body line changed to carry a canary: {rows['D']['verdict']} key={rows['D'].get('key')} canary printed={canary in out}"


def g_equiv_selftest():
    before = measurement_hashes()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = keq().main(["selftest-perturb", "--committed", str(MEASUREMENTS)])
    out = buf.getvalue()
    d = scratch("partial")
    for p in PILLARS[:-1]:
        shutil.copy(MEASUREMENTS / f"{p}-KME-L-{DATE}.md", d)
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc2 = keq().main(["selftest-perturb", "--committed", str(d)])
    ok = (rc == 0 and "KMEQ_SELFTEST=PASS" in out and rc2 == 1 and "KMEQ_SELFTEST=FAIL" in buf2.getvalue()
          and measurement_hashes() == before)
    return ok, f"real files rc={rc} {'PASS' if 'KMEQ_SELFTEST=PASS' in out else 'not PASS'}; a directory missing L rc={rc2}"


GATES_TASK2 = [
    ("V-KMEC-EQUIV-SELF", g_equiv_self),
    ("V-KMEC-EQUIV-VOLATILE-MASKED", g_equiv_volatile_masked),
    ("V-KMEC-EQUIV-PERTURB", g_equiv_perturb),
    ("V-KMEC-EQUIV-SESSIONS", g_equiv_sessions),
    ("V-KMEC-EQUIV-H-VERDICTS", g_equiv_h_verdicts),
    ("V-KMEC-EQUIV-MISSING", g_equiv_missing),
    ("V-KMEC-EQUIV-NO-CONTENT", g_equiv_no_content),
    ("V-KMEC-EQUIV-SELFTEST", g_equiv_selftest),
]


GATES_TASK1 = [
    ("V-KMEC-SUM-EXACT", g_sum_exact),
    ("V-KMEC-FORBID-FIRES", g_forbid_fires),
    ("V-KMEC-UNIQUE-INODE", g_unique_inode),
    ("V-KMEC-SUM-EMPTY-UNMEASURED", g_sum_empty_unmeasured),
    ("V-KMEC-RUN-REAL-STRACE", g_run_real_strace),
    ("V-KMEC-RUN-MEDIAN", g_run_median),
]
GATES = GATES_TASK1 + GATES_TASK2


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    skipped_strace = any(r[0] == "SKIP" for r in RESULTS) and HAVE_STRACE
    return 0 if counted and all(r[0] == "PASS" for r in counted) and not skipped_strace else 1


if __name__ == "__main__":
    sys.exit(run_all())
