#!/usr/bin/env node
// CANONICAL SOURCE - Power Pack repo. Deployed to ~/.claude/hooks/ via
// tools/settings_merger.py register-auto-test-gate (Owner-pasted, never
// auto-installed). Edit here, re-run the consolidator.
/**
 * auto-test-gate.js - PreToolUse hook for the Auto-Testing Skill.
 *
 * Source spec: claude-power-pack/vault/specs/auto-testing-gate.md
 * Plan:        claude-power-pack/vault/plans/auto-testing-skill-2026-05-23.md
 *
 * Triggers on any Bash or PowerShell `git commit` invocation. Resolves
 * the repo root, then spawns
 *   python modules/auto-testing/auto_test.py --gate --cwd <root>
 * and reads ONE JSON verdict object from stdout.
 *
 * Exit code translation:
 *   verdict=pass    -> exit 0
 *   verdict=fail    -> exit 2 (commit BLOCKED; reason printed to stderr)
 *   verdict=ceiling -> exit 0 + warn-line in .auto-spawned.log
 *   verdict=timeout -> exit 0 + WARN-TIMEOUT in .auto-spawned.log
 *   verdict=skip    -> exit 0 silently
 *
 * Fail-OPEN: any internal error, missing python, missing module, etc.
 * results in exit 0. A broken gate must never block real commits.
 *
 * D2 budget guard: 28s wall-clock cap on the child. At 28s the hook
 * kills the child and emits WARN-TIMEOUT (commit proceeds).
 *
 * Opt-out: CLAUDEPP_AUTOTEST_DISABLE=1 in env (passed through to the
 * child, which emits verdict=skip immediately).
 *
 * Recursion guard: if CLAUDEPP_AUTOTEST_RUNNING=1 the hook exits 0
 * silently (set by the runner when subprocess-invoking claude.exe).
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const child_process = require('child_process');

const HOOK_BUDGET_MS = 28000;  // 28s hook-side cap (gate runner has 30s)

const HOME = os.homedir();
const PP_REPO = path.join(HOME, '.claude', 'skills', 'claude-power-pack');
const AUTO_TEST_PY = path.join(
  PP_REPO, 'modules', 'auto-testing', 'auto_test.py'
);
const RESULTS_DIR = path.join(PP_REPO, 'vault', 'test-results');
const WARN_LOG = path.join(RESULTS_DIR, '.auto-spawned.log');

// Two complementary patterns, OR-joined:
//  1. PRIMARY: literal `git ... commit` in any shell shape (bare,
//     absolute-path, with -C/--no-pager flags between). Word-boundary
//     `\bgit\b` rejects `gitlab` etc.
//  2. LOOSE: `commit` followed by a flag that is uniquely git's
//     (-F / -m / -am / -S / --amend / --message / --file / --signoff).
//     Catches PowerShell `& $g -C $pp commit -F ...` where the git
//     binary is held in a variable and the literal `git` token never
//     appears in the command string.
// Excludes `git commit -h` / `git commit --help`. False positives on
// `echo "git commit later"` are acceptable - downstream runner
// returns verdict=skip on an empty staged diff.
const COMMIT_RE_PRIMARY = /\bgit(?:\.exe)?\b['"`]?[\s\S]*?\bcommit\b(?!\s*(?:-h\b|--help\b))/i;
const COMMIT_RE_LOOSE = /\bcommit\b\s+(?:-F\b|-m\b|-am\b|-S\b|-s\b|--amend\b|--message\b|--file\b|--signoff\b)/i;

function failOpen(reason) {
  try { process.stderr.write('auto-test-gate: fail-open: ' + reason + '\n'); }
  catch (_) { /* noop */ }
  process.exit(0);
}

function warnLine(record) {
  try {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
    const line = JSON.stringify({ ts: new Date().toISOString(), ...record });
    fs.appendFileSync(WARN_LOG, line + '\n', 'utf-8');
  } catch (_) { /* noop */ }
}

function readStdin() {
  try {
    const buf = fs.readFileSync(0, 'utf-8');
    return buf ? JSON.parse(buf) : {};
  } catch (e) {
    failOpen('stdin parse: ' + e.message);
  }
}

function findPython() {
  const fromEnv = process.env.CLAUDEPP_PY_EXE;
  if (fromEnv && fs.existsSync(fromEnv)) return fromEnv;
  const candidates = [
    path.join(HOME, 'AppData', 'Local', 'Programs', 'Python',
              'Python312', 'python.exe'),
    path.join(HOME, 'AppData', 'Local', 'Programs', 'Python',
              'Python311', 'python.exe'),
    'python.exe',
    'python3',
    'python',
  ];
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch (_) { /* noop */ }
  }
  return 'python';
}

