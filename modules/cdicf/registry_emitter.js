#!/usr/bin/env node
/*
 * modules/cdicf/registry_emitter.js — CDICF A3
 *
 * Turns a validated Component Manifest (A2) into a shadcn-format CPP Design
 * Registry entry plus a deterministic install manifest.
 *
 * Usage:
 *   node modules/cdicf/registry_emitter.js <manifest.json> [options]
 *
 *   --artifacts <dir>   local files to distribute (required for fork_* modes)
 *   --reference-only    emit a code-free upstream pointer (see ARTIFACT CLASSES)
 *   --out <dir>         write registry-item.json + install-manifest.json
 *   --json              machine-readable result on stdout
 *
 * Exit codes:
 *   0 emitted · 2 argv · 3 io · 4 manifest invalid ·
 *   5 REDISTRIBUTION PROHIBITED · 6 no artifacts for a fork mode ·
 *   7 mode/flag mismatch
 *
 * WHY THIS FILE IS THE POINT OF THE WHOLE SYSTEM
 * ----------------------------------------------
 * A2's INV-02 says a redistribution-prohibited component may not be recorded
 * as a fork. That is a validation rule: it constrains what a manifest may
 * *say*. It does not constrain what the system may *do*, because nothing was
 * consuming it. A3 is where INV-02 stops being a schema opinion and becomes a
 * system boundary — the registry is the distribution channel, so refusing here
 * is refusing to redistribute.
 *
 * POSTURE IS DERIVED, NOT READ
 * ----------------------------
 * The emitter does NOT trust `provenance.redistribution_posture`. It derives
 * the posture from `provenance.license_tier` through the license gate's own
 * REDISTRIBUTION_BY_TIER table. INV-01 already forces the two to agree, but a
 * guard that reads the field it is guarding is not a guard: a hand-edited
 * manifest that never went through the validator would walk straight past it.
 * The tier is the fact; the posture field is a convenience copy of it.
 *
 * ARTIFACT CLASSES — and an open decision for the Owner
 * -----------------------------------------------------
 * Two things are called "a registry entry" and only one of them is
 * redistribution:
 *
 *   local-artifacts  — the entry carries `files[]` with real content. Shipping
 *                      this IS redistributing the component. Refused outright
 *                      when the license prohibits redistribution.
 *   upstream-pointer — the entry carries NO file content at all: a name, a
 *                      provenance block, and an install command that fetches
 *                      from the upstream's own registry. Nothing of the
 *                      component travels through CPP.
 *
 * The strict rule (prohibited => refuse, exit 5, no output) is the DEFAULT and
 * covers both classes. `--reference-only` opts into the pointer class for a
 * prohibited component. It is gated to integration_mode gateway_upstream or
 * metadata_only, it can never emit a byte of component code, and it warns on
 * stderr. Without it the CPP Motion Gateway namespace cannot exist at all,
 * since every component in it is prohibited by construction — so the flag is
 * the lawful path the sealed architecture requires, not a loophole in it.
 *
 * RATIFIED by the Owner 2026-08-06 (decision D-011): redistribution is the
 * movement of the code, and a URL is not code. The Motion Gateway namespace is
 * in scope, with `--reference-only` as its emission mode.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const { REDISTRIBUTION_BY_TIER } = require('../../lib/license_gate');
const { validate, loadSchema } = require('./validate_manifest');

const REFERENCE_ONLY_MODES = ['gateway_upstream', 'metadata_only'];
const FORK_MODES = ['fork_canonical', 'fork_specialized', 'adapter', 'passthrough'];

/* component_type -> shadcn registry item type. */
const REGISTRY_TYPE = {
  primitive:   'registry:ui',
  block:       'registry:block',
  page:        'registry:page',
  composition: 'registry:block',
  hook:        'registry:hook',
  theme:       'registry:theme',
  adapter:     'registry:lib',
  effect:      'registry:component',
};

