#!/usr/bin/env python3
"""V-KMEC-* gates: the KME-L challenger access plan and its guard chain (autonomous-optimization phase 2, plans 01, 03).

Hermetic: every fixture is a synthetic transcript tree plus a fixture usage index built here under a scratch
directory. Nothing outside it is read or written. A SKIP or an INCONCLUSIVE is printed and counted apart; it is never
a PASS and never part of the n/m denominator.

    python3 -I tools/test_kme_challenger.py       run every gate
    python3 -I tools/test_kme_challenger.py --drill   mutation drill: every challenger guard must be shown able to fail
    python3 -I tools/test_kme_challenger.py --real    GEX44 corpus copy: certify, reproduce the 7 KME-L files, read-only proof
    python3 -I tools/test_kme_challenger.py --real-exposure   GEX44: the KME-only query opens no CostaLuz byte (+ control)

The two real modes read /home/kobii/kme-corpus/projects and /home/kobii/ao-scratch/p1/cold.sqlite (read-only, hashed
before and after) and write only under /home/kobii/ao-scratch/p2/. An absent corpus or index is a SKIP and exit 1.

Helpers of tools/test_kme_pillars.py (Fx, ts, write_frozen, run_main, scratch, CANARY) are imported, not copied.
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for _p in (str(HERE), str(REPO / "wiki" / "tools"), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kme_equivalence as ke  # noqa: E402
import kme_pillars as kp  # noqa: E402
import kme_replay as kr  # noqa: E402
import kme_token_audit as kta  # noqa: E402
import test_kme_pillars as T  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)

IN_SCOPE = "-home-x-core-fixture"
OUT_SCOPE = "-home-x-CostaLuz-fixture"


# --------------------------------------------------------------------------- gate plumbing
QUIET = [False]


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


def summary_line(prefix: str = "KMEC_PASS") -> str:
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    n = sum(1 for r in counted if r[0] == "PASS")
    m = len(counted)
    sk = sum(1 for r in RESULTS if r[0] == "SKIP")
    inc = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"{prefix}={n}/{m}  threshold={m}/{m}  skipped={sk}  inconclusive={inc}"


# --------------------------------------------------------------------------- open spy
class OpenSpy:
    """Records every open() of a path under one of `roots` (builtins.open, io.open, os.open)."""

    def __init__(self, *roots):
        self.roots = set()
        for r in roots:
            self.roots |= {str(r), os.path.realpath(str(r))}
        self.opened: list[str] = []
        self._saved = None

    def _hit(self, p) -> None:
        if isinstance(p, (str, bytes, os.PathLike)):
            s = os.fsdecode(os.fspath(p))
            if any(s == r or s.startswith(r + os.sep) for r in self.roots):
                self.opened.append(os.path.realpath(s))

    def __enter__(self):
        spy = self
        self._saved = (builtins.open, io.open, os.open)
        real_open, real_io_open, real_os_open = self._saved

        def w_open(file, *a, **k):
            spy._hit(file)
            return real_open(file, *a, **k)

        def w_io(file, *a, **k):
            spy._hit(file)
            return real_io_open(file, *a, **k)

        def w_os(path, *a, **k):
            spy._hit(path)
            return real_os_open(path, *a, **k)

        builtins.open, io.open, os.open = w_open, w_io, w_os
        return self

    def __exit__(self, *exc):
        builtins.open, io.open, os.open = self._saved
        return False


# --------------------------------------------------------------------------- fixture
def load_usage_index():
    """tools/usage_index.py loaded by path under a test-only name: the oracle's own copy, apart from the one kme_pillars
    loads, so a mutant of kme_pillars' loader cannot also bend the fixture builder."""
    spec = importlib.util.spec_from_file_location("_kmec_ux", REPO / "tools" / "usage_index.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


UX = load_usage_index()


def _kme_session(fx, tag, t0):
    """A KME session by content: a human prompt naming KMEIP and two tool uses on .../kme/... inputs (share 1.0)."""
    fx.human("map the KMEIP arena", T.ts(t0))
    T.hook_ctx(fx, T.ts(t0 + 0.5), 120)     # pillar D needs a hook_additional_context attachment to be measurable
    fx.assistant(f"{tag}1", f"r{tag}1", (5, 800, 0, 30), T.ts(t0 + 1),
                 tool_uses=[(f"{tag}t1", "Read", {"file_path": "/x/kme/a.py"}),
                            (f"{tag}t2", "Bash", {"command": "ls kme/"})])
    fx.tool_result(f"{tag}t1", "R" * 200 + " " + T.CANARY, T.ts(t0 + 2))
    fx.tool_result(f"{tag}t2", "files", T.ts(t0 + 2))
    fx.assistant(f"{tag}2", f"r{tag}2", (5, 100, 800, 40), T.ts(t0 + 3))


def challenger_fixture(root, n2=False, preserved=False, z1=False):
    """In scope (-home-x-core-fixture, no 'kme' in the name): k1 = KME by content (+ one subagent file), n1 = no KME
    signal. Out of scope (-home-x-CostaLuz-fixture): c1 = KME by content, so an unscoped run would select and open it.
    Options (each adds one in-scope shape): n2 = a second non-KME session that no gate touches; preserved = a
    `_preserved/p1.jsonl` file (a shape the index does not hold: the certificate's `uncovered` map); z1 = a session
    whose only file has no timestamped line (review IN-04). Returns {name: path} of every transcript file."""
    files = {}
    k1 = T.Fx(root, project=IN_SCOPE, session="k1")
    _kme_session(k1, "k", 0)
    sub = k1.subagent("a1")
    sub.human("sub task", T.ts(1))
    sub.assistant("ks1", "rks1", (7, 50, 600, 20), T.ts(2))
    n1 = T.Fx(root, project=IN_SCOPE, session="n1")
    n1.human("fix the readme", T.ts(10))
    n1.assistant("n1a", "rn1a", (4, 60, 700, 11), T.ts(11), tool_uses=[("nt1", "Bash", {"command": "echo hi"})])
    n1.tool_result("nt1", "hi", T.ts(12))
    c1 = T.Fx(root, project=OUT_SCOPE, session="c1")
    _kme_session(c1, "c", 20)
    files.update(k1=k1.path, k1_sub=sub.path, n1=n1.path, c1=c1.path)
    if n2:
        f = T.Fx(root, project=IN_SCOPE, session="n2")
        f.human("tidy the docs", T.ts(14))
        f.assistant("n2a", "rn2a", (3, 40, 500, 9), T.ts(15))
        files["n2"] = f.path
    if preserved:
        f = T.Fx(root, project=IN_SCOPE, session="p1", path=Path(root) / "projects" / IN_SCOPE / "_preserved" / "p1.jsonl")
        f.human("preserved note", T.ts(16))
        files["preserved"] = f.path
    if z1:
        f = T.Fx(root, project=IN_SCOPE, session="z1")
        f.meta()                        # a metadata line: real transcripts carry no timestamp on these
        files["z1"] = f.path
    return {k: Path(os.path.realpath(v)) for k, v in files.items()}


def build_index(root, db):
    con = UX.connect(Path(db))
    try:
        UX.refresh(con, Path(root) / "projects", deadline_s=60)
    finally:
        con.close()
    return Path(db)


class World:
    """One fixture tree + its index + the frozen entry the champion's own scoped population of it defines."""

    def __init__(self, tag="w", **shapes):
        self.dir = T.scratch(tag)
        self.root = self.dir / "fx"
        self.projects = self.root / "projects"
        self.files = challenger_fixture(self.root, **shapes)
        self.extra_sessions = sum(1 for k in ("n2", "preserved", "z1") if shapes.get(k))
        self.db = build_index(self.root, self.dir / "ix" / "index.sqlite")
        self.out_n = 0
        self.cert_cache = {}
        self.frozen = self._champion_frozen(sessions=2 + self.extra_sessions)
        self.frozen_global = self._champion_frozen(pf=None, calls=5, sessions=3 + self.extra_sessions,
                                                   name="frozen-global.json")

    def out(self, name="o"):
        self.out_n += 1
        return self.dir / f"{name}{self.out_n}"

    def _champion_frozen(self, pf="core-fixture", calls=3, sessions=2, name="frozen.json"):
        probe = self.dir / ("probe-" + name)
        T.write_frozen(probe, **{"KME-L": dict(T.TRACER_POP)})
        rc, res, _o, err = T.run_json(self.args("d", frozen=probe, pf=pf,
                                                extra=["--out-dir", str(self.dir / ("probe-" + name + "-out"))]))
        assert res is not None, f"champion probe produced no result: rc={rc} err={err[-200:]}"
        pop = {f: res["population"][f] for f in kp.POP_FIELDS}
        # Arrange: the fixture must separate k1 from n1 under the champion's own rule (k1 main 2 calls + subagent 1;
        # n1 would add its 1 call; the out-of-scope c1 adds 2). A fixture that does not separate them fails loudly.
        assert pop["calls"] == calls and res["corpus"]["sessions_scanned"] == sessions, (pop, res["corpus"])
        assert pop["sessions_active"] == (1 if pf else 2), pop
        return T.write_frozen(self.dir / name, **{"KME-L": pop})

    def args(self, pillar="d", frozen=None, plan=None, extra=(), root_flags=True, pf="core-fixture", projects=None):
        extra = list(extra)
        a = [pillar, "--denominator", "KME-L", "--frozen-file", str(frozen or self.frozen)]
        if root_flags:
            a += ["--root", str(projects or self.projects), "--expand"]
        if pf:
            a += ["--project-filter", pf]
        if plan:
            a += ["--plan", plan]
        # a challenger / auto run needs the certificate of ITS question (certified here against the clean index), unless
        # the caller names one, the index does not exist, or the run is a usage error (no scope, no --cross-project)
        if (plan in ("challenger", "auto") and "--index-db" in extra and "--cert" not in extra
                and os.path.isfile(extra[extra.index("--index-db") + 1])
                and (pf or "--cross-project" in extra)):
            until = extra[extra.index("--until") + 1] if "--until" in extra else None
            extra += ["--cert", str(self.cert_for(pf=pf, frozen=frozen, cross="--cross-project" in extra, until=until))]
        return a + extra

    def certify_args(self, cert, pf="core-fixture", frozen=None, cross=False, until=None, index=None, projects=None):
        a = ["certify", "--denominator", "KME-L", "--frozen-file", str(frozen or self.frozen),
             "--root", str(projects or self.projects), "--expand", "--index-db", str(index or self.db),
             "--cert", str(cert)]
        if pf:
            a += ["--project-filter", pf]
        if cross:
            a += ["--cross-project"]
        if until:
            a += ["--until", until]
        return a

    def cert_for(self, pf="core-fixture", frozen=None, cross=False, until=None):
        """Path of the certificate of this question (certify against the clean index, once). The file exists only when
        certify exited 0; a caller that needs it checks."""
        key = (pf, str(frozen or self.frozen), cross, until)
        if key not in self.cert_cache:
            path = self.dir / f"cert-{len(self.cert_cache) + 1}.json"
            T.run_main(self.certify_args(path, pf=pf, frozen=frozen, cross=cross, until=until))
            self.cert_cache[key] = path
        return self.cert_cache[key]

    def measure(self, plan=None, extra=(), pf="core-fixture", spy=True, frozen=None, projects=None):
        """In-process run -> (rc, out, err, files written, opened transcript paths)."""
        outd = self.out()
        cmd = self.args("d", plan=plan, frozen=frozen, projects=projects, extra=list(extra) + ["--out-dir", str(outd)],
                        pf=pf)
        if spy:
            with OpenSpy(self.projects, *([projects] if projects else [])) as sp:
                rc, out, err = T.run_main(cmd)
            opened = sp.opened
        else:
            rc, out, err = T.run_main(cmd)
            opened = []
        written = sorted(outd.glob("D-KME-L-*.md")) if outd.is_dir() else []
        return rc, out, err, written, opened


def mask(front, res):
    """The measurement with only measured_at and command replaced (front matter and json block)."""
    f, r = dict(front), dict(res)
    for d in (f, r):
        d["measured_at"] = "MASKED"
        d["command"] = "MASKED"
    return f, r


def load(path):
    return T.parse_measurement(Path(path).read_text(encoding="utf-8"))


def selected_transcripts(w):
    return {str(w.files["k1"]), str(w.files["k1_sub"])}


# --------------------------------------------------------------------------- gates: tracer (task 1)
def g_scan_project_default():
    w = World("scan")
    pdir = str(w.projects / IN_SCOPE)

    def dump(sessions):
        return json.dumps(sessions, sort_keys=True, default=lambda x: dict(x))
    base = kta.scan_project(pdir)
    same_none = kta.scan_project(pdir, select=None)
    same_all = kta.scan_project(pdir, select=lambda proj, sid, path: True)
    with OpenSpy(w.projects) as sp:
        refused = kta.scan_project(pdir, select=lambda proj, sid, path: False)
    kme_calls = sum(s["main"].get("calls", 0) + s["sub"].get("calls", 0) for s in base)
    # positive control: the same scan really reads transcripts, so "zero opens" below is not a dead spy
    with OpenSpy(w.projects) as sp_ctl:
        kta.scan_project(pdir)
    seen = []
    kta.scan_project(pdir, select=lambda proj, sid, path: seen.append((proj, sid, os.path.basename(path))) or True)
    ok = (dump(base) == dump(same_none) == dump(same_all) and kme_calls == 4
          and len(refused) == len(base) == 2 and sp.opened == [] and len(sp_ctl.opened) == 3
          and sorted(seen) == sorted([(IN_SCOPE, "k1", "k1.jsonl"), (IN_SCOPE, "k1", "agent-a1.jsonl"),
                                      (IN_SCOPE, "n1", "n1.jsonl")]))
    return ok, (f"default==None==all-admit: {dump(base) == dump(same_none) == dump(same_all)}; sessions "
                f"base={len(base)} refused={len(refused)}; opens refused={len(sp.opened)} control={len(sp_ctl.opened)}; "
                f"select saw {len(seen)} files")


def g_tracer_d_e2e():
    w = World("e2e")
    rc_c, _o, err_c, champ, opened_c = w.measure(None)
    rc_h, _o2, err_h, chal, opened_h = w.measure("challenger", ["--index-db", str(w.db)])
    if rc_c != 0 or rc_h != 0 or len(champ) != 1 or len(chal) != 1:
        return False, f"rc champion={rc_c} challenger={rc_h} files={len(champ)}/{len(chal)} err={err_h[-300:]}"
    fc, rc_ = mask(*load(champ[0]))
    fh, rh = mask(*load(chal[0]))
    sel = selected_transcripts(w)
    ok = (fc == fh and rc_ == rh
          and set(opened_h) == sel                       # exactly the selected session's files, nothing else
          and str(w.files["n1"]) in set(opened_c)   # control: champion opens n1
          and rh["corpus"]["sessions_scanned"] == rc_["corpus"]["sessions_scanned"] == 2
          and rh["population"]["calls"] == 3)
    return ok, (f"masked front equal={fc == fh} masked json equal={rc_ == rh}; challenger opened "
                f"{sorted(os.path.basename(p) for p in opened_h)}; champion opened "
                f"{sorted(os.path.basename(p) for p in opened_c)}; sessions_scanned={rh['corpus']['sessions_scanned']}")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def g_index_read_only():
    w = World("ro")
    before = (_sha(w.db), os.stat(w.db).st_mtime_ns)
    ux = kp._usage_index()
    real_connect, calls = ux.connect, []

    def spy_connect(*a, **k):
        calls.append(a)
        raise AssertionError("the challenger must not open the index through usage_index.connect()")
    ux.connect = spy_connect
    try:
        rc, _o, err, written, opened = w.measure("challenger", ["--index-db", str(w.db)])
    finally:
        ux.connect = real_connect
    after = (_sha(w.db), os.stat(w.db).st_mtime_ns)
    # a 0444 copy still takes the index tier (only the selected session's files are opened)
    ro_dir = w.dir / "ro-copy"
    ro_dir.mkdir()
    ro_db = ro_dir / "index.sqlite"
    shutil.copyfile(w.db, ro_db)
    os.chmod(ro_db, 0o444)
    rc2, _o2, err2, written2, opened2 = w.measure("challenger", ["--index-db", str(ro_db)])
    # positive control: the connection kp opens really refuses a write
    con = kp._open_index_ro(w.db)
    try:
        try:
            con.execute("CREATE TABLE kmec_probe(x)")
            write_refused = False
        except sqlite3.OperationalError:
            write_refused = True
    finally:
        con.close()
    ok = (rc == 0 and rc2 == 0 and before == after and not calls and write_refused
          and len(written) == 1 and len(written2) == 1
          and set(opened) == selected_transcripts(w) and set(opened2) == selected_transcripts(w))
    return ok, (f"db unchanged={before == after} connect() calls={len(calls)} rc={rc}/{rc2} write refused on the ro "
                f"connection={write_refused} 0444 copy opened {len(opened2)} files; err={err[-120:]}{err2[-120:]}")

# --------------------------------------------------------------------------- gates: access plan (task 2)
PATH_KEYS = {"schema", "tool", "subcommand", "plan_requested", "plan_taken", "guards", "deopt", "read_set",
             "sessions_registered", "index_db", "denominator", "project_filter", "until", "cross_project", "keys",
             "metric_changed", "plane"}


def names(paths):
    return sorted(os.path.basename(p) for p in paths)


def path_taken(err):
    """(requested, taken, deopt) read from the KMEP-PATH stderr line, or None when absent."""
    for ln in err.splitlines():
        if ln.startswith("KMEP-PATH plan="):
            kv = dict(tok.split("=", 1) for tok in ln.split()[1:] if "=" in tok)
            return kv.get("plan"), kv.get("taken"), kv.get("deopt"), kv.get("read_files")
    return None


def g_plan_order():
    w = World("order")
    c1 = str(w.files["c1"])
    # index first: filter + valid index
    rc1, _o, err1, f1, op1 = w.measure("auto", ["--index-db", str(w.db)])
    # missing index -> scoped raw
    gone = str(w.dir / "no-such-index.sqlite")
    rc2, _o, err2, f2, op2 = w.measure("auto", ["--index-db", gone])
    # no filter + --cross-project + missing index -> global raw
    rc3, _o, err3, f3, op3 = w.measure("auto", ["--index-db", gone, "--cross-project"], pf=None)
    # no filter + --cross-project + valid index (global frozen) -> index, selected sessions only, c1 included
    outd = w.out()
    cmd4 = w.args("d", frozen=w.frozen_global, plan="auto", pf=None,
                  extra=["--index-db", str(w.db), "--cross-project", "--out-dir", str(outd)])
    with OpenSpy(w.projects) as sp4:
        rc4, _o, err4 = T.run_main(cmd4)
    t1, t2, t3, t4 = path_taken(err1), path_taken(err2), path_taken(err3), path_taken(err4)
    ok = (rc1 == 0 and t1 and t1[:3] == ("auto", "index", "none") and set(op1) == selected_transcripts(w)
          and t2 and t2[:3] == ("auto", "scoped", "index_open") and c1 not in set(op2)
          and str(w.files["n1"]) in set(op2) and len(f2) == 1
          and t3 and t3[:3] == ("auto", "global", "index_open") and c1 in set(op3)
          and rc4 == 0 and t4 and t4[:3] == ("auto", "index", "none")
          and set(sp4.opened) == selected_transcripts(w) | {c1})
    return ok, (f"filter+index: {t1} opened {names(op1)}; missing index: {t2} opened {names(op2)}; "
                f"global: {t3} opened {names(op3)}; cross-project index: {t4} opened {names(sp4.opened)}")


def g_cross_project_explicit():
    w = World("cross")
    rows = []
    for plan in ("auto", "challenger"):
        rc, _o, err, files, opened = w.measure(plan, ["--index-db", str(w.db)], pf=None)
        rows.append((plan, rc, len(opened), len(files), "--cross-project" in err))
    # control: the same run with the explicit switch is accepted (the refusal is the missing switch, not the flags)
    rc_ok, _o, _e, files_ok, _op = w.measure("challenger", ["--index-db", str(w.db), "--cross-project"], pf=None)
    ok = all(r[1] == 2 and r[2] == 0 and r[3] == 0 and r[4] for r in rows) and rc_ok in (0, 3)
    return ok, f"rows (plan, rc, opened, files, names --cross-project)={rows}; with the switch rc={rc_ok}"


def g_ks4_forced():
    w = World("ks4")
    out = {}
    rc_n, _o, _e, f_none, _op = w.measure(None)
    rc_c, _o, _e, f_champ, _op = w.measure("champion")
    same = (rc_n == rc_c == 0 and len(f_none) == len(f_champ) == 1
            and mask(*load(f_none[0])) == mask(*load(f_champ[0])))
    # forced champion without a filter opens the out-of-scope file
    rc_u, _o, _e, _f, op_u = w.measure("champion", pf=None)
    out["champion_unfiltered_opens_c1"] = str(w.files["c1"]) in set(op_u)
    # --plan scoped needs a filter
    out["scoped_no_filter"] = w.measure("scoped", pf=None)[0]
    # --index-db belongs to challenger / auto only
    out["champion_index_db"] = w.measure("champion", ["--index-db", str(w.db)])[0]
    out["scoped_index_db"] = w.measure("scoped", ["--index-db", str(w.db)])[0]
    out["champion_cross_project"] = w.measure("champion", ["--cross-project"], pf=None)[0]
    # forced challenger with a missing index: exit 3, nothing written
    gone = w.dir / "missing.sqlite"
    outd = w.out("forced")
    rc_f, _o, err_f = T.run_main(w.args("d", plan="challenger",
                                       extra=["--index-db", str(gone), "--out-dir", str(outd)]))
    out["challenger_missing_rc"] = rc_f
    out["challenger_missing_files"] = len(list(outd.glob("*"))) if outd.exists() else 0
    out["challenger_reason"] = f"index_missing: {gone}" in err_f
    # unknown plan: argparse exit 2
    out["unknown_plan"] = w.measure("bogus")[0]
    # scoped is today's scan: same file as the champion with the same filter
    rc_s, _o, _e, f_sc, _op = w.measure("scoped")
    scoped_same = rc_s == 0 and len(f_sc) == 1 and mask(*load(f_sc[0])) == mask(*load(f_champ[0]))
    # the champion never loads usage_index nor opens the index (own process, so the module list is clean)
    code = ("import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); import kme_pillars as kp; "
            "rc = kp.main(%r); print('LOADED' if (kp._UX_MODULE or any('usage_index' in m for m in sys.modules)) "
            "else 'CLEAN', rc)") % (str(REPO / "wiki" / "tools"), str(REPO),
                                    w.args("d", plan="champion", extra=["--out-dir", str(w.out("sub"))]))
    import subprocess
    p = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=300)
    clean = p.stdout.strip().splitlines()[-1:] == ["CLEAN 0"]
    with OpenSpy(w.db.parent) as sp_db:
        w.measure("champion")
    ok = (same and scoped_same and clean and not sp_db.opened and out["champion_unfiltered_opens_c1"]
          and out["scoped_no_filter"] == 2 and out["champion_index_db"] == 2 and out["scoped_index_db"] == 2
          and out["champion_cross_project"] == 2 and out["challenger_missing_rc"] == 3
          and out["challenger_missing_files"] == 0 and out["challenger_reason"] and out["unknown_plan"] == 2)
    return ok, (f"no-flag==champion={same} scoped==champion={scoped_same} champion clean subprocess="
                f"{p.stdout.strip()[-20:]!r} index opens by champion={len(sp_db.opened)}; {out}")


