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

// 2026-09-16 -- STDIN DEADLOCK FIX. This was `fs.readFileSync(0, "utf-8")`.
//
// readFileSync BLOCKS THE EVENT LOOP, so an in-process watchdog is never
// scheduled: there is no version of this that keeps the sync call and adds a
// timeout beside it. And the harness's own per-hook budget does not save it --
// that kills the shell wrapper, a timeout kills the DIRECT CHILD ONLY, and the
// surviving node process holds the inherited stdout pipe that someone is still
// reading. Measured on the sibling hook (bfb40a1): two processes at 36.5 min,
// zero CPU, parent dead.
//
// This hook is the worst place in the estate for that, because it is a
// PreToolUse gate: it parks the user's turn itself. Same template as
// session-file-guard.js, which V-PIPE-STDIN-BOUNDED-EXITS drives with the pipe
// held open forever and which exits in ~1.1 s.
const STDIN_BUDGET_MS = 2000;

function readStdinBounded() {
  return new Promise((resolve) => {
    let input = "";
    let done = false;
    const finish = (value) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      // Detach AND pause. Removing the listener alone is not enough: a resumed
      // stream keeps its handle referenced, which turns "the read timed out"
      // into "the process never exits" -- the same hang one layer on.
      try { process.stdin.removeAllListeners(); process.stdin.pause(); } catch {}
      resolve(value);
    };
    const timer = setTimeout(() => finish(null), STDIN_BUDGET_MS);
    try {
      process.stdin.setEncoding("utf-8");
      process.stdin.on("data", (chunk) => { input += chunk; });
      process.stdin.on("end", () => finish(input));
      process.stdin.on("error", () => finish(null));
    } catch {
      finish(null);
    }
  });
}

// Absolute backstop. If anything above is wrong in a way I have not foreseen,
// this process dies rather than becoming another 36-minute orphan holding a
// pipe. NOT unref'd on purpose: an unref'd timer cannot keep the process alive
// to fire, and firing is the entire point.
const HARD_EXIT = setTimeout(() => {
  safeLog("hard-exit watchdog fired -- stdin never closed");
  process.exit(0);
}, STDIN_BUDGET_MS + 3000);

