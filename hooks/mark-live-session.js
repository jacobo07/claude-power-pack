#!/usr/bin/env node
'use strict';
/**
 * mark-live-session.js — SessionStart + Stop + SessionEnd hook (Claude Power Pack).
 *
 * Replaces the legacy ~/.claude/hooks/resume-hide-live.js cloaking
 * approach. The legacy hook hid live sessions from the native /resume
 * picker by renaming `<uuid>.jsonl` -> `<uuid>.jsonl.live`. That
 * permanently masked active sessions from the picker, and crashed
 * sessions disappeared forever unless an orphan sweep restored them.
 *
 * This hook keeps every session visible in /resume and writes its state into
 * the session's `custom-title`, which the picker renders verbatim:
 *   "⚡ <title>"            open in some pane right now
 *   "<title>"               died without being closed (crash, reboot): reopen it
 *   "<title> ✓ terminada"   closed on purpose with /clear (also /kclear, which
 *                           ends in /clear), /exit or /logout
 * The title itself and every decision about it come from
 * session-title-lib.decideTitle.
 *
 * Mechanism:
 *   - The native picker scans each `<proj>/<uuid>.jsonl` and renders the
 *     LATEST `{"type":"custom-title", ...}` record it finds. Records are
 *     append-only; the harness never rewrites prior lines. So appending
 *     a fresh custom-title line is the standard way to mutate display state.
 *   - Stop / SessionStart: append "⚡ <title>" when the title is not already
 *     that (idempotent). A resumed "✓ terminada" session becomes live again.
 *   - SessionEnd: reason clear | prompt_input_exit | logout -> "✓ terminada";
 *     any other reason -> drop the "⚡ ".
 *   - SessionStart + Stop also run an orphan sweep across every project's
 *     .jsonl: a session whose last custom-title carries "⚡ " AND whose
 *     process is no longer alive gets the plain title back.
 *
 * Liveness discriminator (same 3-layer gate as the patched
 * resume-hide-live#isOrphanedDead — see
 * ~/.claude/knowledge_vault/errors/resume-hide-live-heartbeat-discriminator-drift.md):
 *   1. mtime(.jsonl) within STALE_MS  -> ALIVE  (recent assistant turn)
 *   2. UUID present in any live claude.exe / node.exe command line
 *                                     -> ALIVE  (idle-but-running)
 *   3. <lazarus>/<proj>/sessions/<uuid>.json timestamp within STALE_MS
 *                                     -> ALIVE  (recent stop_hook write)
 *   else                              -> DEAD, strip the marker.
 *
 * Safety:
 *   - All IO is wrapped; the hook never throws. exit(0) on any error.
 *   - Append-only writes; never rewrites or truncates a .jsonl. Safe
 *     concurrently with the harness's own held fd on Windows (each
 *     `appendFileSync` is atomic for sub-PIPE_BUF payloads).
 *   - Fail-open: if the live-process scan errors out (PowerShell
 *     missing, timeout) the sweep falls back to mtime + index.json
 *     alone — biased toward un-marking rather than over-marking, so a
 *     stuck "⚡ " is never permanent.
 *
 * Input shape (Claude Code hook contract):
 *   stdin = JSON: { session_id, hook_event_name, transcript_path, reason, ... }
 * Output: silence on stdout = success. Exit code is always 0.
 *
 * Registration: Stop via ~/.claude/hooks/hook-dispatcher.js (Stop-chain),
 * SessionStart via session_start_hub.js, SessionEnd as its own entry in
 * ~/.claude/settings.json.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { decideTitle, lastCustomTitle } = require('./session-title-lib.js');

const STALE_MS = 300 * 1000;
const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const LAZARUS_DIR = path.join(os.homedir(), '.claude', 'lazarus');
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const FINISH_REASONS = new Set(['clear', 'prompt_input_exit', 'logout']);

function readStdin() {
  try {
    const buf = fs.readFileSync(0, 'utf-8');
    return buf ? JSON.parse(buf) : {};
  } catch {
    return {};
  }
}

let _liveSessionsCache = null;
function getLiveSessions() {
  if (_liveSessionsCache !== null) return _liveSessionsCache;
  _liveSessionsCache = new Set();
  if (process.platform !== 'win32') return _liveSessionsCache;
  try {
    const { execFileSync } = require('child_process');
    const out = execFileSync(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe' OR Name='claude.exe'\" | Select-Object -ExpandProperty CommandLine",
      ],
      { encoding: 'utf8', timeout: 1500, windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] }
    );
    const uuidRe = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g;
    const matches = out.match(uuidRe);
    if (matches) for (const u of matches) _liveSessionsCache.add(u.toLowerCase());
  } catch {
    // Scan failure -> empty set, fall back to mtime + index.json.
  }
  return _liveSessionsCache;
}

function findSessionFile(sessionId, transcriptPath) {
  if (transcriptPath && transcriptPath.endsWith(sessionId + '.jsonl') && fs.existsSync(transcriptPath)) {
    return transcriptPath;
  }
  if (!sessionId) return null;
  let projDirs;
  try { projDirs = fs.readdirSync(PROJECTS_DIR); } catch { return null; }
  for (const proj of projDirs) {
    const candidate = path.join(PROJECTS_DIR, proj, sessionId + '.jsonl');
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function appendCustomTitle(filePath, sessionId, title) {
  const rec = JSON.stringify({ type: 'custom-title', customTitle: title, sessionId }) + '\n';
  try {
    fs.appendFileSync(filePath, rec, { flag: 'a' });
    return true;
  } catch (e) {
    process.stderr.write('mark-live-session: append failed for '
      + path.basename(filePath) + ': ' + (e.code || e.message) + '\n');
    return false;
  }
}

function isSessionAlive(projName, uuid, filePath) {
  let stat;
  try { stat = fs.statSync(filePath); } catch { return true; /* file gone = leave alone */ }
  if (Date.now() - stat.mtimeMs <= STALE_MS) return true;

  const live = getLiveSessions();
  if (live.has(uuid.toLowerCase())) return true;

  const idxPath = path.join(LAZARUS_DIR, projName, 'sessions', uuid + '.json');
  try {
    const raw = fs.readFileSync(idxPath, 'utf-8');
    const idx = JSON.parse(raw);
    if (idx && typeof idx.timestamp === 'string') {
      const idxAge = Date.now() - new Date(idx.timestamp).getTime();
      if (Number.isFinite(idxAge) && idxAge <= STALE_MS) return true;
    }
  } catch { /* no index = fall through */ }

  return false;
}

