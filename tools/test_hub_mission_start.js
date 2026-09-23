// V-HUBMS-* gates: the SessionStart hub's mission step, through the REAL python CLI.
// Hermetic: GSD_LONG_RUN_STATE_DIR points ledger, mission records AND markers at a temp dir,
// and the hub is required as a module, so none of its other session-start side effects run.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'hubms-'));
process.env.GSD_LONG_RUN_STATE_DIR = TMP;
process.env.GSD_LONG_RUN_SESSIONS_DIR = path.join(TMP, 'sessions');
process.env.GSD_AUTORUN_MARKER_DIR = TMP;  // markers too: never a synthetic marker in the real dir
const hub = require('../hooks/session_start_hub.js');

let pass = 0; let fail = 0;
function check(gate, cond, ev) {
  if (cond) { pass++; console.log(`PASS ${gate} ${ev || ''}`); }
  else { fail++; console.log(`FAIL ${gate} ${ev || ''}`); }
}
function writeMission(id, rec) {
  fs.writeFileSync(path.join(TMP, `gsd-mission-${id}.json`), JSON.stringify(rec));
}
function readMission(id) {
  return JSON.parse(fs.readFileSync(path.join(TMP, `gsd-mission-${id}.json`), 'utf8'));
}
const now = Date.now() / 1000;
const base = { schema_version: 1, mode: 'ralph', cwd: path.resolve(__dirname, '..'),
  resume_command: '/gsd-autonomous', workstream: null, mission_terms: [], max_cycles: null,
  max_hours: null, iterations: 0, failed_launches: 0, note: '', created_at: now,
  updated_at: now, last_progress_at: null, owner: null };

// 1. an ordinary session is not named by any mission -> no python, nothing changes
writeMission('m-a', { ...base, mission_id: 'm-a', state: 'LAUNCHING', epoch: 1,
  pending: { kind: 'worker_start', bg_id: 'abcd1234', deadline: now + 300 } });
check('V-HUBMS-ORDINARY-NOT-NAMED', hub.missionNamesSession('ffff0000-1111') === false);
check('V-HUBMS-ORDINARY-NO-CARD', hub.hookMissionStart('ffff0000-1111', 'startup') === null);
check('V-HUBMS-ORDINARY-UNCHANGED', readMission('m-a').state === 'LAUNCHING');

// 2. the launched worker acks itself through the real CLI
check('V-HUBMS-WORKER-NAMED', hub.missionNamesSession('abcd1234-2222-3333') === true);
const card1 = hub.hookMissionStart('abcd1234-2222-3333', 'startup');
const rec = readMission('m-a');
check('V-HUBMS-WORKER-ACKED', rec.state === 'RUNNING' && rec.owner.session_id === 'abcd1234-2222-3333',
  `${rec.state}`);
check('V-HUBMS-FIRST-EPOCH-NO-CARD', card1 === null);
const marker = path.join(TMP, 'gsd-autorun-abcd1234-2222-3333.json');
check('V-HUBMS-MARKER-IN-REDIRECTED-DIR', fs.existsSync(marker)
  && JSON.parse(fs.readFileSync(marker, 'utf8')).mission_id === 'm-a');

// 3. a successor gets its card as the hook's return value
writeMission('m-b', { ...base, mission_id: 'm-b', state: 'LAUNCHING', epoch: 2,
  note: 'continue at plan 02-03', pending: { kind: 'worker_start', bg_id: 'beef0001', deadline: now + 300 } });
const card2 = hub.hookMissionStart('beef0001-4444', 'startup') || '';
check('V-HUBMS-SUCCESSOR-CARD', card2.startsWith('MISSION CONTINUITY') && card2.includes('plan 02-03'),
  card2.slice(0, 60));

console.log(`HUBMS_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
