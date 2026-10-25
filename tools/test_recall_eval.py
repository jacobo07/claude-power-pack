#!/usr/bin/env python
"""V-RECALL-EVAL-* gates: proof that tools/recall_eval.py can return the other answer.

Every index here is hermetic (built in a temp dir from planted files), never the live one.
Each gate pairs a planted defect with a control that measures the same thing without it, so
an eval that always reports a perfect score, or always reports a failure, cannot pass.

Run: python tools/test_recall_eval.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from modules.gsd_x import recall  # noqa: E402
import recall_eval  # noqa: E402

passes = fails = 0
CWD = "C:/hermetic/proj"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def mem(name, body):
    return f"---\nname: {name}\ndescription: {body}\n---\n\n{body}\n"


class World:
    """A pp root, a memory dir and an index, all under one temp dir."""

    def __init__(self, d: Path):
        self.d = d
        self.pp = d / "pp"
        self.mem = d / "projects" / recall.project_scope(CWD) / "memory"
        self.mem.mkdir(parents=True)
        (self.pp / "vault" / "lessons").mkdir(parents=True)
        self.sources = []

    def memory(self, fname, body):
        f = self.mem / fname
        f.write_text(mem(f.stem, body), encoding="utf-8")
        self.sources.append((f, "memory", self.mem.parent.name))
        return f

    def build(self, name):
        db = self.d / f"{name}.db"
        recall.refresh(sources=self.sources, db=db)
        return db

    def run(self, db, queries):
        return recall_eval.evaluate(db, queries, pp_root=self.pp, mem_dir=self.mem,
                                    default_cwd=CWD)


HIT_A = {"id": "a", "lang": "en", "q": "quokka zeppelin marmalade", "expect": ["mem:alpha.md"]}
HIT_B = {"id": "b", "lang": "en", "q": "harpsichord glacier lantern", "expect": ["mem:bravo.md"]}
# Every term is indexed, but no chunk holds three of them, and the expected one holds none.
MISS_C = {"id": "c", "lang": "es", "q": "quokka harpsichord glacier", "expect": ["mem:charlie.md"]}
NEG = {"id": "n", "negative": True, "q": "walrus saxophone dandelion", "expect": []}


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="test_recall_eval_"))
    try:
        w = World(d)
        w.memory("alpha.md", "The quokka rode a zeppelin to fetch marmalade.")
        w.memory("bravo.md", "A harpsichord left on the glacier lit by a lantern.")
        w.memory("charlie.md", "The basilisk tends an orchid beneath the nebula.")
        db = w.build("base")

        # ---- 1. a planted miss lowers recall
        ctl = w.run(db, [HIT_A, HIT_B])["metrics"]
        check("V-RECALL-EVAL-CONTROL-PERFECT", ctl["recall_at_5"] == 1.0 and ctl["mrr"] == 1.0,
              f"recall={ctl['recall_at_5']} mrr={ctl['mrr']}")
        rep = w.run(db, [HIT_A, HIT_B, MISS_C])
        m = rep["metrics"]
        check("V-RECALL-EVAL-PLANTED-MISS", m["recall_at_5"] == round(2 / 3, 4),
              f"recall={m['recall_at_5']} (control 1.0)")
        row_c = next(r for r in rep["rows"] if r["id"] == "c")
        check("V-RECALL-EVAL-TERM-GATE-CLASS", row_c.get("miss_class") == "term-gate",
              f"class={row_c.get('miss_class')}")
        check("V-RECALL-EVAL-BY-LANG", m["by_lang"].get("es", {}).get("recall_at_5") == 0.0
              and m["by_lang"].get("en", {}).get("recall_at_5") == 1.0, f"by_lang={m['by_lang']}")

        # ---- 2. a planted noise hit raises the false-positive rate
        ctl = w.run(db, [NEG])["metrics"]
        check("V-RECALL-EVAL-NEG-CONTROL", ctl["negative_false_positive_rate"] == 0.0,
              f"fp={ctl['negative_false_positive_rate']}")
        w.memory("noise.md", "A walrus played saxophone among the dandelion field.")
        noisy = w.build("noisy")
        m = w.run(noisy, [NEG])["metrics"]
        check("V-RECALL-EVAL-PLANTED-NOISE", m["negative_false_positive_rate"] == 1.0,
              f"fp={m['negative_false_positive_rate']} (control 0.0)")

        # ---- 3. a deleted file is counted stale (label is a substring: no file to validate)
        stale_q = {"id": "s", "q": "basilisk orchid nebula", "expect": ["memory/charlie.md"]}
        ctl = w.run(db, [stale_q])["metrics"]
        check("V-RECALL-EVAL-STALE-CONTROL", ctl["stale_hit_share"] == 0.0 and ctl["recall_at_5"] == 1.0,
              f"stale={ctl['stale_hit_share']} recall={ctl['recall_at_5']}")
        (w.mem / "charlie.md").unlink()
        m = w.run(db, [stale_q])["metrics"]
        check("V-RECALL-EVAL-PLANTED-STALE", m["stale_hit_share"] == 1.0,
              f"stale={m['stale_hit_share']} (control 0.0)")

        # ---- 4. an unindexed source is classified source-not-indexed
        lesson = w.pp / "vault" / "lessons" / "quokka.md"
        lesson.write_text("# Quokka\n\nThe quokka zeppelin marmalade lesson, never indexed.\n",
                          encoding="utf-8")
        unidx = {"id": "u", "q": "quokka zeppelin marmalade", "expect": ["pp:vault/lessons/quokka.md"]}
        rep = w.run(db, [unidx, HIT_A])
        row_u = next(r for r in rep["rows"] if r["id"] == "u")
        check("V-RECALL-EVAL-UNINDEXED", row_u["status"] == "MISS"
              and row_u.get("miss_class") == "source-not-indexed", f"row={row_u.get('miss_class')}")
        row_a = next(r for r in rep["rows"] if r["id"] == "a")
        check("V-RECALL-EVAL-UNINDEXED-CONTROL", row_a["status"] == "HIT",
              f"same prompt, indexed label -> {row_a['status']}")

        # ---- a broken label is INVALID and leaves every rate alone
        bad = {"id": "x", "q": "quokka zeppelin marmalade", "expect": ["mem:does-not-exist.md"]}
        m = w.run(db, [HIT_A, bad])["metrics"]
        check("V-RECALL-EVAL-INVALID-LABEL", m["invalid_labels"] == 1 and m["positives_scored"] == 1
              and m["recall_at_5"] == 1.0, f"invalid={m['invalid_labels']} recall={m['recall_at_5']}")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"RECALL_EVAL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
