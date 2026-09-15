#!/usr/bin/env node
'use strict';
// V-SCRATCH-* — the PreToolUse Edit chain's scratchpad fast path.
//
// WHY THIS FILE EXISTS, and why the assertions look the way they do.
//
// The filter's failure mode is SILENT AND FAIL-OPEN: `isScratchTarget` returning
// false runs the full eleven-member chain, which is precisely what a WORKING
// filter looks like from outside on a loaded host. When this was first written
// it was inert for its entire life and the timings said the opposite of the
// truth — a scratchpad run measured 12,438 ms against a project run's 7,925 ms,
// the wrong way round, because at 753 MB free the variance swamps the signal.
// Output could not tell them apart either: both emitted the same 17 bytes.
//
// So the instrument here is a COUNT OF WHAT WAS GOING TO RUN, never a clock.
// It can come back either way, which is the whole requirement
// (rules/instrument-before-claim.md).
//
// The BOM case is the regression that made it inert. PowerShell 5.1 prepends a
// UTF-8 BOM when piping to a native exe; JSON.parse throws on it; the catch
// returned false; the filter switched itself off. 204 bytes sent, 207 received.
// Delete the `replace(/^\uFEFF/, '')` and V-SCRATCH-BOM goes red on its own.

const fs = require('fs');
const path = require('path');
const { isScratchTarget, runChain } = require('../hook-dispatcher.js');

let pass = 0;
let fail = 0;
const ok = (g, e) => { console.log('  OK   ' + g + '  ' + e); pass++; };
const no = (g, e) => { console.log('  FAIL ' + g + '  ' + e); fail++; };
const wrap = (o) => JSON.stringify({ tool_input: o });

// ---------------------------------------------------------------- predicate --
const GREEN = [
  ['forward slashes',  'C:/Users/U/AppData/Local/Temp/claude/proj/abc/scratchpad/msg.txt'],
  ['backslashes',      'C:\\Users\\U\\AppData\\Local\\Temp\\claude\\proj\\abc\\scratchpad\\msg.txt'],
  ['mixed case',       'C:/Users/U/AppData/Local/TEMP/Claude/Proj/ABC/Scratchpad/Msg.TXT'],
  ['notebook_path',    null],
];
for (const [label, p] of GREEN) {
  if (p === null) continue;
  isScratchTarget(wrap({ file_path: p })) ? ok('V-SCRATCH-GREEN', label) : no('V-SCRATCH-GREEN', label + ' -> false');
}
isScratchTarget(wrap({ notebook_path: GREEN[0][1] }))
  ? ok('V-SCRATCH-GREEN', 'notebook_path honoured')
  : no('V-SCRATCH-GREEN', 'notebook_path ignored');

// RED. Both segments are required on purpose: a project directory would have to
// live inside the OS temp tree under `claude/` to be mistaken for a scratchpad,
// and `scratchpad` is the harness's own name for that directory.
const RED = [
  ['ordinary project file', 'C:/Users/U/.claude/skills/claude-power-pack/tools/x.py'],
  ['temp but not scratch',  'C:/Users/U/AppData/Local/Temp/claude/proj/abc/other/msg.txt'],
  ['scratch but not temp',  'C:/Users/U/repos/myapp/scratchpad/notes.txt'],
  ['a file merely NAMED scratchpad', 'C:/Users/U/repos/myapp/src/scratchpad.ts'],
];
for (const [label, p] of RED) {
  isScratchTarget(wrap({ file_path: p })) ? no('V-SCRATCH-RED', label + ' -> true') : ok('V-SCRATCH-RED', label);
}

// FAIL-OPEN. Anything unreadable must run the FULL chain, never the short one:
// a filter that cannot tell must not be the reason a safety gate is skipped.
const OPEN = [
  ['empty string', ''],
  ['not json', 'not json at all'],
  ['no tool_input', '{"session_id":"x"}'],
  ['file_path absent', '{"tool_input":{"content":"h"}}'],
  ['file_path not a string', '{"tool_input":{"file_path":42}}'],
];
for (const [label, raw] of OPEN) {
  isScratchTarget(raw) ? no('V-SCRATCH-FAILOPEN', label + ' -> true') : ok('V-SCRATCH-FAILOPEN', label);
}

