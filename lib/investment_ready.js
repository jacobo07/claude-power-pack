#!/usr/bin/env node
/*
 * investment_ready.js — Investment-Ready Audit (IRA) orchestrator.
 *
 * Project-agnostic auditor that scores a repo against five axes used by
 * seed/Series-A due-diligence reviewers:
 *
 *   1. Scalability    — env-mapping + container/config-drivable signals
 *   2. Resilience     — error-handling density across runtime files
 *   3. Traceability   — logging density across runtime files
 *   4. Zero-Stub      — Reality-Contract placeholder score (reused)
 *   5. ROI-Wiring     — producer-consumer connectivity (inverted drift)
 *
 * Pipeline:
 *   discover.js  → subsystems[]
 *   score.js     → per-subsystem raw benchmarks (reused)
 *   (here)       → lift raw benchmarks + 2 new heuristics into 5 axes
 *   render       → progress-bar summary, per-subsystem breakdown, verdict
 *
 * Usage:
 *   node lib/investment_ready.js                      # summary
 *   node lib/investment_ready.js 2                    # drill into subsystem #2
 *   node lib/investment_ready.js --project <path>
 *   node lib/investment_ready.js --json
 *
 * Exit codes: 0 ok, 2 argv error, 3 io error.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const discover = require('./discover');
const score = require('./score');

const RUNTIME_EXTENSIONS = score.RUNTIME_EXTENSIONS;

const SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', 'target',
  '__pycache__', '.venv', 'venv', 'coverage', '_audit_cache',
  'tests', 'test', '__tests__', 'spec',
]);

// Regexes for the two new heuristics. Per-extension to reduce false
// positives: python uses try/except, JS uses try/catch, Go has `defer` +
// `if err != nil`, Rust has `Result<>/?`.
//
// MC-IO-500.1 (2026-04-26, InfinityOps) — recalibrated `.ex`/`.exs` to
// recognise OTP "let-it-crash" idioms beyond `rescue`/`try do`/`catch`.
// Pre-recalibration the rubric false-negatived ~80 % of idiomatic OTP
// code: a `use GenServer` module supervised by `Supervisor`/`DynamicSupervisor`
// IS error-handled (the supervisor restarts it on crash), even though the
// file body has zero `try`/`rescue` tokens. Likewise `with ... <- ... do`
// is the canonical Elixir railway pattern that handles `{:error, _}` returns
// structurally, and `{:error, atom}` tuples are the explicit error contract
// idiom. Adding these patterns lifts genuine OTP signals without inviting
// metric-gaming: agents cannot insert `use GenServer` cosmetically because
// the BEAM rejects modules that fail to implement the GenServer callbacks.
const ERROR_HANDLING_PATTERNS = {
  '.py':  [/\btry\s*:/, /\bexcept\b/, /\braise\s+/, /\bfinally\s*:/],
  '.js':  [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/, /\bfinally\s*\{/],
  '.mjs': [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/],
  '.cjs': [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/],
  // MC-IO-500.3c (2026-04-26, InfinityOps) — React Error Boundary
  // recognition for .ts/.tsx/.jsx. Production React app code rarely uses
  // try/catch in component bodies (errors propagate to ErrorBoundary
  // ancestors via React's render-phase error contract). A component
  // that defines `componentDidCatch` or the static
  // `getDerivedStateFromError` IS error-handled — it IS the error
  // boundary. Next.js / Remix / TanStack Router app dirs surface a
  // file-based equivalent (`error.tsx`, `error-boundary.tsx`,
  // `<ErrorBoundary>` JSX usage); the rubric should credit those too.
  // Anti-gaming: `componentDidCatch(error, info)` has a fixed signature
  // React calls; cosmetic insertion in a non-component function does
  // nothing at runtime — same as `use GenServer` in OTP.
  '.ts':  [
    /\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/,
    /\bcomponentDidCatch\b/, /\bgetDerivedStateFromError\b/,
    /<ErrorBoundary[\s>]/, /\bErrorBoundary\b/,
  ],
  '.tsx': [
    /\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/,
    /\bcomponentDidCatch\b/, /\bgetDerivedStateFromError\b/,
    /<ErrorBoundary[\s>]/, /\bErrorBoundary\b/,
  ],
  '.jsx': [
    /\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/,
    /\bcomponentDidCatch\b/, /\bgetDerivedStateFromError\b/,
    /<ErrorBoundary[\s>]/, /\bErrorBoundary\b/,
  ],
  '.go':  [/if\s+err\s*!=\s*nil/, /\brecover\s*\(/, /\bdefer\s+/],
  '.rs':  [/\?;/, /Result<[^>]*>/, /\bpanic!/, /match\s+.*\{/],
  '.java':[/\btry\s*\{/, /\bcatch\s*\(/, /\bthrows\s+/],
  '.kt':  [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/],
  '.ex':  [
    /\brescue\b/, /\btry\s+do\b/, /\bcatch\b/,
    /\buse\s+Supervisor\b/, /\buse\s+DynamicSupervisor\b/, /\buse\s+GenServer\b/,
    /Process\.flag\(:trap_exit/,
    /\bwith\s+[^\n]*<-/, /\{:error,\s*/,
  ],
  '.exs': [
    /\brescue\b/, /\btry\s+do\b/, /\bcatch\b/,
    /\buse\s+Supervisor\b/, /\buse\s+DynamicSupervisor\b/, /\buse\s+GenServer\b/,
    /Process\.flag\(:trap_exit/,
    /\bwith\s+[^\n]*<-/, /\{:error,\s*/,
  ],
  '.rb':  [/\bbegin\b/, /\brescue\b/, /\braise\b/],
  '.c':   [/\bgoto\s+\w*err/, /errno/, /perror\s*\(/],
  '.cpp': [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/],
  '.cs':  [/\btry\s*\{/, /\bcatch\s*\(/, /\bthrow\b/],
  '.swift':[/\bdo\s*\{/, /\bcatch\b/, /\bthrows\b/, /\btry\?/],
  '.sh':  [/\bset\s+-e\b/, /\btrap\s+/, /\|\|\s*exit/, /\|\|\s*return/],
  '.bash':[/\bset\s+-e\b/, /\btrap\s+/, /\|\|\s*exit/],
  '.ps1': [/\btry\s*\{/, /\bcatch\s*\{/, /\$ErrorActionPreference/],
};

const LOG_PATTERNS = {
  '.py':  [/\blogger\./, /\blogging\./, /\blog\.(info|warn|error|debug)/, /\bprint\s*\(/],
  '.js':  [/console\.(log|info|warn|error|debug)/, /\blogger\./, /\blog\.(info|warn|error|debug)/, /pino|winston|bunyan/],
  '.mjs': [/console\.(log|info|warn|error|debug)/, /\blogger\./],
  '.cjs': [/console\.(log|info|warn|error|debug)/, /\blogger\./],
  '.ts':  [/console\.(log|info|warn|error|debug)/, /\blogger\./],
  '.tsx': [/console\.(log|info|warn|error|debug)/, /\blogger\./],
  '.jsx': [/console\.(log|info|warn|error|debug)/, /\blogger\./],
  '.go':  [/log\.(Print|Fatal|Panic|Debug|Info|Warn|Error)/, /logger?\.\w+\(/, /zap\.|zerolog|logrus/],
  '.rs':  [/log::(info|warn|error|debug|trace)/, /println!|eprintln!/, /tracing::/],
  '.java':[/Logger|LoggerFactory|slf4j|log4j/, /\.info\(|\.warn\(|\.error\(/, /System\.out\.print/],
  '.kt':  [/Logger|LoggerFactory/, /\.info\(|\.warn\(|\.error\(/],
  // MC-IO-500.3a (2026-04-26, InfinityOps) — Elixir/OTP observability is
  // dominated by `:telemetry` events, not Logger calls. Production Phoenix
  // and Broadway pipelines emit `:telemetry.execute/3` for every meaningful
  // state transition (RFC-002 §7.4 telemetry whitelist is a canonical
  // exemplar). A module that emits scrubbed telemetry IS traceable; the
  // pre-recalibration rubric only matched `Logger.*` and `IO.*`, missing
  // the dominant OTP observability primitive. Telemetry handler attachment
  // (`:telemetry.attach`) is also a legitimate signal — the consumer side
  // of the same observability contract.
  '.ex':  [
    /Logger\.(info|warn|error|debug)/, /IO\.(puts|inspect)/,
    /:telemetry\.(execute|span|attach|attach_many)/,
  ],
  '.exs': [
    /Logger\.(info|warn|error|debug)/, /IO\.(puts|inspect)/,
    /:telemetry\.(execute|span|attach|attach_many)/,
  ],
  '.rb':  [/Logger\.new|Rails\.logger|\.debug\(|\.info\(/, /puts\s+/, /p\s+\w/],
  '.c':   [/\bprintf\s*\(/, /\bfprintf\s*\(/, /syslog\s*\(/],
  '.cpp': [/\bstd::c(out|err)/, /\bprintf\s*\(/, /spdlog/],
  '.cs':  [/ILogger|Serilog|NLog/, /Console\.Write/, /Debug\.Write/],
  '.swift':[/\bprint\s*\(/, /os_log|Logger/],
  '.sh':  [/\becho\s+/, /\bprintf\s+/, /logger\s+/],
  '.bash':[/\becho\s+/, /\bprintf\s+/, /logger\s+/],
  '.ps1': [/Write-(Host|Output|Information|Warning|Error|Verbose)/, /\$Host\.UI/],
};

const DOCKER_SIGNALS = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore'];
const K8S_SIGNALS = ['k8s', 'kubernetes', 'helm', 'Chart.yaml'];
const CONFIG_SIGNALS = ['.env.example', '.env.sample', 'config', 'settings.py', 'next.config.js', 'vite.config.js', 'nuxt.config.js'];
const CI_SIGNALS = ['.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci'];

const VERDICT_THRESHOLDS = [
  { min: 85, label: 'SERIES_A_READY',     headline: 'SERIES A READY',    emoji: '🏆' },
  { min: 75, label: 'SEED_READY',         headline: 'SEED READY',        emoji: '🌱' },
  { min: 60, label: 'ANGEL_READY',        headline: 'ANGEL / FRIENDS-&-FAMILY', emoji: '🪽' },
  { min: 0,  label: 'NOT_INVESTABLE',     headline: 'NOT INVESTABLE',    emoji: '❌' },
];

// ─────────────────────────── CLI ───────────────────────────
function parseArgs(argv) {
  const out = { project: process.cwd(), detail: null, json: false, help: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project' || a === '-p') out.project = argv[++i];
    else if (a === '--json') out.json = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else if (!a.startsWith('-') && out.detail === null) out.detail = a;
    else {
      process.stderr.write(`investment_ready.js: unexpected arg ${a}\n`);
      process.exit(2);
    }
  }
  return out;
}

function helpText() {
  return [
    '/ira — Investment-Ready Audit',
    '',
    'Usage: node lib/investment_ready.js [<N|id>] [--project <path>] [--json]',
    '',
    'With no selector: axis-level summary for the whole repo.',
    'With <N> or <id>: drill-down evidence for one subsystem.',
  ].join('\n');
}

// ─────────────────────── heuristics ────────────────────────

function walkRuntimeFiles(root, limit) {
  const results = [];
  const stack = [root];
  while (stack.length && results.length < limit) {
    const dir = stack.pop();
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { continue; }
    for (const e of entries) {
      const abs = path.join(dir, e.name);
      if (e.isDirectory()) {
        if (SKIP_DIRS.has(e.name) || e.name.startsWith('.')) continue;
        stack.push(abs);
        continue;
      }
      if (!e.isFile()) continue;
      const ext = path.extname(e.name);
      if (!RUNTIME_EXTENSIONS.has(ext)) continue;
      results.push({ abs, rel: path.relative(root, abs).replace(/\\/g, '/'), ext });
      if (results.length >= limit) return results;
    }
  }
  return results;
}

function scoreResilience(cwd) {
  const files = walkRuntimeFiles(cwd, 1500);
  if (files.length === 0) {
    return { score: 100, evidence: { scanned: 0, reason: 'no-runtime-files' } };
  }
  let withHandling = 0;
  const missing = [];
  for (const f of files) {
    const patterns = ERROR_HANDLING_PATTERNS[f.ext];
    if (!patterns) continue; // extension has no defined pattern → skip
    let txt;
    try { txt = fs.readFileSync(f.abs, 'utf8'); } catch (_) { continue; }
    const hit = patterns.some((p) => p.test(txt));
    if (hit) withHandling += 1;
    else if (missing.length < 5 && txt.length > 200) missing.push(f.rel);
  }
  const relevant = files.filter((f) => ERROR_HANDLING_PATTERNS[f.ext]).length;
  if (relevant === 0) return { score: 100, evidence: { scanned: files.length, reason: 'no-supported-extensions' } };
  const ratio = withHandling / relevant;
  const s = Math.round(ratio * 100);
  return {
    score: s,
    evidence: {
      scanned_files: relevant,
      files_with_handling: withHandling,
      ratio: Math.round(ratio * 1000) / 1000,
      missing_sample: missing,
    },
  };
}

function scoreTraceability(cwd) {
  const files = walkRuntimeFiles(cwd, 1500);
  if (files.length === 0) {
    return { score: 100, evidence: { scanned: 0, reason: 'no-runtime-files' } };
  }
  let withLog = 0;
  const missing = [];
  for (const f of files) {
    const patterns = LOG_PATTERNS[f.ext];
    if (!patterns) continue;
    let txt;
    try { txt = fs.readFileSync(f.abs, 'utf8'); } catch (_) { continue; }
    const hit = patterns.some((p) => p.test(txt));
    if (hit) withLog += 1;
    else if (missing.length < 5 && txt.length > 200) missing.push(f.rel);
  }
  const relevant = files.filter((f) => LOG_PATTERNS[f.ext]).length;
  if (relevant === 0) return { score: 100, evidence: { scanned: files.length, reason: 'no-supported-extensions' } };
  const ratio = withLog / relevant;
  // Logging is not expected in EVERY file — normalize so 50% → 100.
  const s = Math.min(100, Math.round(ratio * 200));
  return {
    score: s,
    evidence: {
      scanned_files: relevant,
      files_with_logging: withLog,
      ratio: Math.round(ratio * 1000) / 1000,
      missing_sample: missing,
    },
  };
}

function scaleScalability(envScore, cwd) {
  // envScore comes from score.scoreEnvMapping — toolchain presence.
  // Combine with deployability signals: docker / k8s / ci / config.
  const has = (names) => names.some((n) => fs.existsSync(path.join(cwd, n)));
  const docker = has(DOCKER_SIGNALS);
  const k8s = has(K8S_SIGNALS);
  const ci = has(CI_SIGNALS);
  const config = has(CONFIG_SIGNALS);
  // Deployability weight: each signal worth 10 points over 60 base.
  const deploy = 60
    + (docker ? 15 : 0)
    + (k8s ? 10 : 0)
    + (ci ? 10 : 0)
    + (config ? 5 : 0);
  const cappedDeploy = Math.min(100, deploy);
  // Final = mean(envScore, deployability)
  const s = Math.round((envScore + cappedDeploy) / 2);
  return {
    score: s,
    evidence: {
      env_toolchain: envScore,
      deploy_score: cappedDeploy,
      signals: { docker, k8s, ci, config_example: config },
    },
  };
}

function roiWiringFromDrift(driftScore, driftEvidence) {
  // drift: 100 = everything wired, 0 = orphans everywhere.
  // ROI wiring IS drift — surface it under the investment label.
  return {
    score: driftScore,
    evidence: driftEvidence,
  };
}

// ─────────────────── per-subsystem scoring ─────────────────

function auditSubsystem(sub) {
  const cwd = sub.abs_path;
  const completion = score.scoreCompletion(cwd);
  const drift = score.scoreDrift(cwd);
  const env = score.scoreEnvMapping(sub.stack || 'unknown');
  const resilience = scoreResilience(cwd);
  const traceability = scoreTraceability(cwd);
  const scalability = scaleScalability(env.score, cwd);
  const roi = roiWiringFromDrift(drift.score, drift.evidence);

  const axes = {
    scalability:  scalability.score,
    resilience:   resilience.score,
    traceability: traceability.score,
    zero_stub:    completion.score,
    roi_wiring:   roi.score,
  };
  const overall = weightedInvestment(axes);
  return {
    subsystem_id: sub.id,
    subsystem_path: sub.path,
    stack: sub.stack,
    axes,
    overall,
    verdict: verdictFor(overall),
    evidence: {
      scalability:  scalability.evidence,
      resilience:   resilience.evidence,
      traceability: traceability.evidence,
      zero_stub:    completion.evidence,
      roi_wiring:   roi.evidence,
    },
    scored_at: new Date().toISOString(),
  };
}

function weightedInvestment(axes) {
  // Zero-stub is a hard gate — no investor tolerates placeholders.
  // ROI wiring is next: disconnected code = no product.
  const w = {
    scalability:  1,
    resilience:   1,
    traceability: 1,
    zero_stub:    3,
    roi_wiring:   2,
  };
  let num = 0, den = 0;
  for (const k of Object.keys(w)) {
    num += (axes[k] || 0) * w[k];
    den += w[k];
  }
  return Math.round(num / den);
}

function verdictFor(score) {
  for (const v of VERDICT_THRESHOLDS) {
    if (score >= v.min) return v;
  }
  return VERDICT_THRESHOLDS[VERDICT_THRESHOLDS.length - 1];
}

// ─────────────────────── rendering ─────────────────────────

function bar(pct, width) {
  width = width || 20;
  const filled = Math.round((pct / 100) * width);
  return '█'.repeat(filled) + '░'.repeat(Math.max(0, width - filled));
}

function renderSummary(envelope) {
  const { root, scanned_at, reports, aggregate } = envelope;
  const lines = [];
  lines.push('Investment-Ready Audit — /ira');
  lines.push(`root: ${root}`);
  lines.push(`scanned: ${scanned_at}`);
  lines.push(`subsystems: ${reports.length}`);
  lines.push('');
  lines.push(`OVERALL: ${bar(aggregate.overall, 20)}  ${aggregate.overall}%  ${aggregate.verdict.emoji} ${aggregate.verdict.headline}`);
  lines.push('');
  lines.push('AXES (repo-wide mean):');
  const axes = aggregate.axes;
  const axisLabels = {
    scalability:  'Scalability',
    resilience:   'Resilience',
    traceability: 'Traceability',
    zero_stub:    'Zero-Stub',
    roi_wiring:   'ROI-Wiring',
  };
  for (const k of Object.keys(axisLabels)) {
    const pct = axes[k];
    lines.push(`  ${pad(axisLabels[k], 14)} ${bar(pct, 20)}  ${pad(String(pct) + '%', 5)}`);
  }
  lines.push('');
  lines.push('SUBSYSTEMS:');
  const rows = [['#', 'ID', 'STACK', 'SCAL', 'RES', 'TRACE', 'STUB', 'ROI', 'OVERALL', 'VERDICT']];
  reports.forEach((r, idx) => {
    const a = r.axes || {};
    rows.push([
      String(idx + 1),
      r.subsystem_id || '?',
      r.stack || '?',
      String(a.scalability ?? '-'),
      String(a.resilience ?? '-'),
      String(a.traceability ?? '-'),
      String(a.zero_stub ?? '-'),
      String(a.roi_wiring ?? '-'),
      String(r.overall ?? '-'),
      r.verdict.headline,
    ]);
  });
  const widths = rows[0].map((_, c) => Math.max(...rows.map((row) => String(row[c]).length)));
  for (const row of rows) {
    lines.push('  ' + row.map((v, c) => pad(v, widths[c])).join('  '));
  }
  lines.push('');
  lines.push('drill down with: /ira <N>  (or by id)');
  return lines.join('\n');
}

function pad(s, n) {
  s = String(s);
  return s.length >= n ? s : s + ' '.repeat(n - s.length);
}

function renderDetail(envelope, selector) {
  const { reports } = envelope;
  const n = Number(selector);
  let report = null;
  if (!Number.isNaN(n) && n >= 1 && n <= reports.length) report = reports[n - 1];
  else report = reports.find((r) => r.subsystem_id === selector);
  if (!report) return `/ira: no subsystem matches "${selector}"`;

  const lines = [];
  lines.push(`Subsystem: ${report.subsystem_id} (${report.stack})`);
  lines.push(`path: ${report.subsystem_path}`);
  lines.push(`scored: ${report.scored_at}`);
  lines.push('');
  lines.push(`OVERALL: ${bar(report.overall, 20)}  ${report.overall}%  ${report.verdict.emoji} ${report.verdict.headline}`);
  lines.push('');
  const labels = {
    scalability:  'Scalability',
    resilience:   'Resilience',
    traceability: 'Traceability',
    zero_stub:    'Zero-Stub',
    roi_wiring:   'ROI-Wiring',
  };
  for (const k of Object.keys(labels)) {
    const v = report.axes[k];
    lines.push(`— ${labels[k]}: ${bar(v, 20)}  ${v}%`);
    const ev = report.evidence[k];
    if (ev) lines.push('  ' + JSON.stringify(ev, null, 2).split('\n').join('\n  '));
    lines.push('');
  }
  return lines.join('\n');
}

function aggregateReports(reports) {
  if (reports.length === 0) {
    return { overall: 100, axes: { scalability: 100, resilience: 100, traceability: 100, zero_stub: 100, roi_wiring: 100 }, verdict: verdictFor(100) };
  }
  const mean = (getter) => Math.round(reports.reduce((a, r) => a + (getter(r) || 0), 0) / reports.length);
  const axes = {
    scalability:  mean((r) => r.axes.scalability),
    resilience:   mean((r) => r.axes.resilience),
    traceability: mean((r) => r.axes.traceability),
    zero_stub:    mean((r) => r.axes.zero_stub),
    roi_wiring:   mean((r) => r.axes.roi_wiring),
  };
  const overall = weightedInvestment(axes);
  return { overall, axes, verdict: verdictFor(overall) };
}

// ─────────────────────── main ──────────────────────────────

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
    process.stderr.write(`/ira: cannot resolve ${args.project}: ${err.message}\n`);
    return 3;
  }
  const { subsystems } = discover.walk(rootAbs);
  if (subsystems.length === 0) {
    process.stdout.write('/ira: no manifests found at root — nothing to audit.\n');
    return 0;
  }
  const reports = subsystems.map(auditSubsystem);
  const aggregate = aggregateReports(reports);
  const envelope = {
    root: rootAbs.replace(/\\/g, '/'),
    scanned_at: new Date().toISOString(),
    reports,
    aggregate,
  };
  if (args.json) {
    process.stdout.write(JSON.stringify(envelope, null, 2) + '\n');
    return 0;
  }
  const out = args.detail != null ? renderDetail(envelope, args.detail) : renderSummary(envelope);
  process.stdout.write(out + '\n');
  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = {
  auditSubsystem,
  scoreResilience,
  scoreTraceability,
  scaleScalability,
  weightedInvestment,
  verdictFor,
  aggregateReports,
  renderSummary,
  renderDetail,
  VERDICT_THRESHOLDS,
};
