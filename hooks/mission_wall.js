// mission_wall.js -- the mission hand-off wall, checked MID-TURN (PostToolUse).
//
// The context watchdog judges the wall at Stop, i.e. at the END of a turn. A mission worker
// does its work in one long turn, so the wall was never judged while it mattered. Measured
// 2026-09-24 (W8, worker ef5fe657): 16 files into its first turn, its context metrics read
// used_pct=39 against a 40 % wall and context-watchdog.log held zero lines for the session.
// This is the Stop-only twin of the gap buildomator documented for PreCompact ("microcompact").
//
// In-process member of the dispatcher's PostToolUse-default lane: exports run(event).
// Cost for every non-mission session: one fs.statSync on a marker path that does not exist.
// A PostToolUse `decision:"block"` hands the reason back to the model mid-turn.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const STATE = process.env.GSD_AUTORUN_MARKER_DIR || path.join(os.homedir(), '.claude', 'state');
const SID_RE = /^[A-Za-z0-9._-]{1,128}$/;
const NOTE_TAG = 'HANDOFF NOTE:';  // must match tools/gsd_mission.py NOTE_TAG
const REASK_STEP_PCT = 3;          // re-ask a worker still working this many points past its last notice
const DEFAULT_GRACE_S = 1800;      // must match tools/gsd_epoch.py WALL_GRACE_S
const COST_HOLD_GRACE_S = 600;     // must match tools/gsd_epoch.py COST_HOLD_GRACE_S
const MISSION_STATE = process.env.GSD_LONG_RUN_STATE_DIR || path.join(os.homedir(), '.claude', 'state');

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

// spec mission-cost-hold-stops-worker. Measured 2026-10-11 (m-560939805e63): the cost breaker held the
// mission at 74.5M processed; its busy worker never heard of it and autocompacted on in one turn to 265.5M.
// The hold is now told to the worker on every tool call, whatever its context reads.
function isCostHold(hold) {
  return !!hold && (hold.kind === 'cost' || String(hold.reason || '').startsWith('cost breaker'));
}

function costHoldNotice(sid, marker) {
  const rec = readJson(path.join(MISSION_STATE, `gsd-mission-${marker.mission_id}.json`));
  const hold = rec && rec.owner_hold;
  if (!isCostHold(hold) || hold.worker_stopped_at) return null;
  const flag = path.join(STATE, `mission-costhold-${sid}.flag`);
  // The flag belongs to ONE hold (its set_at): a flag left by an earlier, released hold on the same
  // session must not hand the next trip an already-expired grace.
  const read = readJson(flag);
  const prev = read && read.hold_set_at === hold.set_at && Number(read.asked_at) > 0 ? read : null;
  const askedAt = prev ? Number(prev.asked_at) : Date.now();
  const n = prev ? Number(prev.n || 1) + 1 : 1;
  try { fs.writeFileSync(flag, JSON.stringify({ asked_at: askedAt, n, hold_set_at: hold.set_at })); } catch (e) { return null; }
  const graceS = Number((rec.wall || {}).cost_hold_grace_s) > 0 ? Number(rec.wall.cost_hold_grace_s) : COST_HOLD_GRACE_S;
  const stopAt = new Date(askedAt + graceS * 1000).toISOString().slice(11, 16) + 'Z';
  return {
    decision: 'block',
    reason:
      `COST HOLD${n > 1 ? `, NOTICE ${n}` : ''} — mission ${marker.mission_id} is over its token budget and the ` +
      `Owner must decide before more is spent (${String(hold.reason).slice(0, 240)}). Do exactly this: ` +
      '(1) finish ONLY the atomic step in progress and make it durable (commit / save) — start nothing new, ' +
      'launch no agent, run no further plan; (2) end your response with a paragraph that begins ' +
      `\`${NOTE_TAG}\` stating the next exact action. Do NOT run /compact. If this turn has not ended by ` +
      `${stopAt}, the supervisor STOPS this session there.`,
  };
}

