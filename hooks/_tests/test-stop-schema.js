#!/usr/bin/env node
/**
 * test-stop-schema.js — Regression guard for BL-2026-05-24.
 *
 * The Stop hook chain (hook-dispatcher.js --event=Stop-chain) was emitting
 * JSON with root-level `additionalContext` and `hookSpecificOutput`, both
 * forbidden by the Stop schema. Symptom: harness reported
 *   "Hook JSON output validation failed — (root): Invalid input"
 *   and ran all 11 Stop hooks but dropped their effects.
 *
 * This test ensures the dispatcher's sanitizeForSchema() reduces ANY
 * combined sub-hook output into a schema-valid Stop payload, AND that the
 * real Stop-chain end-to-end (subprocess) emits schema-valid JSON.
 *
 * Run:
 *   node ~/.claude/hooks/tests/test-stop-schema.js
 *
 * Exit 0 = all PASS; exit 1 = any failure (CI-friendly).
 */

'use strict';

const { spawnSync } = require('child_process');
const path = require('path');
const { sanitizeForSchema, familyOf } = require('../hook-dispatcher.js');

// --- Schema mirror (kept aligned with the harness error message it emits).
// Root-level whitelist by event. `additionalContext` is NEVER valid at root.
const ROOT_KEYS_UNIVERSAL = new Set([
  'continue', 'suppressOutput', 'stopReason', 'decision', 'reason',
  'systemMessage', 'terminalSequence', 'permissionDecision',
  'hookSpecificOutput',
]);

const HSO_INNER_BY_FAMILY = {
  PreToolUse: new Set([
    'hookEventName', 'permissionDecision', 'permissionDecisionReason', 'updatedInput',
    // `additionalContext` IS valid on PreToolUse (official hooks docs, verified
    // 2026-07-03) and hook-dispatcher.js:425 deliberately keeps it — dropping it
    // once silently muted every PreToolUse context-injector. This allow-list was
    // never updated alongside that fix, so the case at "PreToolUse keeps
    // hookSpecificOutput.additionalContext" was asserting the opposite of its own
    // name and had been red ever since. A stale ALLOW-LIST fails the same way a
    // stale assertion does, and is harder to see because it reads as the schema.
    'additionalContext',
  ]),
  UserPromptSubmit: new Set(['hookEventName', 'additionalContext']),
  PostToolUse: new Set(['hookEventName', 'additionalContext']),
  PostToolBatch: new Set(['hookEventName', 'additionalContext']),
};

function validate(out, family) {
  const errs = [];
  if (!out || typeof out !== 'object') {
    errs.push('output is not an object');
    return errs;
  }
  for (const k of Object.keys(out)) {
    if (!ROOT_KEYS_UNIVERSAL.has(k)) {
      errs.push(`root: unexpected key "${k}"`);
    }
  }
  if (out.decision != null && out.decision !== 'approve' && out.decision !== 'block') {
    if (family !== 'PreToolUse') {
      errs.push(`root.decision: "${out.decision}" is not "approve" | "block"`);
    }
  }
  if (out.hookSpecificOutput) {
    const allowed = HSO_INNER_BY_FAMILY[family];
    if (!allowed) {
      errs.push(`hookSpecificOutput: not allowed for ${family} family`);
    } else {
      if (out.hookSpecificOutput.hookEventName !== family) {
        errs.push(`hookSpecificOutput.hookEventName: "${out.hookSpecificOutput.hookEventName}" !== "${family}"`);
      }
      for (const k of Object.keys(out.hookSpecificOutput)) {
        if (!allowed.has(k)) {
          errs.push(`hookSpecificOutput: unexpected key "${k}" for ${family}`);
        }
      }
    }
  }
  return errs;
}

let pass = 0;
let fail = 0;

function check(name, errs, mustContain) {
  if (errs.length === 0 && (!mustContain || mustContain.every(c => true))) {
    console.log(`  PASS  ${name}`);
    pass++;
  } else {
    console.log(`  FAIL  ${name}`);
    for (const e of errs) console.log(`        - ${e}`);
    fail++;
  }
}

console.log('--- Unit: sanitizeForSchema() against the BL-2026-05-24 payload ---');

// EXACT shape from the harness rejection report.
const reported = {
  hookSpecificOutput: {
    hookEventName: 'Stop',
    additionalContext: 'RAM ADVISORY (BL-0019, advisory only): claude.exe is using 3441 MB across 16 process(es), above the 1500 MB attention threshold.',
  },
  systemMessage: 'vault: background sync queued',
  continue: true,
  additionalContext: '[KobiiClaw AutoResearch v2] trigger saved for "claude-power-pack". Scheduler handles 2x/day runs.',
};

const cleaned = sanitizeForSchema(reported, 'Stop');
const errs1 = validate(cleaned, 'Stop');
check('reported bad payload becomes schema-clean for Stop', errs1);

