#!/usr/bin/env node
/**
 * session_start_hub.js -- single Node process for ALL PP SessionStart
 * concerns. Sealed BL-SESSION-HUB-001 (2026-06-01).
 *
 * Architectural rationale (T-NODE-COLD-001):
 *   Each separate SessionStart hook in ~/.claude/settings.json pays a
 *   Node cold-start floor of 30-150 ms per entry on Windows. Five PP
 *   entries -> ~500-750 ms wall floor regardless of hook body size.
 *   This hub collapses them into ONE Node process so only ONE cold
 *   start is paid; bodies and fire-and-forget spawns add < 50 ms each.
 *
 *   Doctrine: SCS C23 Session-Hub-by-default. New PP SessionStart
 *   concerns are added as functions in this file, NOT as separate
 *   entries in settings.json.
 *
 * What this hub does on every SessionStart event:
 *   1. hookRestartResume (INLINE, may emit additionalContext)
 *      Reads ~/.claude/state/restart_pending.json. If marker matches
 *      the new session's cwd AND is < 5 min old, emits a continuation
 *      hint and consumes the marker.
 *   2. hookJitWarm (DETACHED)
 *      Pre-warms tools/jit_skill_loader.py: primes the walk + spec
 *      disk caches and the OS page cache for the .py file. Identical
 *      semantics to the standalone hooks/jit_warm.js.
 *   3. hookAutoCompactCleanup (DETACHED)
 *      Spawns the Owner-side auto-compact-session-start-cleanup.ps1
 *      detached. Was async-wrapped via async_wrapper.js; now in-hub.
 *   4. hookTcoCompactGate (DETACHED)
 *      Spawns tco_compact_gate.py --session-start-check detached.
 *      Was async-wrapped; now in-hub.
 *   5. hookAutoVaultBootstrap (DETACHED)
 *      Spawns the Owner-side auto-vault-bootstrap.js detached. Was
 *      async-wrapped; now in-hub.
 *
 * stdout contract:
 *   - Exactly ONE JSON object is written, with the additionalContext
 *     from hookRestartResume (or `{"continue": true}` when no
 *     additionalContext applies). All other hooks are fire-and-forget
 *     and emit no stdout.
 *   - Errors in any single hook are logged to %TEMP%/pp-session-hub.log
 *     and the hub continues. A bug in one function cannot break the
 *     others.
 *
 * Fail-open: any uncaught error -> emit `{"continue": true}` + exit 0.
 * The hub never blocks SessionStart.
 *
 * ASCII-only constraint inherited from the .ps1 sibling (Owner-side
 * encoding rules cross-apply when wrappers spawn .ps1 files).
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

// ---------------------------------------------------------------------------
// Constants (extracted from prior magic-number Jobs advisories: BL-LAG-001)
// ---------------------------------------------------------------------------
const HOME = os.homedir();
const PP_PATH = path.resolve(__dirname, '..');
const LOG_FILE = path.join(os.tmpdir(), 'pp-session-hub.log');
const STATE_DIR = path.join(HOME, '.claude', 'state');

// Hot config -- the only behavioral constants in this file.
const MS_PER_MINUTE = 60 * 1000;
const UTF8_BOM_CHARCODE = 0xFEFF;

// Same interpreter path as the cards module; one definition.
const { PYTHON_EXE } = require('./session_cards');
const NODE_EXE = process.execPath;

// Owner-side scripts to spawn detached. Paths inherited from the
// optimizer's WRAP_TARGETS so the hub is a true replacement.
const AUTO_COMPACT_PS1 = path.join(HOME, '.claude', 'hooks',
                                    'auto-compact-session-start-cleanup.ps1');
const AUTO_VAULT_BOOTSTRAP_JS = path.join(HOME, '.claude', 'hooks',
                                          'auto-vault-bootstrap.js');
const TCO_COMPACT_GATE_PY = path.join(PP_PATH, 'tools', 'tco_compact_gate.py');
const JIT_SKILL_LOADER_PY = path.join(PP_PATH, 'tools', 'jit_skill_loader.py');
const RECOVERY_EPOCH_GATE_PY = path.join(PP_PATH, 'tools', 'recovery_epoch_gate.py');

// The recovery gate is the ONE hook here that must run synchronously: its whole
// product is a line the Owner reads THIS session ("4 panes did not come back").
// Detached, the answer would arrive after the turn it belongs to. Measured at
// ~176 ms on this host and silent on a healthy start (nothing printed, no epoch),
// which is inside the inline-hook budget.
const RECOVERY_GATE_TIMEOUT_MS = 8000;

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------
function note(msg, err) {
  // Single source of structured stderr-equivalent log. Never throws.
  try {
    const line = new Date().toISOString() + ' ' + msg
                 + (err ? ' (' + (err.message || err) + ')' : '') + '\n';
    fs.appendFileSync(LOG_FILE, line);
  } catch (writeErr) {
    void writeErr;
  }
}

// ---------------------------------------------------------------------------
// Hook 1: restart_resume (INLINE, may emit additionalContext)
// ---------------------------------------------------------------------------
// 2026-09-16 -- STDIN DEADLOCK FIX. This was `fs.readFileSync(0, 'utf8')`,
// which BLOCKS THE EVENT LOOP: if the pipe never closes the process parks at
// zero CPU forever and no in-process watchdog can save it, because no timer is
// ever scheduled. The harness's per-hook budget kills the shell WRAPPER; a
// timeout kills the direct child only, and the survivor holds the inherited
// stdout pipe. bfb40a1 has the live measurement.
//
// This is the worst one to leave broken: a SessionStart hub measured at 7374 ms
// with NO declared budget, so a stall here holds the session open screen itself.
const { readStdinRaw, armHardExit } = require('./hook-utils');

// 2 s is right for the hub, which lives inside SessionStart-chain's 4 s deadline. A
// top-level hook that requires this module (rollover_autotype.js, 15 s harness timeout)
// sets PP_HUB_STDIN_BUDGET_MS before the require. Measured 2026-09-30 (-> 31ab653e): the
// inherited 2 s expired on a starved host, the payload became {}, and /kresume was never armed.
const STDIN_BUDGET_MS = (() => {
  const v = Number(process.env.PP_HUB_STDIN_BUDGET_MS);
  return (Number.isFinite(v) && v >= 500 && v <= 12000) ? v : 2000;
})();
const HARD_EXIT = armHardExit(STDIN_BUDGET_MS + 3000,
  () => note('hard-exit watchdog fired', new Error('stdin never closed')));

async function readStdin() {
  const { raw, outcome } = await readStdinRaw(STDIN_BUDGET_MS);
  clearTimeout(HARD_EXIT);
  if (raw === null) {
    // Preserves the old catch's return of '' -- but the old code could only
    // reach it on a throw, and this branch also covers a pipe that never closed.
    // note() keeps the two distinguishable in the log, because a hub that timed
    // out and a hub whose payload was empty lose different things downstream.
    note('stdin unreadable', new Error(`readStdinRaw outcome=${outcome}`));
    return '';
  }
  if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
    return raw.slice(1);
  }
  return raw;
}

async function getStdinPayload() {
  // fd 0 can be read only ONCE -- parse the whole payload here and let
  // callers pull cwd / session_id from the returned object. A second read
  // would return empty and silently drop session_id. Still true of the bounded
  // async read: the stream is consumed once and then paused.
  const raw = await readStdin();
  if (!raw) {
    return {};
  }
  try {
    const payload = JSON.parse(raw);
    return (payload && typeof payload === 'object') ? payload : {};
  } catch (err) {
    note('stdin not JSON', err);
    return {};
  }
}

// ---------------------------------------------------------------------------
// Cards (restart / work-state / rollover / mission) live in session_cards.js since C0
// (plan pillar-k-resident-prefix, audit gap 3): that module has no load-time effects, so
// the dispatcher can run them in-process. Re-exported below for the existing tests.
// ---------------------------------------------------------------------------
const {
  composeCards, hookRolloverResume, rolloverFocus, missionNamesSession, hookMissionStart,
} = require('./session_cards');

// Since C1 the dispatcher composes the cards IN-PROCESS before the pool and says so through
// PP_SESSION_CARDS_DONE, so an abandoned hub no longer takes them down with it. Without that
// flag (an older dispatcher, CLAUDE_SESSION_CARDS_INPROC=off, a failed require) the hub still
// composes them, from the same function -- never both, so no one-shot marker is consumed twice.
function hubCards(payload) {
  if (process.env.PP_SESSION_CARDS_DONE === '1') {
    note('cards skipped by hub: delivered in-process by the dispatcher');
    return null;
  }
  return composeCards(payload, { via: 'hub' });
}

// The rollover card is context for a turn that has not started, and nothing starts one:
// measured 2026-09-29 (fe1c49ea -> e9d6887e), /kclear and /clear were both typed by the
// daemon, the card reached the successor, and the capsule sat unclaimed until a human
// asked. So the same condition that shows the card also asks the daemon to TYPE
// `/kresume` into this new session. The daemon types it only while the transcript has no
// assistant turn, and only that one command; /kresume itself refuses a second claim.
// Kill switch CPP_KRESUME_AUTOTYPE=off (the card still shows). Returns the flag path or null.
const KRESUME_DAEMON_PS1 = path.join(HOME, '.claude', 'hooks', 'auto-compact-sendkeys-daemon.ps1');

// How the daemon is launched. Measured 2026-09-30 (614697c1): spawn('powershell.exe',
// {detached:true}) NEVER starts the script -- DETACHED_PROCESS leaves the console host with
// no console and it dies before line 1, with or without -WindowStyle Hidden. Attached, it
// boots but dies with node (libuv's kill-on-close job). 0 of 10 arms that day produced a
// `daemon start`; every /kresume that did arrive came from the Stop launcher one turn
// late. wscript.exe is a GUI-subsystem host that needs no console, survives a detached
// spawn, and hidden_launch.vbs starts powershell hidden from birth.
// Pinned for real (no mock) by V-KRA-HUB-LAUNCH-BOOTS in test_kresume_autotype.py.
const KRESUME_LAUNCHER_VBS = path.join(PP_PATH, 'tools', 'hidden_launch.vbs');

function kresumeLaunchSpec() {
  return {
    label: 'kresume_autotype', cmd: 'wscript.exe', cwd: PP_PATH, log: null, envDelta: null,
    args: ['//B', '//Nologo', KRESUME_LAUNCHER_VBS, KRESUME_DAEMON_PS1],
  };
}

function armKresumeAutotype(sessionId, cwd, transcriptPath, focus) {
  try {
    const sw = String(process.env.CPP_KRESUME_AUTOTYPE || '').trim().toLowerCase();
    if (sw === '0' || sw === 'off' || sw === 'false') {
      return null;
    }
    const safeSid = String(sessionId || '').replace(/[^A-Za-z0-9-]/g, '').slice(0, 64);
    if (!safeSid || !cwd) {
      // No id = no exact route; the daemon would refuse it anyway. Logged, because a
      // silent skip here is exactly how the 2026-09-30 miss stayed invisible.
      note('SKIP kresume_autotype (no session id or cwd -- stdin payload missing?)');
      return null;
    }
    const hooksDir = process.env.AC_DAEMON_DIR || path.join(HOME, '.claude', 'hooks');
    fs.mkdirSync(hooksDir, { recursive: true });
    const flag = path.join(hooksDir, 'auto-compact-trigger-' + safeSid + '.flag');
    const body = {
      ts: new Date().toISOString(), session_id: sessionId, cwd: cwd,
      transcript: transcriptPath || '',
      fresh_line: focus ? '/kresume focus on ' + focus : '/kresume',
      kind: 'kresume',
    };
    const tmp = flag + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(body) + '\n', 'utf8');
    fs.renameSync(tmp, flag);
    // Launched NOW, never queued. Measured 2026-09-29 (435014d6): on a starved host the
    // SessionStart chain abandoned the hub 0.8 s after it armed, before flushSpawns(), so
    // the queued daemon launch died with it; the flag sat until an unrelated daemon run
    // found it 35 s later, after the Owner had typed. Everything else in the queue can be
    // late; this one races the Owner's first keystroke.
    if (!fs.existsSync(KRESUME_DAEMON_PS1)) {
      note('SKIP kresume_autotype (missing target ' + KRESUME_DAEMON_PS1 + ')');
      return flag;
    }
    if (!fs.existsSync(KRESUME_LAUNCHER_VBS)) {
      note('SKIP kresume_autotype (missing launcher ' + KRESUME_LAUNCHER_VBS + ')');
      return flag;   // the Stop launcher still serves the flag, one turn late
    }
    spawnNow(kresumeLaunchSpec());
    note('kresume autotype armed sid=' + safeSid);
    return flag;
  } catch (err) {
    note('kresume autotype failed', err);
    return null;   // the card is still shown; a human can type it
  }
}

// ---------------------------------------------------------------------------
// Hooks 2-5: detached fire-and-forget spawns
// ---------------------------------------------------------------------------
function isAbsolutePathString(p) {
  // True only for fully-qualified paths -- skip the existsSync check for
  // bare binary names that resolve via PATH (e.g. "powershell.exe", "node").
  return path.isAbsolute(p);
}

// Detects the interruption, pins the pre-crash topology, judges what came back.
// Fail-open in every branch: a recovery gate that can block a session start is a
// worse failure than the silence it exists to end.
function hookRecoveryEpoch() {
  try {
    if (!fs.existsSync(RECOVERY_EPOCH_GATE_PY)) return null;
    const out = require('child_process').execFileSync(
      PYTHON_EXE, [RECOVERY_EPOCH_GATE_PY],
      { encoding: 'utf8', timeout: RECOVERY_GATE_TIMEOUT_MS, windowsHide: true,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }) });
    const line = (out || '').trim();
    if (line) note('recovery epoch: ' + line.slice(0, 120));
    return line || null;
  } catch (err) {
    note('recovery epoch gate failed (fail-open)', err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Deferred spawning (T-DETACH-SPAWN-COST-001)
//
//   Detaching a child removes its RUN time from this process. It does not
//   remove CreateProcess, which this process pays synchronously, once per
//   child. The comments below used to assert a detached spawn "never adds
//   to the hub's wall time"; an ablation measured otherwise -- eleven
//   children cost 485 ms of the hub's own 775 ms, and carried essentially
//   all of its run-to-run variance (6 ms spread without them, 160 ms with).
//
//   So the hub now COLLECTS specs and hands the whole list to ONE detached
//   launcher, paying one CreateProcess instead of twelve. This is the same
//   fold the hub already applied to its parents (T-NODE-COLD-001), applied
//   one level down to its children.
//
//   Existence checks stay HERE: SKIP semantics are unchanged and cost
//   nothing measurable (fs.existsSync on a warm path). Only the spawn moves.
// ---------------------------------------------------------------------------
const DETACHED_LAUNCHER_JS = path.join(PP_PATH, 'hooks',
                                       'detached_launcher.js');
const PENDING_SPAWNS = [];
// Fail-open: with no launcher on disk the hub spawns inline exactly as it
// did before. Losing twelve fire-and-forget hooks would be far worse than
// paying 485 ms for them.
let deferSpawns = fs.existsSync(DETACHED_LAUNCHER_JS);

// Only the keys that DIFFER from our own env. The callers build their env
// as Object.assign({}, process.env, {...}), so shipping it whole would put
// the entire environment into the spec twelve times over.
function envDelta(env) {
  if (!env || env === process.env) return null;
  const delta = {};
  for (const k of Object.keys(env)) {
    if (env[k] !== process.env[k]) delta[k] = env[k];
  }
  return Object.keys(delta).length ? delta : null;
}

function spawnNow(spec) {
  const opts = {
    detached: true,
    stdio: 'ignore',
    env: spec.envDelta
      ? Object.assign({}, process.env, spec.envDelta)
      : process.env,
    cwd: spec.cwd || PP_PATH,
    windowsHide: true,
  };
  let fd = null;
  if (spec.log) {
    fs.mkdirSync(path.dirname(spec.log), { recursive: true });
    fd = fs.openSync(spec.log, 'w');
    opts.stdio = ['ignore', fd, fd];
  }
  const child = spawn(spec.cmd, spec.args, opts);
  child.unref();
  if (fd !== null) {
    try { fs.closeSync(fd); } catch (_e) { /* child holds its own dup */ }
  }
  note('SPAWNED ' + spec.label + ' pid=' + (child.pid || '?'));
}

