#!/usr/bin/env node
// CANONICAL SOURCE — Power Pack repo. Deployed to ~/.claude/hooks/ via
// install-global.ps1 + tools/install_global_core.py session-safety manifest.
// Edit here, re-run install-global; never edit the deployed copy directly.
// One-shot: archive solitary empty-shell .jsonl files into
// <proj>/_empty_shells/<uuid>.jsonl so they stop polluting /resume.
//
// HARDENED 2026-05-21 after the 4a600525 false-positive that nearly lost a
// week's worth of KB-distillation work. New triple-gate (ALL must pass before
// considering a .jsonl an "empty shell"):
//
//   GATE 1 — Subagent isolation: no sibling dir <uuid>/ with subagents/* or
//            tool-results/* (any contents). Such a dir means the parent is
//            the orchestrator of a multi-agent session; its .jsonl can be
//            small while the real conversation lives in the children. NEVER
//            move the parent if children exist.
//
//   GATE 2 — Strict no-content: zero user AND zero assistant entries (existing
//            heuristic kept). Inverse of "real conversation has at least one
//            user/assistant turn".
//
//   GATE 3 — Zero-turn meta-attestation: no `turn_duration` entry with
//            messageCount > 0, and no `away_summary` attestation. Either of
//            those means the harness recorded real conversation activity
//            even if user/assistant lines were truncated.
//
// Plus: ALWAYS backup to <proj>/_preserved/ before moving. Belt-and-braces.
// "Empty shell" archive is reversible by design (files moved to _empty_shells/,
// never deleted) — but the preserved copy is the bulletproof fallback.
//
// Usage:
//   node _oneshot_solitary_empty_shell_cleanup.js          # dry-run, prints plan
//   node _oneshot_solitary_empty_shell_cleanup.js --apply  # do it
"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

const APPLY = process.argv.includes("--apply");
const PROJECTS_DIR = path.join(os.homedir(), ".claude", "projects");
const IDLE_MS = 5 * 60 * 1000;
const SIZE_CAP = 16 * 1024;

const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

// GATE 1: detect a sibling <uuid>/ dir with subagent or tool-result content.
// Returns true if the parent is an orchestrator we must NOT touch.
function hasSubagentSiblings(projDir, uuid) {
  const childDir = path.join(projDir, uuid);
  try {
    const st = fs.statSync(childDir);
    if (!st.isDirectory()) return false;
  } catch { return false; }
  // Any file under subagents/ or tool-results/ (or anywhere recursively)
  // disqualifies the parent. Use a shallow then deep scan.
  const stack = [childDir];
  while (stack.length) {
    const d = stack.pop();
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { continue; }
    for (const ent of entries) {
      if (ent.isFile()) return true;
      if (ent.isDirectory()) stack.push(path.join(d, ent.name));
    }
  }
  return false;
}

// GATE 2 + 3 fused: returns true only if the file is conclusively a shell.
// Returns false at the FIRST sign of: user/assistant turn, turn_duration with
// messageCount > 0, or away_summary attestation. Any unparseable line also
// returns false (we never blindly move malformed content).
function isEmptyShell(filePath) {
  let buf;
  try { buf = fs.readFileSync(filePath, "utf-8"); } catch { return false; }
  if (!buf.trim()) return true;
  for (const ln of buf.split(/\r?\n/)) {
    if (!ln.trim()) continue;
    let o;
    try { o = JSON.parse(ln); } catch { return false; }
    if (o.type === "user" || o.type === "assistant") return false;
    if (o.message && (o.message.role === "user" || o.message.role === "assistant")) return false;
    if (o.type === "system" && o.subtype === "turn_duration" && typeof o.messageCount === "number" && o.messageCount > 0) return false;
    if (o.type === "system" && o.subtype === "away_summary") return false;
  }
  return true;
}

// Always-on backup: copy <src> to <proj>/_preserved/<uuid>.preserved-<ts>.jsonl
// before any destructive operation. Idempotent: skips if a same-day backup
// already exists.
function ensureBackup(projDir, uuid, srcPath) {
  const presDir = path.join(projDir, "_preserved");
  try { fs.mkdirSync(presDir, { recursive: true }); } catch {}
  const dateStamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const bakPath = path.join(presDir, `${uuid}.preserved-${dateStamp}.jsonl`);
  if (fs.existsSync(bakPath)) return bakPath;
  try {
    fs.copyFileSync(srcPath, bakPath);
    return bakPath;
  } catch (err) {
    throw new Error(`backup failed for ${uuid}: ${err.code || err.message}`);
  }
}

const plan = [];
for (const proj of fs.readdirSync(PROJECTS_DIR)) {
  const dir = path.join(PROJECTS_DIR, proj);
  let entries;
  try {
    if (!fs.statSync(dir).isDirectory()) continue;
    entries = fs.readdirSync(dir);
  } catch { continue; }
  const lives = new Set(entries.filter(f => f.endsWith(".jsonl.live")).map(f => f.slice(0, -".jsonl.live".length)));
  for (const f of entries) {
    if (!f.endsWith(".jsonl")) continue;
    const uuid = f.slice(0, -".jsonl".length);
    if (!UUID_RE.test(uuid)) continue;
    if (lives.has(uuid)) continue;
    const p = path.join(dir, f);
    let st;
    try { st = fs.statSync(p); } catch { continue; }
    if (st.size > SIZE_CAP) continue;
    if (Date.now() - st.mtimeMs < IDLE_MS) continue;
    if (hasSubagentSiblings(dir, uuid)) continue;  // GATE 1
    if (!isEmptyShell(p)) continue;                // GATES 2 + 3
    plan.push({ proj, uuid, size: st.size, mtime: st.mtime.toISOString(), srcPath: p, projDir: dir });
  }
}

console.log(`Found ${plan.length} solitary empty-shell .jsonl files (triple-gated).`);
if (!APPLY) {
  for (const e of plan.slice(0, 30)) console.log(`  DRY-RUN  ${e.size}B  ${e.mtime}  ${e.proj}/${e.uuid}.jsonl`);
  if (plan.length > 30) console.log(`  ... and ${plan.length - 30} more.`);
  console.log("\nRe-run with --apply to archive them.");
  process.exit(0);
}

let moved = 0, skipped = 0, backedUp = 0;
for (const e of plan) {
  try {
    ensureBackup(e.projDir, e.uuid, e.srcPath);
    backedUp++;
  } catch (err) {
    process.stderr.write(`backup-skip ${e.uuid}: ${err.message}\n`);
    skipped++;
    continue;
  }
  const archDir = path.join(e.projDir, "_empty_shells");
  try { fs.mkdirSync(archDir, { recursive: true }); } catch {}
  const dst = path.join(archDir, `${e.uuid}.jsonl`);
  try {
    if (fs.existsSync(dst)) { skipped++; continue; }
    fs.renameSync(e.srcPath, dst);
    moved++;
  } catch (err) {
    process.stderr.write(`move-skip ${e.uuid}: ${err.code || err.message}\n`);
    skipped++;
  }
}
console.log(`Archived ${moved}, backed-up ${backedUp}, skipped ${skipped}.`);
