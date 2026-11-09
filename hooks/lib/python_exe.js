'use strict';
// The Python a hook should spawn, derived from the host instead of a hardcoded C:\Users\<name>\... path.
// Order: PYTHON_BIN (explicit override) -> the per-user Python 3.12 install under the CURRENT home (the value
// the hardcoded literal held on the author's machine) -> `python` on PATH (win32) / `python3` (elsewhere).
// A literal user path exists on one machine only; elsewhere spawn fails and the caller's fail-open/closed rule
// decides, which hid the defect (review M3 of PR #16, 2026-11-08).
const fs = require('fs');
const os = require('os');
const path = require('path');

function pythonExe(env = process.env, platform = process.platform, home = os.homedir()) {
  if (env.PYTHON_BIN) return env.PYTHON_BIN;
  if (platform === 'win32') {
    const perUser = path.join(home, 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe');
    return fs.existsSync(perUser) ? perUser : 'python';
  }
  return 'python3';
}

module.exports = { pythonExe };
