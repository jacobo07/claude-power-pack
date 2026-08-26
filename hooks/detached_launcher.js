/**
 * detached_launcher.js -- spawn the hub's fire-and-forget children from ONE
 * child process instead of twelve from the hub itself.
 *
 * WHY THIS EXISTS. session_start_hub folded four SessionStart node cold
 * starts into one (T-NODE-COLD-001) and then spawned twelve detached
 * children of its own, on the premise -- written into its comments -- that
 * a detached child "never adds to the hub's wall time". Detaching removes
 * the child's RUN time from the parent. It does not remove CreateProcess,
 * which the parent pays synchronously, once per child.
 *
 * Ablation on the real hub, spawn() neutered and nothing else changed:
 *
 *     with spawns     669 / 775 / 829 ms   (spread 160 ms)
 *     spawns removed  287 / 290 / 293 ms   (spread   6 ms)
 *
 * So eleven detached children cost the hub ~485 ms of its own wall time,
 * and every bit of the run-to-run variance came in through process
 * creation. The hub applied the fold to its parents and never to its
 * children.
 *
 * CONTRACT. argv[2] is a path to a JSON array of specs:
 *
 *     { label, cmd, args, envDelta, log }
 *
 * envDelta is a sparse overlay on this process's env (the hub passes only
 * the keys that differ, so the spec stays small); log, when present, is a
 * file both stdout and stderr are written to, matching the hub's
 * detachedSpawnLogged behaviour.
 *
 * Every child is independent: one bad spec must not cost the other eleven,
 * so each spawn is individually guarded. The spec file is removed after
 * reading -- it is a handoff, not state.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const LOG = path.join(os.tmpdir(), 'pp-session-hub.log');

function note(msg) {
  try {
    fs.appendFileSync(
      LOG, `[${new Date().toISOString()}] launcher: ${msg}\n`, 'utf8');
  } catch (_e) { /* logging must never be the reason a hook dies */ }
}

function launch(spec) {
  const label = (spec && spec.label) || '?';
  try {
    if (!spec || typeof spec.cmd !== 'string' || !Array.isArray(spec.args)) {
      note(`SKIP ${label} (malformed spec)`);
      return false;
    }
    const env = Object.assign({}, process.env, spec.envDelta || {});
    const opts = {
      detached: true,
      env,
      cwd: spec.cwd || process.cwd(),
      windowsHide: true,
      stdio: 'ignore',
    };
    let fd = null;
    if (spec.log) {
      // Failing to open the log must not cancel the child; it only costs
      // the on-disk evidence, and a hook that runs without a log beats a
      // hook that does not run.
      try {
        fs.mkdirSync(path.dirname(spec.log), { recursive: true });
        fd = fs.openSync(spec.log, 'w');
        opts.stdio = ['ignore', fd, fd];
      } catch (logErr) {
        note(`${label} log unavailable (${logErr.message}); stdio ignored`);
      }
    }
    const child = spawn(spec.cmd, spec.args, opts);
    child.unref();
    if (fd !== null) {
      try { fs.closeSync(fd); } catch (_e) { /* child holds its own dup */ }
    }
    note(`SPAWNED ${label} pid=${child.pid || '?'}`);
    return true;
  } catch (err) {
    note(`FAILED ${label}: ${err && err.message}`);
    return false;
  }
}

function main() {
  const specPath = process.argv[2];
  if (!specPath) {
    note('no spec path in argv; nothing to do');
    return;
  }
  let specs;
  try {
    specs = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  } catch (err) {
    note(`unreadable spec ${specPath}: ${err && err.message}`);
    return;
  }
  try { fs.unlinkSync(specPath); } catch (_e) { /* best effort */ }

  if (!Array.isArray(specs)) {
    note('spec is not an array');
    return;
  }
  let ok = 0;
  for (const spec of specs) {
    if (launch(spec)) ok++;
  }
  note(`launched ${ok}/${specs.length}`);
}

if (require.main === module) {
  main();
}

module.exports = { launch, main };
