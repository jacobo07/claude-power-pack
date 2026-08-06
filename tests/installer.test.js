#!/usr/bin/env node
/*
 * tests/installer.test.js — CDICF A3b
 *
 * The load-bearing cases are V-INST-03 and V-INST-04: a genuinely killed
 * process (exit 137 from inside the rename sweep, no unwinding) must leave a
 * tree that recovers to its exact pre-state. Everything else in this file is a
 * property that can be reasoned about; those two can only be observed.
 *
 * Run:
 *   node --test tests/installer.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');

const { emit } = require('../modules/cdicf/registry_emitter');
const { loadSchema } = require('../modules/cdicf/validate_manifest');
const {
  install, rollback, recover, verify, planInstall, txPaths, readInstalled, TX_DIR,
} = require('../modules/cdicf/installer');

const ROOT      = path.join(__dirname, '..');
const INSTALLER = path.join(ROOT, 'modules', 'cdicf', 'installer.js');
const CRASH     = path.join(__dirname, 'fixtures', 'cdicf_crash_child.js');
const EXAMPLES  = path.join(ROOT, 'modules', 'cdicf', 'examples');

const SCHEMA     = loadSchema();
const allowed    = () => JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'shadcn-ui.button.json'), 'utf8'));
const prohibited = () => JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'react-bits.split-text.json'), 'utf8'));

const NEW_TSX = 'export function Button(props) {\n  return <button {...props} />;\n}\n';
const OLD_TSX = '// the version already in the project\n';
const UPD_TSX = '// the version the registry ships\n';

const NS = 'cpp/primitives/button';       // local_namespace + entry name

function tmp(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function mkArtifacts(files) {
  const dir = tmp('cdicf-art-');
  for (const [name, body] of Object.entries(files)) {
    const full = path.join(dir, name);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, body);
  }
  return dir;
}

/* Produces a real emitter output directory — this is also the A3 -> A3b handoff. */
function emitTo(manifest, artifacts, opts) {
  const res = emit(manifest, Object.assign({ schema: SCHEMA }, opts || {},
    artifacts ? { artifactsDir: mkArtifacts(artifacts) } : {}));
  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  const dir = tmp('cdicf-emit-');
  fs.writeFileSync(path.join(dir, 'registry-item.json'), JSON.stringify(res.entry, null, 2));
  fs.writeFileSync(path.join(dir, 'install-manifest.json'), JSON.stringify(res.install_manifest, null, 2));
  return { dir, entry: res.entry, im: res.install_manifest };
}

function readEmit(dir) {
  return {
    entry: JSON.parse(fs.readFileSync(path.join(dir, 'registry-item.json'), 'utf8')),
    im: JSON.parse(fs.readFileSync(path.join(dir, 'install-manifest.json'), 'utf8')),
  };
}

/* A target project holding a file the install will overwrite, plus one it will create. */
function targetWithPrior() {
  const target = tmp('cdicf-proj-');
  const prior = path.join(target, NS, 'existing.tsx');
  fs.mkdirSync(path.dirname(prior), { recursive: true });
  fs.writeFileSync(prior, OLD_TSX);
  return { target, prior };
}

const twoFiles = { 'button.tsx': NEW_TSX, 'existing.tsx': UPD_TSX };
const read = (p) => fs.readFileSync(p, 'utf8');
const exists = (p) => fs.existsSync(p);

/* ---------------- Successful install ------------------------------------- */

test('V-INST-01 — a successful install lands the artifacts and records the state', () => {
  // Arrange
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);

  // Act
  const res = install(entry, im, target, {});

  // Assert
  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(res.status, 'installed');
  assert.equal(read(path.join(target, NS, 'button.tsx')), NEW_TSX);

  const rec = readInstalled(txPaths(target)).components['primitives/button'];
  assert.ok(rec, 'installed.json must name the component');
  assert.equal(rec.checksum, im.checksum);
  assert.equal(rec.provenance.copyright_holder, 'shadcn');
  // Postcondition verification is part of install; verify() re-proves it later.
  assert.equal(verify(target).ok, true);
  // The transaction left no journal and no staging behind.
  assert.equal(exists(txPaths(target).journal), false);
  assert.equal(exists(path.join(target, TX_DIR, 'staging', res.txid)), false);
});

