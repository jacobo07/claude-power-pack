#!/usr/bin/env node
/**
 * V-PIPE-* -- the SECOND blocking primitive, measured 2026-09-16.
 *
 * bfb40a1 fixed a hook that parked inside `fs.readFileSync(0)` on a stdin pipe
 * that never closed, and that fix is correct: V-PIPE-STDIN-BOUNDED below drives
 * the exact template with the pipe held open forever and it exits.
 *
 * It is not sufficient, because a hook has TWO pipes.
 *
 * A hook whose shell wrapper has died inherits a stdout pipe with NO READER. On
 * Windows, Node's stdout-to-a-pipe is SYNCHRONOUS (documented: pipes are sync on
 * Windows and Linux, async on macOS). Once the OS pipe buffer fills and nobody
 * drains it, `process.stdout.write` blocks the event loop exactly the way
 * readFileSync(0) did -- zero CPU, dead parent, held handle, forever.
 *
 * MEASURED with a .NET spawner (RedirectStandardOutput, never read):
 *      1024 exited   4096 exited   8192 BLOCKED   16384 BLOCKED   512K BLOCKED
 * and the 512 KB child logged its `start` marker and NEVER logged the marker on
 * the line after its write -- parked INSIDE the write, not at exit.
 *
 * WHY THIS IS NOT MERELY ANOTHER INSTANCE. The stdin fix worked because an async
 * read YIELDS, so a timer can be scheduled to bound it. A Windows pipe write
 * cannot be made async. There is no version of that fix that keeps the write and
 * adds a timeout beside it, because the timer is never scheduled.
 *
 *      Against a synchronous blocking primitive the only in-process defense is
 *      NOT TO PERFORM IT. The bound must be on the SIZE, not on the time.
 *
 * THE THRESHOLD IS A PROPERTY OF THE SPAWNER, NOT OF NODE. The buffer belongs to
 * whoever created the pipe, so a .NET parent and a Node parent do not agree, and
 * neither is automatically the harness's number. This file measures the Node
 * spawner and PRINTS the value rather than asserting a constant, because a
 * constant copied from the wrong spawner is a budget that lies. What is asserted
 * is the part that does not vary: that SOME reachable size blocks, and that the
 * child is parked inside the write when it does.
 *
 * If a platform change ever makes the write async, V-PIPE-OVER-BUFFER goes red
 * and someone gets to delete a restriction. That is the right way for a
 * constraint to expire.
 */
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

// Asymmetric on purpose, and each direction errs safe. A blocked child is
// blocked FOREVER, so a short window cannot manufacture a false "blocked". A
// healthy child merely has to start node, so a generous window protects the
// controls on a contended host -- and this host was measured at 369 MB free of
// 32 GB while this file was being written.
const BLOCK_WAIT_MS = 3000;
const EXIT_WAIT_MS = 10000;

// Per-PID: this estate runs dozens of panes at once and a shared marker file
// would let one run read another's evidence.
const MARK = (tag) => path.join(os.tmpdir(), `pipe-liveness-${process.pid}-${tag}.mark`);

const passes = [];
const fails = [];
const spawned = [];
const marks = [];

const ok = (g, ev) => { passes.push(g); console.log(`[OK]   ${g} -- ${ev}`); };
const bad = (g, ev) => { fails.push(g); console.log(`[FAIL] ${g} -- ${ev}`); };

/**
 * Run a child with stdout/stderr on pipes we NEVER read and stdin held open.
 *
 * TWO INSTRUMENT FAILURES ARE DESIGNED OUT HERE, both found by running:
 *
 * 1. A child that FAILED TO SPAWN fires 'error', not 'exit'. Reading that as
 *    "it exited" turns "never ran" into "ran fine". MEASURED: an 8 KB case
 *    reported EXITED in 232 ms -- below the 524 ms startup floor the control
 *    measured in the same run. `reached` is now the discriminator and it cannot
 *    be forged, because the child writes it to a FILE.
 * 2. stdout is the subject, so the child cannot use it to report on itself.
 *    Every marker goes to a file for exactly that reason.
 */
