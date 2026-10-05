#!/usr/bin/env node
/**
 * A chain-deadline log line names the session it cut (incremental-cognition pillar K, 2026-10-05).
 *
 * The startup-floor gate refuses to judge a window whose SessionStart chain was abandoned: an abandoned hub and a hub
 * that settled with nothing to say both leave `{"continue":true}` in the transcript, and on a host running many
 * sessions a timestamp cannot say whose start was cut. sessionOf() is what the dispatcher appends as `session=<id>`.
 * Both poles: a real id passes through; anything that is not a plain id reads 'unknown' and never throws.
 *
 * Run: node hooks/tests/test-dispatcher-session-of.js   (DISPATCHER=<path> to test another copy)
 */
'use strict';
const path = require('path');
const fs = require('fs');

const target = process.env.DISPATCHER || path.join(__dirname, '..', 'hook-dispatcher.js');
const { sessionOf } = require(target);
let failures = 0;
function check(name, cond, ev) {
  if (cond) console.log(`  PASS  ${name}${ev ? ` — ${ev}` : ''}`);
  else { failures++; console.error(`  FAIL  ${name}${ev ? ` — ${ev}` : ''}`); }
}

console.log('test-dispatcher-session-of');
check('sessionOf is exported', typeof sessionOf === 'function');
if (typeof sessionOf === 'function') {
  const sid = '6eba7a1f-7d66-49eb-b125-9e554800308d';
  check('a real session id passes through', sessionOf(JSON.stringify({ session_id: sid, hook_event_name: 'SessionStart' })) === sid);
  check('no payload reads unknown', sessionOf('') === 'unknown' && sessionOf(undefined) === 'unknown');
  check('non-JSON reads unknown', sessionOf('{not json') === 'unknown');
  check('a non-string id reads unknown', sessionOf(JSON.stringify({ session_id: 42 })) === 'unknown');
  // Whatever lands in the log must be a plain id: a path, a newline or a separator could forge or split a line.
  check('an id that could forge a log line reads unknown',
    sessionOf(JSON.stringify({ session_id: 'x; session=6eba7a1f\nFAKE' })) === 'unknown'
    && sessionOf(JSON.stringify({ session_id: '../../etc' })) === 'unknown');
}
// Wiring: both abandonment sites carry it. A source read, so it is named as one: the runtime proof is the next real
// abandoned SessionStart whose log line carries session=<id> (evidence/K-prg-*.md).
const src = fs.readFileSync(target, 'utf8');
const sites = (src.match(/CHAIN-DEADLINE-ABANDONED[\s\S]{0,400}?session=' \+ sessionOf\(rawStdin\)/g) || []).length;
check('both deadline-abandonment log sites append session=<id> (source)', sites === 2, `${sites} of 2`);

if (failures) { console.error(`test-dispatcher-session-of: ${failures} failed`); process.exit(1); }
console.log('test-dispatcher-session-of: all passed');
