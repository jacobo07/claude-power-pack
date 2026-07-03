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
const MARKER_PATH = path.join(STATE_DIR, 'restart_pending.json');

// Hot config -- the only behavioral constants in this file.
const FRESHNESS_MINUTES = 5;
const MS_PER_MINUTE = 60 * 1000;
const MARKER_MAX_AGE_MS = FRESHNESS_MINUTES * MS_PER_MINUTE;
const ISO_SECONDS_LEN = 19;  // length of "YYYY-MM-DDTHH:MM:SS"
const UTF8_BOM_CHARCODE = 0xFEFF;

const PYTHON_EXE = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const NODE_EXE = process.execPath;

// Owner-side scripts to spawn detached. Paths inherited from the
// optimizer's WRAP_TARGETS so the hub is a true replacement.
const AUTO_COMPACT_PS1 = path.join(HOME, '.claude', 'hooks',
                                    'auto-compact-session-start-cleanup.ps1');
const AUTO_VAULT_BOOTSTRAP_JS = path.join(HOME, '.claude', 'hooks',
                                          'auto-vault-bootstrap.js');
const TCO_COMPACT_GATE_PY = path.join(PP_PATH, 'tools', 'tco_compact_gate.py');
const JIT_SKILL_LOADER_PY = path.join(PP_PATH, 'tools', 'jit_skill_loader.py');

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
function readStdin() {
  try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
      return raw.slice(1);
    }
    return raw;
  } catch (err) {
    note('stdin unreadable', err);
    return '';
  }
}

