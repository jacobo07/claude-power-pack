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
    con.execute("DROP INDEX IF EXISTS files_content")     # an index blocks DROP COLUMN
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


# -- plan 02 task 2: parser/file failures surfaced; content identity and duplicate groups -----

def plain_user(text: str, h: float = 5.0) -> str:
    return json.dumps({"type": "user", "timestamp": iso(h),
                       "message": {"role": "user", "content": text}}) + "\n"


def last_status(con) -> dict:
    return json.loads(con.execute("SELECT v FROM meta WHERE k='last_refresh_status'").fetchone()[0])


def grp_parse_errors() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        f = _write(proj / "C--p1" / "S1.jsonl",
                   user_prompt("P1", 1, "S1") + "{this is not json\n"
                   + asst("m1", 1.1, "S1") + "}}garbage}}\n" + asst("m2", 1.2, "S1"))
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            pe = con.execute("SELECT parse_errors FROM files WHERE path=?", (os.path.realpath(str(f)),)
                             ).fetchone()[0]
            st = last_status(con)
            ncalls = con.execute("SELECT count(*) FROM calls").fetchone()[0]
            gate("V-UX5-PARSE-ERROR-SURFACED",
                 pe == 2 and r.get("parse_errors") == 2 and st.get("parse_errors") == 2
                 and ncalls == 2 and r["status"] == "OK",
                 f"two undecodable complete lines: files.parse_errors={pe}, refresh result "
                 f"parse_errors={r.get('parse_errors')}, meta last_refresh_status "
                 f"parse_errors={st.get('parse_errors')}; valid calls still ingested={ncalls}/2")
            # a second pass over an unchanged file must not re-count
            r2 = UX.refresh(con, proj, deadline_s=30)
            pe2 = con.execute("SELECT parse_errors FROM files").fetchone()[0]
            gate("V-UX5-PARSE-ERROR-STABLE", pe2 == 2 and r2.get("parse_errors") == 0,
                 f"unchanged file re-refreshed: files.parse_errors={pe2} (want 2), this pass "
                 f"parse_errors={r2.get('parse_errors')} (want 0)")
        finally:
            con.close()

    with tempfile.TemporaryDirectory() as td:                      # control: a clean file
        td = Path(td)
        proj, _ = one_session_store(td)
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            pe = con.execute("SELECT parse_errors FROM files").fetchone()[0]
            st = last_status(con)
            gate("V-UX5-PARSE-ERROR-CLEAN",
                 pe == 0 and r.get("parse_errors") == 0 and st.get("parse_errors") == 0
                 and st.get("files_with_errors") == 0,
                 f"clean file: files.parse_errors={pe}, result parse_errors={r.get('parse_errors')}, "
                 f"meta parse_errors={st.get('parse_errors')} files_with_errors="
                 f"{st.get('files_with_errors')} (a present zero, not an absent key)")
        finally:
            con.close()


def grp_partial_line() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        whole = asst("m2", 1.2, "S1")
        cut = len(whole) // 2
        f = _write(proj / "C--p1" / "S1.jsonl",
                   user_prompt("P1", 1, "S1") + asst("m1", 1.1, "S1") + whole[:cut])
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r1 = UX.refresh(con, proj, deadline_s=30)
            pe1 = con.execute("SELECT parse_errors FROM files").fetchone()[0]
            n1 = con.execute("SELECT count(*) FROM calls").fetchone()[0]
            with f.open("a", encoding="utf-8") as fh:
                fh.write(whole[cut:])
            r2 = UX.refresh(con, proj, deadline_s=30)
            pe2 = con.execute("SELECT parse_errors FROM files").fetchone()[0]
            n2 = con.execute("SELECT count(*) FROM calls").fetchone()[0]
            gate("V-UX5-PARTIAL-LINE-NOT-ERROR",
                 pe1 == 0 and r1.get("parse_errors") == 0 and n1 == 1 and pe2 == 0
                 and r2.get("parse_errors") == 0 and n2 == 2,
                 f"half-written last line: parse_errors={pe1} calls={n1} (want 0 / 1); after the "
                 f"line is completed: parse_errors={pe2} calls={n2} (want 0 / 2)")
        finally:
            con.close()


def _file_error_case(td: Path, inject: bool):
    proj, files = two_file_store(td)
    bad = files[1]
    undo = None
    if inject:                                    # running as root: mode 000 does not stop open()
        real = UX._tis.calls_from

        def failing(path, *a, **k):
            if Path(path).name == bad.name:
                raise PermissionError(13, "Permission denied", str(path))
            return real(path, *a, **k)
        undo = _patch(UX._tis, "calls_from", failing)
    else:
        os.chmod(bad, 0)
    con = UX.connect(td / "db" / "ix.sqlite")
    try:
        r = UX.refresh(con, proj, deadline_s=30)
        row = con.execute("SELECT error, offset FROM files WHERE path=?",
                          (os.path.realpath(str(bad)),)).fetchone()
        ok_calls = con.execute("SELECT count(*) FROM calls WHERE file=?",
                               (os.path.realpath(str(files[0])),)).fetchone()[0]
        st = last_status(con)
        # control: once readable again the error clears and the file is ingested
        if undo:
            undo()
        else:
            os.chmod(bad, 0o644)
        r2 = UX.refresh(con, proj, deadline_s=30)
        row2 = con.execute("SELECT error FROM files WHERE path=?", (os.path.realpath(str(bad)),)).fetchone()
        n2 = con.execute("SELECT count(*) FROM calls WHERE file=?", (os.path.realpath(str(bad)),)).fetchone()[0]
        return r, row, ok_calls, st, r2, row2, n2
    finally:
        con.close()


def grp_file_error() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        probe = td / "probe"
        probe.write_text("x")
        os.chmod(probe, 0)
        try:
            with open(probe, "rb"):
                root_like = True                  # open() succeeded under mode 000
        except OSError:
            root_like = False
        os.chmod(probe, 0o644)
        r, row, ok_calls, st, r2, row2, n2 = _file_error_case(td, inject=root_like)
        mode = "injected PermissionError (mode 000 is readable here)" if root_like else "mode 000"
        gate("V-UX5-FILE-ERROR-TYPED",
             row is not None and (row[0] or "").startswith("PermissionError") and ok_calls == 3
             and r.get("files_with_errors") == 1 and st.get("files_with_errors") == 1
             and r["status"] == "OK" and row[1] == 0,
             f"unreadable transcript ({mode}): files.error={row and row[0]!r}, offset not advanced="
             f"{row and row[1]}; other file ingested={ok_calls}/3 calls; files_with_errors="
             f"{r.get('files_with_errors')}")
        gate("V-UX5-FILE-ERROR-CLEARS",
             row2 is not None and row2[0] is None and n2 == 2 and r2.get("files_with_errors") == 0,
             f"after the file is readable again: files.error={row2 and row2[0]!r}, its calls={n2}/2, "
             f"files_with_errors={r2.get('files_with_errors')}")


def _hist_tree(td: Path, tails, names=("C--a", "C--b")) -> Path:
    proj = td / "projects"
    prefix = user_prompt("P1", 1, "S1") + asst("m1", 1.1, "S1") + asst("m2", 1.2, "S1")
    for name, tail in zip(names, tails):
        _write(proj / name / "S1.jsonl", prefix + plain_user(tail))
    return proj


def grp_content_identity() -> None:
    # same sessionId, shared prefix, different last line of equal length
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = _hist_tree(td, ("alpha", "bravo"))
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            rows = con.execute("SELECT path, content_id, dup_of FROM files ORDER BY path").fetchall()
            ncalls = con.execute("SELECT count(*) FROM calls").fetchone()[0]
            ncf = con.execute("SELECT count(*), count(DISTINCT file) FROM call_files").fetchone()
            ids = [r[1] for r in rows]
            gate("V-UX5-HISTORIES-NOT-MERGED",
                 len(rows) == 2 and all(ids) and ids[0] != ids[1]
                 and all(r[2] is None for r in rows) and ncalls == 2 and ncf == (4, 2),
                 f"two histories, one sessionId, shared prefix: files rows={len(rows)}, content_ids "
                 f"distinct={len(set(ids)) == 2}, dup_of={[r[2] for r in rows]}; shared-prefix calls "
                 f"rows={ncalls} (want 2), call_files rows/files={ncf} (want 4/2)")
        finally:
            con.close()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = _hist_tree(td, ("alpha", "alpha"))
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            rows = con.execute("SELECT path, content_id, dup_of FROM files ORDER BY path").fetchall()
            ncalls = con.execute("SELECT count(*) FROM calls").fetchone()[0]
            ncf = con.execute("SELECT count(*) FROM call_files").fetchone()[0]
            small, large = rows[0][0], rows[1][0]
            gate("V-UX5-COPY-ONCE",
                 len(rows) == 2 and rows[0][1] and rows[0][1] == rows[1][1] and rows[0][2] is None
                 and rows[1][2] == small and ncalls == 2 and ncf == 4,
                 f"byte-identical copies: one content_id={rows[0][1] == rows[1][1]}, smaller path "
                 f"dup_of={rows[0][2]}, larger path dup_of is the smaller={rows[1][2] == small}; "
                 f"calls rows={ncalls} (each key once), call_files rows={ncf} (each copy's own)")
        finally:
            con.close()

    def build_in_order(first: str, second: str):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            proj = t / "projects"
            body = (user_prompt("P1", 1, "S1") + asst("m1", 1.1, "S1") + plain_user("alpha"))
            con = UX.connect(t / "db" / "ix.sqlite")
            try:
                _write(proj / first / "S1.jsonl", body)
                UX.refresh(con, proj, deadline_s=30)
                _write(proj / second / "S1.jsonl", body)
                UX.refresh(con, proj, deadline_s=30)
                m1 = {Path(p).parent.name: Path(d).parent.name if d else None for p, d in
                      con.execute("SELECT path, dup_of FROM files")}
                larger = proj / "C--b" / "S1.jsonl"
                with larger.open("a", encoding="utf-8") as fh:
                    fh.write(asst("m9", 1.9, "S1"))
                UX.refresh(con, proj, deadline_s=30)
                m2 = {Path(p).parent.name: d for p, d in con.execute("SELECT path, dup_of FROM files")}
                ids = [r[0] for r in con.execute("SELECT content_id FROM files")]
                return m1, m2, ids
            finally:
                con.close()

    ab = build_in_order("C--a", "C--b")
    ba = build_in_order("C--b", "C--a")
    gate("V-UX5-DUP-ORDER-INDEPENDENT",
         ab[0] == ba[0] == {"C--a": None, "C--b": "C--a"}
         and ab[1] == ba[1] == {"C--a": None, "C--b": None} and len(set(ab[2])) == 2,
         f"copies ingested a-then-b {ab[0]} and b-then-a {ba[0]} give the same assignment; after "
         f"the larger copy grows its dup_of is cleared {ab[1]} / {ba[1]} and the two content_ids "
         f"differ={len(set(ab[2])) == 2}")