const REFUSAL = {
  MANIFEST_INVALID:          { exit: 4 },
  REDISTRIBUTION_PROHIBITED: { exit: 5 },
  NO_ARTIFACTS:              { exit: 6 },
  MODE_MISMATCH:             { exit: 7 },
};

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function refuse(code, reason, detail) {
  return { ok: false, refusal: { code, reason, detail: detail || null, exit: REFUSAL[code].exit } };
}

/*
 * Walks `dir` and returns [{ path, sha256, bytes }] sorted by path.
 * Sorting is not cosmetic: the roll-up checksum is computed over this list, so
 * an unsorted walk would produce a different checksum for identical content on
 * a different filesystem.
 */
function collectArtifacts(dir) {
  const out = [];
  const walk = (abs, rel) => {
    for (const entry of fs.readdirSync(abs, { withFileTypes: true })) {
      const childAbs = path.join(abs, entry.name);
      const childRel = rel ? `${rel}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(childAbs, childRel);
      else if (entry.isFile()) {
        const buf = fs.readFileSync(childAbs);
        out.push({ path: childRel, sha256: sha256(buf), bytes: buf.length, _abs: childAbs });
      }
    }
  };
  walk(dir, '');
  return out.sort((a, b) => a.path.localeCompare(b.path));
}

function rollupChecksum(artifacts) {
  // Stable digest over the artifact list. Empty list yields the digest of the
  // empty string rather than null, so a pointer entry still has a checksum to
  // compare against on the next emission.
  return sha256(artifacts.map(a => `${a.path}:${a.sha256}`).join('\n'));
}

function registryName(manifest) {
  return manifest.identity.id.split('/').pop();
}

function provenanceBlock(manifest, derivedPosture) {
  const p = manifest.provenance;
  return {
    upstream_repo:          manifest.identity.upstream_repo,
    upstream_namespace:     manifest.identity.upstream_namespace,
    commit_sha:             manifest.identity.commit_sha,
    license_tier:           p.license_tier,
    redistribution_posture: derivedPosture,
    integration_mode:       p.integration_mode,
    license_fingerprint:    p.license_fingerprint,
    copyright_holder:       p.copyright_holder,
    notice_required:        p.notice_required,
    fetch_date:             p.fetch_date,
    confidence:             p.confidence,
  };
}

/*
 * emit(manifest, opts) -> { ok, entry, install_manifest } | { ok:false, refusal }
 *
 * opts: { artifactsDir?: string, referenceOnly?: boolean, schema?: object }
 */
function emit(manifest, opts) {
  const o = opts || {};

  // Gate 1 — A2 validation. An invalid manifest never reaches the license check,
  // because its license fields are exactly what could not be trusted.
  const result = validate(manifest, o.schema || loadSchema());
  if (!result.valid) {
    return refuse('MANIFEST_INVALID', 'manifest failed A2 validation', result.errors);
  }

  const mode = manifest.provenance.integration_mode;
  const tier = manifest.provenance.license_tier;
  const derivedPosture = REDISTRIBUTION_BY_TIER[tier];

  // Gate 2a — flag/mode coherence, checked independently of the licence.
  // A fork mode means "distribute local artifacts"; --reference-only means
  // "distribute nothing". Those contradict. Silently honouring one and
  // discarding the other is how a tool becomes untrustworthy — the caller
  // would get a pointer while believing they had shipped a fork. Refuse.
  if (o.referenceOnly && !REFERENCE_ONLY_MODES.includes(mode)) {
    return refuse(
      'MODE_MISMATCH',
      `--reference-only requires integration_mode in {${REFERENCE_ONLY_MODES.join(', ')}}, got '${mode}'`,
      { hint: `mode '${mode}' distributes local files; drop --reference-only or change the mode` }
    );
  }

  // Gate 2b — the system boundary. Derived posture, never the declared field.
  if (derivedPosture === 'prohibited' && !o.referenceOnly) {
    return refuse(
      'REDISTRIBUTION_PROHIBITED',
      `license_tier ${tier} derives redistribution 'prohibited' via lib/license_gate.js; ` +
      'emitting a registry entry would redistribute it',
      { integration_mode: mode, hint: 'a code-free upstream pointer is available via --reference-only' }
    );
  }

  const pointer = o.referenceOnly || REFERENCE_ONLY_MODES.includes(mode);

  // Gate 3 — a fork entry with no files is not installable. Emitting one would
  // be the Scaffold Illusion: an artifact that looks shipped and installs nothing.
  let artifacts = [];
  if (!pointer) {
    if (!o.artifactsDir) {
      return refuse('NO_ARTIFACTS', `integration_mode '${mode}' distributes local files, but no --artifacts directory was given`);
    }
    let stat;
    try { stat = fs.statSync(o.artifactsDir); } catch (_) { stat = null; }
    if (!stat || !stat.isDirectory()) {
      return refuse('NO_ARTIFACTS', `--artifacts is not a directory: ${o.artifactsDir}`);
    }
    artifacts = collectArtifacts(o.artifactsDir);
    if (artifacts.length === 0) {
      return refuse('NO_ARTIFACTS', `--artifacts directory is empty: ${o.artifactsDir}`);
    }
  }

  const name = registryName(manifest);
  const type = REGISTRY_TYPE[manifest.capability.component_type];
  const prov = provenanceBlock(manifest, derivedPosture);

  const entry = {
    $schema: 'https://ui.shadcn.com/schema/registry-item.json',
    name,
    type,
    title: manifest.identity.name,
    description:
      `${manifest.capability.component_type} for the ${manifest.capability.surface} surface, ` +
      `from ${manifest.identity.upstream_namespace} pinned at ${manifest.identity.commit_sha.slice(0, 12)}.`,
    dependencies: [],
    registryDependencies: [],
    files: artifacts.map(a => ({
      path: `${manifest.identity.local_namespace}/${name}/${a.path}`,
      type,
      content: fs.readFileSync(a._abs, 'utf8'),
    })),
    meta: {
      cpp: {
        artifact_class: pointer ? 'upstream-pointer' : 'local-artifacts',
        manifest_id: manifest.identity.id,
        local_namespace: manifest.identity.local_namespace,
        identity_fit_score: manifest.selection.identity_fit_score,
        reuse_recommendation: manifest.selection.reuse_recommendation,
        abstention_conditions: manifest.selection.abstention_conditions,
        provenance: prov,
      },
    },
  };

  if (pointer) {
    // A pointer carries no code. State that positively rather than by the
    // absence of a key, so a consumer cannot mistake it for a stripped entry.
    delete entry.files;
    entry.meta.cpp.upstream_install = {
      source: manifest.identity.upstream_repo,
      commit_sha: manifest.identity.commit_sha,
      note: 'Install from the upstream registry. No component code is distributed by CPP.',
    };
  }

  const install_manifest = {
    schema: 'cdicf/install-manifest/1',
    component: manifest.identity.id,
    registry_item: name,
    version: manifest.identity.version,
    pinned: manifest.identity.commit_sha !== 'PENDING_CLONE',
    install: {
      mode: pointer ? 'upstream-reference' : 'local-artifacts',
      deterministic: manifest.identity.commit_sha !== 'PENDING_CLONE',
      command: pointer
        ? `# install from upstream, pinned: ${manifest.identity.upstream_repo}@${manifest.identity.commit_sha}`
        : `npx shadcn@latest add ${manifest.identity.local_namespace}/${name}`,
    },
    provenance: prov,
    notice_required: manifest.provenance.notice_required,
    artifacts: artifacts.map(a => ({ path: a.path, sha256: a.sha256, bytes: a.bytes })),
    checksum: rollupChecksum(artifacts),
  };

  return { ok: true, entry, install_manifest };
}

