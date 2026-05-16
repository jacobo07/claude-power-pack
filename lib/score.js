#!/usr/bin/env node
/*
 * score.js — Normalizer & Score Engine (MC-OVO-82)
 *
 * Maps raw evidence (git log, file scan for stubs, toolchain probe) to
 * 0–100% scores on four canonical benchmarks. Consumed by audit_all.js.
 *
 * Benchmarks:
 *   edit-thrashing → churn over last 14 days. More files with >5 commits
 *                    means more thrash. 100 = no thrash, 0 = everything churning.
 *   drift          → producer-consumer gap. Counts new files in last 14 days
 *                    that have NO consumer (import/require/reference) elsewhere.
 *                    100 = every new file is wired; 0 = half or more are orphans.
 *   completion     → Reality Contract stub density. Counts placeholder markers
 *                    across runtime files. 100 = zero; 0 = >1 per 20 files.
 *   env-mapping    → for the subsystem's declared stack, is the toolchain on PATH?
 *                    100 = all required tools callable; 0 = primary tool missing.
 *
 * Input (stdin or --from <file>): a subsystem object from discover.js.
 *   { id, path, abs_path, stack, language_hint, primary_manifest, ... }
 *
 * Output JSON: { subsystem_id, scores: {...}, evidence: {...}, overall }
 *
 * This script is pure Node (no deps) and idempotent — safe to run
 * repeatedly on a clean tree.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

const CHURN_WINDOW_DAYS = 14;
const CHURN_COMMIT_THRESHOLD = 5;

// Runtime-code extensions subject to Reality-Contract scrutiny.
// Pure docs and auto-generated files are out of scope.
const RUNTIME_EXTENSIONS = new Set([
  '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx',
  '.py', '.rb', '.go', '.rs', '.java', '.kt',
  '.ex', '.exs', '.c', '.cpp', '.h', '.hpp',
  '.cs', '.swift', '.m', '.mm', '.php',
  '.sh', '.bash', '.ps1', '.psm1',
]);

// Excluded from stub scanning even with a runtime extension.
// Extended to cover every major language ecosystem's vendor / build
// directory so third-party dependency code isn't scored against the
// host project's Reality Contract. The original list only covered
// Node (`node_modules`) and Python (`.venv`/`venv`); Elixir / Go / Ruby
// / Swift / Rust / Next.js / SvelteKit builds were leaking into stub
// counts (e.g. 72 false-positive TODO hits from `deps/phoenix/...`).
const STUB_EXCLUDE_DIRS = new Set([
  // VCS / auditor meta
  '.git', '_audit_cache',
  // Build artefacts
  'dist', 'build', 'target', 'out',
  '.next', '.nuxt', '.svelte-kit',
  // Test dirs (unit tests are not shipped product)
  'tests', 'test', '__tests__', 'spec',
  // Coverage / pycache
  'coverage', '__pycache__',
  // Language-ecosystem vendor directories
  'node_modules',             // Node / npm / pnpm / yarn
  '.venv', 'venv',            // Python
  'deps', '_build',           // Elixir (mix deps + compiled artefacts)
  'vendor',                   // Go / PHP / Ruby bundler
  'Pods',                     // CocoaPods / iOS
  'Packages',                 // Swift PM / .NET legacy
  '.bundle',                  // Ruby bundler cache
  '.cargo',                   // Rust cargo registry cache
]);

// Tight patterns — each MUST end with a structural marker (colon, paren,
// `raise`, or an explicit phrase) so casual word matches and
// documentation prose don't trigger.
const STUB_PATTERNS = [
  /\bTODO\s*[:(]/,
  /\bFIXME\s*[:(]/,
  /\bXXX\s*:/,
  /\bHACK\s*[:(]/,
  /\bComing\s+Soon\b/i,
  /raise\s+NotImplementedError/,
  /throw\s+new\s+Error\s*\(\s*["']not\s+implemented/i,
  /raise\s+["']not\s+implemented/i,
  /\/\/\s*@stub\b/i,
  /#\s*@stub\b/i,
];

// Files permitted to mention the stub patterns (their source of truth).
const STUB_META_FILES = new Set([
  'lib/score.js',
  'lib/discover.js',
  'lib/audit_all.js',
  'lib/report.js',
]);

// MC-IO-500.3b (2026-04-26, InfinityOps) — drift orphan exclusion for
// ops/infra/provisioning entry-points. Pre-patch, scoreDrift counted any
// runtime file with no `import`/`require` consumer as drift, which
// systematically penalised shell scripts and provisioning entry-points
// that are invoked by humans/cron/CI rather than imported by other code.
// Observed on InfinityOps repo-root: `09_Provisioning/vps_bootstrap.sh`,
// `08_Workflows_Code/smoke/reality_smoke.sh`, etc. dragged the root
// blob's ROI-Wiring score to 13 even though every script was wired into
// CI / runbooks. Paths are matched as POSIX-style prefixes against the
// `rel` path returned by git-log (already forward-slashed by git).
const OPS_DIR_PREFIXES = [
  '08_Workflows_Code/',
  '09_Provisioning/',
  '15_Operations/',
  'scripts/',
  'bin/',
  'deploy/',
  'ops/',
  'infra/',
];

function isOpsEntryPoint(rel) {
  for (const p of OPS_DIR_PREFIXES) if (rel.startsWith(p)) return true;
  return false;
}

// MC-IO-500.3c (2026-04-26, InfinityOps) — drift orphan exclusion for
// test files. Sister patch to MC-IO-500.3b: a *_test.exs / *_test.py /
// *.test.tsx / *.spec.ts file is loaded by a test runner (ExUnit /
// pytest / Jest / Vitest) and never imported by another module by
// design. Pre-patch this inflated InfinityOps root orphan count by 31
// (out of 79). Substring matchers catch nested layouts like
// `01_Core_Systems/infinity_mie/test/...`. Suffix patterns catch
// co-located test files (Jest `*.test.tsx` next to its component).
const TEST_DIR_SUBSTRINGS = [
  '/test/',
  '/tests/',
  '/spec/',
  '/__tests__/',
];

const TEST_FILE_SUFFIX_PATTERNS = [
  /_test\.exs?$/,           // Elixir: _test.ex / _test.exs
  /_test\.py$/,             // Python pytest convention
  /_test\.go$/,             // Go test convention
  /\.test\.[cm]?[jt]sx?$/,  // JS/TS: .test.js/.ts/.tsx/.mjs/.cjs
  /\.spec\.[cm]?[jt]sx?$/,  // JS/TS: .spec.* (Jasmine/Jest/Vitest)
  /Test\.java$/,            // Java JUnit convention
];

function isTestEntryPoint(rel) {
  for (const s of TEST_DIR_SUBSTRINGS) if (rel.includes(s)) return true;
  for (const p of TEST_FILE_SUFFIX_PATTERNS) if (p.test(rel)) return true;
  return false;
}

// Per-stack toolchain probes. Each probe is a list of (cmd, args, required).
// A probe counts as "present" if the process exits 0.
const STACK_TOOLCHAIN = {
  'node':            [['node', ['--version'], true], ['npm', ['--version'], false]],
  'python':          [['python', ['--version'], true]],
  'rust':            [['cargo', ['--version'], true], ['rustc', ['--version'], true]],
  'go':              [['go', ['version'], true]],
  'java':            [['java', ['-version'], true], ['mvn', ['--version'], false]],
  'elixir':          [['elixir', ['--version'], true], ['mix', ['--version'], true]],
  'minecraft':       [['java', ['-version'], true]],
  'cpp':             [['cmake', ['--version'], true]],
  'c':               [['make', ['--version'], true]],
  'claude-skill':    [['node', ['--version'], false]],
  'ai-orchestration':[['node', ['--version'], false]],
  'power-pack':      [['python', ['--version'], true], ['node', ['--version'], true]],
};

function parseArgs(argv) {
  const out = { from: null, pretty: false, help: false, subsystemJson: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--from') out.from = argv[++i];
    else if (a === '--subsystem') out.subsystemJson = argv[++i];
    else if (a === '--pretty') out.pretty = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else {
      process.stderr.write(`score.js: unknown arg ${a}\n`);
      process.exit(2);
    }
  }
  return out;
}

function helpText() {
  return [
    'score.js — Normalizer & Score Engine',
    'Usage: node score.js (--from <file> | --subsystem <json>) [--pretty]',
    '',
    'Reads a subsystem descriptor and emits 0–100 scores on four benchmarks.',
  ].join('\n');
}

function readSubsystemInput(args) {
  if (args.subsystemJson) return JSON.parse(args.subsystemJson);
  if (args.from) return JSON.parse(fs.readFileSync(args.from, 'utf8'));
  // Fallback: read stdin synchronously.
  try {
    const raw = fs.readFileSync(0, 'utf8');
    if (!raw.trim()) throw new Error('empty stdin');
    return JSON.parse(raw);
  } catch (err) {
    process.stderr.write(`score.js: no subsystem input (${err.message})\n`);
    process.exit(2);
  }
}

function gitAvailable(cwd) {
  const r = spawnSync('git', ['rev-parse', '--is-inside-work-tree'], {
    cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  });
  return r.status === 0 && r.stdout.trim() === 'true';
}

function scoreEditThrashing(cwd) {
  if (!gitAvailable(cwd)) {
    return { score: 100, evidence: { reason: 'not-a-git-repo' } };
  }
  const since = `--since=${CHURN_WINDOW_DAYS}.days.ago`;
  const r = spawnSync('git', ['log', since, '--name-only', '--pretty=format:'], {
    cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 16 * 1024 * 1024,
  });
  if (r.status !== 0) {
    return { score: 100, evidence: { reason: 'git-log-failed', stderr: (r.stderr || '').slice(0, 200) } };
  }
  const counts = new Map();
  for (const line of r.stdout.split('\n')) {
    const f = line.trim();
    if (!f) continue;
    counts.set(f, (counts.get(f) || 0) + 1);
  }
  const total = counts.size;
  if (total === 0) return { score: 100, evidence: { touched_files: 0, thrashing: 0 } };
  let thrashing = 0;
  for (const c of counts.values()) if (c >= CHURN_COMMIT_THRESHOLD) thrashing += 1;
  const ratio = thrashing / total;
  const score = Math.max(0, Math.round(100 - ratio * 200)); // 50% thrash ⇒ 0
  return {
    score,
    evidence: {
      touched_files: total,
      thrashing_files: thrashing,
      threshold_commits: CHURN_COMMIT_THRESHOLD,
      window_days: CHURN_WINDOW_DAYS,
    },
  };
}

function scoreDrift(cwd) {
  if (!gitAvailable(cwd)) {
    return { score: 100, evidence: { reason: 'not-a-git-repo' } };
  }
  const since = `--since=${CHURN_WINDOW_DAYS}.days.ago`;
  const r = spawnSync('git', ['log', since, '--diff-filter=A', '--name-only', '--pretty=format:'], {
    cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 16 * 1024 * 1024,
  });
  if (r.status !== 0) {
    return { score: 100, evidence: { reason: 'git-log-failed' } };
  }
  const newFiles = [...new Set(r.stdout.split('\n').map((s) => s.trim()).filter(Boolean))];
  const runtimeNewAll = newFiles.filter((f) => RUNTIME_EXTENSIONS.has(path.extname(f)));
  // MC-IO-500.3b/c: ops entry-points and test files are invoked by a
  // runner, not imported — exclude both from orphan scoring so
  // ROI-Wiring reflects the actual app graph.
  const opsExcluded = runtimeNewAll.filter(isOpsEntryPoint);
  const testsExcluded = runtimeNewAll.filter((f) => !isOpsEntryPoint(f) && isTestEntryPoint(f));
  const runtimeNew = runtimeNewAll.filter((f) => !isOpsEntryPoint(f) && !isTestEntryPoint(f));
  if (runtimeNew.length === 0) {
    return {
      score: 100,
      evidence: {
        new_runtime_files: 0,
        ops_excluded: opsExcluded.length,
        ops_excluded_sample: opsExcluded.slice(0, 5),
        tests_excluded: testsExcluded.length,
        tests_excluded_sample: testsExcluded.slice(0, 5),
      },
    };
  }
  let orphaned = 0;
  const details = [];
  for (const rel of runtimeNew) {
    const base = path.basename(rel, path.extname(rel));
    if (!base || base.length < 2) continue;
    const abs = path.join(cwd, rel);
    if (!fs.existsSync(abs)) continue; // file may have been deleted since
    const grepRe = new RegExp(`\\b${base.replace(/[-_.]/g, '[-_.]')}\\b`, 'i');
    const hasConsumer = hasAnyConsumer(cwd, rel, grepRe);
    if (!hasConsumer) {
      orphaned += 1;
      details.push(rel);
    }
  }
  const ratio = orphaned / runtimeNew.length;
  const score = Math.max(0, Math.round(100 - ratio * 200));
  return {
    score,
    evidence: {
      new_runtime_files: runtimeNew.length,
      orphaned: orphaned,
      orphan_sample: details.slice(0, 5),
      ops_excluded: opsExcluded.length,
      ops_excluded_sample: opsExcluded.slice(0, 5),
      tests_excluded: testsExcluded.length,
      tests_excluded_sample: testsExcluded.slice(0, 5),
    },
  };
}

function hasAnyConsumer(cwd, selfRel, regex) {
  // MC-IO-500.3d (2026-04-26, InfinityOps) — bumped 2000 → 5000 to
  // cover Holding-class repos. Pre-patch, the scan stopped before
  // finding consumers for `lib/infinity_mie/swarm/llm_router.ex`,
  // `lib/infinity_mie_web/vault_controller.ex`, and similar Phoenix /
  // OTP modules whose supervisors and routers live deep in the tree;
  // the auditor reported them as orphans even though the wiring was
  // real. Audit time delta on InfinityOps repo (3 subsystems): ~2s.
  const MAX = 5000;
  let seen = 0;
  const stack = [cwd];
  while (stack.length && seen < MAX) {
    const dir = stack.pop();
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { continue; }
    for (const e of entries) {
      const abs = path.join(dir, e.name);
      const rel = path.relative(cwd, abs).replace(/\\/g, '/');
      if (e.isDirectory()) {
        if (STUB_EXCLUDE_DIRS.has(e.name) || e.name.startsWith('.')) continue;
        stack.push(abs);
        continue;
      }
      if (!e.isFile()) continue;
      if (!RUNTIME_EXTENSIONS.has(path.extname(e.name))) continue;
      if (rel === selfRel) continue;
      seen += 1;
      try {
        const txt = fs.readFileSync(abs, 'utf8');
        if (regex.test(txt)) return true;
      } catch (_) { /* binary or unreadable — skip */ }
      if (seen >= MAX) break;
    }
  }
  return false;
}

