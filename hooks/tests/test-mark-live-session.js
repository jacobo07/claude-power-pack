#!/usr/bin/env node
'use strict';
/**
 * V-MLS-* — mark-live-session.js incremental orphan sweep.
 * Runs the REAL hook as a child process against a temp USERPROFILE/HOME, so the
 * live ~/.claude/projects is never touched. Exit 0 = all pass.
 *
 * V-MLS-01 full pass (no state) unmarks a dead "⚡ " session and seals `since`.
 * V-MLS-02 incremental pass reads only mtime>=since or `marked` files. The
 *          negative control (old mtime, not marked, still "⚡ ") MUST stay
 *          marked: the pre-2026-11-22 full sweep would have rewritten it.
 * V-MLS-03 a 1 ms budget still finishes the first pass over several runs
 *          (resumable cursor) and unmarks every dead file.
 * V-MLS-04 the hook's own session enters `marked` (an idle-then-crashed
 *          session has an old mtime and is found only that way).
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const HOOK = path.resolve(__dirname, '..', 'mark-live-session.js');
const PROJ = 'C--tmp-proj';
let failures = 0;

function check(id, cond, detail) {
  if (cond) { console.log('PASS ' + id); return; }
  failures++;
  console.log('FAIL ' + id + ' :: ' + detail);
}

function uuid() {
  const h = () => Math.floor(Math.random() * 0x10000).toString(16).padStart(4, '0');
  return `${h()}${h()}-${h()}-4${h().slice(1)}-a${h().slice(1)}-${h()}${h()}${h()}`;
}

function sandbox() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'mls-'));
  fs.mkdirSync(path.join(home, '.claude', 'projects', PROJ), { recursive: true });
  return home;
}

function transcript(home, id, title, ageMs) {
  const p = path.join(home, '.claude', 'projects', PROJ, id + '.jsonl');
  const lines = [
    JSON.stringify({ type: 'user', message: { role: 'user', content: 'build the widget pipeline now' }, sessionId: id }),
    JSON.stringify({ type: 'custom-title', customTitle: title, sessionId: id }),
  ];
  fs.writeFileSync(p, lines.join('\n') + '\n');
  const t = (Date.now() - ageMs) / 1000;
  fs.utimesSync(p, t, t);
  return p;
}

function lastTitle(p) {
  const lines = fs.readFileSync(p, 'utf-8').trim().split('\n').reverse();
  for (const l of lines) {
    const o = JSON.parse(l);
    if (o.type === 'custom-title') return o.customTitle;
  }
  return null;
}

const stateFile = (home) => path.join(home, '.claude', 'state', 'mark-live-session', 'sweep.json');
function readState(home) {
  try { return JSON.parse(fs.readFileSync(stateFile(home), 'utf-8')); } catch { return { marked: {} }; }
}
function writeState(home, s) {
  fs.mkdirSync(path.dirname(stateFile(home)), { recursive: true });
  fs.writeFileSync(stateFile(home), JSON.stringify(s));
}

function runHook(home, payload, budgetMs) {
  const env = { ...process.env, USERPROFILE: home, HOME: home };
  delete env.PP_EVT_SID; delete env.PP_EVT_EVENT;
  if (budgetMs) env.PP_MLS_SWEEP_BUDGET_MS = String(budgetMs);
  const r = spawnSync(process.execPath, [HOOK], { input: JSON.stringify(payload || {}), env, timeout: 60000 });
  if (r.status !== 0) throw new Error('hook exit ' + r.status + ': ' + String(r.stderr));
}

const H2 = 2 * 3600 * 1000;

// V-MLS-01
{
  const home = sandbox();
  const dead = uuid();
  const p = transcript(home, dead, '⚡ build the widget pipeline now', H2);
  runHook(home, { hook_event_name: 'Stop' });
  const s = readState(home);
  check('V-MLS-01a dead session unmarked', !lastTitle(p).startsWith('⚡ '), lastTitle(p));
  check('V-MLS-01b since sealed, scan closed', Number.isFinite(s.since) && s.scan === null, JSON.stringify(s));
  check('V-MLS-01c dead not left in marked', !(dead in s.marked), JSON.stringify(s.marked));
}

// V-MLS-02
{
  const home = sandbox();
  const control = uuid(), recent = uuid(), remembered = uuid();
  const pc = transcript(home, control, '⚡ control', H2);
  const pr = transcript(home, recent, '⚡ recent', 30 * 60 * 1000);
  const pm = transcript(home, remembered, '⚡ remembered', H2);
  writeState(home, { v: 2, since: Date.now() - 3600 * 1000, marked: { [remembered]: PROJ }, scan: null });
  runHook(home, { hook_event_name: 'Stop' });
  const s = readState(home);
  check('V-MLS-02a negative control NOT read (pruned)', lastTitle(pc) === '⚡ control', lastTitle(pc));
  check('V-MLS-02b mtime>=since file unmarked', !lastTitle(pr).startsWith('⚡ '), lastTitle(pr));
  check('V-MLS-02c marked file unmarked', !lastTitle(pm).startsWith('⚡ '), lastTitle(pm));
  check('V-MLS-02d unmarked file left `marked`', !(remembered in s.marked), JSON.stringify(s.marked));
}

// V-MLS-03
{
  const home = sandbox();
  const paths = [0, 1, 2, 3].map(() => transcript(home, uuid(), '⚡ chunked', H2));
  let runs = 0;
  let sealed = false;
  while (runs < 12 && !sealed) {
    runHook(home, { hook_event_name: 'Stop' }, 1);
    runs++;
    sealed = Number.isFinite(readState(home).since);
  }
  check('V-MLS-03a first pass completes under a 1 ms budget', sealed, 'runs=' + runs);
  check('V-MLS-03b pass was actually chunked', runs >= 2, 'runs=' + runs);
  check('V-MLS-03c every dead file unmarked', paths.every((p) => !lastTitle(p).startsWith('⚡ ')),
    paths.map(lastTitle).join(' | '));
}

// V-MLS-04
{
  const home = sandbox();
  const me = uuid();
  const p = transcript(home, me, 'build the widget pipeline now', 1000);
  runHook(home, { hook_event_name: 'Stop', session_id: me, transcript_path: p });
  const s = readState(home);
  check('V-MLS-04 own session enters marked', s.marked[me] === PROJ, JSON.stringify(s.marked));
}

// A transcript in a named project folder (V-MLS-05/06 need two folders).
function transcriptIn(home, proj, id, title, ageMs) {
  const dir = path.join(home, '.claude', 'projects', proj);
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, id + '.jsonl');
  fs.writeFileSync(p, [
    JSON.stringify({ type: 'user', message: { role: 'user', content: 'build the widget pipeline now' }, sessionId: id }),
    JSON.stringify({ type: 'custom-title', customTitle: title, sessionId: id }),
  ].join('\n') + '\n');
  const t = (Date.now() - ageMs) / 1000;
  fs.utimesSync(p, t, t);
  return p;
}

// V-MLS-05 (pre-push review of 8f4e20c6): a folder whose name extends another's
// (`P` then `P-wt`) sorts AFTER it, but with a '/' key separator its keys compared
// BELOW a cursor left inside `P` ('-' 0x2D < '/' 0x2F), so a budget cut there
// skipped all of `P-wt` and then sealed the pass. 29 such pairs exist on the
// Owner's host.
{
  const home = sandbox();
  const paths = [];
  for (const proj of [PROJ, PROJ + '-wt']) {
    for (let i = 0; i < 3; i++) paths.push(transcriptIn(home, proj, uuid(), '⚡ prefix pair', H2));
  }
  let runs = 0;
  let sealed = false;
  while (runs < 20 && !sealed) {
    runHook(home, { hook_event_name: 'Stop' }, 1);
    runs++;
    sealed = Number.isFinite(readState(home).since);
  }
  check('V-MLS-05a prefix-pair pass was chunked and sealed', sealed && runs >= 2, 'runs=' + runs);
  check('V-MLS-05b every dead file in BOTH folders unmarked',
    paths.every((p) => !lastTitle(p).startsWith('⚡ ')), paths.map(lastTitle).join(' | '));
}

// V-MLS-06: state saved before SWEEP_STATE_V 2 is restarted, not trusted.
//  a) a pass SEALED under the old '/' key: the `P-wt` file it skipped is older than
//     `since` and not in `marked`, so only a fresh full pass reaches it (the host's
//     own sweep.json was in exactly this shape; review of the 8f4e20c6 fix).
//  b) a scan stopped mid-way under the old key is redone from the start.
//  c) a scan whose cursor is not a string does not stop the sweep.
{
  const home = sandbox();
  const skipped = transcriptIn(home, PROJ + '-wt', uuid(), '⚡ skipped by the old key', H2);
  writeState(home, { since: Date.now() - 60 * 1000, marked: {}, scan: null });
  runHook(home, { hook_event_name: 'Stop' });
  check('V-MLS-06a old sealed pass is redone: skipped file unmarked', !lastTitle(skipped).startsWith('⚡ '), lastTitle(skipped));
  check('V-MLS-06a state now carries v2', readState(home).v === 2, JSON.stringify(readState(home)));
}
{
  const home = sandbox();
  const ids = [uuid(), uuid()].sort();
  const all = [transcriptIn(home, PROJ, ids[0], '⚡ pending', H2), transcriptIn(home, PROJ, ids[1], '⚡ pending', H2),
    transcriptIn(home, PROJ + '-wt', uuid(), '⚡ pending', H2)];
  writeState(home, { since: null, marked: {}, scan: { start: Date.now() - 1000, cursor: PROJ + '/' + ids[0] + '.jsonl' } });
  runHook(home, { hook_event_name: 'Stop' });
  check('V-MLS-06b old mid-scan state redone, every dead file unmarked',
    all.every((p) => !lastTitle(p).startsWith('⚡ ')), all.map(lastTitle).join(' | '));
}
{
  const home = sandbox();
  const p = transcriptIn(home, PROJ, uuid(), '⚡ pending', H2);
  writeState(home, { v: 2, since: null, marked: {}, scan: { start: Date.now() - 1000, cursor: 7 } });
  runHook(home, { hook_event_name: 'Stop' });
  check('V-MLS-06c a non-string cursor does not stop the sweep', !lastTitle(p).startsWith('⚡ '), lastTitle(p));
}

console.log(failures === 0 ? 'ALL PASS' : failures + ' FAILURE(S)');
process.exit(failures === 0 ? 0 : 1);
