#!/usr/bin/env node
/**
 * Gate for agent-solo-guard.js.
 *
 * WHY THIS FILE EXISTS. The guard shipped 2026-05-28 with no test. The harness
 * later renamed the subagent tool "Task" -> "Agent"; the guard tested
 * `tool_name !== "Task"` and settings.json matched on `"Task"`, so from that
 * rename onward it was invoked never, and would have exited 0 even if it had
 * been. Its own log proves it: last entry 2026-05-28 (its self-test day), zero
 * entries in the 99 days to 2026-09-04, across hundreds of real dispatches.
 *
 * A gate that cannot fire is indistinguishable from a gate that passes. The
 * only thing that tells the two apart is a test that DRIVES THE RED BRANCH, so
 * every case below asserts an exit code that the opposite implementation would
 * get wrong.
 *
 * Run: node test-agent-solo-guard.js
 */

'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const GUARD = path.join(__dirname, '..', 'agent-solo-guard.js');
const TRACKER = path.join(os.homedir(), '.claude', 'state', 'agent-solo-tracker.json');

const BLOCK = 2;
const ALLOW = 0;

// A long-running-looking prompt with no instruction to write anything down.
const UNBOUNDED =
  'Disassemble DatabaseDisk::Load and GetRostersCRC in the golden DOL and ' +
  'report every call site you find.';
// The same task, made recoverable by one clause.
const BOUNDED =
  'Disassemble DatabaseDisk::Load and GetRostersCRC in the golden DOL. ' +
  'Write your findings to knowledge/evidence/CHECKSUM_ARCHAEOLOGY.md as you go, ' +
  'appending each confirmed address before moving on.';
// An ordinary short lookup: must never be touched by the bound check.
const LOOKUP = 'Where is KobiiSoundPlaySafe defined?';

function resetTracker() {
  try {
    if (fs.existsSync(TRACKER)) fs.unlinkSync(TRACKER);
  } catch (_) {
    /* best effort; a stale tracker only ever causes a BLOCK, never a false ALLOW */
  }
}

/** Run the guard with one payload. `fresh` clears the inflight tracker first. */
function run(payload, fresh) {
  if (fresh !== false) resetTracker();
  const r = spawnSync(process.execPath, [GUARD], {
    input: typeof payload === 'string' ? payload : JSON.stringify(payload),
    encoding: 'utf8',
  });
  return r.status;
}

const dispatch = (prompt, toolName) => ({
  tool_name: toolName || 'Agent',
  tool_input: { prompt, subagent_type: 'general-purpose' },
});

// --- contract-preflight fixture (2026-09-22) --------------------------------
// SYNTHETIC on purpose. Pinning this to a real read-only agent would make the drill decay the
// day someone gives that agent a Write tool -- a test whose validity depends on a real defect
// surviving has an interest in that defect surviving. These two exist only for this file.
const FIXROOT = fs.mkdtempSync(path.join(os.tmpdir(), 'aguard-'));
const AGENTS = path.join(FIXROOT, '.claude', 'agents');
fs.mkdirSync(AGENTS, { recursive: true });
fs.writeFileSync(path.join(AGENTS, 'readonly-probe.md'),
  '---\nname: readonly-probe\ndescription: fixture\ntools: Read, Grep, Glob\n---\nbody\n');
fs.writeFileSync(path.join(AGENTS, 'writer-probe.md'),
  '---\nname: writer-probe\ndescription: fixture\ntools: Read, Grep, Glob, Write, Edit\n---\nbody\n');

const as = (prompt, subagent_type) => ({
  tool_name: 'Agent',
  cwd: FIXROOT,
  tool_input: { prompt, subagent_type },
});

// A durable-output clause phrased with "create", which the pre-2026-09-22 verb list could not
// see -- so a genuine, explicit, incremental write instruction read as no instruction at all.
const BOUNDED_CREATE =
  'Audit every call site in the corpus. Create knowledge/evidence/AUDIT.md and append each ' +
  'confirmed finding to it as you go, before moving on to the next.';

