#!/usr/bin/env node
'use strict';
/**
 * Done-gate for hooks/gsd_stop_continuation.js.
 *
 * Every case drives a REAL run() against a real temporary HOME, because the
 * hook's entire behaviour is filesystem-derived (marker, state, closer-guard
 * state, task outputs). A mocked filesystem here would be a test of the mock.
 *
 * ISOLATION CONTRACT: HOME + USERPROFILE + TEMP + TMP are all repointed at a
 * per-PID fixture root. This estate has twice had a "hermetic" test write into
 * the real state directory, so the fixture root is asserted to be outside the
 * real ~/.claude before anything runs.
 *
 * BOTH POLES, ALWAYS. A hook that blocks nothing passes every allow-case, and
 * a hook that blocks everything passes every block-case. Each half is only
 * evidence with the other half beside it.
 *
 * Mutation runs: node test_gsd_stop_continuation.js --subject <path-to-copy>
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

let passes = 0;
let fails = 0;
const failed = [];

function ok(gate, evidence) {
  passes += 1;
  console.log(`  PASS ${gate}  ${evidence}`);
}

function bad(gate, diagnostic) {
  fails += 1;
  failed.push(gate);
  console.log(`  FAIL ${gate}  ${diagnostic}`);
}

function check(gate, cond, evidence, diagnostic) {
  if (cond) ok(gate, evidence); else bad(gate, diagnostic);
}

// --- fixture root ----------------------------------------------------------
const ROOT = path.join(os.tmpdir(), `gsdcont-fixture-${process.pid}`);
const REAL_CLAUDE = path.join(os.homedir(), '.claude');

if (ROOT.startsWith(REAL_CLAUDE)) {
  console.log('HARNESS-FAILED: fixture root is inside the real ~/.claude');
  process.exit(2);
}

fs.rmSync(ROOT, { recursive: true, force: true });
const HOME_DIR = path.join(ROOT, 'home');
const TMP_DIR = path.join(ROOT, 'tmp');
for (const d of [HOME_DIR, TMP_DIR]) fs.mkdirSync(d, { recursive: true });

process.env.HOME = HOME_DIR;
process.env.USERPROFILE = HOME_DIR;
process.env.TEMP = TMP_DIR;
process.env.TMP = TMP_DIR;
delete process.env.CPP_GSD_STOP_CONTINUATION;

// Assert the redirection actually took, rather than trusting it. If
// os.homedir() ignored the env the whole suite would silently measure the
// real estate -- which is the failure mode this block exists to prevent.
if (os.homedir() !== HOME_DIR || os.tmpdir() !== TMP_DIR) {
  console.log('HARNESS-FAILED: env redirection did not take: '
    + `homedir=${os.homedir()} tmpdir=${os.tmpdir()}`);
  process.exit(2);
}

const subjectArg = process.argv.indexOf('--subject');
const SUBJECT = subjectArg > -1
  ? path.resolve(process.argv[subjectArg + 1])
  : path.join(__dirname, '..', 'hooks', 'gsd_stop_continuation.js');

if (!fs.existsSync(SUBJECT)) {
  console.log(`HARNESS-FAILED: subject not found at ${SUBJECT}`);
  process.exit(2);
}
const hook = require(SUBJECT);

// --- fixture helpers -------------------------------------------------------
const SID = 'fixture-session-0001';
const PROJ = path.join(ROOT, 'project');
const PLANNING = path.join(PROJ, '.planning');
const PHASE_DIR = path.join(PLANNING, 'phases', '13-benchmark-baseline-integrity');
// Mirrors the real layout: <tmp>/claude/<project-slug>/<sid>/tasks
const TRANSCRIPT = path.join(ROOT, 'projects', 'C--proj', `${SID}.jsonl`);
const TASKS = path.join(TMP_DIR, 'claude', 'C--proj', SID, 'tasks');

const STATE_FILE = path.join(HOME_DIR, '.claude', 'logs', 'gsd-continuation-state.json');
const CLOSER_STATE = path.join(HOME_DIR, '.claude', 'logs', 'closer-guard-state.json');
const MARKER = path.join(HOME_DIR, '.claude', 'state', `gsd-autorun-${SID}.json`);

function resetFixture() {
  fs.rmSync(path.join(HOME_DIR, '.claude'), { recursive: true, force: true });
  fs.rmSync(PROJ, { recursive: true, force: true });
  fs.rmSync(TASKS, { recursive: true, force: true });
  for (const d of [PHASE_DIR, TASKS, path.dirname(TRANSCRIPT),
    path.join(HOME_DIR, '.claude', 'state'),
    path.join(HOME_DIR, '.claude', 'logs')]) {
    fs.mkdirSync(d, { recursive: true });
  }
  fs.writeFileSync(path.join(PLANNING, 'STATE.md'), '# STATE\n', 'utf8');
  fs.writeFileSync(path.join(PLANNING, 'ROADMAP.md'), '# ROADMAP\n', 'utf8');
  fs.writeFileSync(path.join(PHASE_DIR, '13-01-PLAN.md'), 'plan\n', 'utf8');
  fs.writeFileSync(TRANSCRIPT, '', 'utf8');
}

function writeMarker(extra) {
  const now = new Date().toISOString();
  const payload = Object.assign({
    session_id: SID,
    resume_command: '/gsd-autonomous',
    cwd: PROJ,
    phase: 13,
    ts: now,
    armed_at: now,
    cycles: 0,
    max_cycles: null,
    max_hours: null,
    schema_version: 2,
    // The opt-in. A marker without this stays on the legacy path, which is
    // what every marker already on disk does -- see V-GSDCONT-OPT-IN-DEFAULT.
    continuation: 'stop-block',
  }, extra || {});
  fs.writeFileSync(MARKER, JSON.stringify(payload, null, 2), 'utf8');
}

function payload() {
  return { session_id: SID, cwd: PROJ, transcript_path: TRANSCRIPT, hook_event_name: 'Stop' };
}

function finishedTask(name, body) {
  fs.writeFileSync(path.join(TASKS, name), body, 'utf8');
}

console.log('GSD STOP CONTINUATION GATE');
console.log(`subject: ${SUBJECT}`);
console.log(`fixture: ${ROOT}\n`);

// --- 1. negative control: no marker means this is not an autonomous run ----
resetFixture();
let r = hook.run(payload());
check('V-GSDCONT-NO-MARKER', r.continue === true && !r.decision,
  'no marker -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 2. the measured incident: armed mission, finished unread task ---------
resetFixture();
writeMarker();
finishedTask('b4haxctvm.output', 'x'.repeat(3095));
r = hook.run(payload());
check('V-GSDCONT-ARMED-BLOCKS', r.decision === 'block',
  'armed + unread result -> block',
  `expected block, got ${JSON.stringify(r)}`);
check('V-GSDCONT-TASK-POINTER',
  typeof r.reason === 'string'
    && r.reason.includes('b4haxctvm.output') && r.reason.includes('3095'),
  'reason names the finished task and its byte count',
  `reason did not name the artifact: ${String(r.reason).slice(0, 160)}`);

// --- 3. causal delta: an identical world must NOT block again --------------
r = hook.run(payload());
check('V-GSDCONT-NO-DELTA', r.continue === true && !r.decision,
  'unchanged fingerprint -> continue (no spin)',
  `expected continue on no-delta, got ${JSON.stringify(r)}`);
let st = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
check('V-GSDCONT-STALLED-CLASSIFIED', st[SID].classification === 'STALLED',
  'no-delta run classified STALLED',
  `expected STALLED, got ${st[SID].classification}`);

// --- 4. a real change must re-arm the block --------------------------------
finishedTask('second.output', 'y'.repeat(64));
r = hook.run(payload());
check('V-GSDCONT-DELTA-REBLOCKS', r.decision === 'block',
  'new task output -> block again',
  `expected block after delta, got ${JSON.stringify(r)}`);

// --- 5. budgets ------------------------------------------------------------
resetFixture();
writeMarker({ cycles: 40 });
finishedTask('t.output', 'z');
r = hook.run(payload());
check('V-GSDCONT-BUDGET-CYCLES', r.continue === true,
  'cycles at default ceiling -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

resetFixture();
writeMarker({ armed_at: new Date(Date.now() - 13 * 3600 * 1000).toISOString() });
finishedTask('t.output', 'z');
r = hook.run(payload());
check('V-GSDCONT-BUDGET-HOURS', r.continue === true,
  'armed 13 h ago vs 12 h default -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 6. terminal predicate -------------------------------------------------
resetFixture();
writeMarker({ status: 'complete' });
finishedTask('t.output', 'z');
r = hook.run(payload());
check('V-GSDCONT-TERMINAL', r.continue === true,
  'mission complete -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 7. kill switch --------------------------------------------------------
resetFixture();
writeMarker();
finishedTask('t.output', 'z');
process.env.CPP_GSD_STOP_CONTINUATION = 'off';
r = hook.run(payload());
delete process.env.CPP_GSD_STOP_CONTINUATION;
check('V-GSDCONT-KILLSWITCH', r.continue === true,
  'CPP_GSD_STOP_CONTINUATION=off -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 8. do not ping-pong with closer-guard ---------------------------------
resetFixture();
writeMarker();
finishedTask('t.output', 'z');
fs.writeFileSync(CLOSER_STATE,
  JSON.stringify({ [SID]: { blocked: true, fingerprint: 'f', streak: 1, ts: Date.now() } }),
  'utf8');
r = hook.run(payload());
check('V-GSDCONT-NO-PINGPONG', r.continue === true,
  'closer-guard already blocked this session -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 9. streak ceiling -----------------------------------------------------
resetFixture();
writeMarker();
finishedTask('t.output', 'z');
fs.writeFileSync(STATE_FILE,
  JSON.stringify({ [SID]: { blocked: true, fingerprint: 'stale', streak: hook.MAX_STREAK, ts: Date.now() } }),
  'utf8');
r = hook.run(payload());
check('V-GSDCONT-STREAK-CEILING', r.continue === true,
  `streak at MAX_STREAK=${hook.MAX_STREAK} -> continue`,
  `expected continue, got ${JSON.stringify(r)}`);

// --- 10. fail-open on a malformed marker -----------------------------------
resetFixture();
fs.writeFileSync(MARKER, '{ this is not json', 'utf8');
r = hook.run(payload());
check('V-GSDCONT-FAILOPEN', r.continue === true,
  'unparseable marker -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 11. no session id -----------------------------------------------------
r = hook.run({ cwd: PROJ });
check('V-GSDCONT-NO-SID', r.continue === true,
  'missing session_id -> continue',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 12. wrong event -------------------------------------------------------
resetFixture();
writeMarker();
finishedTask('t.output', 'z');
r = hook.run(Object.assign(payload(), { hook_event_name: 'PostToolUse' }));
check('V-GSDCONT-WRONG-EVENT', r.continue === true,
  'PostToolUse payload -> continue (Stop-only contract)',
  `expected continue, got ${JSON.stringify(r)}`);

// --- 13. the opt-in default: a legacy marker must NOT be touched ----------
// This is the case that protects the 11 markers that existed when the hook
// landed. It is the most important allow-case in the file.
resetFixture();
writeMarker({ continuation: undefined });
finishedTask('t.output', 'z');
r = hook.run(payload());
check('V-GSDCONT-OPT-IN-DEFAULT', r.continue === true && !r.decision,
  'marker without continuation:stop-block -> continue (legacy path)',
  `legacy marker was hijacked: ${JSON.stringify(r)}`);

// ...and the paired positive control, so "refuses everything" cannot pass.
resetFixture();
writeMarker();
finishedTask('t.output', 'z');
r = hook.run(payload());
check('V-GSDCONT-OPT-IN-HONOURED', r.decision === 'block',
  'marker WITH continuation:stop-block -> block',
  `opt-in marker was ignored: ${JSON.stringify(r)}`);

// --- population floor ------------------------------------------------------
// A suite that silently stopped running cases reports the same clean exit as
// one that passed them, so the count itself is asserted.
const EXPECTED = 17;
const total = passes + fails;
console.log(`\nGSDCONT_PASS=${passes}/${total}  threshold=${EXPECTED}/${EXPECTED}`);
if (total !== EXPECTED) {
  console.log(`HARNESS-FAILED: ran ${total} gates, expected ${EXPECTED}`);
  process.exit(2);
}
if (fails) {
  console.log('failed gates: ' + failed.join(', '));
}

try {
  fs.rmSync(ROOT, { recursive: true, force: true });
} catch (err) {
  console.log(`note: fixture cleanup incomplete at ${ROOT}`);
}

process.exit(fails === 0 ? 0 : 1);
