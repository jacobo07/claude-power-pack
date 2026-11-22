#!/usr/bin/env node
'use strict';
/**
 * V-CGF-* -- the dispatcher's in-process fallback for capsule_mutation_guard.js (2026-11-22).
 *
 * The guard is a critical step; when its SPAWN fails (ETIMEDOUT on a starved host) the dispatcher
 * used to fail open. Now it re-runs the guard's pure decide() in-process. Driven through the real
 * exported runChain with a 1 ms step timeout, so the spawn always fails and only the fallback can
 * produce a verdict.
 *
 *   node hooks/tests/test-capsule-guard-fallback.js [<hook-dispatcher.js>]
 *
 * V-CGF-ORDER          the guard is the FIRST step of the Bash and Edit chains, once each
 * V-CGF-DENY-WORKER    timeout + matched uncertified worker + Edit  -> deny (guard's message)
 * V-CGF-DRILL-OFF      same with CPP_DISPATCH_INPROC_FALLBACK=off   -> NOT denied (the old fail-open:
 *                      proves V-CGF-DENY-WORKER is produced by the fallback and nothing else)
 * V-CGF-ALLOW-OTHER    timeout + a session that is not the worker   -> NOT denied
 * V-CGF-OBSERVE        timeout + the worker running `git status`    -> NOT denied
 * V-CGF-CONTROL        no timeout, matched worker                   -> deny from the spawned guard
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

const DISP = process.argv[2] || path.join(os.homedir(), '.claude', 'hooks', 'hook-dispatcher.js');
const GUARD = '../skills/claude-power-pack/hooks/capsule_mutation_guard.js';
let pass = 0, fail = 0;
function check(gate, ok, ev) {
  if (ok) { pass++; console.log(`  PASS ${gate}: ${ev}`); } else { fail++; console.log(`  FAIL ${gate}: ${ev}`); }
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'cgf-'));
process.env.CPP_ROLLOVER_STATE_DIR = path.join(tmp, 'rollover');
process.env.CPP_CLAUDE_SESSIONS_DIR = path.join(tmp, 'sessions');
delete process.env.CPP_CAPSULE_ROLLOVER;
fs.mkdirSync(path.join(tmp, 'rollover', 'precert'), { recursive: true });
fs.mkdirSync(path.join(tmp, 'sessions'), { recursive: true });
const WORKER = 'sess-cgf-worker-0001';
fs.writeFileSync(path.join(tmp, 'rollover', 'precert', 'm-cgf000000001.json'), JSON.stringify({
  mission_id: 'm-cgf000000001', worker: 'm-cgf000000001-e2', owner_session: WORKER,
  created_at: Date.now() / 1000, tool: 'C:/PP/tools/mission_capsule.py',
}));

const { runChain, CHAIN_MAP } = require(DISP);
const step = (timeoutMs) => ({ exe: process.execPath, script: GUARD, timeoutMs, block: true, critical: true });
const payload = (sid, tool, input) => JSON.stringify({
  session_id: sid, cwd: tmp, hook_event_name: 'PreToolUse', tool_name: tool, tool_input: input,
});
const EDIT = { file_path: path.join(tmp, 'x.txt'), old_string: 'a', new_string: 'b' };
const denied = (r) => r.outputs.some((o) => o && o.hookSpecificOutput
  && o.hookSpecificOutput.permissionDecision === 'deny'
  && /PRE-CERTIFICATION/.test(o.hookSpecificOutput.permissionDecisionReason || ''));
const show = (r) => JSON.stringify(r.outputs).slice(0, 160);

(async () => {
  for (const chain of ['PreToolUse-Bash-chain', 'PreToolUse-Edit-chain']) {
    const steps = CHAIN_MAP[chain] || [];
    const n = steps.filter((s) => s.script === GUARD).length;
    check(`V-CGF-ORDER ${chain}`, steps.length > 0 && steps[0].script === GUARD && steps[0].critical && n === 1,
      `first=${steps[0] && steps[0].script} occurrences=${n}`);
  }

  let r = await runChain('PreToolUse-Edit-chain', [step(1)], payload(WORKER, 'Edit', EDIT));
  check('V-CGF-DENY-WORKER', denied(r), show(r));

  process.env.CPP_DISPATCH_INPROC_FALLBACK = 'off';
  r = await runChain('PreToolUse-Edit-chain', [step(1)], payload(WORKER, 'Edit', EDIT));
  check('V-CGF-DRILL-OFF', !denied(r), show(r));
  delete process.env.CPP_DISPATCH_INPROC_FALLBACK;

  r = await runChain('PreToolUse-Edit-chain', [step(1)], payload('sess-cgf-interactive-9', 'Edit', EDIT));
  check('V-CGF-ALLOW-OTHER', !denied(r), show(r));

  r = await runChain('PreToolUse-Bash-chain', [step(1)], payload(WORKER, 'Bash', { command: 'git status' }));
  check('V-CGF-OBSERVE', !denied(r), show(r));

  r = await runChain('PreToolUse-Edit-chain', [step(15000)], payload(WORKER, 'Edit', EDIT));
  check('V-CGF-CONTROL', denied(r), show(r));

  try { fs.rmSync(tmp, { recursive: true, force: true }); } catch { /* temp dir */ }
  console.log(`CGF_PASS=${pass}/${pass + fail}`);
  process.exit(fail === 0 ? 0 : 1);
})();
