#!/usr/bin/env node
/**
 * background-verifier.js - Stop hook (Zero-Command Plan, Component C).
 *
 * Source of truth: PP repo (claude-power-pack/hooks/).
 * Deployment path: ~/.claude/hooks/background-verifier.js (Owner-authorized
 * install via tools/settings_merger.py).
 *
 * Runs three background checks AFTER the agent's response is delivered.
 * Each writes a vault/handoffs/<kind>-<ts>.md if a condition warrants
 * Owner attention. Does NOT auto-fix, does NOT auto-push, does NOT
 * auto-OVO. Stop hook returns {} immediately; the heavy work runs in a
 * detached child so Stop never blocks.
 *
 * Three checks (per the Zero-Command plan):
 *   1. Mirror parity   - global vs PP doctrine pair diff (drift -> handoff)
 *   2. OVO staleness   - last verdict age + uncommitted/ahead detection
 *   3. Spec coherence  - bracketed-clarification markers vs chain advance
 *
 * Idempotency: a per-kind handoff file is at most one per 10 minutes (the
 * child checks mtime of the most recent handoff of same kind and refuses
 * to spam if recent).
 *
 * Hook contract (Stop):
 *   stdin JSON: {"session_id":"...","cwd":"...","transcript_path":"..."}
 *   stdout: {} (always)
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const VERIFIER_SCRIPT = path.join(PP_ROOT, 'tools', 'background_verifier_run.py');
const LOG_FILE = path.join(os.homedir(), '.claude', 'logs', 'background-verifier.log');
const STDIN_TIMEOUT_MS = 2000;

function logErr(where, e) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    const line = `${new Date().toISOString()} [${where}] ${e && e.stack || e && e.message || String(e)}\n`;
    fs.appendFileSync(LOG_FILE, line, 'utf8');
  } catch (logFail) {
    try { process.stderr.write(`background-verifier log fail: ${logFail.message}\n`); } catch (_unreachable) { /* I/O fully closed */ }
  }
}

function readStdinSync(timeoutMs) {
  return new Promise(resolve => {
    let buf = '';
    const t = setTimeout(() => resolve(buf), timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => { clearTimeout(t); resolve(buf); });
    process.stdin.on('error', err => { clearTimeout(t); logErr('stdin', err); resolve(buf); });
  });
}

(async function main() {
  let event = {};
  try {
    let raw = await readStdinSync(STDIN_TIMEOUT_MS);
    if (raw && raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
    if (raw && raw.trim()) event = JSON.parse(raw);
  } catch (e) {
    logErr('parse-stdin', e);
  }

  process.stdout.write('{}');

  try {
    const cwd = event && event.cwd;
    if (!cwd) return;
    if (!fs.existsSync(VERIFIER_SCRIPT)) return;
    if (!fs.existsSync(path.join(cwd, '.git'))) return;

    const child = spawn(
      'python',
      [VERIFIER_SCRIPT, '--cwd', cwd, '--session', event.session_id || 'unknown'],
      { detached: true, stdio: 'ignore', windowsHide: true }
    );
    child.unref();
  } catch (e) {
    logErr('main', e);
  }
})();
