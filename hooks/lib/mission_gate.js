// mission_gate.js -- in-turn enforcement for a mission worker and its subagents (CCR v5 Stage A, A3/A4).
//
// Called from session_budget_guard.decide (registered PreToolUse chain), so it needs no new hook registration.
// Measured 2026-10-15 (vault/plans/ccr-v5-vehicle-repair-2026-10-15.md): a cost hold reached the worker only as a
// PostToolUse notice (mission_wall.js cannot deny) and the 5-minute sweep stops it later; one gsd-planner subagent
// spent 24.0M in 157 calls with no cap. Three denials, each only on positive evidence from the mission record:
//   1. COST HOLD   -- the worker's mission carries a cost hold: every tool call is refused until the Owner releases it.
//   2. LEASE WRITE -- the worker may not change its own authority: any write-capable call naming the mission
//                     record, or a state-changing gsd_mission.py verb, is refused (status/topology stay open).
//   3. SUBAGENT CAP-- a subagent call past its per-agent call or processed-token cap is refused.
// The worker is found through its marker `<marker-dir>/mission-worker-<sid>.json`; any other session is untouched.
// Own error -> allow (fail open): a broken gate degrades to the sweep, never to a block of unrelated work.
// Kill switch CPP_MISSION_GATE=off.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const MID_RE = /^m-[0-9a-f]{6,32}$/;
const AGENT_RE = /^[A-Za-z0-9._:-]{1,128}$/;
const DEFAULT_CAP = { calls: 30, tokens: 3000000 };
const USAGE_KEYS = ['input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'];
const WRITERS = /^(Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit)$/;
const RECORD_NAME = /gsd-mission-m-[0-9a-f]{6,32}|mission-worker-|gsd-autorun-/;
const MUTATING_VERB = /gsd_mission\.py['"]?\s+(?:-\S+\s+)*(arm|arm-chain|session-start|handoff|directive|hold|release|bind|obligation|authority|protocol|envelope|admit|supervise)\b/;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

function off() {
  const sw = String(process.env.CPP_MISSION_GATE || '').trim().toLowerCase();
  return sw === '0' || sw === 'off' || sw === 'false';
}

function isCostHold(h) {
  return !!h && (h.kind === 'cost' || String(h.reason || '').startsWith('cost breaker'));
}

function fmt(n) { return Number(n).toLocaleString('en-US'); }

function positive(v) { const n = Number(v); return Number.isFinite(n) && n > 0 ? n : null; }

// Cap for one agent type: record per-type, record default, environment, built-in. Positive numbers only.
function capFor(record, type) {
  const caps = (record && record.subagent_caps) || {};
  const pick = (k) => {
    const c = caps[k];
    return c && typeof c === 'object' ? { calls: positive(c.calls), tokens: positive(c.tokens) } : { calls: null, tokens: null };
  };
  const t = pick(type);
  const d = pick('default');
  return {
    calls: t.calls || d.calls || positive(process.env.CPP_SUBAGENT_CAP_CALLS) || DEFAULT_CAP.calls,
    tokens: t.tokens || d.tokens || positive(process.env.CPP_SUBAGENT_CAP_TOKENS) || DEFAULT_CAP.tokens,
  };
}

// Processed tokens of one subagent transcript, deduped by message id, counted like tools/mission_spend.py.
function agentTokens(file) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) { return null; }
  const seen = new Set();
  let total = 0;
  for (const line of text.split('\n')) {
    if (line.indexOf('"usage"') < 0) continue;
    let r;
    try { r = JSON.parse(line); } catch (e) { continue; }
    const m = (r && r.message) || {};
    const u = m.usage;
    if (!u || m.model === '<synthetic>') continue;
    const id = m.id || r.uuid;
    if (seen.has(id)) continue;
    seen.add(id);
    for (const k of USAGE_KEYS) total += Number(u[k]) || 0;
  }
  return total;
}

