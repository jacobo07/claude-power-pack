#!/usr/bin/env node
/**
 * bug-hunter-ceps-bridge.js -- PostToolUse failure capture.
 *
 * Watches command tool output for failure signatures and records each one
 * into CEPS via tools/ceps_capture.py, then emits a pp-ceps-analyst
 * advisory in additionalContext.
 *
 * Capture surface (D2): Bash AND PowerShell -- global CLAUDE.md mandates
 * the PowerShell tool for python/pytest/pip/git/npm on this host, so a
 * Bash-only matcher instruments the one surface the doctrine forbids.
 * Plus the harness internal-error sentinel on ANY tool, which is the most
 * frequently documented failure class in this repo's memory and had no
 * capture path at all.
 *
 * Ordering rule (D1): capture happens BEFORE the throttle check. The
 * throttle exists to spare the Owner repeated advisories, not to drop
 * events -- a collection gate placed ahead of the recorder silently
 * discards the very data it was built to keep.
 *
 * Fail-open: any capture failure still exits 0. Fail-open is not
 * fail-silent -- rejected records land in vault/ceps/rejections.jsonl and
 * tools/capture_liveness.py fails the build when fires exceed records.
 *
 * Sealed BL-HOOKS-REG-001 (2026-05-29). D1-D2 repair 2026-08-14 after
 * 63 fires produced 0 records over 80 days (vault/specs/capture-layer-liveness.md).
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';
const CAPTURE_TOOL = path.join(PP_PATH, 'tools', 'ceps_capture.py');
const FIRES_PATH = path.join(PP_PATH, 'vault', 'ceps', 'fires.jsonl');

const COMMAND_TOOLS = new Set(['Bash', 'PowerShell']);
const SENTINEL = '[Tool result missing due to internal error]';

// Ordered: first match wins, so the specific patterns precede the generic
// ones. `category` must be a member of tools/ceps.py VALID_CATEGORIES --
// a value outside that tuple is rejected at the validator and the event
// is lost, which is exactly the D1 defect this file was repaired for.
const SIGNATURES = [
  { rx: /\b(?:permission|access)\s+denied\b/i, category: 'env' },
  { rx: /\b(?:command not found|no se reconoce como nombre)\b/i, category: 'env' },
  { rx: /\bModuleNotFoundError\b/, category: 'env' },
  { rx: /\b(?:FAILED|AssertionError)\b/, category: 'regression' },
  { rx: /\b\d+ failed\b/i, category: 'regression' },
  { rx: /\bTraceback\s+\(most recent call last\)/, category: 'tooling' },
  { rx: /^\s*\w+Error:\s+\S+/m, category: 'tooling' },
  { rx: /\bException\b.*:.*\w/, category: 'tooling' },
  { rx: /\bSegmentation fault\b/, category: 'tooling' },
  { rx: /\bfatal:\s+\S+/i, category: 'tooling' },
  { rx: /\bCommand\s+failed\b/i, category: 'tooling' },
  { rx: /\bError\b.*:.*\w/, category: 'tooling' },
];

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
}

function extractOutput(payload) {
  const r = payload.tool_response || {};
  const parts = [];
  for (const key of ['output', 'stdout', 'stderr', 'error']) {
    if (typeof r[key] === 'string') parts.push(r[key]);
  }
  if (typeof r === 'string') parts.push(r);
  return parts.join('\n');
}

/** Leading executable of a command, so repeat failures of one tool share a
 *  subsystem bucket. `command[:40]` made every invocation unique, which
 *  kept `occurrences` pinned at 1 and starved every recurrence gate. */
function subsystemOf(toolName, command) {
  const first = String(command || '')
    .replace(/^[\s&$(]+/, '')
    .split(/[\s;|]+/)[0] || 'unknown';
  const exe = path.basename(first.replace(/['"]/g, '')).slice(0, 24);
  return `${toolName.toLowerCase()}:${exe || 'unknown'}`;
}

function classify(output) {
  if (output.includes(SENTINEL)) {
    // The harness lost the result frame; the subprocess itself usually
    // completed. Recorded as integration -- the defect is in the transport
    // between harness and tool, not in either one alone.
    return { category: 'integration', snippet: SENTINEL };
  }
  for (const s of SIGNATURES) {
    const m = output.match(s.rx);
    if (m) return { category: s.category, snippet: m[0].slice(0, 160) };
  }
  return null;
}

/** Append-only fire counter. capture_liveness.py compares this against
 *  events.jsonl; a producer that fires without recording is the failure
 *  mode that hid for 80 days, and only a durable count exposes it. */
function recordFire(toolName, category) {
  try {
    fs.mkdirSync(path.dirname(FIRES_PATH), { recursive: true });
    fs.appendFileSync(FIRES_PATH, JSON.stringify({
      ts: new Date().toISOString(),
      producer: 'bug-hunter-ceps-bridge',
      tool: toolName,
      category,
    }) + '\n');
  } catch (err) {
    process.stderr.write(`[ceps-bridge] fire log failed: ${err.message}\n`);
  }
}

function py(args, options) {
  return execFileSync(PY, args, Object.assign({
    encoding: 'utf8', timeout: 5000, windowsHide: true,
  }, options || {}));
}

function emitPass() {
  process.exit(0);
}

function emitAdvisory(text) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext: text,
    },
  }));
  process.exit(0);
}

(function main() {
  let payload;
  try {
    payload = JSON.parse(readStdin() || '{}');
  } catch (_e) {
    emitPass();
  }

  const toolName = String(payload.tool_name || '');
  const output = extractOutput(payload);
  if (!output || output.length < 12) emitPass();

  const isCommandTool = COMMAND_TOOLS.has(toolName);
  const isSentinel = output.includes(SENTINEL);
  if (!isCommandTool && !isSentinel) emitPass();

  const hit = classify(output);
  if (!hit) emitPass();

  const command = String(
    (payload.tool_input && payload.tool_input.command) || '');
  const subsystem = isSentinel && !isCommandTool
    ? `harness:${toolName.toLowerCase()}`
    : subsystemOf(toolName, command);

  recordFire(toolName, hit.category);

  // Capture first, throttle second.
  let recorded = '';
  try {
    recorded = py([CAPTURE_TOOL], {
      input: JSON.stringify({
        category: hit.category,
        subsystem,
        root_cause: hit.snippet,
        confidence: 'low',
        scope: 'project',
      }),
    }).trim();
  } catch (err) {
    process.stderr.write(`[ceps-bridge] capture failed: ${err.message}\n`);
    recorded = 'REJECTED capture-subprocess';
  }

  let throttled = 'go';
  try {
    throttled = py([
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import is_throttled;\n' +
      "print('throttled' if is_throttled('pp-ceps-analyst','bash-error',10) else 'go')",
    ], { timeout: 3000 }).trim();
  } catch (_e) {
    throttled = 'go';
  }
  if (throttled === 'throttled') emitPass();

  const advisory =
    `[Woz] [pp-ceps-analyst] ${hit.category} failure captured to CEPS (${recorded}).\n` +
    `Subsystem: ${subsystem}\n` +
    `Snippet: ${hit.snippet.slice(0, 80)}\n` +
    '-> Run /ceps query to inspect recurrence.';

  try {
    py([
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import mark_fired;\n' +
      `mark_fired('pp-ceps-analyst','bash-error', ${JSON.stringify(advisory)})`,
    ], { timeout: 3000 });
  } catch (err) {
    process.stderr.write(`[ceps-bridge] mark_fired failed: ${err.message}\n`);
  }

  emitAdvisory(advisory);
})();
