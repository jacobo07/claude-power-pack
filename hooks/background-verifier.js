#!/usr/bin/env node
/**
 * background-verifier.js - Stop hook (Zero-Command Plan, Component C).
 *
 * Source of truth: PP repo (claude-power-pack/hooks/).
 * Deployment path: ~/.claude/hooks/background-verifier.js (Owner-authorized
 * install via tools/settings_merger.py register-zero-command).
 *
 * Runs three background checks AFTER the agent's response is delivered.
 * Each writes a vault/handoffs/<kind>-<ts>.md if a condition warrants
 * Owner attention. Does NOT auto-fix, does NOT auto-push, does NOT
 * auto-OVO. Stop hook returns {} immediately; heavy work runs in a
 * detached child so Stop never blocks.
 *
 * Three checks (per the Zero-Command plan):
 *   1. Mirror parity   - global vs PP doctrine pair diff (drift -> handoff)
 *   2. OVO staleness   - last verdict age + uncommitted/ahead detection
 *   3. Spec coherence  - bracketed-clarification markers vs chain advance
 *
 * Idempotency: per-kind handoff capped at one per 10 minutes (the child
 * checks mtime of the most recent handoff of same kind).
 *
 * Shared boilerplate lives in hooks/_shared/hook-runtime.js.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const rt = require(path.join(PP_ROOT, 'hooks/_shared/hook-runtime'));
const VERIFIER_SCRIPT = path.join(PP_ROOT, 'tools', 'background_verifier_run.py');
const logErr = rt.makeLogErr('background-verifier');

rt.runHook(logErr, async (event) => {
  const cwd = event && event.cwd;
  if (!cwd) return;
  if (!fs.existsSync(VERIFIER_SCRIPT)) return;
  if (!fs.existsSync(path.join(cwd, '.git'))) return;

  const child = spawn(
    'python',
    [VERIFIER_SCRIPT, '--cwd', cwd, '--session', event.session_id || 'unknown'],
    { detached: true, stdio: 'ignore', windowsHide: true }
  );
  child.unref();
});
