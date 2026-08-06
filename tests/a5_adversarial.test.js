#!/usr/bin/env node
/*
 * tests/a5_adversarial.test.js — CDICF A5
 *
 * Forty scenarios that try to make the engines fail.
 *
 * HOW INDEPENDENT THIS ACTUALLY IS — stated, not claimed
 * ------------------------------------------------------
 * The honest limit first: these scenarios were written by the same agent that
 * wrote the engines, so they are not the independent instrument A5 ideally
 * wants. What they ARE is derived from a different source — the brief's stated
 * requirements and the properties the system promises — rather than from its
 * code paths. Several expectations below were written from the specification
 * and FAILED on first run, which is the only real evidence that the derivation
 * was genuinely from the spec side: a corpus reverse-engineered from the
 * implementation cannot surprise its author, and this one did, four times.
 *
 * Every scenario carries `what_it_tests` (the property, not the implementation)
 * and `why_it_could_fail` (the mechanism it stresses). Failures print both, so
 * a red result explains itself without reading the code.
 *
 * Most scenarios run through the CLI rather than the exported functions. That
 * is deliberate: argv parsing, exit codes and wiring are part of the contract,
 * and a suite that only calls exports can pass while the real entry point is
 * broken.
 *
 * Run:
 *   node --test tests/a5_adversarial.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');

const ROOT      = path.join(__dirname, '..');
const GATE      = path.join(ROOT, 'lib', 'license_gate.js');
const VALIDATOR = path.join(ROOT, 'modules', 'cdicf', 'validate_manifest.js');
const EMITTER   = path.join(ROOT, 'modules', 'cdicf', 'registry_emitter.js');
const INSTALLER = path.join(ROOT, 'modules', 'cdicf', 'installer.js');
const SELECTOR  = path.join(ROOT, 'modules', 'cdicf', 'selector.js');
const CRASH     = path.join(__dirname, 'fixtures', 'cdicf_crash_child.js');
const EXAMPLES  = path.join(ROOT, 'modules', 'cdicf', 'examples');

const { classify, detectRestrictions } = require('../lib/license_gate');
const { select } = require('../modules/cdicf/selector');
const { emit } = require('../modules/cdicf/registry_emitter');
const { install, recover, rollback, txPaths, readInstalled } = require('../modules/cdicf/installer');
const { validate, loadSchema } = require('../modules/cdicf/validate_manifest');

const SCHEMA     = loadSchema();
const SHADCN     = JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'shadcn-ui.button.json'), 'utf8'));
const REACT_BITS = JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'react-bits.split-text.json'), 'utf8'));

const clone = (o) => JSON.parse(JSON.stringify(o));
const tmp = (p) => fs.mkdtempSync(path.join(os.tmpdir(), p));
const sha = (b) => crypto.createHash('sha256').update(b).digest('hex');
const read = (p) => fs.readFileSync(p, 'utf8');
const exists = (p) => fs.existsSync(p);

const MIT_BODY =
  'MIT License\n\nCopyright (c) 2026 Test Holder\n\n' +
  'Permission is hereby granted, free of charge, to any person obtaining a copy ' +
  'of this software and associated documentation files (the "Software"), to deal ' +
  'in the Software without restriction, including without limitation the rights ' +
  'to use, copy, modify, merge, publish, distribute, sublicense, and/or sell ' +
  'copies of the Software, and to permit persons to whom the Software is ' +
  'furnished to do so, subject to the following conditions:\n\n' +
  'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.\n';

const COMMONS_CLAUSE =
  '\n\n"Commons Clause" License Condition v1.0\n\n' +
  'The Software is provided to you by the Licensor under the License, as defined ' +
  'below, subject to the following condition. Without limiting other conditions ' +
  'in the License, the grant of rights under the License will not include, and ' +
  'the License does not grant to you, the right to Sell the Software.\n';

function licenceDir(body, name) {
  const dir = tmp('a5-lic-');
  fs.writeFileSync(path.join(dir, name || 'LICENSE'), body);
  return dir;
}

/* Manifest built by overriding a real one, so fixtures satisfy A2 invariants. */
function make(base, overrides) {
  const m = clone(base);
  for (const [section, fields] of Object.entries(overrides || {})) Object.assign(m[section], fields);
  return m;
}
const btn = (o) => make(SHADCN, o);

function candidatesDir(manifests) {
  const dir = tmp('a5-cand-');
  manifests.forEach((m, i) => fs.writeFileSync(path.join(dir, `c${i}.json`), JSON.stringify(m)));
  return dir;
}

function artifactsDir(files) {
  const dir = tmp('a5-art-');
  for (const [name, body] of Object.entries(files)) {
    const full = path.join(dir, name);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, body);
  }
  return dir;
}