def g_path_log():
    w = World("plog")
    log = w.dir / "logs" / "path.jsonl"
    secret_db = w.dir / ("no-index-" + T.CANARY + ".sqlite")      # a reason that names a secret-shaped path
    errs = []
    for plan, extra in (("auto", ["--index-db", str(w.db)]), ("auto", ["--index-db", str(secret_db)]),
                        ("challenger", ["--index-db", str(secret_db)])):
        rc, _o, err, _f, _op = w.measure(plan, list(extra) + ["--path-log", str(log)])
        errs.append((rc, err))
    raw = log.read_bytes().decode("utf-8") if log.exists() else ""
    lines = [json.loads(x) for x in raw.splitlines()]
    shapes = [set(r) == PATH_KEYS for r in lines]
    first, second, third = (lines + [{}, {}, {}])[:3]
    stderr_ok = all(any(ln.startswith("KMEP-PATH plan=") for ln in e.splitlines()) for _rc, e in errs)
    # a champion run without --path-log prints nothing new; with it, it writes a record too
    _rc, _o, err_champ, _f, _op = w.measure("champion")
    quiet = "KMEP-PATH" not in err_champ
    ok = (len(lines) == 3 and all(shapes) and stderr_ok and quiet
          and T.CANARY not in raw and "[REDACTED" in raw
          and first.get("plan_taken") == "index" and first.get("deopt") is None
          and first["read_set"]["sessions"] == 1 and first["read_set"]["files"] == 2 and first["read_set"]["bytes"] > 0
          and first["sessions_registered"] == 2 and first["tool"] == "kme_pillars" and first["subcommand"] == "d"
          and {g["guard"] for g in first["guards"]} >= {"index_open", "kind", "population"}
          and second.get("plan_taken") == "scoped" and second["deopt"]["guard"] == "index_open"
          and third.get("plan_taken") == "refused" and third["plan_requested"] == "challenger"
          and third["deopt"]["guard"] == "index_open")
    return ok, (f"lines={len(lines)} shapes={shapes} stderr_ok={stderr_ok} champion quiet={quiet} canary in log="
                f"{T.CANARY in raw} redacted marker={'[REDACTED' in raw}; taken={[r.get('plan_taken') for r in lines]}")


