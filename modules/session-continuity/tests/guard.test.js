// <module>/tests/guard.test.js
const assert = require('assert');
const cp = require('child_process');
const path = require('path');
const guard = path.join(__dirname, '..', 'governance-guard.js');

function run(payload) {
  try {
    const out = cp.execSync(`node "${guard}"`, { input: JSON.stringify(payload) });
    return { code: 0, out: out.toString() };
  } catch (e) { return { code: e.status, out: (e.stdout||'').toString() + (e.stderr||'').toString() }; }
}
let r = run({ tool_name: 'Bash', tool_input: { command: 'mv a/S.jsonl a/S.jsonl.live' } });
assert.strictEqual(r.code, 2, 'jsonl shadow rename blocked');
r = run({ tool_name: 'Write', tool_input: { file_path: 'C:/Users/User/.claude/commands/resume.md', content: 'x' } });
assert.strictEqual(r.code, 2, 'resume override blocked');
r = run({ tool_name: 'Write', tool_input: { file_path: 'foo/bar.js', content: 'x' } });
assert.strictEqual(r.code, 0, 'normal write allowed');
console.log('guard.test OK');
