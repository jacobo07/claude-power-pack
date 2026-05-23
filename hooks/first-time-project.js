#!/usr/bin/env node
/**
 * first-time-project.js - SessionStart hook (Zero-Command Plan, Component D).
 *
 * Source of truth: PP repo (claude-power-pack/hooks/).
 * Deployment path: ~/.claude/hooks/first-time-project.js (Owner-authorized
 * install via tools/settings_merger.py register-zero-command).
 *
 * Sibling to zero-command-bootstrap.js (Component A). A handles Spec Kit
 * stub; D runs a quick prereq probe to surface PP install gaps the first
 * time the agent visits a real project dir.
 *
 * Decision tree (idempotent via .pp-onboarded-prereqs marker - distinct
 * from .pp-onboarded so Component A and D don't race or stomp each other):
 *   1. cwd/.pp-onboarded-prereqs exists                  -> silent no-op
 *   2. cwd missing .git                                  -> silent no-op
 *   3. cwd has .git + manifest                           -> detached probe
 *   4. Probe writes .pp-onboarded-prereqs with results,
 *      and vault/handoffs/pp-onboarding-<ts>.md when gaps exist.
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
const PROBE_SCRIPT = path.join(PP_ROOT, 'tools', 'first_time_project_init.py');
const logErr = rt.makeLogErr('first-time-project');

rt.runHook(logErr, async (event) => {
  const cwd = event && event.cwd;
  if (!cwd) return;
  if (fs.existsSync(path.join(cwd, '.pp-onboarded-prereqs'))) return;
  if (!fs.existsSync(path.join(cwd, '.git'))) return;
  if (!rt.detectManifest(cwd)) return;
  if (!fs.existsSync(PROBE_SCRIPT)) return;

  const child = spawn(
    'python',
    [PROBE_SCRIPT, '--cwd', cwd, '--session', event.session_id || 'unknown'],
    { detached: true, stdio: 'ignore', windowsHide: true }
  );
  child.unref();
});
