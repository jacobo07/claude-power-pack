#!/usr/bin/env node
/*
 * tests/component_manifest.test.js — CDICF A2
 *
 * Validates the Component Manifest schema and the six cross-field invariants.
 *
 * The load-bearing case is INV-02: a component whose license prohibits
 * redistribution may not be recorded as a fork. That is the structural form of
 * the 2026-08-06 Owner decision on react-bits — enforced here so it survives
 * everyone forgetting it.
 *
 * Run:
 *   node --test tests/component_manifest.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { validate, validateFile, checkInvariants, loadSchema } =
  require('../modules/cdicf/validate_manifest');

const EXAMPLES = path.join(__dirname, '..', 'modules', 'cdicf', 'examples');
const REACT_BITS = path.join(EXAMPLES, 'react-bits.split-text.json');
const SHADCN     = path.join(EXAMPLES, 'shadcn-ui.button.json');

const SCHEMA = loadSchema();

function base() {
  return JSON.parse(fs.readFileSync(SHADCN, 'utf8'));
}

function rulesIn(result) {
  return result.errors.map(e => e.rule);
}

/* ---------------- Shipped examples ------------------------------------- */

test('V-MANIFEST-01 — the gateway_upstream example validates (react-bits)', () => {
  const r = validateFile(REACT_BITS, SCHEMA);
  assert.equal(r.valid, true, JSON.stringify(r.errors, null, 2));
});

test('V-MANIFEST-02 — the fork_canonical example validates (shadcn/ui)', () => {
  const r = validateFile(SHADCN, SCHEMA);
  assert.equal(r.valid, true, JSON.stringify(r.errors, null, 2));
});

test('V-MANIFEST-03 — the two examples cover two distinct integration modes', () => {
  const a = JSON.parse(fs.readFileSync(REACT_BITS, 'utf8'));
  const b = JSON.parse(fs.readFileSync(SHADCN, 'utf8'));
  assert.equal(a.provenance.integration_mode, 'gateway_upstream');
  assert.equal(b.provenance.integration_mode, 'fork_canonical');
  assert.notEqual(a.provenance.redistribution_posture, b.provenance.redistribution_posture);
});

/* ---------------- INV-02: the load-bearing invariant -------------------- */

test('V-MANIFEST-INV02 — a prohibited component CANNOT be recorded as a fork', () => {
  // Arrange — take the real react-bits manifest and try to fork it.
  const m = JSON.parse(fs.readFileSync(REACT_BITS, 'utf8'));
  m.provenance.integration_mode = 'fork_canonical';

  // Act
  const r = validate(m, SCHEMA);

  // Assert — this is the license violation the whole system exists to prevent.
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-02'), JSON.stringify(r.errors));
});

test('V-MANIFEST-INV02b — metadata_only is the other lawful mode for prohibited', () => {
  const m = JSON.parse(fs.readFileSync(REACT_BITS, 'utf8'));
  m.provenance.integration_mode = 'metadata_only';
  assert.equal(validate(m, SCHEMA).valid, true);
});

/* ---------------- INV-01: one vocabulary, not two ----------------------- */

test('V-MANIFEST-INV01 — posture must match what license_gate derives from the tier', () => {
  const m = base();
  m.provenance.redistribution_posture = 'prohibited'; // PERMISSIVE derives 'allowed'
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-01'));
  // And the message names the gate as the authority, not this file.
  assert.match(r.errors.find(e => e.rule === 'INV-01').message, /license_gate\.js/);
});

test('V-MANIFEST-INV01b — a RESTRICTED tier claiming allowed is rejected', () => {
  const m = base();
  m.provenance.license_tier = 'SOURCE_AVAILABLE_RESTRICTED';
  // posture left as 'allowed'
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-01'));
});

/* ---------------- INV-03..06 -------------------------------------------- */