// Used tokens of the session transcript (deduped, counted like agentTokens), its LAST call's context, and the part
// dated after `afterMs`. A row without a readable timestamp counts in `total` (the session's own count) but never in
// `after`, which is added on top of a floor that may already contain it.
function sessionUsage(file, afterMs) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) { return null; }
  const seen = new Set();
  let total = 0;
  let last = 0;
  let after = 0;
  for (const line of text.split('\n')) {
    if (line.indexOf('"usage"') < 0) continue;
    let r;
    try { r = JSON.parse(line); } catch (e) { continue; }
    const m = (r && r.message) || {};
    const u = m.usage;
    if (!u || m.model === '<synthetic>') continue;
    const id = m.id || r.uuid;
    if (seen.has(id)) continue;
    seen.add(id);
    let n = 0;
    for (const k of USAGE_KEYS) n += Number(u[k]) || 0;
    total += n;
    last = n;
    const t = Date.parse(r.timestamp || '');
    if (Number.isFinite(t) && t > afterMs) after += n;   // undated rows stay in `total` only (no double count)
  }
  return { total, last, after };
}

// The session's subagent transcripts (<transcript dir>/subagents/agent-*.jsonl): the sweep's meter counts them, so the
// gate does too (S13 2026-11-05: they were invisible here). -> {total, after}
function subagentUsage(transcriptPath, afterMs) {
  const dir = path.join(String(transcriptPath).replace(/\.jsonl$/, ''), 'subagents');
  let names;
  try { names = fs.readdirSync(dir); } catch (e) { return { total: 0, after: 0 }; }
  let total = 0;
  let after = 0;
  for (const n of names) {
    if (!/^agent-.*\.jsonl$/.test(n)) continue;
    const u = sessionUsage(path.join(dir, n), afterMs);
    if (u) { total += u.total; after += u.after; }
  }
  return { total, after };
}

// The freshest measured mission spend the supervisor recorded: cost_mark or spend_stamp, each {tokens, at (s)}.
function spendFloor(record) {
  let best = null;
  for (const f of [record.cost_mark, record.spend_stamp]) {
    if (!f || !positive(f.tokens) || !positive(f.at)) continue;
    if (!best || Number(f.at) > Number(best.at)) best = { tokens: Number(f.tokens), at: Number(f.at) };
  }
  return best;
}

// Same rule as tools/mission_spend.py closeout_reserve: closeout_tokens, else min(1M, authority / 20).
function closeoutReserve(record, auth) {
  if (record.closeout_tokens !== undefined && record.closeout_tokens !== null) {
    return Math.max(0, Math.floor(Number(record.closeout_tokens) || 0));
  }
  return auth ? Math.min(1000000, Math.floor(auth / 20)) : 0;
}

// Hard cap of the mission in processed tokens: the tightest of authority minus the closeout reserve (the line the
// breaker trips at), estimate x trip ratio, phase lease hard line.
function hardCap(record) {
  const caps = [];
  const auth = positive(record.authority_tokens);
  if (auth) caps.push({ cap: auth - closeoutReserve(record, auth), what: 'authority minus closeout reserve' });
  const est = positive(record.token_estimate);
  // Same rule as mission_spend.judge: with Owner authority declared, an AUTO envelope over its ratio is a stale
  // forecast the supervisor recompiles, never a trip (m-99fe8fd825d8 S14: denied every call at 30.4M of 60M).
  const autoUnderAuthority = auth && record.token_estimate_src === 'auto';
  if (est && !autoUnderAuthority) caps.push({ cap: Math.floor((positive(record.token_trip_ratio) || 2) * est), what: 'estimate x trip ratio' });
  const l = record.phase_lease;
  if (l && positive(l.forecast) && positive(l.hard)) {
    caps.push({ cap: (Number(l.base) || 0) + Math.floor(l.forecast * l.hard), what: `phase ${l.phase} hard line` });
  }
  caps.sort((a, b) => a.cap - b.cap);
  return caps[0] || null;
}

function subagentTranscript(event, agentId) {
  const tp = event.transcript_path;
  if (!tp || !agentId || !SID_RE.test(agentId.replace(/^agent-/, ''))) return null;
  return path.join(tp.replace(/\.jsonl$/, ''), 'subagents', `agent-${agentId.replace(/^agent-/, '')}.jsonl`);
}

