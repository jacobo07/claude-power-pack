---
type: synthesis
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki, 2026-09-30-yt-9uojngzcjo, 2026-09-30-yt-91b_v-woaws, 2026-09-30-system-prompts-leaks]
---

# Overview — PP thesis

Goal: understand Claude Power Pack and find the changes that would make it better (Owner, 2026-09-30).

## Current thesis (4 PP-relevant sources, 2 measurements)

1. **PP's doctrine is mainstream practice, not an outlier.** Outside advice on specific prompts, a
   don't-do list, small tasks, a memory file and verifying the verifier matches rules PP already
   has ([[2026-09-30-yt-91b_v-woaws]]).
2. **PP's main cost is the weight of what it loads, not missing rules.** ~167 KB loads on every
   session in this repo; the global CLAUDE.md is 190 characters under the harness warning and ~3× its
   own line target ([[always-loaded-prefix-audit]]). Outside advice says keep it short
   ([[2026-09-30-yt-9uojngzcjo]]).
3. **Some knowledge stores compound, some are archives.** UKDL, knowledge_vault, memory and
   RESUMPTION_FILE are read heavily; `PORTFOLIO_LEARNINGS.md` is not
   ([[measure-knowledge-store-consultation]], [[portfolio-learnings]]).
4. **Cheap levers in the harness itself may be unused.** The reported `/compact` prompt honours a
   `## Compact Instructions` section that PP never writes ([[compact-instructions-section]]).

5. **PP's guidance checks that things exist, not what they say.** SDD-OS checks that a spec exists
   and names the task, never its content; an empty draft spec unlocks a T2 task. Of the spec practices
   with measured evidence, none is required ([[sdd-os-gap-analysis]]). The same pattern as point 3:
   machinery exists and runs, while its effect goes unmeasured.
6. **PP builds the enforcement before the content, then delivers the promise anyway.** The
   Constitutive Baseline Ratchet has hash-anchored generations, an anti-downgrade diff and an honest
   check grammar. But its 60 rules carry 0 runnable checks, no generation past B0 exists, and the
   done-gate it tells the agent about has no caller ([[cbr-gap-analysis]]). Converse of point 5:
   there the template allowed what nothing required; here the code requires what no content
   supplies.

## Open questions

- Which always-loaded rules only restate the harness's own prompt?
- Do skills that replaced always-loaded rules get invoked when they should? (stubs note 0/8 auto-invocation)
- How are `_audit_cache` and `_knowledge_graph` actually consumed? (needs hook/tool logs)
