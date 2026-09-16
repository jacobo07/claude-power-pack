#!/usr/bin/env node
/**
 * subagent-bash-avoidance-advisor.js — PreToolUse hook on Task (Agent spawn).
 *
 * Sealed 2026-05-28 after a TUA-X Sprint 8 incident where the
 * `oneshot-architect-auditor` subagent returned
 *   <error>[Tool result missing due to internal error]</error>
 * — the MSYS2 transport-drop sentinel — even though the parent's prompt was
 * carefully written to be Read-only. The subagent has its own internal tool
 * loop and probes Bash before consuming the prompt; that probe hung. The
 * parent's PreToolUse:Bash guard (windows-bash-bridge-guard.js) does NOT
 * see subagent-internal Bash, so it does not protect this surface.
 *
 * This hook closes the gap at the Task-spawn boundary.
 *
 * Behavior:
 *   - Trigger: PreToolUse on Task (only).
 *   - Platform gate: if NOT Windows (process.platform !== "win32"), exit 0
 *     silently. The MSYS2 bridge is the only hang failure mode this addresses.
 *   - Inspect tool_input.prompt for one of the Bash-avoidance phrases:
 *       "avoid bash", "no bash", "do not use bash", "do not call bash",
 *       "do not invoke bash", "do not run bash", "no shell", "bash-free",
 *       "prefer powershell", "use powershell"
 *     (case-insensitive, OR-joined)
 *   - If a phrase is present → exit 0 silently (compliant).
 *   - If a phrase is absent → exit 0 with stderr WARNING (advisory only).
 *     The warning surfaces in the agent's tool result and nudges adding the
 *     directive on next spawn. NEVER blocks.
 *
 * Fail-OPEN by design: parse failure or unexpected shape → exit 0. A buggy
 * advisor MUST NOT brick the workflow.
 *
 * Logs every invocation to ~/.claude/state/subagent-advisor.log for
 * cross-session pattern surfacing.
 *
 * Input shape (Claude Code PreToolUse hook contract):
 *   stdin = JSON: { tool_name: "Task", tool_input: { prompt: "...", ... } }
 *
 * Output: stderr = WARNING text on non-compliant; stdout = nothing.
 *         Exit code 0 always (advisory).
 *
 * Doctrine: ~/.claude/knowledge_vault/core/BL-2026-05-28-subagent-bash-bridge-recovery.md
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const STATE_DIR = path.join(os.homedir(), ".claude", "state");
const LOG_PATH = path.join(STATE_DIR, "subagent-advisor.log");

function safeLog(line) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.appendFileSync(LOG_PATH, `${new Date().toISOString()}\t${line}\n`);
  } catch {
    // never throw from a hook
  }
}

function failOpen(reason) {
  safeLog(`fail-open\t${reason}`);
  process.exit(0);
}

// 2026-09-16 -- STDIN DEADLOCK FIX. This was `fs.readFileSync(0, "utf-8")`,
// which BLOCKS THE EVENT LOOP: if the pipe never closes the process parks at
// zero CPU forever and no in-process watchdog can save it, because no timer is
// ever scheduled. The harness's per-hook budget kills the shell WRAPPER; a
// timeout kills the direct child only, and the survivor holds the inherited
// stdout pipe. bfb40a1 has the live measurement.
//
// This advisor fires on EVERY Agent dispatch, so it is one of the most
// frequently spawned hooks in the estate -- which makes it a cheap way to
// accumulate parked processes.
const { readStdinRaw, armHardExit } = require("./hook-utils");

const STDIN_BUDGET_MS = 2000;
const HARD_EXIT = armHardExit(STDIN_BUDGET_MS + 3000,
  () => safeLog("hard-exit watchdog fired -- stdin never closed"));

async function readStdin() {
  const { raw } = await readStdinRaw(STDIN_BUDGET_MS);
  clearTimeout(HARD_EXIT);
  if (raw === null) {
    // Fail OPEN -- this is an advisory, and an advisory that bricks a dispatch
    // is worse than one that misses it. But SAY SO: "no input" and "the prompt
    // already had the directive" are different facts and used to be spelled
    // the same silence.
    failOpen("stdin never closed within budget -- advisor did NOT inspect the dispatch");
  }
  try {
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    failOpen(`stdin-parse-error: ${e && e.message ? e.message : "unknown"}`);
  }
}

const AVOIDANCE_PHRASES = [
  "avoid bash",
  "no bash",
  "do not use bash",
  "do not call bash",
  "do not invoke bash",
  "do not run bash",
  "no shell",
  "bash-free",
  "prefer powershell",
  "use powershell",
  // Spanish variants (Owner often writes in ES)
  "evita bash",
  "no uses bash",
  "no llames a bash",
  "no invoques bash",
  "usa powershell",
  "prefiere powershell",
];

function hasAvoidanceDirective(prompt) {
  if (!prompt || typeof prompt !== "string") return false;
  const lower = prompt.toLowerCase();
  return AVOIDANCE_PHRASES.some((p) => lower.includes(p));
}

// Async because readStdin() is now a Promise. The advisory logic below is
// UNCHANGED -- only the way the input arrives moved.
async function main() {
  // Platform gate — only Windows MSYS2 has the bridge hang.
  // Stays BEFORE the read: on a non-Windows host this hook must cost nothing
  // and must not touch stdin at all.
  if (process.platform !== "win32") {
    clearTimeout(HARD_EXIT);
    process.exit(0);
  }

  const payload = await readStdin();
  if (!payload || typeof payload !== "object") {
    failOpen("payload-not-object");
  }

  // Tool gate — only Task
  // 2026-09-04: the harness renamed this tool "Task" -> "Agent". Testing only
  // "Task" made this advisor a no-op on every real dispatch for 99 days, the
  // same silent death measured in agent-solo-guard.js. Accept both.
  if (!new Set(["Task", "Agent"]).has(payload.tool_name)) {
    process.exit(0);
  }

  const toolInput = payload.tool_input || {};
  const prompt = typeof toolInput.prompt === "string" ? toolInput.prompt : "";

  if (hasAvoidanceDirective(prompt)) {
    safeLog("compliant");
    process.exit(0);
  }

  // Non-compliant — advisory warning to stderr
  const subagentType = typeof toolInput.subagent_type === "string"
    ? toolInput.subagent_type
    : "(default)";

  const warning = [
    "[BL-2026-05-28 advisory] Subagent spawn on Windows lacks an explicit",
    "Bash-avoidance directive in its prompt. The MSYS2 bridge has dropped",
    "stdout on subagent-internal Bash probes before, returning the",
    "'[Tool result missing due to internal error]' sentinel.",
    "",
    "Recommended: add ONE of these phrases to the subagent prompt body:",
    "  - Prefer Read/Grep/Glob. Avoid Bash; use PowerShell if shell is needed.",
    "  - Evita Bash; prefiere PowerShell para cualquier comando shell.",
    "",
    `subagent_type: ${subagentType}`,
    "doctrine: ~/.claude/knowledge_vault/core/BL-2026-05-28-subagent-bash-bridge-recovery.md",
    "",
    "This is ADVISORY only — execution will proceed. If the spawn hangs,",
    "do NOT retry the same Agent call. Pivot inline (Read in main thread)",
    "or single-redispatch with the directive added. See doctrine §3.",
  ].join("\n");

  safeLog(`advisory-warning\tsubagent=${subagentType}`);
  process.stderr.write(warning + "\n");
  process.exit(0);
}

// A synchronous try/catch cannot see a rejection from an async main, so without
// the .catch an error would escape as an unhandled rejection -- and a process
// that merely logs one stays ALIVE holding the inherited stdout pipe, which is
// the stall this migration removes. Fail OPEN and ALWAYS exit.
try {
  main().catch((e) => failOpen(`unhandled: ${e && e.message ? e.message : "unknown"}`));
} catch (e) {
  failOpen(`unhandled: ${e && e.message ? e.message : "unknown"}`);
}
