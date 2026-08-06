#!/usr/bin/env node
/*
 * license_gate.js — License Classification Gate (MC-ABS-0, hardened CDICF-A1)
 *
 * Inspects a target directory for license signals and classifies the
 * obligation tier so a human (or installer) can decide whether to vendor
 * or wrap the upstream code.
 *
 * Usage:
 *   node lib/license_gate.js <path>                 # human-readable advisory
 *   node lib/license_gate.js <path> --json          # machine-readable verdict
 *   node lib/license_gate.js <path> --strict        # exit 5 if redistribution prohibited
 *   node lib/license_gate.js <path> --expect <sha>  # exit 4 if license text drifted
 *
 * Exit codes: 0 ok, 2 argv error, 3 io error, 4 license drift, 5 restricted (--strict).
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
 *   PERMISSIVE                 — MIT, Apache-2.0, BSD-{2,3}-Clause, ISC, 0BSD, Unlicense
 *   WEAK_COPYLEFT              — LGPL-*, MPL-2.0, EPL-2.0, CDDL-1.0
 *   STRONG_COPYLEFT            — GPL-2.0, GPL-3.0, AGPL-3.0
 *   SOURCE_AVAILABLE_RESTRICTED— a permissive base license with an appended clause
 *                                that withdraws sale/sublicense/redistribution rights
 *                                (Commons Clause, BUSL, SSPL, Elastic, NC terms)
 *   PROPRIETARY                — UNLICENSED, SEE LICENSE IN ..., or "All rights reserved"
 *                                with no permissive grant
 *   UNKNOWN                    — no signal found, or signal matches no known SPDX
 *
 * WHY THE RESTRICTION PASS EXISTS (CDICF Phase 1, 2026-08-06)
 * ----------------------------------------------------------
 * The previous revision matched the MIT grant sentence inside a first-hit-wins
 * loop over `text.slice(0, 4000)` and returned immediately. Against
 * DavidHDev/react-bits — MIT + Commons Clause Restriction v1.0 — it emitted
 * tier PERMISSIVE and the obligation "Otherwise unrestricted", on a component
 * set whose license forbids redistribution "alone, in a bundle, or as a ported
 * version". The gate did not merely fail to prevent the violation; it
 * authorized it. Two structural fixes:
 *   (a) base-license detection and restriction detection are SEPARATE passes.
 *       The base pass still stops at the first match (that is correct — the
 *       canonical id is the first license named). The restriction pass scans
 *       the WHOLE file and collects EVERY hit, because appended clauses live
 *       below the base text and there may be more than one.
 *   (b) a restriction outranks the base tier. A permissive base with a
 *       withdrawal clause is SOURCE_AVAILABLE_RESTRICTED, never PERMISSIVE.
 * A tier vocabulary with no restricted value cannot express the outcome, so
 * even correct detection had nowhere to land. Both halves were required.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const LICENSE_FILES = [
  'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'LICENCE', 'LICENCE.md', 'LICENCE.txt',
  'COPYING', 'COPYING.LESSER', 'COPYING.txt', 'UNLICENSE',
];

/* Base-license heuristics read this many chars. Wide enough for the header of
 * any real license, narrow enough that a passing mention of another license
 * deep in a long file cannot hijack the canonical id. */
const BASE_SCAN_CHARS = 8000;

const TIER = {
  PERMISSIVE:      ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', '0BSD', 'Unlicense'],
  WEAK_COPYLEFT:   ['LGPL-2.1', 'LGPL-3.0', 'LGPL-2.1-or-later', 'LGPL-3.0-or-later', 'MPL-2.0', 'EPL-2.0', 'CDDL-1.0'],
  STRONG_COPYLEFT: ['GPL-2.0', 'GPL-3.0', 'GPL-2.0-or-later', 'GPL-3.0-or-later', 'AGPL-3.0', 'AGPL-3.0-or-later'],
};

const OBLIGATIONS = {
  PERMISSIVE:      'Preserve copyright + license text on redistribution. Otherwise unrestricted.',
  WEAK_COPYLEFT:   'Modifications to the upstream files themselves must remain under the same license. Linking from your own code is generally allowed.',
  STRONG_COPYLEFT: 'Distributing a derivative work requires releasing your linking code under the same license. AGPL extends this to network use. Composition-via-adapter is the safer path; vendoring + modifying is not.',
  SOURCE_AVAILABLE_RESTRICTED:
                   'Usable INSIDE your own application; redistribution of the components themselves is withdrawn — including alone, bundled, renamed, or ported. Do NOT vendor into a distributed registry. Integrate by gateway/adapter that installs from the upstream source, preserve provenance, and keep an exit plan.',
  PROPRIETARY:     'No grant of rights detected. Do not redistribute, modify, or wrap without an explicit license from the author.',
  UNKNOWN:         'Could not classify. Treat as PROPRIETARY until a human verifies upstream terms in writing.',
};

