// V-MWALL-*: the mid-turn mission wall (hooks/mission_wall.js). Hermetic: marker dir and the
// metrics dir are temp; every refusal has a control where the wall fires.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'mwall-'));
process.env.GSD_AUTORUN_MARKER_DIR = TMP;
const wall = require('../hooks/mission_wall.js');
let pass = 0; let fail = 0;
const check = (g, c, ev) => { if (c) { pass++; console.log(`PASS ${g} ${ev || ''}`); } else { fail++; console.log(`FAIL ${g} ${ev || ''}`); } };
const sid = `mwall-${process.pid}`;
const metrics = path.join(os.tmpdir(), `claude-ctx-${sid}.json`);
const marker = (m) => fs.writeFileSync(path.join(TMP, `gsd-autorun-${sid}.json`), JSON.stringify(m));
const used = (pct) => fs.writeFileSync(metrics, JSON.stringify({ session_id: sid, used_pct: pct }));
const W = { snapshot: 35, advisory: 40, rearm: 30 };

check('V-MWALL-NO-MARKER-SILENT', wall.decide({ session_id: sid }) === null);
marker({ session_id: sid, resume_command: '/x', wall: W });            // legacy v2 (no mission)
used(55);
check('V-MWALL-LEGACY-RUN-SILENT', wall.decide({ session_id: sid }) === null, 'the watchdog owns v2 runs');
marker({ session_id: sid, resume_command: '/x', wall: W, mission_id: 'm-t', epoch: 1 });
used(39);
check('V-MWALL-BELOW-WALL-SILENT', wall.decide({ session_id: sid }) === null);
used(41);
const out = wall.decide({ session_id: sid });
check('V-MWALL-FIRES-MID-TURN', out && out.decision === 'block' && out.reason.includes(wall.NOTE_TAG)
  && out.reason.includes('m-t'), out && out.reason.slice(0, 60));
check('V-MWALL-ONCE-PER-EPOCH', wall.decide({ session_id: sid }) === null);
marker({ session_id: sid, resume_command: '/x', wall: W, mission_id: 'm-t', epoch: 2 });
check('V-MWALL-NEW-EPOCH-JUDGED-AFRESH', (wall.decide({ session_id: sid }) || {}).decision === 'block');
check('V-MWALL-BAD-SID-SILENT', wall.decide({ session_id: '../x' }) === null);
try { fs.unlinkSync(metrics); } catch (e) { /* ignore */ }
console.log(`MWALL_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
