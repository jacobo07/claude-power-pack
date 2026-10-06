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
// MultiEdit, NotebookEdit, Read, Grep). Gen3 T3 (2026-10-05): the meter is the whole TREE -- the
// session transcript plus every subagents/agent-*.jsonl -- because a child's events carry the
// parent's session id; running children are reserved pre-call; `per_child_stop` judges a child
// on its own spend; Agent dispatch is gated through agent-solo-guard.js with `child_reserve`.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const UK = ['input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'];
const PROGRESS_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
// session_checkpoint.py is /kclear's writer: the breaker tells the model to rotate, so it must not
// block the seal it asked for (measured live 2026-10-06, d64f90b2).
const EXEMPT_CMD = /rollover\.py|mission_spend\.py|session_checkpoint\.py|session-budget-/;
const MAX_IDS = 20000;
const DEFAULT_CALL_RATIO = 1.5;
const DEFAULT_NOPROGRESS = 25;
// A child whose transcript moved this recently is treated as running (in flight).
const ACTIVE_CHILD_MS = 120000;
// Processed tokens reserved for a NEW child at Agent dispatch when the envelope declares none:
// ~20 calls at the ~104k worker floor measured on every T2 executor (gen3_t2/README.md).
const DEFAULT_CHILD_RESERVE = 2000000;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

function fresh(since) {
  return { since: since || null, offset: 0, tokens: 0, calls: 0, context: 0, progress_at: 0, ids: [], grace: false,
    files: {}, root_context: 0 };
}

// Fold the complete lines appended since slot.offset into st. Mirrors mission_spend.session_tokens.
// `slot` is the per-file cursor: st itself for the session's own transcript (the legacy fields),
// a st.files[path] entry for a subagent transcript, whose tokens are also kept apart so a child
// envelope can be judged on its own spend.
function advance(st, transcript, slot) {
  slot = slot || st;
  const size = fs.statSync(transcript).size;
  if (size < slot.offset) {                                       // truncated/rotated
    if (slot !== st) throw Object.assign(new Error('a child transcript shrank'), { code: 'TRUNCATED' });
    Object.assign(st, fresh(st.since), { grace: st.grace });
  }
  if (size === slot.offset) return;
  const fd = fs.openSync(transcript, 'r');
  let buf;
  try {
    buf = Buffer.alloc(size - slot.offset);
    fs.readSync(fd, buf, 0, buf.length, slot.offset);
  } finally { fs.closeSync(fd); }
  const end = buf.lastIndexOf(0x0a);
  if (end < 0) return;                       // only a partial line so far
  slot.offset += end + 1;
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
    const n = UK.reduce((s, k) => s + (Number(u[k]) || 0), 0);
    st.tokens += n;
    if (slot !== st) slot.tokens = (Number(slot.tokens) || 0) + n;
    slot.context = UK.slice(0, 3).reduce((s, k) => s + (Number(u[k]) || 0), 0);
    if (slot === st) st.root_context = st.context;
  }
  if (st.ids.length > MAX_IDS) st.ids = st.ids.slice(-MAX_IDS);
}

// A subagent writes <dir>/<sid>/subagents/agent-*.jsonl beside the parent's <dir>/<sid>.jsonl, and
// its hook events carry the PARENT's session id. Reading only event.transcript_path left every
// child unmetered: the TOK-18 Gen3 T2 canary passed its cap while this guard saw only the parent
// (2026-10-05, T2-0.5-guard-subagent.md). Whichever file the event names, the tree is the same.
function treeOf(transcript) {
  const dir = path.dirname(transcript);
  const root = path.basename(dir) === 'subagents'
    ? path.join(path.dirname(path.dirname(dir)), path.basename(path.dirname(dir)) + '.jsonl')
    : transcript;
  const subDir = path.join(root.replace(/\.jsonl$/, ''), 'subagents');
  let kids = [];
  try { kids = fs.readdirSync(subDir).filter(f => f.endsWith('.jsonl')).map(f => path.join(subDir, f)); }
  catch (e) { /* no child has started */ }
  return { root, kids };
}

