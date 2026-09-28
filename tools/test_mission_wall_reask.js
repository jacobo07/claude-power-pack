// V-MWALL-REASK-*: the wall re-asks a worker that keeps working past it (hooks/mission_wall.js).
// Measured 2026-09-28 (m-916e905e23d4): asked once at 31 %, the worker worked on to 49 % in the same
// turn. Hermetic: marker dir and metrics are temp. Every "silent" case has a control that fires.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'mwall-reask-'));
process.env.GSD_AUTORUN_MARKER_DIR = TMP;
const wall = require('../hooks/mission_wall.js');
let pass = 0; let fail = 0;
const check = (g, c, ev) => { if (c) { pass++; console.log(`PASS ${g} ${ev || ''}`); } else { fail++; console.log(`FAIL ${g} ${ev || ''}`); } };
const sid = `mwreask-${process.pid}`;
const metrics = path.join(os.tmpdir(), `claude-ctx-${sid}.json`);
const W = { snapshot: 35, advisory: 40, rearm: 30 };
fs.writeFileSync(path.join(TMP, `gsd-autorun-${sid}.json`),
  JSON.stringify({ session_id: sid, resume_command: '/x', wall: W, mission_id: 'm-r', epoch: 1 }));
const used = (pct) => fs.writeFileSync(metrics, JSON.stringify({ session_id: sid, used_pct: pct }));
const flag = path.join(TMP, `mission-wall-${sid}-e1.flag`);
const readFlag = () => JSON.parse(fs.readFileSync(flag, 'utf8'));

used(41);
const first = wall.decide({ session_id: sid });
const f1 = readFlag();
check('V-MWALL-REASK-FIRST-NOTICE', first && first.decision === 'block' && f1.n === 1 && f1.pct === 41,
  JSON.stringify(f1));
check('V-MWALL-REASK-NAMES-ENFORCEMENT', first && /supervisor STOPS this session/.test(first.reason)
  && /\d\d:\d\dZ/.test(first.reason));
used(43);
check('V-MWALL-REASK-SILENT-WITHIN-STEP', wall.decide({ session_id: sid }) === null);
used(44);
const second = wall.decide({ session_id: sid });
const f2 = readFlag();
check('V-MWALL-REASK-SECOND-NOTICE', second && second.decision === 'block' && /NOTICE 2/.test(second.reason)
  && f2.n === 2 && f2.pct === 44, second && second.reason.slice(0, 70));
check('V-MWALL-REASK-CLOCK-IS-FIRST-NOTICE', f2.asked_at === f1.asked_at);

// A flag written before this change holds a bare timestamp: still read, re-asked from the advisory.
fs.writeFileSync(flag, String(Date.now() - 60000));
used(42);
check('V-MWALL-REASK-LEGACY-FLAG-SILENT-WITHIN-STEP', wall.decide({ session_id: sid }) === null);
used(43);
const legacy = wall.decide({ session_id: sid });
check('V-MWALL-REASK-LEGACY-FLAG-REASKS', legacy && legacy.decision === 'block' && readFlag().n === 2);

try { fs.unlinkSync(metrics); } catch (e) { /* temp file */ }
console.log(`MWALL_REASK_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
