#!/usr/bin/env node
'use strict';
// ---------------------------------------------------------------------------
// pm03_publish_stop.js -- Stop-hook committer for the PM-03 Findings Bus (C73/C76).
//
// The producer/consumer pair that finally WIRES PM-03's publish side:
//   * producer  (during work): the agent stages a reusable conclusion the moment
//     it is reached ->  python .../pm_03_bus.py --repo <cwd> --sid <sid> --stage
//                       --topic "<t>" --claim "<c>" --evidence "<e>"
//   * committer (this hook, at Stop): drains the session's staging file into the
//     bus and clears it, so a sibling pane sees the finding at its next
//     SessionStart (the digest is already injected by session_start_hub Hook 13).
//
// CHEAP: a Stop fires every turn-end. This hook does a pure-fs check for the
// staging file FIRST and only spawns python when there is something to drain --
// 99% of Stops return {continue:true} with zero subprocess cost.
//
// FAIL-OPEN ABSOLUTE: any error (no python, bad payload, timeout) -> {continue:true}.
// A findings commit must NEVER block a Stop event. The bus + staging content is
// PP/agent-authored findings text; publish_session_findings writes only topic/claim/
// evidence the agent chose to stage -> no raw-secret egress surface here.
//
// REGISTRATION (Owner-side -- HR-001: auto-mode denies settings.json hook
// self-registration): add to ~/.claude/settings.json "hooks":
//   { "Stop": [ { "hooks": [ { "type": "command",
//     "command": "node \"<PP>/hooks/pm03_publish_stop.js\"" } ] } ] }
// (or add this file to hook-dispatcher.js CHAIN_MAP Stop array), Copy-Item the
// canonical hooks -> ~/.claude/hooks/, then /restart. Until then it is inert.
// ---------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const PP_PATH = path.resolve(__dirname, '..');
const BUS_PY = path.join(PP_PATH, 'modules', 'parallel_mesh', 'pm_03_bus.py');
const PYTHON_EXE =
  'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const EXEC_TIMEOUT_MS = 8000;

function emit(obj) {
  try { process.stdout.write(JSON.stringify(obj)); } catch (e) { void e; }
}

function pythonExe() {
  try { if (fs.existsSync(PYTHON_EXE)) return PYTHON_EXE; } catch (e) { void e; }
  return 'python';
}

// Mirror pm_03_bus._enc (non-alnum -> '-') so we can locate the staging file in
// pure JS and skip spawning python when there is nothing to commit.
function enc(s) { return String(s || '').replace(/[^a-zA-Z0-9]/g, '-'); }

function stagingHasContent(repo, sid) {
  try {
    const p = path.join(os.homedir(), '.claude', 'state', 'parallel_mesh',
      `session_findings_staging_${enc(repo)}_${enc(sid)}.jsonl`);
    return fs.existsSync(p) && fs.statSync(p).size > 0;
  } catch (e) { void e; return false; }
}

function main() {
  let payload = {};
  try { payload = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); }
  catch (e) { void e; emit({ continue: true }); return; }

  const cwd = payload.cwd || process.cwd();
  const sid = payload.session_id || payload.sessionId || '';

  if (!sid || !stagingHasContent(cwd, sid)) { emit({ continue: true }); return; }

  try {
    execFileSync(pythonExe(),
      [BUS_PY, '--repo', cwd, '--sid', sid, '--drain'], {
        timeout: EXEC_TIMEOUT_MS,
        encoding: 'utf8',
        stdio: ['ignore', 'ignore', 'ignore'],
        windowsHide: true,
      });
  } catch (e) { void e; }   // fail-open: a commit failure never blocks Stop

  emit({ continue: true });
}

main();
