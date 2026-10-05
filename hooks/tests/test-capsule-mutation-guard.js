#!/usr/bin/env node
// Gate for hooks/capsule_mutation_guard.js (spec vault/specs/mission-capsule-rollover.md I1, G7-G10, G13).
// Both poles, hermetic (own state + registry dirs). Each block asserts a decision the opposite
// implementation gets wrong: an always-allow guard fails the deny half, an always-deny guard fails
// the observe/not-ours half, a guard that ignores identity fails the legacy-session half.
//   node hooks/tests/test-capsule-mutation-guard.js
//   node hooks/tests/test-capsule-mutation-guard.js --e2e <hook-dispatcher.js>   (+ the real merge)
'use strict';
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const GUARD = path.join(__dirname, '..', 'capsule_mutation_guard.js');
const { judgeTool, matchMarker, decide } = require(GUARD);
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'cmg-'));
const STATE = path.join(TMP, 'rollover');
const REG = path.join(TMP, 'sessions');
const ENV = { CPP_ROLLOVER_STATE_DIR: STATE, CPP_CLAUDE_SESSIONS_DIR: REG, CPP_CAPSULE_ROLLOVER: '' };
fs.mkdirSync(path.join(STATE, 'precert'), { recursive: true });
fs.mkdirSync(REG, { recursive: true });

let pass = 0, fail = 0;
function check(gate, ok, ev) { if (ok) { pass++; console.log(`  PASS ${gate}: ${ev}`); } else { fail++; console.log(`  FAIL ${gate}: ${ev}`); } }

// 1. judgeTool: the pre-certification command policy
const A = true, D = false;
const CASES = [
  ['Edit', { file_path: 'x' }, D], ['Write', { file_path: 'x' }, D], ['MultiEdit', {}, D], ['NotebookEdit', {}, D],
  ['Bash', 'git status --short', A], ['Bash', 'git log --oneline -5', A], ['Bash', 'git rev-parse --short HEAD', A],
  ['Bash', 'git branch --show-current', A], ['Bash', 'git -C C:/w diff HEAD~1', A],
  ['PowerShell', "& 'C:\\Program Files\\Git\\cmd\\git.exe' -C 'C:\\w' log --oneline -3", A],
  ['PowerShell', "Set-Location 'C:\\Users\\User\\Apps\\io-surface'; git status --short", A],
  ['PowerShell', "$env:PYTHONIOENCODING='utf-8'; & 'C:\\Py\\python.exe' C:\\pp\\tools\\mission_capsule.py resume --mission m-1", A],
  ['PowerShell', "python C:/pp/tools/mission_capsule.py certify --mission m-1 --next \"execute phase 2: a; b\" --head abc1234", A],
  ['PowerShell', 'Get-Content .planning/STATE.md | Select-Object -First 40', A],
  ['Bash', 'node ~/.claude/gsd-core/bin/gsd-tools.cjs query init.manager --ws ucep', A],
  // writers and escapes
  ['Bash', 'git commit -m x', D], ['Bash', 'git push', D], ['Bash', 'git checkout -- f', D], ['Bash', 'git stash', D],
  ['PowerShell', "& 'C:\\Program Files\\Git\\cmd\\git.exe' commit -m x", D],
  ['Bash', 'git diff --output=x.patch', D], ['Bash', 'sort -o out.txt in.txt', D],
  ['Bash', 'python -m pytest tests -q', D], ['Bash', 'npm test', D], ['Bash', 'python tools/deploy.py', D],
  ['Bash', 'git log > hist.txt', D], ['PowerShell', 'Get-Content a | Out-File b', D], ['PowerShell', 'Set-Content x y', D],
  ['PowerShell', 'Remove-Item x -Recurse -Force', D], ['Bash', 'ls $(rm x)', D], ['Bash', 'git log && rm x', D],
  ['Bash', 'echo hi > note.md', D], ['Bash', '', D],
  ['Read', { file_path: 'x' }, A],
];
let jp = 0, jf = [];
for (const [tool, input, want] of CASES) {
  const ti = typeof input === 'string' ? { command: input } : input;
  const got = judgeTool(tool, ti).allow;
  if (got === want) jp++; else jf.push(`${tool} ${JSON.stringify(input)} -> ${got}`);
}
check('V-CMG-JUDGE', jf.length === 0, `${jp}/${CASES.length}` + (jf.length ? ' wrong: ' + jf.join(' | ') : ''));
check('V-CMG-SAFE-REDIRECT', judgeTool('Bash', { command: 'git status 2>&1' }).allow
  && judgeTool('PowerShell', { command: 'git log *> $null' }).allow, 'stderr merges and null sinks are not files');

