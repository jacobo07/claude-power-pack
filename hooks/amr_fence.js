// amr_fence.js -- AMR strategy fence at the Agent|Task spawn edge (tools/mission_recovery.py).
//
// A mission recovered from a failed agent topology (e.g. a gsd-planner that burned its stall budget with no
// PLAN.md, KSP-FUSION 2026-10-13) records `amr.deny_agent_types` on its record. Its workers may not spawn
// those agent types again: the same strategy may not renew unchanged. The worker is found through its own
// marker `<state>/mission-worker-<sid>.json`; any other session is untouched.
//
// Live wiring: hook-dispatcher.js 'PreToolUse-Agent-default' (registered on matcher Task|Agent).
// Denies only on positive evidence (marker -> mission record -> listed type). Own error -> allow (fail open):
// the mission's packet carries the same rule in words, so a broken fence degrades to advice, never to a block
// of unrelated work. Kill switch CPP_AMR_FENCE=off.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const MID_RE = /^m-[0-9a-f]{6,32}$/;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

// -> {deny: reason|null, mission, type}
function decide(event) {
  const sid = event && event.session_id;
  const tn = event && event.tool_name;
  if (tn && !/^(Agent|Task)$/.test(tn)) return { deny: null };
  if (!sid || !SID_RE.test(sid)) return { deny: null };
  // The worker index is written to GSD_AUTORUN_MARKER_DIR when set, else the state dir (write_worker_index):
  // resolve it the same way, or the fence silently allows everything (audit F8).
  const markerDir = process.env.GSD_AUTORUN_MARKER_DIR || stateDir();
  const w = readJson(path.join(markerDir, `mission-worker-${sid}.json`));
  if (!w || !MID_RE.test(String(w.mission_id || ''))) return { deny: null };
  const m = readJson(path.join(stateDir(), `gsd-mission-${w.mission_id}.json`));
  const amr = m && m.amr;
  if (!amr || !Array.isArray(amr.deny_agent_types) || !amr.deny_agent_types.length) return { deny: null };
  const type = String(((event.tool_input || {}).subagent_type) || 'general-purpose');
  if (!amr.deny_agent_types.map(String).includes(type)) return { deny: null, mission: w.mission_id, type };
  return {
    mission: w.mission_id, type,
    deny: `AMR FENCE -- mission ${w.mission_id} was recovered from a failed ${type} topology on ${amr.unit || 'its unit'}; `
      + 'that strategy may not run again unchanged. Do the work in the main thread from your recovery packet.',
  };
}

function off() {
  const sw = String(process.env.CPP_AMR_FENCE || '').trim().toLowerCase();
  return sw === '0' || sw === 'off' || sw === 'false';
}

// Dispatcher contract: run(data) -> hook output object or null.
function run(ev) {
  try {
    if (off()) return null;
    const r = decide(ev || {});
    if (r.deny) return { hookSpecificOutput: { hookEventName: 'PreToolUse',
      permissionDecision: 'deny', permissionDecisionReason: r.deny } };
  } catch (e) { /* fail open */ }
  return null;
}

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    let out = null;
    try { out = run(JSON.parse(raw.replace(/^﻿/, ''))); } catch (e) { out = null; }
    process.stdout.write(JSON.stringify(out || {}));
  });
}

module.exports = { run, decide };
