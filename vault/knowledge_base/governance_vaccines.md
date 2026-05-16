# Governance Vaccines — Append-Only

Cross-project preventive rules synthesized from governance misses (skill-skip,
gate-bypass, ceiling violations). Distinct from `distiller_vaccines.md`
(distiller kernel gate failures). Append-only.

---

## VAC-GOV-220000 — Quality-skill skip on multi-file delivery

**Synthesized:** 2026-05-15 · ULTRA-PLAN v220000 (THE QUALITY CORONATION)
**Severity:** Critical (process) · **Status:** ACTIVE, hard-gated

### Trigger pattern

A changeset of **≥ 3 source files** is authored and declared "done" /
committed **without** `code-reviewer`, `software-best-practices`,
`python-pro`, or `kobiicraft-review` ever being invoked in the session.

Empirical origin: 26 KobiiDistillerOS Python files (~2665 LOC) shipped
across multiple sessions with **zero** quality-review skill invocations
(70-transcript `grep` of the `Skill` tool). The CLAUDE.md "code-reviewer
for 3+ files" gate and the mandatory `feedback_auto_activate_skills.md`
were both bypassed silently. This is the structural cause of the repo's
44% preventive-health baseline: high edit volume, low review gating.

### Why it happened (root cause)

Skills of **action** (`kobiicraft-dev`, `kobiicraft-execution`,
`kobiicraft-ops`) were invoked; skills of **quality control**
(`code-reviewer`, `software-best-practices`, TDD, verification) were
systematically skipped. Nothing *mechanically* prevented the skip — the
gate was advisory prose, not an enforced rail. Advisory governance under a
`bypassPermissions` ceiling degrades to "honor system", and the honor
system lost over 76 sessions.

### Prevention (how to apply)

1. **Mechanical hard gate** (Owner-ratified, ceiling v5.5):
   `~/.claude/hooks/quality-skill-gate.js` — PreToolUse on Bash. DENIES
   `git commit` when ≥3 staged source files lack a fresh quality-skill
   evidence receipt at `<repo>/.git/quality-skill-evidence.json`. Receipt
   is produced AFTER the quality skills by:
   `node ~/.claude/hooks/quality-skill-gate.js --record <files...>`.
   The skip is now *impossible to commit through*, not merely discouraged.
2. **Volume-triggered auto-activation**: when a task will touch >1 file,
   the quality skills are activated BEFORE writing code, not after — see
   reinforced `feedback_auto_activate_skills.md`.
3. **Agent-team retro-audit pattern**: 3 parallel auditor sub-agents
   (code-reviewer / python-pro / kobiicraft-review) writing findings to
   disk is the canonical way to retroactively clear an un-reviewed
   changeset without blowing orchestrator context.

### Boundaries (non-generalizing)

This hard gate required explicit Owner ratification via `AskUserQuestion`
(it breaks the sealed velocity ceiling v5.4 for ONE narrow scope). It does
NOT authorize any other agent self-elevation. Reversible by deleting the
`quality-skill-gate.js` stanza from `~/.claude/settings.json` (backup:
`settings.json.bak-v220000`).

### Evidence chain

- `CLAUDE.md` → "Governance ceiling v5.5 — Owner-ratified amendment"
- `reports/verdicts/2026-05-15_ceiling_v5.5_ratification.md`
- `docs/audit/KOBIIDISTILLER_RETRO_AUDIT_v220000.md` (+ 3 `_retro_*.md`)
- Remediation commits: `c523c8e` (A), `d1a3134` (B), `3f5e4b8` (C1+C4),
  `ad0d664` (C3), `35fa549` (C5), `9c3a479` (C6)
- `vault/audits/verdicts.jsonl` (v220000 grade row — Phase F)

### Trigger regex (for automated detection)

`commit .* (?:[^ ]+\.(py|js|ts|java|go|rs)){3,}` with no
`quality-skill-evidence.json` mtime within session window.

---

## VAC-ARCH-230000.1 — Parallel-session false-collision on shared host

**Synthesized:** 2026-05-15 · ULTRA-PLAN v230000.1 (SOVEREIGN RECONCILIATION)
**Severity:** High (process / honesty) · **Status:** ACTIVE (advisory + double-check protocol) · **2-part vaccine (detection + double-check)**

### Trigger pattern

Two Claude Code sessions for the same Owner running on the same dev host
touch the same cross-repo subsystem (e.g., KobiiDistillerOS — workspace
engine + PP kernel). Each session commits architectural work without seeing
the other's commits because neither ran `git fetch origin && git status`
at session start. Later one session reads a fragment of the other's SSOT
manifest (e.g., only the invariant title "Engine NEVER moves") and
declares a **false** Vault-First Conflict (DNA-700 mandato 8), STOPs, and
asks the Owner to choose between two architectures that were **never
actually different** — just named differently.

