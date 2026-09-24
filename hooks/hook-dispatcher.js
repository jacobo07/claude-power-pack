#!/usr/bin/env node
/**
 * Hook Dispatcher — bundle multiple Claude Code hooks into one Node process.
 *
 * Why: each entry in settings.json hooks[] spawns a fresh Node process
 *      (~300–800 ms cold on Windows). Chains of N small hooks pay N × that
 *      cost on every event. This dispatcher loads hook modules in-process,
 *      runs them sequentially or in parallel, and merges their JSON outputs
 *      into a single response — paying only one Node spawn for N hooks.
 *
 * Usage in settings.json:
 *   {
 *     "hooks": [{
 *       "type": "command",
 *       "command": "node \"~/.claude/hooks/hook-dispatcher.js\" --event=PreToolUse-default",
 *       "timeout": 15
 *     }]
 *   }
 *
 * Hook contract: each bundled hook must export `module.exports = { run }`,
 * where `run(input)` returns (or resolves to) the same JSON object the
 * standalone script would have written to stdout. The original CLI mode
 * (gated by `if (require.main === module)`) stays intact for backwards
 * compatibility — Lazarus shell autoresume + manual invocation keep working.
 *
 * Output merge rules:
 *   - decision: "deny" wins over "allow" (most restrictive).
 *   - additionalContext: concatenated with "\n\n" separator.
 *   - hookSpecificOutput: shallow-merged (later hooks override same keys).
 *   - All other top-level keys: last-writer wins.
 *
 * Errors in any single hook are logged to ~/.claude/logs/hook-dispatcher-errors.log
 * and the dispatcher continues — no single hook can break the chain.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync, spawn } = require('child_process');

const HOME = os.homedir();
const LOG_DIR = path.join(HOME, '.claude', 'logs');
const ERROR_LOG = path.join(LOG_DIR, 'hook-dispatcher-errors.log');
// NO-EVENT receipts (incident 2026-09-16/18). Honours CLAUDE_STATE_DIR so an
// isolated replay cannot write into the production state root.
const STATE_DIR = process.env.CLAUDE_STATE_DIR || path.join(HOME, '.claude', 'state');
const NO_EVENT_LOG = path.join(STATE_DIR, 'dispatcher-no-event.jsonl');

// --- Event registry ---
// Add new bundles as more hooks get refactored to export `run()`.
const EVENT_MAP = {
  'PreToolUse-default': [
    './session-init.js',
    './lazarus-heartbeat.js',
    '../skills/claude-power-pack/modules/harness/intent_lock.js',
  ],
  'PostToolUse-default': [
    // Cierra la miga de frontera: la herramienta COMPLETO, el turno sigue vivo.
    // Primero y baratisimo. Si esto no corre, la miga sobrevive y el proximo
    // prompt recibe una correccion de mas — ruido, nunca una sesion perdida.
    './turn-boundary-breadcrumb-close.js',
    // Mission hand-off wall, judged MID-TURN (spec vault/specs/mission-continuity.md).
    // The watchdog judges the wall at Stop; a mission worker works in one long turn, so the
    // wall was never judged while it mattered (W8: used_pct=39 vs 40 % wall, zero watchdog
    // lines). One fs.stat for every non-mission session. Pinned: tools/test_mission_wall.js.
    '../skills/claude-power-pack/hooks/mission_wall.js',
    // gsd-context-monitor.js RETIRADO de este carril 2026-09-15.
    // Es un hook VENDORED (upstream GSD, refs #3709/#2289/#4285) escrito para el
    // contrato STANDALONE: lee stdin y termina por allow()/crash(), que son
    // SALIDAS DE PROCESO (ON_CRASH = HOOK_ON_CRASH.ALLOW; ver su linea 296,
    // "allow(), not raw process.exit"). Su propio comentario (linea 539) lo dice:
    // "the stdin adapter ... must not run on require()". Este EVENT_MAP es el
    // carril in-process (linea 46) y el fichero nunca se refactorizo: exporta
    // solo {resolveThresholds, WARNING_THRESHOLD, CRITICAL_THRESHOLD}.
    // MEDIDO 2026-09-15: "module missing run() export" en CADA PostToolUse de
    // CADA repo -> 417 de las ultimas 3000 lineas del error log, 7.4 MB
    // acumulados, y el unico slot serie (DEFAULT_CONCURRENCY=1) quemado en cada
    // llamada a herramienta. Retirarlo no pierde funcionalidad: por esta via el
    // hook nunca llego a ejecutarse ni una sola vez, solo a lanzar.
    // NO le anadas un run() que delegue en handleStdinEnd: allow() haria
    // process.exit(0) a media cadena y truncaria EN SILENCIO los tres hooks
    // siguientes -- cambia un error ruidoso por una pantalla muerta nueva.
    // El aviso de contexto lleva muerto desde que se registro aqui. Si se quiere
    // de vuelta, va en un carril SPAWN (CHAIN_MAP), que es su contrato real.
    './session-logger.js',
    './dna-flywheel.js',
    './trace-emitter.js',
  ],
  'UserPromptSubmit-default': [
    './power-pack-reminder.js',
    './baseline-translator.js',
  ],

  // COMPANIONS IN-PROCESS de las tres cadenas PreToolUse ya registradas en
  // settings.json (Bash-chain, Edit-chain, Read-chain). El dispatcher ejecuta
  // '<fam>-default' junto a '<fam>-chain' via require, asi que abrir la miga
  // aqui cuesta ~0 procesos. Registrar un hook PreToolUse nuevo habria anadido
  // un cold-start de Node (~250 ms) A CADA LLAMADA A HERRAMIENTA, y la latencia
  // acumulada de la cadena es precisamente el cuelgue transversal que la miga
  // viene a cerrar. Cobertura honesta: Bash, PowerShell, Write, Edit, MultiEdit,
  // NotebookEdit, Read, Grep. NO cubre Agent ni WebFetch — esos no tienen cadena
  // de dispatcher hoy, y preferi cobertura parcial gratis a cobertura total que
  // empeora el sintoma.
  'PreToolUse-Bash-default': ['./turn-boundary-breadcrumb.js'],
  'PreToolUse-Edit-default': ['./turn-boundary-breadcrumb.js'],
  'PreToolUse-Read-default': ['./turn-boundary-breadcrumb.js'],
  // In-process (require-based) bundles only. The Stop event is handled by
  // CHAIN_MAP below instead: those hooks are heterogeneous (one is Python)
  // and not all export run(), so they run as sequential CHILD processes
  // spawned WITHOUT a shell (shell:false) — see runChain().
};

// --- Child-process chain registry (Windows fork-storm fix) ---------------
// Root cause this solves: registering N separate `type:"command"` hooks on
// ONE event makes Claude Code spawn N shell wrappers near-simultaneously.
// On Windows the shell is Git Bash; ≳3 concurrent msys2 forks collapse the
// mount-table init with `add_item("\??\C:\Program Files\Git","/") errno 1`
// (a fatal bash startup crash → the hooks never even run).
//
// Mitigation (durable): collapse the whole event into ONE dispatcher
// process; run each sub-hook here SEQUENTIALLY via spawnSync with
// shell:false, so NO bash.exe is ever spawned for a sub-hook. One event =
// one shell wrapper max (same as the already-stable Pre/PostToolUse path).
//
// `timeoutMs` is real milliseconds (Claude Code's per-hook `timeout` was
// authored inconsistently in settings.json; canonicalised here).
const NODE_EXE = process.execPath; // the very node.exe running this — Win path, no bash
// Portable Python fallback (gap 2 fix, audit 2026-05-19): the prior
// `C:/Users/User/AppData/Local/...` literal broke every host whose
// Windows username is not "User" and every POSIX host. Honest contract:
// derive from os.homedir() if a Windows-style Python install is present;
// otherwise fall back to the PATH-resolved `python3`/`python` so the
// hook fails at registration (settings_merger checks isfile) rather
// than silently at runtime. Explicit CLAUDE_PY_EXE always wins.
const PY_EXE = process.env.CLAUDE_PY_EXE || (function () {
  const winFallback = path.join(os.homedir(), 'AppData', 'Local',
    'Programs', 'Python', 'Python312', 'python.exe');
  try { fs.accessSync(winFallback, fs.constants.X_OK); return winFallback; }
  catch (_) { /* not present — defer to PATH-resolved interpreter */ }
  return process.platform === 'win32' ? 'python.exe' : 'python3';
})();

