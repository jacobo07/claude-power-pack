#!/usr/bin/env node
/*
 * license_gate.js — License Classification Gate (MC-ABS-0)
 *
 * Inspects a target directory for license signals and classifies the
 * obligation tier so a human (or installer) can decide whether to vendor
 * or wrap the upstream code. Advisory only — does not block execution.
 *
 * Usage:
 *   node lib/license_gate.js <path>              # human-readable advisory
 *   node lib/license_gate.js <path> --json       # machine-readable verdict
 *
 * Exit codes: 0 ok, 2 argv error, 3 io error.
 *
 * Detection order (first hit wins for the canonical SPDX id, but every
 * signal collected is included in the verdict for the human):
 *   1. LICENSE / LICENSE.md / LICENSE.txt / COPYING / COPYING.LESSER files
 *   2. package.json "license" field
 *   3. pyproject.toml [project] license = "..." (string form only;
 *      table form like {file = "LICENSE"} is reported as DEFER_TO_FILE)
 *   4. SPDX-License-Identifier comment in any of the above
 *
 * Tiers:
 *   PERMISSIVE       — MIT, Apache-2.0, BSD-{2,3}-Clause, ISC, 0BSD, Unlicense
 *   WEAK_COPYLEFT    — LGPL-*, MPL-2.0, EPL-2.0, CDDL-1.0
 *   STRONG_COPYLEFT  — GPL-2.0, GPL-3.0, AGPL-3.0
 *   PROPRIETARY      — UNLICENSED, SEE LICENSE IN ..., or "All rights reserved" with no permissive grant
 *   UNKNOWN          — no signal found, or signal does not match any known SPDX
 */

'use strict';

const fs = require('fs');
const path = require('path');

const LICENSE_FILES = [
  'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'LICENCE', 'LICENCE.md',
  'COPYING', 'COPYING.LESSER', 'COPYING.txt', 'UNLICENSE',
];

const TIER = {
  PERMISSIVE:      ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', '0BSD', 'Unlicense'],
  WEAK_COPYLEFT:   ['LGPL-2.1', 'LGPL-3.0', 'LGPL-2.1-or-later', 'LGPL-3.0-or-later', 'MPL-2.0', 'EPL-2.0', 'CDDL-1.0'],
  STRONG_COPYLEFT: ['GPL-2.0', 'GPL-3.0', 'GPL-2.0-or-later', 'GPL-3.0-or-later', 'AGPL-3.0', 'AGPL-3.0-or-later'],
};

const OBLIGATIONS = {
  PERMISSIVE:      'Preserve copyright + license text on redistribution. Otherwise unrestricted.',
  WEAK_COPYLEFT:   'Modifications to the upstream files themselves must remain under the same license. Linking from your own code is generally allowed.',
  STRONG_COPYLEFT: 'Distributing a derivative work requires releasing your linking code under the same license. AGPL extends this to network use. Composition-via-adapter is the safer path; vendoring + modifying is not.',
  PROPRIETARY:     'No grant of rights detected. Do not redistribute, modify, or wrap without an explicit license from the author.',
  UNKNOWN:         'Could not classify. Treat as PROPRIETARY until a human verifies upstream terms in writing.',
};

function tierFor(spdxId) {
  if (!spdxId) return 'UNKNOWN';
  const id = spdxId.trim();
  for (const [tier, list] of Object.entries(TIER)) {
    if (list.includes(id)) return tier;
  }
  if (id === 'UNLICENSED' || /^SEE LICENSE/i.test(id)) return 'PROPRIETARY';
  return 'UNKNOWN';
}

function readSafe(p) {
  try { return fs.readFileSync(p, 'utf8'); } catch (_) { return null; }
}

function detectFromText(text) {
  if (!text) return null;
  const head = text.slice(0, 4000);
  // 1. Explicit SPDX identifier
  const spdx = head.match(/SPDX-License-Identifier:\s*([A-Za-z0-9.\-+]+)/);
  if (spdx) return { spdx: spdx[1], source: 'spdx-tag' };
  // 2. Heuristic keyword match — order matters: AGPL before GPL before LGPL.
  const tests = [
    [/GNU AFFERO GENERAL PUBLIC LICENSE\s+Version 3/i, 'AGPL-3.0'],
    [/GNU LESSER GENERAL PUBLIC LICENSE\s+Version 3/i, 'LGPL-3.0'],
    [/GNU LESSER GENERAL PUBLIC LICENSE\s+Version 2\.1/i, 'LGPL-2.1'],
    [/GNU GENERAL PUBLIC LICENSE\s+Version 3/i, 'GPL-3.0'],
    [/GNU GENERAL PUBLIC LICENSE\s+Version 2/i, 'GPL-2.0'],
    [/Mozilla Public License Version 2\.0/i, 'MPL-2.0'],
    [/Eclipse Public License - v ?2\.0/i, 'EPL-2.0'],
    [/Apache License\s+Version 2\.0/i, 'Apache-2.0'],
    [/Permission is hereby granted, free of charge, to any person obtaining a copy/i, 'MIT'],
    [/Redistribution and use in source and binary forms.+three.+conditions/is, 'BSD-3-Clause'],
    [/Redistribution and use in source and binary forms.+two.+conditions/is, 'BSD-2-Clause'],
    [/Permission to use, copy, modify, and\/or distribute this software for any purpose/i, 'ISC'],
    [/This is free and unencumbered software released into the public domain/i, 'Unlicense'],
  ];
  for (const [rx, id] of tests) {
    if (rx.test(head)) return { spdx: id, source: 'heuristic' };
  }
  // 3. Proprietary smell: "All rights reserved" with no permissive verb.
  if (/All rights reserved/i.test(head) &&
      !/Permission is hereby granted/i.test(head) &&
      !/Redistribution and use/i.test(head)) {
    return { spdx: 'UNLICENSED', source: 'proprietary-marker' };
  }
  return null;
}

