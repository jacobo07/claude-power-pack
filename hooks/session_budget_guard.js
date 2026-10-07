// session_budget_guard.js -- the SESSION cost breaker, judged before every tool call (PreToolUse).
//
// tools/mission_spend.py only ever judged MISSIONS (gsd autorun). An ordinary interactive session
// had no envelope at all: the skyparty-spawn closeout (transcript b9dbdfe2, 2026-10-05) was
// estimated far below what it burned, ran 131 calls to 35.45M processed tokens with the context
// growing ~90K -> 349K, and nothing measured it until a person did.
//
// OPT-IN. Inert unless `<state>/session-budget-<sid>.json` exists (written by
// `python tools/mission_spend.py session-declare ...`). Without it the cost is one failed read.
// Unit = mission_spend's: input + cache_write + cache_read + output, deduplicated by message id,
// synthetic rows excluded. Pinned for parity by tools/test_session_budget_guard.py.
//
// Breakers (each a DENY that names its number and the way out):
//   tokens      processed > stop                              (> warn = advisory only)
//   divergence  tool calls > call_ratio x calls_estimate      (when an estimate is declared)
//   context     last turn's context > context_ceiling         -> rotate with /kclear
//   no-progress K calls with no Edit/Write/MultiEdit/NotebookEdit and no `commit` command
// Accounting that cannot be read (no transcript_path, unreadable file, corrupt budget, state that
// cannot be written) gets ONE grace call, then denies: an envelope nobody can measure is not
// silently treated as a zero spend.
//
// Never denied, so a tripped session can still rotate or lift its own envelope: a Bash/PowerShell
// command naming rollover.py, mission_spend.py or session-budget-. Kill switch:
// CPP_SESSION_BUDGET=off, or delete the budget file.
//
// Incremental: the state file keeps a byte offset; each call reads only the complete lines
// appended since. Coverage is the dispatcher's PreToolUse lanes (Bash, PowerShell, Write, Edit,
// MultiEdit, NotebookEdit, Read, Grep); Agent/WebFetch calls are COUNTED (they are in the
// transcript) but not themselves gated -- the next gated call is. In GOAL mode (below) an Agent
// call is gated before launch once the dispatcher's PreToolUse-Agent lane is registered.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const UK = ['input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'];
const PROGRESS_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
const EXEMPT_CMD = /rollover\.py|mission_spend\.py|session-budget-/;
const MAX_IDS = 20000;
const DEFAULT_CALL_RATIO = 1.5;
const DEFAULT_NOPROGRESS = 25;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

function fresh(since) {
  return { since: since || null, offset: 0, tokens: 0, calls: 0, context: 0, progress_at: 0, ids: [], grace: false };
}

// Fold the complete lines appended since st.offset into st. Mirrors mission_spend.session_tokens.
function advance(st, transcript) {
  const size = fs.statSync(transcript).size;
  if (size < st.offset) Object.assign(st, fresh(st.since), { grace: st.grace });   // truncated/rotated
  if (size === st.offset) return;
  const fd = fs.openSync(transcript, 'r');
  let buf;
  try {
    buf = Buffer.alloc(size - st.offset);
    fs.readSync(fd, buf, 0, buf.length, st.offset);
  } finally { fs.closeSync(fd); }
  const end = buf.lastIndexOf(0x0a);
  if (end < 0) return;                       // only a partial line so far
  st.offset += end + 1;
  const seen = new Set(st.ids);
  for (const line of buf.subarray(0, end).toString('utf8').split('\n')) {
    if (!line) continue;
    let r;
    try { r = JSON.parse(line); } catch (e) { continue; }
    if (!r || typeof r !== 'object') continue;
    if (st.since && String(r.timestamp || '') < st.since) continue;
    const m = r.message;
    if (!m || typeof m !== 'object') continue;
    if (r.type === 'assistant' && Array.isArray(m.content)) {
      for (const b of m.content) {
        if (!b || b.type !== 'tool_use') continue;
        st.calls += 1;
        const cmd = b.input && typeof b.input.command === 'string' ? b.input.command : '';
        if (PROGRESS_TOOLS.has(b.name) || /\bcommit\b/.test(cmd)) st.progress_at = st.calls;
      }
    }
    const u = m.usage;
    if (!u || m.model === '<synthetic>') continue;
    const mid = m.id || r.uuid;
    if (seen.has(mid)) continue;
    seen.add(mid);
    st.ids.push(mid);
    st.tokens += UK.reduce((s, k) => s + (Number(u[k]) || 0), 0);
    st.context = UK.slice(0, 3).reduce((s, k) => s + (Number(u[k]) || 0), 0);
  }
  if (st.ids.length > MAX_IDS) st.ids = st.ids.slice(-MAX_IDS);
}

