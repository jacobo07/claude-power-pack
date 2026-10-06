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

function orphanMarkSweep(ownSessionId) {
  let projDirs;
  try { projDirs = fs.readdirSync(PROJECTS_DIR); } catch { return; }
  for (const proj of projDirs) {
    const dir = path.join(PROJECTS_DIR, proj);
    let entries;
    try {
      const st = fs.statSync(dir);
      if (!st.isDirectory()) continue;
      entries = fs.readdirSync(dir);
    } catch { continue; }
    for (const f of entries) {
      if (!f.endsWith('.jsonl')) continue;
      const uuid = f.slice(0, -'.jsonl'.length);
      if (!UUID_RE.test(uuid)) continue;
      if (ownSessionId && uuid.toLowerCase() === ownSessionId.toLowerCase()) continue;
      const filePath = path.join(dir, f);
      const last = lastCustomTitle(filePath);
      if (!last || !last.hasPrefix) continue;
      if (isSessionAlive(proj, uuid, filePath)) continue;
      const title = decideTitle(filePath, uuid, 'dead');
      if (title !== null) appendCustomTitle(filePath, uuid, title);
    }
  }
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
  orphanMarkSweep(sessionId);
  // On SessionStart the .jsonl usually doesn't exist yet, so this is a no-op
  // there; the first Stop applies it.
  markOwnSession(sessionId, input.transcript_path, 'live');
}

if (require.main === module) {
  try { main(); } catch { /* never block the harness */ }
  process.exit(0);
}

module.exports = { markOwnSession, FINISH_REASONS };
