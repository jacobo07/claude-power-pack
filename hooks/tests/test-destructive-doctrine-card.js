#!/usr/bin/env node
// Both poles of hooks/destructive_doctrine_card.js, hermetic (own state dir per run).
//   node hooks/tests/test-destructive-doctrine-card.js            -> the hook alone
//   node hooks/tests/test-destructive-doctrine-card.js --e2e <dispatcher.js>
//        additionally drives the REAL dispatcher with --event=PreToolUse-Bash-chain and requires the
//        deny to survive its merge (a guard that is wired is not a guard that runs).
'use strict';

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.resolve(__dirname, '..', 'destructive_doctrine_card.js');
const STATE = fs.mkdtempSync(path.join(os.tmpdir(), `ddc-${process.pid}-`));
let pass = 0;
let fail = 0;

function run(payload, env = {}, script = HOOK, args = []) {
  const input = typeof payload === 'string' ? payload : JSON.stringify(payload);
  const r = spawnSync(process.execPath, [script, ...args], {
    input, encoding: 'utf8', timeout: 30000, windowsHide: true,
    env: { ...process.env, DESTRUCTIVE_CARD_STATE_DIR: STATE, ...env },
  });
  let out = {};
  try { out = JSON.parse((r.stdout || '').trim() || '{}'); } catch (_) { out = { unparsed: r.stdout }; }
  return out;
}

const denied = (o) => (o.hookSpecificOutput || {}).permissionDecision === 'deny';
const reason = (o) => String((o.hookSpecificOutput || {}).permissionDecisionReason || '');
const bash = (command, session, tool = 'Bash') => ({ hook_event_name: 'PreToolUse', tool_name: tool, session_id: session, tool_input: { command } });

function check(id, cond, detail) {
  if (cond) { pass += 1; console.log(`PASS ${id}`); } else { fail += 1; console.log(`FAIL ${id} ${detail || ''}`); }
}

// 1. first destructive command of a session is denied, with the card and the skill name in the reason
let o = run(bash('rm -rf build/', 'S1'));
check('V-DDC-FIRST-DENY', denied(o) && reason(o).includes('destructive-state-authorization') && reason(o).includes('[rm]'), JSON.stringify(o).slice(0, 200));
// 2. same session, second destructive command passes (shown once)
o = run(bash('rm -rf dist/', 'S1'));
check('V-DDC-SECOND-PASSES', !denied(o), JSON.stringify(o));
// 3. another session is denied again; PowerShell tool is covered
o = run(bash('Remove-Item -Recurse -Force .\\out', 'S2', 'PowerShell'));
check('V-DDC-POWERSHELL-DENY', denied(o) && reason(o).includes('[Remove-Item]'), JSON.stringify(o).slice(0, 200));
// 4. harmless command passes and does not consume the session's card
o = run(bash('git status', 'S3'));
check('V-DDC-HARMLESS-PASSES', !denied(o), JSON.stringify(o));
o = run(bash('git reset --hard HEAD~1', 'S3'));
check('V-DDC-HARMLESS-DID-NOT-CONSUME', denied(o) && reason(o).includes('[git reset --hard]'), JSON.stringify(o).slice(0, 200));
// 5. a heredoc body being WRITTEN is not a command being run
o = run(bash("cat > run.sh <<'EOF'\nrm -rf /srv/old\nEOF", 'S4'));
check('V-DDC-HEREDOC-BODY-ELIDED', !denied(o), JSON.stringify(o));
// 6. a UTF-8 BOM (PowerShell 5.1 pipe) must not blind the parser
o = run('﻿' + JSON.stringify(bash('git clean -fdx', 'S5')));
check('V-DDC-BOM-STRIPPED', denied(o) && reason(o).includes('[git clean -f]'), JSON.stringify(o).slice(0, 200));
// 7. malformed payload fails open
o = run('{not json');
check('V-DDC-MALFORMED-FAILS-OPEN', !denied(o), JSON.stringify(o));
// 8. kill switch
o = run(bash('rm x', 'S6'), { CLAUDE_DESTRUCTIVE_CARD: 'off' });
check('V-DDC-KILL-SWITCH', !denied(o), JSON.stringify(o));
// 9. other tools are not judged
o = run({ hook_event_name: 'PreToolUse', tool_name: 'Edit', session_id: 'S7', tool_input: { file_path: 'x', old_string: 'rm -rf', new_string: '' } });
check('V-DDC-OTHER-TOOL-PASSES', !denied(o), JSON.stringify(o));
// 10. near-misses that are not destructive
for (const [i, c] of ['git log --format=%h', 'echo form -rf', 'npm run format', 'git checkout main'].entries()) {
  o = run(bash(c, `NM${i}`));
  check(`V-DDC-NEAR-MISS-${i}`, !denied(o), `${c} -> ${JSON.stringify(o)}`);
}
// 11. the ledger counts every judgement (liveness counter)
const led = fs.readFileSync(path.join(STATE, 'ledger.jsonl'), 'utf8').trim().split('\n').map((l) => JSON.parse(l));
check('V-DDC-LEDGER-COUNTS', led.filter((r) => r.decision === 'deny-card').length === 4 && led.some((r) => r.decision === 'pass-already-shown'), `${led.length} rows`);

// 12. end to end through the real dispatcher
const e2e = process.argv.indexOf('--e2e');
if (e2e > -1) {
  const disp = process.argv[e2e + 1];
  o = run(bash('rm -rf e2e-target/', `E2E-${process.pid}`), {}, disp, ['--event=PreToolUse-Bash-chain']);
  check('V-DDC-E2E-DISPATCHER-DENIES', denied(o) && reason(o).includes('destructive-state-authorization'), JSON.stringify(o).slice(0, 300));
  o = run(bash('git status', `E2E2-${process.pid}`), {}, disp, ['--event=PreToolUse-Bash-chain']);
  check('V-DDC-E2E-HARMLESS-NOT-DENIED-BY-CARD', !reason(o).includes('destructive-state-authorization'), JSON.stringify(o).slice(0, 300));
}

fs.rmSync(STATE, { recursive: true, force: true });
console.log(`DDC_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
