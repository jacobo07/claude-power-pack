'use strict';
// ICC-10: COMPAT-miss SessionStart line. Both poles + the doubts that must stay silent.
const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');
const { compatMissLine } = require('../ccr_compat_line');

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ccr-compat-'));
function put(rkey, sid, ev, ageMs) {
  const d = path.join(root, 'receipts', rkey);
  fs.mkdirSync(d, { recursive: true });
  const f = path.join(d, sid + '.jsonl');
  fs.writeFileSync(f, JSON.stringify(Object.assign({ ts: 1, sid, ev: 'start' }, ev)) + '\n');
  const t = new Date(Date.now() - (ageMs || 0));
  fs.utimesSync(f, t, t);
}
const clear = () => fs.rmSync(path.join(root, 'receipts'), { recursive: true, force: true });

// RED pole: incompatible build with an enforce mode -> one line naming the version.
put('aaaa', 's1', { version: '2.1.999', compatible: false, modes: { main: 'enforce', subagent: 'shadow' } });
const line = compatMissLine(root);
assert(line && line.includes('2.1.999') && line.includes('ccr_release.py') && !line.includes('\n'), 'incompatible build must surface one line: ' + line);

// GREEN pole: compatible build -> silent.
clear();
put('aaaa', 's1', { version: '2.1.318', compatible: true, modes: { main: 'enforce' } });
assert.strictEqual(compatMissLine(root), null, 'compatible build must be silent');

// Nothing wanted (all shadow/off): nothing was downgraded -> silent.
clear();
put('aaaa', 's1', { version: '2.1.999', compatible: false, modes: { main: 'shadow', subagent: 'off' } });
assert.strictEqual(compatMissLine(root), null, 'no enforce wanted -> silent');

// Newest receipt wins: an old incompatible one under a newer compatible one is silent.
clear();
put('aaaa', 'old', { version: '2.1.999', compatible: false, modes: { main: 'enforce' } }, 3600 * 1000);
put('bbbb', 'new', { version: '2.1.318', compatible: true, modes: { main: 'enforce' } }, 0);
assert.strictEqual(compatMissLine(root), null, 'newest receipt decides');

// Stale (>7d) evidence is not a current reading.
clear();
put('aaaa', 's1', { version: '2.1.999', compatible: false, modes: { main: 'enforce' } }, 8 * 24 * 3600 * 1000);
assert.strictEqual(compatMissLine(root), null, 'stale receipt -> silent');

// Absent dir / unreadable -> fail-open null.
assert.strictEqual(compatMissLine(path.join(root, 'nope')), null, 'missing dir -> null');

fs.rmSync(root, { recursive: true, force: true });
console.log('PASS test-ccr-compat-line (6 assertions)');