// Shared by detachedSpawn and detachedSpawnLogged: the existence gate is
// identical for both, and duplicating it is how the two drift apart.
function enqueue(label, cmd, args, env, logPath) {
  try {
    if (isAbsolutePathString(cmd) && !fs.existsSync(cmd)) {
      note('SKIP ' + label + ' (missing ' + cmd + ')');
      return;
    }
    // For absolute-path args (the script/.py/.ps1 being invoked), check
    // existence too -- a missing target file is the more common reason
    // an Owner-side hook is unavailable on a fresh host.
    const targetArg = args.find(isAbsolutePathString);
    if (targetArg && !fs.existsSync(targetArg)) {
      note('SKIP ' + label + ' (missing target ' + targetArg + ')');
      return;
    }
    const spec = {
      label: label,
      cmd: cmd,
      args: args,
      envDelta: envDelta(env),
      cwd: PP_PATH,
      log: logPath || null,
    };
    if (deferSpawns) {
      PENDING_SPAWNS.push(spec);
      return;
    }
    spawnNow(spec);
  } catch (err) {
    note(label + ' spawn failed', err);
  }
}

// Hand the collected specs to one detached launcher. Any failure here falls
// back to spawning every pending child inline, so the worst case is the old
// cost -- never a lost hook.
function flushSpawns() {
  if (!PENDING_SPAWNS.length) return;
  try {
    // pid alone is not unique: Windows reuses them, and several panes open
    // at once. Two hubs colliding on this filename would cross-read or
    // clobber each other's handoff and silently lose a whole queue.
    const specPath = path.join(
      os.tmpdir(),
      'pp-hub-launch-' + process.pid + '-' + Date.now().toString(36)
        + '-' + Math.random().toString(36).slice(2, 8) + '.json');
    fs.writeFileSync(specPath, JSON.stringify(PENDING_SPAWNS), 'utf8');
    const child = spawn(NODE_EXE, [DETACHED_LAUNCHER_JS, specPath], {
      detached: true,
      stdio: 'ignore',
      env: process.env,
      cwd: PP_PATH,
      windowsHide: true,
    });
    child.unref();
    note('LAUNCHER pid=' + (child.pid || '?')
         + ' children=' + PENDING_SPAWNS.length);
  } catch (err) {
    note('launcher failed; spawning ' + PENDING_SPAWNS.length
         + ' children inline', err);
    for (const spec of PENDING_SPAWNS) {
      try {
        spawnNow(spec);
      } catch (inner) {
        note(spec.label + ' inline fallback failed', inner);
      }
    }
  }
  PENDING_SPAWNS.length = 0;
}

