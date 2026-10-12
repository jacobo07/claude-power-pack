# WU-D11 -- Ph11 scale readiness + knowledge promotion (laptop light)

Common brief: `D28-BRIEF.md`. Plan Ph11, MDG 23-27. Needs W8b DONE. Inputs: `WU-W8b-receipt.md`, D-unit
receipts, `KNOWLEDGE.md`, `KNOWLEDGE-TRFC.md`, the frontiers file.

Steps:
1. Scale Readiness verdict `PASS` or `NO_SCALE` in `vault/programs/tennis-rf/SCALE-READINESS.md`: one line per plan
   precondition (claim-evidence contract live, automatic succession live, deterministic-first gate live, idiom/
   cluster abstention honoured, residual compiler reproduces, incremental build reproduces, Scope-B admission from
   W8b), each with its evidence path. Any missing = NO_SCALE with the exact missing item. Scope B itself is NOT
   started (Owner decision).
2. Promote every new KNOWLEDGE / KNOWLEDGE-TRFC entry from D-units: hard rules (bug that must never recur) into
   PP `vault/knowledge_base/ukdl-universal.md` style entries via the repo's own tool if one exists
   (`tools/` grep `ukdl`), traps and process rules likewise; one line each, citing the entry. Do not hand-write
   into `vault/knowledge_base/ccf/`.
3. Update `vault/plans/tennis-frontier-collapse-2026-10-12.md` front matter `status:` to `EXECUTED` with a short
   `## Outcome` section (per phase: DONE / BLOCKED_HUMAN / NOT_RUN, MDG values, commit ids, tokens from
   `goal-lineage`).
4. Remaining gated phases (Ph8 tournament, Ph9 synthesis) stay for the chain units D8/D9 after you; say in the
   receipt what they need from the Owner (jobs 5-6).
Done-check: SCALE-READINESS.md + plan outcome committed; promotions listed in the receipt.
Receipt: `WU-D11-receipt.md`.