def run_replay(w, plan, extra=()):
    extra = list(extra)
    if plan in ("challenger", "auto") and "--index-db" in extra and os.path.isfile(extra[extra.index("--index-db") + 1]):
        extra += ["--cert", str(w.cert_for())]
    outd = w.out("replay")
    args = ["rank", "--denominator", "KME-L", "--frozen-file", str(w.frozen), "--root", str(w.projects), "--expand",
            "--project-filter", "core-fixture", "--out-dir", str(outd)] + (["--plan", plan] if plan else []) + list(extra)
    saved = kp.DENOMS_REL
    kp.DENOMS_REL = str(w.frozen)
    out, err = io.StringIO(), io.StringIO()
    try:
        with OpenSpy(w.projects) as sp, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = kr.main(args)
    finally:
        kp.DENOMS_REL = saved
    files = sorted(outd.glob("L-KME-L-*.md")) if outd.is_dir() else []
    return rc, err.getvalue(), files, sp.opened


def masked_rank(path):
    text = Path(path).read_text(encoding="utf-8")
    head, _, rest = text.partition(kr.KMER_BODY_MARKER)
    body = json.loads(rest.partition(kr.KMER_BODY_END)[0])
    front = [ln for ln in head.splitlines() if not ln.startswith(("measured_at:", "command:"))]
    body["measured_at"] = body["command"] = "MASKED"
    return front, body


def g_replay_plan():
    w = World("replay")
    log = w.dir / "replay-path.jsonl"
    rc_c, _e, f_c, op_c = run_replay(w, None)
    rc_h, err_h, f_h, op_h = run_replay(w, "challenger", ["--index-db", str(w.db), "--path-log", str(log)])
    recs = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    gone = w.dir / "gone.sqlite"
    rc_r, err_r, f_r, op_r = run_replay(w, "challenger", ["--index-db", str(gone)])
    same = len(f_c) == len(f_h) == 1 and masked_rank(f_c[0]) == masked_rank(f_h[0])
    ok = (same and set(op_h) == selected_transcripts(w) and str(w.files["n1"]) in set(op_c)
          and len(recs) == 1 and recs[0]["tool"] == "kme_replay" and recs[0]["plan_taken"] == "index"
          and recs[0]["subcommand"] == "rank" and rc_r == kp.EXIT_UNMEASURED and not f_r and not op_r)
    return ok, (f"L file equal (masked)={same}; challenger opened {names(op_h)}; champion opened {names(op_c)}; "
                f"path records={[(r['tool'], r['plan_taken']) for r in recs]}; forced refusal rc={rc_r} files={len(f_r)}")


# --------------------------------------------------------------------------- gates: certificate and keys (plan 03, task 1)
def read_log(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()] if Path(path).exists() else []


def run_certify(w, cert, **kw):
    rc, out, err = T.run_main(w.certify_args(cert, **kw))
    return rc, out, err


def go(w, plan, extra=(), pf="core-fixture", frozen=None, projects=None, spy=True):
    """One logged run: {rc, err, files, opened, rec (the path record of the run), out dir}."""
    log = w.dir / f"go-{w.out_n + 1}.jsonl"
    rc, out, err, files, opened = w.measure(plan, list(extra) + ["--path-log", str(log)], pf=pf, spy=spy,
                                            frozen=frozen, projects=projects)
    recs = read_log(log)
    return {"rc": rc, "err": err, "files": files, "opened": opened, "rec": recs[-1] if recs else None}


def masked_of(res):
    return mask(*load(res["files"][0])) if res["files"] else None


@contextlib.contextmanager
def patched_attr(obj, name, value):
    saved = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, saved)


def patch_kme_pillars_text(find, repl):
    """A `_source_text` that serves kme_pillars.py with one definition text changed (nothing on disk is edited)."""
    real = kp._source_text

    def fake(rel):
        text = real(rel)
        if rel == kp._KP_REL:
            assert find in text, f"{find!r} not found in {rel}"
            text = text.replace(find, repl, 1)
        return text
    return patched_attr(kp, "_source_text", fake)


def parser_patch(w):
    """A SELECTION_SOURCES whose kme_report.py is a scratch copy with ONE extra byte (same basename: only the bytes
    differ). Returns the context manager and the digest it produces."""
    mut = w.dir / "mut" / "kme_report.py"
    mut.parent.mkdir(exist_ok=True)
    mut.write_bytes((REPO / "wiki" / "tools" / "kme_report.py").read_bytes() + b"\n")
    srcs = tuple(str(mut) if os.path.basename(x) == "kme_report.py" else x for x in kp.SELECTION_SOURCES)
    return patched_attr(kp, "SELECTION_SOURCES", srcs)


