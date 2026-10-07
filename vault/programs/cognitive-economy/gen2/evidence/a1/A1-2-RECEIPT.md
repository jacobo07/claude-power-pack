# A1-2 receipt -- program meter `turns.py --attribute` (gaps G3, G4, G5)

Branch a1/a1-2 (worktree C:/Users/User/Apps/pp-a1), cut from a1/u1 82a493aa. Built in pane b9bd9469 on the
laptop (account jacobofifa07@gmail.com). Zero model calls inside the meter.

## What landed
- `measure/turns.py`: `scan_file(..., probe=None)` (unset = old behaviour; `gate_turns.py` labels sha unchanged,
  GATE_TURNS=PASS 3000 rows) and the `--attribute` mode: `attribute`, `attribution_controls`, `program_probe`,
  `SHELL_WRITE`, `ledger_session_prefixes`, `PROGRAM_PATHS` / `PROGRAM_ROOTS`.
- `tools/test_ce_a1_attribute.py`: hermetic (temp sqlite + temp transcripts), CE_A1_ATTR_PASS=18/18, three mutants
  killed (lineage-off, exclusion-off, shell-any-write).
- `gen2/ledger.json`: `budget_tokens.coordination_spend` filled from the canary; `a1.spent` + sources + upper bound.

## Rules (G3-G5)
Population = usage-index rows (key `message.id|requestId`, so a streamed message is one call); subagent rows carry
the parent session and roll up. Tier A = calls between a session's first and last WRITE signal (edit of a program
path; shell command naming one that tests, commits, writes or executes). Tier B = other calls between the first and
last signal of any kind (Read of a program path, read-only shell naming one, cwd in a program worktree). Sessions
already in `spent_measured.sources` go to excluded_*. Featureless calls and tool-less sessions are UNKNOWN. A and B
are never summed into one measured value.

## Findings made by the canary (each fixed and pinned before the reading was kept)
1. A read-only `Get-ChildItem` of the program dir from a KobiiCraft pane (bf8eb18a) was booked as a WRITE (tier A).
   Fix: SHELL_WRITE; pinned by V-A1-ATTR-shell-read-is-lineage + MUT-shell-any-write. bf8eb18a now: B 0.6M.
2. bf8eb18a was a wrong negative control: it really read program cards. Negative controls are now picked by an
   independent instrument (substring search of tool_use inputs + cwd, not the meter's regex): sessions with zero
   program mentions must meter 0. Raw full-text search was unusable in the A1 window: SessionStart hooks inject
   program text into every session (0/33 clean).
3. `ledger_session_prefixes` read integer `processed` values (12819555, 17400000...) as session ids. String fields
   only now; pinned in V-A1-ATTR-ledger-prefixes.
4. Plan deviation: the planned "dedup mutant" was replaced. Dedup is structural (index primary key); a mutant that
   double counts cannot be built over it. The streamed-twice fixture pins the property instead.

## Canary: 2026-10-04T18:00Z..2026-10-07T10:33Z (A1-2-canary.json)
15,587 calls, population_ok (bucket sum == window sum 4,022,461,746). Controls ok: pos 87601e81, 71ccfa86
detected; neg d5944dbc, 0f413d45, 5f5bc46f, f9a3447d = 0.
A 258,994,397 | B 119,920,566 | excluded A+B 124,609,059 | outside_span 555,407,655 | not_program 2,962,544,524 |
unknown_no_tools 985,545 | featureless 0.
Versus the amendment's ad-hoc 520M / 368M: the 41 program sessions total 1,058,931,677 as whole sessions; the
write-span rule leaves 555M outside any span. The ad-hoc scan counted whole sessions -- the G5 overcount.

## A1 spend (A1-2-a1-window.json), from the approval turn 2026-10-07T11:12:10Z to 12:22:33Z
Approval turn = 423e33b0's "y" at 11:12:10Z (first commit of the amendment, 6a3eb98c at 11:15:34Z, already says
APPROVED). Controls ok: pos 423e33b0, b9bd9469; neg a45dad7c, f552a163, c14908c3 = 0 (action-clean).
423e33b0 A+B 24,715,309 + b9bd9469 A+B 16,494,861 + U1 (GEX44) 1,097,211 = **42,307,381** (upper bound with
outside-span calls 44,792,057). **A1 cap 20,000,000 is exceeded 2.1x.** C16 on the real ledger: exit 1,
"a1.spent 42,307,381 exceeds cap 20,000,000" -- red for the right reason now, not UNKNOWN.

## Done gate (pp-a1, all exit 0)
CE_A1_PASS=12/12 | CE_A1_ATTR_PASS=18/18 | OBL_TEST=PASS | CEP2_CLI_TEST=PASS | CEP2_TRANCHE_TEST_PASS=9/9 |
CEP2_SELFTEST=PASS | GATE_TURNS=PASS. Real ledger: C15=PASS (vacuous, see U1 receipt), C16=FAIL (over cap).

## UNKNOWN / open
- G6: GEX44 has no meter beyond U1's own transcript; the GEX44 share of coordination_spend is UNKNOWN.
- b9bd9469 keeps spending after 12:22:33Z; a1.spent is a reading at that instant.
- The other program sessions since approval (gen2 T1d/T1e panes, cwops, recon) total 34,214,226 A+B (window A+B
  75,424,396 minus the two A1 panes' 41,210,170); program work, not A1, not in a1.spent.
- Owner decision needed: A1 over cap means the moratorium's own coordination already costs more than its envelope.