test('V-MANIFEST-INV03 — prohibited requires notice_required true', () => {
  const m = JSON.parse(fs.readFileSync(REACT_BITS, 'utf8'));
  m.provenance.notice_required = false;
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-03'));
});

test('V-MANIFEST-INV04 — VERIFIED requires a pinned commit and fingerprint', () => {
  const m = base();
  m.provenance.confidence = 'VERIFIED';   // fingerprint is PENDING_CLONE
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-04'));

  m.identity.commit_sha = 'PENDING_CLONE';
  const r2 = validate(m, SCHEMA);
  assert.equal(r2.errors.filter(e => e.rule === 'INV-04').length, 2,
    'both the unpinned commit and the unpinned fingerprint must be reported');
});

test('V-MANIFEST-INV05 — cannot prefer a component with unmeasured accessibility', () => {
  const m = base();
  m.quality.wcag_level = 'unassessed';    // recommendation is already 'prefer'
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-05'));
});

test('V-MANIFEST-INV06 — high motion requires a reduced-motion path', () => {
  const m = base();
  m.capability.motion_budget = 'high';
  m.quality.reduced_motion_compliant = false;
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('INV-06'));
});

/* ---------------- Structural validation --------------------------------- */

test('V-MANIFEST-04 — unknown top-level keys are rejected', () => {
  const m = base();
  m._notes = 'commentary belongs in the README';
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('additionalProperties'));
});

test('V-MANIFEST-05 — a missing required section is reported by name', () => {
  const m = base();
  delete m.provenance;
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(r.errors.some(e => e.rule === 'required' && e.path === 'provenance'));
});

test('V-MANIFEST-06 — a branch name is not a commit pin', () => {
  const m = base();
  m.identity.commit_sha = 'main';
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(r.errors.some(e => e.path === 'identity.commit_sha'));
});

test('V-MANIFEST-07 — an out-of-vocabulary enum value is rejected', () => {
  const m = base();
  m.provenance.integration_mode = 'vendor_and_hope';
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('enum'));
});

test('V-MANIFEST-08 — an empty copyright_holder is rejected', () => {
  // An MIT notice cannot be written without a name. This is the schema-level
  // form of the Tailark blocker resolved on 2026-08-06.
  const m = base();
  m.provenance.copyright_holder = '';
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('minLength'));
});

test('V-MANIFEST-09 — identity_fit_score is bounded 0..100', () => {
  const m = base();
  m.selection.identity_fit_score = 140;
  assert.equal(validate(m, SCHEMA).valid, false);
  m.selection.identity_fit_score = -1;
  assert.equal(validate(m, SCHEMA).valid, false);
});

test('V-MANIFEST-10 — a non-ISO date is rejected', () => {
  const m = base();
  m.lifecycle.added_date = '06/08/2026';
  const r = validate(m, SCHEMA);
  assert.equal(r.valid, false);
  assert.ok(rulesIn(r).includes('format'));
});

test('V-MANIFEST-11 — invariants do not run on a structurally broken manifest', () => {
  // Otherwise every invariant reports a cascade of the same missing field and
  // the real error is buried.
  const r = validate({}, SCHEMA);
  assert.equal(r.valid, false);
  assert.equal(r.errors.every(e => e.rule === 'required'), true, JSON.stringify(r.errors));
});

test('V-MANIFEST-12 — checkInvariants is null-safe on partial input', () => {
  assert.deepEqual(checkInvariants({}), []);
});

test('V-MANIFEST-13 — schema declares all six invariants for the reader', () => {
  const ids = SCHEMA.cdicfInvariants.map(i => i.id);
  assert.deepEqual(ids, ['INV-01', 'INV-02', 'INV-03', 'INV-04', 'INV-05', 'INV-06']);
  // Each carries a stated reason; a rule with no why is a rule nobody can revise.
  for (const inv of SCHEMA.cdicfInvariants) {
    assert.ok(inv.why && inv.why.length > 20, `${inv.id} has no substantive rationale`);
  }
});
