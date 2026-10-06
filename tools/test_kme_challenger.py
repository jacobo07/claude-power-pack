#!/usr/bin/env python3
"""V-KMEC-* gates: the KME-L challenger access plan (autonomous-optimization phase 2, plan 01).

Hermetic: every fixture is a synthetic transcript tree plus a fixture usage index built here under a scratch
directory. Nothing outside it is read or written. A SKIP or an INCONCLUSIVE is printed and counted apart; it is never
a PASS and never part of the n/m denominator.

    python3 -I tools/test_kme_challenger.py       run every gate

Helpers of tools/test_kme_pillars.py (Fx, ts, write_frozen, run_main, scratch, CANARY) are imported, not copied.
"""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for _p in (str(HERE), str(REPO / "wiki" / "tools"), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kme_pillars as kp  # noqa: E402
import kme_replay as kr  # noqa: E402
import kme_token_audit as kta  # noqa: E402
import test_kme_pillars as T  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)

IN_SCOPE = "-home-x-core-fixture"
OUT_SCOPE = "-home-x-CostaLuz-fixture"


# --------------------------------------------------------------------------- gate plumbing
def record(status: str, gate: str, ev: str = "") -> None:
    RESULTS.append((status, gate, str(ev)))
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
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    n = sum(1 for r in counted if r[0] == "PASS")
    m = len(counted)
    sk = sum(1 for r in RESULTS if r[0] == "SKIP")
    inc = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"KMEC_PASS={n}/{m}  threshold={m}/{m}  skipped={sk}  inconclusive={inc}"


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


def challenger_fixture(root):
    """In scope (-home-x-core-fixture, no 'kme' in the name): k1 = KME by content (+ one subagent file), n1 = no KME
    signal. Out of scope (-home-x-CostaLuz-fixture): c1 = KME by content, so an unscoped run would select and open it.
    Returns {name: path} of every transcript file."""
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

    def __init__(self, tag="w"):
        self.dir = T.scratch(tag)
        self.root = self.dir / "fx"
        self.projects = self.root / "projects"
        self.files = challenger_fixture(self.root)
        self.db = build_index(self.root, self.dir / "ix" / "index.sqlite")
        self.out_n = 0
        self.frozen = self._champion_frozen()
        self.frozen_global = self._champion_frozen(pf=None, calls=5, sessions=3, name="frozen-global.json")

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

    def args(self, pillar="d", frozen=None, plan=None, extra=(), root_flags=True, pf="core-fixture"):
        a = [pillar, "--denominator", "KME-L", "--frozen-file", str(frozen or self.frozen)]
        if root_flags:
            a += ["--root", str(self.projects), "--expand"]
        if pf:
            a += ["--project-filter", pf]
        if plan:
            a += ["--plan", plan]
        return a + list(extra)

    def measure(self, plan=None, extra=(), pf="core-fixture", spy=True):
        """In-process run -> (rc, out, err, files written, opened transcript paths)."""
        outd = self.out()
        cmd = self.args("d", plan=plan, extra=list(extra) + ["--out-dir", str(outd)], pf=pf)
        if spy:
            with OpenSpy(self.projects) as sp:
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
             "sessions_registered", "index_db", "denominator", "project_filter", "until", "cross_project", "plane"}


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
    with OpenSpy(w.projects) as sp4:
        rc4, _o, err4 = T.run_main(w.args("d", frozen=w.frozen_global, plan="auto", pf=None,
                                          extra=["--index-db", str(w.db), "--cross-project", "--out-dir", str(outd)]))
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


GATES = [
    ("V-KMEC-SCAN-PROJECT-DEFAULT", g_scan_project_default),
    ("V-KMEC-TRACER-D-E2E", g_tracer_d_e2e),
    ("V-KMEC-INDEX-READ-ONLY", g_index_read_only),
    ("V-KMEC-PLAN-ORDER", g_plan_order),
    ("V-KMEC-CROSS-PROJECT-EXPLICIT", g_cross_project_explicit),
    ("V-KMEC-KS4-FORCED", g_ks4_forced),
    ("V-KMEC-PATH-LOG", g_path_log),
    ("V-KMEC-REPLAY-PLAN", g_replay_plan),
]


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    bad = [r for r in RESULTS if r[0] != "PASS"]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(run_all())
