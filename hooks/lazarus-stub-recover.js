#!/usr/bin/env node
// CANONICAL SOURCE — Power Pack repo. Deployed to ~/.claude/hooks/ via
// install-global.ps1 + tools/install_global_core.py session-safety manifest.
// Edit here, re-run install-global; never edit the deployed copy directly.
/**
 * lazarus-stub-recover.js — SessionStart hook.
 *
 * Vaccine for the "no conversation found with session ID <uuid>" pathology.
 *
 * Root pathology (observed 2026-05-21, multiple sessions across hosts):
 *   The cloak/restore race in resume-hide-live.js can leave a session's
 *   canonical `<uuid>.jsonl` populated by hook-output metadata stubs
 *   (hook_success attachments, pr-link, custom-title, turn_duration) WITHOUT
 *   any actual user/assistant turns. The Claude CLI's --resume path reads the
 *   canonical .jsonl by path, finds no turns, and emits "No conversation
 *   found". Meanwhile the REAL conversation lives in a sibling file —
 *   typically `<uuid>.jsonl.live` (the cloak target whose held fd never got
 *   promoted) or `<uuid>.jsonl.live.recovered-<date>` (a manual forensic
 *   snapshot).
 *
 * This hook walks ~/.claude/projects/<bucket>/ and, for each canonical .jsonl
 * that is a stub (zero user/assistant entries, no held-fd evidence), promotes
 * the best non-stub sibling into the canonical slot. Original stub is moved
 * to `<uuid>.jsonl.stub-corrupt-<unixMs>` so nothing is destroyed.
 *
 * Safety rails:
 *   - Skips the current session_id passed via stdin (never touch the running
 *     conversation).
 *   - Skips any .jsonl with at least one user/assistant turn (only stubs).
 *   - Skips if no candidate sibling has any user/assistant turn either
 *     (nothing to recover; leave the stub alone).
 *   - Skips if a sibling .jsonl.live exists AND its UUID appears in a live
 *     claude.exe/node.exe process command line (would clobber a live session).
 *   - Fail-open on every fs/process/parse error. Hook output is always `{}`
 *     so SessionStart pipeline never breaks.
 *
 * Performance:
 *   - Bounded scan: at most MAX_PROJECTS project buckets per run.
 *   - Per-file inspection bails after reading INSPECT_MAX_BYTES from head
 *     (real conversations have a user turn within the first ~4 KB).
 *   - Hard time budget: TIME_BUDGET_MS aborts the loop cleanly.
 *
 * Disable via env: LAZARUS_STUB_RECOVER=off
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const PROJECTS_DIR = path.join(os.homedir(), ".claude", "projects");
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const RECOVERED_RE = /^[0-9a-fA-F-]{36}\.jsonl\.live\.recovered-/;
const INSPECT_MAX_BYTES = 64 * 1024;
const TIME_BUDGET_MS = 2500;
const MAX_PROJECTS = 200;

// Always succeed quickly on stdout so the harness never marks us as failed.
process.stdout.write("{}");

if (process.env.LAZARUS_STUB_RECOVER === "off") process.exit(0);

function readStdinJson() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch { return {}; }
}

function safeReaddir(p) { try { return fs.readdirSync(p); } catch { return []; } }
function safeStat(p)    { try { return fs.statSync(p); } catch { return null; } }

/** Returns true iff the file contains at least one user/assistant entry within
 *  the first INSPECT_MAX_BYTES. */
function hasRealTurns(filePath) {
  let fd = -1;
  try {
    fd = fs.openSync(filePath, "r");
    const st = fs.fstatSync(fd);
    const len = Math.min(st.size, INSPECT_MAX_BYTES);
    if (len === 0) return false;
    const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, 0);
    const txt = buf.toString("utf-8");
    // Parse line-by-line, early-exit on first match. Tolerate truncated last
    // line by skipping JSON parse failures.
    let start = 0;
    for (let i = 0; i < txt.length; i++) {
      if (txt.charCodeAt(i) !== 10) continue; // newline
      const line = txt.slice(start, i).trim();
      start = i + 1;
      if (!line) continue;
      try {
        const o = JSON.parse(line);
        if (o && (o.type === "user" || o.type === "assistant")) return true;
      } catch {}
    }
    return false;
  } catch { return false; }
  finally { if (fd >= 0) try { fs.closeSync(fd); } catch {} }
}

