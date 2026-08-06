#!/usr/bin/env node
/*
 * modules/cdicf/validate_manifest.js — CDICF A2
 *
 * Validates a Component Manifest against component_manifest.schema.json, then
 * enforces the six cross-field invariants the schema declares but JSON Schema
 * cannot express.
 *
 * Usage:
 *   node modules/cdicf/validate_manifest.js <manifest.json> [--json]
 *   node modules/cdicf/validate_manifest.js --all <dir>
 *
 * Exit codes: 0 valid, 1 invalid, 2 argv error, 3 io error.
 *
 * Dependency-free by design, matching lib/license_gate.js. This is NOT a
 * general JSON Schema engine — it implements exactly the keywords this schema
 * uses (type, required, properties, additionalProperties:false, enum, const,
 * pattern, minLength, minimum, maximum, items, oneOf, format:date). Feeding it
 * an arbitrary schema will silently under-validate, so it is scoped to this one.
 *
 * INV-01 imports REDISTRIBUTION_BY_TIER from the license gate rather than
 * restating it. The manifest vocabulary and the gate vocabulary are one
 * vocabulary; a copy would let them drift, and the drift would be invisible
 * until an installer acted on the wrong half.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const { REDISTRIBUTION_BY_TIER } = require('../../lib/license_gate');

const SCHEMA_PATH = path.join(__dirname, 'component_manifest.schema.json');

function loadSchema() {
  return JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf8'));
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function typeOk(value, type) {
  switch (type) {
    case 'object':  return value !== null && typeof value === 'object' && !Array.isArray(value);
    case 'array':   return Array.isArray(value);
    case 'string':  return typeof value === 'string';
    case 'number':  return typeof value === 'number' && Number.isFinite(value);
    case 'boolean': return typeof value === 'boolean';
    default:        return true;
  }
}

/* Returns true if `value` satisfies a leaf subschema (used by oneOf branches). */
function leafOk(value, sub) {
  if (Object.prototype.hasOwnProperty.call(sub, 'const')) return value === sub.const;
  if (sub.pattern && (typeof value !== 'string' || !new RegExp(sub.pattern).test(value))) return false;
  return true;
}

function validateNode(value, schema, at, errors) {
  if (schema.type && !typeOk(value, schema.type)) {
    errors.push({ path: at, rule: 'type', message: `expected ${schema.type}, got ${Array.isArray(value) ? 'array' : typeof value}` });
    return; // Further checks would be noise once the type is wrong.
  }

  if (schema.enum && !schema.enum.includes(value)) {
    errors.push({ path: at, rule: 'enum', message: `${JSON.stringify(value)} is not one of ${schema.enum.join(', ')}` });
  }

  if (schema.oneOf) {
    const hits = schema.oneOf.filter(sub => leafOk(value, sub)).length;
    if (hits !== 1) {
      errors.push({ path: at, rule: 'oneOf', message: `${JSON.stringify(value)} matched ${hits} of ${schema.oneOf.length} allowed forms, expected exactly 1` });
    }
  }

  if (typeof value === 'string') {
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) {
      errors.push({ path: at, rule: 'pattern', message: `${JSON.stringify(value)} does not match ${schema.pattern}` });
    }
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      errors.push({ path: at, rule: 'minLength', message: `shorter than ${schema.minLength}` });
    }
    if (schema.format === 'date' && !ISO_DATE.test(value)) {
      errors.push({ path: at, rule: 'format', message: `${JSON.stringify(value)} is not an ISO date (YYYY-MM-DD)` });
    }
  }

  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) {
      errors.push({ path: at, rule: 'minimum', message: `${value} < ${schema.minimum}` });
    }
    if (schema.maximum !== undefined && value > schema.maximum) {
      errors.push({ path: at, rule: 'maximum', message: `${value} > ${schema.maximum}` });
    }
  }

  if (Array.isArray(value) && schema.items) {
    value.forEach((item, i) => validateNode(item, schema.items, `${at}[${i}]`, errors));
  }

  if (typeOk(value, 'object') && (schema.properties || schema.required)) {
    for (const key of schema.required || []) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) {
        errors.push({ path: at === '' ? key : `${at}.${key}`, rule: 'required', message: 'missing' });
      }
    }
    if (schema.additionalProperties === false && schema.properties) {
      for (const key of Object.keys(value)) {
        if (!Object.prototype.hasOwnProperty.call(schema.properties, key)) {
          errors.push({ path: at === '' ? key : `${at}.${key}`, rule: 'additionalProperties', message: 'not permitted by the schema' });
        }
      }
    }
    for (const [key, sub] of Object.entries(schema.properties || {})) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) continue;
      validateNode(value[key], sub, at === '' ? key : `${at}.${key}`, errors);
    }
  }
}

/*
 * The six invariants. Each returns an error object or null.
 * These are the rules that make the manifest load-bearing rather than
 * descriptive — JSON Schema can say "this field is an enum", it cannot say
 * "a prohibited component may not be forked".
 */