def swapped_selection(select_extra=None, drop=None):
    """A usage_index.population that answers with the same totals but a different per-session selection."""
    ux = kp._usage_index()
    real = ux.population

    def fake(*a, **k):
        ans = real(*a, **k)
        for r in ans.get("detail", []):
            if drop and r["session_key"] == drop:
                r["selected"] = False
            if select_extra and r["session_key"] == select_extra:
                r["selected"] = True
        return ans
    return patched_attr(ux, "population", fake)


def g_certify_shadow():
    w = World("cs")
    champ = T.run_json(w.args("d", extra=["--out-dir", str(w.dir / "champ-out")]))[1]["population"]
    want = champ["sessions_active"] + champ["sessions_dead"]
    cert = w.dir / "c-ok.json"
    rc, out, err = run_certify(w, cert)
    c = json.loads(cert.read_text(encoding="utf-8")) if cert.exists() else {}
    ok_main = (rc == 0 and f"verdict=CERTIFIED selected={want} uncovered=0 cert={cert}" in out
               and c.get("shadow", {}).get("agree") is True and c["selected"]["sessions"] == want
               and c["shadow"]["champion_selected"] == c["shadow"]["index_selected"] == want and want == 1)
    # the index's per-session selection swapped (same totals): disagreement, exit 1, ids named, nothing written
    cert2 = w.dir / "c-swap.json"
    with swapped_selection(select_extra="n1", drop="k1"):
        rc2, out2, err2 = run_certify(w, cert2)
    swap_ok = (rc2 == kp.EXIT_DISAGREE and "verdict=NOT_CERTIFIED" in out2 and not cert2.exists()
               and f"{IN_SCOPE}/k1" in err2 and f"{IN_SCOPE}/n1" in err2)
    # a drifted frozen file: the index guard fails, exit 3, nothing written
    pop = json.loads(Path(w.frozen).read_text(encoding="utf-8"))["KME-L"]
    drift = T.write_frozen(w.dir / "frozen-drift.json", **{"KME-L": dict(pop, calls=pop["calls"] + 1)})
    cert3 = w.dir / "c-drift.json"
    rc3, out3, err3 = run_certify(w, cert3, frozen=drift)
    drift_ok = rc3 == kp.EXIT_UNMEASURED and "verdict=UNMEASURED" in out3 and not cert3.exists() and "DRIFTED" in err3
    # a certificate may not be written inside a scanned root
    inside = w.projects / "cert-inside.json"
    rc4, _o, err4 = run_certify(w, inside)
    inside_ok = rc4 == kp.EXIT_USAGE and not inside.exists()
    ok = ok_main and swap_ok and drift_ok and inside_ok
    return ok, (f"certify rc={rc} selected={c.get('selected', {}).get('sessions')} shadow={c.get('shadow')}; swapped "
                f"selection rc={rc2} names k1+n1={swap_ok} written={cert2.exists()}; drifted frozen rc={rc3} "
                f"written={cert3.exists()}; cert inside root rc={rc4}; err={err[-100:]}")


def g_keys_four():
    w = World("k4", preserved=True)
    cert = w.cert_for()
    c = json.loads(cert.read_text(encoding="utf-8")) if cert.exists() else {}
    metric = (c.get("keys") or {}).get("metric") or {}
    pres = str(w.files["preserved"])
    shape_ok = (c.get("schema") == "kmep-cert/1" and len(c["keys"]["parser"]) == 64
                and set(metric) == {"population", "D", "E", "F", "G", "H", "I", "L"}
                and all(len(v) == 64 for v in metric.values())
                and c["index"]["attr_version"] == "1" and len(c["index"]["pattern_set"]) == 64
                and list(c["uncovered"]) == [pres]
                and c["question"]["roots"] == [os.path.realpath(str(w.projects))])
    r1 = go(w, "auto", ["--index-db", str(w.db)])
    rec = r1["rec"]
    run_ok = (r1["rc"] == 0 and rec and rec["plan_taken"] == "index" and rec["keys"] == c["keys"]
              and rec["metric_changed"] == [] and rec["read_set"]["stale"] == [])
    # the certificate vouches for the `_preserved` file by its exact (size, mtime_ns): a change to it is stale
    with open(pres, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user", "timestamp": T.ts(17), "message": {"role": "user", "content": "more"}}) + "\n")
    r2 = go(w, "auto", ["--index-db", str(w.db)])
    touch_ok = (r2["rc"] == 0 and r2["rec"]["plan_taken"] == "index"
                and r2["rec"]["read_set"]["stale"] == [f"{IN_SCOPE}/_preserved"])
    ok = shape_ok and run_ok and touch_ok
    return ok, (f"cert keys parser={str(c.get('keys', {}).get('parser'))[:12]} metric keys={sorted(metric)} attr="
                f"{c.get('index', {}).get('attr_version')} uncovered={[os.path.basename(p) for p in c.get('uncovered', {})]}; "
                f"index run keys==cert={bool(rec) and rec['keys'] == c.get('keys')} metric_changed="
                f"{rec and rec['metric_changed']} stale={rec and rec['read_set']['stale']}; after touching the "
                f"preserved file stale={r2['rec'] and r2['rec']['read_set']['stale']}")


def g_stale_parser():
    w = World("sp")
    w.cert_for()
    digest_clean = kp.selection_parser_digest()
    ctl = go(w, "auto", ["--index-db", str(w.db)])
    scoped = w.measure("scoped")
    with parser_patch(w):
        digest_mut = kp.selection_parser_digest()
        res = go(w, "auto", ["--index-db", str(w.db)])
        forced = go(w, "challenger", ["--index-db", str(w.db)])
    d = res["rec"]["deopt"] if res["rec"] else None
    ok = (digest_clean != digest_mut and ctl["rec"]["plan_taken"] == "index" and ctl["rec"]["deopt"] is None
          and d and d["guard"] == "parser" and digest_clean[:12] in d["reason"] and digest_mut[:12] in d["reason"]
          and res["rec"]["plan_taken"] == "scoped" and res["rc"] == 0 and len(scoped[3]) == 1
          and masked_of(res) == mask(*load(scoped[3][0]))
          and forced["rc"] == 3 and not forced["files"])
    return ok, (f"digest {digest_clean[:12]} -> {digest_mut[:12]}; control taken={ctl['rec']['plan_taken']}; "
                f"auto deopt={d and d['guard']} ({d and d['reason'][:80]}) taken={res['rec']['plan_taken']} output equals "
                f"scoped={masked_of(res) == mask(*load(scoped[3][0]))}; forced challenger rc={forced['rc']} files="
                f"{len(forced['files'])}")


def g_stale_metric():
    w = World("sm")
    w.cert_for()
    ctl = go(w, "auto", ["--index-db", str(w.db)])
    with patch_kme_pillars_text('H_DEFINITION = ("verification:', 'H_DEFINITION = ("verification (changed):'):
        one = go(w, "auto", ["--index-db", str(w.db)])
    with patch_kme_pillars_text('WEIGHTS = {"input": 1.0,', 'WEIGHTS = {"input": 1.5,'):
        many = go(w, "auto", ["--index-db", str(w.db)])
        forced = go(w, "challenger", ["--index-db", str(w.db)])
    want_many = ["D", "E", "F", "G", "H", "I", "L"]
    dm = many["rec"]["deopt"]
    ok = (ctl["rec"]["metric_changed"] == [] and ctl["rec"]["plan_taken"] == "index"
          and one["rec"]["metric_changed"] == ["H"] and one["rec"]["plan_taken"] == "index" and one["rec"]["deopt"] is None
          and one["rc"] == 0
          and many["rec"]["metric_changed"] == want_many and dm and dm["guard"] == "metric"
          and many["rec"]["plan_taken"] == "scoped" and forced["rc"] == 3 and not forced["files"])
    return ok, (f"control metric_changed={ctl['rec']['metric_changed']}; H_DEFINITION changed -> "
                f"{one['rec']['metric_changed']} taken={one['rec']['plan_taken']}; WEIGHTS changed -> "
                f"{many['rec']['metric_changed']} deopt={dm and dm['guard']} taken={many['rec']['plan_taken']}; forced "
                f"challenger rc={forced['rc']}")


def g_attr_version():
    w = World("av")
    w.cert_for()
    ctl = go(w, "auto", ["--index-db", str(w.db)])
    ux = kp._usage_index()
    with patched_attr(ux, "ATTR_VERSION", ux.ATTR_VERSION + 1):
        res = go(w, "auto", ["--index-db", str(w.db)])
        forced = go(w, "challenger", ["--index-db", str(w.db)])
    d = res["rec"]["deopt"]
    ok = (ctl["rec"]["plan_taken"] == "index" and d and d["guard"] == "attribution" and "attribution version" in d["reason"]
          and res["rec"]["plan_taken"] == "scoped" and forced["rc"] == 3 and not forced["files"])
    return ok, (f"control taken={ctl['rec']['plan_taken']}; ATTR_VERSION+1 -> deopt {d and d['guard']}: "
                f"{d and d['reason']}; forced rc={forced['rc']}")


def db_copy(w, name, sql):
    """A copy of the fixture index with one statement applied (the clean index and its certificate stay as they are)."""
    d = w.dir / name
    d.mkdir()
    dst = d / "index.sqlite"
    shutil.copyfile(w.db, dst)
    con = sqlite3.connect(dst)
    try:
        con.execute(sql)
        con.commit()
    finally:
        con.close()
    return dst


def g_pattern_drift():
    w = World("pd")
    drift = db_copy(w, "drift", "UPDATE meta SET v='" + "0" * 64 + "' WHERE k='pattern_set'")
    res = go(w, "auto", ["--index-db", str(drift)])
    d = res["rec"]["deopt"]
    ok = d and d["guard"] == "population" and "pattern set differs" in d["reason"] and res["rec"]["plan_taken"] == "scoped"
    return ok, f"altered meta pattern_set -> deopt {d and d['guard']}: {d and d['reason'][:140]}"


def g_cert_guards():
    w = World("cg")
    rows = {}
    rows["missing"] = go(w, "auto", ["--index-db", str(w.db), "--cert", str(w.dir / "no-such-cert.json")])
    other_pf = w.cert_for(pf=None, frozen=w.frozen_global, cross=True)
    rows["project_filter"] = go(w, "auto", ["--index-db", str(w.db), "--cert", str(other_pf)])
    other_until = w.cert_for(until="2026-10-03T12:00:00Z")
    rows["until"] = go(w, "auto", ["--index-db", str(w.db), "--cert", str(other_until)])
    want = {"missing": "cert_missing", "project_filter": "question.project_filter", "until": "question.until"}
    seen = {k: (r["rec"]["deopt"]["guard"], r["rec"]["deopt"]["reason"]) for k, r in rows.items()}
    ok = (Path(other_pf).exists() and Path(other_until).exists()
          and all(g == "certificate" and want[k] in reason for k, (g, reason) in seen.items())
          and all(r["rec"]["plan_taken"] == "scoped" for r in rows.values()))
    return ok, "; ".join(f"{k}: {g} {reason[:70]}" for k, (g, reason) in seen.items())


def _closure(defs, roots):
    """Module-level names reachable from `roots` through ast Name references (and `kp.<name>` attribute reads)."""
    seen, todo = set(), list(roots)
    while todo:
        c = todo.pop()
        if c in seen or c not in defs:
            continue
        seen.add(c)
        for x in ast.walk(defs[c]):
            if isinstance(x, ast.Name):
                todo.append(x.id)
    return seen


def _module_defs(rel):
    defs = {}
    for node in ast.parse((REPO / rel).read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defs[node.name] = node
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defs[t.id] = node
    return defs


INFRA = {"PillarObserver", "population", "weighted", "parse_instant", "REPO", "_META_CACHE", "_load_redact",
         "_located_block", "_match", "_utcnow", "plane_name", "fmt_instant", "INSTRUMENT", "PILLAR", "command_string"}


def _uncovered_names(listed, roots_by_rel):
    """Names a definition reads (transitively) that its list does not carry: a dependency whose change the key would
    never see."""
    missing = {}
    for rel, roots in roots_by_rel.items():
        need = _closure(_module_defs(rel), roots) - INFRA
        have = {n for r, names in listed for n in names if r == rel}
        if need - have:
            missing[rel] = sorted(need - have)
    return missing


def g_metric_coverage():
    """The METRIC_DEFINITIONS lists are curated; this gate DISCOVERS what each observer reads and checks the lists
    carry all of it, so a dependency added later cannot sit outside the key (PR-COVERAGE-BY-CONSTRUCTION-001)."""
    kp_rel, kr_rel = kp._KP_REL, kp._KR_REL
    roots = {"D": "DObserver", "E": "EObserver", "F": "FObserver", "G": "GObserver", "H": "HObserver", "I": "IObserver"}
    gaps = {}
    for key, cls in roots.items():
        miss = _uncovered_names(kp.METRIC_DEFINITIONS[key], {kp_rel: [cls]})
        if miss:
            gaps[key] = miss
    # L: kme_replay names, then the kme_pillars names they read through `kp.<name>`
    kr_defs = _module_defs(kr_rel)
    l_roots = ["rank_result", "RereadObserver", "RolloverObserver", "RetryObserver"]
    kr_need = _closure(kr_defs, l_roots)
    kp_names = set()
    for n in kr_need:
        for x in ast.walk(kr_defs[n]):
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "kp":
                kp_names.add(x.attr)
    kp_need = _closure(_module_defs(kp_rel), kp_names)
    have_kr = {n for r, names in kp.METRIC_DEFINITIONS["L"] for n in names if r == kr_rel}
    have_kp = {n for r, names in kp.METRIC_DEFINITIONS["L"] for n in names if r == kp_rel}
    miss_l = {"kme_replay": sorted(kr_need - INFRA - have_kr), "kme_pillars": sorted(kp_need - INFRA - have_kp)}
    if any(miss_l.values()):
        gaps["L"] = miss_l
    # population + selection rules: everything population() and make_keep() read is in the population key or in the
    # selection names
    sel_need = _closure(_module_defs(kp_rel), ["population", "make_keep"]) - {"population", "make_keep"}
    covered = set(kp.SELECTION_NAMES) | {n for _r, names in kp.METRIC_DEFINITIONS["population"] for n in names}
    if sel_need - covered:
        gaps["population"] = sorted(sel_need - covered)
    # every listed name exists (a stale name would silently read as 'missing' on both sides of every comparison)
    absent = {k: [n for rel, names in parts for n, seg in kp._module_segments(rel, names) if seg is None]
              for k, parts in kp.METRIC_DEFINITIONS.items()}
    absent = {k: v for k, v in absent.items() if v}
    absent_sel = [n for n, seg in kp._module_segments(kp._KP_REL, kp.SELECTION_NAMES) if seg is None]
    # control: the same check, with one dependency dropped from H's list, must name it
    trimmed = [(rel, tuple(n for n in names if n != "VERIFY_CMD_RE")) for rel, names in kp.METRIC_DEFINITIONS["H"]]
    control = _uncovered_names(trimmed, {kp_rel: ["HObserver"]})
    ctl_ok = control.get(kp_rel) == ["VERIFY_CMD_RE"]
    ok = not gaps and not absent and not absent_sel and ctl_ok
    return ok, (f"uncovered dependencies={gaps or 'none'}; listed names missing from source={absent or 'none'}; "
                f"selection names missing={absent_sel or 'none'}; control (VERIFY_CMD_RE dropped from H) -> {control}")

# --------------------------------------------------------------------------- gates: closure, IN-04, shadow (plan 03, task 2)
def append_line(path, obj):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj) + "\n")


