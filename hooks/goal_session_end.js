// goal_session_end.js -- SessionEnd wake for a goal-bound session (dgl W4).
//
// On SessionEnd for a sid that has a goal-binding record, append ONE row {sid, goal, lease, ended_at, reason}
// to <state>/goal-budget/<goal>/ended.jsonl and nothing else. It never settles, closes, claims or reads a
// transcript: a wake is a hint that the worker is gone, and tools/goal_chain.py accepts it as `dead`
// evidence only together with a measured spend. Not registered in settings (W5 owns registration).
// Fail-open: any error returns null and the session ends normally.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const GOAL_RE = /^[A-Za-z0-9._-]{1,128}$/;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

// The lease this sid last claimed in the workspace registry (read-only), or null.
function claimedLease(sid, goal) {
  let text;
  try { text = fs.readFileSync(path.join(stateDir(), 'goal-budget', 'workspace.journal.jsonl'), 'utf8'); } catch (e) { return null; }
  let lease = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try {
      const r = JSON.parse(line);
      if (r && r.op === 'claim' && r.goal === goal && r.holder_sid === sid) lease = r.lease;
    } catch (e) { /* torn tail */ }
  }
  return lease;
}

function wake(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const rec = readJson(path.join(stateDir(), 'goal-binding', `${sid}.json`));
  const goal = rec && rec.goal;
  if (!goal || goal === 'none' || !GOAL_RE.test(goal)) return null;
  const dir = path.join(stateDir(), 'goal-budget', goal);
  if (!fs.existsSync(dir)) return null;                       // an unknown goal gets no directory made for it
  const row = { sid, goal, lease: claimedLease(sid, goal), ended_at: new Date().toISOString(),
    reason: typeof event.reason === 'string' ? event.reason : null };
  fs.appendFileSync(path.join(dir, 'ended.jsonl'), JSON.stringify(row) + '\n');
  return row;
}

async function run(event) {
  try { wake(event); } catch (e) { /* a wake that cannot be written is silence, never a failure */ }
  return null;
}

module.exports = { run, wake };
