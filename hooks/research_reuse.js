// research_reuse.js -- research reuse + singleflight + negative knowledge (CDC C6).
//
// PreToolUse and PostToolUse on WebSearch|WebFetch (dispatcher chains PreToolUse-Web-default /
// PostToolUse-Web-default). Twin of tools/derivation_store.py: same key, same layout under
// <state>/derivation-store/ (key = sha256(normalized question \0 scope), scope "research").
//   Pre  HIT       fresh stored answer -> additionalContext with its path; DENY the duplicate when the session
//                  is bound to a goal or unit ("bound"), otherwise advisory only.
//        IN-FLIGHT another sid holds a live lock -> deny "subscribe: <lock>". Same sid -> allow.
//        MISS      take the lock (O_EXCL; a lock older than CPP_RESEARCH_LOCK_S, default 300 s, is stale -- the
//                  Post hook never fires on a failed call, so the hook window is shorter than the 30 min store
//                  default), then NEGATIVE KNOWLEDGE: UKDL / CLAE traps lines holding every distinctive query
//                  token -> advisory naming the line and its reopen condition.
//   Post           stores the result (answer file + record) and drops the lock.
// Kill switch CPP_RESEARCH_GATE=off. Any own error -> allow (fail open). Host limit: tool-call edge only.
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const gb = require('./lib/goal_binding');

const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const SCOPE = 'research';
const TTL_S = Number(process.env.CPP_RESEARCH_TTL_S || 24 * 3600);
const LOCK_S = Number(process.env.CPP_RESEARCH_LOCK_S || 300);
const MAX_ANSWER = 200 * 1024;
const KB = path.join(__dirname, '..', 'vault', 'knowledge_base');
const NEG_FILES = process.env.CPP_RESEARCH_NEG_FILES ? process.env.CPP_RESEARCH_NEG_FILES.split(path.delimiter)
  : [path.join(KB, 'clae', 'CLAE_TRAPS.md'), path.join(KB, 'ukdl-universal.md')];
const STOP = new Set(['about', 'with', 'from', 'that', 'this', 'what', 'when', 'where', 'which', 'have', 'does', 'into', 'your']);

const off = () => ['0', 'off', 'false'].includes(String(process.env.CPP_RESEARCH_GATE || '').trim().toLowerCase());
const norm = s => String(s || '').split(/\s+/).filter(Boolean).join(' ').toLowerCase();
const keyOf = q => crypto.createHash('sha256').update([norm(q), SCOPE].join('\0'), 'utf8').digest('hex');
const sdir = () => path.join(gb.stateDir(), 'derivation-store');

function question(ev) {
  const i = (ev && ev.tool_input) || {};
  if (ev.tool_name === 'WebSearch') return i.query ? `search: ${i.query}` : '';
  if (ev.tool_name === 'WebFetch') return i.url ? `fetch: ${i.url}${i.prompt ? ' | ' + i.prompt : ''}` : '';
  return '';
}

function fresh(key, now) {
  const r = gb.readJson(path.join(sdir(), `${key}.json`));
  if (!r || r.status !== 'complete') return null;
  if (now / 1000 - Number(r.created || 0) > Number(r.ttl_s || TTL_S)) return null;
  return fs.existsSync(r.answer || '') ? r : null;
}

function liveLock(key, now) {
  const l = gb.readJson(path.join(sdir(), `${key}.lock`));
  return l && now / 1000 - Number(l.ts || 0) <= LOCK_S ? l : null;
}

function takeLock(key, sid, now) {
  fs.mkdirSync(sdir(), { recursive: true });
  const p = path.join(sdir(), `${key}.lock`);
  for (let n = 0; n < 2; n++) {
    try {
      fs.writeFileSync(p, JSON.stringify({ owner: sid, ts: now / 1000, key, lock: p }), { flag: 'wx' });
      return null;
    } catch (e) {
      if (e.code !== 'EEXIST') return null;                 // cannot lock -> fail open
      const cur = liveLock(key, now);
      if (cur) return cur;
      try { fs.unlinkSync(p); } catch (e2) { /* raced */ }
    }
  }
  return null;
}

