#!/usr/bin/env node
// V-PGREP-* gates for hooks/self_match_pgrep_guard.js. Drives the real file over stdin, both poles.
'use strict';
const path = require('path');
const { spawnSync } = require('child_process');
const HOOK = path.join(__dirname, '..', 'self_match_pgrep_guard.js');

function run(stdin) {
  const r = spawnSync(process.execPath, [HOOK], { input: stdin, encoding: 'utf8' });
  return { code: r.status, out: (r.stdout || '').trim() };
}
const bash = (command) => JSON.stringify({ tool_name: 'Bash', tool_input: { command } });

let pass = 0, fail = 0;
function gate(name, stdin, wantDeny) {
  const r = run(stdin);
  let denied = false, parseErr = '';
  if (r.out) {
    try { denied = JSON.parse(r.out).hookSpecificOutput.permissionDecision === 'deny'; }
    catch (e) { parseErr = ` unparseable stdout: ${e.message}`; }
  }
  const ok = r.code === 0 && denied === wantDeny && !parseErr;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name} (deny=${denied}, exit=${r.code})${parseErr}`);
  if (ok) pass++; else fail++;
}

const S17 = `cd /home/kobii/missions/t1-campaign && timeout 580 bash -c 'until ! pgrep -f "llm_fix run --cohort list --fns evidence/ascension/s17/w2_pilot_id" >/dev/null; do sleep 30; done; echo PILOT_DONE'`;
gate('V-PGREP-S17-STALL-SHAPE-DENIED', bash(S17), true);
gate('V-PGREP-UNQUOTED-DENIED', bash('until ! pgrep -f llm_fix; do sleep 5; done'), true);
gate('V-PGREP-COMBINED-FLAGS-DENIED', bash('pgrep -af "s17_w1_search.py" || echo gone'), true);
gate('V-PGREP-PKILL-SELF-DENIED', bash('pkill -9 -f "python3 tools/s17_w3_sweep.py"'), true);
gate('V-PGREP-BRACKET-ALLOWED', bash('until ! pgrep -f "[l]lm_fix run --cohort list" >/dev/null; do sleep 30; done'), false);
gate('V-PGREP-PID-WAIT-ALLOWED', bash('python3 x.py & PID=$!; while kill -0 $PID; do sleep 30; done'), false);
gate('V-PGREP-NO-FULL-ALLOWED', bash('pgrep llm_fix'), false);
gate('V-PGREP-RUNTIME-VAR-ALLOWED', bash('pgrep -f "$PAT" >/dev/null'), false);
gate('V-PGREP-BAD-REGEX-ALLOWED', bash('pgrep -f "(" || true'), false);
gate('V-PGREP-NON-BASH-ALLOWED', JSON.stringify({ tool_name: 'Read', tool_input: { file_path: 'pgrep -f x' } }), false);
gate('V-PGREP-BAD-STDIN-FAILS-OPEN', 'not json{', false);
gate('V-PGREP-WORD-ONLY-ALLOWED', bash('echo "use pgrep carefully"'), false);
// review 2026-11-07 F1-F4
gate('V-PGREP-F1-DIGIT-SIGNAL-DENIED', bash('pkill -USR1 -f "llm_fix run"'), true);
gate('V-PGREP-F1-SIG-PREFIX-DENIED', bash('pkill -SIGUSR1 -f "llm_fix run"'), true);
gate('V-PGREP-F1-DOUBLE-DASH-DENIED', bash('pgrep -f -- "llm_fix run" >/dev/null'), true);
gate('V-PGREP-F2-CLUSTER-ARG-ALLOWED', bash('pgrep -fu kobii "[l]lm_fix" >/dev/null'), false);
gate('V-PGREP-F2-CLUSTER-ARG-SELF-DENIED', bash('pgrep -fu kobii "llm_fix" >/dev/null'), true);
gate('V-PGREP-F2-HUP-SIGNAL-DENIED', bash('pkill -HUP -f "s17_sweep"'), true);
gate('V-PGREP-F3-COMMIT-PROSE-ALLOWED', bash('git commit -m "docs: pgrep -f llm_fix self-match"'), false);
gate('V-PGREP-F3-ECHO-PROSE-ALLOWED', bash('echo pgrep -f foo'), false);
gate('V-PGREP-F3-SUBSHELL-DENIED', bash('N=$(pgrep -fc "llm_fix run"); echo $N'), true);
gate('V-PGREP-F3-TIMEOUT-DENIED', bash('timeout 60 pgrep -f "llm_fix run"'), true);
gate('V-PGREP-F4-DQ-BACKSLASH-KEPT', bash('pgrep -f "a\\.b" ; echo axb'), false);

console.log(`\n${pass}/${pass + fail} passed`);
process.exit(fail ? 1 : 0);
