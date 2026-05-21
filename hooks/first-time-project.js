#!/usr/bin/env node
/**
 * first-time-project.js - SessionStart hook (Zero-Command Plan, Component D).
 *
 * Source of truth: PP repo (claude-power-pack/hooks/).
 * Deployment path: ~/.claude/hooks/first-time-project.js (Owner-authorized
 * install via tools/settings_merger.py).
 *
 * Sibling to zero-command-bootstrap.js (Component A). A handles Spec Kit
 * stub; D runs a quick prereq probe to surface PP install gaps the first
 * time the agent visits a real project dir.
 *
 * Decision tree (idempotent via .pp-onboarded-prereqs marker - distinct
 * from .pp-onboarded so Component A and D don't race or stomp each other):
 *   1. cwd/.pp-onboarded-prereqs exists                  -> silent no-op
 *   2. cwd missing .git                                  -> silent no-op
 *   3. cwd has .git + manifest                           -> detached probe
 *   4. Probe writes .pp-onboarded-prereqs with results,
 *      and vault/handoffs/pp-onboarding-<ts>.md when gaps exist.
 *
 * Hook contract (SessionStart): same as zero-command-bootstrap.js.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const PROBE_SCRIPT = path.join(PP_ROOT, 'tools', 'first_time_project_init.py');
const LOG_FILE = path.join(os.homedir(), '.claude', 'logs', 'first-time-project.log');
const STDIN_TIMEOUT_MS = 2000;

const MANIFEST_NAMES = [
  'package.json', 'pyproject.toml', 'Cargo.toml',
  'go.mod', 'pom.xml', 'build.gradle', 'build.gradle.kts',
  'mix.exs', 'composer.json', 'Gemfile'
];

function logErr(where, e) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    const line = `${new Date().toISOString()} [${where}] ${e && e.stack || e && e.message || String(e)}\n`;
    fs.appendFileSync(LOG_FILE, line, 'utf8');
  } catch (logFail) {
    try { process.stderr.write(`first-time-project log fail: ${logFail.message}\n`); } catch (_unreachable) { /* I/O fully closed */ }
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

function hasManifest(cwd) {
  for (const m of MANIFEST_NAMES) {
    if (fs.existsSync(path.join(cwd, m))) return m;
  }
  return null;
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
    if (fs.existsSync(path.join(cwd, '.pp-onboarded-prereqs'))) return;
    if (!fs.existsSync(path.join(cwd, '.git'))) return;
    if (!hasManifest(cwd)) return;
    if (!fs.existsSync(PROBE_SCRIPT)) return;

    const child = spawn(
      'python',
      [PROBE_SCRIPT, '--cwd', cwd, '--session', event.session_id || 'unknown'],
      { detached: true, stdio: 'ignore', windowsHide: true }
    );
    child.unref();
  } catch (e) {
    logErr('main', e);
  }
})();