const CHAIN_MAP = {
  'Stop-chain': [
    // FIRST in the chain and cheap: kills the three dead-screen closer classes
    // (empty / passive-wait / intent-narration) before any heavy gate runs.
    // Fail-open ABSOLUTE, never blocks the same session twice consecutively.
    // Back-ported from LIVE 2026-08-31: it was wired into ~/.claude/hooks only,
    // so canonical was NOT a superset and a canonical->live copy would have
    // silently deleted the anti-dead-screen guard (T-HOOK-DISPATCHER-DRIFT-001
    // cuts both ways — the mirror is only safe once canonical contains both).
    // `critical` = runs before the pool opens, uncontended. See the PRIORITY
    // LANE block in runChain for the measurement that forced it. 8000 ms because
    // it now runs alone; solo it measures 644-1245 ms on a 7.6 MB transcript.
    { exe: NODE_EXE, script: './closer-guard.js', timeoutMs: 8000, block: true, critical: true },
    // Bounded autonomous TURN continuation (2026-09-19). SECOND, and critical,
    // for one reason: its whole value is that it reliably gets to speak at turn
    // end, and a member abandoned in the pool is indistinguishable from one that
    // decided to allow. It is cheap enough to belong in the critical lane --
    // statSync plus two small JSON reads, no subprocess, no git, no python --
    // which matters because this chain already measures ~54.9 s per turn end.
    //
    // AFTER closer-guard deliberately: a dead-screen closer is a defect in THIS
    // turn and must win over "carry on with the mission". The hook also reads
    // closer-guard's state read-only and stands down when it blocked, so the two
    // cannot ping-pong.
    //
    // OPT-IN: inert unless the session's autorun marker carries
    // `continuation: "stop-block"`. When this landed there were 11 markers on
    // disk, three still inside budget; none of them opt in, so registering it
    // changed nothing until a run is armed for the new path on purpose.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/gsd_stop_continuation.js', timeoutMs: 5000, block: true, critical: true },
    { exe: NODE_EXE, script: './zero-issue-gate.js', timeoutMs: 70000, block: true },
    { exe: NODE_EXE, script: './kobiiclaw-autoresearch.js', timeoutMs: 30000 },
    { exe: NODE_EXE, script: './trace-flusher.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: './session-summary.js', timeoutMs: 20000 },
    { exe: NODE_EXE, script: './scaffold-auditor.js', timeoutMs: 15000, block: true },
    { exe: NODE_EXE, script: './lazarus-snapshot.js', timeoutMs: 10000 },
    // TIMEOUT RAISED 6000 -> 20000 (2026-09-16). MEASURED by driving the real
    // tier-2 branch in-process with only `_spawn_daemon` stubbed (it types into
    // a Cursor window); checkpoint, telemetry, progress append and trigger flag
    // all ran for real: 3987 / 4026 / 4635 ms, a median of 4026 ms against the
    // old 6000 ms budget. That is 67% CONSUMED with the daemon spawn still
    // EXCLUDED (200-900 ms on this host), measured at a comparatively idle
    // 2781 MB free. The PRIORITY LANE note below records hooks with 4x headroom
    // dying under this very chain's fan-out; this one had 1.5x, and its cheap
    // path alone spread 629-3089 ms at 1114 MB free.
    //
    // A loss here is not a missing advisory: tier 2 IS the auto-compact step of
    // an unattended multi-hour /cpp-gsd-long run. Killed, it fails open with its
    // stdout discarded, the compaction never happens, and the run stalls --
    // the Owner's cross-repo hang wearing a different hat.
    //
    // PROMOTED TO THE CRITICAL LANE 2026-09-20. The note this replaces argued
    // that raising the timeout beat promoting it, and it closed by naming the
    // test: "Whether that is enough is now an observable, not an assumption:
    // logs/context-watchdog.log." The observable answered, and the answer is no.
    //
    // Measured on session 37cfb187 (an armed /cpp-gsd-long run with a 40 % wall):
    //   * its last judged turn was 2026-09-19T13:13 at used_pct=45 -- ABOVE its
    //     own wall, and `pass`, because a separate defect had removed the wall;
    //   * after the wall was restored the log recorded NOTHING for that session
    //     across many ended turns, while the same log kept judging other live
    //     sessions (240 lines that day, one of them a 53.8 MB transcript in
    //     1995 ms -- so this is not transcript size);
    //   * hook-dispatcher-errors.log, 10:27:26Z:
    //       [Stop-chain] context-watchdog.py Error: ETIMEDOUT after 20000ms
    //     and at 10:49:12 TEN members of this chain reported ETIMEDOUT inside
    //     8 ms of each other -- the signature of the whole chain being abandoned
    //     at its deadline, which takes the members that already finished with it.
    //
    // So the raise moved the cliff rather than removing it, exactly as the
    // estate's own doctrine says ("the fix is scheduling, not budget"), and the
    // run stalled for eleven hours with every gate green.
    //
    // The counter-argument was real and was measured rather than dismissed: the
    // lane runs sequentially on EVERY turn, so what matters is the ORDINARY
    // path. Timed alone against an 11.5 MB transcript at 3.5 GB free, n=5:
    // 463 / 1183 / 1523 / 3037 / 6823 ms, median 1523. Beside closer-guard
    // (644-1245 ms) and the cheap continuation hook, the lane stays ~3 s. That
    // is the price of the hook that decides whether an unattended run survives
    // its own context wall, against the measured alternative of it not running
    // at all. THIRD deliberately: a dead screen and a blocking continuation both
    // outrank compaction, and neither of those is what stalled this run.
    { exe: PY_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/context-watchdog.py', timeoutMs: 20000, critical: true },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/ram-watchdog.js', timeoutMs: 6000 },
    // ram-shield.js removed 2026-06-04: never existed (phantom ref produced a
    // recurring Stop-hook "script missing" error). ram-watchdog.js is the real one.
    { exe: NODE_EXE, script: './learning-sentinel.js', timeoutMs: 6000 },
    { exe: NODE_EXE, script: './vault-heartbeat.js', timeoutMs: 8000 },
    // --- Folded standalone Stop hooks (hub-fold 2026-06-04) ---------------
    // These were separate top-level settings.json Stop entries (9 spawns /
    // ~2 s). Folded here so the Stop event spawns ONE dispatcher (no
    // fork-storm). grep process.exit(2) over all of them is clean -> none
    // use the exit-code-2 block mechanism, so any blocking is via stdout
    // JSON which mergeOutputs already preserves -> block:false safe.
    // (auto-compact-stop-launcher.ps1 stays standalone: PowerShell, not part
    // of the node fork-storm.)
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/claude_md_linter_stop.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/mark-live-session.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: './research-intent-detector.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/background-verifier.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/jobs_woz_gate.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/jit_correlate_stop.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/session_snapshot_stop.js', timeoutMs: 10000 },
    // Wired 2026-07-20 (PP audit). Was built + documented as enforcing
    // HR-OUTPUT-001 but registered nowhere. Advisory only, block:false.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/output_contract_stop.js', timeoutMs: 8000 },
    // ADS auto-documentation (BL-ADS-001). Reads cwd from the Stop JSON,
    // diffs the working tree, writes docs/{prd,arch,constitution,changelog}
    // for CREATED/UPDATED modules. NEVER stages/commits; fail-open (always
    // exit 0) so it can never block Stop; block:false. timeoutMs:6000 caps
    // the git+AST work (audit gap #2). MINOR/DELETED are silent; a per-repo
    // docs/.ads-disabled file is the kill switch.
    { exe: PY_EXE, script: '../skills/claude-power-pack/tools/ads_sync.py', timeoutMs: 6000 },
    // GK-08 Session Writeback: re-index the current repo into the central graph
    // store at session close so this session's knowledge changes are navigable
    // next session (bounded: repos > 4000 md files defer to the scheduled
    // indexer --all). Fail-open, ALWAYS exit 0, never blocks Stop; closes the
    // WRITE->READ loop the GK-12 Graph-First gate reads from.
    { exe: PY_EXE, script: '../skills/claude-power-pack/modules/graphify/session_writeback.py', timeoutMs: 8000 },
    // Cross-project baseline (spec vault/specs/cross-project-baseline.md,
    // Owner option B 2026-08-31). Refreshes vault/ceps/promoted.jsonl from the
    // events THIS session wrote, so the next session in ANY project starts
    // with a current baseline. Reads ~68 KB, writes 4 records; safe to run
    // always, which is what "SIEMPRE" requires. Fail-open, never blocks Stop.
    { exe: PY_EXE, script: '../skills/claude-power-pack/tools/ceps_promote_stop.py', timeoutMs: 8000 },
    // FD-07 Fable Learning Flywheel (SCS C82 EXECUTION-mode): at a FRONTIER
    // session's close (kclaude exports PP_FRONTIER_SESSION=1) read this session's
    // captured deltas from the PM-03 bus, classify/triage/writeback each
    // idempotently to the deposits ledger (+ UKDL candidate / CO-05 asset side-
    // writes), and report loop health THROUGH CO-12 (no parallel metric). Gated on
    // PP_FRONTIER_SESSION -> a bare (non-kclaude) session is a silent no-op.
    // Fail-open, ALWAYS exit 0, never blocks Stop; rides this GK-08 Stop boundary
    // (no new plumbing, FD-07 I.4). Live only after Copy-Item canonical->live
    // (T-HOOK-DISPATCHER-DRIFT-001).
    { exe: PY_EXE, script: '../skills/claude-power-pack/modules/fable_distillation/fd_07_flywheel.py', timeoutMs: 8000 },
    // FIOS Token IRR (SCS C84 wiring): at a FRONTIER session's close, price this
    // session's accumulated deposits as R&D capital (assets / reuse / FDI / balance
    // sheet) and feed the IRR to CO-12 as one producer signal -- never a parallel
    // accountant. Gated on PP_FRONTIER_SESSION (same cadence as fd_07_flywheel); a
    // bare session's Stop is a silent no-op. Fail-open, ALWAYS exit 0, never blocks
    // Stop. Live only after Copy-Item canonical->live (T-HOOK-DISPATCHER-DRIFT-001).
    { exe: PY_EXE, script: '../skills/claude-power-pack/modules/frontier_intelligence/token_irr.py', timeoutMs: 8000 },
    // Session Delta Gate (2026-08-03): writes <cwd>/.claude/cache/learnings/ --
    // the input path learning-sentinel.js reads FIRST and that nothing in the
    // estate wrote, which is why LEARNINGS_PENDING.md had never been produced
    // and /cpp-compound was never auto-invoked. LAST in the chain deliberately:
    // it reads the working tree, so it must observe what earlier Stop children
    // (ads_sync docs, session_writeback) already wrote this turn. Detached +
    // unref inside the hook, so it returns in ~130 ms; fail-open, block:false.
    // Live only after Copy-Item canonical->live (T-HOOK-DISPATCHER-DRIFT-001).
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/session_delta_stop.js', timeoutMs: 8000 },
  ],

  // --- SessionEnd-chain (2026-09-15, Owner autorizo "sacar la contabilidad
  // de la frontera de turno") --------------------------------------------
  //
  // POR QUE EXISTE. Medido sobre hook-dispatcher-errors.log (7.4 MB, ventana
  // 2026-05-18 -> 2026-09-15): 15137 lineas ETIMEDOUT. Los tres primeros
  // ofensores del Stop-chain son CONTABILIDAD, no seguridad, y corrian en el
  // cierre de CADA turno de CADA repo:
  //     session_writeback.py   712 timeouts @ 8000 ms
  //     trace-flusher.js       488 timeouts @ 15000 ms
  //     ads_sync.py            418 timeouts @ 6000 ms
  // settings.json da al Stop un techo de 300 s, asi que la frontera de turno
  // puede quedarse parada minutos: eso es la pantalla congelada que el Owner
  // reporta de forma transversal. Un hook muerto en su deadline pierde su
  // stdout y la cadena informa EXACTAMENTE lo que informa un pase limpio.
  //
  // ORDEN: no es alfabetico ni estetico, es una cadena de dependencias que ya
  // estaba documentada en el Stop-chain y que hay que preservar entera:
  //   ads_sync + session_writeback  escriben en el arbol de trabajo
  //     -> session_delta_stop       LEE ese arbol (ver su nota "LAST in the
  //                                 chain deliberately" en el Stop-chain)
  //       -> learning-sentinel      LEE .claude/cache/learnings/ que produce
  //                                 session_delta_stop
  // Mover solo una parte rompe el pipeline de learnings EN SILENCIO: nada se
  // pondria rojo, simplemente LEARNINGS_PENDING.md dejaria de aparecer.
  //
  // INERTE HASTA QUE SE CABLEE. Nada invoca este evento todavia, asi que no
  // hay doble ejecucion. Para activarlo, el Owner (settings.json es suyo,
  // self-mod bloqueado para el agente) hace DOS cambios en el bloque
  // "SessionEnd" de ~/.claude/settings.json:
  //   1. anadir una entrada que invoque:
  //        node hook-dispatcher.js --event=SessionEnd-chain   (timeout: 120)
  //   2. BORRAR la entrada standalone de learning-sentinel.js, que ahora vive
  //      aqui dentro -- si se dejan las dos corre dos veces.
  // Solo DESPUES de eso se retiran del Stop-chain las cuatro entradas
  // duplicadas (doctrina de compactacion: aterrizar la superficie nueva con la
  // vieja todavia presente, y borrar la vieja en un paso posterior).
  //
  // Los timeouts son generosos a proposito: aqui ya no bloquean un turno, solo
  // el cierre de sesion, asi que el trabajo puede COMPLETARSE en vez de morir
  // a medias -- que es la diferencia entre un grafo indexado y uno a medio
  // escribir. Todos son fail-open / exit 0; ninguno lleva block:true.
  'SessionEnd-chain': [
    { exe: PY_EXE,   script: '../skills/claude-power-pack/tools/ads_sync.py', timeoutMs: 30000 },
    { exe: PY_EXE,   script: '../skills/claude-power-pack/modules/graphify/session_writeback.py', timeoutMs: 60000 },
    { exe: NODE_EXE, script: './trace-flusher.js', timeoutMs: 30000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/session_delta_stop.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: './learning-sentinel.js', timeoutMs: 15000 },
  ],

  // PreToolUse fork-storm fix (2026-05-21) — user explicitly authorized.
  // Root cause: settings.json registered 7 standalone PreToolUse hooks on
  // matcher=Bash and 9 on matcher=Edit|Write|*. Each `type:"command"`
  // entry makes Claude Code spawn a fresh git-bash MSYS2 wrapper; ≳3
  // concurrent forks collapse the mount-table init with `add_item errno 1`
  // (env_git_bash_fork_storm.md). Drift evidence: the user's OWN memory
  // file warned "NUNCA re-expandir hooks en settings.json" — but Owner
  // chose to add them anyway over time, and the cumulative count crossed
  // the danger threshold. Mitigation: collapse all per-matcher PreToolUse
  // hooks into these chains; settings.json then registers ONE dispatcher
  // entry per matcher. Same shell:false spawnSync model the Stop-chain
  // has used since 2026-05-15 — proven fork-storm-safe in production.
  'PreToolUse-Bash-chain': [
    // Folded standalone PreToolUse Bash guard (PreToolUse-fold 2026-06-07).
    // Was a top-level matcher=Bash settings.json entry; blocks git/mix/gh/npm/
    // pnpm/corepack via Bash on Windows (emits {decision:"block"} + exit 2 --
    // both now honored by runChain/mergeOutputs). Matcher Bash == chain matcher
    // Bash, so folding loses no coverage. Live-relative path (lives in
    // ~/.claude/hooks, same convention as the Stop-chain ./ entries).
    // `critical`: this guard timing out is the Owner's cross-repo MSYS2 freeze.
    // It failed open 12,237-timeouts-deep into a log nobody reads. Priority lane.
    { exe: NODE_EXE, script: './windows-bash-bridge-guard.js', timeoutMs: 8000, block: true, critical: true },
    // Blocks launching a packaged desktop build as a child of this shell. The app then inherits
    // the Owner's console and prints its diagnostics into their working pane for as long as it
    // runs -- Orca's (already rate-limited) `[pty] hidden-delivery gate ...` line landed there on
    // 2026-09-08. `Start-Process` does NOT detach it; `explorer.exe <path>` re-parents it. This
    // chain's settings matcher is "Bash|PowerShell" despite the chain's name, so PowerShell
    // launches -- the ones that actually caused it -- are covered.
    { exe: NODE_EXE, script: './gui-app-console-inherit-guard.js', timeoutMs: 5000, block: true },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/process-sandbox.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/ovo-push-gate.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/skill-heat-map-advisor.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './quality-skill-gate.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/rtk-core/rtk-rewrite.js', timeoutMs: 10000 },
    // GK-12 Graph-First advisory (level-2, NEVER blocks): nudges toward a graph
    // query before a Bash filesystem search (grep/find/ls). Fail-open; no block.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/graph_first_gate.js', timeoutMs: 4000 },
    // HR-CASCADE-001/002 wiring fix (CGF Phase 2, Workstream A, 2026-07-22): this
    // file existed and was fully correct (fail-open, stdin-piped, no shell
    // injection) but was never registered anywhere -- absent from settings.json
    // AND from this dispatcher's chain map, so the 5 sealed cascade_prevention
    // Hard Rules had zero live enforcement.
    //
    // 2026-09-04 -- SHAPE CORRECTED. This comment used to prescribe
    // {continue:false, stopReason}. That shape does not deny a TOOL, it HALTS
    // THE AGENT: the turn ends at the tool boundary with no assistant text, and
    // the Stop chain never runs, so closer-guard.js (SILENT_TOOL_STOP) cannot
    // see it. Measured as the cross-repo dead screen. Both this gate and
    // secret_firewall_gate.js now deny via
    // hookSpecificOutput.permissionDecision:'deny' -- the SAME shape this file
    // synthesises for exit-2 gates ~400 lines below, and the shape whose
    // recovery is already proven in practice by R1 anti-thrash. Enforcement is
    // identical; only the dead screen is gone. Do NOT reintroduce
    // {continue:false} in a per-tool safety gate: it means "stop the agent",
    // which is never what such a gate intends.
    // Two-way proof: hooks/_tests/test-cascade-deny-and-heredoc.js (8/8).
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/cascade_check_bash.js', timeoutMs: 5000 },
  ],
  'PreToolUse-Edit-chain': [
    // SECURITY FIX (2026-06-04, Owner-authorized "Wire firewall + fix
    // dispatcher block-bug"): wire the HR-SECRET-001 firewall into the
    // already-registered Edit-chain. Investigation found secret_firewall_gate.js
    // was BUILT but NEVER registered -- absent from settings.json AND from the
    // loose ~/.claude/hooks dir -> the secret firewall was INACTIVE. The legacy
    // secret-scanner below blocks via stderr + exit(2); pre-fix runChain
    // swallowed that, post-fix it is honored too. secret_firewall_gate blocks
    // via {continue:false}, preserved by mergeOutputs. Verified: secret passes
    // pre-fix, blocks post-fix.
    // `critical` (2026-09-15): these two ARE the HR-SECRET-001 boundary, and a
    // timeout here fails OPEN -- the write lands with the credential in it and
    // nothing surfaces. MEASURED in the last 3000 lines of hook-dispatcher-errors.log:
    // secret_firewall_gate 31 ETIMEDOUT, secret-scanner 24, every one of them a
    // timeout rather than a logic error. They are not slow: secret-scanner's
    // ISOLATED median is 228 ms against a 5000 ms budget. They die because the host
    // is starved (844 MB free of 32 GB when this was measured), and under starvation
    // a 228 ms spawn takes longer than any budget you can write.
    //
    // The lane stays SMALL on purpose -- widen it and it becomes the pool, which
    // test-priority-lane.js V-PL-POOL-STILL-CONCURRENT exists to refuse. The line
    // that decides membership: a guard whose silent failure is UNSAFE, never one
    // whose silent failure is merely noisy. anti-thrash and the advisories below
    // are noisy; these two and the two anti-hang guards are unsafe.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/secret_firewall_gate.js', timeoutMs: 8000, critical: true },
    { exe: NODE_EXE, script: './secret-scanner.js', timeoutMs: 8000, critical: true },
    { exe: NODE_EXE, script: './quality-gate.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './anti-thrash.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './readonly-prompts-guard.js', timeoutMs: 3000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/skill-heat-map-advisor.js', timeoutMs: 5000 },
    // TIMEOUT RAISED 5000 -> 9000 (2026-09-04). MEASURED: this hook takes ~5,094 ms
    // against a 5,000 ms budget, so it was killed mid-flight on essentially every
    // invocation -- which is what filled hook-dispatcher-errors.log with
    // `spawnSync ETIMEDOUT` for this exact script. A gate that always times out is
    // not a gate: its stdout never reaches mergeOutputs, so it charged ~5 s on EVERY
    // Edit/Write while contributing no protection whatsoever.
    //
    // Generalises: A HOOK WHOSE RUNTIME EXCEEDS ITS OWN TIMEOUT IS INERT AND
    // INVISIBLE -- full price, no result, and no failure surfaced anywhere the agent
    // reads. Budget every gate against a MEASURED runtime, never a guessed one.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/zero-fiction-gate.js', timeoutMs: 9000 },
    { exe: NODE_EXE, script: './jobs-woz-gatekeeper.js', timeoutMs: 20000 },
    // Folded standalone PreToolUse Edit guards (PreToolUse-fold 2026-06-07).
    // Were top-level matcher=Write|Edit|MultiEdit entries (a subset of this
    // chain's Write|Edit|MultiEdit|NotebookEdit matcher -> only EXPANDS to
    // NotebookEdit, no coverage loss; both are inert on non-target paths).
    // uqf_pre_edit_gate = advisory only (.py AST hints via additionalContext);
    // claude_md_firewall = DENY via hookSpecificOutput.permissionDecision when a
    // Write/Edit/MultiEdit would push ~/.claude/CLAUDE.md >= 40000 chars. Both
    // survive mergeOutputs (HSO shallow-merge keeps permissionDecision:deny).
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/uqf_pre_edit_gate.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/claude_md_firewall.js', timeoutMs: 8000, block: true },
    // CDIO I4 design gate (2026-07-13): on a Write/Edit to a visual surface
    // (frontend ext, or a landing/dashboard/component/hero filename), RUN
    // tools/design_gate.py against the project's DESIGN.md. Two tiers:
    //   - project HAS a DESIGN.md -> it adopted the system, so slop against its own
    //     declared system is refusable: DENY on BLOCK (needs block:true to survive
    //     mergeOutputs, same as claude_md_firewall above).
    //   - project has NO DESIGN.md -> never opted in: advise, never deny.
    // A BLOCK is never throttled (the 15-min throttle covers only the advisory).
    // Fail-open absolute: no python / spawn error / timeout / bad JSON -> {}.
    // Was advisory-only under SCS C78; a gate you must remember to invoke is not a
    // gate (T-DESIGN-SLOP-001). timeoutMs raised for the python child.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/cdio_visual_advisory.js', timeoutMs: 10000, block: true },
  ],
  'PreToolUse-Read-chain': [
    { exe: NODE_EXE, script: './gatekeeper-semantic.js', timeoutMs: 3000 },
    { exe: NODE_EXE, script: './anti-thrash.js', timeoutMs: 5000 },
    // GK-12 Graph-First advisory (level-2, NEVER blocks): the Read|Grep matcher
    // catches Grep, the primary file-exploration tool. Fail-open; no block flag.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/graph_first_gate.js', timeoutMs: 4000 },
  ],
  // SessionStart fold (2026-09-22, Jacobo). These three were SEPARATE top-level
  // settings.json registrations, so the harness paid a process spawn for each
  // with NO pooling and NO deadline -- the one event family that had neither.
  // Measured serially on an idle disk: 712 + 465 + 1422 = 2,599 ms. On the disk
  // state that produced the Owner's report (0 % idle, a no-op node spawn costing
  // 965 ms) the same three cost multiples of that, which is the "abro un pane
  // nuevo y tarda muchisimo" half of the complaint.
  //
  // All three were READ before folding and all three are ADVISORY -- no
  // `continue:false`, no block decision -- which is the precondition for giving
  // this chain a deadline at all (see CHAIN_DEADLINE_MS: safe on an advisory
  // chain, a security regression on a blocking one).
  //
  // DELIBERATELY NOT FOLDED: the Orca hook (cmd.exe -> %USERPROFILE%\.orca\
  // agent-hooks\claude-hook.cmd). It belongs to another product; folding a third
  // party's integration into this estate's dispatcher would make Orca's startup
  // depend on a file Orca does not own. It keeps its own registration.
  //
  // host-memory-floor is CRITICAL: it is the guard for the host-starvation class
  // this estate has already paid for repeatedly, so it runs first and uncontended
  // rather than competing in the pool for a slot it might not get.
  'SessionStart-chain': [
    { exe: NODE_EXE, script: './host-memory-floor.js', timeoutMs: 5000, critical: true },
    { exe: NODE_EXE, script: './learning-sentinel.js', timeoutMs: 3000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/session_start_hub.js', timeoutMs: 10000 },
  ],
  // UserPromptSubmit standalone fold (hub-fold 2026-06-04). The EVENT_MAP
  // 'UserPromptSubmit-default' bundle (power-pack-reminder + baseline-
  // translator) stays in-process; these 3 were separate top-level entries.
  // jit_skill_loader is Python -> PY_EXE child. grep exit(2) clean.
  'UserPromptSubmit-chain': [
    // DEAD-CLOSER RECOVERY (2026-09-14, Jacobo). closer-guard.js is a Stop hook,
    // and a turn that follows a USER INTERRUPT does not reach the Stop chain --
    // measured: the guard BLOCKS the dead turn's exact bytes on replay, and its
    // heartbeat never advanced across that turn. So the guard was correct and
    // unreachable in precisely its highest-value case. This is the same event
    // trap the file already carries for {continue:false} at ~line 234: CHECK A
    // HOOK'S EVENT BEFORE ITS LOGIC. Runs FIRST so the correction reaches the
    // model ahead of the other advisories. Never blocks the user's prompt.
    { exe: NODE_EXE, script: './dead-closer-recovery.js', timeoutMs: 6000, critical: true },
    { exe: NODE_EXE, script: './correction-guard.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: './prd-keyword-sentinel.js', timeoutMs: 8000 },
    // GSD X ambient applicability (2026-09-16, Jacobo). Computes the ExecutionOS
    // Lite tier from the prompt's measured evidence instead of leaving it to the
    // model's self-assessment, so the posture stops depending on the operator
    // remembering to ask for it. Registered ONLY after reachability was proven:
    // this path is resolved as path.join(__dirname, script) -> the repo checkout
    // at ~/.claude/skills/claude-power-pack, which IS the main git worktree and
    // not a copy, so a committed file is live-served with no install step. The
    // same relative form already carries 31 other repo-owned hooks on this host.
    //
    // NOT critical: it is advisory, so it must not sit in the lane reserved for
    // guards whose absence is the harm. Silence is a VALID result -- a prompt
    // needing no escalation emits nothing -- so the evidence that it ran is its
    // heartbeat, never its stdout. Kill switch: CLAUDE_GSDX=off.
    // Measured child ~1.2-1.4 s against this chain's 11500 ms deadline.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/gsd_x_tier.js', timeoutMs: 8000 },
    // D2A duplicate advisory (SCS C85 addendum, level-2 — NEVER blocks). Fires only
    // when the prompt PROPOSES CREATING a new system/dataset; spawns the engine
    // (python child) and surfaces the DUPE VERDICT + BUILD CONTRACT before Claude
    // builds. Silent on novel proposals and on use/extend/fix. Fail-open absolute.
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/d2a_gate.js', timeoutMs: 12000 },
    { exe: PY_EXE, script: '../skills/claude-power-pack/tools/jit_skill_loader.py', timeoutMs: 12000 },
  ],
  // CHAIN DEADLINE DRILL (2026-09-15). Registered in NO settings.json event, so it
  // is inert in production and can only be driven by
  //   node hook-dispatcher.js --event=__deadline-drill-chain
  // Synthetic subject by design: it represents the CLASS (fast critical guard +
  // slow straggler) rather than today's offender, so it keeps asserting on the day
  // jit_skill_loader gets fast and cannot be fixed out from under the assertion.
  // Driven by hooks/tests/test-chain-deadline.js, both poles.
  // Named for the REAL family on purpose: familyOf() matches by prefix, so this
  // drill travels the same additionalContext routing the production chain uses.
  // A drill on a synthetic family name proved only that stranded text lands in
  // systemMessage, which is not the claim.
  'UserPromptSubmit-deadline-drill-chain': [
    { exe: NODE_EXE, script: './tests/fixtures/drill-fast-critical.js', timeoutMs: 5000, critical: true },
    { exe: NODE_EXE, script: './tests/fixtures/drill-slow-straggler.js', timeoutMs: 25000 },
  ],
  // Positive control for the same drill: identical shape, everything in budget.
  // Carries NO CHAIN_DEADLINE_MS entry, so it takes the wait-for-everything path
  // and proves the pool still delivers -- otherwise a dispatcher that dropped
  // every pooled hook unconditionally would pass the red case and look correct.
  'UserPromptSubmit-deadline-drill-control-chain': [
    { exe: NODE_EXE, script: './tests/fixtures/drill-fast-critical.js', timeoutMs: 5000, critical: true },
    { exe: NODE_EXE, script: './tests/fixtures/drill-pooled-fast.js', timeoutMs: 5000 },
  ],
  // R269: the CRITICAL LANE ALONE eats the budget -- the starved-host case. Shares
  // CHAIN_DEADLINE_MS with the drill chain above (1500 ms) while its critical step
  // burns 2200 ms, so `left <= 0` by the time the pool is considered and the pool
  // must NEVER BE OPENED. The pooled member writes a filesystem sentinel, because
  // spawned-then-reaped and never-spawned produce identical stdout and an output
  // assertion cannot tell the pre-fix dispatcher from the post-fix one.
  // Step timeouts stay well above the deadline so the DEADLINE is always the actor.
  'UserPromptSubmit-deadline-drill-critstarve-chain': [
    { exe: NODE_EXE, script: './tests/fixtures/drill-slow-critical.js', timeoutMs: 9000, critical: true },
    { exe: NODE_EXE, script: './tests/fixtures/drill-spawn-sentinel.js', timeoutMs: 9000 },
  ],
  // PostToolUse matcher=Bash standalone fold (hub-fold 2026-06-04). Post-hoc
  // hooks; none block. kg-sync-hook (matcher Write|Edit) stays standalone.
  'PostToolUse-Bash-chain': [
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/tty-restore.js', timeoutMs: 6000 },
    { exe: NODE_EXE, script: './bug-hunter-learning.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/osa_deploy_detector.js', timeoutMs: 8000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/bug-hunter-ceps-bridge.js', timeoutMs: 8000 },
  ],
};

// --- Per-chain concurrency (LATENCY FIX 2026-09-04) -----------------------
// SEQUENTIAL (1) was the original contract and remains the DEFAULT: a chain whose
// hooks share mutable state must never interleave.
//
// WHY THIS MAP EXISTS -- measured on this host, real transcript, each chain driven
// exactly as the harness drives it and wall-clocked:
//   Stop-chain              54,907 ms   (fires on EVERY turn-end)
//   PreToolUse-Edit-chain    ~10,000 ms (fires on EVERY Edit/Write)
//   PreToolUse-Bash-chain     ~5,800 ms
//   PreToolUse-Read-chain     ~1,400 ms
// Sequential spawnSync makes a chain cost SUM(hooks), never MAX(hooks). A session
// with 50 edits + 100 reads + 30 shell calls paid ~13.5 MINUTES of pure hook
// overhead on top of ~55 s at every turn-end. The Owner reported this cross-repo as
// "se queda colgado" and the estate spent months attributing it to the MSYS2 Bash
// bridge. It was never Bash. It is this loop -- and because ~/.claude/hooks is
// host-wide, it reproduced in EVERY repository, which was itself the clue: a symptom
// present in all repos lives in what all repos SHARE.
//
// Only chains whose hooks are independent reporters/gates are raised; each was
// checked for shared-file writes and they write distinct paths. Bounded, not
// unbounded: the whole point of the 2026-05-21 fold was to stop a fork storm, and
// ~25 concurrent spawns would recreate the exact failure this dispatcher prevents.
// 4 holds the spawn ceiling at the old per-matcher level while cutting wall time to
// roughly SUM/4.
// Tuned by measurement, not taste. The 2026-05-21 fork-storm that motivated the
// fold was an MSYS2 bash mount-table collapse -- it needed BASH wrappers, and every
// spawn here is `shell:false`, so no bash.exe is ever created. The real ceiling is
// therefore memory (~40 MB per node child), not the mount table. Stop-chain carries
// ~25 hooks so it gets the widest lane; the per-tool-call chains are shorter and
// fire far more often, so they stay narrower to keep peak spawn count low.
const CHAIN_CONCURRENCY = {
  'Stop-chain': 8,
  // 3 members, so 3 slots: the pool is never the constraint here, the spawns are.
  // The critical member runs ahead of the pool regardless, so this governs the
  // two advisory ones only.
  'SessionStart-chain': 3,
  // UserPromptSubmit-chain had NO entry, so it fell to DEFAULT_CONCURRENCY = 1 and
  // cost SUM. See CHAIN_DEADLINE_MS directly below for the measurement that forced
  // both this line and the deadline: sequential, this chain overran the harness
  // ceiling on an ORDINARY prompt and every injection it produced was discarded.
  'UserPromptSubmit-chain': 4,
  'PreToolUse-Edit-chain': 6,
  'PreToolUse-Bash-chain': 4,
  'PreToolUse-Read-chain': 3,
  'PostToolUse-Bash-chain': 4,
};
const DEFAULT_CONCURRENCY = 1;

// --- SCRATCHPAD FAST PATH (2026-09-15, Jacobo) -----------------------------
// MEASURED on this host: ONE Write costs 26,734 ms of chain work sequentially
// (21,937 ms observed at concurrency 6), because the Edit chain spawns ELEVEN
// node processes and each pays interpreter startup on a host with 757 MB free
// of 32 GB. No member exceeds its own budget -- the chain is simply big, and
// about 5.5 s of it is interpreter startup before any hook logic runs. The
// Owner hit this writing a 49-line commit message into the session scratchpad
// and reported it as a hang, which is what 22 s before a text file appears
// looks like from the outside.
//
// Most of that chain judges PROJECT DELIVERABLES: fiction in shipped code,
// conformance to a design system, Python AST hints, the size of CLAUDE.md. A
// throwaway file under the harness's own per-session scratchpad is none of
// those BY CONSTRUCTION -- that directory is handed out precisely for files
// that are not project artifacts.
//
// THE LINE IS THE SAME ONE THE PRIORITY LANE DRAWS: skip a STYLE gate on a
// file that cannot have the style problem, never a SAFETY gate. Both
// HR-SECRET-001 gates keep running here (`critical`), because a credential
// pasted into a scratch file is still a credential, and so does anti-thrash.
const SCRATCH_ALWAYS = new Set([
  './anti-thrash.js',
]);

// A path under the harness's per-session scratchpad. Deliberately requires
// BOTH segments: a project directory would have to live inside the OS temp
// tree under `claude/` to be mistaken for one, and the `scratchpad` segment is
// the harness's own name for it. Fail-open ABSOLUTE -- anything unparseable,
// absent or unexpected returns false and the full chain runs, as before.
function isScratchTarget(rawStdin) {
  try {
    // Strip a leading UTF-8 BOM before parsing. PowerShell 5.1 prepends one when
    // it pipes a string to a native exe (~/.claude/CLAUDE.md documents the same
    // trap against ssh), and JSON.parse THROWS on it -- which lands in the catch
    // below and returns false, i.e. the filter silently switches itself off and
    // the full chain runs. Measured: 204 bytes sent, 207 received, scratch=false
    // on a path the predicate matches perfectly in isolation. A guard that fails
    // open on an invisible three-byte prefix is the estate's favourite defect.
    const d = JSON.parse((rawStdin || '{}').replace(/^\uFEFF/, ''));
    const ti = d && d.tool_input;
    if (!ti) return false;
    const p = ti.file_path || ti.notebook_path;
    if (typeof p !== 'string' || !p) return false;
    const norm = p.replace(/\\/g, '/').toLowerCase();
    return norm.includes('/temp/claude/') && norm.includes('/scratchpad/');
  } catch (_) {
    return false;
  }
}

// --- CHAIN DEADLINE (2026-09-15, Jacobo) ----------------------------------
// The harness gives each registered hook command a timeout in settings.json. A
// dispatcher killed AT that deadline loses ALL of its stdout, and the chain then
// reports EXACTLY what a clean pass reports -- the failure mode this file already
// documents for individual hooks, one level up, where it takes the whole chain.
//
// MEASURED on this host, real payload, driven as the harness drives it:
//   UserPromptSubmit-chain  15,173 ms   vs a 15,000 ms ceiling  -> killed, output lost
//   per-hook: dead-closer-recovery 2,181 | correction-guard 2,713
//             prd-keyword-sentinel 2,856 | d2a_gate 3,386 | jit_skill_loader 11,354
//
// So `dead-closer-recovery` finished its rescue at 2.2 s and had its output held
// hostage by a hook taking five times longer. It logged fired:true, it SPENT its
// one-shot crumb, and the FRONTERA DE TURNO text reached nobody -- which is the
// third rung of rules/guard-event-reachability.md: a guard that fires and cannot
// be heard. Every UserPromptSubmit injector in this estate was mute the same way
// (AKOS, power-pack-reminder, jit_skill_loader), while PreToolUse injectors on the
// same dispatcher arrived fine. That sibling contrast is what acquits the harness.
//
// Concurrency alone was NOT enough: it lands ~13.6 s against 15 s, a 9% margin on
// a host whose load varies, and it leaves the hostage relationship intact. The
// deadline removes it -- critical hooks run first and uncontended, and whatever
// has settled is EMITTED even if the rest is still running. Stragglers are
// abandoned and REAPED (see LIVE_CHILDREN), never orphaned.
//
// Values are the settings.json timeout MINUS a margin for merge+write+exit.
// A chain with no entry keeps the old behaviour: wait for everything.
// ONE ENTRY, DELIBERATELY. The first version of this table also carried the three
// PreToolUse chains at 8500 ms, on a ceiling I had ASSUMED rather than measured.
// Driven for sixty seconds it produced, repeatedly:
//   [PreToolUse-Edit-chain] CHAIN-DEADLINE-ABANDONED before pool
//       critical lane used 10845ms of 8500ms
//   [PreToolUse-Bash-chain] CHAIN-DEADLINE-ABANDONED after 8500ms
//       still running: quality-skill-gate, rtk-rewrite, graph_first_gate, ...
// i.e. the CRITICAL lane alone overran the budget, and the abandoned members
// included zero-fiction-gate and quality-skill-gate. On those chains the critical
// lane IS the HR-SECRET-001 boundary (secret_firewall_gate, secret-scanner) and a
// block:true gate that is abandoned FAILS OPEN -- the write lands with the
// credential in it. A deadline is safe on an ADVISORY chain and is a security
// regression on a BLOCKING one, and no measurement justified adding them.
// Any future entry here needs its own wall-clock measurement AND an argument
// about what failing open on that chain costs.
const CHAIN_DEADLINE_MS = {
  // 2026-09-22 (Jacobo). SessionStart had NO deadline at all, because it had no
  // chain -- three separate registrations, each spawning its own node, none of
  // them bounded by anything but its own per-hook timeout (5 + 3 + 10 = 18 s of
  // worst case with nothing to cap the sum).
  //
  // The measurement AND the argument this table demands: serially on an idle disk
  // the three cost 712 + 465 + 1422 = 2,599 ms, so 4000 leaves real headroom on a
  // healthy host and bounds the pathological one. All three members were read and
  // are ADVISORY, so an abandoned member costs a missing injection and never an
  // enforcement that failed open -- which is the distinction that makes a deadline
  // legitimate here and illegitimate on the PreToolUse chains below.
  //
  // What this does NOT fix: the harness still spawns this dispatcher, and a spawn
  // on a saturated disk measured 965 ms for a no-op. A deadline bounds the wait;
  // it cannot make a spawn cheap.
  'SessionStart-chain': 4000,
  // 2026-09-22 (Jacobo): 11500 -> 3000. The old value was headroom under the 15 s
  // harness ceiling, which is the right question for "does the injection survive"
  // and the WRONG one for "how long does the Owner stare at a pane that will not
  // react".
  //
  // Measured this day, real dispatcher, real payload: an ordinary prompt cost
  // 13,543 ms cold / 4,408 ms warm, and a PASTED 10 KB prompt cost 11,611 and
  // 11,820 ms -- it consumed the ENTIRE deadline every time, with no warm-up
  // benefit. The report was "pego prompts y directamente ni reacciona".
  //
  // The cost is NOT hook logic. Timed individually the members run 0.5-1.7 s. It is
  // SIX PROCESS SPAWNS on a host whose C: drive measured 0% idle time (724 IOPS,
  // driven by another session's `ucr_cif_oracle.py --sessions 573`), where a no-op
  // `node -e "0"` costs 965 ms and `python -c pass` costs 2-4 s. Defender was
  // measured and EXONERATED (0.00 s of MsMpEng CPU across 15 spawns) and the CPU
  // was not saturated (~4.2 of 16 cores), so neither is available as the excuse.
  //
  // A deadline cannot make a spawn cheap. What it CAN do is bound what the Owner
  // waits for, and this chain is ADVISORY -- the paragraph above is explicit that a
  // deadline is safe here and a security regression on a blocking one. The critical
  // lane (dead-closer-recovery, measured 520 ms) runs first and uncontended, so it
  // is unaffected; what a busy host now drops is advisory injection, which was
  // costing ~29 KB of context on EVERY prompt anyway.
  'UserPromptSubmit-chain': 3000,
  'UserPromptSubmit-deadline-drill-chain': 1500,  // drill only; in no settings.json event
  'UserPromptSubmit-deadline-drill-critstarve-chain': 1500,  // drill only; critical lane overruns it alone
};

// Why a deadline log carries the host reading: a chain that overran because the
// host had 0.67 GB free and a chain that overran because a hook regressed need
// opposite fixes, and after the fact the evidence is gone. Recorded at the moment
// of the overrun, the two stop reading alike. Never throws and never blocks --
// a diagnostic that can break the dispatcher is worse than no diagnostic.
function hostPressure() {
  try {
    const os = require('os');
    const freeMB = Math.round(os.freemem() / 1048576);
    const totMB = Math.round(os.totalmem() / 1048576);
    const pct = totMB ? Math.round((1000 * freeMB) / totMB) / 10 : -1;
    return 'host free=' + freeMB + 'MB/' + totMB + 'MB (' + pct + '%)'
      + (pct >= 0 && pct < 5 ? ' STARVED -- hook timeouts here are host, not code' : '');
  } catch (_) {
    return 'host unknown';
  }
}

// One sub-hook as a shell-free child process. Resolves (never rejects) to a
// spawnSync-SHAPED record {status, stdout, stderr, error} so the ordered reducer
// below is byte-for-byte the logic the sequential version used.
// Every child currently in flight. Exists so the CHAIN DEADLINE below can ABANDON
// a straggler without ORPHANING it: process.exit(0) does not reap children, and
// this estate has already paid for that once -- 168 node.exe alive with a dead
// parent and kernelMs=userMs=0, i.e. created and never resumed, which is
// indistinguishable from a clean finish (memory: never-resumed-grandchild-leak).
// An abandoned hook must die, not linger.
const LIVE_CHILDREN = new Set();

function reapLiveChildren() {
  for (const c of LIVE_CHILDREN) {
    try { c.kill(); } catch (_) { /* already gone */ }
  }
  LIVE_CHILDREN.clear();
}

function runStep(step, rawStdin) {
  return new Promise((resolve) => {
    const abs = path.join(__dirname, step.script);
    let stdout = '';
    let stderr = '';
    let settled = false;
    const done = (res) => {
      if (settled) return;
      settled = true;
      if (child) LIVE_CHILDREN.delete(child);
      resolve(res);
    };

    let child;
    try {
      child = spawn(step.exe, [abs], { shell: false, windowsHide: true });
      LIVE_CHILDREN.add(child);
    } catch (e) { return done({ error: e, status: null, stdout: '', stderr: '' }); }

    // Mirror spawnSync's `timeout`: kill the child and surface an ETIMEDOUT error.
    const timer = setTimeout(() => {
      try { child.kill(); } catch (_) { /* already gone */ }
      done({ error: new Error('ETIMEDOUT after ' + step.timeoutMs + 'ms'), status: null, stdout, stderr });
    }, step.timeoutMs);

    const CAP = 8 * 1024 * 1024;               // same ceiling as the old maxBuffer
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (d) => { if (stdout.length < CAP) stdout += d; });
    child.stderr.on('data', (d) => { if (stderr.length < CAP) stderr += d; });
    child.on('error', (e) => { clearTimeout(timer); done({ error: e, status: null, stdout, stderr }); });
    child.on('close', (code) => { clearTimeout(timer); done({ error: null, status: code, stdout, stderr }); });

    // A hook that exits before reading stdin makes this EPIPE. Normal; it must not
    // take the dispatcher down with it.
    try {
      child.stdin.on('error', () => { /* EPIPE: child closed stdin early */ });
      child.stdin.end(rawStdin);
    } catch (_) { /* fail-open */ }
  });
}

// Bounded worker pool. Results land at their ORIGINAL index so downstream merge
// order is identical to the sequential run regardless of completion order.
// mergeOutputs is last-wins per key, so a reordered outputs[] would silently change
// WHICH hook's `reason` survives -- determinism here is load-bearing, not tidiness.
async function runPool(items, limit, worker) {
  const results = new Array(items.length);
  let next = 0;
  const lanes = new Array(Math.max(1, Math.min(limit, items.length))).fill(0).map(async () => {
    for (;;) {
      const i = next++;
      if (i >= items.length) return;
      results[i] = await worker(items[i]);
    }
  });
  await Promise.all(lanes);
  return results;
}

// Run a chain of sub-hooks as shell-free child processes, up to N concurrently.
// Returns { outputs:[parsedJSON], blocked:bool, blockStderr:string }.
async function runChain(event, chain, rawStdin) {
  const chainStart = Date.now();   // CHAIN DEADLINE clock; see CHAIN_DEADLINE_MS
  // The harness's cap starts at PROCESS SPAWN. This clock starts HERE. Node
  // startup, module load and reading stdin are spent against the cap and are
  // invisible to the deadline, so the real budget is cap - startup - flush,
  // never cap. Unmeasured, that gap is what makes a chain overrun a cap it
  // appears to fit inside. Reported on the debug line below, so it costs
  // nothing unless someone is asking.
  const startupMs = Math.round(process.uptime() * 1000);
  const outputs = [];
  let blocked = false;
  const blockStderr = [];

  // SCRATCHPAD FAST PATH (2026-09-15, Jacobo). See SCRATCH_ALWAYS above for the
  // measurement and the rule: skip a STYLE gate on a file that cannot have the
  // style problem, never a SAFETY gate. Fail-open: unparseable -> full chain.
  const scratch = isScratchTarget(rawStdin);

  // Pre-flight exactly as before: a missing script/interpreter is logged and
  // skipped rather than spawned.
  const runnable = [];
  for (const step of chain) {
    if (scratch && !step.critical && !SCRATCH_ALWAYS.has(step.script)) continue;
    const abs = path.join(__dirname, step.script);
    if (!fs.existsSync(abs)) { logError(event, step.script, new Error('script missing')); continue; }
    if (!fs.existsSync(step.exe)) { logError(event, step.script, new Error('interpreter missing: ' + step.exe)); continue; }
    runnable.push(step);
  }

  // --- CHAIN OBSERVABILITY (2026-09-15, Jacobo) ----------------------------
  // The scratchpad filter above could not be verified by TIMING on this host: a
  // scratchpad run measured 12,438 ms against a project run's 7,925 ms -- the
  // wrong way round, because at 753 MB free the variance swamps the signal
  // (identical no-op payloads measured 2,870 / 5,335 / 3,580 ms earlier today).
  // Output could not discriminate either: both runs emitted the same 17 bytes,
  // because a synthetic payload never reaches the advisory hooks that speak.
  //
  // So rather than guess, build the instrument. One line on stderr, behind an
  // env var so it is silent in normal operation, naming WHAT WAS ACTUALLY GOING
  // TO RUN. That is load-independent: it answers "did the filter fire?" without
  // a clock, and it keeps answering it for every future change to this chain.
  // rules/instrument-before-claim.md -- a reading that could only come back one
  // way carries no information; this one can come back either way.
  if (process.env.CLAUDE_DISPATCH_DEBUG) {
    process.stderr.write(
      '[dispatch] ' + event +
      ' raw=' + (rawStdin ? rawStdin.length : 0) + 'B' +
      ' scratch=' + scratch +
      ' startup=' + startupMs + 'ms' +
      ' deadline=' + (CHAIN_DEADLINE_MS[event] || 0) + 'ms' +
      ' runnable=' + runnable.length + '/' + chain.length +
      ' [' + runnable.map((s) => s.script.split('/').pop()).join(',') + ']\n'
    );
  }

  // --- PRIORITY LANE (2026-09-14, Jacobo) ----------------------------------
  // MEASURED on this host from ~/.claude/logs/hook-dispatcher-errors.log:
  // 12,237 ETIMEDOUT entries, and 38 of closer-guard's 45 timeouts land in the
  // SAME SECOND as another hook's timeout. Three hooks of one chain died inside
  // a 7 ms window, twice in one minute. That is HOST SATURATION at the turn
  // boundary, not a slow hook -- closer-guard measures 644-1245 ms solo against
  // its own 5000 ms budget, i.e. 4x headroom that evaporates under the fan-out.
  //
  // Every timeout FAILS OPEN AND SILENT: the child is killed, its stdout never
  // reaches mergeOutputs, and the chain then reports exactly what a clean pass
  // reports. So the two guards whose failure IS the Owner's cross-repo hang were
  // being switched off by the crowd they share a pool with:
  //   - windows-bash-bridge-guard.js -> banned Bash call issues -> MSYS2 freeze
  //   - closer-guard.js              -> dead-screen closer passes -> frozen pane
  // A gate that cannot fire is indistinguishable from a gate that passed
  // (rules/instrument-before-claim.md). These two had been failing into a 6 MB
  // log nobody reads, which is why "the guard is wired" stayed true and useless.
  //
  // The fix is SCHEDULING, not budget. A step marked `critical` runs BEFORE the
  // pool opens, sequentially, on an uncontended host. Raising timeouts would
  // only move the cliff; deleting hooks is the Owner's call, not the
  // dispatcher's. Ordering into `settled` is by ORIGINAL index because
  // mergeOutputs is last-wins per key -- see the note above runPool.
  const limit = CHAIN_CONCURRENCY[event] || DEFAULT_CONCURRENCY;
  const settled = new Array(runnable.length);

  const critIdx = [];
  const restIdx = [];
  runnable.forEach((step, i) => (step.critical ? critIdx : restIdx).push(i));

  for (const i of critIdx) {
    settled[i] = await runStep(runnable[i], rawStdin);
    // A critical guard that COULD NOT RUN is not a clean pass, and until now it
    // read as one. Distinct marker so a liveness sweep can grep for the class
    // rather than for one script's name.
    if (settled[i] && settled[i].error) {
      logError(event, 'CRITICAL-GUARD-INERT ' + runnable[i].script, settled[i].error);
    }
  }

  // CHAIN DEADLINE. Results land in `settled` AS THEY COMPLETE rather than only at
  // pool exit, so that when the deadline fires the work already done is still
  // emitted. Without this the whole chain's stdout dies with the slowest member.
  const restSteps = restIdx.map((i) => runnable[i]);
  const budget = CHAIN_DEADLINE_MS[event];
  const left = budget ? budget - (Date.now() - chainStart) : 0;

  // R269 ORDERING FIX. The pool used to be STARTED here, one statement above the
  // budget check, so the "before pool" branch below reaped a pool it had already
  // paid to spawn. Its own comment said "rather than starting a pool whose output
  // cannot survive" -- and it started it. On a healthy host that is a wasted
  // spawn; on a starved one it is the whole failure:
  //
  //   measured 2026-09-15, this host -- 0.67 GB free of 31.31 GB (2.1 %), 46
  //   claude.exe totalling 10.2 GB. A node spawn costed at 2.2 s healthy thrashes
  //   far past that, the critical lane (sequential, above) eats the 11,500 ms
  //   budget on its own, N MORE advisory spawns are then launched anyway, the
  //   chain overruns settings.json's 15 s ceiling, and the harness kills the
  //   dispatcher BEFORE the ordered reduction below ever flushes. Every member's
  //   stdout dies together -- including the members that finished early and
  //   correctly. dead-closer-recovery logged fired:true for session e615f799 at
  //   20:18:29 and its text never reached the model; the Owner saw a dead screen.
  //
  // A budget is a constant and a spawn's cost is a function of host load, so
  // raising CHAIN_DEADLINE_MS only moves the cliff. Not spawning is the fix that
  // holds at any load. See memory/feedback_fired_true_is_not_delivered.md.
  let poolDone = null;

  if (budget && left <= 0) {
    // Budget already gone. Do NOT open the pool -- emit what critical produced.
    // NAMES, not just a count (2026-09-23, Jacobo). This branch used to log
    // '(N skipped)' while the `after` branch below logs 'still running: <scripts>'.
    // Same event class, two levels of observability -- and the cheaper half is the
    // one that fires when the CRITICAL lane alone blew the budget, i.e. exactly
    // when you most need to know who was dropped. Measured over 2026-09-15..09-23:
    // 193 'before pool' events on UserPromptSubmit-chain abandoned 965 member-slots
    // WITHOUT naming one of them, which is why an audit of how often the live
    // Project Birth owner (gsd_x_tier) is lost could only report a RANGE, 215-408
    // of 639, instead of a count. A log that says how many but not which cannot
    // answer the question it exists for. restSteps is in scope and carries .script,
    // so this is the same expression the `after` branch already uses.
    logError(event, 'CHAIN-DEADLINE-ABANDONED before pool',
      new Error('critical lane used ' + (Date.now() - chainStart) + 'ms of ' + budget
        + 'ms; pool NOT spawned (' + restSteps.length + ' skipped: '
        + (restSteps.map((s) => s.script).join(', ') || '(none)') + '); '
        + hostPressure()));
    reapLiveChildren();   // no-op unless a critical step leaked a child
  } else {
    poolDone = runPool(restSteps, limit, (step) => {
      const orig = restIdx[restSteps.indexOf(step)];
      return runStep(step, rawStdin).then((r) => { settled[orig] = r; return r; });
    });

    if (budget) {
      let timer;
      const expired = new Promise((res) => { timer = setTimeout(() => res(false), left); });
      const finished = await Promise.race([poolDone.then(() => true), expired]);
      clearTimeout(timer);
      if (!finished) {
        // Its own class, greppable, never collapsed into a clean pass -- the same
        // rule this file applies to CRITICAL-GUARD-INERT. A chain that ran out of
        // wall clock and one that had nothing to say must not read alike.
        const lost = restIdx.filter((i) => !settled[i]).map((i) => runnable[i].script);
        logError(event, 'CHAIN-DEADLINE-ABANDONED after ' + budget + 'ms',
          new Error('still running: ' + (lost.join(', ') || '(none)') + '; ' + hostPressure()));
        reapLiveChildren();
      }
    } else {
      await poolDone;
    }
  }

  // Ordered reduction -- identical to the sequential loop's body.
  for (let idx = 0; idx < runnable.length; idx++) {
    const step = runnable[idx];
    const r = settled[idx];
    if (!r) continue;
    if (r.error) { logError(event, step.script, r.error); }
    if (r.stdout) {
      const s = r.stdout.trim();
      if (s) { try { outputs.push(JSON.parse(s)); } catch (_) { /* non-JSON stdout: ignored, like Claude Code */ } }
    }
    // Hook block contract (Claude Code): exit code 2 = block the tool/stop.
    // BLOCK-BUG FIX (2026-06-04): honor exit-2 from ANY step, not only those
    // flagged block:true. Exit-2-only gates (secret-scanner = stderr+exit2,
    // session-file-guard, windows-bash-bridge-guard, anti-thrash,
    // readonly-prompts-guard, agent-solo-guard) were silently swallowed
    // in-chain because runChain previously gated on step.block. main() now
    // maps `blocked` to the family-correct field (PreToolUse ->
    // permissionDecision:deny; Stop -> decision:block).
    if (r.status === 2) {
      blocked = true;
      if (r.stderr) {
        blockStderr.push(stderrIsSafeToSurface(step.script)
          ? String(r.stderr).trim()
          : '[' + path.basename(String(step.script)) + ' blocked; its stderr is '
            + 'withheld because this gate can echo matched content (HR-SECRET-002)]');
      }
    } else if (r.status && r.status !== 0) {
      logError(event, step.script, new Error('exit ' + r.status + (r.stderr ? ': ' + String(r.stderr).slice(0, 400) : '')));
    }
  }
  return { outputs, blocked, blockStderr: blockStderr.join('\n') };
}

/**
 * May this gate's stderr be shown to the agent verbatim?
 *
 * ORIGIN (2026-09-05, measured). main() replaced EVERY exit-2 gate's stderr
 * with the generic line "Blocked by a PreToolUse gate (exit 2). See hook
 * output." — and there is no hook output, because the stderr that WAS the
 * output had just been dropped. The agent therefore learns that it was blocked
 * but not why, and does the only thing left: retries blind. Measured this
 * session — three consecutive blocked writes to one scratchpad file, each
 * reported with no reason, before the cause (anti-thrash R1, count=3) was found
 * by reading a 32 MB log. anti-thrash.js writes a complete, secret-free,
 * four-step recovery to stderr; nobody had ever seen it. 6,847 blocks are
 * recorded in that log, so this was mute across the whole estate.
 *
 * The redaction rule it came from is CORRECT and is preserved: a secret gate's
 * stderr can contain the matched value. But it was written for those gates and
 * applied as a BLANKET, which is this codebase's own recurring shape — a
 * policy sized for one member of a set and imposed on all of them.
 *
 * DEFAULT DENY: an unlisted gate stays withheld. To surface a new gate's
 * stderr, prove it cannot echo file content or user input, then add it here.
 * The listed five emit only text this repo authored.
 */
function stderrIsSafeToSurface(script) {
  return /(?:^|[\\/])(?:anti-thrash|windows-bash-bridge-guard|agent-solo-guard|readonly-prompts-guard|session-file-guard)\.js$/
    .test(String(script || ''));
}

// --- Helpers ---
function logError(event, modPath, err) {
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const line = `${new Date().toISOString()} [${event}] ${modPath} ${err && err.stack ? err.stack : String(err)}\n`;
    fs.appendFileSync(ERROR_LOG, line);
  } catch (_) { /* logging must not throw */ }
}

function parseArgs() {
  for (const a of process.argv.slice(2)) {
    if (a.startsWith('--event=')) return a.slice('--event='.length);
  }
  return null;
}

// --- NO-EVENT recovery (incident 2026-09-16 20:02 -> 2026-09-18 13:55) --------
// An ad-hoc exec-form rewrite of settings.json kept `args: [dispatcher.js]` and
// dropped `--event=<chain>` from all six registrations. The old no-event branch
// printed `{}` and exited 0, which the harness reads as "every hook passed": the
// secret firewall, bash guard, Stop chain and UserPromptSubmit chain were off for
// ~42 h and nothing said so. Missing routing identity is a CONFIGURATION FAILURE,
// never valid silence.
//
// The payload carries enough to recover the route: each registration below owns a
// disjoint matcher, so (hook_event_name, tool_name) selects exactly one of them.
// This table MUST mirror settings.json; tools/test_hook_registration_integrity.py
// asserts they agree, so a new registration cannot drift from it unnoticed.
const NO_EVENT_ROUTES = [
  { hook: 'PreToolUse', tools: ['Bash', 'PowerShell'], chain: 'PreToolUse-Bash-chain' },
  { hook: 'PreToolUse', tools: ['Write', 'Edit', 'MultiEdit', 'NotebookEdit'], chain: 'PreToolUse-Edit-chain' },
  { hook: 'PreToolUse', tools: ['Read', 'Grep'], chain: 'PreToolUse-Read-chain' },
  { hook: 'PostToolUse', tools: null, chain: 'PostToolUse-default' },
  { hook: 'Stop', tools: null, chain: 'Stop-chain' },
  { hook: 'UserPromptSubmit', tools: null, chain: 'UserPromptSubmit-chain' },
];

function deriveEventFromPayload(payload) {
  if (!payload || typeof payload !== 'object') return null;
  const hook = payload.hook_event_name;
  const tool = payload.tool_name;
  const hits = NO_EVENT_ROUTES.filter(r => r.hook === hook && (r.tools === null || r.tools.includes(tool)));
  return hits.length === 1 ? hits[0].chain : null;
}

function recordNoEvent(rec) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.appendFileSync(NO_EVENT_LOG, JSON.stringify(rec) + '\n');
  } catch (_) { /* a receipt failure must not change the verdict */ }
}

