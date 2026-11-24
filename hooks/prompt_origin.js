'use strict';
/**
 * prompt_origin.js -- which part of a UserPromptSubmit prompt the Owner wrote (JS twin of
 * modules/gsd_x/prompt_origin.py, for hooks that run IN-PROCESS in the dispatcher and cannot afford a python child).
 *
 * Subagent hand-backs, compaction summaries, task notifications and skill bodies reach UserPromptSubmit without the
 * Owner typing them (measured 2026-11-22: 53/106 live design routes, efaae877). Classify the Owner's words only.
 * Parity with the python rule is pinned by tools/test_prompt_origin_parity.py (V-POP-*): change both or neither.
 */
const MACHINE_PREFIXES = [
  'another claude session sent a message',
  // the hand-back as the hook RECEIVES it (live capture 2026-11-22); the line above is transcript-only
  '<agent-message',
  'this session is being continued from a previous conversation',
  '<task-notification>',
  'base directory for this skill',
  'userpromptsubmit hook additional context',
  'caveat: the messages below were generated',
];
const LEADING_REMINDERS = /^\s*(?:<system-reminder[^>]*>[\s\S]*?<\/system-reminder>\s*)+/;

/** The Owner-written part of a prompt, or '' when the whole turn is machine-originated. */
function ownerText(prompt) {
  if (typeof prompt !== 'string') return '';
  const rest = prompt.replace(LEADING_REMINDERS, '').replace(/^[ \t\r\n"']+/, '');
  const low = rest.slice(0, 200).toLowerCase();
  if (!rest || MACHINE_PREFIXES.some((p) => low.startsWith(p))) return '';
  return rest;
}

// ---------------------------------------------------------------- mentions vs requests (T3-CT W3)
// Twin of prompt_origin.py mention_reason/live_matches: a match is dropped when quoted, inside talk about routing, or
// a bare item of an unrelated list. Constants and order of the checks are the python ones; V-POP-MENTION pins them.
const QUOTES = { '"': '"', "'": "'", '`': '`', '“': '”', '‘': '’', '«': '»' };
const META_WINDOW = 200;
const META_MIN = 2;
const META_RX = new RegExp(
  'false[ -]positives?|falsos? positivos?|\\bmatched\\b|\\bdetector\\b|design[ -]rout(?:e|er|ing)|\\brouters?\\b'
  + '|\\bincidental(?:ly)?\\b|\\bnouns?\\b|\\bverbs?\\b|\\bclassifier\\b|\\btriggered\\b|\\bfired\\b', 'gi');
const LIST_SEP = /[;,\n|•·]/;
const LIST_FILLER = /^(?:[-*+>\s\d.)]|and\b|or\b|y\b|o\b|e\.g\.|etc\.?|the\b|a\b|an\b|un[ao]?\b|el\b|la\b)+/i;
const LIST_SPAN = 400;
const SHORT_ITEM = 4;

function words(s) { return s.match(/[\p{L}\p{N}]+/gu) || []; }

function quoted(text, start, end) {
  const before = start > 0 ? text[start - 1] : '';
  const after = end < text.length ? text[end] : '';
  return Object.prototype.hasOwnProperty.call(QUOTES, before) && after === QUOTES[before];
}

function metaSignals(text, start, end) {
  const win = text.slice(Math.max(0, start - META_WINDOW), end + META_WINDOW);
  const seen = new Set();
  for (const m of win.matchAll(META_RX)) seen.add(signalFamily(m[0]));
  return [...seen].sort();
}

/** One concept, one signal: lower-case, '-' as ' ', a plural 's' dropped (review of W3, MEDIUM-1). */
function signalFamily(s) {
  const t = s.toLowerCase().split('-').join(' ');
  return t.endsWith('s') ? t.slice(0, -1) : t;
}

function bare(item, match, requestRx) {
  let rest = item.replace(match, ' ').trim();
  rest = rest.replace(LIST_FILLER, '').trim().replace(/^[ :.!?]+|[ :.!?]+$/g, '');
  // "write ads, emails, blog posts": an item that also holds a request word heads a request, it is not a list item.
  if (requestRx && new RegExp(requestRx.source, requestRx.flags.replace('g', '')).test(rest)) return false;
  return words(rest).length <= 1;
}

function listItem(text, start, end, sameKind, requestRx) {
  const lo = Math.max(0, start - LIST_SPAN);
  const hi = Math.min(text.length, end + LIST_SPAN);
  const left = text.slice(lo, start).split(LIST_SEP);
  const right = text.slice(end, hi).split(LIST_SEP);
  const item = left[left.length - 1] + text.slice(start, end) + right[0];
  if (!bare(item, text.slice(start, end), requestRx)) return false;
  // A line ending in ':' heads the list ("Pages:"); it is not one of its items.
  const keep = (s) => s && !s.endsWith(':');
  const l = left.slice(0, -1).reverse().map((s) => s.trim()).filter(keep).slice(0, 2);
  const r = right.slice(1).map((s) => s.trim()).filter(keep).slice(0, 2);
  const sib = l.concat(r).filter((s) => words(s).length <= SHORT_ITEM);
  if (sib.length < 2) return false;
  if (!sameKind) return true;
  const kin = sib.filter((s) => new RegExp(sameKind.source, sameKind.flags.replace('g', '')).test(s)).length;
  return kin * 2 < sib.length;
}

/** '' when the span reads as a request; else why it is a mention: quoted | meta | list. */
function mentionReason(text, start, end, sameKind, requestRx) {
  if (quoted(text, start, end)) return 'quoted';
  if (metaSignals(text, start, end).length >= META_MIN) return 'meta';
  if (listItem(text, start, end, sameKind, requestRx)) return 'list';
  return '';
}

/** The matches of rx in text that are not mentions. rx may lack the g flag. */
function liveMatches(rx, text, sameKind, requestRx) {
  const g = new RegExp(rx.source, rx.flags.includes('g') ? rx.flags : rx.flags + 'g');
  return [...String(text || '').matchAll(g)]
    .filter((m) => !mentionReason(text, m.index, m.index + m[0].length, sameKind, requestRx));
}

module.exports = { ownerText, MACHINE_PREFIXES, mentionReason, liveMatches, metaSignals };

if (require.main === module) {
  // parity CLI: stdin JSON list of prompts -> stdout JSON list of ownerText results;
  // or {"mentions": [[text, start, end, sameKindSource|null], ...]} -> list of mentionReason results.
  const fs = require('fs');
  const input = JSON.parse(fs.readFileSync(0, 'utf8') || '[]');
  if (Array.isArray(input)) process.stdout.write(JSON.stringify(input.map(ownerText)));
  else process.stdout.write(JSON.stringify(input.mentions.map(([t, s, e, k]) => mentionReason(t, s, e, k ? new RegExp(k, 'i') : null))));
}
