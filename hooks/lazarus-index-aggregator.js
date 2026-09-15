#!/usr/bin/env node
/**
 * lazarus-index-aggregator.js — SessionStart + Stop hook (BL-NULL-ERROR Step 8).
 *
 * Walks the distributed Lazarus state on disk and writes one consolidated
 * `~/.claude/lazarus/active_panes.json` that aggregates the per-session JSON
 * files, project-level index.json, and the corresponding .jsonl/.jsonl.live
 * presence in ~/.claude/projects/<bucket>/.
 *
 * Purpose: observability only. lazarus-revive.ps1 does the actual recovery;
 * this hook exists so the Owner has one place to look during the 3-pane kill
 * test and ongoing health checks. The Power-Pack does NOT depend on
 * active_panes.json for correctness.
 *
 * Output schema (~/.claude/lazarus/active_panes.json):
 *   {
 *     "generated_at": "<iso>",
 *     "panes": [
 *       {
 *         "session_id":    "<uuid>",
 *         "project_id":    "<lazarus bucket name>",
 *         "cwd":           "<original cwd or null>",
 *         "status":        "live" | "clean_exit" | "crashed" | "unknown",
 *         "last_seen_iso": "<iso or null>",
 *         "jsonl_path":    "<absolute path or null>",
 *         "jsonl_state":   "jsonl" | "jsonl_live" | "both" | "missing",
 *         "snapshot_path": "<absolute path or null>"
 *       }
 *     ],
 *     "summary": { "live": n, "clean_exit": n, "crashed": n, "total": n }
 *   }
 *
 * Dedup: a single session_id can appear in multiple lazarus project_ids when
 * the session wandered cwds. We keep the FRESHEST record per session_id
 * (highest last_seen). The .jsonl/.jsonl.live lookup scans ALL projects dirs.
 *
 * Hook contract (SessionStart + Stop):
 *   stdin:  JSON, ignored for our purposes (we read disk state)
 *   stdout: `{}` always
 *
 * Idempotent. Never throws. Silent.
 *
 * Disable via env: LAZARUS_INDEX_AGGREGATOR=off
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const LAZARUS_DIR  = path.join(os.homedir(), '.claude', 'lazarus');
const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const OUTPUT_PATH  = path.join(LAZARUS_DIR, 'active_panes.json');

process.stdout.write('{}');

if (process.env.LAZARUS_INDEX_AGGREGATOR === 'off') process.exit(0);

function safeStat(p)        { try { return fs.statSync(p); } catch (_) { return null; } }
function safeReaddir(p)     { try { return fs.readdirSync(p); } catch (_) { return []; } }
function safeReadFile(p)    {
  try { return fs.readFileSync(p, 'utf8').replace(/^﻿/, ''); }
  catch (_) { return null; }
}
function safeParse(s) {
  if (!s) return null;
  try { return JSON.parse(s); } catch (_) { return null; }
}

/** Map<session_id, freshest record from any project's index.json> */
function collectIndexRecords() {
  const map = new Map();
  for (const proj of safeReaddir(LAZARUS_DIR)) {
    const projDir = path.join(LAZARUS_DIR, proj);
    const st = safeStat(projDir);
    if (!st || !st.isDirectory()) continue;
    const idx = safeParse(safeReadFile(path.join(projDir, 'index.json')));
    if (!idx || !Array.isArray(idx.sessions)) continue;
    for (const s of idx.sessions) {
      if (!s || !s.session_id) continue;
      const existing = map.get(s.session_id);
      const newer = !existing || (s.last_seen && (!existing.last_seen || s.last_seen > existing.last_seen));
      if (newer) {
        map.set(s.session_id, {
          session_id: s.session_id,
          project_id: proj,
          status:     s.status || 'unknown',
          last_seen:  s.last_seen || null,
          ended:      s.ended || null,
        });
      }
    }
  }
  return map;
}

