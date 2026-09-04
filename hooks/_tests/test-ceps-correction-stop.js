#!/usr/bin/env node
/**
 * V-CEPS-STOP-* -- gate for the Owner-correction producer's transcript filter.
 *
 * The whole risk of this hook is in ONE decision: which transcript records are
 * the Owner actually speaking. In a Claude Code transcript `type: "user"` does
 * not mean "the human typed this" -- tool results, system reminders, hook
 * output and slash-command stdout all arrive as user records. If any of those
 * reach the correction detector, the hook manufactures Owner corrections out
 * of the harness talking to itself, and every one of them becomes a draft a
 * human then has to triage.
 *
 * So these gates are mostly NEGATIVE controls. A filter that accepted
 * everything would pass a naive happy-path test and fail every case below.
 */
'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { ownerTurns } = require('../ceps_correction_stop.js');

let passes = 0;
let fails = 0;

function ok(gate, evidence) { passes++; console.log(`  PASS  ${gate}  ${evidence}`); }
function bad(gate, diag) { fails++; console.log(`  FAIL  ${gate}  ${diag}`); }

function transcript(records) {
  const p = path.join(
    os.tmpdir(), `pp-ceps-stop-test-${process.pid}-${Math.random().toString(36).slice(2)}.jsonl`,
  );
  fs.writeFileSync(p, records.map((r) => JSON.stringify(r)).join('\n') + '\n', 'utf8');
  return p;
}

const userText = (text) => ({ type: 'user', message: { content: text } });
const userBlocks = (blocks) => ({ type: 'user', message: { content: blocks } });

console.log('== V-CEPS-STOP gates ==');

// ---- V-CEPS-STOP-ACCEPTS-OWNER --------------------------------------------
{
  const p = transcript([
    userText('add the index please'),
    { type: 'assistant', message: { content: [{ type: 'text', text: 'done' }] } },
    userText("no, actually that's wrong -- revert it"),
  ]);
  const turns = ownerTurns(p);
  if (turns.length === 2 && turns[turns.length - 1].includes('revert')) {
    ok('V-CEPS-STOP-ACCEPTS-OWNER', `${turns.length} owner turns, newest last`);
  } else {
    bad('V-CEPS-STOP-ACCEPTS-OWNER', JSON.stringify(turns));
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-DROPS-SYSTEM-REMINDER ------------------------------------
// The exact forgery this filter exists to stop: a reminder quoting a
// correction word, recorded as a user turn.
{
  const p = transcript([
    userText('<system-reminder>That was incorrect, revert the change.</system-reminder>'),
  ]);
  const turns = ownerTurns(p);
  if (turns.length === 0) {
    ok('V-CEPS-STOP-DROPS-SYSTEM-REMINDER', 'harness wrapper is not an Owner turn');
  } else {
    bad('V-CEPS-STOP-DROPS-SYSTEM-REMINDER', JSON.stringify(turns));
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-DROPS-TOOL-RESULT ----------------------------------------
{
  const p = transcript([
    userBlocks([{ type: 'tool_result', content: "that's wrong -- revert" }]),
  ]);
  const turns = ownerTurns(p);
  if (turns.length === 0) {
    ok('V-CEPS-STOP-DROPS-TOOL-RESULT', 'tool output is not an Owner turn');
  } else {
    bad('V-CEPS-STOP-DROPS-TOOL-RESULT', JSON.stringify(turns));
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-DROPS-COMMAND-STDOUT -------------------------------------
{
  const p = transcript([
    userText('<local-command-stdout>nope, incorrect</local-command-stdout>'),
  ]);
  if (ownerTurns(p).length === 0) {
    ok('V-CEPS-STOP-DROPS-COMMAND-STDOUT', 'slash-command stdout excluded');
  } else {
    bad('V-CEPS-STOP-DROPS-COMMAND-STDOUT', 'command stdout treated as Owner prose');
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-DROPS-META -----------------------------------------------
{
  const p = transcript([
    Object.assign(userText("wait, no -- stop that"), { isMeta: true }),
  ]);
  if (ownerTurns(p).length === 0) {
    ok('V-CEPS-STOP-DROPS-META', 'meta record excluded');
  } else {
    bad('V-CEPS-STOP-DROPS-META', 'meta record treated as Owner prose');
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-DROPS-HUGE-PASTE -----------------------------------------
// A correction is short. A 50 KB pasted log that happens to contain "revert"
// is not one, and drafting on it would quote 2 KB of log as a root_cause.
{
  const p = transcript([userText('revert ' + 'x'.repeat(5000))]);
  if (ownerTurns(p).length === 0) {
    ok('V-CEPS-STOP-DROPS-HUGE-PASTE', 'oversized turn excluded');
  } else {
    bad('V-CEPS-STOP-DROPS-HUGE-PASTE', 'a large paste was treated as a correction');
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-BOUNDED --------------------------------------------------
// Newest-first walk with a hard cap: the bound must fall on the RECENT turns,
// not the first five in the file.
{
  const recs = [];
  for (let i = 0; i < 40; i++) recs.push(userText(`turn ${i}`));
  const p = transcript(recs);
  const turns = ownerTurns(p);
  if (turns.length === 5 && turns[4] === 'turn 39' && turns[0] === 'turn 35') {
    ok('V-CEPS-STOP-BOUNDED', 'capped at 5, newest retained, order preserved');
  } else {
    bad('V-CEPS-STOP-BOUNDED', JSON.stringify(turns));
  }
  fs.unlinkSync(p);
}

// ---- V-CEPS-STOP-FAIL-OPEN ------------------------------------------------
// A Stop hook may never throw. Missing path, absent file, garbage lines.
{
  let threw = null;
  let results;
  try {
    const p = transcript([]);
    fs.appendFileSync(p, 'not json at all\n' + JSON.stringify(userText('revert that')) + '\n');
    results = [
      ownerTurns(undefined),
      ownerTurns(''),
      ownerTurns(path.join(os.tmpdir(), 'pp-ceps-does-not-exist.jsonl')),
      ownerTurns(p),
    ];
    fs.unlinkSync(p);
  } catch (err) {
    threw = err;
  }
  if (!threw && results[0].length === 0 && results[1].length === 0
      && results[2].length === 0 && results[3].length === 1) {
    ok('V-CEPS-STOP-FAIL-OPEN', 'absent/garbage input degrades, real line still read');
  } else {
    bad('V-CEPS-STOP-FAIL-OPEN', threw ? `raised: ${threw.message}` : JSON.stringify(results));
  }
}

const total = passes + fails;
console.log(`CEPS_STOP_PASS=${passes}/${total}  threshold=${total}/${total}`);
assert.strictEqual(fails, 0, `${fails} gate(s) failed`);
process.exit(fails === 0 ? 0 : 1);
