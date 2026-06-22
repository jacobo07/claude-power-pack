#!/usr/bin/env node
'use strict';
// ---------------------------------------------------------------------------
// ram-guard-stop.js -- Stop-hook wrapper for tools/ram_guard.py (B1).
//
// *** SUPERSEDED / UNREGISTERED BY DESIGN (2026-06-22, restart-kclear audit PF-4) ***
// This wrapper is NOT in the Stop-chain (hook-dispatcher.js CHAIN_MAP) and NOT in
// ~/.claude/settings.json. The live RAM advisory on the Stop event is
// modules/zero-crash/hooks/ram-watchdog.js (threshold aligned to 20 GB, PF-3); the
// authoritative pressure decision is context_monitor (20/28 GB) via context-watchdog.py.
// ram_guard.py's claude_ram_mb() is still reached as a LIBRARY by context_monitor; only
// this CLI-wrapper hook is dormant. Kept as reference (gaming-mode + snapshot-before-OOM)
// for a future Owner-side wiring; do NOT register it alongside ram-watchdog.js or the
// /kclear advisory will double-fire again. See UKDL T-RAM-DEDUP-001.
//
// RAM Optimization Sprint (2026-06-04). FASE -1 forensics proved the RAM that
// crashes the host is claude.exe's own V8 heap (grew 5.9 GB -> 25 GB in one
// session), NOT the PP's ~12 MB footprint. The PP cannot kill that heap; the
// only lever is reducing context (/kclear, /compact). This hook samples
// claude.exe working-set at most once every THROTTLE_MS and, when it crosses
// the ram_guard threshold, surfaces a /kclear advisory + ensures a crash-
// recovery snapshot exists BEFORE the possible OOM.
//
// THROTTLED: a Stop fires on every turn-end; spawning python+PowerShell each
// time would be wasteful for a signal that only matters at 20 GB+. We sample
// every 5 minutes (matching the vault-heartbeat cadence). 99% of Stops return
// {continue:true} instantly.
//
// FAIL-OPEN: any error (no python, timeout, parse failure) -> {continue:true}.
// A RAM advisory must NEVER block a Stop event. Advisory text is fully
// PP-generated (only GB numbers, no file/user content) -> no redaction needed
// (HR-SECRET-006 surface is empty).
//
// REGISTRATION (Owner-side -- HR-001: auto-mode denies settings.json hook
// self-registration): add to ~/.claude/settings.json "hooks":
//   { "Stop": [ { "hooks": [ { "type": "command",
//     "command": "node \"<PP>/hooks/ram-guard-stop.js\"" } ] } ] }
// then /restart. See commands/kclear-when.md for the full block.
// ---------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const PP_PATH = path.resolve(__dirname, '..');
const RAM_GUARD_PY = path.join(PP_PATH, 'tools', 'ram_guard.py');
const PYTHON_EXE =
  'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const THROTTLE_FILE = path.join(os.tmpdir(), 'pp-ram-guard-last.txt');
const THROTTLE_MS = 5 * 60 * 1000;   // sample at most every 5 min
const EXEC_TIMEOUT_MS = 8000;        // hard cap on the probe subprocess

function emit(obj) {
  try { process.stdout.write(JSON.stringify(obj)); } catch (e) { void e; }
}

function throttled() {
  try {
    const last = parseInt(fs.readFileSync(THROTTLE_FILE, 'utf8').trim(), 10);
    return Number.isFinite(last) && (Date.now() - last) < THROTTLE_MS;
  } catch (e) { void e; return false; }
}

function stampThrottle() {
  try { fs.writeFileSync(THROTTLE_FILE, String(Date.now())); }
  catch (e) { void e; }
}

function pythonExe() {
  try { if (fs.existsSync(PYTHON_EXE)) return PYTHON_EXE; } catch (e) { void e; }
  return 'python';
}

function main() {
  // Drain stdin (Stop payload) so the pipe closes; we don't need its content.
  try { fs.readFileSync(0, 'utf8'); } catch (e) { void e; }

  if (throttled()) { emit({ continue: true }); return; }
  stampThrottle();

  let out = '';
  try {
    out = execFileSync(pythonExe(), [RAM_GUARD_PY, '--json'], {
      timeout: EXEC_TIMEOUT_MS,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      windowsHide: true,
    });
  } catch (e) {
    emit({ continue: true }); return;   // fail-open
  }

  let verdict = null;
  try {
    const s = out.replace(/^﻿/, '').trim();
    const lines = s.split('\n').filter(Boolean);
    verdict = JSON.parse(lines[lines.length - 1]);
  } catch (e) { emit({ continue: true }); return; }

  if (verdict && (verdict.level === 'warn' || verdict.level === 'critical')) {
    emit({ continue: true,
           additionalContext: '[ram_guard] ' + (verdict.advisory || '') });
  } else {
    emit({ continue: true });
  }
}

main();