function noEventWarning(derived) {
  return 'POWER PACK CONFIG INVALID: hook-dispatcher was invoked WITHOUT --event= '
    + '(settings.json registration lost its routing identity). '
    + (derived
      ? `Recovered chain '${derived}' from the payload so its gates still ran. `
      : 'No chain could be derived; NO Power Pack hooks ran for this event. ')
    + 'Repair: python ~/.claude/skills/claude-power-pack/tools/test_hook_registration_integrity.py --live';
}

function loadHook(relativePath) {
  try {
    return require(path.join(__dirname, relativePath));
  } catch (e) {
    logError('LOAD', relativePath, e);
    // Visible signal (gap #5): a silently-dropped hook is a scaffold
    // illusion (Mistake #16). Surface load failures on stderr so a broken
    // cross-tree require (e.g. hooks -> skills/.../intent_lock.js) is
    // never invisible. stderr does not pollute the JSON stdout contract.
    try {
      process.stderr.write('[hook-dispatcher] LOAD FAILED ' + relativePath
        + ': ' + (e && e.message ? e.message : String(e)) + '\n');
    } catch (_) { /* logging must not throw */ }
    return null;
  }
}

// --- Event-family schema constants (BL-2026-05-24, Stop-schema veto fix) ----
// Root-level fields the harness accepts on EVERY event. `hookSpecificOutput`
// is also allowed at root but its inner shape is event-gated below.
const ROOT_ALLOWED = new Set([
  'continue', 'suppressOutput', 'stopReason', 'decision', 'reason',
  'systemMessage', 'terminalSequence', 'permissionDecision',
  'hookSpecificOutput',
]);
// Only these 4 events accept hookSpecificOutput.additionalContext.
// Stop, SessionStart, SessionEnd do NOT — text MUST go to systemMessage.
const EVENTS_HSO_ADDITIONAL_CONTEXT = new Set([
  'UserPromptSubmit', 'PostToolUse', 'PostToolBatch',
]);

