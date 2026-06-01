#!/usr/bin/env node
/**
 * session_snapshot_stop.js -- PP Stop hook (BL-TOOL-AUTO-001, 2026-06-01).
 *
 * Fires tools/session-snapshot.py DETACHED at end of turn. This is Layer 3 of
 * SESSION_SAFETY_CONTRACT.md (durable .jsonl snapshot). PASO 0 timing measured
 * the tool at > 12 s, so it MUST be fire-and-forget -- never block turn end.
 * Detached + unref returns the Stop event in < 50 ms while the snapshot writes
 * in the background.
 *
 * Owner registration (auto-mode cannot write settings.json -- HR-001):
 *   Add to ~/.claude/settings.json under hooks.Stop[].hooks[]:
 *     { "type": "command",
 *       "command": "node \"<PP>/hooks/session_snapshot_stop.js\"" }
 *   where <PP> = C:/Users/User/.claude/skills/claude-power-pack
 *
 * Fail-open: any error -> exit 0. A Stop hook must never break turn end.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const PP_PATH = path.resolve(__dirname, '..');
const PYTHON_EXE =
  'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const TOOL = path.join(PP_PATH, 'tools', 'session-snapshot.py');
const LOG = path.join(os.tmpdir(), 'pp-stop-hooks.log');

function logLine(msg) {
  try {
    fs.appendFileSync(LOG, new Date().toISOString() + ' ' + msg + '\n');
  } catch (writeErr) {
    void writeErr;
  }
}

try {
  if (fs.existsSync(PYTHON_EXE) && fs.existsSync(TOOL)) {
    const child = spawn(PYTHON_EXE, [TOOL], {
      detached: true,
      stdio: 'ignore',
      cwd: PP_PATH,
      windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
    });
    child.unref();
    logLine('session_snapshot dispatched pid=' + (child.pid || '?'));
  } else {
    logLine('session_snapshot SKIP (missing python or tool)');
  }
} catch (err) {
  logLine('session_snapshot ERROR ' + (err && err.message ? err.message : err));
}

process.exit(0);