function checkInvariants(m) {
  const errors = [];
  const prov = m.provenance || {};
  const cap  = m.capability || {};
  const qual = m.quality || {};
  const sel  = m.selection || {};
  const id   = m.identity || {};

  // INV-01 — posture must be the one the gate derives from the tier.
  const derived = REDISTRIBUTION_BY_TIER[prov.license_tier];
  if (derived && prov.redistribution_posture && prov.redistribution_posture !== derived) {
    errors.push({
      path: 'provenance.redistribution_posture', rule: 'INV-01',
      message: `license_tier ${prov.license_tier} derives '${derived}' via lib/license_gate.js, manifest says '${prov.redistribution_posture}'`,
    });
  }

  // INV-02 — prohibited may never be forked or vendored.
  if (prov.redistribution_posture === 'prohibited' &&
      !['gateway_upstream', 'metadata_only'].includes(prov.integration_mode)) {
    errors.push({
      path: 'provenance.integration_mode', rule: 'INV-02',
      message: `redistribution is prohibited, so integration_mode must be gateway_upstream or metadata_only, not '${prov.integration_mode}'`,
    });
  }

  // INV-03 — provenance may never be stripped from restricted code.
  if (prov.redistribution_posture === 'prohibited' && prov.notice_required !== true) {
    errors.push({
      path: 'provenance.notice_required', rule: 'INV-03',
      message: 'redistribution is prohibited, so notice_required must be true',
    });
  }

  // INV-04 — VERIFIED is a claim about a specific artifact.
  if (prov.confidence === 'VERIFIED') {
    if (id.commit_sha === 'PENDING_CLONE') {
      errors.push({ path: 'identity.commit_sha', rule: 'INV-04', message: 'confidence VERIFIED requires a pinned commit_sha' });
    }
    if (prov.license_fingerprint === 'PENDING_CLONE') {
      errors.push({ path: 'provenance.license_fingerprint', rule: 'INV-04', message: 'confidence VERIFIED requires a pinned license_fingerprint' });
    }
  }

  // INV-05 — never launder an unmeasured value into a recommendation.
  if (sel.reuse_recommendation === 'prefer' && ['fail', 'unassessed'].includes(qual.wcag_level)) {
    errors.push({
      path: 'selection.reuse_recommendation', rule: 'INV-05',
      message: `cannot 'prefer' a component whose wcag_level is '${qual.wcag_level}'`,
    });
  }

  // INV-06 — high motion needs a reduced-motion path.
  if (cap.motion_budget === 'high' && qual.reduced_motion_compliant !== true) {
    errors.push({
      path: 'quality.reduced_motion_compliant', rule: 'INV-06',
      message: 'motion_budget high requires reduced_motion_compliant true',
    });
  }

  return errors;
}

function validate(manifest, schema) {
  const s = schema || loadSchema();
  const errors = [];
  validateNode(manifest, s, '', errors);
  // Invariants run only on a structurally sound manifest; otherwise every
  // invariant reports a cascade of the same missing field.
  if (errors.length === 0) errors.push(...checkInvariants(manifest));
  return { valid: errors.length === 0, errors };
}

function validateFile(file, schema) {
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    return { valid: false, errors: [{ path: '', rule: 'parse', message: e.message }] };
  }
  return validate(parsed, schema);
}

function render(file, result) {
  const rel = path.basename(file);
  if (result.valid) return `PASS  ${rel}`;
  const lines = [`FAIL  ${rel}`];
  for (const e of result.errors) {
    lines.push(`        ${e.rule.padEnd(20)} ${e.path || '(root)'}: ${e.message}`);
  }
  return lines.join('\n');
}

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(
      'validate_manifest.js — validate CDICF Component Manifests.\n\n' +
      'Usage: node modules/cdicf/validate_manifest.js <manifest.json> [--json]\n' +
      '       node modules/cdicf/validate_manifest.js --all <dir>\n\n' +
      'Exit: 0 valid, 1 invalid, 2 argv, 3 io\n'
    );
    process.exit(args.length ? 0 : 2);
  }

  const json = args.includes('--json');
  const all = args.includes('--all');
  const positional = args.filter(a => !a.startsWith('-'));
  if (!positional.length) {
    process.stderr.write('validate_manifest.js: missing <manifest.json> or <dir>\n');
    process.exit(2);
  }

  let files;
  const target = path.resolve(positional[0]);
  try {
    if (all) {
      files = fs.readdirSync(target)
        .filter(f => f.endsWith('.json'))
        .sort()
        .map(f => path.join(target, f));
    } else {
      files = [target];
      fs.accessSync(target, fs.constants.R_OK);
    }
  } catch (e) {
    process.stderr.write(`validate_manifest.js: ${e.message}\n`);
    process.exit(3);
  }

  if (all && files.length === 0) {
    // An empty sweep must not read as success. Zero manifests validated is
    // zero evidence, not a pass.
    process.stderr.write(`validate_manifest.js: no .json manifests found in ${target}\n`);
    process.exit(1);
  }

  const schema = loadSchema();
  const results = files.map(f => ({ file: f, result: validateFile(f, schema) }));

  if (json) {
    process.stdout.write(JSON.stringify(
      results.map(r => ({ file: r.file, ...r.result })), null, 2) + '\n');
  } else {
    process.stdout.write(results.map(r => render(r.file, r.result)).join('\n') + '\n');
  }

  process.exit(results.every(r => r.result.valid) ? 0 : 1);
}

if (require.main === module) main(process.argv);

module.exports = { validate, validateFile, checkInvariants, loadSchema, SCHEMA_PATH };
