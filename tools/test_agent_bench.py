"""V-BENCH-* gates for tools/agent_bench.py (S3 scorer). Every rule is driven from both poles:
a scorer that always hits, never hits, counts clean items, or cannot say VOID goes red here."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_bench as B  # noqa: E402

passes = fails = 0
KEY = json.loads((B.BENCH / "answer_key.json").read_text(encoding="utf-8"))["fixtures"]
F1 = KEY["F1-payments-ledger.md"]

PERFECT_F1 = """## Audit Result
**Gaps found:** 8

### Gaps

1. **[INTEGRATION] Step 1 duplicates billing ownership**
   - Why this matters: billing is the single writer; a parallel owner splits it.
2. **[EDGE] Step 2 charge() is not idempotent**
   - Why: a crash between the API call and the insert double charges.
3. **[EDGE] Step 3 dedup by timestamp**
   - Why: two events in the same second collide; use event.id.
4. **[EDGE] Step 4 backfill without dual-write**
   - Why: rows written during the backfill are lost at cutover.
5. **[EDGE] Step 5 balance read-modify-write**
   - Why: lost update race; needs an atomic update.
6. **[ENV] Step 6 secret key in config.yaml**
   - Why: a committed plaintext credential.
7. **[COMPLETION-GATE] Step 7 mock-only done gate**
   - Why: a mock cannot fail the way production reality does.
8. **[INTEGRATION] Step 8 ReconcileService has no caller**
   - Why: nothing schedules it; unreachable.

### Audit clean items (informational, not blocking)
1. Step 2 charge() reviewed for idempotency.
"""


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def s(hits, fp):
    return {"n_hits": hits, "fp": fp}


def grid(mono, virt, crip):
    return {f: {"monolithic": mono, "virtual": virt, "crippled": crip} for f in B.FIXTURES}


def main():
    check("V-BENCH-MANIFEST-CLEAN", B.manifest_mismatches() == [], f"bad={B.manifest_mismatches()}")
    root = Path(tempfile.mkdtemp(prefix="bench_"))
    man = json.loads((B.BENCH / "MANIFEST.json").read_text(encoding="utf-8"))
    for rel in man["files"]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(B.ROOT / rel, root / rel)
    tampered = root / "vault/benchmarks/agent_virtualization/answer_key.json"
    tampered.write_bytes(tampered.read_bytes() + b" ")
    bad = B.manifest_mismatches(root)
    check("V-BENCH-MANIFEST-DETECTS-TAMPER", len(bad) == 1 and "answer_key" in bad[0], f"bad={bad}")

    r = B.score_reply(PERFECT_F1, F1)
    check("V-BENCH-PERFECT-ALL-HITS", r["n_hits"] == 8 and r["fp"] == 0 and r["blocks"] == 8, f"{r}")

    anchors_only = "### Gaps\n\n" + "".join(f"{i}. **[EDGE] Step {i} looks fine**\n" for i in range(1, 9))
    r = B.score_reply(anchors_only, F1)
    check("V-BENCH-ANCHOR-WITHOUT-CONCEPT-MISSES", r["n_hits"] == 0 and r["fp"] == 8, f"{r}")

    noise = PERFECT_F1.replace("### Audit clean", "9. **[AUTH] Missing rate limit on checkout**\n\n### Audit clean")
    r = B.score_reply(noise, F1)
    check("V-BENCH-UNMATCHED-BLOCK-IS-FP", r["n_hits"] == 8 and r["fp"] == 1 and r["blocks"] == 9, f"{r}")

    only_clean = "## Audit Result\n**Gaps found:** 0\n\n### Audit clean items\n1. Step 2 charge() idempotency reviewed, fine.\n"
    r = B.score_reply(only_clean, F1)
    check("V-BENCH-CLEAN-ITEMS-NEVER-COUNT", r["blocks"] == 0 and r["n_hits"] == 0, f"{r}")

    v = B.verdict(grid(s(8, 1), s(7, 2), s(4, 1)), [])
    check("V-BENCH-NON-INFERIOR-AT-MARGIN", v["verdict"] == "NON_INFERIOR", f"{v['verdict']}")
    v = B.verdict(grid(s(8, 1), s(6, 1), s(4, 1)), [])
    check("V-BENCH-RECALL-LOSS-IS-REGRESSION", v["verdict"] == "REGRESSION", f"{v['verdict']}")
    v = B.verdict(grid(s(8, 1), s(8, 3), s(4, 1)), [])
    check("V-BENCH-FP-GROWTH-IS-REGRESSION", v["verdict"] == "REGRESSION", f"{v['verdict']}")
    v = B.verdict(grid(s(8, 1), s(8, 1), s(8, 1)), [])
    check("V-BENCH-BLIND-CONTROL-IS-VOID", v["verdict"] == "VOID", f"{v['verdict']}")
    g = grid(s(8, 1), s(8, 1), s(4, 1))
    g["F2-recovery-daemon.md"]["virtual"] = {"status": "UNMEASURED"}
    v = B.verdict(g, [])
    check("V-BENCH-UNMEASURED-IS-INCONCLUSIVE", v["verdict"] == "INCONCLUSIVE", f"{v}")
    v = B.verdict(grid(s(8, 1), s(8, 1), s(4, 1)), ["x: changed"])
    check("V-BENCH-TAMPER-IS-INCONCLUSIVE", v["verdict"] == "INCONCLUSIVE", f"{v['verdict']}")

    total = passes + fails
    print(f"BENCH_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
