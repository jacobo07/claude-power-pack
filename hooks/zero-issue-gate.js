#!/usr/bin/env node
/**
 * Zero-Issue Gate — Universal Quality Gate Hook
 *
 * Runs on every "stop" event. Auto-detects project language,
 * runs compile + scaffold audit + tests. Creates BLOCKED_DELIVERY.md on failure.
 *
 * Default: ADVISORY mode (always continues, warns on failure).
 * Set ZERO_ISSUE_GATE_ENFORCE=true to enable hard blocking after 3 failures.
 */

// --- JOBS-WOZ-EXEMPT (Apex Doctrine sealed 2026-05-16; expanded 2026-05-20) ---
// JOBS-WOZ-EXEMPT sha256=8739b341b9d38ab118aa7b3dc3348a6f28ea6ce817ec15ffcb6e017c4b6c823a
// JOBS-WOZ-TOKENS: ["t01","t02","t03","t04","t05","t09","t10"]
// --- end JOBS-WOZ-EXEMPT ---

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, execFileSync } = require('child_process');

const crypto = require('crypto');

const TRACKER_DIR = path.join(os.tmpdir(), 'claude-quality-gate');
const REGISTRY_PATH = path.join(__dirname, 'domain-registry.json');
const TRACES_DIR = path.join(os.homedir(), '.claude', 'traces');
const ENFORCE_HARD_BLOCK = process.env.ZERO_ISSUE_GATE_ENFORCE === 'true';