/** Map<session_id, {jsonl, live}> built ONCE from one pass over the buckets.
 *
 * MEASURED 2026-09-15 on this host: this hook took 168,585 ms against a
 * declared 5000 ms SessionStart budget, so it was killed on every session
 * start and every session end and never completed on either.
 *
 * The cause was shape, not size. findJsonlFor() used to re-scan every projects
 * bucket for EACH session record: 2019 records over 157 buckets meant 2019
 * readdirs plus roughly 634,000 stat calls to answer a question that one pass
 * answers for everybody. The directory tree itself is small -- a full recursive
 * listing of it takes about 500 ms.
 *
 * O(sessions x buckets) -> O(buckets). Same answer, same precedence: the first
 * bucket in readdir order wins for each kind, which is what the per-session
 * scan did when it broke out of its loop.
 */
let JSONL_INDEX = null;
function jsonlIndex() {
  if (JSONL_INDEX) return JSONL_INDEX;
  const idx = new Map();
  for (const proj of safeReaddir(PROJECTS_DIR)) {
    const projDir = path.join(PROJECTS_DIR, proj);
    const st = safeStat(projDir);
    if (!st || !st.isDirectory()) continue;
    // Skip reparse points (junctions) to avoid double counting.
    if (st.isSymbolicLink && st.isSymbolicLink()) continue;
    for (const f of safeReaddir(projDir)) {
      let sid = null;
      let isLive = false;
      if (f.endsWith('.jsonl.live')) {
        sid = f.slice(0, -('.jsonl.live'.length));
        isLive = true;
      } else if (f.endsWith('.jsonl')) {
        sid = f.slice(0, -('.jsonl'.length));
      } else {
        continue;
      }
      if (!sid) continue;
      let e = idx.get(sid);
      if (!e) { e = { jsonl: null, live: null }; idx.set(sid, e); }
      const full = path.join(projDir, f);
      if (isLive) { if (!e.live) e.live = full; }
      else if (!e.jsonl) { e.jsonl = full; }
    }
  }
  JSONL_INDEX = idx;
  return idx;
}

/** Find any .jsonl / .jsonl.live for this session across all projects buckets. */
function findJsonlFor(sessionId) {
  // Returns { jsonl_path, jsonl_state }
  const e = jsonlIndex().get(sessionId);
  const jsonlPath = e ? e.jsonl : null;
  const livePath  = e ? e.live  : null;
  if (jsonlPath && livePath) return { jsonl_path: jsonlPath, jsonl_state: 'both' };
  if (jsonlPath)             return { jsonl_path: jsonlPath, jsonl_state: 'jsonl' };
  if (livePath)              return { jsonl_path: livePath,  jsonl_state: 'jsonl_live' };
  return                     { jsonl_path: null, jsonl_state: 'missing' };
}

/** First bytes of a file, without loading the rest of it.
 *
 * MEASURED 2026-09-15: the caller below wants at most the first 20 records and
 * used readFileSync, so it pulled whole transcripts into V8 to read line one --
 * 2.2 GB across 818 files on this host, the largest a single 95 MB session.
 * That is most of this hook's wall time and all of its memory pressure, and a
 * starved host is what makes everything else on the machine look broken.
 */
function readHead(p, maxBytes) {
  let fd = null;
  try {
    fd = fs.openSync(p, 'r');
    const buf = Buffer.allocUnsafe(maxBytes);
    const n = fs.readSync(fd, buf, 0, maxBytes, 0);
    if (!n) return null;
    const text = buf.slice(0, n).toString('utf8');
    // A read that filled the buffer almost certainly cut the final line in
    // half; drop it rather than hand a truncated record to JSON.parse.
    return n === maxBytes ? text.slice(0, text.lastIndexOf('\n') + 1) : text;
  } catch (_) {
    return null;
  } finally {
    if (fd !== null) { try { fs.closeSync(fd); } catch (_) { /* best effort */ } }
  }
}

