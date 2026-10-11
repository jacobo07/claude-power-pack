#!/usr/bin/env node
/**
 * test-closer-guard-evaluation-without-closure.js
 *
 * MEASURED 2026-10-11 (Jacobo, KobiiSports Resort, Madzia P2). A turn rebuilt a
 * venv, built + baked + rendered an asset, compared it against the reference,
 * listed five concrete defects, named the fix, and then ENDED on:
 *     "**Next:** I recommend fixing the hair before writing the P2 evidence file
 *      ... After that I'll write `.ksr_vault/evidence/MADZIA_P2_ASSET_20261011.md`."
 * The fix was internal, reversible and authorised. The Owner had to come back and
 * order it. Replayed through classify() on the transcript's own bytes: null as a
 * text-only turn AND as {toolTurn, endsOnText} -- beside a PASSIVE_WAIT control
 * that fired. The guard was alive; the shape had no class. Trap: EVALUATION
 * WITHOUT CLOSURE -- a report that names five defects is five open defects.
 *
 * Both poles are driven, and the must-not-fire half matters most: a class that
 * fires on honest gated handoffs gets the guard switched off, and an off guard is
 * the dead screen. The run()-level cases spawn the hook exactly as Claude Code
 * does (stdin JSON -> stdout JSON) with USERPROFILE pointed at a temp dir, so the
 * wiring is proven, not just the predicate, and live state is never touched.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const HOOK = path.join(__dirname, '..', 'closer-guard.js');
const guard = require(HOOK);
const CLS = 'EVALUATION_WITHOUT_CLOSURE';

// The measured closer, byte-for-byte tail of the 2026-10-11 turn (case 14).
const MEASURED = 'I recommend fixing the hair before writing the P2 evidence file, so that file '
  + 'describes an asset worth keeping. The fix is a v4: make the side pieces start at the crown '
  + 'and hug the head, and narrow the bare-skin wedge to a thin part. All of this is controlled in '
  + '`tools/kobiimii/specs/madzia.json`. After that I\'ll write '
  + '`.ksr_vault/evidence/MADZIA_P2_ASSET_20261011.md`. Nothing is committed yet; the new renders '
  + 'are copied into `runs/` but not added to git.';

const MUST_FIRE = [
  ['14 measured closer', '**Next:** ' + MEASURED],
  ['1 defect + known next action', 'Build passes. Two defects remain: the hairline wedge and the back panel. Next: fix the hairline in the spec and rebuild.'],
  ['2 evaluation done, fix not executed', 'The review found the blush ring is a blur fringe. I recommend pre-filling the layer with its own colour.'],
  ['3 build green, evidence missing', 'The build is green. After that I\'ll write the evidence document.'],
  ['4 evidence written, own commit pending', 'Evidence is written. The next step is to commit the four changed files.'],
  ['ES recomiendo', 'La revisión encontró dos defectos. Recomiendo corregir el pelo antes de escribir la evidencia.'],
  ['ES siguiente paso', 'El build pasa. Siguiente paso: regenerar los renders y comparar.'],
  ['ES despues hare', 'Quedan los commits. Después haré el commit de la evidencia.'],
];

const MUST_NOT_FIRE = [
  ['12 done', 'DONE: build, verify 8/8 and evidence committed in 1718e0d.'],
  ['5 likeness only', 'The asset is technically verified. HUMAN GATE: likeness needs someone who knows Madzia to judge an in-game capture.'],
  ['6 external authorisation', 'Next: deploying to production requires your approval.'],
  ['6b owner-gated slot', 'I recommend booking the GEX44 slot; it is Owner-gated and the balance is 0.'],
  ['7 budget exhausted', 'BUDGET EXHAUSTED: checkpoint written to RESUMPTION_FILE.md; next action is the P3 wiring.'],
  ['13 check could not run', 'BLOCKED: Dolphin cannot run on this host; the boot is UNVERIFIED, not passed.'],
  ['15 aesthetic preference', 'All objective defects are closed. Blush strength is your call: I left it subtle.'],
  ['assessment scope', 'I recommend shipping after the hair fix. Scope: assessment only.'],
  ['plain report', 'I rewrote 11 entries; the backup is on disk.'],
  ['recommend as noun', 'The recommendation engine now returns 12 results in 40 ms.'],
  ['ES gated', 'Siguiente paso: el despliegue requiere tu aprobación.'],
  // Shapes measured in the 784-closer replay (2026-10-11), each a genuine gate:
  ['handoff block NEXT field', 'PANE pp\nSTATUS COMPLETE\nNEXT: Owner picks A/B/C in the decision packet\nDEBT NONE'],
  ['HANDOFF_STATUS underscore', 'Once merged I will check the deploy. Next: verify the sha. HANDOFF_STATUS: PARTIAL'],
  ['owner confirmation', 'Once you confirm, I\'ll squash-merge #533 and check the deploy.'],
  ['third-party decision', 'If you or Maria say yes, after that I\'ll write the request, whichever way she chooses.'],
  ['async still running', 'The planner is still working, and the next step is to commit its revision.'],
  ['async hands back', '**Next:** when 04-02 hands back, I verify its commits, then run 04-03.'],
  ['ES goal agotado', 'Lo primero que haré es comprobar el guard, y después haré el escaneo; el goal está agotado.'],
];

let pass = 0;
let fail = 0;
const ok = (name) => { pass++; console.log(`  PASS  ${name}`); };
const bad = (name, detail) => { fail++; console.log(`  FAIL  ${name} -- ${detail}`); };

console.log('classify(): text-only and tool-turn-ending-on-text, both poles');
for (const [name, text] of MUST_FIRE) {
  for (const opts of [undefined, { toolTurn: true, endsOnText: true }]) {
    const v = guard.classify(text, opts);
    const mode = opts ? 'tool' : 'text';
    if (v && v.cls === CLS) ok(`fires [${mode}] ${name}`);
    else bad(`fires [${mode}] ${name}`, JSON.stringify(v));
  }
}
for (const [name, text] of MUST_NOT_FIRE) {
  const v = guard.classify(text);
  if (!v || v.cls !== CLS) ok(`silent ${name}`);
  else bad(`silent ${name}`, JSON.stringify(v));
}

// A tool call AFTER the text means the work followed the announcement: exempt.
{
  const v = guard.classify(MUST_FIRE[1][1], { toolTurn: true, endsOnText: false });
  if (!v) ok('exempt when a tool call follows the text');
  else bad('exempt when a tool call follows the text', JSON.stringify(v));
}

// Positive control: the pre-existing class still fires, so silence above means something.
{
  const v = guard.classify('Standing by for your review.');
  if (v && v.cls === 'PASSIVE_WAIT') ok('control: PASSIVE_WAIT still fires');
  else bad('control: PASSIVE_WAIT still fires', JSON.stringify(v));
}

// ---- run()-level: spawn the real hook, isolated home ------------------------
const home = fs.mkdtempSync(path.join(os.tmpdir(), 'cg-ewc-'));
const transcript = path.join(home, 'transcript.jsonl');
fs.writeFileSync(transcript, [
  { type: 'user', message: { role: 'user', content: 'resume Madzia' } },
  { type: 'assistant', message: { role: 'assistant', content: [{ type: 'tool_use', id: 't1', name: 'PowerShell', input: {} }] } },
  { type: 'user', message: { role: 'user', content: [{ type: 'tool_result', tool_use_id: 't1', content: 'exit=0' }] } },
  { type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: '**Next:** ' + MEASURED }] } },
].map((r) => JSON.stringify(r)).join('\n') + '\n');

function invoke(extraEnv) {
  const env = { ...process.env, USERPROFILE: home, HOME: home, ...extraEnv };
  delete env.CLAUDE_CLOSER_GUARD;
  if (!extraEnv || !('CLAUDE_CLOSER_GUARD_DEFERRED' in extraEnv)) delete env.CLAUDE_CLOSER_GUARD_DEFERRED;
  const r = spawnSync(process.execPath, [HOOK], {
    input: JSON.stringify({ session_id: 'ewc-test', transcript_path: transcript }),
    env, encoding: 'utf8', timeout: 15000,
  });
  try { return JSON.parse((r.stdout || '').trim().split('\n').pop()); } catch { return { raw: r.stdout, err: r.stderr }; }
}

console.log('run(): the real hook process');
const r1 = invoke();
if (r1.decision === 'block' && String(r1.reason).includes(CLS)) ok('hook blocks the measured turn and names the class');
else bad('hook blocks the measured turn and names the class', JSON.stringify(r1).slice(0, 200));
if (String(r1.reason || '').includes('HUMAN GATE:')) ok('block reason tells the agent how to mark a genuine gate');
else bad('block reason tells the agent how to mark a genuine gate', 'marker missing from reason');

// Bounded: the same closer repeated is blocked at most MAX_STREAK (2) times, then released.
const r2 = invoke();
const r3 = invoke();
if (r2.decision === 'block' && r3.continue === true) ok('anti-loop: 2nd identical repeat blocked, 3rd released (no infinite loop)');
else bad('anti-loop: 2nd identical repeat blocked, 3rd released (no infinite loop)', JSON.stringify([r2, r3]).slice(0, 200));

// Kill switch for this class alone.
fs.rmSync(path.join(home, '.claude'), { recursive: true, force: true });
const r4 = invoke({ CLAUDE_CLOSER_GUARD_DEFERRED: 'off' });
if (r4.continue === true && !r4.decision) ok('CLAUDE_CLOSER_GUARD_DEFERRED=off disables only this class');
else bad('CLAUDE_CLOSER_GUARD_DEFERRED=off disables only this class', JSON.stringify(r4).slice(0, 200));

fs.rmSync(home, { recursive: true, force: true });
console.log(`EWC_PASS=${pass}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
