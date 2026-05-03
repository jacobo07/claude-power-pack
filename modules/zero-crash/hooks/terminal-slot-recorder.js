#!/usr/bin/env node
/**
 * terminal-slot-recorder.js — SessionStart hook (BL-0044 / MC-SYS-68).
 *
 * Records (cwd, session_id, started_at) on every SessionStart into
 * vault/terminal_slots.json so a future `claude-smart-resume` PS wrapper
 * can map terminal-by-cwd back to the session that owned it.
 *
 * Why cwd-as-proxy: Cursor doesn't expose its xterm.js terminal UUID to the
 * spawned shell, so direct terminal_id mapping requires reading
 * state.vscdb (per memory reference_cursor_state_vscdb.md). Using cwd
 * works for the common case of "one Claude session per project workspace"
 * and fails gracefully (returns most-recent session for that cwd) when a
 * project has multiple parallel sessions.
 *
 * Schema (vault/terminal_slots.json):
 *   {
 *     "schema_version": 1,
 *     "slots": {
 *       "<cwd-as-key>": {
 *         "session_id": "...",
 *         "started_at": "ISO-8601",
 *         "transcript_path": "...",
 *         "previous_session_id": "..." | null
 *       }
 *     }
 *   }
 *
 * Hook contract (SessionStart event):
 *   stdin JSON: {"session_id":"...","transcript_path":"...","cwd":"...","source":"startup"|"resume"|"clear"|"compact"}
 *   stdout: {} (silent, advisory-only)
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.join(os.homedir(), '.claude', 'skills', 'claude-power-pack');
const SLOTS_PATH = path.join(ROOT, 'vault', 'terminal_slots.json');

let aw;
try {
  aw = require(path.join(ROOT, 'lib', 'atomic_write.js'));
} catch (e) {
  // atomic_write missing — degrade silently
  process.stdout.write('{}');
  process.exit(0);
}

function readStdin() {
  return new Promise(resolve => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => resolve(buf));
    setTimeout(() => resolve(buf), 4500);
  });
}

function loadSlots() {
  try {
    if (!fs.existsSync(SLOTS_PATH)) return { schema_version: 1, slots: {} };
    const raw = fs.readFileSync(SLOTS_PATH, 'utf8').replace(/^﻿/, ''); // strip BOM (BL-0036)
    if (!raw.trim()) return { schema_version: 1, slots: {} };
    const parsed = JSON.parse(raw);
    if (!parsed.slots) parsed.slots = {};
    if (!parsed.schema_version) parsed.schema_version = 1;
    return parsed;
  } catch {
    return { schema_version: 1, slots: {} };
  }
}

function normalizeCwd(cwd) {
  if (!cwd) return null;
  // Normalize Windows path separators + lowercase drive letter so the
  // mapping is stable across forward/back slash and case-shifted invocations.
  const norm = cwd.replace(/\\/g, '/').replace(/^([a-z]):\//i, (_, d) => d.toLowerCase() + ':/');
  return norm.replace(/\/+$/, '');
}

(async function main() {
  let event = {};
  try {
    const raw = await readStdin();
    if (raw.trim()) event = JSON.parse(raw);
  } catch (_) {}

  const sessionId = event.session_id;
  const cwd = normalizeCwd(event.cwd);
  if (!sessionId || !cwd) {
    process.stdout.write('{}');
    return;
  }

  const data = loadSlots();
  const prev = data.slots[cwd] || null;

  data.slots[cwd] = {
    session_id: sessionId,
    started_at: new Date().toISOString().replace(/\..+/, '+00:00'),
    transcript_path: event.transcript_path || null,
    source: event.source || 'unknown',
    previous_session_id: prev ? prev.session_id : null,
  };

  try {
    aw.atomicWriteJson(SLOTS_PATH, data, { indent: 2 });
  } catch (_) {
    // Silent degrade — never block SessionStart
  }

  process.stdout.write('{}');
})();