// The regression. A three-byte prefix nobody can see, and the guard is gone.
const bom = '\uFEFF' + wrap({ file_path: GREEN[0][1] });
isScratchTarget(bom)
  ? ok('V-SCRATCH-BOM', 'UTF-8 BOM stripped before parse')
  : no('V-SCRATCH-BOM', 'BOM defeats the filter — the original inert bug');

// ------------------------------------------------------------- end-to-end ----
// A SYNTHETIC chain, so this represents the class and cannot be fixed out from
// under the assertion when a real member is renamed or gets faster. Each fake
// hook records that it ran; the assertion is on WHO RAN, not on how long.
// Per-PID fixture directory. A shared one produced a 16/17 I could not attribute
// to any printed assertion, on a host running dozens of concurrent sessions --
// two instances sharing `ran.log` corrupt each other's evidence, and the result
// is a flake that reads exactly like a regression. A setup collision and a
// product failure must not be the same red (rules/instrument-before-claim.md).
const FIX = path.join(__dirname, '_scratch_fixtures_' + process.pid);
const MARK = path.join(FIX, 'ran.log');
fs.mkdirSync(FIX, { recursive: true });
for (const n of ['crit', 'style']) {
  fs.writeFileSync(path.join(FIX, n + '.js'),
    'require("fs").appendFileSync(' + JSON.stringify(MARK) + ', "' + n + '\\n");\n' +
    'process.stdout.write(JSON.stringify({continue:true}));\n');
}
// DERIVED from FIX, never spelled a second time. Spelling the directory in one
// place and the chain's paths in another is how this file briefly pointed at a
// directory that no longer existed: runChain's pre-flight dropped both fixtures
// as `script missing`, nothing ran, and the two E2E assertions went red — a
// result that reads exactly like the feature breaking and was in fact the
// harness losing its own subject. Reported 15/17 three runs running.
const REL = './tests/' + path.basename(FIX) + '/';
const CHAIN = [
  { exe: process.execPath, script: REL + 'crit.js',  timeoutMs: 5000, critical: true },
  { exe: process.execPath, script: REL + 'style.js', timeoutMs: 5000 },
];

// PRECONDITION, asserted rather than assumed. runChain SILENTLY skips a step
// whose script is missing, so a broken fixture path produces "nobody ran" —
// indistinguishable from a filter that skipped everything, which is the exact
// failure this file exists to detect. A setup failure must never wear the
// costume of a product failure (rules/instrument-before-claim.md).
for (const step of CHAIN) {
  if (!fs.existsSync(path.join(__dirname, '..', step.script))) {
    console.log('  HARNESS-FAILED  fixture missing: ' + step.script);
    process.exit(2);
  }
}

const drive = async (p) => {
  fs.writeFileSync(MARK, '');
  await runChain('PreToolUse-Edit-chain', CHAIN, wrap({ file_path: p }));
  return fs.readFileSync(MARK, 'utf8').split('\n').filter(Boolean).sort();
};

(async () => {
  const scratchRan = await drive(GREEN[0][1]);
  const projectRan = await drive(RED[0][1]);

  // The safety half. A style gate may be skipped on a file that cannot have the
  // style problem; a gate whose silent failure is UNSAFE may not be, ever.
  scratchRan.includes('crit')
    ? ok('V-SCRATCH-E2E-SAFETY', 'critical step still runs on a scratchpad write')
    : no('V-SCRATCH-E2E-SAFETY', 'critical step was SKIPPED — safety gate lost');

  scratchRan.includes('style')
    ? no('V-SCRATCH-E2E-SKIP', 'style step ran on a scratchpad write — filter inert')
    : ok('V-SCRATCH-E2E-SKIP', 'style step skipped (ran: ' + JSON.stringify(scratchRan) + ')');

  // The negative control. Without it, a filter that skipped EVERYTHING on every
  // path would satisfy every assertion above and look like a working feature.
  projectRan.length === 2
    ? ok('V-SCRATCH-E2E-CONTROL', 'project write still runs the full chain')
    : no('V-SCRATCH-E2E-CONTROL', 'project write ran ' + JSON.stringify(projectRan));

  fs.rmSync(FIX, { recursive: true, force: true });
  console.log('SCRATCH_FAST_PATH_PASS=' + pass + '/' + (pass + fail) + '  threshold=' + (pass + fail) + '/' + (pass + fail));
  process.exit(fail === 0 ? 0 : 1);
})();