Empirical origin: 2026-05-15 in this repo. Parallel session named the same
architecture "DNA-11000 Rule-097 roles-not-duplicates" while my session
named it "Opt D Hybrid Kernel-Only". The "Engine NEVER moves" line in
their manifest meant *engine stays in workspace*, not *no kernel package
at PP* — they had explicitly named `kpp-distiller-kernel` in the same
manifest, three lines below. I declared STOP without reading the next
three lines. Antithesis of Anti-Antipattern rule 8 (Double-check).

### Why it happened (root cause)

1. No session-start probe of `git status` + `git log --oneline` on both
   repos surfaced the parallel work. Without that, the agent's context
   begins with a stale snapshot of HEAD.
2. The agent stopped reading SSOT manifests at the first apparent
   contradiction (a heading + invariant title) instead of reading the
   FULL content of the manifest. Manifests use prose to qualify their
   invariants; skipping the prose flips the conclusion.
3. Compaction summary tone amplified the false alarm. Once "conflict"
   was the framing, the agent built an entire 3-option fork without
   verifying the contradiction.

### Prevention (how to apply) — 2-part protocol

**Part A — Detection (session start, MANDATORY for any cross-repo work):**

```bash
# In every repo the task will touch, before reading task-specific files:
git fetch origin && git status --short && git log --oneline -10
```

If any of the recent commits are by a non-current owner email or carry an
unfamiliar phase tag, **assume a parallel session is active** and read its
SSOT manifests in full before any architectural assertion. Append the
findings to `vault/audits/parallel_session_probe.jsonl` (one row per repo).

**Part B — Double-check (before declaring any Vault-First Conflict):**

Before emitting a DNA-700 mandato 8 conflict report, re-read the **FULL**
content of every SSOT manifest cited as evidence — not just headings, not
just invariant titles. Quote at least 2 lines from EACH side, separated by
at least 5 lines of intervening content, to demonstrate the contradiction
is structural and not a misreading of a single sentence taken out of
context.

Trigger phrases that demand the double-check before STOP: "Vault-First
Conflict", "architectural collision", "parallel session contradiction",
"shared-host-parallel-session-collision".

### Boundaries (non-generalizing)

This vaccine is advisory + protocol, not a hard gate. It does NOT
authorize agent self-elevation or change permission rails. A future hard
gate could be: PreToolUse on AskUserQuestion that contains the strings
"conflict" + "parallel session" + "ratify ONE architecture" → require
proof-of-double-read receipt at `<repo>/.git/parallel-session-doublecheck.json`.

### Evidence chain

- `reports/verdicts/2026-05-15_v230000.1_seal.md` (workspace) — full seal
- `vault/audits/verdicts.jsonl` row `session=v230000.1` (line 57)
- Workspace `docs/SSOT_KOBII_DISTILLER.md` → `## v230000.1 — Owner Ratification`
- PP `SSOT.md` → `## 1.1 — v230000.1 Owner Ratification`
- Workspace memory mirror:
  `~/.claude/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/memory/feedback_parallel_session_collision_false_alarm.md`

### Trigger regex (for automated detection)

Prompt or AskUserQuestion text containing: `Vault[-\s]?First Conflict|parallel session.*contradict|architectural collision|ratify ONE architecture`
without a preceding `git fetch.+git log` in the session's Bash history.

---

## VAC-ENV-240000 — Environment leak: hard require() of a quarantine-able path

**Synthesized:** 2026-05-16 · ULTRA-PLAN v240000.1 (SOVEREIGN CONVERGENCE)
**Severity:** High (environment) · **Status:** ACTIVE, hooks hardened · Codified as STANDARDS Rule-102

### Trigger pattern

A long-lived production hook/tool hard-`require()`s/imports a module by a
single absolute path inside a repo that parallel sessions mutate
(`~/.claude/skills/claude-power-pack/lib/atomic_write.js`). A sibling
session performs a working-tree-only `mv lib/ _quarantine/lib_dir/` with
**no tracked git delta** (only `.gitignore` staged). git HEAD still tracks
`lib/`, but the on-disk file is gone — so the require() throws
`MODULE_NOT_FOUND` and the hook silently dies. The breakage is
**intermittent**: it depends on which branch a sibling session last left
the shared working tree on (branches that track `lib/` make it reappear).