function scoreCompletion(cwd) {
  const hits = [];
  let scanned = 0;
  const stack = [cwd];
  const MAX = 3000;
  while (stack.length && scanned < MAX) {
    const dir = stack.pop();
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { continue; }
    for (const e of entries) {
      const abs = path.join(dir, e.name);
      if (e.isDirectory()) {
        if (STUB_EXCLUDE_DIRS.has(e.name) || e.name.startsWith('.')) continue;
        stack.push(abs);
        continue;
      }
      if (!e.isFile()) continue;
      if (!RUNTIME_EXTENSIONS.has(path.extname(e.name))) continue;
      const rel = path.relative(cwd, abs).replace(/\\/g, '/');
      if (STUB_META_FILES.has(rel)) continue; // files that define the patterns
      scanned += 1;
      let txt;
      try { txt = fs.readFileSync(abs, 'utf8'); } catch (_) { continue; }
      const lines = txt.split('\n');
      for (let i = 0; i < lines.length; i++) {
        for (const pat of STUB_PATTERNS) {
          if (pat.test(lines[i])) {
            hits.push({ file: rel, line: i + 1, match: lines[i].trim().slice(0, 120) });
            break;
          }
        }
        if (hits.length >= 200) break;
      }
      if (hits.length >= 200) break;
    }
  }
  if (scanned === 0) return { score: 100, evidence: { scanned: 0, hits: 0 } };
  // Density per 20 files: 0 → 100, 1 → 0.
  const density = (hits.length / scanned) * 20;
  const score = Math.max(0, Math.round(100 - density * 100));
  return {
    score,
    evidence: {
      scanned_files: scanned,
      stub_hits: hits.length,
      sample: hits.slice(0, 5),
    },
  };
}

