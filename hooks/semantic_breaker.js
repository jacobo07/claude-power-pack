// semantic_breaker.js -- stop waste BEFORE the raw token ceiling (CDC C4).
//
// One module, two events (dispatcher lanes PostToolUse-default and the PreToolUse-*-default chains):
//   PostToolUse  fold the call into the per-session counters; on a trip write the token incident,
//                run the C1 role autopsy into it, write the session deny budget.
//   PreToolUse   a tripped session's next call is refused with a recompile message (closeout writes pass).
// BOUND sessions only (goal binding, cognitive unit, or CPP_COG_ROUTE). Unbound = one failed read, no work.
// Progress (resets the counter): a tool Edit/Write/MultiEdit/NotebookEdit (work-tree change, new file,
// receipt write), a commit command or a moved git HEAD, a proof run turning red -> green.
// Counters: calls since progress, rereads (same path, mtime unchanged, since progress), last tool names.
// Context growth is NOT counted: it needs transcript usage and a guess would be worse than nothing; the
// raw-token ceiling (session_budget_guard) still owns it.
// Threshold: CPP_SEM_BREAKER_CALLS > vault/config/semantic-breaker.json (trip_calls = max(calls_p95, 25), written by
// tools/semantic_breaker.py calibrate from historical transcripts) > 25.
// Kill switch CPP_SEM_BREAKER=off. Any own error -> allow (fail open). The model turn itself is not
// interceptable (host limit): this fires at tool calls only.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const gb = require('./lib/goal_binding');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const PY = process.env.PYTHON_BIN || (process.platform === 'win32'
  ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3');
const AUTOPSY = path.join(__dirname, '..', 'tools', 'session_autopsy.py');
const CONFIG = path.join(__dirname, '..', 'vault', 'config', 'semantic-breaker.json');
const DEFAULT_CALLS = 25;
const EDITS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
const COMMIT = /\bcommit\b/;
const PROOF = /\b(pytest|unittest)\b|\btest[_-]\w*\.(py|js)\b|\bnode\s+--test\b|\bnpm\s+(run\s+)?test\b/i;
const FAILTXT = /\bFAIL(ED)?\b|\bfailed\b|Traceback|\bAssertionError\b|\berror\b/i;
const CLOSEOUT_PATH = /(^|[\\/])(vault[\\/]plans[\\/][^\\/]+\.md|memory[\\/]handoffs[\\/][^\\/]+\.md|RESUMPTION_FILE\.md|[^\\/]+-receipt\.md)$/;
const CLOSEOUT_CALLS = 4;
const LAST_N = 12;

function off() {
  const sw = String(process.env.CPP_SEM_BREAKER || '').trim().toLowerCase();
  return sw === '0' || sw === 'off' || sw === 'false';
}

function threshold() {
  const e = Number(process.env.CPP_SEM_BREAKER_CALLS);
  if (Number.isFinite(e) && e > 0) return { calls: e, source: 'env' };
  const c = gb.readJson(CONFIG);
  const v = c && Number(c.trip_calls);
  if (Number.isFinite(v) && v > 0) return { calls: v, source: 'calibrated' };
  return { calls: DEFAULT_CALLS, source: 'default' };
}

function bound(event, sid) {
  if (process.env.CPP_COG_ROUTE) return 'unit-env';
  const u = gb.readJson(path.join(gb.stateDir(), 'cognitive-unit', `${sid}.json`));
  if (u && u.route) return `unit:${u.unit || 'bound'}`;
  const b = gb.goalBinding(event, sid, { observe: true });
  if (b && b.goal && !b.quarantine) return `goal:${b.goal}`;
  return null;
}

