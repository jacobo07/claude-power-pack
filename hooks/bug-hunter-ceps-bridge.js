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
// `quotable: true` marks a signature that appears verbatim in ordinary
// SOURCE CODE (`except Exception as e:`, `Error ? err.message : ...`).
// When a content-producing command prints one, the tool is succeeding at
// showing you a file -- it is not failing. 51 of the first 75 stored
// events were this: greps and file reads of Python and JS, recorded as
// tooling failures because the classifier read text and never asked
// whether anything failed (measured 2026-08-26).
//
// The `env` signatures are NOT quotable: "permission denied" from a grep
// is that grep genuinely failing, and its own output would not contain
// the phrase otherwise.
const SIGNATURES = [
  { rx: /\b(?:permission|access)\s+denied\b/i, category: 'env' },
  { rx: /\b(?:command not found|no se reconoce como nombre)\b/i, category: 'env' },
  { rx: /\bModuleNotFoundError\b/, category: 'env', quotable: true },
  { rx: /\b(?:FAILED|AssertionError)\b/, category: 'regression', quotable: true },
  // `\b\d+ failed\b` matched "0 failed" -- the SUCCESS half of every
  // pytest summary line -- and filed it as a regression (2026-08-25).
  // The negative lookahead refuses an all-zero quantity and still admits
  // "10 failed", whose leading digit is not a zero run.
  { rx: /\b(?!0+\b)\d+ failed\b/i, category: 'regression' },
  { rx: /\bTraceback\s+\(most recent call last\)/, category: 'tooling', quotable: true },
  { rx: /^\s*\w+Error:\s+\S+/m, category: 'tooling', quotable: true },
  { rx: /\bException\b.*:.*\w/, category: 'tooling', quotable: true },
  { rx: /\bSegmentation fault\b/, category: 'tooling', quotable: true },
  { rx: /\bfatal:\s+\S+/i, category: 'tooling', quotable: true },
  { rx: /\bCommand\s+failed\b/i, category: 'tooling', quotable: true },
  { rx: /\bError\b.*:.*\w/, category: 'tooling', quotable: true },
];

// Commands whose whole job is to emit file content. Error-shaped text in
// their stdout is the FILE's text, not theirs.
const READ_TOOLS = new Set([
  'grep', 'rg', 'egrep', 'fgrep', 'ack', 'ag', 'cat', 'head', 'tail',
  'sed', 'awk', 'less', 'more', 'type', 'select-string', 'get-content',
  'gc', 'find', 'ls', 'dir', 'diff', 'git', 'jq',
]);

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
/** Navigation and environment prefixes. These are not the failing tool;
 *  they are what someone typed to reach it. Taking the leading token of a
 *  chain bucketed `cd /repo && pytest` as `cd`, and 15 of 19 stored
 *  regressions carried the subsystem `bash:cd` -- a recurrence key that
 *  fuses every command sharing a directory change. */
const NAV_PREFIXES = new Set([
  'cd', 'chdir', 'pushd', 'popd', 'set-location', 'sl',
  'export', 'set', 'source', '.', 'env', 'call',
]);