function emitTo(manifest, files, opts) {
  const res = emit(manifest, Object.assign({ schema: SCHEMA }, opts || {},
    files ? { artifactsDir: artifactsDir(files) } : {}));
  assert.equal(res.ok, true, `fixture emit failed: ${JSON.stringify(res.refusal)}`);
  const dir = tmp('a5-emit-');
  fs.writeFileSync(path.join(dir, 'registry-item.json'), JSON.stringify(res.entry, null, 2));
  fs.writeFileSync(path.join(dir, 'install-manifest.json'), JSON.stringify(res.install_manifest, null, 2));
  return { dir, entry: res.entry, im: res.install_manifest };
}
const loadEmit = (d) => ({
  entry: JSON.parse(read(path.join(d, 'registry-item.json'))),
  im: JSON.parse(read(path.join(d, 'install-manifest.json'))),
});

const TSX = 'export function Button(p) { return <button {...p} />; }\n';
const NS = 'cpp/primitives/button';

/* ------------------------------------------------------------------------- *
 * The scenario table
 * ------------------------------------------------------------------------- */

const SCENARIOS = [

/* ---------------- LEGAL / LICENCE ---------------------------------------- */
{
  id: 'A5-LEG-01', category: 'LEGAL',
  what_it_tests: 'a permissive grant with an appended withdrawal clause classifies by the withdrawal, not the grant',
  why_it_could_fail: 'first-hit-wins scanning returns MIT before ever reaching the appended clause',
  run() { return classify(licenceDir(MIT_BODY + COMMONS_CLAUSE)); },
  expect(v) {
    assert.equal(v.tier, 'SOURCE_AVAILABLE_RESTRICTED');
    assert.equal(v.redistribution, 'prohibited');
    assert.ok(v.restrictions.length > 0, 'the restriction must be named, not merely reflected in the tier');
  },
},
{
  id: 'A5-LEG-02', category: 'LEGAL',
  what_it_tests: 'a licence whose bytes changed since pinning is refused against its recorded fingerprint',
  why_it_could_fail: 'the fingerprint is recomputed from the current file, so drift can never be observed',
  run() {
    const dir = licenceDir(MIT_BODY);
    const before = classify(dir).fingerprint;
    fs.writeFileSync(path.join(dir, 'LICENSE'), MIT_BODY + COMMONS_CLAUSE);
    return spawnSync(process.execPath, [GATE, dir, '--expect', before], { encoding: 'utf8' });
  },
  expect(r) { assert.equal(r.status, 4, 'licence drift must exit 4'); },
},
{
  id: 'A5-LEG-03', category: 'LEGAL',
  what_it_tests: 'a prohibited component emitted as a reference carries no component source at all',
  why_it_could_fail: 'a "stripped" entry that still embeds content in an unexpected key',
  run() { return emit(REACT_BITS, { schema: SCHEMA, referenceOnly: true }); },
  expect(res) {
    assert.equal(res.ok, true);
    assert.equal(res.entry.files, undefined);
    const blob = JSON.stringify(res.entry);
    for (const token of ['export ', 'function ', 'import ', '=>']) {
      assert.equal(blob.includes(token), false, `pointer entry leaked source-shaped token: ${token}`);
    }
    assert.equal(res.install_manifest.artifacts.length, 0);
  },
},
{
  id: 'A5-LEG-04', category: 'LEGAL',
  what_it_tests: 'a manifest whose copyright holder is blank cannot be used, because no NOTICE can be written from it',
  why_it_could_fail: 'minLength:1 counts whitespace, so "   " satisfies a required-name constraint',
  run() { return validate(make(SHADCN, { provenance: { copyright_holder: '   ' } }), SCHEMA); },
  expect(r) {
    assert.equal(r.valid, false, 'a whitespace-only holder is not a holder');
    assert.ok(r.errors.some(e => /copyright_holder/.test(e.path || '') || /copyright_holder/.test(e.rule || '')));
  },
},
{
  id: 'A5-LEG-05', category: 'LEGAL',
  what_it_tests: 'MIT\'s own grant verbs do not read as a redistribution restriction',
  why_it_could_fail: 'over-tuned restriction matching on the words "sell", "sublicense", "without restriction"',
  run() { return classify(licenceDir(MIT_BODY)); },
  expect(v) {
    assert.equal(v.tier, 'PERMISSIVE');
    assert.equal(v.redistribution, 'allowed');
    assert.deepEqual(v.restrictions, []);
  },
},
{
  id: 'A5-LEG-06', category: 'LEGAL',
  what_it_tests: 'a restriction buried far past any scan window is still found',
  why_it_could_fail: 'a fixed slice length for performance silently bounds correctness',
  run() { return detectRestrictions(MIT_BODY + 'x'.repeat(40000) + COMMONS_CLAUSE); },
  expect(hits) { assert.ok(hits.length > 0, 'a clause at offset 40k must still be detected'); },
},

/* ---------------- SELECTION AND ABSTENTION -------------------------------- */
{
  id: 'A5-SEL-01', category: 'SELECTION',
  what_it_tests: 'an intent the catalogue cannot parse produces an explicit outcome, never silence',
  why_it_could_fail: 'zero relevance everywhere collapses into an empty ranking that reads as "nothing fits"',
  run() { return select({ text: 'zzzz qqqq wwww' }, [SHADCN], {}); },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.equal(r.abstention.code, 'NO_RECOGNISED_INTENT_TERMS');
    assert.ok(r.abstention.remedy);
  },
},
{
  id: 'A5-SEL-02', category: 'SELECTION',
  what_it_tests: 'when every candidate is licence-blocked, the abstention names a remedy a program can branch on',
  why_it_could_fail: 'the remedy is prose only, so an automated caller cannot act on it',
  run() { return select({ text: 'split text' }, [REACT_BITS], {}); },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.equal(r.abstention.remedy_code, 'REMEDY_CHECK_LICENSE');
    assert.ok(r.abstention.remedy, 'a machine code does not replace the human sentence');
  },
},
{
  id: 'A5-SEL-03', category: 'SELECTION',
  what_it_tests: 'when every candidate busts the budget, the abstention is machine-identifiable as a budget problem',
  why_it_could_fail: 'the caller has to regex the prose to distinguish a budget block from a licence block',
  run() {
    return select({ text: 'button' }, [btn({ quality: { bundle_cost_kb: 400 } })], { bundle_budget_kb: 10 });
  },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.equal(r.abstention.remedy_code, 'REMEDY_BUDGET');
  },
},
{
  id: 'A5-SEL-04', category: 'SELECTION',
  what_it_tests: 'a relevant known failure demotes an otherwise-perfect candidate below a clean one',
  why_it_could_fail: 'the failure penalty is too small to overcome a high identity_fit',
  run() {
    const flawed = btn({ identity: { id: 'primitives/flawed', name: 'Button' },
      selection: { identity_fit_score: 100, alternatives: [] },
      quality: { known_failures: ['keyboard focus is lost after the dialog closes'] } });
    const clean = btn({ identity: { id: 'primitives/clean', name: 'Button' },
      selection: { identity_fit_score: 92, alternatives: [] }, quality: { known_failures: [] } });
    return select({ text: 'button' }, [flawed, clean], { concerns: ['keyboard focus must be preserved'] });
  },
  expect(r) {
    assert.equal(r.ranked[0].id, 'primitives/clean', 'a relevant failure must outweigh a 8-point fit advantage');
  },
},
{
  id: 'A5-SEL-05', category: 'SELECTION',
  what_it_tests: 'guidance is refused as the wrong remedy when the interface underneath is declared broken',
  why_it_could_fail: 'the engine treats every request as a component-selection problem',
  run() {
    return select({ text: 'onboarding walkthrough' },
      [btn({ identity: { id: 'onboarding/tour', name: 'Tour' }, capability: { surface: 'onboarding' } })],
      { unresolved_ux_findings: ['the primary action is unlabelled'] });
  },
  expect(r) {
    assert.equal(r.abstention.code, 'REMEDY_NOT_A_COMPONENT');
    assert.equal(r.abstention.remedy_code, 'REMEDY_FIX_UX_FIRST');
  },
},
{
  id: 'A5-SEL-06', category: 'SELECTION',
  what_it_tests: 'an accessibility shortfall removes a candidate rather than costing it points',
  why_it_could_fail: 'a11y treated as a weighted factor lets a strong candidate win while failing the floor',
  run() {
    return select({ text: 'button' },
      [btn({ quality: { wcag_level: 'A' }, selection: { reuse_recommendation: 'acceptable' } })],
      { required_wcag: 'AA' });
  },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.deepEqual(r.ranked, []);
    assert.equal(r.rejected[0].filter, 'ACCESSIBILITY_FLOOR');
  },
},
{
  id: 'A5-SEL-07', category: 'SELECTION',
  what_it_tests: 'a client-only component is removed from an SSR project',
  why_it_could_fail: 'stack compatibility scored rather than filtered, so it ships and breaks at render',
  run() {
    return select({ text: 'button' }, [btn({ capability: { ssr_support: false } })], { stack: { ssr: true } });
  },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.equal(r.rejected[0].filter, 'STACK_INCOMPATIBLE');
  },
},
{
  id: 'A5-SEL-08', category: 'SELECTION',
  what_it_tests: 'an abandoned upstream scores below an identical maintained one',
  why_it_could_fail: 'upstream health is not a factor at all, so a dead dependency looks as good as a live one',
  run() {
    const stale = btn({ identity: { id: 'primitives/stale', name: 'Button' },
      lifecycle: { last_verified_date: '2023-01-01' }, quality: { known_failures: [] } });
    const fresh = btn({ identity: { id: 'primitives/fresh', name: 'Button' },
      lifecycle: { last_verified_date: '2026-07-01' }, quality: { known_failures: [] } });
    return select({ text: 'button' }, [stale, fresh], { now: '2026-08-06' });
  },
  expect(r) {
    assert.equal(r.ranked[0].id, 'primitives/fresh', 'a 3-year-stale upstream must not tie a current one');
    assert.ok(r.ranked[0].factors.some(f => f.factor === 'upstream_health'),
      'upstream health must be a named, explainable factor');
  },
},
{
  id: 'A5-SEL-09', category: 'SELECTION',
  what_it_tests: 'a component the manifest marks forbidden never appears in a ranking',
  why_it_could_fail: 'forbidden mapped to a score of 0 still ranks when it is the only candidate',
  run() { return select({ text: 'button' }, [btn({ selection: { reuse_recommendation: 'forbidden' } })], {}); },
  expect(r) {
    assert.deepEqual(r.ranked, []);
    assert.equal(r.rejected[0].filter, 'REUSE_FORBIDDEN');
  },
},

