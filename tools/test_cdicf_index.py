#!/usr/bin/env python3
"""Done-gate for the CDICF component FTS5 sidecar (V-CDICF-IDX-*).

Two properties carry this suite.

Isolation is asserted as a REFUSAL, not as an arrangement. A sidecar that
merely happens to sit in its own file today is a convention; one that exits
non-zero when pointed at a database holding turns* or design_tools* is a
boundary. Only the second survives someone passing --db by hand.

An empty result set is asserted to have three DISTINCT exit codes. A stale or
unbuilt index that answers "nothing" is answering "cannot say", and collapsing
that into "no component fits" is how a missing capability reads as a genuine
gap (feedback_zero_cannot_fall).

Hermetic: every gate runs against a temporary database via --db, so the real
vault DB is never opened. Run 3x -- output must be identical.

Run:  python tools/test_cdicf_index.py
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from tools.design_index import (  # noqa: E402
    CDICF_DB_NAME,
    CDICF_EXIT,
    cdicf_db_path,
)

INDEXER = os.path.join(HERE, "design_index.py")
SELECTOR = os.path.join(ROOT, "modules", "cdicf", "selector.js")
EXAMPLES = os.path.join(ROOT, "modules", "cdicf", "examples")

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _run(*args: str) -> tuple[int, str, str]:
    env = dict(os.environ)
    env.pop("CDICF_INDEX_DB", None)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, INDEXER, *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    return p.returncode, p.stdout or "", p.stderr or ""


def _node(*args: str) -> tuple[int, str, str]:
    p = subprocess.run(["node", SELECTOR, *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


def _search(db: str, q: str, *extra: str) -> tuple[int, dict]:
    rc, out, _ = _run("--components-search", q, "--db", db, "--json", *extra)
    try:
        return rc, json.loads(out)
    except ValueError:
        return rc, {}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print("V-CDICF-IDX -- component FTS5 sidecar\n")
    tmp = tempfile.mkdtemp(prefix="cdicf_idx_")
    try:
        db = os.path.join(tmp, "sidecar.db")
        src = os.path.join(tmp, "manifests")
        os.makedirs(src)
        for f in ("shadcn-ui.button.json", "react-bits.split-text.json"):
            shutil.copy(os.path.join(EXAMPLES, f), os.path.join(src, f))

        # -- 06 NO_INDEX before anything is built. Asserted FIRST, because
        #    after a build this state is unreachable.
        rc, doc = _search(db, "button")
        if rc == CDICF_EXIT["NO_INDEX"] and doc.get("status") == "NO_INDEX":
            _ok("V-CDICF-IDX-06-NO-INDEX",
                f"unbuilt index exits {rc} with a remedy, not an empty list")
        else:
            _fail("V-CDICF-IDX-06-NO-INDEX", f"rc={rc} doc={doc}")

        # -- 01 build
        rc, out, err = _run("--components-build", src, "--db", db)
        if rc == 0 and "2 rows / 2 fts" in out:
            # Evidence deliberately omits the db path: it is a temp directory,
            # and a volatile string in the output would make the 3x-identical
            # hermeticity check unfalsifiable.
            _ok("V-CDICF-IDX-01-BUILD",
                "2 manifests indexed, fts mirror consistent")
        else:
            _fail("V-CDICF-IDX-01-BUILD", f"rc={rc} out={out!r} err={err!r}")

        # -- 02 relevant candidates, and only those
        rc, doc = _search(db, "button")
        ids = [r["id"] for r in doc.get("results", [])]
        if rc == 0 and ids == ["primitives/button"] and doc["candidates"]:
            _ok("V-CDICF-IDX-02-RELEVANT",
                f"'button' -> {ids}, candidate paths emitted for the selector")
        else:
            _fail("V-CDICF-IDX-02-RELEVANT", f"rc={rc} ids={ids}")

        # -- 03 provenance is not searchable, because it is not stored
        rc, doc = _search(db, "shadcn")
        con = sqlite3.connect(db)
        cols = {r[1] for r in con.execute("PRAGMA table_info(cdicf_components)")}
        con.close()
        leak = {c for c in cols
                if any(t in c for t in ("licen", "fingerprint", "holder",
                                        "copyright", "posture"))}
        if (rc == CDICF_EXIT["NO_MATCH"] and doc.get("status") == "NO_MATCH"
                and not leak):
            _ok("V-CDICF-IDX-03-NO-PROVENANCE",
                "'shadcn' (a copyright_holder) exits 32; no provenance column "
                "exists to leak")
        else:
            _fail("V-CDICF-IDX-03-NO-PROVENANCE", f"rc={rc} leak={leak}")

        # -- 04 the isolation boundary REFUSES rather than coexists
        shared = os.path.join(tmp, "shared_vault.db")
        c = sqlite3.connect(shared)
        c.execute("CREATE TABLE design_tools(x)")
        c.execute("CREATE TABLE turns(x)")
        c.commit()
        c.close()
        rc, out, err = _run("--components-build", src, "--db", shared)
        if rc != 0 and "refuses to share" in err and "design_tools" in err:
            _ok("V-CDICF-IDX-04-REFUSES-SHARED-DB",
                f"exit {rc}: {err.strip().splitlines()[0][:88]}")
        else:
            _fail("V-CDICF-IDX-04-REFUSES-SHARED-DB", f"rc={rc} err={err!r}")

        # -- 05 no foreign objects present, and no filename collision
        con = sqlite3.connect(db)
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master")}
        con.close()
        foreign = names & {"turns", "turns_fts", "design_tools",
                           "design_tools_fts"}
        if (not foreign and CDICF_DB_NAME != "SOVEREIGN-HISTORY-VAULT.db"
                and cdicf_db_path("/x/y.db") == "/x/y.db"):
            _ok("V-CDICF-IDX-05-NO-CONTAMINATION",
                f"sidecar holds {sorted(n for n in names if 'cdicf' in n)[:2]}"
                f"...; filename {CDICF_DB_NAME} cannot collide")
        else:
            _fail("V-CDICF-IDX-05-NO-CONTAMINATION", f"foreign={foreign}")

        # -- 07 INDEX_EMPTY is not NO_MATCH
        empty_db = os.path.join(tmp, "empty.db")
        empty_src = os.path.join(tmp, "no_manifests")
        os.makedirs(empty_src)
        _run("--components-build", empty_src, "--db", empty_db)
        rc, doc = _search(empty_db, "button")
        if rc == CDICF_EXIT["INDEX_EMPTY"] and rc != CDICF_EXIT["NO_MATCH"]:
            _ok("V-CDICF-IDX-07-EMPTY-DISTINCT",
                f"empty index exits {rc}, no-match exits "
                f"{CDICF_EXIT['NO_MATCH']} -- different causes, different codes")
        else:
            _fail("V-CDICF-IDX-07-EMPTY-DISTINCT", f"rc={rc}")

        # -- 08 install state, read from the installer's record
        proj = os.path.join(tmp, "project", ".cdicf")
        os.makedirs(proj)
        rec = os.path.join(proj, "installed.json")
        with open(rec, "w", encoding="utf-8") as fh:
            json.dump({"schema": "cdicf/installed/1",
                       "components": {"primitives/button": {"checksum": "x"}}},
                      fh)
        rc, out, err = _run("--components-sync", os.path.dirname(proj),
                            "--db", db)
        _, doc = _search(db, "button")
        inst = doc["results"][0]["installed"] if doc.get("results") else None
        if rc == 0 and inst is True:
            _ok("V-CDICF-IDX-08-SYNC-INSTALL",
                "installed.json names primitives/button -> indexed installed=1")
        else:
            _fail("V-CDICF-IDX-08-SYNC-INSTALL", f"rc={rc} installed={inst}")

        # -- 09 retirement clears it again. A one-way flag would read as
        #    installed forever after the first install.
        with open(rec, "w", encoding="utf-8") as fh:
            json.dump({"schema": "cdicf/installed/1", "components": {}}, fh)
        _run("--components-sync", os.path.dirname(proj), "--db", db)
        _, doc = _search(db, "button")
        inst = doc["results"][0]["installed"] if doc.get("results") else None
        if inst is False:
            _ok("V-CDICF-IDX-09-SYNC-RETIRE",
                "removed from installed.json -> indexed installed=0")
        else:
            _fail("V-CDICF-IDX-09-SYNC-RETIRE", f"installed={inst}")

        # -- 10 a retired component is not a candidate by default
        ret_src = os.path.join(tmp, "retired")
        os.makedirs(ret_src)
        with open(os.path.join(EXAMPLES, "shadcn-ui.button.json"),
                  encoding="utf-8-sig") as fh:
            m = json.load(fh)
        m["lifecycle"]["state"] = "retired"
        with open(os.path.join(ret_src, "b.json"), "w", encoding="utf-8") as fh:
            json.dump(m, fh)
        ret_db = os.path.join(tmp, "retired.db")
        _run("--components-build", ret_src, "--db", ret_db)
        rc_def, d_def = _search(ret_db, "button")
        rc_inc, d_inc = _search(ret_db, "button", "--include-retired")
        if (rc_def == CDICF_EXIT["NO_MATCH"] and rc_inc == 0
                and d_inc["count"] == 1):
            _ok("V-CDICF-IDX-10-RETIRED-EXCLUDED",
                "retired is not a candidate by default, visible with "
                "--include-retired")
        else:
            _fail("V-CDICF-IDX-10-RETIRED-EXCLUDED",
                  f"default={rc_def} include={rc_inc}")

        # -- 11 an in-place edit makes the index stale, and says so
        with open(os.path.join(src, "shadcn-ui.button.json"), "r+",
                  encoding="utf-8") as fh:
            edited = json.load(fh)
            edited["identity"]["name"] = "Button Renamed"
            fh.seek(0)
            fh.truncate()
            json.dump(edited, fh)
        rc, doc = _search(db, "button")
        rc_strict, _, _ = _run("--components-search", "button", "--db", db,
                               "--json", "--strict-fresh")
        if doc.get("freshness") == "stale" and rc_strict == CDICF_EXIT["STALE"]:
            _ok("V-CDICF-IDX-11-STALENESS",
                f"edited manifest -> freshness=stale; --strict-fresh exits "
                f"{rc_strict}")
        else:
            _fail("V-CDICF-IDX-11-STALENESS",
                  f"freshness={doc.get('freshness')} strict={rc_strict}")

        # -- 12 rebuild is idempotent and the mirror stays consistent
        rc1, o1, _ = _run("--components-build", src, "--db", db)
        rc2, o2, _ = _run("--components-build", src, "--db", db)
        if rc1 == rc2 == 0 and o1 == o2 and "2 rows / 2 fts" in o2:
            _ok("V-CDICF-IDX-12-IDEMPOTENT",
                "two consecutive builds produce identical output; fts mirrors "
                "the base table exactly")
        else:
            _fail("V-CDICF-IDX-12-IDEMPOTENT", f"{o1!r} vs {o2!r}")

        # -- 13 the selector actually consumes the sidecar's output
        rc, doc = _search(db, "button")
        listing = os.path.join(tmp, "narrowed.json")
        with open(listing, "w", encoding="utf-8") as fh:
            json.dump({"candidates": doc["candidates"]}, fh)
        rc, out, err = _node("--intent", "a clickable button primitive",
                             "--candidates-from", listing, "--json")
        try:
            dec = json.loads(out)
        except ValueError:
            dec = {}
        srcinfo = dec.get("candidate_source", {})
        if rc in (0, 20, 21) and srcinfo.get("mode") == "search" \
                and srcinfo.get("caveat"):
            _ok("V-CDICF-IDX-13-SELECTOR-CONSUMES",
                f"selector ran on the narrowed set (decision={dec.get('decision')}"
                f", source=search, caveat carried)")
        else:
            _fail("V-CDICF-IDX-13-SELECTOR-CONSUMES",
                  f"rc={rc} source={srcinfo} err={err[:160]!r}")

        # -- 14 a search miss must not enter the selector as "nothing fits"
        empty_list = os.path.join(tmp, "none.json")
        with open(empty_list, "w", encoding="utf-8") as fh:
            json.dump({"candidates": []}, fh)
        rc, out, err = _node("--intent", "anything", "--candidates-from",
                             empty_list, "--json")
        if rc == 3 and "search miss" in err:
            _ok("V-CDICF-IDX-14-EMPTY-SET-REFUSED",
                "empty narrowed set exits 3 rather than becoming a verdict "
                "about the catalogue")
        else:
            _fail("V-CDICF-IDX-14-EMPTY-SET-REFUSED", f"rc={rc} err={err!r}")

        # -- 15 the full-directory path still works and is labelled as such
        rc, out, err = _node("--intent", "a clickable button primitive",
                             "--candidates", EXAMPLES, "--json")
        try:
            dec = json.loads(out)
        except ValueError:
            dec = {}
        if dec.get("candidate_source", {}).get("mode") == "directory":
            _ok("V-CDICF-IDX-15-DIRECTORY-UNBROKEN",
                "the pre-E2 directory path is unchanged and labelled "
                "mode=directory")
        else:
            _fail("V-CDICF-IDX-15-DIRECTORY-UNBROKEN",
                  f"rc={rc} source={dec.get('candidate_source')}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASSES + FAILS
    print(f"\nCDICF_INDEX_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
