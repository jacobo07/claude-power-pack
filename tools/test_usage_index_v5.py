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


GROUPS = (("grp_schema", grp_schema), ("grp_tool_event", grp_tool_event),
          ("grp_occurrence", grp_occurrence), ("grp_migrate", grp_migrate),
          ("grp_population_empty", grp_population_empty))


def main(argv=None) -> int:
    for name, fn in GROUPS:
        guarded(name, fn)
    total = PASS + FAIL
    print(f"USAGE_INDEX_V5_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
