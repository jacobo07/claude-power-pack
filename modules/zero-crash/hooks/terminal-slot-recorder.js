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

// BL-0072 Lazarus v2: global registry for slot_id-keyed lookups (Q&A Q3-b).
// Composite key (workspace_path, slot_id) -> {uuid, last_seen_unix, ...}.
// Populated when LAZARUS_TERMINAL_KEY env is set; primary source for
// claude_smart_resume.ps1 tier-1 dispatch.
const REGISTRY_PATH = path.join(os.homedir(), '.claude', 'lazarus', 'terminal_registry.json');
const REGISTRY_LOCK = REGISTRY_PATH + '.lock';
const REGISTRY_LOCK_STALE_MS = 30 * 1000;   // gap #7: 30s stale-lock recovery
const REGISTRY_DEDUP_WINDOW_MS = 2 * 1000;  // gap #9: cascade-write dedup
const TMP_ORPHAN_AGE_MS = 60 * 1000;        // BL-0073: reap killed-mid-write tmp siblings

// BL-0073: tmp-orphan reaper. atomic_write.js cleans up tmp on its own success/
// failure paths, but if the parent process is killed mid-rename loop the tmp
// survives. Sweep <base>.tmp.* files older than 60s before each write to keep
// vault/ and lazarus/ from accumulating debris (live state had 7 such orphans).
function reapStaleTmps(targetPath) {
  try {
    const dir = path.dirname(targetPath);
    const base = path.basename(targetPath);
    const prefix = base + '.tmp.';
    const now = Date.now();
    for (const f of fs.readdirSync(dir)) {
      if (!f.startsWith(prefix)) continue;
      const full = path.join(dir, f);
      try {
        const st = fs.statSync(full);
        if (now - st.mtimeMs > TMP_ORPHAN_AGE_MS) fs.unlinkSync(full);
      } catch (_) { /* best-effort */ }
    }
  } catch (_) { /* best-effort */ }
}

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
    // RAM-regression fix 2026-06-08: the SessionStart JSON arrives in a
    // single <1 KB chunk, but the 4500 ms fallback was firing on every
    // session-open (measured 4561 ms ≈ full timeout). Across a 10-pane
    // startup it cost ~45 s of churn. 800 ms keeps a generous margin for
    // event-loop scheduling delay under multi-pane contention while
    // cutting ~3.7 s/pane. Fast path (stdin 'end') is unchanged.
    setTimeout(() => resolve(buf), 800);
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
    reapStaleTmps(SLOTS_PATH);
    aw.atomicWriteJson(SLOTS_PATH, data, 2);
  } catch (_) {
    // Silent degrade — never block SessionStart
  }

  // BL-0072 + BL-0073: write into global registry when LAZARUS_TERMINAL_KEY
  // is set. Tier-1 lookup source for claude_smart_resume.ps1. Validate the key
  // matches slot[N] or UUID-v4; warn on stderr otherwise so leaked vars (e.g.
  // system-wide setx) surface instead of silently collapsing all panes (gap #6).
  const slotId = process.env.LAZARUS_TERMINAL_KEY;
  if (slotId) {
    const slotRe = /^slot[1-9][0-9]*$/;
    const uuidRe = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if (!slotRe.test(slotId) && !uuidRe.test(slotId)) {
      process.stderr.write(`terminal-slot-recorder: LAZARUS_TERMINAL_KEY=${JSON.stringify(slotId)} matches neither slot[N] nor UUID-v4; registry write skipped\n`);
    } else {
      writeRegistryEntry({
        workspace_path: cwd,
        slot_id: slotId,
        cwd: cwd,
        uuid: sessionId,
        transcript_path: event.transcript_path || null,
        source: event.source || 'unknown',
      });
    }
  }

  process.stdout.write('{}');
})();

function writeRegistryEntry(entry) {
  // mkdir-mutex pattern (BL-0007 lineage); 30s stale-lock recovery (gap #7).
  let lockHeld = false;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      fs.mkdirSync(REGISTRY_LOCK);
      lockHeld = true;
      break;
    } catch (e) {
      if (e.code !== 'EEXIST') return; // unknown error -> bail silently
      // Stale-lock check
      try {
        const st = fs.statSync(REGISTRY_LOCK);
        if (Date.now() - st.mtimeMs > REGISTRY_LOCK_STALE_MS) {
          try { fs.rmdirSync(REGISTRY_LOCK); } catch (_) {}
          continue;
        }
      } catch (_) {}
      // Lock fresh; brief backoff then retry once
      const start = Date.now();
      while (Date.now() - start < 100) { /* spin 100ms */ }
    }
  }
  if (!lockHeld) return; // never block hook

  try {
    let registry;
    try {
      const raw = fs.readFileSync(REGISTRY_PATH, 'utf8').replace(/^﻿/, '');
      registry = JSON.parse(raw);
    } catch {
      registry = { schema: 1, entries: [] };
    }
    if (!Array.isArray(registry.entries)) registry.entries = [];

    const now = Date.now();
    const nowUnix = Math.floor(now / 1000);
    const existing = registry.entries.find(
      e => e.workspace_path === entry.workspace_path && e.slot_id === entry.slot_id
    );

    if (existing) {
      // gap #9: cascade dedup. If we just wrote (<2s) and uuid changed, preserve previous.
      const ageMs = now - ((existing.last_seen_unix || 0) * 1000);
      if (ageMs < REGISTRY_DEDUP_WINDOW_MS && existing.uuid && existing.uuid !== entry.uuid) {
        existing.previous_uuid = existing.uuid;
      } else if (existing.uuid && existing.uuid !== entry.uuid) {
        existing.previous_uuid = existing.uuid;
      }
      existing.uuid = entry.uuid;
      existing.cwd = entry.cwd;
      existing.transcript_path = entry.transcript_path;
      existing.source = entry.source;
      existing.last_seen_unix = nowUnix;
      existing.last_seen_iso = new Date(now).toISOString().replace(/\.\d+Z$/, 'Z');
    } else {
      registry.entries.push({
        workspace_path: entry.workspace_path,
        slot_id: entry.slot_id,
        cwd: entry.cwd,
        uuid: entry.uuid,
        previous_uuid: null,
        transcript_path: entry.transcript_path,
        source: entry.source,
        last_seen_unix: nowUnix,
        last_seen_iso: new Date(now).toISOString().replace(/\.\d+Z$/, 'Z'),
      });
    }

    // Atomic write: tmp + rename
    const tmp = REGISTRY_PATH + '.tmp.' + process.pid;
    fs.writeFileSync(tmp, JSON.stringify(registry, null, 2), 'utf8');
    fs.renameSync(tmp, REGISTRY_PATH);
  } catch (_) {
    // never block hook
  } finally {
    try { fs.rmdirSync(REGISTRY_LOCK); } catch (_) {}
  }
}