# -- plan 02 task 3: interrupted and parallel refresh (the AOP-O edge probe) ---------------

def _crash_tree(td: Path) -> Path:
    """Two transcripts of five valid lines each and one undecodable line each, so a double
    count of parse_errors or of any row shows."""
    proj = td / "projects"
    for sess, base in (("S1", 1.0), ("S2", 2.0)):
        _write(proj / "C--p1" / f"{sess}.jsonl",
               user_prompt("P" + sess, base, sess)
               + asst("m1" + sess, base + 0.1, sess, tools=[("tuR" + sess, "Read", {"file_path": WINPATH})])
               + "{broken line\n"
               + user_result(base + 0.2, sess, "tuR" + sess, "abc")
               + asst("m2" + sess, base + 0.3, sess) + asst("m3" + sess, base + 0.4, sess))
    return proj


def table_counts(con) -> dict:
    out = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
           for t in ("files", "calls", "call_files", "tool_events")}
    out["parse_errors"] = {Path(p).name: n for p, n in
                           con.execute("SELECT path, parse_errors FROM files")}
    return out


def grp_crash_resume() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = _crash_tree(td)
        ref = UX.connect(td / "db" / "ref.sqlite")
        try:
            UX.refresh(ref, proj, deadline_s=30)
            want = table_counts(ref)
        finally:
            ref.close()

        real = UX._v5_line
        seen: dict = {}

        class Crash(BaseException):
            """A process death, not an error: no handler in refresh may type it as a file error."""

        def crashing(con, path, state, o, start):
            real(con, path, state, o, start)
            seen[path] = seen.get(path, 0) + 1
            if len(seen) == 2 and seen[path] == 3:       # after the third line of the second file
                raise Crash("injected crash")

        db = td / "db" / "ix.sqlite"
        con = UX.connect(db)
        try:
            undo = _patch(UX, "_v5_line", crashing)
            crashed = None
            try:
                UX.refresh(con, proj, deadline_s=30)
            except Crash as e:
                crashed = e
            finally:
                undo()
                con.close()                              # the process is gone: nothing commits
            con = UX.connect(db)
            second = list(seen)[1] if len(seen) == 2 else None
            leftovers = {}
            if second:
                for t, col in (("files", "path"), ("calls", "file"), ("call_files", "file"),
                               ("tool_events", "file"), ("quota", "file"), ("prompts", "file")):
                    leftovers[t] = con.execute(f"SELECT count(*) FROM {t} WHERE {col}=?",
                                               (second,)).fetchone()[0]
            first_ok = bool(seen) and con.execute("SELECT count(*) FROM files WHERE path=?",
                                                  (list(seen)[0],)).fetchone()[0] == 1
            r2 = UX.refresh(con, proj, deadline_s=30)
            got = table_counts(con)
            gate("V-UX5-CRASH-RESUME",
                 crashed is not None and second is not None
                 and not any(leftovers.values()) and first_ok and r2["status"] == "OK"
                 and got == want and sum(want["parse_errors"].values()) == 2,
                 f"crash injected after line 3 of the second file: escaped refresh={crashed is not None}; rows of "
                 f"that file left behind={leftovers} (want all 0); the first file committed="
                 f"{first_ok}; after the next refresh {got} equals the one-shot build {want}")
        finally:
            con.close()


def grp_concurrent_refresh() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = _crash_tree(td)
        db = td / "db" / "ix.sqlite"
        a = UX.connect(db)
        b = UX.connect(db)
        try:
            UX.refresh(a, proj, deadline_s=30)
            stale = UX._snapshot(b)                       # B looks, then A moves on
            files = sorted((proj / "C--p1").glob("*.jsonl"))
            for f in files:
                with f.open("a", encoding="utf-8") as fh:
                    fh.write("{another broken line\n" + asst("m9" + f.stem, 9.0, f.stem))
            ra = UX.refresh(a, proj, deadline_s=30)
            rb = UX.refresh(b, proj, deadline_s=30, snapshot=stale)
            got = table_counts(a)
            ref = UX.connect(td / "db" / "ref.sqlite")
            try:
                UX.refresh(ref, proj, deadline_s=30)
                want = table_counts(ref)
            finally:
                ref.close()
            gate("V-UX5-STALE-SNAPSHOT-SKIPS",
                 ra["files_read"] == 2 and rb["skipped_concurrent"] == 2 and rb["files_read"] == 0
                 and rb["parse_errors"] == 0 and got == want
                 and last_status(b).get("skipped_concurrent") == 2,
                 f"B started from a snapshot taken before A advanced both files: B skipped_concurrent="
                 f"{rb['skipped_concurrent']} files_read={rb['files_read']} parse_errors this pass="
                 f"{rb['parse_errors']}; rows {got} equal a single refresh {want}")

            # control: an up-to-date snapshot of an appended file is ingested by B
            fresh = UX._snapshot(b)
            with files[0].open("a", encoding="utf-8") as fh:
                fh.write(asst("m10", 10.0, "S1"))
            rb2 = UX.refresh(b, proj, deadline_s=30, snapshot=fresh)
            n = b.execute("SELECT count(*) FROM calls WHERE k LIKE 'm10|%'").fetchone()[0]
            gate("V-UX5-FRESH-SNAPSHOT-INGESTS",
                 rb2["files_read"] == 1 and rb2["skipped_concurrent"] == 0 and n == 1,
                 f"up-to-date snapshot, one appended file: files_read={rb2['files_read']} "
                 f"skipped_concurrent={rb2['skipped_concurrent']} new call ingested={n}")
        finally:
            a.close()
            b.close()


def grp_migrate_once() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, snap, _ = make_v4(td)
        c1 = UX.connect(db)
        c2 = UX.connect(db)
        try:
            UX._migrate_v5(c1)
            first = c1.execute("SELECT v FROM meta WHERE k='v5_migration'").fetchone()[0]
            UX._migrate_v5(c2)
            second = c2.execute("SELECT v FROM meta WHERE k='v5_migration'").fetchone()[0]
            ver = c2.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()[0]
            gate("V-UX5-MIGRATE-ONCE", first and first == second and ver == "5",
                 f"second migration through another connection: v5_migration unchanged="
                 f"{first == second} ({first}), schema_version={ver}")
        finally:
            c1.close()
            c2.close()


# -- plan 03 task 1: effective timestamps, cwds, registered patterns, classifier features ----

_KTA: list = []