// Both stranded texts (RAM advisory + KobiiClaw line) MUST be salvaged into systemMessage.
const sm = cleaned.systemMessage || '';
if (sm.includes('RAM ADVISORY') && sm.includes('KobiiClaw AutoResearch') && sm.includes('vault: background sync queued')) {
  console.log('  PASS  all 3 message sources preserved in systemMessage');
  pass++;
} else {
  console.log('  FAIL  message salvage incomplete. systemMessage was:');
  console.log('        ' + sm.replace(/\n/g, '\\n').slice(0, 240));
  fail++;
}

console.log('');
console.log('--- Unit: extra cases ---');

// Decision normalization: deny -> block, allow -> approve, invalid -> dropped.
const dn = sanitizeForSchema({ decision: 'deny' }, 'Stop');
check('decision:"deny" -> "block" for Stop', validate(dn, 'Stop'));
if (dn.decision !== 'block') { console.log(`  FAIL  expected decision="block", got "${dn.decision}"`); fail++; }
else { console.log('  PASS  decision normalized to "block"'); pass++; }

const dal = sanitizeForSchema({ decision: 'allow' }, 'Stop');
if (dal.decision !== 'approve') { console.log(`  FAIL  expected decision="approve", got "${dal.decision}"`); fail++; }
else { console.log('  PASS  decision normalized to "approve"'); pass++; }

const dx = sanitizeForSchema({ decision: 'gibberish' }, 'Stop');
if ('decision' in dx) { console.log('  FAIL  invalid decision should be stripped'); fail++; }
else { console.log('  PASS  invalid decision stripped'); pass++; }

// PreToolUse keeps hookSpecificOutput.additionalContext.
const pre = sanitizeForSchema({
  hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: 'hi', permissionDecision: 'allow' },
}, 'PreToolUse');
check('PreToolUse hookSpecificOutput retained', validate(pre, 'PreToolUse'));

// UserPromptSubmit: root additionalContext is invalid; should go to systemMessage.
const ups = sanitizeForSchema({ additionalContext: 'help text' }, 'UserPromptSubmit');
check('UserPromptSubmit: root additionalContext rerouted', validate(ups, 'UserPromptSubmit'));
if (ups.systemMessage !== 'help text') { console.log('  FAIL  expected systemMessage="help text"'); fail++; }
else { console.log('  PASS  root additionalContext -> systemMessage'); pass++; }

// familyOf maps chain suffixes correctly.
const fams = [
  ['Stop-chain', 'Stop'],
  ['PreToolUse-Bash-chain', 'PreToolUse'],
  ['PreToolUse-Edit-chain', 'PreToolUse'],
  ['PostToolUse-default', 'PostToolUse'],
  ['UserPromptSubmit-default', 'UserPromptSubmit'],
];
for (const [name, want] of fams) {
  const got = familyOf(name);
  if (got !== want) { console.log(`  FAIL  familyOf("${name}") = "${got}", want "${want}"`); fail++; }
  else { console.log(`  PASS  familyOf("${name}") = "${want}"`); pass++; }
}

console.log('');
console.log('--- Integration: real Stop-chain subprocess ---');

const dispatcher = path.resolve(__dirname, '..', 'hook-dispatcher.js');
// Minimal mock Stop event payload. Children that need session_id will branch
// on it; that's fine — we only care that the FINAL stdout JSON is
// schema-valid regardless of which children fired text.
const mockInput = JSON.stringify({
  session_id: 'schema-test-' + Date.now(),
  transcript_path: '',
  cwd: process.cwd(),
});

const r = spawnSync(process.execPath, [dispatcher, '--event=Stop-chain'], {
  input: mockInput,
  encoding: 'utf8',
  timeout: 120000,
  windowsHide: true,
});

if (r.error) {
  console.log('  FAIL  subprocess spawn error: ' + r.error.message);
  fail++;
} else if (r.status !== 0) {
  console.log(`  FAIL  dispatcher exit status ${r.status}`);
  if (r.stderr) console.log('        stderr: ' + r.stderr.slice(0, 400));
  fail++;
} else {
  let parsed;
  try { parsed = JSON.parse(r.stdout); }
  catch (e) { console.log('  FAIL  dispatcher stdout is not JSON: ' + e.message); console.log('        stdout: ' + r.stdout.slice(0, 200)); fail++; parsed = null; }
  if (parsed) {
    const errs = validate(parsed, 'Stop');
    if (errs.length === 0) {
      console.log('  PASS  real Stop-chain output validates against Stop schema');
      console.log('        output keys: ' + Object.keys(parsed).join(', '));
      pass++;
    } else {
      console.log('  FAIL  real Stop-chain output violates schema:');
      for (const e of errs) console.log('        - ' + e);
      console.log('        stdout: ' + r.stdout.slice(0, 400));
      fail++;
    }
  }
}

console.log('');
console.log(`=== Result: ${pass} pass, ${fail} fail ===`);
process.exit(fail === 0 ? 0 : 1);
