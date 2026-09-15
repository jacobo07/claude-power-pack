#!/usr/bin/env node
// GSD X -- the ExecutionOS Lite tier, measured instead of self-assessed.
//
// UserPromptSubmit. Level-2 advisory: it NEVER blocks, never denies, and never
// costs the user their prompt. On any failure it prints nothing and exits 0,
// which degrades exactly to the behaviour that exists today -- the standing
// reminder's constant "Default LIGHT."
//
// WHY THE BUDGET IS SMALL. This chain is sequential (CHAIN_CONCURRENCY has no
// UserPromptSubmit-chain entry, so DEFAULT_CONCURRENCY = 1) and its per-step
// budgets already sum to 46000 ms against a 15000 ms harness ceiling in
// settings.json. A chain killed at the ceiling loses the dispatcher's stdout
// entirely, so EVERY advisory on this event dies together and silently. A sixth
// step must therefore be cheap enough not to move that sum meaningfully; this
// one is capped well under its own share and kills its child rather than
// inheriting the chain's failure mode.
//
// Registration is Owner-side. HR-001 forbids this agent writing under
// ~/.claude, and CHAIN_MAP lives in ~/.claude/hooks/hook-dispatcher.js. The
// one line required is documented in the module docstring of
// modules/gsd_x/cli.py and in the commit that introduced this file.

'use strict';

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const CHILD_TIMEOUT_MS = 2500;
const KILL_SWITCH = String(process.env.CLAUDE_GSDX || '').toLowerCase() === 'off';

function allow(text) {
  if (text) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: text,
      },
    }));
  }
  process.exit(0);
}

function pythonExe() {
  // Prefer an explicit interpreter; fall back to the launcher, then PATH. A
  // missing interpreter must be silence, never a thrown hook.
  const explicit = process.env.CLAUDE_PY_EXE;
  if (explicit && fs.existsSync(explicit)) return explicit;
  const known = path.join(
    process.env.LOCALAPPDATA || '',
    'Programs', 'Python', 'Python312', 'python.exe'
  );
  if (fs.existsSync(known)) return known;
  return process.platform === 'win32' ? 'py' : 'python3';
}

function main() {
  if (KILL_SWITCH) process.exit(0);

  let raw = '';
  try {
    raw = fs.readFileSync(0, 'utf8');
  } catch (_) {
    process.exit(0);
  }
  if (!raw || !raw.trim()) process.exit(0);

  // Cheap pre-filter. Parsing here avoids paying for a python spawn on a
  // payload that carries no prompt at all.
  let prompt = '';
  try {
    const payload = JSON.parse(raw);
    prompt = payload.prompt || payload.user_prompt || payload.userPrompt || '';
  } catch (_) {
    process.exit(0);
  }
  if (!String(prompt).trim()) process.exit(0);

  const cli = path.resolve(__dirname, '..', 'modules', 'gsd_x', 'cli.py');
  if (!fs.existsSync(cli)) process.exit(0);

  let out = '';
  try {
    const res = spawnSync(pythonExe(), [cli], {
      input: raw,
      encoding: 'utf8',
      timeout: CHILD_TIMEOUT_MS,
      killSignal: 'SIGKILL',
      shell: false,                       // no bash.exe is ever created
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      windowsHide: true,
    });
    // A timed-out or crashed child is silence, not an error. The heartbeat is
    // what distinguishes "did not run" from "ran and had nothing to say" --
    // this hook deliberately does not try to signal that difference inline.
    if (res && res.status === 0 && res.stdout) out = String(res.stdout).trim();
  } catch (_) {
    out = '';
  }

  allow(out);
}

try {
  main();
} catch (_) {
  process.exit(0);          // fail-open, absolute
}