async function readStdin() {
  const raw = await readStdinBounded();
  clearTimeout(HARD_EXIT);
  if (raw === null) {
    // Fail OPEN, per this hook's contract everywhere else -- it is a policy
    // gate, not a security gate, and a policy gate that bricks the agent is
    // worse than one that misses a dispatch. But SAY SO: "no input" and "input
    // described nothing worth blocking" are different facts, and the tracker is
    // deliberately left untouched because we do not know what this dispatch was.
    failOpen("stdin never closed within budget -- guard did NOT inspect the dispatch");
  }
  try {
    return raw ? JSON.parse(raw) : {};
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

// Async because readStdin() is now a Promise (see the deadlock note above). The
// guard logic below is UNCHANGED -- only the way the input arrives moved.
// Keeping the analysis byte-identical is deliberate: this commit fixes a
// liveness bug and must not quietly alter what the guard blocks.
async function main() {
  // Platform gate — only Windows MSYS2 has the parallel-Agent drop.
  // Stays BEFORE the read on purpose: on a non-Windows host this hook must cost
  // nothing and must not touch stdin at all.
  if (process.platform !== "win32") {
    clearTimeout(HARD_EXIT);
    process.exit(0);
  }

  const payload = await readStdin();
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
    // 2026-09-15 MUTE-GATE FIX. The harness reads fd 2 on exit 2; a reason
    // written only to stdout arrives as "blocked, no reason given", which
    // forces a blind retry — the cross-repo dead screen. stderr FIRST.
    try { process.stderr.write(reason + "\n"); } catch {}
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
  // 2026-09-22. "create" was NOT in this list, so a dispatch carrying a genuine, explicit,
  // incremental write instruction ("create <path>.md ... append each finding before the next")
  // was judged to have none and blocked twice. A detector that matches the WORDING of an
  // instruction rather than its presence produces false blocks on correct dispatches, and the
  // author then rewords rather than fixes. Verbs widened; the shape of the clause is unchanged.
  const DURABLE_OUTPUT = [
    /\b(write|save|append|emit|dump|record|create|produce|persist|store)\b[^.]{0,60}\b(to|into|at|in)?\b[^.]{0,60}[\w./\\-]+\.(md|json|txt|csv|jsonl|log)\b/i,
    /\b(write|save|append|record|persist)\b[^.]{0,40}\b(findings|results|output|notes|progress)\b[^.]{0,40}\b(to|into)\b/i,
  ];
  const looksLong = LONG_RUNNING.some((re) => re.test(prompt));
  const hasDurable = DURABLE_OUTPUT.some((re) => re.test(prompt));

  // --- Contract preflight (2026-09-22, KobiiCraft VRC mission) ---------------
  //
  // ORIGIN, measured in the session that added this. A `kme-g1-ownership-arbiter` dispatch
  // carried the mandated durable-output clause and a Read/Grep/Glob toolset. The obligation was
  // UNSATISFIABLE BY CONSTRUCTION, and the only reason nothing was lost is that the arbiter
  // noticed and refused to claim success instead of reporting a file it never wrote.
  //
  // The defect is one level up from the prompt: this guard demanded a write and never asked
  // whether the agent could write. So it blocks satisfiable contracts on a verb technicality
  // (above) and waves through impossible ones — the two failure directions of one missing check.
  //
  // The general rule this mechanises: A MANDATORY OUTPUT MUST NEVER BE ASSIGNED TO AN EXECUTION
  // CONTEXT INCAPABLE OF PRODUCING IT. Same shape as a runtime gate with no runtime, a deploy
  // gate with no deploy access, or a screenshot gate with no display.
  //
  // FAIL-OPEN IS ABSOLUTE. An agent we cannot resolve is UNKNOWN, never "incapable": "could not
  // ask" and "was refused" are different facts and only one of them may block.
  const WRITE_TOOLS = ["write", "edit", "multiedit", "notebookedit"];
  function declaredTools(type) {
    try {
      const fsx = require("fs");
      const pathx = require("path");
      const osx = require("os");
      if (!type || type === "(default)") return null;          // unknown -> fail open
      if (!/^[A-Za-z0-9_-]+$/.test(type)) return null;          // never build a path from junk
      const roots = [];
      if (payload.cwd) roots.push(pathx.join(String(payload.cwd), ".claude", "agents"));
      roots.push(pathx.join(process.cwd(), ".claude", "agents"));
      roots.push(pathx.join(osx.homedir(), ".claude", "agents"));
      for (const root of roots) {
        const file = pathx.join(root, `${type}.md`);
        if (!fsx.existsSync(file)) continue;
        const head = fsx.readFileSync(file, "utf8").slice(0, 4000);
        const fm = head.match(/^---\r?\n([\s\S]*?)\r?\n---/);
        if (!fm) return null;
        const line = fm[1].match(/^tools:\s*(.+)$/im);
        if (!line) return null;                                 // no tools: key -> inherits all
        const raw = line[1].trim();
        if (raw === "*" || /\ball\b/i.test(raw)) return null;    // explicitly everything
        return raw.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
      }
      return null;                                              // not found -> UNKNOWN
    } catch { return null; }                                    // fail open, always
  }

  if (hasDurable &&
      String(process.env.CLAUDE_AGENT_CONTRACT_GUARD || "").toLowerCase() !== "off") {
    const tools = declaredTools(subagentType);
    if (tools && !tools.some((t) => WRITE_TOOLS.includes(t))) {
      const reason = [
        "AGENT-SOLO GUARD blocked an IMPOSSIBLE AGENT CONTRACT.",
        "",
        `This prompt requires durable output, and '${subagentType}' has no write tool.`,
        `  declared tools: ${tools.join(", ")}`,
        "",
        "The obligation is unsatisfiable by construction. The agent will either invent a file it",
        "never wrote, or (at best) spend its whole run and then tell you it could not comply.",
        "",
        "MEASURED 2026-09-22 (KobiiCraft, Visual Reconstruction Compiler): a kme-g1 dispatch",
        "carried the mandated 'write your findings as you go' clause with a Read/Grep/Glob",
        "toolset. Nothing was lost only because the arbiter noticed and said so.",
        "",
        "THREE CORRECT FIXES — pick one, do not reword the prompt:",
        "  (1) Dispatch an agent that HAS Write/Edit (e.g. general-purpose), keeping the clause.",
        "  (2) Keep this specialist and NARROW the obligation: delete the durable-output clause",
        "      and state explicitly that the parent persists the returned report. Then the",
        "      contract is honest and the parent owns the write.",
        "  (3) Give this agent a write tool in its definition, if that is truly its job.",
        "",
        "A guard that demands a write without checking the toolset is the same defect one level",
        "up, which is why this check exists beside the one above it.",
        "",
        `Blocked Agent: subagent_type=${subagentType}`,
        "Bypass for one dispatch: set CLAUDE_AGENT_CONTRACT_GUARD=off",
      ].join("\n");
      safeLog(`BLOCK-IMPOSSIBLE-CONTRACT\tsubagent=${subagentType}\ttools=${tools.join("|")}`);
      try { process.stderr.write(reason + "\n"); } catch {}
      process.stdout.write(JSON.stringify({ decision: "block", reason }));
      process.exit(2);
    }
  }

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
    // 2026-09-15 MUTE-GATE FIX. The harness reads fd 2 on exit 2; a reason
    // written only to stdout arrives as "blocked, no reason given", which
    // forces a blind retry — the cross-repo dead screen. stderr FIRST.
    try { process.stderr.write(reason + "\n"); } catch {}
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

// A synchronous try/catch cannot see a rejection from an async main, so the
// old form would have let an error escape as an unhandled rejection -- and a
// process that merely logs one stays alive holding the inherited stdout pipe,
// which is the 36-minute stall this migration exists to remove. Fail OPEN and
// ALWAYS exit.
try {
  main().catch((e) => failOpen(`unhandled: ${e && e.message ? e.message : "unknown"}`));
} catch (e) {
  failOpen(`unhandled: ${e && e.message ? e.message : "unknown"}`);
}