def kme_text_line(t):
    """An assistant line that mentions KMEIP but carries no usage: it changes the file's bytes (so the source is stale)
    and gives the classifier something to read, yet the session stays unselected and no call is added."""
    return {"type": "assistant", "timestamp": t, "message": {"role": "assistant",
            "content": [{"type": "text", "text": "touching the KMEIP map again"}]}}


def g_stale_source():
    w = World("ss", n2=True)
    w.cert_for()
    sel = selected_transcripts(w)
    ctl = go(w, "auto", ["--index-db", str(w.db)])
    ctl_ok = (ctl["rc"] == 0 and ctl["rec"]["plan_taken"] == "index" and ctl["rec"]["read_set"]["stale"] == []
              and set(ctl["opened"]) == sel)
    append_line(w.files["n1"], kme_text_line(T.ts(13)))
    res = go(w, "auto", ["--index-db", str(w.db)])
    champ = w.measure(None)
    rec = res["rec"]
    n1, n2 = str(w.files["n1"]), str(w.files["n2"])
    ok = (ctl_ok and res["rc"] == 0 and rec["plan_taken"] == "index" and rec["deopt"] is None
          and rec["read_set"]["stale"] == [f"{IN_SCOPE}/n1"]
          and set(res["opened"]) == sel | {n1} and n2 not in set(res["opened"]) and str(w.files["c1"]) not in set(res["opened"])
          and rec["read_set"]["sessions"] == 2 and rec["read_set"]["files"] == 3
          and len(champ[3]) == 1 and masked_of(res) == mask(*load(champ[3][0])))
    return ok, (f"control: taken={ctl['rec']['plan_taken']} stale={ctl['rec']['read_set']['stale']} opened="
                f"{names(ctl['opened'])}; after appending to n1: stale={rec['read_set']['stale']} opened="
                f"{names(res['opened'])} (n2 untouched, never opened) output equals champion on the modified tree="
                f"{masked_of(res) == mask(*load(champ[3][0]))}")


def g_stale_new_file():
    w = World("snf")
    w.cert_for()
    # (a) a new non-KME session appears after certification: read, classified in-process, output equals the champion's
    n3 = T.Fx(w.root, project=IN_SCOPE, session="n3")
    n3.human("rename the helper", T.ts(18))
    n3.assistant("n3a", "rn3a", (2, 30, 300, 7), T.ts(19))
    a = go(w, "auto", ["--index-db", str(w.db)])
    champ_a = w.measure(None)
    a_ok = (a["rc"] == 0 and a["rec"]["plan_taken"] == "index" and a["rec"]["read_set"]["stale"] == [f"{IN_SCOPE}/n3"]
            and str(n3.path.resolve()) in set(a["opened"]) and str(w.files["n1"]) not in set(a["opened"])
            and masked_of(a) == mask(*load(champ_a[3][0])))
    # (b) an indexed file vanishes: its session is stale too (and nothing is opened for it)
    os.remove(w.files["n1"])
    b = go(w, "auto", ["--index-db", str(w.db)])
    champ_b = w.measure(None)
    b_ok = (b["rc"] == 0 and b["rec"]["plan_taken"] == "index"
            and b["rec"]["read_set"]["stale"] == [f"{IN_SCOPE}/n1", f"{IN_SCOPE}/n3"]
            and masked_of(b) == mask(*load(champ_b[3][0])))
    # (c) a new session that the champion classifier DOES select: the frozen population no longer reproduces, so the
    # shadow guard refuses (auto deopts to the scoped tier, challenger exits 3); nothing is served from the index
    w2 = World("snf2")
    w2.cert_for()
    k2 = T.Fx(w2.root, project=IN_SCOPE, session="k2")
    _kme_session(k2, "q", 30)
    c = go(w2, "auto", ["--index-db", str(w2.db)])
    scoped_c = w2.measure("scoped")
    forced = go(w2, "challenger", ["--index-db", str(w2.db)])
    dc = c["rec"]["deopt"]
    c_ok = (c["rec"]["plan_taken"] == "scoped" and dc and dc["guard"] == "shadow" and "population" in dc["reason"]
            and masked_of(c) == mask(*load(scoped_c[3][0])) and forced["rc"] == 3 and not forced["files"]
            and forced["rec"]["deopt"]["guard"] == "shadow")
    ok = a_ok and b_ok and c_ok
    return ok, (f"(a) new non-KME file: stale={a['rec']['read_set']['stale']} equal to champion={a_ok}; (b) file vanished: "
                f"stale={b['rec']['read_set']['stale']} equal={b_ok}; (c) new KME session: auto deopt={dc and dc['guard']} "
                f"({dc and dc['reason'][:70]}) taken={c['rec']['plan_taken']} forced rc={forced['rc']}")