// ── Scaffold Patterns (from scaffold-auditor.js) ────────────────────
const SCAFFOLD_PATTERNS = [
  { regex: /^\s*#\s*\{[\w.]+,\s*\[\]\}/m, desc: 'Commented-out supervisor child', severity: 'CRITICAL' },
  { regex: /^\s*\/\/\s*(import|require|use)\s/m, desc: 'Commented-out import/require', severity: 'HIGH' },
  { regex: /^\s*#\s*(use|alias|import)\s/m, desc: 'Commented-out Elixir use/alias/import', severity: 'HIGH' },
  { regex: /TODO|FIXME|HACK|XXX|PLACEHOLDER/i, desc: 'TODO/FIXME placeholder found', severity: 'HIGH' },
  { regex: /raise\s+"?not\s+implemented/i, desc: 'Unimplemented function', severity: 'CRITICAL' },
  { regex: /:infinity\b/, desc: 'Infinite timeout (:infinity)', severity: 'CRITICAL' },
  { regex: /timeout:\s*0\b/, desc: 'Zero timeout', severity: 'HIGH' },
  { regex: /(?:timeout|delay|interval|wait|sleep)\s*[:=]\s*Infinity\b/i, desc: 'JavaScript Infinity timeout', severity: 'CRITICAL' },
  { regex: /\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)/, desc: 'Empty catch block', severity: 'HIGH' },
];

const SCANNABLE = new Set(['.ex', '.exs', '.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.rs', '.go']);
// Not scaffold-audited, but a change to one can break a compile, so it keeps the compile gate running.
const BUILD_EXT = new Set(['.mjs', '.cjs', '.mts', '.cts', '.json', '.jsonc', '.toml', '.yaml', '.yml', '.lock',
  '.mod', '.sum', '.gradle', '.kts', '.xml', '.cfg', '.ini', '.c', '.h', '.cpp', '.hpp', '.cc', '.cmake', '.heex', '.eex']);

// --- JOBS-WOZ double-scoped cryptographic exemption (parity w/ jobs-woz-gatekeeper.js) ---
// Owner-directed 2026-05-17. Narrows a Mistake #43 quine FP (allowlisted slop-token
// DETECTORS carrying literal tokens as detection DATA) WITHOUT opening a free-text
// bypass: basename allowlist is hardcoded + token-list sha256 must match.
// 2026-05-20 expansion (BLOCKED_DELIVERY.md durable fix — parity w/ scaffold-auditor.js):
// 16 detector basenames added. Each file MUST declare its JOBS-WOZ-TOKENS json +
// matching JOBS-WOZ-EXEMPT sha256 in its own header — basename membership alone is
// not exemption. See vault/standards/blocked-delivery-prevention.md.
const _JW_EXEMPT_BASENAMES = new Set([
  // Original (Owner Q2a/Q3a, 2026-05-17 — slop-token detectors)
  'dataset_enricher.py', 'quality_audit.py',
  // Extended 2026-05-20
  'scaffold-auditor.js', 'zero-issue-gate.js', 'zero-fiction-gate.js',
  'forensic_probes.py', 'test_forensic_probes.py',
  'ingest.py', 'run.py', 'validate.py',
  'score.js', 'investment_ready.js', 'oracle_cascade.py',
  'visual.py', 'skill-heat-map-advisor.js', 'baseline_ledger.py',
  'design_index.py', 'lazarus_revive_all.py',
]);
function _jwCanonHash(tokens) {
  const u = [...new Set(tokens.map(String))];
  u.sort((a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8')));
  return crypto.createHash('sha256').update(u.join(String.fromCharCode(10)), 'utf8').digest('hex');
}
function _jwParseLine(probe, marker) {
  const i = probe.indexOf(marker);
  if (i < 0) return null;
  let j = probe.indexOf(String.fromCharCode(10), i);
  if (j < 0) j = probe.length;
  return probe.slice(i + marker.length, j).trim();
}
function jwExemptionGranted(realPath, contentText) {
  try {
    const norm = String(realPath).split(String.fromCharCode(92)).join('/');
    const base = norm.slice(norm.lastIndexOf('/') + 1);
    if (!_JW_EXEMPT_BASENAMES.has(base)) return false;
    const sha = _jwParseLine(contentText, 'JOBS-WOZ-EXEMPT sha256=');
    const toksRaw = _jwParseLine(contentText, 'JOBS-WOZ-TOKENS:');
    if (!sha || !toksRaw) return false;
    const m = sha.match(/[0-9a-f]{64}/i);
    if (!m) return false;
    let toks;
    try { toks = JSON.parse(toksRaw); } catch (_e) { return false; }
    if (!Array.isArray(toks)) return false;
    return _jwCanonHash(toks) === m[0].toLowerCase();
  } catch (_e) { return false; }
}

// ── Domain Detection ────────────────────────────────────────────────

function loadRegistry() {
  try {
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  } catch {
    return { domains: {}, max_failures_before_block: 3 };
  }
}

function detectDomain(cwd) {
  const registry = loadRegistry();

  // Check per-project override first
  const overridePath = path.join(cwd, registry.override_file || '.claude-quality-gate.json');
  if (fs.existsSync(overridePath)) {
    try {
      const override = JSON.parse(fs.readFileSync(overridePath, 'utf8'));
      return { name: 'custom', ...override };
    } catch { /* fall through to auto-detect */ }
  }

  // Auto-detect from project files
  for (const [name, config] of Object.entries(registry.domains)) {
    for (const marker of config.detect) {
      if (fs.existsSync(path.join(cwd, marker))) {
        return { name, ...config };
      }
    }
  }

  return null; // Unknown project type — skip compile/test, still run scaffold
}

// ── Gate Execution ──────────────────────────────────────────────────

/** `withProjectBin`: put `<cwd>/node_modules/.bin` first on PATH, as `npm run` would, without
 *  paying npm's own startup (measured 1.3-12 s on a starved Windows host, which turned the
 *  declared typecheck into a timeout). The existing PATH key is kept whatever its case. */
function gateEnv(name, cwd, withProjectBin) {
  const env = { ...process.env, MIX_ENV: name === 'test' ? 'test' : process.env.MIX_ENV };
  if (withProjectBin) {
    const key = Object.keys(env).find(k => k.toUpperCase() === 'PATH') || 'PATH';
    env[key] = path.join(cwd, 'node_modules', '.bin') + path.delimiter + (env[key] || '');
  }
  return env;
}

function runGate(name, command, cwd, timeout = 30000, withProjectBin = false) {
  if (!command) return { passed: true, gate: name, output: 'skipped' };

  try {
    const output = execSync(command, {
      cwd,
      timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
      env: gateEnv(name, cwd, withProjectBin),
    });
    return { passed: true, gate: name, output: output.substring(0, 2000) };
  } catch (err) {
    // A command killed at its deadline did not judge the code -- it never finished. Measured
    // 2026-09-16 (KobiiSports Resort): on a starved host genomic_lint ran past the 30 s budget,
    // execSync killed it before Python flushed its block-buffered stdout, and the empty output
    // was counted as a COMPILE failure three times -> BLOCKED_DELIVERY.md with an EMPTY error
    // block naming four files that compile. A gate that could not run is not a gate that
    // rejected; it must never count toward the block.
    if (err.code === 'ETIMEDOUT' || (err.signal && err.status == null)) {
      return {
        passed: false, inconclusive: true, gate: name,
        output: `INCONCLUSIVE: \`${command}\` did not finish within ${timeout} ms ` +
                `(signal ${err.signal || 'none'}); nothing was judged. Likely host contention.`,
      };
    }
    const output = (err.stdout || '') + '\n' + (err.stderr || '');
    // `full` feeds the baseline comparison: a truncated error list would make old debt look new.
    return { passed: false, gate: name, output: output.substring(0, 3000), full: output.substring(0, 1000000), exitCode: err.status };
  }
}

function reportInconclusive(result) {
  process.stderr.write(`\n⚠️ ZERO-ISSUE GATE: ${result.gate.toUpperCase()} ${result.output}\n` +
    'Not counted as a failure and no BLOCKED_DELIVERY.md written. Re-run it when the host is idle.\n');
}

// ── The subject is the CHANGE ───────────────────────────────────────
// A gate that judges the whole repository reports upstream debt as the session's failure, and an
// unattended worker cannot tell the two apart. Measured 2026-09-25 (Orca X, P8 worker): 37 upstream
// TODOs in files the worker never touched, and a root tsconfig.json TypeScript 7 rejects regardless of
// the code. The session's change = everything that differs from the commit HEAD was at the session's
// first gate run, committed or not, plus every file the session edited. No git -> full scan (strict).

const WIN_GIT = 'C:\\Program Files\\Git\\cmd\\git.exe';
const SKIP_DIRS = ['node_modules', '.git', '_build', 'deps', 'target', 'dist', '__pycache__'];

function gitExe() {
  return process.env.CPP_GIT_EXE || (fs.existsSync(WIN_GIT) ? WIN_GIT : 'git');
}

function git(cwd, args, timeout = 15000) {
  try {
    return execFileSync(gitExe(), ['-C', cwd, ...args], {
      encoding: 'utf8', timeout, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch { return null; }
}

function readTracker(name) {
  try { return JSON.parse(fs.readFileSync(path.join(TRACKER_DIR, name), 'utf8')); } catch { return {}; }
}

function writeTracker(name, data) {
  try {
    if (!fs.existsSync(TRACKER_DIR)) fs.mkdirSync(TRACKER_DIR, { recursive: true });
    fs.writeFileSync(path.join(TRACKER_DIR, name), JSON.stringify(data));
  } catch { /* the next run records it again */ }
}

/** The commit HEAD was at this session's first gate run in `cwd`; null when `cwd` is not in git. */
function sessionBase(sessionId, cwd) {
  const name = `base-${sessionId}.json`;
  const bases = readTracker(name);
  const key = path.resolve(cwd);
  if (bases[key]) return bases[key];
  const head = (git(cwd, ['rev-parse', '--verify', '--quiet', 'HEAD']) || '').trim();
  if (!/^[0-9a-f]{40}$/.test(head)) return null;
  bases[key] = head;
  writeTracker(name, bases);
  return head;
}

function isUnder(file, dir) {
  const rel = path.relative(dir, file);
  return rel !== '' && !rel.startsWith('..') && !path.isAbsolute(rel);
}

/** Absolute paths of files the session changed under `cwd`, or null when that cannot be known. */
function changedFiles(sessionId, cwd, base) {
  if (!base) return null;
  const top = (git(cwd, ['rev-parse', '--show-toplevel']) || '').trim();
  const diff = git(cwd, ['diff', '--name-only', '-z', base]);
  const untracked = git(cwd, ['ls-files', '--others', '--exclude-standard', '--full-name', '-z']);
  if (!top || diff === null || untracked === null) return null;
  const files = new Set();
  for (const rel of (diff + untracked).split('\0').filter(Boolean)) files.add(path.resolve(top, rel));
  for (const f of getDirtyFiles(sessionId)) {
    if (typeof f === 'string') files.add(path.resolve(cwd, f));
  }
  const root = path.resolve(cwd);
  return [...files].filter(f => isUnder(f, root) && fs.existsSync(f) && fs.statSync(f).isFile());
}

function auditFile(cwd, full, violations) {
  if (!SCANNABLE.has(path.extname(full).toLowerCase())) return;
  if (path.relative(cwd, full).split(/[\\/]/).some(seg => SKIP_DIRS.includes(seg))) return;
  try {
    const content = fs.readFileSync(full, 'utf8');
    if (jwExemptionGranted(full, content)) return;
    const lines = content.split('\n');
    for (const pattern of SCAFFOLD_PATTERNS) {
      for (let i = 0; i < lines.length; i++) {
        if (pattern.regex.test(lines[i])) {
          violations.push({
            file: path.relative(cwd, full),
            line: i + 1,
            text: lines[i].trim().substring(0, 120),
            desc: pattern.desc,
            severity: pattern.severity,
          });
        }
      }
    }
  } catch { /* skip unreadable */ }
}

/**
 * True while any file a scaffold block names still carries a CRITICAL violation -- or when the block
 * names no file at all, since then nothing can prove it resolved. A block is the only thing that
 * carries a failure across a worker relay: the next session's base is AFTER the offending commit, so
 * its own (scoped) pass is vacuous about that file and must not lift the block.
 */
function scaffoldBlockStillFails(cwd, body) {
  // Only the CRITICAL lines are the block's reason. A block written before CRITICAL-first ordering was
  // truncated in scan order and may list none of them; it names nothing provable, so it stays.
  const named = [...new Set([...body.matchAll(/^\[CRITICAL\] (.+?):\d+ \u2014 /gm)].map(m => m[1]))];
  if (named.length === 0) return true;
  const violations = [];
  for (const rel of named) {
    const full = path.resolve(cwd, rel);
    if (fs.existsSync(full)) auditFile(cwd, full, violations);
  }
  return violations.some(v => v.severity === 'CRITICAL');
}

/** `scope` = the session's changed files; null = unknown, so the whole tree is judged. */
function runScaffoldAudit(cwd, scope = null) {
  const violations = [];

  function scanDir(dir, depth = 0) {
    if (depth > 3) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (SKIP_DIRS.includes(entry.name)) continue;
          scanDir(full, depth + 1);
        } else if (entry.isFile()) {
          auditFile(cwd, full, violations);
        }
      }
    } catch { /* skip unreadable dirs */ }
  }

  if (scope) for (const f of scope) auditFile(cwd, f, violations);
  else scanDir(cwd);
  const critical = violations.filter(v => v.severity === 'CRITICAL');
  return {
    passed: critical.length === 0,
    gate: 'scaffold',
    violations,
    criticalCount: critical.length,
    totalCount: violations.length,
    scope: scope ? `${scope.length} changed file(s)` : 'whole tree (no git scope)',
  };
}

// ── The project's own command, and a red that was already there ─────

const DECLARED_TYPECHECK = ['typecheck', 'type-check', 'check-types', 'tc'];

/** A typecheck the project declares for itself beats the registry's guess for its language. */
function declaredCompile(cwd) {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(cwd, 'package.json'), 'utf8'));
    const key = DECLARED_TYPECHECK.find(k => pkg && pkg.scripts && typeof pkg.scripts[k] === 'string');
    return key ? pkg.scripts[key] : null;
  } catch { return null; }
}

/** Error lines with positions removed, so an edit that shifts a line does not make old debt new. */
function errorFingerprints(output) {
  const set = new Set();
  for (const raw of String(output).replace(/\x1b\[[0-9;]*m/g, '').split(/\r?\n/)) {
    if (!/\berror\b/i.test(raw)) continue;
    const norm = raw.replace(/\\/g, '/').replace(/\(\d+,\d+\)/g, '').replace(/:\d+(:\d+)?/g, '')
      .replace(/\s+/g, ' ').trim();
    if (norm) set.add(norm);
  }
  return set;
}

/**
 * The compile errors `command` reports at `base`, from a throwaway worktree; cached per
 * (repository, base, command). null = could not be established, which the caller must never read
 * as "no errors at the base".
 */
function baselineErrors(cwd, base, command, timeout, withProjectBin = false) {
  const top = (git(cwd, ['rev-parse', '--show-toplevel']) || '').trim();
  if (!top || !base) return null;
  const rel = path.relative(top, path.resolve(cwd));
  const key = crypto.createHash('sha1').update(`${top}\0${rel}\0${base}\0${command}`).digest('hex').slice(0, 20);
  const cache = readTracker(`baseline-${key}.json`);
  if (Array.isArray(cache.errors)) return new Set(cache.errors);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'zig-baseline-'));
  try {
    if (git(top, ['worktree', 'add', '--detach', '--force', tmp, base], 60000) === null) return null;
    const where = path.join(tmp, rel);
    const deps = path.join(path.resolve(cwd), 'node_modules');
    if (fs.existsSync(deps) && !fs.existsSync(path.join(where, 'node_modules'))) {
      try { fs.symlinkSync(deps, path.join(where, 'node_modules'), 'junction'); } catch { /* compile may still run */ }
    }
    const r = runGate('compile', command, where, timeout, withProjectBin);
    if (r.inconclusive) return null;
    const errors = r.passed ? new Set() : errorFingerprints(r.full || r.output);
    if (!r.passed && errors.size === 0) return null;
    writeTracker(`baseline-${key}.json`, { base, command, errors: [...errors] });
    return errors;
  } finally {
    git(top, ['worktree', 'remove', '--force', tmp], 60000);
    // Retries: on Windows a just-exited child or a scanner holds the empty directory for a moment,
    // and a single attempt left one behind on every baseline (27 of 27 measured); Linux left none.
    try { fs.rmSync(tmp, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 }); } catch { /* os tmp */ }
    git(top, ['worktree', 'prune'], 30000);
  }
}

