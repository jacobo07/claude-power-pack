#!/usr/bin/env node
/*
 * discover.js — Subsystem Discovery Core (MC-OVO-80)
 *
 * Scans $PWD (or --project <path>) for manifest files and emits a
 * deterministic JSON description of the real subsystems inside the
 * repository. Consumed by lib/audit_all.js.
 *
 * Design:
 *   - Walks up to MAX_DEPTH levels below the project root.
 *   - At every directory, checks for a known manifest signature.
 *   - Dirs containing at least one manifest become "subsystems".
 *   - Root is always emitted (as subsystem id="root") if at least one
 *     manifest or power-pack signal lives at the top.
 *
 * Output shape (stable contract):
 *   {
 *     version: 1,
 *     root: "<abs path>",
 *     root_basename: "<leaf>",
 *     scanned_at: "<ISO>",
 *     subsystems: [{
 *       id, path, abs_path, name, stack, language_hint,
 *       primary_manifest, manifests[], is_root, depth, frameworks[]
 *     }],
 *     stats: { subsystem_count, dirs_scanned, dirs_skipped }
 *   }
 *
 * Exit codes: 0 ok, 2 argv error, 3 io error.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const MAX_DEPTH = 3;
const SKIP_DIRS = new Set([
  '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
  'dist', 'build', 'target', 'out', '.next', '.nuxt', '.svelte-kit',
  '_audit_cache', 'vault', '.cache', '.parcel-cache', '.turbo',
  '.pytest_cache', '.mypy_cache', '.tox', 'coverage', '.nyc_output',
  '.gradle', '.idea', '.vscode', 'logs', 'tmp',
]);

// Manifest priority — first match wins for "primary_manifest".
// Maps each manifest → {stack, language_hint, frameworks[]}.
const MANIFEST_SIGNATURES = [
  ['mix.exs',        { stack: 'elixir',        language_hint: 'elixir',     frameworks: ['otp'] }],
  ['plugin.yml',     { stack: 'minecraft',     language_hint: 'java',       frameworks: ['paper'] }],
  ['Cargo.toml',     { stack: 'rust',          language_hint: 'rust',       frameworks: [] }],
  ['go.mod',         { stack: 'go',            language_hint: 'go',         frameworks: [] }],
  ['pom.xml',        { stack: 'java',          language_hint: 'java',       frameworks: ['maven'] }],
  ['build.gradle',   { stack: 'java',          language_hint: 'java',       frameworks: ['gradle'] }],
  ['build.gradle.kts', { stack: 'java',        language_hint: 'kotlin',     frameworks: ['gradle'] }],
  ['pyproject.toml', { stack: 'python',        language_hint: 'python',     frameworks: [] }],
  ['setup.py',       { stack: 'python',        language_hint: 'python',     frameworks: [] }],
  ['requirements.txt', { stack: 'python',      language_hint: 'python',     frameworks: [] }],
  ['package.json',   { stack: 'node',          language_hint: 'javascript', frameworks: [] }],
  ['CMakeLists.txt', { stack: 'cpp',           language_hint: 'c++',        frameworks: ['cmake'] }],
  ['Makefile',       { stack: 'c',             language_hint: 'c',          frameworks: ['make'] }],
  ['.powerpack',     { stack: 'power-pack',    language_hint: 'python',     frameworks: ['claude-code'] }],
  ['SKILL.md',       { stack: 'claude-skill',  language_hint: 'markdown',   frameworks: ['claude-code'] }],
  ['CLAUDE.md',      { stack: 'ai-orchestration', language_hint: 'markdown', frameworks: ['claude-code'] }],
];

const MANIFEST_NAMES = new Set(MANIFEST_SIGNATURES.map(([n]) => n));

function parseArgs(argv) {
  const out = { project: process.cwd(), json: true, pretty: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project' || a === '-p') {
      out.project = argv[++i];
    } else if (a === '--json') {
      out.json = true;
    } else if (a === '--pretty') {
      out.pretty = true;
    } else if (a === '--help' || a === '-h') {
      out.help = true;
    } else {
      process.stderr.write(`discover.js: unknown arg ${a}\n`);
      process.exit(2);
    }
  }
  return out;
}

function helpText() {
  return [
    'discover.js — Subsystem Discovery Core',
    'Usage: node discover.js [--project <path>] [--pretty]',
    '',
    'Scans manifests up to 3 levels deep and emits subsystem JSON.',
  ].join('\n');
}

function safeReaddir(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true });
  } catch (err) {
    return null;
  }
}

function detectManifests(dir) {
  const entries = safeReaddir(dir);
  if (entries === null) return [];
  const found = [];
  const seen = new Set();
  for (const sig of MANIFEST_SIGNATURES) {
    const name = sig[0];
    if (seen.has(name)) continue;
    const hit = entries.find((e) => e.isFile() && e.name === name);
    if (hit) {
      found.push({ name, meta: sig[1] });
      seen.add(name);
    }
  }
  return found;
}

function packageJsonFrameworks(dir) {
  try {
    const raw = fs.readFileSync(path.join(dir, 'package.json'), 'utf8');
    const pkg = JSON.parse(raw);
    const deps = Object.assign({}, pkg.dependencies || {}, pkg.devDependencies || {});
    const fw = [];
    if (deps.next) fw.push('next');
    if (deps.react) fw.push('react');
    if (deps.vue) fw.push('vue');
    if (deps.svelte) fw.push('svelte');
    if (deps.express) fw.push('express');
    if (deps.fastify) fw.push('fastify');
    if (deps.nestjs || deps['@nestjs/core']) fw.push('nestjs');
    if (deps.typescript || (pkg.devDependencies && pkg.devDependencies.typescript)) {
      fw.push('typescript');
    }
    return { frameworks: fw, name: pkg.name || null };
  } catch (_) {
    return { frameworks: [], name: null };
  }
}

function slugify(rel) {
  if (rel === '' || rel === '.') return 'root';
  return rel.replace(/[\\/]+/g, '-').replace(/[^a-zA-Z0-9_-]/g, '_');
}

function buildSubsystem(rootAbs, absDir, manifests) {
  const rel = path.relative(rootAbs, absDir).replace(/\\/g, '/');
  const isRoot = rel === '' || rel === '.';
  const primary = manifests[0];
  const stacks = [...new Set(manifests.map((m) => m.meta.stack))];
  const frameworks = [...new Set(manifests.flatMap((m) => m.meta.frameworks || []))];
  const manifestNames = manifests.map((m) => m.name);

  let name = isRoot ? path.basename(rootAbs) : path.basename(absDir);
  if (manifestNames.includes('package.json')) {
    const { frameworks: pfws, name: pkgName } = packageJsonFrameworks(absDir);
    for (const fw of pfws) if (!frameworks.includes(fw)) frameworks.push(fw);
    if (pkgName) name = pkgName;
  }

  // Combined stack label when multiple manifests disagree.
  const stack = stacks.length === 1 ? stacks[0] : `mixed(${stacks.join('+')})`;

  return {
    id: isRoot ? 'root' : slugify(rel),
    path: isRoot ? '.' : rel,
    abs_path: absDir,
    name,
    stack,
    language_hint: primary.meta.language_hint,
    primary_manifest: primary.name,
    manifests: manifestNames,
    frameworks,
    is_root: isRoot,
    depth: isRoot ? 0 : rel.split('/').length,
  };
}

function walk(rootAbs) {
  const stats = { subsystem_count: 0, dirs_scanned: 0, dirs_skipped: 0 };
  const subsystems = [];
  const stack = [[rootAbs, 0]];

  while (stack.length) {
    const [dir, depth] = stack.pop();
    stats.dirs_scanned += 1;

    const manifests = detectManifests(dir);
    if (manifests.length > 0) {
      subsystems.push(buildSubsystem(rootAbs, dir, manifests));
    }

    if (depth >= MAX_DEPTH) continue;

    const entries = safeReaddir(dir);
    if (!entries) continue;
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      if (SKIP_DIRS.has(e.name) || e.name.startsWith('.')) {
        if (!['.powerpack', '.claude'].includes(e.name)) {
          stats.dirs_skipped += 1;
          continue;
        }
      }
      stack.push([path.join(dir, e.name), depth + 1]);
    }
  }

  subsystems.sort((a, b) => (a.depth - b.depth) || a.path.localeCompare(b.path));
  stats.subsystem_count = subsystems.length;
  return { subsystems, stats };
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(helpText() + '\n');
    return 0;
  }

  let rootAbs;
  try {
    rootAbs = fs.realpathSync(path.resolve(args.project));
  } catch (err) {
    process.stderr.write(`discover.js: cannot resolve project path ${args.project}: ${err.message}\n`);
    return 3;
  }

  const { subsystems, stats } = walk(rootAbs);

  const payload = {
    version: 1,
    root: rootAbs.replace(/\\/g, '/'),
    root_basename: path.basename(rootAbs),
    scanned_at: new Date().toISOString(),
    subsystems,
    stats,
  };

  const out = args.pretty ? JSON.stringify(payload, null, 2) : JSON.stringify(payload);
  process.stdout.write(out + '\n');
  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = {
  walk,
  detectManifests,
  MANIFEST_NAMES,
  MANIFEST_SIGNATURES,
  SKIP_DIRS,
  MAX_DEPTH,
};