function decide(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  // A mission worker is named by its v2 marker OR by the worker index the supervisor writes at
  // SessionStart (tools/gsd_mission.py write_worker_index). Measured 2026-10-11: the marker is refused
  // for a resume command over 200 chars, and the hook then never judged that worker at all.
  const markerPath = path.join(STATE, `gsd-autorun-${sid}.json`);
  const indexPath = path.join(STATE, `mission-worker-${sid}.json`);
  let marker = fs.existsSync(markerPath) ? readJson(markerPath) : null;
  if (!marker || !marker.mission_id) {
    if (!fs.existsSync(indexPath)) return null;           // the ordinary path: two stats, done
    marker = readJson(indexPath);
  }
  if (!marker || !marker.mission_id) return null;          // legacy v2 run: the watchdog owns it
  const cost = costHoldNotice(sid, marker);
  if (cost) return cost;
  const wall = marker.wall || {};
  const adv = Number(wall.advisory);
  if (!(adv > 0 && adv <= 95)) return null;
  const metrics = readJson(path.join(os.tmpdir(), `claude-ctx-${sid}.json`));
  const used = metrics && Number(metrics.used_pct);
  if (!(used >= adv)) return null;
  // One flag per worker epoch: the flag carries the epoch, so a successor is judged afresh.
  // It records the FIRST notice (asked_at -- the supervisor's enforcement clock) and the last one.
  // Measured 2026-09-28 (m-916e905e23d4, worker 9e89a87e): asked once at 31 %, the worker kept
  // working in the same turn for 3.5 h up to 49 % and never handed off. A single request is not a
  // wall: past the first notice the worker is asked again every REASK_STEP_PCT, and every notice
  // names the moment the supervisor stops the session (tools/gsd_epoch.py wall_overdue).
  const flag = path.join(STATE, `mission-wall-${sid}-e${marker.epoch}.flag`);
  let prev = null;
  if (fs.existsSync(flag)) {
    prev = readJson(flag);
    if (!prev || typeof prev !== 'object') {       // pre-2026-09-28 flag: a bare timestamp
      let st = null; try { st = fs.statSync(flag); } catch (e) { return null; }
      prev = { asked_at: st.mtimeMs, pct: adv, n: 1 };
    }
    if (!(used >= Number(prev.pct) + REASK_STEP_PCT)) return null;
  }
  const askedAt = prev ? Number(prev.asked_at) : Date.now();
  const n = prev ? Number(prev.n || 1) + 1 : 1;
  try { fs.writeFileSync(flag, JSON.stringify({ asked_at: askedAt, pct: used, n })); } catch (e) { return null; }
  const graceS = Number(wall.grace_s) > 0 ? Number(wall.grace_s) : DEFAULT_GRACE_S;
  const stopAt = new Date(askedAt + graceS * 1000).toISOString().slice(11, 16) + 'Z';
  const head = n === 1
    ? `CONTEXT WALL — ${used}% used (>= ${adv}%).`
    : `CONTEXT WALL, NOTICE ${n} — ${used}% used, ${Math.round(used - adv)} points past the wall. You did not hand off.`;
  return {
    decision: 'block',
    reason:
      `${head} This mission continues in a FRESH session; ` +
      `this one ends here (mission ${marker.mission_id}, epoch ${marker.epoch}). Do exactly this: ` +
      '(1) finish ONLY the atomic step in progress and make it durable (commit / save) — start ' +
      `nothing new; (2) end your response with a paragraph that begins \`${NOTE_TAG}\` stating ` +
      'the next exact action and any fact the repository does not record. Do NOT run /compact ' +
      'and do NOT re-issue the run command: the supervisor starts the next worker once this turn ends. ' +
      `If this turn has not ended by ${stopAt}, the supervisor STOPS this session there and hands ` +
      'the work on as it stands: anything not committed by then is left to the successor to find.',
  };
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }  // fail-open: never break a tool call
}

module.exports = { run, decide, isCostHold, NOTE_TAG, REASK_STEP_PCT, DEFAULT_GRACE_S, COST_HOLD_GRACE_S };
