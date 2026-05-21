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

// Lazy cache of UUIDs that appear in any live claude/node process command
// line. Populated on first read by getLiveSessions(); empty set on scan
// failure so the discriminator stays fail-open (better to restore a few
// false-positives than to leave every crashed session hidden forever).
let _liveSessionsCache = null;
function getLiveSessions() {
  if (_liveSessionsCache !== null) return _liveSessionsCache;
  _liveSessionsCache = new Set();
  if (process.platform !== "win32") return _liveSessionsCache;
  try {
    const { execFileSync } = require("child_process");
    const out = execFileSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe' OR Name='claude.exe'\" | Select-Object -ExpandProperty CommandLine",
      ],
      { encoding: "utf8", timeout: 1500, windowsHide: true, stdio: ["ignore", "pipe", "ignore"] }
    );
    const uuidRe = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g;
    const matches = out.match(uuidRe);
    if (matches) for (const u of matches) _liveSessionsCache.add(u.toLowerCase());
  } catch {
    // Scan failed (PowerShell missing, timeout, permission) — return empty
    // set; downstream falls back to mtime + index.json.
  }
  return _liveSessionsCache;
}

// Replacement discriminator for orphanCleanup. The previous heartbeat-file
// lookup was unreliable: lazarus-heartbeat.js is not producing .lock files
// for the busiest project dirs (claude-power-pack=0, InfinityOps=0, KobiiCraft=0
// as of 2026-05-21), so the catch-block "missing heartbeat = stale" branch
// either timed out the 3s SessionStart budget or failed to rename
// downstream — net effect was zero restores and 69 accumulated orphans.
//
// New gate (3 layers):
//   1. mtime(.jsonl.live) <= 300s          -> ALIVE (recent write)
//   2. UUID in live process command line   -> ALIVE (idle-but-running)
//   3. index.json timestamp <= 300s        -> ALIVE (recent stop_hook)
//   else                                   -> DEAD, restore .jsonl.live -> .jsonl
function isOrphanedDead(projName, uuid, livePath) {
  let liveStat;
  try {
    liveStat = fs.statSync(livePath);
  } catch {
    return false;
  }
  if (Date.now() - liveStat.mtimeMs <= HEARTBEAT_STALE_MS) return false;

  const live = getLiveSessions();
  if (live.has(uuid.toLowerCase())) return false;

  const idxPath = path.join(LAZARUS_DIR, projName, "sessions", `${uuid}.json`);
  try {
    const raw = fs.readFileSync(idxPath, "utf-8");
    const idx = JSON.parse(raw);
    if (idx && typeof idx.timestamp === "string") {
      const idxAge = Date.now() - new Date(idx.timestamp).getTime();
      if (Number.isFinite(idxAge) && idxAge <= HEARTBEAT_STALE_MS) return false;
    }
  } catch {
    // No index.json or unparseable: fall through, mtime verdict stands.
  }

  return true;
}

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

