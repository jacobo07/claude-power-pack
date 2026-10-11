# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(another writer may be active: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000 (Owner "y go p95", 2026-10-11;
38M total minus ctx-rent-a2's 1.12M remainder). Plan: `vault/plans/ccr-mods-backend-2026-10-11.md` (read "M1 results"
and section A only). Thesis: the context rent lives in engine attachments (`instructions`, `skill_listing`,
`agent_listing_delta`, hook context), and a user-tier mod can link them per boundary through `prompt.attachment`.

**State (coherence anchor: HEAD contains ade57445 "feat(ccr M1)").**
- SEALED: plan 5fe4c1cf; M1 probe mod `mods/ccr-probe` + results ade57445. Subagent linking measured 47,591 -> 15,571
  provider input (-67 %); tool deferral -6.8 %; main floor 68,025 outside a repo; no managed policy on this machine.
- PENDING, uncommitted: `mods/cpp-cognitive-runtime/hooks/policy.ts` (pure policy: instruction-file linker, subagent
  attachment decisions, advisory-bytes meter, repo key, page lines).
- BLOCKED: writing `mods/cpp-cognitive-runtime/hooks/register.ts` (the hook wiring: subagent linker enforce, main
  shadow receipts, `page` fault tool, version gate, OFF kill switch) was DENIED by the auto-mode classifier as
  [Self-Modification]. Do not work around it. It needs an Owner decision (see Next).

**Active decisions.** State dir = `<home>/.claude/ccr/state` for a release, `<mod>/.state-dev` for `--plugin-dir`.
Kernel for subagents = `kernel/HARD-RULES-DIGEST.md`, copied from the compiled digest at release build. Release
layout `~/.claude/ccr/releases/<v>` behind a folder marketplace, so activation and rollback switch a folder.
Compaction without the summariser is still UNKNOWN (headless exits first); it is tested in interactive R1.

**Next 3 actions.**
1. With the Owner's permission decision in place: write register.ts (wiring above), plugin.json, hooks.json,
   `.gitignore` (.state-dev), copy the digest to `kernel/`, then `claude plugin validate` and a `*.test.ts` for policy.ts.
2. R1: `scratchpad\probe.ps1`-style headless runs with `--plugin-dir mods\cpp-cognitive-runtime`. Subagent enforce +
   main shadow. Read receipts; compare provider usage against the M1 baseline.
3. Release tooling (`tools/ccr_release.py`: build, activate, rollback), then R2-R5 per the plan's rings.

**Start.** Bind your session to goal `ccr` (`~/.claude/state/goal-binding/<sid>.json`), confirm the Owner's
permission decision, then do action 1.
