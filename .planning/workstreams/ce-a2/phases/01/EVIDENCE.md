# Phase 1 (A2-0 Gate truth) -- EVIDENCE

Production Reality verdict: **PROVEN** for the gate fix (driven in this tree); strikes = **UNKNOWN** (no receipts exist).

## Root cause (C2/C3 "check tool missing ... not found")
`vault/programs/cognitive-economy/gen2/ledger.json` bound C2 and C3 as `["tools/test_ce_t1_state.py"]` (argv with no
interpreter). `tools/cep_gen2.py:run_check` resolved argv[0] with `shutil.which`, found nothing and reported the script as a
missing tool. The files exist in every tree (`Test-Path` True here); the hypothesis in the A2 card (resolution root /
interpreter) was falsified: it was a malformed binding, mislabelled by the diagnostic.
Run alone, both pass: `CE_T1_STATE_PASS=11/11`, `CE_T1_LIFE_PASS=12/12`.

## Fix (RED first)
- Ledger: C2, C3 prefixed with `python`; C15, C16 `python3` -> `python`. `run_check` already maps `python`/`python3` to
  `sys.executable`, so Windows and Linux both resolve; the real defect was never `python3` but the missing interpreter.
- C15, C16 were `OPEN` yet carried a check (gate rule: a bound check is `CHECKED`) -> set `CHECKED`. They now run.
- `tools/cep_gen2.py`: a script path in argv[0] now reports "misconfigured: is a script, not an interpreter; prefix 'python'"
  instead of the false "tool not found". Selftest cases added: `V-CEP2-RUN-script-without-interpreter` (red pole, asserts
  the message), `-python-script-passes` and `-python3-alias-portable` (green poles).
- `python tools/cep_gen2.py --selftest` -> `CEP2_SELFTEST=PASS` rc 0 (includes the existing open-obligation mutation kill).

## Gate after fix
`python tools/test_cognitive_economy_program.py --generation 2 --final`: 28 -> 26 failures; C2 and C3 absent from the list.
Remaining are genuine: W4-W9, R (no terminal), `spend UNKNOWN`, C1, C4-C14, C17-C20 OPEN, and now C15/C16 FAIL honestly:
- C16: `a1.spent None is UNKNOWN` (Phase 2 owns it).
- C15: `a1.families.gen3-envelopes.strikes` is now null (below).

## gen3-envelopes strikes
The card says T1 and T1b "both ended with no product". Searched this tree and the main checkout
(`~/.claude/skills/claude-power-pack/vault/programs/cognitive-economy/gen3`): the only gen3 receipt is `T3-receipt.md`;
there is no T1 or T1b receipt (gen3 has packets for T1/T1b/T1c, no receipt for either). `gen2/evidence/tranche/CE-T1b-receipt.md`
is the unrelated gen2 C2 tranche. So neither 0 nor 2 has file:line evidence. Ledger set to `strikes: null` +
`strikes_note`. This is a regression from a passing-by-assertion C15 to an honest FAIL; clearing it needs the T1/T1b mission
receipts (GEX44 or the missions' own state), an OWNER/Phase-2 follow-up, not something to guess.

## Ledger fields moved
`obligations` C2, C3 (argv), C15, C16 (status/argv); `a1.families.gen3-envelopes.strikes` 0 -> null.

## Spend
Not metered (meter lands in Phase 2): UNKNOWN. Work was ~15 tool calls, well inside the 0.5M cap by inspection only.

## UKDL candidate
T-DIAGNOSTIC-NAMES-WRONG-CAUSE: a "tool not found" message for a path that exists sent three readers (A2 card included) to
resolution-root and interpreter theories; a diagnostic must name the malformation it actually detected.