function emitFile(file, opts) {
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    return refuse('MANIFEST_INVALID', `cannot read manifest: ${e.message}`);
  }
  return emit(parsed, opts);
}

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(
      'registry_emitter.js — emit a CPP Design Registry entry from a Component Manifest.\n\n' +
      'Usage: node modules/cdicf/registry_emitter.js <manifest.json> [options]\n\n' +
      '  --artifacts <dir>   local files to distribute (required for fork modes)\n' +
      '  --reference-only    emit a code-free upstream pointer\n' +
      '  --out <dir>         write registry-item.json + install-manifest.json\n' +
      '  --json              machine-readable result\n\n' +
      'Exit: 0 emitted, 2 argv, 3 io, 4 invalid manifest,\n' +
      '      5 REDISTRIBUTION PROHIBITED, 6 no artifacts, 7 mode mismatch\n'
    );
    process.exit(args.length ? 0 : 2);
  }

  const flagArg = (flag) => {
    const i = args.indexOf(flag);
    if (i === -1) return null;
    const v = args[i + 1];
    if (!v || v.startsWith('-')) {
      process.stderr.write(`registry_emitter.js: ${flag} requires a value\n`);
      process.exit(2);
    }
    return v;
  };

  const artifactsDir = flagArg('--artifacts');
  const outDir = flagArg('--out');
  const referenceOnly = args.includes('--reference-only');
  const json = args.includes('--json');

  const consumed = new Set([artifactsDir, outDir].filter(Boolean));
  const target = args.find(a => !a.startsWith('-') && !consumed.has(a));
  if (!target) {
    process.stderr.write('registry_emitter.js: missing <manifest.json>\n');
    process.exit(2);
  }

  const res = emitFile(path.resolve(target), { artifactsDir, referenceOnly });

  if (!res.ok) {
    // No output on refusal. A refused emission must not leave a half-artifact
    // that a later step could pick up as if it had succeeded.
    const r = res.refusal;
    process.stderr.write(`registry_emitter.js: REFUSED [${r.code}] ${r.reason}\n`);
    if (r.detail) process.stderr.write(`  detail: ${JSON.stringify(r.detail)}\n`);
    process.exit(r.exit);
  }

  if (referenceOnly) {
    process.stderr.write(
      'registry_emitter.js: NOTICE — --reference-only emitted an upstream pointer for a ' +
      'redistribution-restricted component. No component code was written; the consumer ' +
      'installs from the upstream registry (D-011).\n'
    );
  }

  if (outDir) {
    try {
      fs.mkdirSync(outDir, { recursive: true });
      fs.writeFileSync(path.join(outDir, 'registry-item.json'), JSON.stringify(res.entry, null, 2) + '\n');
      fs.writeFileSync(path.join(outDir, 'install-manifest.json'), JSON.stringify(res.install_manifest, null, 2) + '\n');
    } catch (e) {
      process.stderr.write(`registry_emitter.js: ${e.message}\n`);
      process.exit(3);
    }
  }

  if (json) {
    process.stdout.write(JSON.stringify(res, null, 2) + '\n');
  } else {
    const m = res.install_manifest;
    process.stdout.write(
      `EMITTED  ${m.component}\n` +
      `  class      ${res.entry.meta.cpp.artifact_class}\n` +
      `  type       ${res.entry.type}\n` +
      `  mode       ${m.install.mode}\n` +
      `  pinned     ${m.pinned}\n` +
      `  artifacts  ${m.artifacts.length}\n` +
      `  checksum   ${m.checksum}\n`
    );
  }
  process.exit(0);
}

if (require.main === module) main(process.argv);

module.exports = {
  emit, emitFile, collectArtifacts, rollupChecksum,
  REGISTRY_TYPE, REFUSAL, REFERENCE_ONLY_MODES, FORK_MODES,
};