// Cheap git HEAD fingerprint: resolve .git (or a worktree's gitdir file) up from cwd, read HEAD and its ref.
function headOf(cwd) {
  try {
    let d = path.resolve(cwd || '.');
    for (let i = 0; i < 12; i++) {
      const g = path.join(d, '.git');
      let st = null;
      try { st = fs.statSync(g); } catch (e) { st = null; }
      if (st) {
        let gitdir = g;
        if (st.isFile()) {
          const m = /gitdir:\s*(.+)/.exec(fs.readFileSync(g, 'utf8'));
          if (!m) return null;
          gitdir = path.resolve(d, m[1].trim());
        }
        const head = fs.readFileSync(path.join(gitdir, 'HEAD'), 'utf8').trim();
        const r = /^ref:\s*(.+)$/.exec(head);
        if (!r) return head;
        let common = gitdir;
        try { common = path.resolve(gitdir, fs.readFileSync(path.join(gitdir, 'commondir'), 'utf8').trim()); } catch (e) { /* plain repo */ }
        for (const base of [gitdir, common]) {
          try { return fs.readFileSync(path.join(base, r[1]), 'utf8').trim(); } catch (e) { /* try next */ }
        }
        try {
          const pr = fs.readFileSync(path.join(common, 'packed-refs'), 'utf8').split('\n').find(l => l.endsWith(' ' + r[1]));
          if (pr) return pr.split(' ')[0];
        } catch (e) { /* no packed refs */ }
        return head;
      }
      const up = path.dirname(d);
      if (up === d) break;
      d = up;
    }
  } catch (e) { /* unknown head: not progress */ }
  return null;
}

function respText(r) {
  if (r == null) return '';
  if (typeof r === 'string') return r;
  try { return JSON.stringify(r); } catch (e) { return ''; }
}

function fresh() {
  return { calls: 0, since_progress: 0, progress_total: 0, rereads: 0, reads: {}, head: null, red: false,
    tools: [], tripped: null, closeout: 0, bound: null };
}

function statePath(sid) { return path.join(gb.stateDir(), 'semantic-breaker', `${sid}.json`); }

function save(sid, st) {
  const p = statePath(sid);
  const tmp = `${p}.${process.pid}.tmp`;
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(tmp, JSON.stringify(st));
    fs.renameSync(tmp, p);
  } catch (e) { try { fs.unlinkSync(tmp); } catch (_) { /* nothing */ } }
}

// Fold one completed call. Returns the progress reason or null.
function fold(st, event) {
  const tool = String(event.tool_name || '');
  const ti = event.tool_input || {};
  const cmd = typeof ti.command === 'string' ? ti.command : '';
  const fp = String(ti.file_path || ti.path || '');
  st.calls += 1;
  st.tools = st.tools.concat(tool).slice(-LAST_N);
  let progress = null;
  if (EDITS.has(tool)) progress = `edit:${path.basename(fp) || tool}`;
  else if ((tool === 'Bash' || tool === 'PowerShell') && cmd) {
    const res = respText(event.tool_response);
    if (COMMIT.test(cmd) && !FAILTXT.test(res.slice(0, 400))) progress = 'commit';
    else if (PROOF.test(cmd)) {
      const bad = FAILTXT.test(res);
      if (st.red && !bad) progress = 'red_green';
      st.red = bad;
    }
  }
  if (tool === 'Read' && fp) {
    let m = null;
    try { m = fs.statSync(fp).mtimeMs; } catch (e) { m = null; }
    if (m !== null && st.reads[fp] === m) st.rereads += 1;
    if (m !== null) st.reads[fp] = m;
  }
  const head = headOf(event.cwd);
  if (!progress && head && st.head && head !== st.head) progress = 'head_moved';
  if (head) st.head = head;
  if (progress) {
    st.since_progress = 0;
    st.rereads = 0;
    st.reads = {};
    st.progress_total += 1;
    st.last_progress = progress;
  } else st.since_progress += 1;
  return progress;
}

