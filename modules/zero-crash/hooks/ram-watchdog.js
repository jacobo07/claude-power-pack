#!/usr/bin/env node
/**
 * RAM Watchdog — Stop hook (BL-0019 / MC-SYS-35).
 *
 * On session-end, measures RSS of all claude.exe processes (Windows) or the
 * top-N claude/node processes (Posix). If total exceeds RSS_THRESHOLD_MB,
 * injects an additionalContext advising the user to consider /kclear at the
 * next natural pause.
 *
 * ADVISORY ONLY. This hook never auto-triggers /kclear. Per BL-0003: the
 * harness reserves slash-command dispatch as user-initiated. Hooks can advise
 * but cannot fire UI commands. Same constraint as gsd-context-monitor.js.
 *
 * Debounced once per session via tmp flag claude-ramwd-<session_id>.flag.
 * Silent (returns {}) on Posix tasklist-equivalent failure or if total < threshold.
 *
 * Performance: tasklist call ~50-150ms on Windows. Stop-hook timeout headroom
 * is 5000ms; we never exceed 1s.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const RSS_THRESHOLD_MB = 1500;
const STDIN_TIMEOUT_MS = 3000;
const FLAG_TMPL = sid => path.join(os.tmpdir(), `claude-ramwd-${sid}.flag`);

function readStdinSync(timeoutMs) {
  return new Promise(resolve => {
    let buf = '';
    const t = setTimeout(() => resolve(buf), timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => { clearTimeout(t); resolve(buf); });
  });
}

function getClaudeRssMbWindows() {
  // CSV format: "Image Name","PID","Session Name","Session#","Mem Usage"
  // Mem Usage looks like "123,456 K" — comma-separated thousands, in KB.
  let csv = '';
  try {
    csv = execSync('tasklist /FI "IMAGENAME eq claude.exe" /FO CSV /NH', {
      encoding: 'utf8',
      timeout: 2000,
      windowsHide: true,
    });
  } catch {
    return null;
  }
  let totalKb = 0;
  let count = 0;
  for (const line of csv.split(/\r?\n/)) {
    if (!line.includes('claude.exe')) continue;
    // Split CSV with quoted fields. Parse last field (mem usage).
    const m = line.match(/"([^"]*)"\s*$/);
    if (!m) continue;
    const memStr = m[1].replace(/[^0-9]/g, '');
    if (!memStr) continue;
    totalKb += Number(memStr);
    count++;
  }
  if (!count) return null;
  return { rssMb: Math.round(totalKb / 1024), processes: count };
}

function getClaudeRssMbPosix() {
  // Posix fallback: ps -eo rss=,comm= | grep claude | sum.
  let raw = '';
  try {
    raw = execSync('ps -eo rss=,comm=', { encoding: 'utf8', timeout: 2000 });
  } catch {
    return null;
  }
  let totalKb = 0;
  let count = 0;
  for (const line of raw.split('\n')) {
    if (!/claude/i.test(line)) continue;
    const m = line.trim().match(/^(\d+)\s+/);
    if (!m) continue;
    totalKb += Number(m[1]);
    count++;
  }
  if (!count) return null;
  return { rssMb: Math.round(totalKb / 1024), processes: count };
}

function getClaudeRssMb() {
  return process.platform === 'win32' ? getClaudeRssMbWindows() : getClaudeRssMbPosix();
}

(async () => {
  let payload = '';
  try { payload = await readStdinSync(STDIN_TIMEOUT_MS); } catch { /* keep empty */ }

  let event = {};
  try { event = JSON.parse(payload || '{}'); } catch { /* keep empty */ }

  const sessionId = event.session_id;
  if (!sessionId) {
    process.stdout.write(JSON.stringify({ continue: true }));
    return;
  }

  const flag = FLAG_TMPL(sessionId);
  if (fs.existsSync(flag)) {
    process.stdout.write(JSON.stringify({ continue: true }));
    return;
  }

  const measured = getClaudeRssMb();
  if (!measured) {
    process.stdout.write(JSON.stringify({ continue: true }));
    return;
  }
  const { rssMb, processes } = measured;
  if (rssMb < RSS_THRESHOLD_MB) {
    process.stdout.write(JSON.stringify({ continue: true }));
    return;
  }

  try { fs.writeFileSync(flag, '1', 'utf8'); } catch { /* best-effort */ }

  const message =
    `RAM ADVISORY (BL-0019, advisory only): claude.exe is using ` +
    `${rssMb} MB across ${processes} process(es), above the ${RSS_THRESHOLD_MB} MB ` +
    `attention threshold. At the next natural pause consider /kclear (session ` +
    `checkpoint + handoff) to release accumulated transcript state. This hook ` +
    `cannot auto-fire /kclear — slash-command dispatch is user-only (BL-0003).`;

  const out = {
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'Stop',
      additionalContext: message,
    },
  };
  process.stdout.write(JSON.stringify(out));
})();
