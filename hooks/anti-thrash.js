#!/usr/bin/env node
/**
 * anti-thrash.js — PreToolUse hook enforcing Rule 1 of Anti-Antipattern Protocol.
 *
 * Rule: 3+ consecutive Edit/Write on the same file path without an intervening
 * Read MUST be blocked. Claude must Read the file again, plan, and issue ONE
 * consolidated Edit.
 *
 * Behavior:
 *   - On Read  : counter[path] ← 0 (resets the streak for that path).
 *   - On Edit/Write:
 *       counter[path] ← counter[path] + 1
 *       If counter[path] >= 3 → emit blocking exit(2) with explanatory stderr.
 *
 * State persisted to ~/.claude/state/anti-thrash.json
 * Entries older than ANTI_THRASH_TTL_SECONDS are garbage-collected on each run.
 *
 * Enrolled by ~/.claude/settings.json PreToolUse matcher "Edit|Write|Read".
 * Derived from claude-doctor v0.0.3 audit 2026-04-23 (KobiiCraft workspace
 * registered 57 edit-thrash events across 76 sessions).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = process.env.HOME || process.env.USERPROFILE || os.homedir();
const STATE_FILE = path.join(HOME, '.claude', 'state', 'anti-thrash.json');
const LOG_FILE   = path.join(HOME, '.claude', 'state', 'anti-thrash.log');
const LIMIT = 3;                   // 3rd consecutive edit triggers block
const TTL_SECONDS = 3600;          // 1h: stale paths pruned

function logLine(decision, tool, filePath, count) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    const line = JSON.stringify({
      ts: new Date().toISOString(),
      pid: process.pid,
      decision, tool, filePath, count,
    }) + '\n';
    fs.appendFileSync(LOG_FILE, line);
  } catch (_) { /* never block on log failure */ }
}

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); }
  catch { return ''; }
}

function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
  catch { return { paths: {} }; }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function normalize(p) {
  if (!p) return p;
  const resolved = path.isAbsolute(p) ? p : path.resolve(p);
  return resolved.replace(/\\/g, '/').toLowerCase();
}

function prune(state) {
  const now = Date.now() / 1000;
  for (const k of Object.keys(state.paths)) {
    if (now - (state.paths[k].ts || 0) > TTL_SECONDS) {
      delete state.paths[k];
    }
  }
}

function main() {
  const raw = readStdin();
  if (!raw) process.exit(0);

  let event;
  try { event = JSON.parse(raw); }
  catch { process.exit(0); }

  const tool = event.tool_name;
  const filePath = event.tool_input && event.tool_input.file_path;
  if (!filePath) process.exit(0);

  const key = normalize(filePath);
  const state = loadState();
  prune(state);
  const now = Date.now() / 1000;

  if (tool === 'Read') {
    if (state.paths[key]) state.paths[key].count = 0;
    else state.paths[key] = { count: 0, ts: now };
    state.paths[key].ts = now;
    saveState(state);
    logLine('reset', tool, key, 0);
    process.exit(0);
  }

  if (tool === 'Edit' || tool === 'Write') {
    const entry = state.paths[key] || { count: 0, ts: now };
    const nextCount = entry.count + 1;

    if (nextCount >= LIMIT) {
      const msg =
        `ANTI-THRASH BLOCK (Rule 1, claude-doctor derived)\n` +
        `File: ${filePath}\n` +
        `Consecutive ${tool} attempts without intervening Read: ${nextCount}.\n` +
        `\n` +
        `Required recovery:\n` +
        `  1. Call Read on this exact path (full file or the specific region you need).\n` +
        `  2. Plan ONE comprehensive Edit that consolidates your outstanding changes.\n` +
        `  3. Emit that single Edit.\n` +
        `\n` +
        `Counter resets automatically on the next Read of this path.\n` +
        `Rule text: ~/.claude/CLAUDE.md → Anti-Antipattern Protocol, R1.\n` +
        `State file: ${STATE_FILE}`;
      process.stderr.write(msg + '\n');
      logLine('block', tool, key, nextCount);
      process.exit(2);
    }

    state.paths[key] = { count: nextCount, ts: now };
    saveState(state);
    logLine('allow', tool, key, nextCount);
    process.exit(0);
  }

  logLine('passthrough', tool, key, 0);
  process.exit(0);
}

main();
