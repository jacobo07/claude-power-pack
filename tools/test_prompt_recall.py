#!/usr/bin/env python
"""V-RECALL-* gates for Prompt Recall and the memory catalog (vault/specs/prompt-recall.md).

Every refusal is paired with a control in which the fact exists and the hit is admitted, so a
recall that returns nothing at all cannot pass.

Run: python tools/test_prompt_recall.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def mem(name, desc, body):
    return f"---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: feedback\n---\n\n{body}\n"


FILLER = [
    ("kiln", "Glaze firing curve for stoneware", "Cone six oxidation with a slow cool."),
    ("sonar", "Hydrophone gain staging", "Clip at the preamp before the converter."),
    ("orchard", "Pruning schedule for pear trees", "Cut water sprouts in late winter."),
    ("ledger", "Reconciling petty cash", "Count coins before notes, then sign."),
    ("violin", "Bow rehair interval", "Rosin build-up means a rehair is due."),
    ("glacier", "Crevasse rescue pulley", "Build a three to one haul system."),
]


def build_corpus(d: Path) -> list:
    memdir = d / "projects" / "C--proj" / "memory"
    memdir.mkdir(parents=True)
    (memdir / "MEMORY.md").write_text("- [kiln](kiln.md) -- glaze\n- [more](MEMORY-sub.md)\n",
                                      encoding="utf-8")
    # A sub-index MEMORY.md hands off to, as TUA-X does: what it lists is indexed.
    (memdir / "MEMORY-sub.md").write_text("- [glacier](glacier.md) -- haul\n", encoding="utf-8")
    (memdir / "zeppelin.md").write_text(mem(
        "zeppelin-mooring", "Zeppelin mooring tether snaps under gusts",
        "The mooring tether on the zeppelin mast snapped twice; use a swivel shackle."),
        encoding="utf-8")
    for name, desc, body in FILLER:
        (memdir / f"{name}.md").write_text(mem(name, desc, body), encoding="utf-8")
    return [(f, "memory", "C--proj") for f in sorted(memdir.glob("*.md"))
            if not f.name.startswith("MEMORY")]


UKDL_SHAPE = """---
title: x
---
## Section Alpha
Intro prose for the alpha section that is long enough to count as a chunk.

**`T-ALPHA-TRAP-001`** -- A trap about alpha widgets that misbehave under load.