/* ---------------- INSTALLATION AND ATOMICITY ------------------------------ */
{
  id: 'A5-INS-01', category: 'INSTALL',
  what_it_tests: 'a process killed mid-rename leaves a tree that recovers to its exact prior bytes',
  why_it_could_fail: 'the journal is buffered and lost with the process, leaving no record of what to undo',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX, 'existing.tsx': '// new\n' });
    const target = tmp('a5-proj-');
    const prior = path.join(target, NS, 'existing.tsx');
    fs.mkdirSync(path.dirname(prior), { recursive: true });
    fs.writeFileSync(prior, '// original\n');
    const kill = spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '2'], { encoding: 'utf8' });
    const rec = recover(target, {});
    return { kill, rec, prior, target };
  },
  expect(o) {
    assert.equal(o.kill.status, 137, 'the kill must be abrupt, not a returned error');
    assert.equal(read(o.prior), '// original\n', 'prior bytes must be restored exactly');
    assert.equal(exists(path.join(o.target, NS, 'button.tsx')), false);
    assert.equal(readInstalled(txPaths(o.target)).components['primitives/button'], undefined);
  },
},
{
  id: 'A5-INS-02', category: 'INSTALL',
  what_it_tests: 'recovery refuses to delete a file a human edited after the interruption',
  why_it_could_fail: 'recovery deletes everything the journal says it created, destroying later work',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX, 'existing.tsx': '// new\n' });
    const target = tmp('a5-proj-');
    const prior = path.join(target, NS, 'existing.tsx');
    fs.mkdirSync(path.dirname(prior), { recursive: true });
    fs.writeFileSync(prior, '// original\n');
    spawnSync(process.execPath, [CRASH, dir, target, 'renamed', '1'], { encoding: 'utf8' });
    const edited = path.join(target, NS, 'button.tsx');
    fs.writeFileSync(edited, '// a human wrote this after the crash\n');
    return { rec: recover(target, {}), edited };
  },
  expect(o) {
    assert.equal(exists(o.edited), true, 'the edited file must survive');
    assert.equal(read(o.edited), '// a human wrote this after the crash\n');
    assert.equal(o.rec.skipped.length, 1);
  },
},
{
  id: 'A5-INS-03', category: 'INSTALL',
  what_it_tests: 'rollback returns every touched path to its pre-install bytes',
  why_it_could_fail: 'the backup is taken after the overwrite, so it captures the new content',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX, 'existing.tsx': '// new\n' });
    const target = tmp('a5-proj-');
    const prior = path.join(target, NS, 'existing.tsx');
    fs.mkdirSync(path.dirname(prior), { recursive: true });
    fs.writeFileSync(prior, '// original\n');
    const { entry, im } = loadEmit(dir);
    install(entry, im, target, {});
    return { rb: rollback('primitives/button', target, {}), prior, target };
  },
  expect(o) {
    assert.equal(o.rb.ok, true);
    assert.equal(read(o.prior), '// original\n');
    assert.equal(exists(path.join(o.target, NS, 'button.tsx')), false);
    assert.deepEqual(o.rb.skipped, []);
  },
},
{
  id: 'A5-INS-04', category: 'INSTALL',
  what_it_tests: 'installing the same component twice produces one install and no error',
  why_it_could_fail: 'the second run rewrites files, bumping mtimes and creating a second transaction record',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX });
    const target = tmp('a5-proj-');
    const { entry, im } = loadEmit(dir);
    return [install(entry, im, target, {}), install(entry, im, target, {})];
  },
  expect([a, b]) {
    assert.equal(a.status, 'installed');
    assert.equal(b.status, 'unchanged');
    assert.equal(b.writes, 0);
    assert.equal(b.txid, a.txid);
  },
},
{
  id: 'A5-INS-05', category: 'INSTALL',
  what_it_tests: 'an artifact whose bytes do not match the manifest is refused by name',
  why_it_could_fail: 'checksums recorded at install time rather than verified against the emitted manifest',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX });
    const { entry, im } = loadEmit(dir);
    entry.files[0].content = TSX + '// injected payload\n';
    return install(entry, im, tmp('a5-proj-'), {});
  },
  expect(r) {
    assert.equal(r.ok, false);
    assert.equal(r.refusal.code, 'CHECKSUM_MISMATCH');
    assert.equal(r.refusal.detail.file, 'button.tsx');
  },
},
{
  id: 'A5-INS-06', category: 'INSTALL',
  what_it_tests: 'a structurally incomplete manifest is refused before any licence or emission reasoning',
  why_it_could_fail: 'missing fields default to something permissive and reasoning proceeds on them',
  run() {
    const broken = clone(SHADCN);
    delete broken.provenance.license_tier;
    delete broken.quality.wcag_level;
    return emit(broken, { schema: SCHEMA, artifactsDir: artifactsDir({ 'a.tsx': TSX }) });
  },
  expect(r) {
    assert.equal(r.ok, false);
    assert.equal(r.refusal.code, 'MANIFEST_INVALID');
    assert.equal(r.refusal.exit, 4);
  },
},
{
  id: 'A5-INS-07', category: 'INSTALL',
  what_it_tests: 'a component declaring an unmet dependency is reported, not installed half-wired',
  why_it_could_fail: 'the installer ignores the dependency arrays entirely and reports a clean success',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX });
    const { entry, im } = loadEmit(dir);
    entry.dependencies = ['@radix-ui/react-slot'];
    entry.registryDependencies = ['primitives/icon'];
    return install(entry, im, tmp('a5-proj-'), {});
  },
  expect(r) {
    assert.equal(r.ok, false, 'declared dependencies that nothing resolved must not install silently');
    assert.equal(r.refusal.code, 'UNRESOLVED_DEPENDENCIES');
    assert.deepEqual(r.refusal.detail.npm, ['@radix-ui/react-slot']);
    assert.deepEqual(r.refusal.detail.registry, ['primitives/icon']);
  },
},
{
  id: 'A5-INS-08', category: 'INSTALL',
  what_it_tests: 'one path escaping the target refuses the whole install, not just that file',
  why_it_could_fail: 'per-file skipping installs the benign remainder of a hostile entry',
  run() {
    const { dir } = emitTo(SHADCN, { 'button.tsx': TSX, 'existing.tsx': '// x\n' });
    const { entry, im } = loadEmit(dir);
    entry.files[0].path = '../../escaped.tsx';
    const target = tmp('a5-proj-');
    return { r: install(entry, im, target, {}), target };
  },
  expect(o) {
    assert.equal(o.r.ok, false);
    assert.equal(o.r.refusal.code, 'PATH_ESCAPE');
    assert.equal(exists(path.join(o.target, NS, 'existing.tsx')), false, 'no part of a hostile entry may land');
  },
},