def g_in04_no_first_ts():
    w = World("in4", z1=True)
    w.cert_for()
    res = go(w, "auto", ["--index-db", str(w.db)])
    champ = w.measure(None)
    rec = res["rec"]
    z1 = str(w.files["z1"])
    guard = next((g for g in rec["guards"] if g["guard"] == "no_first_ts"), {})
    plain = World("in4b")
    plain.cert_for()
    ctl = go(plain, "auto", ["--index-db", str(plain.db)])
    ctl_guard = next((g for g in ctl["rec"]["guards"] if g["guard"] == "no_first_ts"), {})
    ok = (res["rc"] == 0 and rec["plan_taken"] == "index" and rec["read_set"]["no_first_ts"] == [f"{IN_SCOPE}/z1"]
          and "1 session(s)" in guard.get("reason", "") and "IN-04" in guard.get("reason", "")
          and z1 in set(res["opened"]) and masked_of(res) == mask(*load(champ[3][0]))
          and ctl["rec"]["read_set"]["no_first_ts"] == [] and "0 session(s)" in ctl_guard.get("reason", ""))
    return ok, (f"IN-04 session z1: no_first_ts={rec['read_set']['no_first_ts']} guard='{guard.get('reason', '')[:80]}' "
                f"opened z1={z1 in set(res['opened'])}; without it: {ctl['rec']['read_set']['no_first_ts']} "
                f"'{ctl_guard.get('reason', '')[:40]}'")


def copy_root(w, name):
    """A byte-identical copy of the fixture projects tree at another path (the index was built over the original)."""
    dst = w.dir / name / "projects"
    shutil.copytree(w.projects, dst)
    return dst


def cert_with_roots(w, roots, name="cert-roots.json"):
    c = json.loads(Path(w.cert_for()).read_text(encoding="utf-8"))
    c["question"]["roots"] = sorted(os.path.realpath(str(r)) for r in roots)
    p = w.dir / name
    p.write_text(json.dumps(c), encoding="utf-8")
    return p


def g_root_not_indexed():
    w = World("rni")
    root2 = copy_root(w, "root2")
    cert_p = w.dir / "cert-r2.json"
    rc_c, out_c, err_c = run_certify(w, cert_p, projects=root2)
    forged = cert_with_roots(w, [root2])
    res = go(w, "auto", ["--index-db", str(w.db), "--cert", str(forged)], projects=root2)
    scoped = w.measure("scoped", projects=root2)
    forced = go(w, "challenger", ["--index-db", str(w.db), "--cert", str(forged)], projects=root2)
    d = res["rec"]["deopt"]
    # control: the original root with its own certificate is served by the index
    ctl = go(w, "auto", ["--index-db", str(w.db)])
    ok = (rc_c == kp.EXIT_UNMEASURED and "root_not_indexed" in err_c and not cert_p.exists()
          and d and d["guard"] == "watermark" and d["reason"].startswith("root_not_indexed")
          and res["rec"]["plan_taken"] == "scoped" and masked_of(res) == mask(*load(scoped[3][0]))
          and forced["rc"] == 3 and not forced["files"] and ctl["rec"]["plan_taken"] == "index")
    return ok, (f"certify over a root the index never saw: rc={rc_c} written={cert_p.exists()}; run with a forged "
                f"certificate: deopt {d and d['guard']}: {d and d['reason'][:70]}; forced rc={forced['rc']}; "
                f"control taken={ctl['rec']['plan_taken']}")


def g_deopt_logged():
    w = World("dl")
    good = w.cert_for()
    db4 = db_copy(w, "schema4", "UPDATE meta SET v='4' WHERE k='schema_version'")
    dbpe = db_copy(w, "parse-err", "UPDATE files SET parse_errors=1 WHERE path LIKE '%/n1.jsonl'")
    pop = json.loads(Path(w.frozen).read_text(encoding="utf-8"))["KME-L"]
    drift = T.write_frozen(w.dir / "frozen-drift.json", **{"KME-L": dict(pop, calls=pop["calls"] + 1)})
    root2 = copy_root(w, "root2")
    forged = cert_with_roots(w, [root2])
    ux = kp._usage_index()
    db = str(w.db)
    rows = [  # (row, guard, reason prefix, extra flags, frozen, projects, patch)
        ("index_open/missing", "index_open", "index_missing", ["--index-db", str(w.dir / "gone.sqlite")], None, None, None),
        ("index_open/schema4", "index_open", "schema: 4", ["--index-db", str(db4)], None, None, None),
        ("population/DRIFTED", "population", "population: DRIFTED", ["--index-db", db, "--cert", str(good)], drift, None, None),
        ("population/UNMEASURED", "population", "population: UNMEASURED", ["--index-db", str(dbpe)], None, None, None),
        ("certificate", "certificate", "cert_missing", ["--index-db", db, "--cert", str(w.dir / "none.json")], None, None, None),
        ("parser", "parser", "selection parser digest differs", ["--index-db", db], None, None, lambda: parser_patch(w)),
        ("attribution", "attribution", "attribution version differs", ["--index-db", db], None, None,
         lambda: patched_attr(ux, "ATTR_VERSION", ux.ATTR_VERSION + 1)),
        ("metric", "metric", "population definition differs", ["--index-db", db], None, None,
         lambda: patch_kme_pillars_text('WEIGHTS = {"input": 1.0,', 'WEIGHTS = {"input": 3.0,')),
        ("watermark/root_not_indexed", "watermark", "root_not_indexed", ["--index-db", db, "--cert", str(forged)], None,
         root2, None),
        ("shadow", "shadow", "selection differs", ["--index-db", db], None, None,
         lambda: swapped_selection(select_extra="n1")),
    ]
    out, bad = [], []
    for name, guard, prefix, extra, frozen, projects, patch in rows:
        with contextlib.ExitStack() as st:
            if patch:
                st.enter_context(patch())
            auto = go(w, "auto", extra, frozen=frozen, projects=projects)
            forced = go(w, "challenger", extra, frozen=frozen, projects=projects)
        scoped = w.measure("scoped", frozen=frozen, projects=projects)
        d = (auto["rec"] or {}).get("deopt")
        row_ok = (d is not None and d["guard"] == guard and d["reason"].startswith(prefix)
                  and auto["rec"]["plan_taken"] in ("scoped", "global") and auto["files"] and scoped[3]
                  and masked_of(auto) == mask(*load(scoped[3][0]))
                  and forced["rc"] == 3 and not forced["files"] and forced["rec"]["plan_taken"] == "refused"
                  and forced["rec"]["deopt"]["guard"] == guard)
        out.append(f"{name}:{'ok' if row_ok else 'BAD'}")
        if not row_ok:
            bad.append((name, d, auto["rc"], forced["rc"]))
    ctl = go(w, "auto", ["--index-db", db])
    ctl_ok = ctl["rc"] == 0 and ctl["rec"]["plan_taken"] == "index" and ctl["rec"]["deopt"] is None
    ok = not bad and ctl_ok
    return ok, (f"guards {len(rows)}/10 [{', '.join(out)}] control (all green): taken={ctl['rec']['plan_taken']} "
                f"deopt={ctl['rec']['deopt']}" + (f"; failing {bad}" if bad else ""))


GATES = [
    ("V-KMEC-SCAN-PROJECT-DEFAULT", g_scan_project_default),
    ("V-KMEC-TRACER-D-E2E", g_tracer_d_e2e),
    ("V-KMEC-INDEX-READ-ONLY", g_index_read_only),
    ("V-KMEC-PLAN-ORDER", g_plan_order),
    ("V-KMEC-CROSS-PROJECT-EXPLICIT", g_cross_project_explicit),
    ("V-KMEC-KS4-FORCED", g_ks4_forced),
    ("V-KMEC-PATH-LOG", g_path_log),
    ("V-KMEC-REPLAY-PLAN", g_replay_plan),
    ("V-KMEC-CERTIFY-SHADOW", g_certify_shadow),
    ("V-KMEC-KEYS-FOUR", g_keys_four),
    ("V-KMEC-STALE-PARSER", g_stale_parser),
    ("V-KMEC-STALE-METRIC", g_stale_metric),
    ("V-KMEC-ATTR-VERSION", g_attr_version),
    ("V-KMEC-PATTERN-DRIFT", g_pattern_drift),
    ("V-KMEC-CERT-GUARDS", g_cert_guards),
    ("V-KMEC-METRIC-COVERAGE", g_metric_coverage),
    ("V-KMEC-STALE-SOURCE", g_stale_source),
    ("V-KMEC-STALE-NEW-FILE", g_stale_new_file),
    ("V-KMEC-IN04-NO-FIRST-TS", g_in04_no_first_ts),
    ("V-KMEC-ROOT-NOT-INDEXED", g_root_not_indexed),
    ("V-KMEC-DEOPT-LOGGED", g_deopt_logged),
]


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    bad = [r for r in RESULTS if r[0] != "PASS"]
    return 0 if not bad else 1


# --------------------------------------------------------------------------- real-corpus gates (plan 02-04)
REAL_CORPUS = "/home/kobii/kme-corpus/projects"
REAL_INDEX = "/home/kobii/ao-scratch/p1/cold.sqlite"
REAL_SCRATCH = "/home/kobii/ao-scratch/p2"
REAL_FILTER = "KobiiCraft-Core-Files|kme-wt-arena2"
REAL_FREEZE = "2026-10-03T16:13:37Z"
REAL_COMMITTED = REPO / "vault" / "programs" / "incremental-cognition" / "measurements"
REAL_TIMEOUT = 590
FORBID_RX = "(?i)costaluz"
REAL_STATE: dict = {}


def real_question(until: str = "auto", flt: str = REAL_FILTER) -> list:
    return ["--denominator", "KME-L", "--until", until, "--expand", "--root", REAL_CORPUS, "--project-filter", flt]