function getStdinPayload() {
  // fd 0 can be read only ONCE -- parse the whole payload here and let
  // callers pull cwd / session_id from the returned object. A second
  // readFileSync(0) would return empty and silently drop session_id.
  const raw = readStdin();
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

function hookRestartResume(cwd) {
  if (!fs.existsSync(MARKER_PATH)) {
    return null;
  }
  try {
    const stat = fs.statSync(MARKER_PATH);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > MARKER_MAX_AGE_MS) {
      try {
        fs.unlinkSync(MARKER_PATH);
      } catch (delErr) {
        note('stale marker unlink failed', delErr);
      }
      return null;
    }

    let raw = fs.readFileSync(MARKER_PATH, 'utf8');
    if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
      raw = raw.slice(1);
    }
    const ctx = JSON.parse(raw);

    const markerCwd = (ctx.cwd || '').toLowerCase();
    const sessCwd = (cwd || '').toLowerCase();
    if (markerCwd && sessCwd && markerCwd !== sessCwd) {
      // Different repo -- leave marker for the right session.
      return null;
    }

    try {
      fs.unlinkSync(MARKER_PATH);
    } catch (delErr) {
      note('marker unlink failed', delErr);
    }

    const branch = ctx.branch || 'unknown';
    const ts = (ctx.timestamp || '').slice(0, ISO_SECONDS_LEN);
    const sid = ctx.session_id || '';
    const sessNote = ctx.session_note
      || 'Session restarted via /restart command.';

    let line = '[/restart resume] Continuing from a prior session in this '
             + 'working directory. Branch: ' + branch + '. Restarted at: '
             + (ts || '?') + '.';
    if (sid) {
      line += ' Prior session id: ' + sid + '.';
    }
    line += ' ' + sessNote;
    return line;
  } catch (err) {
    note('restart_resume failed', err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Hook 1b: work_state resume (INLINE, Auto-Reset Orchestrator M5, 2026-06-04)
//   After a /compact or /kclear auto-reset, the orchestrator (M3) saved a
//   structured work_state (task + last_commit + last_file + pending). This
//   injects it into the NEW session so it continues exactly where it left off.
//   Unlike hookRestartResume (gated on the /restart marker), this fires on
//   EVERY SessionStart, matches by cwd (the new session has a fresh
//   session_id), is freshness-bounded (< 6h), and is single-shot (consumes the
//   file so it never re-injects). Fail-open: never breaks SessionStart.
// ---------------------------------------------------------------------------
const WORK_STATE_MAX_AGE_MS = 6 * 60 * MS_PER_MINUTE;  // 6h freshness window
const WORK_STATE_PENDING_SHOWN = 5;

function hookWorkStateResume(cwd) {
  try {
    const cwdL = (cwd || '').toLowerCase();
    if (!cwdL) {
      return null;
    }
    let files;
    try {
      files = fs.readdirSync(STATE_DIR)
        .filter(f => f.startsWith('work_state_') && f.endsWith('.json'));
    } catch (readDirErr) {
      return null;  // no state dir yet -- nothing to resume
    }
    let best = null;
    let bestMtime = -1;
    for (const f of files) {
      const fp = path.join(STATE_DIR, f);
      let st;
      try {
        st = fs.statSync(fp);
      } catch (statErr) {
        continue;
      }
      if (Date.now() - st.mtimeMs > WORK_STATE_MAX_AGE_MS) {
        continue;  // stale reset context -- ignore
      }
      let rec;
      try {
        let raw = fs.readFileSync(fp, 'utf8');
        if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
          raw = raw.slice(1);
        }
        rec = JSON.parse(raw);
      } catch (parseErr) {
        continue;
      }
      if ((rec.cwd || '').toLowerCase() !== cwdL) {
        continue;  // different repo -- leave for the right session
      }
      if (st.mtimeMs > bestMtime) {
        best = { rec, fp };
        bestMtime = st.mtimeMs;
      }
    }
    if (!best) {
      return null;
    }
    const r = best.rec;
    const pending = (Array.isArray(r.pending) && r.pending.length)
      ? r.pending.slice(0, WORK_STATE_PENDING_SHOWN).join('; ')
      : '(none)';
    const line = '[auto-reset resume] Continuing from a context reset. '
      + 'Task: ' + (r.task || '(unknown)') + '. '
      + 'Last commit: ' + (r.last_commit || '(none)') + '. '
      + 'Last file: ' + (r.last_file || '(none)') + '. '
      + 'Pending: ' + pending + '.';
    // Single-shot: consume so it never re-injects on a later SessionStart.
    try {
      fs.unlinkSync(best.fp);
    } catch (delErr) {
      note('work_state unlink failed', delErr);
    }
    return line;
  } catch (err) {
    note('work_state resume failed', err);
    return null;
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

function detachedSpawn(label, cmd, args, env) {
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
    const child = spawn(cmd, args, {
      detached: true,
      stdio: 'ignore',
      env: env || process.env,
      cwd: PP_PATH,
      windowsHide: true,
    });
    child.unref();
    note('SPAWNED ' + label + ' pid=' + (child.pid || '?'));
  } catch (err) {
    note(label + ' spawn failed', err);
  }
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
  try {
    if (isAbsolutePathString(cmd) && !fs.existsSync(cmd)) {
      note('SKIP ' + label + ' (missing ' + cmd + ')');
      return;
    }
    const targetArg = args.find(isAbsolutePathString);
    if (targetArg && !fs.existsSync(targetArg)) {
      note('SKIP ' + label + ' (missing target ' + targetArg + ')');
      return;
    }
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    const out = fs.openSync(logPath, 'w');
    const child = spawn(cmd, args, {
      detached: true,
      stdio: ['ignore', out, out],
      env: process.env,
      cwd: PP_PATH,
      windowsHide: true,
    });
    child.unref();
    try {
      fs.closeSync(out);
    } catch (closeErr) {
      void closeErr;
    }
    note('SPAWNED ' + label + ' pid=' + (child.pid || '?') + ' -> ' + logPath);
  } catch (err) {
    note(label + ' spawn failed', err);
  }
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
  + "    vscode_autorun.generate_from_snapshot(_snap, cwds=[os.environ.get('PP_PANE_CWD') or os.getcwd()])\n"
  + "except Exception:\n"
  + "    pass\n"
  // G6 (BL-G6-RUNTIME): mark this session active+durable with an fsync'd power
  // beacon, so a later ungraceful power-loss (lid-close -> freeze -> reboot) is
  // classified ungraceful at next startup and the cold-start reentry records a
  // recovery. Reuses THIS existing detached python -- no new SessionStart cold
  // start. The graceful counterpart is written at SessionEnd (see activation doc).
  + "try:\n"
  + "    from modules.session_resilience.power_beacon import write_active_beacon\n"
  + "    _bsd = os.path.join(os.path.expanduser('~'), '.claude', 'state')\n"
  + "    write_active_beacon(_bsd, session_id=sid, cwd=os.environ.get('PP_PANE_CWD'))\n"
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
// Main
// ---------------------------------------------------------------------------
function main() {
  const t0 = Date.now();
  let additionalContext = null;

  try {
    const payload = getStdinPayload();
    const cwd = (typeof payload.cwd === 'string' && payload.cwd)
      ? payload.cwd : process.cwd();
    const sessionId = (typeof payload.session_id === 'string')
      ? payload.session_id : '';

    // 1. Sync hook (may write to stdout).
    additionalContext = hookRestartResume(cwd);

    // 1b. Auto-Reset Orchestrator M5: inject saved work_state after a reset.
    const workStateLine = hookWorkStateResume(cwd);
    if (workStateLine) {
      additionalContext = additionalContext
        ? (additionalContext + '\n' + workStateLine)
        : workStateLine;
    }

    // 12. AutoResearch VPS digest -- inline read of the local cache.
    const digestLine = hookAutoResearchDigest();
    if (digestLine) {
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

    // 9-11. Folded fire-and-forget hooks (BL-SESSION-FOLD-001).
    hookMarkLiveSession(cwd, sessionId);
    hookZeroCommandBootstrap(cwd, sessionId);
    hookFirstTimeProject(cwd, sessionId);
  } catch (err) {
    note('hub main caught', err);
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

main();
