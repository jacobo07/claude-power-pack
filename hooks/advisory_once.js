'use strict';
// Once-per-session advisory text (wiki/improvements/hook-injection-diet.md).
//
// Hook additionalContext stays in the model's context for the rest of the session, so an
// advisory repeated on every call is re-billed on every later call (census 2026-10-04: 34
// injections, 65.5k chars in one session). A hook asks firstInSession(sid, key) and sends the
// full text only the first time, a one-line tag after that.
//
// Fail-open toward MORE text: no session id, an unwritable state dir or any error answers true,
// so a broken marker costs tokens, never the advisory. A marker older than TTL_MS counts as
// absent (same 2 h bound as tools/jit_skill_loader.py DEDUPE_TTL_SEC), which also re-sends the
// text to a session long enough to have compacted it away.

const fs = require('fs');
const os = require('os');
const path = require('path');

const TTL_MS = 2 * 60 * 60 * 1000;

function stateDir() {
  return process.env.PP_ADVISORY_ONCE_DIR
    || path.join(os.homedir(), '.claude', 'state', 'advisory-once');
}

function firstInSession(sessionId, key) {
  if (!sessionId) return true;
  try {
    const dir = stateDir();
    fs.mkdirSync(dir, { recursive: true });
    const marker = path.join(dir, `${sessionId}.${key}`.replace(/[^A-Za-z0-9.-]/g, '_'));
    try {
      if (Date.now() - fs.statSync(marker).mtimeMs < TTL_MS) return false;
    } catch { /* no marker yet */ }
    fs.writeFileSync(marker, String(Date.now()));
    return true;
  } catch {
    return true;
  }
}

module.exports = { firstInSession, TTL_MS };