function detachedSpawn(label, cmd, args, env) {
  enqueue(label, cmd, args, env, null);
}

function hookJitWarm(cwd) {
  detachedSpawn('jit_warm', PYTHON_EXE, [JIT_SKILL_LOADER_PY], Object.assign(
    {}, process.env, {
      PP_WARM_RUN: '1',
      PP_WARM_CWD: cwd,
      PYTHONIOENCODING: 'utf-8',
    }));
}

function hookAutoCompactCleanup() {
  // PowerShell is on PATH; spawn the .ps1 file directly via powershell.exe.
  detachedSpawn('auto_compact_cleanup', 'powershell.exe', [
    '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
    '-ExecutionPolicy', 'Bypass',
    '-File', AUTO_COMPACT_PS1,
  ]);
}

function hookTcoCompactGate() {
  detachedSpawn('tco_compact_gate', PYTHON_EXE,
                [TCO_COMPACT_GATE_PY, '--session-start-check']);
}

function hookAutoVaultBootstrap() {
  detachedSpawn('auto_vault_bootstrap', NODE_EXE, [AUTO_VAULT_BOOTSTRAP_JS]);
}

// ---------------------------------------------------------------------------
// Hooks 6-7: detached health checks WITH output capture (BL-TOOL-AUTO-001)
//   Unlike hooks 2-5 (stdio:ignore fire-and-forget), these two write their
//   stdout/stderr to vault/health/<tool>.last.txt so the run leaves on-disk
//   evidence. Only compound_audit (137 ms) and drift_report (131 ms) qualify
//   -- both compute-only, sub-200 ms, no network (PASO 0 timing 2026-06-01).
//   Slower tools were reclassified to Task Scheduler (Mechanism F), never
//   here, per the >1 s rule.
// ---------------------------------------------------------------------------
const COMPOUND_AUDIT_PY = path.join(PP_PATH, 'tools', 'compound_audit.py');
const DRIFT_REPORT_PY = path.join(PP_PATH, 'tools', 'drift_report.py');
const HEALTH_DIR = path.join(PP_PATH, 'vault', 'health');