test('V-INST-02 — checksums are verified against the install manifest, not assumed', () => {
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  install(entry, im, target, {});

  const installed = readInstalled(txPaths(target)).components['primitives/button'];
  const onDisk = require('node:crypto').createHash('sha256')
    .update(fs.readFileSync(path.join(target, NS, 'button.tsx'))).digest('hex');
  assert.equal(installed.files[0].sha256, onDisk);
  assert.equal(installed.files[0].sha256, im.artifacts[0].sha256);
});

/* ---------------- Interrupted install: the real kill ---------------------- */

test('V-INST-03 — a process killed mid-rename leaves a recoverable tree, not a partial one', () => {
  // Arrange — two files, one created and one overwritten, so a crash between
  // the two renames produces genuinely mixed state.
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const created = path.join(target, NS, 'button.tsx');

  // Act — crash after the FIRST rename. Not a thrown error: exit 137, abrupt.
  const r = spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '1'], { encoding: 'utf8' });
  assert.equal(r.status, 137, 'the fixture must die abruptly, not return');

  // Assert — the tree really is partial at this instant. If it were not, the
  // recovery below would be proving nothing.
  assert.equal(exists(created), true, 'first file was renamed in before the kill');
  assert.equal(read(prior), OLD_TSX, 'second file had not been reached');
  assert.equal(exists(txPaths(target).journal), true, 'the journal survives the kill');

  // Act — recover
  const rec = recover(target, {});

  // Assert — exact pre-state
  assert.equal(rec.ok, true);
  assert.equal(rec.recovered, true);
  assert.equal(rec.state, 'applying');
  assert.equal(exists(created), false, 'a file the transaction created must be removed');
  assert.equal(read(prior), OLD_TSX, 'a file it never reached must be untouched');
  assert.deepEqual(rec.skipped, []);
  assert.equal(exists(txPaths(target).journal), false, 'recovery clears the journal');
  // Nothing was committed, so the state of record never named the component.
  assert.equal(readInstalled(txPaths(target)).components['primitives/button'], undefined);
});

test('V-INST-04 — a kill after ALL renames still reverts, restoring overwritten bytes', () => {
  // The harder case: every file is in place and only the commit is missing.
  // The overwritten file must come back from its backup byte-for-byte.
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const created = path.join(target, NS, 'button.tsx');

  const r = spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '2'], { encoding: 'utf8' });
  assert.equal(r.status, 137);
  assert.equal(read(prior), UPD_TSX, 'both renames landed before the kill');

  const rec = recover(target, {});

  assert.equal(rec.recovered, true);
  assert.equal(read(prior), OLD_TSX, 'the prior version must be restored from the backup');
  assert.equal(exists(created), false);
  assert.deepEqual(rec.restored, [`${NS}/existing.tsx`]);
  assert.deepEqual(rec.removed, [`${NS}/button.tsx`]);
  assert.equal(readInstalled(txPaths(target)).components['primitives/button'], undefined);
});

test('V-INST-05 — a kill before any mutation leaves nothing to undo', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();

  const r = spawnSync(process.execPath, [CRASH, dir, target, 'journal-written', '1'], { encoding: 'utf8' });
  assert.equal(r.status, 137);

  const rec = recover(target, {});
  assert.equal(rec.state, 'planning');
  assert.equal(read(prior), OLD_TSX);
  assert.equal(exists(path.join(target, NS, 'button.tsx')), false);
  assert.deepEqual(rec.restored, []);
  assert.deepEqual(rec.removed, []);
});

test('V-INST-06 — the next install auto-reverts an interrupted one before proceeding', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();

  spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '1'], { encoding: 'utf8' });
  assert.equal(exists(txPaths(target).journal), true);

  let notified = null;
  const { entry, im } = readEmit(dir);
  const res = install(entry, im, target, { onRecovered: (r) => { notified = r; } });

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.ok(notified, 'the caller must be told a transaction was reverted, never silently');
  assert.equal(notified.state, 'applying');
  // And the retry itself completed cleanly on top of the restored pre-state.
  assert.equal(read(prior), UPD_TSX);
  assert.equal(read(path.join(target, NS, 'button.tsx')), NEW_TSX);
  assert.equal(verify(target).ok, true);
});

