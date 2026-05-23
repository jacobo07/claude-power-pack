// <module>/tests/mark.test.js
const assert = require('assert');
const os = require('os'); const path = require('path'); const fs = require('fs');
const M = require('../mark');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lzmark-'));
const sid = 'S1';
const f = path.join(tmp, sid + '.jsonl');
fs.writeFileSync(f, [
  JSON.stringify({ type: 'summary', summary: 'Refactor parser', leafUuid: 'x' }),
  JSON.stringify({ type: 'user', message: { content: 'hi' } }),
].join('\n'));

const jsonlSet = d => new Set(fs.readdirSync(d).filter(n => /\.jsonl/.test(n)).sort());
const before = jsonlSet(tmp);
M.mark(tmp, [sid], new Date('2026-05-15T16:38:00Z'));
let lines = fs.readFileSync(f, 'utf8').trim().split('\n').map(JSON.parse);
assert.ok(/^🟡 \[PRE-REBOOT \d\d:\d\d\] Refactor parser$/.test(lines[0].summary), 'summary prefixed');
// Prove "no shadow/rename": the *.jsonl* filename set is unchanged, the
// original <id>.jsonl basename still exists, and no *.jsonl.live appeared.
// (inode equality is vacuous on Windows where fs.statSync().ino === 0.)
const after = jsonlSet(tmp);
assert.deepStrictEqual([...after], [...before], 'jsonl filename set unchanged');
assert.ok(fs.existsSync(f), 'original <id>.jsonl basename still exists');
assert.ok(!fs.readdirSync(tmp).some(n => n.endsWith('.jsonl.live')), 'no shadow .jsonl.live created');

M.mark(tmp, [sid], new Date('2026-05-15T16:38:00Z'));
lines = fs.readFileSync(f, 'utf8').trim().split('\n').map(JSON.parse);
assert.strictEqual((lines[0].summary.match(/PRE-REBOOT/g) || []).length, 1, 'no double mark');

M.unmark(tmp, [sid]);
lines = fs.readFileSync(f, 'utf8').trim().split('\n').map(JSON.parse);
assert.strictEqual(lines[0].summary, 'Refactor parser', 'unmark clean');
console.log('mark.test OK');
