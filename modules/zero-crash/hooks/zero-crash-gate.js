#!/usr/bin/env node
/**
 * Zero-Crash Gate — Advisory Quality Gate (Stop Hook)
 *
 * Runs on session "stop" event. Auto-detects project language,
 * runs compile + scaffold audit + tests.
 *
 * Default: ADVISORY mode — always returns {continue: true}.
 * Creates BLOCKED_DELIVERY.md as evidence on failure.
 * Set ZERO_CRASH_ENFORCE=true to enable hard blocking after max failures.
 *
 * Part of Claude Power Pack — Zero-Crash Environment module.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const ENFORCE = process.env.ZERO_CRASH_ENFORCE === 'true';
const TRACKER_DIR = path.join(os.tmpdir(), 'zero-crash-gate');
const MODULE_DIR = path.join(__dirname, '..');
const CONFIG_PATH = path.join(MODULE_DIR, 'config.json');

// ── Load Config ────────────────────────────────────────────────────

function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  } catch {
    return { quality_gate: { max_failures_before_warning: 3, create_blocked_delivery: true } };
  }
}

// ── Domain Detection (simplified — can be extended via config) ────

const DOMAIN_MARKERS = {
  elixir:     { detect: ['mix.exs'], compile: 'mix compile --warnings-as-errors', test: 'mix test' },
  typescript: { detect: ['tsconfig.json'], compile: 'npx tsc --noEmit', test: 'npm test' },
  python:     { detect: ['pyproject.toml', 'setup.py', 'requirements.txt'], compile: null, test: 'pytest' },
  rust:       { detect: ['Cargo.toml'], compile: 'cargo build', test: 'cargo test' },
  java:       { detect: ['pom.xml'], compile: 'mvn compile -q', test: 'mvn test -q' },
  go:         { detect: ['go.mod'], compile: 'go build ./...', test: 'go test ./...' },
};

function detectDomain(cwd) {
  for (const [name, config] of Object.entries(DOMAIN_MARKERS)) {
    for (const marker of config.detect) {
      if (fs.existsSync(path.join(cwd, marker))) {
        return { name, ...config };
      }
    }
  }
  return null;
}

// ── Gate Execution ─────────────────────────────────────────────────

function runGate(name, command, cwd, timeout = 30000) {
  if (!command) return { passed: true, gate: name, output: 'skipped (no command)' };

  try {
    const output = execSync(command, {
      cwd,
      timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { passed: true, gate: name, output: output.substring(0, 2000) };
  } catch (err) {
    const output = ((err.stdout || '') + '\n' + (err.stderr || '')).substring(0, 3000);
    return { passed: false, gate: name, output, exitCode: err.status };
  }
}

// ── Scaffold Audit ─────────────────────────────────────────────────

const SCAFFOLD_PATTERNS = [
  { regex: /^\s*#\s*\{[\w.]+,\s*\[\]\}/m, desc: 'Commented-out supervisor child', severity: 'CRITICAL' },
  { regex: /^\s*\/\/\s*(import|require|use)\s/m, desc: 'Commented-out import/require', severity: 'HIGH' },
  { regex: /raise\s+"?not\s+implemented/i, desc: 'Unimplemented function', severity: 'CRITICAL' },
  { regex: new RegExp(':infin' + 'ity\\b'), desc: 'Infinite timeout (:infini' + 'ty)', severity: 'CRITICAL' },
  { regex: new RegExp('Infini' + 'ty\\b'), desc: 'JavaScript Infini' + 'ty timeout', severity: 'CRITICAL' },
  { regex: /\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)/, desc: 'Empty catch block', severity: 'HIGH' },
];

const SCANNABLE = new Set(['.ex', '.exs', '.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.rs', '.go']);

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
            const lines = content.split('\n');
            for (const pattern of SCAFFOLD_PATTERNS) {
              for (let i = 0; i < lines.length; i++) {
                if (pattern.regex.test(lines[i])) {
                  violations.push({
                    file: path.relative(cwd, full),
                    line: i + 1,
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
  return { passed: critical.length === 0, gate: 'scaffold', violations, criticalCount: critical.length };
}

// ── Failure Tracking ───────────────────────────────────────────────

function trackFailure(sessionId, gate) {
  try {
    if (!fs.existsSync(TRACKER_DIR)) fs.mkdirSync(TRACKER_DIR, { recursive: true });
    const fpath = path.join(TRACKER_DIR, `failures-${sessionId}.json`);
    let data = {};
    try { data = JSON.parse(fs.readFileSync(fpath, 'utf8')); } catch { }
    if (!data[gate]) data[gate] = 0;
    data[gate]++;
    fs.writeFileSync(fpath, JSON.stringify(data));
    return data[gate];
  } catch { return 1; }
}

function createBlockedDelivery(cwd, gate, output, failureCount) {
  const content = `# BLOCKED DELIVERY — ${path.basename(cwd)}

## Date: ${new Date().toISOString()}
## Gate: ${gate.toUpperCase()}
## Failures: ${failureCount}
## Mode: ${ENFORCE ? 'ENFORCED (session blocked)' : 'ADVISORY (session continues)'}

### Error output:
\`\`\`
${output.substring(0, 5000)}
\`\`\`

### Action required:
Fix the ${gate} errors above. ${ENFORCE ? 'Session was blocked.' : 'Session continued (advisory mode).'}
Delete this file after fixing to clear the warning.
`;

  try {
    fs.writeFileSync(path.join(cwd, 'BLOCKED_DELIVERY.md'), content);
  } catch { /* best effort */ }
}

// ── Telemetry (opt-in) ────────────────────────────────────────────

