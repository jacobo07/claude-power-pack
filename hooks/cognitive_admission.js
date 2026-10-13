// cognitive_admission.js -- model-call admission firewall at the Agent|Task spawn edge (CDC C3).
//
// PreToolUse on Agent|Task (chain PreToolUse-Agent-default). A material cognitive spawn must come out of
// this path with a capability row (<state>/cognitive-admission.jsonl, written by
// tools/cognitive_admission.py -- the one writer, shared with gsd_mission.admit_route).
// Denies only on positive evidence, for a session with a bound unit or goal:
//   NO_WORK    the bound unit's claim is PROVEN at an unchanged dependency fingerprint (work_proof.py twin)
//   EFFECT     the bound unit's effect is ZERO_COGNITION/DETERMINISTIC and its route has no deopt (C2)
//   LEASE      the session's goal lease is exhausted or the session is tombstoned (goal_binding)
//   DUPLICATE  same normalised prompt hash already admitted in this session within the TTL ("subscribe")
// Unbound interactive session: allow + log. Kill switch CPP_COG_ADMISSION=off. Own error -> allow (fail open).
// Host limit: only the spawn edge is interceptable; the main model turn is not.
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawn } = require('child_process');
const gb = require('./lib/goal_binding');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const PY = process.env.PYTHON_BIN || (process.platform === 'win32'
  ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3');
const WRITER = path.join(__dirname, '..', 'tools', 'cognitive_admission.py');
const DUP_TTL_MS = Number(process.env.CPP_COG_DUP_TTL_S || 120) * 1000;
const NO_MODEL = new Set(['ZERO_COGNITION', 'DETERMINISTIC']);
const ALIASES = { satisfied: 'ZERO_COGNITION', sleeping: 'ZERO_COGNITION', deterministic: 'DETERMINISTIC',
  known_transform: 'BOUNDED_COGNITION', bounded_coding: 'BOUNDED_COGNITION', novel: 'NOVEL_COGNITION',
  owner_reality: 'OWNER_COGNITION' };
const ENUM = new Set(['ZERO_COGNITION', 'DETERMINISTIC', 'BOUNDED_COGNITION', 'NOVEL_COGNITION', 'OWNER_COGNITION']);

function phash(text) {
  return crypto.createHash('sha256').update(String(text || '').split(/\s+/).filter(Boolean).join(' ').toLowerCase())
    .digest('hex').slice(0, 16);
}

function normEffect(raw) {
  if (raw == null) return 'BOUNDED_COGNITION';           // absent effect = BOUNDED (C2)
  return ENUM.has(raw) ? raw : (ALIASES[raw] || null);
}

// Twin of tools/work_proof.py fingerprint()/check(): PROVEN at the identical dependency fingerprint.
function noWork(proof, root) {
  if (!proof || !proof.claim || !Array.isArray(proof.deps) || !proof.deps.length || !root) return null;
  const h = crypto.createHash('sha256');
  for (const d of Array.from(new Set(proof.deps)).sort()) {
    if (typeof d !== 'string' || !d) return null;
    let b;
    try { b = fs.readFileSync(path.join(root, d)); } catch (e) { return null; }
    h.update(Buffer.concat([Buffer.from(d + '\0' + crypto.createHash('sha256').update(b).digest('hex') + '\n')]));
  }
  const led = gb.readJson(path.join(root, 'vault', 'config', 'claim-proofs.json'));
  const rec = led && led.claims && led.claims[proof.claim];
  const fp = h.digest('hex');
  return rec && rec.status === 'PROVEN' && rec.fingerprint === fp ? `claim ${proof.claim} PROVEN at unchanged fingerprint ${fp.slice(0, 12)}` : null;
}

function unitFor(sid) {
  const b = gb.readJson(path.join(gb.stateDir(), 'cognitive-unit', `${sid}.json`));
  if (b && b.route) return b;
  if (process.env.CPP_COG_ROUTE) return { unit: process.env.CPP_COG_UNIT || 'env', route: process.env.CPP_COG_ROUTE, root: process.env.CPP_COG_ROOT || '' };
  return null;
}

function dupSeen(sid, h, now) {
  const p = path.join(gb.stateDir(), 'cognitive-inflight', `${sid}.json`);
  const m = gb.readJson(p) || {};
  const live = {};
  for (const [k, t] of Object.entries(m)) if (now - t < DUP_TTL_MS) live[k] = t;
  const dup = Object.prototype.hasOwnProperty.call(live, h);
  if (!dup) {
    live[h] = now;
    try { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, JSON.stringify(live)); } catch (e) { /* fail open */ }
  }
  return dup;
}

