'use strict';
/**
 * wrapper-selfheal.js -- heal a console-allocator re-infection of the LIVE
 * hook registry, on the next event, from inside the dispatcher.
 *
 * WHY HERE. A third-party installer re-registers its hook wrapped as
 * `conhost.exe --headless cmd.exe /d /c <hook>` across ~11 events. A wrapped
 * entry writes the console init/teardown escapes (ESC[2J erase, ESC[H home,
 * ESC]0;title, and the ?9001/?1004 input-mode toggles) straight to the Owner's
 * terminal, out of band, and discards the wrapped hook's own output.
 *
 * The repair already existed in two places and neither can reach this case:
 *   - `bin/repair-hook-wrappers.ps1`, called by the launcher, heals a pane at
 *     BIRTH -- but the current build reloads hooks LIVE, so a pane that started
 *     clean is re-infected while it runs and the launcher never runs again.
 *   - `tools/fix_conhost_hook_leak.py --apply`, run by hand -- which is a chore,
 *     and a chore is not a fix.
 * The dispatcher runs on essentially every event, so it is the one place that
 * observes the re-infection within one event of it happening.
 *
 * WHAT IT DOES NOT DO. It contains NO unwrap logic. It detects, and dispatches
 * the existing fixer. A second implementation of the rewrite would be correct
 * on the day it was written and silently divergent afterwards, and the rewrite
 * is the half that must not be wrong -- it edits the Owner's global settings.
 *
 * COST WHEN HEALTHY: one statSync plus one small stamp read. The scan only
 * runs when settings.json has actually moved.
 *
 * FAIL-OPEN, ABSOLUTE. Every failure returns a verdict and throws nothing. A
 * guard that can break the dispatcher is worse than the screen-clearing it was
 * written to stop.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const HOME = process.env.USERPROFILE || process.env.HOME || os.homedir();

// Console allocators: a wrapper that allocates its own console writes to the
// terminal out of band. `conhost --headless` is the shape measured in this
// estate; the others are named so a NEW shape is reported rather than missed.
// Detection is deliberately wider than the fixer's repair: an allocator this
// module can see but not fix is reported once and left alone (settings.json
// does not move, so the stamp suppresses any retry storm) -- which is a
// visible open problem, where silence would be an invisible one.
const ALLOCATORS = [
  { name: 'conhost-headless', rx: /\bconhost(\.exe)?\b[\s\S]{0,200}?--headless/i, fixable: true },
  { name: 'cmd-start', rx: /cmd(\.exe)?["']?\s+\/[a-z]*c\s+start\s/i, fixable: false },
  { name: 'windows-terminal', rx: /\bwt(\.exe)?["']?\s/i, fixable: false },
];

/**
 * Decide whether a registry is infected, from its STRUCTURE.
 *
 * A raw-text regex cannot answer this, and the failure is silent. On this host
 * the live shape is split across two fields:
 *     "command": "C:\\WINDOWS\\System32\\conhost.exe",
 *     "args": ["--headless", "C:\\WINDOWS\\System32\\cmd.exe", "/d", "/c", ...]
 * A pattern requiring `conhost` and `--headless` inside one string matches
 * nothing there, so the guard calls eleven wrapped events healthy. Measured
 * 2026-09-23: that is exactly what this guard did on its first live run, and a
 * neighbouring pattern (-WindowStyle, since removed) returned a plausible
 * verdict that hid the miss -- a detector whose blind spot wears the costume
 * of a decision.
 *
 * So: parse, join each entry's command with its args, and test the argv the
 * hook will actually run. The parser is part of the guard.
 *
 * The raw fallback exists only for a file that does not parse -- mid-write, or
 * corrupt -- and is labelled, because "could not read the structure" is not
 * the same evidence as "the structure is clean".
 */