function familyOf(eventName) {
  if (!eventName) return null;
  for (const fam of [
    'Stop', 'PreToolUse', 'PostToolBatch', 'PostToolUse',
    'UserPromptSubmit', 'SessionStart', 'SessionEnd',
  ]) {
    if (eventName.startsWith(fam)) return fam;
  }
  return null;
}

// Final schema gate: whitelist root keys per family, salvage stranded text
// into systemMessage so no child-hook drift can produce schema-invalid JSON.
// Same guarantee whether sub-hooks emit legacy or current shape.
function sanitizeForSchema(merged, family) {
  if (!merged || typeof merged !== 'object') return {};
  const clean = {};
  const stranded = [];

  for (const k of Object.keys(merged)) {
    if (!ROOT_ALLOWED.has(k)) {
      if (k === 'additionalContext' && typeof merged[k] === 'string' && merged[k].length > 0) {
        stranded.push(merged[k]);
      }
      continue;
    }
    clean[k] = merged[k];
  }

  if (clean.hookSpecificOutput && typeof clean.hookSpecificOutput === 'object') {
    const hso = clean.hookSpecificOutput;
    if (family === 'PreToolUse') {
      const kept = { hookEventName: 'PreToolUse' };
      if (typeof hso.permissionDecision === 'string') kept.permissionDecision = hso.permissionDecision;
      if (typeof hso.permissionDecisionReason === 'string') kept.permissionDecisionReason = hso.permissionDecisionReason;
      if (hso.updatedInput && typeof hso.updatedInput === 'object') kept.updatedInput = hso.updatedInput;
      // PreToolUse DOES accept hookSpecificOutput.additionalContext (verified
      // against the official hooks docs 2026-07-03: injected into Claude's
      // context at hook-fire time). The prior branch dropped it, silently
      // muting every PreToolUse context-injector (e.g. GK-12 graph_first_gate).
      if (typeof hso.additionalContext === 'string' && hso.additionalContext.length > 0) {
        kept.additionalContext = hso.additionalContext;
      }
      clean.hookSpecificOutput = kept;
    } else if (EVENTS_HSO_ADDITIONAL_CONTEXT.has(family)) {
      const kept = { hookEventName: family };
      if (typeof hso.additionalContext === 'string' && hso.additionalContext.length > 0) {
        kept.additionalContext = hso.additionalContext;
      }
      clean.hookSpecificOutput = kept;
    } else {
      if (typeof hso.additionalContext === 'string' && hso.additionalContext.length > 0) {
        stranded.push(hso.additionalContext);
      }
      delete clean.hookSpecificOutput;
    }
  }

  if (clean.decision != null) {
    if (family === 'PreToolUse') {
      delete clean.decision; // PreToolUse uses hookSpecificOutput.permissionDecision
    } else if (clean.decision === 'deny') {
      clean.decision = 'block';
    } else if (clean.decision === 'allow') {
      clean.decision = 'approve';
    } else if (clean.decision !== 'approve' && clean.decision !== 'block') {
      delete clean.decision;
    }
  }

  if (stranded.length > 0) {
    const existing = typeof clean.systemMessage === 'string' && clean.systemMessage.length > 0
      ? [clean.systemMessage] : [];
    clean.systemMessage = [...existing, ...stranded].join('\n\n');
  }

  return clean;
}

