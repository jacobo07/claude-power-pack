#!/usr/bin/env node
'use strict';
/**
 * test_session_naming.js — V-gates for the LIVE forward-path readable title
 * (session-title-lib.js + mark-live-session.js base resolution).
 *
 * Scope: the ai-title-based forward path ONLY. The RETROACTIVE path is owned by
 * tools/rename_sessions.py + tools/test_rename_sessions.py (do not duplicate).
 *
 * Hermetic: throwaway .jsonl fixtures under a temp dir, removed on exit. AAA.
 *   node tools/test_session_naming.js   ->  exit 0 iff all V-gates pass
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const lib = require('../hooks/session-title-lib.js');

let passes = 0, fails = 0;
const _ok = (g, e) => { passes++; console.log(`  PASS ${g}  ${e}`); };
const _fail = (g, e) => { fails++; console.log(`  FAIL ${g}  ${e}`); };

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'pp-sessname-'));
const fixture = (name, lines) => {
  const p = path.join(TMP, name);
  fs.writeFileSync(p, lines.map(o => JSON.stringify(o)).join('\n') + '\n', 'utf-8');
  return p;
};
// Replicates hooks/mark-live-session.js markOwnSessionLive base resolution.
function markBase(fp, sid) {
  const last = lib.lastCustomTitle(fp);
  let base = last && last.baseTitle;
  if (!base || lib.isHashTitle(base)) base = lib.deriveReadableTitle(fp, sid);
  if (last && last.hasPrefix && last.baseTitle === base) return null; // idempotent
  return '⚡ ' + base;
}
const appendTitle = (fp, sid, title) =>
  fs.appendFileSync(fp, JSON.stringify({ type: 'custom-title', customTitle: title, sessionId: sid }) + '\n');

try {
  // V-AI-TITLE-SOURCE: the base is the clean ai-title, not the raw first prompt.
  {
    const sid = 'aaaaaaaa-1111-2222-3333-444444444444';
    const fp = fixture(sid + '.jsonl', [
      { type: 'user', message: { role: 'user', content: 'Staged Python diff to generate ONE happy-path test scaffold boilerplate' } },
      { type: 'ai-title', aiTitle: 'Add happy-path test scaffold' },
    ]);
    const t = lib.deriveReadableTitle(fp, sid);
    if (t === 'Add happy-path test scaffold') _ok('V-AI-TITLE-SOURCE', `"${t}"`);
    else _fail('V-AI-TITLE-SOURCE', `got "${t}" (should be the ai-title, not the prompt)`);
  }

  // V-NO-BOILERPLATE: even a sub-agent-shaped first prompt cannot leak into the
  // title — the ai-title wins outright (the pollution bug this reworks fixes).
  {
    const sid = 'bbbbbbbb-1111-2222-3333-444444444444';
    const fp = fixture(sid + '.jsonl', [
      { type: 'user', message: { role: 'user', content: 'You are an expert and insightful researcher. Contents from a SERP search:' } },
      { type: 'ai-title', aiTitle: 'Market research summary' },
    ]);
    const t = lib.deriveReadableTitle(fp, sid);
    if (!/researcher|SERP/i.test(t) && t === 'Market research summary') _ok('V-NO-BOILERPLATE', `"${t}"`);
    else _fail('V-NO-BOILERPLATE', `boilerplate leaked: "${t}"`);
  }

  // V-TRUNCATE: >50-char ai-title -> truncated with "…" (byte-match rename_sessions.py).
  {
    const sid = 'cccccccc-1111-2222-3333-444444444444';
    const longAi = 'This ai-title is deliberately much longer than fifty characters to force truncation';
    const fp = fixture(sid + '.jsonl', [{ type: 'ai-title', aiTitle: longAi }]);
    const t = lib.deriveReadableTitle(fp, sid);
    if (t.length <= lib.MAX_LABEL && t.endsWith('…')) _ok('V-TRUNCATE', `"${t}" (${t.length} chars)`);
    else _fail('V-TRUNCATE', `len=${t.length} ends…=${t.endsWith('…')} -> "${t}"`);
  }

  // V-HASH-FALLBACK: no ai-title yet -> degrade to the 8-char hash, never blank.
  {
    const sid = 'dddddddd-1111-2222-3333-444444444444';
    const fp = fixture(sid + '.jsonl', [{ type: 'user', message: { role: 'user', content: 'no ai title present yet' } }]);
    const t = lib.deriveReadableTitle(fp, sid);
    if (t === 'dddddddd') _ok('V-HASH-FALLBACK', `degraded to hash "${t}"`);
    else _fail('V-HASH-FALLBACK', `expected hash, got "${t}"`);
  }

  // V-SELF-HEAL: a legacy "⚡ <hash>" title upgrades to "⚡ <ai-title>" once the
  // ai-title lands, then is idempotent on the next Stop.
  {
    const sid = 'eeeeeeee-1111-2222-3333-444444444444';
    const hash = sid.slice(0, 8);
    const fp = fixture(sid + '.jsonl', [
      { type: 'ai-title', aiTitle: 'Real session topic' },
      { type: 'custom-title', customTitle: '⚡ ' + hash, sessionId: sid },   // legacy hash marker
    ]);
    const first = markBase(fp, sid);
    if (first === '⚡ Real session topic') {
      appendTitle(fp, sid, first);
      const second = markBase(fp, sid);   // must be a no-op now
      if (second === null) _ok('V-SELF-HEAL', `⚡hash -> "${first}", 2nd Stop idempotent`);
      else _fail('V-SELF-HEAL', `not idempotent: 2nd="${second}"`);
    } else _fail('V-SELF-HEAL', `no upgrade: "${first}"`);
  }

  // V-RESPECT-CTRLR: a real human Ctrl+R name (non-hash) is never overwritten.
  {
    const sid = 'ffffffff-1111-2222-3333-444444444444';
    const fp = fixture(sid + '.jsonl', [
      { type: 'ai-title', aiTitle: 'auto generated' },
      { type: 'custom-title', customTitle: 'My Hand Named Session', sessionId: sid },
    ]);
    const b = markBase(fp, sid);
    if (b === '⚡ My Hand Named Session') _ok('V-RESPECT-CTRLR', `kept human name: "${b}"`);
    else _fail('V-RESPECT-CTRLR', `clobbered Ctrl+R name -> "${b}"`);
  }
} finally {
  try { fs.rmSync(TMP, { recursive: true, force: true }); } catch { /* best effort */ }
}

console.log(`\nSESSION_NAMING_PASS=${passes}/${passes + fails}  threshold=${passes + fails}/${passes + fails}`);
process.exit(fails === 0 ? 0 : 1);
