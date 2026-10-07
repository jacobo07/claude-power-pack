# RESUMPTION -- mission ce-a2 (Amendment A2), worktree C:\Users\User\Apps\pp-ce-a2, branch ce/a2

Read first: `.planning/workstreams/ce-a2/ROADMAP.md`, `STATE.md`, `vault/programs/cognitive-economy/gen2/AMENDMENT-A2-2026-10-07.md`.
Done gate: `python tools/test_cognitive_economy_program.py --generation 2 --final` (run with Python312, PowerShell tool).

## State
- SEALED: Phase 1 (A2-0) committed `9063b292`. Root cause: ledger bound C2/C3 as bare script paths (no `python`), and
  `run_check` reported them "not found". Fixed + selftest cases; C15/C16 now CHECKED and honestly red;
  `a1.families.gen3-envelopes.strikes` = null (no T1/T1b receipt exists). Evidence: `phases/01/EVIDENCE.md`.
- UNCOMMITTED, tested, working tree (Phase 2 / A2-1), commit these first with pathspecs:
  - `vault/programs/cognitive-economy/measure/attribute.py` (new) and `measure/turns.py` (`--attribute` delegates)
  - `tools/cep_gen2.py` (receipt rule: self-reported `boundary_calls` < `metered_calls` fails; 3 mutants + 2 positive poles)
  - `tools/test_ce_attribute.py` (new): `CE_ATTRIBUTE_PASS=15/15`; `cep_gen2.py --selftest` PASS
  - mutation drills (tools/mutation_drill.py): dedup-off KILLED by V-ATTR-DEDUP-MESSAGE-ID; receipt-compare-off KILLED by V-ATTR-RECEIPT-3-VS-16-FAILS
  - `vault/programs/cognitive-economy/gen2/evidence/a2/attribution-a2-phase2.json` (real meter run, since 2026-10-07T00Z)
- NOT YET DONE for Phase 2: (1) ledger `a2.spent` still null -> set 17207227 with spent_note "lower-bound snapshot: worker pane
  489481fa 9,827,709 + coordinator 886d7bb9 7,379,518; 302 text-only calls UNKNOWN; worker still running, final higher";
  `a1.spent` stays null, UNKNOWN named: A1 sources are pp-ce-gen2 / GEX44 transcripts, not metered here (G6).
  (2) `phases/02/EVIDENCE.md`, tick Phase 2 in ROADMAP, STATE.md (current_phase 3, completed 2, percent 25), micro-commit.
- SPEND ALERT: worker pane read 10,041,901 processed (session breaker tripped, stop 10M). With the coordinator A2 is at
  ~17.2M of the 20M cap including coordinator; Phases 3-8 (4M+6M+3M+... caps) do NOT fit. Next epoch must re-admit first:
  `python C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py admit --mission m-72fba680c953 --route vault/programs/cognitive-economy/gen2/evidence/a2/route-epoch.json`
  RECOMPILE means stop and report to the Owner; do not raise the cap yourself.

## Decisions active
Write only this tree; never edit ~/.claude (HR-001); metered beats self-reported; null is never zero; no Agent.

## Next 3 actions
1. Commit the uncommitted Phase 2 files (git.exe absolute path, `-F msgfile`, verify `%s`).
2. Finish items (1)-(2) above, then re-admit.
3. If admitted, Phase 3 (A2-2 presence, cap 4M); else write the verdict into phases/02/EVIDENCE.md and stop.
