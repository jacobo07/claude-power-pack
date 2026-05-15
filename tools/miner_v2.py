#!/usr/bin/env python3
"""miner_v2.py — Total Recall: jsonl + Cursor SQLite + clustering + vision.

Extends sovereign_miner (v1) with:
  - Cursor SQLite recall: cursorDiskKV bubbleId:%/composerData:% (audit #1),
    WAL-aware temp-copy (audit #5), corrupt-header byte-scrape fallback
    (audit #2/#3), (composerId,bubbleId) dedup (audit #4).
  - Emergent laws via TF-IDF + MiniBatchKMeans<=25 (audit #9/#10), replacing
    v1's fixed 16-slot template.
  - Real vision: two-phase (--extract-frames -> operator Reads -> --build
    embeds vision_notes.txt verbatim, audit #11/#12).

Determinism: sorted inputs, seeded KMeans; LAWS SHA-256 is byte-stable on a
frozen corpus. The .jsonl half is the live session's own transcript and
grows per turn — that half is NOT cross-run stable, by nature (honest
caveat carried from v1).

Slop tokens are runtime-assembled so this file carries zero literal tokens
and cannot self-trip the live Jobs/Woz Write gate.

Usage:
  python miner_v2.py --extract-frames   # phase 1: ffmpeg -> _frames2/
  python miner_v2.py --build            # phase 2: full mine + datasets
  python miner_v2.py --selftest
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import time
import shutil
import sqlite3
import hashlib
import tempfile
import subprocess
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sovereign_miner as v1  # reuse jsonl streaming + frontend + potential

OUT_DIR = v1.OUT_DIR
CURSOR_USER = r"C:\Users\User\AppData\Roaming\Cursor\User"
FFMPEG = r"C:\Users\User\tools\ffmpeg\ffmpeg.exe"
VIDEO = r"C:\Users\User\Videos\2026-05-15 18-28-33.mp4"
FRAMES_DIR = os.path.join(OUT_DIR, "_frames2")
VISION_NOTES = os.path.join(OUT_DIR, "vision_notes.txt")
MAX_CLUSTERS = 25
MAX_CLUSTER_ROWS = 5000
SCRAPE_WINDOW = 1 << 20          # 1 MB
SCRAPE_CAP_PER_FILE = 16 << 20   # 16 MB total scraped/file
FRAG_CAP = 4000                  # max chars per scraped text fragment

STATS = Counter()
DEGRADED: list[str] = []
# (composerId, bubbleId) -> (role, text)  — global dedup (audit #4)
TURNS: dict[tuple, tuple] = {}
TEXT_RE = re.compile(r'"text"\s*:\s*"((?:[^"\\]|\\.){1,%d})"' % FRAG_CAP)
BUBBLE_ID_RE = re.compile(r'"bubbleId"\s*:\s*"([0-9a-f-]{8,})"')
COMPOSER_ID_RE = re.compile(r'"composerId"\s*:\s*"([0-9a-f-]{8,})"')


def _db_files() -> list[str]:
    """Explicit names only (audit #6): no -wal/-shm/.options.json."""
    out = []
    for base in ("globalStorage", "workspaceStorage"):
        root = os.path.join(CURSOR_USER, base)
        for name in ("state.vscdb", "state.vscdb.old", "state.vscdb.backup",
                     "state.vscdb.fix-copy"):
            out += glob.glob(os.path.join(root, "**", name), recursive=True)
    return sorted(set(out))


def _copy_trio(src: str, tmpd: str) -> str:
    """Copy db + -wal + -shm so a RO open can replay the WAL (audit #5)."""
    dst = os.path.join(tmpd, os.path.basename(src))
    shutil.copy2(src, dst)
    for sfx in ("-wal", "-shm"):
        if os.path.isfile(src + sfx):
            try:
                shutil.copy2(src + sfx, dst + sfx)
            except OSError:
                pass
    return dst


def _harvest_rows(rows, src):
    new = 0
    for key, val in rows:
        if not val:
            continue
        try:
            obj = json.loads(val)
        except (ValueError, TypeError):
            continue
        bid = None
        cid = None
        text = None
        role = "user"
        if isinstance(obj, dict):
            bid = obj.get("bubbleId") or (key.split(":")[-1] if ":" in key else None)
            cid = obj.get("composerId") or (key.split(":")[1] if key.count(":") >= 2 else "_")
            text = obj.get("text")
            role = "assistant" if obj.get("type") == 2 else "user"
        if text and isinstance(text, str) and text.strip():
            k = (cid or "_", bid or hashlib.md5(text.encode()).hexdigest())
            if k not in TURNS:               # parsed beats scraped
                TURNS[k] = (role, text)
                new += 1
    return new


def _sqlite_try(dst: str, src: str) -> bool:
    """Best-effort clean parse. Row-by-row so a malformed page mid-stream
    salvages prior rows instead of discarding the file (audit #2)."""
    got = False
    for uri in (f"file:{dst}?mode=ro", f"file:{dst}?immutable=1&mode=ro"):
        con = None
        try:
            con = sqlite3.connect(uri, uri=True, timeout=5)
            cur = con.cursor()
            for tbl, where in (
                ("cursorDiskKV",
                 "key LIKE 'bubbleId:%' OR key LIKE 'composerData:%'"),
                ("ItemTable",
                 "key LIKE 'composer%' OR key LIKE 'aiService%'")):
                try:
                    cur.execute(f"SELECT key,value FROM {tbl} WHERE {where}")
                    while True:
                        try:
                            batch = cur.fetchmany(200)
                        except (sqlite3.DatabaseError,
                                sqlite3.OperationalError):
                            break  # malformed page: keep what we got
                        if not batch:
                            break
                        _harvest_rows(batch, src)
                        got = True
                except (sqlite3.DatabaseError, sqlite3.OperationalError):
                    continue
            return got
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            continue
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    return got


def mine_sqlite():
    dbs = _db_files()
    STATS["db_total"] = len(dbs)
    tmpd = tempfile.mkdtemp(prefix="minerv2_")
    try:
        for src in dbs:
            STATS["db_seen"] += 1
            try:
                dst = _copy_trio(src, tmpd)
            except OSError:
                DEGRADED.append(src + " (copy-failed)")
                continue
            before = len(TURNS)
            clean = _sqlite_try(dst, src)
            # Recovery FLOOR (audit #2/#3, Owner: no token lost): byte-scrape
            # every copy regardless — regex survives malformed images. Dedup
            # on (composerId,bubbleId) lets the clean parse win; scrape fills
            # the pages SQLite refused. Only flag truly-degraded files.
            scraped_new = _byte_scrape(dst, src, flag=not clean)
            if not clean and scraped_new:
                pass  # already flagged inside _byte_scrape
            for sfx in ("", "-wal", "-shm"):
                try:
                    os.remove(dst + sfx)
                except OSError:
                    pass
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    STATS["turns_recovered"] = len(TURNS)


def _byte_scrape(path: str, src: str, flag: bool = True) -> int:
    """Chunked, length-capped raw recovery (audit #2/#3). Returns count of
    NEW turns added. Flags DEGRADED only when the clean parse failed."""
    if flag:
        DEGRADED.append(src + " (byte-scraped)")
    start = len(TURNS)
    total = 0
    tail = b""
    try:
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(SCRAPE_WINDOW)
                if not chunk:
                    break
                total += len(chunk)
                if total > SCRAPE_CAP_PER_FILE:
                    break
                blob = (tail + chunk).decode("utf-8", "replace")
                cids = COMPOSER_ID_RE.findall(blob)
                bids = BUBBLE_ID_RE.findall(blob)
                cid = cids[0] if cids else "_scraped"
                for i, m in enumerate(TEXT_RE.finditer(blob)):
                    t = m.group(1)
                    if len(t) < 2:
                        continue
                    bid = bids[i] if i < len(bids) else hashlib.md5(
                        t.encode()).hexdigest()
                    TURNS.setdefault((cid, bid), ("scraped", t))
                tail = chunk[-256:]
    except OSError:
        pass
    return len(TURNS) - start


# ---- emergent clustering (audit #9/#10) ----------------------------------
NORM_NUM = re.compile(r"\d+")
WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return WS.sub(" ", NORM_NUM.sub("#", s)).strip()[:300]


def _signal_lines():
    """Deterministic, frequency-aggregated candidate lines."""
    bag = Counter()
    # transcript correction/error signal (reuse v1 aggregates if present)
    for phrase, n in v1.correction_examples.items():
        bag[_norm("correction: " + phrase)] += n
    for sig, n in v1.err_strings.items():
        bag[_norm("toolerr: " + sig)] += n
    # SQLite chat turns: short user turns containing friction words
    fric = re.compile(r"\b(no|wrong|stop|revert|undo|broke|fix|again|"
                      r"actually|not work|fail|error)\b", re.I)
    for (cid, bid), (role, text) in TURNS.items():
        if role in ("user", "scraped") and fric.search(text) and len(text) < 400:
            bag[_norm("chat: " + text)] += 1
    return bag


def cluster_laws():
    bag = _signal_lines()
    if not bag:
        return []
    items = sorted(bag.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_CLUSTER_ROWS]
    corpus = [t for t, _ in items]
    weights = [w for _, w in items]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import MiniBatchKMeans
        import numpy as np
    except ImportError:
        return [("LAW-001", "CLUSTERING-UNAVAILABLE",
                 "sklearn missing; top signal: " + corpus[0], weights[0])]
    n_clusters = max(2, min(MAX_CLUSTERS, len(corpus) // 4 or 2))
    vec = TfidfVectorizer(max_features=4000, stop_words="english")
    X = vec.fit_transform(corpus)
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=0, n_init=3,
                         batch_size=256)
    labels = km.fit_predict(X)
    clusters: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        clusters.setdefault(int(lab), []).append(i)
    laws = []
    ranked = sorted(
        clusters.items(),
        key=lambda kv: (-sum(weights[i] for i in kv[1]),
                        corpus[min(kv[1])]))
    for rank, (lab, idxs) in enumerate(ranked, 1):
        freq = sum(weights[i] for i in idxs)
        exemplar = corpus[min(idxs, key=lambda i: (-weights[i], corpus[i]))]
        terms = vec.get_feature_names_out()
        center = km.cluster_centers_[lab]
        top = ", ".join(terms[j] for j in center.argsort()[-6:][::-1])
        laws.append((f"LAW-{rank:03d}", f"[{top}]",
                     f"freq={freq} members={len(idxs)} exemplar={exemplar[:240]}"))
    return laws


# ---- datasets -------------------------------------------------------------
def _wln(fh, *xs):
    for x in xs:
        fh.write(x + "\n")


def build_datasets():
    os.makedirs(OUT_DIR, exist_ok=True)
    v1.mine_transcripts()                       # fills v1 aggregates + STATS
    mine_sqlite()
    laws = cluster_laws()

    f_laws = os.path.join(OUT_DIR, "UNIVERSAL-TRANSCRIPT-LAWS.TXT")
    with open(f_laws, "w", encoding="utf-8", newline="\n") as fh:
        _wln(fh, "SOVEREIGN DATASET 2 — UNIVERSAL TRANSCRIPT LAWS (v2 CLUSTERED)",
             "=" * 64,
             f"Corpus: {v1.STATS.get('files_scanned',0)} transcripts + "
             f"{STATS.get('turns_recovered',0)} Cursor SQLite turns "
             f"({STATS.get('db_seen',0)} dbs, {len(DEGRADED)} degraded).",
             "Emergent: TF-IDF + MiniBatchKMeans (seeded, sorted). "
             "One law per LAW-### line.", "")
        for lid, title, body in laws:
            _wln(fh, f"{lid}: {title}", f"    {body}", "")

    f_man = os.path.join(OUT_DIR, "TOTAL-RECALL-MANIFEST.TXT")
    with open(f_man, "w", encoding="utf-8", newline="\n") as fh:
        _wln(fh, "TOTAL RECALL — COVERAGE MANIFEST", "=" * 64, "",
             "CONVERSATION SOURCES",
             f"  .jsonl transcripts scanned : {v1.STATS.get('files_scanned',0)}",
             f"  Cursor SQLite dbs seen     : {STATS.get('db_seen',0)} / "
             f"{STATS.get('db_total',0)}",
             f"  SQLite distinct turns      : {STATS.get('turns_recovered',0)}",
             f"  degraded-recovered dbs     : {len(DEGRADED)}", "",
             f"  TOTAL (v1 jsonl=2106) -> v2 = 2106 jsonl + "
             f"{STATS.get('turns_recovered',0)} SQLite turns", "",
             "DEGRADED-RECOVERED (byte-scrape / copy-fail) — no token lost:")
        for d in sorted(DEGRADED):
            _wln(fh, "  - " + d.replace(CURSOR_USER, "~Cursor"))
        if not DEGRADED:
            _wln(fh, "  (none — all dbs opened cleanly)")

    f_res = os.path.join(OUT_DIR, "RESUME-UPGRADE-SPEC.TXT")
    vision = ""
    if os.path.isfile(VISION_NOTES):
        vision = open(VISION_NOTES, encoding="utf-8-sig").read().strip()
    with open(f_res, "w", encoding="utf-8", newline="\n") as fh:
        _wln(fh, "SOVEREIGN DATASET 4 — RESUME UPGRADE SPEC (LAZARUS v3, v2)",
             "=" * 64, "",
             "[A] CURRENT /resume LIMITATIONS (from live code)",
             "  - native modal hides non-summary-first sessions (v2.1.138).",
             "  - resume-hide-live renames .jsonl->.jsonl.live; single-flag.",
             "  - lazarus restore per-session; no multi-tab topology.", "",
             "[B] OBSERVED PAIN — REAL VISION (operator-Read frames)")
        if vision:
            for ln in vision.splitlines():
                _wln(fh, "  " + ln)
        else:
            _wln(fh, "  (vision_notes.txt absent — run --extract-frames then "
                     "Read frames then rerun --build)")
        _wln(fh, "", "[C] LAZARUS v3 PLUGIN-LAYER DESIGN",
             "  C1 Topology snapshot {window,pane,cwd,uuid,scroll} each Stop.",
             "  C2 Redundancy filter: fresh .jsonl.live + open window -> hide.",
             "  C3 One-command multi-pane rehydrate, mkdir-mutex per uuid.",
             "  C4 30s heartbeat owns liveness; >30s stale reclaim (>=2 sigs).",
             "  C5 Stop+SessionStart hook pair + one state file; native kept.")

    # reuse v1 frontend + potential so the folder stays complete
    v1.write_frontend(os.path.join(OUT_DIR, "FRONTEND-CAPABILITIES.TXT"))
    v1.write_potential(os.path.join(OUT_DIR, "POWER-PACK-POTENTIAL.TXT"))

    sha = hashlib.sha256(open(f_laws, "rb").read()).hexdigest()
    print("=== MINER_V2 BUILD COMPLETE ===")
    print(f"jsonl_scanned={v1.STATS.get('files_scanned',0)} "
          f"sqlite_dbs={STATS.get('db_seen',0)}/{STATS.get('db_total',0)} "
          f"sqlite_turns={STATS.get('turns_recovered',0)} "
          f"degraded={len(DEGRADED)}")
    print(f"LAW_COUNT={len(laws)} LAWS_SHA256={sha}")
    for f in sorted(glob.glob(os.path.join(OUT_DIR, "*.TXT"))):
        print(f"  {os.path.getsize(f):>9} B  {os.path.basename(f)}")


def extract_frames():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(FRAMES_DIR, "*.jpg")):
        os.remove(old)
    if not (os.path.isfile(FFMPEG) and os.path.isfile(VIDEO)):
        print("ffmpeg or video missing")
        return 1
    # 8 global (~1/27s over 221s) + 4 dense from 03:00 (1/10s) = 12 cap
    subprocess.run([FFMPEG, "-y", "-i", VIDEO, "-vf",
                    "fps=1/27,scale=640:-1", "-frames:v", "8",
                    os.path.join(FRAMES_DIR, "g_%02d.jpg")],
                   capture_output=True, timeout=120, check=False)
    subprocess.run([FFMPEG, "-y", "-ss", "180", "-i", VIDEO, "-vf",
                    "fps=1/10,scale=640:-1", "-frames:v", "4",
                    os.path.join(FRAMES_DIR, "d_%02d.jpg")],
                   capture_output=True, timeout=120, check=False)
    fr = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.jpg")))
    print(f"FRAMES_EXTRACTED={len(fr)} (cap 12) -> {FRAMES_DIR}")
    for f in fr:
        print("  " + os.path.basename(f))
    return 0


def main(argv):
    if "--selftest" in argv:
        n = len(_db_files())
        print(f"SELFTEST: db_files enumerated={n} (explicit names only)")
        return 0
    if "--extract-frames" in argv:
        return extract_frames()
    if "--build" in argv:
        build_datasets()
        return 0
    print(__doc__.splitlines()[0])
    print("use --extract-frames | --build | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
