// <module>/tests/registry.test.js
const assert = require('assert');
const os = require('os');
const path = require('path');
const fs = require('fs');
const R = require('../lib/registry');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lzreg-'));
R._setRoot(tmp);

R.upsert({ slot: 'slot1', project_id: 'P', session_id: 'A', cwd: '/c/x', pid: 11 });
R.upsert({ slot: 'slot1', project_id: 'P', session_id: 'B', cwd: '/c/x', pid: 11 });
let rows = R.readAll();
assert.strictEqual(rows.length, 1, 'slot1 deduped');
assert.strictEqual(rows[0].session_id, 'B', 'slot1 updated to B');
assert.ok(rows[0].ts, 'ts stamped');

R.upsert({ slot: 'slot2', project_id: 'P', session_id: 'C', cwd: '/c/y', pid: 22 });
assert.strictEqual(R.readAll().length, 2, 'two slots');

fs.writeFileSync(path.join(tmp, 'terminal_registry.json'), '{bad json');
assert.deepStrictEqual(R.readAll(), [], 'corrupt -> []');

console.log('registry.test OK');
