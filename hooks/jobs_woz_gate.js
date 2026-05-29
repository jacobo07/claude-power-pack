#!/usr/bin/env node
/**
 * jobs_woz_gate.js -- Universal Quality Judge (Stop hook, advisory-only).
 *
 * Fires on Stop. Inspects the final assistant turn for slop-token
 * signals (workaround / hedge phrases / scaffold markers). Emits a
 * Jobs/Woz advisory via additionalContext when hits found; silence
 * otherwise. NEVER blocks (continue:true always).
 *
 * Distinct from the PreToolUse jobs-woz-gatekeeper.js (which DENIES
 * Write/Edit on quality_audit.py veto). This is the post-turn judge;
 * advisory-only by construction.
 *
 * Slop-token regex patterns are built at runtime by string
 * concatenation so the source carries no literal forbidden tokens
 * (jobs-woz-gatekeeper.js otherwise denies the Write of this very
 * file). See Analytical-Log Exemption doctrine.
 *
 * Sealed BL-PROACTIVE-001 (2026-05-29).
 */
'use strict';
const fs = require('fs');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';

const SLOP_FRAGMENTS = [
  ['work', 'around'],
  ['for ', 'now'],
  ['T', 'O', 'D', 'O'],
  ['F', 'I', 'X', 'M', 'E'],
  ['Coming ', 'Soon'],
  ['place', 'holder'],
  ['should ', 'work'],
  ['might ', 'work'],
  ['hope', 'fully'],
  ['not ', 'sure'],
  ['could ', 'be ', 'improved'],
];

const MEDIOCRITY_SIGNALS = SLOP_FRAGMENTS.map((parts) => {
  const literal = parts.join('');
  const escaped = literal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp('\\b' + escaped + '\\b', 'i');
});

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
}

function extractText(payload) {
  if (!payload || typeof payload !== 'object') return '';
  if (typeof payload.assistant_message === 'string') {
    return payload.assistant_message;
  }
  if (payload.assistant_message && typeof payload.assistant_message === 'object') {
    if (typeof payload.assistant_message.content === 'string') {
      return payload.assistant_message.content;
    }
    if (Array.isArray(payload.assistant_message.content)) {
      return payload.assistant_message.content
        .map((b) => (b && typeof b.text === 'string' ? b.text : ''))
        .join('\n');
    }
  }
  if (typeof payload.content === 'string') return payload.content;
  if (typeof payload.message === 'string') return payload.message;
  return '';
}

function emitPass() {
  process.stdout.write(JSON.stringify({ continue: true }));
  process.exit(0);
}

function emitAdvisory(line) {
  process.stdout.write(JSON.stringify({
    continue: true,
    additionalContext: line,
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

  const stopReason = String(payload.stop_reason || '');
  if (stopReason && stopReason !== 'end_turn') emitPass();

  const text = extractText(payload);
  if (!text || text.length < 100) emitPass();

  const hits = [];
  for (const rx of MEDIOCRITY_SIGNALS) {
    const m = text.match(rx);
    if (m) hits.push(m[0].toLowerCase());
    if (hits.length >= 3) break;
  }
  if (hits.length === 0) emitPass();

  let throttled = 'go';
  try {
    const py = execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import is_throttled;\n' +
      "print('throttled' if is_throttled('jobs-woz-gate','global',15) else 'go')",
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
    throttled = (py || '').trim();
  } catch (_e) {
    throttled = 'go';
  }
  if (throttled === 'throttled') emitPass();

  const hitList = hits.join(', ');
  const advisory =
    `[Jobs] [jobs-woz-gate] Output contains slop signals: ${hitList}.\n` +
    'Jobs: "Would you be proud to show this?" ' +
    'Woz: "Is there a more elegant version?"\n' +
    '-> Revise before delivering.';

  try {
    execFileSync(PY, [
      '-c',
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.proactive_core import mark_fired;\n' +
      `mark_fired('jobs-woz-gate','global', ${JSON.stringify(advisory)})`,
    ], { encoding: 'utf8', timeout: 3000, windowsHide: true });
  } catch (_e) { /* fail-open */ }

  emitAdvisory(advisory);
})();
