#!/usr/bin/env node
/**
 * test-closer-guard-recommendation.js -- EWC E4, class RECOMMENDATION_STOP.
 * Both poles. The must-not-fire half is the half that matters: a class that fires on a
 * legitimate Owner question, a human-gate package or a HANDOFF BLOCK gets the whole guard
 * switched off with CLAUDE_CLOSER_GUARD=off, and an off guard IS the dead screen.
 */
'use strict';

const path = require('path');
const guard = require(path.join(__dirname, '..', 'closer-guard.js'));

const REPORT = 'Gate result: 12 of 12 green, commit abc1234 landed. ';

const MUST_FIRE = [
  REPORT + 'The next iteration should wire the reachability registry.',
  REPORT + 'I recommend doing the schema migration next.',
  REPORT + 'I suggest you run the full suite before merging.',
  REPORT + 'The parser cleanup is left for a follow-up.',
  REPORT + 'I would recommend running the drill again with the larger corpus.',
  REPORT + 'The remaining lint debt is left to a follow-up.',
  REPORT + 'The next step should be adding the second fixture.',
  REPORT + 'Recommended next step: add the second fixture.',
];

const MUST_NOT_FIRE = [
  // closing question to the Owner
  REPORT + 'I recommend doing the migration next. Do you want me to start it?',
  // genuine human-gate package / Owner category
  REPORT + 'The next step is the Owner\'s call: publishing the release is outward-facing.',
  REPORT + 'Decision needed (yes/no): deploy to production? I recommend running it Monday.',
  REPORT + 'The next iteration should rotate the credentials, which I lack access to.',
  // estate handoff contract
  REPORT + 'HANDOFF BLOCK: the next task for another pane is wiring the registry; the next iteration should start there.',
  REPORT + 'Next session should pick up the follow-up per the handoff.',
  // near-miss: plain reports that share words
  REPORT + 'No follow-up is left; the next step was already done in commit abc1234.',
  REPORT + 'The recommended config is now the default.',
  REPORT + 'Suggestions are rendered in the card.',
  'Done. 12 of 12 green.',
];

let pass = 0; let total = 0; const fails = [];
function check(label, got, want) {
  total++;
  if (got === want) pass++; else fails.push(`${label}: got ${got}, want ${want}`);
}
const cls = (t, o) => { const v = guard.classify(t, o); return v ? v.cls : null; };

for (const t of MUST_FIRE) {
  check('text-only fire: ' + t, cls(t), 'RECOMMENDATION_STOP');
  check('tool-turn endsOnText fire: ' + t, cls(t, { toolTurn: true, endsOnText: true }), 'RECOMMENDATION_STOP');
  // tool call followed the text => the work happened; must not fire
  check('tool call followed text: ' + t, cls(t, { toolTurn: true, endsOnText: false }), null);
}
for (const t of MUST_NOT_FIRE) {
  check('text-only clean: ' + t, cls(t), null);
  check('tool-turn clean: ' + t, cls(t, { toolTurn: true, endsOnText: true }), null);
}

for (const f of fails) console.log('FAIL ' + f);
console.log(`CLOSER_RECOMMENDATION=${pass}/${total}  (fire: ${MUST_FIRE.length}, must-not-fire: ${MUST_NOT_FIRE.length})`);
process.exit(pass === total ? 0 : 1);
