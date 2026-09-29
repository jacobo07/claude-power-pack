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
const hub = require('./session_start_hub.js');

async function main() {
  const payload = await hub.getStdinPayload();
  const source = (typeof payload.source === 'string') ? payload.source : '';
  const cwd = (typeof payload.cwd === 'string' && payload.cwd) ? payload.cwd : process.cwd();
  if (!hub.hookRolloverResume(cwd, source)) {
    return;
  }
  hub.armKresumeAutotype(
    (typeof payload.session_id === 'string') ? payload.session_id : '',
    cwd,
    (typeof payload.transcript_path === 'string') ? payload.transcript_path : '',
    hub.rolloverFocus(cwd, source));
}

if (require.main === module) {
  main().catch(() => { /* fail-open: the hub's card still tells a human to type /kresume */ })
    .finally(() => process.exit(0));
}

module.exports = { main };
