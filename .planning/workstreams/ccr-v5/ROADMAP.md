# Roadmap: CCR v5 — Semantic Working Set + Institutional Mutation Coordination

Plan of record: `vault/plans/ccr-v5-svm-imc-2026-10-14.md` (Owner `approve p95`, packet
`ccr-v5-2026-10-14.json` sha 0b87df4e9b02, applied 2026-10-14; programme goal `ccr` 195,000,000; lease **L13**
`ccr:v5` cap 79,000,000). Laws and done-gates: the Owner brief in pane d124ce03 (2026-10-14); the plan file lists them.

Principle: context size scales with the current semantic frontier, not project age. A blocked mutation becomes a
durable dependency, never an Owner reminder. Nothing is SEALED while successor-critical continuation is dirty.

## Operating constraints (every phase)

- Work tree: `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr-v5`, branch `ccr/v5`. Commit here
  freely (pathspec-scoped, `git commit -F <msgfile> -- <paths>`, message file in `$env:TEMP`, never `.git/`).
- The main tree (`C:\Users\User\.claude\skills\claude-power-pack`, `feature/knowledge-acquisition`) is SHARED with
  live panes (1,172 dirty paths at start). Never edit, stage, revert or commit a path there that this mission did not
  write; merges into it go ONLY through the Phase 3 guarded path (`land_worktree.py` + validation + rollback).
  `vault/knowledge_base/ukdl-universal.md` there carries a foreign writer's uncommitted bytes: never touch them.
- Git: `& 'C:\Program Files\Git\cmd\git.exe' -C <repo> ...`. Python:
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`. PowerShell,
  not Bash. No `rm -rf`.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, credentials. Hook behaviour may
  change only inside code already reached by the registered `hook-dispatcher.js` chain; anything needing a new
  registration is an OWNER STEP written to the phase EVIDENCE.
- CCR releases: only `tools/ccr_release.py release` from this worktree after the phase's tests pass, never during a
  Madzia driver attempt, rollback kept. No push. No game servers. No Stage 4.
- Spend: before ending each epoch, book your own session:
  `python tools/mission_spend.py goal-settle --goal ccr --session <your session id> --measured <processed>`
  (processed = input + cache_read + cache_write + output over the whole session transcript; watermark-based, books
  only the delta). Stop-loss: a phase above 1.5x its route twice → mark BLOCKED, write why, continue to the next
  phase only if it does not depend on it.
- Self-hosting: run with `CCR_WORK_UNIT` pointing at a unit JSON for the phase class where the tooling supports it.
- Never ask the Owner mid-run: write blockers into the phase EVIDENCE.md, mark BLOCKED/UNJUDGED, continue.
- Every phase ends with EVIDENCE.md: commands, exit codes, observed output, Production Reality verdict
  (PROVEN / OBSERVED / UNJUDGED / BLOCKED — never upgraded). Apply
  `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at each phase end.
