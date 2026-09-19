#!/usr/bin/env node
'use strict';
/**
 * gsd_stop_continuation.js -- bounded autonomous TURN continuation (Stop).
 *
 * WHAT THIS IS FOR, and what it deliberately is not.
 *
 * Measured 2026-09-19 in KobiiCraft Core Files (session de7f3c91): a GSD
 * autonomous mission ran a STATE.md blocker read, the harness backgrounded it
 * at its 120 s timeout, and the job COMPLETED at 12:41:58 -- 3,095 bytes, exit
 * code 0, written to tasks/b4haxctvm.output. Two <task-notification> rows were
 * ENQUEUED. Then the turn ended, and nothing re-invoked the model. The queue
 * does not pump itself: those notifications were delivered 7 h 08 m later, when
 * the Owner came back and typed. The mission sat still with a finished answer
 * on disk saying "no blockers -- proceed".
 *
 * So the gap is not context compaction and it is not the background job. It is
 * that NOBODY OWNS TURN CONTINUATION. This hook owns exactly that, and nothing
 * else:
 *
 *   - it does NOT compact, and does not ask anyone to compact;
 *   - it does NOT re-plan -- the next action comes from GSD's own durable
 *     state, never from the model being asked what it feels like doing;
 *   - it does NOT type, focus a window, or route to a terminal.
 *
 * It answers one question at turn end: "this mission is armed and unfinished,
 * and something changed that it has not acted on yet -- say so." Claude Code
 * re-invokes the model on a Stop `decision: block`, in the same session, with
 * the same cwd and transcript. `closer-guard.js` has proven that primitive in
 * production on this host: 867 runs / 385 blocks as of this writing.
 *
 * WHY A SEPARATE STATE FILE FROM closer-guard.
 * The plan said to reuse closer-guard's store. That is wrong and this is the
 * correction: closer-guard's `blocked` flag drives ITS OWN "never block the
 * same session twice in a row" suppression. Sharing one record would let a
 * continuation block satisfy closer-guard's suppression (silently disarming a
 * dead-screen guard) and let a closer-guard block satisfy this one's causal
 * delta rule. Two writers, one file, two incompatible meanings. Separate
 * files; this hook READS closer-guard's state, read-only, purely to avoid
 * ping-ponging with it.
 *
 * ANTI-LOOP (the thing that makes a blocking Stop hook safe):
 * A SECOND BLOCK REQUIRES A CAUSAL DELTA. The fingerprint is built from
 * durable mission facts -- phase, plans on disk, STATE.md identity, and the
 * set of background task outputs. If nothing moved since the last block, this
 * hook does NOT block; it classifies the run STALLED and lets the turn end.
 * A no-delta block is precisely the "model finishes -> Stop says continue ->
 * model says still waiting -> forever" failure, and the streak ceiling is the
 * backstop for the case where the fingerprint moves for an uninteresting
 * reason.
 *
 * FAIL-OPEN, ABSOLUTELY. Every unexpected condition allows the turn to end.
 * A continuation hook that can wedge a session is worse than no continuation
 * hook, because the failure it creates is the failure it exists to prevent.
 *
 * NEVER SPAWNS A SUBPROCESS. This runs on every turn end in the estate, so it
 * is filesystem stats and small JSON reads only -- no git, no gsd-tools, no
 * python. The measured Stop-chain already costs ~54.9 s per turn end on this
 * host; this must not add to that meaningfully.
 *
 * Kill switch: CPP_GSD_STOP_CONTINUATION=off
 * Diagnostics: CPP_GSD_CONT_DEBUG=1 writes one attributable line to stderr.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const STATE_DIR = path.join(HOME, '.claude', 'state');
const LOG_DIR = path.join(HOME, '.claude', 'logs');
const STATE_FILE = path.join(LOG_DIR, 'gsd-continuation-state.json');
const HEARTBEAT = path.join(LOG_DIR, 'gsd-continuation-heartbeat.json');
const CLOSER_STATE = path.join(LOG_DIR, 'closer-guard-state.json');

// Budget defaults. The marker may override both (write_marker already carries
// max_cycles / max_hours, schema_version 2), so these are the values used when
// a marker leaves them null -- not a second source of truth.
const DEFAULT_MAX_CYCLES = 40;
const DEFAULT_MAX_HOURS = 12;
// Consecutive blocks allowed even while the fingerprint keeps moving. The
// delta rule is the primary bound; this catches a fingerprint that churns for
// an uninteresting reason (a log file in the phase dir, say).
const MAX_STREAK = 6;
// Below this the host cannot do useful work and re-invoking the model just
// deepens the hole. Measured repeatedly in this estate: under ~5% free,
// timeouts and "hangs" are the host, not the code.
const FLOOR_MB = 900;

function readJson(p) {
  try {
    const raw = fs.readFileSync(p, 'utf8').replace(/^﻿/, '');
    const v = JSON.parse(raw);
    return (v && typeof v === 'object') ? v : null;
  } catch (err) {
    return null;   // absent/unreadable/malformed are all "no signal" here
  }
}

function writeJsonBestEffort(p, obj) {
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    const tmp = p + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(obj), 'utf8');
    fs.renameSync(tmp, p);
  } catch (err) {
    // Accounting only. Losing a state write costs one extra continuation at
    // worst; throwing here would break the turn, which is strictly worse.
  }
}

/**
 * Heartbeat on EVERY judgement, not only on blocks.
 *
 * rules/guard-event-reachability.md: "a guard that never ran and one that ran
 * and passed are the same observable". This estate has already lost days to
 * that twice. Build the counter before you need it -- after the incident the
 * evidence is gone.
 */