function leadingExe(segment) {
  const first = String(segment || '')
    .replace(/^[\s&$(]+/, '')
    .split(/\s+/)[0] || '';
  return path.basename(first.replace(/['"]/g, '')).slice(0, 24);
}

function subsystemOf(toolName, command) {
  const raw = String(command || '');
  const segments = raw.split(/&&|\|\||[;|]/).map((s) => s.trim()).filter(Boolean);
  let exe = '';
  for (const seg of segments) {
    // `$env:VAR='x'` / `VAR=x` set the environment; they run nothing.
    if (/^\$?(?:env:)?[A-Za-z_][\w:]*=/.test(seg)) continue;
    const cand = leadingExe(seg);
    if (!cand || NAV_PREFIXES.has(cand.toLowerCase())) continue;
    exe = cand;
    break;
  }
  // A command that is ONLY navigation really is that command; falling
  // back to the leading token keeps the bucket honest rather than empty.
  if (!exe) exe = leadingExe(segments[0] || raw);
  return `${toolName.toLowerCase()}:${exe || 'unknown'}`;
}

// A dropped result frame IS the sentinel -- the harness substitutes it for
// the entire result. A long file that merely CONTAINS the literal is that
// file's content, quoted, not a transport failure experienced here.
// Reading this very file recorded two phantom integration failures before
// the bound existed (2026-08-25T14:15:51Z and 16:13:03Z).
const SENTINEL_FRAME_MAX = 200;

/** Did the tool FAIL, as opposed to print text about failure?
 *
 *  'yes' / 'no' / 'unknown'. The harness's field names are not contracted
 *  anywhere we control, so every known spelling is probed and an absent
 *  signal degrades to 'unknown' rather than to a guess. recordFire logs
 *  which arm was taken, so the question "does this harness even give us a
 *  failure signal?" is answered by measurement instead of by assumption. */
function failureSignal(toolResponse) {
  const r = toolResponse || {};
  if (typeof r.error === 'string' && r.error.trim()) return 'yes';
  if (r.is_error === true || r.isError === true) return 'yes';
  for (const k of ['exit_code', 'exitCode', 'returncode', 'status', 'code']) {
    const v = r[k];
    if (typeof v === 'number') return v === 0 ? 'no' : 'yes';
  }
  if (r.is_error === false || r.isError === false) return 'no';
  return 'unknown';
}

/** True when the command's job is to print file content, so error-shaped
 *  text in its output belongs to the file and not to the command. */
function isReadCommand(command) {
  const raw = String(command || '');
  const segments = raw.split(/&&|\|\||[;|]/).map((s) => s.trim()).filter(Boolean);
  let sawExec = false;
  for (const seg of segments) {
    if (/^\$?(?:env:)?[A-Za-z_][\w:]*=/.test(seg)) continue;
    const cand = leadingExe(seg).toLowerCase();
    if (!cand || NAV_PREFIXES.has(cand)) continue;
    sawExec = true;
    if (!READ_TOOLS.has(cand.replace(/\.exe$/, ''))) return false;
  }
  return sawExec;
}

function classify(output, command, signal) {
  if (output.includes(SENTINEL)) {
    if (output.trim().length <= SENTINEL_FRAME_MAX) {
      // The harness lost the result frame; the subprocess itself usually
      // completed. Recorded as integration -- the defect is in the
      // transport between harness and tool, not in either one alone.
      return { category: 'integration', snippet: SENTINEL };
    }
    return null;
  }
  // An explicit success is decisive: whatever the text says, nothing here
  // failed. Only a measured 'no' suppresses; 'unknown' never does.
  const succeeded = signal === 'no';
  const quoting = succeeded || isReadCommand(command);
  const cmd = String(command || '');
  for (const s of SIGNATURES) {
    const m = output.match(s.rx);
    if (!m) continue;
    // The command asked for this text (`grep "Error:"`, `echo FAILED`), so
    // finding it is the tool succeeding, not failing.
    if (cmd && cmd.includes(m[0])) continue;
    // Source-code-shaped signatures printed by a command that only prints
    // are quotation. Genuine tool-level failures (`env`) still record.
    if (quoting && s.quotable) continue;
    return { category: s.category, snippet: m[0].slice(0, 160) };
  }
  return null;
}

/** Append-only fire counter. capture_liveness.py compares this against
 *  events.jsonl; a producer that fires without recording is the failure
 *  mode that hid for 80 days, and only a durable count exposes it. */
function recordFire(toolName, category, signal) {
  try {
    fs.mkdirSync(path.dirname(FIRES_PATH), { recursive: true });
    fs.appendFileSync(FIRES_PATH, JSON.stringify({
      ts: new Date().toISOString(),
      producer: 'bug-hunter-ceps-bridge',
      tool: toolName,
      category,
      // Which arm of failureSignal() this fire took. Turns "does the
      // harness expose a failure signal?" into a countable fact.
      signal: signal || 'unknown',
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

function main() {
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

  const command = String(
    (payload.tool_input && payload.tool_input.command) || '');

  // Classified against the command that produced it AND whatever failure
  // signal the harness exposes, so text the caller asked for is not
  // mistaken for a failure the caller suffered.
  const signal = failureSignal(payload.tool_response);
  const hit = classify(output, command, signal);
  if (!hit) emitPass();
  const subsystem = isSentinel && !isCommandTool
    ? `harness:${toolName.toLowerCase()}`
    : subsystemOf(toolName, command);

  recordFire(toolName, hit.category, signal);

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
}

// The classifier shipped untested because requiring this file ran it: the
// IIFE read stdin and exited before a test could reach a single function.
// An unreachable pure function is an unasserted one, and all three defects
// repaired here lived in these two functions.
module.exports = {
  classify, subsystemOf, failureSignal, isReadCommand,
  SENTINEL, SENTINEL_FRAME_MAX, NAV_PREFIXES, READ_TOOLS,
};

if (require.main === module) main();
