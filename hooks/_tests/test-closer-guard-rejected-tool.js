#!/usr/bin/env node
/**
 * Two-way self-test for D5: A REJECTED TOOL CALL IS NOT WORK.
 *
 * MEASURED 2026-09-14 (Jacobo, claude-power-pack). The Owner rejected an Edit on
 * USEA_TRAPS.md. The turn then ended on the single sentence "No response
 * requested." and the screen died; the Owner had to interrupt and report the
 * hang by hand. That closer is NULL_ACK — a class this file added on 2026-09-02
 * for precisely that sentence — and it was never even tested, because the turn
 * carried a `tool_use` block and every class but PASSIVE_WAIT is exempt on a
 * tool turn. Measured against the live transcript:
 *     classify("No response requested.")                  -> NULL_ACK
 *     classify("No response requested.", {toolTurn:true}) -> null
 *
 * WHY EIGHT PREVIOUS PASSES OVER THIS FILE DID NOT FIND IT: every transcript
 * fixture in this suite is built from `user` + `assistant` records only. Not one
 * of them writes a `tool_result`, so `is_error` did not exist anywhere in the
 * corpus and A REFUSED CALL WAS UNREPRESENTABLE IN THE FIXTURES. The patterns
 * were exercised hard; the input shape that mattered could not be expressed.
 * This file exists to make that shape expressible.
 *
 * THE FALSE-POSITIVE HALF IS THE HALF THAT MATTERS. The repair must narrow the
 * exemption by exactly one predicate — did a call SUCCEED, not was a call
 * ISSUED — and nothing else. Cases 4-8 below fail if it widens: an ordinary
 * successful tool turn, a turn where only ONE of two calls was refused, and an
 * error belonging to somebody else's tool_use_id must all stay exempt. A guard
 * that fires on ordinary agentic work gets switched off, and an off guard is
 * the dead screen this file exists to prevent.
 *
 * Run: node ~/.claude/hooks/tests/test-closer-guard-rejected-tool.js
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const { run, lastAssistantTurn } =
  require(path.join(os.homedir(), '.claude', 'hooks', 'closer-guard.js'));

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'closer-guard-rej-'));

const text = (s) => ({ type: 'text', text: s });
const call = (id, name) => ({ type: 'tool_use', id, name: name || 'Edit', input: {} });

/** A harness tool_result record. `err` true reproduces a refusal or a tool error. */
function result(id, err, body) {
  return {
    type: 'user',
    message: {
      role: 'user',
      content: [{
        type: 'tool_result',
        tool_use_id: id,
        content: body || (err ? '[Request interrupted by user for tool use]' : 'ok'),
        ...(err ? { is_error: true } : {}),
      }],
    },
  };
}

const assistant = (content) => ({ type: 'assistant', message: { role: 'assistant', content } });

/** Write a transcript from an ordered record list, after an opening human message. */
function transcript(records, tag) {
  const p = path.join(TMP, `t-${tag}.jsonl`);
  const lines = [JSON.stringify({ type: 'user', message: { role: 'user', content: 'go' } })]
    .concat(records.map((r) => JSON.stringify(r)));
  fs.writeFileSync(p, lines.join('\n') + '\n', 'utf8');
  return p;
}

const DEAD = 'No response requested.';

