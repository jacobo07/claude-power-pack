#!/usr/bin/env node
/**
 * restart_resume.js -- SessionStart marker detector for /restart.
 *
 * FOLD NOTE (2026-06-22, restart-kclear audit PF-7): this standalone file is now
 * REFERENCE-ONLY. The live SessionStart logic runs as hookRestartResume INSIDE
 * hooks/session_start_hub.js (hub-fold 2026-06-04); this file is NOT registered in
 * settings.json. Keep the two in sync if either changes. See UKDL T-RESTART-001.
 *
 * /restart writes a marker file at ~/.claude/state/restart_pending.json
 * with the prior session's SID, cwd, branch, and timestamp. When a NEW
 * Claude Code session starts and this hook fires, if the marker exists
 * AND is fresh (< 5 min old) AND the cwd matches:
 *   1. Inject a one-line additionalContext note so the new session
 *      knows it is continuing from a /restart.
 *   2. Consume (delete) the marker so it does not fire on every
 *      subsequent SessionStart.
 *
 * Honest scope: this hook gives a CONTEXTUAL HINT, not a true
 * conversation restore. The kclaude.bat MC-LAZ-26 wrapper does the
 * actual `claude --resume <uuid>` when it is the parent of the new
 * pane. This marker is the UNIVERSAL fallback for panes NOT under
 * kclaude.bat (PowerShell, Git Bash, VPS profiles).
 *
 * Cwd guard: the marker is consumed only when the new session's cwd
 * MATCHES the marker's cwd. A claude session in a different repo
 * leaves the marker alone (would otherwise leak the hint into an
 * unrelated session).
 *
 * Fail-open contract: errors are routed to stderr (visible in dev mode
 * but not blocking) so they are observable but never break SessionStart.
 *
 * Sealed BL-RESTART-001 (2026-05-31).
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const MARKER = path.join(os.homedir(), '.claude', 'state',
                        'restart_pending.json');
const FRESHNESS_MINUTES = 5;
const MS_PER_MINUTE = 60 * 1000;
const MAX_AGE_MS = FRESHNESS_MINUTES * MS_PER_MINUTE;

// Length of an ISO-8601 timestamp truncated to seconds precision
// ("YYYY-MM-DDTHH:MM:SS" = 19 chars). Used to drop milliseconds + tz
// for the additionalContext display.
const ISO_SECONDS_LEN = 19;

function note(reason, err) {
  // Stderr only; visible in dev mode, never blocks the session.
  try {
    process.stderr.write(`restart_resume: ${reason}`
      + (err ? ` (${err && err.message ? err.message : err})` : '')
      + '\n');
  } catch (writeErr) {
    // If stderr itself is gone, nothing more we can do; explicit no-op
    // so the catch is not empty.
    void writeErr;
  }
}

// UTF-8 BOM as a single string char (U+FEFF). Cross-tool stdin (PowerShell
// `Set-Content -Encoding UTF8` notoriously writes one) trips JSON.parse if
// not stripped. Same trap caught for Python in
// `feedback_python_utf8_bom.md` (BL-0036, 2026-05-03).
const UTF8_BOM = '﻿';

function readStdin() {
  try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.charCodeAt(0) === 0xFEFF) {
      return raw.slice(UTF8_BOM.length);
    }
    return raw;
  } catch (err) {
    note('stdin unreadable', err);
    return '';
  }
}

let cwd = process.cwd();
try {
  const raw = readStdin();
  if (raw) {
    const payload = JSON.parse(raw);
    if (payload && typeof payload.cwd === 'string' && payload.cwd) {
      cwd = payload.cwd;
    }
  }
} catch (err) {
  note('cwd extraction failed', err);
}

try {
  if (!fs.existsSync(MARKER)) {
    process.exit(0); // no pending restart -- silent
  }

  const stat = fs.statSync(MARKER);
  const age = Date.now() - stat.mtimeMs;
  if (age > MAX_AGE_MS) {
    // Stale marker -- delete and exit silent.
    try {
      fs.unlinkSync(MARKER);
    } catch (delErr) {
      note('stale marker unlink failed', delErr);
    }
    process.exit(0);
  }

  let markerRaw = fs.readFileSync(MARKER, 'utf8');
  if (markerRaw && markerRaw.charCodeAt(0) === 0xFEFF) {
    // PowerShell 5.1's Set-Content -Encoding UTF8 writes a BOM. Strip
    // before parsing -- the .ps1 writer is meant to use UTF-8 without
    // BOM but this guard makes the hook resilient to either form.
    markerRaw = markerRaw.slice(1);
  }
  const ctx = JSON.parse(markerRaw);

  // Cwd guard: only consume when the new session's cwd matches.
  const markerCwd = (ctx.cwd || '').toLowerCase();
  const sessCwd = (cwd || '').toLowerCase();
  if (markerCwd && sessCwd && markerCwd !== sessCwd) {
    // Different repo -- leave marker for the right session.
    process.exit(0);
  }

  // Consume marker (single-shot).
  try {
    fs.unlinkSync(MARKER);
  } catch (delErr) {
    note('marker unlink failed', delErr);
  }

  const branch = ctx.branch || 'unknown';
  const ts = (ctx.timestamp || '').slice(0, ISO_SECONDS_LEN);
  const sid = ctx.session_id || '';
  const sessNote = ctx.session_note
    || 'Session restarted via /restart command.';

  let line = `[/restart resume] Continuing from a prior session in this `
           + `working directory. Branch: ${branch}. Restarted at: `
           + `${ts || '?'}.`;
  if (sid) {
    line += ` Prior session id: ${sid}.`;
  }
  line += ` ${sessNote}`;

  process.stdout.write(JSON.stringify({
    continue: true,
    additionalContext: line,
  }));
  process.exit(0);
} catch (err) {
  // Never fail SessionStart; surface to stderr for observability.
  note('marker handling failed', err);
  process.exit(0);
}