function beat(verdict, sid) {
  try {
    const hb = readJson(HEARTBEAT) || { runs: 0, blocks: 0 };
    hb.runs = (hb.runs || 0) + 1;
    if (verdict === 'block') hb.blocks = (hb.blocks || 0) + 1;
    hb.lastRunIso = new Date().toISOString();
    hb.lastVerdict = verdict;
    hb.lastSessionId = sid || null;
    if (verdict === 'block') hb.lastBlockIso = hb.lastRunIso;
    writeJsonBestEffort(HEARTBEAT, hb);
  } catch (err) {
    // A diagnostic that can break the dispatcher is worse than no diagnostic.
  }
}

function statOf(p) {
  try {
    const st = fs.statSync(p);
    return `${st.size}:${Math.floor(st.mtimeMs)}`;
  } catch (err) {
    return 'x';    // absent is a legitimate, stable fingerprint term
  }
}

function listDir(p) {
  try {
    return fs.readdirSync(p).sort();
  } catch (err) {
    return [];     // absent dir contributes nothing rather than throwing
  }
}

/**
 * Durable mission facts, as one short string.
 *
 * Deliberately NOT a hash of the universe (plan §17). Each term answers "has
 * the mission's world moved in a way the model could act on?":
 *   phase / cycles   - GSD advanced, or a continuation was already spent
 *   STATE.md         - the authoritative blocker + status document
 *   plan files       - plans appearing, or a VERIFICATION landing
 *   task outputs     - a background job finished; THIS is the term that turns
 *                      the measured incident into a single block
 */
function fingerprint(marker, cwd, tasksDir) {
  const parts = [];
  parts.push('ph=' + String(marker.phase));
  parts.push('cy=' + String(marker.cycles || 0));

  const planning = path.join(cwd, '.planning');
  parts.push('state=' + statOf(path.join(planning, 'STATE.md')));
  parts.push('road=' + statOf(path.join(planning, 'ROADMAP.md')));

  const phasesDir = path.join(planning, 'phases');
  for (const d of listDir(phasesDir)) {
    if (marker.phase != null && !d.startsWith(String(marker.phase))) continue;
    const full = path.join(phasesDir, d);
    for (const f of listDir(full)) {
      parts.push(`${d}/${f}=${statOf(path.join(full, f))}`);
    }
  }

  const tasks = [];
  for (const f of listDir(tasksDir)) {
    if (!f.endsWith('.output')) continue;
    tasks.push(`${f}=${statOf(path.join(tasksDir, f))}`);
  }
  parts.push('tasks[' + tasks.join(',') + ']');

  return parts.join('|');
}

