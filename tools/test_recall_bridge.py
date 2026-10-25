#!/usr/bin/env python
"""V-RECALL-BRG-* gates: ES/EN term bridge, paraphrase aliases and the score floor.

Hermetic: a private index in a temp dir (CPP_RECALL_DIR), planted English-only documents
plus filler. Each gate has a positive control (the thing it must still find) so a gate that
refuses everything cannot pass.

Run: python tools/test_recall_bridge.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.gsd_x import recall  # noqa: E402

passes = fails = 0

FILLER_WORDS = ("apple orchard harvest cider barrel tractor meadow lantern compass voyage harbor "
                "glacier summit canyon prairie lagoon thicket pasture quarry bridge tunnel ferry "
                "violin cello trumpet drummer chorus ballet sculpture mosaic fresco tapestry").split()


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def plant(d: Path) -> list:
    docs = {
        "hook-screen.md": ("# Hook console host clears screen\n\nA hook that launches a headless "
                           "console host clears the terminal screen of the pane. Never spawn the "
                           "console host from a hook; the screen stays blank until restart."),
        "timeout-orphans.md": ("# Timeout reaping\n\nA timeout that kills only the direct child "
                               "leaves orphan processes behind. Reap the whole tree, never the "
                               "child alone, or the orphan processes accumulate."),
        # Long and unrelated: mentions three ordinary words once each, deep in the body.
        "long-misc.md": ("# Quarterly logistics notes\n\n" + ("Shipping lanes were reviewed and "
                         "pallets were counted twice by the night crew. " * 40) +
                         "\nOne line mentions a backup, a schedule and a report in passing.\n" +
                         ("The warehouse doors were repainted and the forklift batteries rotated. " * 40)),
    }
    for i, w in enumerate(FILLER_WORDS):
        docs[f"filler{i:02d}.md"] = (f"# Filler {w}\n\nNote about {w} and {FILLER_WORDS[(i + 1) % len(FILLER_WORDS)]} "
                                     f"and {FILLER_WORDS[(i + 2) % len(FILLER_WORDS)]} for padding the index.")
    out = []
    for name, text in docs.items():
        p = d / name
        p.write_text(text, encoding="utf-8")
        out.append((p, "lesson", "global"))
    return out


def names(hits) -> list:
    return [Path(h["path"]).name for h in hits]


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="test_recall_bridge_"))
    old = os.environ.get("CPP_RECALL_DIR")
    os.environ["CPP_RECALL_DIR"] = str(d / "state")
    os.environ["CPP_RECALL_NO_SPAWN"] = "1"
    try:
        docs = d / "docs"
        docs.mkdir()
        src = plant(docs)
        db = recall.db_path()                  # state_dir() creates the temp dir
        recall.refresh(sources=src, db=db)

        # (a) a Spanish query reaches an English-only document through the bridge.
        es = "la pantalla queda en blanco cuando se lanza la consola sin ventana"
        check("V-RECALL-BRG-ES-TO-EN", "hook-screen.md" in names(recall.query(es, db=db)),
              f"hits={names(recall.query(es, db=db))}")
        # control: the English wording of the same question already finds it (no bridge needed).
        en = "the hook launches a console host and the terminal screen goes blank"
        check("V-RECALL-BRG-ES-CONTROL", "hook-screen.md" in names(recall.query(en, db=db)),
              f"hits={names(recall.query(en, db=db))}")

        # (b) an English paraphrase reaches its target through an alias.
        para = "the watchdog terminates one process and abandons stray subprocesses"
        check("V-RECALL-BRG-ALIAS", "timeout-orphans.md" in names(recall.query(para, db=db)),
              f"hits={names(recall.query(para, db=db))}")
        direct = "the timeout kills only the direct child and leaves orphan processes behind"
        check("V-RECALL-BRG-ALIAS-CONTROL", "timeout-orphans.md" in names(recall.query(direct, db=db)),
              f"hits={names(recall.query(direct, db=db))}")

        # (c) a query below the score floor abstains while a known HIT still returns.
        weak = "backup schedule report"
        wh = recall.query(weak, db=db)
        check("V-RECALL-BRG-FLOOR-ABSTAIN", wh == [], f"hits={names(wh)}")
        strong = recall.query(direct, db=db)
        check("V-RECALL-BRG-FLOOR-CONTROL", bool(strong) and strong[0].get("score", -1) >= getattr(recall, "MIN_SCORE", float("inf")),
              f"top={names(strong)[:1]} score={strong[0].get("score") if strong else None}")
    finally:
        if old is None:
            os.environ.pop("CPP_RECALL_DIR", None)
        else:
            os.environ["CPP_RECALL_DIR"] = old
        os.environ.pop("CPP_RECALL_NO_SPAWN", None)
        shutil.rmtree(d, ignore_errors=True)

    print(f"RECALL_BRG_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