def champion():
    """wiki/tools/kme_token_audit.py loaded straight from its file by this gate (the gate's own
    reference for what the champion counts), never through the module under test."""
    if not _KTA:
        import importlib.util
        src = HERE.parent / "wiki" / "tools" / "kme_token_audit.py"
        spec = importlib.util.spec_from_file_location("kme_token_audit_gate", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _KTA.append(mod)
    return _KTA[0]


def no_ts(line: str) -> str:
    o = json.loads(line)
    o.pop("timestamp", None)
    return json.dumps(o) + "\n"


def line_offsets(lines) -> list[int]:
    offs, pos = [], 0
    for ln in lines:
        offs.append(pos)
        pos += len(ln.encode("utf-8"))
    return offs


def one_file_db(td: Path, lines, store="C--p1", sid="S1"):
    """projects/<store>/<sid>.jsonl holding `lines`; returns (proj, file, db path)."""
    proj = td / "projects"
    f = _write(proj / store / f"{sid}.jsonl", "".join(lines))
    return proj, f, td / "db" / "ix.sqlite"


def grp_ts_inherit() -> None:
    t1, t2 = T0 + 1 * 3600, T0 + 2 * 3600
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        lines = [no_ts(asst("m1", 0, "S1", tools=[("tuA", "Read", {"file_path": WINPATH})])),
                 user_prompt("P1", 1, "S1"),
                 no_ts(asst("m2", 0, "S1", tools=[("tuB", "Read", {"file_path": WINPATH})])),
                 asst("m3", 2, "S1", tools=[("tuC", "Read", {"file_path": WINPATH})])]
        proj, f, db = one_file_db(td, lines)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            ev = dict(con.execute("SELECT tool_use_id, ts FROM tool_events"))
            cf = dict(con.execute("SELECT k, ts FROM call_files"))
            first, last = con.execute("SELECT first_ts, last_ts FROM files WHERE path=?",
                                      (str(f),)).fetchone()
            resolved_a = con.execute(
                "SELECT coalesce(e.ts, f.first_ts) FROM tool_events e JOIN files f ON f.path=e.file "
                "WHERE e.tool_use_id='tuA'").fetchone()[0]
            gate("V-UX5-TS-INHERIT",
                 ev["tuA"] is None and ev["tuB"] == t1 and ev["tuC"] == t2
                 and cf["m1|rm1"] is None and cf["m2|rm2"] == t1 and cf["m3|rm3"] == t2
                 and first == t1 and last == t2 and resolved_a == t1,
                 f"leading ts-less event stores NULL ({ev['tuA']}) and resolves to files.first_ts "
                 f"({resolved_a} == {t1}); ts-less line inherits ({ev['tuB']} == {t1}); a line with "
                 f"its own ts keeps it ({ev['tuC']} == {t2}); call_files.ts {cf}; first/last={first}/{last}")
            with f.open("a", encoding="utf-8") as fh:        # a second pass opens on a ts-less line
                fh.write(no_ts(asst("m4", 0, "S1", tools=[("tuD", "Read", {"file_path": WINPATH})])))
            UX.refresh(con, proj, deadline_s=30)
            ev2 = dict(con.execute("SELECT tool_use_id, ts FROM tool_events"))
            last2 = con.execute("SELECT last_ts FROM files WHERE path=?", (str(f),)).fetchone()[0]
            gate("V-UX5-TS-INHERIT-ACROSS-PASSES", ev2["tuD"] == t2 and last2 == t2,
                 f"a second pass starting with a ts-less line inherits files.last_ts: "
                 f"{ev2['tuD']} == {t2}; last_ts stays {last2}")
        finally:
            con.close()


def grp_cwd() -> None:
    a, sub = WINCWD, WINCWD + "\\sub"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        lines = [asst("m1", 1.0, "S1", cwd=a), asst("m2", 1.5, "S1", cwd=sub),
                 user_result(1.6, "S1", "none", "x"), asst("m3", 2.0, "S1", cwd=a)]
        offs = line_offsets(lines)
        proj, f, db = one_file_db(td, lines)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            rows = {r[0]: r[1:] for r in con.execute(
                "SELECT cwd, first_off, first_ts FROM file_cwds WHERE file=?", (str(f),))}
            gate("V-UX5-CWD",
                 set(rows) == {a, sub} and rows[a] == (offs[0], T0 + 3600)
                 and rows[sub] == (offs[1], T0 + 1.5 * 3600),
                 f"two distinct cwds A, A/sub (A seen again adds nothing, the cwd-less line adds "
                 f"nothing); first_off/first_ts: {rows} want A={offs[0]}, sub={offs[1]}")
        finally:
            con.close()


def _pattern_tree(td: Path):
    inp_hit = {"command": "echo KobiMapEngine and KobiMapEngine"}
    lines = [user_prompt("P1", 1, "S1"),
             asst("m1", 1.1, "S1", tools=[("tuH", "Bash", inp_hit),
                                          ("tuN", "Bash", {"command": "ls"}),
                                          ("tuU", "Bash", {"command": "KMEñ"})])]
    return one_file_db(td, lines), inp_hit


def grp_pattern_source() -> None:
    kta = champion()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (proj, f, db), _ = _pattern_tree(td)
        con = UX.connect(db)
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            row = con.execute("SELECT regex, flags, source, version FROM patterns WHERE name='kme'"
                              ).fetchone()
            pv = con.execute("SELECT pat_ver FROM files WHERE path=?", (str(f),)).fetchone()[0]
            ps = (con.execute("SELECT v FROM meta WHERE k='pattern_set'").fetchone() or [None])[0]
            other = UX._pattern_set({"kme": (kta.PATH_KME_RE.pattern, kta.PATH_KME_RE.flags)})
            same = UX._pattern_set({"kme": (kta.KME_RE.pattern, kta.KME_RE.flags)})
            gate("V-UX5-PATTERN-SOURCE",
                 row is not None and row[0] == kta.KME_RE.pattern and row[1] == kta.KME_RE.flags
                 and pv == ps and ps is not None and same == ps and other != ps
                 and r.get("pattern_error") is None,
                 f"patterns.kme regex==KME_RE.pattern: {row and row[0] == kta.KME_RE.pattern}, "
                 f"flags {row and row[1]}=={kta.KME_RE.flags}; files.pat_ver==meta pattern_set: "
                 f"{pv == ps}; control: a different regex gives a different pattern_set "
                 f"({other != ps}); pattern_error={r.get('pattern_error')}")
        finally:
            con.close()


def grp_pat_hits() -> None:
    kta = champion()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (proj, f, db), inp_hit = _pattern_tree(td)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            want = len(kta.KME_RE.findall(json.dumps(inp_hit, ensure_ascii=False)))
            got = dict(con.execute("SELECT tool_use_id, pat_hits FROM tool_events"))
            gate("V-UX5-PAT-HITS",
                 want == 2 and got["tuH"] is not None and json.loads(got["tuH"]) == {"kme": want}
                 and got["tuN"] is None,
                 f"two mentions: pat_hits={got['tuH']} want {{'kme': {want}}} (the champion "
                 f"expression on the same input); control: no hit stores NULL ({got['tuN']})")
            # the champion serializes with ensure_ascii=False: `KME` followed by a non-ASCII letter
            # is no word boundary there, but WOULD match in the ASCII-escaped form
            esc = len(kta.KME_RE.findall(json.dumps({"command": "KMEñ"}, ensure_ascii=True)))
            raw = len(kta.KME_RE.findall(json.dumps({"command": "KMEñ"}, ensure_ascii=False)))
            gate("V-UX5-PAT-HITS-SERIALIZATION", esc == 1 and raw == 0 and got["tuU"] is None,
                 f"ascii-escaped form hits {esc}, champion form hits {raw}; stored {got['tuU']} "
                 f"(must follow the champion form)")
        finally:
            con.close()


def _user_line(content, h, **extra) -> str:
    o = {"type": "user", "timestamp": iso(h), "message": {"role": "user", "content": content}}
    o.update(extra)
    return json.dumps(o) + "\n"


def grp_user_hits() -> None:
    kta = champion()
    human = "please look at KobiMapEngine and KMEIP"
    cmd = "<command-name>x</command-name> KobiMapEngine KobiMapEngine"
    skill = "Base directory for this skill: KME KME KME"
    long_ = "KobiMapEngine " + "x" * 20000
    listed = [{"type": "text", "text": "KMEIP again"},
              {"type": "tool_result", "tool_use_id": "t9", "content": "KobiMapEngine"}]
    lines = [user_prompt("P1", 1, "S1"),
             _user_line(human, 2), _user_line(cmd, 3), _user_line(skill, 4),
             _user_line(long_, 5), _user_line("KobiMapEngine meta", 6, isMeta=True),
             _user_line(listed, 7)]
    offs = line_offsets(lines)
    controls = (cmd, skill, long_, "KobiMapEngine meta")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, f, db = one_file_db(td, lines)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            rows = {r[0]: (r[1], r[2]) for r in con.execute(
                "SELECT off, ts, pat_hits FROM user_hits WHERE file=?", (str(f),))}
            raw_hits = [len(kta.KME_RE.findall(c)) for c in controls]
            want = len(kta.KME_RE.findall(human))
            gate("V-UX5-USER-HITS-FILTER",
                 want == 2 and all(h > 0 for h in raw_hits) and offs[1] in rows
                 and json.loads(rows[offs[1]][1]) == {"kme": want}
                 and rows[offs[1]][0] == T0 + 2 * 3600
                 and not {offs[2], offs[3], offs[4], offs[5]} & set(rows),
                 f"human text -> one row with the champion count {want} (rows at offsets "
                 f"{sorted(rows)}); the four controls (<command-name> in the first 400, skill base "
                 f"directory in the first 200, length >= 20000, isMeta) all hit in raw text "
                 f"({raw_hits}) and produce no row")
            gate("V-UX5-USER-HITS-LIST-SHAPE",
                 offs[6] in rows and json.loads(rows[offs[6]][1]) == {"kme": 1},
                 f"a list-content human text item counts, a tool_result item inside it does not "
                 f"({rows.get(offs[6])})")
        finally:
            con.close()


def grp_result_text_parity() -> None:
    kta = champion()
    shapes = ["plain", "", None, [], {"k": 1}, 7,
              [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}],
              [{"type": "text", "text": "x"},
               {"type": "tool_result", "content": [{"type": "text", "text": "nested"}, "bare"]},
               {"type": "image", "source": {}}, "bare string", {"type": "unknown", "text": "t"}],
              [{"type": "tool_result", "content": "inner str"}, {"type": "text"}]]
    bad = [repr(s)[:40] for s in shapes if UX._result_text(s) != kta.text_of(s)]
    gate("V-UX5-RESULT-TEXT-PARITY", not bad,
         f"_result_text == kme_token_audit.text_of on {len(shapes)} shapes (str, None, empty, "
         f"mixed list with nested tool_result, image, bare strings); differing: {bad}")


def grp_pattern_unavailable() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (proj, f, db), _ = _pattern_tree(td)
        con = UX.connect(db)
        undo = _patch(UX, "PATTERN_SOURCES",
                      (("kme", "wiki/tools/no_such_pattern_source.py", "KME_RE"),))
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            pv = con.execute("SELECT pat_ver FROM files WHERE path=?", (str(f),)).fetchone()[0]
            hits = [x[0] for x in con.execute("SELECT pat_hits FROM tool_events")]
            meta_pe = json.loads(con.execute(
                "SELECT v FROM meta WHERE k='last_refresh_status'").fetchone()[0]).get("pattern_error")
            gate("V-UX5-PATTERN-UNAVAILABLE",
                 pv is None and r.get("pattern_error") and meta_pe and all(h is None for h in hits)
                 and r["status"] == "OK",
                 f"source cannot load: pat_ver={pv} (typed absence), refresh pattern_error="
                 f"{r.get('pattern_error')!r}, meta carries it: {bool(meta_pe)}, a hit-bearing input "
                 f"stores {hits} (never a zero count), the burn index itself stays {r['status']}")
        finally:
            undo()
            con.close()
    # control: the same fixture with the real source is fully measured
    with tempfile.TemporaryDirectory() as td2:
        (proj2, f2, db2), _ = _pattern_tree(Path(td2))
        con2 = UX.connect(db2)
        try:
            r2 = UX.refresh(con2, proj2, deadline_s=30)
            pv2 = con2.execute("SELECT pat_ver FROM files WHERE path=?", (str(f2),)).fetchone()[0]
            h2 = con2.execute("SELECT pat_hits FROM tool_events WHERE tool_use_id='tuH'").fetchone()[0]
            gate("V-UX5-PATTERN-UNAVAILABLE-CONTROL",
                 pv2 is not None and h2 is not None and not r2.get("pattern_error"),
                 f"control: with the real source pat_ver={pv2} and the hit is stored ({h2})")
        finally:
            con2.close()