/** Read the cwd from the first record carrying one in the jsonl.
 *
 * Two sizes rather than one. A transcript's opening record carries the cwd and
 * is small, so 16 KB answers almost every file; the 256 KB retry exists for the
 * rare session whose first records are long enough to push it past that. Fixing
 * the size at the larger value cost about 200 MB of reads across this host for
 * an answer the first few KB already held.
 */
function getSessionCwd(jsonlPath) {
  if (!jsonlPath) return null;
  const found = cwdFromText(readHead(jsonlPath, 16384));
  if (found) return found;
  return cwdFromText(readHead(jsonlPath, 262144));
}

function cwdFromText(raw) {
  if (!raw) return null;
  const lines = raw.split(/\r?\n/);
  const limit = Math.min(lines.length, 20);
  for (let i = 0; i < limit; i++) {
    const line = lines[i] && lines[i].trim();
    if (!line) continue;
    const obj = safeParse(line);
    if (obj && obj.cwd) return String(obj.cwd);
  }
  return null;
}

function classify(rec) {
  if (rec.status === 'clean_exit') return 'clean_exit';
  if (rec.status === 'live' && rec.ended)  return 'crashed';
  if (rec.status === 'live' && !rec.ended) return 'live';
  return 'unknown';
}

function snapshotPathFor(sessionId, projectId) {
  // Snapshot files live at ~/.claude/lazarus/<proj>/sessions/<sid>.json (from
  // lazarus-livesnap.js / lazarus-snapshot.js). project_id is the freshest
  // we saw; this may not match every snapshot location for wandering sessions,
  // but it's the canonical one for observability.
  const p = path.join(LAZARUS_DIR, projectId, 'sessions', sessionId + '.json');
  return safeStat(p) ? p : null;
}

function build() {
  const map = collectIndexRecords();
  const panes = [];
  const summary = { live: 0, clean_exit: 0, crashed: 0, unknown: 0, total: 0 };
  for (const rec of map.values()) {
    const cls = classify(rec);
    const jsonlInfo = findJsonlFor(rec.session_id);
    const cwd = getSessionCwd(jsonlInfo.jsonl_path);
    panes.push({
      session_id:    rec.session_id,
      project_id:    rec.project_id,
      cwd:           cwd,
      status:        cls,
      last_seen_iso: rec.last_seen,
      jsonl_path:    jsonlInfo.jsonl_path,
      jsonl_state:   jsonlInfo.jsonl_state,
      snapshot_path: snapshotPathFor(rec.session_id, rec.project_id),
    });
    summary[cls]++;
    summary.total++;
  }
  // Sort: live first, then crashed, then clean_exit, then unknown. Within
  // each group, freshest last_seen first. Use `??` (not `||`) because
  // `order.live` is 0 and `0 || 9` evaluates to 9 in JS — a classic falsy
  // bug that would push every live session to the bottom.
  const order = { live: 0, crashed: 1, clean_exit: 2, unknown: 3 };
  panes.sort((a, b) => {
    const aOrd = order[a.status] ?? 9;
    const bOrd = order[b.status] ?? 9;
    if (aOrd !== bOrd) return aOrd - bOrd;
    return (b.last_seen_iso || '').localeCompare(a.last_seen_iso || '');
  });
  return {
    generated_at: new Date().toISOString(),
    panes,
    summary,
  };
}

function writeAtomic(content) {
  const tmp = OUTPUT_PATH + '.tmp.' + process.pid;
  try {
    fs.mkdirSync(LAZARUS_DIR, { recursive: true });
    fs.writeFileSync(tmp, content, 'utf8');
    fs.renameSync(tmp, OUTPUT_PATH);
    return true;
  } catch (_) {
    try { fs.unlinkSync(tmp); } catch (_) {}
    return false;
  }
}

(function main() {
  try {
    const payload = build();
    writeAtomic(JSON.stringify(payload, null, 2));
  } catch (_) {
    // never throw
  }
})();
