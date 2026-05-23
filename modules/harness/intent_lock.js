#!/usr/bin/env node
'use strict';
/**
 * intent_lock.js — Intent-Lock workspace mutex (Power Pack harness).
 *
 * Purpose: prevent two concurrent Claude panes from corrupting the same
 * physical worktree by interleaving Write/Edit/commit operations. Soft-pause
 * policy: a mutating tool is denied ONLY when another LIVE pane already holds
 * the lock for the SAME physical worktree and the lock is fresh (< 5 min).
 * Reads are never blocked. Different physical worktrees never collide
 * (surfaced as information only). Fail-open: any internal error allows the
 * tool through — the lock must never break a session.
 *
 * Wiring: loaded by ~/.claude/hooks/hook-dispatcher.js in the
 * PreToolUse-default bundle. Contract: module.exports = { run(data) }
 * returning the same JSON a standalone PreToolUse hook would emit. The
 * dispatcher translates `decision:'deny'` -> hookSpecificOutput.
 *
 * Conflict key (Q2): realpath(worktree) + live PID. Liveness triad (gap #6):
 * deny requires (different PID) AND (PID alive) AND (stored worktree ===
 * current) AND (lock age < STALE_MS). PID alone never denies (PID reuse).
 *
 * Self-test:  node modules/harness/intent_lock.js --self-test   (6 cases)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const STALE_MS = 5 * 60 * 1000;      // 5 min — lock auto-expires (Q1)
const REFRESH_THROTTLE_MS = 30 * 1000; // ts-refresh cadence (gap #7)
const MUTATING_TOOLS = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit']);

function loadAtomic() {
  // Live lib (skills/claude-power-pack/lib/atomic_write.js). Fall back to a
  // local tmp+rename if the lib ever relocates — lock must still function.
  try {
    return require(path.join(__dirname, '..', '..', 'lib', 'atomic_write.js'));
  } catch (_) {
    return {
      atomicWriteJson(fp, obj) {
        const tmp = fp + '.tmp.' + process.pid;
        fs.writeFileSync(tmp, JSON.stringify(obj, null, 2));
        fs.renameSync(tmp, fp);
      },
    };
  }
}
const atomic = loadAtomic();

function resolveWorktree(data) {
  const raw = (data && data.cwd)
    || process.env.CLAUDE_PROJECT_DIR
    || process.cwd();
  try { return fs.realpathSync(raw); } catch (_) { return path.resolve(raw); }
}

function readBranch(worktree) {
  // Cheap branch read — no git spawn on the PreToolUse hot path. Handles
  // both a normal .git dir and a worktree .git file (gitdir: pointer).
  try {
    const gitPath = path.join(worktree, '.git');
    let headFile;
    const st = fs.statSync(gitPath);
    if (st.isDirectory()) {
      headFile = path.join(gitPath, 'HEAD');
    } else {
      const m = /gitdir:\s*(.+)\s*/.exec(fs.readFileSync(gitPath, 'utf8'));
      if (!m) return null;
      let gd = m[1].trim();
      if (!path.isAbsolute(gd)) gd = path.resolve(worktree, gd);
      headFile = path.join(gd, 'HEAD');
    }
    const head = fs.readFileSync(headFile, 'utf8').trim();
    const rm = /ref:\s*refs\/heads\/(.+)/.exec(head);
    return rm ? rm[1].trim() : head.slice(0, 12);
  } catch (_) { return null; }
}

function isAlive(pid) {
  if (!pid || pid === process.pid) return true;
  try {
    process.kill(pid, 0);
    return true;                 // signal delivered -> alive
  } catch (e) {
    if (e && e.code === 'EPERM') return true; // exists, no permission
    return false;                // ESRCH (or anything else) -> dead
  }
}

function lockPathFor(worktree) {
  return path.join(worktree, '.claude', 'intent.lock');
}

function readLock(lockPath) {
  try {
    const raw = fs.readFileSync(lockPath, 'utf8');
    const obj = JSON.parse(raw.charCodeAt(0) === 0xFEFF ? raw.slice(1) : raw);
    if (obj && typeof obj === 'object' && obj.pid) return obj;
    return null;
  } catch (_) { return null; }
}

function writeLock(lockPath, worktree, data, prevTs) {
  try {
    fs.mkdirSync(path.dirname(lockPath), { recursive: true });
    const goal = (data && data.intent_goal)
      || process.env.CPP_INTENT_GOAL
      || '';
    const rec = {
      pid: process.pid,
      branch: readBranch(worktree),
      worktree,
      goal: String(goal).slice(0, 240),
      ts: Date.now(),
      tool: (data && data.tool_name) || '',
    };
    if (prevTs) rec.acquired_ts = prevTs;
    atomic.atomicWriteJson(lockPath, rec);
    return rec;
  } catch (_) { return null; }
}

