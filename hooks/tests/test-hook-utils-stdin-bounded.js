#!/usr/bin/env node
/**
 * V-UTILS-* -- hook-utils.readStdin, and the difference between "resolved" and
 * "exited".
 *
 * The old helper looked bounded: it had a timer, and on that timer it resolved
 * {}. Callers got their object on schedule. THE PROCESS STILL HUNG, because the
 * 'data' listener stayed attached to a flowing stream, and an attached listener
 * is a referenced libuv handle. The event loop never emptied.
 *
 * That distinction is the whole file. A promise settling is a fact about the
 * CALLER. A process exiting is a fact about the PROCESS. A helper can deliver
 * the first perfectly while leaving a node process alive forever holding an
 * inherited pipe -- which is what kg-sync-hook.js was doing, measured at 11.6
 * minutes with zero CPU and a dead parent, while this was being written.
 *
 * So every gate here asserts on the CHILD PROCESS EXITING with stdin held open
 * forever. A test that merely awaited readStdin() in-process would have passed
 * against the broken version, which is precisely how this survived.
 *
 * V-UTILS-MUTANT-HANGS runs the OLD implementation inline. Without it, the
 * green above it could mean the helper is fixed or could mean stdin happens to
 * close by itself in this harness -- and those need opposite responses.
 */
'use strict';

const { spawn } = require('child_process');
const path = require('path');

const UTILS = path.join(__dirname, '..', 'hook-utils.js').replace(/\\/g, '/');
const EXIT_WAIT_MS = 10000;
const HANG_WAIT_MS = 3000;

const passes = [];
const fails = [];
const spawned = [];

const ok = (g, ev) => { passes.push(g); console.log(`[OK]   ${g} -- ${ev}`); };
const bad = (g, ev) => { fails.push(g); console.log(`[FAIL] ${g} -- ${ev}`); };

/**
 * Spawn a child whose stdin is a pipe we NEVER close and NEVER write to -- what
 * a hook inherits when its wrapper died mid-flight. stdout IS drained here, on
 * purpose: this file is about the read side, and leaving it undrained would
 * import the separate write-side hang (see test-pipe-write-liveness.js) and
 * make every failure ambiguous between the two.
 */
function run(code, waitMs) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const child = spawn(process.execPath, ['-e', code], { stdio: ['pipe', 'pipe', 'pipe'] });
    spawned.push(child);
    let out = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { out += d; });
    let settled = false;
    const done = (exited, code2) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ exited, code: code2, ms: Date.now() - t0, out: out.trim() });
    };
    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch {}
      done(false, null);
    }, waitMs);
    child.on('exit', (c) => done(true, c));
    child.on('error', (e) => done(true, `SPAWN-ERROR:${e && e.message}`));
  });
}

const REQ = `const {readStdin}=require(${JSON.stringify(UTILS)});`;

// The old implementation, verbatim in shape: a timer that resolves but never
// detaches. This is the mutant, and it must hang.
const OLD_IMPL = `
function readStdinOld(timeoutMs){
  return new Promise((resolve)=>{
    let input='';
    const timer=setTimeout(()=>resolve({}),timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data',c=>input+=c);
    process.stdin.on('end',()=>{clearTimeout(timer);try{resolve(JSON.parse(input));}catch{resolve({});}});
  });
}
readStdinOld(500).then(()=>{console.log('RESOLVED');});
`;

