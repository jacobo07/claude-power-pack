#!/usr/bin/env python
"""V-RECALL-* gates for Prompt Recall and the memory catalog (vault/specs/prompt-recall.md).

Every refusal is paired with a control in which the fact exists and the hit is admitted, so a
recall that returns nothing at all cannot pass.

Run: python tools/test_prompt_recall.py
"""
from __future__ import annotations

import json
import os
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