function isMutating(data) {
  const tn = data && data.tool_name;
  if (!tn) return false;
  if (MUTATING_TOOLS.has(tn)) return true;
  if (tn === 'Bash') {
    const cmd = data.tool_input && (data.tool_input.command || data.tool_input.cmd);
    if (typeof cmd === 'string' && /\bgit\s+commit\b/.test(cmd)) return true;
  }
  return false;
}

function targetsOwnLock(data, lockPath) {
  const ti = data && data.tool_input;
  if (!ti) return false;
  const fp = ti.file_path || ti.path || ti.notebook_path;
  if (!fp) return false;
  try { return path.resolve(fp) === path.resolve(lockPath); }
  catch (_) { return false; }
}

function ageMs(lock) {
  const t = lock && Number(lock.ts);
  if (!t || Number.isNaN(t)) return Number.POSITIVE_INFINITY;
  return Date.now() - t;
}

/**
 * Core decision. Returns a PreToolUse JSON object.
 *  - allow / passthrough: { continue: true }
 *  - soft-pause:          { decision: 'deny', reason, additionalContext }
 */
function decide(data) {
  const worktree = resolveWorktree(data);
  const lockPath = lockPathFor(worktree);

  // Never evaluate a tool whose target IS the lock file (gap #7: no
  // self-deny / re-entry on the lock's own write).
  if (targetsOwnLock(data, lockPath)) return { continue: true };

  // Reads / non-mutating tools are never blocked (Q1).
  if (!isMutating(data)) return { continue: true };

  const lock = readLock(lockPath);

  if (!lock) {
    writeLock(lockPath, worktree, data, null);
    return { continue: true };
  }

  // Different physical worktree -> information only, never blocks (Q2).
  if (path.resolve(lock.worktree || '') !== path.resolve(worktree)) {
    return { continue: true };
  }

  // Same worktree, our own PID -> refresh ts (throttled, gap #7) and allow.
  if (Number(lock.pid) === process.pid) {
    if (ageMs(lock) > REFRESH_THROTTLE_MS) {
      writeLock(lockPath, worktree, data, lock.acquired_ts || lock.ts);
    }
    return { continue: true };
  }

  // Same worktree, foreign PID. Liveness triad (gap #6).
  const alive = isAlive(Number(lock.pid));
  const fresh = ageMs(lock) < STALE_MS;

  if (alive && fresh) {
    const mins = Math.max(0, Math.round((STALE_MS - ageMs(lock)) / 60000));
    const topo = [
      'INTENT-LOCK: another live Claude pane holds this worktree.',
      '  worktree : ' + worktree,
      '  held_by  : pid ' + lock.pid
        + (lock.branch ? ' on branch ' + lock.branch : ''),
      '  goal     : ' + (lock.goal || '(none declared)'),
      '  this_pane: pid ' + process.pid
        + (readBranch(worktree) ? ' on branch ' + readBranch(worktree) : ''),
      'Soft-pause: mutating tools are held until the other pane finishes '
        + 'or the lock self-expires (~' + mins + ' min of inactivity). '
        + 'Reads are unaffected. Run a non-mutating command, switch to a '
        + 'separate worktree, or wait for auto-expiry.',
    ].join('\n');
    return {
      decision: 'deny',
      reason: 'Intent-Lock: worktree held by live pid ' + lock.pid
        + ' (self-expires in ~' + mins + ' min).',
      additionalContext: topo,
    };
  }

  // Stale (foreign PID dead OR lock older than STALE_MS) -> reclaim + allow.
  writeLock(lockPath, worktree, data, null);
  return { continue: true };
}

function run(data) {
  try {
    return decide(data || {});
  } catch (_) {
    return { continue: true }; // fail-open: lock never breaks a session
  }
}

module.exports = { run, decide, isAlive, resolveWorktree, lockPathFor };

