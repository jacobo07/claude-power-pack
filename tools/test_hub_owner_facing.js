// V-HUBOF-* gates: which SessionStart hub lines are Owner-facing, and when a digest carries no signal.
// Incremental-cognition pillar K (evidence/K-sessionstart-attribution.md): a headless worker or probe
// (entrypoint sdk-cli) was handed the OWNER_QUEUE digest (1,536 chars), the estate recovery verdict (608) and a
// "no notable signals" AutoResearch digest (261) -- text addressed to the Owner, in a session the Owner never sees.
// Pure functions, required as a module: none of the hub's session-start side effects run.
'use strict';
const hub = require('../hooks/session_start_hub.js');

let pass = 0; let fail = 0;
function check(gate, cond, ev) {
  if (cond) { pass++; console.log(`PASS ${gate} ${ev || ''}`); }
  else { fail++; console.log(`FAIL ${gate} ${ev || ''}`); }
}

const fn = (name) => typeof hub[name] === 'function';
check('V-HUBOF-EXPORTED', fn('ownerFacingAllowed') && fn('digestHasSignal'),
  `ownerFacingAllowed=${fn('ownerFacingAllowed')} digestHasSignal=${fn('digestHasSignal')}`);

if (fn('ownerFacingAllowed')) {
  check('V-HUBOF-HEADLESS-OMITS', hub.ownerFacingAllowed('sdk-cli') === false, 'sdk-cli -> false');
  check('V-HUBOF-INTERACTIVE-KEEPS', hub.ownerFacingAllowed('cli') === true, 'cli -> true');
  // Absent is not headless: an unknown entrypoint keeps today's behaviour (fail toward visibility).
  check('V-HUBOF-UNKNOWN-KEEPS', hub.ownerFacingAllowed(undefined) === true
    && hub.ownerFacingAllowed('') === true && hub.ownerFacingAllowed('some-future-surface') === true);
}

if (fn('digestHasSignal')) {
  const empty = '# Autoresearch Digest - 2026-10-05 20:00 UTC\n\n**Pending signals processed:** 3\n'
    + '**Signals accepted (above threshold):** 0\n**Cross-project signals found:** 0\n\n*No notable signals this run.*';
  const accepted = empty.replace('(above threshold):** 0', '(above threshold):** 2');
  const crossOnly = empty.replace('signals found:** 0', 'signals found:** 1');
  check('V-HUBOF-DIGEST-EMPTY-OMITTED', hub.digestHasSignal(empty) === false, 'accepted 0, cross 0 -> no signal');
  check('V-HUBOF-DIGEST-ACCEPTED-KEPT', hub.digestHasSignal(accepted) === true, 'accepted 2 -> signal');
  check('V-HUBOF-DIGEST-CROSS-KEPT', hub.digestHasSignal(crossOnly) === true, 'cross 1 -> signal');
  // A format the predicate does not recognise is kept: only a positive "zero" reading removes it.
  check('V-HUBOF-DIGEST-UNKNOWN-KEPT', hub.digestHasSignal('# Digest\nsomething new happened') === true);
}

console.log(`HUBOF_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
