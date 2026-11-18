#!/usr/bin/env node
// CDIO-10 publish gate (spec vault/specs/cdio-10-publish-gate.md). PreToolUse-Bash-chain member (Bash + PowerShell).
// Pure-node prefilter: python (tools/legal_deploy_gate.py) is spawned ONLY when the command starts a production web
// publish, so every other shell call costs one regex pass. Deny shape is permissionDecision:'deny', never
// continue:false (that halts the agent; see cascade_check_bash.js defect 1). Fail-open on any internal error.
'use strict';

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const PP_ROOT = path.resolve(__dirname, '..');
const PY = process.env.PYTHON_BIN
  || (process.platform === 'win32'
    ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
    : 'python3');

// A command position: line start, after ; & | ( or a runner. Words inside a quoted commit message do not qualify.
const POS = String.raw`(?:^|[;&|(]\s*|\b(?:npx|bunx|yarn|pnpm(?:\s+dlx)?)\s+)`;
const TAIL = String.raw`[^\n;&|]*`;
const PUBLISH = [
  new RegExp(POS + String.raw`vercel\b` + TAIL + String.raw`--prod\b`, 'im'),
  new RegExp(POS + String.raw`netlify\s+deploy\b` + TAIL + String.raw`--prod\b`, 'im'),
  new RegExp(POS + String.raw`firebase\s+deploy\b(?!` + TAIL + String.raw`--only\s+(?![^\s]*hosting)\S)`, 'im'),
  new RegExp(POS + String.raw`wrangler\s+pages\s+deploy\b`, 'im'),
  new RegExp(POS + String.raw`gh-pages\s+(?:-d|--dist)\b`, 'im'),
  new RegExp(POS + String.raw`surge\b(?:\s|$)`, 'im'),
];

function elide(cmd) {
  return cmd
    .replace(/@(['"])[\s\S]*?\1@/g, "''")
    .replace(/<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1[\s\S]*?^[ \t]*\2[ \t]*$/gm, '<<X');
}

function isPublish(cmd) {
  const c = elide(cmd);
  return PUBLISH.some((rx) => rx.test(c));
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

async function main() {
  if (/^(off|0|false)$/i.test((process.env.CPP_LEGAL_DEPLOY_GATE || '').trim())) return emit({ continue: true });
  let raw = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) raw += chunk;
  } catch { return emit({ continue: true }); }
  if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
  let req;
  try { req = JSON.parse(raw); } catch { return emit({ continue: true }); }
  if (!['Bash', 'PowerShell'].includes(req.tool_name || '')) return emit({ continue: true });
  const cmd = ((req.tool_input || {}).command || '');
  if (!cmd.trim() || !isPublish(cmd)) return emit({ continue: true });

  let r;
  try {
    r = spawnSync(PY, [path.join(PP_ROOT, 'tools', 'legal_deploy_gate.py')], {
      input: JSON.stringify({ ...req, cwd: req.cwd || process.cwd() }),
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      encoding: 'utf8', timeout: 15000, windowsHide: true,
    });
  } catch { return emit({ continue: true }); }
  let out;
  try { out = JSON.parse(String(r.stdout || '').trim().split('\n').pop()); } catch { return emit({ continue: true }); }
  if (!out || !out.deny) return emit({ continue: true });
  return emit({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: out.reason
        + ' Do NOT end the turn here: say what was denied and what you are doing instead.',
    },
  });
}

if (require.main === module) main();
module.exports = { isPublish };