test('V-INST-07 — recovery declines to delete a file edited after the interruption', () => {
  // Over-reaching recovery destroys work that was never ours. It must stop and
  // name the path instead.
  const { dir } = emitTo(allowed(), twoFiles);
  const { target } = targetWithPrior();
  const created = path.join(target, NS, 'button.tsx');

  spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '1'], { encoding: 'utf8' });
  fs.writeFileSync(created, '// a human edited this after the crash\n');

  const rec = recover(target, {});
  assert.equal(exists(created), true, 'the edited file must survive recovery');
  assert.equal(rec.removed.length, 0);
  assert.equal(rec.skipped.length, 1);
  assert.match(rec.skipped[0].why, /modified after the interruption/);
});

/* ---------------- Rollback ------------------------------------------------ */

test('V-INST-08 — rollback returns the project to its pre-install state', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const created = path.join(target, NS, 'button.tsx');
  const { entry, im } = readEmit(dir);

  assert.equal(install(entry, im, target, {}).ok, true);
  assert.equal(read(prior), UPD_TSX);
  assert.equal(exists(created), true);

  const res = rollback('primitives/button', target, {});

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(read(prior), OLD_TSX, 'the overwritten file returns to its prior bytes');
  assert.equal(exists(created), false, 'the created file is removed');
  assert.deepEqual(res.skipped, []);
  assert.equal(readInstalled(txPaths(target)).components['primitives/button'], undefined);
  assert.equal(exists(txPaths(target).journal), false);
});

test('V-INST-09 — rolling back something that was never installed is refused, not silently ok', () => {
  const target = tmp('cdicf-proj-');
  const res = rollback('primitives/button', target, {});
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'NOT_INSTALLED');
  assert.equal(res.refusal.exit, 9);
});

/* ---------------- Idempotence -------------------------------------------- */

test('V-INST-10 — installing twice writes once and reports the second as unchanged', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const { entry, im } = readEmit(dir);

  const first = install(entry, im, target, {});
  const second = install(entry, im, target, {});

  assert.equal(first.status, 'installed');
  assert.equal(second.status, 'unchanged');
  assert.equal(second.writes, 0);
  assert.equal(second.txid, first.txid, 'the original transaction id is preserved');
  assert.equal(read(prior), UPD_TSX);
  assert.equal(verify(target).ok, true);
});

test('V-INST-11 — a component whose files were deleted is reinstalled, not called unchanged', () => {
  // installed.json alone would say "already installed". The bytes disagree, and
  // the bytes are the state that matters.
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  install(entry, im, target, {});
  fs.rmSync(path.join(target, NS, 'button.tsx'));

  const res = install(entry, im, target, {});
  assert.equal(res.status, 'installed');
  assert.equal(read(path.join(target, NS, 'button.tsx')), NEW_TSX);
});

/* ---------------- Dry run ------------------------------------------------- */

test('V-INST-12 — dry-run reports the plan and writes absolutely nothing', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const before = fs.readdirSync(target).sort();
  const { entry, im } = readEmit(dir);

  const res = install(entry, im, target, { dryRun: true });

  assert.equal(res.status, 'dry-run');
  assert.equal(res.writes, 2);
  assert.deepEqual(res.would.map(w => w.action).sort(), ['create', 'overwrite']);
  assert.equal(read(prior), OLD_TSX, 'dry-run must not touch existing files');
  assert.equal(exists(path.join(target, NS, 'button.tsx')), false);
  // Not even the transaction directory may appear.
  assert.equal(exists(path.join(target, TX_DIR)), false);
  assert.deepEqual(fs.readdirSync(target).sort(), before);
});

/* ---------------- The licence boundary, again ---------------------------- */

