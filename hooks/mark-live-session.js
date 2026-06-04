#!/usr/bin/env node
'use strict';
/**
 * mark-live-session.js — SessionStart + Stop hook (Claude Power Pack).
 *
 * Replaces the legacy ~/.claude/hooks/resume-hide-live.js cloaking
 * approach. The legacy hook hid live sessions from the native /resume
 * picker by renaming `<uuid>.jsonl` -> `<uuid>.jsonl.live`. That
 * permanently masked active sessions from the picker, and crashed
 * sessions disappeared forever unless an orphan sweep restored them.
 *
 * This hook keeps every session visible in /resume — including the live
 * ones — and tags the live ones with a leading "⚡ " on the session's
 * `custom-title`, which the picker renders verbatim. The result: the user
 * sees every session, can tell at a glance which ones are currently
 * open in another pane, and never loses a crashed session because
 * nothing was ever hidden.
 *
 * Mechanism:
 *   - The native picker scans each `<proj>/<uuid>.jsonl` and renders the
 *     LATEST `{"type":"custom-title", ...}` record it finds. Records are
 *     append-only; the harness never rewrites prior lines. So appending
 *     a fresh custom-title line is the standard way to mutate display state.
 *   - On Stop (every assistant turn) we append a "⚡ <title>" line IF the
 *     current last custom-title does not already carry the prefix
 *     (idempotent — never double-prefix, never accumulate dupes).
 *   - On SessionStart + on every Stop we run an orphan sweep across
 *     every project's .jsonl: any session whose last custom-title carries
 *     the prefix AND whose underlying process is no longer alive gets a
 *     strip-line appended, undoing the marker.
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
 *   stdin = JSON: { session_id, hook_event_name, cwd, ... }
 * Output: silence on stdout = success. stderr writes survive but don't
 *   block the harness; exit code is always 0.
 *
 * Registration (Owner step, opt-out default in the Power Pack rollout):
 *   python claude-power-pack/tools/settings_merger.py register-sessionstart \
 *     --node-script <abs path to this file> --timeout 5
 *   python claude-power-pack/tools/settings_merger.py register-stop \
 *     --node-script <abs path to this file> --timeout 5
 *   then /restart.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const LIVE_PREFIX = '⚡ ';                 // "⚡ " (HIGH VOLTAGE SIGN + space)
const STALE_MS = 300 * 1000;
const TAIL_BYTES = 64 * 1024;
const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const LAZARUS_DIR = path.join(os.homedir(), '.claude', 'lazarus');
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

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

function findSessionFile(sessionId) {
  if (!sessionId) return null;
  let projDirs;
  try { projDirs = fs.readdirSync(PROJECTS_DIR); } catch { return null; }
  for (const proj of projDirs) {
    const candidate = path.join(PROJECTS_DIR, proj, sessionId + '.jsonl');
    if (fs.existsSync(candidate)) {
      return { proj, dir: path.join(PROJECTS_DIR, proj), filePath: candidate };
    }
  }
  return null;
}

// Returns the *latest* custom-title record's effective state, or null.
// { rawTitle: "⚡ Foo", baseTitle: "Foo", hasPrefix: true }
function lastCustomTitle(filePath) {
  let stat;
  try { stat = fs.statSync(filePath); } catch { return null; }
  const start = Math.max(0, stat.size - TAIL_BYTES);
  const length = stat.size - start;
  if (length <= 0) return null;
  let buf;
  try {
    const fd = fs.openSync(filePath, 'r');
    try {
      buf = Buffer.alloc(length);
      fs.readSync(fd, buf, 0, length, start);
    } finally { fs.closeSync(fd); }
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
      return {
        rawTitle: raw,
        baseTitle: has ? raw.slice(LIVE_PREFIX.length) : raw,
        hasPrefix: has,
      };
    }
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

function fallbackTitle(sessionId) {
  // 8-char UUID prefix is what /resume shows for un-titled sessions
  // anyway, so the fallback degrades gracefully — never blank.
  return sessionId ? sessionId.slice(0, 8) : 'session';
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

function markOwnSessionLive(sessionId) {
  if (!sessionId) return;
  const found = findSessionFile(sessionId);
  if (!found) return;
  const last = lastCustomTitle(found.filePath);
  if (last && last.hasPrefix) return;
  const base = (last && last.baseTitle) || fallbackTitle(sessionId);
  appendCustomTitle(found.filePath, sessionId, LIVE_PREFIX + base);
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
      appendCustomTitle(filePath, uuid, last.baseTitle);
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
  orphanMarkSweep(sessionId);
  // On Stop we also refresh our own marker. On SessionStart the .jsonl
  // for this session usually doesn't exist yet, so markOwnSessionLive is
  // a no-op there — the first Stop after the first assistant turn will
  // apply it.
  if (event === 'Stop' || event === '') {
    markOwnSessionLive(sessionId);
  } else if (event === 'SessionStart') {
    // Attempt mark anyway — harmless if the .jsonl already exists.
    markOwnSessionLive(sessionId);
  }
  process.exit(0);
}

main();
