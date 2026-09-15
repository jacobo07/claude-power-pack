#!/usr/bin/env node
'use strict';
// V-DISPATCHER-DRIFT
//
// The repo's hooks/hook-dispatcher.js was 34,424 bytes last touched 08-31 while
// the live ~/.claude/hooks/hook-dispatcher.js was 63,809 bytes touched the same
// day it was measured. Nothing generated one from the other. It was an abandoned
// twin asserting an authority it did not have, and it is why GSDX-U04 was
// carried for a session as "one line the Owner must add": there was no artifact
// that could own a registration and survive a reinstall.
//
// Adopting the live file fixed that once. This gate is what stops it decaying
// again, because a mirror with no drift check is a mirror that WILL rot -- and a
// stale twin is worse than no twin, since it reads as a source of truth.
//
// Deliberately NOT a fixer. It reports the direction of the drift and refuses to
// guess which side is right: the live file is the one the harness executes, but
// a change committed here and not yet synced is also legitimate. Overwriting
// either side automatically is how a session destroys another pane's work.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const REPO = path.resolve(__dirname, '..', 'hooks', 'hook-dispatcher.js');
const LIVE = process.env.CLAUDE_DISPATCHER_PATH ||
  path.join(os.homedir(), '.claude', 'hooks', 'hook-dispatcher.js');

let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log('  OK   ' + id + '  ' + ev); };
const no = (id, ev) => { fail++; console.log('  FAIL ' + id + '  ' + ev); };

function sha(p) {
  return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
}

// Positive control FIRST. An absent file must not read as "no drift" -- that is
// the empty-expectation trap: a check that found nothing looks exactly like a
// check that found everything in order.
if (!fs.existsSync(REPO)) {
  no('CTRL-REPO-PRESENT', 'repo copy missing at ' + REPO);
} else {
  ok('CTRL-REPO-PRESENT', path.basename(REPO) + ' ' + fs.statSync(REPO).size + ' bytes');
}

if (!fs.existsSync(LIVE)) {
  // Not a failure of the subject: this repo is portable and a clone on another
  // host has no live dispatcher. Say so rather than inventing a verdict.
  console.log('  SKIP DRIFT  no live dispatcher at ' + LIVE + ' -- UNMEASURED, not clean');
  console.log('DISPATCHER_DRIFT=' + pass + '/' + (pass + fail) + '  (drift UNMEASURED on this host)');
  process.exit(fail === 0 ? 0 : 1);
}
ok('CTRL-LIVE-PRESENT', fs.statSync(LIVE).size + ' bytes');

const a = sha(REPO), b = sha(LIVE);
if (a === b) {
  ok('NO-DRIFT', 'repo and live are byte-identical (' + a.slice(0, 16) + ')');
} else {
  const ra = fs.statSync(REPO).mtimeMs, rb = fs.statSync(LIVE).mtimeMs;
  const newer = rb > ra ? 'LIVE is newer' : 'REPO is newer';
  no('NO-DRIFT',
    'diverged -- ' + newer + '. repo=' + a.slice(0, 12) + ' live=' + b.slice(0, 12) +
    '. Reconcile deliberately: if live is newer, copy live->repo and commit; if repo ' +
    'is newer, sync repo->live. Never guess, and bracket the copy on the live file\'s ' +
    'hash before and after -- another pane may be writing it.');
}

const total = pass + fail;
console.log('DISPATCHER_DRIFT=' + pass + '/' + total + '  threshold=' + total + '/' + total);
process.exit(fail === 0 ? 0 : 1);
