#!/usr/bin/env node
/**
 * test_gsd_x_sh_dispatch.js -- characterizes the `sh` dispatch boundary that
 * W1 (GSDX-M05) left UNPROVEN, measured through GSD's own code path.
 *
 * WHY THIS EXISTS. gsd-x-n4/n5 recorded the open question as "does `sh` resolve
 * inside the real GSD dispatch environment", and every attempt to answer it so
 * far used a PowerShell-spawned probe -- a proxy for the thing, not the thing.
 * Measured here through `shell-command-projection.execTool`, which is what
 * `check-command-router.cjs:1100` actually calls:
 *
 *     resolveExecutableBinary('sh')  -> null
 *     execTool('sh', ['-c', ...])    -> exit 127, "sh: not found"
 *
 * `sh.exe` EXISTS on this host, twice (Git for Windows: bin\sh.exe and
 * usr\bin\sh.exe). So this is a RESOLUTION contract, never "Windows-
 * incompatible" -- present, discoverable, configured and complete are four
 * different states and only the first is true here.
 *
 * WHY IT MATTERS MORE THAN A PORTABILITY NOTE. Our manifest's only surface is a
 * `command-exit-zero` gate, and gate-predicate-evaluator.cjs:94-102 maps ANY
 * non-zero exit to `block: true`. With `blocking: true` + `onError: halt`,
 * ship.md step 2 HALTS the ship. So on this host, switching
 * `gsd_x_mission.enabled` on would halt EVERY ship, always, with
 * "command exited 127: sh: not found" -- regardless of whether any obligation
 * is open.
 *
 * That is the dangerous shape: not a gate that fails to fire, but one that
 * fires ALWAYS and looks like it is working. W1's red pole ("an open obligation
 * blocks the ship") would have passed here for entirely the wrong reason. Only
 * a negative control -- no obligations, must NOT block -- separates the two,
 * which is exactly why one is required.
 *
 * OWNERSHIP. The `sh` assumption is UPSTREAM (@opengsd/gsd-core,
 * check-command-router.cjs:1100). Nothing here patches it: there is no
 * sanctioned overlay seam on this host, and an in-place edit is vendor mutation
 * that the next update erases. What is OURS is that the manifest declares no
 * runtime requirement for a shell it cannot run without. This file keeps the
 * defect visible and fails loudly when upstream fixes it.
 *
 * Read-only. It never installs, updates, consents, or ships.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const GSD_LIB = 'C:/Users/User/.claude/gsd-core/bin/lib';
const PROJECTION = path.join(GSD_LIB, 'shell-command-projection.cjs');
const EVALUATOR = path.join(GSD_LIB, 'gate-predicate-evaluator.cjs');
const MANIFEST = path.join(
  __dirname, '..', 'capabilities', 'cpp-gsd-x-mission', 'capability.json'
);

let pass = 0;
let fail = 0;
const ok = (gate, evidence) => { pass++; console.log(`ok   ${gate}  ${evidence}`); };
const no = (gate, why) => { fail++; console.log(`FAIL ${gate}  ${why}`); };

// A missing dependency is a HARNESS failure, never a finding about the subject.
for (const p of [PROJECTION, EVALUATOR, MANIFEST]) {
  if (!fs.existsSync(p)) {
    console.log(`HARNESS-FAILED: required input missing: ${p}`);
    process.exit(2);
  }
}

const P = require(PROJECTION);
const E = require(EVALUATOR);
const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));

/** The seam exactly as check-command-router.cjs:1100 builds it. */
function shellDeps() {
  return {
    runBoundedShell(o) {
      const r = P.execTool('sh', ['-c', o.command], { cwd: o.cwd, timeout: o.timeoutMs });
      return {
        exitCode: r.exitCode,
        stdout: r.stdout || '',
        stderr: r.stderr || '',
        signal: r.signal,
        timedOut: false,
      };
    },
  };
}

