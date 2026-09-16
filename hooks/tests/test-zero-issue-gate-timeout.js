#!/usr/bin/env node
/**
 * zero-issue-gate: a gate killed at its deadline is INCONCLUSIVE, never a failure.
 *
 * Origin 2026-09-16 (KobiiSports Resort): genomic_lint ran past the hook's 30 s budget on a
 * starved host; execSync killed it before Python flushed stdout, the empty output was counted
 * as a COMPILE failure three times, and BLOCKED_DELIVERY.md was written with an EMPTY error
 * block against four files that compile.
 *
 * Both poles, driven through the real hook as a subprocess (the way the dispatcher runs it):
 *   V-ZIG-TIMEOUT-NO-BLOCK   3 timed-out runs -> no BLOCKED_DELIVERY.md, INCONCLUSIVE reported
 *   V-ZIG-TIMEOUT-NOT-PASS   ...and the timed-out gate is NOT reported as passed
 *   V-ZIG-REAL-FAIL-BLOCKS   3 genuine failures -> BLOCKED_DELIVERY.md, carrying the real output
 *   V-ZIG-PASS-CONTROL       a passing command -> ALL PASSED, no block
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const HOOK = path.join(__dirname, '..', 'zero-issue-gate.js');
const NODE = `"${process.execPath}"`;
let passes = 0, fails = 0;
const ok = (g, m) => { passes++; console.log(`[PASS] ${g}: ${m}`); };
const bad = (g, m) => { fails++; console.log(`[FAIL] ${g}: ${m}`); };

function fixture(tag, override) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `zig-${tag}-${process.pid}-`));
  fs.writeFileSync(path.join(dir, '.claude-quality-gate.json'), JSON.stringify(override));
  return dir;
}

function drive(dir, sessionId, times) {
  let stderr = '';
  for (let i = 0; i < times; i++) {
    const r = spawnSync(process.execPath, [HOOK], {
      input: JSON.stringify({ cwd: dir, session_id: sessionId }),
      encoding: 'utf8', timeout: 60000, windowsHide: true,
      env: { ...process.env, ZERO_ISSUE_GATE_ENFORCE: '' },
    });
    if (r.error) throw new Error(`HARNESS-FAILED: hook did not run: ${r.error.message}`);
    stderr += r.stderr || '';
  }
  return stderr;
}

function cleanup(dir) { try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) { /* tmp */ } }

const stamp = `${process.pid}-${Date.now()}`;

// --- timeout pole ---
{
  const dir = fixture('timeout', {
    compile: `${NODE} -e "setTimeout(function(){}, 4000)"`,
    compile_timeout_ms: 300,
    test: null,
  });
  const err = drive(dir, `zig-timeout-${stamp}`, 3);
  const blocked = fs.existsSync(path.join(dir, 'BLOCKED_DELIVERY.md'));
  if (!blocked && /COMPILE INCONCLUSIVE/.test(err) && /did not finish within 300 ms/.test(err)) {
    ok('V-ZIG-TIMEOUT-NO-BLOCK', 'three timeouts, no BLOCKED_DELIVERY.md, INCONCLUSIVE named with its budget');
  } else {
    bad('V-ZIG-TIMEOUT-NO-BLOCK', `blocked=${blocked} stderr=${JSON.stringify(err.slice(0, 300))}`);
  }
  if (!/ALL PASSED \([^)]*compile/.test(err) && !/COMPILE FAILED/.test(err)) {
    ok('V-ZIG-TIMEOUT-NOT-PASS', 'timed-out compile reported neither as passed nor as failed');
  } else {
    bad('V-ZIG-TIMEOUT-NOT-PASS', `stderr=${JSON.stringify(err.slice(0, 300))}`);
  }
  cleanup(dir);
}

// --- genuine failure pole (the block must still work) ---
{
  const dir = fixture('fail', {
    compile: `${NODE} -e "console.error('zig-real-compile-error-marker'); process.exit(1)"`,
    test: null,
  });
  drive(dir, `zig-fail-${stamp}`, 3);
  const f = path.join(dir, 'BLOCKED_DELIVERY.md');
  const body = fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : '';
  if (/Gate that failed: COMPILE/.test(body) && /zig-real-compile-error-marker/.test(body)) {
    ok('V-ZIG-REAL-FAIL-BLOCKS', 'three real failures -> BLOCKED_DELIVERY.md carrying the real error text');
  } else {
    bad('V-ZIG-REAL-FAIL-BLOCKS', `exists=${fs.existsSync(f)} body=${JSON.stringify(body.slice(0, 200))}`);
  }
  cleanup(dir);
}

// --- pass control ---
{
  const dir = fixture('pass', { compile: `${NODE} -e "0"`, test: null });
  const err = drive(dir, `zig-pass-${stamp}`, 1);
  const blocked = fs.existsSync(path.join(dir, 'BLOCKED_DELIVERY.md'));
  if (!blocked && /ALL PASSED \([^)]*compile/.test(err)) {
    ok('V-ZIG-PASS-CONTROL', 'passing compile -> ALL PASSED (compile), no block');
  } else {
    bad('V-ZIG-PASS-CONTROL', `blocked=${blocked} stderr=${JSON.stringify(err.slice(0, 300))}`);
  }
  cleanup(dir);
}

console.log(`ZIG_TIMEOUT_PASS=${passes}/${passes + fails}  threshold=4/4`);
process.exit(fails === 0 ? 0 : 1);
