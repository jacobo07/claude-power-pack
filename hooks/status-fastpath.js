#!/usr/bin/env node
// UserPromptSubmit shim for tools/status_fastpath.py (ctx-same-pane S4). Fail-open: any error,
// a timeout or empty output prints nothing and exits 0, so the prompt reaches the model unchanged.
'use strict';
const { spawnSync } = require('child_process');
const path = require('path');

if ((process.env.CPP_STATUS_FASTPATH || '').toLowerCase() === 'off') process.exit(0);
const PY = process.env.CPP_PYTHON || (process.platform === 'win32'
  ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3');
const SCRIPT = path.join(__dirname, '..', 'tools', 'status_fastpath.py');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => { input += c; });
process.stdin.on('end', () => {
  try {
    const r = spawnSync(PY, [SCRIPT], {
      // Python enforces its own 3 s projection deadline; this outer bound only covers interpreter start-up
      // on a loaded host (measured 0.3-1 s), and a kill here is a pass-through, never a block.
      input, encoding: 'utf8', timeout: 6000, windowsHide: true,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    const out = (r.stdout || '').trim();
    if (r.status === 0 && out) {
      const parsed = JSON.parse(out);
      if (parsed.decision === 'block' && typeof parsed.reason === 'string') process.stdout.write(JSON.stringify(parsed));
    }
  } catch (e) {
    process.stderr.write(`status-fastpath: pass-through (${e.message})\n`);
  }
  process.exit(0);
});