function detachedSpawnLogged(label, cmd, args, logPath) {
  enqueue(label, cmd, args, null, logPath);
}

function hookCompoundAudit() {
  detachedSpawnLogged('compound_audit', PYTHON_EXE, [COMPOUND_AUDIT_PY],
                      path.join(HEALTH_DIR, 'compound_audit.last.txt'));
}

function hookDriftReport() {
  detachedSpawnLogged('drift_report', PYTHON_EXE, [DRIFT_REPORT_PY],
                      path.join(HEALTH_DIR, 'drift_report.last.txt'));
}

// ---------------------------------------------------------------------------
// Hook 8: CPC-OS pane registration + snapshot (DETACHED, BL-CPCOS-001 wiring)
//   Registers THIS pane in the atomic CPC-OS registry on session open, then
//   regenerates ~/.claude/state/session_snapshot.md so the crash-recovery
//   manifest always includes the just-opened pane. Both happen in ONE
//   detached python subprocess (register THEN snapshot, sequential, no race)
//   so it never adds to the hub's wall time. pane_id, cwd, task, and the
//   claude session_id are passed via env (no argv quoting of the inline
//   script). Capturing session_id is what makes recovery's high-confidence
//   `claude --resume <id>` line live instead of the cd-only fallback.
// ---------------------------------------------------------------------------
const CPC_REGISTER_SCRIPT =
  "import os, sys\n"
  + "sys.path.insert(0, os.environ['PP_ROOT_CPC'])\n"
  + "from modules.cpc_os.registry import PaneRegistry\n"
  + "reg = PaneRegistry.load()\n"
  + "sid = os.environ.get('PP_PANE_SID') or None\n"
  // Beacon FIRST, before the heavier registry/snapshot work: the ancestor walk
  // needs this process's parent chain still present in the process table, and
  // that chain runs back through the node hub which is exiting. kclaude.ps1 can
  // only beacon a session whose id it knows AT LAUNCH (--resume), so a FRESH
  // session never got one and fell out of tasks.json as soon as it idled past
  // the ACTIVE tier -- exactly the day-old pane the Owner expects back
  // (T-BEACON-NEW-SESSION-GAP-001). Idempotent and fail-open: returns None and
  // writes nothing when the id or the owning claude.exe cannot be resolved.
  + "try:\n"
  + "    from modules.cpc_os.beacon import write_session_beacon\n"
  + "    write_session_beacon(sid, os.environ.get('PP_PANE_CWD'))\n"
  + "except Exception:\n"
  + "    pass\n"
  + "reg.register_pane(os.environ['PP_PANE_ID'], "
  + "os.environ['PP_PANE_CWD'], os.environ.get('PP_PANE_TASK', 'active'), "
  + "session_id=sid)\n"
  // C1 (RAM Optimization Sprint 2026-06-04): prune dead/stale panes >24h.
  // Forensics found 115 panes (112 stale); keep the registry honest so
  // recovery/switch iterate only live panes.
  + "try:\n"
  + "    reg.prune_stale()\n"
  + "except Exception:\n"
  + "    pass\n"
  // C2: bound the state-dir walk caches (size + TTL insurance).
  + "try:\n"
  + "    from tools.walk_cache_guard import prune_walk_caches\n"
  + "    prune_walk_caches(apply=True)\n"
  + "except Exception:\n"
  + "    pass\n"
  + "try:\n"
  + "    from modules.cpc_os.snapshot import generate_snapshot\n"
  // Trust THIS live session's sid even before Claude Code flushes its
  // <sid>.jsonl (~1-2 min after SessionStart) so the current pane resumes
  // EXACTLY instead of opening a fresh "History restored" session
  // (BL-CPCOS-RESTORE-003).
  + "    generate_snapshot(live_sid=sid)\n"
  + "except Exception:\n"
  + "    pass\n"
  // Refresh THIS repo's .vscode/tasks.json from the fresh snapshot so a Cursor
  // reopen auto-restores each live chat as its OWN dedicated terminal tab
  // (BL-CPCOS-RESTORE-002). Current cwd only -> low churn; generate_from_snapshot
  // is idempotent (skips the write when the doc is unchanged) and merge-safe.
  + "try:\n"
  + "    from modules.cpc_os import vscode_autorun\n"
  + "    _snap = os.path.join(os.path.expanduser('~'), '.claude', 'state', 'session_snapshot.json')\n"
  // keep_sids pins THIS session: the snapshot marks a pane "stale" the moment its
  // heartbeat lapses, and a beacon may not exist for it, so the liveness gate that
  // drops abandoned panes would otherwise drop the pane the Owner is typing in
  // (measured 2026-07-19 on sid aa863758). Beacon set UNION own sid.
  + "    vscode_autorun.generate_from_snapshot(_snap, cwds=[os.environ.get('PP_PANE_CWD') or os.getcwd()],\n"
  + "                                          keep_sids=({sid} if sid else None))\n"
  + "except Exception:\n"
  + "    pass\n"
  // G6 (BL-G6-RUNTIME): mark this session active+durable with an fsync'd power
  // beacon, so a later ungraceful power-loss (lid-close -> freeze -> reboot) is
  // classified ungraceful at next startup and the cold-start reentry records a
  // recovery. Reuses THIS existing detached python -- no new SessionStart cold
  // start. The graceful counterpart is written at SessionEnd (see activation doc).
  + "try:\n"
  + "    from modules.session_resilience.power_beacon import write_active_beacon\n"
  + "    from modules.session_resilience.epoch import newest_snapshot\n"
  + "    _bsd = os.path.join(os.path.expanduser('~'), '.claude', 'state')\n"
  // snapshot_ref is the pin: the topology recorded while this session is ALIVE.
  // The field was declared when the beacon shipped and no producer ever wrote it,
  // so every recovery had to fall back to guessing a reference from post-crash
  // state. Filling it here is what makes the next crash judgeable.
  + "    write_active_beacon(_bsd, session_id=sid, cwd=os.environ.get('PP_PANE_CWD'),\n"
  + "                        snapshot_ref=newest_snapshot(_bsd))\n"
  + "except Exception:\n"
  + "    pass\n";

