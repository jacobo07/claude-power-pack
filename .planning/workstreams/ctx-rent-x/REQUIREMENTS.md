# Requirements — ctx-rent-x

Source of truth: `vault/plans/ctx-rent-x-2026-10-31.md` (approved). The Owner contract's 32 master done-gate conditions are
requirements CR-01..CR-32; Phase 8's `done_gate.py` checks each one by receipt.

- CR-01 current CCR release and runtime behaviour verified (release id, generation per process, main/subagent/unit modes)
- CR-02 interactive vs successor/subagent context behaviour measured
- CR-03 real context-rent baseline (Phase 1)
- CR-04 Context Rent measured on >= 1 representative real workload
- CR-05 Dead Context Rent measured or a justified approximation (offline Belady, labelled APPROX)
- CR-06 dominant recurring context classes identified
- CR-07 provider cache and logical rent reported separately
- CR-08 existing ownership reused (plan section 1 list), no parallel system
- CR-09 semantic liveness in an executable path (Safe-to-Forget judgement / projection consumers)
- CR-10 Safe-to-Forget protects authority, obligations, proof
- CR-11 ContextImage equivalent (capsule / successor frontier) compiled from live dependencies
- CR-12 >= 1 capability class materially sparse-loaded (Phase 2 / CCR)
- CR-13 >= 1 large recurring class paged/externalised (Phase 5)
- CR-14 successor uses compiled state (frontier.basis capsule)
- CR-15 fresh-start cost measured
- CR-16 rollover economics measurable (gsd_epoch breakeven advisory)
- CR-17 one representative Work Unit with materially lower rent than baseline (MEASURED, live arm)
- CR-18 correctness and Production Reality preserved
- CR-19 reduction not bought with retries/rereads (page faults, repairs reported)
- CR-20 waiting calls classified (shadow)
- CR-21 realised enforcement measured beyond shadow (Phase 3 canary)
- CR-22 KSR-style high-rent behaviour replayed or analysed
- CR-23 X -> X-prime reported
- CR-24 weekly/account effect measured, not inferred
- CR-25 errors entered into Knowledge Vault + UKDL
- CR-26 UKDL HR/PR/Traps updated where justified
- CR-27 Baseline Ratchet evaluation complete
- CR-28 proven improvements inherited by future construction (gate or default, not a document)
- CR-29 fresh-agent recovery succeeds
- CR-30 all required tests exit 0
- CR-31 all work committed
- CR-32 final branch/HEAD/dirty/push state truthful