// MC-IO-500.2 (2026-04-26, InfinityOps) — module-level probe cache +
// retry-once. Pre-cache, scoreEnvMapping spawned `elixir --version`
// and `mix --version` once per subsystem (3× per /ira run on a
// 3-subsystem repo). On Windows under Scoop, transient PATH or spawn
// flakes could produce a 100% envScore on call N and 0% on call N+1,
// swinging Scalability by ±50 points between back-to-back /ira runs
// (observed on InfinityOps: infinity_mie 83 ↔ 33). The cache memoises
// per (bin, args) within a single Node process; the retry-once layer
// absorbs the dominant single-flake mode without masking real absence
// (two consecutive failures = real absence).
const PROBE_CACHE = new Map();

function probeBinary(bin, args) {
  const key = `${bin}:${(args || []).join(' ')}`;
  if (PROBE_CACHE.has(key)) return PROBE_CACHE.get(key);
  const doProbe = () => {
    try {
      // MC-IO-500.3e (2026-04-26, InfinityOps) — bumped 5000 → 60000.
      // Empirical Windows + Scoop runtime: `mix --version` takes 32s
      // and `elixir --version` takes 31s on Erlang/OTP 28 + Elixir 1.19.5
      // because the BEAM bootstraps the full runtime before printing.
      // Pre-bump, both required probes timed out → infinity_mie's
      // envMapping deterministically capped at 33 % despite both
      // binaries being present and on PATH. The PROBE_CACHE above
      // amortises the 30 s cost across subsystems within a single
      // /ira run; user-level penalty is one-time per invocation.
      const r = spawnSync(bin, args, {
        stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', timeout: 60000,
        shell: process.platform === 'win32',
      });
      return r.status === 0 || (r.stderr && /version/i.test(r.stderr));
    } catch (_) { return false; }
  };
  const result = doProbe() || doProbe();
  PROBE_CACHE.set(key, result);
  return result;
}