function hookCpcOsRegister(cwd, sessionId) {
  const paneId = 'pane-' + process.pid + '-' + Date.now();
  detachedSpawn('cpc_register', PYTHON_EXE, ['-c', CPC_REGISTER_SCRIPT],
    Object.assign({}, process.env, {
      PP_ROOT_CPC: PP_PATH,
      PP_PANE_ID: paneId,
      PP_PANE_CWD: cwd || process.cwd(),
      PP_PANE_TASK: process.env.PP_PANE_TASK || 'active',
      PP_PANE_SID: sessionId || '',
      PYTHONIOENCODING: 'utf-8',
    }));
}

// ---------------------------------------------------------------------------
// Hooks 9-11: fire-and-forget SessionStart hooks folded from standalone
//   settings.json entries (BL-SESSION-FOLD-001, 2026-06-04). Each was its own
//   SessionStart spawn; the hub now detached-spawns them so Claude Code pays
//   ONE SessionStart Node cold start instead of four (T-NODE-COLD-001).
//
//   They are stdin-payload-coupled (need cwd/session_id from the SessionStart
//   event). A detached child gets no stdin, so the hub passes the payload via
//   env (PP_EVT_CWD / PP_EVT_SID); each hook reads those as a fallback when its
//   own stdin is empty. All three are idempotent (append-only / marker-gated),
//   so the brief double-run window before the settings.json migration
//   (tools/migrate_sessionstart_fold.py --apply) is benign.
//
//   Only fire-and-forget hooks are folded here. stdout-consumed hooks
//   (restart-target-consumer, learning-sentinel, token-shield-refresh) and
//   load-bearing recovery hooks (lazarus-*, terminal-slot-recorder) stay
//   standalone -- they are NOT safe to detach (UKDL T-SESSIONFOLD-001).
// ---------------------------------------------------------------------------
const MARK_LIVE_SESSION_JS = path.join(PP_PATH, 'hooks', 'mark-live-session.js');
const ZERO_COMMAND_BOOTSTRAP_JS = path.join(PP_PATH, 'hooks',
                                            'zero-command-bootstrap.js');
