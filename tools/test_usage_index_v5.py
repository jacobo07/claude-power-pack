#!/usr/bin/env python3
"""V-UX5-* gates for the usage_index v5 substrate (phase 1, pillar O).

Governing spec: vault/specs/autonomous-optimization.md.

Hermetic: every fixture lives in a temp dir; no model call, no corpus, never
~/.claude/projects. No pytest.

Paired-control contract: a refusal passes only when its admitting control is green.
  - the zero-reread migration gate is paired with two spy controls (a grown file and
    an index stamped below V2 must make the very same spy fire);
  - the empty-population refusal is paired with the one-session fixture that must be
    MEASURED with exact counts.

Module globals UX and TIS are what every gate group reads, so the mutation drill
(plan 01 task 3) can swap in a mutated copy of the module under test.
"""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import tis_observed as _tis_mod  # noqa: E402
import usage_index as _ux_mod  # noqa: E402

UX = _ux_mod
TIS = _tis_mod

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
WINCWD = "C:\\Users\\User\\Apps\\proj"
WINPATH = "C:\\Users\\User\\Apps\\proj\\x.py"

# The v5 shape, written out here (not read from the module under test).
V5_TABLES = ("call_files", "tool_events", "user_hits", "file_cwds", "file_attribution", "patterns")
V5_FILE_COLS = ("resolved", "store", "project", "archived", "session_key", "first_ts", "last_ts",
                "parse_errors", "error", "v5_from", "head_sha", "tail_sha", "content_id", "dup_of",
                "pat_ver")
V4_TABLES = ("files", "calls", "quota", "prompts", "spawns", "subagents")

PASS = FAIL = 0
_CUR: dict = {}
_QUIET = False


def gate(name: str, cond, evidence: str = "") -> bool:
    global PASS, FAIL
    cond = bool(cond)
    _CUR[name] = cond
    if not _QUIET:
        PASS += cond
        FAIL += not cond
        print(f"  {'PASS' if cond else 'FAIL'} {name}: {evidence}", flush=True)
    return cond


def guarded(name: str, fn) -> dict:
    """Run one gate group; a crash is a FAIL of its own, never a silent skip and never
    a reason to skip the later groups."""
    global _CUR
    _CUR = {}
    try:
        fn()
    except Exception as e:  # noqa: BLE001 -- a crash is a red gate
        gate(f"{name}-CRASH", False, f"{type(e).__name__}: {e}")
    return dict(_CUR)


# -- fixtures ------------------------------------------------------------------

def iso(h: float) -> str:
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def user_prompt(pid, h, sess, cwd=WINCWD) -> str:
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": sess,
                       "cwd": cwd, "origin": {"kind": "human"},
                       "message": {"role": "user", "content": "hello"}}) + "\n"


def asst(mid, h, sess, tools=(), cr=100, cwd=WINCWD, model="claude-opus-5-5") -> str:
    content = [{"type": "tool_use", "id": tid, "name": name, "input": inp}
               for tid, name, inp in tools]
    o = {"type": "assistant", "timestamp": iso(h), "sessionId": sess, "cwd": cwd,
         "message": {"id": mid, "model": model, "content": content,
                     "usage": {"input_tokens": 1, "cache_read_input_tokens": cr,
                               "cache_creation_input_tokens": 0, "output_tokens": 5}},
         "requestId": "r" + mid}
    return json.dumps(o) + "\n"


def user_result(h, sess, tid, body, is_error=False) -> str:
    return json.dumps({"type": "user", "timestamp": iso(h), "sessionId": sess,
                       "message": {"role": "user", "content": [
                           {"type": "tool_result", "tool_use_id": tid, "content": body,
                            "is_error": is_error}]}}) + "\n"