function runUndrained(args, waitMs, markerFile) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    try { if (markerFile && fs.existsSync(markerFile)) fs.unlinkSync(markerFile); } catch {}
    // 'pipe' on all three is the point: we never attach a 'data' listener, so
    // nothing drains them -- the state a hook is left in when its wrapper dies.
    const child = spawn(process.execPath, args, { stdio: ['pipe', 'pipe', 'pipe'] });
    spawned.push(child);
    let settled = false;
    let spawnError = null;
    const done = (exited, code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      let reached = null;
      try {
        reached = markerFile && fs.existsSync(markerFile)
          ? fs.readFileSync(markerFile, 'utf8').trim() : null;
      } catch {}
      resolve({ exited, code, ms: Date.now() - t0, pid: child.pid, reached, spawnError });
    };
    const timer = setTimeout(() => {
      // Kill BEFORE resolving. A test for orphaned processes that orphans a
      // process has refuted itself.
      try { child.kill('SIGKILL'); } catch {}
      done(false, null);
    }, waitMs);
    child.on('exit', (code) => done(true, code));
    child.on('error', (e) => { spawnError = e && e.message; done(true, 'SPAWN-ERROR'); });
  });
}

// The child marks the file AFTER the write returns, so:
//   no marker + no exit  -> parked INSIDE the write   (the defect)
//   marker   + exit      -> the write completed       (under the buffer)
//   no marker + exit     -> it never ran              (instrument failure)
const writeN = (n, marker) => [
  '-e',
  `process.stdout.write('x'.repeat(${n}));` +
  `require('fs').writeFileSync(${JSON.stringify(marker)},'wrote-${n}');` +
  'process.exit(0);',
];

const SIZES = [4096, 16384, 65536, 262144, 1048576];

