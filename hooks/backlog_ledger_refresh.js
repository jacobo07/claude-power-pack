#!/usr/bin/env node
'use strict';
/**
 * SessionStart gate for the reconciliation-ledger refresh (spec vault/specs/backlog-ledger-refresh.md).
 *
 * The ledger build measured 148 s (2026-11-16), so it NEVER runs here: this gate does cheap checks (<100 ms) and
 * may launch tools/backlog_ledger_refresh.py detached. It also delivers the previous refresh's result: the first PP
 * session start after a refresh gets ONE line with coverage, the delta vs the refresh before, and the verify verdict.
 *
 * Bounded on purpose (recurring-work-cardinality): only the PP tree this file lives in, only when the session cwd is
 * inside it, at most once per interval, one worker per tree, never under the free-memory floor.
 * Fail-open: any error returns {continue:true}. Kill switch: CPP_BACKLOG_REFRESH=off.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { spawn } = require('child_process');

const PP_ROOT = path.resolve(__dirname, '..');
const LOCK_STALE_MS = 3600 * 1000;

function stateDir(env) {
  return env.CPP_BACKLOG_STATE_DIR || path.join(os.homedir(), '.claude', 'state', 'backlog_ledger');
}

function canon(p) {
  let r = p;
  try { r = fs.realpathSync.native(p); } catch (_) { r = path.resolve(p); }
  return process.platform === 'win32' ? r.toLowerCase() : r;
}

function slugOf(root) {
  return crypto.createHash('sha1').update(canon(root)).digest('hex').slice(0, 12);
}

function inside(child, parent) {
  const c = canon(child), p = canon(parent);
  const rel = path.relative(p, c);
  return rel === '' || (!!rel && !rel.startsWith('..') && !path.isAbsolute(rel));
}

function readRows(file) {
  try {
    return fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean)
      .map((l) => { try { return JSON.parse(l); } catch (_) { return null; } }).filter(Boolean);
  } catch (_) { return []; }
}

function pct(m) { return m && m.denominator ? `${m.numerator}/${m.denominator} (${(100 * m.ratio).toFixed(1)}%)` : 'n/a'; }

function delta(cur, prev, key) {
  if (!prev || !prev[key] || !cur[key]) return '';
  const dn = cur[key].numerator - prev[key].numerator, dd = cur[key].denominator - prev[key].denominator;
  return (dn || dd) ? ` [${dn >= 0 ? '+' : ''}${dn}/${dd >= 0 ? '+' : ''}${dd}]` : ' [=]';
}

function announce(rows, now) {
  const last = rows[rows.length - 1];
  const prev = rows.slice(0, -1).reverse().find((r) => !r.error) || null;
  const ageH = ((now - last.ts * 1000) / 3600e3).toFixed(1);
  if (last.error) {
    return `Backlog ledger refresh FAILED ${ageH} h ago (head ${last.head || '?'}): ${String(last.error).slice(0, 200)}. ` +
      'The stored ledger is stale until it succeeds; run `python -m modules.backlog_autopilot.ledger --verify` to see why.';
  }
  return `Backlog ledger refreshed ${ageH} h ago (head ${last.head || '?'}): RECONCILIATION ${pct(last.reconciliation)}` +
    `${delta(last, prev, 'reconciliation')}, OPERATIONAL ${pct(last.operational)}${delta(last, prev, 'operational')}, ` +
    `VERIFY ${last.verify}${last.verify === 'FAIL' ? ' ' + JSON.stringify((last.verify_fails || []).slice(0, 3)) : ''}.`;
}

function gateRow(dir, slug, row) {
  try { fs.appendFileSync(path.join(dir, `${slug}.gate.jsonl`), JSON.stringify(row) + '\n'); } catch (_) { /* noop */ }
}

function pidAlive(pid) {
  try { process.kill(pid, 0); return true; } catch (e) { return !!(e && e.code === 'EPERM'); }
}

/**
 * A worker killed from outside (TerminateProcess, OOM, a reaped process tree) runs neither its except nor its
 * finally: no history row, lock left behind. Observed 2026-11-16 (live tree, pid 33948: lock from 19:12, no row).
 * Without this, the next start reads "worker running" for an hour and then "never refreshed", and the failure is
 * invisible. A lock whose pid is gone becomes a FAILED row dated at the lock, so it is announced and rate-limited.
 */
