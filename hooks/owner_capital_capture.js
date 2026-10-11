#!/usr/bin/env node
/**
 * owner_capital_capture.js -- UserPromptSubmit. When the Owner types a capital approval ("approve everything",
 * "approve dgl only", "modify dgl to 37M", "revoke dgl"), record {session_id, transcript_path, prompt, ts} and
 * start `mission_spend.py capital-apply-pending` detached and windowless. The apply leg retries until the
 * transcript has flushed the Owner entry, and it re-verifies that entry itself; this hook is a trigger, not an
 * authority. Never blocks the prompt, never writes stdout. Fail-open absolute.
 * Kill switch: CPP_OCA_CAPTURE=off. Test seam: CPP_OCA_NO_SPAWN=1 skips the spawn, CPP_CAPITAL_ROOT moves the store.
 * Red branch: tools/test_capital_authority.py V-OCA-HOOK-CAPTURE. Grammar mirrors capital_authority.parse_approval.
 */
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const GOAL = '[a-z0-9][a-z0-9._-]*';
const NEG = /(?:\b(?:don't|dont|do not|not|never|can't|cannot|no)\b|n't\b)/;
const GRAMMAR = [
  /^(?:yes[, ]+)?approve(?:d)?(?: everything| all)?$/,
  /^approve (?:all )?p(?:50|80|95)$/,
  new RegExp(`^approve ${GOAL} only$`),
  new RegExp(`^modify ${GOAL} to [0-9][0-9,_.]*[mk]?$`),
  new RegExp(`^revoke ${GOAL}$`),
];

function isCapitalIntent(text) {
  if (typeof text !== 'string') return false;
  const t = text.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!]+$/, '');
  if (!t || NEG.test(t)) return false;
  return GRAMMAR.some((g) => g.test(t));
}

// (sha, goal) pairs in pending.json with no capsule row yet. A capsule row of any state is final for the sweep:
// APPLIED is done and a journalled refusal needs a new packet, so only a never-tried pair re-fires the apply leg.
function outstanding(root) {
  let pend;
  try { pend = JSON.parse(fs.readFileSync(path.join(root, 'pending.json'), 'utf8').replace(/^﻿/, '')); } catch { return []; }
  const done = new Set();
  try {
    for (const ln of fs.readFileSync(path.join(root, 'capsules.jsonl'), 'utf8').split('\n')) {
      try { const r = JSON.parse(ln); done.add(`${r.sha}|${r.goal}`); } catch { /* partial line */ }
    }
  } catch { /* no capsules yet */ }
  const out = [];
  for (const ent of Array.isArray(pend) ? pend : [pend]) {
    let sha;
    try { sha = crypto.createHash('sha256').update(fs.readFileSync(ent.packet)).digest('hex'); } catch { continue; }
    for (const g of ent.goals || []) if (!done.has(`${sha}|${g}`)) out.push(`${sha}|${g}`);
  }
  return out;
}

// Two triggers, one authority. An approval typed now is captured; an approval typed BEFORE this hook could see
// it (or whose transcript flush the apply leg missed) is swept on the Owner's next message while its pair is
// still outstanding. Neither row is authority: apply() re-reads the Owner-typed entry after the displayed sha.
function run(raw) {
  let ev;
  try { ev = JSON.parse(raw); } catch { return; }
  if (!ev || typeof ev.prompt !== 'string') return;
  const root = process.env.CPP_CAPITAL_ROOT || path.join(os.homedir(), '.claude', 'state', 'capital-authority');
  const intent = isCapitalIntent(ev.prompt);
  if (!intent && (!ev.transcript_path || outstanding(root).length === 0)) return;
  fs.mkdirSync(root, { recursive: true });
  fs.appendFileSync(path.join(root, 'approvals.jsonl'), JSON.stringify({
    session_id: ev.session_id || null, transcript_path: ev.transcript_path || null,
    prompt: intent ? ev.prompt : null, kind: intent ? 'approval' : 'pending-sweep', ts: new Date().toISOString(),
  }) + '\n');
  if (process.env.CPP_OCA_NO_SPAWN === '1') return;
  const py = process.env.CLAUDE_PY_EXE || 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
  const tool = path.join(__dirname, '..', 'tools', 'mission_spend.py');
  const child = spawn(py, ['-I', tool, 'capital-apply-pending'], {
    detached: true, stdio: 'ignore', windowsHide: true, env: process.env,
  });
  child.on('error', () => {});
  child.unref();
}

if (require.main === module) {
  if (process.env.CPP_OCA_CAPTURE === 'off') process.exit(0);
  let buf = '';
  const timer = setTimeout(() => process.exit(0), 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (d) => { buf += d; });
  process.stdin.on('end', () => {
    clearTimeout(timer);
    try { run(buf); } catch { /* fail-open: a capture failure must never cost the prompt */ }
    process.exit(0);
  });
  process.stdin.on('error', () => process.exit(0));
}
module.exports = { isCapitalIntent, outstanding, run };