async function main() {
  // --- The mutant. Drives the defect so the gate below is not a tautology.
  const mutant = await run(OLD_IMPL, HANG_WAIT_MS);
  if (!mutant.exited && /RESOLVED/.test(mutant.out)) {
    ok('V-UTILS-MUTANT-HANGS',
      `old impl RESOLVED its promise and the process was STILL ALIVE at ${HANG_WAIT_MS}ms ` +
      '(killed) -- resolved is not exited, which is the entire defect');
  } else if (!mutant.exited) {
    ok('V-UTILS-MUTANT-HANGS',
      `old impl still alive at ${HANG_WAIT_MS}ms (killed); its RESOLVED line did not reach us, ` +
      'so only the hang is evidenced here, not the resolve');
  } else {
    bad('V-UTILS-MUTANT-HANGS',
      `old impl EXITED in ${mutant.ms}ms -- the defect does not reproduce in this harness, so ` +
      'V-UTILS-EXITS below proves nothing. Most likely stdin is being closed for us; check ' +
      'the stdio config before reading any green in this file');
  }

  // --- The fix. Same conditions, must exit.
  const fixed = await run(`${REQ}readStdin(500).then(()=>{console.log('RESOLVED');});`, EXIT_WAIT_MS);
  if (fixed.exited && fixed.code === 0) {
    ok('V-UTILS-EXITS',
      `hardened readStdin: process exited (code 0) in ${fixed.ms}ms with stdin never closed`);
  } else {
    bad('V-UTILS-EXITS',
      `hardened readStdin did NOT exit cleanly (exited=${fixed.exited} code=${fixed.code}) -- ` +
      `out=${JSON.stringify(fixed.out.slice(0, 200))}`);
  }

  // --- Timeout and empty must be DISTINGUISHABLE while both still yield {}.
  // This is the test a refactor back to a bare {} fails.
  const outcome = await run(
    `${REQ}readStdin(400).then(o=>{console.log(JSON.stringify({keys:Object.keys(o),json:JSON.stringify(o),st:o.__stdin}));});`,
    EXIT_WAIT_MS);
  let parsed = null;
  try { parsed = JSON.parse(outcome.out.split('\n').filter(Boolean).pop()); } catch {}
  if (parsed && parsed.st === 'timeout') {
    ok('V-UTILS-OUTCOME-TIMEOUT', 'a never-closed pipe reports __stdin=timeout, not silence');
  } else {
    bad('V-UTILS-OUTCOME-TIMEOUT',
      `expected __stdin=timeout, got ${parsed ? JSON.stringify(parsed.st) : `unparseable out=${JSON.stringify(outcome.out.slice(0, 200))}`} ` +
      '-- without this a guard cannot tell "nobody told us anything" from "there was nothing to say"');
  }

  // --- Back-compat. Existing callers must not be able to see the new field.
  if (parsed && Array.isArray(parsed.keys) && parsed.keys.length === 0 && parsed.json === '{}') {
    ok('V-UTILS-BACKCOMPAT', 'outcome is non-enumerable: Object.keys=[] and JSON.stringify={}');
  } else {
    bad('V-UTILS-BACKCOMPAT',
      `the outcome leaked into the object shape (keys=${parsed && JSON.stringify(parsed.keys)} ` +
      `json=${parsed && parsed.json}) -- every existing caller that iterates or serialises ` +
      'its payload just changed behaviour');
  }

  // --- Real input still parses. A bound that broke the happy path would be a
  // worse bug than the one it fixed.
  const happy = await run(
    `${REQ}readStdin(2000).then(o=>{console.log(JSON.stringify({v:o.tool_name,st:o.__stdin}));});` +
    "process.stdin.push(JSON.stringify({tool_name:'Bash'}));process.stdin.push(null);",
    EXIT_WAIT_MS);
  let hp = null;
  try { hp = JSON.parse(happy.out.split('\n').filter(Boolean).pop()); } catch {}
  if (hp && hp.v === 'Bash' && hp.st === 'ok') {
    ok('V-UTILS-PARSES', 'real JSON still parses and reports __stdin=ok');
  } else {
    bad('V-UTILS-PARSES',
      `happy path broken: got ${happy.out ? JSON.stringify(happy.out.slice(0, 200)) : '(no output)'} ` +
      '-- a bound that breaks normal input is worse than the hang it replaced');
  }

  await new Promise((r) => setTimeout(r, 200));
  const alive = spawned.filter((c) => c.exitCode === null && c.signalCode === null);
  if (alive.length === 0) ok('V-UTILS-NO-LEAK', `all ${spawned.length} probe children reaped`);
  else bad('V-UTILS-NO-LEAK', `${alive.length} probe child(ren) still alive: ${alive.map((c) => c.pid).join(', ')}`);

  const total = passes.length + fails.length;
  console.log(`HOOK_UTILS_STDIN=${passes.length}/${total}  threshold=${total}/${total}`);
  process.exit(fails.length === 0 ? 0 : 1);
}

main().catch((e) => {
  console.log(`[FAIL] V-UTILS-HARNESS -- probe threw: ${e && e.message}`);
  console.log('HOOK_UTILS_STDIN=HARNESS-FAILED');
  process.exit(2);
});
