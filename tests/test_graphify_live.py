#!/usr/bin/env python3
"""
V-gates for the Graphify live build (GK-03/04/08/10/12 Python surface).

Hermetic: GRAPHIFY_STATE_DIR is redirected to a fresh tmp dir BEFORE the graph
modules run, so no test ever writes the real ~/.claude/state/graphify. Every
node is built inside a TemporaryDirectory, so the suite is re-run-safe (no
global writes, no time-window dedup) — run it 3x, same result.

Gates:
  V-GRAPHIFY-CLASSIFY        — _classify maps paths to the right node type and
                               does NOT over-promote a bare report_NN_ to dataset.
  V-GRAPHIFY-PROMOTION-GATE  — _is_promotable rejects a bare promotable-type node
                               and accepts a governance / observed-edge one.
  V-GRAPHIFY-WRITEBACK-LOOP  — session_writeback WRITES a repo's node into the
                               central store and a cross-repo query READS it back
                               (the WRITE->READ cycle the Graph-First gate needs).
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# --- hermetic store redirect (must precede any state_dir() call) -------------
_TMP_STATE = tempfile.mkdtemp(prefix="graphify_test_state_")
os.environ["GRAPHIFY_STATE_DIR"] = _TMP_STATE

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT / "modules" / "graphify"))
sys.path.insert(0, str(_REPO_ROOT / "tools"))

import global_store as gs           # noqa: E402
import graphify_knowledge as gkk    # noqa: E402
import session_writeback as swb     # noqa: E402

passes = 0
fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {ev}")


def gate_classify():
    ds = gkk._classify("vault/knowledge_base/graphify/graphify_00_x.md")
    doc = gkk._classify("reports/report_01_summary.md")   # bare _NN_ must NOT be a dataset
    hr = gkk._classify("vault/hard_rules/HARD_RULES.md")
    if ds == "dataset" and doc == "doc" and hr == "hard_rule":
        _ok("V-GRAPHIFY-CLASSIFY", f"kb->dataset, report_01_->{doc}, hard_rules->{hr}")
    else:
        _fail("V-GRAPHIFY-CLASSIFY", f"kb={ds} report={doc} hr={hr}")


def gate_promotion():
    hard = {"node_type": "hard_rule", "node_id": "hard_rule/HR-X", "name": "HR-X", "summary": "", "edges": []}
    bare = {"node_type": "decision", "node_id": "decision/foo", "name": "foo", "summary": "a local note", "edges": []}
    gov = {"node_type": "decision", "node_id": "decision/co", "name": "CO-03 tiering", "summary": "", "edges": []}
    obs = {"node_type": "contract", "node_id": "contract/x", "name": "x", "summary": "",
           "edges": [{"type": "extends", "confidence": "observed"}]}
    checks = [
        gs._is_promotable(hard) is True,
        gs._is_promotable(bare) is False,   # the anti-pollution assertion
        gs._is_promotable(gov) is True,
        gs._is_promotable(obs) is True,
    ]
    if all(checks):
        _ok("V-GRAPHIFY-PROMOTION-GATE", "hard=Y bare=N gov=Y observed=Y")
    else:
        _fail("V-GRAPHIFY-PROMOTION-GATE", f"results={checks}")


def gate_writeback_loop():
    repo = tempfile.mkdtemp(prefix="graphify_test_repo_")
    try:
        kb = Path(repo) / "vault" / "knowledge_base"
        kb.mkdir(parents=True)
        (kb / "graphify_test_dataset.md").write_text(
            "> A hermetic test dataset node.\n\nGoverned by CO-03.\n", encoding="utf-8")

        v = swb.writeback(repo)
        store_exists = gs._global_file().exists()
        res = gs.query_global(node_type="dataset")
        found = any("graphify_test_dataset" in r.get("node_id", "") for r in res)

        if v.get("verdict") == "indexed" and store_exists and found:
            _ok("V-GRAPHIFY-WRITEBACK-LOOP",
                f"verdict={v['verdict']} nodes={v.get('nodes')} query_read_back=True")
        else:
            _fail("V-GRAPHIFY-WRITEBACK-LOOP",
                  f"verdict={v.get('verdict')} store={store_exists} found={found}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def main():
    print("=== test_graphify_live (hermetic) ===")
    gate_classify()
    gate_promotion()
    gate_writeback_loop()
    total = passes + fails
    print(f"GRAPHIFY_LIVE_PASS={passes}/{total}  threshold={total}/{total}")
    shutil.rmtree(_TMP_STATE, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
