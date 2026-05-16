# Session Lessons — Atomic Learning

Append-only log of concrete, non-derivable learnings per session.
One entry per `/kclear` with a `lesson` field. Keep each entry short and
self-contained — if a future reader can't grok it without the conversation,
rewrite it.

---

## 2026-05-10 — BL-0073 ONESHOT cycle on Multi-Terminal Resurrection Engine

**Session:** `e15093ca-c3b2-416f-a652-dff27eb39819` (same UUID as BL-0072; survived 2 prior `.jsonl.conflict.*` events from BL-0013 hide-live)

Five non-derivable findings (auditor surfaced 11 gaps; verdict-defining ones below):

1. **Empty registry was symptom, not bug.** `~/.claude/lazarus/terminal_registry.json` had `entries: []` despite `terminal-slot-recorder.js` having complete write logic. Root cause: registry write is gated on `process.env.LAZARUS_TERMINAL_KEY` (line 125), which is only set when Cursor profiles inject it. **No profiles were ever installed.** Implication: the BL-0072 architecture was correct; the harness step (Cursor user-settings patch) was missing. **Rule:** before "fixing" code that "should populate", check the env-var path that gates it.

2. **`atomic_write.js` already had EPERM retry; the recorder was bypassing it.** Lines 209-212 of recorder did raw `fs.writeFileSync` + `fs.renameSync` for the registry while the SLOTS_PATH path used `aw.atomicWriteJson`. The 7 stale `.tmp.<pid>.<hex>` orphans came from atomic_write itself (process killed before unlink-on-failure ran). **Fix:** swap to `aw.atomicWriteJson` + add a pre-write tmp-reaper for >60s siblings. **Rule:** when you see tmp orphans matching a `.tmp.<pid>.<hex>` pattern, the writer has crash-cleanup logic but no startup-cleanup. Always pair them.

3. **Settings.json hide-live deletion required removing TWO entries, not one.** `~/.claude/settings.json:288` (Stop) AND `:365` (SessionStart) both registered `resume-hide-live.js`. Deleting the script alone leaves orphan refs that error on every SessionStart. `lazarus-janitor.js` also matched on `.jsonl.live` but for benign mtime fallback — left in place, no breakage. **Rule:** always grep-count refs to a hook BEFORE deleting it.

4. **`.jsonl.live` orphans were 41, not 13.** Auditor estimated 13 from a partial scan; full walk showed 41 across all `~/.claude/projects/*/`. The BL-0013 hide-live hook ran for months across many projects, accumulating debris on every Alt+F4. **Rule:** when planning a purger, scope the count via Glob/find FIRST. Conservative ARCHIVE-when-both-files-exist semantics shipped because we cannot tell which is fresher without reading both — let Owner pick.

5. **CWD-norm drift fix was a one-line PS edit, not a JS+PS twin module.** Original plan called for `lib/Get-LazarusProjectId.ps1` + `lib/project_id.js` twins. Reality: `claude_smart_resume.ps1` already computed `$cwdNorm` (line 82-83) but passed raw `$cwd` to `Get-CSRRegistryEntry`. **Rule:** before designing parallel helpers, check whether the data is already computed and just plumbed wrong.

**Empirical evidence (Phase 7 verification):**
- `lost_chat_recovery.py e15093ca-...` returned `PRIOR_CONFLICTS` (exit 12) — 2 .jsonl.conflict.* siblings flagged correctly; no auto-resume risk.
- `lazarus_orphan_purge.py` dry-run: 41 .jsonl.live found, 39 ARCHIVE, 2 SKIP_LIVE (e15093ca correctly skipped as live writer at 40s heartbeat).
- `lazarus_post_reboot_arm.py --dry-run`: would clean 75/81 stale heartbeats + 48 tmp orphans + 0 ghost registry entries (registry currently empty pre-Cursor-profile-install).
- `~/.claude/settings.json` post-edit: `node -e "JSON.parse(...)"` valid; hide-live refs = 0.

