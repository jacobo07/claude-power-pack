// <module>/tests/recorder.test.js
const assert = require('assert');
const os = require('os'); const path = require('path'); const fs = require('fs');
const cp = require('child_process');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lzrec-'));
const recorder = path.join(__dirname, '..', 'recorder.js');
const stdin = JSON.stringify({ session_id: 'SID1', cwd: 'C:/proj/Foo' });

function run(env) {
  cp.execSync(`node "${recorder}"`, { input: stdin, env: { ...process.env, LAZARUS_REG_ROOT: tmp, ...env } });
}
run({ LAZARUS_TERMINAL_KEY: 'slot3' });
let rows = JSON.parse(fs.readFileSync(path.join(tmp, 'terminal_registry.json'))).rows;
assert.strictEqual(rows[0].slot, 'slot3');
assert.strictEqual(rows[0].session_id, 'SID1');
assert.strictEqual(rows[0].project_id, 'C--proj-Foo', 'cwd -> sanitized project id');

run({});
rows = JSON.parse(fs.readFileSync(path.join(tmp, 'terminal_registry.json'))).rows;
assert.ok(rows.some(r => /^pid:/.test(r.slot)), 'pid fallback slot present');
console.log('recorder.test OK');