// ── Failure Tracking & Escalation ───────────────────────────────────

function getFailurePath(sessionId) {
  return path.join(TRACKER_DIR, `failures-${sessionId}.json`);
}

function trackFailure(sessionId, gate, cwd) {
  try {
    if (!fs.existsSync(TRACKER_DIR)) fs.mkdirSync(TRACKER_DIR, { recursive: true });
    const fpath = getFailurePath(sessionId);
    let data = {};
    try { data = JSON.parse(fs.readFileSync(fpath, 'utf8')); } catch { }
    if (!data[gate]) data[gate] = 0;
    data[gate]++;
    fs.writeFileSync(fpath, JSON.stringify(data));
    return data[gate];
  } catch { return 1; }
}

/** A pass ends the run of failures: the block threshold counts CONSECUTIVE failures. */
function resetFailure(sessionId, gate) {
  try {
    const fpath = getFailurePath(sessionId);
    const data = JSON.parse(fs.readFileSync(fpath, 'utf8'));
    if (data[gate]) { data[gate] = 0; fs.writeFileSync(fpath, JSON.stringify(data)); }
  } catch { /* no record, nothing to reset */ }
}

/**
 * The block this hook wrote for `gate` is lifted by that same gate passing -- nothing else. A block
 * for another gate, or a file a person or another tool wrote, is left exactly where it is.
 */