// Apply `mode` ('live' | 'finished' | 'dead') to one session's title.
function markOwnSession(sessionId, transcriptPath, mode) {
  if (!sessionId) return null;
  const filePath = findSessionFile(sessionId, transcriptPath);
  if (!filePath) return null;
  const title = decideTitle(filePath, sessionId, mode);
  if (title !== null) appendCustomTitle(filePath, sessionId, title);
  return title;
}

// Incremental sweep state. The full sweep read a 256 KB tail of EVERY .jsonl on
// every Stop: 3147 transcripts took 47.9 s (2026-11-22), so the Stop-chain's 8 s
// kill fired 1724 times in 7 days and the sweep never finished. Exact pruning:
// a "⚡ " title reaches a file only through an append, and an append bumps its
// mtime. After a COMPLETED pass that started at `since`, a file can carry "⚡ "
// only if its mtime >= since, or that pass left it marked (alive): `marked`.
// A first pass (no state) is resumable: `scan` keeps its start and a
// (proj, file) cursor, so a budget cut costs progress, never correctness.
const STATE_FILE = path.join(os.homedir(), '.claude', 'state', 'mark-live-session', 'sweep.json');
// 3 s: one slow file overran a 4 s budget by 1.9 s on a loaded host, and the
// dispatcher kills the hook at 8 s.
const SWEEP_BUDGET_MS = Number(process.env.PP_MLS_SWEEP_BUDGET_MS) || 3000;
const MTIME_SLACK_MS = 5000;   // clock / mtime granularity margin

// v2: resume key proj + '\u0000' + f. A state saved before v2 (cursor key proj + '/' + f) may
// have SEALED a pass that skipped whole folders (`P-wt` after a cut inside `P`), and those files
// are below `since` and not in `marked`, so no incremental pass would revisit them. Any state
// without v2 therefore starts one fresh full pass (resumable, so bounded); `marked` is kept.
// Pre-push review of 8f4e20c6 and of its fix; V-MLS-05/06.
const SWEEP_STATE_V = 2;

function loadSweepState() {
  try {
    const s = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    if (s && typeof s === 'object') {
      const current = s.v === SWEEP_STATE_V;
      return {
        v: SWEEP_STATE_V,
        since: current && Number.isFinite(s.since) ? s.since : null,
        marked: s.marked && typeof s.marked === 'object' ? s.marked : {},
        scan: current && s.scan && Number.isFinite(s.scan.start) && typeof s.scan.cursor === 'string'
          ? s.scan : null,
      };
    }
  } catch { /* missing or corrupt -> full pass */ }
  return { v: SWEEP_STATE_V, since: null, marked: {}, scan: null };
}

function saveSweepState(state) {
  try {
    fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
    const tmp = STATE_FILE + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(state));
    fs.renameSync(tmp, STATE_FILE);   // concurrent writers: last rename wins; each is a sound state
  } catch { /* next run redoes the work */ }
}