function resolveRepoRoot(cwd) {
  // Walk up from cwd looking for .git. If none, return cwd as-is so
  // the runner can still detect the project type.
  let d = path.resolve(cwd || process.cwd());
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(d, '.git'))) return d;
    const parent = path.dirname(d);
    if (parent === d) break;
    d = parent;
  }
  return cwd || process.cwd();
}

function extractCommand(input) {
  // Harness shapes the JSON as { tool_name: "Bash", tool_input: { command: "..." } }.
  const ti = input && input.tool_input;
  if (!ti) return '';
  return ti.command || ti.cmd || ti.script || '';
}

function looksLikeGitCommit(cmd) {
  if (!cmd || typeof cmd !== 'string') return false;
  return COMMIT_RE_PRIMARY.test(cmd) || COMMIT_RE_LOOSE.test(cmd);
}

function spawnGate(repoRoot) {
  const py = findPython();
  return new Promise((resolve) => {
    let settled = false;
    let buf = '';
    let errBuf = '';
    const t0 = Date.now();
    const child = child_process.spawn(
      py,
      [AUTO_TEST_PY, '--gate', '--cwd', repoRoot, '--mode', 'fast'],
      {
        cwd: repoRoot,
        windowsHide: true,
        env: process.env,
      },
    );
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try { child.kill('SIGKILL'); } catch (_) { /* noop */ }
      resolve({
        ok: false,
        verdict: 'timeout',
        reason: 'hook-side WARN-TIMEOUT after ' + HOOK_BUDGET_MS + 'ms',
        elapsed_ms: Date.now() - t0,
        raw: buf,
        stderr: errBuf,
      });
    }, HOOK_BUDGET_MS);
    child.stdout.on('data', (d) => { buf += d.toString('utf-8'); });
    child.stderr.on('data', (d) => { errBuf += d.toString('utf-8'); });
    child.on('error', (e) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({
        ok: false, verdict: 'error',
        reason: 'spawn error: ' + e.message,
        elapsed_ms: Date.now() - t0,
        raw: '', stderr: errBuf,
      });
    });
    child.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      // Parse the last non-empty line of stdout as JSON.
      let parsed = null;
      const lines = buf.split('\n').map(l => l.trim()).filter(Boolean);
      for (let i = lines.length - 1; i >= 0; i--) {
        try { parsed = JSON.parse(lines[i]); break; } catch (_) { /* noop */ }
      }
      if (!parsed) {
        resolve({
          ok: false, verdict: 'error',
          reason: 'gate produced no JSON (exit ' + code + ')',
          elapsed_ms: Date.now() - t0,
          raw: buf, stderr: errBuf,
        });
        return;
      }
      resolve({
        ok: true,
        verdict: parsed.verdict || 'unknown',
        reason: parsed.reason || '',
        elapsed_ms: Date.now() - t0,
        raw: buf, stderr: errBuf, parsed,
      });
    });
  });
}

async function main() {
  // RECURSION GUARD - if a child claude.exe re-fires the chain.
  if (process.env.CLAUDEPP_AUTOTEST_RUNNING === '1') {
    process.exit(0);
  }
  // Opt-out short-circuit.
  if (process.env.CLAUDEPP_AUTOTEST_DISABLE === '1') {
    warnLine({ verdict: 'skipped-by-env', reason: 'CLAUDEPP_AUTOTEST_DISABLE=1' });
    process.exit(0);
  }

  const input = readStdin();
  const cmd = extractCommand(input);

  if (!looksLikeGitCommit(cmd)) {
    process.exit(0);  // not a commit; silent pass-through
  }

  const cwd = input.cwd || process.cwd();
  const repoRoot = resolveRepoRoot(cwd);

  const res = await spawnGate(repoRoot);
  warnLine({
    verdict: res.verdict,
    reason: (res.reason || '').slice(0, 200),
    elapsed_ms: res.elapsed_ms,
    repo: repoRoot,
    cmd_excerpt: cmd.slice(0, 120),
  });

  if (res.verdict === 'fail') {
    try {
      process.stderr.write(
        '\n[auto-test-gate] BLOCKED: ' + (res.reason || 'gate verdict=fail') + '\n'
        + 'Generated test failed. See vault/test-results/ for the artifact.\n'
      );
    } catch (_) { /* noop */ }
    process.exit(2);
  }

  // Any other verdict (pass, ceiling, timeout, skip, error) lets the
  // commit through. The warn log preserves the signal for review.
  process.exit(0);
}

try { main(); }
catch (e) { failOpen('top-level: ' + e.message); }
