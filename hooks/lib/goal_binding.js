// goal_binding.js -- which goal a session spends against (extracted from session_budget_guard.js).
//
// Resolution order (WU-1, prospective binding). Python twin: tools/mission_spend.py resolve_binding.
//   (a) <state>/goal-binding/<sid>.json, immutable once written:
//         {goal, since_ts, source: launcher|explicit|cwd, pid}. It always wins; a session whose record
//         names another goal (or "none") is never re-bound by cwd.
//       GENERATIONS (econ-contain WS-E): a recovery transition never edits a record, it writes the next
//       one, <sid>.g<N>.json ('wx'), carrying {gen, prev, reason, fenced:[goal...]}. The highest
//       generation is the binding. Only the recovery plane writes one (hooks/econ_admission.js and
//       mission_spend.py econ-*); the guard denies a bound session writing goal-binding state.
//   (b) env CPP_GOAL: honoured when the record agrees; a record that disagrees ignores it and logs a
//         warning row (<state>/goal-binding/warnings.jsonl). With no record, env binds as before
//         (explicit, no cut) so existing env-bound sessions keep their behaviour.
//   (c) cwd under a goal root: WRITES the record with since_ts = now, at the first MUTATING call. A
//         session that has only read (Read/Grep/Glob, goal-status, git log/status/show) gets an
//         in-memory binding from now and leaves no record (observer isolation).
//       QUARANTINE (econ-contain WS-C): cwd never binds to a goal whose current lease is EXHAUSTED.
//         d5063bac bound itself to ctx-same-pane 50 minutes after the cap was crossed and every turn
//         after that bought ~200K to be refused. Such a session is returned `quarantine` instead:
//         reads pass uncharged, mutation of the goal's workspace is FENCED, nothing is renewed.
//   (d) the budget file's `goal` field (legacy, no cut).
// CPP_PROSPECTIVE_BIND=0 restores the old resolver exactly (no record read or written).
// opts.observe: resolve without ever writing a record (the pre-model admission hook uses it).
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

function normPath(p) {
  const r = path.resolve(String(p || '')).replace(/[\\/]+$/, '');
  return process.platform === 'win32' ? r.toLowerCase() : r;
}

function under(p, root) {
  const a = normPath(p), b = normPath(root);
  return a === b || a.startsWith(b + path.sep);
}

function prospective() {
  const v = String(process.env.CPP_PROSPECTIVE_BIND || '').trim().toLowerCase();
  return !(v === '0' || v === 'off' || v === 'false');
}

function bindingDir() { return path.join(stateDir(), 'goal-binding'); }
function bindingPath(sid, gen) { return path.join(bindingDir(), gen && gen > 1 ? `${sid}.g${gen}.json` : `${sid}.json`); }

function nowTs() { return new Date().toISOString().slice(0, 19); }

function validRec(r) { return r && typeof r === 'object' && typeof r.goal === 'string' && r.goal ? r : null; }

// The highest generation is the binding. Generation 1 is <sid>.json; a missing g<N> ends the chain.
function readBinding(sid) {
  let rec = validRec(readJson(bindingPath(sid, 1)));
  if (!rec) return null;
  rec = Object.assign({ gen: 1 }, rec);
  for (let n = 2; n < 1000; n++) {
    const r = validRec(readJson(bindingPath(sid, n)));
    if (!r) break;
    rec = Object.assign({ gen: n }, r);
  }
  return rec;
}

// Immutable: 'wx' fails when the record exists, and the existing one is returned instead.
function writeBinding(sid, goal, source) {
  const rec = { goal, since_ts: nowTs(), source, pid: process.pid };
  try {
    fs.mkdirSync(bindingDir(), { recursive: true });
    fs.writeFileSync(bindingPath(sid, 1), JSON.stringify(rec), { flag: 'wx' });
    return rec;
  } catch (e) {
    return readBinding(sid) || rec;
  }
}

// Recovery transition: the next generation, never an edit. A goal the session leaves stays in `fenced`
// (accumulated over generations), so a detached pane cannot keep mutating that goal's workspace
// outside its accounting (NO_SESSION_LAUNDERING). Returns the written record, or null on a lost race.
function supersedeBinding(sid, goal, source, reason) {
  const cur = readBinding(sid);
  const gen = cur ? cur.gen + 1 : 1;
  const fenced = Array.from(new Set([...(cur && Array.isArray(cur.fenced) ? cur.fenced : []),
    ...(cur && cur.goal && cur.goal !== 'none' && cur.goal !== goal ? [cur.goal] : [])]));
  const rec = { goal, since_ts: nowTs(), source, pid: process.pid, gen, prev: cur ? cur.goal : null, reason, fenced };
  try {
    fs.mkdirSync(bindingDir(), { recursive: true });
    fs.writeFileSync(bindingPath(sid, gen), JSON.stringify(rec), { flag: 'wx' });
    fs.appendFileSync(path.join(bindingDir(), 'transitions.jsonl'),
      JSON.stringify({ ts: rec.since_ts, sid, from: rec.prev, to: goal, gen, source, reason, fenced }) + '\n');
    return rec;
  } catch (e) { return null; }
}

