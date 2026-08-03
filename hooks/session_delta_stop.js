#!/usr/bin/env node
/**
 * session_delta_stop.js -- Session Delta Gate, Stop-chain child (2026-08-03).
 *
 * Dispatches modules/session_delta/delta.py against the Stop payload's own cwd
 * and session_id. The module writes <cwd>/.claude/cache/learnings/<date>_<sid>.md
 * -- the input path hooks/learning-sentinel.js reads first and that nothing in
 * the estate wrote, which is why LEARNINGS_PENDING.md has never been produced.
 *
 * Detached + unref, same shape as jit_correlate_stop.js: the common path is a
 * throttled no-op in <50 ms, but the branch that runs when a module changed calls
 * liveness.reachability.scan() (~2.2 s measured). Turn end must not wait on it.
 *
 * The module is fail-open and always exits 0; this wrapper adds its own guards so
 * a missing interpreter, a malformed payload or a spawn failure is a logged
 * no-op. A Stop hook must never break turn end.
 *
 * Owner registration: this file is referenced from hooks/hook-dispatcher.js
 * CHAIN_MAP['Stop-chain']; the dispatcher itself must be copied canonical -> live
 * (HR-001 -- the agent may not write ~/.claude/hooks). See vault/OWNER_QUEUE.md.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const PP_PATH = path.resolve(__dirname, '..');
const PYTHON_EXE =
  'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const MODULE = path.join(PP_PATH, 'modules', 'session_delta', 'delta.py');
const LOG = path.join(os.tmpdir(), 'pp-stop-hooks.log');
const STDIN_TIMEOUT_MS = 3000;

function logLine(msg) {
  try {
    fs.appendFileSync(LOG, new Date().toISOString() + ' session-delta ' + msg + '\n');
  } catch (writeErr) {
    void writeErr;
  }
}

function dispatch(data) {
  const cwd = (data && data.cwd) || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const sid = (data && (data.session_id || data.sessionId)) || '';
  if (!fs.existsSync(PYTHON_EXE) || !fs.existsSync(MODULE)) {
    logLine('SKIP (missing python or module)');
    return;
  }
  if (!fs.existsSync(cwd)) {
    logLine('SKIP (cwd does not exist: ' + cwd + ')');
    return;
  }
  const child = spawn(PYTHON_EXE, [MODULE, '--repo', cwd, '--sid', sid], {
    detached: true,
    stdio: 'ignore',
    cwd: PP_PATH,
    windowsHide: true,
    env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
  });
  child.unref();
  logLine('dispatched pid=' + (child.pid || '?') + ' cwd=' + cwd);
}

function finish() {
  try { process.exit(0); } catch (exitErr) { void exitErr; }
}

let input = '';
const timer = setTimeout(() => {
  try { dispatch({}); } catch (err) {
    logLine('ERROR(timeout-path) ' + (err && err.message ? err.message : err));
  }
  finish();
}, STDIN_TIMEOUT_MS);

process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  clearTimeout(timer);
  let data = {};
  try { data = JSON.parse(input); } catch (parseErr) { void parseErr; }
  try { dispatch(data); } catch (err) {
    logLine('ERROR ' + (err && err.message ? err.message : err));
  }
  finish();
});
process.stdin.on('error', (err) => {
  clearTimeout(timer);
  logLine('STDIN ERROR ' + (err && err.message ? err.message : err));
  finish();
});