// Fold the whole tree into st, then derive what the judge needs: the caller's own context and
// spend, and a RESERVE for children that are running right now -- each can finish one more model
// call before its next gated tool call, so that call is counted before it happens. The overshoot
// past `stop` is then bounded by the caller's one call, not by every child's unobserved run.
function advanceTree(st, transcript) {
  const { root, kids } = treeOf(transcript);
  const fold = () => {
    if (!st.files || typeof st.files !== 'object') st.files = {};
    advance(st, root);
    for (const k of kids) advance(st, k, st.files[k] || (st.files[k] = { offset: 0, tokens: 0, context: 0 }));
  };
  try { fold(); } catch (e) {
    if (e.code !== 'TRUNCATED') throw e;
    Object.assign(st, fresh(st.since), { grace: st.grace, files: {} });
    fold();
  }
  const caller = transcript === root ? null : st.files[transcript];
  st.caller = caller ? path.basename(transcript) : 'root';
  st.caller_tokens = caller ? caller.tokens : null;
  st.context = caller ? caller.context : (Number(st.root_context) || 0);
  const now = Date.now();
  let reserve = 0, active = 0;
  for (const k of kids) {
    if (k === transcript) continue;
    try {
      if (now - fs.statSync(k).mtimeMs < ACTIVE_CHILD_MS) { reserve += Number(st.files[k].context) || 0; active += 1; }
    } catch (e) { /* vanished: nothing in flight */ }
  }
  st.reserve = reserve;
  st.active_children = active;
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
  // Pre-call: what is already in flight (running children) and, at Agent dispatch, the new child.
  const inflight = Number(st.reserve) || 0;
  const dispatch = Number(st.dispatch_reserve) || 0;
  if (inflight + dispatch > 0 && st.tokens + inflight + dispatch > budget.stop) {
    return deny(`processed ${fmt(st.tokens)} + reserve ${fmt(inflight)} for ${st.active_children || 0} running ` +
      `child(ren)${dispatch ? ` + ${fmt(dispatch)} for the child being dispatched` : ''} > stop ${fmt(budget.stop)}.`);
  }
  const childStop = Number(budget.per_child_stop) || 0;
  if (childStop > 0 && st.caller_tokens != null && st.caller_tokens > childStop) {
    return deny(`CHILD ENVELOPE: ${st.caller} processed ${fmt(st.caller_tokens)} > per-child stop ${fmt(childStop)}. ` +
      'Return what you have to the parent now.');
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

// opts.dispatch: the event is an Agent dispatch (called from agent-solo-guard.js, because Agent
// has no dispatcher lane); the new child's reserve is added before it is allowed to start.
function decide(event, opts) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const sw = String(process.env.CPP_SESSION_BUDGET || '').trim().toLowerCase();
  if (sw === '0' || sw === 'off' || sw === 'false') return null;
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
  st.dispatch_reserve = opts && opts.dispatch && budget
    ? (Number(budget.child_reserve) || DEFAULT_CHILD_RESERVE) : 0;

  let unreadable = null;
  const okBudget = budget && [budget.target, budget.warn, budget.stop].every(v => Number.isFinite(Number(v)) && Number(v) > 0);
  if (!okBudget) unreadable = 'the budget file is unreadable or incomplete';
  else if (!event.transcript_path) unreadable = 'the event carries no transcript_path';
  else {
    try { advanceTree(st, event.transcript_path); } catch (e) { unreadable = `the transcript cannot be read (${e.code || e.message})`; }
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
    verdict = judge(budget, st);
  }
  try {
    fs.writeFileSync(sPath + '.tmp', JSON.stringify(st));
    fs.renameSync(sPath + '.tmp', sPath);
  } catch (e) {
    return deny(`accounting state cannot be written (${e.code || e.message}).`);
  }
  return verdict;
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }  // a bug in the guard never breaks a tool call
}

module.exports = { run, decide, advance, advanceTree, treeOf, fresh, judge, DEFAULT_CALL_RATIO, DEFAULT_NOPROGRESS,
  DEFAULT_CHILD_RESERVE, ACTIVE_CHILD_MS };