function clearOwnBlock(cwd, gate, stillFailing = null) {
  const f = path.join(cwd, 'BLOCKED_DELIVERY.md');
  try {
    const body = fs.readFileSync(f, 'utf8');
    if (!body.includes(`## Gate that failed: ${gate.toUpperCase()}\n`)) return false;
    if (!body.includes(`consecutive attempts to fix the ${gate} gate failed.`)) return false;
    if (stillFailing && stillFailing(body)) return false;
    fs.unlinkSync(f);
    process.stderr.write(`\n✅ BLOCKED_DELIVERY.md cleared: the ${gate} gate that wrote it now passes.\n`);
    return true;
  } catch { return false; }
}

function createBlockedDelivery(cwd, gate, output, failureCount, dirtyFiles) {
  const content = `# BLOCKED DELIVERY — ${path.basename(cwd)}

## Date: ${new Date().toISOString()}
## Gate that failed: ${gate.toUpperCase()}
## Failure count: ${failureCount}

### Exact error output:
\`\`\`
${output.substring(0, 5000)}
\`\`\`

### Files modified this session:
${dirtyFiles.map(f => `- ${f}`).join('\n') || '(unknown)'}

### Kill-switch status: ACTIVE
This file was created because ${failureCount} consecutive attempts to fix the ${gate} gate failed.
It clears itself when the ${gate} gate passes again (only the session's change is judged; a red
already present at the session base is reported as pre-existing, never counted). A person may delete it.
`;

  try {
    fs.writeFileSync(path.join(cwd, 'BLOCKED_DELIVERY.md'), content);
  } catch { /* best effort */ }
}