// Collision-aware promotion: an empirically-observed failure mode (2026-05-21,
// 69 orphans on this host) was that .jsonl.live restore is blocked because a
// tiny stub .jsonl sits in the target slot — the harness or some script touches
// the UUID and writes only metadata lines, occupying the filename without ever
// holding real conversation content. Even with the discriminator above
// classifying the .jsonl.live as dead, the legacy no-clobber guard then skipped
// the restore forever. This helper classifies such stubs so the cleanup can
// safely sidestep them.
//
// Detection (sealed 2026-05-21, /resume-empty fix): the stub allowlist was
// brittle — empirically the harness writes `ai-title`, `pr-link`, and
// `attachment` (hook output) types BEFORE any conversation turn, and those
// types were not in the allowlist, so `looksLikeStubJsonl` returned false and
// the restore path was skipped, leaving the user staring at an empty /resume.
// The robust signal is the INVERSE: a stub is any small file that contains NO
// `user` or `assistant` entries. Real conversation history always contains at
// least one of those.
//
// SAFETY: the size cap (8 KB) is a fast-path bail — real conversations exceed
// it within the first turn. The idle gate (60 s) prevents misclassifying a
// session that JUST started and has only written metadata so far; once a
// session sits idle for a minute with zero turns, it is definitionally a stub.
//
// 2026-05-21 fix (sealed): when `siblingLiveExists` is true (a `.jsonl.live`
// of the same UUID is alongside the `.jsonl` under inspection), the idle
// gate is bypassed. Rationale: a sibling .live can ONLY arise from a
// previous cloak — meaning the real conversation already flows through the
// .live's open fd. Any sibling .jsonl is by definition a stub-collision
// created by the harness or hooks writing metadata-by-path. Waiting 60 s
// in that case is what causes the /resume-empty bug: the picker enumerates
// `.jsonl`, finds the freshly-written stub, shows it, the user opens it
// and the chat appears empty.
const STUB_MAX_BYTES = 8192;
const STUB_IDLE_MS = 60 * 1000;
function looksLikeStubJsonl(p, opts) {
  const siblingLiveExists = !!(opts && opts.siblingLiveExists);
  try {
    const st = fs.statSync(p);
    if (st.size > STUB_MAX_BYTES) return false;
    if (!siblingLiveExists && Date.now() - st.mtimeMs < STUB_IDLE_MS) return false;
    const txt = fs.readFileSync(p, "utf-8").trim();
    if (!txt) return true;
    const lines = txt.split(/\r?\n/);
    for (const line of lines) {
      if (!line.trim()) continue;
      let obj;
      try { obj = JSON.parse(line); } catch { return false; }
      if (obj.type === "user" || obj.type === "assistant") return false;
    }
    return true;
  } catch {
    return false;
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
      const livePath = path.join(dir, f);
      if (!isOrphanedDead(proj, uuid, livePath)) continue;
      const restoredPath = path.join(dir, `${uuid}.jsonl`);
      try {
        if (fs.existsSync(restoredPath)) {
          if (!looksLikeStubJsonl(restoredPath, { siblingLiveExists: true })) continue;
          let liveSt;
          try { liveSt = fs.statSync(livePath); } catch { continue; }
          // Only promote if .live carries strictly more content than the stub
          // — otherwise the swap loses data. Comparing sizes is sufficient
          // because looksLikeStubJsonl already proved .jsonl has zero turns.
          let stubSt;
          try { stubSt = fs.statSync(restoredPath); } catch { continue; }
          if (liveSt.size <= stubSt.size) continue;
          // Timestamped backup so concurrent restores never clobber each other.
          const bak = path.join(dir, `${uuid}.jsonl.bak.stub-${Date.now()}`);
          try {
            fs.renameSync(restoredPath, bak);
          } catch (e) {
            process.stderr.write(`resume-hide-live: stub-backup failed for ${uuid}: ${e.code || e.message}\n`);
            continue;
          }
        }
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
        if (fs.existsSync(dst)) {
          // .live already cloaked — but if a .jsonl ALSO exists, the harness
          // re-created a stub (ai-title / pr-link / hook attachments) by path
          // while the real conversation continues to flow through the holder's
          // fd into .jsonl.live. That stub is the source of the /resume-empty
          // bug: the picker enumerates .jsonl files and shows the stub.
          // Shadow-rename the stub out of the picker's enumeration scope so
          // the live session is fully hidden until it dies; orphanCleanup will
          // then promote .live -> .jsonl cleanly because the stub is gone.
          if (looksLikeStubJsonl(src, { siblingLiveExists: true })) {
            const shadow = path.join(dir, `${uuid}.jsonl.stub-collision-${Date.now()}`);
            try {
              fs.renameSync(src, shadow);
            } catch (e) {
              if (e.code !== "EPERM" && e.code !== "EBUSY" && e.code !== "EACCES" && e.code !== "ENOENT") {
                process.stderr.write(`resume-hide-live: shadow-stub ${uuid}: ${e.code || e.message}\n`);
              }
            }
          }
          continue;
        }
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

// Active-session marker (2026-05-21 sealed, Owner request):
//   Instead of cloaking OTHER live sessions out of the picker (the old
//   liveCloakSweep behavior), keep them visible in /resume and prefix their
//   displayed title with `⚡ [activa] ` so the Owner can SEE which sessions
//   are running in other panes and still click into them if intentional.
//   Picker source field is `type:"custom-title"` (empirically verified
//   2026-05-21 against the user's own .jsonl corpus — 13 of 25 sampled files
//   have it as their first line; the picker reads the LATEST custom-title in
//   the file so appending one is enough to override the displayed title).
//   The current session itself is still hidden via hideOwnSession — you
//   should never see yourself in your own /resume picker.
const ACTIVE_MARKER_PREFIX = "⚡ [activa] ";

function readLatestCustomTitle(filePath) {
  try {
    const st = fs.statSync(filePath);
    const start = Math.max(0, st.size - 16384);
    const fd = fs.openSync(filePath, "r");
    const buf = Buffer.alloc(st.size - start);
    fs.readSync(fd, buf, 0, buf.length, start);
    fs.closeSync(fd);
    const lines = buf.toString("utf-8").split(/\r?\n/);
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (!line) continue;
      try {
        const obj = JSON.parse(line);
        if (obj.type === "custom-title" && typeof obj.customTitle === "string") {
          return obj.customTitle;
        }
      } catch {}
    }
  } catch {}
  return null;
}

function appendCustomTitle(filePath, sessionId, title) {
  const line = JSON.stringify({
    type: "custom-title",
    customTitle: title,
    sessionId,
  }) + "\n";
  try {
    fs.appendFileSync(filePath, line, "utf-8");
  } catch (e) {
    if (e.code !== "EPERM" && e.code !== "EBUSY" && e.code !== "EACCES") {
      process.stderr.write(`resume-hide-live: append-title ${sessionId}: ${e.code || e.message}\n`);
    }
  }
}

function markLiveSessions(ownSessionId) {
  const live = getLiveSessions();
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
      if (!f.endsWith(".jsonl")) continue;
      const uuid = f.slice(0, -".jsonl".length);
      if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(uuid)) continue;
      if (ownSessionId && uuid === ownSessionId) continue;
      const filePath = path.join(dir, f);
      const isLive = live.has(uuid.toLowerCase());
      const currentTitle = readLatestCustomTitle(filePath) || "";
      const alreadyMarked = currentTitle.startsWith(ACTIVE_MARKER_PREFIX);
      if (isLive && !alreadyMarked) {
        const baseTitle = currentTitle || `session ${uuid.slice(0, 8)}`;
        appendCustomTitle(filePath, uuid, ACTIVE_MARKER_PREFIX + baseTitle);
      } else if (!isLive && alreadyMarked) {
        const restored = currentTitle.slice(ACTIVE_MARKER_PREFIX.length);
        appendCustomTitle(filePath, uuid, restored);
      }
    }
  }
}

function main() {
  const input = readStdin();
  orphanCleanup();
  hideOwnSession(input.session_id);
  // liveCloakSweep REPLACED 2026-05-21 by markLiveSessions per Owner request:
  // see "Active-session marker" block above for rationale. The cloak hid
  // OTHER live sessions out of the /resume picker entirely; the marker keeps
  // them visible AND differentiated so the Owner can still navigate to them.
  markLiveSessions(input.session_id);
  process.exit(0);
}

main();
