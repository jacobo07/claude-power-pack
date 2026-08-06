#!/usr/bin/env node
/*
 * tests/fixtures/cdicf_crash_child.js
 *
 * Kills itself in the middle of a real CDICF install so the recovery path can
 * be tested against an actual abrupt exit rather than a simulated one.
 *
 * `process.exit` from inside the phase callback is genuinely abrupt: no finally
 * blocks run, no cleanup happens, and the journal is left exactly as an OOM
 * kill or a power loss would leave it. A test that instead called `recover()`
 * on a hand-built directory would be testing the recovery function against a
 * state a crash may never actually produce.
 *
 * Usage:
 *   node cdicf_crash_child.js <emitDir> <target> <phaseToCrashAt> [nthOccurrence]
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { install } = require('../../modules/cdicf/installer');

const [, , emitDir, target, crashAt, nthRaw] = process.argv;
const nth = Number(nthRaw || 1);

const entry = JSON.parse(fs.readFileSync(path.join(emitDir, 'registry-item.json'), 'utf8'));
const im = JSON.parse(fs.readFileSync(path.join(emitDir, 'install-manifest.json'), 'utf8'));

let hits = 0;
const res = install(entry, im, target, {
  onPhase(phase) {
    if (phase !== crashAt) return;
    if (++hits < nth) return;
    process.exit(137);          // SIGKILL-shaped: no unwinding, no cleanup
  },
});

process.stdout.write(JSON.stringify(res) + '\n');
process.exit(res.ok ? 0 : res.refusal.exit);