function detect(raw) {
  let doc = null;
  try { doc = JSON.parse(raw); } catch (_) { doc = null; }
  if (!doc || !doc.hooks || typeof doc.hooks !== 'object') {
    const loose = ALLOCATORS.find(a => a.rx.test(raw));
    return loose ? Object.assign({}, loose, { source: 'raw-fallback' }) : null;
  }
  for (const event of Object.keys(doc.hooks)) {
    const groups = Array.isArray(doc.hooks[event]) ? doc.hooks[event] : [];
    for (const group of groups) {
      const entries = group && Array.isArray(group.hooks) ? group.hooks : [];
      for (const h of entries) {
        if (!h) continue;
        const argv = [h.command].concat(Array.isArray(h.args) ? h.args : [])
          .filter(x => typeof x === 'string').join(' ');
        const a = ALLOCATORS.find(x => x.rx.test(argv));
        if (a) return Object.assign({}, a, { source: 'structured', event });
      }
    }
  }
  return null;
}
// NOT an allocator, and the live registry proved it on this guard's first real
// run: `-WindowStyle Hidden` was in the ALLOCATORS list and matched a HEALTHY
// settings.json, so `clean` was a branch this host could never reach. It is
// the opposite of the defect -- the estate's own documented way to spawn
// without a window flash -- and a detector that flags the fix as the fault
// teaches the next reader to undo it.

const COOLDOWN_MS = 30000; // one repair dispatch per half-minute, per pane

function pythonPath() {
  const candidates = [
    process.env.CLAUDE_PYTHON,
    path.join(HOME, 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
  ].filter(Boolean);
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch (_) { /* keep looking */ }
  }
  return 'python';
}

/**
 * @param {object} opts
 *   settings   path to the live settings.json  (default ~/.claude/settings.json)
 *   stateDir   where the stamp lives           (default ~/.claude/state)
 *   fixer      path to fix_conhost_hook_leak.py
 *   now        injected clock, for the drill
 *   dispatch   injected spawner, for the drill (must not actually spawn)
 * @returns {{status:string, allocator?:string, dispatched?:boolean, reason?:string}}
 *   status is one of: unchanged | clean | dispatched | cooling | unfixable |
 *                     no-settings | error
 */
function selfHeal(opts) {
  const o = opts || {};
  const settings = o.settings || path.join(HOME, '.claude', 'settings.json');
  const stateDir = o.stateDir || process.env.CLAUDE_STATE_DIR || path.join(HOME, '.claude', 'state');
  const fixer = o.fixer || path.join(HOME, '.claude', 'skills', 'claude-power-pack',
    'tools', 'fix_conhost_hook_leak.py');
  const now = typeof o.now === 'function' ? o.now : Date.now;
  const stamp = path.join(stateDir, 'wrapper-selfheal.json');

  let st;
  try {
    st = fs.statSync(settings);
  } catch (_) {
    return { status: 'no-settings' };
  }

  let last = null;
  try { last = JSON.parse(fs.readFileSync(stamp, 'utf8')); } catch (_) { /* first run */ }

  // The cheap path, taken on every healthy event: the file has not moved, so
  // whatever the last scan concluded still holds.
  if (last && last.mtimeMs === st.mtimeMs && last.size === st.size) {
    return { status: 'unchanged' };
  }

  let raw;
  try {
    raw = fs.readFileSync(settings, 'utf8');
  } catch (_) {
    return { status: 'error', reason: 'unreadable' };
  }
  if (raw.charCodeAt(0) === 0xfeff) raw = raw.slice(1); // a BOM is not a finding

  const hit = detect(raw);
  const record = {
    mtimeMs: st.mtimeMs, size: st.size, ts: new Date(now()).toISOString(),
    allocator: hit ? hit.name : null, lastDispatch: last && last.lastDispatch || 0,
  };

  const persist = () => {
    try {
      fs.mkdirSync(stateDir, { recursive: true });
      fs.writeFileSync(stamp, JSON.stringify(record), 'utf8');
    } catch (_) { /* a stamp we cannot write costs one extra scan, nothing more */ }
  };

  if (!hit) { persist(); return { status: 'clean' }; }
  if (!hit.fixable) { persist(); return { status: 'unfixable', allocator: hit.name }; }

  if (now() - (record.lastDispatch || 0) < COOLDOWN_MS) {
    persist();
    return { status: 'cooling', allocator: hit.name };
  }

  record.lastDispatch = now();
  persist();

  try {
    const run = typeof o.dispatch === 'function' ? o.dispatch : (cmd, args) => {
      const child = spawn(cmd, args, {
        detached: true, stdio: 'ignore', windowsHide: true,
      });
      child.unref();
    };
    run(pythonPath(), [fixer, '--apply']);
  } catch (_) {
    return { status: 'error', reason: 'dispatch-failed', allocator: hit.name };
  }
  return { status: 'dispatched', allocator: hit.name, dispatched: true };
}

module.exports = { selfHeal, ALLOCATORS, COOLDOWN_MS };