/**
 * The single most actionable pointer available from durable state.
 *
 * This is a LOOKUP, not a plan. §15/§40: Stop continuation must never become a
 * second planner, so the strongest thing it may do is name the artifact the
 * mission has not consumed yet and point at GSD's own state for the rest.
 */
function nextAction(marker, cwd, tasksDir) {
  let newest = null;
  for (const f of listDir(tasksDir)) {
    if (!f.endsWith('.output')) continue;
    const full = path.join(tasksDir, f);
    try {
      const st = fs.statSync(full);
      if (st.size > 0 && (!newest || st.mtimeMs > newest.mtimeMs)) {
        newest = { name: f, full, size: st.size, mtimeMs: st.mtimeMs };
      }
    } catch (err) {
      continue;    // a task file that vanished mid-scan is simply not newest
    }
  }
  if (newest) {
    return 'A background task finished and its result has not been read: '
      + `${newest.name} (${newest.size} bytes). Read it now with the Read tool `
      + `at ${newest.full}, then act on what it says.`;
  }
  const phase = marker.phase == null ? 'the current phase' : `phase ${marker.phase}`;
  return `Continue ${phase}. The authoritative next action is in `
    + `${path.join(cwd, '.planning', 'STATE.md')} and the phase's plan files; `
    + 'read them rather than re-planning.';
}

