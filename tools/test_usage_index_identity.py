#!/usr/bin/env python3
"""V-UXID-* gates: one transcript store, one identity (plan s12 commit 2, audit G1-G3).

A real directory junction (`mklink /J`) aliases a project dir, as
`projects/C--Users-User-Apps-mcp-video-analyzer` aliases the PP dir on this host
(RCA s16). The alias is named so that it lists BEFORE the real dir: the pre-fix
index then records calls under the alias path, which is the order-dependence
these gates exist to remove. Hermetic; no model call. Windows only: when the
junction cannot be created the run is INCONCLUSIVE (exit 2), never a pass."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import usage_index as ux  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(mid, h, sess, spawn=None, quota=False):
    content = []
    if spawn:
        content.append({"type": "tool_use", "id": spawn, "name": "Agent",
                        "input": {"subagent_type": "Explore", "prompt": "x"}})
    o = {"type": "assistant", "timestamp": iso(h), "sessionId": sess,
         "message": {"model": "claude-opus-5-5", "content": content,
                     "usage": {"input_tokens": 1, "cache_read_input_tokens": 100,
                               "cache_creation_input_tokens": 0, "output_tokens": 5}}}
    if mid:
        o["message"]["id"] = mid
        o["requestId"] = "r" + mid
    if quota:
        o["quotaLimits"] = {"status": "rejected", "rateLimitType": "seven_day",
                            "resetsAt": T0 + 99 * 3600}
    return json.dumps(o) + "\n"


def user(pid, h, sess):
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": sess,
                       "origin": {"kind": "human"}}) + "\n"


def junction(link: Path, target: Path) -> bool:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0 and link.is_dir()


def build_real(proj: Path, name: str, sess: str) -> Path:
    real = proj / name
    (real / sess / "subagents").mkdir(parents=True)
    # one id-less call (an `off|<path>|<offset>` key: the key that embeds the path)
    (real / f"{sess}.jsonl").write_text(
        user("P" + sess, 1, sess) + asst("m" + sess, 1.1, sess, spawn="tu" + sess)
        + asst(None, 1.2, sess, quota=True), encoding="utf-8")
    (real / sess / "subagents" / "agent-a.jsonl").write_text(asst("s" + sess, 1.15, sess),
                                                               encoding="utf-8")
    (real / sess / "subagents" / "agent-a.meta.json").write_text(
        json.dumps({"agentType": "Explore", "toolUseId": "tu" + sess, "spawnDepth": 1}),
        encoding="utf-8")
    return real


def paths(con) -> dict:
    """Every path-bearing column (audit G1 + spawns.parent_k)."""
    q = {"files": "SELECT path FROM files", "calls.file": "SELECT file FROM calls",
         "calls.k": "SELECT k FROM calls WHERE k LIKE 'off|%'", "quota": "SELECT file FROM quota",
         "prompts": "SELECT file FROM prompts", "spawns.file": "SELECT file FROM spawns",
         "spawns.parent_k": "SELECT parent_k FROM spawns", "subagents": "SELECT file FROM subagents"}
    return {k: [r[0] for r in con.execute(s)] for k, s in q.items()}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "projects"
        proj.mkdir()
        real = build_real(proj, "C--zreal", "S1")
        alias = proj / "C--alias"                 # lists BEFORE C--zreal
        if not junction(alias, real):
            print("INCONCLUSIVE: could not create a directory junction (mklink /J)")
            return 2
        other = build_real(proj, "C--other", "S2")  # a distinct dir must stay distinct
        outside = Path(td) / "elsewhere"
        build_real(outside.parent, outside.name, "S3")
        if not junction(proj / "C--outlink", outside):
            print("INCONCLUSIVE: could not create the outside junction")
            return 2

        con = ux.connect(Path(td) / "ix.sqlite")
        r = ux.refresh(con, proj, deadline_s=30)
        ok("V-UXID-REFRESH", r["status"] == "OK", json.dumps(r))
        p = paths(con)
        flat = [v for vs in p.values() for v in vs]
        ok("V-UXID-NO-ALIAS-PATH", not any("C--alias" in v for v in flat),
           f"alias spellings left: {[v for v in flat if 'C--alias' in v][:3]}")
        ok("V-UXID-ONE-IDENTITY", sum("C--zreal" in v for v in p["files"]) == 2,
           f"files under the real dir: {sum('C--zreal' in v for v in p['files'])} (main + subagent)")
        ok("V-UXID-DISTINCT-STAYS", sum("C--other" in v for v in p["files"]) == 2,
           "an unaliased sibling keeps its own identity (control)")
        ok("V-UXID-OUTSIDE-KEPT", sum("C--outlink" in v for v in p["files"]) == 2,
           "a junction whose target is outside the store is still indexed (audit G3)")
        w = ux.window(con, T0, T0 + 10 * 3600)
        ok("V-UXID-TOTALS", w["calls"] == 9 and w["subagent_calls"] == 3,
           f"calls={w['calls']} sub={w['subagent_calls']} (3 dirs x (2 main + 1 subagent))")

        # Migration: an index written by the pre-fix code holds alias rows, including
        # duplicates of canonical ones. Seed them, refresh, require one identity and
        # unchanged totals, with a verified backup taken first.
        a = str(alias) + "\\"
        z = str(real) + "\\"
        seeded = 0
        for table, col in (("files", "path"), ("calls", "file"), ("quota", "file"),
                           ("prompts", "file"), ("spawns", "file"), ("subagents", "file")):
            cols = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
            for row in con.execute(f"SELECT * FROM {table} WHERE {col} LIKE ?", (z + "%",)).fetchall():
                d = dict(zip(cols, row))
                d[col] = a + d[col][len(z):]
                if table == "calls":
                    d["k"] = d["k"].replace(z, a)
                if table == "spawns":
                    d["parent_k"] = d["parent_k"].replace(z, a)
                if table == "prompts":
                    d["prompt_id"] = d["prompt_id"] + "-dup"      # PK; keeps a row to rewrite
                if table == "spawns":
                    d["tool_use_id"] = d["tool_use_id"] + "-dup"
                con.execute(f"INSERT OR IGNORE INTO {table}({','.join(d)}) VALUES"
                            f"({','.join('?' * len(d))})", list(d.values()))
                seeded += 1
        con.commit()
        before = ux.window(con, T0, T0 + 10 * 3600)
        ok("V-UXID-SEED-VISIBLE", seeded >= 8 and before["calls"] > w["calls"],
           f"seeded {seeded} alias rows; window now {before['calls']} calls (duplicates counted)")
        r2 = ux.refresh(con, proj, deadline_s=30)
        p2 = paths(con)
        flat2 = [v for vs in p2.values() for v in vs]
        after = ux.window(con, T0, T0 + 10 * 3600)
        ok("V-UXID-MIGRATED", r2["status"] == "OK" and not any("C--alias" in v for v in flat2),
           f"status={r2['status']} alias left={[v for v in flat2 if 'C--alias' in v][:3]}")
        ok("V-UXID-MIGRATION-TOTALS", after["calls"] == w["calls"]
           and after["cache_read"] == w["cache_read"],
           f"calls {before['calls']} -> {after['calls']} (expected {w['calls']})")
        bk = json.loads((con.execute("SELECT v FROM meta WHERE k='identity_backup'").fetchone()
                         or ["{}"])[0])
        bpath = Path(bk.get("path", ""))
        good = False
        if bpath.is_file():
            b = sqlite3.connect(str(bpath))
            good = (b.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                    and b.execute("SELECT count(*) FROM calls").fetchone()[0] == bk.get("calls"))
            b.close()
        ok("V-UXID-BACKUP-VERIFIED", good and len(bk.get("sha256", "")) == 64,
           f"backup={bpath.name or None} rows={bk.get('calls')} verified={good}")
        r3 = ux.refresh(con, proj, deadline_s=30)
        bk2 = (con.execute("SELECT v FROM meta WHERE k='identity_backup'").fetchone() or [None])[0]
        ok("V-UXID-IDEMPOTENT", r3["status"] == "OK" and bk2 == json.dumps(bk)
           and ux.window(con, T0, T0 + 10 * 3600)["calls"] == w["calls"],
           "a clean index takes no second backup and changes nothing")
        con.close()

    total = PASS + FAIL
    print(f"USAGE_INDEX_IDENTITY_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
