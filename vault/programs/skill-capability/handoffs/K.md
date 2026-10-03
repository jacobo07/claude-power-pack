[K] -> modules/capability_runtime/agent_spec.py

Handoff of skill-capability pillar [K] (capability routing + ACV), predicted MERGED_INTO_EXISTING_OWNER.

Frozen rule (ledger `frozen.pillars`):

> routing lives with ACV; this program contributes opportunity rows through CO-12 and builds no second router

Frozen owners: `vault/specs/agent-capability-virtualization.md`, `modules/capability_runtime/agent_spec.py`.

- measured_at_commit: d0f7bab78458471956fa7b9c005f73c77185e35b
- freeze: 217d72b5944a664fbc0baa1060c04617ff10f481
- host: kobicraft-gex44
- plane: committed blobs at measured_at_commit (git grep / cat-file / diff / archive), never the working tree; plus the host-state row count named below
- produced by: python3 tools/skill_handoffs.py --write K
- claim: PASS aperture=PASS router=PASS control=PASS

## Commands and observed output

| command | observed |
|---|---|
| `git diff --name-only --diff-filter=A 217d72b5 d0f7bab7 -- modules tools` | 15 added files |
| `router marker over each added file (basename, then each line)` | 0 hits |
| `router marker over the controls modules/cost_collapse/router.py, modules/cognitive_os/router.py, modules/knowledge_acquisition/routing.py` | 3 of 3 hit by content |
| `python3 tools/skill_opportunity_signals.py report  (in-process report(); never sync)` | {"rows": 0, "by_decision": {}, "opportunities": 0, "delivered_by_card": 0, "unknown": 0} |

## Claim parts

| part | outcome | reason |
|---|---|---|
| aperture | PASS | 15 added files |
| router | PASS | 0 hits in 15 files |
| control | PASS | modules/cost_collapse/router.py:65; modules/cognitive_os/router.py:75; modules/knowledge_acquisition/routing.py:189 |

## Aperture

- Population: every file ADDED between the freeze 217d72b5 and the measured commit under modules/ and tools/ (`--diff-filter=A`, endpoints compared). The range includes commits of other programs, so it is a superset of this program's files; a file added and removed inside the range is not in it.
- Router marker: a basename matching `rout(e|er|ing)`, or a line starting with `def route(` or `class <Name>Router` (case-insensitive). A router under another name or shape is outside it; the three controls show the marker reaches the repository's existing routers.
- CO-12 row count: host state `UNMEASURED` read on kobicraft-gex44, not a committed blob.

## Evidence

### Router sweep at d0f7bab7

| added file | router hits | hit lines |
|---|---|---|
| tools/card_lineage.py | 0 | - |
| tools/skill_coverage.py | 0 | - |
| tools/skill_creation_gate.py | 0 | - |
| tools/skill_dedup_sweep.py | 0 | - |
| tools/skill_handoffs.py | 0 | - |
| tools/skill_mirror_drift.py | 0 | - |
| tools/test_card_lineage.py | 0 | - |
| tools/test_card_precision.py | 0 | - |
| tools/test_contribution_verdict.py | 0 | - |
| tools/test_listing_floor_verdict.py | 0 | - |
| tools/test_skill_coverage.py | 0 | - |
| tools/test_skill_creation_gate.py | 0 | - |
| tools/test_skill_delivery.py | 0 | - |
| tools/test_skill_drift.py | 0 | - |
| tools/test_skill_representation.py | 0 | - |

### Router controls (must hit by content)

- modules/cost_collapse/router.py: 65: `def route(description: str) -> RouteResult:`
- modules/cognitive_os/router.py: 75: `def route(task: str, *, budget_pressure: bool = False,`
- modules/knowledge_acquisition/routing.py: 189: `def route(`

### CO-12 opportunity rows

- state: UNMEASURED; gex44 has no card ledger (file present: False, rows 0)
- producer: `tools/skill_opportunity_signals.py` (kind `capability_opportunity`, capability `concurrent-writers-shared-tree`), which writes only through `record_signal`.

## What the owner should do

- ACV (`vault/specs/agent-capability-virtualization.md`, `modules/capability_runtime/agent_spec.py`): routing stays with you. Consume this program's opportunity rows from CO-12 (kind `capability_opportunity`, read with `python3 tools/skill_opportunity_signals.py report`).
- The row count on this host is UNMEASURED (reason above). The laptop count is an Owner item `[K]` written by plan 08-04.

## What this program did not do

- Built no router: the sweep above found no router marker in any added file under modules/ or tools/.
- Did not run `sync` (it writes); only `report` was read.
