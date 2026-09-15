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
// THIRD BUCKET, outside the denominator. A suite that could not judge its
// subject has produced no evidence about it, and folding that into `passed`
// makes the runner report success exactly when the thing it measures is
// broken. Measured: test-stop-chain-budget already prints
// `STOP_CHAIN_BUDGET=INCONCLUSIVE host_starved` and exits 0 with the comment
// "not a pass and not a subject failure: it judged nothing" -- the SUITE was
// honest and this RUNNER flattened it back to green. So the one instrument
// able to see host starvation reported PASS while the host was starved, which
// is how 15,574 dispatcher timeouts and 49 orphaned hook processes accumulated
// under a green suite. A verdict that could not be reached must never be
// spelled like one that was.
const inconclusive = [];
const INCONCLUSIVE_RE = /\bINCONCLUSIVE\b/;

for (const t of targets) {
  const name = path.basename(t);
  const r = spawnSync(process.execPath, [t], { encoding: 'utf8' });
  const out = ((r.stdout || '') + (r.stderr || '')).trim();
  const summary = out.split('\n').filter(Boolean).pop() || '(no output)';

  if (r.status === 0 && INCONCLUSIVE_RE.test(out)) {
    // Detected on the suite's own OUTPUT rather than a reserved exit code: a
    // suite that already says INCONCLUSIVE should not have to be rewritten to
    // be heard, and an exit code nobody adopted would leave this dead.
    inconclusive.push(name);
    console.log(`  INCONC ${name}  ${summary}`);
  } else if (r.status === 0) {
    passed += 1;
    console.log(`  PASS  ${name}  ${summary}`);
  } else {
    failed.push(name);
    console.log(`  FAIL  ${name}  exit=${r.status}`);
    for (const line of out.split('\n')) console.log(`        ${line}`);
  }
}

// Denominator excludes the inconclusive, and they are printed on their own
// axis. Reporting `28/29` when one judged nothing claims evidence that does
// not exist; reporting `28/28 inconclusive=1` is the true statement.
const judged = targets.length - inconclusive.length;
console.log(`HOOK_SELFTESTS=${passed}/${judged}  inconclusive=${inconclusive.length}`);
if (inconclusive.length) {
  console.log(`inconclusive (judged nothing, NOT a pass): ${inconclusive.join(', ')}`);
}
if (failed.length) console.log(`failing: ${failed.join(', ')}`);
// Exit status is unchanged: inconclusive does not fail the run, because a busy
// host is not a defect in the subject. It is reported, never counted.
process.exit(failed.length === 0 ? 0 : 1);