function resolveStackKeys(stack) {
  // stack may be "python", "mixed(power-pack+claude-skill)", etc.
  const m = stack.match(/^mixed\((.+)\)$/);
  if (m) return m[1].split('+').map((s) => s.trim());
  return [stack];
}

function scoreEnvMapping(stack) {
  const keys = resolveStackKeys(stack);
  const probeMap = new Map(); // dedupe probes across mixed sub-stacks
  const matchedKeys = [];
  for (const k of keys) {
    const probes = STACK_TOOLCHAIN[k];
    if (!probes) continue;
    matchedKeys.push(k);
    for (const p of probes) {
      const sig = `${p[0]}:${p[1].join(' ')}`;
      const prev = probeMap.get(sig);
      // If same probe appears required in any stack, keep it required.
      probeMap.set(sig, prev ? [p[0], p[1], prev[2] || p[2]] : p);
    }
  }
  if (probeMap.size === 0) {
    return { score: 100, evidence: { reason: 'no-probe-for-stack', stack, resolved: keys } };
  }
  const results = [];
  let requiredPresent = 0;
  let requiredTotal = 0;
  for (const [bin, probeArgs, required] of probeMap.values()) {
    const ok = probeBinary(bin, probeArgs);
    results.push({ bin, required, present: ok });
    if (required) {
      requiredTotal += 1;
      if (ok) requiredPresent += 1;
    }
  }
  if (requiredTotal === 0) {
    const optionalPresent = results.filter((r) => r.present).length;
    const score = results.length === 0 ? 100 : Math.round((optionalPresent / results.length) * 100);
    return { score, evidence: { probes: results, resolved: matchedKeys } };
  }
  const score = Math.round((requiredPresent / requiredTotal) * 100);
  return { score, evidence: { probes: results, resolved: matchedKeys } };
}

