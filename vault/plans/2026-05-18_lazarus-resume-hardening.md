# Ultra Plan — Lazarus Persistence + /resume Dedup Hardening

Origin: video instruction `2026-05-15 18-28-33.mp4` (whisper `base` transcript,
221 s). Owner decisions locked 2026-05-18 via AskUserQuestion:
1. Repair/reactivate existing system (NOT a new plugin).
2. Restore scope = session content + composer + tab-set (xterm scrollback is an
   accepted honest limit, not in scope).
3. Global `~/.claude/hooks/` scope (self-mod authorized this cycle).
4. The 3-day-old `.DISABLED` MODULE_NOT_FOUND crash = treated as resolved
   (hooks verified present/healthy on host 2026-05-18); focus on the 2 features.

## The two real requests (from audio, not the screen)

- **P1** `[00:01:23–00:02:48]` Auto-save session/tab state so that after a
  reset / crash / "se destruye el ordenador", reopening Cursor restores the
  exact chat **and the number of tabs** that were open.
- **P2** `[00:02:50–00:03:31]` `/resume` must NOT list sessions already open in
  another tab (redundant); hide already-open, surface the recently-closed
  rescuable ones.

## Verified current state (grounding, No Guessing)

- `resume-hide-live.js` = **SessionStart** hook (settings.json, JSON-verified).
  Implements P2: `orphanCleanup` (stale/crashed → visible) + `hideOwnSession` +
  `liveCloakSweep` (LIVE → hidden). Code byte-identical to its BL-0073
  `.removed` snapshot — wiring is live.
- `lazarus-snapshot.js` = **Stop** hook. `terminal-slot-recorder.js` also
  registered. `lazarus-heartbeat.js`/`lazarus_revive.py`/
  `lazarus-shell-autoresume.*` present. Sovereign Vault tooling present.
- `tools/resume_reindex.py` (built earlier this session) is the
  heartbeat-contract-identical orphan/monotonicity health+repair tool.

## Root-cause gaps (why the Owner still feels pain)

- **G-P1**: snapshot fires only on **Stop**. A hard crash / power loss emits no
  Stop → the last snapshot can be very stale → tab-set + composer not faithfully
  restored. Claude Code exposes no "tab changed" event; the only honest
  high-frequency anchor is the existing **heartbeat** cadence (~5 s).
- **G-P2**: `liveCloakSweep` only runs at **SessionStart of a NEW session**.
  Pre-existing already-open tabs stay visible in `/resume` until the next new
  session starts → exactly the Owner's "me sale otra vez" complaint.

## Plan (5 phases · ≤5 files/commit · Anti-Crash)

### Phase A — Empirical baseline (NO edits, kills Mistake #51)
- A1 run `python tools/resume_reindex.py` (orphan/stale/monotonicity baseline).
- A2 read `lazarus-snapshot.js` + `terminal-slot-recorder.js` +
  `lazarus-shell-autoresume.ps1` + `lazarus_revive.py`: trace exactly what is
  captured (composer id per tab? terminal slot count?) and what the reopen path
  restores. Document the precise capture/restore contract + the G-P1/G-P2 gap
  surface. No assumptions — cite line numbers.

### Phase B — P1 hardening: crash-safe snapshot (≤3 files)
- B1 add a heartbeat-cadence snapshot path so a no-Stop crash still has a
  recent tab-set + composer snapshot (reuse `lazarus-heartbeat.js`'s existing
  ~5 s tick; single-flight + throttle; fail-open; never block Stop pipeline).
- B2 ensure the snapshot records: per-tab composer/session id + terminal slot
  count, in an atomic write (temp+rename, utf-8, no BOM).
- B3 reopen path restores the recorded tab count + the right composer per tab.
- Honest limit (Owner-accepted): terminal **scrollback/input buffer** is
  xterm.js renderer state (not in `state.vscdb`) → restored = chat content +
  composer + tab-set, NOT pixel-exact scroll. Documented, not silently dropped.

### Phase C — P2 hardening: prompt dedup (≤2 files)
- C1 run `liveCloakSweep`-equivalent on a more frequent trigger (the existing
  heartbeat/Stop tick) so already-open tabs vanish from `/resume` promptly,
  not only at the next new-session start. Idempotent, no-clobber, same
  heartbeat-staleness contract as `resume-hide-live.js`.
- C2 wire `tools/resume_reindex.py --repair` as the manual superset / health
  gate; document it cannot disagree with the hook (identical contract).

### Phase D — Real-input verification (Ley 25 / Gate 7)
- D1 P1: snapshot, kill the harness WITHOUT a Stop (simulate crash), run the
  reopen path, assert tab-count + per-tab composer restored. Show output.
- D2 P2: with ≥2 sessions open, trigger the cloak, assert `/resume` /
  `resume_reindex` shows already-open = hidden, closed = visible. Show output.
- D3 `python tools/resume_reindex.py` green; no Node MODULE_NOT_FOUND on Stop.

### Phase E — Snowball + ship
- E1 `vault/knowledge_base/session_lessons.md`: root cause (Stop-only snapshot
  + SessionStart-only cloak), vaccine (heartbeat-cadence anchor; the only
  honest "frequent" trigger Claude Code exposes), xterm scrollback boundary.
- E2 commits scoped on the current branch; NO push / PR / OVO unless asked.

## Reality Contract
Zero placeholders/stubs. Hooks fail-open (never break Stop/SessionStart).
Global-hook edits via the authorized self-mod route. The xterm scrollback
limit is stated, never papered over.

## Out of scope (honest)
New standalone plugin (rejected — reuse existing). Pixel-exact terminal
scrollback restore. The stale `.DISABLED` crash (treated resolved).

---

## Phase 5 — Audit corrections (7 gaps; locked 2026-05-18)

Auditor (oneshot-architect-auditor) proved the G-P1 premise FALSE:
`lazarus-heartbeat.js` is **PreToolUse-driven, 30 s-throttled**, RAM-skipped,
0 ticks during long generations/idle — there is no ~5 s cadence to reuse.

Owner decisions (AskUserQuestion #2):
- **P1 resilience = best-effort within Claude Code events** (Stop +
  SessionStart + PreToolUse throttled). NO external OS ticker. Honest limit:
  an abrupt power-loss between events loses at most the delta since the last
  tool call — NOT power-loss-proof. Stated, not papered over.
- **Restore deliverable = durable composer/session set + full chat content**,
  reopenable post-crash/reboot. Tab COUNT reconstructed best-effort from that
  durable set, NOT via `tab-<PPID>` (PPIDs do not survive reboot).

Injected fixes: #2 recompute staleness from real 30 s throttle (≥90 s or
`bindings.json last_seen`) + fix the false "5 s" doc comments. #3 Phase A0
empirically proves cross-process `.jsonl` rename on this Win11 box before
Phase C depends on it. #4 snapshot reuses `isLegacyMirrorOurs`, high-cadence
writes only per-session canonical files, legacy mirror deferred to Stop,
2-pane concurrent test. #5 real latency risk is the PreToolUse path → snapshot
strictly best-effort/sub-budget with RAM-pressure skip; Phase D latency
assertion. #6 Phase A0 read-only `state.vscdb` query proving what tab/composer
topology is durable; deliverable narrowed accordingly. #7 Phase A0 go/no-go:
ONE real hook mutation via intended route; if denied → HALT to Owner; then
micro-batch 1 file/turn with verification between (parallel-edit-cascade).

Cloak "more frequent trigger" (G-P2) is re-anchored to **Stop** (a real,
frequent Claude Code event that already exists), not a fictitious 5 s tick.
