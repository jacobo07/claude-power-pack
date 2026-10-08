// goal_binding.js -- which goal a session spends against (extracted from session_budget_guard.js).
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

function goalBinding(event, sid) {
  const ix = readJson(path.join(stateDir(), 'goal-budget', 'index.json'));
  const entry = g => (ix && typeof ix === 'object' && ix[g] && typeof ix[g] === 'object') ? ix[g] : null;
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

module.exports = { goalBinding, normPath, under, stateDir, readJson };