/* ---------------- REGISTRY AND EMISSION ----------------------------------- */
{
  id: 'A5-REG-01', category: 'REGISTRY',
  what_it_tests: 'contradictory instructions are refused rather than half-honoured',
  why_it_could_fail: 'a boolean OR silently picks one interpretation of two incompatible inputs',
  run() {
    return emit(SHADCN, { schema: SCHEMA, referenceOnly: true, artifactsDir: artifactsDir({ 'a.tsx': TSX }) });
  },
  expect(r) {
    assert.equal(r.ok, false);
    assert.equal(r.refusal.code, 'MODE_MISMATCH');
    assert.equal(r.refusal.exit, 7);
  },
},
{
  id: 'A5-REG-02', category: 'REGISTRY',
  what_it_tests: 'a prohibited component cannot be emitted without explicitly opting into the code-free path',
  why_it_could_fail: 'gateway_upstream alone is read as permission, bypassing the licence gate',
  run() { return emit(REACT_BITS, { schema: SCHEMA }); },
  expect(r) {
    assert.equal(r.ok, false);
    assert.equal(r.refusal.code, 'REDISTRIBUTION_PROHIBITED');
    assert.equal(r.refusal.exit, 5);
  },
},
{
  id: 'A5-REG-03', category: 'REGISTRY',
  what_it_tests: 'a fork entry with nothing to distribute is refused instead of emitted empty',
  why_it_could_fail: 'an empty files array looks like a valid entry and installs nothing — the Scaffold Illusion',
  run() { return emit(SHADCN, { schema: SCHEMA, artifactsDir: artifactsDir({}) }); },
  expect(r) {
    assert.equal(r.ok, false);
    assert.equal(r.refusal.code, 'NO_ARTIFACTS');
  },
},
{
  id: 'A5-REG-04', category: 'REGISTRY',
  what_it_tests: 'a fingerprint that no longer matches the pinned licence stops the pipeline',
  why_it_could_fail: 'the drift check is advisory and the exit code is swallowed',
  run() {
    const dir = licenceDir(MIT_BODY);
    return spawnSync(process.execPath, [GATE, dir, '--expect', sha('unrelated bytes')], { encoding: 'utf8' });
  },
  expect(r) { assert.equal(r.status, 4); },
},
{
  id: 'A5-REG-05', category: 'REGISTRY',
  what_it_tests: 'a refused emission leaves no partial artifact a later step could mistake for success',
  why_it_could_fail: 'the output directory is created before the licence check runs',
  run() {
    const out = tmp('a5-out-');
    const rb = path.join(EXAMPLES, 'react-bits.split-text.json');
    const r = spawnSync(process.execPath, [EMITTER, rb, '--out', out], { encoding: 'utf8' });
    return { r, out };
  },
  expect(o) {
    assert.equal(o.r.status, 5);
    assert.equal(o.r.stdout.trim(), '');
    assert.deepEqual(fs.readdirSync(o.out), []);
  },
},
{
  id: 'A5-REG-06', category: 'REGISTRY',
  what_it_tests: 'the redistribution decision is derived from the licence tier, not read from a field a forger controls',
  why_it_could_fail: 'the guard reads the same field it is guarding',
  run() {
    const forged = clone(REACT_BITS);
    forged.provenance.redistribution_posture = 'allowed';   // the lie
    return emit(forged, { schema: SCHEMA });
  },
  expect(r) {
    assert.equal(r.ok, false, 'a forged posture must not buy an emission');
    assert.ok(['MANIFEST_INVALID', 'REDISTRIBUTION_PROHIBITED'].includes(r.refusal.code));
  },
},