// -- V-GSDXSH-SUBJECT-NEEDS-SH ----------------------------------------------
// The subject really does depend on a shell: our only gate is command-exit-zero.
{
  const gates = manifest.gates || [];
  const kinds = gates.map((g) => g && g.check && g.check.predicate && g.check.predicate.kind);
  if (gates.length > 0 && kinds.every((k) => k === 'command-exit-zero')) {
    ok('V-GSDXSH-SUBJECT-NEEDS-SH', `${gates.length} gate(s), all command-exit-zero -> sh -c`);
  } else {
    no('V-GSDXSH-SUBJECT-NEEDS-SH', `expected all command-exit-zero, got ${JSON.stringify(kinds)}`);
  }
}

// -- V-GSDXSH-CONTROL-EVALUATOR-CAN-SAY-FALSE -------------------------------
// A detector that always answers "block" would satisfy the defect gate below
// while proving nothing. Drive the evaluator with a seam that exits 0 and
// require block:false, so a block:true later is about sh and not about the
// function being always-true.
{
  const pred = { kind: 'command-exit-zero', command: 'irrelevant', timeout: 5 };
  const deps = { runBoundedShell: () => ({ exitCode: 0, stdout: '', stderr: '', signal: null, timedOut: false }) };
  const v = E.evaluatePredicate(pred, { PHASE_DIR: 'X', PHASE_NUMBER: '01', cwd: process.cwd() }, deps);
  if (v && v.block === false) {
    ok('V-GSDXSH-CONTROL-EVALUATOR-CAN-SAY-FALSE', 'exit 0 -> block:false');
  } else {
    no('V-GSDXSH-CONTROL-EVALUATOR-CAN-SAY-FALSE', `always-block detector? got ${JSON.stringify(v)}`);
  }
}

// -- V-GSDXSH-CONTROL-COMMAND-IS-SOUND --------------------------------------
// Attribute the failure to RESOLUTION, not to our command being wrong. Run the
// same shape through an explicit Git-for-Windows sh. If this exits 0, the only
// broken link is how `sh` is found.
{
  const candidates = [
    'C:/Program Files/Git/bin/sh.exe',
    'C:/Program Files/Git/usr/bin/sh.exe',
  ].filter((c) => fs.existsSync(c));

  if (candidates.length === 0) {
    no('V-GSDXSH-CONTROL-COMMAND-IS-SOUND', 'no explicit sh found; cannot attribute the failure');
  } else {
    const r = P.execTool(candidates[0], ['-c', 'echo SH_OK'], { timeout: 15000 });
    if (r.exitCode === 0 && String(r.stdout || '').includes('SH_OK')) {
      ok('V-GSDXSH-CONTROL-COMMAND-IS-SOUND', `${candidates[0]} -c echo -> exit 0`);
    } else {
      no('V-GSDXSH-CONTROL-COMMAND-IS-SOUND',
        `explicit sh also failed: exit=${r.exitCode} err=${String(r.stderr || '').slice(0, 120)}`);
    }
  }
}

// -- V-GSDXSH-DEFECT --------------------------------------------------------
// TODAY: bare `sh` does not resolve, so our REAL manifest predicate, through the
// REAL evaluator, blocks with exit 127. When upstream resolves `sh` (or ships a
// shell-free execution surface), this gate goes RED -- deliberately. Invert it
// then, and record the fixing version.
{
  const pred = manifest.gates[0].check.predicate;
  const v = E.evaluatePredicate(
    pred,
    { PHASE_DIR: path.join(__dirname, '..', 'vault', 'benchmarks', 'mission_spine'), PHASE_NUMBER: '01', cwd: process.cwd() },
    shellDeps()
  );
  const isShNotFound = v && v.block === true
    && v.details && v.details.exitCode === 127
    && /sh: not found/i.test(String(v.message || ''));

  if (isShNotFound) {
    ok('V-GSDXSH-DEFECT',
      'characterized: block:true exit:127 "sh: not found" -- the gate would halt EVERY ship');
  } else {
    no('V-GSDXSH-DEFECT',
      `sh may now resolve, or the failure changed shape. INVERT THIS GATE and record the fixing `
      + `version. verdict=${JSON.stringify(v)}`);
  }
}

console.log(`GSDXSH_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
