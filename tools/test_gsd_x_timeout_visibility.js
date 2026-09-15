#!/usr/bin/env node
'use strict';
// V-GSDX-TIMEOUT-VISIBILITY
//
// The defect this pins, measured 2026-09-15: a child killed at the cap and a
// child that ran and correctly had nothing to say produced the IDENTICAL
// observable -- no stdout -- and the heartbeat could not separate them either,
// because the heartbeat is written by the child. A killed child records nothing,
// so the counter reported only its own successes: an instrument structurally
// incapable of counting its misses, which reads healthy exactly when it is not.
//
// Every run here uses an isolated CLAUDE_STATE_DIR. A gate that writes the
// production heartbeat would corrupt the very number it exists to protect.

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOOK = path.resolve(__dirname, '..', 'hooks', 'gsd_x_tier.js');
let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log('  OK   ' + id + '  ' + ev); };
const no = (id, ev) => { fail++; console.log('  FAIL ' + id + '  ' + ev); };

const HEAVY = 'restart the production server and redeploy the plugin jar to the live node, then verify the world data survived';
const TRIVIAL = 'fix the typo in the readme title';

function runHook(script, prompt, extraEnv) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gsdx-hb-'));
  const payload = JSON.stringify({
    session_id: 'gate', hook_event_name: 'UserPromptSubmit', prompt, cwd: process.cwd(),
  });
  const res = spawnSync(process.execPath, [script], {
    input: payload, encoding: 'utf8', timeout: 60000, windowsHide: true,
    env: { ...process.env, CLAUDE_STATE_DIR: dir, ...(extraEnv || {}) },
  });
  let hb = {};
  try {
    hb = JSON.parse(fs.readFileSync(path.join(dir, 'gsd-x-heartbeat.json'), 'utf8'));
  } catch (_) { hb = {}; }
  return { stdout: (res.stdout || '').trim(), status: res.status, hb, dir };
}

// --- 1. The hook never costs a turn, whatever happens ----------------------
{
  const r = runHook(HOOK, HEAVY);
  if (r.status === 0) ok('EXIT-ZERO', 'advisory exits 0 on the real path');
  else no('EXIT-ZERO', 'exit=' + r.status);
}

// --- 2. RED BRANCH: a child killed at the cap is COUNTED, not silent -------
// Drive it by building a mutant whose cap cannot be met. This is the only way
// to reach the branch deterministically; waiting for real contention is a
// flake, not a test.
{
  const src = fs.readFileSync(HOOK, 'utf8');
  const mutated = src.replace(/const CHILD_TIMEOUT_MS = \d+;/, 'const CHILD_TIMEOUT_MS = 1;');
  if (mutated === src) {
    no('TIMEOUT-LOCATED', 'could not find CHILD_TIMEOUT_MS to drive the red branch');
  } else {
    ok('TIMEOUT-LOCATED', 'cap constant located');
    // The mutant MUST live beside the real hook. The hook resolves its child as
    // path.resolve(__dirname, '..', 'modules', 'gsd_x', 'cli.py'), so a mutant
    // written to the temp directory resolves that to a path which does not
    // exist and the hook exits BEFORE spawning -- the branch under test is never
    // reached and the gate reports a clean miss. Found the hard way: the first
    // version of this file did exactly that and read as "timeout not counted".
    const mutantPath = path.join(path.dirname(HOOK), '.gsd_x_tier_cap1_' + process.pid + '.js');
    fs.writeFileSync(mutantPath, mutated, 'utf8');
    const r = runHook(mutantPath, HEAVY);
    if (r.stdout === '') ok('TIMEOUT-SILENT', 'a killed child still emits nothing to the user');
    else no('TIMEOUT-SILENT', 'killed child emitted ' + r.stdout.length + ' bytes');
    const n = Number(r.hb.child_timeouts) || 0;
    if (n >= 1) ok('TIMEOUT-COUNTED', 'child_timeouts=' + n + ' -- the miss is now visible');
    else no('TIMEOUT-COUNTED', 'child_timeouts=' + n + ' -- the instrument still cannot see its own miss');
    if (r.hb.last_failure_kind === 'child_timeouts') ok('TIMEOUT-KIND', 'kind recorded');
    else no('TIMEOUT-KIND', 'kind=' + r.hb.last_failure_kind);
    if (!('judgements' in r.hb)) ok('DENOM-UNTOUCHED', 'a dead child did not inflate the rate denominator');
    else no('DENOM-UNTOUCHED', 'judgements was written by the failure path: ' + r.hb.judgements);
    try { fs.unlinkSync(mutantPath); }
    catch (e) { console.log('  note: mutant left at ' + mutantPath + ' (' + e.code + ')'); }
  }
}

// --- 3. GREEN CONTROL: a healthy run must NOT be counted as a timeout ------
// Without this, a countFailure() that fired unconditionally would pass part 2
// and look like a working detector.
{
  const r = runHook(HOOK, TRIVIAL);
  const n = Number(r.hb.child_timeouts) || 0;
  if (n === 0) ok('GREEN-NO-FALSE-TIMEOUT', 'a completed child records no timeout');
  else no('GREEN-NO-FALSE-TIMEOUT', 'child_timeouts=' + n + ' on a healthy run');
}

// --- 4. Kill switch: off means no GSD X behaviour at all -------------------
{
  const r = runHook(HOOK, HEAVY, { CLAUDE_GSDX: 'off' });
  if (r.stdout === '' && r.status === 0) ok('KILL-SWITCH', 'CLAUDE_GSDX=off is silent and harmless');
  else no('KILL-SWITCH', 'stdout=' + r.stdout.length + ' exit=' + r.status);
  if (!('child_timeouts' in r.hb) && !('child_failures' in r.hb)) ok('KILL-SWITCH-CLEAN', 'disabled hook writes no failure counters');
  else no('KILL-SWITCH-CLEAN', 'disabled hook wrote counters');
}

const total = pass + fail;
console.log('GSDX_TIMEOUT_VISIBILITY=' + pass + '/' + total + '  threshold=' + total + '/' + total);
process.exit(fail === 0 ? 0 : 1);