function mergeOutputs(outputs, eventName) {
  const merged = {};
  const contexts = [];
  let decisionDeny = false;
  let decisionAllow = false;
  // Stop schema: `continue` defaults to true; any explicit `false` wins.
  let continueSeen = false;
  let continueFalse = false;

  for (const out of outputs) {
    if (!out || typeof out !== 'object') continue;

    // BLOCK-BUG FIX (2026-06-04): legacy gates emit {decision:"block"} (the
    // pre-2026-04 wire shape, e.g. windows-bash-bridge-guard). Treat it the
    // same as "deny" so a chained gate's block is not silently dropped. For
    // PreToolUse this maps to permissionDecision:deny; for Stop it round-trips
    // back to decision:block via sanitizeForSchema.
    if (out.decision === 'deny' || out.decision === 'block') decisionDeny = true;
    else if (out.decision === 'allow') decisionAllow = true;

    if (Object.prototype.hasOwnProperty.call(out, 'continue')) {
      continueSeen = true;
      if (out.continue === false) continueFalse = true;
    }

    if (typeof out.additionalContext === 'string' && out.additionalContext.length > 0) {
      contexts.push(out.additionalContext);
    }

    if (out.hookSpecificOutput && typeof out.hookSpecificOutput === 'object') {
      merged.hookSpecificOutput = { ...(merged.hookSpecificOutput || {}), ...out.hookSpecificOutput };
      // Pull additionalContext out of child hookSpecificOutput too so it can
      // be re-routed by sanitizeForSchema for non-PreToolUse families.
      if (typeof out.hookSpecificOutput.additionalContext === 'string'
          && out.hookSpecificOutput.additionalContext.length > 0) {
        contexts.push(out.hookSpecificOutput.additionalContext);
      }
    }

    for (const k of Object.keys(out)) {
      if (k === 'decision' || k === 'additionalContext' || k === 'hookSpecificOutput' || k === 'continue') continue;
      merged[k] = out[k];
    }
  }

  if (eventName && eventName.startsWith('PreToolUse')) {
    if (decisionDeny || decisionAllow) {
      merged.hookSpecificOutput = {
        hookEventName: 'PreToolUse',
        ...(merged.hookSpecificOutput || {}),
        permissionDecision: decisionDeny ? 'deny' : 'allow',
      };
    }
  } else {
    if (decisionDeny) merged.decision = 'deny';
    else if (decisionAllow) merged.decision = 'allow';
  }

  if (continueSeen) merged.continue = !continueFalse;

  if (contexts.length > 0) {
    const joined = contexts.length === 1 ? contexts[0] : contexts.join('\n\n');
    const fam = familyOf(eventName);
    // HSO-ROUTING FIX (2026-06-04): additionalContext is a valid
    // hookSpecificOutput field for PreToolUse AND the
    // EVENTS_HSO_ADDITIONAL_CONTEXT families (UserPromptSubmit, PostToolUse,
    // PostToolBatch). Route it INTO hookSpecificOutput for all of those so it
    // actually reaches the MODEL context. The prior code special-cased only
    // PreToolUse and dumped UPS/PostToolUse context to root
    // merged.additionalContext -> sanitizeForSchema then stranded it into
    // systemMessage (UI-only), so the jit_skill_loader / power-pack-reminder
    // UPS injections never reached the model. Stop / SessionStart / SessionEnd
    // genuinely do NOT accept additionalContext -> leave at root for
    // sanitizeForSchema to salvage into systemMessage.
    if (fam === 'PreToolUse' || EVENTS_HSO_ADDITIONAL_CONTEXT.has(fam)) {
      merged.hookSpecificOutput = {
        hookEventName: fam,
        ...(merged.hookSpecificOutput || {}),
        additionalContext: joined,
      };
    } else {
      merged.additionalContext = joined;
    }
  }

  return merged;
}