function warn(sid, text) {
  try {
    fs.mkdirSync(bindingDir(), { recursive: true });
    fs.appendFileSync(path.join(bindingDir(), 'warnings.jsonl'),
      JSON.stringify({ ts: nowTs(), sid, warning: text }) + '\n');
  } catch (e) { /* a warning that cannot be written is not a reason to fail a call */ }
}

// --- Journal reads (the GoalLedger journal is the authority; see modules/provider_routing/ledger.py) --
// Only rows whose raw text carries the needle are parsed, so a long journal costs one read + a scan.
function journalRows(goal, needles) {
  let text;
  try { text = fs.readFileSync(path.join(stateDir(), 'goal-budget', goal, 'spend.journal.jsonl'), 'utf8'); } catch (e) { return []; }
  const out = [];
  for (const line of text.split('\n')) {
    if (!line || !needles.some(n => line.indexOf(n) >= 0)) continue;
    try { out.push(JSON.parse(line)); } catch (e) { /* a torn tail row is skipped, as the ledger does */ }
  }
  return out;
}

// The current lease's EXHAUSTED marker (ledger op "exhausted"). Lease ids follow _gfold: L1 plus one
// per distinct lease_open succession id.
function goalExhausted(goal) {
  const rows = journalRows(goal, ['"exhausted"', '"lease_open"']);
  const opened = new Set(rows.filter(r => r.op === 'lease_open').map(r => r.succession_id));
  const cur = `L${opened.size + 1}`;
  return rows.some(r => r.op === 'exhausted' && (r.lease || 'L1') === cur);
}

// Fold in journal order: an Owner raise ("untomb", written with the successor lease it opened) lifts the
// session's fence; a later tombstone (the successor lease crossed too) fences it again.
function sidTombstoned(goal, sid) {
  let t = false;
  for (const r of journalRows(goal, ['"tombstone"', '"untomb"'])) {
    if (r.sid !== sid) continue;
    if (r.op === 'tombstone') t = true;
    else if (r.op === 'untomb') t = false;
  }
  return t;
}

