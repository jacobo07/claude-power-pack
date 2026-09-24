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

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { return null; }
}

function decide(event) {
  const sid = event && event.session_id;
  if (!sid || !SID_RE.test(sid)) return null;
  const markerPath = path.join(STATE, `gsd-autorun-${sid}.json`);
  if (!fs.existsSync(markerPath)) return null;            // the ordinary path: one stat, done
  const marker = readJson(markerPath);
  if (!marker || !marker.mission_id) return null;          // legacy v2 run: the watchdog owns it
  const wall = marker.wall || {};
  const adv = Number(wall.advisory);
  if (!(adv > 0 && adv <= 95)) return null;
  const metrics = readJson(path.join(os.tmpdir(), `claude-ctx-${sid}.json`));
  const used = metrics && Number(metrics.used_pct);
  if (!(used >= adv)) return null;
  // Once per worker epoch: the flag carries the epoch, so a successor is judged afresh.
  const flag = path.join(STATE, `mission-wall-${sid}-e${marker.epoch}.flag`);
  if (fs.existsSync(flag)) return null;
  try { fs.writeFileSync(flag, String(Date.now())); } catch (e) { return null; }
  return {
    decision: 'block',
    reason:
      `CONTEXT WALL — ${used}% used (>= ${adv}%). This mission continues in a FRESH session; ` +
      `this one ends here (mission ${marker.mission_id}, epoch ${marker.epoch}). Do exactly this: ` +
      '(1) finish ONLY the atomic step in progress and make it durable (commit / save) — start ' +
      `nothing new; (2) end your response with a paragraph that begins \`${NOTE_TAG}\` stating ` +
      'the next exact action and any fact the repository does not record. Do NOT run /compact ' +
      'and do NOT re-issue the run command: the supervisor starts the next worker once this turn ends.',
  };
}

async function run(event) {
  try { return decide(event); } catch (e) { return null; }  // fail-open: never break a tool call
}

module.exports = { run, decide, NOTE_TAG };