function fmt(n) { return Number(n).toLocaleString('en-US'); }

function deny(reason) {
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `SESSION BUDGET BREAKER -- ${reason} Way out: end this turn with a status ` +
      'and the next exact action, then /kclear (rotate). The Owner lifts or raises the envelope with ' +
      '`python tools/mission_spend.py session-declare ...` or by deleting the session-budget file.' } };
}

function advise(text) {
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: text } };
}

function judge(budget, st) {
  if (st.tokens > budget.stop) {
    return deny(`processed ${fmt(st.tokens)} > stop ${fmt(budget.stop)} (target ${fmt(budget.target)}).`);
  }
  const est = Number(budget.calls_estimate) || 0;
  const ratio = Number(budget.call_ratio) || DEFAULT_CALL_RATIO;
  if (est > 0 && st.calls > ratio * est) {
    return deny(`${st.calls} tool calls > ${ratio} x estimate ${est}: the plan diverged; recompute the remaining work.`);
  }
  const ceil = Number(budget.context_ceiling) || 0;
  if (ceil > 0 && st.context > ceil) {
    return deny(`context ${fmt(st.context)} > ceiling ${fmt(ceil)}: every further call re-reads it.`);
  }
  const k = Number(budget.noprogress_calls) || DEFAULT_NOPROGRESS;
  if (st.calls - st.progress_at > k) {
    return deny(`${st.calls - st.progress_at} calls since the last edit or commit (limit ${k}): spend without progress.`);
  }
  if (st.tokens > budget.warn) {
    return advise(`SESSION BUDGET: processed ${fmt(st.tokens)} is past warn ${fmt(budget.warn)} ` +
      `(stop ${fmt(budget.stop)}). Finish the unit in hand; start nothing new.`);
  }
  return null;
}

// Closeout allowance. A tripped breaker denied EVERYTHING, Read included, so the pane could neither
// record its spend row nor write a handoff: measured 2026-10-06, session 1fd598fe tripped at 922K
// against stop 800K and every later call (a plain Read too) was denied. A tripped session now gets
// `closeout_calls` (default 4) calls that are read-only or write a closeout file; nothing else.
const READ_ONLY = new Set(['Read', 'Grep', 'Glob']);
const CLOSEOUT_PATH = /(^|[\\/])(vault[\\/]plans[\\/][^\\/]+\.md|memory[\\/]handoffs[\\/][^\\/]+\.md|RESUMPTION_FILE\.md)$/;
const DEFAULT_CLOSEOUT = 4;

// Goal mode passes `goal`: one handoff write, no reads. The live canary of 2026-10-07 (CANARY.md,
// 51e46273) refused at 3,005,579 against a 3M cap, then admitted 4 Reads per pane at ~100K each:
// 793K of a 1.17M overshoot. A Read does not write a handoff, it only spends.
function closeout(budget, st, event, verdict, goal = false) {
  const d = verdict && verdict.hookSpecificOutput;
  if (!d || d.permissionDecision !== 'deny') return verdict;
  const declared = Number(budget.closeout_calls);
  const limit = goal ? 1 : (Number.isFinite(declared) && declared >= 0 ? declared : DEFAULT_CLOSEOUT);
  const tool = String(event.tool_name || '');
  const fp = event.tool_input && typeof event.tool_input.file_path === 'string' ? event.tool_input.file_path : '';
  const eligible = (!goal && READ_ONLY.has(tool)) || (PROGRESS_TOOLS.has(tool) && CLOSEOUT_PATH.test(fp));
  const used = Number(st.closeout) || 0;
  if (!eligible || used >= limit) {
    d.permissionDecisionReason += ` Closeout allowance ${used}/${limit} used; only ` +
      (goal ? '' : 'Read/Grep/Glob and ') + 'writes to vault/plans/*.md, memory/handoffs/*.md or RESUMPTION_FILE.md qualify.';
    return verdict;
  }
  st.closeout = used + 1;
  const why = d.permissionDecisionReason.split(' Way out')[0].replace('SESSION BUDGET BREAKER -- ', '');
  return advise(`SESSION BUDGET TRIPPED (${why}) -- closeout call ${st.closeout}/${limit} allowed: ` +
    'record the spend row and the handoff, then stop.');
}

