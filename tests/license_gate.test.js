#!/usr/bin/env node
/*
 * tests/license_gate.test.js — MC-ABS-0
 *
 * Unit tests for lib/license_gate.js. Uses Node's built-in test runner
 * (node:test, stable since Node 20) so there's no extra dependency.
 *
 * Run:
 *   node --test tests/license_gate.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { classify, tierFor, detectFromText } = require('../lib/license_gate');

// Real fragments — first ~20 chars of each canonical license, enough for the
// heuristic to fire without committing the full license text into the repo.
const FRAGMENTS = {
  MIT:
    'MIT License\n\n' +
    'Permission is hereby granted, free of charge, to any person obtaining a copy ' +
    'of this software and associated documentation files (the "Software"), to deal ' +
    'in the Software without restriction.',
  APACHE2:
    '                                 Apache License\n' +
    '                           Version 2.0, January 2004\n' +
    '                        http://www.apache.org/licenses/\n',
  AGPL3:
    '                    GNU AFFERO GENERAL PUBLIC LICENSE\n' +
    '                       Version 3, 19 November 2007\n',
  GPL3:
    '                    GNU GENERAL PUBLIC LICENSE\n' +
    '                       Version 3, 29 June 2007\n',
  LGPL3:
    '                   GNU LESSER GENERAL PUBLIC LICENSE\n' +
    '                       Version 3, 29 June 2007\n',
  MPL2:
    'Mozilla Public License Version 2.0\n==================================\n',
  ISC:
    'ISC License\n\n' +
    'Permission to use, copy, modify, and/or distribute this software for any purpose ' +
    'with or without fee is hereby granted.',
  PROPRIETARY:
    'Copyright (c) 2026 ACME Corp.\nAll rights reserved.\n' +
    'No part of this software may be reproduced without prior written consent.',
  SPDX_TAG:
    '/* SPDX-License-Identifier: BSD-3-Clause */\n',
};

function mkdtemp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'lg-test-'));
}

function writeLicense(dir, name, body) {
  fs.writeFileSync(path.join(dir, name), body);
  return dir;
}

function writeJson(dir, name, obj) {
  fs.writeFileSync(path.join(dir, name), JSON.stringify(obj, null, 2));
  return dir;
}

test('detectFromText — MIT heuristic', () => {
  const sig = detectFromText(FRAGMENTS.MIT);
  assert.equal(sig.spdx, 'MIT');
  assert.equal(sig.source, 'heuristic');
});

test('detectFromText — AGPL beats GPL beats LGPL (order matters)', () => {
  assert.equal(detectFromText(FRAGMENTS.AGPL3).spdx, 'AGPL-3.0');
  assert.equal(detectFromText(FRAGMENTS.GPL3).spdx, 'GPL-3.0');
  assert.equal(detectFromText(FRAGMENTS.LGPL3).spdx, 'LGPL-3.0');
});

test('detectFromText — SPDX tag wins immediately', () => {
  const sig = detectFromText(FRAGMENTS.SPDX_TAG);
  assert.equal(sig.spdx, 'BSD-3-Clause');
  assert.equal(sig.source, 'spdx-tag');
});

test('detectFromText — proprietary marker without permissive grant', () => {
  const sig = detectFromText(FRAGMENTS.PROPRIETARY);
  assert.equal(sig.spdx, 'UNLICENSED');
  assert.equal(sig.source, 'proprietary-marker');
});

test('detectFromText — empty / null returns null', () => {
  assert.equal(detectFromText(''), null);
  assert.equal(detectFromText(null), null);
});

test('tierFor — classifications', () => {
  assert.equal(tierFor('MIT'),         'PERMISSIVE');
  assert.equal(tierFor('Apache-2.0'),  'PERMISSIVE');
  assert.equal(tierFor('LGPL-3.0'),    'WEAK_COPYLEFT');
  assert.equal(tierFor('MPL-2.0'),     'WEAK_COPYLEFT');
  assert.equal(tierFor('GPL-3.0'),     'STRONG_COPYLEFT');
  assert.equal(tierFor('AGPL-3.0'),    'STRONG_COPYLEFT');
  assert.equal(tierFor('UNLICENSED'),  'PROPRIETARY');
  assert.equal(tierFor('SEE LICENSE IN ./WEIRD.txt'), 'PROPRIETARY');
  assert.equal(tierFor('Whatever-1.0'), 'UNKNOWN');
  assert.equal(tierFor(null),          'UNKNOWN');
});

test('classify — MIT LICENSE file', () => {
  const dir = writeLicense(mkdtemp(), 'LICENSE', FRAGMENTS.MIT);
  const v = classify(dir);
  assert.equal(v.canonical, 'MIT');
  assert.equal(v.tier, 'PERMISSIVE');
  assert.ok(v.signals.length >= 1);
});

test('classify — AGPL is flagged STRONG_COPYLEFT', () => {
  const dir = writeLicense(mkdtemp(), 'COPYING', FRAGMENTS.AGPL3);
  const v = classify(dir);
  assert.equal(v.canonical, 'AGPL-3.0');
  assert.equal(v.tier, 'STRONG_COPYLEFT');
  assert.match(v.obligation, /AGPL extends this to network use/);
});

test('classify — package.json license field', () => {
  const dir = writeJson(mkdtemp(), 'package.json', { name: 't', license: 'Apache-2.0' });
  const v = classify(dir);
  assert.equal(v.canonical, 'Apache-2.0');
  assert.equal(v.tier, 'PERMISSIVE');
});

test('classify — package.json UNLICENSED → PROPRIETARY', () => {
  const dir = writeJson(mkdtemp(), 'package.json', { name: 't', license: 'UNLICENSED' });
  const v = classify(dir);
  assert.equal(v.canonical, 'UNLICENSED');
  assert.equal(v.tier, 'PROPRIETARY');
});

test('classify — pyproject.toml string form', () => {
  const dir = mkdtemp();
  fs.writeFileSync(path.join(dir, 'pyproject.toml'),
    '[project]\nname = "x"\nlicense = "MIT"\n');
  const v = classify(dir);
  assert.equal(v.canonical, 'MIT');
});

test('classify — empty dir is UNKNOWN, not crash', () => {
  const dir = mkdtemp();
  const v = classify(dir);
  assert.equal(v.canonical, null);
  assert.equal(v.tier, 'UNKNOWN');
  assert.equal(v.signals.length, 0);
});

test('classify — LICENSE file beats package.json (heuristic > manifest)', () => {
  const dir = mkdtemp();
  writeLicense(dir, 'LICENSE', FRAGMENTS.AGPL3);
  writeJson(dir, 'package.json', { name: 't', license: 'MIT' });
  const v = classify(dir);
  // Heuristic from LICENSE file should win because of the source ranking.
  assert.equal(v.canonical, 'AGPL-3.0');
  assert.equal(v.tier, 'STRONG_COPYLEFT');
  // But both signals should be reported for the human.
  assert.equal(v.signals.length, 2);
});

test('classify — non-existent dir throws', () => {
  assert.throws(() => classify('/no/such/path/exists/here/probably'), /not a directory/);
});
