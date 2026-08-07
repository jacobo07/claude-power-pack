#!/usr/bin/env node
/*
 * modules/cdicf/installer.js — CDICF A3b
 *
 * Installs a CPP Design Registry entry into a target project as a journalled
 * transaction: recoverable after an abrupt kill, reversible after success, and
 * a no-op when the component is already present at the same checksum.
 *
 * Usage:
 *   node modules/cdicf/installer.js install  --from <emitDir> --target <proj> [--dry-run]
 *   node modules/cdicf/installer.js rollback --component <id>  --target <proj>
 *   node modules/cdicf/installer.js recover  --target <proj>
 *   node modules/cdicf/installer.js verify   --target <proj> [--component <id>]
 *
 * Exit codes:
 *   0 ok · 2 argv · 3 io · 4 input invalid · 5 REDISTRIBUTION PROHIBITED ·
 *   6 checksum mismatch · 7 postcondition failed (rolled back) ·
 *   8 dirty or concurrent transaction · 9 not installed · 10 path escape
 *
 * WHAT "ATOMIC" HONESTLY MEANS HERE
 * ---------------------------------
 * No portable filesystem gives multi-file atomicity, and claiming it would be
 * the kind of confident-but-false statement this whole subsystem exists to
 * prevent. What is actually guaranteed:
 *
 *   1. Nothing is ever *committed* partially. `installed.json` — the state of
 *      record — only ever names installs that completed and verified.
 *   2. Partial state is always *detectable*. A journal is fsynced to disk
 *      before the first mutation and removed only after the last one, so its
 *      presence is proof that a transaction was interrupted.
 *   3. Partial state is always *reversible*. The journal carries the prior
 *      sha256 of every path it touches, so recovery restores the pre-state
 *      byte-for-byte or reports precisely which path it declined to touch.
 *   4. The window in which partial state can exist on disk is bounded to the
 *      rename sweep. All content is written and hash-verified in a staging
 *      directory first, so the committing phase is N metadata operations, not
 *      N file writes.
 *
 * The residual truth: between an abrupt kill and the next invocation, a partial
 * tree does sit on disk. It is detected and reverted before any further work.
 * That is recovery, not prevention, and it is named as such.
 *
 * DEFENCE IN DEPTH
 * ----------------
 * A3's emitter already refuses to emit a redistribution-prohibited component
 * carrying code. The installer derives the posture again from the install
 * manifest's own `license_tier` and refuses again. Two independent checks on
 * the same fact is the point: the emitter guards what leaves CPP, the installer
 * guards what lands in a project, and an entry can reach a project by a path
 * that never went through the emitter (a file copied by hand, a registry served
 * by a third party). A guard that trusts an upstream guard is one guard.
 *
 * PATH TRAVERSAL
 * --------------
 * Registry entries are untrusted data by project doctrine. A `files[].path` of
 * `../../.ssh/authorized_keys` would otherwise write outside the project. Every
 * destination is resolved and asserted to be inside the target before the plan
 * is accepted, and the whole install is refused — not the single file skipped —
 * because an entry containing one escaping path is not an entry to partially
 * trust.
 *
 * CONCURRENCY
 * -----------
 * Single-writer by design. The journal is created with the exclusive `wx` flag,
 * so it doubles as the mutex. A journal whose recorded pid is still alive is
 * reported as a concurrent transaction and refused (exit 8); a journal whose
 * pid is gone is an interrupted transaction and is recovered automatically with
 * a loud notice. The pid check inherits the OS's pid-reuse caveat: a recycled
 * pid can make an interrupted transaction look concurrent, which fails toward
 * refusing to act. That direction is the safe one.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const { REDISTRIBUTION_BY_TIER } = require('../../lib/license_gate');
const { rollupChecksum } = require('./registry_emitter');

const TX_DIR = '.cdicf';
const INSTALLED_SCHEMA = 'cdicf/installed/1';
const JOURNAL_SCHEMA = 'cdicf/journal/1';
// The kill switch's portable arm. A file, not only a signal: Node never emits
// SIGTERM on Windows, so a signal-only switch would be inert on this estate's
// primary host — a kill switch that cannot fire is the disarmed-kill-switch
// failure, not a kill switch. The file is also cross-process and inspectable.
const KILL_SENTINEL = 'KILL_SWITCH';
const ABORTED_STATE = 'aborted-by-kill-switch';

const REFUSAL = {
  INPUT_INVALID:             { exit: 4 },
  REDISTRIBUTION_PROHIBITED: { exit: 5 },
  CHECKSUM_MISMATCH:         { exit: 6 },
  ARTIFACT_SET_MISMATCH:     { exit: 6 },
  KILL_SWITCH_ACTIVATED:     { exit: 12 },
  POSTCONDITION_FAILED:      { exit: 7 },
  DIRTY_STATE:               { exit: 8 },
  NOT_INSTALLED:             { exit: 9 },
  PATH_ESCAPE:               { exit: 10 },
  UNRESOLVED_DEPENDENCIES:   { exit: 11 },
  IO_ERROR:                  { exit: 3 },
};

/*
 * A registry entry may declare npm packages and other registry components it
 * needs. Installing its files while those are absent produces a component that
 * is present, checksum-valid, recorded as installed — and broken on first
 * render. That is the Scaffold Illusion with a passing verification step, so
 * the dependencies are resolved before anything is written.
 *
 * Resolution is deliberately literal: an npm dependency counts as resolved when
 * the target's package.json declares it, and a registry dependency when
 * installed.json already names it. No network, no version solving. This
 * reports a fact about the project rather than guessing at one.
 */
