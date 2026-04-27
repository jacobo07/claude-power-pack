#!/usr/bin/env node
/**
 * Lazarus Shadow-Folder Engine — MC-LAZ-06a (k_qa v17000.0)
 *
 * Hides the .jsonl transcripts of OTHER currently-alive Claude sessions
 * from the cwd's project directory by renaming them with a suffix the
 * native /resume picker won't list. The other sessions keep writing
 * via their open file handles (Claude Code uses FILE_SHARE_DELETE on
 * Windows; rename does not invalidate the descriptor) so no events are
 * lost. On Stop, we restore the names we own.
 *
 * Suffix format: <sid>.jsonl.live-shadow-<ownerSid>
 *   - <sid>          — the session whose .jsonl is being hidden
 *   - <ownerSid>     — THIS session, the one that decided to hide it
 *
 * Ownership tracking ensures we only restore shadows we created — if
 * three sessions are alive, each owns a different overlapping subset
 * of shadows; last-survivor restores its own batch on Stop.
 *
 * Kill-switch (REQUIRED for activation):
 *   LAZARUS_SHADOW_FOLDER=1   — engine inert otherwise
 *
 * Atomic operations only. Any error during shadow → in-flight shadows
 * are NOT rolled back here (caller decides); but emit() always logs
 * what happened for the panic-restore script to clean up.
 *
 * Usage as module:
 *   const eng = require('./shadow_engine');
 *   eng.shadow({ projectId, ownerSid, dryRun: false });
 *   eng.restore({ projectId, ownerSid });
 *
 * Usage as CLI:
 *   node shadow_engine.js shadow  --project-id <pid> --owner-sid <sid>
 *   node shadow_engine.js restore --project-id <pid> --owner-sid <sid>
 *   node shadow_engine.js list    --project-id <pid>
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const LAZARUS_DIR = path.join(HOME, '.claude', 'lazarus');
const PROJECTS_DIR = path.join(HOME, '.claude', 'projects');
const SHADOW_SUFFIX_PREFIX = '.jsonl.live-shadow-';
const HEARTBEAT_FRESH_MS = 5 * 60 * 1000;

function isEnabled(env = process.env) {
  return env.LAZARUS_SHADOW_FOLDER === '1';
}

function log(level, msg, extra) {
  // Structured log to stderr — never stdout (caller may parse stdout).
  const line = JSON.stringify({
    iso: new Date().toISOString(),
    component: 'shadow_engine',
    level,
    msg,
    ...(extra || {}),
  });
  try { process.stderr.write(line + '\n'); } catch { /* drop */ }
}

function liveOtherSessions({ projectId, ownerSid }) {
  // Read heartbeats/<sid>.lock for this project; return sids whose
  // mtime is fresh AND who are NOT the owner. These are the .jsonl
  // we should hide.
  const hbDir = path.join(LAZARUS_DIR, projectId, 'heartbeats');
  if (!fs.existsSync(hbDir)) return [];
  const cutoff = Date.now() - HEARTBEAT_FRESH_MS;
  const out = [];
  let entries;
  try { entries = fs.readdirSync(hbDir); } catch { return []; }
  for (const name of entries) {
    if (!name.endsWith('.lock')) continue;
    const sid = name.slice(0, -5);
    if (sid === ownerSid) continue;
    let st;
    try { st = fs.statSync(path.join(hbDir, name)); }
    catch { continue; }
    if (st.mtimeMs >= cutoff) out.push(sid);
  }
  return out;
}

function originalJsonl({ projectId, sid }) {
  return path.join(PROJECTS_DIR, projectId, sid + '.jsonl');
}

function shadowPath({ projectId, sid, ownerSid }) {
  return path.join(
    PROJECTS_DIR,
    projectId,
    sid + SHADOW_SUFFIX_PREFIX + ownerSid,
  );
}

/**
 * Hide the .jsonl files of OTHER live sessions in this project.
 * Returns { shadowed: [...sids], skipped: [...{sid, reason}] }.
 *
 * Re-entrant: if a session's .jsonl is already shadowed by anyone
 * (any owner), skip — the picker already won't see it.
 */
function shadow({ projectId, ownerSid, dryRun = false } = {}) {
  if (!projectId || !ownerSid) {
    throw new Error('shadow_engine.shadow: projectId and ownerSid required');
  }
  const shadowed = [];
  const skipped = [];
  const sids = liveOtherSessions({ projectId, ownerSid });

  for (const sid of sids) {
    const orig = originalJsonl({ projectId, sid });
    if (!fs.existsSync(orig)) {
      // Already shadowed by someone, or no transcript yet — pass.
      const projDir = path.join(PROJECTS_DIR, projectId);
      let alreadyShadowed = false;
      try {
        for (const f of fs.readdirSync(projDir)) {
          if (f.startsWith(sid + SHADOW_SUFFIX_PREFIX)) {
            alreadyShadowed = true;
            break;
          }
        }
      } catch { /* dir gone, nothing to do */ }
      skipped.push({
        sid,
        reason: alreadyShadowed ? 'already-shadowed-by-other' : 'no-transcript',
      });
      continue;
    }

    const dst = shadowPath({ projectId, sid, ownerSid });
    if (dryRun) {
      shadowed.push({ sid, from: orig, to: dst, dryRun: true });
      continue;
    }
    try {
      fs.renameSync(orig, dst);
      shadowed.push({ sid, from: orig, to: dst });
      log('info', 'shadowed', { sid, ownerSid, projectId });
    } catch (e) {
      skipped.push({ sid, reason: 'rename-failed', error: String(e) });
      log('error', 'shadow-rename-failed', {
        sid, ownerSid, projectId, error: String(e),
      });
    }
  }
  return { shadowed, skipped };
}