**`PR-BETA-RULE-002`** -- A process rule about beta gadgets and their calibration.
### B
**`HR-GAMMA-STOP-003`** -- A hard rule: stop before deleting gamma records.
"""


def _set_last_refresh(recall, db, ts):
    con = recall.connect(db)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('last_refresh', ?)", (str(ts),))
    con.commit()
    con.close()


def spawn_gates(tmp: Path, recall) -> None:
    """Fresh index: no spawn. Stale: exactly one detached refresh, the lock held while it runs and
    released after, the index fresh again. A refresh that just ran blocks the next one even if
    the index reads stale (attempt stamp, review L1). The child gets a temp USERPROFILE so it
    indexes a tiny corpus, not the live estate."""
    home = tmp / "home"
    mdir = home / ".claude" / "projects" / "C--spawn" / "memory"
    mdir.mkdir(parents=True)
    (mdir / "MEMORY.md").write_text("", encoding="utf-8")
    (mdir / "puffin.md").write_text(mem("puffin", "Puffin burrow survey", "Count burrows."),
                                    encoding="utf-8")
    saved = {k: os.environ.get(k) for k in ("CPP_RECALL_DIR", "CPP_RECALL_NO_SPAWN", "USERPROFILE")}
    os.environ["CPP_RECALL_DIR"] = str(tmp / "spawn_state")
    os.environ.pop("CPP_RECALL_NO_SPAWN", None)
    os.environ["USERPROFILE"] = str(home)
    try:
        db = recall.db_path()
        lock = recall.state_dir() / "refresh.lock"
        recall.connect(db).close()
        _set_last_refresh(recall, db, time.time())
        check("V-RECALL-SPAWN-FRESH-NO", recall.spawn_refresh_if_stale(db) is False and not lock.exists(),
              "control: a fresh index launches nothing")
        _set_last_refresh(recall, db, time.time() - 10 * recall.STALE_S)
        first = recall.spawn_refresh_if_stale(db)
        held = lock.exists()
        second = recall.spawn_refresh_if_stale(db)
        check("V-RECALL-SPAWN-SINGLE", first is True and held and second is False,
              f"first={first} lock={held} second={second}")
        end = time.time() + 180
        while lock.exists() and time.time() < end:
            time.sleep(1)
        age = recall._age_s(db)
        check("V-RECALL-SPAWN-COMPLETES", not lock.exists() and age < 120,
              f"lock_released={not lock.exists()} age_s={age:.0f}")
        _set_last_refresh(recall, db, time.time() - 10 * recall.STALE_S)
        check("V-RECALL-SPAWN-ATTEMPT-BOUND", recall.spawn_refresh_if_stale(db) is False,
              "a refresh launched seconds ago blocks a relaunch even though the index reads stale")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def unvalidated_gates(tmp: Path, recall) -> None:
    """KACQ answers and the SEO/GEO corpus are candidates, not truth: titled by their question,
    labelled in the block, at most one per prompt, and never displacing a validated memory."""
    d = tmp / "unval"
    raw = d / "raw"
    hits_src = []
    for n, (pid, did) in enumerate((("c1" * 32, "a1" * 32), ("c2" * 32, "a2" * 32))):
        (raw / "prompt" / pid[:2]).mkdir(parents=True, exist_ok=True)
        (raw / "prompt" / pid[:2] / f"{pid}.md").write_text(
            f"Which narwhal tusk sonar method works best, variant {n}?", encoding="utf-8")
        rdir = raw / "response" / did[:2]
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / f"{did}.md").write_text("Narwhal tusk ivory acts as a sonar sensor; "
                                         "measure with a hydrophone array.", encoding="utf-8")
        (rdir / f"{did}.meta.json").write_text(json.dumps({"prompt_id": pid}), encoding="utf-8")
        hits_src.append((rdir / f"{did}.md", "candidate", "kacq"))
    jl = d / "seo-geo-answers-x-full.jsonl"
    jl.write_text("\n".join(json.dumps(r) for r in (
        {"id": "SG-0001", "question": "Does narwhal tusk sonar content rank?", "answer":
         "Narwhal tusk ivory sonar pages rank when the hydrophone data is original."},
        {"id": "SG-0002", "question": "Crawl budget from logs?", "answer": "Count fetches."})),
        encoding="utf-8")
    hits_src.append((jl, "seo-geo", "global"))
    mdir = d / "memory"
    mdir.mkdir()
    (mdir / "narwhal.md").write_text(mem("narwhal-tusk-sonar", "Narwhal tusk sonar hydrophone",
                                         "Our narwhal tusk ivory sonar test used a hydrophone."),
                                     encoding="utf-8")
    hits_src.append((mdir / "narwhal.md", "memory", "C--proj"))
    # 4 chunks share the query terms; the 15% common-term ceiling needs >= 27 chunks in all.
    for i in range(24):
        (mdir / f"pad{i}.md").write_text(mem(f"pad{i}", "Kelp forest", f"Kelp grows {i}."),
                                         encoding="utf-8")
    hits_src += [(f, "memory", "C--x") for f in mdir.glob("pad*.md")]
    db = d / "u.db"
    recall.refresh(hits_src, db)
    same = recall.refresh(hits_src, db)
    real_chunker = recall.CHUNKER
    recall.CHUNKER = real_chunker + "-next"
    try:
        bumped = recall.refresh(hits_src, db)
    finally:
        recall.CHUNKER = real_chunker
    check("V-RECALL-CHUNKER-VERSION", same["changed"] == 0 and bumped["changed"] == len(hits_src),
          f"same chunker changed={same['changed']} (control); new chunker changed="
          f"{bumped['changed']}/{len(hits_src)}")
    cand = recall.chunk_candidate(hits_src[0][0])
    check("V-RECALL-CANDIDATE-TITLED", bool(cand) and cand[0][0].startswith("Which narwhal")
          and "hydrophone" in cand[0][1], f"{cand[:1]}")
    jc = recall.chunk_jsonl(jl)
    check("V-RECALL-JSONL-CHUNKS", [t.split()[0] for t, _ in jc] == ["SG-0001", "SG-0002"], f"{jc}")
    q = recall.query("narwhal tusk ivory sonar hydrophone", "C:\\proj", db)
    kinds = [h["kind"] for h in q]
    unval = [k for k in kinds if k in recall.UNVALIDATED]
    check("V-RECALL-UNVALIDATED-CAPPED", len(unval) == recall.MAX_UNVALIDATED,
          f"kinds={kinds} (3 unvalidated sources match, cap {recall.MAX_UNVALIDATED})")
    check("V-RECALL-VALIDATED-KEPT", "memory" in kinds, "control: the validated memory still shows")

    # Window flood (review MEDIUM): >80 strong seo-geo rows in ONE jsonl must not push a weaker
    # validated memory out of the SQL row window before the cap is applied.
    fd = tmp / "flood"
    fd.mkdir()
    recs = [{"id": "SG-%04d" % i, "question": "quokka wombat dingo platypus %d" % i,
             "answer": "quokka wombat dingo platypus quokka wombat dingo platypus"}
            for i in range(120)]
    recs += [{"id": "SG-F%04d" % i, "question": "filler topic %d" % i, "answer": "nothing"}
             for i in range(900)]
    fj = fd / "flood-full.jsonl"
    fj.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    fm = fd / "wombat.md"
    fm.write_text(mem("wombat-survey", "Field notes",
                      "A long survey of many things. " * 40 + "quokka wombat dingo once."),
                  encoding="utf-8")
    fdb = fd / "f.db"
    recall.refresh([(fj, "seo-geo", "global"), (fm, "memory", "C--proj")], fdb)
    con = sqlite3.connect(str(fdb))
    try:
        order = [r[0] for r in con.execute(
            "SELECT c.path FROM recall_fts JOIN chunks c ON c.id = recall_fts.rowid "
            "WHERE recall_fts MATCH '\"quokka\" OR \"wombat\" OR \"dingo\"' "
            "ORDER BY bm25(recall_fts, 4.0, 1.0)")]
    finally:
        con.close()
    rank = order.index(str(fm)) if str(fm) in order else -1
    fq = recall.query("quokka wombat dingo sighting", "C:\\proj", fdb)
    check("V-RECALL-WINDOW-FLOOD", rank >= 80 and any(h["kind"] == "memory" for h in fq),
          f"precondition: memory at raw bm25 rank {rank} (>=80 = outside a single window); "
          f"hits={[h['kind'] for h in fq]}")
    saved = os.environ.get("CPP_RECALL_DIR")
    os.environ["CPP_RECALL_DIR"] = str(d / "state")
    try:
        import shutil
        shutil.copy(db, recall.db_path())
        block = recall.recall_block("narwhal tusk ivory sonar hydrophone",
                                    {"session_id": "s-unval", "cwd": "C:\\proj"})
    finally:
        os.environ["CPP_RECALL_DIR"] = saved
    label_ok = any(lbl in block for lbl in recall.UNVALIDATED.values())
    check("V-RECALL-UNVALIDATED-LABELLED", label_ok and "[memory]" in block,
          "the candidate carries its label; the memory carries none")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="recall_test_"))
    os.environ["CPP_RECALL_DIR"] = str(tmp / "state")
    os.environ["CPP_RECALL_NO_SPAWN"] = "1"
    from modules.gsd_x import recall

    # -- chunking
    chunks = recall.chunk_rules(UKDL_SHAPE)
    titles = [t for t, _ in chunks]
    check("V-RECALL-CHUNK-RULES",
          titles == ["Section Alpha", "T-ALPHA-TRAP-001", "PR-BETA-RULE-002", "HR-GAMMA-STOP-003"],
          f"titles={titles}")
    mt = recall.chunk_memory(mem("n1", "the description", "body text"), "stem")
    check("V-RECALL-CHUNK-MEMORY", mt and mt[0][0] == "n1" and mt[0][1].startswith("the description"),
          f"{mt}")

    # -- positive + negative control on one index
    src = build_corpus(tmp)
    db = recall.db_path()
    r = recall.refresh(src, db)
    check("V-RECALL-BUILD", r["changed"] == len(src) and r["chunks"] == len(src), f"{r}")
    hit = recall.query("the zeppelin mooring tether keeps failing", "C:\\proj", db)
    check("V-RECALL-POSITIVE", bool(hit) and hit[0]["title"] == "zeppelin-mooring",
          f"hits={[h['title'] for h in hit]}")
    miss = recall.query("bake a sourdough bread with rye flour", "C:\\proj", db)
    check("V-RECALL-NEGATIVE-CONTROL", miss == [], f"hits={[h['title'] for h in miss]}")
    one = recall.query("zeppelin", "C:\\proj", db)
    check("V-RECALL-ONE-TERM-ABSTAINS", one == [], f"hits={len(one)}")
    two = recall.query("zeppelin rosin", "C:\\proj", db)
    check("V-RECALL-SPLIT-TERMS-REFUSED", two == [], "terms from two different files do not combine")

    # -- incremental refresh: edit then delete
    z = next(f for f, _, _ in src if f.name == "zeppelin.md")
    time.sleep(0.05)
    z.write_text(mem("zeppelin-mooring", "Albatross gannet petrel sightings",
                     "Albatross and gannet near the petrel colony."), encoding="utf-8")
    r2 = recall.refresh(src, db)
    after = recall.query("albatross gannet petrel colony", "", db)
    check("V-RECALL-EDIT-REINDEXED", r2["changed"] == 1 and bool(after),
          f"changed={r2['changed']} hits={len(after)}")
    z.unlink()
    r3 = recall.refresh([s for s in src if s[0] != z], db)
    gone = recall.query("albatross gannet petrel colony", "", db)
    check("V-RECALL-DELETE-REMOVED", r3["removed"] == 1 and gone == [] and r3["chunks"] == len(src) - 1,
          f"{r3}")

    # -- session dedupe through the hook-facing block
    z.write_text(mem("zeppelin-mooring", "Zeppelin mooring tether snaps under gusts",
                     "The mooring tether on the zeppelin mast snapped."), encoding="utf-8")
    recall.refresh(src, db)
    p = "zeppelin mooring tether snapped again"
    first = recall.recall_block(p, {"session_id": "s-one", "cwd": "C:\\proj"})
    second = recall.recall_block(p, {"session_id": "s-one", "cwd": "C:\\proj"})
    other = recall.recall_block(p, {"session_id": "s-two", "cwd": "C:\\proj"})
    check("V-RECALL-BLOCK-FIRST", "zeppelin-mooring" in first, f"{len(first)} B")
    check("V-RECALL-SESSION-DEDUPE", second == "", "same session sees it once")
    check("V-RECALL-NEW-SESSION-SEES", "zeppelin-mooring" in other, "control: a new session sees it")
    os.environ["CPP_RECALL"] = "off"
    check("V-RECALL-KILL-SWITCH", recall.recall_block(p, {"session_id": "s-3"}) == "", "")
    del os.environ["CPP_RECALL"]

    # -- fail-open: corrupt db and missing db
    bad = tmp / "bad_state"
    bad.mkdir()
    (bad / "recall.db").write_bytes(b"this is not sqlite" * 50)
    os.environ["CPP_RECALL_DIR"] = str(bad)
    try:
        out = recall.recall_block(p, {"session_id": "s-4"})
        check("V-RECALL-FAILOPEN-CORRUPT", out == "", "corrupt db -> ''")
    except Exception as e:                              # noqa: BLE001
        check("V-RECALL-FAILOPEN-CORRUPT", False, f"raised {e!r}")
    check("V-RECALL-FAILOPEN-MISSING", recall.query(p, "", tmp / "nope.db") == [], "")
    os.environ["CPP_RECALL_DIR"] = str(tmp / "state")

    # -- unvalidated kinds: KACQ candidates and the SEO/GEO corpus
    unvalidated_gates(tmp, recall)

    # -- end to end through the real owner (cli.py), as the hook spawns it
    env = dict(os.environ, PYTHONIOENCODING="utf-8", CLAUDE_STATE_DIR=str(tmp / "hb"))
    res = subprocess.run([sys.executable, str(ROOT / "modules" / "gsd_x" / "cli.py")],
                         input=json.dumps({"prompt": p, "cwd": "C:\\proj"}),
                         capture_output=True, text=True, env=env, timeout=60)
    check("V-RECALL-OWNER-E2E", res.returncode == 0 and "Recall --" in res.stdout
          and "zeppelin-mooring" in res.stdout, f"rc={res.returncode} out={len(res.stdout)} B")

    # -- catalog
    import memory_catalog as mc
    root = tmp / "projects"
    memdir = root / "C--proj" / "memory"
    files = [f.name for f in mc.unindexed(memdir)]
    check("V-RECALL-CATALOG-UNINDEXED", "kiln.md" not in files and "zeppelin.md" in files
          and len(files) == len(FILLER) - 1, f"{files}")
    check("V-RECALL-CATALOG-SUBINDEX", "glacier.md" not in files and "MEMORY-sub.md" not in files,
          "a file listed in a sub-index is indexed, and the sub-index is not a memory")
    mc.main(["--root", str(root), "--apply"])
    idx1 = (memdir / "MEMORY.md").read_bytes()
    cat = (memdir / "MEMORY_CATALOG.md").read_text(encoding="utf-8")
    check("V-RECALL-CATALOG-WRITTEN", "zeppelin-mooring" in cat and "(kiln.md)" not in cat
          and idx1.count(b"MEMORY_CATALOG.md") == 1, "")
    mc.main(["--root", str(root), "--apply"])
    check("V-RECALL-CATALOG-IDEMPOTENT", (memdir / "MEMORY.md").read_bytes() == idx1, "")
    check("V-RECALL-CATALOG-WHOLE-NAME", not mc.mentions("- [a](prefix_x.md)", "x.md")
          and mc.mentions("- [a](x.md)", "x.md"), "prefix_x.md does not index x.md; control: x.md does")

    # -- WAL: hook readers must not wait on a refresh's write transaction (review M1)
    con = recall.connect(db)
    mode = con.execute("PRAGMA journal_mode").fetchone()[0]
    con.close()
    check("V-RECALL-WAL", mode == "wal", f"journal_mode={mode}")

    # -- the detached refresh, driven for real (review M2)
    spawn_gates(tmp, recall)

    # -- live index: measured, never assumed
    live = Path.home() / ".claude" / "state" / "recall" / "recall.db"
    if live.is_file():
        t0 = time.perf_counter()
        hits = recall.query("session hangs after a background task notification", "", live)
        ms = (time.perf_counter() - t0) * 1000
        check("V-RECALL-LIVE-LATENCY", ms < 1500 and bool(hits), f"query_ms={ms:.0f} hits={len(hits)}")
    else:
        print("INCONCLUSIVE V-RECALL-LIVE-LATENCY no live index (run --refresh)")

    print(f"RECALL_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
