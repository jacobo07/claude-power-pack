'use strict';
// ICC Phase 1 (ICC-10): a host build outside CCR's COMPAT list silently downgrades every enforce to shadow
// (CLASS 0, recurred on every host auto-update). The runtime already says so on its own status line, which nobody
// reads in a headless or scrolled session. This is the SessionStart half: read the newest CCR start receipt and, when
// it says compatible:false with an enforce mode wanted, return ONE line naming the host version and the reprobe command.
// The newest receipt belongs to the previous session (this session's plugin has not started yet); a host build is the
// same across both, so it is the right evidence. Fail-open: any error or doubt -> null. Never blocks SessionStart.
const fs = require('fs');
const path = require('path');

const MAX_AGE_MS = 7 * 24 * 3600 * 1000;
const HEAD_BYTES = 8192;

function newestReceipt(receiptsDir) {
  let best = null;
  for (const d of fs.readdirSync(receiptsDir)) {
    const dir = path.join(receiptsDir, d);
    let files;
    try { files = fs.readdirSync(dir); } catch (e) { continue; }
    for (const f of files) {
      if (!f.endsWith('.jsonl')) continue;
      let st;
      try { st = fs.statSync(path.join(dir, f)); } catch (e) { continue; }
      if (!best || st.mtimeMs > best.mtimeMs) best = { file: path.join(dir, f), mtimeMs: st.mtimeMs };
    }
  }
  return best;
}

function startEvent(file) {
  const fd = fs.openSync(file, 'r');
  try {
    const buf = Buffer.alloc(HEAD_BYTES);
    const n = fs.readSync(fd, buf, 0, HEAD_BYTES, 0);
    for (const line of buf.slice(0, n).toString('utf8').split('\n')) {
      if (!line.startsWith('{')) continue;
      try {
        const e = JSON.parse(line);
        if (e && e.ev === 'start') return e;
      } catch (err) { /* a truncated tail line is expected at the head bound */ }
    }
  } finally {
    fs.closeSync(fd);
  }
  return null;
}

function compatMissLine(stateDir, now) {
  try {
    const receiptsDir = path.join(stateDir, 'receipts');
    if (!fs.existsSync(receiptsDir)) return null;
    const best = newestReceipt(receiptsDir);
    if (!best || ((now || Date.now()) - best.mtimeMs) > MAX_AGE_MS) return null;
    const e = startEvent(best.file);
    if (!e || e.compatible !== false) return null;
    const modes = e.modes || {};
    const wanted = Object.keys(modes).some((k) => modes[k] === 'enforce');
    if (!wanted) return null;
    return '[CCR] SHADOW: host ' + (e.version || 'unknown') + ' is not in CCR COMPAT, so every enforce is downgraded to shadow '
      + '(no context savings). Reprobe: add the build to COMPAT in mods/cpp-cognitive-runtime/hooks/policy.ts after a green '
      + 'smoke, then python tools/ccr_release.py release';
  } catch (err) {
    return null;
  }
}

module.exports = { compatMissLine };
