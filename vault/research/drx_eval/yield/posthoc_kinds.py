"""POST-HOC (not pre-registered): LLM-call outcomes by kind and arm, and per-pair B-A with A's failure cause."""
import json, sys
from collections import defaultdict
from pathlib import Path

root = Path(sys.argv[1])
ARMS = ("A_t120_c25k", "B_t240_c25k", "C_t120_c12k")
kinds = defaultdict(lambda: defaultdict(lambda: [0, 0, 0.0]))  # arm -> kind -> [calls, timeouts, secs]
cell = {}
for arm in ARMS:
    for d in sorted((root / arm).iterdir()):
        if not d.is_dir() or "_infra_" in d.name or "_lockheld_" in d.name:
            continue
        raws = list(d.glob("*.raw.jsonl"))
        rows = [json.loads(x) for x in raws[0].read_text(encoding="utf-8").splitlines() if x.strip()] if raws else []
        calls = [r for r in rows if r.get("type") == "llm_call"]
        for c in calls:
            k = kinds[arm][c["kind"]]
            k[0] += 1; k[1] += bool(c["timeout"]); k[2] += c["secs"]
        dec = next((c for c in calls if c["kind"] == "decompose"), None)
        cell[(arm, d.name)] = {
            "learnings": sum(1 for r in rows if r.get("type") == "learning"),
            "decompose_timeout": bool(dec and dec["timeout"]),
            "decompose_secs": dec["secs"] if dec else None,
        }
print("== LLM calls by kind: calls / timeouts / mean secs")
for arm in ARMS:
    for kind, (n, t, s) in sorted(kinds[arm].items()):
        print(f"{arm:12} {kind:14} {n:4} {t:3} {s / n:7.1f}")
print("== pairs (B vs A): cell, A learnings, B learnings, A decompose timeout, B decompose secs")
for name in sorted({n for (_, n) in cell}):
    a, b = cell.get(("A_t120_c25k", name)), cell.get(("B_t240_c25k", name))
    if a and b:
        print(f"{name:8} A={a['learnings']:3} B={b['learnings']:3} A_dec_timeout={a['decompose_timeout']!s:5} B_dec_secs={b['decompose_secs']}")
