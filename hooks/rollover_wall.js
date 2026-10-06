// rollover_wall.js -- the INTERACTIVE rollover wall, checked MID-TURN (PostToolUse).
//
// The context watchdog judges the wall at Stop, i.e. at the END of a turn, and the rollover
// (/kclear -> gate -> /clear -> /kresume focus on ...) can only start from there. A turn that
// runs for hours never gets judged. Measured 2026-09-29, session f8ea8727: the last turn that
// ended closed at 381k (~38 %); the next one ran 3+ hours in auto mode with agents to 688k
// (~69 %) and was interrupted before any Stop, so the 45 % wall passed unseen -- zero
// watchdog ledger rows for the session.
//
// Interactive twin of mission_wall.js (which owns mission workers and is left alone here).
// Same metrics bridge and same thresholds as context-watchdog.py, so both judge one wall.
// In-process member of the dispatcher's PostToolUse-default lane: exports run(event).
// Cost below the wall: one small JSON read. A PostToolUse `decision:"block"` hands the
// reason back to the model mid-turn; it never blocks the Owner.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

// Must match modules/zero-crash/hooks/context-watchdog.py (pinned by tools/test_rollover_wall.py).
const ADVISORY_PCT = 45;
const REARM_PCT = 30;
const REARM_FLOOR_PCT = 28;
const REASK_STEP_PCT = 3;     // same step as mission_wall.js: one notice was ignored for 3.5 h
const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;

function stateDir() {
  return process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');
}

function markerDir() {
  return process.env.GSD_AUTORUN_MARKER_DIR || path.join(os.homedir(), '.claude', 'state');
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '')); } catch (e) { return null; }
}

// context-watchdog.py valid_thresholds(): rearm < snapshot <= advisory, all in floor..95.
function validThresholds(snap, adv, rearm) {
  const s = Number(snap), a = Number(adv), r = Number(rearm);
  if (![s, a, r].every(Number.isFinite)) return null;
  return (REARM_FLOOR_PCT <= r && r < s && s <= a && a <= 95) ? { adv: a, rearm: r } : null;
}

// Same sources and order as context-watchdog.py _thresholds(), minus the mission marker
// (missions are mission_wall.js's): the session's own file, then the env, then constants.
function thresholds(sid) {
  const f = readJson(path.join(stateDir(), `ctxwd-thresholds-${sid}.json`));
  const fromFile = f ? validThresholds(f.snapshot, f.advisory, f.rearm) : null;
  if (fromFile) return fromFile;
  const raw = String(process.env.CTXWD_TEST_THRESHOLDS || '');
  if (raw) {
    const parts = raw.split(',');
    const fromEnv = parts.length === 3 ? validThresholds(parts[0], parts[1], parts[2]) : null;
    if (fromEnv) return fromEnv;
  }
  return { adv: ADVISORY_PCT, rearm: REARM_PCT };
}

function decide(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const sw = String(process.env.CPP_ROLLOVER_ACTIVE || '').trim().toLowerCase();
  if (sw === '0' || sw === 'off' || sw === 'false') return null;    // the watchdog's own switch
  if (fs.existsSync(path.join(markerDir(), `gsd-autorun-${sid}.json`))) return null;  // a run's wall
  const metrics = readJson(path.join(os.tmpdir(), `claude-ctx-${sid}.json`));
  const used = metrics && Number(metrics.used_pct);
  if (!Number.isFinite(used)) return null;
  const { adv, rearm } = thresholds(sid);
  const flag = path.join(stateDir(), `rollover-wall-${sid}.flag`);
  if (used < rearm) {
    // A fresh context: the crossing is over, the next one is noticed again (watchdog rearm).
    try { fs.unlinkSync(flag); } catch (e) { /* nothing was armed */ }
    return null;
  }
  if (used < adv) return null;
  const prev = readJson(flag);
  if (prev && !(used >= Number(prev.pct) + REASK_STEP_PCT)) return null;
  const n = prev ? Number(prev.n || 1) + 1 : 1;
  try {
    fs.mkdirSync(stateDir(), { recursive: true });
    fs.writeFileSync(flag, JSON.stringify({ pct: used, n: n, at: new Date().toISOString() }));
  } catch (e) {
    return null;   // a notice that cannot be debounced would repeat on every tool call
  }
  const head = n === 1
    ? `CONTEXT WALL — ${used}% used (>= ${adv}%), in the middle of a turn.`
    : `CONTEXT WALL, NOTICE ${n} — ${used}% used, ${Math.round(used - adv)} points past the wall, and this turn has still not ended.`;
  return {
    decision: 'block',
    reason:
      `${head} This pane continues in a FRESH session (/kclear -> /clear -> /kresume focus on ` +
      'the next step), and YOU start it. Do exactly this, in THIS turn: ' +
      '(1) finish ONLY the atomic step in progress and make it durable (commit / save) -- start ' +
      'nothing new, dispatch no new agents; (2) invoke the kclear skill NOW (Skill tool, ' +
      'skill: "kclear"), naming the next exact action as the first open obligation -- that seals ' +
      'the capsule; (3) END this turn with a short status. The Stop that follows gates the sealed ' +
      'capsule (context-watchdog _self_sealed_step) and, on SAFE_TO_FORGET, types /clear and arms ' +
      '/kresume focus on that obligation in the fresh session. Ending the turn WITHOUT /kclear ' +
      'strands the rollover (measured 2026-10-06: the Owner had to type it). Do NOT run /compact ' +
      'or /clear yourself.',
  };
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }  // fail-open: never break a tool call
}

module.exports = { run, decide, ADVISORY_PCT, REARM_PCT, REARM_FLOOR_PCT, REASK_STEP_PCT };