// Judge one file; keeps `marked` equal to "carries ⚡ and was left so".
function sweepOne(proj, uuid, filePath, marked) {
  const last = lastCustomTitle(filePath);
  if (!last || !last.hasPrefix) { delete marked[uuid]; return; }
  if (!isSessionAlive(proj, uuid, filePath)) {
    const title = decideTitle(filePath, uuid, 'dead');
    if (title !== null && appendCustomTitle(filePath, uuid, title)) { delete marked[uuid]; return; }
  }
  marked[uuid] = proj;
}

function orphanMarkSweep(ownSessionId, state = loadSweepState()) {
  const start = Date.now();
  const deadline = start + SWEEP_BUDGET_MS;
  const own = (ownSessionId || '').toLowerCase();
  const full = state.since === null;
  if (full && !state.scan) state.scan = { start, cursor: '' };
  // The resume key joins folder and file with '\u0000', which sorts below every
  // character a folder name can hold. With '/', a folder `P-wt` (after `P` in the
  // sort) had keys BELOW a cursor left inside `P` ('-' < '/'), so a budget cut
  // there skipped all of `P-wt` for good (pre-push review of 8f4e20c6; V-MLS-05). A state from
  // before this key is not resumed but restarted (SWEEP_STATE_V, V-MLS-06).
  const since = full ? null : state.since - MTIME_SLACK_MS;
  const seen = new Set();
  let cut = false;
  let projDirs;
  try { projDirs = fs.readdirSync(PROJECTS_DIR).sort(); } catch { return state; }
  outer:
  for (const proj of projDirs) {
    const dir = path.join(PROJECTS_DIR, proj);
    let entries;
    try {
      if (!fs.statSync(dir).isDirectory()) continue;
      entries = fs.readdirSync(dir).sort();
    } catch { continue; }
    for (const f of entries) {
      if (!f.endsWith('.jsonl')) continue;
      const uuid = f.slice(0, -'.jsonl'.length);
      if (!UUID_RE.test(uuid)) continue;
      if (own && uuid.toLowerCase() === own) continue;
      const key = proj + '\u0000' + f;
      if (full && key <= state.scan.cursor) continue;          // done in an earlier chunk
      const filePath = path.join(dir, f);
      if (!full) {
        let mtime;
        try { mtime = fs.statSync(filePath).mtimeMs; } catch { continue; }
        if (mtime < since && !Object.prototype.hasOwnProperty.call(state.marked, uuid)) continue;
      }
      // At least one file per run, so a budget below readdir time still progresses.
      if (seen.size > 0 && Date.now() > deadline) { cut = true; break outer; }
      seen.add(uuid);
      sweepOne(proj, uuid, filePath, state.marked);
      if (full) state.scan.cursor = key;
    }
  }
  // A marked file that vanished (deleted/moved) is no longer a candidate.
  if (!cut && !full) {
    for (const uuid of Object.keys(state.marked)) if (!seen.has(uuid) && uuid.toLowerCase() !== own) delete state.marked[uuid];
  }
  if (!cut) {
    // Files appended to after this pass started are caught by mtime next time.
    state.since = full ? state.scan.start : start;
    state.scan = null;
  }
  return state;
}

function main() {
  const input = readStdin();
  // Env-payload fallback (BL-SESSION-FOLD-001): when session_start_hub.js
  // detached-spawns this hook, the child has no stdin, so cwd/session_id/event
  // arrive via env. The standalone settings.json entry still feeds stdin.
  const sessionId = input.session_id || process.env.PP_EVT_SID || '';
  const event = input.hook_event_name || input.event
    || process.env.PP_EVT_EVENT || '';
  if (event === 'SessionEnd') {
    markOwnSession(sessionId, input.transcript_path, FINISH_REASONS.has(input.reason) ? 'finished' : 'dead');
    return;
  }
  const state = orphanMarkSweep(sessionId);
  // On SessionStart the .jsonl usually doesn't exist yet, so this is a no-op
  // there; the first Stop applies it.
  markOwnSession(sessionId, input.transcript_path, 'live');
  // The sweep skips its own session, so it enters `marked` here: an idle
  // session that later crashes keeps an old mtime and is found only this way.
  const ownFile = sessionId ? findSessionFile(sessionId, input.transcript_path) : null;
  if (ownFile) state.marked[sessionId] = path.basename(path.dirname(ownFile));
  saveSweepState(state);
}

if (require.main === module) {
  try { main(); } catch { /* never block the harness */ }
  process.exit(0);
}

module.exports = { markOwnSession, FINISH_REASONS };
