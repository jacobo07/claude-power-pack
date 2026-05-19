#!/usr/bin/env node
/**
 * resume-hide-live.js — SessionStart + Stop hook.
 *
 * Purpose (BL-0013):
 *   The native /resume modal enumerates ~/.claude/projects/<id>/*.jsonl, filtered
 *   by `endsWith(".jsonl")` (verified empirically against the bundled source of
 *   Claude Code 2.1.126). To hide LIVE sessions from that picker without
 *   reimplementing the modal UI, we rename `<uuid>.jsonl` -> `<uuid>.jsonl.live`
 *   while the session is alive. The harness keeps writing through its held fd,
 *   so post-rename writes still land in the renamed file (verified on
 *   Windows + Node v24).
 *
 * Lifecycle:
 *   1. claude creates `<session_id>.jsonl` and opens an append fd.
 *   2. SessionStart hook fires (this script).
 *   3. We do orphan-cleanup: any `.jsonl.live` whose heartbeat is stale
 *      (>5min old) gets restored to `.jsonl` so it shows up in /resume again
 *      — that's how crashed sessions become visible.
 *   4. We rename the current session's `.jsonl` -> `.jsonl.live`.
 *   5. The session continues writing to the renamed file via its open fd.
 *   6. There is no Stop/SessionEnd-time restore: when the session dies, its
 *      heartbeat goes stale; the *next* session's orphan-cleanup pass restores
 *      it.
 *
 *   Stop wiring (sealed 2026-05-19, G-P2 fix): the same main() now ALSO runs on
 *   Stop. This makes liveCloakSweep promptly hide pre-existing open tabs from
 *   the native /resume picker without waiting until the next NEW SessionStart
 *   elsewhere (the Owner's 'me sale otra vez' symptom). orphanCleanup on Stop
 *   surfaces just-crashed sessions in /resume within one session-end. Both
 *   passes are idempotent + no-clobber (existence guards at :104 and :180),
 *   so dual-triggering on SessionStart AND Stop is safe by construction.
 *
 * Edge cases:
 *   - First-ever session start: orphan cleanup is a no-op (nothing to restore),
 *     and the hide step finds the new .jsonl and renames it.
 *   - Heartbeat infra unavailable (`heartbeats/<uuid>.lock` missing): we treat
 *     the session as stale (restore). Conservative; better to show than to hide
 *     orphaned sessions.
 *   - Manual restore needed before any other session start: Owner can
 *     `mv <uuid>.jsonl.live <uuid>.jsonl` by hand or via /resume-restore.
 *   - Hook never throws: every IO failure is swallowed so the harness's
 *     SessionStart pipeline never breaks.
 *
 * Input shape (Claude Code SessionStart hook contract):
 *   stdin = JSON: { session_id: "<uuid>", source: "startup" | "resume" | ... }
 *
 * Output: nothing on stdout (silence is success). Errors on stderr but exit 0.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

// Heartbeat staleness threshold (recomputed 2026-05-19 from MEASURED reality).
// The previous comment overstated heartbeat cadence; the verified source of
// truth is lazarus-heartbeat.js with HEARTBEAT_THROTTLE_MS_NORMAL = 30 s on
// PreToolUse. Idle LLM generations (multi-minute turns with no tool calls)
// commonly exceed one minute, so the previous one-minute threshold
// misclassified live-but-idle sessions as stale, causing flapping (orphan
// cleanup restored them while the live-cloak sweep refused to re-hide them).
// 300 s = ten times the verified 30 s throttle floor: long enough that a
// truly dead session is detected, short enough that crashed sessions surface
// in the native /resume picker within roughly five minutes.
const HEARTBEAT_STALE_MS = 300 * 1000;
const PROJECTS_DIR = path.join(os.homedir(), ".claude", "projects");
const LAZARUS_DIR = path.join(os.homedir(), ".claude", "lazarus");

function readStdin() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch {
    return {};
  }
}

// Heartbeat lock files live under ~/.claude/lazarus/<proj>/heartbeats/<uuid>.lock,
// NOT under ~/.claude/projects/<proj>/heartbeats/. Maintained by
// hooks/lazarus-heartbeat.js (PreToolUse hook, 30s throttle). Same <proj>
// basename as the projects
// dir, so we just translate the parent.
function isHeartbeatStale(projName, uuid) {
  const hb = path.join(LAZARUS_DIR, projName, "heartbeats", `${uuid}.lock`);
  try {
    const st = fs.statSync(hb);
    return Date.now() - st.mtimeMs > HEARTBEAT_STALE_MS;
  } catch {
    // No heartbeat file = treat as stale (show in /resume)
    return true;
  }
}

function orphanCleanup() {
  let projDirs;
  try {
    projDirs = fs.readdirSync(PROJECTS_DIR);
  } catch {
    return;
  }
  for (const proj of projDirs) {
    const dir = path.join(PROJECTS_DIR, proj);
    let entries;
    try {
      const st = fs.statSync(dir);
      if (!st.isDirectory()) continue;
      entries = fs.readdirSync(dir);
    } catch {
      continue;
    }
    for (const f of entries) {
      if (!f.endsWith(".jsonl.live")) continue;
      const uuid = f.slice(0, -".jsonl.live".length);
      if (!isHeartbeatStale(proj, uuid)) continue;
      const livePath = path.join(dir, f);
      const restoredPath = path.join(dir, `${uuid}.jsonl`);
      try {
        // Don't clobber: if .jsonl already exists for some reason, skip
        if (fs.existsSync(restoredPath)) continue;
        fs.renameSync(livePath, restoredPath);
      } catch (e) {
        process.stderr.write(`resume-hide-live: orphan restore failed for ${f}: ${e.code || e.message}\n`);
      }
    }
  }
}

function hideOwnSession(sessionId) {
  if (!sessionId) return;
  let projDirs;
  try {
    projDirs = fs.readdirSync(PROJECTS_DIR);
  } catch {
    return;
  }
  for (const proj of projDirs) {
    const dir = path.join(PROJECTS_DIR, proj);
    const src = path.join(dir, `${sessionId}.jsonl`);
    if (!fs.existsSync(src)) continue;
    const dst = `${src}.live`;
    try {
      fs.renameSync(src, dst);
    } catch (e) {
      process.stderr.write(`resume-hide-live: hide failed for ${sessionId}: ${e.code || e.message}\n`);
    }
    return; // unique match
  }
  // It's normal for the .jsonl to not exist yet at SessionStart — claude may
  // create it on first message. In that case the hook is a no-op for this
  // session; the orphan-cleanup still ran.
}

/**
 * Live-cloak sweep: for every project, find `<uuid>.jsonl` whose heartbeat is
 * FRESH (session running cross-process) and rename to `.jsonl.live`. This is
 * the "catch up other terminals' live sessions on every new session start"
 * pass — gives Owner steady-state hide of pre-existing terminals after one
 * fresh session start, without needing them to all /restart.
 *
 * Cross-process rename on Windows requires the holder process opened the .jsonl
 * with FILE_SHARE_DELETE. Node's libuv defaults satisfy this; failures are
 * swallowed (ERROR_SHARING_VIOLATION) so the sweep is safe to attempt.
 *
 * Skips the current session's own UUID (already hidden by hideOwnSession).
 */
