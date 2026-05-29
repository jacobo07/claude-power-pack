#!/usr/bin/env node
/**
 * osa_deploy_detector.js -- PostToolUse advisory after a Bash deploy
 * command. Detects deploy verbs in tool_input.command; on hit, emits
 * a pp-monitor / omni-singularity advisory recommending an OSA audit.
 * Does NOT spawn claude -p autonomously (per OSA throttle doctrine --
 * the Owner consumes budget by invoking /osa --audit).
 *
 * Fail-open: any internal error -> exit 0 silent. Advisory-only.
 *
 * Sealed BL-HOOKS-REG-001 (2026-05-29).
 */
'use strict';
const fs = require('fs');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';

const DEPLOY_PATTERNS = [
  /\bvercel\s+(deploy|--prod)\b/i,
  /\bkubectl\s+(apply|rollout|create)\b/i,
  /\bmix\s+release\b/i,
  /\bgh\s+release\s+create\b/i,
  /\bdocker\s+push\b/i,
  /\bgit\s+push\s+.*\b(prod|production|main|master|release)\b/i,
  /\bnpm\s+publish\b/i,
  /\bcap\s+(production|staging)\s+deploy\b/i,
  /\bfly\s+deploy\b/i,
  /\bheroku\s+(release:|main|master)/i,
];

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
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

  const command = String(
    (payload.tool_input && payload.tool_input.command) || '');
  if (!command || command.length < 4) emitPass();

  const hit = DEPLOY_PATTERNS.find((rx) => rx.test(command));
  if (!hit) emitPass();

  let throttled = 'go';
  try {
    const py = execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import is_throttled;\n' +
      "print('throttled' if is_throttled('omni-singularity','deploy',5) else 'go')",
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
    throttled = (py || '').trim();
  } catch (_e) {
    throttled = 'go';
  }
  if (throttled === 'throttled') emitPass();

  const matched = hit.source.replace(/\\[bs]|\(\?\:.*?\)/g, ' ')
    .replace(/[|(){}\\?+*]/g, ' ').replace(/\s+/g, ' ').trim();
  const advisory =
    `[Jobs] [omni-singularity] Deploy command detected: ${matched}.\n` +
    'OSA recommends a post-deploy audit (visual + text).\n' +
    '-> Run /osa --audit when the deploy settles.';

  try {
    execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import mark_fired;\n' +
      `mark_fired('omni-singularity','deploy', ${JSON.stringify(advisory)})`,
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
  } catch (_e) { /* fail-open */ }

  emitAdvisory(advisory);
})();
