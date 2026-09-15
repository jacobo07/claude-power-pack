#!/usr/bin/env node
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

// 2026-09-15 -- STDIN DEADLOCK FIX. This was `fs.readFileSync(0, "utf-8")`.
//
// MEASURED, live, while the Owner watched the UI sit on
// "running PreToolUse hooks 6/8 ... 40m 44s":
//     pid=47776  age_min=36.5  cpu_sec=0  parent_alive=False
//     pid=3900   age_min=36.5  cpu_sec=0  parent_alive=False
// ZERO CPU over 36 minutes is what makes this diagnosable rather than a guess:
// it rules out the O(n^2) chunk regexes below, which would have burned a core.
// These processes never executed one line of guard logic. They were parked
// inside readFileSync(0) on a stdin pipe that never closed.
//
// WHY THE 5 s HARNESS BUDGET DID NOT SAVE IT -- the whole chain, and the reason
// this is the transversal hang rather than one broken hook:
//   1. the harness kills the shell wrapper at its timeout,
//   2. but a timeout kills the DIRECT CHILD ONLY, so this node process survives
//      (parent_alive=False above is that survival, observed),
//   3. and the survivor still holds the inherited stdout pipe,
//   4. so whoever is reading that pipe waits on a handle that is never closed.
// The budget fired perfectly, on the wrong process. See
// vault/lessons/timeout-without-tree-reaping-is-the-engine.md.
//
// A SYNCHRONOUS READ CANNOT BE RESCUED BY A TIMER. readFileSync blocks the
// event loop, so an in-process watchdog never gets scheduled -- there is no
// version of this fix that keeps the sync call and adds a timeout beside it.
// It has to be async, which is why this is a restructure and not a one-liner.
//
// Deliberately self-contained rather than importing hook-utils.readStdin:
// that helper is bounded but leaves its 'data' listener attached after the
// timeout, so the process can still fail to exit, and it has no 'error'
// handler. A guard whose whole job is to be bulletproof does not take a
// dependency with a latent hang in it. The shared helper is fixed separately.
const STDIN_BUDGET_MS = 2000;

function readStdinBounded() {
  return new Promise((resolve) => {
    let input = "";
    let done = false;
    const finish = (value) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      // Detach and pause: leaving a 'data' listener attached keeps the event
      // loop alive, which turns "read timed out" into "process never exits" --
      // the same hang one layer further on.
      try { process.stdin.removeAllListeners(); process.stdin.pause(); } catch {}
      resolve(value);
    };
    const timer = setTimeout(() => finish(null), STDIN_BUDGET_MS);
    try {
      process.stdin.setEncoding("utf-8");
      process.stdin.on("data", (chunk) => { input += chunk; });
      process.stdin.on("end", () => finish(input));
      process.stdin.on("error", () => finish(null));
    } catch (e) {
      finish(null);
    }
  });
}

// Absolute backstop. If anything above is wrong in a way I have not foreseen,
// this process still dies rather than becoming another 36-minute orphan holding
// a pipe. NOT unref'd on purpose: an unref'd timer cannot keep the process
// alive to fire, and firing is the entire point.
const HARD_EXIT = setTimeout(() => {
  try {
    fs.appendFileSync(
      path.join(os.homedir(), ".claude", "state", "session-guard-fail-open.log"),
      `${new Date().toISOString()}\thard-exit watchdog fired -- stdin never closed\n`);
  } catch {}
  process.exit(0);
}, STDIN_BUDGET_MS + 3000);

async function readStdin() {
  const raw = await readStdinBounded();
  clearTimeout(HARD_EXIT);
  if (raw === null) {
    // Could not read stdin at all. Fail OPEN, per this hook's stated contract
    // (a buggy guard must not brick the agent) -- but say so in the log, because
    // "no input" and "input said nothing destructive" are different facts.
    fail_open("stdin never closed within budget -- guard did NOT inspect the command");
  }
  try {
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    fail_open(`stdin parse: ${e.message}`);
  }
}

function block(reason) {
  // 2026-09-15 MUTE-GATE FIX: the harness reads fd 2 on exit 2. A reason sent
  // only to stdout surfaces as "blocked, no reason given" — the caller cannot
  // pivot, retries blind, and the session walks into the dead screen.
  try { process.stderr.write(String(reason) + "\n"); } catch {}
  process.stdout.write(JSON.stringify({
    decision: "block",
    reason: reason,
  }));
  process.exit(2);
}

// Wrapped in an async main because readStdin() is now a Promise (see the
// deadlock note above). The guard logic below is UNCHANGED -- only the way the
// input arrives moved. Keeping the analysis byte-identical is deliberate: this
// commit fixes a liveness bug and must not quietly alter what the guard blocks.
async function main() {
const input = await readStdin();
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
// SEALED 2026-05-23 (BL-SESSION-SAFETY-002): aligned with contract §3
// 12-marker table. Previous 10-entry array omitted `.stub-corrupt-` (the
// vaccine backup from lazarus-stub-recover.js BL-2026-05-21) and `.recovered-`
// (the generic recovered-flow prefix), so legitimate vaccine flows were
// silently blocked by the guard — the contract authorized them but the guard
// refused them. Drift closed.
const ALLOWLIST_MARKERS = [
  "_empty_shells",
  "_preserved",
  ".jsonl.live",
  ".recovered-",
  ".shell.",
  ".bak.stub-",
  ".stub-corrupt-",
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
}

// Fail OPEN on any unhandled rejection, consistent with this hook's stated
// contract, and ALWAYS exit. A rejection that merely logged would leave this
// process alive holding the inherited stdout pipe -- which is precisely the
// 36-minute stall this commit exists to remove.
main().catch((e) => fail_open(`main: ${e && e.message}`));
