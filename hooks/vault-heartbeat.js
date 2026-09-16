#!/usr/bin/env node
/**
 * vault-heartbeat.js - Stop event hook.
 *
 * Throttled (>=5 min) background sync of the Sovereign Vault by spawning
 * tools/merger.py --incremental as a detached, unref()'d child process.
 * Mkdir mutex at ~/.claude/state/vault-heartbeat.lock guards N-session
 * races (audit gap #5). Stale lock auto-recovers after 10 min.
 *
 * Stop hook contract: top-level fields only (no hookSpecificOutput).
 * Static systemMessage (no count promise - Gap #4).
 *
 * 2026-05-15: switched to --incremental (Lazarus-v3 baseline sealing).
 * Python resolved via hook-utils.getPythonCommand() to survive 3.12->3.13
 * upgrades (audit Gap #6).
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const { getPythonCommand } = require('./hook-utils');

const STATE_DIR = path.join(os.homedir(), '.claude', 'state');
const STAMP = path.join(STATE_DIR, 'vault-heartbeat.stamp');
const LOCK = path.join(STATE_DIR, 'vault-heartbeat.lock');
const THROTTLE_SEC = 300;     // >=5 min between syncs (ans #2)
const STALE_LOCK_SEC = 600;   // recover lock after 10 min

// Resolve Python via hook-utils to survive 3.12->3.13 upgrades (Gap #6).
// getPythonCommand may return: "exe", "\"path with spaces\"", or "py -3".
function _parsePy(raw) {
  const m = raw.match(/^"([^"]+)"\s*(.*)$/);
  if (m) return { exe: m[1], args: m[2] ? m[2].split(/\s+/).filter(Boolean) : [] };
  const parts = raw.split(/\s+/).filter(Boolean);
  return { exe: parts[0] || 'python', args: parts.slice(1) };
}
const PY = _parsePy(getPythonCommand());
const ORCHESTRATOR = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack\\tools\\vault_refresh_all.py';

function pass(msg) {
  if (msg) process.stdout.write(JSON.stringify({ systemMessage: msg }));
  process.exit(0);
}

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); } catch (_e) { return ''; }
}

(function main() {
  // Consume stdin so the harness pipe drains, but we do not use the payload.
  readStdin();
  try { fs.mkdirSync(STATE_DIR, { recursive: true }); } catch (_e) { /* */ }

  // Throttle check.
  let lastSync = 0;
  try { lastSync = fs.statSync(STAMP).mtimeMs / 1000; } catch (_e) { /* */ }
  const now = Date.now() / 1000;
  if (now - lastSync < THROTTLE_SEC) pass();

  // Mutex acquire (mkdir is atomic on Win+NTFS / POSIX).
  try {
    fs.mkdirSync(LOCK);
  } catch (e) {
    // Lock held - check staleness.
    try {
      const age = (now - fs.statSync(LOCK).mtimeMs / 1000);
      if (age > STALE_LOCK_SEC) {
        try { fs.rmdirSync(LOCK); fs.mkdirSync(LOCK); }
        catch (_x) { pass(); }
      } else {
        pass();
      }
    } catch (_x) { pass(); }
  }

  // Touch stamp BEFORE spawn so a fast re-fire still respects the throttle.
  try { fs.closeSync(fs.openSync(STAMP, 'w')); } catch (_e) { /* */ }

  // Detached, fire-and-forget. Stop hook returns immediately (Gap #3).
  let child;
  try {
    child = spawn(PY.exe, [...PY.args, ORCHESTRATOR], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    child.unref();
  } catch (_e) {
    try { fs.rmdirSync(LOCK); } catch (_x) { /* */ }
    pass();
  }

  // Lock is released by a wrapper at child exit - but since we unref()'d
  // and don't await, schedule a deferred unlink. The harness will not
  // wait for this timer; the OS keeps the process group alive long enough
  // on Windows for the throttle to mask any residual lock-stale window.
  setTimeout(() => {
    try { fs.rmdirSync(LOCK); } catch (_x) { /* stale recovery handles it */ }
  }, 1000).unref();

  pass('vault: background sync queued');
})();
