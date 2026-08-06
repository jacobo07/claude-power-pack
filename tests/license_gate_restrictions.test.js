#!/usr/bin/env node
/*
 * tests/license_gate_restrictions.test.js — CDICF-A1
 *
 * Covers the restriction pass added to lib/license_gate.js on 2026-08-06.
 *
 * The founding case: DavidHDev/react-bits ships MIT + Commons Clause
 * Restriction v1.0 in LICENSE.md. The previous gate returned PERMISSIVE /
 * "Otherwise unrestricted" for it. These tests fail if that ever returns.
 *
 * Run:
 *   node --test tests/license_gate_restrictions.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  classify, tierFor, detectRestrictions, REDISTRIBUTION_BY_TIER, OBLIGATIONS,
} = require('../lib/license_gate');

const MIT_BODY =
  'MIT License\n\n' +
  'Copyright (c) 2026 David Haz\n\n' +
  'Permission is hereby granted, free of charge, to any person obtaining a copy ' +
  'of this software and associated documentation files (the "Software"), to deal ' +
  'in the Software without restriction, including without limitation the rights ' +
  'to use, copy, modify, merge, publish, distribute, sublicense, and/or sell ' +
  'copies of the Software, and to permit persons to whom the Software is ' +
  'furnished to do so, subject to the following conditions:\n';

/* Canonical Commons Clause wording, as appended below an MIT grant. */
const COMMONS_CLAUSE =
  '\n\n"Commons Clause" License Condition v1.0\n\n' +
  'The Software is provided to you by the Licensor under the License, as defined ' +
  'below, subject to the following condition. Without limiting other conditions in ' +
  'the License, the grant of rights under the License will not include, and the ' +
  'License does not grant to you, the right to Sell the Software.\n';

/* React Bits' own summary wording, as reported by its LICENSE.md. */
const REACT_BITS_TERM =
  '\n\nYou may not sell, sublicense, or redistribute the components themselves — ' +
  'whether alone, in a bundle, or as a ported version.\n';

function mkdtemp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'lgr-test-'));
}

function writeFileIn(dir, name, body) {
  fs.writeFileSync(path.join(dir, name), body);
  return dir;
}

/* ---------------- V-LICENSE-RESTRICT-01 — the founding case ------------- */

test('V-LICENSE-RESTRICT-01 — MIT + Commons Clause in LICENSE.md is RESTRICTED, not PERMISSIVE', () => {
  // Arrange — react-bits' real shape: the terms live in LICENSE.md, not LICENSE.
  const dir = writeFileIn(mkdtemp(), 'LICENSE.md', MIT_BODY + COMMONS_CLAUSE);

  // Act
  const v = classify(dir);

  // Assert — the exact three values that were wrong before.
  assert.equal(v.tier, 'SOURCE_AVAILABLE_RESTRICTED');
  assert.equal(v.redistribution, 'prohibited');
  assert.notEqual(v.obligation, OBLIGATIONS.PERMISSIVE);
  assert.match(v.obligation, /do NOT vendor into a distributed registry/i);
  // The base license is still reported — it is true, just not sufficient.
  assert.match(v.canonical, /^MIT \+ /);
  assert.ok(v.restrictions.length >= 1);
  assert.equal(v.restrictions[0].file, 'LICENSE.md');
});

test('V-LICENSE-RESTRICT-02 — react-bits component-redistribution wording is caught', () => {
  const dir = writeFileIn(mkdtemp(), 'LICENSE.md', MIT_BODY + REACT_BITS_TERM);
  const v = classify(dir);
  assert.equal(v.tier, 'SOURCE_AVAILABLE_RESTRICTED');
  assert.equal(v.redistribution, 'prohibited');
});

/* ---------------- V-LICENSE-RESTRICT-03 — the window bug ---------------- */

test('V-LICENSE-RESTRICT-03 — a clause past 8000 chars is still found', () => {
  // Arrange — the old code read only text.slice(0, 4000). Bury the clause
  // far below any head window; the restriction pass must scan the whole file.
  const filler = '\n' + 'This paragraph is padding to push the clause down. '.repeat(400);
  assert.ok(MIT_BODY.length + filler.length > 8000, 'padding must exceed the base-scan window');
  const dir = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY + filler + COMMONS_CLAUSE);

  const v = classify(dir);

  // Base license still detected from the head...
  assert.match(v.canonical, /^MIT/);
  // ...and the buried clause still caught.
  assert.equal(v.tier, 'SOURCE_AVAILABLE_RESTRICTED');
  assert.equal(v.redistribution, 'prohibited');
});

/* ---------------- V-LICENSE-RESTRICT-04 — no first-hit-wins ------------- */

test('V-LICENSE-RESTRICT-04 — every distinct clause is collected, not just the first', () => {
  const dir = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY + COMMONS_CLAUSE + REACT_BITS_TERM);
  const v = classify(dir);
  const clauses = new Set(v.restrictions.map(r => r.clause));
  assert.ok(clauses.size >= 2, `expected >= 2 distinct clauses, got ${clauses.size}`);
  // Each carries the real words, not just our label.
  for (const r of v.restrictions) {
    assert.ok(r.excerpt.length > 0);
    assert.ok(r.withdraws.length > 0);
  }
});