/* Redistribution posture implied by each tier. This is the field an installer
 * or registry emitter should branch on — never the SPDX id alone, because
 * "MIT" is true of react-bits and says nothing useful about it. */
const REDISTRIBUTION_BY_TIER = {
  PERMISSIVE:                  'allowed',
  WEAK_COPYLEFT:               'conditional',
  STRONG_COPYLEFT:             'conditional',
  SOURCE_AVAILABLE_RESTRICTED: 'prohibited',
  PROPRIETARY:                 'prohibited',
  UNKNOWN:                     'unknown',
};

/* Appended clauses that withdraw rights a permissive base license granted.
 * Each entry: [regex, clause name, what it withdraws].
 * These are matched against the ENTIRE license text, not a head window —
 * a withdrawal clause is appended BELOW the grant it modifies. */
const RESTRICTION_CLAUSES = [
  [/Commons\s+Clause/i,
    'Commons Clause', 'sale of the software'],
  [/the\s+License\s+does\s+not\s+grant\s+to\s+you,?\s+the\s+right\s+to\s+Sell/i,
    'Commons Clause (canonical wording)', 'the right to Sell'],
  [/Business\s+Source\s+License/i,
    'Business Source License', 'production use until the change date'],
  [/Server\s+Side\s+Public\s+License/i,
    'SSPL', 'offering as a service without releasing the service source'],
  [/Elastic\s+License/i,
    'Elastic License', 'providing the software as a hosted service'],
  [/\bNon[-\s]?Commercial\b/i,
    'NonCommercial term', 'commercial use'],
  [/\bmay\s+not\s+(?:be\s+)?(?:sell|sold|resell|resold|sublicens\w*|redistribut\w*)/i,
    'explicit prohibition', 'sale, sublicense or redistribution'],
  [/(?:you\s+may\s+not|shall\s+not|are\s+not\s+permitted\s+to)[\s\S]{0,120}?\b(?:sell|resell|sublicense|redistribute)\b/i,
    'explicit prohibition', 'sale, sublicense or redistribution'],
  [/\b(?:prohibited|forbidden)\b[\s\S]{0,80}?\b(?:sell|resell|sublicens\w*|redistribut\w*)/i,
    'explicit prohibition', 'sale, sublicense or redistribution'],
  [/redistribute\s+the\s+components?\s+themselves/i,
    'component redistribution ban', 'redistributing components alone, bundled or ported'],
];

