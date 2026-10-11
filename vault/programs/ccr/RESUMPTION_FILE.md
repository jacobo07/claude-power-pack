# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(another writer may be active: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000 (Owner "y go p95").
Plan: `vault/plans/ccr-mods-backend-2026-10-11.md` (read "M1 results" and "S1 results"). Owner chose **option 2**:
`Edit(mods/cpp-cognitive-runtime/**)` is allowed in `.claude/settings.local.json`. Global install/enable is the Owner's.

**State (coherence anchor: HEAD contains 1a0a62da "feat(ccr S2)").**
- SEALED: plan 5fe4c1cf; M1 probe ade57445; runtime v0.1 369593ab; release tooling 1a0a62da
  (`tools/test_ccr_release.py` 13/13, `claude plugin test mods/cpp-cognitive-runtime` 8/8).
- Rings (n=1 each, per-agent provider usage from runtime receipts, answers correct both arms, 0 page faults):
  R1 no-repo Explore 49,872 -> 29,814; R2 PP repo general-purpose 144,684 -> 72,748; R3 fresh non-CPP repo
  general-purpose 164,203 -> 111,792.
- Main session: shadow only (receipts say which rule files would be unlinked). Not enforced.
- UNKNOWN: compaction without the summariser (headless exits first).
- Liveness gate exits 1 on 54 PRE-EXISTING `modules/` offenders; it does not scan `tools/` or `mods/`.

**Active decisions.** Release root `~/.claude/ccr` (`active/`, `active.prev/`, `state/OFF`, folder marketplace
`cpp-local`). Subagent tier enforces; main tier shadows until a quality canary proves main linking.

**Next 3 actions.**
1. OWNER: `python tools/ccr_release.py release`, then the two commands from `python tools/ccr_release.py install-commands`.
   New sessions load it; open sessions keep stock behaviour until restart.
2. After install: in a NEW session, confirm the status line `CCR 0.1.0 sub:enforce main:shadow` and receipts under
   `~/.claude/ccr/state/receipts/`. Rollback: `python tools/ccr_release.py off` (instant) or `rollback` / `claude plugin disable`.
3. Then: main-session linking canary (skills/agents listing via the `page` tool), interactive compaction probe,
   R4 Madzia canary under KSR's own goal, then UKDL/CBR after proof.

**Start.** Bind your session to goal `ccr`, check `python tools/ccr_release.py status`, then continue at the first undone action.
