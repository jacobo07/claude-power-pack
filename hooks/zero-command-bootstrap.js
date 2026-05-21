#!/usr/bin/env node
/**
 * zero-command-bootstrap.js — SessionStart hook (Zero-Command Plan, Component A).
 *
 * Source of truth: this file (PP repo, hooks/).
 * Deployment path: ~/.claude/hooks/zero-command-bootstrap.js (copied by
 * tools/settings_merger.py register-zero-command during Owner-authorized install).
 *
 * Companion to auto-vault-bootstrap.js (vault extraction) but covers the
 * Spec Kit auto-stub path: if the cwd looks like an active dev project
 * (.git + a recognized manifest) AND lacks .specify/, drop a pre-stubbed
 * constitution.md so the Spec Kit JIT chain can begin without an Owner
 * command.
 *
 * Decision tree (idempotent via .pp-onboarded marker):
 *   1. cwd/.pp-onboarded exists                          -> silent no-op
 *   2. cwd missing .git                                  -> silent no-op (not a project)
 *   3. cwd has .git + manifest + no .specify/            -> stub constitution.md
 *   4. Touch .pp-onboarded with timestamp + actions log  -> done
 *
 * Constraints:
 *   - Never blocks SessionStart (stdout {} immediately, work happens after).
 *   - Never creates files the Owner did not consent to (only on project signals).
 *   - The .pp-onboarded marker doubles as audit trail (records what was done).
 *   - Idempotent under repeat session starts on same cwd.
 *   - Never throws from main: SessionStart hook contract requires {} stdout.
 *     All errors are logged to ~/.claude/logs/zero-command-bootstrap.log;
 *     no error is silently swallowed (Woz #1: every catch records the why).
 *
 * Hook contract (SessionStart):
 *   stdin JSON: {"session_id":"...","cwd":"...","source":"startup"|"resume"|"clear"}
 *   stdout: {} (always)
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const CONSTITUTION_TEMPLATE = path.join(
  PP_ROOT, 'vault/templates/speckit/constitution.md.template'
);
const LOG_FILE = path.join(os.homedir(), '.claude', 'logs', 'zero-command-bootstrap.log');
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
    try { process.stderr.write(`zero-command-bootstrap log fail: ${logFail.message}\n`); } catch (_unreachable) { /* I/O fully closed; demonstrable not silent */ }
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

function stubConstitution(cwd) {
  const tplPath = CONSTITUTION_TEMPLATE;
  if (!fs.existsSync(tplPath)) return { skipped: 'template-missing' };

  const specifyMem = path.join(cwd, '.specify', 'memory');
  fs.mkdirSync(specifyMem, { recursive: true });

  const constitutionPath = path.join(specifyMem, 'constitution.md');
  if (fs.existsSync(constitutionPath)) return { skipped: 'already-present' };

  const tpl = fs.readFileSync(tplPath, 'utf8');
  const projectName = path.basename(cwd);
  const stubbed = tpl.replace(/\[PROJECT_NAME\]/g, projectName);
  fs.writeFileSync(constitutionPath, stubbed, 'utf8');
  return { stubbed: constitutionPath };
}

(async function main() {
  let event = {};
  try {
    let raw = await readStdinSync(STDIN_TIMEOUT_MS);
    if (raw && raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1); // strip UTF-8 BOM (PS 5.1 pipe writes one)
    if (raw && raw.trim()) event = JSON.parse(raw);
  } catch (e) {
    logErr('parse-stdin', e);
  }

  process.stdout.write('{}');

  try {
    const cwd = event && event.cwd;
    if (!cwd) return;

    const marker = path.join(cwd, '.pp-onboarded');
    if (fs.existsSync(marker)) return;

    if (!fs.existsSync(path.join(cwd, '.git'))) return;

    const manifest = hasManifest(cwd);
    if (!manifest) return;

    const log = {
      timestamp: new Date().toISOString(),
      session: event.session_id || 'unknown',
      cwd,
      manifest,
      actions: []
    };

    const specifyDir = path.join(cwd, '.specify');
    if (!fs.existsSync(specifyDir)) {
      try {
        const result = stubConstitution(cwd);
        log.actions.push({ component: 'A-stub-constitution', ...result });
      } catch (e) {
        log.actions.push({ component: 'A-stub-constitution', error: String(e && e.message || e) });
        logErr('stub-constitution', e);
      }
    } else {
      log.actions.push({ component: 'A-stub-constitution', skipped: 'specify-dir-already-present' });
    }

    try {
      fs.writeFileSync(marker, JSON.stringify(log, null, 2), 'utf8');
    } catch (e) {
      logErr('write-marker', e);
    }
  } catch (e) {
    logErr('main', e);
  }
})();
