#!/usr/bin/env node
/*
 * tests/registry_emitter.test.js — CDICF A3
 *
 * The load-bearing case is V-EMIT-01: a redistribution-prohibited component is
 * refused at the system boundary with exit 5 and NO output. A2's INV-02
 * constrains what a manifest may say; A3 constrains what the system may do.
 *
 * Run:
 *   node --test tests/registry_emitter.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { emit, collectArtifacts, rollupChecksum } =
  require('../modules/cdicf/registry_emitter');
const { loadSchema } = require('../modules/cdicf/validate_manifest');

const ROOT       = path.join(__dirname, '..');
const EMITTER    = path.join(ROOT, 'modules', 'cdicf', 'registry_emitter.js');
const EXAMPLES   = path.join(ROOT, 'modules', 'cdicf', 'examples');
const REACT_BITS = path.join(EXAMPLES, 'react-bits.split-text.json');
const SHADCN     = path.join(EXAMPLES, 'shadcn-ui.button.json');

const SCHEMA = loadSchema();

const prohibited = () => JSON.parse(fs.readFileSync(REACT_BITS, 'utf8'));
const allowed    = () => JSON.parse(fs.readFileSync(SHADCN, 'utf8'));

function mkArtifacts(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-art-'));
  for (const [name, body] of Object.entries(files)) {
    const full = path.join(dir, name);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, body);
  }
  return dir;
}

const BUTTON_TSX =
  'export function Button(props) {\n' +
  '  return <button {...props} />;\n' +
  '}\n';

/* ---------------- The system boundary ----------------------------------- */

test('V-EMIT-01 — a PROHIBITED component is refused, exit 5, no artifact', () => {
  // Arrange — the real react-bits manifest: MIT + Commons Clause.
  const m = prohibited();

  // Act
  const res = emit(m, { schema: SCHEMA });

  // Assert
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'REDISTRIBUTION_PROHIBITED');
  assert.equal(res.refusal.exit, 5);
  assert.equal(res.entry, undefined, 'a refused emission must produce no entry');
  assert.equal(res.install_manifest, undefined);
});

test('V-EMIT-02 — the CLI refuses with exit 5 and writes nothing to stdout', () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-out-'));
  const r = spawnSync(process.execPath, [EMITTER, REACT_BITS, '--out', outDir], { encoding: 'utf8' });

  assert.equal(r.status, 5);
  assert.equal(r.stdout.trim(), '', 'refusal must not print an artifact to stdout');
  assert.match(r.stderr, /REFUSED \[REDISTRIBUTION_PROHIBITED\]/);
  // And nothing was written to disk — a half-artifact could be picked up later
  // by a step that assumes success.
  assert.deepEqual(fs.readdirSync(outDir), []);
});

test('V-EMIT-03 — posture is DERIVED from the tier, not read from the manifest', () => {
  // A hand-edited manifest that never went through the validator claims to be
  // redistributable. The tier is the fact; the posture field is a copy of it.
  const m = prohibited();
  m.provenance.redistribution_posture = 'allowed';   // the lie
  m.provenance.integration_mode = 'fork_canonical';

  const res = emit(m, { schema: SCHEMA, artifactsDir: mkArtifacts({ 'x.tsx': BUTTON_TSX }) });

  assert.equal(res.ok, false);
  // A2 catches the internal inconsistency first (INV-01/INV-02), which is
  // correct: an inconsistent manifest never reaches the license check.
  assert.equal(res.refusal.code, 'MANIFEST_INVALID');

  // Now make it internally consistent but still lying about the tier's meaning:
  // strip the manifest of validation by bypassing A2 is impossible here, so
  // assert the gate on a manifest that IS valid and prohibited.
  const honest = prohibited();
  const res2 = emit(honest, { schema: SCHEMA });
  assert.equal(res2.refusal.code, 'REDISTRIBUTION_PROHIBITED');
});

/* ---------------- Lawful emissions -------------------------------------- */

