#!/usr/bin/env node
/*
 * audit_all.js — Unified Audit Orchestrator (MC-OVO-81)
 *
 * End-to-end flow for /audit-all:
 *   1. discover.js → subsystems[]
 *   2. score.js    → per-subsystem scores
 *   3. (optional) oracle_delta.py if Power-Pack tooling is resolvable
 *   4. report.js   → summary table or drill-down detail
 *
 * Usage:
 *   node lib/audit_all.js               # summary of current dir
 *   node lib/audit_all.js 2             # drill into subsystem #2
 *   node lib/audit_all.js root          # drill into subsystem by id
 *   node lib/audit_all.js --json        # machine-readable bundle
 *   node lib/audit_all.js --no-oracle   # skip python oracle probe
 *   node lib/audit_all.js --project X   # audit a different root
 *
 * Exit codes: 0 ok, 2 argv error, 3 io error.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const discover = require('./discover');
const score = require('./score');
const report = require('./report');

const POWER_PACK_ROOT = path.resolve(__dirname, '..');

function parseArgs(argv) {
  const out = { project: process.cwd(), detail: null, json: false,
    noOracle: false, help: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project' || a === '-p') out.project = argv[++i];
    else if (a === '--json') out.json = true;
    else if (a === '--no-oracle') out.noOracle = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else if (!a.startsWith('-') && out.detail === null) out.detail = a;
    else {
      process.stderr.write(`audit_all.js: unexpected arg ${a}\n`);
      process.exit(2);
    }
  }
  return out;
}

function helpText() {
  return [
    'audit_all.js — Unified Audit Orchestrator',
    '',
    'Usage: node lib/audit_all.js [<N|id>] [--project <path>] [--json] [--no-oracle]',
    '',
    'With no selector: emits a summary table.',
    'With <N> or <id>: emits full drill-down detail for one subsystem.',
    '',
    'Flags:',
    '  --json        emit the raw bundle JSON (includes evidence + oracle_delta)',
    '  --no-oracle   skip the python oracle_delta.py probe',
    '  --project     audit a different root (default: cwd)',
  ].join('\n');
}

function runDiscovery(rootAbs) {
  const { subsystems, stats } = discover.walk(rootAbs);
  return {
    version: 1,
    root: rootAbs.replace(/\\/g, '/'),
    root_basename: path.basename(rootAbs),
    scanned_at: new Date().toISOString(),
    subsystems,
    stats,
  };
}

function scoreSubsystem(sub) {
  const cwd = sub.abs_path;
  const thrash = score.scoreEditThrashing(cwd);
  const drift = score.scoreDrift(cwd);
  const completion = score.scoreCompletion(cwd);
  const env = score.scoreEnvMapping(sub.stack || 'unknown');
  const scores = {
    edit_thrashing: thrash.score,
    drift: drift.score,
    completion: completion.score,
    env_mapping: env.score,
  };
  return {
    subsystem_id: sub.id,
    subsystem_path: sub.path,
    stack: sub.stack,
    scores,
    overall: score.weightedOverall(scores),
    evidence: {
      edit_thrashing: thrash.evidence,
      drift: drift.evidence,
      completion: completion.evidence,
      env_mapping: env.evidence,
    },
    scored_at: new Date().toISOString(),
  };
}

function probeOracle(projectRoot) {
  // Optional Phase-A call into the Power-Pack oracle_delta.py, for repos
  // that carry a Power-Pack installation. Non-fatal on any failure.
  const toolPath = path.join(POWER_PACK_ROOT, 'tools', 'oracle_delta.py');
  if (!fs.existsSync(toolPath)) {
    return { available: false, reason: 'oracle_delta.py not found' };
  }
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const r = spawnSync(python, [toolPath, '--project', projectRoot, '--json'], {
    cwd: projectRoot, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 60_000, shell: process.platform === 'win32',
  });
  if (r.status !== 0 || !r.stdout.trim()) {
    return { available: false, reason: `exit=${r.status}`, stderr: (r.stderr || '').slice(0, 500) };
  }
  try {
    // Oracle may print warnings to stderr; stdout must be valid JSON.
    return { available: true, delta: JSON.parse(r.stdout) };
  } catch (err) {
    return { available: false, reason: `parse: ${err.message}` };
  }
}

function runAll(args) {
  let rootAbs;
  try {
    rootAbs = fs.realpathSync(path.resolve(args.project));
  } catch (err) {
    process.stderr.write(`audit_all.js: cannot resolve project path ${args.project}: ${err.message}\n`);
    return { code: 3 };
  }
  const discovery = runDiscovery(rootAbs);

  if (discovery.subsystems.length === 0) {
    return {
      code: 0,
      envelope: {
        root: discovery.root,
        scanned_at: discovery.scanned_at,
        reports: [],
        discovery,
        oracle: null,
        notice: 'No manifests detected — nothing to audit at this root.',
      },
    };
  }

  const reports = discovery.subsystems.map((s) => scoreSubsystem(s));
  const oracle = args.noOracle ? { available: false, reason: 'disabled' } : probeOracle(rootAbs);

  const envelope = {
    root: discovery.root,
    root_basename: discovery.root_basename,
    scanned_at: discovery.scanned_at,
    reports,
    discovery,
    oracle,
  };
  return { code: 0, envelope };
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(helpText() + '\n');
    return 0;
  }
  const { code, envelope } = runAll(args);
  if (code !== 0) return code;

  if (args.json) {
    process.stdout.write(JSON.stringify(envelope, null, 2) + '\n');
    return 0;
  }

  if (envelope.notice) {
    process.stdout.write(envelope.notice + '\n');
    return 0;
  }

  const out = args.detail != null
    ? report.renderDetail(envelope, args.detail)
    : report.renderSummary(envelope);
  process.stdout.write(out + '\n');

  // Oracle post-script on summary view only (keeps drill-down clean).
  if (args.detail == null && envelope.oracle) {
    if (envelope.oracle.available) {
      const d = envelope.oracle.delta || {};
      const changed = (d.changed || []).length;
      const added = (d.new || []).length;
      const deleted = (d.deleted || []).length;
      process.stdout.write(`\noracle_delta: ${changed} changed / ${added} new / ${deleted} deleted  `
        + `(sha256_pre=${(d.sha256_pre || '').slice(0, 12)})\n`);
    } else {
      process.stdout.write(`\noracle_delta: skipped (${envelope.oracle.reason})\n`);
    }
  }

  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { runAll, scoreSubsystem, runDiscovery, probeOracle };
