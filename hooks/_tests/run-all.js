#!/usr/bin/env node
/**
 * Runs every hook self-test in one command.
 *
 * Why this exists: as of 2026-09-02 the guard suite was five standalone files invoked by
 * hand from prose in CLAUDE.md. A test nobody can run in one keystroke is a test that
 * silently rots the first time someone edits the hook it protects — and these particular
 * hooks are the ones that stop the cross-repo dead screen, so their rot is expensive.
 *
 * Discovery is by pattern, not by a hardcoded list: a list would go stale the same way,
 * and a runner that cannot see a new test is the same defect one layer up.
 *
 * Run: node ~/.claude/hooks/tests/run-all.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const HERE = __dirname;
const HOOKS = path.dirname(HERE);

const targets = [];

for (const f of fs.readdirSync(HERE).sort()) {
  if (/^test[-_].*\.js$/i.test(f) && f !== path.basename(__filename)) {
    targets.push(path.join(HERE, f));
  }
}
// Legacy siblings that live one level up rather than in tests/.
for (const f of fs.readdirSync(HOOKS).sort()) {
  if (/^test[-_].*\.js$/i.test(f)) targets.push(path.join(HOOKS, f));
}

if (targets.length === 0) {
  console.error('FAIL: no self-tests discovered — the runner found nothing to run, which is');
  console.error('      not a pass. Check the discovery pattern before trusting this green.');
  process.exit(1);
}

let passed = 0;
const failed = [];

for (const t of targets) {
  const name = path.basename(t);
  const r = spawnSync(process.execPath, [t], { encoding: 'utf8' });
  const out = ((r.stdout || '') + (r.stderr || '')).trim();
  const summary = out.split('\n').filter(Boolean).pop() || '(no output)';

  if (r.status === 0) {
    passed += 1;
    console.log(`  PASS  ${name}  ${summary}`);
  } else {
    failed.push(name);
    console.log(`  FAIL  ${name}  exit=${r.status}`);
    for (const line of out.split('\n')) console.log(`        ${line}`);
  }
}

console.log(`HOOK_SELFTESTS=${passed}/${targets.length}`);
if (failed.length) console.log(`failing: ${failed.join(', ')}`);
process.exit(failed.length === 0 ? 0 : 1);
