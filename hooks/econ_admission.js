// econ_admission.js -- PRE-MODEL economic admission (UserPromptSubmit, critical lane).
//
// econ-contain WS-B, vault/plans/econ-containment-2026-10-10.md. The goal guard
// (session_budget_guard.js) is PreToolUse: by the time it refuses a tool call, the model request that
// wrote the call is already bought. On 2026-10-10 a pane bound to the exhausted ctx-same-pane goal paid
// ~200K per Owner message to be told "budget spent" (d5063bac: 345,519 -> 530,093 -> 1,089,380 settled
// after the cap). This hook runs BEFORE the model: when the session's goal is known to be spent, the
// Owner's message is blocked (decision:block, zero model tokens) and the reason IS the status, folded
// from the GoalLedger journal. PreToolUse stays as defence in depth.
//
// It is also the zero-cost egress: an Owner message `econ status` or `econ detach` is executed here,
// outside the exhausted goal's authority, and answered without a model call. /clear and /kclear are
// harness commands and never reach this hook, so a block cannot trap them.
//
// Blocks ONLY on positive evidence (a tombstone for this session, an exhausted current lease, or a
// settled total that already leaves less than the next request). Unbound or unreadable -> silent: a
// hook that cannot read the ledger must not swallow the Owner's message. Kill switch:
// CPP_ECON_ADMISSION=off.
'use strict';
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const gb = require('./lib/goal_binding');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const PY = process.env.PYTHON_BIN || (process.platform === 'win32'
  ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3');
const ECON_PLANE = path.join(__dirname, '..', 'tools', 'econ_plane.py');
const VERB = /^\s*econ\s+(status|detach)\b/i;

function fmt(n) { return Number(n || 0).toLocaleString('en-US'); }

// Display fold of the journal (same ops as GoalLedger._gfold; agent-hold shrink is not modelled, so an
// open agent hold reads at its full amount -- it errs toward "less is left", never more).
function ledgerView(goal) {
  const rows = gb.journalRows(goal, ['"op"']);
  if (!rows.length) return null;
  const marks = {}, res = {}, tombs = {};
  let cap = null, programme = null, leases = 1, leaseSettled = 0;
  const opened = new Set(), exhausted = new Set();
  for (const r of rows) {
    const cur = `L${leases}`;
    if (r.op === 'cap' && (!r.lease || r.lease === cur)) cap = Number(r.value);
    else if (r.op === 'programme') programme = Number(r.value);
    else if (r.op === 'lease_open' && !opened.has(r.succession_id)) {
      opened.add(r.succession_id); leases += 1; cap = Number(r.cap); leaseSettled = 0;
    } else if (r.op === 'reserve') res[r.id] = { sid: r.sid, amount: Number(r.amount) || 0, kind: r.kind, open: true, lease: cur };
    else if (r.op === 'settle') {
      const nv = Math.max(marks[r.sid] || 0, Number(r.measured) || 0);
      leaseSettled += nv - (marks[r.sid] || 0);
      marks[r.sid] = nv;
      for (const id of r.closes || []) if (res[id]) res[id].open = false;
    } else if (r.op === 'correct') marks[r.sid] = Number(r.measured) || 0;
    else if (r.op === 'tombstone' && !tombs[r.sid]) tombs[r.sid] = r;
    else if (r.op === 'exhausted') exhausted.add(r.lease || cur);
  }
  const lease = `L${leases}`;
  const totalSettled = Object.values(marks).reduce((s, v) => s + v, 0);
  const allOpen = Object.values(res).filter(x => x.open).reduce((s, x) => s + x.amount, 0);
  const open = Object.values(res).filter(x => x.open && x.lease === lease).reduce((s, x) => s + x.amount, 0);
  // Admission reads the CURRENT lease (as _gfold does); the programme reads the lifetime totals.
  return { cap, programme, settled: leaseSettled, open, used: leaseSettled + open, lease, leases,
    totalSettled, totalOpen: allOpen, exhausted: exhausted.has(lease), tombs, marks };
}

function nextRequest(sid) {
  const gs = gb.readJson(path.join(gb.stateDir(), `session-budget-${sid}.goal.json`));
  if (!gs) return 0;
  const last = gs.lastTotal > 0 ? gs.lastTotal : (gs.context || 0);
  return last + Math.max(0, ...(Array.isArray(gs.deltas) ? gs.deltas : []));
}

function render(sid, rec, v, state, next) {
  const L = [`ECONOMIC STATUS -- session ${sid.slice(0, 8)}: ${state}  (answered by the control plane; 0 model tokens)`];
  if (rec) L.push(`binding: goal=${rec.goal} gen=${rec.gen || 1} source=${rec.source}` +
    (Array.isArray(rec.fenced) && rec.fenced.length ? ` fenced=${rec.fenced.join(',')}` : ''));
  if (v) {
    L.push(`goal ${rec.goal}: used ${fmt(v.used)} of cap ${fmt(v.cap)} (settled ${fmt(v.settled)}, reserved ${fmt(v.open)}, lease ${v.lease})`);
    if (v.programme != null) L.push(`programme ${fmt(v.programme)}`);
    L.push('unknown in-flight: spend since this session\'s last settle is settled from its transcript on detach, never assumed zero.');
  }
  L.push(`next: ${next}`);
  L.push('Verbs (type as a message): `econ status`, `econ detach`.  `/clear` = fresh session in this pane.  The cap is never raised here.');
  return L.join('\n');
}

function block(reason) {
  process.stdout.write(JSON.stringify({ decision: 'block', reason }));
}

function decide(event) {
  const sw = String(process.env.CPP_ECON_ADMISSION || '').trim().toLowerCase();
  if (sw === '0' || sw === 'off' || sw === 'false') return null;
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const prompt = String((event && event.prompt) || '');
  const verb = (prompt.match(VERB) || [])[1];
  const rec = gb.readBinding(sid);

  if (verb && verb.toLowerCase() === 'detach') {
    const r = spawnSync(PY, [ECON_PLANE, 'detach', '--session', sid, '--reason', 'owner-econ-detach'],
      { encoding: 'utf8', timeout: 9000, windowsHide: true });
    let out = null;
    try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch (e) { out = null; }
    if (out && out.ok) {
      return out.applied
        ? `ECONOMIC DETACH -- session ${sid.slice(0, 8)} left goal ${out.from} (0 model tokens).\n` +
          `settled at ${fmt(out.measured)} measured since binding; tombstoned on ${out.from}; binding generation ${out.binding && out.binding.gen}.\n` +
          `This pane is NEUTRAL now: reads anywhere are free; changes to ${out.from}'s workspace stay fenced. Send your next message normally.`
        : `ECONOMIC DETACH -- session ${sid.slice(0, 8)} is not bound to a goal; nothing to do (0 model tokens).`;
    }
    // The ledger half failed (python slow/absent): still free the pane, and say the settle is UNKNOWN.
    const w = rec && rec.goal !== 'none' ? gb.supersedeBinding(sid, 'none', 'econ-detach-fallback', 'econ_plane unavailable') : null;
    return `ECONOMIC DETACH -- the ledger settle could not run (${r.error ? (r.error.code || r.error.message) : 'exit ' + r.status}); ` +
      (w ? `binding generation ${w.gen} written: this pane is neutral, ${w.fenced.join(',')} stays fenced. Unsettled in-flight spend is UNKNOWN, not zero; run econ_plane.py detach later to settle it.`
         : 'no binding was changed.');
  }

  if (!rec || rec.goal === 'none') {
    if (verb) return render(sid, rec, null, rec ? 'DETACHED' : 'NEUTRAL',
      rec ? `fenced workspaces: ${(rec.fenced || []).join(', ') || 'none'}` : 'no goal pays for this session.');
    return null;
  }
  const v = ledgerView(rec.goal);
  if (!v || v.cap == null) return verb ? render(sid, rec, null, 'UNKNOWN', `goal ${rec.goal} has no readable ledger; unknown is never admitted.`) : null;
  const tomb = !!v.tombs[sid];
  const nxt = nextRequest(sid);
  const short = nxt > 0 && v.cap - v.settled < nxt;
  if (!verb && !tomb && !v.exhausted && !short) return null;
  const state = tomb ? 'TOMBSTONED' : v.exhausted ? 'EXHAUSTED' : short ? 'NEXT CALL DOES NOT FIT' : 'ACTIVE';
  let next;
  if (state === 'ACTIVE') next = 'admitted: the goal still holds at least one call.';
  else if (v.programme != null && v.programme - v.totalSettled - v.totalOpen > 0)
    next = `SUCCESSOR AVAILABLE: the programme still holds ${fmt(v.programme - v.totalSettled - v.totalOpen)}; /clear starts a fresh session that binds to the successor lease. This session stays fenced.`;
  else next = `WAITING_OWNER_CAPITAL: goal ${rec.goal} is spent${short && !tomb ? ` (next request ~${fmt(nxt)} > ${fmt(v.cap - v.settled)} left)` : ''}. ` +
    'One decision: approve a successor lease, or close the goal. Nothing runs meanwhile. `econ detach` frees this pane for other work now.';
  const text = render(sid, rec, v, state, next);
  return verb ? text : `${text}\n\nYour message was NOT sent to the model: the goal paying for this session cannot afford it.`;
}

// Pre-budget Owner router (OCP Phase 3): a whole-message capital-grammar form is answered here, before the
// affordability fence and before any model call. Every failure path returns null so decide() still runs.
const OCP_ROUTER = path.join(__dirname, '..', 'tools', 'ocp_router.py');
const OCP_CANDIDATE = /\d|\b(?:keep|mantener|stop|para|cierra|revoke)\b/i;

function routeOwner(event) {
  if (String(process.env.CPP_OCP_ROUTER || '').trim().toLowerCase() === 'off') return null;
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const prompt = String((event && event.prompt) || '');
  if (prompt.length > 160 || prompt.includes('\n') || VERB.test(prompt) || !OCP_CANDIDATE.test(prompt)) return null;
  const r = spawnSync(PY, ['-I', OCP_ROUTER], { input: JSON.stringify(event), encoding: 'utf8', timeout: 9000, windowsHide: true });
  let out = null;
  try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch (e) { return null; }
  if (!out || out.outcome === 'NOT_CONTROL' || out.outcome === 'ERROR' || !out.reply) return null;
  return out.reply;
}

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    // Owner capital capture rides this registered UserPromptSubmit hook (no settings.json edit): it runs
    // first, so a prompt this hook then blocks is still captured. Spawns detached; never touches stdout.
    if (process.env.CPP_OCA_CAPTURE !== 'off') {
      try { require('./owner_capital_capture').run(raw.replace(/^﻿/, '')); } catch (e) { /* fail-open */ }
    }
    let reason = null;
    try {
      const ev = JSON.parse(raw.replace(/^﻿/, ''));
      try { reason = routeOwner(ev); } catch (e) { reason = null; }
      if (!reason) reason = decide(ev);
    } catch (e) { reason = null; }
    if (reason) block(reason);
    else process.stdout.write('{}');
  });
}

module.exports = { decide, ledgerView, render };
