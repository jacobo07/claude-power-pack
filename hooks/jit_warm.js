#!/usr/bin/env node
/**
 * jit_warm.js -- SessionStart pre-warmer for tools/jit_skill_loader.py.
 *
 * Triggers when Claude Code starts a new session. Spawns a detached
 * background python process that runs jit_skill_loader with
 * PP_WARM_RUN=1, paying the heavy first-time costs (Python interpreter
 * cold start, module imports, OS page cache for the .py + stdlib +
 * .pyc bytecode, walk + spec disk caches) so the user's FIRST real
 * UserPromptSubmit skips them.
 *
 * Honest scope: the warm subprocess CANNOT share its in-process caches
 * (tiktoken handle, sys.modules) with the user's later subprocess.
 * The wins that survive across subprocess boundaries:
 *   * OS page cache for python.exe + stdlib + jit_skill_loader.py
 *   * STATE_DIR/jit-walk-<sha>.json (1 h)
 *   * STATE_DIR/jit-spec-<sha>.json (5 min)
 *   * .pyc bytecode files on disk
 *
 * Fire-and-forget: NEVER blocks SessionStart. Any error -> exit 0
 * silently. SessionStart hooks must NOT emit additionalContext from
 * stdout in this PP profile -- we only run the warm and exit.
 *
 * Sealed BL-JIT-001 (2026-05-31).
 */
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';
const JIT = path.join(PP_PATH, 'tools', 'jit_skill_loader.py');
const LOG = path.join(os.tmpdir(), 'pp-jit-warm.log');

function logLine(msg) {
  try {
    fs.appendFileSync(LOG, `${new Date().toISOString()} ${msg}\n`);
  } catch (_e) { /* ignore */ }
}

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); }
  catch (_e) { return ''; }
}

let cwd = process.cwd();
try {
  const raw = readStdin();
  if (raw) {
    const payload = JSON.parse(raw);
    if (payload && typeof payload.cwd === 'string' && payload.cwd) {
      cwd = payload.cwd;
    }
  }
} catch (_e) { /* fail-open */ }

try {
  if (!fs.existsSync(PY) || !fs.existsSync(JIT)) {
    logLine(`SKIP: missing PY (${fs.existsSync(PY)}) or JIT (${fs.existsSync(JIT)})`);
    process.exit(0);
  }

  const env = Object.assign({}, process.env, {
    PP_WARM_RUN: '1',
    PP_WARM_CWD: cwd,
    PYTHONIOENCODING: 'utf-8',
  });

  const child = spawn(PY, [JIT], {
    detached: true,
    stdio: 'ignore',
    cwd: PP_PATH,
    env,
    windowsHide: true,
  });
  child.unref();
  logLine(`SPAWNED pid=${child.pid || '?'} cwd=${cwd}`);
} catch (e) {
  logLine(`ERROR ${e && e.message ? e.message : e}`);
}

process.exit(0);