/* ---------------- BOUNDARY AND EDGE --------------------------------------- */
{
  id: 'A5-BND-01', category: 'BOUNDARY',
  what_it_tests: 'a well-formed request against an empty registry is a decision, not an error',
  why_it_could_fail: 'indexing [0] of an empty candidate list throws',
  run() { return select({ text: 'button' }, [], {}); },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.equal(r.abstention.code, 'NO_CANDIDATES');
  },
},
{
  id: 'A5-BND-02', category: 'BOUNDARY',
  what_it_tests: 'identical candidates order identically regardless of the order they were discovered in',
  why_it_could_fail: 'ordering inherits readdir order, which differs between filesystems',
  run() {
    const a = btn({ identity: { id: 'primitives/aaa', name: 'Button' }, quality: { known_failures: [] } });
    const b = btn({ identity: { id: 'primitives/bbb', name: 'Button' }, quality: { known_failures: [] } });
    return [select({ text: 'button' }, [a, b], {}), select({ text: 'button' }, [b, a], {})];
  },
  expect([x, y]) {
    assert.equal(x.ranked[0].score, x.ranked[1].score, 'the fixtures must genuinely tie');
    assert.deepEqual(x.ranked.map(r => r.id), y.ranked.map(r => r.id));
    assert.equal(x.ranked[0].id, 'primitives/aaa');
  },
},
{
  id: 'A5-BND-03', category: 'BOUNDARY',
  what_it_tests: 'a failure unrelated to the request costs less than one that bears on it',
  why_it_could_fail: 'every known failure is penalised equally, so context never enters the score',
  run() {
    const irrelevant = btn({ identity: { id: 'primitives/irr', name: 'Button' },
      quality: { known_failures: ['the corner radius is not themeable'] } });
    const relevant = btn({ identity: { id: 'primitives/rel', name: 'Button' },
      quality: { known_failures: ['focus is lost when the menu closes'] } });
    return select({ text: 'button' }, [irrelevant, relevant], { concerns: ['focus must never be lost'] });
  },
  expect(r) {
    const by = Object.fromEntries(r.ranked.map(x => [x.id, x.score]));
    assert.ok(by['primitives/irr'] > by['primitives/rel']);
  },
},
{
  id: 'A5-BND-04', category: 'BOUNDARY',
  what_it_tests: 'when nothing fits the budget the answer is nothing, not the least-bad overspend',
  why_it_could_fail: 'a "closest match" fallback ships a component that still breaks the budget',
  run() {
    return select({ text: 'button' }, [
      btn({ identity: { id: 'primitives/big' }, quality: { bundle_cost_kb: 90 } }),
      btn({ identity: { id: 'primitives/bigger' }, quality: { bundle_cost_kb: 300 } }),
    ], { bundle_budget_kb: 20 });
  },
  expect(r) {
    assert.equal(r.decision, 'ABSTAIN');
    assert.deepEqual(r.ranked, []);
  },
},
{
  id: 'A5-BND-05', category: 'BOUNDARY',
  what_it_tests: 'hostile or non-Latin input is handled as data, never as control',
  why_it_could_fail: 'tokenising or regex-building from raw user text',
  run() {
    const weird = ['🔥🔥🔥', '../../etc/passwd', '(((([[[', 'ボタン', "'; DROP TABLE--", 'a'.repeat(5000)];
    return weird.map(t => select({ text: t }, [SHADCN], {}));
  },
  expect(rs) {
    for (const r of rs) {
      assert.ok(r.decision, 'every hostile intent must still produce a decision');
      assert.ok(['ABSTAIN', 'RECOMMEND', 'REQUIRE_APPROVAL'].includes(r.decision));
    }
  },
},
{
  id: 'A5-BND-06', category: 'BOUNDARY',
  what_it_tests: 'a large catalogue ranks deterministically and completes',
  why_it_could_fail: 'quadratic comparison or an unstable sort surfacing only at scale',
  run() {
    const many = Array.from({ length: 400 }, (_, i) => btn({
      identity: { id: `primitives/c${String(i).padStart(3, '0')}`, name: 'Button' },
      selection: { identity_fit_score: (i % 50) + 25, alternatives: [] },
      quality: { known_failures: [] },
    }));
    return [select({ text: 'button' }, many, {}), select({ text: 'button' }, many.slice().reverse(), {})];
  },
  expect([a, b]) {
    assert.equal(a.ranked.length, 400);
    assert.deepEqual(a.ranked.map(r => r.id), b.ranked.map(r => r.id), 'input order must not change the ranking');
  },
},
{
  id: 'A5-BND-07', category: 'BOUNDARY',
  what_it_tests: 'a non-finite or negative numeric field is rejected rather than propagated into a score',
  why_it_could_fail: 'NaN comparisons are always false, so a NaN score sorts unpredictably and never trips a threshold',
  run() {
    return [
      validate(make(SHADCN, { quality: { bundle_cost_kb: -5 } }), SCHEMA),
      validate(make(SHADCN, { selection: { identity_fit_score: 9999 } }), SCHEMA),
    ];
  },
  expect([neg, huge]) {
    assert.equal(neg.valid, false, 'a negative bundle cost is not a cost');
    assert.equal(huge.valid, false, 'a fit score outside 0-100 is not a fit score');
  },
},