const FIRST_TIME_PROJECT_JS = path.join(PP_PATH, 'hooks', 'first-time-project.js');

function foldedEnv(cwd, sessionId) {
  return Object.assign({}, process.env, {
    PP_EVT_CWD: cwd || '',
    PP_EVT_SID: sessionId || '',
    PP_EVT_EVENT: 'SessionStart',
  });
}

function hookMarkLiveSession(cwd, sessionId) {
  detachedSpawn('mark_live_session', NODE_EXE, [MARK_LIVE_SESSION_JS],
                foldedEnv(cwd, sessionId));
}

function hookZeroCommandBootstrap(cwd, sessionId) {
  detachedSpawn('zero_command_bootstrap', NODE_EXE, [ZERO_COMMAND_BOOTSTRAP_JS],
                foldedEnv(cwd, sessionId));
}

function hookFirstTimeProject(cwd, sessionId) {
  detachedSpawn('first_time_project', NODE_EXE, [FIRST_TIME_PROJECT_JS],
                foldedEnv(cwd, sessionId));
}

// ---------------------------------------------------------------------------
// Hook 12: AutoResearch VPS digest (BL-AUTORESEARCH-VPS-001, 2026-06-30)
//   AutoResearch runs on the KobiiClaw VPS (cron, every 6h). This hub PULLS the
//   latest digest into a local cache for SessionStart context -- pull, never
//   push, zero interruption (the old local Stop-hook "Stop says" message was
//   silenced in V4). Two halves:
//     - hookAutoResearchDigest (INLINE): read the local cache (a plain file
//       read, no network) and surface a short pointer as additionalContext.
//     - hookAutoResearchPull (DETACHED): TTL-gated background scp that refreshes
//       the cache from the VPS for the NEXT session. Never awaited (the >1s rule:
//       network egress must not block SessionStart), windowsHide:true (Block A
//       hygiene), fail-open. detachedSpawn SKIPs it when the SSH key is absent
//       (non-laptop hosts), so it is a no-op off the Owner's laptop.
// ---------------------------------------------------------------------------
const AUTORESEARCH_DIR = path.join(HOME, '.claude', 'autoresearch-triggers');
const VPS_DIGEST_CACHE = path.join(AUTORESEARCH_DIR, 'vps_digest.md');
const VPS_SSH_KEY = path.join(HOME, '.ssh', 'kobicraft_vps');
const VPS_TARGET = 'kobicraft@204.168.166.63';
const VPS_DIGEST_REMOTE = '.claude/autoresearch-triggers/latest_digest.md';
const DIGEST_PULL_TTL_MS = 6 * 60 * MS_PER_MINUTE;   // refresh at most every 6h
const DIGEST_SHOWN_CHARS = 600;

function hookAutoResearchDigest() {
  try {
    if (!fs.existsSync(VPS_DIGEST_CACHE)) {
      return null;
    }
    let raw = fs.readFileSync(VPS_DIGEST_CACHE, 'utf8');
    if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
      raw = raw.slice(1);
    }
    raw = raw.trim();
    if (!raw) {
      return null;
    }
    const stat = fs.statSync(VPS_DIGEST_CACHE);
    const ageH = ((Date.now() - stat.mtimeMs) / MS_PER_MINUTE / 60).toFixed(1);
    const body = raw.length > DIGEST_SHOWN_CHARS
      ? raw.slice(0, DIGEST_SHOWN_CHARS) + '\n... (truncated; full digest at '
        + VPS_DIGEST_CACHE + ')'
      : raw;
    return '[AutoResearch VPS] Latest digest (cache pulled ' + ageH
      + 'h ago from KobiiClaw):\n' + body;
  } catch (err) {
    note('autoresearch digest read failed', err);
    return null;
  }
}

function hookAutoResearchPull() {
  try {
    let needPull = true;
    try {
      const stat = fs.statSync(VPS_DIGEST_CACHE);
      if (Date.now() - stat.mtimeMs < DIGEST_PULL_TTL_MS) {
        needPull = false;  // cache fresh -- skip the network round trip
      }
    } catch (statErr) {
      void statErr;  // missing cache -> pull
    }
    if (!needPull) {
      return;
    }
    fs.mkdirSync(AUTORESEARCH_DIR, { recursive: true });
    // detachedSpawn SKIPs when VPS_SSH_KEY (first absolute arg) is absent, so
    // this is a clean no-op on hosts without the laptop's key.
    detachedSpawn('autoresearch_pull', 'scp', [
      '-i', VPS_SSH_KEY,
      '-o', 'BatchMode=yes',
      '-o', 'ConnectTimeout=10',
      '-o', 'StrictHostKeyChecking=accept-new',
      VPS_TARGET + ':' + VPS_DIGEST_REMOTE,
      VPS_DIGEST_CACHE,
    ]);
  } catch (err) {
    note('autoresearch pull failed', err);
  }
}

// ---------------------------------------------------------------------------
// Hook 13: PM-03 Findings Bus digest (INLINE, SCS C70 wiring)
//   Consume side of the Parallel Mesh Findings Bus. Reads the repo's append-only
//   JSONL bus DIRECTLY (a plain fs read, like hookAutoResearchDigest -- NOT a
//   synchronous python shell-out, which would add ~300 ms python cold-start to
//   every SessionStart and violate the hub latency doctrine, SCS C23). Emits a
//   compact topic digest so a launching pane consults what other panes already
//   concluded before re-reasoning (targets the C69 P5 repeated-question leak).
//   Publish stays agent-driven via the pm_03_bus CLI (hub_wiring_instructions.md).
//   Bounded + fail-open: any error -> null (silent), never blocks SessionStart.
// ---------------------------------------------------------------------------
const PARALLEL_MESH_DIR = path.join(STATE_DIR, 'parallel_mesh');
const BUS_MAX_TOPICS = 20;
const BUS_CLAIM_CHARS = 140;