function bound(ev, sid) {
  try {
    if (gb.readJson(path.join(gb.stateDir(), 'cognitive-unit', `${sid}.json`))) return true;
    const b = gb.goalBinding(ev, sid, { observe: true });
    return !!(b && b.goal);
  } catch (e) { return false; }
}

function negative(q) {
  const toks = Array.from(new Set(norm(q).replace(/^(search|fetch):/, '').split(/[^a-z0-9]+/)
    .filter(t => t.length >= 4 && !STOP.has(t))));
  if (toks.length < 3) return null;
  for (const f of NEG_FILES) {
    let txt;
    try { txt = fs.readFileSync(f, 'utf8'); } catch (e) { continue; }
    for (const line of txt.split('\n')) {
      const l = line.toLowerCase();
      if (l.length < 400 && toks.every(t => l.includes(t))) {
        const m = /reopen[^.|\n]*/i.exec(line);
        return `${path.basename(f)}: "${line.trim().slice(0, 160)}" -- reopen condition: ${m ? m[0].trim() : 'none recorded; treat as closed unless the premise changed'}`;
      }
    }
  }
  return null;
}

const ctx = (event, msg) => ({ hookSpecificOutput: { hookEventName: event, additionalContext: msg } });
const deny = reason => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: `RESEARCH REUSE -- ${reason}` } });

function pre(ev, now) {
  const sid = ev.session_id, q = question(ev);
  if (!q || !sid || !SID_RE.test(sid)) return null;
  const key = keyOf(q);
  const hit = fresh(key, now);
  if (hit) {
    const msg = `an equivalent derivation is already stored (${key.slice(0, 12)}): read ${hit.answer} (provenance: ${hit.provenance || 'n/a'}).`;
    return bound(ev, sid) ? deny(msg + ' Duplicate research denied for a bound session.') : ctx('PreToolUse', 'RESEARCH REUSE -- ' + msg);
  }
  const cur = liveLock(key, now);
  if (cur && cur.owner !== sid) return deny(`the same research is in flight in session ${cur.owner}; subscribe: ${cur.lock}`);
  if (!cur) { const o = takeLock(key, sid, now); if (o && o.owner !== sid) return deny(`in flight in session ${o.owner}; subscribe: ${o.lock}`); }
  const neg = negative(q);
  return neg ? ctx('PreToolUse', `NEGATIVE KNOWLEDGE -- this question matches a recorded trap/closed finding: ${neg}`) : null;
}

function post(ev, now) {
  const q = question(ev);
  if (!q || !ev.session_id) return null;
  const resp = ev.tool_response;
  let text = typeof resp === 'string' ? resp : JSON.stringify(resp == null ? '' : resp);
  if (!text || text.length < 2) return null;
  const key = keyOf(q);
  const d = sdir();
  fs.mkdirSync(path.join(d, 'answers'), { recursive: true });
  const ans = path.join(d, 'answers', `${key}.txt`);
  fs.writeFileSync(ans, text.slice(0, MAX_ANSWER), 'utf8');
  const rec = { key, status: 'complete', question: norm(q), scope: SCOPE, answer: ans,
    provenance: `${ev.tool_name} by ${ev.session_id}`, created: now / 1000, ttl_s: TTL_S, invalidators: {} };
  fs.writeFileSync(path.join(d, `${key}.json.tmp${process.pid}`), JSON.stringify(rec));
  fs.renameSync(path.join(d, `${key}.json.tmp${process.pid}`), path.join(d, `${key}.json`));
  try { fs.unlinkSync(path.join(d, `${key}.lock`)); } catch (e) { /* none */ }
  return null;
}

function run(ev) {
  try {
    if (off() || !ev) return null;
    const now = Date.now();
    return /^PostToolUse/.test(ev.hook_event_name || '') ? post(ev, now) : pre(ev, now);
  } catch (e) { return null; }
}

if (require.main === module) {
  let raw = '';
  process.stdin.on('data', d => { raw += d; }).on('end', () => {
    let out = null;
    try { out = run(JSON.parse(raw.replace(/^﻿/, ''))); } catch (e) { /* fail open */ }
    process.stdout.write(JSON.stringify(out || {}));
  });
}

module.exports = { run, keyOf, question, negative };
