// goal_binding.js -- which goal a session spends against (extracted from session_budget_guard.js).
//
// Resolution order (WU-1, prospective binding). Python twin: tools/mission_spend.py resolve_binding.
//   (a) <state>/goal-binding/<sid>.json, immutable once written:
//         {goal, since_ts, source: launcher|explicit|cwd, pid}. It always wins; a session whose record
//         names another goal (or "none") is never re-bound by cwd.
//   (b) env CPP_GOAL: honoured when the record agrees; a record that disagrees ignores it and logs a
//         warning row (<state>/goal-binding/warnings.jsonl). With no record, env binds as before
//         (explicit, no cut) so existing env-bound sessions keep their behaviour.
//   (c) cwd under a goal root: WRITES the record with since_ts = now, at the first MUTATING call. A
//         session that has only read (Read/Grep/Glob, goal-status, git log/status/show) gets an
//         in-memory binding from now and leaves no record (observer isolation).
//   (d) the budget file's `goal` field (legacy, no cut).
// CPP_PROSPECTIVE_BIND=0 restores the old resolver exactly (no record read or written).
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
function bindingPath(sid) { return path.join(bindingDir(), `${sid}.json`); }

function nowTs() { return new Date().toISOString().slice(0, 19); }

function readBinding(sid) {
  const r = readJson(bindingPath(sid));
  return r && typeof r === 'object' && typeof r.goal === 'string' && r.goal ? r : null;
}

// Immutable: 'wx' fails when the record exists, and the existing one is returned instead.
function writeBinding(sid, goal, source) {
  const rec = { goal, since_ts: nowTs(), source, pid: process.pid };
  try {
    fs.mkdirSync(bindingDir(), { recursive: true });
    fs.writeFileSync(bindingPath(sid), JSON.stringify(rec), { flag: 'wx' });
    return rec;
  } catch (e) {
    return readBinding(sid) || rec;
  }
}

function warn(sid, text) {
  try {
    fs.mkdirSync(bindingDir(), { recursive: true });
    fs.appendFileSync(path.join(bindingDir(), 'warnings.jsonl'),
      JSON.stringify({ ts: nowTs(), sid, warning: text }) + '\n');
  } catch (e) { /* a warning that cannot be written is not a reason to fail a call */ }
}

const READ_TOOLS = new Set(['Read', 'Grep', 'Glob']);
const READ_ONLY_CMD = /^\s*(?:&\s*)?(?:(?:['"]?[^\s'"]*[\\/])?git(?:\.exe)?['"]?\s+(?:-C\s+\S+\s+)?(?:log|status|show)\b|(?:['"]?[^\s'"]*[\\/])?(?:python3?|py)(?:\.exe)?['"]?\s+['"]?(?:[^\s'"]*[\\/])?mission_spend\.py['"]?\s+goal-status\b)/i;

// A call is read-only when it is Read/Grep/Glob, or a single shell command that is goal-status or
// git log/status/show with no chaining, redirection or substitution. Everything else mutates.
function isReadOnlyCall(event) {
  const tool = String((event && event.tool_name) || '');
  if (READ_TOOLS.has(tool)) return true;
  const cmd = event && event.tool_input && typeof event.tool_input.command === 'string' ? event.tool_input.command : '';
  if (!cmd || /[;&|<>`\n]|\$\(/.test(cmd.replace(/^\s*&\s*/, ''))) return false;
  return READ_ONLY_CMD.test(cmd);
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

function goalBinding(event, sid) {
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
  if (ix && typeof ix === 'object' && event.cwd) {
    for (const [g, e] of Object.entries(ix)) {
      if (e && Array.isArray(e.roots) && e.roots.some(r => under(event.cwd, r))) {
        if (isReadOnlyCall(event)) return { goal: g, entry: e, record: null, sinceTs: nowTs(), provisional: true };
        const w = writeBinding(sid, g, 'cwd');
        return { goal: w.goal, entry: w.goal === g ? e : entry(w.goal), record: w, sinceTs: w.since_ts || null };
      }
    }
  }
  return legacyBinding(event, sid, ix, entry);
}

module.exports = { goalBinding, normPath, under, stateDir, readJson, readBinding, writeBinding, bindingPath,
  isReadOnlyCall, prospective };
