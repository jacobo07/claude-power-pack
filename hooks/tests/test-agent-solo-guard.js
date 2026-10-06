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
// A private state dir: the suite used to unlink the LIVE estate-wide tracker on every case,
// silently clearing other panes' inflight entries while it ran.
const STATE = fs.mkdtempSync(path.join(os.tmpdir(), 'aguard-state-'));
const TRACKER = path.join(STATE, 'agent-solo-tracker.json');
// GSD_LONG_RUN_STATE_DIR: the session-budget envelope the guard consults at dispatch (c4) is read
// from here too, never from the live ~/.claude/state.
const ENV = Object.assign({}, process.env, { AGENT_SOLO_STATE_DIR: STATE, GSD_LONG_RUN_STATE_DIR: STATE });
delete ENV.CPP_SESSION_BUDGET;

// A declared session envelope with an empty transcript: 0 processed, so only the dispatch
// reserve can push it past stop. reserve > stop -> deny; reserve < stop -> allow.
function envelope(sid, childReserve) {
  const tx = path.join(STATE, `${sid}.jsonl`);
  fs.writeFileSync(tx, '');
  fs.writeFileSync(path.join(STATE, `session-budget-${sid}.json`),
    JSON.stringify({ target: 500, warn: 800, stop: 1000, child_reserve: childReserve }));
  try { fs.unlinkSync(path.join(STATE, `session-budget-${sid}.state.json`)); } catch (_) { /* fresh */ }
  return tx;
}
const budgeted = (sid, childReserve) => Object.assign(dispatch(BOUNDED),
  { session_id: sid, transcript_path: envelope(sid, childReserve) });

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
    env: ENV,
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

  // --- 2026-10-05 cross-pane false positive (TOK-18 Gen3 T2) ----------------
  // The tracker is one file for every pane; the rule is per message. Another session's inflight
  // dispatch must not block this one. The pre-fix guard returns BLOCK here.
  ['another session inflight does not block this one', () => {
    run(Object.assign(dispatch(BOUNDED), { session_id: 'pane-A' }));
    return run(Object.assign(dispatch(BOUNDED), { session_id: 'pane-B' }), false);
  }, ALLOW],
  // ...while the same session's second dispatch still does (the rule itself is unchanged).
  ['same session inflight still blocks', () => {
    run(Object.assign(dispatch(BOUNDED), { session_id: 'pane-A' }));
    return run(Object.assign(dispatch(BOUNDED), { session_id: 'pane-A' }), false);
  }, BLOCK],
  // An entry written before entries carried a session id cannot be attributed: it still counts.
  ['unattributable legacy entry still blocks', () => {
    resetTracker();
    fs.writeFileSync(TRACKER, JSON.stringify([{ ts: Date.now(), subagent_type: 'x', prompt_head: 'y' }]));
    return run(Object.assign(dispatch(BOUNDED), { session_id: 'pane-B' }), false);
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

  // --- 2026-09-30 deadlock: the two checks demanded opposite things ---------
  // Measured: the contract check told the caller to drop the clause and let the parent
  // persist; the bound check then blocked the narrowed prompt. Every case below is one the
  // opposite implementation gets wrong.
  ['long + read-only + "parent persists" is the honest contract',
    () => run(as(UNBOUNDED + ' Return the report; the parent persists it.', 'readonly-probe')), ALLOW],
  ['long + read-only + no clause at all still unbounded',
    () => run(as(UNBOUNDED, 'readonly-probe')), BLOCK],
  // A writer CAN write, so it must carry the clause itself; the exemption is for incapacity only.
  ['long + writer + "parent persists" is not an excuse',
    () => run(as(UNBOUNDED + ' Return the report; the parent persists it.', 'writer-probe')), BLOCK],
  // Unresolvable is UNKNOWN, not incapable: the original demand stands.
  ['long + unresolvable agent + "parent persists" still blocks',
    () => run(as(UNBOUNDED + ' Return the report; the parent persists it.', 'no-such-agent-anywhere')), BLOCK],

  // --- 2026-10-06 Gen3 T3 c4: the session cost breaker at dispatch ---------
  // Agent has no dispatcher lane; before c4 nothing judged the new child's reserve, so the
  // pre-c4 guard returns ALLOW on the first case. The green control proves the check is not
  // simply refusing every budgeted dispatch.
  ['dispatch whose child reserve passes stop is denied', () => run(budgeted('sbg-red', 5000)), BLOCK],
  ['dispatch inside the envelope is allowed', () => run(budgeted('sbg-green', 10)), ALLOW],
  // A denied dispatch must not leave a tracker entry, or it would also block the next one for 30s.
  ['a budget-denied dispatch does not hold the solo slot', () => {
    run(budgeted('sbg-slot', 5000));
    fs.unlinkSync(path.join(STATE, 'session-budget-sbg-slot.json'));   // the Owner lifts the envelope
    return run(Object.assign(dispatch(BOUNDED), { session_id: 'sbg-slot' }), false);
  }, ALLOW],
  // Past warn, far from stop: allowed AND the advisory reaches stdout as parseable JSON
  // (c4 review LOW: a dropped or malformed print kept every other case green).
  ['past-warn dispatch is allowed and carries the advisory', () => {
    const p = budgeted('sbg-warn', 10);
    fs.writeFileSync(p.transcript_path, JSON.stringify({ type: 'assistant', timestamp: '2026-10-06T10:00:00.000Z',
      uuid: 'u-w1', message: { id: 'w1', model: 'claude-opus-5-5', content: [{ type: 'text', text: 'x' }],
        usage: { input_tokens: 900, cache_creation_input_tokens: 0, cache_read_input_tokens: 0, output_tokens: 0 } } }) + '\n');
    fs.writeFileSync(path.join(STATE, 'session-budget-sbg-warn.json'),
      JSON.stringify({ target: 500, warn: 800, stop: 1e9, child_reserve: 10 }));
    resetTracker();
    const r = spawnSync(process.execPath, [GUARD], { input: JSON.stringify(p), encoding: 'utf8', env: ENV });
    let ctx = '';
    try { ctx = JSON.parse(r.stdout).hookSpecificOutput.additionalContext || ''; } catch (_) { /* stays '' */ }
    return r.status === ALLOW && /SESSION BUDGET/.test(ctx) ? ALLOW : `status=${r.status} stdout=${r.stdout.slice(0, 80)}`;
  }, ALLOW],
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

try { fs.rmSync(FIXROOT, { recursive: true, force: true }); } catch (_) { /* tmp only */ }
try { fs.rmSync(STATE, { recursive: true, force: true }); } catch (_) { /* tmp only */ }
console.log(
  `AGENT_SOLO_GUARD=${pass}/${pass + fail}  ` +
  `(blocks: ${CASES.filter((c) => c[2] === BLOCK).length}, ` +
  `allows: ${CASES.filter((c) => c[2] === ALLOW).length})`
);
process.exit(fail === 0 ? 0 : 1);