function liveCloakSweep(ownSessionId) {
  let projDirs;
  try {
    projDirs = fs.readdirSync(PROJECTS_DIR);
  } catch {
    return;
  }
  for (const proj of projDirs) {
    const dir = path.join(PROJECTS_DIR, proj);
    let entries;
    try {
      const st = fs.statSync(dir);
      if (!st.isDirectory()) continue;
      entries = fs.readdirSync(dir);
    } catch {
      continue;
    }
    for (const f of entries) {
      if (!f.endsWith(".jsonl")) continue;
      // UUID format only — avoid cloaking unrelated files
      const uuid = f.slice(0, -".jsonl".length);
      if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(uuid)) {
        continue;
      }
      if (ownSessionId && uuid === ownSessionId) continue;
      if (isHeartbeatStale(proj, uuid)) continue; // Only cloak LIVE
      const src = path.join(dir, f);
      const dst = `${src}.live`;
      try {
        if (fs.existsSync(dst)) continue; // Already cloaked
        fs.renameSync(src, dst);
      } catch (e) {
        // Swallow ERROR_SHARING_VIOLATION + EBUSY + similar; fall back to no-op
        if (e.code !== "EPERM" && e.code !== "EBUSY" && e.code !== "EACCES") {
          process.stderr.write(`resume-hide-live: live-cloak ${uuid}: ${e.code || e.message}\n`);
        }
      }
    }
  }
}

function main() {
  const input = readStdin();
  orphanCleanup();
  hideOwnSession(input.session_id);
  liveCloakSweep(input.session_id);
  process.exit(0);
}

main();
