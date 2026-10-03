[M] -> tools/usage_index.py

Handoff of skill-capability pillar [M] (economics / model / goal relativity), predicted MERGED_INTO_EXISTING_OWNER.

Frozen rule (ledger `frozen.pillars`):

> cost figures come from tools/usage_index.py windows; this program reports token and turn deltas relative to a named denominator and owns no cost model

Frozen owners: `tools/usage_index.py`.

- measured_at_commit: 1e32ae7a3a6404070cb8e5ff6fa9c983ace8c5d6
- freeze: 217d72b5944a664fbc0baa1060c04617ff10f481
- host: kobicraft-gex44
- plane: committed blobs at measured_at_commit (git grep / cat-file / diff / archive), never the working tree
- produced by: python3 tools/skill_handoffs.py --write M
- claim: PASS aperture=PASS cost=PASS control=PASS

## Commands and observed output

| command | observed |
|---|---|
| `git diff --name-only --diff-filter=A 217d72b5 1e32ae7a -- modules tools` | 16 added files |
| `cost-model marker over each added file (each line)` | 2 hits: 0 open, 2 adjudicated not a cost model |
| `cost-model marker over the control tools/usage_index.py` | 3 hits, kinds ['def', 'import'] |
| `ledger state.<P>.savings[] at 1e32ae7a (vault/programs/skill-capability/ledger.json)` | 2 entries |
| `delta lines of evidence/B-listing-floor.md and evidence/E-contribution.md (pattern `(?i)\bdelta [+-]\d\|\bmoved\b.*[+-]\d\|\blargest effect\b`; denominator from line 1)` | 4 lines |

## Claim parts

| part | outcome | reason |
|---|---|---|
| aperture | PASS | 16 added files |
| cost | PASS | 0 open hits in 16 files (2 adjudicated) |
| control | PASS | tools/usage_index.py: 3 hits |

## Aperture

- Population: the same added-file set as K (modules/ and tools/, `--diff-filter=A`, freeze to the measured commit, a superset of this program's files).
- Cost-model marker: a line starting with `def <name containing price|pricing|cost|usd>(`, an import of `pricing_source`, or an UPPER_CASE constant containing PRICE|PRICING|COST|USD assigned at line start. A cost model under other names is outside it; the control shows the marker reaches the owner.
- Figures: read from the ledger's `savings[]` and the delta lines of the B and E evidence files, never by searching evidence for the word token.

## Evidence

### Turn and token figures this program reported

| pillar | what | value | unit | status | displacement | denominator |
|---|---|---|---|---|---|---|
| A | turns saved per false deny (re-issue after the card) | 5 | turns | upper_bound | unknown | D-CARD |
| B | startup tokens per fresh session if a gateway that also pages plugin skills brings full latent listing demand under the cap (recorded next hypothesis, not measured) | 9000 | tokens | upper_bound | unknown | D-LISTING |

### Delta lines quoted from evidence (denominator from each file's line 1)

| source | denominator | line |
|---|---|---|
| B-listing-floor.md:21 | D-LISTING | - ok V-LF-TOKENS: challenger startup_tokens 89844 vs champion 87739 (delta +2105): not below champion, no saving |
| B-listing-floor.md:45 | D-LISTING | - C6 moved the initial listing +11 chars (29991 -> 30002). |
| B-listing-floor.md:46 | D-LISTING | - K4 moved startup tokens +2105 (87739 -> 89844) against the stated noise +-1500 (vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 12): startup tokens rose by 2105, above the stated noise (+-1500) by 605. fresh-session first-call figures; one session each, n=1 per arm. |
| E-contribution.md:45 | D-SESSIONS | Largest effect against N0: authoritative 0 (0 points), stored 1/2 (50 points). |

E reports no turn or token delta. Its only effect figure is a pass-rate difference against arm N0, denominator D-SESSIONS.

### Cost-model sweep at 1e32ae7a

| added file | cost-model hits | hit lines |
|---|---|---|
| tools/card_lineage.py | 0 | - |
| tools/skill_coverage.py | 0 | - |
| tools/skill_creation_gate.py | 0 | - |
| tools/skill_dedup_sweep.py | 1 | 324:def |
| tools/skill_handoffs.py | 0 | - |
| tools/skill_mirror_drift.py | 0 | - |
| tools/test_card_lineage.py | 0 | - |
| tools/test_card_precision.py | 1 | 330:def |
| tools/test_contribution_verdict.py | 0 | - |
| tools/test_listing_floor_verdict.py | 0 | - |
| tools/test_skill_coverage.py | 0 | - |
| tools/test_skill_creation_gate.py | 0 | - |
| tools/test_skill_delivery.py | 0 | - |
| tools/test_skill_drift.py | 0 | - |
| tools/test_skill_handoffs.py | 0 | - |
| tools/test_skill_representation.py | 0 | - |

### Marker hits adjudicated not a cost model: 2

Each is pinned in `M_ADJUDICATED` of tools/skill_handoffs.py by path and exact line; an edit to the line re-opens the hit. The Owner may disagree with a reason.

| file:line | line | why it is not a cost model |
|---|---|---|
| tools/skill_dedup_sweep.py:324 | `def _line_cost(name, status, shape):` | pillar F listing arithmetic: the characters one listing line occupies (len(name) + overhead + N), an integer char count with no price, currency or rate |
| tools/test_card_precision.py:330 | `def write_unborn_pricing(repo: str) -> None:` | pillar A drill fixture: writes a pricing.py into a temporary repo as the subject the commit card judges; its domain is test data, not a cost model of this program |

### Control tools/usage_index.py

- 51: import: `from pricing_source import current_pricing_path  # noqa: E402`
- 520: def: `def load_prices() -> dict:`
- 524: def: `def price_for(model: str, prices: dict):`

## What the owner should do

- `tools/usage_index.py`: cost figures stay yours, from your windows. The figures above are turn and token deltas relative to a named denominator, upper bounds unless the status says realized; none is a cost.

## What this program did not do

- Owns no cost model: the sweep above found no open cost-model marker hit in any added file (2 hit(s) read and adjudicated not a cost model, listed above).
- Converted no token or turn figure to money.
