# SCS C68 — Token-Corpus-Doctrine-by-default

**Sealed:** 2026-07-03
**Type:** process doctrine (NOT a technical fix)
**Predecessor slot check:** C67 = Transparent-Process-Hibernation (`cognitive_os/hibernation_scs_c67.md`) — taken; this is C68.
**Evidence commit:** `548d062` (corpus analyzer + fat-tail classifier, 6/6 ×3 hermetic)

---

## Doctrine

The `.jsonl` corpus at `~/.claude/projects/` is the **source of truth** for any
proposed token optimization. Only optimizations with **quantitative evidence
from the audit** are implemented. No speculative "optimizations" — a pattern
without measurable ROI that does not sacrifice output quality is **ignored**
(reality contract: "si un patrón no tiene ROI medible → ignorar").

## Audit result 2026-07-03 (the sealed finding)

| Dimension | Measured | Verdict |
|---|---|---|
| **Cache ratio** | 96.3% lifetime (0 repos <90% with >500k output) | near-optimal — **no action** |
| **Output fat tail** | top-40 turns: 72% dense-unique reasoning + 22% real `Write` deliverables, **0% repetitive/dataset** | **not reducible** without output-quality loss |
| **Parallel budget** | peak hours run 17–26 concurrent panes (real burn driver) | already governed by **PM-04 Budget Auction** |
| **First-load system prompt** | mean ~57k input (one-time per session, cached after) | **only surviving lever**, modest, Owner-side (see trim proposal) |

**Conclusion:** the PP is near-optimal on every token lever that does not cost
output quality. The audit's value is proving that with numbers, not prose.

## Tooling

```
python tools/token_corpus_audit.py --report <out> [--sample-fat N]
```

- `audit()` — per-repo cache ratio, output distribution, hour-of-day burn,
  re-read detection, context%→output correlation.
- `sample_fat_turns()` — classifies the fattest output turns on disk
  (repetition ratio + primary tool) WITHOUT loading raw content into context.
- Hermetic test: `tools/test_token_corpus_audit.py` (6 V-gates, ×3 stable).

## Re-audit trigger

Re-run the corpus audit after **major PP changes** OR when the **burn rate
shifts >20%** from the 2026-07-03 baseline (lifetime out ≈ 524M, cacheR 96.3%,
first-load mean ~57k). A shift means a pattern changed; re-measure before
acting.

## Cross-references

- Trim proposal (first-load lever): `vault/proposals/2026-07-03_first-load-trim.md`
- Full corpus report: `vault/plans/token-optimization-audit-2026-07-03.md`
- Behavioral (qualitative) audit: `[[conversation-quality-audit]]` — the
  complementary axis measuring *behavior* in content, not *volume*.