- Before building any NEW module: grep for an existing owner (the plan's ownership map is the starting point);
  extend, never parallel. UNKNOWN is never zero.

## Phases

### Phase 1: Context-rent attribution (route 3.0M) -- COMPLETE 2026-10-15 (G1 not triggered; see phases/01-*/01-EVIDENCE.md)
Decompose the LuckyArena Lobby first-call context (measured floor 206,186, `vault/programs/ccr/evidence-v4-stage3-A4.md:39`)
into constitution / memory / rules / hook injections / tool schemas / skills / history / thinking, using existing
receipts and transcripts (no re-spend to reproduce known numbers). Split project-age vs epoch-age drivers. Write a
Context Rent Ledger (per-category rows, schema in code, not prose). **Gate G1:** if >70% of the lobby floor is
host-fixed, Phase 6 shrinks to receipts only and the saving moves to Phase 8.

### Phase 2: Quick CCR residuals (route 2.0M) -- COMPLETE 2026-10-15 (see phases/02-*/02-EVIDENCE.md; residuals a-d open there)
X2 step 5 (copy `vault/programs/ccr/stage3/a3/pgo-classes.json` and `stage3/a4/pgo/*.breakeven.json` into
`~/.claude/ccr/state/pgo/`; verify DEFLATE reads them; `CPP_CCR_DEFLATE=off` hold documented). Version the GEX44
driver (`kobii@gex44:~/missions/ccr-s3-data/drive3.sh`, read via ssh `gex44`) into `vault/programs/ccr/stage3/driver/`
with a regression test proving a string-`message` line and an empty/ERR measurement trip the breaker (the v3
`over()` already fails closed: prove it, do not re-fix it). Bring the CCR RESUMPTION_FILE continuation into a durable
owner (Phase 4 defines the seal; here: commit its current content on ccr/v5).

### Phase 3: Institutional Mutation Coordination (route 8.0M)
Extend `modules/lease/store.py` from ledger mutex to resource leases (resource id, intent, expected base revision,
writer identity). Writer probe for a dirty shared path (who: live pane/session if discoverable, else UNKNOWN).
Conflict ⇒ durable `WAIT_ON_RESOURCE` row (extend `tools/mission_recovery.py` DURABLE_WAIT): blocked goal/WU,
resource, writer, expected event, resume action, validation, timeout. Wakeup from the existing PP-GsdLongRun-Sweep
pass (no model polling) on commit / lease release / writer death. Fold the scratchpad `step2.ps1` logic into
`tools/land_worktree.py` as the resume action (dirty-path check, merge, tests, rollback on ANY test failure — fixes
the a6-test no-revert bug). Abandoned writer: never touch its bytes; bounded merge WU instead. Register the real case:
merge `ccr/v4` (then `ccr/v5`) into the main tree, waiting on `vault/knowledge_base/ukdl-universal.md`.

### Phase 4: Continuation sealing (route 3.0M)
Seal gate: a WU cannot enter SEALED while successor-critical continuation is dirty unless a certified durable store
owns it (ledger / committed page). Wire into the existing closer/rehydration verification path. RESUMPTION_FILE
becomes a projection of durable state; test both refusal and admitted control.

### Phase 5: Semantic page ownership (ULTRA-PLAN, narrow; route 2.5M)
Run `/d2a-family` on {page compiler, page graph, live dependency closure, semantic GC, epoch compiler, mutation
coordinator}. Decide page identity (`type:stable-key`), version (sha256 of source span + authority), invalidators,
store location, disclosure levels L0-L3. Owner-scope decisions only if a new authority boundary appears.

### Phase 6: Semantic page compiler + closure (route 10.0M)
`ccr_pages`: typed pages compiled from RESUMPTION files, receipts, plans and vault (Goal, WU, decision, proof,
failure, file-contract, economic, continuation). Live dependency closure from the current WU. Serve through the
existing CCR `page` MCP tool (new kinds), lowest sufficient disclosure first. No fixed-token chunking.

### Phase 7: Page faults, Semantic GC, raw recall (route 4.0M)
Fault receipts (fact, page, reason, size, decision-changed); fault-storm → PGO prefetch; GC = demotion at rotation;
raw evidence stays addressable (test).

### Phase 8: Cognitive Epoch Compiler (route 5.0M)
Replace the fixed 300k TURN_CONTINUATION constant in `tools/gsd_epoch.py` with carry-rent vs rehydration+locality
(`tools/ccr_breakeven.py`, per Work Class PGO); keep the wall as breaker. Successor ContextImage = closure pages only;
fold the `ccr_continuation` capsule into the mission card (one compiler).

### Phase 9: CI suite (route 5.0M)
Elasticity (same WU vs growing unrelated history), overmaterialization, page fault, stale page, raw recall, epoch
economics (different lifetimes when economics differ), conflict, abandoned writer, sealing. Wire into
`verification_registry`-style gates of this repo.

### Phase 10: Lobby Phase 2.1 canary (route 4.0M CCR-side)
Compile the minimum ContextImage for Lobby Phase 2.1 (se_social footprint from LBY-02, terminal decision per LBY-02
fall) from `KobiiCraft Core Files/vault/kme/intake/luckyarena-lobby/RESUMPTION.md` + its roadmap; launch a fresh
epoch in a KobiiCraft worktree (never the shared Core Files tree); measure first-call and mean context vs the old
pane and a plain fresh session; record page faults. The Phase 2.1 work itself bills goal luckyarena-lobby: check its
authority first; if none, mark BLOCKED (Owner step) and measure the compile only.

### Phase 11: Knowledge, UKDL, CBR, release, close (route 3.0M)
Knowledge Vault / FIOS entries for every confirmed failure pattern; UKDL HR/PR/Trap (deduplicated, in THIS worktree,
merged via Phase 3); CBR promotions only for canary-proven items; retire fixed one-session-per-phase and manual
retry. A7 read-out if the Owner opened the canary pane (`python tools/ccr_main_shadow.py --canary
$env:USERPROFILE\.claude\ccr\state\receipts`), else A7 stays CANARY_PENDING, never certified. Final CCR release,
main-tree merge via the guarded path, final HANDOFF with the Owner brief's field list.
