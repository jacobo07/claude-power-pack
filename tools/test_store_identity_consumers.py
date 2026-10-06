#!/usr/bin/env python3
"""V-SIC-* gates: every ACCOUNTING consumer of ~/.claude/projects reads a store once (plan s14 S1).

`projects/C--Users-User-Apps-mcp-video-analyzer` is a directory junction to the
PP project dir. Measured 2026-10-02 on the live store before this fix: the
tis_observed scan shape yielded 152 transcripts twice, co_12 counted 2,275
sessions for 2,123 distinct ids, sovereign_miner's recursive glob yielded 273
files twice, and budget_monitor counted 1,378 programmatic calls over 7 days
where 1,313 exist (+65, 4.95 %).

Identity is typed: per-call and per-file readers dedupe the STORE by resolved
path (tis_observed.store_dirs); co_12 counts SESSIONS, so it dedupes by session
id, the rule cognitive_os.scheduler and token_autopsy already follow.

Each gate compares a store holding an alias against the same store without it.
Hermetic; no model call. When a junction cannot be created the run is
INCONCLUSIVE (exit 2), never a pass."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "modules" / "cognitive_os"))

import tis_observed as tob  # noqa: E402
import budget_monitor  # noqa: E402
import sovereign_miner as sm  # noqa: E402
import co_12_telemetry as co12  # noqa: E402

PASS = FAIL = 0
NOW = datetime.now(timezone.utc)
S1, S2, S3 = ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222",
              "33333333-3333-3333-3333-333333333333")


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def line(mid, mins_ago, sess):
    ts = (NOW - timedelta(minutes=mins_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    o = {"type": "assistant", "timestamp": ts, "sessionId": sess, "entrypoint": "sdk-cli",
         "message": {"model": "claude-opus-5-5", "content": [],
                     "usage": {"input_tokens": 1, "cache_read_input_tokens": 100,
                               "cache_creation_input_tokens": 0, "output_tokens": 5}}}
    if mid:
        o["message"]["id"] = mid
        o["requestId"] = "r" + mid
    return json.dumps(o) + "\n"


def junction(link: Path, target: Path) -> bool:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                           capture_output=True, text=True)
        return r.returncode == 0 and link.is_dir()
    try:                                          # POSIX: a directory symlink aliases like a junction
        os.symlink(str(target), str(link), target_is_directory=True)
    except OSError:
        return False
    return link.is_dir()


def build(proj: Path, name: str, sess: str) -> Path:
    d = proj / name
    (d / sess / "subagents").mkdir(parents=True)
    (d / f"{sess}.jsonl").write_text(line("m" + sess[:4], 60, sess) + line(None, 50, sess),
                                     encoding="utf-8")
    (d / sess / "subagents" / "agent-a.jsonl").write_text(line("s" + sess[:4], 55, sess),
                                                           encoding="utf-8")
    return d


def store(root: Path, alias: bool) -> Path | None:
    proj = root / "projects"
    proj.mkdir(parents=True)
    real = build(proj, "C--zreal", S1)
    build(proj, "C--other", S2)
    if alias:
        if not junction(proj / "C--alias", real):          # lists BEFORE C--zreal
            return None
        outside = build(root / "elsewhere", "C--ext", S3)   # junction OUT of the store
        if not junction(proj / "C--ext", outside):
            return None
    else:
        build(proj, "C--ext", S3)                           # same content, no alias
    return proj


def measure(proj: Path) -> dict:
    tob.PROJECTS_DIR = proj
    dirs = tob._project_dirs(SimpleNamespace(project_dir=None, all_projects=True))
    tis = tob.summarize(tob.scan(dirs))
    budget = budget_monitor._aggregate_observed(7, None)
    sm.PROJECTS_DIR = str(proj)
    sm.STATS.clear()
    sm.mine_transcripts()
    return {"tis_calls": tis["calls"], "tis_sub": tis["subagent_calls"],
            "tis_sessions": tis["sessions"], "budget_calls": budget.get("calls"),
            "co12_sessions": co12.loop_boundedness(proj)["sessions"],
            "miner_files": sm.STATS["files_total"]}


def usage_index_gates(td: Path, aliased: Path, clean: Path) -> None:
    """usage_index is a CONSUMER of store identity (2026-10-03): its alias map comes
    from tis_observed.store_identity, and the destructive row rewrite follows it."""
    import os
    import re
    import usage_index as ux

    ext_link = aliased / "C--ext"
    ext_real = Path(os.path.realpath(ext_link))
    zreal = Path(os.path.realpath(aliased / "C--zreal"))
    dirs, aliases = tob.store_identity(aliased)
    ok("V-SIC-ALIAS-MAP", aliases == {str(aliased / "C--alias"): str(zreal),
                                      str(ext_link): str(ext_real)}
       and tob.store_dirs(aliased) == dirs,
       f"aliases={aliases}; store_dirs == store_identity()[0]: {tob.store_dirs(aliased) == dirs}")

    # Legacy rows recorded under the two link spellings, as an index built before the
    # identity fix holds them; one call is id-less, so its key embeds the path.
    con = ux.connect(td / "legacy.sqlite")
    try:
        legacy = {"in": aliased / "C--alias" / f"{S1}.jsonl", "out": ext_link / f"{S3}.jsonl"}
        for tag, fp in legacy.items():
            con.execute("INSERT INTO files(path, offset, size, mtime_ns, is_sub) VALUES(?,?,?,?,0)",
                        (str(fp), 10, 10, 1))
            con.execute("INSERT INTO calls(k, file, ts, is_sub, inp, cw, cr, out) "
                        "VALUES(?,?,1.0,0,1,0,100,5)", (f"off|{fp}|0", str(fp)))
        con.commit()
        r = ux._canonicalize(con, aliased)
        files = {row[0] for row in con.execute("SELECT path FROM files")}
        keys = {row[0] for row in con.execute("SELECT k FROM calls")}
        want_out, want_in = str(ext_real / f"{S3}.jsonl"), str(zreal / f"{S1}.jsonl")
        ok("V-SIC-UX-CANON-IN-STORE", want_in in files and f"off|{want_in}|0" in keys,
           f"in-store alias rows -> {want_in}: files={sorted(files)}")
        ok("V-SIC-UX-CANON-OUT-OF-STORE", want_out in files and f"off|{want_out}|0" in keys
           and not any(str(ext_link) in v for v in files | keys),
           f"out-of-store link rows -> RESOLVED {want_out} (S1 decision); rewritten={r.get('rewritten')}")
    finally:
        con.close()

    # Totals: an aliased store indexes exactly what the same store without aliases holds,
    # id-less calls included (their key embeds the path, so a second spelling would add one).
    totals = {}
    for name, proj in (("clean", clean), ("aliased", aliased)):
        c = ux.connect(td / f"{name}.sqlite")
        try:
            ux.refresh(c, proj, deadline_s=30)
            totals[name] = c.execute("SELECT count(*), sum(cr) FROM calls").fetchone()
        finally:
            c.close()
    ok("V-SIC-UX-TOTALS", totals["clean"] == totals["aliased"], f"{totals}")

    src = (HERE / "usage_index.py").read_text(encoding="utf-8")
    # Any local link inspection is a second producer (review 2026-10-03: the first
    # version caught only the deleted copy's own tokens). Path(__file__).resolve() is
    # module location, not store identity, so bare .resolve( is not listed.
    local = re.findall(r"def _store_dirs|realpath|\.resolve\(strict|readlink|is_junction"
                       r"|is_symlink|iterdir\(", src)
    ok("V-SIC-UX-ONE-PRODUCER", not local and "store_identity(" in src,
       f"usage_index resolves store paths itself: {local}; consumes store_identity: "
       f"{'store_identity(' in src}")


def main() -> int:
    saved_tis, saved_sm = tob.PROJECTS_DIR, sm.PROJECTS_DIR
    try:
        with tempfile.TemporaryDirectory() as td:
            aliased = store(Path(td) / "a", alias=True)
            if aliased is None:
                print("INCONCLUSIVE: could not create a directory junction (mklink /J)")
                return 2
            clean = store(Path(td) / "c", alias=False)

            dirs = [d for d in aliased.iterdir() if d.is_dir()]
            ok("V-SIC-FIXTURE", len(dirs) == 4, f"{len(dirs)} dirs listed: alias, real, other, ext")

            sd = tob.store_dirs(aliased) if hasattr(tob, "store_dirs") else []
            ok("V-SIC-STORE-DIRS", len(sd) == 3 and any(p.name == "C--ext" for p in sd),
               f"{len(sd)} stores; outside junction kept={any(p.name == 'C--ext' for p in sd)}")

            want, got = measure(clean), measure(aliased)
            ok("V-SIC-CONTROL", want == {"tis_calls": 6, "tis_sub": 3, "tis_sessions": 3,
                                         "budget_calls": 9, "co12_sessions": 3,
                                         "miner_files": 6}, f"clean store: {want}")
            for k, gate in (("tis_calls", "V-SIC-TIS-ALLPROJECTS"),
                            ("budget_calls", "V-SIC-BUDGET-PROGRAMMATIC"),
                            ("co12_sessions", "V-SIC-CO12-SESSIONS"),
                            ("miner_files", "V-SIC-MINER-FILES")):
                ok(gate, got[k] == want[k], f"{got[k]} vs {want[k]}")
            usage_index_gates(Path(td), aliased, clean)
    finally:
        tob.PROJECTS_DIR, sm.PROJECTS_DIR = saved_tis, saved_sm

    print(f"STORE_IDENTITY_CONSUMERS_PASS={PASS}/{PASS + FAIL}  threshold={PASS + FAIL}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
