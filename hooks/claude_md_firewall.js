#!/usr/bin/env node
'use strict';
// ---------------------------------------------------------------------------
// claude_md_firewall.js - PreToolUse firewall for the GLOBAL ~/.claude/CLAUDE.md
//   (CLAUDE.md Router M4, 2026-06-04, BL-CLAUDEMD-ROUTER).
//
// Blocks a Write/Edit/MultiEdit whose RESULT would push ~/.claude/CLAUDE.md to
// >= 40,000 chars (Claude Code's performance-warning threshold). This is a
// CHAR-BUDGET firewall, NOT prose-line counting: the file is mostly legitimate
// long-form always-on safety doctrine, so "block prose > N lines" would harm
// legitimate maintenance. The real metric is total chars vs the 40k limit.
//
// FAIL-OPEN: any parse/read error, or a non-CLAUDE.md target -> ALLOW (emit
// nothing = default allow). A firewall must never wedge an unrelated edit.
//
// Owner-side registration (HR-001 -- auto-mode cannot self-register hooks):
//   settings.json "hooks":
//   { "PreToolUse": [ { "matcher": "Write|Edit|MultiEdit",
//       "hooks": [ { "type": "command",
//         "command": "node \"<PP>/hooks/claude_md_firewall.js\"" } ] } ] }
//   (or add the script to the hook-dispatcher PreToolUse-Edit/Write chains.)
// ---------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');

const HARD_LIMIT = 40000;
const CM = path.join(os.homedir(), '.claude', 'CLAUDE.md');
const BOM = 0xFEFF;

function allow() { /* emit nothing -> harness default-allows */ }

function deny(reason) {
  try {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reason,
      },
    }));
  } catch (e) { void e; }
}

function norm(p) { return String(p || '').replace(/\\/g, '/').toLowerCase(); }

function readCM() {
  try {
    let t = fs.readFileSync(CM, 'utf8');
    if (t.charCodeAt(0) === BOM) { t = t.slice(1); }
    return t;
  } catch (e) { return null; }
}

function resultingText(tool, ti) {
  if (tool === 'Write') {
    return ti.content != null ? String(ti.content) : null;
  }
  const cur = readCM();
  if (cur == null) { return null; }
  if (tool === 'Edit') {
    const o = String(ti.old_string || '');
    const nw = String(ti.new_string || '');
    if (ti.replace_all) { return cur.split(o).join(nw); }
    return cur.indexOf(o) >= 0 ? cur.replace(o, nw) : cur;
  }
  if (tool === 'MultiEdit') {
    let r = cur;
    for (const e of (ti.edits || [])) {
      const o = String(e.old_string || '');
      const nw = String(e.new_string || '');
      r = e.replace_all ? r.split(o).join(nw) : r.replace(o, nw);
    }
    return r;
  }
  return null;
}

function main() {
  let payload;
  try {
    let raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.charCodeAt(0) === BOM) { raw = raw.slice(1); }
    payload = JSON.parse(raw);
  } catch (e) { allow(); return; }

  const tool = payload.tool_name || '';
  const ti = payload.tool_input || {};
  const fp = norm(ti.file_path);
  // Only guard the GLOBAL CLAUDE.md (not project CLAUDE.md files).
  if (!fp.endsWith('/.claude/claude.md')) { allow(); return; }

  let result;
  try { result = resultingText(tool, ti); }
  catch (e) { allow(); return; }      // fail-open
  if (result == null) { allow(); return; }

  const n = result.length;
  if (n >= HARD_LIMIT) {
    deny(`HR-CLAUDEMD-FIREWALL: this ${tool} would make ~/.claude/CLAUDE.md `
      + `${n} chars >= ${HARD_LIMIT} (Claude Code performance warning). `
      + `Trim provenance first (python tools/trim_claude_md.py --apply), or put `
      + `new long-form doctrine in vault/ -- but NEVER move the always-on `
      + `safety rules (Bash-Bridge, Parallel-Subagent, Anti-Waiting) out.`);
    return;
  }
  allow();
}

main();