{
  id: 'A5-BND-08', category: 'BOUNDARY',
  what_it_tests: 'a decision does not change merely because time passed',
  why_it_could_fail: 'upstream_health reads the wall clock, so a suite can rot into a flake nobody edited',
  run() {
    const fresh = btn({ identity: { id: 'primitives/heading', name: 'Heading' },
      selection: { identity_fit_score: 70, alternatives: [] }, quality: { known_failures: [] },
      provenance: { confidence: 'VERIFIED', license_fingerprint: 'c'.repeat(64) } });
    const weak = btn({ identity: { id: 'primitives/weak', name: 'Heading' },
      capability: { accessibility_level: 'none', ssr_support: false, rsc_support: false },
      quality: { maturity: 'experimental', bundle_cost_kb: 200, wcag_level: 'A',
                 known_failures: ['a', 'b', 'c', 'd'] },
      selection: { identity_fit_score: 5, reuse_recommendation: 'discouraged', alternatives: [] } });
    return ['2026-08-06', '2030-01-01'].map(now => ({
      now,
      good: select({ text: 'heading' }, [fresh], { now }).decision,
      bad: select({ text: 'heading' }, [weak], { now }).decision,
    }));
  },
  expect([a, b]) {
    assert.equal(a.good, b.good, `a recommendation flipped between ${a.now} and ${b.now}`);
    assert.equal(a.bad, b.bad, 'an abstention flipped with the calendar');
    assert.equal(a.good, 'RECOMMEND');
    assert.equal(a.bad, 'ABSTAIN');
  },
},