// --- Goal mode (A1 incident 2026-10-07, vault/specs/goal-budget-admission.md) ----------------------
// A session envelope judged one pane. A1's 42.3M was spent by two undeclared coordinator panes and
// their subagents against one 20M cap that nothing checked before a call. In goal mode a session is
// BOUND to a goal (env CPP_GOAL > cwd under a goal's roots > `goal` in its budget file), measured
// over its own transcript AND <sid>/subagents/*.jsonl (subagent tool calls fire this hook with the
// parent's session id, but their usage is written there), and admitted against a lease reserved from
// the goal's GoalLedger. When the lease is spent, `mission_spend.py goal-renew` settles the measured
// total and reserves the next one, or refuses. Unlike the session envelope, goal mode fails CLOSED:
// an unknown goal, a host outside the goal, an unreadable transcript or a renew that fails is a deny.
// The deny is a plain permissionDecision, never {continue:false} (dispatcher:423-433, dead screen).
const PY = process.env.PYTHON_BIN || (process.platform === 'win32'
  ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3');
const MISSION_SPEND = path.join(__dirname, '..', 'tools', 'mission_spend.py');
const RENEW_TIMEOUT_MS = 8000;              // below the Read chain's 20 s, so a slow renew is a deny, not a kill

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

// Only a bare status read is exempt in goal mode, anchored on the WHOLE command: python, then
// mission_spend.py, then goal-status --goal <id>, then nothing. A substring match (audit gap 4) and
// an unanchored token match (review H2: `python heavy_job.py --tag mission_spend.py goal-status`)
// both let another program run unjudged.
const GOAL_STATUS_ONLY = /^\s*(?:&\s*)?(?:(['"])(?:[^'"]*[\\/])?(?:python3?|py)(?:\.exe)?\1|(?:[^\s'"]*[\\/])?(?:python3?|py)(?:\.exe)?)\s+(['"]?)(?:[^\s'"]*[\\/])?mission_spend\.py\2\s+goal-status\s+--goal\s+[A-Za-z0-9._-]+\s*$/i;
function goalExempt(cmd) {
  return GOAL_STATUS_ONLY.test(String(cmd));
}

// The state a bound session must not write: the goal ledger and index, its own guard state and
// budget file (a forged lease or a dropped `goal` field un-binds it), and the goal CLI's mutating
// verbs. Same OS user, so this defeats the casual and accidental path, not an agent that edits this
// hook -- see the spec's trust boundary (review H1).
const GOAL_STATE = /goal-budget|session-budget-|mission_spend\.py['"]?\s+goal-(?:declare|renew|spawn)\b/i;
function touchesGoalState(event) {
  const ti = event.tool_input || {};
  return GOAL_STATE.test(String(ti.command || '') + ' ' + String(ti.file_path || '') + ' ' + String(ti.path || ''));
}

// A cached lease is admitted only while the journal still holds it OPEN: its id appears exactly once
// (the reserve row; a settle or leak names it again) and that row carries the same amount and base.
// The local state file is a cache, never the authority (review H1a: a forged {amount: 1e15}).
function leaseOpenInJournal(goal, lease) {
  if (!lease || typeof lease.id !== 'string') return false;
  let text;
  try { text = fs.readFileSync(path.join(stateDir(), 'goal-budget', goal, 'spend.journal.jsonl'), 'utf8'); } catch (e) { return false; }
  const needle = JSON.stringify(lease.id);
  const first = text.indexOf(needle);
  if (first < 0 || text.indexOf(needle, first + needle.length) >= 0) return false;
  const start = text.lastIndexOf('\n', first) + 1;
  const end = text.indexOf('\n', first);
  try {
    const r = JSON.parse(text.slice(start, end < 0 ? undefined : end));
    return r.op === 'reserve' && r.kind === 'lease' && r.id === lease.id &&
      r.amount === lease.amount && r.base === lease.base;
  } catch (e) { return false; }
}

function goalDeny(goal, reason) {
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `GOAL BUDGET (${goal}) -- ${reason} Way out: end this turn now with a ` +
      'status line and the next exact action. Nothing new starts on this goal; the Owner decides ' +
      '(a crossed cap is never raised -- a new goal id is). Read the ledger with ' +
      `\`python tools/mission_spend.py goal-status --goal ${goal}\`.` } };
}

function foldFile(gs, file, isMain) {
  let size;
  try { size = fs.statSync(file).size; } catch (e) { if (isMain) throw e; return; }
  let off = gs.files[file] || 0;
  if (size < off) off = 0;                    // truncated: message ids keep the re-read from double counting
  if (size === off) return;
  const fd = fs.openSync(file, 'r');
  let buf;
  try {
    buf = Buffer.alloc(size - off);
    fs.readSync(fd, buf, 0, buf.length, off);
  } finally { fs.closeSync(fd); }
  const end = buf.lastIndexOf(0x0a);
  if (end < 0) return;
  gs.files[file] = off + end + 1;
  const seen = new Set(gs.ids);
  for (const line of buf.subarray(0, end).toString('utf8').split('\n')) {
    if (!line) continue;
    let r;
    try { r = JSON.parse(line); } catch (e) { continue; }
    if (!r || typeof r !== 'object') continue;
    if (gs.since && String(r.timestamp || '') < gs.since) continue;
    const m = r.message;
    if (!m || typeof m !== 'object' || !m.usage || m.model === '<synthetic>') continue;
    const mid = m.id || r.uuid;
    if (seen.has(mid)) continue;
    seen.add(mid);
    gs.ids.push(mid);
    gs.tokens += UK.reduce((s, k) => s + (Number(m.usage[k]) || 0), 0);
    if (isMain) {
      gs.context = UK.slice(0, 3).reduce((s, k) => s + (Number(m.usage[k]) || 0), 0);
      // The next request re-reads this one's context AND its output, plus whatever the turn appends.
      // Canary #3 reserved the context alone and each final reply came in 831-1,230 over it.
      const total = UK.reduce((s, k) => s + (Number(m.usage[k]) || 0), 0);
      if (gs.lastTotal > 0 && total > gs.lastTotal) gs.deltas = (gs.deltas || []).concat(total - gs.lastTotal).slice(-GROWTH_WINDOW);
      gs.lastTotal = total;
    }
  }
  if (gs.ids.length > MAX_IDS) gs.ids = gs.ids.slice(-MAX_IDS);
}

// Size of the pane's next request: the last main request's full total (context + output) plus the
// largest growth between consecutive main requests in the last GROWTH_WINDOW. This is the per-call
// the ledger reserves as the pane's final reply, so it errs high: one spike stays for 5 requests.
const GROWTH_WINDOW = 5;
function nextRequest(gs) {
  const last = gs.lastTotal > 0 ? gs.lastTotal : (gs.context || 0);
  return last + Math.max(0, ...(Array.isArray(gs.deltas) ? gs.deltas : []));
}

function measureGoal(gs, transcript) {
  foldFile(gs, transcript, true);
  const subDir = path.join(path.dirname(transcript), path.basename(transcript, '.jsonl'), 'subagents');
  let names = [];
  try { names = fs.readdirSync(subDir).filter(n => n.endsWith('.jsonl')).sort(); } catch (e) { names = []; }
  for (const n of names) foldFile(gs, path.join(subDir, n), false);
}

function callGoal(args) {
  const r = spawnSync(PY, [MISSION_SPEND, ...args],
    { encoding: 'utf8', timeout: RENEW_TIMEOUT_MS, windowsHide: true });
  if (r.error || (r.status !== 0 && r.status !== 3)) {
    return { failed: `${args[0]} did not answer (${r.error ? (r.error.code || r.error.message) : 'exit ' + r.status})` };
  }
  const line = String(r.stdout || '').trim().split('\n').pop();
  try {
    const out = JSON.parse(line);
    return out && typeof out === 'object' ? out : { failed: `${args[0]} answered no object` };
  } catch (e) { return { failed: `${args[0]} answered unparseable output` }; }
}

function decideGoal(event, sid, bind) {
  const { goal, entry } = bind;
  const cmd = event.tool_input && typeof event.tool_input.command === 'string' ? event.tool_input.command : '';
  if (cmd && goalExempt(cmd)) return null;
  if (!entry) return goalDeny(goal, `UNKNOWN: goal ${goal} is not declared on this host; unknown is never admitted.`);
  if (touchesGoalState(event)) return goalDeny(goal, 'a call that touches goal-budget state is not admitted from a bound session.');
  const gPath = path.join(stateDir(), `session-budget-${sid}.goal.json`);
  let gs = readJson(gPath);
  const since = entry.since ? String(entry.since) : null;
  if (!gs || gs.goal !== goal || gs.since !== since || !gs.files || !Array.isArray(gs.ids)) {
    gs = { goal, since, files: {}, ids: [], tokens: 0, context: 0, lease: null, closeout: 0 };
  }
  let verdict = null;
  if (!event.transcript_path) verdict = goalDeny(goal, 'UNKNOWN: the event carries no transcript_path.');
  else {
    try { measureGoal(gs, event.transcript_path); } catch (e) {
      verdict = goalDeny(goal, `UNKNOWN: the transcript cannot be read (${e.code || e.message}).`);
    }
  }
  const next = nextRequest(gs);
  const base = ['--goal', goal, '--session', sid, '--per-call', String(next), '--measured', String(gs.tokens)];
  // Renew BEFORE the call whose next request would cross the lease: an admitted call is paid by the
  // request that follows it (`next`), so the lease must still hold that much.
  const crossing = gs.lease && gs.tokens - gs.lease.base + next > gs.lease.amount;
  if (!verdict && (!gs.lease || crossing || !leaseOpenInJournal(goal, gs.lease))) {
    const r = callGoal(['goal-renew', ...base]);
    if (r.failed) verdict = goalDeny(goal, `UNKNOWN: ${r.failed}.`);
    else if (!r.ok) {
      gs.lease = null;
      verdict = closeout(entry, gs, event, goalDeny(goal, `refused: ${r.reason}.`), true);
    } else gs.lease = r.lease;
  }
  const tool = String(event.tool_name || '');
  if (!verdict && (tool === 'Agent' || tool === 'Task')) {
    const r = callGoal(['goal-spawn', ...base]);
    if (r.failed) verdict = goalDeny(goal, `UNKNOWN: ${r.failed}; no child starts on an unmeasured goal.`);
    else if (!r.ok) verdict = goalDeny(goal, `child refused before launch: ${r.reason}.`);
  }
  const tmp = `${gPath}.${process.pid}.tmp`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(gs));
    fs.renameSync(tmp, gPath);
  } catch (e) {
    try { fs.unlinkSync(tmp); } catch (_) { /* nothing to clean */ }
    // The journal is the authority; a lost local write only means the next call renews early.
  }
  return verdict;
}