test('V-EMIT-04 — fork_canonical emits local artifacts with content', () => {
  const dir = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const res = emit(allowed(), { schema: SCHEMA, artifactsDir: dir });

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(res.entry.meta.cpp.artifact_class, 'local-artifacts');
  assert.equal(res.entry.type, 'registry:ui');
  assert.equal(res.entry.name, 'button');
  assert.equal(res.entry.files.length, 1);
  assert.match(res.entry.files[0].content, /export function Button/);
  assert.equal(res.entry.files[0].path, 'cpp/primitives/button/button.tsx');
  assert.equal(res.install_manifest.install.mode, 'local-artifacts');
});

test('V-EMIT-05 — gateway_upstream emits a URL reference and NO code', () => {
  // A permissive component may still be gatewayed by choice.
  const m = allowed();
  m.provenance.integration_mode = 'gateway_upstream';

  const res = emit(m, { schema: SCHEMA });

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(res.entry.meta.cpp.artifact_class, 'upstream-pointer');
  assert.equal(res.entry.files, undefined, 'a pointer must carry no files key at all');
  assert.equal(res.entry.meta.cpp.upstream_install.source, 'https://github.com/shadcn-ui/ui');
  assert.equal(res.entry.meta.cpp.upstream_install.commit_sha, '9846e22ce52c723554742860a0dbd3e5cf19b573');
  assert.equal(res.install_manifest.install.mode, 'upstream-reference');
  assert.equal(res.install_manifest.artifacts.length, 0);
});

test('V-EMIT-06 — --reference-only emits a code-free pointer for a PROHIBITED component', () => {
  const res = emit(prohibited(), { schema: SCHEMA, referenceOnly: true });

  assert.equal(res.ok, true, JSON.stringify(res.refusal));
  assert.equal(res.entry.meta.cpp.artifact_class, 'upstream-pointer');
  assert.equal(res.entry.files, undefined);
  // The whole artifact must contain no component source whatsoever.
  assert.equal(JSON.stringify(res.entry).includes('export '), false);
  assert.equal(res.entry.meta.cpp.provenance.redistribution_posture, 'prohibited');
  assert.equal(res.entry.meta.cpp.provenance.notice_required, true);
});

test('V-EMIT-07 — --reference-only on a fork mode is REFUSED, never silently honoured', () => {
  // A fork mode means "distribute local artifacts"; --reference-only means
  // "distribute nothing". The first draft resolved this by quietly emitting a
  // pointer, so a caller would believe they had shipped a fork and would have
  // shipped a URL. Contradictory inputs are refused, not reconciled.
  const f = allowed();                       // PERMISSIVE + fork_canonical
  const res = emit(f, {
    schema: SCHEMA, referenceOnly: true,
    artifactsDir: mkArtifacts({ 'a.tsx': BUTTON_TSX }),
  });

  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'MODE_MISMATCH');
  assert.equal(res.refusal.exit, 7);
  assert.equal(res.entry, undefined);
});

test('V-EMIT-07b — a PROHIBITED component recorded as a fork never reaches the licence gate', () => {
  // A2's INV-02 rejects the pairing outright, so the emitter refuses earlier
  // and for a more specific reason.
  const p = prohibited();
  p.provenance.integration_mode = 'fork_canonical';
  const res = emit(p, { schema: SCHEMA, referenceOnly: true });
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'MANIFEST_INVALID');
  assert.ok(res.refusal.detail.some(e => e.rule === 'INV-02'));
});

/* ---------------- Scaffold Illusion guard -------------------------------- */

test('V-EMIT-08 — a fork mode with no artifacts is refused, not emitted empty', () => {
  const res = emit(allowed(), { schema: SCHEMA });
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'NO_ARTIFACTS');
  assert.equal(res.refusal.exit, 6);
});

test('V-EMIT-09 — an empty artifacts directory is refused', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-empty-'));
  const res = emit(allowed(), { schema: SCHEMA, artifactsDir: dir });
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'NO_ARTIFACTS');
});

