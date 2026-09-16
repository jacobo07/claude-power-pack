#!/usr/bin/env node
/**
 * Two-way self-test for the closer-guard NULL_ACK class.
 *
 * A gate exercised only on the cases it was written for is a rubber stamp: it would pass
 * identically with every clause commented out. So half of these cases MUST NOT fire, and
 * the false-positive half is the half that matters — NULL_ACK is narrow on purpose, and a
 * regression that widens it would spam every ordinary short reply.
 *
 * Run: node ~/.claude/hooks/tests/test-closer-guard-nullack.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const GUARD = path.join(os.homedir(), '.claude', 'hooks', 'closer-guard.js');

// classify() is module-private, so lift it out of the source rather than exporting it —
// the hook's public contract is the hook protocol, and widening it just to be testable
// would be the test changing the subject to suit itself.
const src = fs.readFileSync(GUARD, 'utf8');
const sandbox = { module: {}, exports: {}, require, console, process };
const start = src.indexOf('const PASSIVE_WAIT');
const end = src.indexOf('// --- Transcript reading');
if (start < 0 || end < 0) {
  console.error('FAIL: could not locate the classifier block in closer-guard.js');
  process.exit(1);
}
const fn = new Function(`${src.slice(start, end)}; return classify;`);
const classify = fn.call(sandbox);

// [text, expected class or null]
const CASES = [
  // --- MUST fire -----------------------------------------------------------
  ['No response requested.', 'NULL_ACK'],          // the measured 2026-09-02 closer
  ['No response requested', 'NULL_ACK'],
  ['no reply needed.', 'NULL_ACK'],
  ['No further action required.', 'NULL_ACK'],
  ['Acknowledged.', 'NULL_ACK'],
  ['Noted', 'NULL_ACK'],
  ['Nothing to report.', 'NULL_ACK'],

  // --- MUST NOT fire: ordinary human acknowledgements -----------------------
  // These are legitimate replies to a PERSON. Blocking them is noise, and noise is how
  // a guard gets switched off.
  ['Understood.', null],
  ['Got it.', null],
  ['Sounds good.', null],
  ['OK.', null],

  // --- MUST NOT fire: substantive turns that merely CONTAIN an ack ----------
  [
    'The bisect landed: 320 MB is the lowest heap that reads the world completely, ' +
    'in both arms. The defensive copies were not the memory driver — what removing ' +
    'them changed is the failure mode, from a hard OOM to a partial read. Noted.',
    null,
  ],
  [
    'Acknowledged. Now re-running the nine held-out worlds one JVM at a time, because ' +
    'the sweep\'s three concurrent workers are themselves under suspicion.',
    null,
  ],

  // --- MUST NOT fire: the other classes still work (no regression) ---------
  ['Awaiting the completion notification.', 'PASSIVE_WAIT'],
  ['Let me read the output file.', 'INTENT_NARRATION'],
  ['', 'EMPTY'],
  ['Done: 9/9 worlds re-measured, ledger written to _logs/.', null],
];

let pass = 0;
let fail = 0;
for (const [text, expected] of CASES) {
  const got = classify(text);
  const cls = got ? got.cls : null;
  const ok = cls === expected;
  if (ok) {
    pass += 1;
  } else {
    fail += 1;
    const shown = text.length > 62 ? text.slice(0, 62) + '...' : text;
    console.log(`  FAIL  expected=${expected}  got=${cls}  <<${shown}>>`);
  }
}

console.log(`CLOSER_GUARD_NULLACK=${pass}/${pass + fail}  (fires: 7, must-not-fire: 6, other-classes: 4)`);
process.exit(fail === 0 ? 0 : 1);