test('V-INST-13 — a prohibited component carrying code is refused at install too', () => {
  // The emitter would never produce this. It reaches the project by a path that
  // never went through the emitter — a hand-copied directory, a third-party
  // registry — which is exactly why the installer re-derives the posture.
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  im.provenance.license_tier = 'SOURCE_AVAILABLE_RESTRICTED';

  const res = install(entry, im, target, {});

  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'REDISTRIBUTION_PROHIBITED');
  assert.equal(res.refusal.exit, 5);
  assert.equal(exists(path.join(target, NS, 'button.tsx')), false);
  assert.equal(exists(path.join(target, TX_DIR)), false, 'a refusal must not create a transaction');
});

test('V-INST-14 — a prohibited component installs as a pointer with no code on disk', () => {
  // D-011 as executed: the Motion Gateway namespace is installable, and what
  // lands is a record, not a component.
  const { dir } = emitTo(prohibited(), null, { referenceOnly: true });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);

  const res = install(entry, im, target, {});

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(res.mode, 'upstream-reference');
  assert.equal(res.files.length, 0);
  const rec = readInstalled(txPaths(target)).components['motion-gateway/split-text'];
  assert.ok(rec);
  assert.equal(rec.provenance.copyright_holder, 'David Haz');
  assert.ok(rec.upstream_install.source.includes('react-bits'));
  // The only thing written into the project is the CDICF record itself.
  assert.deepEqual(fs.readdirSync(target), [TX_DIR]);
});

/* ---------------- Tampering and malformed input --------------------------- */

test('V-INST-15 — a tampered artifact is refused and named', () => {
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  entry.files[0].content = NEW_TSX + '// injected\n';

  const res = install(entry, im, target, {});

  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'CHECKSUM_MISMATCH');
  assert.equal(res.refusal.exit, 6);
  assert.equal(res.refusal.detail.file, 'button.tsx');
  assert.equal(exists(path.join(target, TX_DIR)), false);
});

test('V-INST-16 — a path escaping the target refuses the whole install', () => {
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  entry.files[0].path = '../escaped.tsx';

  const res = install(entry, im, target, {});

  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'PATH_ESCAPE');
  assert.equal(res.refusal.exit, 10);
  assert.equal(exists(path.join(path.dirname(target), 'escaped.tsx')), false);
});

test('V-INST-17 — an entry and manifest describing different components are refused', () => {
  const a = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const b = emitTo(prohibited(), null, { referenceOnly: true });
  const target = tmp('cdicf-proj-');

  const res = install(a.entry, b.im, target, {});
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'INPUT_INVALID');
  assert.match(res.refusal.reason, /different components/);
});

test('V-INST-18 — a manifest declaring an artifact the entry lacks is refused', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  entry.files = entry.files.filter(f => !f.path.endsWith('existing.tsx'));

  const res = install(entry, im, target, {});
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'ARTIFACT_SET_MISMATCH');
  assert.deepEqual(res.refusal.detail.missing, ['existing.tsx']);
});

/* ---------------- Postconditions and drift -------------------------------- */

test('V-INST-19 — a file corrupted between rename and verify fails the install and reverts', () => {
  // Proves the postcondition check reads from disk rather than trusting the
  // write it just performed.
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();
  const created = path.join(target, NS, 'button.tsx');
  const { entry, im } = readEmit(dir);

  const res = install(entry, im, target, {
    onPhase(phase, info) {
      if (phase === 'renamed' && info.path.endsWith('existing.tsx')) {
        fs.writeFileSync(created, '// corrupted by something outside the transaction\n');
      }
    },
  });

  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'POSTCONDITION_FAILED');
  assert.equal(res.refusal.exit, 7);
  assert.equal(read(prior), OLD_TSX, 'the overwritten file was restored');
  assert.equal(readInstalled(txPaths(target)).components['primitives/button'], undefined,
    'a failed install must never appear in the state of record');
});

test('V-INST-20 — verify detects a component edited after a clean install', () => {
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);
  install(entry, im, target, {});

  assert.equal(verify(target).ok, true);
  fs.writeFileSync(path.join(target, NS, 'button.tsx'), NEW_TSX + '// local edit\n');

  const v = verify(target);
  assert.equal(v.ok, false);
  assert.equal(v.status, 'drift');
  assert.equal(v.report[0].issues[0].why, 'checksum mismatch');
  assert.equal(v.report[0].issues[0].path, `${NS}/button.tsx`);
});