function getDirtyFiles(sessionId) {
  try {
    const trackerPath = path.join(TRACKER_DIR, `dirty-${sessionId}.json`);
    if (fs.existsSync(trackerPath)) {
      const data = JSON.parse(fs.readFileSync(trackerPath, 'utf8'));
      return Object.values(data).flat();
    }
  } catch { }
  return [];
}

// ── Agent Lightning Reward Emission ─────────────────────────────────

function emitReward(sessionId, value, source, metadata = {}) {
  try {
    if (!fs.existsSync(TRACES_DIR)) fs.mkdirSync(TRACES_DIR, { recursive: true });
    const bufferPath = path.join(TRACES_DIR, `pending_${sessionId}.jsonl`);
    const reward = {
      trace_id: `${sessionId}_reward_${Date.now()}`,
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      type: 'reward',
      value,
      source,
      ...metadata
    };
    fs.appendFileSync(bufferPath, JSON.stringify(reward) + '\n');
  } catch { /* best effort — never block gate evaluation */ }
}

// ── Core processing (extracted so hook-dispatcher.js can require this module) ──
function runGates(data) {
  try {
    data = data || {};
    const cwd = data.cwd || process.cwd();
    const sessionId = data.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';
    const registry = loadRegistry();
    const maxFailures = registry.max_failures_before_block || 3;

    const base = sessionBase(sessionId, cwd);
    const domain = detectDomain(cwd);
    const results = [];

    // Gate 1: COMPILE -- an explicit per-project override, else the project's own declared
    // typecheck, else the registry's guess for the language.
    const overridden = domain && domain.name === 'custom' && Object.prototype.hasOwnProperty.call(domain, 'compile');
    const declared = overridden ? null : declaredCompile(cwd);
    const compileCommand = overridden ? domain.compile : (declared || (domain && domain.compile) || null);
    const projectBin = Boolean(declared) && compileCommand === declared;
    const compileTimeout = (domain && domain.compile_timeout_ms) || 30000;
    const scope = changedFiles(sessionId, cwd, base);
    // A real typecheck at every turn end is a real cost. Measured 2026-09-27: Orca's declared typecheck
    // (three projects) plus its baseline checkout on a Windows host at 265-519 MB free. So compile runs
    // only when the change touched source or build files, and never when the host lacks the headroom:
    // an instrument must not consume the resource the whole machine is short of.
    const compileRelevant = (f) => path.basename(f) !== 'BLOCKED_DELIVERY.md' &&
      (SCANNABLE.has(path.extname(f).toLowerCase()) || BUILD_EXT.has(path.extname(f).toLowerCase()));
    const noSourceChanged = scope !== null && !scope.some(compileRelevant);
    const freeMb = Math.round(os.freemem() / 1048576);
    const floorMb = Number(process.env.ZIG_MIN_FREE_MB) || 1536;
    if (compileCommand && noSourceChanged) {
      process.stderr.write('\nℹ️ ZERO-ISSUE GATE: COMPILE skipped -- the session changed no source or build file.\n');
    } else if (compileCommand && freeMb < floorMb) {
      reportInconclusive({ gate: 'compile', output: `INCONCLUSIVE: the host has ${freeMb} MB free, below the ` +
        `${floorMb} MB floor (ZIG_MIN_FREE_MB); a typecheck now would starve it. Nothing was judged.` });
    } else if (compileCommand) {
      const compileResult = runGate('compile', compileCommand, cwd, compileTimeout, projectBin);
      if (compileResult.inconclusive) reportInconclusive(compileResult);
      let newErrors = null;
      if (!compileResult.passed && !compileResult.inconclusive) {
        const now = errorFingerprints(compileResult.full || compileResult.output);
        const before = now.size ? baselineErrors(cwd, base, compileCommand, compileTimeout, projectBin) : null;
        if (before) newErrors = [...now].filter(e => !before.has(e));
        if (newErrors && newErrors.length === 0) {
          process.stderr.write(`\n⚠️ ZERO-ISSUE GATE: COMPILE red is PRE-EXISTING -- all ${now.size} error(s) were already ` +
            `present at the session base ${base.slice(0, 9)}; none is new. Not counted.\n`);
          resetFailure(sessionId, 'compile');
        }
      }
      if (compileResult.passed) {
        results.push(compileResult);
        resetFailure(sessionId, 'compile');
        clearOwnBlock(cwd, 'compile');
      }
      if (!compileResult.passed && !compileResult.inconclusive && !(newErrors && newErrors.length === 0)) {
        results.push(compileResult);
        const count = trackFailure(sessionId, 'compile', cwd);
        emitReward(sessionId, 0.0, 'zero-issue-gate', { failed_gate: 'compile', failure_count: count });
        let msg = `\n❌ ZERO-ISSUE GATE: COMPILE FAILED (${domain ? domain.name : 'declared'}: ${compileCommand})\n`;
        msg += `${'─'.repeat(60)}\n`;
        if (newErrors) msg += `New since the session base ${base.slice(0, 9)}:\n${newErrors.slice(0, 30).join('\n')}\n\n`;
        else msg += `(no baseline for comparison -- every error counts)\n`;
        msg += compileResult.output.substring(0, 2000) + '\n';
        msg += `${'─'.repeat(60)}\n`;
        msg += `Fix the compile error before claiming done. Failure ${count}/${maxFailures}.\n`;
        if (count >= maxFailures) {
          createBlockedDelivery(cwd, 'compile', compileResult.output, count, getDirtyFiles(sessionId));
          msg += `\n🛑 BLOCKED: ${count} consecutive compile failures. BLOCKED_DELIVERY.md created.`;
          msg += ENFORCE_HARD_BLOCK ? ' STOPPING.\n' : ' (advisory — session continues)\n';
          process.stderr.write(msg);
          return { continue: !ENFORCE_HARD_BLOCK };
        }
        process.stderr.write(msg);
        return { continue: true };
      }
    }

    // Gate 2: SCAFFOLD AUDIT
    if (registry.scaffold_audit_enabled !== false) {
      const scaffoldResult = runScaffoldAudit(cwd, scope);
      results.push(scaffoldResult);
      if (scaffoldResult.passed) {
        resetFailure(sessionId, 'scaffold');
        clearOwnBlock(cwd, 'scaffold', (body) => scaffoldBlockStillFails(cwd, body));
      } else {
        const count = trackFailure(sessionId, 'scaffold', cwd);
        emitReward(sessionId, 0.0, 'zero-issue-gate', { failed_gate: 'scaffold', failure_count: count, critical_count: scaffoldResult.criticalCount });
        let msg = `\n❌ ZERO-ISSUE GATE: SCAFFOLD AUDIT FAILED (${scaffoldResult.criticalCount} CRITICAL in ${scaffoldResult.scope})\n`;
        msg += `${'─'.repeat(60)}\n`;
        for (const v of scaffoldResult.violations.slice(0, 10)) {
          msg += `[${v.severity}] ${v.file}:${v.line} — ${v.desc}\n`;
        }
        msg += `${'─'.repeat(60)}\n`;
        msg += `Fix CRITICAL violations before claiming done. Failure ${count}/${maxFailures}.\n`;
        if (count >= maxFailures) {
          // CRITICAL first: the block is truncated, and its CRITICAL lines are what lifting it re-checks.
          const ordered = [...scaffoldResult.violations].sort((a, b) => (b.severity === 'CRITICAL') - (a.severity === 'CRITICAL'));
          const output = ordered.map(v => `[${v.severity}] ${v.file}:${v.line} — ${v.desc}`).join('\n');
          createBlockedDelivery(cwd, 'scaffold', output, count, getDirtyFiles(sessionId));
          msg += `\n🛑 BLOCKED: ${count} consecutive scaffold failures. BLOCKED_DELIVERY.md created.`;
          msg += ENFORCE_HARD_BLOCK ? ' STOPPING.\n' : ' (advisory — session continues)\n';
          process.stderr.write(msg);
          return { continue: !ENFORCE_HARD_BLOCK };
        }
        process.stderr.write(msg);
        return { continue: true };
      }
    }

    // Gate 3: TESTS — opt-in only (env ZERO_ISSUE_GATE_RUN_TESTS=true).
    // Running the full suite synchronously on EVERY Stop event collided with the
    // dispatcher spawnSync wrap -> recurring ETIMEDOUT. Stop fires constantly; the
    // test gate belongs at commit time (HR-CASCADE-003). Default OFF keeps the fast
    // scaffold+slop gates; Owner opts in for a full run (dispatcher wrap is 70s > 60s).
    if (domain && domain.test && process.env.ZERO_ISSUE_GATE_RUN_TESTS === 'true') {
      const testResult = runGate('test', domain.test, cwd, 60000);
      if (testResult.inconclusive) reportInconclusive(testResult);
      else results.push(testResult);
      if (testResult.passed) {
        resetFailure(sessionId, 'test');
        clearOwnBlock(cwd, 'test');
      }
      if (!testResult.passed && !testResult.inconclusive) {
        const count = trackFailure(sessionId, 'test', cwd);
        emitReward(sessionId, 0.0, 'zero-issue-gate', { failed_gate: 'test', failure_count: count });
        let msg = `\n❌ ZERO-ISSUE GATE: TESTS FAILED (${domain.name})\n`;
        msg += `${'─'.repeat(60)}\n`;
        msg += testResult.output.substring(0, 2000) + '\n';
        msg += `${'─'.repeat(60)}\n`;
        msg += `Fix failing tests before claiming done. Failure ${count}/${maxFailures}.\n`;
        if (count >= maxFailures) {
          createBlockedDelivery(cwd, 'test', testResult.output, count, getDirtyFiles(sessionId));
          msg += `\n🛑 BLOCKED: ${count} consecutive test failures. BLOCKED_DELIVERY.md created.`;
          msg += ENFORCE_HARD_BLOCK ? ' STOPPING.\n' : ' (advisory — session continues)\n';
          process.stderr.write(msg);
          return { continue: !ENFORCE_HARD_BLOCK };
        }
        process.stderr.write(msg);
        return { continue: true };
      }
    }

    const passedGates = results.filter(r => r.passed).map(r => r.gate).join(', ');
    if (passedGates) {
      emitReward(sessionId, 1.0, 'zero-issue-gate', { gates_passed: passedGates.split(', ') });
      process.stderr.write(`\n✅ ZERO-ISSUE GATE: ALL PASSED (${passedGates})\n`);
    }
    return { continue: true };
  } catch (_) {
    // On hook error, allow continuation (don't block on hook bugs)
    return { continue: true };
  }
}

// The standing-block warning comes AFTER the gates: a run that just cleared the block must not
// also tell the worker to fix it.
function run(data) {
  const result = runGates(data);
  try {
    const f = path.join((data && data.cwd) || process.cwd(), 'BLOCKED_DELIVERY.md');
    if (fs.existsSync(f)) {
      process.stderr.write(`\n🛑 BLOCKED_DELIVERY.md EXISTS. Fix the issues before doing anything else:\n${fs.readFileSync(f, 'utf8').substring(0, 1000)}\n`);
    }
  } catch { /* the warning is advisory */ }
  return result;
}

// ── Dual-mode entry point ──
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 10000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    let data = {};
    try { data = JSON.parse(input); } catch (_) { /* keep empty */ }
    console.log(JSON.stringify(run(data)));
    process.exit(0);
  });
} else {
  module.exports = { run, runGate };
}
