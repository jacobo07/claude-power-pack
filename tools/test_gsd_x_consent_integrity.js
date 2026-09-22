// V-GSDXCONSENT-* -- characterization of an UPSTREAM consent-integrity defect.
//
// gsd-core's capability-trust.cjs computes, at :635,
//   hasExecutable = hooks || commandModules || mcpServers || reviewerLanes
// and `gates` is absent. The whole file contains no occurrence of "gates" or
// "command-exit-zero". So a manifest whose only surface is a
// gates[].check.predicate of kind command-exit-zero -- which
// gate-predicate-evaluator.cjs runs through execTool('sh', ['-c', ...]) -- is
// disclosed at install as "This capability ships no executable surfaces
// (declarative only)." Our own cpp-gsd-x-mission manifest printed exactly that
// on `capability update` (2026-09-22).
//
// It is worse than a wording defect. The same `hasExecutable` drives
// `executableSetChanged` and the auto-update re-consent trigger (the comment at
// :633-634 says so), so a gate's command can be changed after consent without
// re-consent being asked for.
//
// This is a CHARACTERIZATION: it asserts today's defective behaviour so the
// defect cannot become invisible. When upstream fixes it, V-GSDXCONSENT-DEFECT
// goes red with a message saying so -- invert it deliberately then; do not
// delete it. Upstream-owned; nothing here patches gsd-core.
//
// Positive control: a synthetic manifest carrying a surface class the function
// DOES count must come back hasExecutable:true, or a false from our manifest
// would just be a function that always says false.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const TRUST = path.join(os.homedir(), '.claude', 'gsd-core', 'bin', 'lib', 'capability-trust.cjs');
const CAP_DIR = path.resolve(__dirname, '..', 'capabilities', 'cpp-gsd-x-mission');
const MANIFEST = path.join(CAP_DIR, 'capability.json');

let pass = 0, fail = 0;
const ok = (g, e) => { pass++; console.log(`  PASS ${g}: ${e}`); };
const bad = (g, e) => { fail++; console.log(`  FAIL ${g}: ${e}`); };
function harness(why) {
  console.log(`\nHARNESS-FAILED: ${why}`);
  console.log('GSDX_CONSENT_PASS=0/0  threshold=HARNESS');
  process.exit(2);
}

if (!fs.existsSync(TRUST)) harness(`capability-trust.cjs not found at ${TRUST}`);
if (!fs.existsSync(MANIFEST)) harness(`manifest not found at ${MANIFEST}`);

let trust;
try { trust = require(TRUST); } catch (e) { harness(`cannot load capability-trust.cjs: ${e.message}`); }
if (typeof trust.discloseExecutableSurfaces !== 'function') {
  harness('discloseExecutableSurfaces is no longer exported; the seam this pins has moved');
}

const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8').replace(/^﻿/, ''));

// --- precondition: the manifest really does reach a shell -----------------
const execGates = (manifest.gates || []).filter(g =>
  g && g.check && g.check.predicate && g.check.predicate.kind === 'command-exit-zero'
  && typeof g.check.predicate.command === 'string' && g.check.predicate.command.length > 0);
if (execGates.length === 0) {
  harness('manifest no longer declares a command-exit-zero gate; this characterization has no subject');
}
ok('V-GSDXCONSENT-SUBJECT-EXECUTES',
   `${execGates.length} gate(s) of kind command-exit-zero, e.g. ${JSON.stringify(execGates[0].check.predicate.command).slice(0, 80)}...`);

// --- positive control: the function can say true --------------------------
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gsdx_consent_'));
try {
  fs.writeFileSync(path.join(tmp, 'router.cjs'), 'module.exports = {};\n');
  const control = {
    id: 'consent-control', role: 'feature', version: '0.0.0',
    commands: [{ family: 'consentctl', module: 'router.cjs', router: 'route' }],
  };
  const c = trust.discloseExecutableSurfaces(control, tmp);
  if (c && c.hasExecutable === true) {
    ok('V-GSDXCONSENT-CONTROL-CAN-SAY-TRUE',
       `a manifest with a command module -> hasExecutable true (commandModules=${c.commandModules.length})`);
  } else {
    harness(`positive control came back hasExecutable=${c && c.hasExecutable}; the function may be ` +
            `always-false, so a false below would mean nothing`);
  }
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

// --- the characterization ---------------------------------------------------
const d = trust.discloseExecutableSurfaces(manifest, CAP_DIR);
const surfaces = `hooks=${d.hooks.length} commands=${d.commandModules.length} ` +
                 `mcp=${d.mcpServers.length} lanes=${d.reviewerLanes.length}`;
if (d.hasExecutable === false) {
  ok('V-GSDXCONSENT-DEFECT',
     `DEFECT PRESENT (characterized): a shell-reaching gate is disclosed as non-executable ` +
     `(hasExecutable=false; ${surfaces}). Install prints "declarative only", and re-consent ` +
     `is not triggered when the gate command changes.`);
} else {
  bad('V-GSDXCONSENT-DEFECT',
      `hasExecutable is now TRUE (${surfaces}). Upstream appears to have fixed the gates ` +
      `omission. Invert this assertion deliberately and record the gsd-core version that fixed it.`);
}

console.log(`\nGSDX_CONSENT_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