function detectFromPackageJson(pkgPath) {
  const txt = readSafe(pkgPath);
  if (!txt) return null;
  let parsed;
  try { parsed = JSON.parse(txt); } catch (_) { return null; }
  if (typeof parsed.license === 'string' && parsed.license.length) {
    return { spdx: parsed.license, source: 'package.json' };
  }
  if (parsed.license && typeof parsed.license === 'object' && parsed.license.type) {
    return { spdx: parsed.license.type, source: 'package.json (deprecated object form)' };
  }
  return null;
}

function detectFromPyproject(tomlPath) {
  const txt = readSafe(tomlPath);
  if (!txt) return null;
  // Minimal scan, no full TOML parser; first match wins.
  const direct = txt.match(/^\s*license\s*=\s*["']([^"']+)["']/m);
  if (direct) return { spdx: direct[1], source: 'pyproject.toml' };
  if (/^\s*license\s*=\s*\{/m.test(txt)) {
    return { spdx: null, source: 'pyproject.toml (table form, see LICENSE file)', defer: true };
  }
  return null;
}

function classify(targetDir) {
  const result = {
    target: targetDir,
    signals: [],
    canonical: null,
    tier: 'UNKNOWN',
    obligation: OBLIGATIONS.UNKNOWN,
    files_inspected: [],
  };

  if (!fs.existsSync(targetDir) || !fs.statSync(targetDir).isDirectory()) {
    throw new Error(`not a directory: ${targetDir}`);
  }

  // Pass 1 — license files.
  for (const name of LICENSE_FILES) {
    const p = path.join(targetDir, name);
    if (!fs.existsSync(p)) continue;
    result.files_inspected.push(name);
    const sig = detectFromText(readSafe(p));
    if (sig) result.signals.push({ ...sig, file: name });
  }

  // Pass 2 — package.json.
  const pkg = path.join(targetDir, 'package.json');
  if (fs.existsSync(pkg)) {
    result.files_inspected.push('package.json');
    const sig = detectFromPackageJson(pkg);
    if (sig) result.signals.push({ ...sig, file: 'package.json' });
  }

  // Pass 3 — pyproject.toml.
  const py = path.join(targetDir, 'pyproject.toml');
  if (fs.existsSync(py)) {
    result.files_inspected.push('pyproject.toml');
    const sig = detectFromPyproject(py);
    if (sig) result.signals.push({ ...sig, file: 'pyproject.toml' });
  }

  // Canonical pick: prefer SPDX-tag > license-file heuristic > manifest.
  const ranked = result.signals
    .filter(s => s.spdx)
    .sort((a, b) => {
      const order = { 'spdx-tag': 0, 'heuristic': 1, 'package.json': 2, 'pyproject.toml': 3, 'proprietary-marker': 4 };
      return (order[a.source] ?? 9) - (order[b.source] ?? 9);
    });
  if (ranked.length) {
    result.canonical = ranked[0].spdx;
    result.tier = tierFor(result.canonical);
    result.obligation = OBLIGATIONS[result.tier];
  }

  return result;
}

function renderHuman(verdict) {
  const lines = [];
  lines.push(`License Gate — ${verdict.target}`);
  lines.push('-'.repeat(40 + verdict.target.length));
  lines.push(`Files inspected: ${verdict.files_inspected.join(', ') || '(none)'}`);
  if (!verdict.signals.length) {
    lines.push('Signals: NONE — no license metadata detected.');
  } else {
    lines.push('Signals:');
    for (const s of verdict.signals) {
      lines.push(`  - ${s.file}: ${s.spdx || '(deferred)'} [${s.source}]`);
    }
  }
  lines.push(`Canonical SPDX: ${verdict.canonical || 'UNKNOWN'}`);
  lines.push(`Tier:           ${verdict.tier}`);
  lines.push(`Obligation:     ${verdict.obligation}`);
  return lines.join('\n');
}

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(
      'license_gate.js — classify a directory\'s license obligation tier.\n' +
      '\n' +
      'Usage: node lib/license_gate.js <path> [--json]\n' +
      '\n' +
      'Tiers: PERMISSIVE | WEAK_COPYLEFT | STRONG_COPYLEFT | PROPRIETARY | UNKNOWN\n'
    );
    process.exit(args.length ? 0 : 2);
  }
  const json = args.includes('--json');
  const target = args.find(a => !a.startsWith('-'));
  if (!target) {
    process.stderr.write('license_gate.js: missing <path>\n');
    process.exit(2);
  }
  let verdict;
  try {
    verdict = classify(path.resolve(target));
  } catch (e) {
    process.stderr.write(`license_gate.js: ${e.message}\n`);
    process.exit(3);
  }
  process.stdout.write((json ? JSON.stringify(verdict, null, 2) : renderHuman(verdict)) + '\n');
  process.exit(0);
}

if (require.main === module) main(process.argv);

module.exports = { classify, tierFor, detectFromText, detectFromPackageJson, detectFromPyproject, OBLIGATIONS };