/* ---------------- V-LICENSE-RESTRICT-05 — no false positives ------------ */

test('V-LICENSE-RESTRICT-05 — plain MIT stays PERMISSIVE (grant verbs must not trip)', () => {
  // MIT itself contains "without restriction", "sublicense", "sell" and
  // "distribute". None of those is a withdrawal. A gate that trips here would
  // block every permissive upstream in the estate.
  const dir = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY);
  const v = classify(dir);
  assert.equal(v.restrictions.length, 0);
  assert.equal(v.tier, 'PERMISSIVE');
  assert.equal(v.redistribution, 'allowed');
});

test('V-LICENSE-RESTRICT-06 — GPL-3.0 negation wording is not a redistribution ban', () => {
  // GPL says "You may not propagate or modify..." and "Sublicensing is not
  // allowed". Neither withdraws redistribution — GPL is conditional, not
  // prohibited. Locking this stops the pass drifting into over-blocking.
  const gpl =
    '                    GNU GENERAL PUBLIC LICENSE\n' +
    '                       Version 3, 29 June 2007\n\n' +
    'Sublicensing is not allowed; section 10 makes it unnecessary.\n\n' +
    'You may not propagate or modify a covered work except as expressly ' +
    'provided under this License. Any attempt otherwise to propagate or modify ' +
    'it is void, and will automatically terminate your rights under this License.\n\n' +
    'You may not impose any further restrictions on the exercise of the rights ' +
    'granted or affirmed under this License.\n';
  const dir = writeFileIn(mkdtemp(), 'LICENSE', gpl);
  const v = classify(dir);
  assert.equal(v.restrictions.length, 0, 'GPL must not be read as a redistribution ban');
  assert.equal(v.tier, 'STRONG_COPYLEFT');
  assert.equal(v.redistribution, 'conditional');
});

/* ---------------- V-LICENSE-RESTRICT-07 — precedence -------------------- */

test('V-LICENSE-RESTRICT-07 — PROPRIETARY is not downgraded by a restriction', () => {
  const proprietary =
    'Copyright (c) 2026 ACME Corp.\nAll rights reserved.\n' +
    'You may not sell or redistribute this software.\n';
  const dir = writeFileIn(mkdtemp(), 'LICENSE', proprietary);
  const v = classify(dir);
  assert.equal(v.tier, 'PROPRIETARY', 'restricted is looser than proprietary; never relax');
  assert.equal(v.redistribution, 'prohibited');
});

test('V-LICENSE-RESTRICT-08 — tierFor recognises a composite id', () => {
  assert.equal(tierFor('MIT + Commons Clause'), 'SOURCE_AVAILABLE_RESTRICTED');
  assert.equal(tierFor('Business Source License 1.1'), 'SOURCE_AVAILABLE_RESTRICTED');
  // Untouched base behaviour.
  assert.equal(tierFor('MIT'), 'PERMISSIVE');
});

/* ---------------- V-LICENSE-RESTRICT-09 — drift fingerprint ------------- */

test('V-LICENSE-RESTRICT-09 — fingerprint is stable and moves when the text changes', () => {
  const a = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY);
  const b = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY);
  const c = writeFileIn(mkdtemp(), 'LICENSE', MIT_BODY + COMMONS_CLAUSE);

  const fa = classify(a).fingerprint;
  const fb = classify(b).fingerprint;
  const fc = classify(c).fingerprint;

  assert.equal(fa, fb, 'identical text must fingerprint identically');
  assert.notEqual(fa, fc, 'appended clause must change the fingerprint');
  assert.match(fa, /^[0-9a-f]{64}$/);
});

test('V-LICENSE-RESTRICT-10 — dir with no license file has a null fingerprint, no crash', () => {
  const v = classify(mkdtemp());
  assert.equal(v.fingerprint, null);
  assert.equal(v.tier, 'UNKNOWN');
  assert.equal(v.redistribution, 'unknown');
});

/* ---------------- V-LICENSE-RESTRICT-11 — contract completeness --------- */

test('V-LICENSE-RESTRICT-11 — every tier maps to a redistribution posture and an obligation', () => {
  const tiers = [
    'PERMISSIVE', 'WEAK_COPYLEFT', 'STRONG_COPYLEFT',
    'SOURCE_AVAILABLE_RESTRICTED', 'PROPRIETARY', 'UNKNOWN',
  ];
  for (const t of tiers) {
    assert.ok(REDISTRIBUTION_BY_TIER[t], `no redistribution posture for tier ${t}`);
    assert.ok(OBLIGATIONS[t], `no obligation text for tier ${t}`);
  }
});

test('V-LICENSE-RESTRICT-12 — detectRestrictions is pure and null-safe', () => {
  assert.deepEqual(detectRestrictions(''), []);
  assert.deepEqual(detectRestrictions(null), []);
  assert.deepEqual(detectRestrictions(MIT_BODY), []);
  assert.ok(detectRestrictions(MIT_BODY + COMMONS_CLAUSE).length >= 1);
});