/**
 * Restore .jsonl files we (ownerSid) shadowed. Walk the project dir
 * for *.live-shadow-<ownerSid> entries; rename each back to <sid>.jsonl.
 * If the original .jsonl path is somehow occupied (race with another
 * owner's restore), append a timestamp suffix so no data is overwritten.
 */
function restore({ projectId, ownerSid, dryRun = false } = {}) {
  if (!projectId || !ownerSid) {
    throw new Error('shadow_engine.restore: projectId and ownerSid required');
  }
  const projDir = path.join(PROJECTS_DIR, projectId);
  if (!fs.existsSync(projDir)) return { restored: [], skipped: [] };

  const restored = [];
  const skipped = [];
  const ownedSuffix = SHADOW_SUFFIX_PREFIX + ownerSid;

  let entries;
  try { entries = fs.readdirSync(projDir); } catch { return { restored, skipped }; }
  for (const f of entries) {
    if (!f.endsWith(ownedSuffix)) continue;
    const sid = f.slice(0, -ownedSuffix.length);
    const src = path.join(projDir, f);
    const dst = originalJsonl({ projectId, sid });

    if (fs.existsSync(dst)) {
      // Conflict — another writer or owner already restored. Rather
      // than overwrite, park ours under a timestamped name so panic-
      // restore (or a human) can reconcile.
      const ts = new Date().toISOString().replace(/[:.]/g, '-');
      const parked = `${dst}.conflict.${ts}`;
      if (dryRun) {
        skipped.push({ sid, reason: 'conflict-would-park', parked });
        continue;
      }
      try {
        fs.renameSync(src, parked);
        skipped.push({ sid, reason: 'conflict-parked', parked });
        log('warn', 'restore-conflict-parked', { sid, ownerSid, parked });
      } catch (e) {
        skipped.push({ sid, reason: 'conflict-park-failed', error: String(e) });
        log('error', 'restore-park-failed', { sid, error: String(e) });
      }
      continue;
    }

    if (dryRun) {
      restored.push({ sid, from: src, to: dst, dryRun: true });
      continue;
    }
    try {
      fs.renameSync(src, dst);
      restored.push({ sid, from: src, to: dst });
      log('info', 'restored', { sid, ownerSid, projectId });
    } catch (e) {
      skipped.push({ sid, reason: 'restore-failed', error: String(e) });
      log('error', 'restore-failed', { sid, error: String(e) });
    }
  }
  return { restored, skipped };
}

/**
 * Diagnostic: list every shadow currently present in the project dir,
 * grouped by owner. Used by panic-restore + debugging.
 */
function listShadows({ projectId } = {}) {
  if (!projectId) throw new Error('shadow_engine.listShadows: projectId required');
  const projDir = path.join(PROJECTS_DIR, projectId);
  if (!fs.existsSync(projDir)) return [];
  const out = [];
  let entries;
  try { entries = fs.readdirSync(projDir); } catch { return []; }
  for (const f of entries) {
    const idx = f.indexOf(SHADOW_SUFFIX_PREFIX);
    if (idx < 0) continue;
    const sid = f.slice(0, idx);
    const ownerSid = f.slice(idx + SHADOW_SUFFIX_PREFIX.length);
    let size = null, mtime = null;
    try {
      const st = fs.statSync(path.join(projDir, f));
      size = st.size;
      mtime = st.mtimeMs;
    } catch { /* ignore */ }
    out.push({ sid, ownerSid, file: f, size, mtimeMs: mtime });
  }
  return out;
}

// ─────────────────────────── CLI ──────────────────────────────────

function parseFlags(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project-id') out.projectId = argv[++i];
    else if (a === '--owner-sid') out.ownerSid = argv[++i];
    else if (a === '--dry-run') out.dryRun = true;
    else if (a === '--no-gate') out.noGate = true;
  }
  return out;
}

function main() {
  const cmd = process.argv[2];
  const flags = parseFlags(process.argv.slice(3));

  // Kill-switch: refuse to mutate state unless LAZARUS_SHADOW_FOLDER=1
  // OR --no-gate is passed (only the sandbox test should use --no-gate).
  if (cmd === 'shadow' || cmd === 'restore') {
    if (!isEnabled() && !flags.noGate) {
      console.error(
        'shadow_engine: refusing to run — set LAZARUS_SHADOW_FOLDER=1 to enable.',
      );
      process.exit(2);
    }
  }

  let result;
  try {
    if (cmd === 'shadow') result = shadow(flags);
    else if (cmd === 'restore') result = restore(flags);
    else if (cmd === 'list') result = listShadows(flags);
    else {
      console.error('Usage: shadow_engine.js [shadow|restore|list] --project-id <pid> [--owner-sid <sid>] [--dry-run] [--no-gate]');
      process.exit(64);
    }
  } catch (e) {
    console.error('shadow_engine error:', e.message);
    process.exit(1);
  }
  console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
  main();
} else {
  module.exports = {
    isEnabled,
    liveOtherSessions,
    shadow,
    restore,
    listShadows,
    SHADOW_SUFFIX_PREFIX,
    HEARTBEAT_FRESH_MS,
  };
}
