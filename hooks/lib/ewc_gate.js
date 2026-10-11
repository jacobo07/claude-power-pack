'use strict';
/**
 * ewc_gate.js -- Pre-Stop Unresolved Obligation Gate (EWC M5). Pure filesystem reads, no subprocess.
 *
 * evaluate() answers one question at turn end: is an AGENT-owned, actionable obligation still open?
 * Sources: goal log (goal-bound session, via goal_binding.readBinding, observe only) else the E2
 * session ledger (<goals_root>/<repo-id>/session-<sid>/NNNNNN.json), plus the shared
 * modules/autonomy_gate/obligation_patterns.json applied to the LAST assistant turn (backstop).
 * Unknown state is never COMPLETE: it is STOP_UNKNOWN.
 *
 * Mirrors (does not re-invent): modules/autonomy_gate/obligations.py classify_obligation,
 * modules/daif/turn_obligations.py compile_turn, session_scope.obligation_id. WISH/FRAME regexes
 * mirror modules/daif/obligation_extractor.py (test_ewc.py asserts the Python/Node agreement).
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const PATTERNS_FILE = path.join(__dirname, '..', '..', 'modules', 'autonomy_gate', 'obligation_patterns.json');
const TAIL_BYTES = 512 * 1024;
const MAX_LEN = 600;
const MIN_SUBJECT_WORDS = 4;
const WISH_RE = /\b(?:keep an eye|be careful|at some point|somewhere down the line|ten(?:er)? cuidado|alg(?:ú|u)n d(?:í|i)a|estar(?:í|i)a bien)\b/i;
const FRAME_RE = /(?:\b(?:I|we|you|let'?s|I'?ll|we'?ll)\b|\b(?:must|should|need(?:s)? to|have to|has to|will)\b|\b(?:pending|deferred|remaining|next)\b|\b(?:hay que|falta|faltan|queda|quedan|pendiente|voy a|vamos a|debe|debemos|no tocar)\b)/i;
const SEV_RANK = { RED: 3, AMBER: 2, INFO: 1 };
const REASON = { eval_table_fail: 'FAILED_GATE', eval_table_warn: 'ACTIONABLE_WARNING',
  missing_evidence: 'MISSING_EVIDENCE', next_step: 'KNOWN_NEXT_ACTION' };

function goalsRoot() {
  const e = String(process.env.GSDX_GOALS_ROOT || '').trim();
  return e || path.join(os.homedir(), '.claude', 'state', 'gsd-x', 'goals');
}

function obligationId(text) {
  const norm = String(text).toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').split(/\s+/).filter(Boolean).join(' ');
  return 's-' + crypto.createHash('sha256').update(norm, 'utf8').digest('hex').slice(0, 10);
}

function scopeId(sid) {
  const s = String(sid || '').toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^[-.]+|[-.]+$/g, '');
  return s ? ('session-' + s).slice(0, 64).replace(/[-.]+$/, '') : '';
}

// ---- reading logs ---------------------------------------------------------
// Returns {events, ok}. A directory that is absent is "nothing recorded" (ok); a directory whose
// events cannot be read as a gapless sequence is NOT ok -- never an empty log.
function readEvents(dir) {
  let names;
  try { names = fs.readdirSync(dir); } catch (e) { return { events: [], ok: e.code === 'ENOENT', absent: true }; }
  const nums = [];
  for (const n of names) { const m = /^(\d{6})\.json$/.exec(n); if (m) nums.push([parseInt(m[1], 10), n]); }
  nums.sort((a, b) => a[0] - b[0]);
  const events = [];
  for (let i = 0; i < nums.length; i++) {
    if (nums[i][0] !== i + 1) return { events: [], ok: false };
    try {
      const ev = JSON.parse(fs.readFileSync(path.join(dir, nums[i][1]), 'utf8').replace(/^﻿/, ''));
      if (!ev || typeof ev !== 'object' || typeof ev.type !== 'string') return { events: [], ok: false };
      events.push(ev);
    } catch (e) { return { events: [], ok: false }; }
  }
  return { events, ok: true, absent: nums.length === 0 };
}

function foldObligations(events) {
  const obs = new Map();
  for (const ev of events) {
    const d = ev.data || {};
    if (ev.type === 'obligation.accepted' && d.id) {
      obs.set(d.id, { id: d.id, text: String(d.text || ''), source: String(d.source || 'goal'),
        severity: d.severity || 'RED', actionability: d.actionability || 'NOW',
        owner_class: d.owner_class || 'AGENT', next_action: String(d.next_action || d.text || ''), open: true });
    } else if (ev.type === 'obligation.satisfied' && obs.has(d.id)) {
      obs.get(d.id).open = false;
    } else if (ev.type === 'obligation.dispositioned' && obs.has(d.id)) {
      obs.get(d.id).open = false;
    } else if (ev.type === 'obligation.carried' && obs.has(d.id)) {
      // carried keeps the current state (a satisfied one re-opens in Python only if proof was stale)
    }
  }
  return obs;
}

function repoDirs(root) {
  try { return fs.readdirSync(root).map((n) => path.join(root, n)).filter((p) => { try { return fs.statSync(p).isDirectory(); } catch (e) { return false; } }); }
  catch (e) { return []; }
}

// ---- turn text (bounded tail) ----------------------------------------------
function lastTurnText(transcriptPath) {
  const size = fs.statSync(transcriptPath).size;
  let raw;
  if (size <= TAIL_BYTES) raw = fs.readFileSync(transcriptPath, 'utf8');
  else {
    const buf = Buffer.allocUnsafe(TAIL_BYTES);
    const fd = fs.openSync(transcriptPath, 'r');
    try { fs.readSync(fd, buf, 0, TAIL_BYTES, size - TAIL_BYTES); } finally { fs.closeSync(fd); }
    const s = buf.toString('utf8'); const nl = s.indexOf('\n');
    raw = nl === -1 ? '' : s.slice(nl + 1);
  }
  const lines = raw.split(/\r?\n/);
  const chunks = [];
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim(); if (!line) continue;
    let rec; try { rec = JSON.parse(line); } catch (e) { continue; }
    const msg = rec.message || rec; const role = msg.role || rec.type;
    if (role === 'user') {
      const c = msg.content;
      if (Array.isArray(c) && c.some((b) => b && b.type === 'tool_result')) continue;
      break;
    }
    if (role !== 'assistant') continue;
    const c = msg.content;
    if (typeof c === 'string') { if (c) chunks.unshift(c); continue; }
    if (Array.isArray(c)) for (let j = c.length - 1; j >= 0; j--) if (c[j] && c[j].type === 'text' && c[j].text) chunks.unshift(c[j].text);
  }
  return chunks.join('\n');
}

// ---- compiler mirror ---------------------------------------------------------
function loadPatterns() {
  const spec = JSON.parse(fs.readFileSync(PATTERNS_FILE, 'utf8').replace(/^﻿/, ''));
  return { split: new RegExp(spec.sentence_split), list: spec.patterns.map((p) => {
    const fl = (p.flags || '').includes('i') ? 'i' : '';
    return { p, rx: new RegExp(p.regex, fl), ex: p.exclude ? new RegExp(p.exclude, fl) : null };
  }) };
}

function* units(text, split) {
  for (const line of text.split(/\r?\n/)) {
    const s = line.trim(); if (!s) continue;
    if (s.startsWith('|')) { if (/^[|\s:\-]+$/.test(s)) continue; yield ['table_row', s]; }
    else for (const sent of s.split(split)) if (sent.trim()) yield ['sentence', sent.trim()];
  }
}

// classify_obligation mirror for compiled items: INFO -> ignore; declared HUMAN_PREF (non-RED) -> OWNER; else AGENT/NOW.
function classifyCompiled(sev, declared) {
  if (declared === 'HUMAN_PREF' && sev !== 'RED') return { owner_class: 'OWNER', actionability: 'HUMAN_PREF' };
  if (sev === 'INFO' || declared === 'INFO') return { owner_class: 'AGENT', actionability: 'INFO' };
  return { owner_class: 'AGENT', actionability: 'NOW' };
}

function compileTurn(text, pats) {
  const found = new Map();
  if (typeof text !== 'string' || !text.trim()) return [];
  for (const [scope, unit] of units(text, pats.split)) {
    if (unit.length > MAX_LEN || WISH_RE.test(unit)) continue;
    for (const { p, rx, ex } of pats.list) {
      if (p.scope !== scope || !rx.test(unit) || (ex && ex.test(unit))) continue;
      if (p.frame && !FRAME_RE.test(unit)) break;
      if (scope === 'sentence' && unit.split(/\s+/).filter(Boolean).length < MIN_SUBJECT_WORDS) break;
      const cell = scope === 'table_row' ? unit.replace(/^\||\|$/g, '').split('|').map((c) => c.trim()).filter(Boolean).join(' ') : unit;
      const id = obligationId(cell);
      if (!found.has(id)) {
        const cls = classifyCompiled(p.severity, p.declared_actionability || 'NOW');
        found.set(id, Object.assign({ id, text: cell, source: p.source, severity: p.severity,
          next_action: p.next_action.replace('{text}', cell), open: true }, cls));
      }
      break;
    }
  }
  return Array.from(found.values());
}

// ---- evaluate -----------------------------------------------------------------
function digestOf(open) {
  const rows = open.map((o) => `${o.id}:${o.actionability}:${o.severity}`).sort().join('|');
  return crypto.createHash('sha1').update(rows).digest('hex').slice(0, 12);
}

/**
 * @returns {{verdict:string, ob:object|null, package:string[], digest:string, nowCount:number,
 *            maxSev:number, open:object[], goalBound:boolean, why:string}}
 */
