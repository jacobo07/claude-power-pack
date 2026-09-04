#!/usr/bin/env node
/**
 * agent-solo-guard.js — PreToolUse hook on Task (Agent spawn).
 *
 * Sealed 2026-05-28 after the 4th cross-repo recurrence of the parallel-
 * Agent transport-drop pattern on Windows. Hard-block companion to the
 * existing `subagent-bash-avoidance-advisor.js` (advisory) — that hook
 * warned about missing Bash-avoidance directives in the prompt, but did
 * not prevent the structural failure of dispatching multiple Agents in
 * one tool-batch. This hook closes that gap.
 *
 * Recurrence log (4 incidents in 14 days, 3 in 24h on 2026-05-28):
 *   1. KobiiCraft Sprint 8 Phase 2 audit  — oneshot-architect-auditor
 *   2. TUA-X    Sprint 8 (pre-Sprint 9)   — Explore fanout drop
 *   3. WhisprFlow APK 2026-05-28          — 3-parallel Explore, 1 missing
 *   4. TUA-X    Sprint 9 2026-05-28       — 2 parallel Explore + AskUserQ,
 *                                             Explore #1 returned the sentinel
 *                                             (this hook author's own violation)
 *
 * Doctrine source: ~/.claude/CLAUDE.md § "Coherence rules" Rule 4
 *   "Agent dispatch ALWAYS SOLO in its batch (sealed 2026-05-28 LuckyArena
 *   Sesión 1 turn, cross-project). Even ONE Agent + ONE Read in the same
 *   parallel batch produces [Tool result missing due to internal error] on
 *   the Read ~50% of the time on Windows. ... An Agent tool call must be
 *   the ONLY tool call in its message."
 *
 * Behavior:
 *   - Trigger: PreToolUse on Task (only).
 *   - Platform gate: if NOT Windows, exit 0 silently.
 *   - Inflight tracking via ~/.claude/state/agent-solo-tracker.json :
 *       [{ ts: <unix_ms>, prompt_head: "<first 60 chars>" }, ...]
 *     Window: 30 seconds. Anything older is GC'd on every read.
 *   - If non-empty after GC → HARD-BLOCK (decision="block", exit 2) with
 *     a clear pivot recommendation (inline Read/Glob/Grep in main thread).
 *   - Else → append our own entry, write tracker, exit 0 allow.
 *
 * Fail-OPEN by design: any parse/IO error → exit 0. A hook bug must
 * NEVER brick the workflow.
 *
 * Logs every invocation to ~/.claude/state/agent-solo-guard.log.
 *
 * Input shape (Claude Code PreToolUse contract):
 *   stdin = JSON: { tool_name: "Task", tool_input: { prompt, subagent_type, ... } }
 *
 * Output:
 *   on block: stdout = {"decision":"block","reason":"..."}, exit 2
 *   on pass : stdout empty, exit 0
 *   on fail-open: exit 0
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const STATE_DIR = path.join(os.homedir(), ".claude", "state");
const TRACKER_PATH = path.join(STATE_DIR, "agent-solo-tracker.json");
const LOG_PATH = path.join(STATE_DIR, "agent-solo-guard.log");
const WINDOW_MS = 30_000; // 30s window = "same batch"

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

function readStdin() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch (e) {
    failOpen(`stdin-parse-error: ${e && e.message ? e.message : "unknown"}`);
  }
}

function readTracker() {
  try {
    if (!fs.existsSync(TRACKER_PATH)) return [];
    const raw = fs.readFileSync(TRACKER_PATH, "utf-8");
    if (!raw.trim()) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeTracker(entries) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(TRACKER_PATH, JSON.stringify(entries));
  } catch (e) {
    safeLog(`tracker-write-error: ${e && e.message ? e.message : "unknown"}`);
  }
}

function gc(entries, now) {
  return entries.filter(e => typeof e.ts === "number" && (now - e.ts) < WINDOW_MS);
}

function main() {
  // Platform gate — only Windows MSYS2 has the parallel-Agent drop
  if (process.platform !== "win32") {
    process.exit(0);
  }

  const payload = readStdin();
  if (!payload || typeof payload !== "object") {
    failOpen("payload-not-object");
  }

  // Tool gate — only Task (the internal name for Agent dispatch)
  // 2026-09-04 REVIVAL. The harness renamed this tool "Task" -> "Agent". This
  // check tested only "Task", so it exited 0 on EVERY real dispatch. Proof: the
  // log's last entry was 2026-05-28, this guard's own self-test day — ZERO
  // decisions recorded in the 99 days since, across hundreds of dispatches.
  // settings.json carried the same dead "Task" matcher, so the hook was never
  // even invoked. Two independent causes, both silent, both fatal.
  //
  // A gate that cannot fire is indistinguishable from a gate that passes. Accept
  // both names so a future rename degrades to "fires too often", never to
  // "silently never fires".
  const TOOL_NAMES = new Set(["Task", "Agent"]);
  if (!TOOL_NAMES.has(payload.tool_name)) {
    process.exit(0);
  }

  const toolInput = payload.tool_input || {};
  const prompt = typeof toolInput.prompt === "string" ? toolInput.prompt : "";
  const subagentType = typeof toolInput.subagent_type === "string"
    ? toolInput.subagent_type
    : "(default)";

  const now = Date.now();
  const tracker = gc(readTracker(), now);

  if (tracker.length > 0) {
    // Hard block — there's already an Agent inflight within the same batch window
    const recent = tracker[tracker.length - 1];
    const ageS = ((now - recent.ts) / 1000).toFixed(1);
    const reason = [
      "AGENT-SOLO GUARD blocked a parallel Agent dispatch on Windows.",
      "",
      `Another Agent (${recent.subagent_type || "?"}) was dispatched ${ageS}s ago`,
      `with prompt head: "${recent.prompt_head || "(empty)"}"`,
      "",
      "Doctrine: ~/.claude/CLAUDE.md § Coherence rules, Rule 4 (sealed 2026-05-28):",
      "  'Agent dispatch ALWAYS SOLO in its batch. Even ONE Agent + ONE Read in",
      "   the same parallel batch produces [Tool result missing due to internal",
      "   error] on the Read ~50% of the time on Windows. ... An Agent tool",
      "   call must be the ONLY tool call in its message.'",
      "",
      "Empirical record: 4 cross-repo recurrences in 14 days",
      "  1. KobiiCraft Sprint 8 Phase 2 — oneshot-architect-auditor",
      "  2. TUA-X      Sprint 8       — Explore fanout drop",
      "  3. WhisprFlow APK 2026-05-28  — 3-parallel Explore",
      "  4. TUA-X      Sprint 9 2026-05-28 — 2 parallel Explore (this guard's origin)",
      "",
      "Two correct pivots (per CLAUDE.md):",
      "  (1) INLINE: do the work in main thread with Read/Glob/Grep — no transport",
      "      layer, no bridge hang. Recommended for code-base lookups.",
      "  (2) SERIALIZE: wait for the inflight Agent to return, then dispatch the",
      "      second Agent SOLO in its own message.",
      "",
      `Blocked Agent: subagent_type=${subagentType}`,
      "",
      "If this block is wrong (e.g. you intentionally want concurrent agents and",
      "accept the ~50% transport-drop risk), wait 30s for the tracker to GC, or",
      "delete ~/.claude/state/agent-solo-tracker.json manually.",
    ].join("\n");

    safeLog(`BLOCK\tsubagent=${subagentType}\tinflight=${tracker.length}\tage=${ageS}s`);
    process.stdout.write(JSON.stringify({ decision: "block", reason }));
    process.exit(2);
  }

  // Allow — record our entry
  // --- Unbounded-research check (2026-09-04, FIFA 11 Mod) -------------------
  //
  // ORIGIN. A general-purpose agent was dispatched to disassemble
  // DatabaseDisk::Load and GetRostersCRC. It ran 2h31m, consumed 112.9k tokens,
  // was instructed to REPORT rather than to WRITE, and so left nothing on disk.
  // The session was restarted and 100% of that work was lost. The main thread
  // had parked with no parallel work, which is the dead screen the Owner sees
  // across every repo.
  //
  // Doctrine had rule (I) for run_in_background but NO equivalent for Agent, so
  // nothing stopped it. This is that rule, mechanised.
  //
  // The remedy is one clause in the prompt, so the block is cheap to satisfy:
  // tell the agent to write findings to a file AS IT GOES. Then a timeout, a
  // restart or a dropped frame costs the tail of the work, never all of it.
  //
  // Scope is deliberately narrow: only dispatches that LOOK long-running. A
  // short "where is X defined" lookup is untouched.
  const LONG_RUNNING = [
    /\b(disassembl|reverse[- ]engineer|decompil)/i,
    /\b(audit|investigat|archaeolog|forensic)/i,
    /\b(exhaustive|comprehensive|every (?:call|site|reference))/i,
    /\b(trace|map out|survey|enumerate)\b[^.]{0,40}\b(codebase|binary|repo|corpus)/i,
  ];
  const DURABLE_OUTPUT = [
    /\b(write|save|append|emit|dump|record)\b[^.]{0,60}\b(to|into)\b[^.]{0,60}[\w./\\-]+\.(md|json|txt|csv|jsonl|log)\b/i,
    /\b(write|save|append)\b[^.]{0,40}\b(findings|results|output|notes|progress)\b[^.]{0,40}\b(to|into)\b/i,
  ];
  const looksLong = LONG_RUNNING.some((re) => re.test(prompt));
  const hasDurable = DURABLE_OUTPUT.some((re) => re.test(prompt));

  if (looksLong && !hasDurable &&
      String(process.env.CLAUDE_AGENT_BOUND_GUARD || "").toLowerCase() !== "off") {
    const reason = [
      "AGENT-SOLO GUARD blocked an UNBOUNDED research dispatch.",
      "",
      "This prompt looks long-running but never tells the agent to write anything",
      "to disk. If it times out, drops a frame, or the session restarts, 100% of",
      "its work is lost. There is no partial credit.",
      "",
      "MEASURED 2026-09-04 (FIFA 11 Mod): a general-purpose agent disassembling",
      "DatabaseDisk::Load ran 2h31m, burned 112.9k tokens, wrote nothing, and was",
      "lost entirely on restart. Doctrine had rule (I) for run_in_background but",
      "no equivalent for Agent. This is that rule.",
      "",
      "FIX. Add a durable-output clause to the prompt, e.g.:",
      '  "Write your findings to <repo>/knowledge/evidence/<topic>.md AS YOU GO,',
      '   appending each confirmed fact before moving on. Do not batch the write',
      '   to the end."',
      "",
      "Also state a BOUND (how many functions / addresses / minutes) and, while it",
      "runs, keep the main thread on parallel work. Never park the session.",
      "",
      `Blocked Agent: subagent_type=${subagentType}`,
      "Bypass for one dispatch: set CLAUDE_AGENT_BOUND_GUARD=off",
    ].join("\n");

    safeLog(`BLOCK-UNBOUNDED\tsubagent=${subagentType}`);
    process.stdout.write(JSON.stringify({ decision: "block", reason }));
    process.exit(2);
  }

  const entry = {
    ts: now,
    subagent_type: subagentType,
    prompt_head: prompt.slice(0, 60).replace(/\s+/g, " ").trim(),
  };
  tracker.push(entry);
  writeTracker(tracker);
  safeLog(`ALLOW\tsubagent=${subagentType}\thead="${entry.prompt_head}"`);
  process.exit(0);
}

try {
  main();
} catch (e) {
  failOpen(`unhandled: ${e && e.message ? e.message : "unknown"}`);
}