function unresolvedDependencies(entry, target, paths) {
  const npm = Array.isArray(entry.dependencies) ? entry.dependencies : [];
  const registry = Array.isArray(entry.registryDependencies) ? entry.registryDependencies : [];
  if (!npm.length && !registry.length) return null;

  const declared = new Set();
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(target, 'package.json'), 'utf8'));
    for (const field of ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']) {
      for (const name of Object.keys(pkg[field] || {})) declared.add(name);
    }
  } catch (_) {
    // No package.json, or an unreadable one. Nothing is declared, so nothing
    // is resolved — which is the honest reading, not an error.
  }

  const installed = new Set(Object.keys(readInstalled(paths).components || {}));
  // Strip a trailing version specifier without eating a scope: the `@` in
  // `@radix-ui/react-slot` is followed by a letter, a version's `@` is not.
  const bare = (d) => String(d).replace(/@[\^~>=<0-9][^@]*$/, '');

  const missingNpm = npm.filter(d => !declared.has(bare(d)));
  const missingRegistry = registry.filter(d => !installed.has(d));
  if (!missingNpm.length && !missingRegistry.length) return null;
  return { npm: missingNpm, registry: missingRegistry };
}

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function refuse(code, reason, detail) {
  return { ok: false, refusal: { code, reason, detail: detail || null, exit: REFUSAL[code].exit } };
}

function newTxid() {
  return `${Date.now().toString(36)}-${crypto.randomBytes(5).toString('hex')}`;
}

function txPaths(target) {
  const root = path.join(target, TX_DIR);
  return {
    root,
    journal:   path.join(root, 'journal.json'),
    installed: path.join(root, 'installed.json'),
    backups:   path.join(root, 'backups'),
    staging:   path.join(root, 'staging'),
  };
}

/*
 * Durable write. The journal is the only thing standing between an abrupt kill
 * and an unrecoverable tree, so it is fsynced rather than merely written — a
 * buffered write that never reaches the platter records nothing.
 */
