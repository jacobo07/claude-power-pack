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
const crypto = require('crypto');
const os = require('os');
const { spawn } = require('child_process');
const gb = require('./lib/goal_binding');

// --- Owner capital capture + approval receipt (merged from owner_capital_capture.js, econ-succession S2) ----
// Capture: an Owner capital approval ("approve", "approve p80", "modify dgl to 37M", "revoke dgl") is recorded
// {session_id, transcript_path, prompt, ts} and `mission_spend.py capital-apply-pending` starts detached. The apply
// leg re-verifies the Owner entry itself; the capture row is a trigger, not an authority. Kill switch
// CPP_OCA_CAPTURE=off. Test seam: CPP_OCA_NO_SPAWN=1 skips the spawn, CPP_CAPITAL_ROOT moves the store.
// Receipt: the same message, in an interactive pane that displayed exactly one pending packet for the bound
// goal, becomes an immutable OWNER_APPROVED receipt BEFORE the model (the python leg decides; this hook only
// relays) and the message is answered with 0 model tokens. Kill switch CPP_ECON_APPROVE=off.
const GOAL = '[a-z0-9][a-z0-9._-]*';
const NEG = /(?:\b(?:don't|dont|do not|not|never|can't|cannot|no)\b|n't\b)/;
const GRAMMAR = [
  /^(?:yes[, ]+)?approve(?:d)?(?: everything| all)?$/,
  /^approve (?:all )?p(?:50|80|95)$/,
  new RegExp(`^approve ${GOAL} only$`),
  new RegExp(`^modify ${GOAL} to [0-9][0-9,_.]*[mk]?$`),
  new RegExp(`^revoke ${GOAL}$`),
];
const APPROVE_GRAMMAR = GRAMMAR.slice(0, 4);   // approve forms + modify; never revoke
const MISSION_SPEND = path.join(__dirname, '..', 'tools', 'mission_spend.py');

function normIntent(text) {
  return String(text).trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!]+$/, '');
}
function isCapitalIntent(text) {
  if (typeof text !== 'string') return false;
  const t = normIntent(text);
  if (!t || NEG.test(t)) return false;
  return GRAMMAR.some((g) => g.test(t));
}
function isApproveIntent(text) {
  if (typeof text !== 'string') return false;
  const t = normIntent(text);
  return !!t && !NEG.test(t) && APPROVE_GRAMMAR.some((g) => g.test(t));
}

function capitalRoot() {
  return process.env.CPP_CAPITAL_ROOT || path.join(os.homedir(), '.claude', 'state', 'capital-authority');
}

// (sha, goal) pairs in pending.json with no capsule row yet. A capsule row of any state is final for the sweep.
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
// still outstanding. Neither row is authority.
function capture(ev) {
  if (!ev || typeof ev.prompt !== 'string') return;
  const root = capitalRoot();
  const intent = isCapitalIntent(ev.prompt);
  if (!intent && (!ev.transcript_path || outstanding(root).length === 0)) return;
  fs.mkdirSync(root, { recursive: true });
  fs.appendFileSync(path.join(root, 'approvals.jsonl'), JSON.stringify({
    session_id: ev.session_id || null, transcript_path: ev.transcript_path || null,
    prompt: intent ? ev.prompt : null, kind: intent ? 'approval' : 'pending-sweep', ts: new Date().toISOString(),
  }) + '\n');
  if (process.env.CPP_OCA_NO_SPAWN === '1') return;
  const py = process.env.CLAUDE_PY_EXE || 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
  const child = spawn(py, ['-I', MISSION_SPEND, 'capital-apply-pending'], {
    detached: true, stdio: 'ignore', windowsHide: true, env: process.env,
  });
  child.on('error', () => {});
  child.unref();
}

// The receipt leg. Returns the block text, or null to let the message through to the model (every refusal:
// not an approval, no binding, not an interactive pane, zero or several displayed packets, packet invalid).
function approveReceipt(event, rec) {
  const sw = String(process.env.CPP_ECON_APPROVE || '').trim().toLowerCase();
  if (sw === '0' || sw === 'off' || sw === 'false') return null;
  if (!event.transcript_path || !rec || !rec.goal || rec.goal === 'none' || !isApproveIntent(event.prompt)) return null;
  const r = spawnSync(PY, ['-I', MISSION_SPEND, 'capital-receipt', '--session', event.session_id,
    '--transcript', event.transcript_path, '--goal', rec.goal, '--prompt', event.prompt],
  { encoding: 'utf8', timeout: 15000, windowsHide: true, env: process.env });
  let out = null;
  try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch (e) { out = null; }
  if (!out || !out.ok || !out.receipt) return null;
  const x = out.receipt;
  if (!process.env.CPP_OCA_NO_SPAWN) {
    try {
      const child = spawn(PY, ['-I', MISSION_SPEND, 'capital-apply-pending'],
        { detached: true, stdio: 'ignore', windowsHide: true, env: process.env });
      child.on('error', () => {}); child.unref();
    } catch (e) { /* the sweep on the next message applies it */ }
  }
  return `OWNER APPROVAL RECORDED -- receipt ${x.id}: state OWNER_APPROVED (answered by the control plane; 0 model tokens)\n` +
    `goal ${x.goal}: programme ceiling ${fmt(x.ceiling)} (${x.tier}) for packet ${String(x.sha).slice(0, 12)}; ` +
    `provenance ${x.provenance}; ${out.issued ? 'issued now' : 'already issued (idempotent)'}.\n` +
    'It applies below the model next; `econ status` shows the result. Nothing else is needed from you.';
}

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

  const receipt = approveReceipt(event, rec);
  if (receipt) return receipt;

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

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    // The receipt (inside decide) is written before the capture spawn, so the detached apply leg finds it.
    // A prompt this hook blocks is still captured. Capture never touches stdout; every leg is fail-open.
    let ev = null, reason = null;
    try { ev = JSON.parse(raw.replace(/^﻿/, '')); } catch (e) { ev = null; }
    try { reason = decide(ev); } catch (e) { reason = null; }
    if (process.env.CPP_OCA_CAPTURE !== 'off') {
      try { capture(ev); } catch (e) { /* fail-open: a capture failure must never cost the prompt */ }
    }
    if (reason) block(reason);
    else process.stdout.write('{}');
  });
}

module.exports = { decide, ledgerView, render, isCapitalIntent, isApproveIntent, outstanding, capture };
