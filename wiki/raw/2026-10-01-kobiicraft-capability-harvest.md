# KobiiCraft capability harvest (maturity-transfer pilot)

- repo: `C:\Users\User\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files`
- HEAD: 7f8f9d66
- date: 2026-10-01
- method: read-only; capabilities harvested from source. Paths below are relative to repo root.

Taxonomy: L1 WORKS · L2 SURVIVES FAILURE · L3 OPERABLE · L4 EVOLVABLE · L5 PRODUCT · LG GOVERNED.
Traits: T-LIVE-SERVICE, T-PERSISTENT-USER-STATE, T-CONCURRENT-USERS, T-REMOTE-DEPLOY, T-CONTENT-HEAVY, T-BUILD-ARTIFACT, T-LOCALIZED, T-AI-PIPELINE, T-ECONOMY, T-EXTERNAL-INTEGRATIONS, T-CONSTRAINED-TARGET, T-UI-SURFACE, T-MODDING-A-BINARY, T-PLAYABLE.

## Capabilities

### KC-01 Shared-index-safe commit helper
level: LG GOVERNED
does: Commits with an exit code that describes the commit itself: waits for index.lock (never deletes it), requires pathspec scoping, verifies HEAD subject == message-file first line (exit 4 on mismatch), has --selftest.
evidence: scripts/safe_commit.py:1-38 (docstring contract + exit codes), :52-60 (absolute git path, SUBJECT_MISMATCH=4, DEFAULT_LOCK_WAIT=300)
traits: T-CONCURRENT-USERS (multiple agent/human writers on one working tree)
portable form: A system with several concurrent writers on one repo should commit through a helper whose exit code reflects the commit, not the trailing command, and verifies the landed subject.
kobiicraft-specific: Windows absolute git path candidates; sibling-pane lock wording.
maturity signal: Young projects trust `git commit && git log` exit codes; this helper exists because the same false-green happened twice after prose lessons did not prevent it.

### KC-02 Change-derived in-game verification, fail-closed on coverage gaps
level: L4 EVOLVABLE
does: Derives from git which files changed, selects registered verifiers (declarative registry), runs them; a changed in-game surface with NO registered verifier FAILS; config-scope files that reach no verifier need a written non-operational reason.
evidence: scripts/verify_change.py:1-57 (contract, modes --staged/--since/--all/--list), :70 (REGISTRY = vault/config/verification_registry.json)
traits: T-PLAYABLE, T-LIVE-SERVICE
portable form: A system whose truth is only observable by an end-user-like actor should map changed surfaces -> verifiers in a registry and treat "no verifier" as failure, since absence of a check reads as a pass.
kobiicraft-specific: surfaces are Minecraft plugin/NPC/menu paths; verifier is the GEX44 mineflayer bot.
maturity signal: Young projects run whatever tests exist; coverage holes are invisible. This one makes holes cost something (born from a 37/37 config gate that passed while a player could not be delivered).

### KC-03 Vital-plugin preflight against the live panel
level: L3 OPERABLE
does: Reads a single-source registry of vital plugins and queries each server's /plugins/ via the Pterodactyl Files API; fails if a vital JAR is missing or *.jar.disabled; exit 2 = cannot verify (soft skip logged as open asterisk, not silent pass).
evidence: scripts/preflight_vital_plugins.py:1-24 (exit codes), :38-42 (registry docs/KOBII_PHILOSOPHY/VITAL_PLUGINS.md, panel URL)
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY
portable form: A remotely deployed service should have a read-only preflight asserting required components are present AND enabled on every target, with a distinct "unable to verify" outcome that is not a pass.
kobiicraft-specific: Pterodactyl API, .jar.disabled convention.
maturity signal: Young projects discover a disabled critical plugin from player reports; here it is a pipeline gate with a three-valued result.

### KC-04 Chaos-monkey repeatability gate
level: L4 EVOLVABLE
does: Runs the QA watcher N (default 10) consecutive times on a feature; 10/10 PASS = STABLE, any failure = FLAKY = not DONE; results appended to a JSON file.
evidence: scripts/qa_chaos_monkey.sh:1-50
traits: T-AI-PIPELINE or T-BUILD-ARTIFACT (any deterministic generation pipeline)
portable form: A pipeline claimed to be deterministic should be run N times consecutively and declared done only if all N pass; flaky = not done.
kobiicraft-specific: uses a stubbed verdict (QA_STUB_VERDICT) so only block-map generation determinism is proven; real verdict validated separately.
maturity signal: Young projects declare done on one green run.

### KC-05 Declarative-state NPC/click-path gate with verified-backup repair
level: L2 SURVIVES FAILURE
does: Verifies (default) or repairs (--apply) lobby NPCs against a declarative desired-state JSON; repair drives the owning plugin's own commands (never hand-writes its state file); every mutated production file is backed up and the backup verified non-empty before any write (exit 3 = no write performed); verification reads persisted state back, not the 204.
evidence: scripts/network/lobby_npc_gate.py:1-42 (contract, exits 0/1/2/3), :60 (STATE_FILE vault/config/lobby_npc_desired_state.json)
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY, T-PLAYABLE
portable form: A system with a live config surface owned by another process should hold a declarative desired state, repair through the owner's API, verify-backup before write, and verify by reading persisted state back.
kobiicraft-specific: Citizens/BungeeCord/DecentHolograms semantics.
maturity signal: Young projects hand-edit the plugin's data file and trust the command's return code.

