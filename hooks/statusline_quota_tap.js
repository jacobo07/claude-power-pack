#!/usr/bin/env node
// statusline_quota_tap.js -- BAMR P1 (2026-11-20): official quota source for account_governor.
//
// The statusline is the one place Claude Code hands a process its own usage picture on every
// render, at zero model cost. This tap sits in front of the real statusline (gsd-statusline.js):
// it copies the harness's `rate_limits` object (whatever shape this build sends) into
// ~/.claude/state/quota-reading.json, then forwards stdin unchanged and prints the real
// statusline's output. It never polls a usage endpoint.
//
// Honesty: when the build sends no `rate_limits`, the file says source "absent" with the
// top-level key names (names only) so the schema is discoverable; the governor then treats the
// official reading as UNKNOWN, never as zero. Fail-open for rendering: any fault here still
// prints the real statusline (or nothing), exit 0.
// Kill switch: CPP_QUOTA_TAP=off (forward only, write nothing).
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const REAL = process.env.CPP_QUOTA_TAP_TARGET || path.join(os.homedir(), '.claude', 'hooks', 'gsd-statusline.js');
const OUT = process.env.CPP_QUOTA_TAP_OUT || path.join(os.homedir(), '.claude', 'state', 'quota-reading.json');
const MIN_WRITE_S = 15;   // a statusline renders many times a minute; a reading this fresh is not rewritten

function reading(data, now) {
  const rl = data && typeof data === 'object' ? data.rate_limits : undefined;
  return {
    captured_at: now,
    cc_version: (data && data.version) || null,
    source: rl && typeof rl === 'object' ? 'harness_statusline' : 'absent',
    top_level_keys: data && typeof data === 'object' ? Object.keys(data).sort() : [],
    rate_limits: rl && typeof rl === 'object' ? rl : null,
  };
}

function writeReading(rec, out) {
  try {
    const st = fs.statSync(out);
    const prev = JSON.parse(fs.readFileSync(out, 'utf8'));
    const same = JSON.stringify(prev.rate_limits) === JSON.stringify(rec.rate_limits) && prev.source === rec.source;
    if (same && (Date.now() - st.mtimeMs) / 1000 < MIN_WRITE_S) return false;
  } catch (e) { /* first write or unreadable: write */ }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const tmp = `${out}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(rec));
  fs.renameSync(tmp, out);
  return true;
}

function forward(input) {
  const r = spawnSync(process.execPath, [REAL], { input, encoding: 'utf8', timeout: 4000, windowsHide: true });
  if (r.stdout) process.stdout.write(r.stdout);
}

function main() {
  let input = '';
  const guard = setTimeout(() => process.exit(0), 3500);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => { input += c; });
  process.stdin.on('end', () => {
    if ((process.env.CPP_QUOTA_TAP || '').toLowerCase() !== 'off') {
      try { writeReading(reading(JSON.parse(input), Date.now() / 1000), OUT); } catch (e) { /* never block a render */ }
    }
    try { forward(input); } catch (e) { /* render nothing rather than break the statusline */ }
    clearTimeout(guard);
    process.exit(0);
  });
}

if (require.main === module) main();
module.exports = { reading, writeReading };
