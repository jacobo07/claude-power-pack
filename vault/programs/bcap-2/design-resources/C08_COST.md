# D21-C08 context cost measurement (epoch 2, 2026-11-19)

Instrument: `reference_intel.rank` over `TEST_CORPUS.json` (24 self-authored items, 8 queries), bytes of JSON, not tokens.

| Quantity | Bytes | Source |
|---|---|---|
| Whole corpus loaded into context | 6291 | `json.dumps(items)` |
| Retrieval, per query (8 queries) | 2, 270, 276, 524, 527, 751, 785, 800 (mean 492) | picks only |
| Existing design-md README + 6 prompts | 20637 | `wc -c modules/design-md` |

Reading: retrieving top-k costs 0-13% of loading the 24-item corpus, and an ABSTAIN costs ~nothing. Bytes are a proxy for
tokens (unmeasured ratio). The ratio is for 24 authored items, so it says nothing about a real catalogue of thousands.

NOT measured: prompt effectiveness (does a retrieved reference improve a render vs the existing DESIGN.md workflow).
That needs rendered comparisons and stays OPEN; D21-C08 is PARTIALLY_PROVEN on the cost half only.