// 2. identity: which session is the pre-certification worker
const now = Date.now() / 1000;
const W = 'm-abc123def456-e5';
function marker(fields) {
  fs.writeFileSync(path.join(STATE, 'precert', 'm-abc123def456.json'),
    JSON.stringify({ mission_id: 'm-abc123def456', worker: W, epoch: 5, cwd: 'C:\\proj', created_at: now,
      capsule_key: 'mission-m-abc123def456-e4', ...fields }));
}
function reg(pid, sessionId, name) {
  fs.writeFileSync(path.join(REG, `${pid}.json`), JSON.stringify({ pid, sessionId, name, kind: 'bg', cwd: 'C:\\proj' }));
}
marker({});
reg(101, 'sess-worker-0001', W);
reg(102, 'sess-legacy-0002', 'infinityops-df');
// A path unique to this run: a fixed one tripped the LIVE anti-thrash counter across runs, whose
// deny then satisfied the e2e gate in this guard's place (measured 2026-10-03).
const EDIT_PATH = path.join(TMP, `cmg-edit-${process.pid}-${Date.now()}.txt`);
const EDIT = (sid, cwd = 'C:\\proj') => ({ session_id: sid, cwd, tool_name: 'Edit',
  tool_input: { file_path: EDIT_PATH, old_string: 'a', new_string: 'b' } });
check('V-CMG-REGISTRY-NAME-MATCH', decide(EDIT('sess-worker-0001'), ENV, now).allow === false,
  'bg id not bound yet: the registry names this session as our worker (G7)');
check('V-CMG-LEGACY-SAME-CWD-ALLOWED', decide(EDIT('sess-legacy-0002'), ENV, now).allow === true,
  'an ordinary session in the same repo, inside the launch window, is not ours');
check('V-CMG-UNREGISTERED-IN-WINDOW', decide(EDIT('sess-unknown-0003'), ENV, now).allow === false,
  'no registry record at all + launch cwd + window: treated as the worker (fail-closed side)');
check('V-CMG-UNREGISTERED-OUT-OF-WINDOW', decide(EDIT('sess-unknown-0003'), ENV, now + 301).allow === true,
  'outside the launch window an unregistered session is not presumed ours');
check('V-CMG-OTHER-CWD', decide(EDIT('sess-unknown-0003', 'C:\\elsewhere'), ENV, now).allow === true, 'other cwd');
marker({ bg_id: 'abcd1234' });
check('V-CMG-BG-PREFIX', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === false, 'bound bg id prefix');
check('V-CMG-BOUND-NO-CWD-GUESS', decide(EDIT('sess-unknown-0003'), ENV, now).allow === true,
  'once bound, the cwd guess is retired');
check('V-CMG-OBSERVE-ALLOWED', decide({ ...EDIT('abcd1234-ffff-0000'), tool_name: 'Bash',
  tool_input: { command: 'git status --short' } }, ENV, now).allow === true, 'reconcile is allowed');
marker({ owner_session: 'sess-owner-0009' });
check('V-CMG-OWNER-SESSION', decide(EDIT('sess-owner-0009', 'C:\\x'), ENV, now).allow === false, 'acked owner');
marker({ bg_id: 'abcd1234', certified_at: now });
check('V-CMG-CERTIFIED-LIFTS', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === true,
  'RESUME_CERTIFIED restores authority');
marker({ bg_id: 'abcd1234', created_at: now - 25 * 3600 });
check('V-CMG-STALE-MARKER-IGNORED', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === true, '> 24 h');
marker({ bg_id: 'abcd1234' });
fs.writeFileSync(path.join(STATE, 'capsule-v2.off'), '');
check('V-CMG-FILE-KILL-SWITCH', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === true, 'G13 file switch');
fs.unlinkSync(path.join(STATE, 'capsule-v2.off'));
check('V-CMG-POSITIVE-CONTROL', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === false,
  'the switch removed, the same call is denied again');
fs.rmSync(path.join(STATE, 'precert'), { recursive: true, force: true });
check('V-CMG-NO-MARKERS-FAST-ALLOW', decide(EDIT('abcd1234-ffff-0000'), ENV, now).allow === true,
  'no precert dir: every session passes');
fs.mkdirSync(path.join(STATE, 'precert'), { recursive: true });