**WSLENV caveat (audit gap #6):** Cursor's `terminal.integrated.profiles.windows[*].env.LAZARUS_TERMINAL_KEY` is honored by pwsh child but does NOT cross WSL boundary. Add `LAZARUS_TERMINAL_KEY/u` to `WSLENV` if running wsl inside a slot pane. Documented but not auto-installed.

**$PROFILE caveat (audit gap #7):** patch `$PROFILE.CurrentUserAllHosts` (covers pwsh + Windows PowerShell 5.1), NOT bare `$PROFILE` (= CurrentUserCurrentHost only — misses one shell). Sentinel keyed on `Win32_OperatingSystem.LastBootUpTime` so arming happens once-per-logon, not once-per-shell.

**Files shipped (BL-0073):**
- `modules/zero-crash/hooks/terminal-slot-recorder.js` (registry path now uses atomic_write + slot-id validation + tmp reaper)
- `tools/claude_smart_resume.ps1` (cwd-norm fix + ghost-UUID fall-through + slotN added to Tier-1)
- `tools/lost_chat_recovery.py` (refuse-if-live probe; 5min freshness window)
- `tools/install_lazarus_v3_profiles.ps1` (4 Cursor terminal profiles, regex-safe JSON5 patcher)
- `tools/lazarus_orphan_purge.py` (.jsonl.live decision matrix, dry-run by default)
- `tools/lazarus_post_reboot_arm.py` (registry sanitizer + bootid sentinel)
- `tools/install_csr_profile_hook.ps1` ($PROFILE wiring with marker-block idempotency)
- `~/.claude/settings.json` (Stop + SessionStart hide-live entries removed)
- `~/.claude/hooks/resume-hide-live.js.removed.BL-0073-<ISO>` (soft-deleted, not hard-rmed)

**Phase 7 deferred (next-session):** Owner runs `install_lazarus_v3_profiles.ps1` + `install_csr_profile_hook.ps1` + reload Cursor + open 4 panes from slot1-4 profiles → confirm `terminal_registry.json | jq '.entries | length' == 4` with 4 distinct slot_ids. Then `lazarus_orphan_purge.py --apply` once this session ends gracefully (e15093ca's .live can rejoin .jsonl namespace).

---

## 2026-05-08 — BL-0072 ONESHOT cycle on Lazarus v2 Multi-Slot Terminal Persistence Engine

**Session:** `e15093ca-c3b2-416f-a652-dff27eb39819`

Three non-derivable findings from this /ultra cycle (9 audit gaps from `oneshot-architect-auditor`, all addressed):

1. **Auditor surfaced two pre-existing artifacts the original plan was about to duplicate:** `terminal-slot-recorder.js` (BL-0044, cwd-keyed `vault/terminal_slots.json` SessionStart writer) AND `tools/claude_smart_resume.ps1` (cwd-only resolver with `csr` alias). Plan was correctly amended to EXTEND both — recorder gained dual-target writes (cwd + new slot_id-keyed registry when LAZARUS_TERMINAL_KEY set) and smart_resume gained 4-tier dispatch with format-detector. **Rule:** when proposing new files, grep the codebase for similar names/responsibilities BEFORE Phase 3; BL-0067 sub-agent dispatch is the formal mechanism but a manual `Glob '*recorder*'` + `*resume*` 30s pre-check would have caught these.

2. **VSCode TerminalAPI does NOT support reliable per-terminal env injection without `registerTerminalProfileProvider`.** Original plan called for BL-0070 ext to dispose+recreate terminals on `onDidOpenTerminal` to inject unique LAZARUS_TERMINAL_KEY UUID v4. Auditor flagged this as unsafe (gap #3): `creationOptions` is read-only and may not capture profile resolution; dispose loses user shell state; `EnvironmentVariableCollection.replace()` sets the SAME value for ALL future terminals (not per-terminal-unique). The clean architectural path is `TerminalProfileProvider`, which is significant scope. Cycle was honestly downscoped: slot scaling stays at slot1-N hardcoded Cursor profiles + cwd-fallback, with infinite-scaling deferred to a future BL.

3. **PS5.1 inline `(if A { B } else { C })` in `Write-Host -ForegroundColor` argument and `exit $(...)` consistently fails with "El término 'if' no se reconoce".** Same bug pattern as BL-0066 ghost-input v2 harness. **Rule:** never use parenthesized inline if-expression as an argument to a cmdlet parameter; ALWAYS assign to a variable first (`$col = if (X) { 'A' } else { 'B' }; Write-Host msg -ForegroundColor $col`). Add to feedback memory once seen 3+ times — already 2 occurrences this session pair.

Empirical artifacts (Phase 7 simulator):
- `vault/audits/lazarus_v2_sim_1778263173.json` — `coverage=1, pass=4, total=4`
- `vault/audits/lazarus_v2_e2e_protocol.md` — full architecture + reboot protocol

Real-reboot test (Phase 7-B) gated on Owner — orchestrator BL-0065 reusable, prerequisite is FIFO clean (BL-0065 finding #1 still applies: pre-validator refuses if FIFOs reference dead .jsonls).

---

## 2026-05-04 — BL-0065/0066/0067 ONESHOT cycle on Lazarus E2E + Vault Rollout + Ghost-Input v2

**Session:** `e15093ca-c3b2-416f-a652-dff27eb39819`

Three non-derivable findings from the first real `/ultra plan` cycle:

1. **BL-0065 — Pre-validator must surface state honestly even when invariant fails.** `lazarus_e2e_pre_validator.py` enumerated 3 active panes correctly via `~/.claude/lazarus/<proj>/heartbeats/` (avoiding the `state.vscdb` dual-path complexity per gap #1). Invariant `all_fifo_sids_have_jsonl` returned `false` because the FIFO contained UUIDs of sessions that no longer exist in `~/.claude/projects/` — the lazarus-janitor (BL-0062) sorts FIFOs by mtime but does NOT prune dead UUIDs. Pre-validator surfaces this honestly; orchestrator refuses to fire reboot when `invariants.all_pass=false`. Failing-fast > fake green. Future work: add janitor pass to drop FIFO entries whose `<sid>.jsonl[.live]` is missing.

2. **BL-0066 — PowerShell 5.1 uint64 arithmetic is fundamentally broken; use SHA-256 instead of FNV-1a.** Three failed attempts to implement FNV-1a 64-bit hash in PS5.1: (a) decimal literal `14695981039346656037` parses as `double` (>int64.max), `[uint64]` cast throws InvalidCast; (b) hex literal `0xCBF29CE484222325` ALSO parses as double (same overflow); (c) `[uint64]::Parse('CBF29CE484222325', [hex])` parses correctly but `$hash * $prime` for two large uint64 promotes to double on overflow (PS5.1 op_Multiply doesn't wrap-mask). The pivot to SHA-256 truncated to 16 hex chars (`[System.Security.Cryptography.SHA256]::ComputeHash`) closed all three problems in 8 lines. **Rule:** for any cryptographic-or-hash work in PS5.1, use `System.Security.Cryptography.*` not hand-rolled arithmetic.

3. **BL-0067 — Agent files in `~/.claude/agents/<name>.md` cold-load like hooks (require `/restart`).** Created `oneshot-architect-auditor.md` in the previous turn (BL-0063), tried to dispatch via Agent tool same session: harness rejected with `"Agent type 'oneshot-architect-auditor' not found"`. The agent definitions are read at session-start and cached. Slash commands (`~/.claude/commands/<name>.md`) hot-discover (verified turn previous: `/ultra` appeared in next system-reminder), but agents do not. Distinction: **commands hot-discover, hooks cold-load, agents cold-load, permission rules hot-reload (BL-0049 #2)**. Pivot pattern: when sub-agent not yet loaded, run the equivalent checklist inline with full integrity, document the gap, expect next-restart to use the proper agent.

Empirical artifacts (Phase 7 evidence):
- `vault/audits/lazarus_e2e_pre_smoke.json` — 3 panes, 2/3 invariants pass
- `vault/audits/vault_rollout_<ts>.json` — 167 candidates, 3 eligible, 164 already-covered
- `vault/audits/ghost_input_v2_results.md` — Empirical run section, 3/3 PASS

---

## 2026-05-04 — BL-0063/0064 ULTRA-PLAN CLI capacitation (ONESHOT 7-phase + architect-auditor sub-agent)

**Session:** `e15093ca-c3b2-416f-a652-dff27eb39819`

Two non-derivable findings:

1. **`/ultra` is a filesystem-discovered slash command, NOT a settings.json registration** — the original prompt asked to "edit settings.json to define /ultra plan behavior", but slash commands in Claude Code live as markdown files in `~/.claude/commands/<name>.md` (or `<repo>/.claude/commands/`). settings.json has no key for command registration. The fix to "Unknown command: /ultra" (3x rejection) is creating `~/.claude/commands/ultra.md`. Verified: command appeared in next system-reminder skills list immediately after Write (no /restart). **BL-0064 sealed**: filesystem > settings.json for command discovery.

2. **Slash commands with spaces parse as `/<cmd> <args>`, not as multi-word command names** — `/ultra plan` is `/ultra` with `plan` as first arg. The command file's body interprets `$ARGUMENTS`. Multi-word command names (`/ultra-plan`) work but require hyphen, not space. ONESHOT protocol implementation in `ultra.md` parses `$ARGUMENTS` first token to switch modes. **BL-0063 sealed**: ULTRA-PLAN protocol locked into 7 phases (Q&A is gate 2, mandatory stop), with `oneshot-architect-auditor` sub-agent (`~/.claude/agents/`) called at phase 4 for read-only gap audit.

---

## 2026-05-03 — BL-0046/47/48 empirical seal + BL-0049 self-mod-guard finding

**Session:** `omni-max-empirical-2026-05-03`

Five non-derivable findings:

1. **Self-modification guard ≠ bypassPermissions** — even with `defaultMode: bypassPermissions` in `~/.claude/settings.json`, edits to `~/.claude/CLAUDE.md` AND `~/.claude/skills/claude-power-pack/parts/core.md` AND `vault/knowledge_base/session_lessons.md` were denied with reason "Self-Modification". Harness explicitly treats `(y/n)` confirmation prompts as "awaiting confirmation, not explicit authorization". To unlock: add a Bash permission rule like `"Edit(file:~/.claude/CLAUDE.md)"` to `permissions.allow` in `~/.claude/settings.json`. **Update `feedback_bypasspermissions_defeats_deny.md`.**

2. **Permission rules HOT-RELOAD mid-session** — unlike hooks (which load once per session per `feedback_settings_session_load.md`, requires `/restart`), `permissions.allow` entries in settings.json are picked up immediately. Verified empirically 2026-05-03: Owner added `"Edit(file:~/.claude/CLAUDE.md)"` mid-session, the next `Edit` call to that path passed without restart. **NEW finding** — distinguish hot-reload (permissions) from cold-load (hooks).

3. **`zero-fiction-gate.js` SOFT_PATTERNS only match line-leading comments** — regex `(^|\\n)\\s*(\\/\\/|#|\\/\\*|\\*)\\s*(TODO|FIXME|HACK|XXX)\\b` (`zero-fiction-gate.js:54`). Inline `function foo() { /* TODO */ }` does NOT trigger soft advisory. Anti-false-positive design. Test fixtures must use line-leading comments.

4. **`context-watchdog.py` cross-project snapshot is empirically green** — BL-0046 probe confirms tier-1 (65%) lands in `<cwd>/vault/progress.md` when `vault/` exists, falls through to `<cwd>/.claude/progress.md` when bare project. Tier-2 (72%) emits `additionalContext` with literal `CONTEXT THRESHOLD CROSSED`. Verified across 2 scratch projects with SHA-256 mutation evidence (`vault/audits/probe_global_watchdog.json`).

5. **Primary-cerebrum coverage gap: 0/5 decoded projects have per-project vault** — BL-0047 probe shows globals all present (`~/.claude/CLAUDE.md`, `~/.claude/vault/INDEX.md`, `~/.claude/knowledge_vault/INDEX.md`, GAL ledger) but only 1/5 projects has `_knowledge_graph/INDEX.md` and 0/5 have per-project `vault/INDEX.md` or `progress.md`. The "primary brain" is global-only — per-project enrichment requires `/cpp-vault-setup` or `/cpp-obsidian-setup` runs (`vault/audits/probe_vault_load.json`).

---

## 2026-04-22 — Shipped 5 MC-OVO cycles on claude-power-pack: sleepless_qa atomic landing (34 fi

**Session:** `kpp-supremacy-v7000-marathon`

Before promoting any inline-one-liner failure to an audit recommendation, run the canonical tool (--help / official CLI). Mistake #52: my ad-hoc script's bug got misattributed to the audited file.

---

## 2026-05-14 — Stop-hook PATH: bare `python` resolves to Store stub on Win11

**Session:** `kobiidistilleros-genesis-v82000`

Stop-chain hooks were emitting "command not found" because `hook-utils.js#getPythonCommand` returned bare `python` on win32. Windows 11's PATH includes a Microsoft Store stub `python.exe` that exits non-zero (it opens the Store), not the real interpreter under `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe`. Inline copies of the same pattern existed in `kobiiclaw-autoresearch.js`, `baseline-translator.js`, `dna-flywheel.js`, `session-init.js`.

Fix: `getPythonCommand()` now probes in priority — `$CLAUDE_PYTHON` → `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe` → `py -3` → bare `python`. Memoized after first resolution. Added matching `getNodeCommand()` returning `process.execPath` to neutralize the same risk for bare-`node` shell-outs. `kobiiclaw-autoresearch.js` (the Stop-chain offender) migrated to call the helper.

**Vaccine:** never write `const x = process.platform === 'win32' ? 'python' : 'python3'` inline; always import the helper. Reviewers reject bare-interpreter execSync templates outright.

---

## 2026-05-14 — Stop-hook schema: no `hookSpecificOutput`, top-level fields only

**Session:** `kobiidistilleros-22-section-singularity-v210000`

Earlier RAM Shield + voice-gate cycles emitted `hookSpecificOutput: {hookEventName: "Stop", additionalContext: "..."}` on Stop events. The harness rejects every such payload with "Hook JSON output validation failed", drops the advisory, and floods the validation log. The schema constraint is: Stop hooks accept ONLY `{continue, suppressOutput, stopReason, decision, reason, systemMessage}` at top level. `hookSpecificOutput` is valid for PreToolUse / UserPromptSubmit / PostToolUse / PostToolBatch — NOT Stop. The canonical re-engagement pattern when a Stop hook needs the model to keep working is `decision: "block" + reason` (see `modules/zero-crash/hooks/context-watchdog.py:209-216`). `systemMessage` is the correct field for UI-visible advisories on Stop (see `modules/zero-crash/hooks/ram-watchdog.js:135-142` and the post-patch `ram-shield.js:213-223`).

**Audit pass:** Glob'd `~/.claude/hooks/*.{js,py}` + `~/.claude/skills/**/hooks/*.{js,py}` and enumerated the 10-entry Stop chain in `settings.json:206-303` by name. Every Stop hook either never used `hookSpecificOutput` or already cited the schema constraint in a header comment. Zero patches needed beyond ram-shield.js (Owner-patched today). Earlier memory entry `BL-0040` incorrectly generalized "additionalContext IS supported on Stop" — that claim was true for PreToolUse, not Stop. Correction landed in this entry.

**Vaccine:** When emitting JSON from a Stop hook, treat any field outside the top-level six as schema-poison. Cite `context-watchdog.py:207-209` in the hook header so future contributors don't re-introduce the bug. `BL-0040` superseded.

---

## 2026-05-14 — Voice gate enforcement: global scope, exit 5, anchor-OR-blacklist

**Session:** `kobiidistilleros-22-section-singularity-v210000`

KobiiDistillerOS v1.2 ships `voice_gate.mode: "enforcing"` in `schema.json`. Validator implementation (`validate.py#_check_voice_gate`) aggregates every materialized section body, strips code fences (so contract docs enumerating the blacklist by name don't trip the gate), and counts hits across two lists:

- `blacklist_candidates` — corporate vocabulary (KPI, synergy, leverage, stakeholder, roadmap, paradigm shift, holistic, …).
- `anchors_candidates` — nostalgic / Refugio-voice tokens (Refugio, MCPE, 2014, cabaña, linterna, Helsinki, KobiiCraft, Andorra, …).

Exit 5 fires **iff** ≥1 blacklist hit AND 0 anchor hits across the **entire** output (global scope per `voice_gate.scope: "global"`). The OR semantic was chosen over AND because:

- A document with anchors + blacklist may be a deliberate translation of corporate-vocabulary readers into Refugio voice (legitimate use case).
- A document with no blacklist + no anchors is "neutral" and shouldn't be punished.
- A document with blacklist + zero anchors is the exact failure mode the gate exists to catch: corporate vocabulary winning, Refugio losing.

**Vaccine:** Voice gates that scan per-section are too strict (most sections legitimately don't reference 2014 / Refugio). Global scope is the right granularity. When wiring the next voice-shaped contract, default to aggregation across the unit-of-distribution (here: the 22-section dataset; for other systems: the PR diff, the commit body, the released chapter).

---

## 2026-05-14 — 22-section schema expansion + Tandas & Partes structural contract

**Session:** `kobiidistilleros-22-section-singularity-v210000`

Schema v1.2.1 expanded the canonical Mother Prompt from 19 to **22 sections** by adding the Sovereignty layer (§14-16: Cognitive Mirror, Decision Traceability, Antifragilidad) and the Cashflow/Telemetría/Outside-the-Box trio (§20-22). §22 was fused at Owner direction: "Inferencia Decisional Exógena & Conocimiento Negativo (Outside-the-Box Time-Saver)" — outside-the-box inference IS the harvest mechanism for inheriting other people's negative knowledge.

A new top-level block `tandas_partes_spec` declares the structural contract every materialized section MUST honor:

- 3 **depth-tandas** (`### Tanda T1` Baseline / `### Tanda T2` Chase-Gain / `### Tanda T3` Síntesis & Ventaja Estructural).
- 3 **orthogonal partes** per tanda (`#### Parte I` Narrativa / `#### Parte II` Estructura / `#### Parte III` ROI).
- Validator enforces both marker regexes (`tanda_heading_regex`, `parte_heading_regex`) per section file. Missing any tanda or parte → exit 1.

The §2 native "POR TANDAS" semantic (quick-wins / structural / arquitectura) collapses cleanly onto the depth-tanda axis: T1 = quick wins, T2 = structural, T3 = arquitectura. No duplication, no conflict.

**Vaccine:** When a schema names a structural concept twice (the §2 title "POR TANDAS" pre-existed; the structural layer reuses "Tandas"), explicitly map the older concept onto the newer abstraction in BOTH the schema description block AND the Mother Prompt instructions. Future readers will hit the collision and need the bridge documented inline. Done here in `parts/sleepy/distiller.md` §2 body and `schema.json#description`.

---

## 2026-05-14 — RAM Shield (BL-0033 RAM channel)

**Session:** `kobiidistilleros-consolidation-v82001`

Two-stage RAM management for 30+h unattended sessions. `ram-watchdog.js` already advised at 1500 MB ("consider /kclear"). New `ram-shield.js` adds an *active* 2 GB trip: append a timestamped snapshot block to `<cwd>/vault/progress.md` (or `.claude/progress.md` fallback, or `~/.claude/state/progress.md` global), emit a `systemMessage` carrying the exact `/compact focus on …` line (task summary auto-derived from `git log -1 --pretty=%s`), and emit `hookSpecificOutput.additionalContext` with the literal `CONTEXT THRESHOLD CROSSED` phrase so BL-0033 fires Claude's next-turn `/compact` emission. Live empirical: 20 claude.exe procs at 7 GB tripped cleanly on smoke (synthetic session ID kept the real session's debounce flag clean).

**Schema-field uncertainty:** `ram-watchdog.js` header claims `additionalContext` is rejected on Stop; memory `BL-0040` claims it IS supported. `ram-shield.js` emits BOTH `systemMessage` (reliable) and `additionalContext` (BL-0033 channel) — if the harness drops the latter, the former still surfaces the human-readable instruction. **Vaccine:** when two governance artifacts disagree on a harness schema, ship both and let the harness pick.

**Process-name resolution:** `tasklist /FI "IMAGENAME eq claude.exe"` matches Claude Code on Windows (verified, not inferred — `ram-watchdog.js` already uses it). `process_name_candidates` config array `["claude.exe","claude","claude-code"]` covers Posix + future renames.

**CWD-relative snapshot path:** Stop hook stdin carries `cwd`; resolve project-local first (`vault/progress.md` then `.claude/progress.md`), global fallback last (`~/.claude/state/progress.md`). Never assume `process.cwd()` is the project root inside a hook.
## 2026-04-25 — Shipped multi-session Lazarus (tools/lazarus_revive_all.py + /lazarus all/window

**Session:** `5ed443a6-0735-4409-a264-06be1c43bceb`

AGPL-3.0 and research-only licenses prohibit metadata stripping. When Owner asks to absorb OSS repos, refuse + offer vendor/NOTICE.md + adapter pattern with license retention.

---

## 2026-04-26 — Shipped MC-OVO-107 partial: JS cascade populator via esprima (tools/cascade_popu

**Session:** `unknown`

ANALYSIS_STALEMATE with full reason string > silent skip. Honest partial graph proves limits matter as much as positive findings; fake completeness is worse than acknowledged gaps.

---

## 2026-04-27 — Shipped: /ovo-audit canonical Spanish RESULT format + Anti-Echo Gate; bug-hunter

**Session:** `unknown`

Doctrinal-disqualification-first: verify upstream API/model existence (gh + vendor docs) BEFORE writing adapter. 0 cycles vs probe-fail-fix. Saved 3+ scaffold-illusions this session.

---

## 2026-04-27 — Lazarus multi-pane sovereignty cascade: lister --exclude-live + current-session

**Session:** `a4f80c66-4ab0-472a-a45a-a4a716de0173`

When N panes consume a shared FIFO concurrently, atomic-claim via mkdir-mutex (atomic on NTFS) prevents simultaneous reads popping the same entry. Without lock, all panes pick the first item -> silent collision.

---

## 2026-04-29 — Lazarus multi-pane fixes (MC-LAZ-23 bindings auto-populate, MC-LAZ-24 clean-exit

**Session:** `35da8c8f-3d0c-44ce-a25b-912050c91802`

ULTRA-PLAN MODE prompts with multiple gated MCs: reply 1-line (X MCs gated, wait for Y event) instead of full analysis. Each verbose response burns 5-7k against a 200k budget.

---

## 2026-04-30 — Zero-touch Win repair chain: rebuild es-ES ISO + setup.exe rejected 0xC1900204 M

**Session:** `0a2b14ee-87e9-4886-848d-2027da82494d`

Docker on broken VMP: enable Hyper-V backend instead of WSL2 (Hyper-V often already enabled). Win setup.exe /Auto Upgrade rejects 0xC1900204 if ISO build too close to installed.

---

## 2026-05-01 — Power-pack hardened over 2 days, 9 commits / 10 BL laws shipped: plugin scanner

**Session:** `f21c4d94-7929-4667-afef-0a69c56e07d3`

Stale project-memory entries that drive DESTRUCTIVE remediation must be live-probed before action — the MC-SYS-09 misfire spawned REPAIR_WINDOWS_v2.bat against a Docker that was already working (memory was 2 days stale). BL-0008 codifies probe-before-repair.

---

## 2026-05-03 — Hardened claude-power-pack across 7 phases: 11 commits (9 pushed to origin/main,

**Session:** `unknown`

User-authored security gates (secret-scanner, ovo-push-gate, readonly-prompts-guard) are the contract, not obstacles. Surface as blocked, ask for explicit auth — never bypass.

---

## 2026-05-03 — Phases V-VIII shipped + OVO audit verdict A recorded + 2 pending commits pushed

**Session:** `unknown`

OVO Phase A breadcrumb expires at 120s. Long-running audit turns must re-run --json before --record-verdict, or the verdict is rejected with no orphan write.

---

## 2026-05-03 — Phase IX globalization: per-project progress.md (BL-0043), terminal-slot recorde

**Session:** `unknown`

MCP env-var expansion IS supported by Claude Code launcher including digit-leading names. Verified empirically via 21st.dev deferred tools appearing post-restart.

---

## 2026-05-04 — LaptOps Genesis: Plan Maestro (docs/PLAN_MAESTRO.md) + Phase 0 bootstrap (monore

**Session:** `laptops-genesis-2026-05-03`

Reality Contract under platform reality: when a test or claim hits a platform-specific limitation, mark ignore with documented reason in module-level docstring + add LEARNINGS entry. Faking a pass or weakening the assert is a lie.

---

