#!/usr/bin/env node
/**
 * bug-hunter-ceps-bridge.js -- PostToolUse Bash advisory + CEPS
 * capture. When the Bash output contains an error / failure / traceback
 * pattern, calls modules.ceps.record_error() to capture and emits a
 * pp-ceps-analyst advisory in additionalContext.
 *
 * Categories use the CEPS taxonomy ({regression, security, drift,
 * scaffold, incomplete-shell, integration, spec-violation, tooling,
 * env}). Default classification is 'tooling' when ambiguous.
 *
 * Fail-open: CEPS capture failure -> still emit silence rather than
 * crash. Hooks must never disrupt the user path.
 *
 * Sealed BL-HOOKS-REG-001 (2026-05-29).
 */
'use strict';
const fs = require('fs');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';

const ERROR_PATTERNS = [
  /\bTraceback\s+\(most recent call last\)/,
  /\bError\b.*:.*\w/,
  /\bFAILED\b/,
  /\bException\b.*:.*\w/,
  /\bSegmentation fault\b/,
  /\bfatal:\s+\S+/i,
  /^\s*\w+Error:\s+\S+/m,
  /\bCommand\s+failed\b/i,
  /\b(?:permission|access)\s+denied\b/i,
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
  if (typeof r.output === 'string') parts.push(r.output);
  if (typeof r.stdout === 'string') parts.push(r.stdout);
  if (typeof r.stderr === 'string') parts.push(r.stderr);
  return parts.join('\n');
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
  if (String(payload.tool_name || '') !== 'Bash') emitPass();

  const output = extractOutput(payload);
  if (!output || output.length < 12) emitPass();

  let hit = null;
  let snippet = '';
  for (const rx of ERROR_PATTERNS) {
    const m = output.match(rx);
    if (m) {
      hit = rx;
      snippet = m[0].slice(0, 160);
      break;
    }
  }
  if (!hit) emitPass();

  let throttled = 'go';
  try {
    const py = execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import is_throttled;\n' +
      "print('throttled' if is_throttled('pp-ceps-analyst','bash-error',10) else 'go')",
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
    throttled = (py || '').trim();
  } catch (_e) {
    throttled = 'go';
  }
  if (throttled === 'throttled') emitPass();

  const command = String(
    (payload.tool_input && payload.tool_input.command) || '');

  try {
    execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from tools.ceps import record_error;\n' +
      'record_error(\n' +
      "  category='tooling',\n" +
      `  subsystem='bash:' + ${JSON.stringify(command.slice(0, 40))},\n` +
      `  root_cause=${JSON.stringify(snippet)},\n` +
      "  confidence='low',\n" +
      "  scope='session'\n" +
      ')',
    ], { encoding: 'utf8', timeout: 5000, windowsHide: true });
  } catch (_e) { /* fail-open */ }

  const advisory =
    `[Woz] [pp-ceps-analyst] Bash error captured to CEPS.\n` +
    `Snippet: ${snippet.slice(0, 80)}\n` +
    '-> Run /ceps query to inspect recurrence.';

  try {
    execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import mark_fired;\n' +
      `mark_fired('pp-ceps-analyst','bash-error', ${JSON.stringify(advisory)})`,
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
  } catch (_e) { /* fail-open */ }

  emitAdvisory(advisory);
})();
