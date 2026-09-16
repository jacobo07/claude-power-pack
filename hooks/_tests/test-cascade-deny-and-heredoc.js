#!/usr/bin/env node
/**
 * Two-way self-test for cascade_check_bash.js (2026-09-04).
 *
 * Covers the two defects fixed that day, and covers them in BOTH directions,
 * because each fix is a LOOSENING and a loosening verified only where it should
 * pass is indistinguishable from having deleted the gate:
 *
 *   A. SHAPE. A denial must arrive as `permissionDecision:'deny'` and must NOT
 *      carry `continue:false`. `continue:false` halts the agent instead of the
 *      tool, ends the turn with no text, and puts the block beyond the reach of
 *      the Stop chain (closer-guard.js). That is the cross-repo dead screen.
 *
 *   B. APERTURE. A dangerous pattern inside a heredoc / PowerShell here-string
 *      is FILE CONTENT being written, usually to another machine, and must not
 *      block. The same pattern as a bare local command MUST still block.
 *
 * The cases that must NOT fire are the half that matters. If the detector or
 * python is unreachable the hook fails open, every "must block" case goes red,
 * and that red is the correct signal -- not a flake to be retried away.
 *
 *   node ~/.claude/skills/claude-power-pack/hooks/_tests/test-cascade-deny-and-heredoc.js
 */
'use strict';

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const HOOK = path.resolve(__dirname, '..', 'cascade_check_bash.js');

let pass = 0;
let fail = 0;

function runHook(toolName, command) {
  const res = spawnSync(process.execPath, [HOOK], {
    input: JSON.stringify({ tool_name: toolName, tool_input: { command } }),
    encoding: 'utf8',
    timeout: 20000,
  });
  try {
    return JSON.parse((res.stdout || '{}').trim());
  } catch {
    return {};
  }
}

function isDeny(out) {
  const hso = out.hookSpecificOutput || {};
  return hso.permissionDecision === 'deny';
}

function check(gate, cond, evidence, diag) {
  if (cond) {
    pass += 1;
    console.log(`  [PASS] ${gate}: ${evidence}`);
  } else {
    fail += 1;
    console.log(`  [FAIL] ${gate}: ${diag}`);
  }
}

// The exact shape that produced the measured dead screen: a PowerShell
// here-string carrying a remote run.sh whose body resets a git checkout on a
// DIFFERENT machine. Nothing here resets anything locally.
const HERESTRING_CMD = [
  "$script = @'",
  'set -e',
  'cd /opt/kobiicraft-autodeploy/repo',
  'git fetch --quiet origin main',
  'git reset --hard --quiet origin/main',
  'exec python3 scripts/network/auto_deploy.py --poll',
  "'@",
  '[System.IO.File]::WriteAllText($tmp, $script, (New-Object System.Text.UTF8Encoding($false)))',
  '& scp -P 22022 $tmp root@example.invalid:/root/install.sh',
].join('\n');

const HEREDOC_CMD = [
  'cat > /opt/run.sh <<\'RUNEOF\'',
  '#!/bin/bash',
  'git reset --hard origin/main',
  'RUNEOF',
  'chmod 750 /opt/run.sh',
].join('\n');

// Same pattern, no literal body: this one really is a local reset.
const BARE_CMD = 'git reset --hard origin/main';

// A here-string WITH a local execution sink: the body can become a local
// command, so the aperture must NOT narrow here.
const SINK_CMD = [
  "$s = @'",
  'git reset --hard origin/main',
  "'@",
  'Invoke-Expression $s',
].join('\n');

console.log('=== cascade_check_bash: deny-shape + heredoc aperture ===');

console.log('[A] denial shape');
const bare = runHook('PowerShell', BARE_CMD);
check('V-CASCADE-DENY-SHAPE', isDeny(bare),
  'a real dangerous command denies via permissionDecision=deny',
  `expected permissionDecision=deny; got ${JSON.stringify(bare).slice(0, 220)}`);
check('V-CASCADE-NO-AGENT-HALT', bare.continue !== false,
  'the denial does NOT carry continue:false, so the turn survives',
  'denial still halts the agent (continue:false) -- the dead screen is back');
check('V-CASCADE-REASON-TEXT',
  String((bare.hookSpecificOutput || {}).permissionDecisionReason || '')
    .includes('Do NOT end the turn here'),
  'the reason instructs the model not to close silently',
  'the denial reason lost its anti-dead-screen instruction');

console.log('[B] aperture: literal bodies are data, not commands');
check('V-CASCADE-HERESTRING-EXEMPT', !isDeny(runHook('PowerShell', HERESTRING_CMD)),
  'a PowerShell here-string carrying a remote script no longer blocks',
  'the measured false positive is STILL blocking (here-string body scanned)');
check('V-CASCADE-HEREDOC-EXEMPT', !isDeny(runHook('Bash', HEREDOC_CMD)),
  'a POSIX heredoc body no longer blocks',
  'a heredoc body is still being scanned as a local command');

console.log('[C] the half that matters: enforcement survived the loosening');
check('V-CASCADE-STILL-ENFORCES', isDeny(bare),
  'the bare local command is still denied -- the gate was narrowed, not disabled',
  'the bare dangerous command now PASSES: the fix removed the gate');
check('V-CASCADE-LOCAL-SINK-NOT-ELIDED', isDeny(runHook('PowerShell', SINK_CMD)),
  'a here-string piped into Invoke-Expression keeps the full aperture',
  'a body that becomes a LOCAL command was elided -- real hole opened');

console.log('[D] unrelated tools are untouched');
check('V-CASCADE-TOOL-SCOPE', !isDeny(runHook('Read', BARE_CMD)),
  'a non-shell tool is not judged by this gate',
  'the gate fired on a tool it does not govern');

const total = pass + fail;
console.log(`\nCASCADE_GATE_PASS=${pass}/${total}  threshold=${total}/${total}`);
process.exit(fail === 0 ? 0 : 1);
