# WU-W6 -- Causal token ledger over the programme's own workers (zero model work on Tennis)

Common brief: `PROGRAMME.md`. Plan section 5 (W6). Needs W5b DONE.

Goal: every processed token of W1-W5b attributed to a cause, so the reforecast separates irreducible semantic
inference from architecture tax.
1. Collect the transcripts of this programme's workers (mission records in `~/.claude/state/gsd-mission-*.json` whose
   wu_packet path is under `vault/programs/tennis-rf/`; include subagent transcripts if any).
2. Classify each call deterministically: STARTUP/FLOOR (first call of an epoch), READ, REREAD (same path, unchanged),
   SEARCH (grep/glob), SEMANTIC (reasoning turn that precedes a new source/transform edit), IMPLEMENT (edit/write of
   tooling), PROOF (tests, judge, oracle runs), REPAIR (edit after a red test or failed judge), CONTROL (git, status,
   mission/chain tools), RECOVERY (retry of an identical failed command), RECEIPT. Reuse `tools/session_autopsy.py`
   in PP if it already classifies (read it; extend only through its CLI if a role is missing, never fork it).
3. Output `measure/causal-ledger.json`: per unit and per category -- calls, processed tokens, share; the unattributed
   share stated; tokens per verified function split into semantic vs tax.
4. Derived metrics (UNKNOWN where not measured): LLM invocation density, context duplication factor, startup tax,
   raw-binary page-fault rate (re-reads of disassembly for already-recorded functions), model displacement rate.
Receipt (write it to vault/programs/tennis-rf/WU-W6-receipt.md, Status line per PROGRAMME.md step 3; the chain reads only that file): the category table, unattributed share (>= 95 % attributed or the gap named), commits.