### KC-06 Private-index hunk-level commit under shared-tree lock
level: LG GOVERNED
does: Commits only the hunks of a file that contain a MARKER (plus named whole files) via a private GIT_INDEX_FILE; takes the shared index lock exclusively before seeding and holds it through commit; re-reads HEAD, refuses on move (exit 5), verifies parent/subject/file set (exit 4), re-syncs shared index afterwards.
evidence: scripts/hunk_commit.py:1-37
traits: T-CONCURRENT-USERS
portable form: When two writers share one file, commit granularity must be hunk-level and serialized against the shared lock; file-level pathspec is coarser than the collision.
kobiicraft-specific: panes = concurrent Claude Code sessions; kg-sync hook holding commits open for minutes.
maturity signal: Young projects have one writer, so the failure mode (a sibling's hunks swept into your commit) has never been measured.

### KC-07 Artifact provenance receipts (build-time lineage)
level: LG GOVERNED
does: Standalone tool writes, beside a built archive, identity hash, membership, pack shape, source revision + dirty flag, declared builder, destination; refuses to record env/paths/tokens; deliberately cannot adopt the artifact into the authoritative ledger (a human does that in a diff); an artifact with a receipt but no ledger entry still fails the gate.
evidence: scripts/pack_provenance_receipt.py:1-40 ; ledger target vault/config/pack_artifact_provenance.json (named at :25-26)
traits: T-BUILD-ARTIFACT, T-REMOTE-DEPLOY
portable form: A system that ships built artifacts should record lineage at build time (hash, source rev, dirty flag, builder, destination) and separate "producer writes receipt" from "human enrols into the authority".
kobiicraft-specific: resource-pack zips (MundiCraft_RP).
maturity signal: Young projects reconstruct artifact lineage by archaeology months later.

### KC-08 Plan-supersession gate (machine-readable decision lineage)
level: LG GOVERNED
does: Reads `supersedes:` front matter across plan files and refuses (exit 1) work against a superseded plan; exit 2 when the sweep itself cannot be trusted (population floor breached or a supersedes entry names a missing plan), outranking subject findings.
evidence: scripts/plan_supersession_gate.py:1-33
traits: T-CONCURRENT-USERS (parallel planners/agents), any system with versioned decisions/specs
portable form: A project with many dated specs should make supersession machine-readable and check it before building, with a distinct "cannot judge" code.
kobiicraft-specific: kseip-wNN plan filenames, SkyParty kit roster.
maturity signal: Young projects have few plans; the failure (two panes building on a retired roster in the same hour) needs scale.

### KC-09 Log-sensor "Bug War Report" with append-only failure memory
level: L3 OPERABLE
does: Scans runtime logs (local or read-only pull from prod), classifies by signature, appends events/memory to JSONL, derives recurrence (1=bug, 2=suspected pattern, 3+=NEVER_AGAIN rule candidate, owner review never auto), seeds known bug cards, emits dated MD+JSON report; hard-stop classes route to HUMAN_REQUIRED; exit 1 on live P0/human-required.
evidence: tools/bughunter/cli.py:1-23,44-60 ; tools/bughunter/memory.py:1-26 (RULE_CANDIDATE_THRESHOLD=3)
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY
portable form: A long-running service should have a read-only log sensor that signature-clusters errors, counts recurrence in an append-only store, and promotes 3x repeats to rule candidates for a human.
kobiicraft-specific: Paper log formats, boot-noise catalogue, economy/inventory hard-stop classes.
maturity signal: Young projects grep logs ad hoc and re-discover the same error each week.

### KC-10 Crash-safe scheduled run with overlap lock and stale-lock reclaim
level: L2 SURVIVES FAILURE
does: Bughunter scheduled mode = pull->scan->report->alert (Telegram on new P0/P1)->log line, invoked by cron/systemd timer (no daemon); lock file prevents overlap, stale lock (>3h) is reclaimed so a crashed run cannot wedge the schedule.
evidence: tools/bughunter/scheduler.py:1-13, :31 (DEFAULT_MAX_LOCK_AGE=3h), :34 (OverlapError)
traits: T-LIVE-SERVICE
portable form: Periodic jobs should be independent invocations guarded by a lock with a max age, rather than long-lived daemons.
kobiicraft-specific: Telegram alert transport.
maturity signal: Young cron jobs either overlap or wedge forever on a stale lock.

### KC-11 Runtime in-server guardian: JAR integrity, command health, blacklist, restart flag, potion leak, gameplay guard
level: L3 OPERABLE
does: In-process plugin runs a monitor set (jar presence/min size/age, command health, blacklisted plugins, restart flag, potion leak, gameplay guard) with alert levels and a health report writer.
evidence: KobiCraftServer/plugins/KobiiClawGuardian/src/main/java/com/kobiicraft/claw/monitor/ (JarIntegrityMonitor.java:13-70, MonitorManager.java, PluginBlacklistMonitor.java, HealthReportWriter.java)
traits: T-LIVE-SERVICE, T-MODDING-A-BINARY (plugin host)
portable form: A live service should carry an internal watchdog with pluggable monitors, severity levels, and a machine-readable health report.
kobiicraft-specific: Bukkit plugin lifecycle, potion-leak monitor.
maturity signal: Young projects only have external uptime pings.

### KC-12 Fail-open compatibility gate at the front door
level: L5 PRODUCT
does: Proxy plugin corrects the advertised supported-version range in ping responses and refuses too-old protocols at login with a readable localized message; fail-open by construction (unknown protocol / bad config / any throw -> let through), failures logged once not per ping; has a self-check test.
evidence: KobiCraftServer/plugins/KobiiVersionGate/src/main/java/com/kobiicraft/versiongate/KobiiVersionGate.java:21-62 ; src/test/.../VersionGateSelfCheck.java
traits: T-LIVE-SERVICE, T-CONCURRENT-USERS, T-LOCALIZED
portable form: A service with a client-compatibility floor should advertise the truth before connection and refuse early with a readable reason, and a safety gate must fail open and log-once.
kobiicraft-specific: BungeeCord ProxyPingEvent, ViaVersion protocol numbers.
maturity signal: Young projects let incompatible clients through to an unreadable backend disconnect.

### KC-13 Closed-loop economy balancer (inflation detect -> sink/source adjust) with dashboard/web export
level: L5 PRODUCT
does: Takes periodic economy snapshots, classifies deflation/stable/mild/high inflation via configurable thresholds, adjusts sinks and sources, bridges Vault/tokens/placeholders, shows GUI dashboard and exports to web.
evidence: KobiCraftServer/plugins/KobiiEconomyEngine/src/main/java/com/kobiicraft/economy/balancer/InflationDetector.java:11-60 ; balancer/SinkAdjuster.java, SourceAdjuster.java ; dashboard/WebExporter.java
traits: T-ECONOMY, T-PERSISTENT-USER-STATE, T-LIVE-SERVICE
portable form: A system with a virtual economy should monitor supply growth and have automatic sink/source levers with thresholds in config and an operator dashboard.
kobiicraft-specific: Prison tokens/Kriptonitas bridges.
maturity signal: Young economies are tuned by hand after players complain.

### KC-14 Kernel-drift identity guard for shim collapse
level: L4 EVOLVABLE
does: Asserts every symbol of a legacy re-export shim IS the same object as the SSOT package's, and that shims stay <=60 lines; exit 2 on drift, 1 on preflight failure.
evidence: scripts/check_kernel_drift.py:1-54 (MAX_SHIM_LINES=60)
traits: T-BUILD-ARTIFACT (multi-package codebase after de-duplication)
portable form: After collapsing duplicated code into a shared kernel, guard the shims by object identity and size so re-copying cannot silently return.
kobiicraft-specific: kpp_distiller_kernel pip package.
maturity signal: Young repos duplicate code; mature ones need a mechanism to keep de-duplication from regressing.

### KC-15 Blackbox player-journey observer with proof-of-context and positive-control channels
level: L4 EVOLVABLE
does: Headless mineflayer bot walks the real player path (network entry -> auth -> first minute -> discovery -> queue -> match -> post-match) acting as a player (without QA-only permissions); reports last PROVEN phase, refuses to interpret observations until context (which server/lobby) is proven, and reports NO_PROBADO unless each observation channel passed a positive control; it prints no PASS - a human reads the report.
evidence: tools/smoke-test/gex44-journey-run.js:1-40 ; tools/smoke-test/assertions.js, gex44-bot.js
traits: T-PLAYABLE, T-LIVE-SERVICE, T-CONCURRENT-USERS
portable form: A system whose users traverse a multi-step journey should have a synthetic-user observer with the user's real privilege level, phase-reached reporting, context proof and per-channel positive controls.
kobiicraft-specific: mineflayer, GEX44 host, Bungee /server permission bug (BUG-016).
maturity signal: Young projects test at config/unit level; this one learned that a QA bot with extra permissions makes the gate green because of its privilege.

### KC-16 Liveness-bounded automated playtest drill
level: L4 EVOLVABLE
does: Every tick wait has a wall-clock deadline derived from tick budget x slack with a typed DrillAbort (NO_PROGRESS_TIMEOUT / NONFINITE_STATE / RUN_WATCHDOG); non-finite numbers encoded as strings so JSON null is not read as "missing"; timers stay ref'd so a hang cannot exit 0.
evidence: tools/smoke-test/drill-liveness.js:1-40 (DEFAULTS msPerTick 50, slack 4, floorMs 5000, perRunTicks 640)
traits: T-PLAYABLE, T-AI-PIPELINE (any automated test driver)
portable form: Any automated driver of a live system must bound every wait and type every ending, so a hang cannot read as a clean exit.
kobiicraft-specific: NaN-position/physicsTick incident in mineflayer 4.37.
maturity signal: Young harnesses hang for 30 minutes (this one did, 2026-09-23) before gaining deadlines.

### KC-17 Unattended patrol with RUN-vs-MISSION status, dedup and news-only escalation
level: L3 OPERABLE
does: Runs a declared verifier set on a cadence; classifies MISSION status separately from RUN status; selecting zero verifiers = CANNOT_EVALUATE (never PASS), unknown verifier id fatal; dedups via the bughunter signature primitive; escalates only NEW incidents.
evidence: scripts/patrol.py:1-45 ; scripts/patrol_notify.py ; vault/config/patrol_manifest.json
traits: T-LIVE-SERVICE, T-PLAYABLE
portable form: A monitoring job must separate "the scheduler ran" from "the thing worked", treat empty selection as unknown, dedup, and alert only on news.
kobiicraft-specific: GEX44 verifiers, Telegram.
maturity signal: Young projects' scheduled checks exit 0 when they checked nothing.

### KC-18 Static "praxis guard" + config scanner QA pipeline
level: L4 EVOLVABLE
does: Node static guard and config scanner (whitelist, JSON report) plus a QA pipeline script for plugin source/config; CI invokes it conditionally.
evidence: KobiCraftServer/tools/praxis-guard/{praxis-guard.js,config-scanner.js,run-qa-pipeline.sh,whitelist.json} ; .github/workflows/ci.yml (Praxis guard step)
traits: T-BUILD-ARTIFACT, T-LIVE-SERVICE
portable form: A plugin/config-heavy codebase should have a repo-specific static scanner with a whitelist and report.
kobiicraft-specific: Minecraft plugin idioms.
maturity signal: Young projects rely on code review for house rules. CAVEAT: CI calls tools/praxis-guard/run.sh which does NOT exist in the tree (listing shows run-qa-pipeline.sh), so the CI step prints "praxis-guard not found, skipping" -- see unverified list.

### KC-19 CI: Maven verify with a zero-tests-ran tripwire
level: L4 EVOLVABLE
does: GitHub Actions JDK21 `mvn verify`, then aggregates surefire XML; fails if total tests < 1 ("tests did not run") or any failure/error; reports built JAR count; path-filtered triggers.
evidence: .github/workflows/ci.yml:1-62
traits: T-BUILD-ARTIFACT
portable form: A CI that runs tests must also assert the test count is non-zero, since a green with zero tests is a pass nobody earned.
kobiicraft-specific: Maven/surefire, multi-module KobiCraftServer.
maturity signal: Young CI is "mvn test" and green when nothing ran.

### KC-20 Pre-push branch-freshness guardian
level: LG GOVERNED
does: git pre-push hook blocks push of a branch behind origin/main (fetches silently), allows main push and no-remote; documented bypass; installed via core.hooksPath .githooks.
evidence: .githooks/pre-push:1-40 ; install_hooks.sh
traits: T-CONCURRENT-USERS
portable form: Multi-branch/multi-agent repos should block stale-branch pushes.
kobiicraft-specific: none notable.
maturity signal: Young repos hit mass merge conflicts first.

### KC-21 Staged, hash-verified, reversible artifact promotion
level: L2 SURVIVES FAILURE
does: JAR deploy in phases: --inspect (download what is live; name, size, sha256, declared version) -> --stage (upload as `<final>.upload`, re-download, compare sha256; live artifact untouched) -> --promote (refuses without a verified stage from THIS run; renames old to `.bak.<ts>` same volume, re-reads sha256, only then renames .upload to final; nothing deleted) -> --restart -> --verify (boot log must show `Enabling <Plugin> vX`). Class-name diff proves overwrite is additive.
evidence: scripts/network/jar_deploy.py:1-50 ; scripts/network/kme_deploy.py (HR-01 park .bak.<ts>.disabled, referenced at kme_resource_rollback.py:5-8)
traits: T-REMOTE-DEPLOY, T-BUILD-ARTIFACT, T-LIVE-SERVICE
portable form: A system deploying artifacts to a host it cannot run on should stage->verify-hash->promote-with-backup->restart->verify-by-running-version, never delete, and refuse promote without a same-run verified stage.
kobiicraft-specific: Pterodactyl Files API, plugin.yml version.
maturity signal: Young deploys are scp + restart with no read-back; here the version string itself was made truthful (commit 1eadeac4) so the log can tell a deploy from a non-deploy.

### KC-22 Restart proof by uptime regression, not by state
level: L3 OPERABLE
does: Restart verifier proves a restart happened only if uptime goes BACKWARDS (a post-uptime greater than pre means no restart regardless of HTTP reply); tri-state PASS/FAIL/INCONCLUSIVE(3); polls panel for each named backend.
evidence: scripts/network/restart_verified.py:1-36 (HOSTS map, PASS/FAIL/INCONCLUSIVE = 0/1/3, POLL_S=10)
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY
portable form: Prove a restart by a monotonic counter that can only retreat on a new process; "running" before the old process dies is a false green.
kobiicraft-specific: Pterodactyl resources endpoint.
maturity signal: Young ops trust a 204/`running`; here the new JAR was on disk and the old one in memory for 21 minutes.

### KC-23 Ownership-aware (byte-identity) rollback for data-backed capabilities
level: L2 SURVIVES FAILURE
does: Rollback tool deletes seeded resources only when bytes are IDENTICAL to the packaged ones AND the path was proven absent pre-activation; any difference = operator-owned = never deleted; documents that data-only revert is transient and a durable revert needs binary then data then boot; says explicitly it does not revert generated worlds.
evidence: scripts/network/kme_resource_rollback.py:1-50
traits: T-PERSISTENT-USER-STATE, T-REMOTE-DEPLOY, T-CONTENT-HEAVY
portable form: When a feature is backed by seeded data, rollback must identify what is ours by content identity (not name), and state what it cannot undo.
kobiicraft-specific: InteriorResourceProvisioner seeding semantics.
maturity signal: Young systems roll back binaries only, leaving the feature on through its data.

### KC-24 Declared-surface drift gates for messages/menus/permissions/plugins (state-file + gate pairs)
level: L4 EVOLVABLE
does: Family of `<x>_gate.py` scripts each paired with a vault/config/<x>_state.json that declares the surface; gates fail on DRIFT (new undeclared surface, declared surface vanished, dialect change), not on pre-existing debt, so they are not switched off. Instances: message_surface, menu_integrity, permission_scope, plugin_baseline, plugin_ownership, plugin_version, storage_backend, spawn_on_join, chat_format, identity_store, module_readiness, minigame_residue, world_persistence, tracked_secret, root_hygiene.
evidence: scripts/network/message_surface_gate.py, plugin_baseline_gate.py, permission_scope_gate.py, tracked_secret_gate.py ; vault/config/verification_registry.json (_why_message_surface_does_not_fail_on_debt) ; vault/config/*_state.json (listing)
traits: T-LIVE-SERVICE, T-LOCALIZED, T-REMOTE-DEPLOY
portable form: Make every externally visible surface declare itself in a state file and gate on drift rather than on debt, so a new undeclared surface cannot appear silently and the gate is not turned off for being red on day one.
kobiicraft-specific: 429 message surfaces, plugin.yml/Citizens/DeluxeMenus.
maturity signal: Young projects have no inventory of their own surfaces; "invisible" has never been converted to "declared".

### KC-25 Gate-failure-mode self-documentation inside the registry (negative scope and named debt)
level: LG GOVERNED
does: The verification registry records, per entry, why a surface IS or IS NOT in scope, what the verifier does NOT prove, and named residual debt with the condition that would change it (e.g. boss auto-spawn interval-minutes 0 -> becomes player-surface when >0), and a closed-note with the prediction error.
evidence: vault/config/verification_registry.json:1-50 (_what_the_versiongate_verifier_does_not_prove, _gap_prison_boss_ingame, _gap_safechat_ingame)
traits: any system with gates
portable form: A gate registry should state what each check does not prove and keep named, conditioned debt, rather than faking coverage.
kobiicraft-specific: none.
maturity signal: Young gate registries are lists; this one is a decision record.

### KC-26 Localization-quality gate (accents/ortography) that refuses to auto-fix ambiguity
level: L5 PRODUCT
does: Gate on Spanish orthography of player-visible text: touches only YAML VALUES (never keys), masks commands/permission nodes/PAPI placeholders/MiniMessage/color codes/enums/URLs, auto-fixes only unambiguous words, reports ambiguous ones for a human, declares ALL-CAPS as a known limitation; exit 1 on remaining unequivocal faults.
evidence: scripts/network/spanish_orthography_gate.py:1-40 ; scripts/mundicraft_i18n_audit.py:1-70 (bare-English-word audit)
traits: T-LOCALIZED, T-UI-SURFACE
portable form: A localized system should gate on language QUALITY (not only absence of the source language), with masking of machine-readable tokens and no guessing between two valid words.
kobiicraft-specific: Spanish tildes/enies, Minecraft color codes.
maturity signal: Young projects certify "0 English strings" and read it as good Spanish; here the same confusion was caught and split into two gates.

### KC-27 Data-directory persistence invariants (classify, atomic save, quarantine-not-delete, writer-vs-open-server)
level: L2 SURVIVES FAILURE
does: Two-plane gate: live world dir classification completeness (unclassified = authoritative), quarantine artifacts still present, session.lock/server-running precondition (`--assert-safe-to-write`); and static check that repo tooling touching world paths reads server current_state, writes also rename (atomic publish), deletes also move aside.
evidence: scripts/network/world_persistence_gate.py:1-40
traits: T-PERSISTENT-USER-STATE, T-LIVE-SERVICE
portable form: A system with a user-data directory should classify every file (authoritative/regenerable/ephemeral), save atomically, quarantine instead of delete, and make "server stopped?" part of every writing operation.
kobiicraft-specific: Anvil region files, session.lock.
maturity signal: Young projects regenerate corrupt data silently (indistinguishable from griefing to the player).

### KC-28 Credential rotation with all-or-nothing preflight and verified backup
level: L2 SURVIVES FAILURE
does: Rotates a shared proxy secret across proxy and all backends: dry-run default; abort if any consumer unreadable; back up each consumer and re-read/compare; write backends first, proxy last; reload then verify by a real login; secret never printed (only a SHA-256 prefix); all backup paths printed before first write; states plainly that nobody can log in while the window is open.
evidence: scripts/network/rotate_proxy_shared_secret.py:1-39
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY, T-EXTERNAL-INTEGRATIONS
portable form: Rotating a shared credential needs read-all/backup-all/verify-backup preflight, ordered writes, verify by a real transaction, and non-printing of the secret.
kobiicraft-specific: AuthMe proxySharedSecret.
maturity signal: Young projects rotate by hand-editing configs host by host.

### KC-29 Secret hygiene: tracked-secret gate + dispositions + credential registry
level: LG GOVERNED
does: Gate scanning tracked files for secrets with an explicit dispositions file (known/accepted entries), credential gate/query scripts and a credential registry state; infra endpoints canonicalized (hard rule HR-INFRA-ENDPOINTS-CANONICAL-001 referenced in auto-deploy.py:33-42 after hardcoded creds were stripped and env-sourced).
evidence: scripts/network/tracked_secret_gate.py ; vault/config/tracked_secret_dispositions.json, credential_registry_state.json ; scripts/auto-deploy.py:33-42 ; tools/bughunter/credscan.py
traits: T-EXTERNAL-INTEGRATIONS, T-REMOTE-DEPLOY
portable form: Any repo with deploy credentials should have a gate over tracked secrets with a reviewed dispositions file and env-only credential sourcing that fails fast when unset.
kobiicraft-specific: Pterodactyl/Discord tokens.
maturity signal: Young repos have credentials in scripts; this repo found a leaked one in a deploy script and retired the path.

### KC-30 Pterodactyl panel backups and gex44 recovery archive
level: L2 SURVIVES FAILURE
does: Scripts to create panel-side backups before change and archive recovery material from GEX44 with a manifest.
evidence: scripts/network/ptero_backup_create.py ; scripts/network/gex44_recovery_archive.py ; gex44/recovery-archive-manifest.json
traits: T-REMOTE-DEPLOY, T-PERSISTENT-USER-STATE
portable form: Remote hosts should have a scripted, manifested backup/recovery archive step before destructive operations.
kobiicraft-specific: Pterodactyl, GEX44 box.
maturity signal: Young projects rely on the host provider's snapshots.
(NOTE: evidence is file existence + manifest; contents not read in depth.)

### KC-31 Mutation drills proving gates and clauses are load-bearing
level: LG GOVERNED
does: Table-driven byte-level mutation drill: removes each clause of a Java subject, asserts the RIGHT test turns red (a mutant killed by a different test is a finding); restores bytes and verifies hash; exit 2 HARNESS-FAILED (baseline red / anchor not unique / restore mismatch) is distinct from exit 1 (mutant survived). Sibling drills for hunk_commit and observability.
evidence: scripts/tests/java_mutation_drill.py:1-40 ; scripts/tests/mutation_drill_hunk_commit.py ; scripts/tests/mutation_drill_observability.py ; scripts/tests/test_verify_change_failclosed.py
traits: T-BUILD-ARTIFACT, any system with gates
portable form: Every gate/test suite on critical logic should be proven by mutation (remove clause -> expected test fails), with "could not run" distinguished from "survived".
kobiicraft-specific: KobiSkyWars Java subjects, Windows JDK path.
maturity signal: Young suites assert green; they have never been shown to go red.

### KC-32 Load test with percentile report against the live panel/console
level: L4 EVOLVABLE
does: Fires N concurrent stadium-load requests via Pterodactyl console API, parses plugin-reported latency from latest.log, outputs p50/p95/p99 JSON report; has concurrent and sequential-warm modes; honestly states it does not spawn 500 real clients.
evidence: scripts/tests/load_test_500players.py:1-35
traits: T-LIVE-SERVICE, T-CONCURRENT-USERS
portable form: A concurrent service should have a load script producing latency percentiles with a stated scope.
kobiicraft-specific: /kobimap doomsday-load, StadiumLoader.
maturity signal: Young projects have no latency numbers. (Scope caveat: console-driven, not real clients.)

### KC-33 Test-harness host-admission gate (refuse to start a run the host cannot survive)
level: L4 EVOLVABLE
does: Before a long golden-run, checks the desktop host has headroom (floor derived from the one observed death point, ~4.05 GiB free of 31.31), refuses to start otherwise; each admitted run records free-before/free-after/min footprint so the floor can be tuned from evidence; verdicts are not a severity scale.
evidence: scripts/harness/host_admission.py:1-40 ; scripts/harness/artifact_identity.py
traits: T-PLAYABLE, T-CONSTRAINED-TARGET
portable form: A long-running test harness should admit-or-refuse based on measured host headroom and treat its own load generator as part of the system under test.
kobiicraft-specific: LuckyArena golden journey, mineflayer bots.
maturity signal: Young harnesses die mid-run and the result is hand-labelled INCONCLUSIVE.

### KC-34 Human-approval quarantine before external publishing
level: LG GOVERNED
does: Videos enter a quarantine file posted to Discord; Owner approval reaction (check/X) required; approved ones emit a signal file for the social bridge; rejected carry a reason; no video reaches social without approval.
evidence: discord_bot_deploy/video_quarantine.py:1-40 ; discord_bot_deploy/rescue_verify.py:1-30 (dry-run default, --apply)
traits: T-AI-PIPELINE, T-EXTERNAL-INTEGRATIONS
portable form: A system that auto-generates public-facing content should hold it in a quarantine with explicit human approval and a durable record before publishing.
kobiicraft-specific: Discord reactions, TikTok.
maturity signal: Young content automation posts straight to social.

### KC-35 Commit-time gates: UKDL citation, plugin tracking, advisor, vault distill
level: LG GOVERNED
does: Repo hooks (pre-commit, commit-msg, post-commit) and Python gates enforce citation format of knowledge-base rule entries, plugin-tracking, wikilink validity and staged-id uniqueness, with their own tests; a hook-stage-ordering test exists.
evidence: scripts/hooks/ukdl_citation_gate.py ; scripts/hooks/plugin-tracking-gate.py ; scripts/tests/test_ukdl_citation_gate.py ; test_ukdl_wikilink_gate.py ; test_ukdl_staged_uniqueness.py ; test_hook_stage_ordering.sh
traits: T-CONCURRENT-USERS, any system with a rules corpus
portable form: A rules/knowledge corpus should be protected at commit time by gates with unique ids, valid links and citations, tested like code.
kobiicraft-specific: UKDL format (280 HR-ish markers counted by regex in vault/knowledge_base/ukdl-universal.md).
maturity signal: Young repos' notes rot; this corpus has CI on its own integrity.

### KC-36 Declared-routers + resident-agent roles with wiring gates ("a role with no destination is a FAILURE")
level: LG GOVERNED
does: CLAUDE.md routers dispatch to roles (KCOO portfolio arbiter, KDDI demand council 1-14, KME arbiter/G2/S1/S2/R1, KIS) and each has a wiring gate (`kcoo_wiring_gate.py`, `kddi_wiring_gate.py`, `kme_agent_wiring_gate.py`) exiting non-zero when a role has no destination; INCONCLUSIVE never degrades to NEW; evidence-substrate ladder forces ABSTAIN when player behaviour was not observed.
evidence: CLAUDE.md:15-40 ; .claude/agents/ (kcoo-g1.md, kddi-01..14, kme-g1/g2/s1/s2/r1/a6) ; scripts/kcoo, scripts/kddi, scripts/kme (counts only)
traits: T-AI-PIPELINE (agent-assisted development), T-CONCURRENT-USERS
portable form: A system governed by AI agent roles should machine-check that every role is wired to a trigger and has an ownership arbiter that runs before new capability is designed.
kobiicraft-specific: portfolio of game modes; Minecraft substrate.
maturity signal: Young projects have one assistant and no precedent arbiter; this one measured 14 EXISTS / 0 new on a 130-engine roster before building (CLAUDE.md:38).

### KC-37 Pre-generation approval gate (binary APPROVED / NO_BUILD naming every failed gate)
level: L1 WORKS
does: Pure stateless arbiter evaluates a world plan graph before any block is placed against 9 structural gates (spawn anchor, visual gravity, has districts, district purpose, traversal reachability, uniqueness, expansion reserve, dependency DAG, footprint overlap with verified-vs-estimated asymmetry); only APPROVED reaches painters; null graph = NO_BUILD. 144 kill-switch/gate test occurrences across 30 KME test files.
evidence: KobiCraftServer/plugins/KobiMapEngine/src/main/java/dev/kobicraft/mapengine/megascale/PreGenerationKillSwitch.java:6-50 ; src/test/.../megascale/KillSwitchTierTest.java
traits: T-AI-PIPELINE, T-CONTENT-HEAVY
portable form: A generative pipeline should have a cheap, pure pre-flight arbiter over its plan (before expensive generation) returning pass/fail with every failed gate named; an estimated input must not be allowed to veto.
kobiicraft-specific: district/skyline/spawn semantics.
maturity signal: Young generators validate output after the fact; this gates the plan.

### KC-38 Deterministic launch dress-rehearsal simulator and live launch monitor
level: L4 EVOLVABLE
does: In-memory T-6h..T+12h simulation of the launch (arrival curve, queue depth, match cycles, TPS pressure) with fixed --seed reproducibility emitting a READY verdict only if every declared gate holds; paired static readiness simulator; a live monitor polls TPS, plugin enabled state, queue depth, SEVERE rate every 15s with Discord events and --dry-run; a rehearsal script runs the ceremony end-to-end with --stress N bots and exit codes 2/3.
evidence: scripts/mundicraft_dress_rehearsal_sim.py:1-22 ; scripts/mundicraft_live_monitor.sh:1-21 ; scripts/mundicraft_rehearsal.sh:1-21
traits: T-LIVE-SERVICE, T-CONCURRENT-USERS, T-PLAYABLE
portable form: A launch-dated system should have a seeded simulation of the launch against declared gates, a rehearsal driver, and a live monitor with thresholds.
kobiicraft-specific: June 11 2026 MundiCraft event, 5v5 match ceremony.
maturity signal: Young projects have no launch rehearsal; sim is in-memory, so it proves the gates' logic, not real load.

### KC-39 Semantic-drift linter for banned concepts (gambling language, FOMO, stale class names)
level: LG GOVERNED
does: Shell linter fails (exit 1) on banned Java class names, gambling language in messages, stale BettingManager refs in plugin.yml, FOMO references in config, doc description drift, and missing required core references.
evidence: scripts/mundicraft_semantic_lint.sh:1-91
traits: T-ECONOMY, T-LOCALIZED, T-UI-SURFACE
portable form: A product with a legal/ethical positioning constraint (here no gambling/FOMO/pay-to-win) should enforce vocabulary bans in code, config and docs mechanically.
kobiicraft-specific: gambling/FOMO vocabulary, MundiCraft naming.
maturity signal: Young projects state values in docs; mature ones lint them.

### KC-40 Chat-filter self-sanity: refuse to install a blocking pattern that matches ordinary messages
level: L2 SURVIVES FAILURE
does: SafeChat compiles each blocked phrase (with leet-speak mapping) and refuses to install it, logging a warning naming the phrase, regex and colliding ordinary message, if it matches a built-in sanity corpus; warn-threshold + timed mute, filter log; replacement phrases are constructive ("gg", "buen intento").
evidence: KobiCraftServer/plugins/safechat/src/main/java/com/kobicraft/safechat/services/FilterService.java:27-60 ; verification_registry.json (_why_safechat_source_and_config: "1" leet-collision muted players)
traits: T-CONCURRENT-USERS, T-LOCALIZED, T-UI-SURFACE
portable form: Any moderation rule engine should self-test new rules against a corpus of ordinary content and refuse unsafe rules rather than mute innocents.
kobiicraft-specific: leet map l->[l1], Spanish phrases.
maturity signal: Young filters ship rules that false-positive on common text.

### KC-41 No-pay-to-win commerce and design-philosophy plugins (values encoded as modules)
level: L5 PRODUCT
does: Commerce plugin sells only cosmetics (particle_trail, chat_color, join_sound, title_glow) with toggle semantics, coins earned in play (CoinEarningListener, PrisonCoinListener); sibling plugins named for design intents (comeback-balancer, sportsmanship, reputation-by-kindness, warmjoin, seasonal-rituals, safechat, family-play) and KobiMemory with weekly build and mining contests, seasons and clip moments.
evidence: KobiCraftServer/plugins/no-pay-to-win-commerce/src/main/java/com/kobicraft/commerce/commands/BuyCommand.java:19-60 ; KobiCraftServer/plugins/KobiMemory/.../modules/SeasonsModule.java:19-45 ; plugin dir list
traits: T-ECONOMY, T-CONCURRENT-USERS, T-PERSISTENT-USER-STATE
portable form: A community product should encode its fairness/retention principles as explicit modules with ownership, not scattered rules. 
kobiicraft-specific: all of the content.
maturity signal: Young projects have features, not a deliberate fairness/progression/community design; (note: BuyCommand prices are hard-coded in a Map.of, not config - a young trait inside a mature repo).

### KC-42 Truthful scaled-surface kill-switch at network admin (remote command dispatch with testable pure core)
level: L3 OPERABLE
does: In-proxy network admin plugin dispatches commands to backends through the Pterodactyl API using a pure DispatchPlan (mode, permission bit, args, backend map, API-key present -> DENY/DISPATCH/INFO with message keys) that is unit-tested without Bungee or HTTP; PterodactylClient has its own test.
evidence: KobiCraftServer/plugins/KobiiNetworkAdmin/src/main/java/com/kobiicraft/netadmin/DispatchPlan.java:9-50 ; src/test/.../DispatchPlanTest.java, PterodactylClientTest.java
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY, T-CONCURRENT-USERS
portable form: Admin/operator commands that fan out to hosts should separate a pure decision function from I/O so permission/misconfig branches are unit-testable.
kobiicraft-specific: BungeeCord + Pterodactyl.
maturity signal: Young admin tooling is glue code with no tests.

### KC-43 TCP port watchdog: alert-only, one alert per outage, side-effect-free
level: L3 OPERABLE
does: Probes configured host:port targets every 30s, counts consecutive failures against a per-target threshold, appends one structured JSONL alert per outage, resets on recovery; deliberately does NOT restart (a separate consumer decides), systemd-installed (Restart=on-failure); separate alert consumer service exists.
evidence: kobicraft_content_intelligence/infra/port_watchdog.py:1-36 ; scripts/systemd/kobicraft-port-watchdog.service:1-28 ; scripts/systemd/kobicraft-alert-consumer.service
traits: T-LIVE-SERVICE
portable form: Keep the detector side-effect-free and alert-deduplicated (one per outage); put remediation in a separate consumer.
kobiicraft-specific: Minecraft 25565 TCP probe.
maturity signal: Young watchdogs restart blindly and flap.

### KC-44 Alert-consumer auto-remediation with dry-run default, cooldown and cursor persistence
level: L2 SURVIVES FAILURE
does: Separate consumer tails the watchdog's append-only alert log and issues a Pterodactyl restart; starts in dry_run, 180s per-target cooldown (anti restart-storm), persists a cursor so a daemon restart does not replay old events; deleting it stops auto-restarts without blinding observability.
evidence: kobicraft_content_intelligence/infra/alert_consumer.py:1-40 ; scripts/systemd/kobicraft-alert-consumer.service
traits: T-LIVE-SERVICE, T-REMOTE-DEPLOY
portable form: Auto-remediation should be a separable, dry-run-by-default consumer with cooldown and cursor, independent of detection.
kobiicraft-specific: Pterodactyl power action.
maturity signal: Young auto-restarters storm-loop and re-fire stale alerts.

### KC-45 Crash-idempotent on-demand GPU host state machine
level: L2 SURVIVES FAILURE
does: Stateless-between-ticks dispatcher drives OFF->BOOTING->RUNNING->SHUTTING_DOWN->OFF from a JSON state file with atomic writes (tempfile, fcntl lock) and an append-only JSONL transition log; wake via Hetzner Robot hw reset / WoL, sleep via ssh shutdown; side effects idempotent so crash recovery = read state and continue.
evidence: vps-bootstrap/kobiiclaw/gex44_dispatcher.py:1-45 ; vps-bootstrap/kobiiclaw/hetzner_robot.py
traits: T-REMOTE-DEPLOY, T-AI-PIPELINE, T-CONSTRAINED-TARGET (costly on-demand compute)
portable form: Expensive on-demand compute should be managed by a tick-driven state machine with atomic state, an append-only log and idempotent side effects.
kobiicraft-specific: Hetzner Robot API, GEX44 server number.
maturity signal: Young systems leave GPUs on or hand-start them.

### KC-46 Local LLM API router with key rotation, per-key daily budget and key masking
level: L3 OPERABLE
does: Flask streaming proxy between dev tools and the Anthropic API; rotates multiple keys (skipping placeholders), enforces a per-key daily token budget (default 150000) tracked in a usage file, masks keys in logs, local auth token.
evidence: infrastructure/claude_router.py:1-40
traits: T-AI-PIPELINE, T-EXTERNAL-INTEGRATIONS
portable form: A system that spends on external LLM APIs should route through a budgeted, key-rotating proxy with masked logging.
kobiicraft-specific: Anthropic endpoint, ports.
maturity signal: Young AI systems have one key in an env var and no budget.

### KC-47 Overlayable i18n with disk-over-defaults and JAR default fallback; per-player language persistence
level: L5 PRODUCT
does: Language manager loads ES and EN message files from the data folder (user-editable), falls back per-key to JAR defaults, supports legacy & hex & partial MiniMessage; per-player language is persisted (LanguageStorage), GUI selector and /idioma command, join listener.
evidence: KobiCraftServer/plugins/KobiiLang/src/main/java/com/kobiicraft/lang/LanguageManager.java:20-70 ; LanguageStorage.java ; gui/LanguageGUI.java ; commands/IdiomaCommand.java
traits: T-LOCALIZED, T-PERSISTENT-USER-STATE, T-UI-SURFACE
portable form: A localized product should let operators override message files while new keys fall back to shipped defaults, and persist per-user language.
kobiicraft-specific: Minecraft colour codes.
maturity signal: Young i18n is hardcoded strings or one language file with no default overlay.

### KC-48 Landing page security headers and cache policy
level: L5 PRODUCT
does: Static landing ships _headers (X-Frame-Options, nosniff, referrer policy, Permissions-Policy interest-cohort off, caching tiers) and _redirects; placeholder-swap script and swap state exist.
evidence: web/landing/_headers:1-12 ; web/landing/_redirects ; scripts/landing_placeholder_swap.sh ; web/landing/.swap_state.json
traits: T-UI-SURFACE
portable form: Public web surfaces should ship explicit header/caching policy and a swap-state mechanism for placeholders.
kobiicraft-specific: Cloudflare-Pages-style files.
maturity signal: Young landings have none; note: no CSP header present (verified absence in _headers).

### KC-49 Phased, partially-idempotent VPS bootstrap with abort-on-phase-failure
level: L4 EVOLVABLE
does: Master script runs phase0..phase6 (secure, tooling, workspace, sftp test, pipeline scripts, content pipeline, initial state) as root, aborts on first failing phase; phase0 skips key/user creation if present.
evidence: vps-bootstrap/bootstrap-master.sh:23-44 ; vps-bootstrap/phase0-secure.sh:25-44
traits: T-REMOTE-DEPLOY, T-LIVE-SERVICE
portable form: Host provisioning should be phase-scripted, ordered, abort-on-fail and skip-if-present.
kobiicraft-specific: kobicraft user, ed25519.
maturity signal: Young provisioning is manual. CAVEAT (young trait inside mature repo): phase0 prints the new root password to stdout and installs sudo NOPASSWD for kobicraft; rotates root password on every run (not idempotent); a later HR (secret hygiene) post-dates it.

### KC-50 Calibration-instrument "best-case ceiling" analysis (evidence-independent verdict at both ends of a bracket)
level: LG GOVERNED
does: Before building an expensive evidence-recovery step, measure whether even a perfect resolution would stabilize the metric, evaluating at BOTH ends of each uncertain row's bracket so the verdict cannot choose flattering evidence; changes no threshold; exit 3 INCONCLUSIVE, exit 4 selftest failed; a V-CEIL-BOTH-ENDS-DIFFER check guards the property.
evidence: scripts/kme/admission_ceiling.py:1-35
traits: T-AI-PIPELINE, T-CONTENT-HEAVY
portable form: Before investing in better evidence, compute the best-case outcome at both ends of the uncertainty and stop if neither stabilizes the result.
kobiicraft-specific: Wave 4C corpus bands/taper.
maturity signal: Young projects build the evidence step before asking whether it could matter.


## Counts per level (50 capabilities)

| level | count | KC ids |
|---|---|---|
| L1 WORKS | 1 | 37 |
| L2 SURVIVES FAILURE | 10 | 05,10,21,23,27,28,30,40,44,45 |
| L3 OPERABLE | 8 | 03,09,11,17,22,42,43,46 |
| L4 EVOLVABLE | 12 | 02,04,14,15,16,18,19,24,32,33,38,49 |
| L5 PRODUCT | 6 | 12,13,26,41,47,48 |
| LG GOVERNED | 13 | 01,06,07,08,20,25,29,31,34,35,36,39,50 |

Skew note: L1 is deliberately thin. Core gameplay (KME 613 main java files, ~70 plugins) was sampled for mechanism, not enumerated; breadth across levels was the brief. Interpretation: the mature signal is concentrated in L2-L4 and LG, not L1.

## Ten judged most portable (INTERPRETATION, not measured)

1. KC-02 change-derived verification, fail-closed on coverage gaps
2. KC-21 staged, hash-verified, reversible artifact promotion (with version-truthful boot line)
3. KC-22 restart proof by monotonic counter regression
4. KC-24 declared-surface drift gates (gate on drift, not debt)
5. KC-17 patrol with RUN-vs-MISSION status and CANNOT_EVALUATE on empty selection
6. KC-31 mutation drills proving clauses are load-bearing (HARNESS-FAILED distinct from survived)
7. KC-19 CI zero-tests-ran tripwire
8. KC-44 detector/remediator split with dry-run default, cooldown, cursor
9. KC-07 build-time provenance receipts, producer cannot self-enrol
10. KC-01/KC-06 commit helpers whose exit code describes the commit (only if concurrent writers exist)

## DOC-ONLY or doc-asserted (not counted as harvested)

- KIS Done-Gate: CLAUDE.md:31 says a done-claim without a `KIS-RECEIPT:` trailer is blocked. Only 5 textual mentions of KIS-RECEIPT in scripts/hooks/tools were found by grep; enforcement code NOT read or confirmed. DOC-ONLY pending check.
- K-ADOS fail-closed feature done-gate (Work Packet, Cascade Risk, Kill-Switch Record, Evidence Pack...): described in CLAUDE.md:34 and docs/kados/; no gate script located in this pass. DOC-ONLY.
- KCOO/KDDI/KME wiring gates: scripts exist (Test-Path true for kcoo_wiring_gate.py, kddi_wiring_gate.py, kme_agent_wiring_gate.py) but their bodies were not read; the "role with no destination = FAIL" behaviour is taken from CLAUDE.md. Existence confirmed, behaviour DOC-ONLY.
- "33 DNAs / 8 Pillars / 15 Pillars" standards (SOVEREIGN_STANDARD, BASELINE_S): doc layer only, not examined.
- Runbooks (docs/launch/*RUNBOOK*, docs/skyparty/SKYWARS_DEPLOY_RUNBOOK.md, docs/server/PLAYTEST_AUDIT_RUNBOOK.md, docs/ops/MUNDICRAFT_STAGING_BUILD_RUNBOOK.md): exist; content not read, so L3 runbook capability is DOC-ONLY.

## Could not verify / gaps and young traits found inside the mature repo

- CI references KobiCraftServer/tools/praxis-guard/run.sh; it does NOT exist (Test-Path false; dir holds run-qa-pipeline.sh). ci.yml:51-56 `if [ -f ... ] else echo skipping` therefore silently skips the guard. A gate that cannot fire (KC-18).
- ci.yml triggers only on *.java and pom.xml under KobiCraftServer; Python gates (verify_change, bughunter, 118 test_*.py under tools/) are NOT run in GitHub CI as far as .github/workflows shows (one workflow file only). Local/pre-commit only. Not confirmed whether another runner executes them.
- pre-commit hook (kobii_advisor) is explicitly non-blocking (`|| true; exit 0`); the repo's commit-time hard gates live in scripts/hooks, whose installation state (core.hooksPath) was not checked.
- Config/data migration framework: grep for config-version/schemaVersion found only 11 java files with 19 hits; no systematic plugin-config migration found. Migration-ish work is hand-written one-off deploy scripts (scripts/network has ~60 deploy_*/fix_*/skyparty_* one-shots, e.g. deploy_staging_kme_v2232..v2239). Treated as a gap in L4.
- Backup depth (KC-30): only file existence confirmed; no restore drill or retention policy read. No evidence of a tested restore of the survival/prison databases.
- BuyCommand prices hard-coded (Map.of) rather than config; phase0-secure prints root password to stdout (KC-49).
- Not read: KME engine internals beyond PreGenerationKillSwitch; kobicraft_content_intelligence video/AI pipeline (distiller kernel is a shim re-exporting kpp_distiller_kernel, whose gates hawkins_gate/placeholder_guard/roi_calculator were not opened); Remotion/sentient_videos; Discord bot brain; kobiiclaw mission control; GEX44 job queue runner; tools/CaptureBot. Counts: scripts/kme 519 files, scripts/network 541, scripts/probe 176, scripts/audit 234 (counted, not read).
- Test counts: 522 Java files matching *Test*.java under KobiCraftServer/plugins (includes target-free filter only for 'target' path), KME 441 test java files, 118 test_*.py under tools/, 50 under kobicraft_content_intelligence/tests. File counts, not pass counts; no test was executed (read-only).
- Hive systemd units (kobii-hive-orchestrator etc., Restart=always, NoNewPrivileges only on ingestion) are real but of the content-automation estate; running as User=root on atomic-ingestion.