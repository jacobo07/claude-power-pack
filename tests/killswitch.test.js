/*
 * V-KILL-* — the installer kill switch (E4).
 *
 * The kill switch exists to satisfy HR-APA-009, which requires a write surface
 * to declare one. A declared-but-inert switch would satisfy the letter of that
 * rule and none of its purpose — this estate has already shipped one disarmed
 * kill switch, so every gate here asserts the switch FIRING, not its presence.
 *
 * Two properties are load-bearing and easy to get wrong:
 *
 *   1. An abort must NOT roll back. `recover` deletes the journal, and the
 *      journal is the post-mortem. So the abort stops and preserves; recovery
 *      repairs and ARCHIVES. Asserting only "the tree is clean afterwards"
 *      would pass on an implementation that destroyed the evidence.
 *   2. The switch must not auto-disarm. A switch that resets after one trip is
 *      a pause button, and every refusal must name the disarm command, because
 *      a switch nobody can turn off is an outage rather than a safeguard.
 */
'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { emit } = require('../modules/cdicf/registry_emitter');
const { loadSchema } = require('../modules/cdicf/validate_manifest');
const {
  install, recover, txPaths, readInstalled,
  armKillSwitch, disarmKillSwitch, killSwitchStatus, killSentinelPath,
} = require('../modules/cdicf/installer');

const ROOT      = path.join(__dirname, '..');
const INSTALLER = path.join(ROOT, 'modules', 'cdicf', 'installer.js');
const EXAMPLES  = path.join(ROOT, 'modules', 'cdicf', 'examples');

const SCHEMA  = loadSchema();
const allowed = () => JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'shadcn-ui.button.json'), 'utf8'));

const NEW_TSX = 'export function Button(props) {\n  return <button {...props} />;\n}\n';
const OLD_TSX = '// the version already in the project\n';
const UPD_TSX = '// the version the registry ships\n';
const NS = 'cpp/primitives/button';

const tmp = (p) => fs.mkdtempSync(path.join(os.tmpdir(), p));
const read = (p) => fs.readFileSync(p, 'utf8');

function mkArtifacts(files) {
  const dir = tmp('cdicf-art-');
  for (const [name, body] of Object.entries(files)) {
    const full = path.join(dir, name);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, body);
  }
  return dir;
}

function emitTo(files) {
  const res = emit(allowed(), { schema: SCHEMA, artifactsDir: mkArtifacts(files) });
  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  return { entry: res.entry, im: res.install_manifest };
}

/* A project holding a file the install will overwrite, plus one it will create. */
function targetWithPrior() {
  const target = tmp('cdicf-proj-');
  const prior = path.join(target, NS, 'existing.tsx');
  fs.mkdirSync(path.dirname(prior), { recursive: true });
  fs.writeFileSync(prior, OLD_TSX);
  return { target, prior };
}

const twoFiles = { 'button.tsx': NEW_TSX, 'existing.tsx': UPD_TSX };

/* ---------------- Arming refuses before anything is touched -------------- */

