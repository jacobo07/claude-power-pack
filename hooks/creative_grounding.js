#!/usr/bin/env node
/**
 * creative_grounding.js -- UserPromptSubmit, ADVISORY, fail-open.
 *
 * Why (2026-10-13, Owner): a VLCE ad and its Meta copy were written with no retrieval at all, although AKOS
 * (30,535 units) and 01_Datasets (121k chunks) held directly relevant material. Every knowledge system was
 * pull-only, so nothing reached for it. This hook makes the reach automatic: when a prompt asks for creative
 * work (ad, brief, copy, hook, headline, script, image prompt), it queries the AKOS search index and injects
 * the top hits WITH CITABLE IDS, plus the instruction to cite them and write an evidence pack.
 *
 * In-process on purpose: node:sqlite reads the FTS5 index in ~0.5 s. A python child costs 2-4 s on this host
 * and the UserPromptSubmit chain deadline is 3000 ms, so a python hook would be abandoned silently.
 * Query expansion reads the SAME lexicon as akos.retrieval.search (akos/retrieval/lexicon.json).
 *
 * Silence is valid: a non-creative prompt, a missing index, an error or a timeout emits nothing and exits 0.
 * Kill switch: AKOS_GROUNDING=0. Spec: AKOS docs/specs/akos-retrieval-and-autonomous-grounding.md.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const AKOS_ROOT = process.env.AKOS_ROOT || 'C:/Users/User/Desktop/Cursor Projects/AKOS';
const INDEX = process.env.AKOS_INDEX || path.join(AKOS_ROOT, 'datasets', 'indexes', 'akos_search.sqlite');
const LEXICON = path.join(AKOS_ROOT, 'akos', 'retrieval', 'lexicon.json');
const TOP_K = 8;
const MAX_PER_ORIGIN = 2;
const SNIPPET = 220;

// Creative intent: a creative NOUN (what is being made) AND, unless the noun is unambiguous, a making VERB.
const STRONG = /\b(anuncios?|creatividad(es)?|ad\s*copy|ad\s*creatives?|copys?\b|copywriting|titulares?|headlines?|ganchos?|hooks?\s+(for|para)|guion(es)?\s+(de|para)\s+(anuncio|video|reel)|ugc\s+script|prompt\s+de\s+imagen|image\s+prompt|brief\s+creativo|creative\s+brief|visual\s+lab\s+(slot|brief|round|ronda))\b/i;
const NOUN = /\b(ads?|advert|creatives?|brief|campa[nñ]a|campaign|landing|slogan|claim|tagline|banner|post\s+de\s+instagram|reel)\b/i;
const VERB = /\b(haz|hazme|crea|cr[eé]ame|genera|escribe|redacta|dise[nñ]a|mejora|make|create|generate|write|draft|design|improve|rework|rehaz)\b/i;
// Prompts ABOUT the pipeline, not creative work: code, hooks, gates, tests.
const NOT_CREATIVE = /\b(hook\s+(de|del|que|in|for\s+the)\s+(power\s+pack|dispatcher|chain)|pytest|stack\s*trace|traceback|regex)\b/i;

function fold(s) {
  return s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function isCreative(prompt) {
  if (!prompt || NOT_CREATIVE.test(prompt)) return false;
  if (STRONG.test(prompt)) return true;
  return NOUN.test(prompt) && VERB.test(prompt);
}

function loadLexicon() {
  const d = JSON.parse(fs.readFileSync(LEXICON, 'utf8'));
  const groups = new Map();
  for (const g of d.groups) {
    const fg = g.map(fold);
    for (const t of fg) {
      const set = groups.get(t) || new Set();
      fg.forEach((x) => set.add(x));
      groups.set(t, set);
    }
  }
  return { groups, stop: new Set(d.stopwords.map(fold)), amb: new Set((d.ambiguous || []).map(fold)) };
}

// Mirrors akos.retrieval.search.concepts(): one term set per query word; an ambiguous word is represented
// only by the other terms of its group. Parity is pinned by AKOS akos/tests/test_retrieval_parity.py.
function concepts(prompt, lex) {
  const out = [];
  for (const w of fold(prompt).match(/[a-z0-9]+/g) || []) {
    if (w.length <= 2 || lex.stop.has(w)) continue;
    let ts = new Set([...(lex.groups.get(w) || []), w]);
    if (lex.amb.has(w)) {
      const keep = new Set([...ts].filter((t) => !lex.amb.has(t)));
      if (keep.size) ts = keep;
    }
    const sub = (a, b) => [...a].every((x) => b.has(x));
    if (!out.some((c) => sub(ts, c) || sub(c, ts))) out.push(ts);
  }
  return out.slice(0, 20);
}

function expand(prompt, lex) {
  const flat = [];
  for (const c of concepts(prompt, lex)) for (const t of [...c].sort()) if (!flat.includes(t)) flat.push(t);
  return flat;
}

function coverage(text, cs) {
  const toks = new Set(fold(text).match(/[a-z0-9]+/g) || []);
  let n = 0;
  for (const c of cs) {
    if ([...c].some((t) => toks.has(t) || (t.length >= 4 && [...toks].some((x) => x.startsWith(t))))) n += 1;
  }
  return n;
}

function search(prompt) {
  const { DatabaseSync } = require('node:sqlite');
  const lex = loadLexicon();
  const cs = concepts(prompt, lex);
  const terms = expand(prompt, lex);
  if (!terms.length) return [];
  const q = terms.map((t) => (t.length >= 4 ? `"${t}"*` : `"${t}"`)).join(' OR ');
  const db = new DatabaseSync(INDEX, { readOnly: true });
  try {
    const rows = db.prepare(
      "SELECT sid, origin, tier, confidence, snippet(chunks, 6, '', '', ' … ', 32) AS snip, " +
      "bm25(chunks, 0, 0, 0, 0, 0, 3.0, 1.0) AS bm, origin || ' ' || content AS txt FROM chunks WHERE chunks MATCH ? " +
      'ORDER BY bm LIMIT ?').all(q, TOP_K * 8);
    const boost = { 1: 2.0, 2: 1.5, 3: 1.0 };
    rows.forEach((r) => {
      r.score = -r.bm * (boost[r.tier] || 1) * (0.5 + Number(r.confidence));
      r.coverage = coverage(r.txt, cs);
      delete r.txt;
    });
    rows.sort((a, b) => (b.coverage - a.coverage) || (b.score - a.score));
    const per = new Map();
    const hits = [];
    for (const r of rows) {
      const n = per.get(r.origin) || 0;
      if (n >= MAX_PER_ORIGIN) continue;
      per.set(r.origin, n + 1);
      hits.push(r);
      if (hits.length >= TOP_K) break;
    }
    return hits;
  } finally {
    db.close();
  }
}

function render(hits) {
  const lines = [
    'AKOS CREATIVE GROUNDING (auto): this prompt asks for creative work. Ground it in retrieval BEFORE writing',
    'any brief, prompt, hook or copy. Cite the ids you rely on; an uncited creative choice is an unsupported claim.',
    'Full pack (all sources, counts, absences): python "' + AKOS_ROOT + '/run_akos.py" evidence --task "<task>" --out <file>',
    'KobiiSpy is NOT in this index (connector pending): query it separately and report the measured count.',
    '',
  ];
  hits.forEach((h, i) => {
    lines.push(`${i + 1}. ${h.sid}  (${String(h.origin).slice(0, 80)})`);
    lines.push('   ' + String(h.snip).replace(/\s+/g, ' ').slice(0, SNIPPET));
  });
  return lines.join('\n');
}

/** The hook's whole decision for one prompt: an output object, or null for silence. Never throws. */
function run(data) {
  try {
    if (process.env.AKOS_GROUNDING === '0') return null;
    const prompt = (data && data.prompt) || '';
    if (!isCreative(prompt)) return null;
    if (!fs.existsSync(INDEX)) return null;  // no index: nothing to ground with; never invent
    const hits = search(prompt);
    if (!hits.length) return null;
    return { hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: render(hits) } };
  } catch (_e) {
    return null;  // fail-open: an advisory must never break the prompt
  }
}

// Registered IN-PROCESS in hook-dispatcher.js EVENT_MAP 'UserPromptSubmit-default' (require + run()), not as a
// spawned chain member: measured 2026-10-13 on a loaded host, the chain's critical lane alone used 11-13 s of
// its 3000 ms deadline and the advisory pool was never spawned, so a spawned grounding hook reached nobody.
// The CLI path below is kept for tests and manual use.
if (require.main === module) {
  let data = {};
  try { data = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_e) { data = {}; }
  const out = run(data);
  if (out) process.stdout.write(JSON.stringify(out));
  process.exit(0);
}

module.exports = { run, isCreative, concepts, expand, coverage, loadLexicon, search, render };
