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
 * Decision tree (idempotent via a marker OUTSIDE the project since B-5, 2026-11-23:
 * ~/.claude/state/first-time-project/<stateKey(cwd)>.json):
 *   1. legacy cwd/.pp-onboarded-prereqs, or the state marker, exists -> silent no-op
 *   2. cwd missing .git                                  -> silent no-op
 *   3. cwd has .git + manifest                           -> detached probe
 *   4. Probe writes the state marker with results. When gaps exist it writes a
 *      handoff: vault/handoffs/pp-onboarding-<ts>.md only if the repo already has
 *      vault/ (a PP project); otherwise next to the state marker. A repo that never
 *      adopted the Power Pack gets nothing written into it.
 *
 * Shared boilerplate lives in hooks/_shared/hook-runtime.js.
 */
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

// B-5 (2026-11-23): the run-once marker lives OUTSIDE the project, keyed by its path, because the
// probe checks the global PP install and its old <cwd>/.pp-onboarded-prereqs landed in every client
// repo. Must equal state_key() in tools/first_time_project_init.py (V-FRW-FIRSTTIME-KEY-PARITY).
function stateKey(cwd) {
  let norm = path.resolve(cwd);
  if (process.platform === 'win32') norm = norm.toLowerCase();
  return crypto.createHash('sha1').update(norm, 'utf8').digest('hex').slice(0, 16);
}
function stateFile(cwd) {
  const dir = process.env.CPP_FIRST_TIME_STATE_DIR ||
    path.join(os.homedir(), '.claude', 'state', 'first-time-project');
  return path.join(dir, stateKey(cwd) + '.json');
}
module.exports = { stateKey, stateFile };

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const rt = require(path.join(PP_ROOT, 'hooks/_shared/hook-runtime'));
const PROBE_SCRIPT = path.join(PP_ROOT, 'tools', 'first_time_project_init.py');
const logErr = rt.makeLogErr('first-time-project');

if (require.main === module) rt.runHook(logErr, async (event) => {
  // Env-payload fallback (BL-SESSION-FOLD-001): the hub detached-spawns this
  // hook with no stdin, passing cwd via PP_EVT_CWD. The standalone entry
  // still supplies cwd via stdin.
  const cwd = (event && event.cwd) || process.env.PP_EVT_CWD;
  if (!cwd) return;
  if (fs.existsSync(path.join(cwd, '.pp-onboarded-prereqs'))) return;   // legacy in-repo marker
  if (fs.existsSync(stateFile(cwd))) return;
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