function weightedOverall(scores) {
  // Completion is weighted 2x because a stub is a delivery blocker per
  // the Reality Contract; others carry equal weight.
  const w = { edit_thrashing: 1, drift: 1, completion: 2, env_mapping: 1 };
  let num = 0, den = 0;
  for (const k of Object.keys(w)) {
    num += (scores[k] || 0) * w[k];
    den += w[k];
  }
  return Math.round(num / den);
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(helpText() + '\n');
    return 0;
  }
  const sub = readSubsystemInput(args);
  const cwd = sub.abs_path || sub.path || process.cwd();
  if (!fs.existsSync(cwd)) {
    process.stderr.write(`score.js: path does not exist: ${cwd}\n`);
    return 3;
  }
  const thrash = scoreEditThrashing(cwd);
  const drift = scoreDrift(cwd);
  const completion = scoreCompletion(cwd);
  const env = scoreEnvMapping(sub.stack || 'unknown');

  const scores = {
    edit_thrashing: thrash.score,
    drift: drift.score,
    completion: completion.score,
    env_mapping: env.score,
  };
  const payload = {
    subsystem_id: sub.id,
    subsystem_path: sub.path,
    stack: sub.stack,
    scores,
    overall: weightedOverall(scores),
    evidence: {
      edit_thrashing: thrash.evidence,
      drift: drift.evidence,
      completion: completion.evidence,
      env_mapping: env.evidence,
    },
    scored_at: new Date().toISOString(),
  };
  process.stdout.write(args.pretty ? JSON.stringify(payload, null, 2) + '\n' : JSON.stringify(payload) + '\n');
  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = {
  scoreEditThrashing,
  scoreDrift,
  scoreCompletion,
  scoreEnvMapping,
  weightedOverall,
  STUB_PATTERNS,
  RUNTIME_EXTENSIONS,
  OPS_DIR_PREFIXES,
  isOpsEntryPoint,
  TEST_DIR_SUBSTRINGS,
  TEST_FILE_SUFFIX_PATTERNS,
  isTestEntryPoint,
};
