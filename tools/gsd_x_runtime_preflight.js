#!/usr/bin/env node
/**
 * gsd_x_runtime_preflight.js -- answer, BEFORE activation, whether this host can
 * actually run what a capability manifest declares it needs.
 *
 * WHY THIS EXISTS. The manifest used to declare its shell requirement as prose in
 * `runtimeCompat.notes`. Prose is not a check: nothing reads it, nothing fails on
 * it, and a capability whose prerequisite is documented is indistinguishable from
 * one whose prerequisite holds. The consequence here is not cosmetic -- gsd-core
 * maps ANY non-zero exit from a `command-exit-zero` predicate to `block: true`
 * (gate-predicate-evaluator.cjs:94-102), so a missing runtime does not surface as
 * "I could not run"; it surfaces as a domain verdict that halts every ship.
 *
 * THE THREE QUESTIONS, KEPT APART. A pass on one is not a pass on another:
 *   A. can the executable be RESOLVED?      -> resolveExecutableBinary
 *   B. does it actually EXECUTE here?       -> execTool + a trivial probe
 *   C. does the command mean what we think? -> NOT this tool's job; that is the
 *      gate's own semantic check, and it cannot even be asked until B holds.
 * B is AUTHORITATIVE and A is DIAGNOSTIC. They genuinely disagree by design: on
 * POSIX `execTool` passes the bare name to spawnSync and lets libuv search PATH,
 * while `resolveExecutableBinary` answers existence separately -- so deciding on
 * A would report a working POSIX host as broken.
 *
 * FOUR OUTCOMES, NOT TWO. A verifier that cannot say "I could not judge this"
 * eventually says SATISFIED about nothing:
 *   SATISFIED    -- probed, and it ran
 *   UNMET        -- probed, and it did not
 *   UNMEASURABLE -- the instrument itself failed (gsd-core absent, manifest
 *                   unreadable, unknown requirement kind)
 * UNMEASURABLE OUTRANKS UNMET in the aggregate, because a run that could not
 * measure proves nothing about what it did not reach -- including the
 * requirements it never got to.
 *
 * Read-only. It never installs, activates, consents, writes or ships.
 *
 * Exit: 0 SATISFIED | 1 UNMET | 2 UNMEASURABLE (instrument failure)
 * Usage: node tools/gsd_x_runtime_preflight.js [--manifest <path>] [--json]
 *        [--gsd-lib <dir>]   (test seam: point the probe at a different surface)
 */
'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_GSD_LIB = 'C:/Users/User/.claude/gsd-core/bin/lib';
const DEFAULT_MANIFEST = path.join(
  __dirname, '..', 'capabilities', 'cpp-gsd-x-mission', 'capability.json'
);

const SATISFIED = 'SATISFIED';
const UNMET = 'UNMET';
const UNMEASURABLE = 'UNMEASURABLE';

const EXIT = { [SATISFIED]: 0, [UNMET]: 1, [UNMEASURABLE]: 2 };

/** Spawn-level "the program was not there", as distinct from "it ran and said no". */
function isNotFound(probe) {
  return probe.errorCode === 'ENOENT' || probe.exitCode === 127;
}

/**
 * Probe ONE requirement. Never throws: an unanticipated shape is UNMEASURABLE for
 * that requirement alone, so one bad entry cannot take down the whole verdict and
 * silently leave the rest unjudged.
 */
function probeRequirement(req, surface) {
  const base = { id: req && req.id, kind: req && req.kind };
  try {
    if (!req || typeof req !== 'object' || !req.id) {
      return { ...base, state: UNMEASURABLE, why: 'malformed requirement entry' };
    }

    if (req.kind === 'file') {
      if (typeof req.path !== 'string' || req.path.length === 0) {
        return { ...base, state: UNMEASURABLE, why: 'file requirement has no "path"' };
      }
      const exists = fs.existsSync(req.path);
      return {
        ...base,
        state: exists ? SATISFIED : UNMET,
        target: req.path,
        why: exists ? 'file exists' : 'file does not exist',
      };
    }

    if (req.kind === 'executable') {
      if (typeof req.name !== 'string' || req.name.length === 0) {
        return { ...base, state: UNMEASURABLE, why: 'executable requirement has no "name"' };
      }
      // A -- diagnostic only.
      let resolved = null;
      try {
        resolved = surface.resolveExecutableBinary(req.name);
      } catch (e) {
        resolved = null;
      }
      // B -- authoritative.
      const args = Array.isArray(req.probeArgs) ? req.probeArgs : ['--version'];
      const r = surface.execTool(req.name, args, { timeout: 15000 });
      const probe = {
        exitCode: r.exitCode,
        errorCode: r.error && r.error.code ? r.error.code : null,
        stderr: String(r.stderr || '').slice(0, 200),
      };
      if (probe.exitCode === 0) {
        return { ...base, state: SATISFIED, resolved, probe, why: 'probe exited 0' };
      }
      return {
        ...base,
        state: UNMET,
        resolved,
        probe,
        why: isNotFound(probe)
          ? `not executable here: ${req.name} could not be started`
          : `probe exited ${probe.exitCode}`,
      };
    }

    return { ...base, state: UNMEASURABLE, why: `unknown requirement kind: ${String(req.kind)}` };
  } catch (e) {
    return { ...base, state: UNMEASURABLE, why: `probe threw: ${e && e.message}` };
  }
}

