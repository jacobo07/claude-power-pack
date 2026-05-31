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

  // Capture stdin so the wrapped hook still gets the SessionStart payload.
  // Strip UTF-8 BOM defensively (PowerShell test harnesses inject one;
  // production Claude Code stdin is BOM-less but cheap to guard).
  let payload = '';
  try {
    const raw = fs.readFileSync(0, 'utf8');
    payload = (raw && raw.charCodeAt(0) === 0xFEFF)
      ? raw.slice(1) : raw;
  } catch (stdinErr) {
    note('stdin read failed (continuing anyway)', stdinErr);
  }

  // Spawn detached. Pipe the captured payload via stdin to the child.
  const child = spawn(wrappedCmd, wrappedArgs, {
    detached: true,
    stdio: ['pipe', 'ignore', 'ignore'],
    windowsHide: true,
  });

  // Write the captured payload and close stdin so the child does not block.
  try {
    if (payload) {
      child.stdin.write(payload);
    }
    child.stdin.end();
  } catch (writeErr) {
    note('child stdin write failed', writeErr);
  }

  child.unref();
  note(`SPAWNED detached pid=${child.pid || '?'} cmd=${wrappedCmd}`);
  process.exit(0);
} catch (err) {
  note('wrapper threw', err);
  process.exit(0);
}