function evaluate(data, opts) {
  opts = opts || {};
  const sid = data.session_id;
  const out = { verdict: 'STOP_UNKNOWN', ob: null, package: [], digest: '', nowCount: 0, maxSev: 0,
    open: [], goalBound: false, why: '' };
  const root = goalsRoot();
  const all = new Map();       // id -> obligation (ledger/goal state wins over pattern re-derivation)
  let unknown = false; let readSomething = false;

  // (b) goal log when goal-bound, else the session ledger
  let logName = null;
  try {
    const gb = require('./goal_binding.js');
    const rec = gb.readBinding(sid);
    if (rec && rec.goal) { logName = String(rec.goal); out.goalBound = true; }
  } catch (e) { /* unreadable binding == not bound; the ledger below still answers */ }
  if (!logName) logName = scopeId(sid);
  if (logName) {
    for (const rd of repoDirs(root)) {
      const r = readEvents(path.join(rd, logName));
      if (!r.ok) { unknown = true; continue; }
      if (r.absent) continue;
      readSomething = true;
      for (const [id, o] of foldObligations(r.events)) all.set(id, o);
    }
  }

  // (b2) backstop on the last assistant turn
  const tp = data.transcript_path;
  if (tp) {
    try {
      const text = lastTurnText(String(tp));
      readSomething = true;
      for (const o of compileTurn(text, loadPatterns())) if (!all.has(o.id)) all.set(o.id, o);
    } catch (e) { unknown = true; }
  } else if (!readSomething) unknown = true;

  const open = Array.from(all.values()).filter((o) => o.open && o.actionability !== 'WAIVED'
    && o.actionability !== 'INFO' && !(o.severity === 'INFO' && o.owner_class === 'AGENT'));
  out.open = open;
  out.digest = digestOf(open);
  const now = open.filter((o) => o.owner_class === 'AGENT' && o.actionability === 'NOW');
  out.nowCount = now.length;
  out.maxSev = open.reduce((m, o) => Math.max(m, SEV_RANK[o.severity] || 0), 0);

  if (now.length) {                                  // (d)
    now.sort((a, b) => (SEV_RANK[b.severity] || 0) - (SEV_RANK[a.severity] || 0));
    out.ob = now[0];
    out.verdict = 'CONTINUE_' + (REASON[now[0].source] || 'OPEN_OBLIGATION');
    out.why = `${now.length} open AGENT/NOW; next ${now[0].id}`;
    return out;
  }
  if (unknown) { out.verdict = 'STOP_UNKNOWN'; out.why = 'obligation state unreadable'; return out; }   // (c)
  if (open.some((o) => o.actionability === 'AFTER_DEP')) { out.verdict = 'STOP_SCHEDULED_WAIT'; out.why = 'AFTER_DEP open'; return out; }
  const owner = open.filter((o) => o.owner_class === 'OWNER');
  if (owner.length) {                                // (e)
    const res = owner.some((o) => o.actionability === 'RESOURCE');
    out.verdict = res ? 'STOP_RESOURCE_BLOCKED' : 'STOP_HUMAN_GATE';
    out.ob = owner[0];
    out.package = [
      'Proven green: no AGENT/NOW obligation remains open.',
      `Remains (${owner.length}, Owner-only): ${owner.map((o) => o.id).join(', ')}`,
      `Subjective/external: ${owner[0].text.slice(0, 160)}`,
      `Decision needed (yes/no): ${owner[0].next_action.slice(0, 160)}`,
    ];
    out.why = `${owner.length} Owner-only open`;
    return out;
  }
  out.verdict = 'STOP_COMPLETE'; out.why = 'no open obligation';   // (f)
  return out;
}

