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

const NIE_WHY = 'raise NotImplementedError stub';

// An abstract method is not a stub: a base class raises it so every subclass must override.
// Measured 2026-10-04 (GEX44, kme_pillars.py Observer.result). Exempt only when EVERY raise sits
// in a def that is decorated @abstractmethod, or whose name is defined again in the same text
// (base + override). An Edit carrying only the base method stays flagged -- conservative.
function allNotImplementedAreAbstract(text) {
  const lines = text.split(/\r?\n/);
  let found = 0;
  for (let i = 0; i < lines.length; i++) {
    if (!/\braise\s+NotImplementedError\b/.test(lines[i])) continue;
    found++;
    let j = i - 1;
    while (j >= 0 && !/^\s*(async\s+)?def\s+\w+\s*\(/.test(lines[j])) j--;
    if (j < 0) return false;
    const name = lines[j].match(/def\s+(\w+)/)[1];
    let k = j - 1;
    let abstract = false;
    while (k >= 0 && /^\s*@/.test(lines[k])) {
      if (/abstractmethod\b/.test(lines[k])) abstract = true;
      k--;
    }
    const defs = (text.match(new RegExp(`(^|\\n)\\s*(async\\s+)?def\\s+${name}\\s*\\(`, 'g')) || []).length;
    if (!abstract && defs < 2) return false;
  }
  return found > 0;
}

// HARD-FAIL: tight patterns. Only literal user-visible placeholders + clearly stub-only code.
const HARD_PATTERNS = [
  { re: /\bComing\s+Soon\b/i,                  why: 'literal "Coming Soon" UI copy' },
  { re: /\braise\s+NotImplementedError\b/,     why: NIE_WHY },
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

// --- JOBS-WOZ double-scoped cryptographic exemption (Owner Q2a/Q3a) ---
const _JW_EXEMPT_BASENAMES = new Set(['dataset_enricher.py', 'quality_audit.py']);
function _jwCanonHash(tokens) {
  const u = [...new Set(tokens.map(String))];
  u.sort((a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8')));
  return require('crypto').createHash('sha256').update(u.join(String.fromCharCode(10)), 'utf8').digest('hex');
}
function _jwParseLine(probe, marker) {
  const i = probe.indexOf(marker);
  if (i < 0) return null;
  let j = probe.indexOf(String.fromCharCode(10), i);
  if (j < 0) j = probe.length;
  return probe.slice(i + marker.length, j).trim();
}
function _jwExemptionGranted(realPath, toolName, contentText) {
  try {
    const norm = String(realPath).split(String.fromCharCode(92)).join('/');
    const base = norm.slice(norm.lastIndexOf('/') + 1);
    if (!_JW_EXEMPT_BASENAMES.has(base)) return false;
    let probe = contentText;
    if (toolName === 'Edit' || toolName === 'MultiEdit') {
      try { probe = require('fs').readFileSync(realPath, 'utf8'); } catch (_e) { probe = contentText; }
    }
    const sha = _jwParseLine(probe, 'JOBS-WOZ-EXEMPT sha256=');
    const toksRaw = _jwParseLine(probe, 'JOBS-WOZ-TOKENS:');
    if (!sha || !toksRaw) return false;
    const m = sha.match(/[0-9a-f]{64}/i);
    if (!m) return false;
    let toks;
    try { toks = JSON.parse(toksRaw); } catch (_e) { return false; }
    if (!Array.isArray(toks)) return false;
    return _jwCanonHash(toks) === m[0].toLowerCase();
  } catch (_e) { return false; }
}

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

  const _zfRealPath = (event.tool_input && event.tool_input.file_path) || '';
  if (_jwExemptionGranted(_zfRealPath, toolName, text)) {
    process.stdout.write('{}');
    return;
  }

  const hardHits = HARD_PATTERNS
    .filter(p => p.re.test(text))
    .filter(p => !(p.why === NIE_WHY && allNotImplementedAreAbstract(text)))
    .map(p => p.why);
  const softHits = SOFT_PATTERNS.filter(p => p.re.test(text)).map(p => p.why);

  if (hardHits.length > 0) {
    // A background session has nobody to answer "ask": it waits forever (measured 2026-10-04,
    // GEX44 m-d2bdfa31de21, 39 min). There the verdict is deny, so the agent reads the reason
    // and rewrites. Interactive sessions keep the confirm.
    const unattended = process.env.CLAUDE_CODE_SESSION_KIND === 'bg';
    const reason =
      `Zero-Fiction gate (BL-0035 Eight Marks #1): write ` +
      (unattended ? 'refused (background session: nobody can confirm). '
                  : 'blocked pending user confirm. ') +
      `Detected: ${hardHits.join('; ')}. ` +
      (unattended
        ? 'Replace it with a real implementation; for an abstract method use abc.abstractmethod with an ellipsis body.'
        : 'Either replace with real implementation or override (set env ZERO_FICTION_GATE=off in this session).');
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: unattended ? 'deny' : 'ask',
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