def real_prereq() -> str:
    """'' when the real inputs exist, else the reason the real gates cannot run."""
    if not os.path.isdir(REAL_CORPUS):
        return f"corpus absent: {REAL_CORPUS}"
    if not os.path.isfile(REAL_INDEX):
        return f"index absent: {REAL_INDEX}"
    return ""


def corpus_manifest(root: str = REAL_CORPUS) -> dict:
    """sha256 over the sorted `size mtime_ns relpath` lines of an lstat pass; no file is opened."""
    lines = []
    for d, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            st = os.lstat(p)
            lines.append("%d %d %s" % (st.st_size, st.st_mtime_ns, os.path.relpath(p, root)))
    lines.sort()
    body = ("\n".join(lines) + "\n").encode("utf-8")
    return {"files": len(lines), "bytes": sum(int(x.split(" ", 1)[0]) for x in lines),
            "sha256": hashlib.sha256(body).hexdigest()}


def file_identity(path: str = REAL_INDEX) -> dict:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    st = os.stat(path)
    side = {sfx: os.path.exists(path + sfx) for sfx in ("-wal", "-shm", "-journal")}
    return {"sha256": h.hexdigest(), "mtime_ns": st.st_mtime_ns, "size": st.st_size, "sidecars": side}


def sh(argv: list, timeout: int = REAL_TIMEOUT) -> dict:
    """Run one command from the repo root; {argv, rc, out, err, wall_s}. A timeout is rc -9, never a success."""
    t0 = time.monotonic()
    try:
        cp = subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)
        rc, out, err = cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired as exc:
        rc = -9
        out = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = f"TIMEOUT after {timeout}s"
    return {"argv": argv, "rc": rc, "out": out, "err": err, "wall_s": round(time.monotonic() - t0, 3)}


def py(script: str, *args) -> list:
    return [sys.executable, "-I", script, *args]


def real_run() -> dict:
    """The whole --real sequence, executed once; every real gate reads this record."""
    if REAL_STATE:
        return REAL_STATE
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Path(REAL_SCRATCH) / f"real-{stamp}"
    run.mkdir(parents=True, exist_ok=False)
    cert, plog, outd = run / "kmel.cert.json", run / "path.jsonl", run / "challenger"
    outd.mkdir()
    st = REAL_STATE
    st["run_dir"] = str(run)
    st["before"] = {"manifest": corpus_manifest(), "index": file_identity()}
    q = real_question()
    st["certify"] = sh(py("wiki/tools/kme_pillars.py", "certify", *q, "--index-db", REAL_INDEX, "--cert", str(cert)))
    plan = ["--plan", "challenger", "--index-db", REAL_INDEX, "--cert", str(cert), "--path-log", str(plog),
            "--out-dir", str(outd)]
    certified = st["certify"]["rc"] == 0 and cert.is_file()
    if certified:
        st["all"] = sh(py("wiki/tools/kme_pillars.py", "all", *q, *plan))
        st["rank"] = sh(py("wiki/tools/kme_replay.py", "rank", *q, *plan))
        st["compare"] = sh(py("tools/kme_equivalence.py", "compare", "--candidate", str(outd),
                              "--committed", str(REAL_COMMITTED)))
    st["perturb"] = sh(py("tools/kme_equivalence.py", "selftest-perturb", "--committed", str(REAL_COMMITTED)))
    st["after"] = {"manifest": corpus_manifest(), "index": file_identity()}
    st["cert_path"], st["path_log"], st["out_dir"] = str(cert), str(plog), str(outd)
    (run / "real-run.json").write_text(json.dumps(st, indent=1, sort_keys=True), encoding="utf-8")
    return st


def g_real_certified():
    st = real_run()
    c = st["certify"]
    doc = json.loads(Path(st["cert_path"]).read_text(encoding="utf-8")) if Path(st["cert_path"]).is_file() else {}
    sel, sh_ = doc.get("selected", {}), doc.get("shadow", {})
    ok = (c["rc"] == 0 and "KMEP-CERT verdict=CERTIFIED" in c["out"] and sel.get("sessions") == 102
          and sh_.get("agree") is True and sh_.get("champion_selected") == 102 and sh_.get("index_selected") == 102)
    return ok, (f"rc={c['rc']} {c['out'].strip()} selected={sel.get('sessions')} shadow={sh_} "
                f"wall_s={c['wall_s']} err={c['err'].strip()[:200]!r}")


def g_real_equiv():
    st = real_run()
    c = st.get("compare")
    if c is None:
        return False, "no compare: certify did not produce a certificate"
    lines = [x for x in c["out"].splitlines() if x.startswith("KMEQ")]
    ok = c["rc"] == 0 and "KMEQ_VERDICT=SAME same=7/7" in c["out"] and len(lines) == 8
    return ok, f"rc={c['rc']} " + " | ".join(x.split(" committed=")[0] for x in lines)


def g_real_sessions():
    st = real_run()
    got = {}
    for p in ke.PILLARS:
        fs = sorted(Path(st["out_dir"]).glob(f"{p}-KME-L-*.md"))
        got[p] = ke.sessions_of(ke.parse_json_block(fs[0].read_text(encoding="utf-8"))) if len(fs) == 1 else None
    return all(v == 568 for v in got.values()) and len(got) == 7, f"sessions_scanned={got}"


def g_real_h_verdicts():
    """H is SAME with a masked commit; the owner-verdict map of the candidate equals the committed one and is non-empty."""
    st = real_run()
    c = st.get("compare")
    if c is None:
        return False, "no compare"
    h = [x for x in c["out"].splitlines() if x.startswith("KMEQ pillar=H ")]
    fs = sorted(Path(st["out_dir"]).glob("H-KME-L-*.md"))
    cand = ke.h_verdict_map(ke.parse_json_block(fs[0].read_text(encoding="utf-8"))) if len(fs) == 1 else None
    comm = ke.h_verdict_map(ke.parse_json_block((REAL_COMMITTED / "H-KME-L-2026-10-05.md").read_text(encoding="utf-8")))
    ok = len(h) == 1 and "verdict=SAME" in h[0] and "verdict_map=SAME" in h[0] and bool(cand) and cand == comm
    return ok, (h[0].split(" committed=")[0] if h else "no H line") + f" verdict_map equal={cand == comm} map={cand}"


def g_real_perturb():
    c = real_run()["perturb"]
    return c["rc"] == 0 and "KMEQ_SELFTEST=PASS" in c["out"], f"rc={c['rc']} {c['out'].strip().splitlines()[-1:]}"


def g_real_index_path():
    """Two records, each plan_taken index, no deopt, nothing stale. The planned read set is the index-selected sessions
    plus, by design (02-03 IN-04), the sessions the index holds no first timestamp for, read raw; nothing else."""
    st = real_run()
    recs = read_log(st["path_log"])
    tools = [r.get("tool") for r in recs]
    cert = json.loads(Path(st["cert_path"]).read_text(encoding="utf-8")) if Path(st["cert_path"]).is_file() else {}
    n_sel = cert.get("selected", {}).get("sessions")
    ok = (len(recs) == 2 and tools == ["kme_pillars", "kme_replay"]
          and all(r.get("plan_taken") == "index" and r.get("deopt") is None
                  and r["read_set"].get("stale") == []
                  and r["read_set"]["sessions"] == n_sel + len(r["read_set"].get("no_first_ts") or [])
                  for r in recs))

    def brief(r):
        rs = r["read_set"]
        return (f"{r.get('tool')}.{r.get('subcommand')} plan_taken={r.get('plan_taken')} deopt={r.get('deopt')} "
                f"stale={rs.get('stale')} sessions={rs['sessions']} (selected {n_sel} + no_first_ts "
                f"{len(rs.get('no_first_ts') or [])}) files={rs['files']} bytes={rs['bytes']}")
    return ok, "; ".join(brief(r) for r in recs)


def g_real_readonly():
    st = real_run()
    b, a = st["before"], st["after"]
    ok = b["manifest"] == a["manifest"] and b["index"] == a["index"]
    return ok, (f"manifest before={b['manifest']['sha256'][:12]} after={a['manifest']['sha256'][:12]} "
                f"files={a['manifest']['files']}; index sha before={b['index']['sha256'][:12]} "
                f"after={a['index']['sha256'][:12]} mtime_ns equal={b['index']['mtime_ns'] == a['index']['mtime_ns']}")


REAL_GATES = [
    ("V-KMEC-REAL-CERTIFIED", g_real_certified),
    ("V-KMEC-EQUIV-REAL", g_real_equiv),
    ("V-KMEC-SESSIONS-SCANNED-568", g_real_sessions),
    ("V-KMEC-H-VERDICTS", g_real_h_verdicts),
    ("V-KMEC-EQUIV-PERTURB-REAL", g_real_perturb),
    ("V-KMEC-REAL-INDEX-PATH", g_real_index_path),
    ("V-KMEC-REAL-READONLY", g_real_readonly),
]


def run_real_gates(gates, prefix: str) -> int:
    """A real gate that could not run is a SKIP and the mode exits 1; it is never a pass."""
    why = real_prereq()
    for name, fn in gates:
        if why:
            record("SKIP", name, why)
        else:
            run_gate(name, fn)
    print(summary_line(prefix))
    bad = [r for r in RESULTS if r[0] != "PASS"]
    return 0 if not bad else 1


def run_real() -> int:
    return run_real_gates(REAL_GATES, "KMEC_REAL_PASS")


EXPO_STATE: dict = {}


def strace_args(label: str, trace_dir: Path, steps: list, ok_exit: int = 0) -> list:
    """argv of tools/strace_io_sum.py run: one traced repetition, no untraced walls, KME scope, CostaLuz forbidden."""
    a = py("tools/strace_io_sum.py", "run", "--label", label, "--repeat", "0", "--trace-repeat", "1",
           "--trace-dir", str(trace_dir), "--corpus-root", REAL_CORPUS, "--scope-regex", REAL_FILTER,
           "--forbid-regex", FORBID_RX, "--index-path", REAL_INDEX)
    if ok_exit:
        a += ["--ok-exit", "0", "--ok-exit", str(ok_exit)]
    for st in steps:
        a += ["--step", st]
    return a


def json_of(res: dict) -> dict:
    try:
        return json.loads(res["out"])
    except ValueError:
        return {}