/** UNMEASURABLE outranks UNMET outranks SATISFIED. */
function aggregate(results) {
  if (results.some((r) => r.state === UNMEASURABLE)) return UNMEASURABLE;
  if (results.some((r) => r.state === UNMET)) return UNMET;
  return SATISFIED;
}

function loadSurface(libDir) {
  const p = path.join(libDir, 'shell-command-projection.cjs');
  if (!fs.existsSync(p)) {
    const e = new Error(`gsd-core surface not found at ${p}`);
    e.unmeasurable = true;
    throw e;
  }
  const mod = require(p);
  for (const fn of ['resolveExecutableBinary', 'execTool']) {
    if (typeof mod[fn] !== 'function') {
      const e = new Error(`gsd-core surface is missing ${fn}`);
      e.unmeasurable = true;
      throw e;
    }
  }
  return mod;
}

function run(opts = {}) {
  const manifestPath = opts.manifest || DEFAULT_MANIFEST;
  const libDir = opts.gsdLib || DEFAULT_GSD_LIB;

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (e) {
    return {
      verdict: UNMEASURABLE,
      why: `manifest unreadable: ${e && e.message}`,
      manifest: manifestPath,
      results: [],
    };
  }

  const block = manifest.runtimeRequirements;
  const reqs = block && Array.isArray(block.requirements) ? block.requirements : null;

  // A manifest that declares nothing is NOT "satisfied" -- it is a manifest that
  // was never asked the question. Say so rather than answering for it.
  if (!reqs) {
    return {
      verdict: UNMEASURABLE,
      why: 'manifest declares no runtimeRequirements.requirements[]',
      manifest: manifestPath,
      results: [],
    };
  }
  if (reqs.length === 0) {
    return {
      verdict: UNMEASURABLE,
      why: 'runtimeRequirements.requirements[] is empty',
      manifest: manifestPath,
      results: [],
    };
  }

  let surface;
  try {
    surface = loadSurface(libDir);
  } catch (e) {
    return {
      verdict: UNMEASURABLE,
      why: e.message,
      manifest: manifestPath,
      results: [],
    };
  }

  const results = reqs.map((r) => probeRequirement(r, surface));
  return {
    verdict: aggregate(results),
    onUnmet: block.onUnmet || 'refuse-activation',
    manifest: manifestPath,
    gsdLib: libDir,
    results,
  };
}

function main(argv) {
  const opts = {};
  let json = false;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--manifest') opts.manifest = argv[++i];
    else if (argv[i] === '--gsd-lib') opts.gsdLib = argv[++i];
    else if (argv[i] === '--json') json = true;
  }

  const out = run(opts);

  if (json) {
    console.log(JSON.stringify(out, null, 2));
  } else {
    for (const r of out.results) {
      const target = r.target || (r.probe ? `resolved=${r.resolved}` : '');
      console.log(`${r.state.padEnd(12)} ${String(r.id).padEnd(20)} ${r.why}${target ? '  [' + target + ']' : ''}`);
    }
    console.log(`PREFLIGHT=${out.verdict}${out.why ? '  (' + out.why + ')' : ''}`);
    if (out.verdict === UNMET) {
      console.log(
        `REFUSE-ACTIVATION: do not set the activation key on this host. An unmet runtime does not `
        + `surface as "could not run" -- gsd-core maps it to block:true, which halts every ship.`
      );
    }
    if (out.verdict === UNMEASURABLE) {
      console.log(
        `NOT A FINDING ABOUT THE HOST: the instrument failed, so nothing was judged. `
        + `Fix the instrument before reading this as a pass or a fail.`
      );
    }
  }

  return EXIT[out.verdict];
}

if (require.main === module) {
  process.exit(main(process.argv.slice(2)));
}

module.exports = { run, probeRequirement, aggregate, SATISFIED, UNMET, UNMEASURABLE, EXIT };
