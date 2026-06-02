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

function getCwdFromStdin() {
  const raw = readStdin();
  if (!raw) {
    return process.cwd();
  }
  try {
    const payload = JSON.parse(raw);
    if (payload && typeof payload.cwd === 'string' && payload.cwd) {
      return payload.cwd;
    }
  } catch (err) {
    note('stdin not JSON', err);
  }
  return process.cwd();
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
// Hook 8: CPC-OS pane registration (DETACHED, BL-CPCOS-001 wiring)
//   Registers THIS pane in the atomic CPC-OS registry on session open.
//   Fire-and-forget: the registry write happens in a detached python
//   subprocess so it never adds to the hub's wall time. pane_id, cwd,
//   and task are passed via env (no argv quoting of the inline script).
// ---------------------------------------------------------------------------
const CPC_REGISTER_SCRIPT =
  "import os, sys\n"
  + "sys.path.insert(0, os.environ['PP_ROOT_CPC'])\n"
  + "from modules.cpc_os.registry import PaneRegistry\n"
  + "reg = PaneRegistry.load()\n"
  + "reg.register_pane(os.environ['PP_PANE_ID'], "
  + "os.environ['PP_PANE_CWD'], os.environ.get('PP_PANE_TASK', 'active'))\n";

function hookCpcOsRegister(cwd) {
  const paneId = 'pane-' + process.pid + '-' + Date.now();
  detachedSpawn('cpc_register', PYTHON_EXE, ['-c', CPC_REGISTER_SCRIPT],
    Object.assign({}, process.env, {
      PP_ROOT_CPC: PP_PATH,
      PP_PANE_ID: paneId,
      PP_PANE_CWD: cwd || process.cwd(),
      PP_PANE_TASK: process.env.PP_PANE_TASK || 'active',
      PYTHONIOENCODING: 'utf-8',
    }));
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
function main() {
  const t0 = Date.now();
  let additionalContext = null;

  try {
    const cwd = getCwdFromStdin();

    // 1. Sync hook (may write to stdout).
    additionalContext = hookRestartResume(cwd);

    // 2-5. Fire-and-forget spawns (all detached, no waiting).
    hookJitWarm(cwd);
    hookAutoCompactCleanup();
    hookTcoCompactGate();
    hookAutoVaultBootstrap();
    hookCompoundAudit();
    hookDriftReport();
    hookCpcOsRegister(cwd);
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
