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

// Authorship recency of the REPO copy, which is not the same question as its
// mtime. git stamps mtime at CHECKOUT time, so creating a worktree, switching a
// branch or merging makes this file "newer" than a live dispatcher nobody has
// touched for days. Returns null when it cannot be established -- an uncommitted
// copy, or no reachable git -- because the alternative is inventing a direction.
function repoAuthoredMs() {
  const { execFileSync } = require('child_process');
  const dir = path.dirname(REPO);
  const candidates = [process.env.CLAUDE_GIT_EXE, 'git'];
  if (process.platform === 'win32') {
    // This host's non-interactive PATH carries GitHub CLI, not git's cmd dir.
    candidates.push('C:\\Program Files\\Git\\cmd\\git.exe');
  }
  for (const exe of candidates) {
    if (!exe) continue;
    try {
      const run = (args) => execFileSync(exe, ['-C', dir].concat(args),
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
      // Uncommitted bytes are not described by any commit's timestamp.
      if (run(['status', '--porcelain', '--', REPO]).trim()) return null;
      const ct = run(['log', '-1', '--format=%ct', '--', REPO]).trim();
      return ct ? parseInt(ct, 10) * 1000 : null;
    } catch (_) { /* try the next candidate */ }
  }
  return null;
}

const a = sha(REPO), b = sha(LIVE);
if (a === b) {
  ok('NO-DRIFT', 'repo and live are byte-identical (' + a.slice(0, 16) + ')');
} else {
  const authored = repoAuthoredMs();
  // The live copy is unversioned and nothing rewrites it mechanically, so its
  // mtime is an honest authorship signal. The repo copy's is not.
  const liveMs = fs.statSync(LIVE).mtimeMs;
  const hashes = 'repo=' + a.slice(0, 12) + ' live=' + b.slice(0, 12);
  const bracket = ' Bracket any copy on the live file\'s hash before and after -- ' +
    'another pane may be writing it.';

  if (authored === null) {
    // Third outcome. A direction we cannot establish must not be reported as
    // one we can: naming the wrong one here sends the operator to overwrite the
    // executing dispatcher with a stale snapshot.
    no('NO-DRIFT',
      'diverged, DIRECTION UNDETERMINED -- the repo copy is uncommitted or git ' +
      'is unreachable, so its authorship time is unknown. ' + hashes +
      '. Attribute the change before reconciling: find which pane wrote the live ' +
      'file and what it changed. Do NOT copy in either direction on a guess.' + bracket);
  } else if (liveMs > authored) {
    no('NO-DRIFT',
      'diverged -- LIVE is newer (live mtime ' + new Date(liveMs).toISOString() +
      ' > repo authored ' + new Date(authored).toISOString() + '). ' + hashes +
      '. Reconcile by copying live->repo and committing, once you have attributed ' +
      'the live change.' + bracket);
  } else {
    no('NO-DRIFT',
      'diverged -- REPO is newer (repo authored ' + new Date(authored).toISOString() +
      ' > live mtime ' + new Date(liveMs).toISOString() + '). ' + hashes +
      '. The repo carries a committed change the live dispatcher has not received; ' +
      'sync repo->live.' + bracket);
  }
}

const total = pass + fail;
console.log('DISPATCHER_DRIFT=' + pass + '/' + total + '  threshold=' + total + '/' + total);
process.exit(fail === 0 ? 0 : 1);