test('V-KILL-01 — an armed switch refuses the install without creating a journal', () => {
  // Arrange
  const { entry, im } = emitTo({ 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  armKillSwitch(target);

  // Act
  const res = install(entry, im, target, {});

  // Assert
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');
  assert.equal(res.refusal.exit, 12);
  assert.equal(fs.existsSync(txPaths(target).journal), false,
    'refusing before the lock means no dirty-state marker is left behind');
  assert.equal(fs.existsSync(path.join(target, NS, 'button.tsx')), false);
});

test('V-KILL-02 — every refusal names the command that disarms it', () => {
  const { entry, im } = emitTo({ 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  armKillSwitch(target);

  const res = install(entry, im, target, {});
  // A switch with no documented way off is an outage, not a safeguard.
  assert.match(res.refusal.detail.next, /kill-switch disarm/);
});

/* ---------------- Tripping mid-transaction -------------------------------- */

test('V-KILL-03 — tripping mid-transaction preserves the journal instead of deleting it', () => {
  // Arrange
  const { entry, im } = emitTo(twoFiles);
  const { target } = targetWithPrior();
  let armed = false;

  // Act — arm as the first file is staged, so the trip lands BETWEEN two
  // content writes. There is a seam per write, not per loop, which is what
  // makes "stop before the next write" true rather than approximately true.
  const res = install(entry, im, target, {
    killSwitch: () => armed,
    onPhase: (name) => { if (name === 'staging-file') armed = true; },
  });

  // Assert
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');
  const paths = txPaths(target);
  assert.equal(fs.existsSync(paths.journal), true,
    'the journal IS the post-mortem; an abort that deletes it destroys the evidence');
  const j = JSON.parse(read(paths.journal));
  assert.equal(j.state, 'aborted-by-kill-switch');
  assert.equal(j.aborted.by, 'kill-switch');
  assert.equal(j.aborted.via, 'programmatic');
  assert.equal(j.aborted.at_phase, 'staging-file');
  assert.equal(j.aborted.last_valid_state, 'backed-up',
    'the last DURABLE journal state, not the phase label — they differ, and the ' +
    'recoverable one is the state that reached disk');
  assert.ok(j.aborted.at, 'the abort carries a timestamp');
  // Nothing reached the project tree: the trip was before the rename sweep.
  assert.equal(fs.existsSync(path.join(target, NS, 'button.tsx')), false);
});

test('V-KILL-04 — the abort is recorded in the state of record, and NOT as an install', () => {
  const { entry, im } = emitTo(twoFiles);
  const { target } = targetWithPrior();
  let armed = false;

  const res = install(entry, im, target, {
    killSwitch: () => armed,
    onPhase: (name) => { if (name === 'applying') armed = true; },
  });
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');

  const installed = readInstalled(txPaths(target));
  assert.equal(installed.aborted.length, 1);
  const row = installed.aborted[0];
  assert.equal(row.status, 'ABORTED_BY_KILL_SWITCH');
  assert.equal(row.component, im.component);
  assert.ok(row.at && row.txid && row.last_valid_state);
  // The component was never installed. A record claiming otherwise is worse
  // than no record at all.
  assert.equal(installed.components[im.component], undefined);
});

test('V-KILL-05 — inside the rename sweep it stops before the next rename', () => {
  // Arrange
  const { entry, im } = emitTo(twoFiles);
  const { target, prior } = targetWithPrior();
  let armed = false;
  let renamed = 0;

  // Act — arm as soon as the FIRST rename completes. renameSync is one atomic
  // syscall, so the in-flight rename finishes and the sweep stops before the next.
  const res = install(entry, im, target, {
    killSwitch: () => armed,
    onPhase: (name) => { if (name === 'renamed') { renamed += 1; armed = true; } },
  });

  // Assert
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');
  assert.equal(renamed, 1, 'exactly one rename completed; the sweep stopped before the second');
  assert.equal(read(path.join(target, NS, 'button.tsx')), NEW_TSX, 'the completed rename was not undone');
  assert.equal(read(prior), OLD_TSX, 'the second file was never touched');
});

test('V-KILL-06 — recovery returns the pre-state and ARCHIVES the journal', () => {
  // Arrange
  const { entry, im } = emitTo(twoFiles);
  const { target, prior } = targetWithPrior();
  let armed = false;
  install(entry, im, target, {
    killSwitch: () => armed,
    onPhase: (name) => { if (name === 'renamed') armed = true; },
  });
  const paths = txPaths(target);
  const txid = JSON.parse(read(paths.journal)).txid;

  // Act
  const rec = recover(target, { force: true });

  // Assert — the tree is repaired...
  assert.equal(rec.ok, true);
  assert.equal(rec.recovered, true);
  assert.equal(fs.existsSync(path.join(target, NS, 'button.tsx')), false);
  assert.equal(read(prior), OLD_TSX);
  assert.equal(fs.existsSync(paths.journal), false);
  // ...and the evidence outlives the repair.
  const archive = path.join(paths.root, 'aborted', `${txid}.json`);
  assert.equal(rec.archived_journal, archive);
  assert.equal(fs.existsSync(archive), true,
    'repairing the tree must not cost the post-mortem');
  assert.equal(JSON.parse(read(archive)).aborted.by, 'kill-switch');
});

/* ---------------- Scope: in-flight only ----------------------------------- */

test('V-KILL-07 — an earlier completed install is untouched by a later abort', () => {
  // Arrange — a real, committed install first.
  const first = emitTo({ 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const ok = install(first.entry, first.im, target, {});
  assert.equal(ok.ok, true);
  const before = readInstalled(txPaths(target)).components[first.im.component];
  assert.ok(before);

  // Act — arm, then attempt a different install.
  armKillSwitch(target);
  const second = emitTo(twoFiles);
  const res = install(second.entry, second.im, target, {});

  // Assert — refused, and the committed install is byte-for-byte still there.
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');
  const after = readInstalled(txPaths(target)).components[first.im.component];
  assert.deepEqual(after, before, 'the kill switch stops what is in flight; it is not a retro-active uninstall');
  assert.equal(read(path.join(target, NS, 'button.tsx')), NEW_TSX);
});

/* ---------------- Arming is sticky ---------------------------------------- */

test('V-KILL-08 — the switch does not auto-disarm, and disarming restores installs', () => {
  // Arrange
  const target = tmp('cdicf-proj-');
  armKillSwitch(target);
  const a = emitTo({ 'button.tsx': NEW_TSX });

  // Act + Assert — refused twice, so one trip did not consume the arm.
  assert.equal(install(a.entry, a.im, target, {}).refusal.code, 'KILL_SWITCH_ACTIVATED');
  assert.equal(install(a.entry, a.im, target, {}).refusal.code, 'KILL_SWITCH_ACTIVATED');
  assert.equal(killSwitchStatus(target).status, 'armed');

  // Act — disarm
  const d = disarmKillSwitch(target);
  assert.equal(d.status, 'disarmed');
  assert.equal(fs.existsSync(killSentinelPath(target)), false);

  const res = install(a.entry, a.im, target, {});
  assert.equal(res.ok, true, 'a disarmed switch must not leave the project permanently fenced');
  assert.equal(res.status, 'installed');
});

test('V-KILL-09 — a dry run into a fenced project reports the refusal, not a forecast', () => {
  const { entry, im } = emitTo({ 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  armKillSwitch(target);

  const res = install(entry, im, target, { dryRun: true });
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'KILL_SWITCH_ACTIVATED');
});

/* ---------------- The operator surface ------------------------------------ */

test('V-KILL-10 — the CLI arms, reports and disarms, and install exits 12 while armed', () => {
  // Arrange
  const { entry, im } = emitTo({ 'button.tsx': NEW_TSX });
  const target = tmp('cdicf-proj-');
  const from = tmp('cdicf-emit-');
  fs.writeFileSync(path.join(from, 'registry-item.json'), JSON.stringify(entry, null, 2));
  fs.writeFileSync(path.join(from, 'install-manifest.json'), JSON.stringify(im, null, 2));
  const cli = (...a) => spawnSync(process.execPath, [INSTALLER, ...a], { encoding: 'utf8' });

  // Act + Assert — status before arming
  const s0 = cli('kill-switch', 'status', '--target', target, '--json');
  assert.equal(s0.status, 0);
  assert.equal(JSON.parse(s0.stdout).status, 'disarmed');

  const armRes = cli('kill-switch', 'arm', '--target', target, '--json');
  assert.equal(armRes.status, 0);
  assert.equal(JSON.parse(armRes.stdout).status, 'armed');

  // The real entry point, not the exported function: exit codes are the contract.
  const blocked = cli('install', '--from', from, '--target', target, '--json');
  assert.equal(blocked.status, 12, blocked.stderr);
  assert.match(blocked.stderr, /KILL_SWITCH_ACTIVATED/);

  const disarmRes = cli('kill-switch', 'disarm', '--target', target, '--json');
  assert.equal(disarmRes.status, 0);
  const allowedRun = cli('install', '--from', from, '--target', target, '--json');
  assert.equal(allowedRun.status, 0, allowedRun.stderr);
});
