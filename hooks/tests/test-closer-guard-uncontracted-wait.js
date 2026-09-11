#!/usr/bin/env node
/**
 * test-closer-guard-uncontracted-wait.js
 *
 * MEASURED 2026-09-11 (Jacobo, claude-power-pack). PASSIVE_WAIT carried
 * `/\bi'?ll wait\b/i`, which matches "I'll wait" and "Ill wait" and returns
 * NULL on "I will wait" -- the uncontracted form of the most canonical
 * dead-screen closer in the whole doctrine.
 *
 * It hid because of the tool-turn split. On a text-only turn INTENT_NARRATION
 * caught it by accident (`/i(?:'ll| will) ...$/`), so the guard looked healthy.
 * On a TOOL-CALL turn classify() runs PASSIVE_WAIT and nothing else -- so on
 * exactly the shape CLAUDE.md rule (G) was written for, the hole was open.
 *
 * Both directions are driven. The must-not-fire half is the half that matters:
 * this class was widened, and a widened class that fires on ordinary prose gets
 * the whole guard switched off with CLAUDE_CLOSER_GUARD=off -- and an off guard
 * IS the dead screen.
 *
 * MUSTNOT carries two hyphenated subjects on purpose. The first draft of the
 * widening used a bare `\bwait\b`, `\b` fires inside "wait-list", and this
 * file's own negative control is what caught it before it shipped.
 */

'use strict';

const path = require('path');
const guard = require(path.join(__dirname, '..', 'closer-guard.js'));

// Every one of these ends a turn that ALSO issued a tool call -- the branch
// where PASSIVE_WAIT is the only class that runs.
const MUST_FIRE = [
  'I will wait for the notification.',
  'I will wait.',
  'We will wait for CI to go green.',
  'I am waiting on the build.',
  "I'm waiting.",
  'We are waiting for the run to land.',
  "Let's wait for it.",
  'Lets wait for it.',
  // Regression anchors: the shapes that already worked must keep working.
  'Standing by.',
  "I'll wait for the notification.",
  'Awaiting the result.',
  'Quedo a la espera.',
  'Esperando a que termine el build.',
  'Sigo esperando la notificacion.',
];

const MUST_NOT_FIRE = [
  // Honest reports. Each carries a real result.
  'Listo: 11 entradas reescritas, 0 restantes.',
  'I rewrote 11 entries; the backup is on disk.',
  'El resultado: 9 de 9 en verde.',
  // "wait" as ordinary vocabulary, not as a closer.
  'The gate will wait up to 60s before timing out.',
  'Waiting rooms are not part of this change.',
  // Hyphenated: \b fires inside a hyphenated word. This is why (?!-) exists.
  'I will wait-list the module only if you ask.',
  "I'm waiting-room agnostic here.",
];

let pass = 0;
let fail = 0;

for (const text of MUST_FIRE) {
  const v = guard.classify(text, { toolTurn: true });
  if (v && v.cls === 'PASSIVE_WAIT') {
    pass++;
  } else {
    fail++;
    console.log(`  [FAIL] should fire PASSIVE_WAIT, got ${v ? v.cls : 'null'}: ${JSON.stringify(text)}`);
  }
}

for (const text of MUST_NOT_FIRE) {
  const v = guard.classify(text, { toolTurn: true });
  if (!v) {
    pass++;
  } else {
    fail++;
    console.log(`  [FAIL] false positive ${v.cls}: ${JSON.stringify(text)}`);
  }
}

// Positive control. A detector that stopped detecting reports the same clean
// green as one that works, so assert the sweep actually judged something.
const total = MUST_FIRE.length + MUST_NOT_FIRE.length;
if (pass + fail !== total) {
  console.log(`  [FAIL] judged ${pass + fail} cases, expected ${total}`);
  fail++;
}

console.log(
  `CLOSER_UNCONTRACTED_WAIT=${pass}/${total}  ` +
  `(fires: ${MUST_FIRE.length}, must-not-fire: ${MUST_NOT_FIRE.length})`
);
process.exit(fail === 0 ? 0 : 1);