function reapDeadWorker(dir, slug, hist, alive) {
  const lock = path.join(dir, `${slug}.lock`);
  let text;
  try { text = fs.readFileSync(lock, 'utf8'); } catch (_) { return false; }
  const [pidS, tsS] = text.trim().split(/\s+/);
  const pid = Number(pidS);
  if (!Number.isInteger(pid) || pid <= 0 || alive(pid)) return false;
  let ts = Number(tsS);
  if (!Number.isFinite(ts) || ts <= 0) { try { ts = fs.statSync(lock).mtimeMs / 1000; } catch (_) { ts = Date.now() / 1000; } }
  const row = { ts, slug, head: null, killed: true, pid,
    error: `worker pid ${pid} died without a result (no history row, lock left): killed from outside` };
  try {
    fs.appendFileSync(hist, JSON.stringify(row) + '\n');
    fs.unlinkSync(lock);
  } catch (_) { return false; }
  gateRow(dir, slug, { ts: Date.now() / 1000, decision: 'reaped', pid, started: ts });
  return true;
}

/** The whole decision, pure enough to test: {action: 'spawn'|'skip', why, context, slug, dir}. */
function decide(payload, opts = {}) {
  const env = opts.env || process.env;
  const root = opts.root || PP_ROOT;
  const now = opts.now || Date.now();
  const free = opts.freemem != null ? opts.freemem : os.freemem();
  const out = { action: 'skip', why: '', context: '', slug: '', dir: '' };
  if (['off', '0', 'false'].includes(String(env.CPP_BACKLOG_REFRESH || '').trim().toLowerCase())) {
    out.why = 'kill switch'; return out;
  }
  const cwd = String((payload && payload.cwd) || '');
  if (!cwd || !inside(cwd, root)) { out.why = 'cwd outside the tree'; return out; }
  if (!fs.existsSync(path.join(root, 'modules', 'backlog_autopilot', 'ledger.py'))) { out.why = 'no ledger module'; return out; }
  const dir = stateDir(env);
  fs.mkdirSync(dir, { recursive: true });
  const slug = slugOf(root);
  Object.assign(out, { slug, dir });

  const hist = path.join(dir, `${slug}.history.jsonl`);
  reapDeadWorker(dir, slug, hist, opts.alive || pidAlive);
  const rows = readRows(hist);
  const marker = path.join(dir, `${slug}.announced`);
  const last = rows[rows.length - 1];
  if (last) {
    let seen = 0;
    try { seen = Number(fs.readFileSync(marker, 'utf8').trim()) || 0; } catch (_) { seen = 0; }
    if (last.ts > seen) {
      out.context = announce(rows, now);
      try { fs.writeFileSync(marker, String(last.ts)); } catch (_) { /* announce again next time: harmless */ }
    }
  }
  try {
    if (now - fs.statSync(path.join(dir, `${slug}.lock`)).mtimeMs < LOCK_STALE_MS) { out.why = 'worker running'; return out; }
  } catch (_) { /* no lock */ }
  const intervalMs = Number(env.CPP_BACKLOG_REFRESH_INTERVAL_H || 24) * 3600e3;
  if (last && now - last.ts * 1000 < intervalMs) { out.why = 'fresh'; return out; }
  const floor = Number(env.CPP_BACKLOG_REFRESH_MIN_FREE_MB || 3072) * 1048576;
  if (free < floor) {
    out.why = 'low memory';
    gateRow(dir, slug, { ts: now / 1000, decision: 'skip', why: out.why, free_mb: Math.round(free / 1048576) });
    return out;
  }
  out.action = 'spawn'; out.why = last ? 'stale' : 'never refreshed';
  return out;
}

function pyExe(env) {
  if (env.CLAUDE_PY_EXE) return env.CLAUDE_PY_EXE;
  const win = path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe');
  if (process.platform === 'win32' && fs.existsSync(win)) return win;
  return process.platform === 'win32' ? 'python' : 'python3';
}

function launch(d, opts = {}) {
  const env = opts.env || process.env;
  const root = opts.root || PP_ROOT;
  const child = spawn(pyExe(env), [path.join(root, 'tools', 'backlog_ledger_refresh.py'), '--root', root, '--slug', d.slug],
    { detached: true, stdio: 'ignore', windowsHide: true, cwd: root, env });
  child.on('error', () => { /* recorded below as spawned; the worker's own history row is the proof it ran */ });
  child.unref();
  gateRow(d.dir, d.slug, { ts: Date.now() / 1000, decision: 'spawn', why: d.why, pid: child.pid || null });
  return child.pid || null;
}

function run(payload) {
  try {
    const d = decide(payload);
    if (d.action === 'spawn') launch(d);
    if (!d.context) return { continue: true };
    return { continue: true, hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: d.context } };
  } catch (_) {
    return { continue: true };
  }
}

if (require.main === module) {
  let input = '';
  const t = setTimeout(() => { try { process.stdout.write(JSON.stringify({ continue: true })); } catch (_) { /* noop */ } process.exit(0); }, 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(input.replace(/^﻿/, '')); } catch (_) { data = {}; }
    process.stdout.write(JSON.stringify(run(data)));
    process.exit(0);
  });
} else {
  module.exports = { decide, launch, run, slugOf, inside, announce, PP_ROOT };
}
