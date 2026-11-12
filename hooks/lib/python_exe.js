'use strict';
// The Python a hook should spawn, derived from the host instead of a hardcoded install path.
// Order: PYTHON_BIN (explicit override) -> the newest per-user CPython 3.x under the CURRENT home
// (any Python3NN folder, not one pinned minor version) -> an absolute `python` / `python3` found on PATH
// (skipping the Microsoft Store alias in WindowsApps, which opens the Store instead of running) ->
// the bare name, which callers that check existence will correctly report as missing.
//
// Why it changed (2026-11-12): the previous version pinned Python312. On a host with only Python313 it
// returned the bare name 'python'; the dispatcher then ran fs.existsSync('python.exe'), which looks for a
// RELATIVE file, logged "interpreter missing" and skipped EVERY Python hook, including the context
// watchdog that performs the automatic /kclear rollover at the context wall. Nothing surfaced it.
const fs = require('fs');
const os = require('os');
const path = require('path');

function newestPerUserPython(home) {
  const base = path.join(home, 'AppData', 'Local', 'Programs', 'Python');
  let entries = [];
  try { entries = fs.readdirSync(base); } catch (_) { return null; } // no per-user installs: fall through
  const found = entries
    .map(name => ({ name, minor: (/^Python3(\d+)$/.exec(name) || [])[1] }))
    .filter(e => e.minor !== undefined)
    .sort((a, b) => Number(b.minor) - Number(a.minor))
    .map(e => path.join(base, e.name, 'python.exe'))
    .filter(p => fs.existsSync(p));
  return found[0] || null;
}

function onPath(names, env, platform) {
  const dirs = String(env.PATH || env.Path || '').split(path.delimiter).filter(Boolean);
  for (const dir of dirs) {
    if (platform === 'win32' && /[\\/]WindowsApps[\\/]?$/i.test(dir)) continue; // Store alias stub
    for (const n of names) {
      const p = path.join(dir, n);
      if (fs.existsSync(p)) return p;
    }
  }
  return null;
}

function pythonExe(env = process.env, platform = process.platform, home = os.homedir()) {
  if (env.PYTHON_BIN) return env.PYTHON_BIN;
  if (platform === 'win32') {
    return newestPerUserPython(home) || onPath(['python.exe'], env, platform) || 'python';
  }
  return onPath(['python3', 'python'], env, platform) || 'python3';
}

module.exports = { pythonExe, newestPerUserPython, onPath };