async function runHook(event, modPath, data) {
  const mod = loadHook(modPath);
  if (!mod || typeof mod.run !== 'function') {
    logError(event, modPath, new Error('module missing run() export'));
    return null;
  }
  try {
    const result = mod.run(data);
    return await Promise.resolve(result);
  } catch (e) {
    logError(event, modPath, e);
    return null;
  }
}

function readStdin(timeoutMs) {
  return new Promise(resolve => {
    let input = '';
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      resolve(input);
    };
    const timer = setTimeout(finish, timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { input += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); finish(); });
    process.stdin.on('error', () => { clearTimeout(timer); finish(); });
  });
}

// --- Module exports for unit tests (BL-2026-05-24 regression-guard) -------
// Exported BEFORE the IIFE so `require('./hook-dispatcher.js')` succeeds
// without triggering the CLI path. The IIFE below is gated by
// `require.main === module` so test imports do NOT block on stdin.
// `runChain` is exported for tests/test-priority-lane.js. The priority-lane
// partition is invisible from outside -- a chain with a broken lane returns the
// same outputs as a working one -- so the only instrument that can tell them
// apart is an ORDERING assertion, and that needs the function itself.
// `isScratchTarget` is exported for tests/test-scratchpad-fast-path.js. Its
// failure mode is SILENT AND FAIL-OPEN -- a false return runs the full chain,
// which is exactly what a working filter looks like from the outside on a
// starved host, so only a direct assertion on the predicate can tell them apart.
module.exports = { sanitizeForSchema, familyOf, mergeOutputs, stderrIsSafeToSurface, runChain, isScratchTarget,
  deriveEventFromPayload, NO_EVENT_ROUTES, CHAIN_NAMES: Object.keys(CHAIN_MAP), EVENT_NAMES: Object.keys(EVENT_MAP) };