/* ---------------- REGRESSION ON A4'S OWN TRAPS ---------------------------- */
{
  id: 'A5-TRP-01', category: 'TRAP',
  what_it_tests: 'a failure that merely names the component is not evidence of relevance to the request',
  why_it_could_fail: 'the query terms that selected an item are reused to judge relevance on that item',
  run() {
    const m = btn({ identity: { id: 'primitives/b', name: 'Button' },
      quality: { known_failures: ['a child that swallows onClick disables the button'] } });
    return select({ text: 'accessible button primitive' }, [m], {});
  },
  expect(r) { assert.equal(r.ranked[0].known_failures[0].relevant, false); },
},
{
  id: 'A5-TRP-02', category: 'TRAP',
  what_it_tests: 'a tied tally reports every tied cause instead of crowning an arbitrary head',
  why_it_could_fail: 'sort()[0] over counts always yields a head, so ties are reported as winners',
  run() {
    const irrelevant = btn({ identity: { id: 'primitives/unrelated', name: 'Widget' },
      selection: { alternatives: [] } });
    return select({ text: 'split' }, [irrelevant, REACT_BITS], {});
  },
  expect(r) {
    assert.equal(r.abstention.code, 'ALL_FILTERED');
    assert.equal(r.dominant_filter, null);
    assert.equal(r.tied_filters.length, 2);
  },
},
{
  id: 'A5-TRP-03', category: 'TRAP',
  what_it_tests: 'the matcher\'s documented limit still holds, so nobody trusts it past its boundary',
  why_it_could_fail: 'a later "improvement" silently makes matching fuzzy and unpredictable',
  run() {
    const m = btn({ identity: { id: 'primitives/b', name: 'Button' },
      quality: { known_failures: ['a child that swallows onClick disables the button'] } });
    return select({ text: 'button' }, [m], { concerns: ['clicks must always fire'] });
  },
  expect(r) {
    assert.equal(r.ranked[0].known_failures[0].relevant, false,
      'lexical matching does not connect "clicks" to onClick, and that limit is asserted');
  },
},
{
  id: 'A5-TRP-04', category: 'TRAP',
  what_it_tests: 'the query-varying term actually changes the ordering — the factors are not all constants',
  why_it_could_fail: 'a weighted sum of per-item constants ranks the catalogue identically for every query',
  run() {
    const heading = btn({ identity: { id: 'primitives/heading', name: 'Heading' }, selection: { alternatives: [] } });
    const dialog  = btn({ identity: { id: 'primitives/dialog', name: 'Dialog' }, selection: { alternatives: [] } });
    return [select({ text: 'heading' }, [heading, dialog], {}),
            select({ text: 'dialog' }, [heading, dialog], {})];
  },
  expect([h, d]) {
    assert.equal(h.ranked[0].id, 'primitives/heading');
    assert.equal(d.ranked[0].id, 'primitives/dialog');
  },
},
];

