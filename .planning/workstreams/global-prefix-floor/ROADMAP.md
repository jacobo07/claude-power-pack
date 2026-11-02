# Roadmap: global-prefix-floor (v1)

Authority: `vault/plans/global-prefix-floor-2026-11-02.md` (Owner `y go`, 2026-11-02, laptop). Read it first. Do NOT re-scan
what its Reality Scan states. It EXTENDS ctx-rent-x (`vault/programs/ctx-rent-x/`, done_gate.py, l5/l6 drivers, floor_diet,
floor_regression_gate). Never create a parallel system.
PLANE: **GEX44** (Owner "do it on GEX44", 2026-11-02; the laptop arm was refused at 1,496 MB free vs the 3000 MB floor). You run in
the clone `~/missions/global-prefix-floor`, branch `mission/global-prefix-floor`. Commit with the repo-local identity, one causal
delta per commit. Do NOT push. Use Bash (Linux). The laptop coordinator fetches your branch.
**Never touch GEX44's live `~/.claude` or `~/.claude/skills/claude-power-pack`** (agora-mission-sweep runs that tree for other
missions). Measure in an ISOLATED config: copy `~/.claude` to `~/missions/gpf-cfg/<arm>` (CLAUDE.md, rules, memory, settings,
plugins incl. the CCR release or `--plugin-dir mods/cpp-cognitive-runtime`), launch with `CLAUDE_CONFIG_DIR=<that dir>` and
`/home/kobii/.local/bin/claude` (2.1.316, `stdin </dev/null`). Before trusting any arm, prove the isolation took effect
(the arm's call-1 differs, or its start receipt names that dir). Interactive panes: drive them with a pty (python `pty`/`pexpect`),
porting the ConPTY l5 driver as an extension, not a fork. Label every number `plane=GEX44`.
- **Laptop-only items** (the laptop's live CLAUDE.md/rules/memory, laptop CCR release, laptop interactive panes, and the ctx-rent-x
  CR items its HANDOFF names as laptop-plane) are written as numbered, copy-pasteable entries in
  `vault/programs/ctx-rent-x/LAPTOP_STEPS.md`, and the phase is marked BLOCKED-ON-LAPTOP. Continue with any phase that does not
  depend on them. The PP repo `CLAUDE.md` is in-repo: its edit is a commit, and you measure it here. Edits to `~/.claude/CLAUDE.md`
  and `~/.claude/rules` are measured on GEX44 copies, then shipped as a LAPTOP STEP with the exact diff and its revert.
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

## Phase Details

### Phase 1: W0 floor decomposition
**Depends on**: nothing. P50 4M, ceiling 5M. Requirement GPF-01. Scope as in the Phases list above.

### Phase 2: W1 resident doctrine compile-out
**Depends on**: Phase 1. P50 9M, ceiling 12M. Requirement GPF-02. Needs stage-2 authority unless the Phase-1 spend leaves room.

### Phase 3: W2 close ctx-rent-x laptop UNKNOWNs
**Depends on**: nothing (runs after Phase 2 by order). P50 11M, ceiling 15M. Requirement GPF-03.

### Phase 4: W3 Resident Context Admission
**Depends on**: Phase 2. P50 3M, ceiling 4M. Requirement GPF-04.

### Phase 5: Closeout
**Depends on**: Phases 1-4. P50 2M, ceiling 3M. Requirement GPF-05.
