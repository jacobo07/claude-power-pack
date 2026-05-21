/**
 * hook-runtime.js - shared boilerplate for PP SessionStart/Stop Node hooks.
 *
 * Source of truth: PP repo (claude-power-pack/hooks/_shared/).
 * Loaded by deployed hooks via absolute path:
 *   const rt = require(path.join(os.homedir(), '.claude/skills/claude-power-pack/hooks/_shared/hook-runtime'));
 *
 * Why absolute path: deployment to ~/.claude/hooks/ copies one .js file at
 * a time via settings_merger.py register-zero-command. Resolving _shared
 * from PP source at runtime means the deploy stays a single-file copy.
 *
 * Why this module exists: 3 new hooks (zero-command-bootstrap.js,
 * first-time-project.js, background-verifier.js) all need readStdin +
 * BOM-strip + JSON-parse + logErr + project-detection. Without sharing,
 * each hook is ~95 LOC, ~70% boilerplate. With sharing, ~25 LOC of unique
 * logic each. Code-review agent flagged this as the highest-ROI cleanup.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const STDIN_TIMEOUT_MS_DEFAULT = 2000;

const MANIFEST_NAMES = Object.freeze([
  'package.json', 'pyproject.toml', 'Cargo.toml',
  'go.mod', 'pom.xml', 'build.gradle', 'build.gradle.kts',
  'mix.exs', 'composer.json', 'Gemfile',
]);

/**
 * Strip a UTF-8 BOM if present. PowerShell 5.1's pipe-to-native-exe
 * always writes one; harness-direct invocations don't. Robust to both.
 */
function stripBom(s) {
  return (s && s.charCodeAt(0) === 0xFEFF) ? s.slice(1) : s;
}

/**
 * Read stdin with timeout, strip BOM, parse JSON. Returns {} on any
 * failure (parse error, timeout, stdin closed). Never throws.
 */
function readStdinJson(timeoutMs = STDIN_TIMEOUT_MS_DEFAULT) {
  return new Promise(resolve => {
    let buf = '';
    const t = setTimeout(() => resolve(_safeParse(buf)), timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => { clearTimeout(t); resolve(_safeParse(buf)); });
    process.stdin.on('error', () => { clearTimeout(t); resolve(_safeParse(buf)); });
  });
}

function _safeParse(raw) {
  try {
    const s = stripBom(raw || '').trim();
    return s ? JSON.parse(s) : {};
  } catch (_) {
    return {};
  }
}

/**
 * Build a per-hook error logger. Logs to ~/.claude/logs/<logName>.log
 * with one line per error. Never throws.
 */
function makeLogErr(logName) {
  const logFile = path.join(os.homedir(), '.claude', 'logs', `${logName}.log`);
  return function logErr(where, e) {
    try {
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      const line = `${new Date().toISOString()} [${where}] ${e && e.stack || e && e.message || String(e)}\n`;
      fs.appendFileSync(logFile, line, 'utf8');
    } catch (logFail) {
      try { process.stderr.write(`${logName} log fail: ${logFail.message}\n`); } catch (_unreachable) { /* I/O fully closed */ }
    }
  };
}

/**
 * Return the first manifest filename found in cwd, or null. Project-detect
 * signal: .git + at least one of these means "this is an active dev project".
 */
function detectManifest(cwd) {
  for (const m of MANIFEST_NAMES) {
    if (fs.existsSync(path.join(cwd, m))) return m;
  }
  return null;
}

/**
 * Wrap a SessionStart/Stop hook body. Handles stdin read + immediate
 * `{}` stdout emit + top-level catch + per-hook error logging. Each
 * caller supplies only the unique work via `handler(event, logErr)`.
 *
 *   const rt = require('.../hook-runtime');
 *   const logErr = rt.makeLogErr('zero-command-bootstrap');
 *   rt.runHook(logErr, async (event) => { ... });
 */
function runHook(logErr, handler) {
  return (async () => {
    let event = {};
    try {
      event = await readStdinJson();
    } catch (e) {
      logErr('parse-stdin', e);
    }
    process.stdout.write('{}');
    try {
      await handler(event);
    } catch (e) {
      logErr('main', e);
    }
  })();
}

module.exports = {
  MANIFEST_NAMES,
  STDIN_TIMEOUT_MS_DEFAULT,
  stripBom,
  readStdinJson,
  makeLogErr,
  detectManifest,
  runHook,
};
