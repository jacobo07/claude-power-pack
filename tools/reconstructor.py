#!/usr/bin/env python3
"""reconstructor.py - physical .recover rebuild of corrupted Cursor SQLite.

Uses the full sqlite-tools build's .recover (page-walking salvage) to
rebuild integrity-clean copies of state.vscdb.old / state.vscdb.fix-copy
into <OUT>/_reconstructed/<basename>.fixed.db plus MANIFEST.json.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import hashlib
import argparse
import tempfile
import subprocess

DEFAULT_SQ3 = r"C:\Users\User\Apps\sqlite-full\sqlite3.exe"
ALLOWED = {"state.vscdb.old", "state.vscdb.fix-copy", "state.vscdb.backup"}
OUT_DEFAULT = (os.environ.get("SOVEREIGN_MINER_OUT_DIR")
               or r"C:\Users\User\Downloads\PowerPack_Sovereign_Datasets")
RECON_DIR = os.path.join(OUT_DEFAULT, "_reconstructed")
CURSOR_GLOBAL = os.path.expandvars(r"%APPDATA%\Cursor\User\globalStorage")
# Runtime-assembled trigger string for the smoke gate.
STRIPPED_TRIGGER = "un" + "known" + " command"


def _resolve_sq3(arg):
    return arg or os.environ.get("RECONSTRUCTOR_SQLITE3") or DEFAULT_SQ3


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _smoke(sq3):
    if not os.path.isfile(sq3):
        sys.exit(f"reconstructor: sqlite3.exe not at {sq3}")
    r = subprocess.run([sq3, ":memory:", ".recover"],
                       capture_output=True, text=True, timeout=10)
    if STRIPPED_TRIGGER in (r.stderr + r.stdout):
        sys.exit(f"reconstructor: {sq3} is a stripped build, no .recover")
    if r.returncode != 0:
        sys.exit(f"reconstructor: smoke failed rc={r.returncode} "
                 f"stderr={r.stderr[:200]}")


def _run_to_file(sq3, db, sql_cmd, out_path):
    with open(out_path, "wb") as fh:
        r = subprocess.run([sq3, db, sql_cmd], stdout=fh,
                           stderr=subprocess.PIPE, timeout=600)
    return r.returncode


def _query(sq3, db, sql):
    r = subprocess.run([sq3, db, sql], capture_output=True, text=True,
                       timeout=30)
    return (r.stdout or "").strip()


def reconstruct_one(src, sq3, work):
    base = os.path.basename(src)
    if base not in ALLOWED:
        return {"src": src, "status": "REFUSED", "reason": "not in allowlist"}
    if not os.path.isfile(src):
        return {"src": src, "status": "MISSING"}

    copy_db = os.path.join(work, base + ".copy.db")
    shutil.copy2(src, copy_db)

    sql_path = os.path.join(work, base + ".recover.sql")
    rec_rc = _run_to_file(sq3, copy_db, ".recover", sql_path)
    sql_size = os.path.getsize(sql_path) if os.path.isfile(sql_path) else 0
    if rec_rc != 0 or sql_size < 1024:
        return {"src": src, "status": "RECOVER_FAILED",
                "rec_rc": rec_rc, "sql_bytes": sql_size}

    fixed_db = os.path.join(work, base + ".fixed.db")
    if os.path.isfile(fixed_db):
        os.remove(fixed_db)
    r = subprocess.run([sq3, fixed_db, f".read {sql_path}"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return {"src": src, "status": "APPLY_FAILED",
                "stderr": (r.stderr or "")[:300]}

    quick = _query(sq3, fixed_db, "PRAGMA quick_check;")
    integ = _query(sq3, fixed_db, "PRAGMA integrity_check;")
    cursor_rows = _query(
        sq3, fixed_db,
        "SELECT count(*) FROM cursorDiskKV WHERE "
        "key LIKE 'bubbleId:%' OR key LIKE 'composerData:%';") or "0"
    laf_present = _query(
        sq3, fixed_db,
        "SELECT count(*) FROM sqlite_master WHERE type='table' "
        "AND name='lost_and_found';") or "0"
    laf_chat = "0"
    if laf_present == "1":
        laf_chat = _query(
            sq3, fixed_db,
            "SELECT count(*) FROM lost_and_found WHERE "
            "c0 LIKE 'bubbleId:%' OR c0 LIKE 'composerData:%';") or "0"

    integrity_ok = (quick.strip() == "ok" and integ.strip() == "ok")

    os.makedirs(RECON_DIR, exist_ok=True)
    final = os.path.join(RECON_DIR, base + ".fixed.db")
    if os.path.isfile(final):
        os.remove(final)
    shutil.copy2(fixed_db, final)

    return {
        "src": src,
        "status": "OK" if integrity_ok else "INTEGRITY_FAIL",
        "fixed": final,
        "quick_check": quick,
        "integrity_check": integ,
        "cursorDiskKV_chat_rows": int(cursor_rows),
        "lost_and_found_present": laf_present == "1",
        "lost_and_found_chat_rows": int(laf_chat),
        "recover_sql_bytes": sql_size,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite3-path", default=None)
    ap.add_argument("--targets", nargs="*",
                    default=[os.path.join(CURSOR_GLOBAL, "state.vscdb.old"),
                             os.path.join(CURSOR_GLOBAL,
                                          "state.vscdb.fix-copy")])
    args = ap.parse_args()
    sq3 = _resolve_sq3(args.sqlite3_path)
    _smoke(sq3)
    work = tempfile.mkdtemp(prefix="recon_")
    try:
        results = [reconstruct_one(t, sq3, work) for t in args.targets]
    finally:
        shutil.rmtree(work, ignore_errors=True)

    os.makedirs(RECON_DIR, exist_ok=True)
    manifest = {
        "sqlite3_path": sq3,
        "sqlite3_sha256": _sha256(sq3),
        "sqlite3_version": subprocess.run(
            [sq3, "--version"], capture_output=True, text=True
        ).stdout.strip(),
        "results": results,
    }
    with open(os.path.join(RECON_DIR, "MANIFEST.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    print("=== RECONSTRUCTOR COMPLETE ===")
    for r in results:
        print(f"  {os.path.basename(r['src']):28} {r['status']:18} "
              f"chat={r.get('cursorDiskKV_chat_rows','-')} "
              f"laf_chat={r.get('lost_and_found_chat_rows','-')}")
    fails = [r for r in results if r["status"] not in ("OK", "MISSING")]
    return 0 if not fails else 5


if __name__ == "__main__":
    raise SystemExit(main())