/* ------------------------------------------------------------------------- *
 * Runner — one binary pass/fail per scenario, with its metadata on failure.
 * ------------------------------------------------------------------------- */

const seen = new Set();
for (const s of SCENARIOS) {
  assert.equal(seen.has(s.id), false, `duplicate scenario id ${s.id}`);
  seen.add(s.id);

  test(`${s.id} [${s.category}] — ${s.what_it_tests}`, () => {
    let actual;
    try {
      actual = s.run();
    } catch (e) {
      assert.fail(`scenario threw during setup: ${e.message}\n` +
                  `  tests: ${s.what_it_tests}\n  stresses: ${s.why_it_could_fail}`);
    }
    try {
      s.expect(actual);
    } catch (e) {
      e.message = `${e.message}\n  property under test: ${s.what_it_tests}\n` +
                  `  failure mechanism stressed: ${s.why_it_could_fail}`;
      throw e;
    }
  });
}

test('A5-META — the corpus covers every mandated category at the declared size', () => {
  // A corpus that quietly shrinks is the ratio failure in another costume, so
  // the count and the category spread are themselves asserted.
  const byCat = {};
  for (const s of SCENARIOS) byCat[s.category] = (byCat[s.category] || 0) + 1;

  // Exact, not a floor. A corpus allowed to shrink silently is the ratio
  // failure in another costume. It grew to 41 when the upstream_health fix
  // introduced a wall-clock dependency that needed its own guard (A5-BND-08).
  assert.equal(SCENARIOS.length, 41, 'the corpus is declared as 41 scenarios');
  for (const cat of ['LEGAL', 'SELECTION', 'INSTALL', 'REGISTRY', 'BOUNDARY', 'TRAP']) {
    assert.ok(byCat[cat] >= 4, `category ${cat} has only ${byCat[cat] || 0} scenarios`);
  }
  for (const s of SCENARIOS) {
    assert.ok(s.what_it_tests && s.what_it_tests.length > 20, `${s.id} has no property statement`);
    assert.ok(s.why_it_could_fail && s.why_it_could_fail.length > 20, `${s.id} names no failure mechanism`);
  }
});