function trip(sid, st, event, th, why) {
  const ts = new Date().toISOString();
  const dir = path.join(gb.stateDir(), 'token-incidents');
  const file = path.join(dir, `${ts.replace(/[:.]/g, '-')}-${sid}.json`);
  const inc = { class: 'TOKEN_INCIDENT', ts, session_id: sid, reason: why, bound: st.bound,
    threshold: th, counters: { calls: st.calls, calls_since_progress: st.since_progress, progress_total: st.progress_total,
      rereads: st.rereads, context_growth: null, context_growth_note: 'not measured: needs transcript usage; owned by session_budget_guard' },
    last_tools: st.tools, cwd: event.cwd || null, transcript: event.transcript_path || null, autopsy: null, deny_budget: null };
  if (event.transcript_path) {
    try {
      const r = spawnSync(PY, [AUTOPSY, event.transcript_path, '--roles', '--json'],
        { encoding: 'utf8', timeout: 30000, windowsHide: true });
      const a = JSON.parse(r.stdout);
      inc.autopsy = { calls: a.calls, processed_tokens: a.processed_tokens, transitions: a.transitions,
        roles: Object.fromEntries(Object.entries(a.roles || {}).filter(([, v]) => v.calls).map(([k, v]) => [k, { calls: v.calls, tokens: v.tokens, share: v.share }])) };
    } catch (e) { inc.autopsy = { unavailable: String(e && e.message || e).slice(0, 200) }; }
  } else inc.autopsy = { unavailable: 'event carries no transcript_path' };
  // Deny budget through session_budget_guard's own state: stop=1 makes its token breaker refuse every
  // further call after the closeout allowance. Never overwrites an envelope the Owner declared.
  const bPath = path.join(gb.stateDir(), `session-budget-${sid}.json`);
  try {
    if (fs.existsSync(bPath)) inc.deny_budget = 'kept existing envelope';
    else {
      fs.writeFileSync(bPath, JSON.stringify({ target: 1, warn: 1, stop: 1, closeout_calls: CLOSEOUT_CALLS,
        since: null, source: 'semantic_breaker', incident: path.basename(file) }));
      inc.deny_budget = bPath;
    }
  } catch (e) { inc.deny_budget = `unwritable: ${e.code || e.message}`; }
  try { fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(file, JSON.stringify(inc, null, 2)); } catch (e) { inc.file_error = e.code || e.message; }
  st.tripped = { ts, why, incident: file };
}

function denyMsg(st) {
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `TOKEN_INCIDENT (semantic breaker) -- ${st.tripped.why}. The loop is refused, not the goal: ` +
      'stop calling tools, write the status and the exact next action (a receipt or handoff write is still admitted), ' +
      `then recompile the unit with a narrower step. Incident: ${st.tripped.incident}. Kill switch CPP_SEM_BREAKER=off is the Owner's.` } };
}

function decide(event) {
  if (off()) return null;
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const pre = event.hook_event_name === 'PreToolUse' || (event.hook_event_name == null && event.tool_response === undefined);
  const sp = statePath(sid);
  let st = gb.readJson(sp);
  if (pre) {
    if (!st || !st.tripped) return null;
    const tool = String(event.tool_name || '');
    const fp = String((event.tool_input && event.tool_input.file_path) || '');
    if (EDITS.has(tool) && CLOSEOUT_PATH.test(fp) && (st.closeout || 0) < CLOSEOUT_CALLS) {
      st.closeout = (st.closeout || 0) + 1;
      save(sid, st);
      return null;
    }
    return denyMsg(st);
  }
  if (st && st.tripped) return null;                      // latched; the Pre lane refuses
  const b = bound(event, sid);
  if (!b) return null;
  if (!st || typeof st !== 'object' || !Array.isArray(st.tools)) st = fresh();
  st.bound = b;
  const progress = fold(st, event);
  const th = threshold();
  if (!progress && st.since_progress >= th.calls) {
    trip(sid, st, event, th, `${st.since_progress} calls without progress (limit ${th.calls}, ${th.source}); ${st.rereads} unchanged rereads`);
  }
  save(sid, st);
  return null;
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }   // a bug in the breaker never breaks a tool call
}

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    let out = null;
    try { out = decide(JSON.parse(raw.replace(/^\uFEFF/, ''))); } catch (e) { out = null; }
    process.stdout.write(out ? JSON.stringify(out) : '{}');
  });
}

module.exports = { run, decide, fold, fresh, threshold, headOf, DEFAULT_CALLS };