function hookFindingsBusDigest(cwd) {
  try {
    const enc = (cwd || '').replace(/[^a-zA-Z0-9]/g, '-');
    if (!enc) {
      return null;
    }
    const busFile = path.join(PARALLEL_MESH_DIR, 'findings_bus_' + enc + '.jsonl');
    if (!fs.existsSync(busFile)) {
      return null;
    }
    let raw = fs.readFileSync(busFile, 'utf8');
    if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
      raw = raw.slice(1);
    }
    // topic -> newest {claim, ts}; dedup so the digest is topics, not a log.
    const byTopic = new Map();
    for (const line of raw.split('\n')) {
      const s = line.trim();
      if (!s) {
        continue;
      }
      let rec;
      try {
        rec = JSON.parse(s);
      } catch (parseErr) {
        continue;
      }
      const topic = (rec && rec.topic) ? String(rec.topic) : '';
      if (!topic) {
        continue;
      }
      const ts = (rec.ts || '');
      const prev = byTopic.get(topic);
      if (!prev || ts > prev.ts) {
        byTopic.set(topic, { claim: String(rec.claim || ''), ts: ts });
      }
    }
    if (byTopic.size === 0) {
      return null;
    }
    const topics = Array.from(byTopic.keys()).sort().slice(0, BUS_MAX_TOPICS);
    const lines = ['[Findings Bus] Conclusions other panes already reached in '
      + 'this repo -- consult BEFORE re-reasoning (PM-03, SCS C70):'];
    for (const topic of topics) {
      let claim = byTopic.get(topic).claim.replace(/\s+/g, ' ');
      if (claim.length > BUS_CLAIM_CHARS) {
        claim = claim.slice(0, BUS_CLAIM_CHARS) + '...';
      }
      lines.push('- ' + topic + ': ' + claim);
    }
    return lines.join('\n');
  } catch (err) {
    note('findings bus digest failed', err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Hook 14: OWNER_QUEUE digest (INLINE, D4 strategic-gaps)
//   HR-001 Owner-side residuals (a Copy-Item, a scheduled-task registration)
//   were tracked nowhere as a set, so a stale one could hide for days (the PM-03
//   wiring sat pending 6+ days). The OWNER_QUEUE engine (modules/owner_queue)
//   maintains a materialized OWNER_QUEUE.pending.json; this reads it DIRECTLY (a
//   plain fs read, NOT a python shell-out -- the hub latency doctrine, SCS C23)
//   and surfaces only residuals past the grace window (> 24h) so a fresh
//   same-session residual does not nag. When the residual's component goes LIVE,
//   the D1 auditor auto-clears the row -- so a cleared item drops off silently.
//   Bounded + fail-open: any error -> null, never blocks SessionStart.
// ---------------------------------------------------------------------------
const OWNER_QUEUE_PENDING = path.join(STATE_DIR, 'OWNER_QUEUE.pending.json');
const OWNER_QUEUE_GRACE_MINUTES = 24 * 60;  // surface residuals pending > 24h
const OWNER_QUEUE_GRACE_MS = OWNER_QUEUE_GRACE_MINUTES * MS_PER_MINUTE;
const OWNER_QUEUE_SHOWN = 8;

function hookOwnerQueue() {
  try {
    if (!fs.existsSync(OWNER_QUEUE_PENDING)) {
      return null;
    }
    let raw = fs.readFileSync(OWNER_QUEUE_PENDING, 'utf8');
    if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
      raw = raw.slice(1);
    }
    raw = raw.trim();
    if (!raw) {
      return null;
    }
    let rows;
    try {
      rows = JSON.parse(raw);
    } catch (parseErr) {
      return null;
    }
    if (!Array.isArray(rows) || rows.length === 0) {
      return null;
    }
    const now = Date.now();
    const stale = rows.filter((r) => {
      if (!r || r.status !== 'pending') {
        return false;
      }
      const t = Date.parse(r.created || '');
      if (Number.isNaN(t)) {
        return true;  // unparseable age -> surface (fail toward visibility)
      }
      return (now - t) >= OWNER_QUEUE_GRACE_MS;
    });
    if (stale.length === 0) {
      return null;
    }
    const lines = ['[OWNER_QUEUE] ' + stale.length + ' HR-001 residual(s) pending '
      + '> 24h -- run the exact command, then it auto-clears:'];
    for (const r of stale.slice(0, OWNER_QUEUE_SHOWN)) {
      const cmd = (r.command || '').replace(/\s+/g, ' ');
      lines.push('- ' + (r.action || '(action?)') + ': ' + cmd);
    }
    return lines.join('\n');
  } catch (err) {
    note('owner_queue digest failed', err);
    return null;
  }
}

// Hook 14b (DETACHED): refresh the materialized pending view from the durable
// vault/OWNER_QUEUE.md so the inline read above stays synced. Detached python
// (the hub forbids a synchronous python shell-out inline, SCS C23) -> this
// refreshes pending.json for the NEXT session; the inline hookOwnerQueue reads
// the CURRENT one. Same one-session-lag pattern as the AutoResearch pull. The
// ingest is idempotent and fail-open (never touches the durable md).
const OWNER_QUEUE_PY = path.join(PP_PATH, 'modules', 'owner_queue', 'owner_queue.py');

function hookOwnerQueueIngest() {
  detachedSpawn('owner_queue_ingest', PYTHON_EXE, [OWNER_QUEUE_PY, '--ingest'],
    Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }));
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
// Async because getStdinPayload() is now a Promise. Everything below is
// UNCHANGED -- only the way the input arrives moved. The surrounding try/catch
// still works here because the await is INSIDE it, so a rejection from the read
// is caught exactly as a throw was.
// Owner-facing lines (incremental-cognition pillar K, 2026-10-05). The recovery verdict, the OWNER_QUEUE digest
// and the AutoResearch digest address the Owner ("run /lazarus", "run the exact command"). A headless session --
// a mission worker or a probe, entrypoint sdk-cli -- has no Owner watching, and the K probe measured those three
// at 2,405 chars of its startup window. Only a POSITIVE headless reading omits them; an absent or unknown
// entrypoint keeps today's behaviour. The hooks still RUN (hookRecoveryEpoch pins crash evidence): only the
// emitted line is scoped. Evidence: vault/programs/incremental-cognition/evidence/K-sessionstart-attribution.md.
function ownerFacingAllowed(entrypoint) {
  return entrypoint !== 'sdk-cli';
}

