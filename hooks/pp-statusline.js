#!/usr/bin/env node
// Power Pack statusline: model | project | context meter.
//
// Standalone on purpose: no GSD files, no ./lib requires. The GSD statusline it
// replaces rescaled the meter for an autocompact buffer (48% shown at a real 40%),
// and a /gsd-update could restore that silently. This file is PP-owned.
//
// The meter shows RAW used = 100 - remaining_percentage, the same number the
// context watchdog (modules/zero-crash/hooks/context-watchdog.py) and the rollover
// wall judge. It also writes that number to <tmpdir>/claude-ctx-<session>.json,
// the bridge file the watchdog reads; without this script running the watchdog is
// blind.
//
// Orca: when Orca's statusline hook is installed, the same payload is forwarded to
// it after the line is printed. Orca's hook prints nothing itself.
//
// Guarded by tools/test_statusline_raw_pct.py (V-SL-*).
'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const STDIN_TIMEOUT_MS = 3000;
const ORCA_TIMEOUT_MS = 3000;
const BAR_SEGMENTS = 10;

// Colour bands follow the watchdog tiers: snapshot at 60%, wall at 70%.
function meterColor(used) {
  if (used < 50) return '\x1b[32m';
  if (used < 60) return '\x1b[33m';
  if (used < 70) return '\x1b[38;5;208m';
  return '\x1b[1;31m';
}

function usedPercent(remaining) {
  if (typeof remaining !== 'number' || !Number.isFinite(remaining)) return null;
  return Math.max(0, Math.min(100, Math.round(100 - remaining)));
}

function writeBridge(session, remaining, used) {
  if (!session || /[/\\]|\.\./.test(session)) return;
  const bridgePath = path.join(os.tmpdir(), `claude-ctx-${session}.json`);
  try {
    fs.writeFileSync(bridgePath, JSON.stringify({
      session_id: session,
      remaining_percentage: remaining,
      used_pct: used,
      timestamp: Math.floor(Date.now() / 1000),
    }));
  } catch (err) {
    // The line must still render; the watchdog falls back to its own estimate.
    process.stderr.write(`pp-statusline: bridge write failed: ${err.message}\n`);
  }
}

function render(data) {
  const model = (data.model && data.model.display_name) || 'Claude';
  const dir = (data.workspace && data.workspace.current_dir) || process.cwd();
  const remaining = data.context_window && data.context_window.remaining_percentage;
  const used = usedPercent(remaining);

  let meter = '';
  if (used !== null) {
    writeBridge(data.session_id || '', remaining, used);
    const filled = Math.floor(used / BAR_SEGMENTS);
    const bar = '█'.repeat(filled) + '░'.repeat(BAR_SEGMENTS - filled);
    meter = ` │ ${meterColor(used)}${bar} ${used}%\x1b[0m`;
  }
  return `\x1b[2m${model}\x1b[0m │ \x1b[2m${path.basename(dir)}\x1b[0m${meter}`;
}

function forwardToOrca(input) {
  const isWin = process.platform === 'win32';
  const hook = path.join(os.homedir(), '.orca', 'agent-hooks',
    isWin ? 'claude-statusline.cmd' : 'claude-statusline.sh');
  if (!fs.existsSync(hook)) return;
  const r = isWin
    ? spawnSync(process.env.ComSpec || 'cmd.exe', ['/d', '/c', hook],
      { input, timeout: ORCA_TIMEOUT_MS, windowsHide: true })
    : spawnSync('/bin/sh', [hook], { input, timeout: ORCA_TIMEOUT_MS });
  if (r.error) process.stderr.write(`pp-statusline: orca forward failed: ${r.error.message}\n`);
}

function main() {
  const chunks = [];
  const guard = setTimeout(() => process.exit(0), STDIN_TIMEOUT_MS);
  process.stdin.on('data', (c) => chunks.push(c));
  process.stdin.on('end', () => {
    clearTimeout(guard);
    const input = Buffer.concat(chunks);
    let data;
    try {
      data = JSON.parse(input.toString('utf8').replace(/^﻿/, ''));
    } catch (err) {
      process.stderr.write(`pp-statusline: bad payload: ${err.message}\n`);
      return;
    }
    process.stdout.write(render(data));
    forwardToOrca(input);
  });
}

if (require.main === module) main();

module.exports = { render, usedPercent };
