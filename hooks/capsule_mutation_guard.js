#!/usr/bin/env node
/**
 * capsule_mutation_guard.js -- no mission successor mutates before RESUME_CERTIFIED.
 *
 * Spec: vault/specs/mission-capsule-rollover.md, invariant I1 and section 8 (G7-G10, G13, G19).
 *
 * A capsule-v2 mission worker starts in a fresh context with NO mutation authority. The supervisor
 * writes a marker per mission (<rollover state>/precert/<mission>.json, by tools/rollover.py
 * precert_write) BEFORE it spawns the worker; tools/rollover.py certify_flow flips it to certified.
 * Until then this guard denies, for THAT worker only:
 *   Write / Edit / MultiEdit / NotebookEdit            always
 *   Bash / PowerShell                                   unless every segment is on the observe list
 *
 * Which session is the worker, decided in this order (G7: the bg id is bound only AFTER the spawn
 * returns, and the worker may act before that):
 *   1. the marker's owner_session, or the session id starts with the marker's bg_id;
 *   2. the host registry (~/.claude/sessions/<pid>.json) names this session with the marker's
 *      `worker` name -- WE chose that name (`<mission>-e<epoch>`), so the match is exact;
 *   3. only when the registry has no record of this session at all: same cwd as the launch, inside
 *      the launch window. Anything else is not ours and is allowed untouched.
 *
 * Fail-closed ONLY for a session matched to an uncertified marker (an error judging its command
 * denies). For every other session it fails open, like every guard in its chain. Scope: mission
 * successors only (G19) -- an interactive /kresume pane has a human and is never denied here.
 * Kill switch: file <rollover state>/capsule-v2.off, or env CPP_CAPSULE_ROLLOVER=off (G13).
 * Remaining fail-open, stated: a dispatcher chain abandoned at its deadline (wired critical).
 *
 * Wired in hooks/hook-dispatcher.js 'PreToolUse-Bash-chain' and 'PreToolUse-Edit-chain'.
 * Test: hooks/tests/test-capsule-mutation-guard.js
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const LAUNCH_WINDOW_S = 300;
const MARKER_MAX_AGE_S = 24 * 3600;
const MUTATING = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit']);
const SHELLS = new Set(['Bash', 'PowerShell']);

function stateDir(env = process.env) {
  if (env.CPP_ROLLOVER_STATE_DIR) return env.CPP_ROLLOVER_STATE_DIR;
  return path.join(env.CLAUDE_STATE_DIR || path.join(os.homedir(), '.claude', 'state'), 'rollover');
}

function sessionsDir(env = process.env) {
  return env.CPP_CLAUDE_SESSIONS_DIR || path.join(os.homedir(), '.claude', 'sessions');
}

function switchedOff(env = process.env) {
  if ((env.CPP_CAPSULE_ROLLOVER || '').trim().toLowerCase() === 'off') return true;
  try { fs.statSync(path.join(stateDir(env), 'capsule-v2.off')); return true; } catch { return false; }
}

const norm = (p) => (p ? path.resolve(String(p)).toLowerCase() : '');

// G10: this guard's OWN list. Not the carrier list: that one admits test runners (which write
// files), `sort -o` and `git diff --output`, and lacks the commands certification needs.
const ALLOW = [
  /^git\s+(-C\s+\S+\s+)?(status|log|show|rev-parse|ls-files|cat-file|describe|blame|branch\s+--show-current|remote\s+-v|worktree\s+list)\b/i,
  /^git\s+(-C\s+\S+\s+)?diff\b(?!.*--output)/i,
  /^\S*python[0-9.]*(\.exe)?\s+(-u\s+)?\S*[\\/](rollover|mission_capsule)\.py\s+(resume|certify|status)\b/i,
  /^node(\.exe)?\s+\S*gsd-tools\.cjs\s+query\b/i,
  /^(cd|set-location|sl|pushd|popd)\b/i,
  /^(get-content|gc|get-childitem|gci|ls|dir|select-string|sls|get-item|gi|test-path|resolve-path|get-location|pwd|cat|head|tail|wc|grep|rg|type|where-object|where|select-object|select|measure-object|sort-object|format-table|ft|format-list|fl|out-string|convertfrom-json|convertto-json|write-output|write-host|echo|get-date|get-filehash)\b/i,
  /^\$env:[A-Za-z_][A-Za-z0-9_]*\s*=\s*['"][^'"]*['"]$/i,
];
const SAFE_REDIRECTS = /\s*\d?>&\d|\s*\*?\d?>\s*(\$null|\/dev\/null|nul)\b/gi;

// PowerShell's call operator with a quoted exe: `& 'C:\Program Files\Git\cmd\git.exe' -C x log`.
function unwrapCall(seg) {
  const m = seg.match(/^&\s*(['"])([^'"]+)\1\s*(.*)$/);
  if (!m) return seg;
  return `${path.basename(m[2]).replace(/\.exe$/i, '')} ${m[3]}`.trim();
}

function splitSegments(cmd) {
  const out = [];
  let cur = '', q = null;
  for (let i = 0; i < cmd.length; i++) {
    const ch = cmd[i];
    if (q) { cur += ch; if (ch === q) q = null; continue; }
    if (ch === '"' || ch === "'") { q = ch; cur += ch; continue; }
    if (ch === ';' || ch === '\n' || ch === '\r' || ch === '|' || (ch === '&' && cmd[i + 1] === '&')) {
      if (ch === '&' || (ch === '|' && cmd[i + 1] === '|')) i++;
      out.push(cur); cur = ''; continue;
    }
    cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim()).filter(Boolean);
}

function stripQuoted(s) {
  return s.replace(/"[^"]*"|'[^']*'/g, '""');
}

/** Pure: may a NOT-YET-CERTIFIED mission successor run this? {allow, reason} */
function judgeTool(toolName, toolInput) {
  if (MUTATING.has(toolName)) return { allow: false, reason: `${toolName} is a mutation` };
  if (!SHELLS.has(toolName)) return { allow: true, reason: 'not a mutation surface of this chain' };
  const command = (toolInput || {}).command;
  if (typeof command !== 'string' || !command.trim()) return { allow: false, reason: 'empty or unreadable command' };
  const bare = stripQuoted(command);
  if (/\$\(|`\(|<\(/.test(bare)) return { allow: false, reason: 'command substitution' };
  if (/>/.test(bare.replace(SAFE_REDIRECTS, ''))) return { allow: false, reason: 'output redirection writes a file' };
  for (const raw of splitSegments(command)) {
    const seg = unwrapCall(raw);
    if (!ALLOW.some((re) => re.test(seg))) return { allow: false, reason: `"${raw.slice(0, 80)}" is not an observe command` };
  }
  return { allow: true, reason: 'observe command' };
}

function registryName(sessionId, env) {
  let names;
  try { names = fs.readdirSync(sessionsDir(env)); } catch { return { found: false }; }
  for (const n of names) {
    if (!n.endsWith('.json')) continue;
    try {
      const rec = JSON.parse(fs.readFileSync(path.join(sessionsDir(env), n), 'utf8').replace(/^\uFEFF/, ''));
      if (rec && rec.sessionId === sessionId) return { found: true, name: rec.name || null };
    } catch { /* one unreadable record is not this session */ }
  }
  return { found: false };
}

/** The uncertified marker this session is the worker of, or null. */
function matchMarker(sessionId, cwd, env = process.env, nowS = Date.now() / 1000) {
  const dir = path.join(stateDir(env), 'precert');
  let files;
  try { files = fs.readdirSync(dir).filter((f) => f.endsWith('.json')); } catch { return null; }
  const open = [];
  for (const f of files) {
    let m;
    try { m = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); } catch {
      process.stderr.write(`capsule_mutation_guard: unreadable marker ${f} (written atomically; skipped)\n`);
      continue;
    }
    if (!m || m.certified_at) continue;
    if (typeof m.created_at === 'number' && nowS - m.created_at > MARKER_MAX_AGE_S) continue;
    open.push(m);
  }
  if (!open.length || !sessionId) return null;
  for (const m of open) {
    if (m.owner_session && m.owner_session === sessionId) return m;
    if (m.bg_id && String(sessionId).startsWith(m.bg_id)) return m;
  }
  const reg = registryName(sessionId, env);
  if (reg.found) return open.find((m) => m.worker && m.worker === reg.name) || null;
  return open.find((m) => !m.bg_id && m.cwd && norm(m.cwd) === norm(cwd)
    && typeof m.created_at === 'number' && nowS - m.created_at <= LAUNCH_WINDOW_S) || null;
}

function decide(req, env = process.env, nowS) {
  if (switchedOff(env)) return { allow: true, reason: 'capsule-v2 switched off' };
  if (!MUTATING.has(req.tool_name) && !SHELLS.has(req.tool_name)) return { allow: true, reason: 'not ours' };
  let marker;
  try { marker = matchMarker(req.session_id, req.cwd, env, nowS); } catch (e) {
    return { allow: true, reason: `guard could not read markers: ${e && e.message}` };
  }
  if (!marker) return { allow: true, reason: 'not a pre-certification mission successor' };
  try {
    const v = judgeTool(req.tool_name, req.tool_input);
    return { ...v, marker };
  } catch (e) {
    return { allow: false, reason: `guard error on a pre-certification worker: ${e && e.message}`, marker };
  }
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

async function main() {
  let raw = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const c of process.stdin) raw += c;
  } catch { return emit({ continue: true }); }
  if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
  let req;
  try { req = JSON.parse(raw); } catch { return emit({ continue: true }); }
  const v = decide(req);
  if (v.allow) return emit({ continue: true });
  const m = v.marker || {};
  return emit({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: `PRE-CERTIFICATION -- mission ${m.mission_id} worker ${m.worker || '?'}: ${v.reason}. `
        + 'You have no mutation authority until RESUME_CERTIFIED. Read-only until then: run '
        // `tool` is mission_capsule.py's own path, written into the marker by arm_successor (spec 11.5).
        // Never `resume_cmd`: that is the mission's slash command, not a script python can run.
        + `\`python ${m.tool || '<PP>/tools/mission_capsule.py'} resume --mission ${m.mission_id}\`, read the goal file `
        + 'and the tree, answer the exam with `... certify ...` as printed, then continue.',
    },
  });
}

if (require.main === module) main();
module.exports = { judgeTool, matchMarker, decide, splitSegments, stateDir };