/* ---------------- Concurrency --------------------------------------------- */

test('V-INST-21 — a journal held by a live process is refused, not recovered', async () => {
  // The journal is the mutex. Reverting another process's in-flight
  // transaction would corrupt the very state it is protecting.
  const target = tmp('cdicf-proj-');
  const sleeper = spawn(process.execPath, ['-e', 'setTimeout(()=>{}, 30000)'], { stdio: 'ignore' });
  try {
    const paths = txPaths(target);
    fs.mkdirSync(paths.root, { recursive: true });
    fs.writeFileSync(paths.journal, JSON.stringify({
      schema: 'cdicf/journal/1', txid: 'held', pid: sleeper.pid,
      started: new Date().toISOString(), state: 'applying', files: [],
    }));

    const res = recover(target, {});
    assert.equal(res.ok, false);
    assert.equal(res.refusal.code, 'DIRTY_STATE');
    assert.equal(res.refusal.exit, 8);
    assert.match(res.refusal.reason, /in progress/);

    // --force is the explicit override, and it works.
    assert.equal(recover(target, { force: true }).ok, true);
  } finally {
    sleeper.kill();
  }
});

/* ---------------- CLI ----------------------------------------------------- */

test('V-INST-22 — the CLI installs, verifies and rolls back with the documented exit codes', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const { target, prior } = targetWithPrior();

  const ins = spawnSync(process.execPath, [INSTALLER, 'install', '--from', dir, '--target', target], { encoding: 'utf8' });
  assert.equal(ins.status, 0, ins.stderr);
  assert.match(ins.stdout, /INSTALLED\s+primitives\/button/);

  const ok = spawnSync(process.execPath, [INSTALLER, 'verify', '--target', target], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);

  fs.writeFileSync(path.join(target, NS, 'button.tsx'), '// drifted\n');
  const drift = spawnSync(process.execPath, [INSTALLER, 'verify', '--target', target], { encoding: 'utf8' });
  assert.equal(drift.status, 6);
  assert.match(drift.stdout, /DRIFT/);

  const rb = spawnSync(process.execPath, [INSTALLER, 'rollback', '--component', 'primitives/button', '--target', target], { encoding: 'utf8' });
  assert.equal(rb.status, 0, rb.stderr);
  // The drifted file was not ours to delete by then, so rollback says so
  // rather than removing a file it no longer recognises.
  assert.equal(read(prior), OLD_TSX);
});

test('V-INST-23 — the CLI refuses a prohibited entry with exit 5 and installs nothing', () => {
  const { dir } = emitTo(allowed(), { 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const im = JSON.parse(fs.readFileSync(path.join(dir, 'install-manifest.json'), 'utf8'));
  im.provenance.license_tier = 'SOURCE_AVAILABLE_RESTRICTED';
  fs.writeFileSync(path.join(dir, 'install-manifest.json'), JSON.stringify(im, null, 2));

  const r = spawnSync(process.execPath, [INSTALLER, 'install', '--from', dir, '--target', target], { encoding: 'utf8' });
  assert.equal(r.status, 5);
  assert.match(r.stderr, /REFUSED \[REDISTRIBUTION_PROHIBITED\]/);
  assert.deepEqual(fs.readdirSync(target), []);
});

/* ---------------- Planning is pure ---------------------------------------- */

test('V-INST-24 — planning touches nothing, so every refusal is decided before the first write', () => {
  const { dir } = emitTo(allowed(), twoFiles);
  const target = tmp('cdicf-proj-');
  const { entry, im } = readEmit(dir);

  const planned = planInstall(entry, im, target);
  assert.equal(planned.ok, true);
  assert.equal(planned.plan.files.length, 2);
  assert.deepEqual(planned.plan.files.map(f => f.action), ['create', 'create']);
  assert.deepEqual(fs.readdirSync(target), [], 'planning must not create anything');
});
