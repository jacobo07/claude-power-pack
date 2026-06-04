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
const { execSync } = require('child_process');

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

function runGate(name, command, cwd, timeout = 30000) {
  if (!command) return { passed: true, gate: name, output: 'skipped' };

  try {
    const output = execSync(command, {
      cwd,
      timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, MIX_ENV: name === 'test' ? 'test' : process.env.MIX_ENV },
    });
    return { passed: true, gate: name, output: output.substring(0, 2000) };
  } catch (err) {
    const output = (err.stdout || '') + '\n' + (err.stderr || '');
    return { passed: false, gate: name, output: output.substring(0, 3000), exitCode: err.status };
  }
}

function runScaffoldAudit(cwd) {
  const violations = [];

  function scanDir(dir, depth = 0) {
    if (depth > 3) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (['node_modules', '.git', '_build', 'deps', 'target', 'dist', '__pycache__'].includes(entry.name)) continue;
          scanDir(full, depth + 1);
        } else if (entry.isFile() && SCANNABLE.has(path.extname(entry.name).toLowerCase())) {
          try {
            const content = fs.readFileSync(full, 'utf8');
            if (jwExemptionGranted(full, content)) continue;
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
      }
    } catch { /* skip unreadable dirs */ }
  }

  scanDir(cwd);
  const critical = violations.filter(v => v.severity === 'CRITICAL');
  return {
    passed: critical.length === 0,
    gate: 'scaffold',
    violations,
    criticalCount: critical.length,
    totalCount: violations.length,
  };
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
Manual intervention required. Delete this file after fixing to re-enable delivery.
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
function run(data) {
  try {
    data = data || {};
    const cwd = data.cwd || process.cwd();
    const sessionId = data.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';
    const registry = loadRegistry();
    const maxFailures = registry.max_failures_before_block || 3;

    if (fs.existsSync(path.join(cwd, 'BLOCKED_DELIVERY.md'))) {
      const blockContent = fs.readFileSync(path.join(cwd, 'BLOCKED_DELIVERY.md'), 'utf8');
      process.stderr.write(`\n🛑 BLOCKED_DELIVERY.md EXISTS. Fix the issues before doing anything else:\n${blockContent.substring(0, 1000)}\n`);
    }

    const domain = detectDomain(cwd);
    const results = [];

    // Gate 1: COMPILE
    if (domain && domain.compile) {
      const compileResult = runGate('compile', domain.compile, cwd);
      results.push(compileResult);
      if (!compileResult.passed) {
        const count = trackFailure(sessionId, 'compile', cwd);
        emitReward(sessionId, 0.0, 'zero-issue-gate', { failed_gate: 'compile', failure_count: count });
        let msg = `\n❌ ZERO-ISSUE GATE: COMPILE FAILED (${domain.name})\n`;
        msg += `${'─'.repeat(60)}\n`;
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
      const scaffoldResult = runScaffoldAudit(cwd);
      results.push(scaffoldResult);
      if (!scaffoldResult.passed) {
        const count = trackFailure(sessionId, 'scaffold', cwd);
        emitReward(sessionId, 0.0, 'zero-issue-gate', { failed_gate: 'scaffold', failure_count: count, critical_count: scaffoldResult.criticalCount });
        let msg = `\n❌ ZERO-ISSUE GATE: SCAFFOLD AUDIT FAILED (${scaffoldResult.criticalCount} CRITICAL)\n`;
        msg += `${'─'.repeat(60)}\n`;
        for (const v of scaffoldResult.violations.slice(0, 10)) {
          msg += `[${v.severity}] ${v.file}:${v.line} — ${v.desc}\n`;
        }
        msg += `${'─'.repeat(60)}\n`;
        msg += `Fix CRITICAL violations before claiming done. Failure ${count}/${maxFailures}.\n`;
        if (count >= maxFailures) {
          const output = scaffoldResult.violations.map(v => `[${v.severity}] ${v.file}:${v.line} — ${v.desc}`).join('\n');
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
      results.push(testResult);
      if (!testResult.passed) {
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
  module.exports = { run };
}