function log(sid, unit, effect, decision, reason, h) {
  try {
    const c = spawn(PY, [WRITER, 'record', sid || '-', unit || 'unbound', effect || 'UNKNOWN', decision, reason, h || '-', 'agent'],
      { detached: true, stdio: 'ignore', windowsHide: true, env: process.env });
    c.unref();
  } catch (e) { /* the writer must never stop a spawn */ }
}

// -> {deny: reason|null, unit, effect, reason, h}
function decide(event, now) {
  const sid = event && event.session_id;
  const input = (event && event.tool_input) || {};
  const h = phash(input.prompt || input.description || '');
  // C10 canary defect: wired on '*' every Read/Grep hashed the empty prompt and was denied as DUPLICATE.
  // Only spawn tools carry a prompt; any other tool, or an empty prompt, is not admission's business.
  const tn = event && event.tool_name;
  if (tn && !/^(Agent|Task)$/.test(tn)) return { deny: null, unit: 'unbound', effect: 'UNKNOWN', reason: 'not a spawn tool', h };
  if (!(input.prompt || input.description)) return { deny: null, unit: 'unbound', effect: 'UNKNOWN', reason: 'empty prompt', h };
  if (!sid || !SID_RE.test(sid)) return { deny: null, unit: 'unbound', effect: 'UNKNOWN', reason: 'no session id', h };
  const bu = unitFor(sid);
  let unit = bu ? bu.unit || 'bound' : 'unbound', effect = 'UNKNOWN';
  if (bu) {
    const route = gb.readJson(bu.route);
    if (route) {
      effect = normEffect(route.effect) || 'UNKNOWN';
      const w = noWork(route.proof, bu.root);
      if (w) return { deny: `NO_WORK -- ${w}. No model call is needed for unit ${unit}; read the proof instead of spawning.`, unit, effect, reason: `NO_WORK ${w}`, h };
      if (NO_MODEL.has(effect) && !(Array.isArray(route.deopt) && route.deopt.length))
        return { deny: `EFFECT -- unit ${unit} is ${effect} and declares no deopt: a model spawn is not admissible. Add a deopt assumption to the route or run the deterministic path.`, unit, effect, reason: `EFFECT ${effect} without deopt`, h };
    }
  }
  const bind = gb.goalBinding(event, sid, { observe: true });
  if (bind && bind.goal) {
    if (bind.quarantine || gb.goalExhausted(bind.goal) || gb.sidTombstoned(bind.goal, sid))
      return { deny: `LEASE -- goal ${bind.goal} lease is closed/exhausted for this session; no new model spawn is admitted.`, unit, effect, reason: `LEASE ${bind.goal} closed`, h };
  }
  if (dupSeen(sid, h, now))
    return { deny: `DUPLICATE -- an identical subagent prompt (${h}) was admitted in this session within ${DUP_TTL_MS / 1000}s. Subscribe to its result instead of spawning again.`, unit, effect, reason: `DUPLICATE ${h}`, h };
  return { deny: null, unit, effect, reason: bu ? 'admitted: bound unit' : 'unbound interactive: log only', h };
}

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    try {
      const sw = String(process.env.CPP_COG_ADMISSION || '').trim().toLowerCase();
      if (sw === '0' || sw === 'off' || sw === 'false') { process.stdout.write('{}'); return; }
      const ev = JSON.parse(raw.replace(/^\uFEFF/, ''));
      const r = decide(ev, Date.now());
      log(ev.session_id, r.unit, r.effect, r.deny ? 'deny' : 'allow', r.reason, r.h);
      if (r.deny) {
        process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PreToolUse',
          permissionDecision: 'deny', permissionDecisionReason: `COGNITIVE ADMISSION -- ${r.deny}` } }));
        return;
      }
    } catch (e) { /* fail open */ }
    process.stdout.write('{}');
  });
}

// Dispatcher contract (PreToolUse-Agent-default chain calls mod.run(data)); same verdict as the CLI path.
function run(ev) {
  try {
    const sw = String(process.env.CPP_COG_ADMISSION || '').trim().toLowerCase();
    if (sw === '0' || sw === 'off' || sw === 'false') return null;
    const r = decide(ev || {}, Date.now());
    log(ev && ev.session_id, r.unit, r.effect, r.deny ? 'deny' : 'allow', r.reason, r.h);
    if (r.deny) return { hookSpecificOutput: { hookEventName: 'PreToolUse',
      permissionDecision: 'deny', permissionDecisionReason: `COGNITIVE ADMISSION -- ${r.deny}` } };
  } catch (e) { /* fail open */ }
  return null;
}

module.exports = { run, decide, phash, normEffect, noWork };