// Count this call against the subagent's key and persist. Per-process temp name: parallel calls run concurrently.
function bump(sid, key) {
  const file = path.join(stateDir(), `mission-subagents-${sid}.json`);
  const st = readJson(file) || { calls: {} };
  if (!st.calls || typeof st.calls !== 'object') st.calls = {};
  st.calls[key] = (Number(st.calls[key]) || 0) + 1;
  const tmp = `${file}.${process.pid}.tmp`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(st));
    fs.renameSync(tmp, file);
  } catch (e) {
    try { fs.unlinkSync(tmp); } catch (_) { /* nothing to clean */ }
  }
  return st.calls[key];
}

function touchesRecord(event) {
  const ti = event.tool_input || {};
  const text = `${ti.command || ''} ${ti.file_path || ''} ${ti.path || ''} ${ti.notebook_path || ''}`;
  if (RECORD_NAME.test(text)) return 'names the mission record or a worker marker';
  if (MUTATING_VERB.test(text)) return 'runs a state-changing gsd_mission.py verb';
  return null;
}

// The worker's mission record, found through its marker. -> {sid, mid, record} | null
function workerRecord(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const markerDir = process.env.GSD_AUTORUN_MARKER_DIR || stateDir();
  const w = readJson(path.join(markerDir, `mission-worker-${sid}.json`));
  if (!w || !MID_RE.test(String(w.mission_id || ''))) return null;
  const record = readJson(path.join(stateDir(), `gsd-mission-${w.mission_id}.json`));
  return record ? { sid, mid: w.mission_id, record } : null;
}

// Denial 1 alone, with no side effect (no counter is bumped): safe to run from a second registration.
// -> {deny, mission, kind} | null
// spec mission-closeout-reserve-launch: the ONE session the sweep launched on the closeout reserve, while its lease is
// live (CLOSEOUT_LAUNCHED, this record's owner, this epoch). Every other session of a held mission stays denied.
function closeoutLease(record, sid) {
  const l = record && record.closeout_lease;
  if (!l || l.state !== 'CLOSEOUT_LAUNCHED' || !positive(l.tokens)) return null;
  const o = record.owner || {};
  if (!sid || o.session_id !== sid || Number(l.epoch) !== Number(record.epoch)) return null;
  return l;
}

function holdDecision(event, found) {
  const f = found || workerRecord(event);
  const hold = f && f.record.owner_hold;
  if (!isCostHold(hold)) return null;
  if (closeoutLease(f.record, f.sid)) return null;   // admitted; exposureDecision caps it at the lease
  return {
    mission: f.mid, kind: 'cost_hold',
    deny: `MISSION COST HOLD -- ${f.mid} is held (${String(hold.reason || 'cost breaker').slice(0, 240)}). ` +
      'No further tool calls are admitted for this worker or its subagents. End this turn with a status and ' +
      'the next exact action; the Owner releases the hold or approves a reforecast.',
  };
}

