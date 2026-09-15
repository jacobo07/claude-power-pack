#!/usr/bin/env node
// GSD X -- the ExecutionOS Lite tier, measured instead of self-assessed.
//
// UserPromptSubmit. Level-2 advisory: it NEVER blocks, never denies, and never
// costs the user their prompt. On any failure it prints nothing and exits 0,
// which degrades exactly to the behaviour that exists today -- the standing
// reminder's constant "Default LIGHT."
//
// WHY THE BUDGET WAS SMALL, AND WHY IT IS NOT ANY MORE. MEASURED 2026-09-15.
//
// The premise above this line was: the chain is sequential (CHAIN_CONCURRENCY
// carried no UserPromptSubmit-chain entry, so DEFAULT_CONCURRENCY = 1), its
// per-step budgets sum to 46000 ms against a 15000 ms ceiling, and a chain
// killed at the ceiling loses the dispatcher's stdout so every advisory dies
// together. That premise is now FALSE: the dispatcher carries
// 'UserPromptSubmit-chain': 4, added with the measurement that forced it. The
// bound is the slowest member, not the sum, so a sixth step no longer has to be
// priced against 46 seconds.
//
// The 2500 ms cap was derived from that dead premise and it was doing real
// damage. Measured, 7 runs each, real payloads, host headroom bracketed:
//   python interpreter floor      681 ms median
//   + import modules.gsd_x.tier   774 ms median   (the module costs ~93 ms)
//   full cli.py, real prompt     1233 ms median, 1443 ms max
// So the child is NOT intrinsically over budget -- 60% of its cost is
// interpreter startup, which no amount of module work removes and which only a
// resident process would, and this estate does not get one. But under ordinary
// contention the same child exceeded 2500 ms on 3 of 7 heavy prompts, and the
// hook then emitted NOTHING.
//
// THAT SILENCE IS THE DEFECT, NOT THE LATENCY. A child killed at the cap and a
// child that ran and correctly had nothing to say produce the identical
// observable: no stdout. The heartbeat cannot tell them apart either, because
// the heartbeat is written BY THE CHILD -- so a killed child records nothing and
// the counter reports only its own successes. An instrument structurally
// incapable of counting its misses reads as healthy exactly when it is not.
//
// Two changes follow. The cap rises to a measured multiple of observed
// worst-case rather than a guessed constant. And the node side -- the only
// party that can observe the kill, because it is the one that kills -- records
// the timeout into the SAME heartbeat, so VALID_SILENCE and HOOK_TIMED_OUT stop
// being one state. No second heartbeat authority is created.

'use strict';

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// 6000 ms = ~4x the observed child median and ~4x its observed max on a starved
// host. Sized against the thing we are willing to call slow, not against noise:
// a generous cap costs nothing when the child is fast, because spawnSync returns
// as soon as the child exits.
const CHILD_TIMEOUT_MS = 6000;
const KILL_SWITCH = String(process.env.CLAUDE_GSDX || '').toLowerCase() === 'off';

function allow(text) {
  if (text) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: text,
      },
    }));
  }
  process.exit(0);
}

function pythonExe() {
  // Prefer an explicit interpreter; fall back to the launcher, then PATH. A
  // missing interpreter must be silence, never a thrown hook.
  const explicit = process.env.CLAUDE_PY_EXE;
  if (explicit && fs.existsSync(explicit)) return explicit;
  const known = path.join(
    process.env.LOCALAPPDATA || '',
    'Programs', 'Python', 'Python312', 'python.exe'
  );
  if (fs.existsSync(known)) return known;
  return process.platform === 'win32' ? 'py' : 'python3';
}

// Same file, same convention, same atomic replace as modules/gsd_x/heartbeat.py.
// Deliberately NOT a second heartbeat authority -- one store, two writers, and
// the python side stays the only writer of `judgements`.
//
// `judgements` is left alone on purpose. It is the denominator of
// informative_rate(), and a run whose child died made no judgement; counting it
// would dilute a rate with events that were never evaluated. A non-zero
// child_timeouts is instead the signal that the denominator is INCOMPLETE,
// which is a different and more honest statement than a lower percentage.
//
// Honest limit: read-modify-write across two processes can lose an update if a
// child write and a timeout write interleave. One prompt is handled at a time
// per session, so the window needs two concurrent sessions to open at all, and
// this is an observability aid whose failure must never cost a turn. Recorded
// rather than solved with a lock nobody would maintain.
function countFailure(key) {
  try {
    const dir = process.env.CLAUDE_STATE_DIR ||
      path.join(os.homedir(), '.claude', 'state');
    const file = path.join(dir, 'gsd-x-heartbeat.json');
    let state = {};
    try {
      state = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^﻿/, ''));
    } catch (_) {
      state = {};
    }
    state[key] = (Number(state[key]) || 0) + 1;
    state.last_failure = Date.now() / 1000;
    state.last_failure_kind = key;
    fs.mkdirSync(dir, { recursive: true });
    const tmp = file + '.node.tmp';
    fs.writeFileSync(tmp, JSON.stringify(state), 'utf8');
    fs.renameSync(tmp, file);                    // atomic; no torn reads
  } catch (_) {
    /* fail-open absolute: an observability aid must never cost a turn */
  }
}

function main() {
  if (KILL_SWITCH) process.exit(0);

  let raw = '';
  try {
    raw = fs.readFileSync(0, 'utf8');
  } catch (_) {
    process.exit(0);
  }
  if (!raw || !raw.trim()) process.exit(0);

  // Cheap pre-filter. Parsing here avoids paying for a python spawn on a
  // payload that carries no prompt at all.
  let prompt = '';
  try {
    const payload = JSON.parse(raw);
    prompt = payload.prompt || payload.user_prompt || payload.userPrompt || '';
  } catch (_) {
    process.exit(0);
  }
  if (!String(prompt).trim()) process.exit(0);

  const cli = path.resolve(__dirname, '..', 'modules', 'gsd_x', 'cli.py');
  if (!fs.existsSync(cli)) process.exit(0);

  let out = '';
  try {
    const res = spawnSync(pythonExe(), [cli], {
      input: raw,
      encoding: 'utf8',
      timeout: CHILD_TIMEOUT_MS,
      killSignal: 'SIGKILL',
      shell: false,                       // no bash.exe is ever created
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      windowsHide: true,
    });
    // A timed-out or crashed child still emits nothing to the user -- that part
    // is unchanged and deliberate, because an advisory must never cost a turn.
    // What changes is that the failure is now COUNTED. Only this side can do it:
    // the child that was killed never reached its own heartbeat write.
    // THREE states, and collapsing any two is the defect this block exists to
    // prevent. Measured shapes, 2026-09-15:
    //   healthy, had something to say : status 0, signal null, stdout non-empty
    //   healthy, correctly silent     : status 0, signal null, stdout ""
    //   killed at the cap             : status null, signal SIGKILL, ETIMEDOUT
    // The middle row is the trap, and the first version of this block fell in
    // it: an exit-0 child with empty stdout is a JUDGEMENT -- a trivial prompt
    // that earned no escalation -- and counting it as a failure makes the floor
    // look broken every time it works.
    if (res && res.status === 0) {
      out = res.stdout ? String(res.stdout).trim() : '';
    } else if (res && (res.signal === 'SIGKILL' ||
                       (res.error && res.error.code === 'ETIMEDOUT'))) {
      countFailure('child_timeouts');
    } else {
      countFailure('child_failures');
    }
  } catch (_) {
    out = '';
    countFailure('child_failures');
  }

  allow(out);
}

try {
  main();
} catch (_) {
  process.exit(0);          // fail-open, absolute
}