def canon(inp) -> str:
    return json.dumps(inp, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def one_session_store(root: Path) -> tuple[Path, Path]:
    """projects/C--p1/S1.jsonl: 2 calls (cr 100 each), a Read with a result, a Grep without."""
    proj = root / "projects"
    d = proj / "C--p1"
    d.mkdir(parents=True)
    f = d / "S1.jsonl"
    f.write_text(
        user_prompt("P1", 1, "S1")
        + asst("m1", 1.1, "S1", tools=[("tuR1", "Read", {"file_path": WINPATH})])
        + user_result(1.2, "S1", "tuR1", "abc")
        + asst("m2", 1.3, "S1", tools=[("tuG1", "Grep", {"pattern": "needle"})]),
        encoding="utf-8")
    return proj, f


def two_file_store(root: Path) -> tuple[Path, list[Path]]:
    """Two sessions in two project dirs, one unanswered Agent spawn (result_ts stays NULL)."""
    proj, f1 = one_session_store(root)
    with f1.open("a", encoding="utf-8") as fh:
        fh.write(asst("m3", 1.4, "S1", tools=[("tuA1", "Agent",
                                              {"subagent_type": "Explore", "prompt": "look"})]))
    d2 = proj / "C--p2"
    d2.mkdir()
    f2 = d2 / "S2.jsonl"
    f2.write_text(user_prompt("P2", 2, "S2") + asst("m4", 2.1, "S2", cr=50)
                  + asst("m5", 2.2, "S2", cr=60), encoding="utf-8")
    return proj, [f1, f2]


def downgrade_to_v4(con) -> None:
    """Make the index look like one written by v4 code: no v5 table, no v5 column."""
    for t in V5_TABLES:
        con.execute(f"DROP TABLE IF EXISTS {t}")
    have = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    for c in V5_FILE_COLS:
        if c in have:
            con.execute(f"ALTER TABLE files DROP COLUMN {c}")
    con.execute("DELETE FROM meta WHERE k='v5_migration'")
    con.execute("INSERT OR REPLACE INTO meta VALUES('schema_version', '4')")
    con.commit()


def snapshot(con) -> dict:
    return {"offsets": {r[0]: tuple(r[1:]) for r in
                        con.execute("SELECT path, offset, size, mtime_ns FROM files")},
            "counts": {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in V4_TABLES}}


class Spy:
    """Records every open() of a path under `root` (builtins.open, io.open, os.open)."""

    def __init__(self, root: Path):
        self.roots = {str(root), os.path.realpath(str(root))}
        self.opened: list[str] = []
        self._saved = None

    def _hit(self, p) -> None:
        if isinstance(p, (str, bytes, os.PathLike)):
            s = os.fsdecode(os.fspath(p))
            if any(s == r or s.startswith(r + os.sep) for r in self.roots):
                self.opened.append(s)

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


def make_v4(td: Path):
    """A store, indexed once, then downgraded to the v4 shape. -> (proj, db, files, snapshot)."""
    proj, files = two_file_store(td)
    db = td / "db" / "ix.sqlite"
    con = UX.connect(db)
    try:
        UX.refresh(con, proj, deadline_s=30)
        downgrade_to_v4(con)
        snap = snapshot(con)
        todo = con.execute("SELECT v FROM meta WHERE k='spawn_backfill'").fetchone()
    finally:
        con.close()
    return proj, db, files, snap, todo


# -- gate groups ---------------------------------------------------------------

def grp_schema() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _ = one_session_store(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            tables = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            cols = {x[1] for x in con.execute("PRAGMA table_info(files)")}
            ver = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()[0]
            gate("V-UX5-SCHEMA",
                 r["status"] == "OK" and set(V5_TABLES) <= tables and set(V5_FILE_COLS) <= cols
                 and ver == "5",
                 f"status={r['status']} missing tables={sorted(set(V5_TABLES) - tables)} "
                 f"missing files columns={sorted(set(V5_FILE_COLS) - cols)} schema_version={ver}")
        finally:
            con.close()


def grp_tool_event() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _ = one_session_store(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            q = ("SELECT tool, input_hash, input_bytes, path, result_bytes, result_chars, is_error, "
                 "result_off FROM tool_events WHERE tool_use_id=?")
            row = con.execute(q, ("tuR1",)).fetchone()
            n = con.execute("SELECT count(*) FROM tool_events WHERE tool_use_id='tuR1'").fetchone()[0]
            want = canon({"file_path": WINPATH})
            ok = (row is not None and n == 1 and row[0] == "Read"
                  and row[1] == hashlib.sha256(want.encode("utf-8")).hexdigest()[:16]
                  and len(row[1]) == 16 and row[2] == len(want.encode("utf-8"))
                  and row[3] == "C:/Users/User/Apps/proj/x.py"
                  and row[4] == 3 and row[5] == 3 and row[6] == 0 and row[7] is not None)
            gate("V-UX5-TOOL-EVENT", ok, f"rows={n} row={row}")
            row2 = con.execute(q, ("tuG1",)).fetchone()
            gate("V-UX5-TOOL-EVENT-NO-RESULT",
                 row2 is not None and row2[0] == "Grep" and row2[4] is None and row2[5] is None
                 and row2[3] is None,
                 f"a tool_use with no tool_result keeps result NULL (never 0): {row2}")
        finally:
            con.close()


def grp_occurrence() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        for proj_dir, sess, cr in (("C--p1", "S1", 100), ("C--p2", "S2", 150)):
            (proj / proj_dir).mkdir(parents=True)
            (proj / proj_dir / f"{sess}.jsonl").write_text(
                user_prompt("P" + sess, 1, sess) + asst("mdup", 1.1, sess, cr=cr),
                encoding="utf-8")
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            occ = con.execute("SELECT file, cr FROM call_files WHERE k='mdup|rmdup' ORDER BY file"
                              ).fetchall()
            calls = con.execute("SELECT count(*), max(cr) FROM calls WHERE k='mdup|rmdup'").fetchone()
            gate("V-UX5-OCCURRENCE",
                 len(occ) == 2 and sorted(c for _, c in occ) == [100, 150] and calls == (1, 150),
                 f"call_files rows={[(Path(f).name, c) for f, c in occ]} calls rows/max cr={calls}")
        finally:
            con.close()


def grp_migrate() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, snap, todo = make_v4(td)
        with Spy(proj) as spy:                        # connect() AND refresh() are both measured
            con = UX.connect(db)
            r = UX.refresh(con, proj, deadline_s=30)
        try:
            after = snapshot(con)
            bf = con.execute("SELECT v FROM meta WHERE k='spawn_backfill'").fetchone()
            legacy = con.execute("SELECT count(*) FROM files WHERE v5_from IS NOT NULL").fetchone()[0]
            mig = json.loads((con.execute("SELECT v FROM meta WHERE k='v5_migration'").fetchone()
                              or ["{}"])[0])
            ver = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()[0]
            unresolved = con.execute("SELECT count(*) FROM spawns WHERE result_ts IS NULL").fetchone()[0]
            gate("V-UX5-MIGRATE-ZERO-REREAD",
                 not spy.opened and r["status"] == "OK" and r.get("files_opened") == 0
                 and r.get("bytes_read") == 0 and r["calls_upserted"] == 0
                 and bf is not None and bf[0] == "[]" and unresolved >= 1
                 and after == snap and legacy == 0 and ver == "5" and mig.get("files_opened") == 0,
                 f"opens under the fixture root={len(spy.opened)} status={r['status']} "
                 f"files_opened={r.get('files_opened')} bytes_read={r.get('bytes_read')} "
                 f"upserted={r['calls_upserted']} spawn_backfill={bf and bf[0]} "
                 f"unanswered spawns={unresolved} snapshot equal={after == snap} "
                 f"files with v5_from set={legacy} v5_migration={mig} schema_version={ver}")
        finally:
            con.close()

    # Control 1: the spy fires when one file grows, on exactly that file.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, snap, _ = make_v4(td)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)          # migrate (zero reads), as above
            grown = files[1]
            old_off = snap["offsets"][str(grown)][0]
            line = asst("m6", 2.3, "S2", cr=70)
            with grown.open("a", encoding="utf-8") as fh:
                fh.write(line)
            with Spy(proj) as spy:
                r = UX.refresh(con, proj, deadline_s=30)
            v5_from = con.execute("SELECT v5_from FROM files WHERE path=?", (str(grown),)).fetchone()[0]
            gate("V-UX5-SPY-FIRES-ON-GROWTH",
                 [os.path.realpath(p) for p in spy.opened] == [os.path.realpath(str(grown))]
                 and r.get("files_opened") == 1 and r.get("bytes_read") == len(line.encode("utf-8"))
                 and v5_from == old_off,
                 f"opened={[Path(p).name for p in spy.opened]} files_opened={r.get('files_opened')} "
                 f"bytes_read={r.get('bytes_read')} appended={len(line.encode('utf-8'))} "
                 f"v5_from={v5_from} old offset={old_off}")
        finally:
            con.close()

    # Control 2: an index stamped below V2 re-reads every file, and the spy sees it.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, snap, _ = make_v4(td)
        raw = sqlite3.connect(str(db))
        raw.execute("INSERT OR REPLACE INTO meta VALUES('schema_version', '1')")
        raw.commit()
        raw.close()
        con = UX.connect(db)
        try:
            with Spy(proj) as spy:
                r = UX.refresh(con, proj, deadline_s=30)
            seen = {os.path.realpath(p) for p in spy.opened}
            want = {os.path.realpath(str(f)) for f in files}
            gate("V-UX5-SPY-FIRES-ON-V1",
                 want <= seen and r.get("files_opened") == len(files) and r.get("bytes_read", 0) > 0,
                 f"files re-read={len(want & seen)}/{len(want)} files_opened={r.get('files_opened')} "
                 f"bytes_read={r.get('bytes_read')}")
        finally:
            con.close()


def grp_population_empty() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        db = td / "db" / "ix.sqlite"
        con = UX.connect(db)
        try:
            pop = UX.population(con)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = UX.main(["population", "--db", str(db)])
            try:
                printed = json.loads(buf.getvalue()).get("verdict")
            except ValueError:
                printed = None
            # Also a migrated v5 index whose scope holds no file at all.
            empty_proj = td / "empty_projects"
            empty_proj.mkdir()
            UX.refresh(con, empty_proj, deadline_s=30)
            pop5 = UX.population(con)
            gate("V-UX5-EMPTY-REFUSES",
                 pop.get("verdict") == "UNMEASURED" and bool(pop.get("reasons"))
                 and rc == 3 and printed == "UNMEASURED"
                 and pop5.get("verdict") == "UNMEASURED"
                 and "no file in scope" in " ".join(pop5.get("reasons", [])),
                 f"v4-shaped empty index: verdict={pop.get('verdict')} reasons={pop.get('reasons')} "
                 f"cli exit={rc} cli verdict={printed}; migrated empty scope: "
                 f"verdict={pop5.get('verdict')} reasons={pop5.get('reasons')}")
        finally:
            con.close()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _ = one_session_store(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            pop = UX.population(con)
            p = pop.get("population", {})
            miss = UX.population(con, project_filter="no-such-project")
            gate("V-UX5-EMPTY-CONTROL",
                 pop.get("verdict") == "MEASURED" and p.get("sessions_active") == 1
                 and p.get("calls") == 2 and p.get("cache_read") == 200
                 and miss.get("verdict") == "UNMEASURED",
                 f"one-session fixture: verdict={pop.get('verdict')} population={p}; "
                 f"unmatched project filter -> {miss.get('verdict')}")
        finally:
            con.close()


def _text_hits(db: Path, needles) -> list[str]:
    """Every (table.column) of the index whose value contains any needle. Scans EVERY column
    of every table, whatever its declared type."""
    hits = []
    raw = sqlite3.connect(str(db))
    try:
        tables = [r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for t in tables:
            cols = [r[1] for r in raw.execute(f"PRAGMA table_info({t})")]
            for row in raw.execute(f"SELECT * FROM {t}"):
                for c, v in zip(cols, row):
                    if isinstance(v, bytes):
                        v = v.decode("utf-8", "replace")
                    if isinstance(v, str) and any(n in v for n in needles):
                        hits.append(f"{t}.{c}")
    finally:
        raw.close()
    return sorted(set(hits))


def grp_no_raw_text() -> None:
    """HR-SECRET-002 / T-01-01: the index keeps hashes, sizes and normalized paths, never the
    text of a tool input or a tool result. The marker literals are assembled at run time and
    are clearly fake (HR-SECRET-005); no real key shape is ever written."""
    marker_in = "FAKE-MARKER-" + "A" * 40
    marker_out = "FAKE-MARKER-" + "B" * 40
    body = "out: " + marker_out
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        d = proj / "C--p1"
        d.mkdir(parents=True)
        (d / "S1.jsonl").write_text(
            user_prompt("P1", 1, "S1")
            + asst("m1", 1.1, "S1", tools=[("tuB1", "Bash", {"command": "echo " + marker_in,
                                                           "file_path": WINPATH})])
            + user_result(1.2, "S1", "tuB1", body), encoding="utf-8")
        db = td / "db" / "ix.sqlite"
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            row = con.execute("SELECT input_hash, input_bytes, result_chars FROM tool_events "
                              "WHERE tool_use_id='tuB1'").fetchone()
            con.commit()
            clean = _text_hits(db, (marker_in, marker_out))
            gate("V-UX5-NO-RAW-TEXT", row is not None and row[2] == len(body) and not clean,
                 f"the tool event was ingested (hash/size row={row}); columns holding either "
                 f"marker: {clean}")
            con.execute("CREATE TABLE scratch(x TEXT)")
            con.execute("INSERT INTO scratch VALUES(?)", (marker_in,))
            con.commit()
            seen = _text_hits(db, (marker_in, marker_out))
            gate("V-UX5-NO-RAW-TEXT-CONTROL", seen == ["scratch.x"],
                 f"the same scan finds a marker written into a scratch table of the same DB: {seen}")
        finally:
            con.close()


# -- plan 02 task 1: path identity, the declared _archived rule, the skipped-shape census ----

def _write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def quota_line(h, sess) -> str:
    return json.dumps({"type": "system", "timestamp": iso(h), "sessionId": sess,
                       "quotaLimits": {"status": "rejected", "rateLimitType": "seven_day",
                                       "resetsAt": T0 + 99 * 3600}}) + "\n"


def mixed_tree(td: Path, archived=True, drop_sub=False) -> Path:
    """projects/C--p1 {S1 main + subagent agent-a}, and (archived) projects/_archived/P {S2 main,
    S2 subagent agent-b}. S2 holds a prompt, an Agent spawn, a Read, a quota line: every
    ancestry fact a v4 table would store."""
    proj = td / "projects"
    d = proj / "C--p1"
    _write(d / "S1.jsonl", user_prompt("P1", 1, "S1")
           + asst("m1", 1.1, "S1", tools=[("tuR1", "Read", {"file_path": WINPATH})])
           + user_result(1.2, "S1", "tuR1", "abc") + asst("m2", 1.3, "S1"))
    if not drop_sub:
        _write(d / "S1" / "subagents" / "agent-a.jsonl", asst("ms1", 1.15, "S1", cr=30))
        _write(d / "S1" / "subagents" / "agent-a.meta.json",
               json.dumps({"agentType": "Explore", "toolUseId": "tuX", "spawnDepth": 1}))
    if archived:
        a = proj / "_archived" / "P"
        _write(a / "S2.jsonl", user_prompt("PA", 3, "S2") + quota_line(3.05, "S2")
               + asst("ma1", 3.1, "S2", cr=500,
                      tools=[("tuAG", "Agent", {"subagent_type": "Explore", "prompt": "look"}),
                             ("tuAR", "Read", {"file_path": WINPATH})]))
        _write(a / "S2" / "subagents" / "agent-b.jsonl", asst("mab1", 3.2, "S2", cr=40))
        _write(a / "S2" / "subagents" / "agent-b.meta.json",
               json.dumps({"agentType": "Explore", "toolUseId": "tuAG", "spawnDepth": 1}))
    return proj


def path_values(con) -> list[str]:
    """Every value of every path column of the index (files.resolved included)."""
    vals = []
    for table, col, _kind in UX._path_columns(con):
        vals += [r[0] for r in con.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL")]
    vals += [r[0] for r in con.execute("SELECT resolved FROM files WHERE resolved IS NOT NULL")]
    return vals


def grp_alias() -> None:
    # alias lists BEFORE its target ("A--" < "Z--"), the order that exposed the v4 defect
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        real = proj / "Z--real"
        _write(real / "S1.jsonl", user_prompt("P1", 1, "S1") + asst("m1", 1.1, "S1"))
        _write(real / "S1" / "subagents" / "agent-a.jsonl", asst("ms1", 1.15, "S1", cr=30))
        os.symlink(str(real), str(proj / "A--alias"), target_is_directory=True)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            n_files = con.execute("SELECT count(*) FROM files").fetchone()[0]
            n_cf = con.execute("SELECT count(*), count(DISTINCT k) FROM call_files").fetchone()
            vals = path_values(con)
            leaked = [v for v in vals if "A--alias" in v]
            gate("V-UX5-ALIAS-ONCE", n_files == 2 and n_cf == (2, 2) and vals and not leaked,
                 f"alias listed before its target: files rows={n_files} (want 2), call_files "
                 f"rows/distinct keys={n_cf} (want 2/2), path-column values={len(vals)}, "
                 f"carrying the alias spelling={len(leaked)}")
        finally:
            con.close()

    # control: a DIFFERENT directory with the same file names is its own store
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        for name, mid in (("B--one", "mA"), ("C--two", "mB")):
            _write(proj / name / "S1.jsonl", user_prompt("P" + mid, 1, "S1") + asst(mid, 1.1, "S1"))
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            rows = con.execute("SELECT store, session_key FROM files ORDER BY store").fetchall()
            gate("V-UX5-ALIAS-DISTINCT", rows == [("B--one", "S1"), ("C--two", "S1")],
                 f"two directories, same file name: files rows={rows}")
        finally:
            con.close()

    # a link to a directory OUTSIDE the root: ingested once, under its resolved path
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        proj.mkdir()
        out = td / "elsewhere" / "ext-store"
        _write(out / "S9.jsonl", user_prompt("P9", 1, "S9") + asst("m9", 1.1, "S9"))
        os.symlink(str(out), str(proj / "A--link-out"), target_is_directory=True)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            paths = [r[0] for r in con.execute("SELECT path FROM files")]
            want = os.path.realpath(str(out / "S9.jsonl"))
            vals = path_values(con)
            gate("V-UX5-ALIAS-OUTSIDE",
                 paths == [want] and not [v for v in vals if "A--link-out" in v],
                 f"link to an outside dir: files paths={[Path(p).name for p in paths]} "
                 f"resolved to the outside store={paths == [want]}; "
                 f"alias spelling in path columns={len([v for v in vals if 'A--link-out' in v])}")
        finally:
            con.close()


def grp_identity_columns() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = mixed_tree(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            want = {
                proj / "C--p1" / "S1.jsonl": ("C--p1", "C--p1", 0, "S1", 0),
                proj / "C--p1" / "S1" / "subagents" / "agent-a.jsonl": ("C--p1", "C--p1", 0, "S1", 1),
                proj / "_archived" / "P" / "S2.jsonl": ("_archived", "P", 1, "S2", 0),
                proj / "_archived" / "P" / "S2" / "subagents" / "agent-b.jsonl":
                    ("_archived", "P", 1, "S2", 1),
            }
            bad = []
            for p, (store, project, arch, skey, is_sub) in want.items():
                row = con.execute("SELECT resolved, store, project, archived, session_key, is_sub "
                                  "FROM files WHERE path=?", (os.path.realpath(str(p)),)).fetchone()
                exp = (TIS.resolved_path(os.path.realpath(str(p))), store, project, arch, skey, is_sub)
                if row != exp:
                    bad.append((p.name, row, exp))
            n = con.execute("SELECT count(*) FROM files").fetchone()[0]
            gate("V-UX5-IDENTITY-COLUMNS", not bad and n == len(want),
                 f"files rows={n}/{len(want)}; rows differing from the path-derived identity "
                 f"(resolved, store, project, archived, session_key, is_sub)={bad}")
        finally:
            con.close()


V4_ARCHIVE_TABLES = ("calls", "quota", "prompts", "spawns", "subagents")


def grp_archived() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = mixed_tree(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            arch = [r[0] for r in con.execute("SELECT path FROM files WHERE archived=1")]
            like = "%/_archived/%"
            v4_rows = {t: con.execute(f"SELECT count(*) FROM {t} WHERE file LIKE ?",
                                      (like,)).fetchone()[0] for t in V4_ARCHIVE_TABLES}
            cf = con.execute("SELECT count(*), coalesce(sum(cr),0) FROM call_files WHERE file LIKE ?",
                             (like,)).fetchone()
            te = con.execute("SELECT count(*) FROM tool_events WHERE file LIKE ?", (like,)).fetchone()[0]
            spawn_ids = con.execute("SELECT count(*) FROM spawns WHERE tool_use_id='tuAG'").fetchone()[0]
            gate("V-UX5-ARCHIVED-INDEXED",
                 len(arch) == 2 and cf == (2, 540) and te == 2 and not any(v4_rows.values())
                 and spawn_ids == 0,
                 f"archived files rows={len(arch)} (want 2); call_files rows/cr={cf} (want 2/540); "
                 f"tool_events rows={te}; rows in v4 tables for archived files={v4_rows}; "
                 f"archived Agent spawn leaked into spawns={spawn_ids}")
        finally:
            con.close()

    # the declared twin rule: a live file with the same project + session_key wins
    def sessions_with_archive(arch_project):
        with tempfile.TemporaryDirectory() as t3:
            t3 = Path(t3)
            pr = t3 / "projects"
            _write(pr / "C--p1" / "S2.jsonl", user_prompt("PL", 1, "S2") + asst("mlive", 1.1, "S2"))
            _write(pr / "_archived" / arch_project / "S2.jsonl",
                   user_prompt("PL2", 2, "S2") + asst("march", 2.1, "S2", cr=7))
            c = UX.connect(t3 / "db" / "ix.sqlite")
            try:
                UX.refresh(c, pr, deadline_s=30)
                p = UX.population(c, include_archived=True)
                return p["verdict"], p["population"]["sessions_active"], p["population"]["calls"]
            finally:
                c.close()

    twin, other = sessions_with_archive("C--p1"), sessions_with_archive("C--other")
    gate("V-UX5-ARCHIVED-TWIN-LIVE-WINS",
         twin == ("MEASURED", 1, 1) and other == ("MEASURED", 2, 2),
         f"include_archived with a live twin (same project + session): verdict/sessions/calls={twin} "
         f"(want 1 session, the live one); control, same session id under another project: {other} "
         f"(two sessions)")

    def windows(tree_kwargs):
        with tempfile.TemporaryDirectory() as t2:
            t2 = Path(t2)
            pr = mixed_tree(t2, **tree_kwargs)
            c = UX.connect(t2 / "db" / "ix.sqlite")
            try:
                UX.refresh(c, pr, deadline_s=30)
                return UX.window(c, T0, T0 + 24 * 3600)
            finally:
                c.close()

    with_arch = windows({"archived": True})
    without = windows({"archived": False})
    fewer = windows({"archived": True, "drop_sub": True})
    keys = ("calls", "cache_read", "subagent_calls")
    gate("V-UX5-V4-READERS-UNCHANGED",
         with_arch == without and with_arch["calls"] == 3 and with_arch["subagent_calls"] == 1
         and with_arch != fewer and fewer["subagent_calls"] == 0,
         f"window() with _archived {[with_arch[k] for k in keys]} vs without "
         f"{[without[k] for k in keys]} (equal); control, a live subagent file removed: "
         f"{[fewer[k] for k in keys]} (the comparison can see a difference)")


def grp_shapes() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = mixed_tree(td, archived=False)
        a = _write(proj / "C--p1" / "_preserved" / "x.jsonl", "{}\n")
        b = _write(proj / "C--p1" / "_empty_shells" / "y.jsonl", "{}\n{}\n")
        _write(proj / "C--p1" / "S1.jsonl.bak-1", "not a transcript\n")
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            meta = json.loads(con.execute("SELECT v FROM meta WHERE k='skipped_shapes'").fetchone()[0])
            in_files = con.execute("SELECT count(*) FROM files WHERE path LIKE '%/_preserved/%' "
                                   "OR path LIKE '%/_empty_shells/%'").fetchone()[0]
            samples = sorted(meta.get("samples", []))
            gate("V-UX5-SHAPE-SKIP-VISIBLE",
                 meta.get("count") == 2 and meta.get("bytes") == 3 + 6
                 and meta.get("by_shape") == {"_preserved": 1, "_empty_shells": 1, "other": 0}
                 and samples == sorted([str(a), str(b)]) and in_files == 0
                 and r.get("skipped_shapes") == meta,
                 f"meta skipped_shapes={meta}; rows in files for those shapes={in_files}; "
                 f"refresh result carries the same census={r.get('skipped_shapes') == meta}")
        finally:
            con.close()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _ = one_session_store(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            row = con.execute("SELECT v FROM meta WHERE k='skipped_shapes'").fetchone()
            meta = json.loads(row[0]) if row else None
            rule = con.execute("SELECT v FROM meta WHERE k='archived_rule'").fetchone()
            gate("V-UX5-SHAPE-SKIP-ZERO",
                 meta is not None and meta.get("count") == 0 and meta.get("bytes") == 0
                 and meta.get("samples") == [] and rule is not None and rule[0] == UX.ARCHIVED_RULE,
                 f"tree without odd shapes: meta skipped_shapes={meta} (present, count 0); "
                 f"archived_rule recorded={rule is not None}")
        finally:
            con.close()


def grp_identity_fill() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, snap, _ = make_v4(td)
        with Spy(proj) as spy:
            con = UX.connect(db)
            UX.refresh(con, proj, deadline_s=30)
        try:
            rows = con.execute("SELECT path, resolved, store, project, archived, session_key "
                               "FROM files ORDER BY path").fetchall()
            want = sorted((os.path.realpath(str(f)), TIS.resolved_path(str(f)), f.parent.name,
                           f.parent.name, 0, f.stem) for f in files)
            v5_null = con.execute("SELECT count(*) FROM files WHERE v5_from IS NULL").fetchone()[0]
            gate("V-UX5-IDENTITY-FILL-NO-OPEN",
                 not spy.opened and [tuple(r) for r in rows] == want and v5_null == len(files),
                 f"migrated v4 index: opens under the fixture root={len(spy.opened)}; identity "
                 f"columns filled for {len(rows)}/{len(files)} legacy rows equal to the path "
                 f"derivation={[tuple(r) for r in rows] == want}; their v5 facts stay unknown "
                 f"(v5_from NULL on {v5_null})")
        finally:
            con.close()


GROUPS = (("grp_schema", grp_schema), ("grp_tool_event", grp_tool_event),
          ("grp_occurrence", grp_occurrence), ("grp_migrate", grp_migrate),
          ("grp_population_empty", grp_population_empty), ("grp_no_raw_text", grp_no_raw_text),
          ("grp_alias", grp_alias), ("grp_identity_columns", grp_identity_columns),
          ("grp_archived", grp_archived), ("grp_shapes", grp_shapes),
          ("grp_identity_fill", grp_identity_fill))


# -- mutation drill ------------------------------------------------------------
# Every gate is shown able to go red: each mutant breaks the code under test in one
# way, the gates it must kill are re-run, the mutant is restored. The unmutated control
# runs first and must be green (a drill whose control is red proves nothing), and the
# unmutated rerun at the end proves the restore. Later plans append to MUTANTS.

class InvalidMutant(Exception):
    """The anchor text is not present exactly once: the mutant does not exist."""


def _quiet(groups) -> dict:
    global _QUIET
    saved, _QUIET = _QUIET, True
    res: dict = {}
    try:
        for fn in groups:
            res.update(guarded(fn.__name__, fn))
    finally:
        _QUIET = saved
    return res


def _patch(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, saved)


_MUT_N = [0]


def _source_mutant(rel_path, old, new):
    """A copy of tools/<rel_path> with `old` replaced by `new` (strings, or equal-length
    sequences of them), each anchor required to occur exactly once. The copy is loaded under
    a unique module name and swapped into UX (or TIS, via UX._tis); the returned callable
    puts the original back."""
    import importlib.util

    global UX, TIS
    src_path = HERE.parent / rel_path
    src = src_path.read_text(encoding="utf-8")
    olds = [old] if isinstance(old, str) else list(old)
    news = [new] if isinstance(new, str) else list(new)
    for o in olds:
        if src.count(o) != 1:
            raise InvalidMutant(f"anchor occurs {src.count(o)}x in {rel_path}: {o[:60]!r}")
    for o, n in zip(olds, news):
        src = src.replace(o, n)
    tmp = tempfile.TemporaryDirectory(prefix="ux5mut_")
    dst = Path(tmp.name) / src_path.name
    dst.write_text(src, encoding="utf-8")
    _MUT_N[0] += 1
    name = f"{src_path.stem}__mut{_MUT_N[0]}"
    spec = importlib.util.spec_from_file_location(name, dst)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    saved = (UX, TIS, getattr(UX, "_tis", None))
    if src_path.stem == "usage_index":
        UX = mod
    elif src_path.stem == "tis_observed":
        TIS = mod
        UX._tis = mod

    def restore():
        global UX, TIS
        UX, TIS = saved[0], saved[1]
        if saved[2] is not None:
            UX._tis = saved[2]
        sys.modules.pop(name, None)
        tmp.cleanup()
    return restore


def _m_spawn_backfill_requeued():
    """M1: _migrate_spawns gated on SCHEMA_VERSION again, so the v5 bump re-queues the spawn
    backfill and re-opens ingested files."""
    return _source_mutant(
        "tools/usage_index.py",
        ("    if row is not None and int(row[0]) >= SPAWN_SCHEMA:",
         "        if row is None or int(row[0]) < SPAWN_SCHEMA:"),
        ("    if row is not None and int(row[0]) >= SCHEMA_VERSION:",
         "        if row is None or int(row[0]) < SCHEMA_VERSION:"))


def _m_migrate_resets_offsets():
    """M2: _migrate_v5 also resets the file sizes, which forces a re-read of every file."""
    return _source_mutant(
        "tools/usage_index.py",
        "                        (str(SCHEMA_VERSION),))",
        "                        (str(SCHEMA_VERSION),))\n"
        "            con.execute(\"UPDATE files SET size=-1\")")


def _m_occurrence_dropped():
    """M3: the call_files upsert becomes a no-op."""
    return _source_mutant(
        "tools/usage_index.py",
        "con.execute(\n                    \"INSERT INTO call_files(k,file,ts,model,inp,cw,cw5,cw1,cr,out) \"",
        "(lambda *a: None)(\n                    \"INSERT INTO call_files(k,file,ts,model,inp,cw,cw5,cw1,cr,out) \"")


def _m_empty_population_measured():
    """M4: population reports MEASURED on a scope that holds nothing."""
    real = UX.population

    def mutant(*a, **k):
        out = real(*a, **k)
        if out.get("verdict") == "UNMEASURED":
            out["verdict"] = "MEASURED"
        return out
    return _patch(UX, "population", mutant)


def _m_store_identity_bypassed():
    """M5: store identity bypassed: every listed child dir is a store, no alias map."""
    def mutant(base=None):
        b = Path(base or TIS.PROJECTS_DIR)
        return (sorted(c for c in b.iterdir() if c.is_dir()) if b.is_dir() else []), {}
    return _patch(UX._tis, "store_identity", mutant)


def _m_archived_into_calls():
    """M6: the archived guard around the calls upsert is inverted into `if True`, so archived
    transcripts are written to calls."""
    return _source_mutant(
        "tools/usage_index.py",
        "                if not archived:  # ARCHIVED_RULE: v5 tables only\n",
        "                if True:  # ARCHIVED_RULE: v5 tables only\n")


MUTANTS = [
    ("M1 _migrate_spawns gated on SCHEMA_VERSION (backfill re-queued)", _m_spawn_backfill_requeued,
     [grp_migrate], ["V-UX5-MIGRATE-ZERO-REREAD"]),
    ("M2 _migrate_v5 resets file sizes (forces a re-read)", _m_migrate_resets_offsets,
     [grp_migrate], ["V-UX5-MIGRATE-ZERO-REREAD"]),
    ("M3 call_files occurrence upsert removed", _m_occurrence_dropped,
     [grp_occurrence], ["V-UX5-OCCURRENCE"]),
    ("M4 population MEASURED on an empty scope", _m_empty_population_measured,
     [grp_population_empty], ["V-UX5-EMPTY-REFUSES"]),
    ("M5 store identity bypassed (alias counted twice)", _m_store_identity_bypassed,
     [grp_alias], ["V-UX5-ALIAS-ONCE"]),
    ("M6 archived transcripts written to calls", _m_archived_into_calls,
     [grp_archived], ["V-UX5-V4-READERS-UNCHANGED", "V-UX5-ARCHIVED-INDEXED"]),
]


def run_drill() -> int:
    control = _quiet([fn for _, fn in GROUPS])
    control_ok = bool(control) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL DRILL-CONTROL'} DRILL-CONTROL unmutated run: "
          f"{sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, groups, targets in MUTANTS:
        try:
            restore = apply()
        except InvalidMutant as e:
            print(f"INVALID {label}: {e}")
            continue
        try:
            seen = _quiet(groups)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            print(f"SURVIVED {label} (still green or absent: "
                  f"{', '.join(t for t in targets if seen.get(t) is not False)}; saw {seen})")
    after = _quiet([fn for _, fn in GROUPS])
    clean = bool(after) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL DRILL-CLEAN-AFTER-MUTANTS'} DRILL-CLEAN-AFTER-MUTANTS "
          f"unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


def main(argv=None) -> int:
    if "--drill" in (argv or []):
        return run_drill()
    for name, fn in GROUPS:
        guarded(name, fn)
    total = PASS + FAIL
    print(f"USAGE_INDEX_V5_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