// Lazy single-shot scan of running claude/node command lines. Returns a Set
// of lowercase UUIDs that are currently held by a live process. Empty set on
// any failure (fail-open: a false-negative means we MIGHT promote a sibling
// of a live session; the canonical-stub gate above already guards the common
// case, since a live session's canonical is rarely a stub).
let _liveCache = null;
function getLiveUuids() {
  if (_liveCache !== null) return _liveCache;
  _liveCache = new Set();
  if (process.platform !== "win32") return _liveCache;
  try {
    const { execFileSync } = require("child_process");
    const out = execFileSync(
      "powershell.exe",
      [
        "-NoProfile", "-NonInteractive", "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe' OR Name='claude.exe'\" | Select-Object -ExpandProperty CommandLine"
      ],
      { encoding: "utf8", timeout: 1200, windowsHide: true, stdio: ["ignore", "pipe", "ignore"] }
    );
    const re = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g;
    const matches = out.match(re);
    if (matches) for (const u of matches) _liveCache.add(u.toLowerCase());
  } catch {}
  return _liveCache;
}

function listCandidateSiblings(dir, uuid) {
  const cands = [];
  for (const name of safeReaddir(dir)) {
    if (!name.startsWith(uuid)) continue;
    if (name === `${uuid}.jsonl`) continue; // canonical is the target, not a candidate
    if (name === `${uuid}.jsonl.live` || RECOVERED_RE.test(name)) {
      const full = path.join(dir, name);
      const st = safeStat(full);
      if (st && st.isFile()) cands.push({ path: full, name, size: st.size, mtime: st.mtimeMs });
    }
  }
  return cands;
}

function recoverProject(projDir, ownSessionId, deadline) {
  const liveUuids = getLiveUuids();
  const entries = safeReaddir(projDir);
  let promoted = 0;
  for (const name of entries) {
    if (Date.now() > deadline) break;
    if (!name.endsWith(".jsonl")) continue;
    const uuid = name.slice(0, -".jsonl".length);
    if (!UUID_RE.test(uuid)) continue;
    if (ownSessionId && uuid === ownSessionId) continue;
    const canonical = path.join(projDir, name);
    // Skip files that already have turns — they're healthy.
    if (hasRealTurns(canonical)) continue;
    // Skip if a live process holds this UUID's fd — promoting could clobber
    // a session that's just early in its lifecycle (legitimately empty).
    if (liveUuids.has(uuid.toLowerCase())) continue;

    const cands = listCandidateSiblings(projDir, uuid);
    if (cands.length === 0) continue;

    // Pick the candidate with real turns AND largest size. If none has real
    // turns, this stub has no recoverable history; leave it alone.
    let best = null;
    for (const c of cands) {
      if (!hasRealTurns(c.path)) continue;
      if (!best || c.size > best.size) best = c;
    }
    if (!best) continue;

    // Atomic-ish swap: backup canonical, then rename candidate -> canonical.
    const bak = path.join(projDir, `${uuid}.jsonl.stub-corrupt-${Date.now()}`);
    try {
      fs.renameSync(canonical, bak);
    } catch (e) {
      if (e && e.code !== "ENOENT") {
        // Couldn't move out of the way — bail this UUID.
        continue;
      }
    }
    try {
      fs.renameSync(best.path, canonical);
      promoted++;
      process.stderr.write(
        `lazarus-stub-recover: ${uuid} promoted ${best.name} (${best.size}B) over stub\n`
      );
    } catch (e) {
      // Promote failed; try to restore the canonical from backup so we don't
      // leave the slot empty.
      try { fs.renameSync(bak, canonical); } catch {}
      process.stderr.write(
        `lazarus-stub-recover: ${uuid} promote failed: ${e.code || e.message}\n`
      );
    }
  }
  return promoted;
}

function main() {
  const input = readStdinJson();
  const own = input && typeof input.session_id === "string" ? input.session_id : null;
  const deadline = Date.now() + TIME_BUDGET_MS;
  let totalPromoted = 0;
  const projs = safeReaddir(PROJECTS_DIR).slice(0, MAX_PROJECTS);
  for (const p of projs) {
    if (Date.now() > deadline) break;
    const dir = path.join(PROJECTS_DIR, p);
    const st = safeStat(dir);
    if (!st || !st.isDirectory()) continue;
    try { totalPromoted += recoverProject(dir, own, deadline); } catch {}
  }
  if (totalPromoted > 0) {
    process.stderr.write(`lazarus-stub-recover: promoted ${totalPromoted} session(s)\n`);
  }
  process.exit(0);
}

try { main(); } catch { process.exit(0); }
