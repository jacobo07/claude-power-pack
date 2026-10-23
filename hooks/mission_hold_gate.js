// mission_hold_gate.js -- standalone PreToolUse hold gate for a mission worker and its subagents (T1 F1).
//
// lib/mission_gate.js refuses every tool call of a cost-held worker, but it is reached only through
// session_budget_guard inside hook-dispatcher's Bash/Edit/Read/Agent lanes. Measured 2026-10-23 (T1,
// m-260aa89142c8 on GEX44): that host registers no such lane, so 145.85M were processed after the 06:41Z
// stall hold and 43.52M after the 09:41Z authority hold. This is the same hold check with its own stdin
// entrypoint, registered directly (matcher "*"). Subagents carry the parent's session_id, so they are
// fenced by the same marker. Hold-only: it bumps no subagent counter, so it is safe beside the dispatcher
// lane. Cost for every non-mission session: one failed read of a marker that does not exist.
// Own error -> allow (fail open). Kill switch CPP_MISSION_GATE=off. Pinned: tools/test_mission_gate.py.
'use strict';
const gate = require('./lib/mission_gate');

// -> hook output object or null (never throws).
function run(event) {
  try {
    if (gate.off()) return null;
    const r = gate.holdDecision(event || {});
    if (r && r.deny) {
      return { hookSpecificOutput: { hookEventName: 'PreToolUse',
        permissionDecision: 'deny', permissionDecisionReason: r.deny } };
    }
  } catch (e) { /* fail open */ }
  return null;
}

if (require.main === module) {
  let buf = '';
  process.stdin.on('data', (d) => { buf += d; });
  process.stdin.on('end', () => {
    try {
      const out = run(JSON.parse(buf.replace(/^﻿/, '') || '{}'));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) { /* fail open: unreadable event */ }
    process.exit(0);
  });
}

module.exports = { run };