async function main() {
  // --- CONTROL. Without it, every "blocked" below could mean only that the
  // probe cannot observe an exit at all, and this file would be a machine for
  // producing the answer it expected.
  const cm = MARK('control'); marks.push(cm);
  const quiet = await runUndrained(
    ['-e', `require('fs').writeFileSync(${JSON.stringify(cm)},'ran');process.exit(0);`],
    EXIT_WAIT_MS, cm);
  if (quiet.exited && quiet.code === 0 && quiet.reached === 'ran') {
    ok('V-PIPE-CONTROL-EXITS', `no-write child ran and exited in ${quiet.ms}ms`);
  } else {
    bad('V-PIPE-CONTROL-EXITS',
      `a child that writes NOTHING did not cleanly run+exit (exited=${quiet.exited} ` +
      `code=${quiet.code} reached=${quiet.reached} err=${quiet.spawnError}) -- the probe is ` +
      'broken and every other verdict in this file is unsafe to read');
  }

  // --- Ladder. Report the threshold; assert only what does not vary.
  const results = [];
  for (const n of SIZES) {
    const m = MARK(`w${n}`); marks.push(m);
    const r = await runUndrained(writeN(n, m), r0(n), m);
    results.push({ n, ...r });
  }
  function r0(n) { return n <= 4096 ? EXIT_WAIT_MS : BLOCK_WAIT_MS; }

  const line = results.map((r) =>
    `${r.n}=${r.exited ? (r.reached ? 'exited' : 'NEVER-RAN') : 'BLOCKED'}`).join('  ');
  console.log(`       node-spawner ladder: ${line}`);

  const neverRan = results.filter((r) => r.exited && !r.reached);
  if (neverRan.length) {
    bad('V-PIPE-LADDER-RAN',
      `${neverRan.length} child(ren) exited without reaching their marker ` +
      `(sizes ${neverRan.map((r) => r.n).join(', ')}) -- these never executed the write, ` +
      'so their "exited" says nothing about the buffer');
  } else {
    ok('V-PIPE-LADDER-RAN', `all ${results.length} ladder children actually executed`);
  }

  const blocked = results.filter((r) => !r.exited);
  if (blocked.length) {
    const first = blocked[0];
    // The second half of the claim: parked INSIDE the write. A child blocked
    // somewhere else would be a different bug wearing the same symptom.
    if (first.reached === null) {
      ok('V-PIPE-OVER-BUFFER-BLOCKS',
        `${first.n} B to an undrained pipe still running after ${BLOCK_WAIT_MS}ms with its ` +
        'post-write marker ABSENT -- parked inside the write (killed). Node-spawner ' +
        `threshold is between ${SIZES[SIZES.indexOf(first.n) - 1] || 0} and ${first.n} B`);
    } else {
      bad('V-PIPE-OVER-BUFFER-BLOCKS',
        `${first.n} B blocked but its post-write marker EXISTS -- the write returned and the ` +
        'child is stuck somewhere else. Same symptom, different mechanism; do not file this ' +
        'under the pipe-buffer finding until it is diagnosed');
    }
  } else {
    bad('V-PIPE-OVER-BUFFER-BLOCKS',
      `no size up to ${SIZES[SIZES.length - 1]} B blocked under the NODE spawner. Either the ` +
      'platform made pipe writes async (good: the size cap can be revisited) or this probe ' +
      'stopped draining-by-not-draining (bad: the instrument died). The .NET spawner blocked ' +
      'at 8192 B on this same host, so a disagreement here indicts one of the two -- read ' +
      'both before believing either');
  }

  // --- The template bfb40a1 installed, driven with stdin held open forever.
  // Proves the READ side is genuinely solved, so the remaining exposure is the
  // WRITE side and nothing else.
  const bs = await runUndrained(
    ['-e',
      'let d=false;const f=()=>{if(d)return;d=true;clearTimeout(t);' +
      'try{process.stdin.removeAllListeners();process.stdin.pause();}catch{}' +
      'process.exit(0);};const t=setTimeout(f,800);' +
      "process.stdin.setEncoding('utf-8');process.stdin.on('data',()=>{});" +
      "process.stdin.on('end',f);process.stdin.on('error',f);"],
    EXIT_WAIT_MS, null);
  if (bs.exited && bs.code === 0) {
    ok('V-PIPE-STDIN-BOUNDED-EXITS',
      `bounded async read exited in ${bs.ms}ms with stdin never closed`);
  } else {
    bad('V-PIPE-STDIN-BOUNDED-EXITS',
      `the bounded-async template did NOT cleanly exit (exited=${bs.exited} code=${bs.code}) ` +
      "-- bfb40a1's fix does not hold here and Class A migration is built on sand");
  }

  // --- No leak. This suite spawns children DESIGNED to hang; leaving one
  // behind would manufacture the population it exists to remove.
  await new Promise((r) => setTimeout(r, 250));
  const alive = spawned.filter((c) => c.exitCode === null && c.signalCode === null);
  if (alive.length === 0) ok('V-PIPE-NO-LEAK', `all ${spawned.length} probe children reaped`);
  else bad('V-PIPE-NO-LEAK',
    `${alive.length} probe child(ren) still alive: ${alive.map((c) => c.pid).join(', ')}`);

  for (const m of marks) { try { fs.unlinkSync(m); } catch {} }

  const total = passes.length + fails.length;
  console.log(`PIPE_LIVENESS=${passes.length}/${total}  threshold=${total}/${total}`);
  process.exit(fails.length === 0 ? 0 : 1);
}

main().catch((e) => {
  // A probe that crashed judged nothing. Say so rather than exiting 0.
  for (const m of marks) { try { fs.unlinkSync(m); } catch {} }
  console.log(`[FAIL] V-PIPE-HARNESS -- probe threw: ${e && e.message}`);
  console.log('PIPE_LIVENESS=HARNESS-FAILED');
  process.exit(2);
});
