#!/usr/bin/env node
// PreToolUse Cascade Prevention gate -- BL-CASCADE-001 wiring.
// Checks Bash commands before execution. A C4+ cascade hit OR a
// dangerous-command-registry match -> block. Everything else passes.
// Fail-open on any internal error: a guard that crashes is worse than
// one that under-fires.
'use strict';

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const PP_ROOT = path.resolve(__dirname, '..');
const PY = process.env.PYTHON_BIN
  || (process.platform === 'win32'
    ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
    : 'python3');
const DETECTOR_TIMEOUT_MS = 2500;
const MAX_COMMAND_LEN = 2000;  // commands beyond this are truncated for the probe

// The command text is passed via stdin (NOT interpolated into the -c
// body) so shell metacharacters in the command can never break the
// probe or inject code.
const PY_SCRIPT = `import json, os, sys
sys.path.insert(0, os.environ['PP_ROOT'])
from modules.cascade_prevention.engine import detect
from modules.cascade_prevention.dangerous_cmds import is_dangerous, reasons
cmd = sys.stdin.read()
hits = detect('bash', {'command': cmd})
blockers = [h for h in hits if h.should_block]
danger = is_dangerous(cmd)
print(json.dumps({
    'block': bool(blockers) or danger,
    'cascade_blockers': len(blockers),
    'dangerous': danger,
    'reasons': reasons(cmd)[:4],
}))
`;

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

(async () => {
  let payload = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) payload += chunk;
  } catch {
    return emit({ continue: true });
  }

  // PowerShell 5.1 on Windows prepends a UTF-8 BOM on the pipe -- strip
  // (sibling fix to hooks/secret_firewall_gate.js + the BOM doctrine).
  if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1);

  let req;
  try {
    req = JSON.parse(payload);
  } catch {
    return emit({ continue: true });
  }

  if ((req.tool_name || '') !== 'Bash') return emit({ continue: true });

  const command = ((req.tool_input || {}).command || '').slice(0, MAX_COMMAND_LEN);
  if (!command.trim()) return emit({ continue: true });

  let result;
  try {
    result = spawnSync(PY, ['-c', PY_SCRIPT], {
      input: command,
      env: { ...process.env, PP_ROOT },
      encoding: 'utf8',
      timeout: DETECTOR_TIMEOUT_MS,
      windowsHide: true,
    });
  } catch {
    return emit({ continue: true });
  }

  if (result.status !== 0 || !result.stdout) return emit({ continue: true });

  let info;
  try {
    info = JSON.parse(result.stdout.trim().split('\n').pop());
  } catch {
    return emit({ continue: true });
  }

  if (info.block) {
    const why = (info.reasons && info.reasons.length)
      ? info.reasons.join('; ')
      : `${info.cascade_blockers} cascade blocker(s)`;
    return emit({
      continue: false,
      stopReason:
        'HR-CASCADE-002 -- Cascade Prevention blocked a dangerous or '
        + `cascade-risk command (${why}). Review and add an explicit `
        + 'backup / verification, or confirm the override before retrying.',
    });
  }

  return emit({ continue: true });
})();