// A digest that positively reports zero accepted and zero cross-project signals says nothing a session can act
// on. Anything else -- a non-zero count, or a format these patterns do not recognise -- is kept.
function digestHasSignal(text) {
  const t = String(text || '');
  const accepted = /Signals accepted[^\n:]*:\**\s*(\d+)/i.exec(t);
  const cross = /Cross-project signals found[^\n:]*:\**\s*(\d+)/i.exec(t);
  if (!accepted || !cross) return true;
  return Number(accepted[1]) > 0 || Number(cross[1]) > 0;
}

async function main() {
  const t0 = Date.now();
  let additionalContext = null;

  try {
    const payload = await getStdinPayload();
    const cwd = (typeof payload.cwd === 'string' && payload.cwd)
      ? payload.cwd : process.cwd();
    const sessionId = (typeof payload.session_id === 'string')
      ? payload.session_id : '';

    // 0. Cards (rollover / mission / restart / work-state): see hubCards above. FIRST in the
    // context: the host truncates SessionStart output near 9 KB.
    additionalContext = hubCards(payload);

    // 1a. Recovery epoch. MUST run before hookCpcOsRegister, which writes a fresh
    // ACTIVE beacon: that beacon is what proves the PREVIOUS session died without
    // closing, and overwriting it before reading it would destroy the evidence of
    // the very crash we are recovering from. Order is load-bearing, not cosmetic.
    const ownerFacing = ownerFacingAllowed(process.env.CLAUDE_CODE_ENTRYPOINT);
    const recoveryLine = hookRecoveryEpoch();
    if (recoveryLine && ownerFacing) {
      additionalContext = additionalContext
        ? (additionalContext + '\n' + recoveryLine)
        : recoveryLine;
    }

    // 12. AutoResearch VPS digest -- inline read of the local cache.
    const digestLine = hookAutoResearchDigest();
    if (digestLine && ownerFacing && digestHasSignal(digestLine)) {
      additionalContext = additionalContext
        ? (additionalContext + '\n' + digestLine)
        : digestLine;
    }

    // 13. PM-03 Findings Bus digest -- inline read of the repo's bus (SCS C70).
    const busLine = hookFindingsBusDigest(cwd);
    if (busLine) {
      additionalContext = additionalContext
        ? (additionalContext + '\n' + busLine)
        : busLine;
    }

    // 14. OWNER_QUEUE digest -- inline read of the materialized pending view (D4).
    const ownerQueueLine = hookOwnerQueue();
    if (ownerQueueLine && ownerFacing) {
      additionalContext = additionalContext
        ? (additionalContext + '\n' + ownerQueueLine)
        : ownerQueueLine;
    }

    // 2-5. Fire-and-forget spawns (all detached, no waiting).
    hookJitWarm(cwd);
    hookAutoCompactCleanup();
    hookTcoCompactGate();
    hookAutoVaultBootstrap();
    hookCompoundAudit();
    hookDriftReport();
    hookCpcOsRegister(cwd, sessionId);
    // 12b. AutoResearch VPS digest -- detached TTL-gated pull for next session.
    hookAutoResearchPull();
    // 14b. OWNER_QUEUE ingest -- detached refresh of pending.json from the vault doc.
    hookOwnerQueueIngest();

    // 9-11. Folded fire-and-forget hooks (BL-SESSION-FOLD-001).
    hookMarkLiveSession(cwd, sessionId);
    hookZeroCommandBootstrap(cwd, sessionId);
    hookFirstTimeProject(cwd, sessionId);

    // Every hook above only ENQUEUED. One CreateProcess now covers all of
    // them; the launcher fans them out off this process's critical path.
    flushSpawns();
  } catch (err) {
    note('hub main caught', err);
    // A throw between the first enqueue and the flush would strand the
    // whole queue: the hooks would be silently skipped rather than merely
    // slow. Flush on the way out too -- it is idempotent (the queue is
    // emptied) and fail-open.
    try {
      flushSpawns();
    } catch (flushErr) {
      note('flush after error also failed', flushErr);
    }
  }

  const elapsedMs = Date.now() - t0;
  note('DONE elapsed_ms=' + elapsedMs
       + ' additional_context=' + (additionalContext ? 'yes' : 'no'));

  // Emit stdout JSON. Either continuation hint or bare-continue.
  const payload = additionalContext
    ? { continue: true, additionalContext: additionalContext }
    : { continue: true };
  try {
    process.stdout.write(JSON.stringify(payload));
  } catch (writeErr) {
    note('stdout write failed', writeErr);
  }
  process.exit(0);
}

// .catch is mandatory now that main is async. main() has an internal try/catch
// around its body, but a rejection from OUTSIDE that block would otherwise
// escape unhandled -- and a process that merely logs one stays ALIVE holding the
// inherited stdout pipe, which on a SessionStart hub means the session never
// finishes opening. Emit the bare-continue the harness expects, then exit.
// Run only when executed as the hook. A test that requires this file to reach one
// function must not fire every side effect of a session start (live-session marks,
// detached jobs) under a synthetic session id.
if (require.main === module) {
  main().catch((err) => {
    note('main rejected', err);
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch (_) { /* noop */ }
    process.exit(0);
  });
}

module.exports = { hubCards, missionNamesSession, hookMissionStart, hookRolloverResume, armKresumeAutotype,
  rolloverFocus, getStdinPayload, note, ownerFacingAllowed, digestHasSignal };
