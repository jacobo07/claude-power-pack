# WU-W7 -- Families and novelty density over all 1,797 Tennis candidates (zero model calls on functions)

Common brief: `PROGRAMME.md`. Plan section 5 (W7). Needs W3 DONE (runs after W6 in the chain). Scripts only.

1. Features per function (from step0-3 artefacts + W3's m2c run extended to all 1,797, still no compile): masked
   shape hash (exact and loose), size, CFG block count, call targets, callers, data objects touched, controller-getter
   use (step3), unresolved-type and unk-field counts, Resort exact/loose donor and whether that donor is SRC PROVEN.
2. Families: cluster with at least two independent views agreeing (e.g. loose shape AND call-context); a singleton is
   a family of one. Report method, thresholds and a red control (shuffle features -> family structure collapses).
3. Outputs `measure/families.json` and a summary: family count, size distribution, recurrence (functions in families
   of >= 3), novelty density = independent families / functions, deterministic-eligible share (exact donor proven,
   or m2c-clean + family with a verified member from W5), model-needed share (the rest), and which W5 results
   validate or contradict the clustering.
4. Scope A closure: using step3's 50 getter callers + one level of argument propagation (D21 step 4), list the motion
   closure functions and how many families they span. State the closure definition used.
Receipt: the summary numbers with method, the Scope A closure count, commits.