def grp_pattern_drift() -> None:
    """A pass under a different pattern never re-tags a file whose earlier rows were measured
    under the first one: its pat_ver stops matching meta pattern_set (plan 04 refuses on that)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (proj, f, db), _ = _pattern_tree(td)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            pv1 = con.execute("SELECT pat_ver FROM files WHERE path=?", (str(f),)).fetchone()[0]
            undo = _patch(UX, "PATTERN_SOURCES",
                          (("kme", "wiki/tools/kme_token_audit.py", "PATH_KME_RE"),))
            try:
                with f.open("a", encoding="utf-8") as fh:
                    fh.write(asst("m2", 2, "S1", tools=[("tuX", "Bash", {"command": "ls"})]))
                UX.refresh(con, proj, deadline_s=30)
            finally:
                undo()
            pv2 = con.execute("SELECT pat_ver FROM files WHERE path=?", (str(f),)).fetchone()[0]
            ps = con.execute("SELECT v FROM meta WHERE k='pattern_set'").fetchone()[0]
            gate("V-UX5-PATTERN-DRIFT-NOT-RETAGGED", pv1 is not None and pv2 != ps,
                 f"first pass pat_ver={pv1}; after a pass under another pattern the file's "
                 f"pat_ver={pv2} is not the new pattern_set {ps} (mixed file never claims one set)")
        finally:
            con.close()


def grp_result_head() -> None:
    """spawns.result_head (v3 column, kept: v4 data is never dropped) stays at its 200-char
    ceiling, so the only free text the index holds is bounded."""
    body = "R" * 5000
    lines = [user_prompt("P1", 1, "S1"),
             asst("m1", 1.1, "S1",
                  tools=[("tuAG", "Agent", {"subagent_type": "Explore", "prompt": "p"})]),
             user_result(1.2, "S1", "tuAG", body)]
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, f, db = one_file_db(td, lines)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            head = con.execute("SELECT result_head FROM spawns WHERE tool_use_id='tuAG'").fetchone()[0]
            gate("V-UX5-RESULT-HEAD-BOUND", head is not None and len(head) == UX.RESULT_HEAD == 200,
                 f"spawns.result_head holds {len(head or '')} of {len(body)} chars (ceiling "
                 f"{UX.RESULT_HEAD}); the column is kept, not widened, not dropped")
        finally:
            con.close()


# -- plan 03 task 2: project and workstream attribution from a discovered registry -----------

APPS = "C:\\Users\\User\\Apps\\"


def pname(cwd: str) -> str:
    """The project name the registry gives a launch cwd (the transcript dir name Claude Code uses)."""
    return TIS.project_key(cwd)


def sess_file(proj: Path, cwd: str, sid: str, tool_paths, h: float = 1.0) -> Path:
    """projects/<store of cwd>/<sid>.jsonl: a prompt and one assistant line reading `tool_paths`."""
    tools = [(f"tu{sid}{i}", "Read", {"file_path": p}) for i, p in enumerate(tool_paths)]
    return _write(proj / pname(cwd) / f"{sid}.jsonl",
                  user_prompt("P" + sid, h, sid, cwd=cwd)
                  + asst("m" + sid, h + 0.1, sid, tools=tools, cwd=cwd))


def attr_of(db_con, store_cwd: str, sid: str) -> dict:
    return UX.attribution(db_con, pname(store_cwd), sid)


def grp_attr_mixed() -> None:
    A, B = APPS + "alpha", APPS + "beta"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        sess_file(proj, A, "SA", [A + "\\a.py", B + "\\b.py"])
        sess_file(proj, A, "SC", ["C:\\USERS\\User\\Apps\\alpha\\c.py",
                                  "C:\\Users\\User\\AppData\\Local\\Temp\\x.tmp"])
        sess_file(proj, A, "SW", [A + "\\.planning\\workstreams\\ws-one\\STATE.md",
                                  A + "\\.planning\\workstreams\\ws-two\\x.md"])
        sess_file(proj, B, "SB", [B + "\\b2.py"])
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            sa, sb, sc, sw = (attr_of(con, A, "SA"), attr_of(con, B, "SB"),
                              attr_of(con, A, "SC"), attr_of(con, A, "SW"))
            gate("V-UX5-MIXED-BOTH",
                 r["status"] == "OK"
                 and sa["projects"] == {pname(A): {"home": 2}, pname(B): {"touched": 1}}
                 and sa["mixed"] is True,
                 f"launched in alpha, reads under alpha and under registered beta: projects="
                 f"{sa['projects']} mixed={sa['mixed']}")
            gate("V-UX5-MIXED-CONTROL",
                 sb["projects"] == {pname(B): {"home": 2}} and sb["mixed"] is False,
                 f"all paths under the launch root: exactly one project row {sb['projects']} "
                 f"mixed={sb['mixed']}")
            names = [x[0] for x in con.execute("SELECT DISTINCT name FROM file_attribution "
                                               "WHERE kind='project'")]
            bucket = con.execute("SELECT name, role, n FROM file_attribution WHERE kind='bucket' "
                                 "AND file LIKE '%SC.jsonl'").fetchall()
            gate("V-UX5-UNATTRIBUTED-BUCKET",
                 sc["unattributed"] == 1 and bucket == [(UX.UNATTRIBUTED, "touched", 1)]
                 and not any("appdata" in n.lower() for n in names)
                 and sc["projects"] == {pname(A): {"home": 2}},
                 f"an AppData path counts in the <unattributed> bucket {bucket} and names no project "
                 f"(project names {sorted(names)}); an upper-cased Windows path still resolves under "
                 f"its root (home={sc['projects']})")
            gate("V-UX5-WORKSTREAM",
                 sw["workstreams"] == {"ws-one": {"touched": 1}, "ws-two": {"touched": 1}}
                 and sb["workstreams"] == {} and sa["workstreams"] == {},
                 f"two workstream rows {sw['workstreams']}; control: sessions without such paths "
                 f"have none ({sb['workstreams']}, {sa['workstreams']})")
        finally:
            con.close()


def grp_attr_nested() -> None:
    K, S, B = APPS + "core", APPS + "core\\server", APPS + "beta"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        sess_file(proj, K, "SK", [S + "\\x.py", K + "\\y.py"])
        sess_file(proj, S, "SS", [S + "\\z.py"])
        sess_file(proj, B, "SB", [S + "\\x.py"])
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            sk, sb = attr_of(con, K, "SK"), attr_of(con, B, "SB")
            gate("V-UX5-NESTED-ROOT-STAYS-HOME",
                 sk["projects"] == {pname(K): {"home": 3}}
                 and sb["projects"] == {pname(B): {"home": 1}, pname(S): {"touched": 1}},
                 f"a path under the home root AND under nested registered root core\\server stays "
                 f"home ({sk['projects']}); control: from another root the same path is the nested "
                 f"root's, the longest match ({sb['projects']})")
        finally:
            con.close()


def grp_attr_segment() -> None:
    F, S = APPS + "Core-Files", APPS + "Core-Files-Server"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        sess_file(proj, F, "SF", [S + "\\q.py", F + "\\w.py"])
        sess_file(proj, S, "SS", [F + "\\r.py"])
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            sf, ss = attr_of(con, F, "SF"), attr_of(con, S, "SS")
            gate("V-UX5-SEGMENT-PREFIX",
                 sf["projects"] == {pname(F): {"home": 2}, pname(S): {"touched": 1}}
                 and ss["projects"] == {pname(S): {"home": 1}, pname(F): {"touched": 1}},
                 f"Core-Files-Server is never under Core-Files: {sf['projects']}; and the reverse "
                 f"direction {ss['projects']}")
        finally:
            con.close()


def _order_tree(td: Path, first: str) -> Path:
    """Two stores whose sessions read each other's roots. The `first` store's files are the
    only ones new enough for the first pass (since_epoch), so the two builds ingest in opposite
    orders."""
    A, B = APPS + "alpha", APPS + "beta"
    proj = td / "projects"
    fa = sess_file(proj, A, "SA", [A + "\\a.py", B + "\\b.py"])
    fb = sess_file(proj, B, "SB", [B + "\\b2.py", A + "\\a2.py"])
    new, old = (fa, fb) if first == "A" else (fb, fa)
    os.utime(new, (2_000_000_100, 2_000_000_100))
    os.utime(old, (1_000_000_000, 1_000_000_000))
    return proj


def _attr_dump(con) -> list:
    return [(Path(r[0]).parent.name + "/" + Path(r[0]).name,) + tuple(r[1:]) for r in con.execute(
        "SELECT file, kind, name, role, n FROM file_attribution ORDER BY 1,2,3,4,5")]


def grp_attr_order() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dumps, mids = [], []
        for first in ("A", "B"):
            sub = td / first
            proj = _order_tree(sub, first)
            con = UX.connect(sub / "db" / "ix.sqlite")
            try:
                UX.refresh(con, proj, deadline_s=30, since_epoch=1_500_000_000)
                mids.append(_attr_dump(con))
                UX.refresh(con, proj, deadline_s=30)
                dumps.append(_attr_dump(con))
            finally:
                con.close()
        gate("V-UX5-ATTR-ORDER-INDEPENDENT",
             dumps[0] == dumps[1] and len(dumps[0]) >= 4 and mids[0] != dumps[0]
             and mids[1] != dumps[1] and mids[0] != mids[1],
             f"two ingest orders end with identical file_attribution rows ({len(dumps[0])} rows); "
             f"control: the half-built states differ from the final ones and from each other, so "
             f"the equality is not the trivial case")


def grp_attr_no_open() -> None:
    A, B = APPS + "alpha", APPS + "beta"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        sess_file(proj, B, "SB", [B + "\\b2.py", A + "\\a2.py"])
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            before = attr_of(con, B, "SB")
            sess_file(proj, A, "SA", [A + "\\a.py"])
            with Spy(proj) as spy:
                r = UX.refresh(con, proj, deadline_s=30)
            after = attr_of(con, B, "SB")
            in_beta = [p for p in spy.opened if "/" + pname(B) + "/" in p]
            in_alpha = [p for p in spy.opened if "/" + pname(A) + "/" in p]
            gate("V-UX5-ATTR-NO-OPEN",
                 r["status"] == "OK" and not in_beta and before["unattributed"] == 1
                 and before["projects"] == {pname(B): {"home": 2}}
                 and after["unattributed"] == 0
                 and after["projects"] == {pname(B): {"home": 2}, pname(A): {"touched": 1}},
                 f"a new launch root recomputed the old session without opening it (opens under "
                 f"its store: {len(in_beta)}); before {before['projects']} unattributed="
                 f"{before['unattributed']}, after {after['projects']} unattributed="
                 f"{after['unattributed']}")
            gate("V-UX5-ATTR-NO-OPEN-CONTROL", len(in_alpha) >= 1,
                 f"the same spy sees the new store's file being read ({len(in_alpha)} opens): it "
                 f"can fire")
        finally:
            con.close()


# -- plan 04 task 1: population against the champion's own classifier ---------------------------
# The champion side is wiki/tools/kme_pillars.py (scan_project with make_keep(None, U), finish_session,
# is_kme, population), used read-only; the index side never opens a transcript.

HIT = "grep -rn KobiMapEngine src"          # a tool input KME_RE matches
MISS = "ls -la"
U_H = 10                                    # the freeze instant, hours after T0
TOT_FIELDS = ("sessions_active", "sessions_dead", "calls", "cache_read", "input", "cache_write",
              "output")


def _tool_lines(sid, prefix, plan, cwd=WINCWD):
    """plan = [(hour | None, hit)]: one assistant line with one Bash tool_use each; hour None
    writes the line without a timestamp."""
    out = []
    for i, (h, hit) in enumerate(plan):
        ln = asst(f"{prefix}{i}", 0 if h is None else h, sid,
                  tools=[(f"{prefix}t{i}", "Bash", {"command": HIT if hit else MISS})],
                  cr=100 + i, cwd=cwd)
        out.append(no_ts(ln) if h is None else ln)
    return out


def kme_tree(td: Path) -> Path:
    """Hermetic projects root covering every selection case of the champion."""
    proj = td / "projects"
    alpha = proj / "C--Users-User-Apps-alpha"

    def sess(d, sid, lines):
        _write(d / f"{sid}.jsonl", "".join(lines))

    sess(alpha, "STRONG", [user_prompt("PS", 0.5, "STRONG")]
         + _tool_lines("STRONG", "s", [(1, 1), (2, 1), (3, 1), (4, 1), (11, 1), (12, 1)]))
    _write(alpha / "STRONG" / "subagents" / "agent-1.jsonl",
           "".join(_tool_lines("STRONG", "a", [(2.5, 1), (11, 1)])))
    sess(alpha, "WEAK", _tool_lines("WEAK", "w", [(1 + 0.1 * i, i in (3, 9)) for i in range(20)]))
    sess(alpha, "NONE", _tool_lines("NONE", "n", [(h, 0) for h in (1, 2, 3, 4, 5)]))
    sess(alpha, "AFTER", _tool_lines("AFTER", "f", [(1, 0), (2, 0), (3, 0), (11, 1), (12, 1),
                                                   (13, 1), (14, 1)]))
    sess(alpha, "FUTURE", [user_prompt("PF", 12, "FUTURE")]
         + _tool_lines("FUTURE", "u", [(12, 1), (13, 1)]))
    sess(alpha, "NOTS", _tool_lines("NOTS", "t", [(None, 1), (2, 1), (None, 1), (3, 1)]))
    sess(alpha, "USERKME", _tool_lines("USERKME", "k", [(1 + 0.2 * i, i == 4) for i in range(10)])
         + [plain_user("please map the KME arena", 1.5), plain_user("and check the KME spawns", 1.6)])
    sess(alpha, "LATERCWD", [asst("l0", 1, "LATERCWD", tools=[("lt0", "Bash", {"command": MISS})]),
                             asst("l1", 2, "LATERCWD", tools=[("lt1", "Bash", {"command": MISS})],
                                  cwd="C:\\Users\\User\\Apps\\kme-lab")])
    sess(proj / "C--Users-User-Apps-KobiMapEngine", "PATHPROJ",
         _tool_lines("PATHPROJ", "p", [(1, 0), (2, 0)]))
    sess(proj / "C--Users-User-Apps-beta", "CWDKME",
         _tool_lines("CWDKME", "c", [(1, 0), (2, 0)], cwd="C:\\Users\\User\\Apps\\kme-sandbox"))
    sess(proj / "-home-kobii-kobii-a5-env", "HOSTA5",
         _tool_lines("HOSTA5", "h", [(1, 0), (2, 0)], cwd="/home/kobii/a5"))
    sess(proj / "_archived" / "C--Users-User-Apps-alpha-old", "ARCH1",
         _tool_lines("ARCH1", "r", [(1, 1), (2, 1)]))
    return proj


UNTIL = T0 + U_H * 3600


def champion_pop(proj: Path, host):
    """The frozen instrument on the live project dirs of `proj`: scan_project with
    make_keep(None, U), finish_session, population (kme_pillars), existence counted by wrapping
    the keep predicate per session (the champion's own `kept` notion)."""
    import collections
    wt = str(HERE.parent / "wiki" / "tools")
    if wt not in sys.path:
        sys.path.insert(0, wt)
    import kme_pillars as kp
    import kme_report as kr
    import kme_token_audit as kta
    keep = kp.make_keep(None, datetime.fromtimestamp(UNTIL, timezone.utc))
    sessions, kept_by_id, exists, selected = [], {}, {}, set()
    for d in sorted(p for p in proj.iterdir() if p.is_dir() and p.name != "_archived"):
        kc = collections.Counter()

        def counting(path, o, d=d, kc=kc):
            r = keep(path, o)
            if r:
                rel = os.path.relpath(path, str(d)).replace("\\", "/")
                kc[rel.split("/")[0].replace(".jsonl", "")] += 1
            return r

        for s in kta.scan_project(str(d), keep=counting):
            kta.finish_session(s, host)
            sessions.append(s)
            kept_by_id[id(s)] = kc[s["session"]]
            if kc[s["session"]] > 0:
                key = (s["project"], s["session"])
                exists[key] = (s["class"], s["main"].get("calls", 0) + s["sub"].get("calls", 0),
                               s["main"].get("cr", 0) + s["sub"].get("cr", 0))
                if kr.is_kme(s):
                    selected.add(key)
    pop = kp.population(sessions, {"select": "kme"}, kept_by_id, True)
    return {"exists": exists, "selected": selected, "totals": {f: pop[f] for f in TOT_FIELDS}}


def kme_db(td: Path):
    proj = kme_tree(td)
    con = UX.connect(td / "db" / "ix.sqlite")
    UX.refresh(con, proj, deadline_s=60)
    return proj, con


def grp_kme_parity() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, con = kme_db(td)
        try:
            champ = champion_pop(proj, "gex44")
            pop = UX.population(con, until=UNTIL, select="kme", host="gex44", detail=True)
            rows = {(r["project"], r["session_key"]): r for r in pop.get("detail") or []}
            mine = {k: (r["class"], r["calls"], r["cache_read"]) for k, r in rows.items()}
            msel = {k for k, r in rows.items() if r["selected"]}
            tot = pop.get("population") or {}
            same_tot = all(tot.get(f) == champ["totals"][f] for f in TOT_FIELDS)
            gate("V-UX5-KME-CLASSIFIER-PARITY",
                 pop.get("verdict") == "MEASURED" and mine == champ["exists"]
                 and msel == champ["selected"] and same_tot,
                 f"index vs champion at U={U_H}h: sessions equal={mine == champ['exists']} "
                 f"(index {len(mine)}, champion {len(champ['exists'])}), selected equal="
                 f"{msel == champ['selected']} ({len(msel)}), totals equal={same_tot} "
                 f"(index {tot}, champion {champ['totals']}); verdict={pop.get('verdict')} "
                 f"reasons={pop.get('reasons')}")
            classes = {v[0] for v in champ["exists"].values()}
            nocut = UX.population(con, select="kme", host="gex44", detail=True)
            nrows = {(r["project"], r["session_key"]): r for r in nocut.get("detail") or []}
            lap = UX.population(con, until=UNTIL, select="kme", host="laptop", detail=True)
            lrows = {(r["project"], r["session_key"]): r["selected"] for r in lap.get("detail") or []}
            a5 = ("-home-kobii-kobii-a5-env", "HOSTA5")
            alpha = "C--Users-User-Apps-alpha"
            gate("V-UX5-KME-PARITY-NONDEGENERATE",
                 classes == {"KME_PATH", "KME_STRONG", "KME_WEAK", "NONE"}
                 and (alpha, "FUTURE") not in champ["exists"]
                 and champ["exists"][(alpha, "AFTER")][0] == "NONE"
                 and nrows[(alpha, "AFTER")]["class"] == "KME_STRONG"
                 and (alpha, "FUTURE") in nrows
                 and a5 in champ["selected"] and lrows.get(a5) is False
                 and 0 < len(champ["selected"]) < len(champ["exists"]),
                 f"the fixture exercises all four classes {sorted(classes)}; the session that turns "
                 f"KME only after U is NONE at U but KME_STRONG without the cut; the session that "
                 f"starts after U does not exist at U; the host rule selects the a5 env only for "
                 f"gex44 (laptop: {lrows.get(a5)}); {len(champ['selected'])} of "
                 f"{len(champ['exists'])} sessions selected")
        finally:
            con.close()


def _pop_cli(db: Path, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = UX.main(["population", "--db", str(db), *argv])
        except SystemExit as e:             # argparse usage error: exit code 2
            rc = e.code
    try:
        return rc, json.loads(buf.getvalue())
    except ValueError:
        return rc, {}


def grp_pop_verdicts() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, con = kme_db(td)
        try:
            champ = champion_pop(proj, "gex44")
            ef = td / "expect.json"
            ef.write_text(json.dumps({"FIX": champ["totals"]}), encoding="utf-8")
            db = td / "db" / "ix.sqlite"
            base = ["--until", iso(U_H), "--select", "kme", "--host", "gex44", "--expect", "FIX",
                    "--expect-file", str(ef)]
            rc0, o0 = _pop_cli(db, *base)
            rc1, o1 = _pop_cli(db, *base, "--perturb", "calls=1")
            gate("V-UX5-POP-EXACT",
                 rc0 == 0 and o0.get("verdict") == "EXACT" and not o0.get("deltas")
                 and all(o0.get("secondary", {}).get(f, {}).get("match") is True
                         for f in ("input", "cache_write", "output")),
                 f"expected = the champion totals {champ['totals']}: cli exit={rc0} "
                 f"verdict={o0.get('verdict')} deltas={o0.get('deltas')} reasons={o0.get('reasons')}")
            d1 = (o1.get("deltas") or {}).get("calls", {})
            gate("V-UX5-POP-DRIFTED",
                 rc1 == 1 and o1.get("verdict") == "DRIFTED" and d1.get("delta") == -1
                 and set(o1.get("deltas") or {}) == {"calls"},
                 f"the same expectation with calls+1: cli exit={rc1} verdict={o1.get('verdict')} "
                 f"deltas={o1.get('deltas')} (want exactly calls, delta -1)")
        finally:
            con.close()


def grp_archived_rule() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "projects"
        _write(proj / "C--p1" / "S1.jsonl", user_prompt("PL", 1, "S1") + asst("l1", 1.1, "S1")
               + asst("l2", 1.2, "S1"))
        _write(proj / "_archived" / "C--p1" / "S1.jsonl", user_prompt("PT", 2, "S1")
               + asst("t1", 2.1, "S1", cr=7))
        _write(proj / "_archived" / "C--old" / "S9.jsonl", user_prompt("PO", 3, "S9")
               + asst("o1", 3.1, "S9", cr=40) + asst("o2", 3.2, "S9", cr=41))
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            d = UX.population(con)
            i = UX.population(con, include_archived=True)
            dr, ir = d.get("reconcile") or {}, i.get("reconcile") or {}
            dp, ip = d.get("population") or {}, i.get("population") or {}
            ex_d, tw_d = dr.get("archived_excluded") or {}, dr.get("archived_twins") or {}
            ex_i, tw_i = ir.get("archived_excluded") or {}, ir.get("archived_twins") or {}
            gate("V-UX5-ARCHIVED-RULE",
                 d.get("verdict") == "MEASURED" and dp.get("sessions_active") == 1
                 and dp.get("calls") == 2 and dp.get("cache_read") == 200
                 and (ex_d.get("sessions"), ex_d.get("calls"), ex_d.get("cache_read")) == (1, 2, 81)
                 and (tw_d.get("sessions"), tw_d.get("calls"), tw_d.get("cache_read")) == (1, 1, 7)
                 and ip.get("sessions_active") == 2 and ip.get("calls") == 4
                 and ip.get("cache_read") == 281
                 and ex_i.get("sessions") == 0 and ex_i.get("calls") == 0
                 and (tw_i.get("sessions"), tw_i.get("calls")) == (1, 1),
                 f"default: live session only (population {dp}), archived_excluded={ex_d} "
                 f"(the non-twin archived session: 1 session, 2 calls, cr 81), archived_twins={tw_d}; "
                 f"include_archived: population {ip} (live + the non-twin archived, never the twin), "
                 f"archived_excluded={ex_i}, archived_twins={tw_i}")
        finally:
            con.close()


def grp_pop_refuses() -> None:
    def named(pop, word):
        return word in " ".join(pop.get("reasons") or [])

    # parse errors: refused, with an admitting control (tolerated and counted)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, f = one_session_store(td)
        with f.open("a", encoding="utf-8") as fh:
            fh.write("this is not json\n")
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            refused = UX.population(con)
            tol = UX.population(con, tolerate_parse_errors=True)
            tp = tol.get("population") or {}
            gate("V-UX5-POP-REFUSES-PARSE",
                 refused.get("verdict") == "UNMEASURED" and named(refused, "parse error")
                 and refused.get("population") is None,
                 f"a bad line in an in-scope file: verdict={refused.get('verdict')} "
                 f"reasons={refused.get('reasons')} population={refused.get('population')}")
            gate("V-UX5-POP-TOLERATES-PARSE",
                 tol.get("verdict") == "MEASURED" and tol.get("parse_errors_tolerated") == 1
                 and tp.get("calls") == 2 and tp.get("cache_read") == 200,
                 f"the same index with tolerate_parse_errors: verdict={tol.get('verdict')} "
                 f"parse_errors_tolerated={tol.get('parse_errors_tolerated')} population={tp}")
            con.execute("UPDATE files SET error='OSError: injected'")
            con.commit()
            ferr = UX.population(con, tolerate_parse_errors=True)
            gate("V-UX5-POP-REFUSES-FILE-ERROR",
                 ferr.get("verdict") == "UNMEASURED" and named(ferr, "file error")
                 and tol.get("verdict") == "MEASURED",
                 f"a file carrying an error: verdict={ferr.get('verdict')} reasons="
                 f"{ferr.get('reasons')}; control (no error): {tol.get('verdict')}")
        finally:
            con.close()

    # legacy coverage: a migrated v4 index is refused; a cold build of the same tree is measured
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, _files, _snap, _todo = make_v4(td)
        con = UX.connect(db)
        cold = UX.connect(td / "cold" / "ix.sqlite")
        try:
            UX.refresh(con, proj, deadline_s=30)
            UX.refresh(cold, proj, deadline_s=30)
            legacy = UX.population(con)
            ctl = UX.population(cold)
            cp = ctl.get("population") or {}
            gate("V-UX5-POP-REFUSES-LEGACY",
                 legacy.get("verdict") == "UNMEASURED" and named(legacy, "incomplete v5 coverage")
                 and ctl.get("verdict") == "MEASURED" and cp.get("calls") == 5,
                 f"migrated v4 index: verdict={legacy.get('verdict')} reasons={legacy.get('reasons')}; "
                 f"control, a cold build of the same tree: {ctl.get('verdict')} calls={cp.get('calls')}")
        finally:
            con.close()
            cold.close()

    # pattern drift: meta (and per-file) pattern identity must equal the champion's current set
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        lines = [user_prompt("P1", 1, "S1"),
                 asst("m1", 1.1, "S1", tools=[("tu1", "Bash", {"command": HIT})])]
        proj, f, db = one_file_db(td, lines)
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
            ok = UX.population(con, select="kme")
            con.execute("UPDATE meta SET v='drifted' WHERE k='pattern_set'")
            con.commit()
            drift = UX.population(con, select="kme")
            plain = UX.population(con)
            con.execute("DELETE FROM meta WHERE k='pattern_set'")
            con.execute("UPDATE files SET pat_ver=NULL")
            con.commit()
            unset = UX.population(con, select="kme")
            gate("V-UX5-POP-REFUSES-PATTERN-DRIFT",
                 drift.get("verdict") == "UNMEASURED" and named(drift, "pattern set")
                 and unset.get("verdict") == "UNMEASURED" and named(unset, "pattern set")
                 and ok.get("verdict") == "MEASURED" and plain.get("verdict") == "MEASURED",
                 f"meta pattern_set changed after ingest: verdict={drift.get('verdict')} "
                 f"reasons={drift.get('reasons')}; files without a pattern identity: "
                 f"{unset.get('verdict')}; controls: unchanged -> {ok.get('verdict')}, a selector "
                 f"that reads no pattern (select all) on the drifted index -> {plain.get('verdict')}")
        finally:
            con.close()


def _pair_db(td: Path, sb_first: bool):
    """SA and SC are KME_STRONG and share the call ma2; SA and SB share the call mshare (SB is
    not selected). sb_first controls which writer ingests mshare first. SD is a byte-identical
    copy of SB: a duplicate file in scope."""
    proj = td / "projects"
    sb = user_prompt("PB", 1, "SB") + asst("mshare", 1.0, "SB", tools=[("tb", "Bash", {"command": MISS})])
    sa = (user_prompt("PA", 1, "SA")
          + asst("mshare", 1.0, "SA", tools=[("ta1", "Bash", {"command": HIT})])
          + asst("ma2", 1.1, "SA", tools=[("ta2", "Bash", {"command": HIT})], cr=200))
    sc = (user_prompt("PC", 1, "SC")
          + asst("ma2", 1.1, "SC", tools=[("tc2", "Bash", {"command": HIT})], cr=200)
          + asst("mc3", 1.2, "SC", tools=[("tc3", "Bash", {"command": HIT})], cr=300))
    unselected = (("C--rb", "SB", sb), ("C--rd", "SD", sb))
    selected = (("C--ra", "SA", sa), ("C--rc", "SC", sc))
    con = UX.connect(td / "db" / "ix.sqlite")
    for grp in ((unselected, selected) if sb_first else (selected, unselected)):
        for d, sid, text in grp:
            _write(proj / d / f"{sid}.jsonl", text)
        UX.refresh(con, proj, deadline_s=30)
    return con


def grp_reconcile() -> None:
    res = {}
    for order in (True, False):
        with tempfile.TemporaryDirectory() as td:
            con = _pair_db(Path(td), order)
            try:
                res[order] = UX.population(con, select="kme", detail=True)
            finally:
                con.close()
    a, b = res[True], res[False]
    pa, pb = a.get("population") or {}, b.get("population") or {}
    ra, rb = a.get("reconcile") or {}, b.get("reconcile") or {}
    fw = (ra.get("first_writer") or {}).get("calls"), (rb.get("first_writer") or {}).get("calls")
    so = ra.get("shared_outside") or {}
    un = ra.get("unique") or {}
    gate("V-UX5-RECONCILE-SHARED",
         a.get("verdict") == "MEASURED" and pa.get("sessions_active") == 2 and pa.get("calls") == 4
         and pa.get("cache_read") == 800 and pa == pb and ra.get("unique") == rb.get("unique")
         and ra.get("shared_outside") == rb.get("shared_outside")
         and so.get("keys") == 1 and so.get("cache_read") == 100
         and un.get("calls") == 3 and un.get("cache_read") == 600
         and ra.get("dup_files_in_scope") == 1
         and fw[0] != fw[1] and sorted(fw) == [2, 3],
         f"selection SA+SC (4 occurrences, 3 unique keys): occurrence totals {pa} equal for both "
         f"ingest orders ({pa == pb}); unique={un}; shared_outside={so} (mshare, present in the "
         f"unselected SB and its copy); duplicate files in scope={ra.get('dup_files_in_scope')}; "
         f"the v4 first-writer figure differs by order: {fw}")


# -- plan 04 task 2: opt-in history backfill, cold build, CLI cost counters -------------------------

V5_ROW_TABLES = (("call_files", "k, file"), ("tool_events", "file, tool_use_id"),
                 ("user_hits", "file, off"), ("file_cwds", "file, cwd"),
                 ("file_attribution", "file, kind, name, role"))
V5_FILE_STATE = "path, v5_from, first_ts, last_ts, head_sha, tail_sha, content_id, pat_ver, parse_errors, dup_of"


def v5_rows(con) -> dict:
    """Every v5 row and the v5 columns of `files`, in a comparable order."""
    out = {t: con.execute(f"SELECT * FROM {t} ORDER BY {o}").fetchall() for t, o in V5_ROW_TABLES}
    out["files"] = con.execute(f"SELECT {V5_FILE_STATE} FROM files ORDER BY path").fetchall()
    return out


def _legacy_db(td: Path):
    """A v4-shaped index of two_file_store, then migrated by one refresh (every file legacy)."""
    proj, db, files, snap, _todo = make_v4(td)
    con = UX.connect(db)
    UX.refresh(con, proj, deadline_s=30)
    return proj, db, files, con


def grp_backfill() -> None:
    expected = {"sessions_active": 2, "sessions_dead": 0, "calls": 5, "cache_read": 410}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, con = _legacy_db(td)
        try:
            before = UX.population(con)
            offs = sum(r[0] for r in con.execute("SELECT offset FROM files"))
            snap = snapshot(con)
            legacy_n = con.execute("SELECT count(*) FROM files WHERE v5_from IS NULL").fetchone()[0]
            r1 = UX.backfill_v5(con, proj)
            after = snapshot(con)
            v5f = [r[0] for r in con.execute("SELECT v5_from FROM files")]
            pop = UX.population(con, expected=expected)
            r2 = UX.backfill_v5(con, proj)
            cold = UX.connect(td / "cold" / "ix.sqlite")
            try:
                UX.refresh(cold, proj, deadline_s=30)
                same_as_cold = v5_rows(con) == v5_rows(cold)
            finally:
                cold.close()
            gate("V-UX5-BACKFILL",
                 before.get("verdict") == "UNMEASURED" and legacy_n == 2
                 and r1.get("status") == "OK" and r1.get("files_backfilled") == 2
                 and r1.get("bytes_reread") == offs and r1.get("pending") == 0
                 and after == snap and v5f == [0, 0] and pop.get("verdict") == "EXACT"
                 and r2.get("files_backfilled") == 0 and r2.get("bytes_reread") == 0
                 and same_as_cold,
                 f"legacy index: population {before.get('verdict')}; backfill: {r1}; bytes below the "
                 f"committed offsets = {offs}; v4 row counts and offsets unchanged={after == snap}; "
                 f"v5_from={v5f}; population against the expected record: {pop.get('verdict')}; "
                 f"second backfill reads {r2.get('bytes_reread')} bytes in {r2.get('files_backfilled')} "
                 f"files; every v5 row equals a cold build of the tree: {same_as_cold}")
        finally:
            con.close()


def grp_backfill_stops_at_offset() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, con = _legacy_db(td)
        try:
            offs = {r[0]: r[1] for r in con.execute("SELECT path, offset FROM files")}
            tail = asst("m6", 3.0, "S2", tools=[("tuNew", "Read", {"file_path": WINPATH})], cr=70)
            with files[1].open("a", encoding="utf-8") as fh:
                fh.write(tail)
            r1 = UX.backfill_v5(con, proj)
            offs_after = {r[0]: r[1] for r in con.execute("SELECT path, offset FROM files")}
            leaked = con.execute("SELECT count(*) FROM tool_events WHERE tool_use_id='tuNew'").fetchone()[0]
            leaked_c = con.execute("SELECT count(*) FROM call_files WHERE k='m6|rm6'").fetchone()[0]
            r2 = UX.refresh(con, proj, deadline_s=30)
            cold = UX.connect(td / "cold" / "ix.sqlite")
            try:
                UX.refresh(cold, proj, deadline_s=30)
                same_as_cold = v5_rows(con) == v5_rows(cold)
            finally:
                cold.close()
            gate("V-UX5-BACKFILL-STOPS-AT-OFFSET",
                 r1.get("bytes_reread") == sum(offs.values()) and offs_after == offs
                 and leaked == 0 and leaked_c == 0
                 and r2.get("files_read") == 1 and r2.get("bytes_ingested") == len(tail.encode("utf-8"))
                 and same_as_cold,
                 f"a legacy file grew past its offset: backfill read {r1.get('bytes_reread')} bytes "
                 f"(committed offsets {sum(offs.values())}), offsets unchanged={offs_after == offs}, "
                 f"the appended tool event / call leaked in={leaked}/{leaked_c}; the next refresh "
                 f"read {r2.get('files_read')} file and ingested {r2.get('bytes_ingested')} of "
                 f"{len(tail.encode('utf-8'))} tail bytes; every v5 row equals a cold build: "
                 f"{same_as_cold}")
        finally:
            con.close()


def _cli_refresh(db: Path, proj: Path, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = UX.main(["refresh", "--db", str(db), "--proj", str(proj), *argv])
    return rc, json.loads(buf.getvalue())


def grp_cold_all() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, files = two_file_store(td)
        old = T0 - 60 * 86400
        os.utime(files[1], (old, old))
        rc_d, dflt = _cli_refresh(td / "d" / "ix.sqlite", proj)
        rc_a, allr = _cli_refresh(td / "a" / "ix.sqlite", proj, "--all")
        rc_z, zero = _cli_refresh(td / "z" / "ix.sqlite", proj, "--since-days", "0")
        gate("V-UX5-COLD-ALL",
             rc_d == 0 and dflt["files_seen"] == 2 and dflt["files_read"] == 1
             and rc_a == 0 and allr["files_read"] == allr["files_seen"] == 2
             and zero["files_read"] == zero["files_seen"] == 2,
             f"a transcript 60 days old: default refresh files_read={dflt['files_read']} of "
             f"files_seen={dflt['files_seen']}; refresh --all files_read={allr['files_read']} of "
             f"{allr['files_seen']}; --since-days 0 files_read={zero['files_read']} of "
             f"{zero['files_seen']}")


def grp_cli_cost_keys() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _ = one_session_store(td)
        rc, r = _cli_refresh(td / "ix.sqlite", proj)
        proc = r.get("proc") or {}
        saved = UX.PROC_IO
        UX.PROC_IO = str(td / "no-such-io-file")
        try:
            _rc2, r2 = _cli_refresh(td / "ix2.sqlite", proj)
        finally:
            UX.PROC_IO = saved
        proc2 = r2.get("proc") or {}
        keys = ("wall_s", "bytes_read", "bytes_ingested", "files_opened", "files_seen")
        gate("V-UX5-CLI-COST-KEYS",
             rc == 0 and all(k in r for k in keys) and r["files_opened"] == 1 and r["bytes_read"] > 0
             and r["bytes_read"] == r["bytes_ingested"]
             and set(proc) == {"rchar_delta", "maxrss_kb"}
             and isinstance(proc["rchar_delta"], int) and proc["rchar_delta"] >= r["bytes_read"]
             and isinstance(proc["maxrss_kb"], int) and proc["maxrss_kb"] > 0
             and set(proc2) == {"rchar_delta", "maxrss_kb"} and proc2["rchar_delta"] is None
             and isinstance(proc2["maxrss_kb"], int),
             f"cli refresh keys {[k for k in keys if k in r]}, proc={proc} (rchar_delta >= bytes_read "
             f"{r['bytes_read']}); control, /proc/self/io unreadable: proc={proc2} (rchar_delta null, "
             f"maxrss still reported)")


def grp_pop_until_refused() -> None:
    """CR-01: a --until the CLI cannot read is refused (UNMEASURED, exit 3, a reason), never
    dropped into 'every row counts'. Control: a valid instant on the same index is MEASURED."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, _f = one_session_store(td)
        db = td / "db" / "ix.sqlite"
        con = UX.connect(db)
        try:
            UX.refresh(con, proj, deadline_s=30)
        finally:
            con.close()
        rc_bad, o_bad = _pop_cli(db, "--until", "2026-09-01")
        rc_ok, o_ok = _pop_cli(db, "--until", iso(10))
        gate("V-UX5-POP-UNTIL-REFUSED",
             rc_bad == 3 and o_bad.get("verdict") == "UNMEASURED"
             and any("until" in r for r in o_bad.get("reasons") or [])
             and o_bad.get("population") is None
             and rc_ok == 0 and o_ok.get("verdict") == "MEASURED"
             and (o_ok.get("population") or {}).get("calls") == 2,
             f"--until 2026-09-01 (date only): exit={rc_bad} verdict={o_bad.get('verdict')} "
             f"reasons={o_bad.get('reasons')} population={o_bad.get('population')}; control "
             f"--until {iso(10)}: exit={rc_ok} verdict={o_ok.get('verdict')} "
             f"calls={(o_ok.get('population') or {}).get('calls')}")


def grp_file_error_any() -> None:
    """WR-01: a non-OSError failure inside one transcript (a lone surrogate SQLite cannot bind)
    is typed on that file and the pass goes on; it never fails the pass or starves later files."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, files = two_file_store(td)
        bad_line = asst("mx", 1.5, "S1", tools=[("tuX", "Read", {"file_path": "C:\\a\\ud83d"})])
        with files[0].open("a", encoding="utf-8") as fh:
            fh.write(bad_line.replace("\\\\ud83d", "\\ud83d"))     # JSON escape of a lone surrogate
        con = UX.connect(td / "db" / "ix.sqlite")
        try:
            r = UX.refresh(con, proj, deadline_s=30)
            bad = con.execute("SELECT error, offset FROM files WHERE path=?",
                              (os.path.realpath(str(files[0])),)).fetchone()
            other = con.execute("SELECT count(*) FROM calls WHERE file=?",
                                (os.path.realpath(str(files[1])),)).fetchone()[0]
            pop = UX.population(con)
            gate("V-UX5-FILE-ERROR-ANY",
                 r.get("status") == "OK" and bad is not None
                 and (bad[0] or "").startswith("UnicodeEncodeError") and bad[1] == 0
                 and other == 2 and r.get("files_with_errors") == 1
                 and pop.get("verdict") == "UNMEASURED",
                 f"lone surrogate in one transcript: pass status={r.get('status')} "
                 f"error={r.get('error')!r}; that file's error={bad and bad[0]!r} offset="
                 f"{bad and bad[1]}; the other file's calls={other}/2; files_with_errors="
                 f"{r.get('files_with_errors')}; population={pop.get('verdict')} {pop.get('reasons')}")
        finally:
            con.close()


def grp_legacy_home() -> None:
    """WR-02: a legacy file that grows is read from mid-file, so the first cwd it shows is not
    the session's launch cwd. Its home is unknown (absent from the registry), never guessed.
    Control: a cold build of the same tree names the true launch cwd."""
    other = "C:\\Users\\User\\Apps\\elsewhere"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj, db, files, con = _legacy_db(td)
        try:
            with files[0].open("a", encoding="utf-8") as fh:
                fh.write(asst("m9", 1.9, "S1", cwd=other))
            UX.refresh(con, proj, deadline_s=30)
            v5f = con.execute("SELECT v5_from FROM files WHERE path=?",
                              (os.path.realpath(str(files[0])),)).fetchone()[0]
            reg, homes, _d = UX._registry(con)
            home = homes.get(("C--p1", "C--p1", "S1"))
            guessed = [k for k in reg if "elsewhere" in k.lower()]
            cold = UX.connect(td / "cold" / "ix.sqlite")
            try:
                UX.refresh(cold, proj, deadline_s=30)
                creg, chomes, _cd = UX._registry(cold)
            finally:
                cold.close()
            chome = [v for (s, p, k), v in chomes.items() if k == "S1"]
            gate("V-UX5-LEGACY-HOME-UNKNOWN",
                 (v5f or 0) > 0 and not guessed
                 and not [v for (s, p, k), v in homes.items() if k == "S1"]
                 and len(chome) == 1 and "proj" in chome[0].lower(),
                 f"legacy file grew with a new cwd: v5_from={v5f}; registry roots from it="
                 f"{guessed}; S1 home={home} (want none); cold build S1 home={chome}")
        finally:
            con.close()


GROUPS = (("grp_schema", grp_schema), ("grp_tool_event", grp_tool_event),
          ("grp_occurrence", grp_occurrence), ("grp_migrate", grp_migrate),
          ("grp_population_empty", grp_population_empty), ("grp_no_raw_text", grp_no_raw_text),
          ("grp_alias", grp_alias), ("grp_identity_columns", grp_identity_columns),
          ("grp_archived", grp_archived), ("grp_shapes", grp_shapes),
          ("grp_identity_fill", grp_identity_fill), ("grp_parse_errors", grp_parse_errors),
          ("grp_partial_line", grp_partial_line), ("grp_file_error", grp_file_error),
          ("grp_content_identity", grp_content_identity), ("grp_crash_resume", grp_crash_resume),
          ("grp_concurrent_refresh", grp_concurrent_refresh), ("grp_migrate_once", grp_migrate_once),
          ("grp_ts_inherit", grp_ts_inherit), ("grp_cwd", grp_cwd),
          ("grp_pattern_source", grp_pattern_source), ("grp_pat_hits", grp_pat_hits),
          ("grp_user_hits", grp_user_hits), ("grp_result_text_parity", grp_result_text_parity),
          ("grp_pattern_unavailable", grp_pattern_unavailable),
          ("grp_pattern_drift", grp_pattern_drift), ("grp_result_head", grp_result_head),
          ("grp_attr_mixed", grp_attr_mixed), ("grp_attr_nested", grp_attr_nested),
          ("grp_attr_segment", grp_attr_segment), ("grp_attr_order", grp_attr_order),
          ("grp_attr_no_open", grp_attr_no_open), ("grp_kme_parity", grp_kme_parity),
          ("grp_pop_verdicts", grp_pop_verdicts), ("grp_archived_rule", grp_archived_rule),
          ("grp_pop_refuses", grp_pop_refuses), ("grp_reconcile", grp_reconcile),
          ("grp_backfill", grp_backfill),
          ("grp_backfill_stops_at_offset", grp_backfill_stops_at_offset),
          ("grp_cold_all", grp_cold_all), ("grp_cli_cost_keys", grp_cli_cost_keys),
          ("grp_pop_until_refused", grp_pop_until_refused),
          ("grp_file_error_any", grp_file_error_any), ("grp_legacy_home", grp_legacy_home))


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
    """M3: the call_files upsert of refresh becomes a no-op."""
    head = ('like every other v5 row.\n'
            '                    cts = vals[0] if vals[0] is not None else state["call_ts"].get(c["key"])\n'
            '                    ')
    return _source_mutant("tools/usage_index.py", head + "con.execute(\n",
                          head + "(lambda *a: None)(\n")


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


def _m_bad_line_counter_removed():
    """M7: tis_observed stops counting undecodable complete lines (the counter becomes a no-op),
    swapped in through UX._tis."""
    return _source_mutant("tools/tis_observed.py",
                          '                    stats["bad"] += 1\n',
                          '                    pass\n')


def _m_content_id_head_only():
    """M8: the content id is built from the head hash only, so histories that share a first line
    collapse into one content id."""
    def mutant(end, head, tail):
        return hashlib.sha256(f"{head}".encode()).hexdigest()[:32]
    return _patch(UX, "_content_id", mutant)


def _m_begin_file_always_admits():
    """M9: the per-file snapshot check always admits, so a refresh working from a stale snapshot
    re-ingests files another writer already advanced."""
    def mutant(con, path, prev):
        con.commit()
        con.execute("BEGIN IMMEDIATE")
        return True
    return _patch(UX, "_begin_file", mutant)


def _m_ts_inherit_dropped():
    """M10: the timestamp fallback to the file's last timestamp becomes None (source text)."""
    return _source_mutant(
        "tools/usage_index.py",
        '    ts = own if own is not None else state.get("last_ts")\n',
        '    ts = own if own is not None else None\n')


def _m_pattern_source_drift():
    """M11: the pattern source names another compiled regex of the same file (in-process patch
    of PATTERN_SOURCES), so the registered regex is no longer the champion's KME_RE."""
    return _patch(UX, "PATTERN_SOURCES",
                  (("kme", "wiki/tools/kme_token_audit.py", "PATH_KME_RE"),))


def _m_touched_rows_dropped():
    """M13: the attribution row builder drops every touched row (in-process patch), so a mixed
    session looks like a single-project one."""
    real = UX._attribution_rows

    def mutant(*a, **k):
        return [r for r in real(*a, **k) if r[2] != "touched"]
    return _patch(UX, "_attribution_rows", mutant)


def _m_plain_string_prefix():
    """M14: the segment-prefix helper becomes a plain string prefix (in-process patch)."""
    return _patch(UX, "_under", lambda key, root: key.startswith(root))


def _m_user_length_guard_removed():
    """M12: the human-text length guard is removed (source text)."""
    return _source_mutant("tools/usage_index.py",
                          "and len(tx) < USER_TEXT_MAX", "and True")


def _m_archived_exclusion_removed():
    """M15: the archived exclusion of population is removed (source text), so a default answer
    counts `_archived` sessions."""
    return _source_mutant("tools/usage_index.py",
                          'if f["archived"] and not include_archived:',
                          'if False:')


def _m_time_cut_removed():
    """M16: the time cut is removed from the classifier's feature query (source text), so a
    session is classified on tool uses recorded after the freeze instant."""
    return _source_mutant("tools/usage_index.py",
                          '"WHERE e.pat_hits IS NOT NULL AND " + cut("e.ts"), cp):',
                          '"WHERE e.pat_hits IS NOT NULL AND " + "(? IS NULL OR ? IS NULL OR 1)", cp):')


def _m_calls_from_first_writer():
    """M17: a session's calls are read from calls.file (first writer) instead of the occurrence
    view call_files (source text)."""
    return _source_mutant("tools/usage_index.py",
                          '"coalesce(sum(c.cr),0), coalesce(sum(c.out),0) FROM call_files c "',
                          '"coalesce(sum(c.cr),0), coalesce(sum(c.out),0) FROM calls c "')


def _m_backfill_unbounded():
    """M18: backfill reads without end_offset (in-process patch of calls_from), so it ingests
    bytes the index never consumed."""
    real = UX._tis.calls_from

    def mutant(path, offset=0, on_line=None, stats=None, end_offset=None):
        return real(path, offset, on_line=on_line, stats=stats)
    return _patch(UX._tis, "calls_from", mutant)



def _m_cli_until_dropped():
    """M19 (CR-01): the CLI turns an unreadable --until into None before population sees it."""
    return _source_mutant("tools/usage_index.py",
                          "        res = population(con, until=a.until,",
                          "        res = population(con, until=_epoch(a.until) if a.until else None,")


def _m_file_error_oserror_only():
    """M20 (WR-01): the per-file handler types only OSError again."""
    return _source_mutant("tools/usage_index.py",
                          "            except Exception as e:  # noqa: BLE001 -- this file only:",
                          "            except OSError as e:  # noqa: BLE001 -- this file only:")


def _m_legacy_home_guessed():
    """M21 (WR-02): a main file read from mid-file names its session's home root again."""
    return _source_mutant("tools/usage_index.py",
                          "WHERE f.is_sub=0 AND f.v5_from=0 AND c.first_off=",
                          "WHERE f.is_sub=0 AND c.first_off=")


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
    ("M7 undecodable-line counter removed", _m_bad_line_counter_removed,
     [grp_parse_errors], ["V-UX5-PARSE-ERROR-SURFACED"]),
    ("M8 content id built from the head hash only", _m_content_id_head_only,
     [grp_content_identity], ["V-UX5-HISTORIES-NOT-MERGED"]),
    ("M9 per-file snapshot check always admits", _m_begin_file_always_admits,
     [grp_concurrent_refresh], ["V-UX5-STALE-SNAPSHOT-SKIPS"]),
    ("M10 timestamp inheritance dropped", _m_ts_inherit_dropped,
     [grp_ts_inherit], ["V-UX5-TS-INHERIT"]),
    ("M11 pattern source drifts to another regex", _m_pattern_source_drift,
     [grp_pattern_source], ["V-UX5-PATTERN-SOURCE"]),
    ("M12 human-text length guard removed", _m_user_length_guard_removed,
     [grp_user_hits], ["V-UX5-USER-HITS-FILTER"]),
    ("M13 touched attribution rows dropped", _m_touched_rows_dropped,
     [grp_attr_mixed], ["V-UX5-MIXED-BOTH"]),
    ("M14 segment prefix replaced by a plain string prefix", _m_plain_string_prefix,
     [grp_attr_segment], ["V-UX5-SEGMENT-PREFIX"]),
    ("M15 archived exclusion removed from population", _m_archived_exclusion_removed,
     [grp_archived_rule], ["V-UX5-ARCHIVED-RULE"]),
    ("M16 time cut removed from the classifier feature query", _m_time_cut_removed,
     [grp_kme_parity], ["V-UX5-KME-CLASSIFIER-PARITY"]),
    ("M17 session calls read from calls.file instead of call_files", _m_calls_from_first_writer,
     [grp_reconcile], ["V-UX5-RECONCILE-SHARED"]),
    ("M18 backfill reads past the committed offset", _m_backfill_unbounded,
     [grp_backfill_stops_at_offset], ["V-UX5-BACKFILL-STOPS-AT-OFFSET"]),
    ("M19 unreadable --until dropped to None by the CLI", _m_cli_until_dropped,
     [grp_pop_until_refused], ["V-UX5-POP-UNTIL-REFUSED"]),
    ("M20 per-file handler narrowed back to OSError", _m_file_error_oserror_only,
     [grp_file_error_any], ["V-UX5-FILE-ERROR-ANY"]),
    ("M21 legacy mid-file cwd names the session home", _m_legacy_home_guessed,
     [grp_legacy_home], ["V-UX5-LEGACY-HOME-UNKNOWN"]),
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
