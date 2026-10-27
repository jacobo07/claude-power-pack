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
// Owner raise: WHOLE message only (`subelo 70M`, `sube 1.5M`, `econ raise 800k`), accents ignored. The same words
// inside a sentence are ordinary prose and reach the model. Amount 1..RAISE_MAX tokens; no comma decimals ("1,5M"
// would read as 15M), so anything ambiguous is not the verb.
// Optional trailing goal name addresses a goal from ANY pane (`subelo 70M ccr`). Amount ceiling is an arithmetic
// guard only (Owner 2026-10-20: "debo poder subirlo la cantidad que quiera"), mirrored in tools/econ_plane.py.
const RAISE = /^(?:econ\s+)?(?:sube(?:lo)?|raise)\s+(\d+(?:\.\d+)?)\s*([mk])?(?:\s+([a-z0-9][a-z0-9._-]*))?\s*[.!]?$/;
const RAISE_MAX = 1e12;

function fmt(n) { return Number(n || 0).toLocaleString('en-US'); }

// null = not the verb; {error} = the verb with an unusable amount; {amount, goal?} = tokens.
function parseRaise(prompt) {
  const t = String(prompt || '').normalize('NFD').replace(/\p{M}/gu, '').trim().toLowerCase().replace(/\s+/g, ' ');
  const m = t.match(RAISE);
  if (!m) return null;
  const amount = Math.round(parseFloat(m[1]) * (m[2] === 'm' ? 1e6 : m[2] === 'k' ? 1e3 : 1));
  if (!(amount >= 1 && amount <= RAISE_MAX)) return { error: `amount ${fmt(amount)} is outside 1..${fmt(RAISE_MAX)} tokens` };
  return m[3] ? { amount, goal: m[3] } : { amount };
}

function goalIndex() {
  const ix = gb.readJson(path.join(gb.stateDir(), 'goal-budget', 'index.json'));
  return ix && typeof ix === 'object' ? ix : {};
}

// Goals worth naming to the Owner: the most recently written ledgers, scratch/canary goals left out.
function goalHints(limit) {
  const ix = goalIndex();
  const rows = [];
  for (const g of Object.keys(ix)) {
    if (/^canary-/.test(g)) continue;
    let mt = 0;
    try { mt = fs.statSync(path.join(gb.stateDir(), 'goal-budget', g, 'spend.journal.jsonl')).mtimeMs; } catch (e) { /* no ledger yet */ }
    rows.push([g, mt]);
  }
  return rows.sort((a, b) => b[1] - a[1]).slice(0, limit).map(r => r[0]);
}

function raiseUsage(why) {
  const hints = goalHints(8);
  return `OWNER RAISE NOT APPLIED -- ${why} Nothing was changed (0 model tokens).\n` +
    'Name the goal from any pane: `subelo 70M <goal>`' + (hints.length ? `  (recent goals: ${hints.join(', ')})` : '') + '.';
}

// Goal-addressed raise: programme += N and a successor lease, no pane unfenced (tools/econ_plane.py raise_goal).
// Answered here with zero model tokens; blocked panes of that goal pick the successor up on /clear.
function doRaiseGoal(goal, raise, why) {
  const ix = goalIndex();
  const key = Object.keys(ix).find(g => g.toLowerCase() === String(goal).toLowerCase());
  if (!key) return raiseUsage(`goal "${goal}" is not declared on this host.`);
  const r = spawnSync(PY, [ECON_PLANE, 'raise', '--goal', key, '--amount', String(raise.amount)],
    { encoding: 'utf8', timeout: 9000, windowsHide: true });
  let out = null;
  try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch (e) { out = null; }
  if (!out) return `OWNER RAISE FAILED -- the ledger leg could not run (${r.error ? (r.error.code || r.error.message) : 'exit ' + r.status}). ` +
    'Nothing is assumed written; send the same message again (the raise is idempotent per goal and lease).';
  if (!out.ok) return `OWNER RAISE REFUSED -- ${out.reason}. Goal ${key} is unchanged (0 model tokens).`;
  if (!out.applied) return `OWNER RAISE -- goal ${key}: lease ${out.lease} is already open from this same raise; nothing added (0 model tokens).`;
  return `DONE, NOT AN ERROR -- the harness label "operation blocked by hook" only means this message was answered without a model call. ` +
    `OWNER RAISE APPLIED (${why}; 0 model tokens). Goal ${key}: programme ${fmt(out.programme_old)} -> ${fmt(out.programme_new)} ` +
    `(+${fmt(raise.amount)}); lease ${out.from_lease} -> ${out.lease}, cap ${fmt(out.cap_old)} -> ${fmt(out.cap_new)}.\n` +
    'A pane already fenced on this goal stays fenced: `/clear` there starts a fresh session on the new lease. Panes that were never fenced just keep working.';
}

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
    else if (r.op === 'untomb') delete tombs[r.sid];
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
  L.push('Verbs (type as a message): `econ status`, `econ detach`, `subelo 70M` (adds 70M to this pane\'s goal and opens a successor lease; then /kclear + /kresume), `subelo 70M <goal>` (same for any named goal, from any pane; no size limit).  `/clear` = fresh session in this pane.');
  return L.join('\n');
}

