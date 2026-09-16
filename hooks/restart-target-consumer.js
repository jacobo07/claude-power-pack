#!/usr/bin/env node
/**
 * restart-target-consumer.js — SessionStart hook (BL-NULL-ERROR Step 5).
 *
 * Companion to restart-claude.ps1's Write-RestartTarget. The main script writes
 *   ~/.claude/lazarus/restart-target.json
 * with the session_id that /restart was supposed to land on. When the next
 * session starts, this hook compares:
 *
 *   - target.session_id (what we asked /restart to relaunch with --resume)
 *   - currentSessionId (what we actually got, from the SessionStart payload)
 *
 * Outcomes:
 *   - Marker missing  -> no /restart in flight, exit 0 silently.
 *   - Marker > 90s    -> stale (race lost or different event); delete + exit 0.
 *   - Match           -> /restart worked. Delete marker. exit 0.
 *   - Mismatch        -> SendKeys race, helper crash, or wrapper missed.
 *                        Delete marker, then spawn detached
 *                        ~/.claude/scripts/lazarus-revive.ps1 -Launch
 *                        -OnlySession <target.session_id>. Append a forensic
 *                        line to ~/.claude/lazarus/restart-target-misses.log.
 *                        exit 0.
 *
 * Always emits `{}` on stdout (Claude Code SessionStart hook contract).
 * Never throws — every IO failure is swallowed so the bootup pipeline survives.
 *
 * Input shape (stdin JSON):
 *   { session_id: "<uuid>", source: "startup"|"resume"|..., cwd: "<path>" }
 *
 * Output: `{}` (silence is success). Errors on stderr; exit 0 always.
 *
 * Disable via env: RESTART_TARGET_CONSUMER=off
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const TARGET_FILE = path.join(os.homedir(), '.claude', 'lazarus', 'restart-target.json');
const MISS_LOG    = path.join(os.homedir(), '.claude', 'lazarus', 'restart-target-misses.log');
const REVIVE_PS1  = path.join(os.homedir(), '.claude', 'scripts', 'lazarus-revive.ps1');
const STALE_MS    = 90 * 1000;

// Always emit valid hook output FIRST so a later crash can't poison the
// SessionStart pipeline.
process.stdout.write('{}');

if (process.env.RESTART_TARGET_CONSUMER === 'off') process.exit(0);

function safeRead(p) {
  try { return fs.readFileSync(p, 'utf8'); } catch (_) { return null; }
}
function safeUnlink(p) {
  try { fs.unlinkSync(p); } catch (_) {}
}
function logMiss(line) {
  try { fs.appendFileSync(MISS_LOG, line); } catch (_) {}
}

// 2026-09-16 -- STDIN DEADLOCK FIX. The read below was `fs.readFileSync(0,
// 'utf8')` at TOP LEVEL, which BLOCKS THE EVENT LOOP: if the pipe never closes
// the process parks at zero CPU forever and no in-process watchdog can save it,
// because no timer is ever scheduled. The harness's per-hook budget kills the
// shell WRAPPER; a timeout kills the direct child only, and the survivor holds
// the inherited stdout pipe. bfb40a1 has the live measurement.
//
// This hook consumes a single-shot marker on SessionStart, so a stall here
// delays every /restart.
//
// STRUCTURE. There was no main() to make async -- the whole script was top
// level -- so the body is wrapped in an async IIFE. CommonJS has no top-level
// await, so there is no smaller change that works. The body itself is UNCHANGED
// apart from indentation: this commit fixes a liveness bug and must not alter
// what the consumer does with the marker.
const { readStdinRaw, armHardExit } = require('./hook-utils');

const STDIN_BUDGET_MS = 2000;
const HARD_EXIT = armHardExit(STDIN_BUDGET_MS + 3000);

(async function main() {
  let input = {};
  const { raw: stdinRaw } = await readStdinRaw(STDIN_BUDGET_MS);
  clearTimeout(HARD_EXIT);
  try {
    // Defensive BOM strip on stdin — real Claude Code hook IPC is BOM-free, but
    // tools that pipe via files (testing, certain shells) may inject one.
    // Unreadable and empty both land as '' here, exactly as the old catch did:
    // no session_id, which the mismatch path below already handles as '<none>'.
    const stdinStripped = stdinRaw ? stdinRaw.replace(/^﻿/, '') : '';
    input = stdinStripped ? JSON.parse(stdinStripped) : {};
  } catch (_) {}
  const currentSid = input.session_id || '';

  if (!fs.existsSync(TARGET_FILE)) process.exit(0);

  let target;
  try {
    // Strip UTF-8 BOM defensively — PowerShell 5.1 `Set-Content -Encoding UTF8`
    // writes EF BB BF, which JSON.parse rejects. The producer side also uses
    // BOM-free UTF8Encoding($false) now, but stripping here makes the hook
    // resilient against any future writer that forgets.
    const raw = safeRead(TARGET_FILE);
    const stripped = raw ? raw.replace(/^﻿/, '') : null;
    target = JSON.parse(stripped);
  } catch (_) {
    // Malformed marker: delete and bail.
    safeUnlink(TARGET_FILE);
    process.exit(0);
  }

  if (!target || typeof target !== 'object' || !target.session_id) {
    safeUnlink(TARGET_FILE);
    process.exit(0);
  }

  const ts = Date.parse(target.iso_timestamp || '');
  if (isNaN(ts) || Date.now() - ts > STALE_MS) {
    // Stale marker; some other event fired the SessionStart, not our /restart.
    safeUnlink(TARGET_FILE);
    process.exit(0);
  }

  // Consume the marker regardless of match — single-shot semantics. A stale
  // marker can never re-fire a revive on a subsequent SessionStart.
  safeUnlink(TARGET_FILE);

  if (target.session_id === currentSid) {
    // Clean /restart: typed --resume <sid> landed on the same session_id.
    process.exit(0);
  }

  // Mismatch path. Spawn lazarus-revive against the target as a self-heal.
  // Detached + unref so this hook returns immediately and the spawned process
  // outlives us.
  const args = [
    '-NoProfile',
    '-WindowStyle', 'Hidden',
    '-ExecutionPolicy', 'Bypass',
    '-File', REVIVE_PS1,
    '-Launch',
    '-OnlySession', target.session_id
  ];
  let launched = false;
  try {
    const child = spawn('powershell.exe', args, {
      detached: true,
      stdio: 'ignore',
      windowsHide: true
    });
    child.unref();
    launched = true;
  } catch (e) {
    process.stderr.write('restart-target-consumer: spawn failed: ' + (e && e.message ? e.message : e) + '\n');
  }

  const iso = new Date().toISOString();
  logMiss(
    `${iso} mismatch current=${currentSid || '<none>'} target=${target.session_id} ` +
    `relaunch_path=${target.relaunch_path || 'unknown'} producer_pid=${target.producer_pid || '?'} ` +
    `revive_spawned=${launched}\n`
  );

  process.exit(0);
})().catch(() => {
  // An async IIFE cannot be wrapped in a synchronous try/catch, so without this
  // a rejection escapes as an unhandled rejection -- and a process that merely
  // logs one stays ALIVE holding the inherited stdout pipe. Always exit.
  process.exit(0);
});
