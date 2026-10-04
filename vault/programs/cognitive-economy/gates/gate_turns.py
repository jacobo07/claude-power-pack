#!/usr/bin/env python
"""gate_turns.py -- pillar H gate of the cognitive-economy campaign.

Re-runs the turn classifier (`measure/turns.py::classify`, imported) over the frozen feature
sample `measure/turns_frozen_sample.json` and checks that the sha256 of the label sequence equals
the one frozen with the sample. The sample file itself is pinned by sha256 in the ledger's
evidence for H, so the expected hash cannot be regenerated silently next to a changed classifier.

Checks:
  * the sample loads and holds >= 1000 rows (a truncated sample cannot pass);
  * the class order recorded with the sample is the classifier's CLASSES (a reordered rule set is a
    different classifier);
  * labels_sha256 recomputed == frozen labels_sha256;
  * positive control: >= 5 distinct classes in the sample (a classifier collapsed to one answer
    would also change the hash, but this names the failure).

`--perturb-order` swaps the first two classes before classifying; it exists only to drive the red
branch (a gate never seen failing is a rumour).

Exit codes: 0 all checks hold; 1 any check fails or the sample cannot be read.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = HERE.parent / "measure" / "turns_frozen_sample.json"
sys.path.insert(0, str(HERE.parent / "measure"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--perturb-order", action="store_true", help="swap the first two classes (red drill)")
    a = ap.parse_args(argv)
    import turns

    fails = []
    try:
        frozen = json.loads(SAMPLE.read_text(encoding="utf-8"))
        rows = frozen["rows"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"GATE_TURNS=FAIL could not read sample ({exc})")
        return 1
    order = tuple(turns.CLASSES)
    if a.perturb_order:
        order = (order[1], order[0]) + order[2:]
        print(f"  perturbed class order -> {order[:2]}")
    if len(rows) < 1000:
        fails.append(f"sample has {len(rows)} rows (< 1000)")
    if list(frozen.get("classes_order", [])) != list(turns.CLASSES):
        fails.append(f"frozen class order {frozen.get('classes_order')} != classifier {list(turns.CLASSES)}")
    got = turns.labels_sha(rows, order)
    ok = got == frozen.get("labels_sha256")
    print(f"  {'ok  ' if ok else 'FAIL'} labels_sha256 expected {frozen.get('labels_sha256')} observed {got}")
    if not ok:
        fails.append("labels_sha256 mismatch")
    dist = Counter(turns.classify(r, order) for r in rows)
    print(f"  distribution {dict(sorted(dist.items()))}")
    if len(dist) < 5:
        fails.append(f"only {len(dist)} distinct classes (< 5)")
    print(f"GATE_TURNS={'PASS' if not fails else 'FAIL'} failures={len(fails)} rows={len(rows)}")
    for f in fails:
        print(f"  failed: {f}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
