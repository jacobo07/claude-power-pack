#!/usr/bin/env node
/**
 * Two-way self-test for the closer-guard SILENT_TOOL_STOP class.
 *
 * This class exists because the tool-call exemption was BLANKET until 2026-09-02:
 * `if (turn.usedTool) return { continue: true }`. A turn whose final message was an
 * Edit and nothing else sailed straight through and produced the dead screen the hook
 * exists to kill. NULL_ACK caught only the SECOND screen (the "No response requested."
 * reply to the Owner's nudge); the first was invisible by construction.
 *
 * The narrowing is one word wide — a tool-call turn is exempt only if it ALSO carries
 * text — so the false-positive half of this file is the half that matters. If this
 * class ever widens to "any tool-call turn", it fires on every ordinary agentic step
 * and the guard gets switched off, which is how a noisy gate dies.
 *
 * Unlike the NULL_ACK self-test, this one drives run() against real transcript files:
 * the defect lives in the transcript-shape branch, not in classify(), so a
 * classify()-only test could not have caught it. That is the point.
 *
 * Run: node ~/.claude/hooks/tests/test-closer-guard-silent-tool-stop.js
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const { run } = require(path.join(os.homedir(), '.claude', 'hooks', 'closer-guard.js'));

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'closer-guard-sts-'));

/** Write a one-line transcript whose last assistant message has the given content blocks. */
function transcriptWith(content, tag) {
  const p = path.join(TMP, `t-${tag}.jsonl`);
  const lines = [
    JSON.stringify({ type: 'user', message: { role: 'user', content: 'go' } }),
    JSON.stringify({ type: 'assistant', message: { role: 'assistant', content } }),
  ];
  fs.writeFileSync(p, lines.join('\n') + '\n', 'utf8');
  return p;
}

const TOOL = { type: 'tool_use', id: 'tu_1', name: 'Edit', input: {} };
const text = (s) => ({ type: 'text', text: s });

// [label, content blocks, expected class or null-for-allowed]
const CASES = [
  // --- MUST fire -----------------------------------------------------------
  // The measured 2026-09-02 dead screen: an Edit landed, the turn ended, no text.
  ['tool call alone', [TOOL], 'SILENT_TOOL_STOP'],
  ['tool call + whitespace only', [TOOL, text('   \n  ')], 'SILENT_TOOL_STOP'],
  ['two tool calls, no text', [TOOL, TOOL], 'SILENT_TOOL_STOP'],

  // --- MUST NOT fire: ordinary agentic work --------------------------------
  // A narrated tool call is the NORMAL shape of every good turn. If these ever
  // block, the guard fires on every step of every task and gets disabled.
  ['narration then tool call', [text('Compilo el modulo y sigo.'), TOOL], null],
  ['tool call then narration', [TOOL, text('37/37 verdes, cierro.')], null],
  // CORRECTED 2026-09-04 (FIFA 11 Mod). This case asserted `null` and was
  // therefore a fixture defending the bug it should have caught: classify() was
  // never run on a tool-call turn, so PASSIVE_WAIT could not fire there, and
  // this expectation locked that in. "El build sigue en curso" = "the build is
  // still in progress" — at Stop the loop is ALREADY OVER, so that sentence is
  // the canonical rule-(H) dead screen (CLAUDE.md names "Commit + push in
  // progress" as the example). A tool call before it makes it look alive, which
  // is worse, not better.
  //
  // The neighbouring fear — "if these block, the guard fires on every step" —
  // is answered by the two cases above and the one below, which still pass:
  // ordinary narration is untouched. Only a literal statement of waiting fires.
  ['tool call + passive wait (ES)', [TOOL, text('El build sigue en curso.')], 'PASSIVE_WAIT'],
  ['tool call + narration that merely sounds passive',
   [text('Sigo con el siguiente modulo.'), TOOL], null],

  // The shape that hung the 2026-09-04 session: an Agent was dispatched and the
  // turn closed describing it as still running. INTENT_NARRATION stays exempt on
  // a tool turn (the announced action happened); PASSIVE_WAIT does not.
  ['tool call + agent-still-running closer',
   [TOOL, text('Dispatched the auditor; standing by for its report.')], 'PASSIVE_WAIT'],

  // --- MUST NOT fire: no regression in the text-only classes ---------------
  ['text-only substantive close', [text('Listo: 37/37 verdes, rama roja conducida.')], null],
  ['text-only empty', [text('')], 'EMPTY'],
  ['text-only null-ack', [text('No response requested.')], 'NULL_ACK'],
  ['text-only passive wait', [text('Awaiting the completion notification.')], 'PASSIVE_WAIT'],
];

let pass = 0;
let fail = 0;

for (const [label, content, expected] of CASES) {
  const tag = label.replace(/[^a-z0-9]+/gi, '-');
  const out = run({
    transcript_path: transcriptWith(content, tag),
    // A fresh session id per case: the anti-loop deliberately lets a REPEATED
    // identical closer through, so sharing an id would silently mask a real block.
    session_id: `test-sts-${tag}-${Date.now()}`,
  });

  const blocked = out && out.decision === 'block';
  const cls = blocked ? String(out.reason).split('\n')[0].replace(/^CLOSER GUARD — /, '').replace(/\.$/, '') : null;
  const ok = cls === expected;

  if (ok) {
    pass += 1;
  } else {
    fail += 1;
    console.log(`  FAIL  ${label}: expected=${expected}  got=${cls}`);
  }
}

// Fail-open is a contract, not a nicety: a guard that throws must never wedge a turn.
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
  `CLOSER_GUARD_SILENT_TOOL_STOP=${pass}/${pass + fail}  ` +
  `(fires: 3, must-not-fire: 4, other-classes: 3, fail-open: 3)`
);
process.exit(fail === 0 ? 0 : 1);
