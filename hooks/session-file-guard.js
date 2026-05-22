#!/usr/bin/env node
// CANONICAL SOURCE — Power Pack repo. Deployed to ~/.claude/hooks/ via
// install-global.ps1 + tools/install_global_core.py session-safety manifest.
// Edit here, re-run install-global; never edit the deployed copy directly.
/**
 * session-file-guard.js — PreToolUse hook.
 *
 * Bulletproof defense against involuntary destruction of session .jsonl files
 * inside ~/.claude/projects/. Sealed 2026-05-21 after the 4a600525 incident
 * where a (now-fixed) cleanup script nearly archived a week of KB-distillation
 * work into _empty_shells/ because the parent .jsonl looked empty (real
 * content lived in subagents).
 *
 * Triggers on every Bash and PowerShell tool call. If the command performs a
 * destructive operation on a path matching ~/.claude/projects/**\/*.jsonl, the
 * hook returns decision="block" (exit 2) with a verbose explanation. The agent
 * sees the block reason and can either rewrite the command or escalate to the
 * Owner for ratification.
 *
 * Sacred allowlist (NOT blocked — these are the legitimate flows):
 *   1. The cloak rename `<uuid>.jsonl` <-> `<uuid>.jsonl.live` performed by
 *      resume-hide-live.js. Detected by a Move/Rename ending in `.jsonl.live`
 *      OR starting from `.jsonl.live`.
 *   2. The archive flow `<uuid>.jsonl` -> `<proj>/_empty_shells/<uuid>.jsonl`
 *      performed by _oneshot_solitary_empty_shell_cleanup.js. Detected by the
 *      destination path containing `_empty_shells/`. This flow is now itself
 *      triple-gated upstream, so we trust the destination signal.
 *   3. The preserve flow `<uuid>.jsonl` -> `<proj>/_preserved/...`. Detected
 *      by the destination path containing `_preserved/`.
 *
 * Blocked patterns (any one is enough to deny):
 *   - Remove-Item / rm / del / Clear-Content / Out-File overwriting an
 *     existing .jsonl that's not in the allowlist
 *   - Move-Item / mv / Rename-Item on .jsonl outside the allowlist
 *   - >, > redirection truncating a .jsonl
 *   - Compress-Archive that DELETES source (-Force on RemoveSource flag)
 *
 * Fail-OPEN by design: if the hook itself crashes or can't parse the command,
 * it lets the operation proceed AND writes a diagnostic to
 * ~/.claude/state/session-guard-fail-open.log so we can audit later. This is
 * deliberate — a buggy guard MUST NOT brick the agent. The real safety net is
 * the daily snapshot backup, not this hook.
 *
 * Input shape: stdin = JSON: { tool_name: "Bash"|"PowerShell", tool_input: { command: "..." } }
 * Output: stdout = JSON: { decision: "block", reason: "..." } on block; nothing on pass.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

function fail_open(reason) {
  try {
    const logDir = path.join(os.homedir(), ".claude", "state");
    fs.mkdirSync(logDir, { recursive: true });
    const logPath = path.join(logDir, "session-guard-fail-open.log");
    fs.appendFileSync(logPath, `${new Date().toISOString()}\t${reason}\n`);
  } catch {}
  process.exit(0);
}

function readStdin() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch (e) {
    fail_open(`stdin parse: ${e.message}`);
  }
}

function block(reason) {
  process.stdout.write(JSON.stringify({
    decision: "block",
    reason: reason,
  }));
  process.exit(2);
}

const input = readStdin();
const toolName = input.tool_name || "";
if (toolName !== "Bash" && toolName !== "PowerShell") process.exit(0);

const command = (input.tool_input && input.tool_input.command) || "";
if (!command) process.exit(0);

// Refined 2026-05-21 — analyse the command CHUNK BY CHUNK. The previous version
// looked at the whole command string at once, which produced false positives
// when a multi-step command included BOTH a destructive verb (acting on an
// unrelated path) AND a separate read/use of a session .jsonl. Split on shell
// chaining operators and analyse each piece in isolation.
//
// Chaining operators (PowerShell + bash): ; && || newline | (pipe — splits
// into independent commands). We include `|` because piped chunks are also
// separate process invocations from the verb-target binding perspective.
const ALLOWLIST_MARKERS = [
  "_empty_shells",
  "_preserved",
  ".jsonl.live",
  ".shell.",
  ".bak.stub-",
  ".stub-collision-",
  ".bak-",
  ".preserved-",
  "_archived",
  "_audit_cache",
];
const PROJECTS_MARKERS = [
  ".claude/projects",
  ".claude\\projects",
  "~/.claude/projects",
  "$env:userprofile\\.claude\\projects",
  "%userprofile%\\.claude\\projects",
];
// Destructive verbs are matched as the FIRST token of a chunk OR after a `|`
// in PowerShell (e.g. `Get-ChildItem ... | Remove-Item`). We additionally
// require that the *target* in the same chunk be a session .jsonl path.
const DESTRUCTIVE_VERB_RE = /(^|\s|\|)(rm|del|erase|remove-item|move-item|rename-item|mv|ren|clear-content|out-file)(\s|$)/i;

function chunksOf(cmd) {
  // Split on ; && || newline. Do NOT split on | because pipelines often pass
  // file paths as args to the LAST stage which may be Remove-Item — but a
  // PowerShell `Get-ChildItem -Include *.jsonl | Remove-Item` DOES bind the
  // destructive verb to the jsonl file. To keep this safe, treat each piped
  // stage as its own chunk AND additionally evaluate the full pipeline.
  const pieces = cmd.split(/(?:&&|\|\||;|\r?\n)/g).map(s => s.trim()).filter(Boolean);
  const piped = [];
  for (const p of pieces) {
    for (const sub of p.split(/\|/g)) piped.push(sub.trim());
  }
  // Always include the full command as one chunk so pipelines like
  // `<command-with-jsonl> | Remove-Item` are caught.
  return [...new Set([...pieces, ...piped, cmd])];
}

function isProjectsJsonlPath(s) {
  const lower = s.toLowerCase();
  if (!lower.includes(".jsonl")) return false;
  // Strip trailing .live (cloak target) — those are sanctioned anyway, but
  // membership in projects still indicates a session asset.
  return PROJECTS_MARKERS.some(m => lower.includes(m.toLowerCase()));
}

function chunkIsBlocked(chunk) {
  const lower = chunk.toLowerCase();
  // 1) Allow-listed flows — sanctioned, never block.
  if (ALLOWLIST_MARKERS.some(m => lower.includes(m.toLowerCase()))) return null;
  // 2) Destructive verb?
  const hasVerb = DESTRUCTIVE_VERB_RE.test(chunk);
  // 3) Truncating > redirect to a .jsonl path?
  const redirMatch = chunk.match(/(?<![>])>(?!>)\s*["']?([^"'\s|&;]*\.jsonl)\b/i);
  if (!hasVerb && !redirMatch) return null;
  // 4) Find the operative path: the LAST .jsonl-like token in the chunk. Some
  //    real commands include unrelated .jsonl paths as args to readers — those
  //    chunks lack a destructive verb. If a destructive verb IS present and the
  //    last .jsonl token belongs to projects/, that's the operative target.
  const jsonlTokens = chunk.match(/["']?([^"'\s|&;,()`]+\.jsonl(?:\.live)?)["']?/gi) || [];
  if (jsonlTokens.length === 0) return null;
  // Look at every .jsonl token in this chunk — if ANY belongs to projects/ and
  // a destructive verb is present, the chunk is unsafe. Be conservative.
  const targetsProjects = jsonlTokens.some(t => isProjectsJsonlPath(t));
  if (!targetsProjects) return null;
  return {
    chunk,
    verbHit: hasVerb,
    redirHit: !!redirMatch,
    targets: jsonlTokens.filter(t => isProjectsJsonlPath(t)).slice(0, 3),
  };
}

const offenders = [];
for (const ch of chunksOf(command)) {
  const r = chunkIsBlocked(ch);
  if (r) offenders.push(r);
}
if (offenders.length === 0) process.exit(0);
const o = offenders[0];
const hasDestructiveVerb = o.verbHit;
const hasTruncateRedir = o.redirHit;
const jsonlMatches = o.targets;

// We got here: command touches a .jsonl in ~/.claude/projects, performs a
// destructive verb, and does NOT match any sanctioned-flow marker.
// BLOCK with a verbose, instructive reason.
const reason = [
  "Session-file-guard BLOCKED a destructive operation on a session .jsonl.",
  "",
  "Why: this command would delete/move/rename/truncate a .jsonl inside",
  "~/.claude/projects/ — exactly the kind of involuntary loss that the",
  "2026-05-21 4a600525 incident sealed against. Sessions live in those files.",
  "",
  "Detected verb pattern: " + (hasDestructiveVerb ? "destructive verb (rm/Remove-Item/Move-Item/Rename-Item/Clear-Content/Out-File)" : "truncating redirection (>)"),
  "Target(s): " + jsonlMatches.slice(0, 3).join(", "),
  "",
  "If this operation is legitimate, route it through one of the sanctioned flows",
  "(markers the guard recognizes):",
  "  - _empty_shells/ (archive, idempotent + reversible)",
  "  - _preserved/ (always-backup before any destructive op)",
  "  - .jsonl.live (LEGACY forensic — retired 2026-05-21 with resume-hide-live.js;",
  "      current marker hook is claude-power-pack/hooks/mark-live-session.js which",
  "      is append-only and never renames; existing .jsonl.live files may be",
  "      promoted to canonical by lazarus-stub-recover.js — BL-2026-05-21)",
  "  - .recovered-* / .jsonl.live.recovered-* (forensic backups of legacy cloaks)",
  "  - .stub-corrupt-* (lazarus-stub-recover.js vaccine backups — BL-2026-05-21)",
  "  - .bak-* / .preserved-* / .shell.* / .stub-collision-* / .bak.stub-* (timestamped backups)",
  "",
  "Or, if you genuinely need to delete a session, ask the Owner for explicit",
  "ratification — agent cannot self-grant deletion of session data.",
  "",
  "Full law: ~/.claude/SESSION_SAFETY_CONTRACT.md",
].join("\n");

block(reason);
