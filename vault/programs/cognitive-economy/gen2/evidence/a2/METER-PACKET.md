# Work packet -- infallible program meter (Owner order 2026-10-07: "hay que hacer infalible el medidor")

work_tree: C:\Users\User\Apps\pp-ce-a2   (branch ce/a2; you are the only writer; never push; never edit ~/.claude/)
done_gate: python tools/test_ce_attribute.py  AND  python tools/test_ce_meter_truth.py  (both exit 0)
bound: 35 turns. Write `evidence/a2/METER-RECEIPT.md` AS YOU GO (append each confirmed fact before moving on).

A2 was stopped by the Owner after a cap breach that the meters disagreed about. The Phase 2 meter
(`vault/programs/cognitive-economy/measure/attribute.py`, `tools/test_ce_attribute.py`, edits in `tools/cep_gen2.py`
and `measure/turns.py`) is committed as WIP. Make metering impossible to get silently wrong.

## Failures observed today (each becomes a RED fixture before its fix)
F1 `gen2/evidence/stage0/self_spend.py --session 489481fa-...` returned `None` (no transcript) because it searched
   only the claude-power-pack project dir; the transcript lives in `~/.claude/projects/C--Users-User-Apps-pp-ce-a2/`.
   With `--dir` it gave 10,695,300 / 61 calls.
F2 `attribute.py` reported session 886d7bb9 at 7,379,518 (28 attributed calls) while the session holds
   16,916,777 / 71 calls: 302 "text-only calls outside every basis" were dropped from the totals.
F3 Receipts self-report boundaries (EDD WU-1: 3) far below metered calls (16).

## Required properties
M1 Find a session by id across EVERY `~/.claude/projects/*/` dir, including subagent transcripts. Zero matches ->
   UNKNOWN (non-zero exit), never 0 or None-as-zero. Several matches -> union, deduplicated.
M2 Session total = every assistant record with usage, dedup by message.id (requestId as tiebreak), unit processed =
   input + cache_creation + cache_read + output. Attribution basis is a SEPARATE breakdown and can never reduce a
   session total; unattributed calls are their own row.
M3 Two independent counters (attribute.py and self_spend.py after the M1 fix) must agree to the token on the same
   input; disagreement -> verdict DISAGREE, never a number. One shared parser is NOT independence: keep them separate.
M4 Torn/unparseable JSONL lines are counted and reported (UNKNOWN fragment), never skipped silently.
M5 Sessions on another host (GEX44) are reported UNKNOWN with the host named unless a local transcript exists.
M6 `cep_gen2.py check_receipt`: a receipt whose self-reported calls/boundaries are below the metered count fails.
M7 Golden values (pin with a timestamp cut-off): 489481fa = 10,695,300 / 61; 886d7bb9 >= 16,916,777 / 71 up to
   2026-10-07T18:00Z.

## Proof
`tools/test_ce_meter_truth.py`: fixtures for F1, F2, F3, duplicate ids, torn line, missing transcript, multi-dir; each
driven red first; `tools/mutation_drill.py` kills a null-as-zero mutant, a drop-text-only mutant and a single-dir
mutant; a positive control shows a correct meter passes. Summary line `CE_METER_PASS=n/m`.
Then write ledger `a2.spent` from the fixed meter (sources listed, UNKNOWN named), commit, and end the receipt with
measured totals for A2 (worker + coordinator) and your own session.
</content>
</invoke>
