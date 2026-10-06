#!/usr/bin/env node
'use strict';
// Rollover autotype, as its OWN SessionStart hook (registered top-level in settings.json,
// never inside SessionStart-chain).
//
// Measured 2026-09-29 (cf02a0a5 -> 7e953f9d): /kclear and /clear were typed, the capsule
// was sealed, and no `/kresume focus on ...` ever arrived. The dispatcher log shows why:
//   [SessionStart-chain] CHAIN-DEADLINE-ABANDONED after 4000ms ... still running:
//   session_start_hub.js ... host free=3716MB/32061MB
// The hub was reaped before it wrote a single log line, so moving the arm to the top of
// its main() (435014d6) could not help: the hub never got that far. The chain's 4 s budget
// is right for the card and wrong for the one action that races the Owner's first
// keystroke. A top-level hook has only the harness timeout, so the arm no longer shares a
// deadline with ten other SessionStart jobs.
//
// Same functions as the hub (required, not copied, so the card and the autotype cannot
// disagree about which capsule is here). Emits nothing; the hub still shows the card.
// Kill switch: CPP_KRESUME_AUTOTYPE=off (checked inside armKresumeAutotype).
//
// Measured 2026-09-30 (0518ccd0 -> 31ab653e): the require below also imported the hub's
// 2 s stdin budget. On a starved host the payload arrived later, the read timed out, the
// payload became {}, and the arm was skipped for want of a session id. The budget is the
// hub's to own, so this hook sets its own. Must be set BEFORE the require.
//
// Measured 2026-10-01 (bf89cbb9 -> 66f6a312): four panes cleared within minutes, every
// SessionStart hook took 16-25 s, and the harness cancelled this one at its 15 s timeout
// (`hook_cancelled ... timedOut:true durationMs:17878`) before it armed or logged. The
// timeout is now 60 s in settings.json; the budget is 45 s, so the hub's hard-exit
// (budget + 3 s = 48 s) still lands inside it. On a healthy host this exits in < 1 s.
if (!process.env.PP_HUB_STDIN_BUDGET_MS) {
  process.env.PP_HUB_STDIN_BUDGET_MS = '45000';
}
const hub = require('./session_start_hub.js');

// One arm, two callers: the SessionStart payload below, and the PREDECESSOR's courier
// (tools/kresume_courier.py) through `--arm`. Spec vault/specs/kresume-courier.md. The flag is
// written only by hub.armKresumeAutotype, so the two paths cannot disagree about its shape,
// and it is keyed by session id, so both arming the same successor still types one line.
function arm(sessionId, cwd, transcriptPath) {
  if (!hub.hookRolloverResume(cwd, 'clear')) {
    return { armed: null, why: 'no unretired capsule for this cwd' };
  }
  const flag = hub.armKresumeAutotype(sessionId, cwd, transcriptPath, hub.rolloverFocus(cwd, 'clear'));
  return { armed: flag, why: flag ? 'armed' : 'declined (kill switch, no session id, or write failed)' };
}

async function main() {
  const payload = await hub.getStdinPayload();
  const sid = (typeof payload.session_id === 'string') ? payload.session_id : '';
  const source = (typeof payload.source === 'string') ? payload.source : '';
  if (!sid || !source) {
    // Measured 2026-10-01: this returned silently, so two missed /kresume left no trace at
    // all. A starved stdin cannot be armed from here (there is no session id to route to);
    // the courier is the path that still arms it, and this line is how a miss stays visible.
    hub.note('rollover_autotype: SessionStart payload had no ' + (sid ? 'source' : 'session id')
      + ' (stdin starved?) -- not armed here; the predecessor courier covers a rollover');
    return;
  }
  if (source !== 'clear') {
    return;   // a startup, resume or compaction is not a rollover crossing
  }
  const cwd = (typeof payload.cwd === 'string' && payload.cwd) ? payload.cwd : process.cwd();
  arm(sid, cwd, (typeof payload.transcript_path === 'string') ? payload.transcript_path : '');
}

// `node rollover_autotype.js --arm <sid> <cwd> <transcript>`: never reads stdin, prints one
// JSON line {armed, why}, exits 0. The courier reads the line; a missing line is ARM_FAILED.
function cli(argv) {
  const [sid, cwd, transcript] = argv.slice(argv.indexOf('--arm') + 1);
  let out;
  try {
    out = arm(sid || '', cwd || '', transcript || '');
  } catch (err) {
    out = { armed: null, why: 'arm threw: ' + ((err && err.message) || err) };
  }
  process.stdout.write(JSON.stringify(out) + '\n', () => process.exit(0));
}

if (require.main === module) {
  if (process.argv.includes('--arm')) {
    cli(process.argv);
  } else {
    main().catch((err) => hub.note('rollover_autotype: main rejected', err))
      .finally(() => process.exit(0));
  }
}

module.exports = { main, arm };