// --------------------------------------------------------------------------
// Self-test (require.main). Six cases, real filesystem, real child process.
// --------------------------------------------------------------------------
function selfTest() {
  const { spawnSync, spawn } = require('child_process');
  const assert = require('assert');
  const results = [];
  const rec = (name, ok, detail) => {
    results.push({ name, ok });
    process.stdout.write((ok ? 'PASS ' : 'FAIL ') + name
      + (detail ? '  — ' + detail : '') + '\n');
  };

  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'intentlock-'));
  const wtA = fs.realpathSync(fs.mkdtempSync(path.join(root, 'wtA-')));
  const wtB = fs.realpathSync(fs.mkdtempSync(path.join(root, 'wtB-')));
  const lpA = lockPathFor(wtA);
  const writeTool = { tool_name: 'Write', cwd: wtA,
    tool_input: { file_path: path.join(wtA, 'x.txt') } };

  // Spawn a guaranteed-alive foreign process (sleeps 60s).
  const child = spawn(process.execPath,
    ['-e', 'setTimeout(()=>{},60000)'], { stdio: 'ignore' });
  const foreignAlivePid = child.pid;

  try {
    // 1. Acquire: no lock -> create + allow.
    let r = run(writeTool);
    let lk = readLock(lpA);
    rec('1 acquire-on-empty',
      r.continue === true && lk && Number(lk.pid) === process.pid,
      'pid=' + (lk && lk.pid));

    // 2. Same-pid passthrough: our own fresh lock -> allow, no deny.
    r = run(writeTool);
    rec('2 same-pid-passthrough', r.continue === true && !r.decision);

    // 3. Foreign live pid, same worktree, fresh -> DENY.
    atomic.atomicWriteJson(lpA, {
      pid: foreignAlivePid, branch: 'other', worktree: wtA,
      goal: 'rival', ts: Date.now(), tool: 'Edit' });
    r = run(writeTool);
    rec('3 foreign-live-fresh-deny',
      r.decision === 'deny' && /Intent-Lock/.test(r.reason || ''),
      'decision=' + r.decision);

    // 4. Foreign live pid but STALE ts (6 min old) -> reclaim + allow.
    atomic.atomicWriteJson(lpA, {
      pid: foreignAlivePid, branch: 'other', worktree: wtA,
      goal: 'rival', ts: Date.now() - 6 * 60 * 1000, tool: 'Edit' });
    r = run(writeTool);
    lk = readLock(lpA);
    rec('4 foreign-stale-ts-reclaim',
      r.continue === true && !r.decision
        && lk && Number(lk.pid) === process.pid);

    // 5. Foreign DEAD pid, fresh ts -> reclaim + allow.
    const deadPid = 0x7fffffff; // not a live process
    assert.strictEqual(isAlive(deadPid), false);
    atomic.atomicWriteJson(lpA, {
      pid: deadPid, branch: 'other', worktree: wtA,
      goal: 'ghost', ts: Date.now(), tool: 'Edit' });
    r = run(writeTool);
    lk = readLock(lpA);
    rec('5 foreign-dead-pid-reclaim',
      r.continue === true && !r.decision
        && lk && Number(lk.pid) === process.pid);

    // 6. Read tool is never blocked, even under a foreign live lock.
    atomic.atomicWriteJson(lpA, {
      pid: foreignAlivePid, branch: 'other', worktree: wtA,
      goal: 'rival', ts: Date.now(), tool: 'Edit' });
    r = run({ tool_name: 'Read', cwd: wtA,
      tool_input: { file_path: path.join(wtA, 'x.txt') } });
    rec('6 read-never-blocked', r.continue === true && !r.decision);

    // Bonus: different worktree never collides (Q2 info-only).
    atomic.atomicWriteJson(lpA, {
      pid: foreignAlivePid, branch: 'other', worktree: wtA,
      goal: 'rival', ts: Date.now(), tool: 'Edit' });
    r = run({ tool_name: 'Write', cwd: wtB,
      tool_input: { file_path: path.join(wtB, 'y.txt') } });
    rec('7 cross-worktree-no-collision',
      r.continue === true && !r.decision);
  } finally {
    try { child.kill(); } catch (_) { /* noop */ }
    try { fs.rmSync(root, { recursive: true, force: true }); } catch (_) { /* noop */ }
  }

  const failed = results.filter(x => !x.ok).length;
  process.stdout.write('\n' + (results.length - failed) + '/'
    + results.length + ' passed\n');
  process.exit(failed === 0 ? 0 : 1);
}

if (require.main === module) {
  if (process.argv.includes('--self-test')) {
    selfTest();
  } else {
    // CLI hook mode (parity with standalone PreToolUse hooks).
    let input = '';
    const t = setTimeout(() => {
      try { process.stdout.write(JSON.stringify({ continue: true })); }
      catch (_) { /* noop */ }
      process.exit(0);
    }, 3000);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { input += c; });
    process.stdin.on('end', () => {
      clearTimeout(t);
      let data = {};
      try { data = JSON.parse(input); } catch (_) { /* keep empty */ }
      try { process.stdout.write(JSON.stringify(run(data))); }
      catch (_) { /* noop */ }
      process.exit(0);
    });
  }
}