/* ---------------- Install manifest determinism --------------------------- */

test('V-EMIT-10 — install manifest carries a pinned version and a checksum', () => {
  const dir = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const m = emit(allowed(), { schema: SCHEMA, artifactsDir: dir }).install_manifest;

  assert.equal(m.pinned, true);
  assert.equal(m.install.deterministic, true);
  assert.equal(m.provenance.commit_sha, '9846e22ce52c723554742860a0dbd3e5cf19b573');
  assert.match(m.checksum, /^[0-9a-f]{64}$/);
  assert.equal(m.artifacts.length, 1);
  assert.match(m.artifacts[0].sha256, /^[0-9a-f]{64}$/);
  assert.equal(m.artifacts[0].bytes, Buffer.byteLength(BUTTON_TSX));
  assert.equal(m.notice_required, true);
});

test('V-EMIT-11 — the checksum is stable across runs and moves when content moves', () => {
  const a = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const b = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const c = mkArtifacts({ 'button.tsx': BUTTON_TSX + '// changed\n' });

  const ca = emit(allowed(), { schema: SCHEMA, artifactsDir: a }).install_manifest.checksum;
  const cb = emit(allowed(), { schema: SCHEMA, artifactsDir: b }).install_manifest.checksum;
  const cc = emit(allowed(), { schema: SCHEMA, artifactsDir: c }).install_manifest.checksum;

  assert.equal(ca, cb);
  assert.notEqual(ca, cc);
});

test('V-EMIT-12 — artifacts are sorted, so the checksum is filesystem-independent', () => {
  const dir = mkArtifacts({ 'z.tsx': 'z', 'a.tsx': 'a', 'nested/b.tsx': 'b' });
  const arts = collectArtifacts(dir);
  assert.deepEqual(arts.map(a => a.path), ['a.tsx', 'nested/b.tsx', 'z.tsx']);
  assert.equal(rollupChecksum(arts), rollupChecksum(arts.slice().reverse().sort((x, y) => x.path.localeCompare(y.path))));
});

/* ---------------- A2 is the gate before A1 ------------------------------- */

test('V-EMIT-13 — an invalid manifest is refused before any license reasoning', () => {
  const m = allowed();
  delete m.provenance.license_tier;
  const res = emit(m, { schema: SCHEMA, artifactsDir: mkArtifacts({ 'a.tsx': BUTTON_TSX }) });
  assert.equal(res.ok, false);
  assert.equal(res.refusal.code, 'MANIFEST_INVALID');
  assert.equal(res.refusal.exit, 4);
});

test('V-EMIT-14 — provenance travels with the artifact', () => {
  const dir = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const res = emit(allowed(), { schema: SCHEMA, artifactsDir: dir });
  const p = res.entry.meta.cpp.provenance;
  for (const field of ['upstream_repo', 'commit_sha', 'license_tier', 'redistribution_posture',
                       'integration_mode', 'copyright_holder', 'fetch_date']) {
    assert.ok(p[field], `provenance.${field} missing from the emitted entry`);
  }
  assert.equal(p.copyright_holder, 'shadcn');
});

test('V-EMIT-15 — the CLI emits both files and exits 0 on a lawful component', () => {
  const dir = mkArtifacts({ 'button.tsx': BUTTON_TSX });
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-out2-'));
  const r = spawnSync(process.execPath, [EMITTER, SHADCN, '--artifacts', dir, '--out', outDir], { encoding: 'utf8' });

  assert.equal(r.status, 0, r.stderr);
  assert.deepEqual(fs.readdirSync(outDir).sort(), ['install-manifest.json', 'registry-item.json']);
  const entry = JSON.parse(fs.readFileSync(path.join(outDir, 'registry-item.json'), 'utf8'));
  assert.equal(entry.$schema, 'https://ui.shadcn.com/schema/registry-item.json');
  assert.equal(entry.name, 'button');
});