Empirical origin: 2026-05-15. Commit `753422d`
("chore(tree): sanitize working tree + quarantine fossils", a parallel
`/ultra` Q&A) moved 18 `lib/` files to `_quarantine/lib_dir/` working-tree
only. `~/.claude/hooks/lazarus-snapshot.js` (Stop) and `kg-sync-hook.js`
(PostToolUse) both did `require(path.join(... 'lib','atomic_write.js'))`
and started failing whenever the shared PP tree sat on a branch without
`lib/`.

### Why it happened (root cause)

1. A hook trusted a single mutable path with no fallback. The path lived
   in a repo owned by a different concern (PP skill content), not by the
   hook — a cross-boundary hard dependency.
2. The quarantine was a half-operation: `mv` on the working tree with no
   `git rm`/`git mv`, so git's tracked state and the filesystem
   disagreed. Consumers that read the filesystem broke; consumers that
   read git did not.

### Prevention (how to apply)

1. **Multi-location resolver, never a bare require of a mutable path.**
   Resolve in priority: canonical (`lib/`) → quarantine
   (`_quarantine/lib_dir/`) → **inline last-resort** implementation. The
   process must degrade, never throw `MODULE_NOT_FOUND`. Reference impl:
   `loadAtomicWrite()` in `~/.claude/hooks/{lazarus-snapshot,kg-sync-hook}.js`
   (v240000.1).
2. **Quarantine must be a complete operation.** Either `git mv` (tracked
   delta) or leave the canonical path intact. A working-tree-only `mv`
   with "no tracked delta" is a landmine for any filesystem consumer.
3. **Hooks own their dependencies.** A hook that needs a helper should
   vendor it or carry an inline fallback — never hard-depend on a path in
   a repo that other sessions triage.

### Boundaries (non-generalizing)

`~/.claude/hooks/` is not a git repo (global system hooks); the resolver
fix is a direct system edit, not a tracked commit. This vaccine does not
authorize moving hook logic into any tracked repo.

### Trigger regex (for automated detection)

Hook/tool source containing `require(` or `import ` with a path under
`skills/claude-power-pack/lib/` AND no sibling `_quarantine` /
inline-fallback resolver in the same file.

---

## VAC-VIS-290000 — Capture starts before the scene settles (UI modal captured as "gameplay")

**Synthesized:** 2026-05-16 · ULTRA-PLAN v290000.2 (SOVEREIGN VISION OVERHAUL)
**Severity:** High (visual integrity) · **Status:** ACTIVE, fix deployed + structurally guarded; live behavior proof is a secret-gated residual · STANDARDS Rule-102 family

### Trigger pattern

A headless screen-capture pipeline (Xvfb + real game client + ffmpeg
x11grab) starts recording before the client is actually in the target
scene, so the captured "gameplay" is really a blocking UI modal — a
resource-pack prompt, login screen, or loading screen. A metrics-only
verdict (bitrate/resolution/frame-count) PASSES because the file is a
valid video; only a real vision check catches that the *content* is a
dialog.

Empirical origin: 2026-05-15, audit `20260515T162133Z`. MundiCraft
`server.properties` had `require-resource-pack=false` **but** still set
`resource-pack=<url>` + a prompt. MC 1.21 sends the RP offer in the
**configuration phase** (before spawn/AuthMe), so the portablemc real
client showed a blocking "Pack de futbol — Proceed/Decline" modal during
the recorder's 30s warmup. The recorder's `Return×2` (written for the
Mojang accessibility welcome) did not actuate the 1.21 RP screen, so the
client sat on the modal and x11grab captured the dialog. The v250000
metrics verdict said PASS; the v290000 real Claude-Vision pass caught it.

### Why it happened (root cause)

1. **No scene-state precondition before capture.** Capture-start was a
   fixed sleep, not a gate on "client is in-world at the target".
2. **A new blocking modal class (config-phase RP) was unhandled.** The
   recorder only dismissed the dialogs it knew about (Mojang welcome,
   AuthMe), not the RP offer that 1.21 moved earlier in the join flow.
3. **The PASS gate was metrics-only.** Bitrate/resolution/frames cannot
   distinguish a stadium from a menu; only content-vision can.

### Prevention (how to apply)

1. **Capture-after-scene-settle GATE.** ffmpeg/x11grab MUST NOT start
   until: (a) all known blocking modals are dismissed, (b) the scene
   command (RCON tp) is dispatched + settled, (c) a forensic snapshot of
   the active window title is logged so a future dialog-capture is
   diagnosable from the run log alone.
2. **Dismiss modals across the whole warmup window, not at one instant.**
   Modal arrival time is non-deterministic (config-phase timing varies
   with server lag); interleave N resilient, screen-state-safe accept
   attempts across warmup rather than a single timed press.