function run(data) {
  const sid = data && data.session_id;
  if (!sid) return { continue: true };

  if (String(process.env.CPP_GSD_STOP_CONTINUATION || '').toLowerCase() === 'off') {
    return { continue: true };
  }
  // Check the EVENT before the logic. This hook's contract is Stop only; a
  // `decision: block` is meaningless on most other events and rejected by the
  // host on some. An absent name is treated as Stop because that is how the
  // dispatcher invokes this chain.
  const ev = data.hook_event_name;
  if (typeof ev === 'string' && ev && ev !== 'Stop') return { continue: true };

  const marker = readJson(path.join(STATE_DIR, `gsd-autorun-${sid}.json`));
  if (!marker) return { continue: true };          // not an autonomous mission
  if (marker.status === 'complete' || marker.terminal === true) {
    return { continue: true };                      // mission terminal predicate
  }

  // --- OPT-IN, and deliberately so (plan §23/§69) -------------------------
  // NATIVE_CONTINUITY is the new path; LEGACY_EXPLICIT remains the default
  // until an A/B says otherwise. Without this gate, registering the hook
  // would change behaviour tonight for every marker already on disk -- there
  // were 11 when it landed, three still inside their budget, one of them a
  // live mission. A new default is a decision earned by evidence, not a side
  // effect of shipping the code that might justify it.
  const forced = process.env.CPP_GSD_CONT_FORCE === '1';
  if (!forced && marker.continuation !== 'stop-block') {
    return { continue: true };
  }

  // --- budget -------------------------------------------------------------
  const maxCycles = Number.isFinite(marker.max_cycles) && marker.max_cycles > 0
    ? marker.max_cycles : DEFAULT_MAX_CYCLES;
  if ((Number(marker.cycles) || 0) >= maxCycles) return { continue: true };

  const maxHours = Number.isFinite(marker.max_hours) && marker.max_hours > 0
    ? marker.max_hours : DEFAULT_MAX_HOURS;
  const armedAt = Date.parse(marker.armed_at || marker.ts || '');
  if (Number.isFinite(armedAt)
      && (Date.now() - armedAt) > maxHours * 3600 * 1000) {
    return { continue: true };
  }

  // --- resource admission -------------------------------------------------
  // Re-invoking a model on a host with no headroom produces the very stall
  // this hook exists to prevent, so a starved host ends the turn honestly.
  let freeMB = Infinity;
  try {
    freeMB = Math.round(os.freemem() / 1048576);
  } catch (err) {
    freeMB = Infinity;   // unmeasurable headroom must not silently block work
  }
  if (freeMB < FLOOR_MB) return { continue: true };

  // --- do not ping-pong with closer-guard ---------------------------------
  const closer = readJson(CLOSER_STATE);
  if (closer && closer[sid] && closer[sid].blocked === true) {
    return { continue: true };
  }

  const cwd = (typeof marker.cwd === 'string' && marker.cwd) ? marker.cwd
    : (data.cwd || process.cwd());
  const tasksDir = path.join(
    os.tmpdir(), 'claude',
    path.basename(path.dirname(String(data.transcript_path || ''))) || '_',
    sid, 'tasks');

  const fp = fingerprint(marker, cwd, tasksDir);
  const state = readJson(STATE_FILE) || {};
  const prev = state[sid];

  // --- CAUSAL DELTA: the rule that makes a second block legitimate ---------
  if (prev && prev.fingerprint === fp) {
    state[sid] = {
      blocked: false, fingerprint: fp, streak: 0,
      classification: 'STALLED', ts: Date.now(),
    };
    writeJsonBestEffort(STATE_FILE, state);
    return { continue: true };
  }

  const streak = (prev && prev.streak) ? prev.streak : 0;
  if (streak >= MAX_STREAK) {
    state[sid] = {
      blocked: false, fingerprint: fp, streak: 0,
      classification: 'STREAK_CEILING', ts: Date.now(),
    };
    writeJsonBestEffort(STATE_FILE, state);
    return { continue: true };
  }

  state[sid] = {
    blocked: true, fingerprint: fp, streak: streak + 1,
    classification: 'CONTINUE', ts: Date.now(),
  };
  writeJsonBestEffort(STATE_FILE, state);

  // Minimum sufficient context (§41): mission status, ONE authoritative next
  // action, and the pointer. Everything else the model already has, or can
  // read. A large injected prompt on every continuation is a context tax paid
  // once per turn end for the life of the run.
  return {
    decision: 'block',
    reason: 'GSD AUTONOMOUS RUN STILL ARMED -- the mission is not finished and '
      + 'this turn ended without completing it.\n\n'
      + nextAction(marker, cwd, tasksDir)
      + '\n\nDo not re-plan the roadmap and do not ask the Owner what to do. '
      + 'If the mission is genuinely complete, or it needs an irreducible Owner '
      + 'decision, say so plainly and it will not be resumed again.',
  };
}

module.exports = { run, fingerprint, nextAction, MAX_STREAK, FLOOR_MB };

if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try {
      process.stdout.write(JSON.stringify({ continue: true }));
    } catch (err) {
      // stdout already gone; the host treats no output as allow, which is the
      // same verdict this branch wanted.
    }
    process.exit(0);
  }, 5000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => { input += c; });
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    let data = {};
    try {
      data = JSON.parse(input || '{}');
    } catch (err) {
      data = {};   // fail-open: an unparseable payload never blocks a turn
    }
    let out;
    try {
      out = run(data);
    } catch (err) {
      out = { continue: true };                     // fail-open ABSOLUTE
    }
    beat(out && out.decision === 'block' ? 'block' : 'allow', data.session_id);
    if (process.env.CPP_GSD_CONT_DEBUG === '1') {
      try {
        process.stderr.write('[gsd-stop-continuation] sid='
          + String(data.session_id).slice(0, 8)
          + ' verdict=' + (out.decision || 'allow') + '\n');
      } catch (err) {
        // A debug line that cannot be written is not worth a failed turn.
      }
    }
    try {
      console.log(JSON.stringify(out));
    } catch (err) {
      console.log(JSON.stringify({ continue: true }));
    }
    process.exit(0);
  });
}
