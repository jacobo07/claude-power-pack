#!/usr/bin/env node
/**
 * Bridges the two Python liveness ratchets into the canonical hook suite, so
 * `node ~/.claude/hooks/tests/run-all.js` enforces them rather than relying on
 * someone remembering a command from a document.
 *
 *   tools/test_hook_stdin_liveness.py   V-STDIN-*  + V-EMIT-*
 *   tools/test_hook_mirror_identity.py  V-MIRROR-*
 *
 * A thin bridge on purpose. The alternative was a second runner, and this estate
 * already has one that discovers tests by pattern -- a gate nobody runs is the
 * failure these gates were written to stop, so wiring beats inventing.
 *
 * INCONCLUSIVE, NOT PASS, when the drive is skipped. The stdin gate spawns every
 * harness-spawned hook and takes ~90 s; CLAUDE_SKIP_HOOK_DRIVE=1 exists so a
 * fast loop can opt out. A skipped drive has judged NOTHING, and this runner
 * already has a third bucket for exactly that (see run-all.js: a verdict that
 * could not be reached must never be spelled like one that was). So the word
 * INCONCLUSIVE is emitted and the runner keeps it out of the denominator.
 */
'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const PP = path.join(os.homedir(), '.claude', 'skills', 'claude-power-pack');
const GATES = [
  ['V-STDIN / V-EMIT', path.join(PP, 'tools', 'test_hook_stdin_liveness.py')],
  ['V-MIRROR', path.join(PP, 'tools', 'test_hook_mirror_identity.py')],
];

// Absolute path first: `python` is not reliably on this host's non-interactive
// PATH, and a bare name that resolves to nothing would make a missing
// interpreter look like a failing gate.
const PY_CANDIDATES = [
  path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
  'python',
];

function resolvePython() {
  for (const p of PY_CANDIDATES) {
    if (p.includes(path.sep) && fs.existsSync(p)) return p;
    if (!p.includes(path.sep)) {
      const probe = spawnSync(p, ['--version'], { encoding: 'utf8' });
      if (probe.status === 0) return p;
    }
  }
  return null;
}

if (process.env.CLAUDE_SKIP_HOOK_DRIVE === '1') {
  console.log('HOOK_LIVENESS_GATES=INCONCLUSIVE  drive skipped by CLAUDE_SKIP_HOOK_DRIVE=1');
  process.exit(0);
}

const py = resolvePython();
if (!py) {
  // A missing interpreter is not evidence about the hooks. Say so on its own
  // axis rather than failing the subject for the harness's absence.
  console.log('HOOK_LIVENESS_GATES=INCONCLUSIVE  no python interpreter found');
  process.exit(0);
}

let failed = 0;
for (const [label, script] of GATES) {
  if (!fs.existsSync(script)) {
    console.log(`  MISSING ${label} -- ${script}`);
    failed += 1;
    continue;
  }
  const r = spawnSync(py, [script], {
    encoding: 'utf8',
    cwd: PP,
    env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
  });
  const out = ((r.stdout || '') + (r.stderr || '')).trim();
  const summary = out.split('\n').filter(Boolean).pop() || '(no output)';
  if (r.status === 0) {
    console.log(`  PASS  ${label}  ${summary}`);
  } else {
    failed += 1;
    console.log(`  FAIL  ${label}  exit=${r.status}`);
    for (const line of out.split('\n')) console.log(`        ${line}`);
  }
}

console.log(`HOOK_LIVENESS_GATES=${GATES.length - failed}/${GATES.length}  threshold=${GATES.length}/${GATES.length}`);
process.exit(failed === 0 ? 0 : 1);
