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
// transcript) but not themselves gated -- the next gated call is.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

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

// ---- checkpoint mode -------------------------------------------------------------------------
// A session that hits its stop ceiling used to be denied EVERYTHING, including the commit that
// would have saved its work and the RESUMPTION file the successor reads. When the calls remaining
// before the stop ceiling fall to the reserve (default 6; `checkpoint_reserve` in the budget file),
// or the ceiling is passed by fewer than `reserve` calls, the guard denies everything EXCEPT:
//   (a) PowerShell/Bash commands made only of git add / git commit / git status / git log;
//   (b) Write/Edit/MultiEdit of RESUMPTION*.md, TOKENS.md or a path in the budget's `checkpoint_paths`.
// Beyond the reserve the ordinary deny applies to everything. The reserve is capped at a quarter of
// the envelope's calls so a tiny envelope is not all checkpoint.
const DEFAULT_CHECKPOINT_RESERVE = 6;
const GIT_EXE = String.raw`(?:git(?:\.exe)?|"[^"]*git(?:\.exe)?"|'[^']*git(?:\.exe)?')`;
const GIT_SEGMENT = new RegExp(String.raw`^(?:&\s*)?${GIT_EXE}\s+(?:-C\s+(?:"[^"]*"|'[^']*'|\S+)\s+)?(?:add|commit|status|log)(?:\s|$)`);

// Split a command at unquoted ; && || newline. null when it holds anything that could do more than
// run those segments: an unquoted pipe, redirect or backtick, or $( / backtick inside double quotes.
function splitCommand(cmd) {
  const segs = [];
  let cur = '', q = null;
  for (let i = 0; i < cmd.length; i++) {
    const c = cmd[i];
    if (q) {
      if (q === '"' && (c === '`' || (c === '$' && cmd[i + 1] === '('))) return null;
      if (c === q) q = null;
      cur += c;
      continue;
    }
    if (c === "'" || c === '"') { q = c; cur += c; continue; }
    if (c === '`' || c === '<' || c === '>') return null;
    if (c === '$' && cmd[i + 1] === '(') return null;
    if (c === '&' && cmd[i + 1] === '&') { segs.push(cur); cur = ''; i++; continue; }
    if (c === '|') { if (cmd[i + 1] === '|') { segs.push(cur); cur = ''; i++; continue; } return null; }
    if (c === ';' || c === '\n' || c === '\r') { segs.push(cur); cur = ''; continue; }
    cur += c;
  }
  if (q) return null;
  segs.push(cur);
  return segs.map(s => s.trim()).filter(Boolean);
}

function gitOnly(cmd) {
  const segs = splitCommand(String(cmd || ''));
  return !!segs && segs.length > 0 && segs.every(s => GIT_SEGMENT.test(s));
}

function checkpointPathOk(p, budget) {
  const norm = String(p || '').replace(/\\/g, '/').toLowerCase();
  const base = norm.split('/').pop();
  if (/^resumption.*\.md$/.test(base) || base === 'tokens.md') return true;
  const extra = Array.isArray(budget.checkpoint_paths) ? budget.checkpoint_paths : [];
  return extra.some(e => {
    const n = String(e || '').replace(/\\/g, '/').toLowerCase();
    return n && (norm === n || norm.endsWith('/' + n));
  });
}

function checkpointAllowed(call, budget) {
  if (!call || !call.tool) return false;
  const inp = call.input || {};
  if (call.tool === 'Bash' || call.tool === 'PowerShell') return gitOnly(inp.command);
  if (call.tool === 'Write' || call.tool === 'Edit' || call.tool === 'MultiEdit') return checkpointPathOk(inp.file_path, budget);
  return false;
}

// Calls left before the stop ceiling (negative once past it), and the envelope's total calls.
function callsRemaining(budget, st) {
  const est = Number(budget.calls_estimate) || 0;
  const ratio = Number(budget.call_ratio) || DEFAULT_CALL_RATIO;
  let rem = Infinity, total = Infinity;
  if (est > 0) { total = ratio * est; rem = total - st.calls; }
  if (st.calls > 0 && st.tokens > 0) {
    const per = st.tokens / st.calls;
    const tr = Math.floor((budget.stop - st.tokens) / per);
    if (tr < rem) { rem = tr; total = Math.min(total, st.calls + tr); }
  } else if (st.tokens > budget.stop) { rem = -1; }
  return { rem, total };
}

function checkpointVerdict(budget, st, call, why) {
  const reserve = Math.max(0, Math.floor(Number(budget.checkpoint_reserve ?? DEFAULT_CHECKPOINT_RESERVE)));
  const { rem, total } = callsRemaining(budget, st);
  if (rem >= 0) delete st.over_at;
  else if (st.over_at === undefined) st.over_at = st.calls;
  if (reserve === 0 || rem === Infinity) return null;
  const cap = Number.isFinite(total) ? Math.floor(total / 4) : reserve;
  const preWindow = Math.min(reserve, cap) > 0 && rem >= 0 && rem <= Math.min(reserve, cap);
  const overBy = st.over_at === undefined ? 0 : st.calls - st.over_at;
  const postWindow = rem < 0 && overBy < reserve;
  if (!preWindow && !postWindow) return null;
  const extra = Array.isArray(budget.checkpoint_paths) && budget.checkpoint_paths.length
    ? `, ${budget.checkpoint_paths.join(', ')}` : '';
  const left = postWindow ? reserve - overBy : rem;
  const text = `${why || `${rem} calls remain before the stop ceiling.`} ` +
    `Allowed now: (a) PowerShell/Bash commands that are only git add / git commit / git status / git log; ` +
    `(b) Write/Edit of RESUMPTION*.md, TOKENS.md${extra}. Everything else is denied. ` +
    `${left} checkpoint call(s) left: commit your work, write RESUMPTION.md, then end the turn and /kclear.`;
  if (checkpointAllowed(call, budget)) return advise(`SESSION BUDGET CHECKPOINT MODE -- ${text}`);
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `SESSION BUDGET CHECKPOINT MODE -- ${text}` } };
}

function judge(budget, st, call) {
  if (call) {
    const cp = checkpointVerdict(budget, st, call,
      st.tokens > budget.stop ? `processed ${fmt(st.tokens)} > stop ${fmt(budget.stop)} (target ${fmt(budget.target)}).` : null);
    if (cp) return cp;
  }
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

function decide(event) {
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
    verdict = judge(budget, st, { tool: event.tool_name, input: event.tool_input || {} });
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

module.exports = { run, decide, advance, fresh, judge, gitOnly, DEFAULT_CALL_RATIO, DEFAULT_NOPROGRESS,
  DEFAULT_CHECKPOINT_RESERVE };