// ---- diagnosis obligation (STALLED) -------------------------------------------
function canon(v) {
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map((k) => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}';
  return JSON.stringify(v);
}

function recordDiagnosis(sid, text, nextAction) {
  try {
    const root = goalsRoot(); const name = scopeId(sid); if (!name) return false;
    let dir = null;
    for (const rd of repoDirs(root)) { const d = path.join(rd, name); if (fs.existsSync(d)) { dir = d; break; } }
    if (!dir) dir = path.join(root, 'e0c0e0c0e0c0', name);   // no repo id without git: neutral hex id
    fs.mkdirSync(dir, { recursive: true });
    const r = readEvents(dir); if (!r.ok) return false;
    const id = obligationId(text);
    if (foldObligations(r.events).get(id) && foldObligations(r.events).get(id).open) return true;
    let prev = '0'.repeat(64);
    if (r.events.length) prev = r.events[r.events.length - 1].digest || prev;
    const body = { seq: r.events.length + 1, type: 'obligation.accepted', ts: new Date().toISOString(), actor: 'ewc-stop-gate',
      data: { id, plane: 'OUTCOME', text, done_gate: '', gate_pin: [], revision: 'session', gate_class: '', scope: 'SESSION',
        source: 'stalled_diagnosis', severity: 'RED', actionability: 'NOW', owner_class: 'AGENT', next_action: nextAction },
      prev_digest: prev };
    body.digest = crypto.createHash('sha256').update(canon(body), 'utf8').digest('hex');
    const target = path.join(dir, String(body.seq).padStart(6, '0') + '.json');
    const tmp = path.join(dir, '.tmp-' + crypto.randomBytes(8).toString('hex'));
    fs.writeFileSync(tmp, JSON.stringify(body, null, 2), 'utf8');
    try { fs.linkSync(tmp, target); } finally { try { fs.unlinkSync(tmp); } catch (e) { /* harmless leftover */ } }
    return true;
  } catch (e) { return false; }
}

module.exports = { evaluate, compileTurn, loadPatterns, obligationId, scopeId, digestOf, recordDiagnosis, readEvents, foldObligations, SEV_RANK, goalsRoot };