3. **Never trust a metrics-only PASS for visual work.** A content-vision
   check (does the frame show the target scene?) is mandatory before any
   visual verdict is graded — metrics validate the container, not the
   content.

### Boundaries (non-generalizing)

The fix targets the portablemc real-client recorder
(`vision-recorder.js`), the only path that renders the vanilla client
GUI. The mineflayer+prismarine-viewer watcher path
(`sentinel-runner.js`) renders the 3D world headlessly and never shows
the RP modal — it is correctly out of scope. Live behavior proof of the
fix requires the `MC_BOT_PASSWORD` AuthMe secret + stopping the active
production watcher (shared `KobiiCapture` username) — that is an
explicit, Owner-gated residual, NOT something to fake green.

### Trigger regex (for automated detection)

Recorder/capture source where an `ffmpeg`/`x11grab` spawn is reachable
without a preceding modal-dismiss + scene-settle + window-title forensic
log, OR a visual verdict graded on bitrate/resolution/frame-count with no
content-vision assertion.

---

## VAC-SEC-300000 — Runtime secret handling on a shared, logged host

**Synthesized:** 2026-05-16 · ULTRA-PLAN v300000.0 (SECRET CORONATION)
**Severity:** High (credential exposure) · **Status:** bridge ACTIVE; rotation = irreducible Owner action · STANDARDS Rule-102 family

### Trigger pattern

A pipeline needs a production credential. It ends up exposed by one of:
(a) a credential committed cleartext into a tracked file (and pushed),
(b) a secret passed on argv (visible in `ps`/`/proc/*/cmdline`),
(c) a secret echoed into stdout/stderr/logs or an audit ledger,
(d) an agent asking for the secret in chat (the transcript IS a log).

Empirical origin: 2026-05-15/16. `bin/vision-capture` carried a cleartext
`MC_VISION_LOGIN_PASSWORD=` and was git-tracked + pushed to a GitHub
`origin/main`; the "established convention" (`flywheel_vision_detonate.sh`)
documented harvesting it with `grep`. The B4 live-proof residual could
not be closed without the secret, and every channel for the agent to
obtain it (chat, fabrication, harvesting the leaked value) was either a
new leak or propagation of the compromised one.

### Why it happened (root cause)

1. "Convenience convention" beat hygiene: a real password in a tracked
   helper script because it was the easy place to `grep` it from.
2. No designed secret boundary: nothing said *where* a runtime secret
   may live or *how* it crosses a host hop.
3. The honesty trap: under pressure to "collapse the residual", the
   tempting paths (ask in chat / reuse the leaked value / fake the run)
   all violate either the Reality Contract or the remediation itself.

### Prevention (how to apply)

1. **Secret lives out-of-tree, mode 0600, loaded at runtime.** Canonical:
   `~/.kobii/secrets/mc_bot.env` + a sourceable loader
   (`tools/flywheel/secret_bridge.sh`) with a **fail-closed** permission
   gate (refuse if not provably 0600; a documented, default-OFF,
   self-announcing test-only escape is the ONLY bypass and never ships
   to prod).
2. **Never argv — cross host hops over stdin.** `printf '%s' "$S" | ssh
   host 'S="$(cat)" cmd'`. argv is world-readable via `ps`.
3. **Redact every stream.** A passthrough-safe filter that replaces the
   live value with an **ASCII** marker (a non-ASCII marker mojibakes
   through locale/codepage round-trips and silently defeats leak checks)
   on anything headed to a log/terminal/ledger.
4. **An agent never receives a secret through chat.** Chat transcripts
   are logged. The secret enters only via the out-of-band file the human
   writes in their own terminal. If that file is absent, the honest
   outcome is a documented residual + an agent-runnable command — never a
   faked success and never reuse of an already-leaked value.
5. **A committed secret is compromised forever.** `.gitignore` cannot
   un-track it. Remediation = ROTATE (only the system admin can) +
   `git rm --cached` + history purge + collaborator re-clone. Surfacing
   the leak and stopping is correct; silently working around it is not.

### Boundaries (non-generalizing)

The 0600 fail-closed gate is correct for the real Linux target; on a
non-POSIX-perm dev host it is intentionally un-satisfiable (fail-closed
is the secure default there too). The test-only escape is loud and
default-OFF. This vaccine does not authorize an agent to rotate
credentials or to read a secret from any channel a human did not
explicitly place out-of-band.

### Trigger regex (for automated detection)

A tracked file matching `(PASSWORD|SECRET|TOKEN|API_KEY)\s*=\s*\S` that is
not gitignored; OR a secret-named var interpolated into argv of `ssh`/
`curl`/`node`; OR an `AskUserQuestion`/prompt requesting a password value.