// 3. wire contract: the real process, real JSON
marker({ bg_id: 'abcd1234' });
function run(script, payload, args = []) {
  const r = spawnSync(process.execPath, [script, ...args], { input: JSON.stringify(payload), encoding: 'utf8',
    timeout: 60000, windowsHide: true, env: { ...process.env, ...ENV } });
  try { return JSON.parse((r.stdout || '').trim().split(/\r?\n/).pop() || '{}'); } catch { return { raw: r.stdout, err: r.stderr }; }
}
const denied = (o) => ((o.hookSpecificOutput || {}).permissionDecision === 'deny');
let o = run(GUARD, { ...EDIT('abcd1234-ffff-0000'), hook_event_name: 'PreToolUse' });
check('V-CMG-WIRE-DENY', denied(o) && /PRE-CERTIFICATION/.test(o.hookSpecificOutput.permissionDecisionReason), JSON.stringify(o).slice(0, 160));
o = run(GUARD, { ...EDIT('sess-legacy-0002'), hook_event_name: 'PreToolUse' });
check('V-CMG-WIRE-ALLOW', !denied(o) && o.continue === true, JSON.stringify(o).slice(0, 120));
// spec 11.5: the deny names the runnable script, never the mission's slash command (`resume_cmd`)
marker({ bg_id: 'abcd1234', resume_cmd: '/gsd-autonomous', tool: 'C:/PP/tools/mission_capsule.py' });
o = run(GUARD, { ...EDIT('abcd1234-ffff-0000'), hook_event_name: 'PreToolUse' });
let why = (o.hookSpecificOutput || {}).permissionDecisionReason || '';
check('V-CMG-DENY-NAMES-TOOL', why.includes('python C:/PP/tools/mission_capsule.py resume --mission m-abc123def456')
  && !why.includes('/gsd-autonomous'), why.slice(0, 220));
marker({ bg_id: 'abcd1234', resume_cmd: '/gsd-autonomous' });
o = run(GUARD, { ...EDIT('abcd1234-ffff-0000'), hook_event_name: 'PreToolUse' });
why = (o.hookSpecificOutput || {}).permissionDecisionReason || '';
check('V-CMG-DENY-NO-TOOL-GENERIC', why.includes('python <PP>/tools/mission_capsule.py resume --mission m-abc123def456')
  && !why.includes('/gsd-autonomous'), why.slice(0, 220));
marker({ bg_id: 'abcd1234' });

// 4. end to end through the real dispatcher (G9: the deny must survive mergeOutputs)
const e2e = process.argv.indexOf('--e2e');
if (e2e > -1) {
  const disp = process.argv[e2e + 1];
  o = run(disp, { ...EDIT('abcd1234-ffff-0000'), hook_event_name: 'PreToolUse' }, ['--event=PreToolUse-Edit-chain']);
  check('V-CMG-E2E-EDIT-DENIED', denied(o) && /PRE-CERTIFICATION/.test(JSON.stringify(o)), JSON.stringify(o).slice(0, 200));
  // PowerShell, and THIS guard's reason required: via Bash, windows-bash-bridge-guard denies `git`
  // first, and a bare "denied" read that other guard's verdict as this one's (measured 2026-10-03).
  o = run(disp, { session_id: 'abcd1234-ffff-0000', cwd: 'C:\\proj', tool_name: 'PowerShell', hook_event_name: 'PreToolUse',
    tool_input: { command: "& 'C:\\Program Files\\Git\\cmd\\git.exe' commit -m x" } }, ['--event=PreToolUse-Bash-chain']);
  check('V-CMG-E2E-COMMIT-DENIED', denied(o) && /PRE-CERTIFICATION/.test(JSON.stringify(o)), JSON.stringify(o).slice(0, 200));
  o = run(disp, { session_id: 'abcd1234-ffff-0000', cwd: 'C:\\proj', tool_name: 'PowerShell', hook_event_name: 'PreToolUse',
    tool_input: { command: "& 'C:\\Program Files\\Git\\cmd\\git.exe' status --short" } }, ['--event=PreToolUse-Bash-chain']);
  check('V-CMG-E2E-OBSERVE-NOT-DENIED-BY-GUARD', !/PRE-CERTIFICATION/.test(JSON.stringify(o)), JSON.stringify(o).slice(0, 160));
  o = run(disp, { ...EDIT('sess-legacy-0002'), hook_event_name: 'PreToolUse' }, ['--event=PreToolUse-Edit-chain']);
  check('V-CMG-E2E-LEGACY-NOT-DENIED-BY-GUARD', !/PRE-CERTIFICATION/.test(JSON.stringify(o)), JSON.stringify(o).slice(0, 160));
}

fs.rmSync(TMP, { recursive: true, force: true });
console.log(`CMG_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail ? 1 : 0);