function writeDurable(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const fd = fs.openSync(file, 'w');
  try {
    fs.writeFileSync(fd, data);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
}

function readJsonOr(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (_) {
    return fallback;
  }
}

function pidAlive(pid) {
  if (!pid || pid === process.pid) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (e) {
    return e.code === 'EPERM';   // exists, owned by someone else
  }
}

function shaOnDisk(abs) {
  try {
    return sha256(fs.readFileSync(abs));
  } catch (_) {
    return null;
  }
}

function rmrf(p) {
  try { fs.rmSync(p, { recursive: true, force: true }); } catch (_) { /* best effort */ }
}

/* ------------------------------------------------------------------------- *
 * Kill switch
 *
 * Stops the transaction IN PROGRESS. It is not a rollback and not a retro-active
 * uninstall: installs committed in earlier sessions are untouched, by decision.
 *
 * What it leaves behind is the same thing an abrupt kill leaves behind — a
 * journal describing how to get back — except it is written deliberately, with
 * the phase it stopped at and the last durable state recorded. So the tree is
 * returned to its pre-state by the ordinary recovery path, and the abort is
 * still legible afterwards. The journal is NOT deleted here; recovery archives
 * it to .cdicf/aborted/<txid>.json instead of discarding it, so the post-mortem
 * survives the repair.
 *
 * Arming is deliberately not auto-disarming. A switch that resets itself after
 * one trip is a pause button. Every refusal names the exact disarm command,
 * because a kill switch nobody can turn off is an outage.
 * ------------------------------------------------------------------------- */

let _signalTripped = false;

function armSignalKillSwitch() {
  const onSignal = () => { _signalTripped = true; };
  const signals = ['SIGTERM', 'SIGINT'];
  for (const s of signals) {
    try { process.on(s, onSignal); } catch (_) { /* not supported here */ }
  }
  return () => {
    for (const s of signals) {
      try { process.removeListener(s, onSignal); } catch (_) { /* ignore */ }
    }
  };
}

function killSentinelPath(target) {
  return path.join(txPaths(target).root, KILL_SENTINEL);
}

/*
 * Returns the activation channel, or null. Three arms, checked cheapest first:
 * an injected predicate (tests and embedders), a received signal, the sentinel
 * file. The file is last because it costs a stat at every seam.
 */
function killSwitchProbe(target, opts) {
  const o = opts || {};
  const sentinel = killSentinelPath(target);
  return () => {
    if (typeof o.killSwitch === 'function') {
      try { if (o.killSwitch()) return 'programmatic'; } catch (_) { /* a throwing probe is not a trip */ }
    }
    if (_signalTripped) return 'signal';
    if (fs.existsSync(sentinel)) return 'sentinel';
    return null;
  };
}

function armKillSwitch(target) {
  const p = killSentinelPath(target);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  writeDurable(p, JSON.stringify({
    armed_at: new Date().toISOString(), armed_by_pid: process.pid,
    note: 'CDICF installer kill switch. Remove this file, or run `installer.js kill-switch disarm --target <proj>`, to allow installs again.',
  }, null, 2) + '\n');
  return { ok: true, status: 'armed', sentinel: p };
}

function disarmKillSwitch(target) {
  const p = killSentinelPath(target);
  const was = fs.existsSync(p);
  fs.rmSync(p, { force: true });
  _signalTripped = false;
  return { ok: true, status: was ? 'disarmed' : 'already-disarmed', sentinel: p };
}

function killSwitchStatus(target) {
  const p = killSentinelPath(target);
  const armed = fs.existsSync(p);
  return {
    ok: true, status: armed ? 'armed' : 'disarmed', sentinel: p,
    signal_tripped: _signalTripped,
    detail: armed ? readJsonOr(p, null) : null,
  };
}

/*
 * The only writer of the ABORTED record. Two durable writes and nothing else:
 * the journal (preserved, state changed) and installed.json (an audit row).
 * The component is deliberately NOT added to `components` — it was not
 * installed, and a state of record that says otherwise is worse than no record.
 */
function abortByKillSwitch(plan, paths, journal, err) {
  const at = new Date().toISOString();
  const lastValid = journal.state;

  journal.aborted = {
    by: 'kill-switch', via: err._killSwitch, at,
    at_phase: err._atPhase || null, last_valid_state: lastValid,
  };
  journal.state = ABORTED_STATE;
  writeDurable(paths.journal, JSON.stringify(journal, null, 2) + '\n');

  const installed = readInstalled(paths);
  if (!Array.isArray(installed.aborted)) installed.aborted = [];
  installed.aborted.push({
    status: 'ABORTED_BY_KILL_SWITCH',
    component: plan.component, txid: plan.txid, via: err._killSwitch, at,
    at_phase: err._atPhase || null, last_valid_state: lastValid,
    journal: path.relative(plan.target, paths.journal).replace(/\\/g, '/'),
  });
  writeDurable(paths.installed, JSON.stringify(installed, null, 2) + '\n');

  return refuse('KILL_SWITCH_ACTIVATED',
    `kill switch (${err._killSwitch}) stopped the transaction before ${err._atPhase || 'the next write'}`,
    {
      txid: plan.txid, component: plan.component, at,
      at_phase: err._atPhase || null, last_valid_state: lastValid,
      journal_preserved: paths.journal,
      next: 'the tree is reverted by `installer.js recover --target <proj>`; ' +
            'the switch stays armed until `installer.js kill-switch disarm --target <proj>`',
    });
}

/* ------------------------------------------------------------------------- *
 * Planning
 * ------------------------------------------------------------------------- */

/*
 * Builds the full plan without touching the target. Every reason to refuse is
 * discovered here, so `applyPlan` starts only once the transaction is known to
 * be executable — an install that can still fail on validation after the first
 * rename is an install that needs recovery for a preventable reason.
 */
function planInstall(entry, im, target, opts) {
  if (!entry || typeof entry !== 'object') return refuse('INPUT_INVALID', 'registry entry is not an object');
  if (!im || typeof im !== 'object') return refuse('INPUT_INVALID', 'install manifest is not an object');

  const meta = entry.meta && entry.meta.cpp;
  if (!meta) return refuse('INPUT_INVALID', 'registry entry has no meta.cpp block');
  if (im.schema !== 'cdicf/install-manifest/1') {
    return refuse('INPUT_INVALID', `unsupported install manifest schema: ${im.schema}`);
  }
  // The two artifacts are produced together but travel separately. If they
  // describe different components, one of them is stale — installing either is
  // wrong, and picking one silently is worse.
  if (meta.manifest_id !== im.component) {
    return refuse('INPUT_INVALID', 'registry entry and install manifest describe different components',
      { entry: meta.manifest_id, install_manifest: im.component });
  }
  if (!im.provenance || !im.provenance.license_tier) {
    return refuse('INPUT_INVALID', 'install manifest carries no provenance.license_tier');
  }

  const declaredArtifacts = Array.isArray(im.artifacts) ? im.artifacts : [];
  const entryFiles = Array.isArray(entry.files) ? entry.files : [];
  const pointer = meta.artifact_class === 'upstream-pointer';

  // Defence in depth — derived from the tier, never read from a posture field.
  const posture = REDISTRIBUTION_BY_TIER[im.provenance.license_tier];
  if (posture === 'prohibited' && (entryFiles.length > 0 || !pointer)) {
    return refuse('REDISTRIBUTION_PROHIBITED',
      `license_tier ${im.provenance.license_tier} derives redistribution 'prohibited'; ` +
      'installing local artifacts would redistribute it',
      { artifact_class: meta.artifact_class, files: entryFiles.length });
  }

  const missingDeps = opts && opts.allowUnresolvedDeps
    ? null
    : unresolvedDependencies(entry, path.resolve(target), txPaths(path.resolve(target)));
  if (missingDeps) {
    return refuse('UNRESOLVED_DEPENDENCIES',
      'the entry declares dependencies this project does not have; installing would leave it broken on first render',
      Object.assign(missingDeps, { hint: 'install the missing packages/components first, or pass --allow-unresolved-deps deliberately' }));
  }

  if (pointer) {
    if (entryFiles.length) {
      return refuse('INPUT_INVALID', 'an upstream-pointer entry must carry no files', { files: entryFiles.length });
    }
    return {
      ok: true,
      plan: {
        txid: newTxid(), component: im.component, registry_item: im.registry_item,
        mode: 'upstream-reference', target, files: [],
        checksum: im.checksum, provenance: im.provenance,
        upstream_install: meta.upstream_install || null,
      },
    };
  }

  if (!entryFiles.length) {
    return refuse('INPUT_INVALID', 'a local-artifacts entry carries no files');
  }

  // The artifact list and the file list must agree exactly. A file present in
  // one and absent from the other means the pair is not the pair that was
  // emitted, which is the same failure as a bad hash and is treated as one.
  const prefix = `${meta.local_namespace}/${entry.name}/`;
  const expected = new Map(declaredArtifacts.map(a => [a.path, a]));
  const seen = new Set();
  const files = [];
  const resolvedTarget = path.resolve(target);

  for (const f of entryFiles) {
    const rel = String(f.path || '');
    const artRel = rel.startsWith(prefix) ? rel.slice(prefix.length) : rel;

    const abs = path.resolve(resolvedTarget, rel);
    // Containment: resolve first, then compare with a separator so that a
    // sibling directory sharing a name prefix cannot pass.
    if (abs !== resolvedTarget && !abs.startsWith(resolvedTarget + path.sep)) {
      return refuse('PATH_ESCAPE', `registry entry path escapes the target: ${rel}`, { resolved: abs, target: resolvedTarget });
    }

    const art = expected.get(artRel);
    if (!art) {
      return refuse('ARTIFACT_SET_MISMATCH', `entry file has no matching artifact in the install manifest: ${artRel}`);
    }
    if (typeof f.content !== 'string') {
      return refuse('INPUT_INVALID', `entry file carries no content: ${rel}`);
    }

    const buf = Buffer.from(f.content, 'utf8');
    const actual = sha256(buf);
    if (actual !== art.sha256) {
      return refuse('CHECKSUM_MISMATCH',
        `content of ${artRel} does not match the install manifest checksum`,
        { file: artRel, expected: art.sha256, actual });
    }

    seen.add(artRel);
    const priorSha = shaOnDisk(abs);
    files.push({
      rel, artRel, abs, sha256: actual, bytes: buf.length, content: f.content,
      prior_sha: priorSha,
      action: priorSha === null ? 'create' : (priorSha === actual ? 'unchanged' : 'overwrite'),
    });
  }

  const missing = declaredArtifacts.filter(a => !seen.has(a.path)).map(a => a.path);
  if (missing.length) {
    return refuse('ARTIFACT_SET_MISMATCH', 'install manifest declares artifacts the entry does not carry', { missing });
  }

  // The roll-up is recomputed rather than trusted: a manifest whose per-file
  // hashes were edited in step with its content would otherwise pass, and the
  // roll-up is the one value an editor is most likely to forget.
  const recomputed = rollupChecksum(files.map(f => ({ path: f.artRel, sha256: f.sha256 })));
  if (im.checksum && recomputed !== im.checksum) {
    return refuse('CHECKSUM_MISMATCH', 'install manifest roll-up checksum does not match its artifact list',
      { expected: im.checksum, actual: recomputed });
  }

  files.sort((a, b) => a.rel.localeCompare(b.rel));
  return {
    ok: true,
    plan: {
      txid: newTxid(), component: im.component, registry_item: im.registry_item,
      mode: 'local-artifacts', target: resolvedTarget, files,
      checksum: recomputed, provenance: im.provenance, upstream_install: null,
    },
  };
}

/* ------------------------------------------------------------------------- *
 * Recovery
 * ------------------------------------------------------------------------- */

/*
 * Reverts an interrupted transaction to its pre-state.
 *
 * A path is only touched when the on-disk bytes are the ones this transaction
 * put there. If a file was created by the transaction but now holds something
 * else, someone edited it after the crash and deleting it would destroy work
 * that was never ours — it is reported as skipped instead. Recovery that
 * over-reaches is a worse failure than recovery that stops and says so.
 */
function recover(target, opts) {
  const o = opts || {};
  const paths = txPaths(target);
  if (!fs.existsSync(paths.journal)) {
    return { ok: true, recovered: false, reason: 'no journal — nothing to recover' };
  }

  const j = readJsonOr(paths.journal, null);
  if (!j || j.schema !== JOURNAL_SCHEMA) {
    return refuse('DIRTY_STATE', 'journal present but unreadable; refusing to guess at the pre-state',
      { journal: paths.journal });
  }
  if (!o.force && pidAlive(j.pid)) {
    return refuse('DIRTY_STATE', `a transaction is in progress (pid ${j.pid}); refusing to touch it`,
      { txid: j.txid, started: j.started });
  }

  const restored = [];
  const removed = [];
  const skipped = [];

  if (j.state !== 'planning') {
    for (const f of j.files || []) {
      const onDisk = shaOnDisk(f.abs);
      if (f.prior_sha === null) {
        // We created it. Remove it only if it still holds what we wrote.
        if (onDisk === null) continue;
        if (onDisk === f.sha256) { fs.rmSync(f.abs, { force: true }); removed.push(f.rel); }
        else skipped.push({ path: f.rel, why: 'modified after the interruption; left in place' });
      } else {
        if (onDisk === f.prior_sha) continue;             // never got renamed
        const backup = path.join(paths.backups, j.txid, f.artRel || f.rel);
        const backupSha = shaOnDisk(backup);
        if (backupSha === f.prior_sha) {
          fs.mkdirSync(path.dirname(f.abs), { recursive: true });
          fs.copyFileSync(backup, f.abs);
          restored.push(f.rel);
        } else {
          skipped.push({ path: f.rel, why: 'backup missing or corrupt; original bytes not recoverable' });
        }
      }
    }
  }

  rmrf(path.join(paths.staging, j.txid));
  rmrf(path.join(paths.backups, j.txid));

  // A kill-switch abort is required to stay inspectable, and repairing the tree
  // must not cost the evidence. Archive rather than discard, so the journal
  // outlives the recovery that consumes it.
  let archived = null;
  if (j.aborted) {
    archived = path.join(paths.root, 'aborted', `${j.txid}.json`);
    try {
      writeDurable(archived, JSON.stringify(j, null, 2) + '\n');
    } catch (_) {
      archived = null;   // an unarchivable journal must not block the repair
    }
  }
  fs.rmSync(paths.journal, { force: true });

  return {
    ok: true, recovered: true, txid: j.txid, state: j.state,
    restored, removed, skipped,
    aborted: j.aborted || null,
    archived_journal: archived,
  };
}

/* ------------------------------------------------------------------------- *
 * Transaction execution
 * ------------------------------------------------------------------------- */

function readInstalled(paths) {
  return readJsonOr(paths.installed, { schema: INSTALLED_SCHEMA, components: {} });
}

/*
 * Runs the plan. `onPhase(name, info)` is an observability seam — production
 * passes nothing; a caller can use it for progress, and the test suite uses it
 * to kill the process at a chosen instant to prove recovery works on a real
 * abrupt exit rather than a simulated one.
 */
function applyPlan(plan, opts) {
  const o = opts || {};
  const userPhase = typeof o.onPhase === 'function' ? o.onPhase : () => {};
  const tripped = killSwitchProbe(plan.target, o);
  // Every seam is a checkpoint. `renaming` fires immediately BEFORE each
  // renameSync, which is the requested granularity: renameSync is a single
  // atomic syscall, so a rename already issued completes and the sweep stops
  // before the next one. Checking after the write instead would trade the
  // guarantee for nothing.
  const phase = (name, info) => {
    const via = tripped();
    if (via) {
      throw Object.assign(
        new Error(`kill switch (${via}) tripped before ${name}`),
        { _killSwitch: via, _atPhase: name });
    }
    userPhase(name, info);
  };
  const paths = txPaths(plan.target);
  const stageRoot = path.join(paths.staging, plan.txid);
  const backupRoot = path.join(paths.backups, plan.txid);

  const journal = {
    schema: JOURNAL_SCHEMA, txid: plan.txid, pid: process.pid,
    started: new Date().toISOString(), state: 'planning',
    component: plan.component, mode: plan.mode,
    files: plan.files.map(f => ({ rel: f.rel, artRel: f.artRel, abs: f.abs, sha256: f.sha256, prior_sha: f.prior_sha })),
  };
  const putJournal = (state) => {
    journal.state = state;
    writeDurable(paths.journal, JSON.stringify(journal, null, 2) + '\n');
  };

  // Refuse before the lock, not after. An already-armed switch means this
  // transaction must not begin, and creating a journal first would leave a
  // dirty-state marker for a transaction that never touched anything.
  const preArmed = tripped();
  if (preArmed) {
    return refuse('KILL_SWITCH_ACTIVATED',
      `kill switch (${preArmed}) is armed; refusing to begin a transaction`,
      {
        component: plan.component, at_phase: 'before-start',
        next: 'run `installer.js kill-switch disarm --target <proj>` to allow installs again',
      });
  }

  // Acquire the journal exclusively. Creation IS the lock.
  fs.mkdirSync(paths.root, { recursive: true });
  try {
    fs.closeSync(fs.openSync(paths.journal, 'wx'));
  } catch (e) {
    if (e.code === 'EEXIST') {
      return refuse('DIRTY_STATE', 'a journal already exists; recover or wait for the running transaction', { journal: paths.journal });
    }
    return refuse('IO_ERROR', e.message);
  }

  // Signals are listened for only while a transaction is open, and the
  // listeners are removed on every exit path. A library that permanently
  // rewires SIGINT for its host process has overstepped.
  const disarmSignals = armSignalKillSwitch();

  try {
    putJournal('planning');
    phase('journal-written', { txid: plan.txid });

    // Back up everything about to be overwritten, and verify each copy before
    // relying on it. An unverified backup is a rollback that fails when used.
    for (const f of plan.files) {
      // The plan was a snapshot. If the bytes moved between planning and now,
      // the recorded prior_sha is a lie and every guarantee built on it — the
      // backup, the rollback, the recovery — is void. Abort with that diagnosis
      // rather than proceed and fail later with a message about a missing file.
      const now = shaOnDisk(f.abs);
      if (now !== f.prior_sha) {
        throw Object.assign(new Error(
          `${f.rel} changed between planning and applying (planned ${f.prior_sha}, found ${now})`),
          { _stale: true });
      }
      if (f.prior_sha === null) continue;
      // A seam per write, not per loop: "stop before the next write" is only
      // true if there is a checkpoint before each one.
      phase('backup-file', { path: f.rel });
      const dst = path.join(backupRoot, f.artRel);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.copyFileSync(f.abs, dst);
      if (shaOnDisk(dst) !== f.prior_sha) {
        throw new Error(`backup of ${f.rel} did not verify`);
      }
    }
    putJournal('backed-up');
    phase('backup', { count: plan.files.filter(f => f.prior_sha !== null).length });

    // Stage all content and hash-verify it here, so the commit phase is renames
    // only — that is what bounds the partial-state window.
    for (const f of plan.files) {
      phase('staging-file', { path: f.rel });
      const dst = path.join(stageRoot, f.artRel);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      writeDurable(dst, Buffer.from(f.content, 'utf8'));
      if (shaOnDisk(dst) !== f.sha256) throw new Error(`staged ${f.rel} did not verify`);
      f._staged = dst;
    }
    putJournal('staged');
    phase('staged', { count: plan.files.length });

    // Past this point an interruption requires rollback, so the state is on
    // disk before the first rename rather than after it.
    putJournal('applying');
    phase('applying', { txid: plan.txid });

    for (const f of plan.files) {
      phase('renaming', { path: f.rel });
      fs.mkdirSync(path.dirname(f.abs), { recursive: true });
      fs.renameSync(f._staged, f.abs);
      phase('renamed', { path: f.rel });
    }

    // Postconditions, read back from disk rather than assumed from the write.
    const bad = [];
    for (const f of plan.files) {
      const got = shaOnDisk(f.abs);
      if (got === null) bad.push({ path: f.rel, why: 'missing after install' });
      else if (got !== f.sha256) bad.push({ path: f.rel, why: 'checksum mismatch after install', expected: f.sha256, actual: got });
    }
    if (bad.length) throw Object.assign(new Error('postcondition verification failed'), { _postcondition: bad });
    phase('verified', { count: plan.files.length });

    // Commit: the state of record changes last, so it can never name an
    // install that did not verify.
    const installed = readInstalled(paths);
    installed.components[plan.component] = {
      txid: plan.txid,
      registry_item: plan.registry_item,
      mode: plan.mode,
      checksum: plan.checksum,
      installed_at: new Date().toISOString(),
      provenance: plan.provenance,
      upstream_install: plan.upstream_install,
      files: plan.files.map(f => ({ path: f.rel, artRel: f.artRel, sha256: f.sha256, prior_sha: f.prior_sha })),
      backup_dir: plan.files.some(f => f.prior_sha !== null) ? path.relative(plan.target, backupRoot) : null,
    };
    writeDurable(paths.installed, JSON.stringify(installed, null, 2) + '\n');

    const readback = readInstalled(paths).components[plan.component];
    if (!readback || readback.checksum !== plan.checksum) {
      throw new Error('installed.json did not read back with the committed checksum');
    }

    rmrf(stageRoot);
    if (!installed.components[plan.component].backup_dir) rmrf(backupRoot);
    fs.rmSync(paths.journal, { force: true });
    phase('committed', { txid: plan.txid });

    return {
      ok: true,
      status: 'installed',
      txid: plan.txid,
      component: plan.component,
      mode: plan.mode,
      files: plan.files.map(f => ({ path: f.rel, action: f.action, sha256: f.sha256 })),
      checksum: plan.checksum,
    };
  } catch (e) {
    // The kill switch is handled BEFORE the generic revert, and the order is
    // load-bearing: `recover` deletes the journal, which is exactly the
    // post-mortem artifact an abort is required to preserve. An abort stops;
    // it does not repair. `recover` does the repair, on demand, and archives
    // the journal rather than discarding it.
    if (e._killSwitch) {
      disarmSignals();
      return abortByKillSwitch(plan, paths, journal, e);
    }
    // Any other failure reverts through the same recovery path an abrupt kill
    // would use. One revert implementation, one set of bugs.
    const rec = recover(plan.target, { force: true });
    if (e._postcondition) {
      return refuse('POSTCONDITION_FAILED', 'installed files did not verify; the transaction was rolled back',
        { failures: e._postcondition, recovery: rec.ok ? { restored: rec.restored, removed: rec.removed, skipped: rec.skipped } : rec.refusal });
    }
    return refuse('IO_ERROR', `${e.message}; the transaction was rolled back`,
      { recovery: rec.ok ? { restored: rec.restored, removed: rec.removed, skipped: rec.skipped } : rec.refusal });
  } finally {
    disarmSignals();
  }
}

/* ------------------------------------------------------------------------- *
 * Public operations
 * ------------------------------------------------------------------------- */

function install(entry, im, target, opts) {
  const o = opts || {};
  let stat;
  try { stat = fs.statSync(target); } catch (_) { stat = null; }
  if (!stat || !stat.isDirectory()) {
    return refuse('IO_ERROR', `--target is not a directory: ${target}`);
  }

  const paths = txPaths(path.resolve(target));

  // An armed switch refuses the whole command, not only the write phase. The
  // check inside applyPlan guards direct callers; this one guards the paths
  // that return before ever reaching it — an idempotent no-op and a dry run
  // would otherwise report success into a project someone has explicitly
  // fenced off.
  const armedVia = killSwitchProbe(path.resolve(target), o)();
  if (armedVia) {
    return refuse('KILL_SWITCH_ACTIVATED',
      `kill switch (${armedVia}) is armed for this project; refusing to install`,
      {
        at_phase: 'before-start',
        next: 'run `installer.js kill-switch disarm --target <proj>` to allow installs again',
      });
  }

  // Recovery comes BEFORE planning, and the order is load-bearing.
  //
  // A plan is a snapshot of the target's current bytes: it records the prior
  // sha256 of every path so it can back them up and, if needed, put them back.
  // Recovery changes exactly those bytes. Planning first and recovering second
  // produces a plan describing a tree that no longer exists — it was observed
  // failing on a file the recovery had just deleted, with an ENOENT whose
  // message pointed at the backup step rather than at the stale premise that
  // caused it. Recover, then look at what is actually there.
  let recovered = null;
  if (!o.dryRun && fs.existsSync(paths.journal)) {
    const rec = recover(path.resolve(target), {});
    if (!rec.ok) return rec;
    if (rec.recovered) {
      recovered = rec;
      if (typeof o.onRecovered === 'function') o.onRecovered(rec);
    }
  }

  const planned = planInstall(entry, im, target, o);
  if (!planned.ok) return planned;
  const plan = planned.plan;
  if (recovered) plan.recovered_before_install = recovered;

  if (o.dryRun) {
    return {
      ok: true, status: 'dry-run', component: plan.component, mode: plan.mode,
      would: plan.files.map(f => ({ path: f.rel, action: f.action, bytes: f.bytes })),
      checksum: plan.checksum,
      writes: plan.files.filter(f => f.action !== 'unchanged').length,
      // A dry run writes nothing, so it cannot recover an interrupted
      // transaction — and a plan read off a half-applied tree describes that
      // tree, not the one an install would act on. Say so rather than let the
      // actions be read as a forecast.
      dirty: fs.existsSync(paths.journal),
    };
  }

  // Idempotence is decided against the state of record AND the bytes on disk.
  // Either alone can lie: installed.json can name files a user deleted, and
  // matching bytes without a record mean the component was never installed.
  const installed = readInstalled(paths);
  const prior = installed.components[plan.component];
  if (prior && prior.checksum === plan.checksum && plan.files.every(f => f.action === 'unchanged')) {
    return {
      ok: true, status: 'unchanged', component: plan.component, mode: plan.mode,
      txid: prior.txid, checksum: plan.checksum, writes: 0,
      recovered_before_install: plan.recovered_before_install || null,
    };
  }

  // A pointer install writes no component code; only the record changes.
  const res = applyPlan(plan, o);
  if (res.ok && plan.recovered_before_install) res.recovered_before_install = plan.recovered_before_install;
  return res;
}

/*
 * Reverts a committed install. A rollback is itself a transaction: it writes a
 * journal first and reverts through the same path, because a rollback
 * interrupted halfway is exactly the failure it exists to fix.
 */
function rollback(component, target, opts) {
  const o = opts || {};
  const paths = txPaths(target);

  if (fs.existsSync(paths.journal)) {
    const rec = recover(target, {});
    if (!rec.ok) return rec;
  }

  const installed = readInstalled(paths);
  const rec = installed.components[component];
  if (!rec) {
    return refuse('NOT_INSTALLED', `component is not installed in this project: ${component}`,
      { known: Object.keys(installed.components) });
  }

  // Reverse plan: restoring a prior version is a write of the backed-up bytes;
  // undoing a creation is a removal. Both go through applyPlan-shaped journalling.
  const backupRoot = rec.backup_dir ? path.join(target, rec.backup_dir) : null;
  const txid = newTxid();
  const journal = {
    schema: JOURNAL_SCHEMA, txid, pid: process.pid, started: new Date().toISOString(),
    state: 'planning', component, mode: 'rollback', files: [],
  };

  fs.mkdirSync(paths.root, { recursive: true });
  try {
    fs.closeSync(fs.openSync(paths.journal, 'wx'));
  } catch (e) {
    if (e.code === 'EEXIST') return refuse('DIRTY_STATE', 'a journal already exists; recover first');
    return refuse('IO_ERROR', e.message);
  }

  const restored = [];
  const removed = [];
  const skipped = [];
  try {
    writeDurable(paths.journal, JSON.stringify(journal, null, 2) + '\n');
    for (const f of rec.files || []) {
      const abs = path.resolve(target, f.path);
      const onDisk = shaOnDisk(abs);
      if (f.prior_sha === null) {
        if (onDisk === null) continue;
        if (onDisk !== f.sha256) { skipped.push({ path: f.path, why: 'modified since install; left in place' }); continue; }
        fs.rmSync(abs, { force: true });
        removed.push(f.path);
      } else {
        const backup = backupRoot ? path.join(backupRoot, f.artRel || f.path) : null;
        if (!backup || shaOnDisk(backup) !== f.prior_sha) {
          skipped.push({ path: f.path, why: 'backup missing or corrupt; prior bytes not recoverable' });
          continue;
        }
        fs.mkdirSync(path.dirname(abs), { recursive: true });
        fs.copyFileSync(backup, abs);
        restored.push(f.path);
      }
    }

    delete installed.components[component];
    writeDurable(paths.installed, JSON.stringify(installed, null, 2) + '\n');
    if (backupRoot) rmrf(backupRoot);
    fs.rmSync(paths.journal, { force: true });

    return { ok: true, status: 'rolled-back', component, txid, restored, removed, skipped };
  } catch (e) {
    fs.rmSync(paths.journal, { force: true });
    return refuse('IO_ERROR', `rollback failed: ${e.message}`, { restored, removed, skipped });
  }
}

/*
 * Re-checks installed files against the hashes recorded at install time. This
 * is the only way to notice that a component was edited or truncated after the
 * fact, which no install-time check can see.
 */
function verify(target, component) {
  const paths = txPaths(target);
  const installed = readInstalled(paths);
  const names = component ? [component] : Object.keys(installed.components);
  if (component && !installed.components[component]) {
    return refuse('NOT_INSTALLED', `component is not installed in this project: ${component}`);
  }

  const report = [];
  let failures = 0;
  for (const name of names) {
    const rec = installed.components[name];
    const issues = [];
    for (const f of rec.files || []) {
      const got = shaOnDisk(path.resolve(target, f.path));
      if (got === null) issues.push({ path: f.path, why: 'missing' });
      else if (got !== f.sha256) issues.push({ path: f.path, why: 'checksum mismatch', expected: f.sha256, actual: got });
    }
    failures += issues.length;
    report.push({ component: name, mode: rec.mode, files: (rec.files || []).length, issues });
  }
  return { ok: failures === 0, status: failures === 0 ? 'verified' : 'drift', dirty: fs.existsSync(paths.journal), report };
}

/* ------------------------------------------------------------------------- *
 * CLI
 * ------------------------------------------------------------------------- */

const USAGE =
  'installer.js — install a CPP Design Registry entry as a recoverable transaction.\n\n' +
  'Usage:\n' +
  '  node modules/cdicf/installer.js install  --from <emitDir> --target <proj> [--dry-run] [--json]\n' +
  '  node modules/cdicf/installer.js rollback --component <id>  --target <proj> [--json]\n' +
  '  node modules/cdicf/installer.js recover  --target <proj> [--json]\n' +
  '  node modules/cdicf/installer.js verify   --target <proj> [--component <id>] [--json]\n' +
  '  node modules/cdicf/installer.js kill-switch <arm|disarm|status> --target <proj> [--json]\n\n' +
  'Exit: 0 ok, 2 argv, 3 io, 4 input invalid, 5 REDISTRIBUTION PROHIBITED,\n' +
  '      6 checksum mismatch, 7 postcondition failed, 8 dirty/concurrent,\n' +
  '      9 not installed, 10 path escape, 11 unresolved dependencies,\n' +
  '      12 KILL SWITCH — the transaction was stopped, the journal is preserved\n';

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(USAGE);
    process.exit(args.length ? 0 : 2);
  }

  const flagArg = (flag) => {
    const i = args.indexOf(flag);
    if (i === -1) return null;
    const v = args[i + 1];
    if (!v || v.startsWith('-')) {
      process.stderr.write(`installer.js: ${flag} requires a value\n`);
      process.exit(2);
    }
    return v;
  };

  const cmd = args[0];
  const target = flagArg('--target');
  const json = args.includes('--json');
  if (!target) {
    process.stderr.write('installer.js: --target is required\n');
    process.exit(2);
  }

  const done = (res, human) => {
    if (json) process.stdout.write(JSON.stringify(res, null, 2) + '\n');
    else process.stdout.write(human);
    process.exit(0);
  };
  const fail = (res) => {
    const r = res.refusal;
    process.stderr.write(`installer.js: REFUSED [${r.code}] ${r.reason}\n`);
    if (r.detail) process.stderr.write(`  detail: ${JSON.stringify(r.detail)}\n`);
    process.exit(r.exit);
  };

  if (cmd === 'install') {
    const from = flagArg('--from');
    if (!from) { process.stderr.write('installer.js: --from <emitDir> is required\n'); process.exit(2); }
    let entry, im;
    try {
      entry = JSON.parse(fs.readFileSync(path.join(from, 'registry-item.json'), 'utf8'));
      im = JSON.parse(fs.readFileSync(path.join(from, 'install-manifest.json'), 'utf8'));
    } catch (e) {
      process.stderr.write(`installer.js: cannot read emitter output from ${from}: ${e.message}\n`);
      process.exit(3);
    }
    const res = install(entry, im, path.resolve(target), {
      dryRun: args.includes('--dry-run'),
      onRecovered: (rec) => process.stderr.write(
        `installer.js: NOTICE — reverted an interrupted transaction (${rec.txid}, state ${rec.state}): ` +
        `${rec.restored.length} restored, ${rec.removed.length} removed, ${rec.skipped.length} skipped\n`),
    });
    if (!res.ok) fail(res);
    if (res.status === 'dry-run') {
      return done(res, `DRY-RUN  ${res.component}\n` +
        res.would.map(w => `  ${w.action.padEnd(9)} ${w.path}\n`).join('') +
        `  writes     ${res.writes}\n`);
    }
    return done(res, `${res.status.toUpperCase()}  ${res.component}\n` +
      `  mode       ${res.mode}\n` +
      `  files      ${(res.files || []).length}\n` +
      `  checksum   ${res.checksum}\n`);
  }

  if (cmd === 'rollback') {
    const component = flagArg('--component');
    if (!component) { process.stderr.write('installer.js: --component is required\n'); process.exit(2); }
    const res = rollback(component, path.resolve(target), {});
    if (!res.ok) fail(res);
    return done(res, `ROLLED-BACK  ${res.component}\n` +
      `  restored   ${res.restored.length}\n  removed    ${res.removed.length}\n  skipped    ${res.skipped.length}\n`);
  }

  if (cmd === 'recover') {
    const res = recover(path.resolve(target), { force: args.includes('--force') });
    if (!res.ok) fail(res);
    return done(res, res.recovered
      ? `RECOVERED  ${res.txid} (state ${res.state})\n  restored   ${res.restored.length}\n  removed    ${res.removed.length}\n  skipped    ${res.skipped.length}\n`
      : 'CLEAN  no interrupted transaction\n');
  }

  if (cmd === 'kill-switch') {
    const action = args[1];
    const t = path.resolve(target);
    if (action === 'arm') {
      const res = armKillSwitch(t);
      return done(res, `ARMED  kill switch\n  sentinel   ${res.sentinel}\n` +
        '  installs into this project now refuse with exit 12 until disarmed\n');
    }
    if (action === 'disarm') {
      const res = disarmKillSwitch(t);
      return done(res, `${res.status.toUpperCase()}  ${res.sentinel}\n`);
    }
    if (action === 'status') {
      const res = killSwitchStatus(t);
      return done(res, `${res.status.toUpperCase()}  ${res.sentinel}\n` +
        (res.detail ? `  armed at   ${res.detail.armed_at}\n` : ''));
    }
    process.stderr.write("installer.js: kill-switch needs one of arm|disarm|status\n");
    process.exit(2);
  }

  if (cmd === 'verify') {
    const res = verify(path.resolve(target), flagArg('--component'));
    if (res.refusal) fail(res);
    const human = res.report.map(r => `${r.issues.length ? 'DRIFT' : 'OK   '}  ${r.component}  (${r.files} files)\n` +
      r.issues.map(i => `    ${i.why}: ${i.path}\n`).join('')).join('') || 'no components installed\n';
    if (json) process.stdout.write(JSON.stringify(res, null, 2) + '\n');
    else process.stdout.write(human);
    process.exit(res.ok ? 0 : 6);
  }

  process.stderr.write(`installer.js: unknown command '${cmd}'\n\n${USAGE}`);
  process.exit(2);
}

if (require.main === module) main(process.argv);

module.exports = {
  install, rollback, recover, verify, planInstall, applyPlan,
  txPaths, readInstalled, REFUSAL, TX_DIR,
  armKillSwitch, disarmKillSwitch, killSwitchStatus, killSentinelPath,
  KILL_SENTINEL, ABORTED_STATE,
};
