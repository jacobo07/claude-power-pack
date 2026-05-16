#!/usr/bin/env node
/**
 * zero-fiction-gate.js — PreToolUse hook (BL-0038 / MC-SYS-74).
 *
 * Scans Edit / Write / MultiEdit tool_input BEFORE the write lands. Catches
 * placeholder/fictional strings that violate the Zero-Fiction Standard
 * (vault/zero-fiction-standard.md, BL-0035 Eight Marks #1).
 *
 * Two severity levels:
 *   - HARD-FAIL: returns permissionDecision="ask" so the user must confirm.
 *     Only literal "Coming Soon" UI copy, NotImplementedError raises, and
 *     empty-catch-with-comment fall here. Patterns are tight to avoid
 *     false-positives on legit code.
 *   - SOFT-FAIL: returns advisory via additionalContext so the model sees
 *     the warning but the write proceeds. TODO/FIXME/HACK/XXX comments are
 *     soft.
 *
 * Output schema (PreToolUse):
 *   {} — clean
 *   {"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"..."}} — soft
 *   {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"..."}} — hard
 *
 * Disable via env: ZERO_FICTION_GATE=off
 *
 * Hook contract (PreToolUse):
 *   stdin JSON: {"tool_name":"Edit"|"Write"|"MultiEdit","tool_input":{...},...}
 *   stdout: {} or hookSpecificOutput per above
 */
'use strict';

if (process.env.ZERO_FICTION_GATE === 'off') {
  process.stdout.write('{}');
  process.exit(0);
}

const TARGETS = new Set(['Edit', 'Write', 'MultiEdit']);

// HARD-FAIL: tight patterns. Only literal user-visible placeholders + clearly stub-only code.
const HARD_PATTERNS = [
  { re: /\bComing\s+Soon\b/i,                  why: 'literal "Coming Soon" UI copy' },
  { re: /\braise\s+NotImplementedError\b/,     why: 'raise NotImplementedError stub' },
  { re: /pass\s*#\s*TODO\b/,                   why: 'pass # TODO stub body' },
  { re: /\bLorem\s+ipsum/i,                    why: 'Lorem ipsum placeholder' },
  { re: /\bPLACEHOLDER\b/,                     why: 'literal PLACEHOLDER token' },
  { re: /throw\s+new\s+Error\(['"]not\s+implemented/i, why: 'throw "not implemented" stub' },
];

// SOFT-FAIL: word-boundary only on COMMENT lines to avoid catching "TODO_LIST" identifiers etc.
// Match comment markers followed by TODO/FIXME/HACK/XXX.
const SOFT_PATTERNS = [
  { re: /(^|\n)\s*(\/\/|#|\/\*|\*)\s*(TODO|FIXME|HACK|XXX)\b/, why: 'TODO/FIXME/HACK/XXX comment' },
];

function extractWriteText(toolName, toolInput) {
  if (!toolInput || typeof toolInput !== 'object') return '';
  if (toolName === 'Write')  return String(toolInput.content || '');
  if (toolName === 'Edit')   return String(toolInput.new_string || '');
  if (toolName === 'MultiEdit') {
    const edits = Array.isArray(toolInput.edits) ? toolInput.edits : [];
    return edits.map(e => String(e && e.new_string || '')).join('\n');
  }
  return '';
}

function readStdin() {
  return new Promise(resolve => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => resolve(buf));
    setTimeout(() => resolve(buf), 4500);
  });
}

(async function main() {
  let event = {};
  try {
    const raw = await readStdin();
    if (raw.trim()) event = JSON.parse(raw);
  } catch (_) {}

  const toolName = event && event.tool_name;
  if (!TARGETS.has(toolName)) {
    process.stdout.write('{}');
    return;
  }

  const text = extractWriteText(toolName, event.tool_input);
  if (!text) {
    process.stdout.write('{}');
    return;
  }

  const hardHits = HARD_PATTERNS.filter(p => p.re.test(text)).map(p => p.why);
  const softHits = SOFT_PATTERNS.filter(p => p.re.test(text)).map(p => p.why);

  if (hardHits.length > 0) {
    const reason =
      `Zero-Fiction gate (BL-0035 Eight Marks #1): write blocked pending user confirm. ` +
      `Detected: ${hardHits.join('; ')}. ` +
      `Either replace with real implementation or override (set env ZERO_FICTION_GATE=off in this session).`;
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'ask',
        permissionDecisionReason: reason,
      },
    }));
    return;
  }

  if (softHits.length > 0) {
    const msg =
      `Zero-Fiction advisory (BL-0035 Eight Marks #1): about to write content with ` +
      `${softHits.join('; ')}. The write is proceeding, but consider whether the placeholder ` +
      `is intentional. If shipping production, replace before merge.`;
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: msg,
      },
    }));
    return;
  }

  process.stdout.write('{}');
})();
