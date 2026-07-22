#!/usr/bin/env node
/**
 * prompt_minimalism_gate.js — PreToolUse advisory on Task (Agent/subagent dispatch).
 *
 * CGF Workstream D (2026-07-22). OWNERSHIP_OVERLAP_AUDIT.md confirmed this is the
 * one genuinely-NEW mechanism in the whole CGF proposal: `prompt_pattern_optimizer.py`
 * finds CLAUDE.md token waste (n-gram repetition) and `prompt_defense_baseline.py`
 * checks security defenses (role override, secrets, XSS) — neither looks at whether
 * an outgoing sub-agent prompt hands over literal implementation instead of a
 * contract. The Agent tool's own description already states the doctrine this
 * enforces: "Never delegate understanding... push synthesis onto the agent instead
 * of doing it yourself" is about UNDER-specification; this hook is the OTHER failure
 * mode — OVER-specification, where the dispatching turn writes the sub-agent's code
 * for it inline instead of stating intent/constraints/done-criteria and trusting the
 * sub-agent's own judgment (Intent-Lock / API Bounding, CLAUDE.md "Anti-Monolith").
 *
 * Sibling precedent: `subagent-bash-avoidance-advisor.js` and `agent-solo-guard.js`
 * are both registered directly on `matcher: "Task"` in settings.json (not through
 * hook-dispatcher.js's CHAIN_MAP) — this file follows the same standalone shape.
 *
 * Conjunctive by design (T-D2A-GATE-KEYWORD-SCOPE-001 precedent: a false positive
 * that nags a legitimate technical constraint is worse than a missed one). Fires
 * ONLY when ALL of:
 *   1. The prompt contains a fenced code block (```...```).
 *   2. That block contains >= CODE_LINE_MIN lines matching real code-authoring
 *      syntax (function/class/def declarations, control flow, assignment) — not
 *      just a file path, a single identifier, or a shell one-liner.
 *   3. The prompt does NOT frame that block as existing/reference code (an
 *      "existing/current/reference/already/see below" cue within EXEMPT_WINDOW
 *      chars before the fence) — quoting real code as CONTEXT is legitimate per
 *      the Agent tool's own guidance ("explain what you've already learned").
 *
 * Silence otherwise: a prompt that names files, technologies, invariants, done-
 * gates, or constraints — however long or detailed — is exactly what a contract-
 * style delegation prompt should contain, and must never trip this gate.
 *
 * Level-2 (advisory, never blocks): mirrors d2a_gate.js's contract exactly.
 * Fail-open ABSOLUTE: any error -> empty stdout, exit 0.
 */
"use strict";

const fs = require("fs");

const CODE_LINE_MIN = 3;
const EXEMPT_WINDOW = 200;   // chars scanned before a fence for an "existing code" cue
const MAX_LEN = 20000;       // never classify a giant paste; silence and move on

// Lines that read as literal code-authoring, not prose or a path/identifier.
const CODE_LINE_RE = new RegExp(
  [
    "^\\s*(def|class|function|const|let|var)\\s+\\w+.*[:={(]",
    "^\\s*(if|elif|for|while|switch)\\b.*[:(]",
    "^\\s*(else|try|except|finally)\\s*:?\\s*$",
    "^\\s*(return|import|from|require|raise|yield)\\b",
    "^\\s*(public|private|async)\\s+\\w+",
    "^\\s*\\w+(\\.\\w+)*\\s*[+\\-*/]?=(?!=)\\s*\\S",
  ].join("|"),
  "i"
);

const EXEMPT_CUE_RE = /\b(existing|current|currently|already|reference|see (below|above)|as (shown|written)|the (test|file|code) (looks|reads|is))\b/i;

function readStdin() {
  try {
    const buf = fs.readFileSync(0, "utf-8");
    return buf ? JSON.parse(buf) : {};
  } catch (_) {
    return {};
  }
}

/** Every ```...``` fenced block, as {start, body} (start = char offset of the fence). */
function fencedBlocks(text) {
  const out = [];
  const re = /```[^\n]*\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    out.push({ start: m.index, body: m[1] || "" });
  }
  return out;
}

function codeLineCount(body) {
  return body.split("\n").filter((ln) => CODE_LINE_RE.test(ln)).length;
}

function isExempted(text, fenceStart) {
  const from = Math.max(0, fenceStart - EXEMPT_WINDOW);
  return EXEMPT_CUE_RE.test(text.slice(from, fenceStart));
}

/**
 * True only when the prompt hands over literal implementation via an
 * un-exempted, code-dense fenced block. Exported for tests.
 */
function isOverPrescriptive(prompt) {
  const text = String(prompt || "");
  if (!text || text.length > MAX_LEN) return false;
  const blocks = fencedBlocks(text);
  for (const b of blocks) {
    if (codeLineCount(b.body) >= CODE_LINE_MIN && !isExempted(text, b.start)) {
      return true;
    }
  }
  return false;
}

function buildAdvisory() {
  return (
    "PROMPT MINIMALISM advisory (CGF Workstream D, level-2 -- never blocks):\n" +
    "This sub-agent prompt contains a fenced code block that reads as literal\n" +
    "implementation (function/class/control-flow lines), not framed as existing\n" +
    "code shown for context. Per Intent-Lock / API Bounding (CLAUDE.md Anti-\n" +
    "Monolith) and the Agent tool's own doctrine, a delegation prompt should\n" +
    "state intent, constraints, invariants, and done-criteria -- and let the\n" +
    "sub-agent decide the implementation. If this code is genuinely required\n" +
    "(an exact existing signature, a fixed config snippet), proceed; otherwise\n" +
    "consider rephrasing as a contract."
  );
}

function run(input) {
  try {
    const data = input && typeof input === "object" ? input : {};
    if (data.tool_name !== "Task") return {};
    const toolInput = data.tool_input || {};
    const prompt = typeof toolInput.prompt === "string" ? toolInput.prompt : "";
    if (!isOverPrescriptive(prompt)) return {};
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        additionalContext: buildAdvisory(),
      },
    };
  } catch (_) {
    return {};
  }
}

module.exports = { run, isOverPrescriptive, fencedBlocks, codeLineCount };

if (require.main === module) {
  let data = {};
  try {
    data = readStdin();
  } catch (_) {
    data = {};
  }
  let out = {};
  try {
    out = run(data) || {};
  } catch (_) {
    out = {};
  }
  try {
    process.stdout.write(Object.keys(out).length ? JSON.stringify(out) : "");
  } catch (_) {
    /* stdout closed */
  }
  process.exit(0);
}
