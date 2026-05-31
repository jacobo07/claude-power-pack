#!/usr/bin/env node
/**
 * async_wrapper.js -- generic detached spawner for slow SessionStart hooks.
 *
 * Usage in ~/.claude/settings.json:
 *   {
 *     "hooks": [{
 *       "type": "command",
 *       "command": "node \"<PP>/hooks/async_wrapper.js\" -- <real-hook-cmd> <args>"
 *     }]
 *   }
 *
 * The wrapper:
 *   1. Reads stdin (the hook payload) and writes it to a temp file
 *      so the wrapped hook still receives the SessionStart payload.
 *   2. Spawns the wrapped command DETACHED with stdio:'ignore'.
 *   3. Calls child.unref() to disconnect from the event loop.
 *   4. Calls process.exit(0) IMMEDIATELY -- typical wall time < 30 ms.
 *
 * Use ONLY for hooks that:
 *   - Do not emit additionalContext on stdout (their stdout is dropped).
 *   - Do side-effecting cleanup / watchdog work that the Owner does not
 *     need to see synchronously at SessionStart.
 *
 * Do NOT wrap hooks that produce additionalContext (the wrapper drops
 * stdout). Examples of NOT-WRAPPABLE hooks: jit_warm only because it
 * already self-detaches; restart_resume.js because its whole purpose
 * is to emit additionalContext.
 *
 * Sealed BL-LAG-001 (2026-05-31).
 */
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function note(reason, err) {
  try {
    const logDir = path.join(os.tmpdir());
    const logFile = path.join(logDir, 'pp-async-wrapper.log');
    fs.appendFileSync(logFile,
      `${new Date().toISOString()} ${reason}`
      + (err ? ` (${err && err.message ? err.message : err})` : '')
      + '\n');
  } catch (writeErr) {
    void writeErr;
  }
}

try {
  // Parse argv: everything after "--" is the wrapped command + args.
  const argv = process.argv.slice(2);
  const sep = argv.indexOf('--');
  if (sep === -1 || sep === argv.length - 1) {
    note('no -- separator or no wrapped command');
    process.exit(0);
  }
  const wrappedCmd = argv[sep + 1];
  const wrappedArgs = argv.slice(sep + 2);

  // Drain our own stdin so subprocess.run(shell=True, input=...) does not
  // sit waiting for the pipe to close. Discard the bytes -- wrapped hooks
  // do NOT receive the original SessionStart payload (sealed 2026-05-31
  // evening, BL-LAG-001 iteration 2 after empirical variance with
  // stdio:['pipe', ...] holding the parent alive 200-3700 ms on Windows).
  // Wrapped hooks must derive context from cwd / env, never from stdin.
  try {
    fs.readFileSync(0);
  } catch (stdinErr) {
    // Stdin already closed by parent -- expected, not an error.
    note('stdin drain noop', stdinErr);
  }

  // Spawn fully ignored stdio. On Windows this is the only configuration
  // where child.unref() + process.exit(0) reliably returns under 100 ms
  // even when the wrapped script runs for several seconds.
  const child = spawn(wrappedCmd, wrappedArgs, {
    detached: true,
    stdio: 'ignore',
    windowsHide: true,
  });

  child.unref();
  note(`SPAWNED detached pid=${child.pid || '?'} cmd=${wrappedCmd}`);
  process.exit(0);
} catch (err) {
  note('wrapper threw', err);
  process.exit(0);
}