const CASES = [
  // --- the revival: the tool is called "Agent" now -------------------------
  // Pre-fix these three all returned ALLOW because the name test rejected them
  // before any logic ran. They are the regression that matters most.
  ['Agent + unbounded research', () => run(dispatch(UNBOUNDED)), BLOCK],
  ['Task (legacy name) still honoured', () => run(dispatch(UNBOUNDED, 'Task')), BLOCK],
  ['Agent + durable-output clause', () => run(dispatch(BOUNDED)), ALLOW],

  // --- the bound check must stay narrow ------------------------------------
  // If a short lookup ever blocks, the guard becomes noise and gets turned off.
  ['Agent + short lookup', () => run(dispatch(LOOKUP)), ALLOW],

  // --- not our tool --------------------------------------------------------
  ['a Read is none of our business', () => run({ tool_name: 'Read', tool_input: {} }), ALLOW],

  // --- the original rule 4: solo dispatch ----------------------------------
  // Second dispatch inside the 30s window blocks even when perfectly bounded.
  ['second Agent within the window', () => {
    run(dispatch(BOUNDED));                 // fresh: records an inflight entry
    return run(dispatch(BOUNDED), false);   // keep tracker: must block
  }, BLOCK],

  // --- fail-open is absolute ----------------------------------------------
  // A guard that crashes the dispatch is worse than the bug it prevents.
  ['garbage stdin fails open', () => run('not json at all'), ALLOW],
  ['empty stdin fails open', () => run(''), ALLOW],

  // --- contract preflight: obligation vs action surface --------------------
  // The F-2 case, reproduced. A durable-output clause handed to an agent with no write tool is
  // unsatisfiable BY CONSTRUCTION; the guard used to demand the clause and never ask whether the
  // agent could honour it, so it blocked satisfiable contracts on a verb and waved impossible
  // ones through. Both directions are driven here.
  ['durable clause + read-only agent is impossible',
    () => run(as(BOUNDED, 'readonly-probe')), BLOCK],
  ['durable clause + write-capable agent is fine',
    () => run(as(BOUNDED, 'writer-probe')), ALLOW],
  // Narrowness control: without the obligation there is nothing to be incapable OF, so a
  // read-only agent on a short lookup must pass untouched. Otherwise this check is noise.
  ['read-only agent, no obligation, short lookup',
    () => run(as(LOOKUP, 'readonly-probe')), ALLOW],
  // Fail-open: an agent we cannot resolve is UNKNOWN, never "incapable". "Could not ask" and
  // "was refused" are different facts and only one of them may block.
  ['unresolvable agent fails open',
    () => run(as(BOUNDED, 'no-such-agent-anywhere')), ALLOW],
  // The verb fix. Pre-2026-09-22 this exact prompt was judged to carry NO durable-output clause
  // and blocked as unbounded research -- measured twice in one session on correct dispatches.
  ['"create <path>.md ... append as you go" counts as durable',
    () => run(as(BOUNDED_CREATE, 'writer-probe')), ALLOW],
  // ...and the same wording must still be refused when the agent cannot write, or the widened
  // verb list would have opened a new hole exactly where it closed one.
  ['"create" clause + read-only agent still impossible',
    () => run(as(BOUNDED_CREATE, 'readonly-probe')), BLOCK],
];

let pass = 0;
let fail = 0;

if (os.platform() !== 'win32') {
  // The guard self-gates to Windows; on any other host every case would trivially
  // return ALLOW and the suite would be vacuously green. Say so rather than lie.
  console.log('AGENT_SOLO_GUARD=SKIPPED  (not win32; guard is platform-gated)');
  process.exit(0);
}

for (const [label, fn, expected] of CASES) {
  let got;
  try {
    got = fn();
  } catch (e) {
    got = 'threw: ' + (e && e.message);
  }
  if (got === expected) {
    pass += 1;
  } else {
    fail += 1;
    console.log(`  FAIL  ${label}: expected exit=${expected} got=${got}`);
  }
}

resetTracker();
try { fs.rmSync(FIXROOT, { recursive: true, force: true }); } catch (_) { /* tmp only */ }
console.log(
  `AGENT_SOLO_GUARD=${pass}/${pass + fail}  ` +
  `(blocks: 5, allows: 6, fail-open: 3)`
);
process.exit(fail === 0 ? 0 : 1);
