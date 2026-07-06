#!/usr/bin/env node
'use strict';
/**
 * session-title-lib.js — readable /resume titles for the LIVE forward path.
 *
 * The native /resume picker renders the LATEST `{"type":"custom-title", ...}`
 * record in `<uuid>.jsonl`; an un-titled session falls back to the 8-char UUID
 * hash. hooks/mark-live-session.js is the ONLY per-Stop writer of custom-title,
 * and it historically wrote the hash as the base -> the picker showed hashes.
 *
 * This lib supplies the COMPLIANT base title for that forward path, following
 * PR-TRANSCRIPT-RENAME-SAFETY-001 (sealed 2026-07-06): the name source is the
 * session's own CLEAN Claude-generated ai-title
 * ({"type":"ai-title","aiTitle":"..."}) — NOT the raw first prompt (which leaks
 * sub-agent boilerplate). Byte-for-byte consistent with tools/rename_sessions.py
 * (the retroactive authority): same 50-char cap, same "…" ellipsis, no repo
 * prefix (the picker already groups per project).
 *
 * mark-live only ever titles the OWN live session, so no sub-session /
 * mislocated-copy exclusion is needed here (those are a BULK-rename concern that
 * rename_sessions.py owns). When no ai-title exists yet (early in a new session)
 * the base degrades to the hash; a later Stop self-heals it once the ai-title
 * lands.
 *
 * Pure + dependency-free (fs only). Every function fails soft: any error or
 * missing signal returns null / the hash, never throws.
 */
const fs = require('fs');

const HEAD_BYTES = 128 * 1024;      // bounded head scan for the ai-title record
const TAIL_BYTES = 64 * 1024;       // bounded tail scan for the latest custom-title
const MAX_LABEL = 50;               // matches rename_sessions.py MAX_LABEL
const LIVE_PREFIX = '⚡ ';           // the mark-live voltage marker
const HASH_TITLE_RE = /^[0-9a-fA-F]{8}$/;
const FULL_UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

// A custom-title that is empty / a bare 8-hex hash / a full UUID is the
// machine fallback the picker shows un-titled — never a human/Ctrl+R name.
function isHashTitle(s) {
  const b = (s || '').trim();
  if (!b) return true;
  return HASH_TITLE_RE.test(b) || FULL_UUID_RE.test(b);
}

function hashFallback(sessionId) {
  return sessionId ? String(sessionId).slice(0, 8) : 'session';
}

// The session's clean Claude-generated ai-title, or '' if none yet.
function readAiTitle(filePath) {
  let buf;
  try {
    const fd = fs.openSync(filePath, 'r');
    try {
      const stat = fs.fstatSync(fd);
      const len = Math.min(stat.size, HEAD_BYTES);
      if (len <= 0) return '';
      buf = Buffer.alloc(len);
      fs.readSync(fd, buf, 0, len, 0);
    } finally { fs.closeSync(fd); }
  } catch { return ''; }
  for (const line of buf.toString('utf-8').split('\n')) {
    if (line.indexOf('"ai-title"') === -1) continue;
    let o;
    try { o = JSON.parse(line.trim()); } catch { continue; }
    if (o && o.type === 'ai-title' && typeof o.aiTitle === 'string' && o.aiTitle.trim()) {
      return o.aiTitle.trim();
    }
  }
  return '';
}

// Truncate to <=MAX_LABEL, appending "…" when cut — identical to
// rename_sessions.py make_title (repo_prefix off).
function truncateTitle(s, n = MAX_LABEL) {
  const label = (s || '').trim();
  if (label.length <= n) return label;
  return label.slice(0, n - 1).replace(/\s+$/, '') + '…';
}

/**
 * The COMPLIANT base title for the forward path: the clean ai-title (truncated),
 * else the hash fallback. Never blank, never raw first-prompt.
 */
function deriveReadableTitle(filePath, sessionId) {
  const ai = truncateTitle(readAiTitle(filePath));
  return ai || hashFallback(sessionId);
}

// The effective state of the LATEST custom-title record (what the picker shows),
// or null if the session has none. { rawTitle, baseTitle, hasPrefix }.
function lastCustomTitle(filePath) {
  let stat;
  try { stat = fs.statSync(filePath); } catch { return null; }
  const start = Math.max(0, stat.size - TAIL_BYTES);
  const length = stat.size - start;
  if (length <= 0) return null;
  let buf;
  try {
    const fd = fs.openSync(filePath, 'r');
    try { buf = Buffer.alloc(length); fs.readSync(fd, buf, 0, length, start); }
    finally { fs.closeSync(fd); }
  } catch { return null; }
  const lines = buf.toString('utf-8').split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    let obj;
    try { obj = JSON.parse(line); } catch { continue; }
    if (obj && obj.type === 'custom-title' && typeof obj.customTitle === 'string') {
      const raw = obj.customTitle;
      const has = raw.startsWith(LIVE_PREFIX);
      return { rawTitle: raw, baseTitle: has ? raw.slice(LIVE_PREFIX.length) : raw, hasPrefix: has };
    }
  }
  return null;
}

module.exports = {
  isHashTitle,
  hashFallback,
  readAiTitle,
  truncateTitle,
  deriveReadableTitle,
  lastCustomTitle,
  MAX_LABEL,
  LIVE_PREFIX,
};