// Owner raise, executed here (model-free) from the harness-supplied prompt. Effect and invariants:
// vault/specs/econ-owner-raise.md. The blocked pane stays fenced; a successor lease opens and a fresh session binds to it.
function doRaise(sid, rec, v, raise, tomb, short) {
  const s8 = sid.slice(0, 8);
  if (raise.error) return `OWNER RAISE REFUSED -- ${raise.error}. Nothing was changed (0 model tokens).`;
  if (!(tomb || v.exhausted || short))
    return `OWNER RAISE -- session ${s8} is not blocked (goal ${rec.goal} still holds a call); nothing raised (0 model tokens).`;
  const args = [ECON_PLANE, 'raise', '--session', sid, '--amount', String(raise.amount)];
  if (!tomb && !v.exhausted) args.push('--short');
  const r = spawnSync(PY, args, { encoding: 'utf8', timeout: 9000, windowsHide: true });
  let out = null;
  try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch (e) { out = null; }
  if (!out) return `OWNER RAISE FAILED -- the ledger leg could not run (${r.error ? (r.error.code || r.error.message) : 'exit ' + r.status}). ` +
    'Nothing is assumed written; send the same message again (the raise is idempotent per session and lease).';
  if (!out.ok) return `OWNER RAISE REFUSED -- ${out.reason}. Goal ${rec.goal} is unchanged (0 model tokens).`;
  if (!out.applied) return `OWNER RAISE -- ${out.reason} (0 model tokens).`;
  // Applied: do NOT block. The message passes to the model with this context, and the model runs the existing
  // rollover (/kclear seals; context-watchdog's self-sealed step types /clear; rollover_autotype types /kresume).
  const what = out.resumed
    ? `The Owner's earlier raise had already opened lease ${out.lease} (cap ${fmt(out.cap_new)}); this pane's fence is now lifted.`
    : `Goal ${out.goal}: programme ${fmt(out.programme_old)} -> ${fmt(out.programme_new)} (+${fmt(raise.amount)}); ` +
      `lease ${out.from_lease} -> ${out.lease}, cap ${fmt(out.cap_old)} -> ${fmt(out.cap_new)}. This pane's fence is lifted.`;
  return { context: `OWNER RAISE APPLIED by the econ hook (0 model tokens). ${what} ` +
    'The Owner wants the context rollover to start now, automatically: run the /kclear skill immediately (Skill tool, skill "kclear") ' +
    'to seal the capsule, do no other work first, and do not ask for confirmation. The watchdog then types /clear and /kresume follows in the fresh session.' };
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

  const raise = parseRaise(prompt);
  if (raise && raise.error) return `OWNER RAISE REFUSED -- ${raise.error}. Nothing was changed (0 model tokens).`;
  if (raise && raise.goal) return doRaiseGoal(raise.goal, raise, 'named goal');
  if (raise && (!rec || rec.goal === 'none')) {
    // No binding record: the goal this pane would bind to by cwd (observe-only, nothing is written) is the one it
    // is working on. Same resolver as the PreToolUse guard, so a pane quarantined on an exhausted goal finds it.
    let pb = null;
    try { pb = gb.goalBinding(event, sid, { observe: true }); } catch (e) { pb = null; }
    if (pb && pb.goal) return doRaiseGoal(pb.goal, raise, `pane cwd is under goal ${pb.goal}`);
    return raiseUsage(`session ${sid.slice(0, 8)} is not bound to a goal and its directory is under no goal root.`);
  }
  if (!rec || rec.goal === 'none') {
    if (verb || raise) return render(sid, rec, null, rec ? 'DETACHED' : 'NEUTRAL',
      rec ? `fenced workspaces: ${(rec.fenced || []).join(', ') || 'none'}` : 'no goal pays for this session.');
    return null;
  }
  const v = ledgerView(rec.goal);
  if (!v || v.cap == null) return (verb || raise) ? render(sid, rec, null, 'UNKNOWN', `goal ${rec.goal} has no readable ledger; unknown is never admitted.`) : null;
  const tomb = !!v.tombs[sid];
  const nxt = nextRequest(sid);
  const short = nxt > 0 && v.cap - v.settled < nxt;
  if (raise) return doRaise(sid, rec, v, raise, tomb, short);
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
    // Owner capital capture rides this registered UserPromptSubmit hook (no settings.json edit): it runs
    // first, so a prompt this hook then blocks is still captured. Spawns detached; never touches stdout.
    if (process.env.CPP_OCA_CAPTURE !== 'off') {
      try { require('./owner_capital_capture').run(raw.replace(/^﻿/, '')); } catch (e) { /* fail-open */ }
    }
    let reason = null;
    try { reason = decide(JSON.parse(raw.replace(/^﻿/, ''))); } catch (e) { reason = null; }
    if (reason && typeof reason === 'object') {
      process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: reason.context } }));
    } else if (reason) block(reason);
    else process.stdout.write('{}');
  });
}

module.exports = { decide, ledgerView, render };