def exposure_run() -> dict:
    """certify once, then two traced `population` runs: the challenger (KME-only) and the control (filter + CostaLuz)."""
    if EXPO_STATE:
        return EXPO_STATE
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Path(REAL_SCRATCH) / f"exposure-{stamp}"
    run.mkdir(parents=True, exist_ok=False)
    cert, plog = run / "kmel.cert.json", run / "pop-path.jsonl"
    st = EXPO_STATE
    st["run_dir"] = str(run)
    st["before"] = {"manifest": corpus_manifest(), "index": file_identity()}
    q = real_question()
    st["certify"] = sh(py("wiki/tools/kme_pillars.py", "certify", *q, "--index-db", REAL_INDEX, "--cert", str(cert)))
    if st["certify"]["rc"] == 0 and cert.is_file():
        pop = " ".join(["python3", "-I", "wiki/tools/kme_pillars.py", "population"] + [shlex.quote(x) for x in q]
                       + ["--plan", "challenger", "--index-db", REAL_INDEX, "--cert", str(cert),
                          "--path-log", str(plog)])
        st["challenger"] = sh(strace_args("challenger-population", run / "strace", [pop]))
        ctl = " ".join(["python3", "-I", "wiki/tools/kme_pillars.py", "population"]
                       + [shlex.quote(x) for x in real_question(REAL_FREEZE, REAL_FILTER + "|CostaLuz")]
                       + ["--plan", "scoped"])
        st["control"] = sh(strace_args("control-filter-costaluz", run / "strace", [ctl], ok_exit=3))
    st["after"] = {"manifest": corpus_manifest(), "index": file_identity()}
    st["cert_path"], st["path_log"] = str(cert), str(plog)
    (run / "exposure-run.json").write_text(json.dumps(st, indent=1, sort_keys=True), encoding="utf-8")
    return st


def _traced(res: dict) -> dict:
    j = json_of(res)
    t = (j.get("traced") or [{}])[0]
    return t if t.get("verdict") == "MEASURED" and not t.get("failed") else {}


def g_costaluz_zero_real():
    st = exposure_run()
    if "challenger" not in st:
        return False, "certify did not produce a certificate"
    ch, ct = _traced(st["challenger"]), _traced(st["control"])
    recs = read_log(st["path_log"])
    planned = recs[-1]["read_set"]["files"] if recs else None
    keys = ("forbidden_bytes", "forbidden_opens", "cross_project_bytes", "raw_bytes", "raw_files_opened",
            "unique_bytes", "index_bytes")
    half1 = (bool(ch) and ch["forbidden_bytes"] == 0 and ch["forbidden_opens"] == 0 and ch["cross_project_bytes"] == 0
             and ch["raw_files_opened"] == planned and len(recs) == 1 and recs[0].get("plan_taken") == "index")
    half2 = bool(ct) and ct["forbidden_bytes"] > 0
    return half1 and half2, (f"challenger {({k: ch.get(k) for k in keys} if ch else 'UNMEASURED/failed')} "
                             f"planned_files={planned}; control forbidden_bytes={ct.get('forbidden_bytes')} "
                             f"forbidden_opens={ct.get('forbidden_opens')} cross_project_bytes="
                             f"{ct.get('cross_project_bytes')} (halves: challenger={half1} control_fires={half2})")


def g_exposure_readonly():
    st = exposure_run()
    b, a = st["before"], st["after"]
    return b == a, (f"manifest before={b['manifest']['sha256'][:12]} after={a['manifest']['sha256'][:12]}; index sha "
                    f"before={b['index']['sha256'][:12]} after={a['index']['sha256'][:12]} "
                    f"mtime_ns equal={b['index']['mtime_ns'] == a['index']['mtime_ns']}")


EXPOSURE_GATES = [
    ("V-KMEC-COSTALUZ-ZERO-REAL", g_costaluz_zero_real),
    ("V-KMEC-EXPOSURE-READONLY", g_exposure_readonly),
]


def run_real_exposure() -> int:
    if real_prereq() == "" and not (shutil.which("strace") or os.path.exists("/usr/bin/strace")):
        for name, _fn in EXPOSURE_GATES:
            record("SKIP", name, "strace not found")
        print(summary_line("KMEC_EXPOSURE_PASS"))
        return 1
    return run_real_gates(EXPOSURE_GATES, "KMEC_EXPOSURE_PASS")


# --------------------------------------------------------------------------- mutation drill
# A guard that cannot fail proves nothing (RESEARCH Pitfall 9). Each mutant below breaks ONE mechanism of the challenger
# by replacing a kme_pillars / kme_token_audit attribute, and the gate(s) named beside it must turn red; the unmutated
# run must be green before and after. A mutant that survives means a guard no gate can tell from a working one.
GATE_FN = dict(GATES)
DRILL_GATES = [n for n, _ in GATES]


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


def _patch(mod, attr, value):
    saved = getattr(mod, attr)
    setattr(mod, attr, value)
    return lambda: setattr(mod, attr, saved)


def _m_watermark_never_stale():
    return _patch(kp, "_watermark", lambda ctx, state, cert: set())


def _m_watermark_all_stale():
    return _patch(kp, "_watermark", lambda ctx, state, cert: {(p, s) for (p, s, _z, _m) in state["disk"].values()})


def _m_parser_constant():
    return _patch(kp, "selection_parser_digest", lambda: "0" * 64)


def _m_attribution_skipped():
    return _patch(kp, "_check_attribution", lambda *a: None)


def _m_metric_constant():
    return _patch(kp, "metric_digests", lambda: {k: "0" * 64 for k in kp.METRIC_DEFINITIONS})


def _m_metric_changed_all():
    return _patch(kp, "_metric_changed", lambda cert_metric, live: list(kp.PILLAR_KEYS))


def _m_select_admits_all():
    return _patch(kp, "_make_select", lambda read_set, admitted: (lambda proj, sid, path: True))


def _m_refused_session_unregistered():
    real = kta.scan_project

    def mutant(pdir, observer=None, keep=None, select=None):
        if select is None:
            return real(pdir, observer=observer, keep=keep)
        touched = set()

        def spy(proj, sid, path):
            r = select(proj, sid, path)
            if r:
                touched.add((proj, sid))
            return r
        return [s for s in real(pdir, observer=observer, keep=keep, select=spy)
                if (s["project"], s["session"]) in touched]
    return _patch(kta, "scan_project", mutant)


def _m_deopt_not_recorded():
    real = kp._resolve

    def mutant(ctx, pillars, observer_factories=None):
        out = real(ctx, pillars, observer_factories)
        ctx["deopt"] = None
        return out
    return _patch(kp, "_resolve", mutant)


def _m_forced_challenger_falls_back():
    real = kp._resolve

    def mutant(ctx, pillars, observer_factories=None):
        if ctx.get("plan") == "challenger":
            ctx["plan"] = "auto"
        return real(ctx, pillars, observer_factories)
    return _patch(kp, "_resolve", mutant)


def _m_missing_scope_runs_global():
    real = kp._prepare

    def mutant(a, pillars):
        if getattr(a, "plan", "champion") in ("challenger", "auto") and getattr(a, "project_filter", None) is None:
            a.cross_project = True
        return real(a, pillars)
    return _patch(kp, "_prepare", mutant)


def _m_no_first_ts_dropped():
    return _patch(kp, "_no_first_ts_sessions", lambda until, state: set())


def _m_shadow_always_admits():
    return _patch(kp, "_shadow_check", lambda ctx, sc, access: None)


def _m_certify_skips_comparison():
    return _patch(kp, "_selection_agreement", lambda champion, index: (True, [], []))


def _m_index_read_write():
    return _patch(kp, "_open_index_ro", lambda path: kp._usage_index().connect(Path(path)))


MUTANTS = [
    ("M1 _watermark never reports a stale session", _m_watermark_never_stale, ["V-KMEC-STALE-SOURCE"]),
    ("M2 _watermark marks every session stale", _m_watermark_all_stale, ["V-KMEC-STALE-SOURCE"]),
    ("M3 selection_parser_digest is a constant", _m_parser_constant, ["V-KMEC-STALE-PARSER"]),
    ("M4 attribution version comparison skipped", _m_attribution_skipped, ["V-KMEC-ATTR-VERSION"]),
    ("M5 metric_digests are constants", _m_metric_constant, ["V-KMEC-STALE-METRIC"]),
    ("M6 metric_changed lists every pillar", _m_metric_changed_all, ["V-KMEC-STALE-METRIC"]),
    ("M7 the select callable admits every file", _m_select_admits_all, ["V-KMEC-TRACER-D-E2E"]),
    ("M8 a refused file's session is not registered", _m_refused_session_unregistered, ["V-KMEC-TRACER-D-E2E"]),
    ("M9 an auto deopt is recorded as null", _m_deopt_not_recorded, ["V-KMEC-DEOPT-LOGGED"]),
    ("M10 a forced challenger falls back to the scoped tier with exit 0", _m_forced_challenger_falls_back,
     ["V-KMEC-KS4-FORCED"]),
    ("M11 a missing scope without --cross-project runs global", _m_missing_scope_runs_global,
     ["V-KMEC-CROSS-PROJECT-EXPLICIT"]),
    ("M12 sessions without a first timestamp (IN-04) are not added", _m_no_first_ts_dropped,
     ["V-KMEC-IN04-NO-FIRST-TS"]),
    ("M13 the post-scan shadow guard always admits", _m_shadow_always_admits, ["V-KMEC-DEOPT-LOGGED"]),
    ("M14 certify skips the per-session comparison", _m_certify_skips_comparison, ["V-KMEC-CERTIFY-SHADOW"]),
    ("M15 the index is opened read-write through the usage_index connect helper", _m_index_read_write,
     ["V-KMEC-INDEX-READ-ONLY"]),
]


def run_drill() -> int:
    """Control first (every in-process gate green), each mutant applied and restored, then an unmutated rerun."""
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
    _argv = sys.argv[1:]
    if "--drill" in _argv:
        sys.exit(run_drill())
    elif "--real" in _argv:
        sys.exit(run_real())
    elif "--real-exposure" in _argv:
        sys.exit(run_real_exposure())
    else:
        sys.exit(run_all())