// --- Main (CLI path only — skipped when required as a module) ---
if (require.main === module) (async () => {
  // Heal a console-allocator re-infection of the LIVE registry within one event
  // of it happening. The launcher's repair only reaches a pane at birth, and
  // this build reloads hooks live, so a pane that started clean gets re-infected
  // while it runs -- which is when the Owner's screen starts clearing on every
  // tool call. Detects here, delegates the rewrite to the one existing fixer.
  // Fail-open, absolute: a guard that can break the dispatcher is worse than
  // the screen-clearing it was written to stop.
  try { require('./wrapper-selfheal.js').selfHeal({}); } catch (_) { /* never fatal */ }

  let event = parseArgs();
  let preRaw = null;          // stdin already consumed by the no-event path
  let noEventMsg = null;      // loud warning merged into this invocation's output

  if (!event) {
    // Read stdin FIRST: exiting without draining it can wedge the harness's
    // payload write once it exceeds the pipe buffer (the Orca claude-hook shape).
    preRaw = await readStdin(3000);
    let p = null;
    try { p = JSON.parse(preRaw || '{}'); } catch (_) { /* p stays null */ }
    const derived = deriveEventFromPayload(p);
    recordNoEvent({
      ts: new Date().toISOString(), pid: process.pid, ppid: process.ppid,
      argv: process.argv.slice(2).map(a => (a.length > 120 ? a.slice(0, 120) + '...' : a)),
      hook_event_name: p && p.hook_event_name, tool_name: p && p.tool_name,
      session_id: p && p.session_id, derived,
    });
    noEventMsg = noEventWarning(derived);
    try { process.stderr.write(noEventMsg + '\n'); } catch (_) { /* best effort */ }
    if (!derived || !CHAIN_MAP[derived] && !EVENT_MAP[derived]) {
      // CONFIG_INVALID, not VALID_SILENCE. Exit 1 = a visible non-blocking
      // hook error on every event family; exit 2 would block/loop.
      process.exit(1);
    }
    event = derived;
  }

  // --- Child-process chain path (Stop event — fork-storm-safe) ---
  if (event && CHAIN_MAP[event]) {
    const rawIn = preRaw !== null ? preRaw : await readStdin(3000);
    const { outputs, blocked, blockStderr } = await runChain(event, CHAIN_MAP[event], rawIn || '');
    // COMPANION IN-PROCESS BUNDLE (2026-06-04): a "<fam>-chain" event ALSO runs
    // its "<fam>-default" EVENT_MAP bundle IN-PROCESS (require, ~0 extra spawn)
    // and merges the outputs. Empirically (live timing): 2 in-process UPS hooks
    // = 62 ms vs a child cold-start ~250 ms each. This lets a folded event keep
    // its fast Node hooks (power-pack-reminder + baseline-translator) in-process
    // while only the heterogeneous / Python hooks (jit_skill_loader.py) stay as
    // shell-free child spawns. Only UserPromptSubmit-chain has a matching
    // EVENT_MAP companion today; every other *-chain has none -> no-op for them.
    const companionKey = event.replace(/-chain$/, '-default');
    if (companionKey !== event && EVENT_MAP[companionKey]) {
      let cData = {};
      try { cData = JSON.parse(rawIn || '{}'); } catch (_) { /* keep empty */ }
      for (const modPath of EVENT_MAP[companionKey]) {
        outputs.push(await runHook(event, modPath, cData));
      }
    }
    const merged = mergeOutputs(outputs, event);
    if (noEventMsg) {
      merged.systemMessage = merged.systemMessage ? noEventMsg + '\n\n' + merged.systemMessage : noEventMsg;
    }
    if (blocked) {
      const fam = familyOf(event);
      if (fam === 'PreToolUse') {
        // exit-2 from a PreToolUse gate = DENY the tool.
        //
        // The reason now CARRIES the blocking gate's stderr, already redacted
        // per-gate by stderrIsSafeToSurface() in runChain: gates that can echo
        // a matched secret contribute a withheld-marker instead of their text,
        // so HR-SECRET-002 still holds. What changed is that the four gates
        // whose stderr is authored recovery prose no longer block in silence.
        //
        // The old text said "See hook output." while dropping the only hook
        // output there was. A denial the agent cannot read is a denial it can
        // only answer by retrying blind — which is how three identical blocked
        // writes happened this session before anyone knew the rule was R1
        // anti-thrash. A gate that cannot explain itself trains the exact
        // behaviour it exists to stop.
        merged.hookSpecificOutput = Object.assign(
          { hookEventName: 'PreToolUse' }, merged.hookSpecificOutput || {},
          {
            permissionDecision: 'deny',
            permissionDecisionReason: blockStderr
              ? 'Blocked by a PreToolUse gate (exit 2).\n\n' + blockStderr
              : 'Blocked by a PreToolUse gate (exit 2), which emitted no reason. '
                + 'Do NOT retry the same call: identify the gate in '
                + '~/.claude/state/ before trying again.',
          });
      } else {
        merged.decision = 'block';
        if (blockStderr) merged.reason = blockStderr;
      }
    }
    const safe = sanitizeForSchema(merged, familyOf(event));
    try { process.stdout.write(JSON.stringify(safe)); }
    catch (e) { logError(event, 'STDOUT', e); process.stdout.write('{}'); }
    process.exit(0);
  }

  const bundle = event ? EVENT_MAP[event] : null;

  if (!event || !bundle) {
    // Unknown --event= name: a registration pointing at a chain that does not
    // exist is CONFIG_INVALID too. Drain stdin, leave a receipt, fail visibly
    // (exit 1 = non-blocking error) instead of a success-shaped `{}`.
    if (preRaw === null) await readStdin(3000);
    recordNoEvent({ ts: new Date().toISOString(), pid: process.pid, ppid: process.ppid,
      argv: process.argv.slice(2), unknown_event: event });
    try { process.stderr.write(`POWER PACK CONFIG INVALID: hook-dispatcher has no chain named '${event}'.\n`); } catch (_) { /* best effort */ }
    process.exit(1);
  }

  const raw = preRaw !== null ? preRaw : await readStdin(3000);
  let data = {};
  try { data = JSON.parse(raw || '{}'); } catch (_) { /* keep empty */ }

  // Sequential execution — preserves ordering semantics of original chain.
  // Switch to Promise.all if a future bundle has truly independent hooks.
  const outputs = [];
  for (const modPath of bundle) {
    const out = await runHook(event, modPath, data);
    outputs.push(out);
  }

  const merged = mergeOutputs(outputs, event);
  if (noEventMsg) {
    merged.systemMessage = merged.systemMessage ? noEventMsg + '\n\n' + merged.systemMessage : noEventMsg;
  }
  const safe = sanitizeForSchema(merged, familyOf(event));
  try {
    process.stdout.write(JSON.stringify(safe));
  } catch (e) {
    logError(event, 'STDOUT', e);
    process.stdout.write('{}');
  }
  process.exit(0);
})();