// [label, ordered records after the human message, expected class or null]
const CASES = [
  // --- MUST fire: no call succeeded, so the turn owes the Owner a sentence ---

  // THE MEASURED CASE. Verbatim shape of the 2026-09-14 dead screen.
  ['rejected Edit then null-ack',
   [assistant([call('tu_1')]), result('tu_1', true), assistant([text(DEAD)])],
   'NULL_ACK'],

  // Refused call and not one word afterwards: the screen simply stops.
  ['rejected Edit, no text at all',
   [assistant([call('tu_1')]), result('tu_1', true)],
   'EMPTY'],

  // The announced repair that never happened, because the call was refused.
  ['rejected Edit then intent narration',
   [assistant([call('tu_1')]), result('tu_1', true), assistant([text('Voy a corregirlo.')])],
   'INTENT_NARRATION'],

  // A tool ERROR (not a refusal) is the same evidence: nothing was accomplished.
  ['errored tool then null-ack',
   [assistant([call('tu_1', 'Grep')]),
    result('tu_1', true, 'Ripgrep search timed out after 20 seconds.'),
    assistant([text(DEAD)])],
   'NULL_ACK'],

  // --- MUST NOT fire: the exemption is narrowed by one predicate, not removed -

  // Shipped behaviour, deliberately preserved. A turn that DID work is not a
  // null acknowledgement; widening this is a separate decision with its own
  // false-positive budget, and it is not what the 2026-09-14 hang was about.
  ['successful Edit then null-ack',
   [assistant([call('tu_1')]), result('tu_1', false), assistant([text(DEAD)])],
   null],

  ['successful Edit then ordinary report',
   [assistant([call('tu_1')]), result('tu_1', false), assistant([text('17/17 verdes, sigo.')])],
   null],

  // Partial failure is not failure. One refused call among several does not
  // make the turn idle, and treating it that way would fire on ordinary work.
  ['one rejected, one successful, then null-ack',
   [assistant([call('tu_1'), call('tu_2', 'Read')]),
    result('tu_1', true), result('tu_2', false),
    assistant([text(DEAD)])],
   null],

  // The control that proves the fix matches on IDENTITY rather than on "an
  // error appeared somewhere". Without it, a fix that disabled the exemption
  // whenever any error was present would pass every case above.
  ['error belonging to a different tool_use_id',
   [assistant([call('tu_1')]), result('tu_9', true), result('tu_1', false),
    assistant([text(DEAD)])],
   null],

  // --- MUST fire regardless: no regression in the one class already live here -
  ['rejected Edit then passive wait',
   [assistant([call('tu_1')]), result('tu_1', true),
    assistant([text('Quedo a la espera de tu confirmacion.')])],
   'PASSIVE_WAIT'],

  ['successful Edit then passive wait',
   [assistant([call('tu_1')]), result('tu_1', false),
    assistant([text('Standing by for the notification.')])],
   'PASSIVE_WAIT'],
];

let pass = 0;
let fail = 0;

for (const [label, records, expected] of CASES) {
  const tag = label.replace(/[^a-z0-9]+/gi, '-');
  const out = run({
    transcript_path: transcript(records, tag),
    // Fresh session id per case: the anti-loop lets a REPEATED identical closer
    // through, so a shared id would silently mask a real block.
    session_id: `test-rej-${tag}-${Date.now()}`,
  });

  const blocked = out && out.decision === 'block';
  const cls = blocked
    ? String(out.reason).split('\n')[0].replace(/^CLOSER GUARD — /, '').replace(/\.$/, '')
    : null;

  if (cls === expected) {
    pass += 1;
  } else {
    fail += 1;
    console.log(`  FAIL  ${label}: expected=${expected}  got=${cls}`);
  }
}

// --- Positive control on the READ itself -----------------------------------
// If lastAssistantTurn stopped reporting the new field, every case above would
// still pass through the `!== false` compatibility clause and this file would
// report a clean green while the guard was back to its old aperture. Assert the
// field exists AND that it discriminates.
{
  const rejected = lastAssistantTurn(
    transcript([assistant([call('tu_1')]), result('tu_1', true)], 'ctl-rej'));
  const worked = lastAssistantTurn(
    transcript([assistant([call('tu_1')]), result('tu_1', false)], 'ctl-ok'));

  for (const [label, cond] of [
    ['read reports productiveTool', typeof rejected.productiveTool === 'boolean'],
    ['rejected call is not productive', rejected.productiveTool === false],
    ['successful call is productive', worked.productiveTool === true],
    ['both still report usedTool', rejected.usedTool === true && worked.usedTool === true],
  ]) {
    if (cond) { pass += 1; } else { fail += 1; console.log(`  FAIL  ${label}`); }
  }
}

// Fail-open is a contract: a guard that throws must never wedge a turn.
for (const [label, input] of [
  ['missing transcript path', {}],
  ['nonexistent transcript', { transcript_path: path.join(TMP, 'nope.jsonl') }],
  ['garbage input', null],
]) {
  const out = run(input);
  if (out && out.continue === true) {
    pass += 1;
  } else {
    fail += 1;
    console.log(`  FAIL  ${label}: expected fail-open continue, got ${JSON.stringify(out)}`);
  }
}

try { fs.rmSync(TMP, { recursive: true, force: true }); } catch (_) { /* best effort */ }

console.log(
  `CLOSER_GUARD_REJECTED_TOOL=${pass}/${pass + fail}  ` +
  `(fires: 6, must-not-fire: 4, read-controls: 4, fail-open: 3)`
);
process.exit(fail === 0 ? 0 : 1);
