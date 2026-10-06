'use strict';
/**
 * session_cards.js -- the SessionStart "cards": the lines a new session cannot work
 * without (rollover successor, mission rehydration, /restart resume, auto-reset work
 * state). Extracted from session_start_hub.js (plan pillar-k-resident-prefix, C0,
 * audit gap 3).
 *
 * WHY A SEPARATE MODULE. Requiring session_start_hub.js arms a hard-exit timer at load
 * (armHardExit, cleared only by the hub's own stdin read): any process that requires the
 * hub for these functions without reading stdin through the hub is killed at 5 s with
 * exit 0 and no stdout. The dispatcher (C1) must run the cards in-process, so they live
 * here, where loading the module does NOTHING: no timers, no stdin, no spawns, no writes.
 *
 * The hub and rollover_autotype.js require this module (the hub re-exports the names its
 * tests use), so the card, the autotype and /kresume keep one definition of "the capsule
 * that is here".
 *
 * Side effects happen only when a function is CALLED: hookRestartResume and
 * hookWorkStateResume consume their one-shot files, hookMissionStart runs gsd_mission.py.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const PP_PATH = path.resolve(__dirname, '..');
const LOG_FILE = path.join(os.tmpdir(), 'pp-session-hub.log');
const STATE_DIR = path.join(HOME, '.claude', 'state');
const MARKER_PATH = path.join(STATE_DIR, 'restart_pending.json');

const FRESHNESS_MINUTES = 5;
const MS_PER_MINUTE = 60 * 1000;
const MARKER_MAX_AGE_MS = FRESHNESS_MINUTES * MS_PER_MINUTE;
const ISO_SECONDS_LEN = 19;  // length of "YYYY-MM-DDTHH:MM:SS"
const UTF8_BOM_CHARCODE = 0xFEFF;

const PYTHON_EXE = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';

// Same log file as the hub, so one session start stays one readable story.
function note(msg, err) {
  // Single source of structured stderr-equivalent log. Never throws.
  try {
    const line = new Date().toISOString() + ' ' + msg
                 + (err ? ' (' + (err.message || err) + ')' : '') + '\n';
    fs.appendFileSync(LOG_FILE, line);
  } catch (writeErr) {
    void writeErr;
  }
}

function readJsonNoBom(fp) {
  let raw = fs.readFileSync(fp, 'utf8');
  if (raw && raw.charCodeAt(0) === UTF8_BOM_CHARCODE) {
    raw = raw.slice(1);
  }
  return JSON.parse(raw);
}

// ---------------------------------------------------------------------------
// /restart resume (one-shot: consumes restart_pending.json)
// ---------------------------------------------------------------------------
function hookRestartResume(cwd) {
  if (!fs.existsSync(MARKER_PATH)) {
    return null;
  }
  try {
    const stat = fs.statSync(MARKER_PATH);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > MARKER_MAX_AGE_MS) {
      try {
        fs.unlinkSync(MARKER_PATH);
      } catch (delErr) {
        note('stale marker unlink failed', delErr);
      }
      return null;
    }

    const ctx = readJsonNoBom(MARKER_PATH);

    const markerCwd = (ctx.cwd || '').toLowerCase();
    const sessCwd = (cwd || '').toLowerCase();
    if (markerCwd && sessCwd && markerCwd !== sessCwd) {
      // Different repo -- leave marker for the right session.
      return null;
    }

    try {
      fs.unlinkSync(MARKER_PATH);
    } catch (delErr) {
      note('marker unlink failed', delErr);
    }

    const branch = ctx.branch || 'unknown';
    const ts = (ctx.timestamp || '').slice(0, ISO_SECONDS_LEN);
    const sid = ctx.session_id || '';
    const sessNote = ctx.session_note
      || 'Session restarted via /restart command.';

    let line = '[/restart resume] Continuing from a prior session in this '
             + 'working directory. Branch: ' + branch + '. Restarted at: '
             + (ts || '?') + '.';
    if (sid) {
      line += ' Prior session id: ' + sid + '.';
    }
    line += ' ' + sessNote;
    return line;
  } catch (err) {
    note('restart_resume failed', err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// work_state resume (Auto-Reset Orchestrator M5, 2026-06-04)
//   After a /compact or /kclear auto-reset, the orchestrator (M3) saved a
//   structured work_state (task + last_commit + last_file + pending). This
//   injects it into the NEW session so it continues exactly where it left off.
//   Fires on EVERY SessionStart, matches by cwd (the new session has a fresh
//   session_id), is freshness-bounded (< 6h), and is single-shot (consumes the
//   file so it never re-injects). Fail-open: never breaks SessionStart.
// ---------------------------------------------------------------------------
const WORK_STATE_MAX_AGE_MS = 6 * 60 * MS_PER_MINUTE;  // 6h freshness window
const WORK_STATE_PENDING_SHOWN = 5;

function hookWorkStateResume(cwd) {
  try {
    const cwdL = (cwd || '').toLowerCase();
    if (!cwdL) {
      return null;
    }
    let files;
    try {
      files = fs.readdirSync(STATE_DIR)
        .filter(f => f.startsWith('work_state_') && f.endsWith('.json'));
    } catch (readDirErr) {
      return null;  // no state dir yet -- nothing to resume
    }
    let best = null;
    let bestMtime = -1;
    for (const f of files) {
      const fp = path.join(STATE_DIR, f);
      let st;
      try {
        st = fs.statSync(fp);
      } catch (statErr) {
        continue;
      }
      if (Date.now() - st.mtimeMs > WORK_STATE_MAX_AGE_MS) {
        continue;  // stale reset context -- ignore
      }
      let rec;
      try {
        rec = readJsonNoBom(fp);
      } catch (parseErr) {
        continue;
      }
      if ((rec.cwd || '').toLowerCase() !== cwdL) {
        continue;  // different repo -- leave for the right session
      }
      if (st.mtimeMs > bestMtime) {
        best = { rec, fp };
        bestMtime = st.mtimeMs;
      }
    }
    if (!best) {
      return null;
    }
    const r = best.rec;
    const pending = (Array.isArray(r.pending) && r.pending.length)
      ? r.pending.slice(0, WORK_STATE_PENDING_SHOWN).join('; ')
      : '(none)';
    const line = '[auto-reset resume] Continuing from a context reset. '
      + 'Task: ' + (r.task || '(unknown)') + '. '
      + 'Last commit: ' + (r.last_commit || '(none)') + '. '
      + 'Last file: ' + (r.last_file || '(none)') + '. '
      + 'Pending: ' + pending + '.';
    // Single-shot: consume so it never re-injects on a later SessionStart.
    try {
      fs.unlinkSync(best.fp);
    } catch (delErr) {
      note('work_state unlink failed', delErr);
    }
    return line;
  } catch (err) {
    note('work_state resume failed', err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Active rollover (P3), successor side. After `/clear` the predecessor's context is gone
// and the ONLY thing carrying the thread is the capsule it sealed. This does not decide
// which capsule, and it does not claim one: `/kresume` is the single authority for both,
// and it refuses cleanly when there is nothing to adopt. All this does is notice that a
// capsule for THIS repo is lying unretired and tell the successor to go and claim it --
// silence here is a session that quietly starts from nothing.
// ---------------------------------------------------------------------------
const ROLLOVER_CAPSULE_MAX_AGE_MS = 24 * 60 * 60 * 1000;

// Same identity rule as rollover.py capsule_is_here(), which `/kresume` uses to claim: the
// card and the autotype must see exactly the capsules the claim will. A capsule belongs to
// this session's directory when that directory is its session_cwd (the predecessor's own
// directory, recorded since 2026-09-29), its shell cwd, or its repo root. The exact cwd
// compare this replaces missed both a seal from a subdirectory (ea5c9025) and a seal after
// a `cd` into another repo (357823a8): no card, no autotype, capsule claimed by hand.
// Never "any ancestor": a nested repo's capsule must not surface in its parent.
function rolloverPathKey(p) {
  const s = String(p || '').trim();
  if (!s) return '';
  const n = path.normalize(s).replace(/[\\/]+$/, '');
  return process.platform === 'win32' ? n.toLowerCase() : n;
}

function capsuleIsHere(rec, cwd) {
  const here = rolloverPathKey(cwd);
  if (!here || !rec) return false;
  const repo = (rec.repo && typeof rec.repo === 'object') ? rec.repo : {};
  return [rec.session_cwd, rec.cwd, repo.root].some(k => rolloverPathKey(k) === here);
}

// The newest unretired capsule sealed for this cwd, or null. Newest, because that is the
// one `/kresume` claims; the card only needs one to exist, the focus needs the right one.
function findRolloverCapsule(cwd, source) {
  try {
    if (source !== 'clear') {
      return null;   // a fresh start or a compaction is not a rollover crossing
    }
    const sw = String(process.env.CPP_ROLLOVER_ACTIVE || '').trim().toLowerCase();
    if (sw === '0' || sw === 'off' || sw === 'false') {
      return null;
    }
    if (!rolloverPathKey(cwd)) {
      return null;
    }
    const dir = path.join(STATE_DIR, 'rollover', 'capsules');
    let files;
    try {
      files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
    } catch (readDirErr) {
      return null;   // nothing has ever been sealed on this host
    }
    let best = null;
    let bestMtime = -1;
    for (const f of files) {
      const fp = path.join(dir, f);
      try {
        const st = fs.statSync(fp);
        if (Date.now() - st.mtimeMs > ROLLOVER_CAPSULE_MAX_AGE_MS || st.mtimeMs <= bestMtime) {
          continue;
        }
        if (fs.existsSync(fp.replace(/\.json$/, '.certified'))) {
          continue;  // already adopted and retired by a successor
        }
        const rec = readJsonNoBom(fp);
        if (!capsuleIsHere(rec, cwd)) {
          continue;  // another repo's crossing -- leave it for its own successor
        }
        best = rec;
        bestMtime = st.mtimeMs;
      } catch (entryErr) {
        continue;
      }
    }
    return best;
  } catch (err) {
    return null;   // fail-open: a card step that throws costs the successor its whole start
  }
}

function hookRolloverResume(cwd, source) {
  if (!findRolloverCapsule(cwd, source)) {
    return null;
  }
  return 'ROLLOVER — the session that was working here crossed the context wall and '
    + 'sealed a capsule before clearing. Run `/kresume` NOW, before anything else: it '
    + 'claims the capsule (one successor only), refreshes the repo facts, and prints '
    + 'the goal, the open obligations and a short exam. Do not reconstruct the task '
    + 'from this message or from the repo — the capsule is the record.';
}

// The first open obligation, as ONE clean line of at most 200 chars, or ''. Owner
// 2026-09-29: type `/kresume focus on <it>` like /compact, so the successor's first
// prompt names the work. It is typed into a terminal, so a newline would submit early
// and put the rest in a second prompt: control characters become spaces. The daemon
// re-checks the same shape and refuses anything else; this is not the only guard.
const KRESUME_FOCUS_MAX = 200;

function rolloverFocus(cwd, source) {
  try {
    const rec = findRolloverCapsule(cwd, source);
    const first = rec && Array.isArray(rec.obligations) ? rec.obligations[0] : null;
    const text = (first && typeof first === 'object') ? first.title : first;
    if (typeof text !== 'string') {
      return '';
    }
    return text.replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]+/g, ' ')
      .replace(/\s+/g, ' ').trim().slice(0, KRESUME_FOCUS_MAX).trim();
  } catch (err) {
    return '';   // no focus is a bare /kresume, which still continues from the capsule
  }
}

// ---------------------------------------------------------------------------
// Mission continuity (spec vault/specs/mission-continuity.md). A `claude --bg` worker
// launched by tools/gsd_mission.py acknowledges itself HERE -- its own SessionStart is the
// first event only it can produce, which is what moves the mission from LAUNCHING to
// RUNNING -- and a successor receives its rehydration card as additionalContext.
// Every other session pays one directory read: python runs only when a mission record
// names this session (owner, or the pending launch whose host-printed id prefixes it).
// ---------------------------------------------------------------------------
const GSD_MISSION_PY = path.join(PP_PATH, 'tools', 'gsd_mission.py');
// A card step killed at its deadline loses EVERY line it would have emitted, not just this
// one. The ack is written before the git reads, so a timeout here costs the card only --
// the successor still reconciles from GSD. Callers on a tighter budget (the dispatcher's
// in-process cards, audit gap 2) pass their own timeoutMs. The env override exists ONLY so
// a logic test on a starved host does not measure process-spawn latency (measured: 5 s
// ETIMEDOUT with a 243 ms import at 2.7 GB free). Production default stays at 5000.
const MISSION_START_TIMEOUT_MS = Number(process.env.CPP_MISSION_START_TIMEOUT_MS) || 5000;

function missionNamesSession(sessionId) {
  if (!sessionId) return false;
  const dir = process.env.GSD_LONG_RUN_STATE_DIR || STATE_DIR;
  let names;
  try {
    names = fs.readdirSync(dir).filter((n) => n.startsWith('gsd-mission-') && n.endsWith('.json'));
  } catch (err) {
    return false;
  }
  for (const n of names) {
    try {
      const rec = JSON.parse(fs.readFileSync(path.join(dir, n), 'utf8'));
      const owner = rec.owner || {};
      const pend = rec.pending || {};
      if (owner.session_id === sessionId) return true;
      if (rec.state === 'LAUNCHING' && pend.bg_id && sessionId.startsWith(pend.bg_id)) return true;
    } catch (err) {
      // A record being rewritten reads as malformed for an instant; python re-reads it.
      continue;
    }
  }
  return false;
}

function hookMissionStart(sessionId, source, timeoutMs) {
  try {
    if (!missionNamesSession(sessionId) || !fs.existsSync(GSD_MISSION_PY)) return null;
    const out = require('child_process').execFileSync(
      PYTHON_EXE, [GSD_MISSION_PY, 'session-start', '--session', sessionId, '--source', source || ''],
      { encoding: 'utf8', timeout: timeoutMs || MISSION_START_TIMEOUT_MS, windowsHide: true,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }) });
    const card = (out || '').trim();
    note('mission start: ' + (card ? 'card ' + card.length + ' chars' : 'acked, no card'));
    return card || null;
  } catch (err) {
    note('mission start failed (fail-open; the start deadline will surface it)', err);
    return null;
  }
}

module.exports = {
  HOME, PP_PATH, LOG_FILE, STATE_DIR, MS_PER_MINUTE, UTF8_BOM_CHARCODE, PYTHON_EXE,
  note, hookRestartResume, hookWorkStateResume,
  rolloverPathKey, capsuleIsHere, findRolloverCapsule, hookRolloverResume, rolloverFocus,
  missionNamesSession, hookMissionStart,
};
