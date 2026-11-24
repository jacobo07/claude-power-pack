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
// Bare "copy" is NOT strong (T3-CT W3): it is an engineering verb and noun too ("Cognitive Copy-on-Write",
// "Zero-Copy", "do not let agents copy the institution" fired grounding on a 103k amendment). It is a NOUN, so it
// needs a making verb beside it ("escribe el copy"), and never inside a hyphenated compound.
const STRONG = /\b(anuncios?|creatividad(es)?|ad\s*copy|ad\s*creatives?|copywriting|titulares?|headlines?|ganchos?|hooks?\s+(for|para)|guion(es)?\s+(de|para)\s+(anuncio|video|reel)|ugc\s+script|prompt\s+de\s+imagen|image\s+prompt|brief\s+creativo|creative\s+brief|visual\s+lab\s+(slot|brief|round|ronda))\b/i;
const NOUN = /\b(ads?|adverts?|creatives?|briefs?|campa[nñ]as?|campaigns?|landings?|slogans?|claims?|taglines?|banners?|post\s+de\s+instagram|reels?|(?<!-)copys?(?!-))\b/i;
const VERB = /\b(haz|hazme|crea|cr[eé]ame|genera|escribe|redacta|dise[nñ]a|mejora|make|create|generate|write|draft|design|improve|rework|rehaz)\b/i;
// Prompts ABOUT the pipeline, not creative work: code, hooks, gates, tests.
const NOT_CREATIVE = /\b(hook\s+(de|del|que|in|for\s+the)\s+(power\s+pack|dispatcher|chain)|pytest|stack\s*trace|traceback|regex)\b/i;

function fold(s) {
  return s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

// T3-CT W3 (FP-AKOS-GROUNDING-NOUN-VERB-FAR-APART): NOUN and VERB anywhere in the prompt made every long text
// creative (103k amendment: "a brief genuine preference" + "Do not create another loop engine", 50 KB apart). Now the
// verb must govern the noun: same line, at most PAIR_WINDOW chars apart, not negated, and neither one a mention
// (quoted, router talk, bare item of an unrelated list; shared rule, prompt_origin.js).
const PAIR_WINDOW = 80;
const HEADER_BLOCK = 600;   // chars a "<verb> ...:" header line governs below it, cut at the first blank line
const NEGATION = /\b(not|don'?t|never|no|nunca|sin|without|ni)\s+(\w+\s+)?$/i;

function negated(text, at) {
  return NEGATION.test(text.slice(Math.max(0, at - 24), at));
}

function isCreative(prompt) {
  if (!prompt || NOT_CREATIVE.test(prompt)) return false;
  const { liveMatches } = require('./prompt_origin');
  // A list of creative things ("ads, banners, reels") is still a request: same kind = any creative noun.
  const kind = new RegExp(STRONG.source + '|' + NOUN.source, 'i');
  if (liveMatches(STRONG, prompt, kind).length) return true;
  // "make ads, banners, reels": the verb's list siblings are creative nouns, so its kind is verb OR creative noun.
  const verbKind = new RegExp(VERB.source + '|' + kind.source, 'i');
  // An item that holds a creative noun beside the verb ("write ads, emails") heads a request, so nouns pass VERB and
  // verbs pass the nouns as the request pattern (review of W3, MEDIUM-3).
  const verbs = liveMatches(VERB, prompt, verbKind, kind).filter((v) => !negated(prompt, v.index));
  if (!verbs.length) return false;
  const nouns = liveMatches(NOUN, prompt, kind, VERB);
  for (const v of verbs) {
    // A verb that heads a list ("Create the following:\n- 3 ads\n- 2 banners") governs the list lines under it, up
    // to the next blank line (review of W3, MEDIUM-2).
    const eol = prompt.indexOf('\n', v.index);
    const header = eol > 0 && prompt.slice(v.index, eol).trimEnd().endsWith(':');
    let blockEnd = -1;
    if (header) {
      const blank = prompt.slice(eol, eol + HEADER_BLOCK).search(/\n[ \t]*\r?\n/);
      blockEnd = blank > 0 ? eol + blank : Math.min(prompt.length, eol + HEADER_BLOCK);
    }
    for (const n of nouns) {
      if (header && n.index > eol && n.index < blockEnd) return true;
      const a = Math.min(n.index, v.index);
      const b = Math.max(n.index + n[0].length, v.index + v[0].length);
      if (b - a <= PAIR_WINDOW && !prompt.slice(a, b).includes('\n')) return true;
    }
  }
  return false;
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
    // The Owner's words only: a subagent hand-back that mentions "hooks for" or "landing" is not a creative request
    // (observed 2026-11-22: ~1 KB of retrieval injected on a hand-back). Shared rule, see prompt_origin.js.
    const prompt = require('./prompt_origin').ownerText((data && data.prompt) || '');
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