const READ_TOOLS = new Set(['Read', 'Grep', 'Glob']);
const READ_ONLY_CMD = /^\s*(?:&\s*)?(?:(?:['"]?[^\s'"]*[\\/])?git(?:\.exe)?['"]?\s+(?:-C\s+\S+\s+)?(?:log|status|show)\b|(?:['"]?[^\s'"]*[\\/])?(?:python3?|py)(?:\.exe)?['"]?\s+['"]?(?:[^\s'"]*[\\/])?(?:mission_spend\.py['"]?\s+(?:goal-status|goal-lineage)|econ_plane\.py['"]?\s+status)\b)/i;

// A call is read-only when it is Read/Grep/Glob, or a single shell command that is goal-status,
// goal-lineage, econ_plane status or git log/status/show with no chaining, redirection or substitution.
// Everything else mutates.
function isReadOnlyCall(event) {
  const tool = String((event && event.tool_name) || '');
  if (READ_TOOLS.has(tool)) return true;
  const cmd = event && event.tool_input && typeof event.tool_input.command === 'string' ? event.tool_input.command : '';
  if (!cmd || /[;&|<>`\n]|\$\(/.test(cmd.replace(/^\s*&\s*/, ''))) return false;
  return READ_ONLY_CMD.test(cmd);
}

// The subject a mutating call acts on: the file it names, else the directory it runs in.
function callTarget(event) {
  const ti = (event && event.tool_input) || {};
  for (const k of ['file_path', 'notebook_path', 'path']) if (typeof ti[k] === 'string' && ti[k]) return ti[k];
  return event && event.cwd ? event.cwd : null;
}

// FENCE (econ-contain WS-E/I): a mutating call whose subject lies in a goal's workspace is refused when
// that goal's lease is exhausted, when this session left that goal (detach), or when this session is
// tombstoned on it. Keyed by the subject (goal roots), never by cwd, pane, sid freshness or host, so a
// changed directory, a detach or a fresh pane cannot continue an exhausted goal's work unaccounted.
// `skipGoal`: the goal the session is legitimately bound to (decideGoal judges that one).
function fenceFor(event, sid, rec, skipGoal) {
  if (isReadOnlyCall(event)) return null;
  const target = callTarget(event);
  if (!target) return null;
  const ix = readJson(path.join(stateDir(), 'goal-budget', 'index.json'));
  if (!ix || typeof ix !== 'object') return null;
  for (const [g, e] of Object.entries(ix)) {
    if (g === skipGoal || !e || !Array.isArray(e.roots) || !e.roots.some(r => under(target, r))) continue;
    if (rec && Array.isArray(rec.fenced) && rec.fenced.includes(g)) return { goal: g, why: 'this session detached from it' };
    if (goalExhausted(g)) return { goal: g, why: 'its current lease is exhausted' };
    if (sidTombstoned(g, sid)) return { goal: g, why: 'this session is tombstoned on it' };
  }
  return null;
}

function legacyBinding(event, sid, ix, entry) {
  const env = String(process.env.CPP_GOAL || '').trim();
  if (env) return { goal: env, entry: entry(env) };
  if (ix && typeof ix === 'object' && event.cwd) {
    for (const [g, e] of Object.entries(ix)) {
      if (e && Array.isArray(e.roots) && e.roots.some(r => under(event.cwd, r))) return { goal: g, entry: e };
    }
  }
  const b = readJson(path.join(stateDir(), `session-budget-${sid}.json`));
  if (b && typeof b.goal === 'string' && b.goal) return { goal: b.goal, entry: entry(b.goal) };
  return null;
}

// Latest claim per workspace from the append-only journal; null when the registry does not exist yet
// (the pre-W2 behaviour) or cannot be read as a registry.
function registryClaims() {
  let txt;
  try { txt = fs.readFileSync(path.join(stateDir(), 'goal-budget', 'workspace.journal.jsonl'), 'utf8'); } catch (e) { return null; }
  const held = {};
  for (const line of txt.split('\n')) {
    if (!line.trim()) continue;
    let r;
    try { r = JSON.parse(line); } catch (e) { continue; }
    if (r && r.op === 'claim' && typeof r.workspace === 'string' && typeof r.goal === 'string') held[r.workspace] = r;
  }
  return held;
}

function quarantined(goal, entry) {
  return { goal, entry, record: null, sinceTs: nowTs(), provisional: true, quarantine: true };
}

function goalBinding(event, sid, opts) {
  const observe = !!(opts && opts.observe);
  const ix = readJson(path.join(stateDir(), 'goal-budget', 'index.json'));
  const entry = g => (ix && typeof ix === 'object' && ix[g] && typeof ix[g] === 'object') ? ix[g] : null;
  if (!prospective()) return legacyBinding(event, sid, ix, entry);
  const env = String(process.env.CPP_GOAL || '').trim();
  const rec = readBinding(sid);
  if (rec) {
    if (env && env !== rec.goal) warn(sid, `CPP_GOAL=${env} ignored: the binding record names ${rec.goal} (${rec.source})`);
    if (rec.goal === 'none') return null;
    return { goal: rec.goal, entry: entry(rec.goal), record: rec, sinceTs: rec.since_ts || null };
  }
  if (env) return { goal: env, entry: entry(env) };
  const claims = registryClaims();
  if (claims && event.cwd) {                  // (W2) an explicit registry holder beats the goal roots
    let best = null;
    for (const c of Object.values(claims)) {
      if (under(event.cwd, c.workspace) && (!best || c.workspace.length > best.workspace.length)) best = c;
    }
    if (best && entry(best.goal)) {
      const extra = { gen: best.gen, lease: best.lease };
      if (goalExhausted(best.goal)) return quarantined(best.goal, entry(best.goal));
      if (observe || isReadOnlyCall(event)) return Object.assign({ goal: best.goal, entry: entry(best.goal), record: null, sinceTs: nowTs(), provisional: true }, extra);
      const w = writeBinding(sid, best.goal, 'registry');
      return Object.assign({ goal: w.goal, entry: entry(w.goal), record: w, sinceTs: w.since_ts || null }, extra);
    }
  }
  if (ix && typeof ix === 'object' && event.cwd) {
    for (const [g, e] of Object.entries(ix)) {
      if (e && Array.isArray(e.roots) && e.roots.some(r => under(event.cwd, r))) {
        if (goalExhausted(g)) return quarantined(g, e);
        // observe only once the registry exists: entering a goal worktree never binds, claims or settles
        if (observe || claims || isReadOnlyCall(event)) return { goal: g, entry: e, record: null, sinceTs: nowTs(), provisional: true };
        const w = writeBinding(sid, g, 'cwd');
        return { goal: w.goal, entry: w.goal === g ? e : entry(w.goal), record: w, sinceTs: w.since_ts || null };
      }
    }
  }
  return legacyBinding(event, sid, ix, entry);
}

module.exports = { goalBinding, normPath, under, stateDir, readJson, readBinding, writeBinding, bindingPath,
  isReadOnlyCall, prospective, supersedeBinding, goalExhausted, sidTombstoned, fenceFor, journalRows, callTarget };
