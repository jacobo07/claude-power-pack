# Roadmap: global-prefix-floor (v1)

Authority: `vault/plans/global-prefix-floor-2026-11-02.md` (Owner `y go`, 2026-11-02, laptop). Read it first. Do NOT re-scan
what its Reality Scan states. It EXTENDS ctx-rent-x (`vault/programs/ctx-rent-x/`, done_gate.py, l5/l6 drivers, floor_diet,
floor_regression_gate). Never create a parallel system.
PLANE: **laptop** DESKTOP-PMT5BS8, live install `~/.claude/skills/claude-power-pack`, branch `feature/knowledge-acquisition`.
The tree is shared, with 1,200+ dirty paths from other panes. Commit ONLY your own paths (`git commit -- <paths>`), one causal
delta per commit, and verify `git log -1 --format=%s` after each commit. Do NOT push. Use PowerShell (Bash is guarded).
**RAM:** free RAM was 2.2 GB at arm, under the 3000 MB floor. Run probe panes one at a time, in the foreground. Before each probe
batch, check free MB. If it is under 2500, wait (an event, not a sleep loop) or stop and write the Owner note. A probe killed by the
reaper is INCOMPLETE, never data.
EXECUTION mode. Plan each phase inline. Do NOT dispatch gsd-planner / gsd-phase-researcher subagents. At most 2 bounded subagents.
Measure your own spend after each phase (`python tools/mission_spend.py session-tree --session <sid>`) and record it in STATE.md.
Stage-1 authority is 8M. If phases 1-2 have not produced a measured call-1 delta by 8M: METHOD_PIVOT, then stop with an Owner note.
UNKNOWN/UNMEASURED are never PASS. CACHE_HIT is not CONTEXT_ELIMINATED. A shorter file is not a saving until call-1 drops.
Before editing anything under `~/.claude/` (HR-001): back it up to `~/.claude/backups/gpf-<ts>/` and record the revert command.

## Phases

- [ ] **Phase 1: W0 floor decomposition.** Extend l5_canary_driver.py (do not fork it) with single-variable arms on the live
  canary release: full | -CLAUDE.md chain | -rules | -memory | -SessionStart injections | -MCP. N=3/arm, interleaved. Always
  restore and verify the tree hash. Residual = provider floor (Claude Code system + built-in tools). Output:
  `vault/programs/ctx-rent-x/floor-decomposition.json` with MEASURED/ESTIMATE labels. Ceiling 5M.
- [ ] **Phase 2: W1 resident doctrine compile-out.** Classify every block of ~/.claude/CLAUDE.md, ~/CLAUDE.md, the PP CLAUDE.md
  and ~/.claude/rules (IRREDUCIBLE_JUDGMENT / SAFETY_CRITICAL / RUNTIME_ENFORCEABLE / QUERYABLE / CAPABILITY_SPECIFIC /
  DUPLICATE / SUPERSEDED). Move capability prose into the existing skills. Replace the inline HR mirror with the digest router.
  Measure with the floor_diet contract (N=4/arm, spread<1%) plus the l6 quality arm (6/6). Keep only what passes. Ceiling 12M.
- [ ] **Phase 3: W2 close the ctx-rent-x laptop UNKNOWNs.** Phase-4 successor smoke + fresh-start cost (CR-11,14,15,16,29),
  Phase-5 Safe-to-Forget (CR-09,10,13), per ctx-rent-x LAPTOP_STEPS.md. Ceiling 15M.
- [ ] **Phase 4: W3 Resident Context Admission.** Per-surface budgets (CLAUDE.md chain, rules, memory) in floor_regression_gate,
  with a mutation drill that goes red. Add a baseline_ledger row that splits availability from residency. Ceiling 4M.
- [ ] **Phase 5: Closeout.** done_gate.py CR-33..36 (decomposition, W1 delta, quality, pinned budget). UKDL entries only where
  evidence-backed. HANDOFF.md with the plan's closeout answers. Ceiling 3M.