function reportToVPS(sessionId, gate, passed, platform) {
  const apiKey = process.env.ZERO_CRASH_API_KEY;
  if (!apiKey) return;

  const endpoint = process.env.ZERO_CRASH_VPS_ENDPOINT || 'http://204.168.166.63:9879';
  const http = require('http');
  const body = JSON.stringify({
    session_hash: require('crypto').createHash('sha256').update(sessionId).digest('hex').substring(0, 16),
    gate,
    passed,
    platform: process.platform,
    timestamp: new Date().toISOString(),
    enforce_mode: ENFORCE,
  });

  try {
    const url = new URL(`${endpoint}/api/v1/zero-crash/report`);
    const req = http.request({
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}`, 'Content-Length': Buffer.byteLength(body) },
      timeout: 3000,
    });
    req.on('error', () => {});
    req.on('timeout', () => req.destroy());
    req.write(body);
    req.end();
  } catch { /* best effort — never block gate */ }
}

// ── Main ───────────────────────────────────────────────────────────

let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 10000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);

  try {
    const data = JSON.parse(input);
    const cwd = data.cwd || process.cwd();
    const sessionId = data.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';
    const config = loadConfig();
    const maxFailures = config.quality_gate?.max_failures_before_warning || 3;

    // Remind if BLOCKED_DELIVERY.md exists
    if (fs.existsSync(path.join(cwd, 'BLOCKED_DELIVERY.md'))) {
      process.stderr.write('\n[Zero-Crash] BLOCKED_DELIVERY.md exists — fix issues before claiming done\n');
    }

    const domain = detectDomain(cwd);
    const results = [];

    // Gate 1: COMPILE
    if (domain && domain.compile) {
      const result = runGate('compile', domain.compile, cwd);
      results.push(result);
      reportToVPS(sessionId, 'compile', result.passed);

      if (!result.passed) {
        const count = trackFailure(sessionId, 'compile');
        let msg = `\n[Zero-Crash] COMPILE FAILED (${domain.name}) — ${count}/${maxFailures}\n`;
        msg += result.output.substring(0, 1500) + '\n';

        if (count >= maxFailures) {
          if (config.quality_gate?.create_blocked_delivery !== false) {
            createBlockedDelivery(cwd, 'compile', result.output, count);
          }
          msg += ENFORCE ? '[Zero-Crash] BLOCKED — session stopping\n' : '[Zero-Crash] BLOCKED_DELIVERY.md created (advisory — session continues)\n';
          process.stderr.write(msg);
          console.log(JSON.stringify({ continue: !ENFORCE }));
          return;
        }
        process.stderr.write(msg);
        console.log(JSON.stringify({ continue: true }));
        return;
      }
    }

    // Gate 2: SCAFFOLD AUDIT
    const scaffoldResult = runScaffoldAudit(cwd);
    results.push(scaffoldResult);
    reportToVPS(sessionId, 'scaffold', scaffoldResult.passed);

    if (!scaffoldResult.passed) {
      const count = trackFailure(sessionId, 'scaffold');
      let msg = `\n[Zero-Crash] SCAFFOLD AUDIT FAILED (${scaffoldResult.criticalCount} CRITICAL) — ${count}/${maxFailures}\n`;
      for (const v of scaffoldResult.violations.slice(0, 8)) {
        msg += `  [${v.severity}] ${v.file}:${v.line} — ${v.desc}\n`;
      }

      if (count >= maxFailures) {
        const output = scaffoldResult.violations.map(v => `[${v.severity}] ${v.file}:${v.line} — ${v.desc}`).join('\n');
        if (config.quality_gate?.create_blocked_delivery !== false) {
          createBlockedDelivery(cwd, 'scaffold', output, count);
        }
        msg += ENFORCE ? '[Zero-Crash] BLOCKED — session stopping\n' : '[Zero-Crash] BLOCKED_DELIVERY.md created (advisory — session continues)\n';
        process.stderr.write(msg);
        console.log(JSON.stringify({ continue: !ENFORCE }));
        return;
      }
      process.stderr.write(msg);
      console.log(JSON.stringify({ continue: true }));
      return;
    }

    // Gate 3: TESTS
    if (domain && domain.test) {
      const result = runGate('test', domain.test, cwd, 60000);
      results.push(result);
      reportToVPS(sessionId, 'test', result.passed);

      if (!result.passed) {
        const count = trackFailure(sessionId, 'test');
        let msg = `\n[Zero-Crash] TESTS FAILED (${domain.name}) — ${count}/${maxFailures}\n`;
        msg += result.output.substring(0, 1500) + '\n';

        if (count >= maxFailures) {
          if (config.quality_gate?.create_blocked_delivery !== false) {
            createBlockedDelivery(cwd, 'test', result.output, count);
          }
          msg += ENFORCE ? '[Zero-Crash] BLOCKED — session stopping\n' : '[Zero-Crash] BLOCKED_DELIVERY.md created (advisory — session continues)\n';
          process.stderr.write(msg);
          console.log(JSON.stringify({ continue: !ENFORCE }));
          return;
        }
        process.stderr.write(msg);
        console.log(JSON.stringify({ continue: true }));
        return;
      }
    }

    // All passed
    const passed = results.filter(r => r.passed).map(r => r.gate).join(', ');
    if (passed) {
      process.stderr.write(`\n[Zero-Crash] ALL GATES PASSED (${passed})\n`);
    }
    console.log(JSON.stringify({ continue: true }));

  } catch (e) {
    // Hook errors never block
    console.log(JSON.stringify({ continue: true }));
  }
});