function tierFor(spdxId) {
  if (!spdxId) return 'UNKNOWN';
  const id = spdxId.trim();
  // A composite id carrying a restriction name is restricted regardless of base.
  if (/Commons\s+Clause|Business\s+Source|SSPL|Elastic\s+License/i.test(id)) {
    return 'SOURCE_AVAILABLE_RESTRICTED';
  }
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
  const head = text.slice(0, BASE_SCAN_CHARS);
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

/*
 * Second pass. Scans the WHOLE text and returns EVERY withdrawal clause found.
 * Never returns early: a file may append more than one restriction, and the
 * strictest is not necessarily the first.
 */
function detectRestrictions(text) {
  if (!text) return [];
  const found = [];
  const seen = new Set();
  for (const [rx, clause, withdraws] of RESTRICTION_CLAUSES) {
    const m = text.match(rx);
    if (!m) continue;
    if (seen.has(clause)) continue;
    seen.add(clause);
    // Capture a short excerpt so the human sees the actual words, not our label.
    const at = m.index || 0;
    const excerpt = text.slice(at, at + 180).replace(/\s+/g, ' ').trim();
    found.push({ clause, withdraws, excerpt });
  }
  return found;
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
    restrictions: [],
    canonical: null,
    tier: 'UNKNOWN',
    redistribution: 'unknown',
    obligation: OBLIGATIONS.UNKNOWN,
    files_inspected: [],
    fingerprint: null,
  };

  if (!fs.existsSync(targetDir) || !fs.statSync(targetDir).isDirectory()) {
    throw new Error(`not a directory: ${targetDir}`);
  }

  const hash = crypto.createHash('sha256');
  let hashedAnything = false;

  // Pass 1 — license files: base license signal + restriction scan + fingerprint.
  for (const name of LICENSE_FILES) {
    const p = path.join(targetDir, name);
    if (!fs.existsSync(p)) continue;
    result.files_inspected.push(name);
    const body = readSafe(p);
    if (body !== null) {
      hash.update(`${name}\n${body}\n`);
      hashedAnything = true;
    }
    const sig = detectFromText(body);
    if (sig) result.signals.push({ ...sig, file: name });
    for (const r of detectRestrictions(body)) {
      result.restrictions.push({ ...r, file: name });
    }
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
  }

  // A withdrawal clause OUTRANKS the base tier. This is the whole point of the
  // pass: "MIT" is a true statement about react-bits and a useless one.
  // PROPRIETARY is already stricter, so it is not downgraded.
  if (result.restrictions.length && result.tier !== 'PROPRIETARY') {
    result.tier = 'SOURCE_AVAILABLE_RESTRICTED';
    if (result.canonical) {
      const names = [...new Set(result.restrictions.map(r => r.clause))].join(' + ');
      result.canonical = `${result.canonical} + ${names}`;
    }
  }

  result.obligation = OBLIGATIONS[result.tier];
  result.redistribution = REDISTRIBUTION_BY_TIER[result.tier];
  result.fingerprint = hashedAnything ? hash.digest('hex') : null;

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
  if (verdict.restrictions.length) {
    lines.push('RESTRICTIONS DETECTED:');
    for (const r of verdict.restrictions) {
      lines.push(`  ! ${r.file}: ${r.clause} — withdraws ${r.withdraws}`);
      lines.push(`      "${r.excerpt}"`);
    }
  }
  lines.push(`Canonical SPDX: ${verdict.canonical || 'UNKNOWN'}`);
  lines.push(`Tier:           ${verdict.tier}`);
  lines.push(`Redistribution: ${verdict.redistribution.toUpperCase()}`);
  lines.push(`Obligation:     ${verdict.obligation}`);
  lines.push(`Fingerprint:    ${verdict.fingerprint || '(no license file)'}`);
  return lines.join('\n');
}

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(
      'license_gate.js — classify a directory\'s license obligation tier.\n' +
      '\n' +
      'Usage: node lib/license_gate.js <path> [--json] [--strict] [--expect <sha256>]\n' +
      '\n' +
      '  --json           machine-readable verdict\n' +
      '  --strict         exit 5 when redistribution is prohibited\n' +
      '  --expect <sha>   exit 4 when the license text no longer matches <sha>\n' +
      '\n' +
      'Tiers: PERMISSIVE | WEAK_COPYLEFT | STRONG_COPYLEFT |\n' +
      '       SOURCE_AVAILABLE_RESTRICTED | PROPRIETARY | UNKNOWN\n'
    );
    process.exit(args.length ? 0 : 2);
  }
  const json = args.includes('--json');
  const strict = args.includes('--strict');
  const expectIdx = args.indexOf('--expect');
  const expected = expectIdx !== -1 ? args[expectIdx + 1] : null;
  if (expectIdx !== -1 && (!expected || expected.startsWith('-'))) {
    process.stderr.write('license_gate.js: --expect requires a sha256 value\n');
    process.exit(2);
  }
  const flagValues = new Set(expected ? [expected] : []);
  const target = args.find(a => !a.startsWith('-') && !flagValues.has(a));
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

  // Drift beats strictness: a changed license invalidates every artifact
  // derived from the old one, so the human must see that first.
  if (expected && verdict.fingerprint !== expected) {
    process.stderr.write(
      `license_gate.js: LICENSE DRIFT — expected ${expected}, got ${verdict.fingerprint}. ` +
      'Every artifact derived from the previous snapshot is invalidated until re-reviewed.\n'
    );
    process.exit(4);
  }
  if (strict && verdict.redistribution === 'prohibited') {
    process.stderr.write(
      `license_gate.js: REDISTRIBUTION PROHIBITED (${verdict.tier}). ` +
      'Gateway/adapter integration only — do not vendor into a distributed registry.\n'
    );
    process.exit(5);
  }
  process.exit(0);
}

if (require.main === module) main(process.argv);

module.exports = {
  classify, tierFor, detectFromText, detectRestrictions,
  detectFromPackageJson, detectFromPyproject,
  OBLIGATIONS, REDISTRIBUTION_BY_TIER, RESTRICTION_CLAUSES,
};
