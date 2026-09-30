#!/usr/bin/env node
/**
 * Gate for carrier_bash_guard.js. Every case asserts a decision the opposite
 * implementation gets wrong: a guard that allowed everything fails the deny
 * half, one that denied everything fails the allow half, and one that ignored
 * agent_type fails the not-ours half. The last block drives the real stdin/stdout
 * contract, because an in-process judge() can be right while the wire shape is not.
 *
 * Run: node hooks/tests/test-carrier-bash-guard.js
 */
'use strict';
const { spawnSync } = require('child_process');
const path = require('path');
const GUARD = path.join(__dirname, '..', 'carrier_bash_guard.js');
const { judge } = require(GUARD);

const V = 'cpp-carrier-verifier';
const CASES = [
  // verifier: observe/test is allowed
  [V, 'Bash', 'git log --oneline -5', true],
  [V, 'Bash', 'git -C C:/repo diff HEAD~1 -- tools/x.py', true],
  [V, 'Bash', 'python -m pytest tests/test_a.py -q 2>&1', true],
  [V, 'Bash', 'python tools/test_agent_spec.py', true],
  [V, 'Bash', 'node hooks/tests/test-carrier-bash-guard.js', true],
  [V, 'Bash', 'cd modules && ls -la | head -20', true],
  [V, 'Bash', 'grep -rn "def load" modules/ | wc -l', true],
  [V, 'Bash', 'find . -name "*.py" -newer x', true],
  // verifier: anything that changes state is denied
  [V, 'Bash', 'rm -rf build', false],
  [V, 'Bash', 'git commit -m x', false],
  [V, 'Bash', 'git push origin main', false],
  [V, 'Bash', 'git checkout -- file.py', false],
  [V, 'Bash', 'echo x > notes.md', false],
  [V, 'Bash', 'git log >> history.txt', false],
  [V, 'Bash', 'mv a b', false],
  [V, 'Bash', 'curl -X POST https://example.com', false],
  [V, 'Bash', 'python -c "open(\'x\',\'w\').write(1)"', false],
  [V, 'Bash', 'python tools/deploy.py', false],
  [V, 'Bash', 'find . -name "*.tmp" -delete', false],
  [V, 'Bash', 'git log && rm x', false],
  [V, 'Bash', 'ls $(rm x)', false],
  [V, 'PowerShell', 'Remove-Item x -Recurse -Force', false],
  [V, 'Bash', '', false],
  // investigator has no shell authority at all
  ['cpp-carrier-investigator', 'Bash', 'git log', false],
  // writer and non-carriers are not this guard's business
  ['cpp-carrier-writer', 'Bash', 'rm -rf build', true],
  ['general-purpose', 'Bash', 'rm -rf build', true],
  [undefined, 'Bash', 'rm -rf build', true],
  // non-shell tools pass
  [V, 'Read', undefined, true],
];

let pass = 0, fail = 0;
for (const [agent, tool, cmd, want] of CASES) {
  const got = judge(agent, tool, cmd).allow;
  if (got === want) pass++; else { fail++; console.log(`  FAIL judge(${agent}, ${tool}, ${JSON.stringify(cmd)}) = ${got}, want ${want}`); }
}

// wire contract: real process, real JSON
function wire(payload) {
  const r = spawnSync(process.execPath, [GUARD], { input: payload, encoding: 'utf8' });
  return { code: r.status, out: r.stdout };
}
const denyWire = wire(JSON.stringify({ agent_type: V, tool_name: 'Bash', tool_input: { command: 'git push' } }));
const allowWire = wire(JSON.stringify({ agent_type: V, tool_name: 'Bash', tool_input: { command: 'git status' } }));
const junkWire = wire('not json');
const WIRE = [
  ['deny emits permissionDecision deny, exit 0', denyWire.code === 0 && /"permissionDecision":"deny"/.test(denyWire.out)],
  ['allow emits continue', allowWire.code === 0 && /"continue":true/.test(allowWire.out)],
  ['garbage stdin fails open', junkWire.code === 0 && /"continue":true/.test(junkWire.out)],
];
for (const [label, ok] of WIRE) {
  if (ok) pass++; else { fail++; console.log(`  FAIL wire: ${label}`); }
}
console.log(`CARRIER_BASH_GUARD=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