// Denial 4 alone (next-call exposure), side-effect free like holdDecision, so the standalone hold gate can run it on
// a host with no dispatcher lane (GEX44, 2026-11-06: the S13 overshoot ran with only the sweep enforcing). -> |null
function exposureDecision(event, found) {
  const f = found || workerRecord(event);
  if (!f) return null;
  const { mid, record } = f;
  const lease = closeoutLease(record, f.sid);
  if (lease) {
    // The closeout session is fresh: its own usage (main + subagents) against the lease, not the mission's line.
    const lu = event.transcript_path ? sessionUsage(event.transcript_path, 0) : null;
    if (!lu) return null;
    const ls = subagentUsage(event.transcript_path, 0);
    const lused = lu.total + ls.total;
    if (lused + lu.last <= Number(lease.tokens)) return null;
    return { mission: mid, kind: 'closeout_lease',
      deny: `CLOSEOUT LEASE -- ${mid}'s closeout session has processed ${fmt(lused)} tokens and the next call costs about ` +
        `${fmt(lu.last)}; that passes its closeout lease of ${fmt(lease.tokens)}. Commit what is written, declare the ` +
        'checkpoint if you can, and end the turn.' };
  }
  const cap = hardCap(record);
  if (!cap || !event.transcript_path) return null;
  const floor = spendFloor(record);
  const afterMs = floor ? floor.at * 1000 : 0;
  const u = sessionUsage(event.transcript_path, afterMs);
  if (!u) return null;
  const s = subagentUsage(event.transcript_path, afterMs);
  const own = u.total + s.total + (Number(record.spend_carried) || 0);
  const used = floor ? Math.max(own, floor.tokens + u.after + s.after) : own;
  if (used + u.last <= cap.cap) return null;
  return { mission: mid, kind: 'next_call_exposure',
    deny: `MISSION CAP -- ${mid} has processed at least ${fmt(used)} tokens and the next call costs about ${fmt(u.last)} ` +
      `(context of the last call); that passes the ${cap.what} hard cap ${fmt(cap.cap)}. End this turn with a status and ` +
      'the next exact action; only the Owner or the supervisor reforecasts.' };
}

// -> {deny: string|null, mission?, kind?}
function decide(event) {
  const found = workerRecord(event);
  if (!found) return { deny: null };
  const { sid, mid, record } = found;
  const held = holdDecision(event, found);
  if (held) return held;
  if (WRITERS.test(String(event.tool_name || ''))) {
    const why = touchesRecord(event);
    if (why) {
      return {
        mission: mid, kind: 'lease_write',
        deny: `MISSION AUTHORITY -- this call ${why} of ${mid}. A worker may request a reforecast but never grants itself ` +
          'authority: the envelope, phase lease and holds change only through the supervisor or the Owner.',
      };
    }
  }
  // 4. NEXT-CALL EXPOSURE (Env 0): used + the last call's context would pass the hard cap -> refuse, so a
  //    mission overshoots by at most one call. `used` = this session's transcript + record.spend_carried (spend of
  //    earlier sessions, when the supervisor recorded it): a lower bound of mission spend, so a deny is positive evidence.
  //    2026-11-06 (spec mission-gate-carried-spend, S13 overshoot 33.4M on 30M): `used` also counts this session's
  //    subagents and the supervisor's measured floor (cost_mark / spend_stamp) plus everything dated after it, so a
  //    later epoch's worker sees what earlier epochs spent.
  const exposed = exposureDecision(event, found);
  if (exposed) return exposed;
  const agentId = event.agent_id ? String(event.agent_id) : '';
  const agentType = event.agent_type ? String(event.agent_type) : '';
  const key = agentId || (agentType ? `type:${agentType}` : '');
  if (key && AGENT_RE.test(key)) {
    const cap = capFor(record, agentType);
    const calls = bump(sid, key);
    if (calls > cap.calls) {
      return { mission: mid, kind: 'subagent_calls',
        deny: `SUBAGENT CAP -- ${agentType || key} reached ${cap.calls} calls (this is call ${calls}). Stop and return what you ` +
          'have to the main thread; the main thread decides what is worth another agent.' };
    }
    const file = subagentTranscript(event, agentId);
    const spent = file ? agentTokens(file) : null;
    if (spent !== null && spent >= cap.tokens) {
      return { mission: mid, kind: 'subagent_tokens',
        deny: `SUBAGENT CAP -- ${agentType || key} has processed ${fmt(spent)} tokens, cap ${fmt(cap.tokens)}. Stop and ` +
          'return what you have to the main thread.' };
    }
  }
  return { deny: null, mission: mid };
}

// -> hook output object or null (never throws).
function run(ev) {
  try {
    if (off()) return null;
    const r = decide(ev || {});
    if (r.deny) return { hookSpecificOutput: { hookEventName: 'PreToolUse',
      permissionDecision: 'deny', permissionDecisionReason: r.deny } };
  } catch (e) { /* fail open */ }
  return null;
}

module.exports = { run, decide, holdDecision, exposureDecision, off, capFor, agentTokens, sessionUsage, hardCap, DEFAULT_CAP };