function decide(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const sw = String(process.env.CPP_SESSION_BUDGET || '').trim().toLowerCase();
  if (sw === '0' || sw === 'off' || sw === 'false') return null;
  const bind = goalBinding(event, sid);
  if (bind) {
    let gv;
    try { gv = decideGoal(event, sid, bind); } catch (e) {
      gv = goalDeny(bind.goal, `UNKNOWN: the goal check itself failed (${e.code || e.message}); a bound session fails closed.`);
    }
    if (gv) return gv;
  }
  const bPath = path.join(stateDir(), `session-budget-${sid}.json`);
  if (!fs.existsSync(bPath)) return null;                     // the opt-in: no envelope, no guard
  const cmd = event.tool_input && typeof event.tool_input.command === 'string' ? event.tool_input.command : '';
  if (cmd && EXEMPT_CMD.test(cmd)) return null;               // rotation / lifting stays reachable
  const sPath = path.join(stateDir(), `session-budget-${sid}.state.json`);
  const budget = readJson(bPath);
  const prev = readJson(sPath);
  let st = prev && typeof prev === 'object' && Array.isArray(prev.ids) ? prev : null;
  const since = budget && budget.since ? String(budget.since) : null;
  if (!st || st.since !== since) st = Object.assign(fresh(since), { grace: !!(st && st.grace) });

  let unreadable = null;
  const okBudget = budget && [budget.target, budget.warn, budget.stop].every(v => Number.isFinite(Number(v)) && Number(v) > 0);
  if (!okBudget) unreadable = 'the budget file is unreadable or incomplete';
  else if (!event.transcript_path) unreadable = 'the event carries no transcript_path';
  else {
    try { advance(st, event.transcript_path); } catch (e) { unreadable = `the transcript cannot be read (${e.code || e.message})`; }
  }
  let verdict;
  if (unreadable) {
    if (st.grace) verdict = deny(`accounting unreadable: ${unreadable}; the one grace call is spent.`);
    else {
      st.grace = true;
      verdict = advise(`SESSION BUDGET: accounting unreadable (${unreadable}). ONE grace call allowed; the next one is denied.`);
    }
  } else {
    st.grace = false;
    verdict = closeout(budget, st, event, judge(budget, st));
  }
  // Per-process temp name: parallel tool calls run the guard concurrently, and on Windows two
  // renames onto one target race to EPERM (measured 2026-10-05: a parallel Read pair was denied).
  const tmp = `${sPath}.${process.pid}.tmp`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(st));
    fs.renameSync(tmp, sPath);
  } catch (e) {
    try { fs.unlinkSync(tmp); } catch (_) { /* nothing to clean */ }
    // The verdict was computed from a readable transcript; a lost write only means the next call
    // re-reads from the older offset (same totals). Only the grace record must persist, so the
    // unreadable path still fails closed.
    if (unreadable) return deny(`accounting unreadable and the grace record cannot be written (${e.code || e.message}).`);
  }
  return verdict;
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }  // a bug in the guard never breaks a tool call
}

module.exports = { run, decide, advance, fresh, judge, DEFAULT_CALL_RATIO, DEFAULT_NOPROGRESS };
