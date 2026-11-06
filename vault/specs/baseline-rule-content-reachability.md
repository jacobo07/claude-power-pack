---
status: APPROVED 2026-11-06 (Owner "y" to the S15 plan, coordinator lane "baseline rule-content reachability"; S15 brief XXIX)
covers: [baseline-rule-content-reachability, deferred-rule-retrieval, knowledge-obligation]
tier: T2
owner: modules/tower (select, donegate, baselines) · modules/gsd_x/cli.family_block · tools/family_baseline.py
---

# A deferred baseline rule must be retrievable, and an unread one must be an explicit obligation

## Incident (measured, 2026-11-06, binary_reconstruction/B1)
B1 holds 12 active rules. `select.select_for_injection` keeps at most 8 entries / 1,400 characters per family, so 7 are
shown and 5 are deferred, all 4 new S14 rules among them. The injected block says only
"Not shown (prompt ceiling), judged anyway: <ids>". A fresh agent sees the 5 rule NAMES and no way to read their content.
The S14 inheritance check counted a PASS on the block stamp alone.

## Distinctions the system must keep (brief XXIX)
selected -> name injected -> content available -> content retrieved -> applied -> validated. A name in a prompt is
"name injected", never "content available".

## Change (extend the owners; the 1,400 ceiling stays)
1. **Retrieval command.** `tools/family_baseline.py rule <family> (--deferred | <id>...)` prints each entry's
   requirement, why, check and origin. Each call appends `{"kind": "rule_retrieved", family, judged_under,
   generation_sha256, ids}` to the tower consumption ledger, the same file `family_block` writes.
2. **Block text.** The deferred line becomes an instruction carrying the ABSOLUTE retrieval command, so it works from
   any repo: "Not shown (prompt ceiling) -- read them before building: `python <PP>/tools/family_baseline.py rule
   <family> --deferred` (ids ...)".
3. **Done-gate.** `donegate.judge` reports, per entry, `content`: INJECTED | RETRIEVED | NAME_ONLY. `RETRIEVED` means a
   rule_retrieved row exists for this generation's sha. The report also carries `knowledge_unmet`: the entries that are
   NAME_ONLY and whose verdict is neither APPLIED_VERIFIED nor NOT_APPLICABLE, each an explicit unmet knowledge
   obligation. `judge` (CLI) prints them. Like the rest of the done-gate this is report-only, and `would_block` keeps its
   meaning.

## Acceptance (tools/test_tower_donegate.py and tools/test_family_injection.py)
- The deferred line names a runnable absolute command. Running that command prints the full requirement of every
  deferred entry and writes one ledger row.
- judge, before any retrieval: deferred prose entries are NAME_ONLY and appear in `knowledge_unmet`; injected entries are
  INJECTED. After `rule --deferred`, the same entries are RETRIEVED and `knowledge_unmet` is empty.
- Control: a generation whose entries all fit has no deferred line, and `knowledge_unmet` is empty.
- Mutation: when the ledger write is skipped, the RETRIEVED assertion goes red.

## Residual (stated)
Retrieval is scoped to the generation, not to a session: a retrieval by any session satisfies the obligation. "Applied"
remains what the existing checks prove. Retrieval proves the content was read, not that it was followed.

## Rollback
Revert the commit. The ledger rows are additive, and an old reader ignores `kind: rule_retrieved`.
