#!/usr/bin/env node
/**
 * lazarus-livesnap.js - SessionStart + PreToolUse lightweight live snapshot.
 *
 * Why this exists (G-P1, sealed 2026-05-18):
 *   lazarus-snapshot.js captures the rich per-session snapshot ONLY on Stop.
 *   A hard crash / power-loss emits no Stop, so a crashed session's revive
 *   offer (lazarus_revive.py -> pending_resume.txt) is built from a stale or
 *   missing snapshot ("no funciona" warm-up profile, MC-LAZ-26).
 *
 *   There is NO ~5s timer in Claude Code. The only honest sub-Stop anchors
 *   are SessionStart and the PreToolUse path (throttled). This hook writes a
 *   FRESH minimal per-session marker on those events so lazarus_revive.py
 *   always has a recent "this session was alive as of <ts>" record, keyed by
 *   the reboot-durable session UUID (NOT PPID). The rich context still comes
 *   from lazarus-snapshot.js on clean Stop; this only closes the crash gap.
 *
 * Honest limit (Owner-accepted): an abrupt power-loss BETWEEN events loses at
 * most the delta since the last tool call. This is best-effort within Claude
 * Code's real event surface, NOT a power-loss-proof guarantee.
 *
 * Auditor-injected constraints:
 *   - #4 high-cadence path writes ONLY the per-session canonical file; the
 *     legacy mirror (last_session.json) stays exclusively in the Stop hook.
 *   - #5 strictly sub-budget on the PreToolUse path: single-flight throttle
 *     (>=30s, matching the real heartbeat floor) + a hard self-timeout +
 *     RAM-pressure skip; every failure swallowed; ALWAYS exit 0 (fail-open).
 *
 * Input (Claude Code hook contract): stdin JSON
 *   { session_id, cwd, hook_event_name, ... }
 * Output: nothing on stdout (silence = success). exit 0 always.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const HOME = os.homedir();
const LAZARUS_DIR = path.join(HOME, ".claude", "lazarus");
// Match the real heartbeat throttle floor (lazarus-heartbeat.js = 30s).
// A faster cadence would only add PreToolUse latency without finer recovery.
const THROTTLE_MS = 30 * 1000;
// Hard wall so this can never dominate a tool call's pre-budget.
const SELF_TIMEOUT_MS = 1500;
const startedAt = Date.now();

function overBudget() {
  return Date.now() - startedAt > SELF_TIMEOUT_MS;
}

function readStdin() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch (_) {
    return {};
  }
}

function sanitizeProjectId(cwd) {
  return String(cwd || "").replace(/[^a-zA-Z0-9-]/g, "-");
}

// RAM-pressure skip: skip ONLY under true starvation. A ratio gate is wrong
// on a 32GB dev box that idles at ~4% free (RAM-shield hooks active) - it
// would disable this hook entirely (a no-op hook is a scaffold illusion).
// The livesnap write is one small JSON (<100ms, ~0 alloc), so an absolute
// floor is the honest guard: below ~256MB the OS is thrashing and we yield.
const RAM_FLOOR_BYTES = 256 * 1024 * 1024;
function underRamPressure() {
  try {
    return os.freemem() < RAM_FLOOR_BYTES;
  } catch (_) {
    return false;
  }
}

function atomicWriteJson(target, obj) {
  const dir = path.dirname(target);
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (_) { /* ignore */ }
  const tmp = target + ".tmp." + process.pid + "." +
    Math.random().toString(16).slice(2);
  const fd = fs.openSync(tmp, "w");
  try {
    fs.writeFileSync(fd, JSON.stringify(obj, null, 2), "utf8");
    try { fs.fsyncSync(fd); } catch (_) { /* best-effort durability */ }
  } finally {
    fs.closeSync(fd);
  }
  fs.renameSync(tmp, target);
}

// Single-flight throttle: the lock file's mtime is the cadence gate. If the
// last live-snap for this project is younger than THROTTLE_MS, do nothing.
function throttledOut(projDir) {
  const lock = path.join(projDir, ".livesnap.lock");
  try {
    const st = fs.statSync(lock);
    if (Date.now() - st.mtimeMs < THROTTLE_MS) return true;
  } catch (_) { /* no lock yet -> not throttled */ }
  try {
    fs.mkdirSync(projDir, { recursive: true });
    fs.writeFileSync(lock, String(Date.now()), "utf8");
  } catch (_) { /* if we cannot stamp, still proceed once */ }
  return false;
}

function newestSessionLog(cwd) {
  // Cheap, reboot-durable context pointer: newest memory/sessions/session_*.md
  // for this project, if present. Pure read, no heavy walk.
  try {
    const sdir = path.join(cwd, "memory", "sessions");
    const files = fs.readdirSync(sdir)
      .filter((f) => f.startsWith("session_") && f.endsWith(".md"));
    if (!files.length) return null;
    files.sort();
    return path.join(sdir, files[files.length - 1]);
  } catch (_) {
    return null;
  }
}

function main() {
  const input = readStdin();
  const sessionId = input.session_id;
  const cwd = input.cwd || process.cwd();
  if (!sessionId) return;
  if (underRamPressure() || overBudget()) return;

  const projId = sanitizeProjectId(cwd);
  const projDir = path.join(LAZARUS_DIR, projId);
  if (throttledOut(projDir) || overBudget()) return;

  const sessDir = path.join(projDir, "sessions");
  const target = path.join(sessDir, sessionId + ".json");

  // Preserve any richer fields a prior Stop snapshot wrote; only refresh the
  // liveness envelope. NEVER downgrade a clean_exit record to "live".
  let prev = {};
  try {
    prev = JSON.parse(fs.readFileSync(target, "utf8")) || {};
  } catch (_) { prev = {}; }
  if (prev && prev.clean_exit === true) return;

  const snap = Object.assign({}, prev, {
    session_id: sessionId,
    cwd: cwd,
    project_id: projId,
    status: "live",
    clean_exit: false,
    source: "lazarus-livesnap",
    event: input.hook_event_name || "unknown",
    session_log_path: prev.session_log_path || newestSessionLog(cwd),
    live_ts: new Date().toISOString(),
    live_epoch_ms: Date.now(),
  });

  try {
    atomicWriteJson(target, snap);
  } catch (_) { /* fail-open: never block the event pipeline */ }
}

try {
  main();
} catch (_) {
  /* swallow everything: this hook must never break SessionStart/PreToolUse */
} finally {
  process.exit(0);
}
