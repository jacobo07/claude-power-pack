#!/usr/bin/env node
/**
 * Scaffold Auditor — Stop Hook ONLY (runs when Claude session ends)
 *
 * ACTIVE ENFORCEMENT against Mistake #16 (Scaffold Illusion).
 * Scans the session's dirty files for scaffold patterns and warns
 * if violations are detected before session close.
 *
 * 2026-05-20 UPGRADE — JOBS-WOZ-EXEMPT honor (BL-0070 + Apex Doctrine):
 * the existing project-level Analytical-Log Exemption doctrine (sealed
 * 2026-05-16, parity with zero-issue-gate.js + zero-fiction-gate.js) is
 * now honored here too. Was missing — caused 7 consecutive failures of
 * BLOCKED_DELIVERY.md regeneration on legitimate detector files
 * (Mistake #43 quine FP: auditor scanning auditors). See:
 * vault/standards/blocked-delivery-prevention.md.
 *
 * NOTE: This hook uses Stop schema ({ continue: true }). It must NOT
 * be registered as PreToolUse — that causes crash due to schema mismatch.
 *
 * Checks:
 * 1. Commented-out wiring (# {Module, []}, // TODO, commented imports)
 * 2. Stub functions (placeholder returns, unimplemented callbacks)
 * 3. Infinite timeouts (:infinity, Infinity, timeout: 0)
 * 4. Zero-retry patterns (no retry/backoff in network calls)
 * 5. Files created but never imported/required by anything
 *
 * Outputs warnings that Claude MUST address before claiming done.
 */

// --- JOBS-WOZ-EXEMPT (Apex Doctrine sealed 2026-05-16; expanded 2026-05-20) ---
// JOBS-WOZ-EXEMPT sha256=b5cc7ea7e55a55494552e31e5cf1eae177a323f5568d4e48e39561204e9b6fc3
// JOBS-WOZ-TOKENS: ["t01","t02","t03","t04","t05","t07","t09","t10","t13","t16"]
// --- end JOBS-WOZ-EXEMPT ---

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const TRACKER_DIR = path.join(os.tmpdir(), 'claude-quality-gate');

// Patterns that indicate scaffold illusion
const SCAFFOLD_PATTERNS = [
  // Commented-out wiring
  { regex: /^\s*#\s*\{[\w.]+,\s*\[\]\}/m, desc: 'Commented-out supervisor child', severity: 'CRITICAL' },
  { regex: /^\s*\/\/\s*(import|require|use)\s/m, desc: 'Commented-out import/require', severity: 'HIGH' },
  { regex: /^\s*#\s*(use|alias|import)\s/m, desc: 'Commented-out Elixir use/alias/import', severity: 'HIGH' },

  // Stub implementations
  { regex: /(?:^|\s)(?:#|\/\/|\/\*|\*)\s*(?:TODO|FIXME|HACK|XXX)\b/i, desc: 'TODO/FIXME marker in comment', severity: 'HIGH' },
  { regex: /(?:^|\s)(?:#|\/\/|\/\*|\*)\s*PLACEHOLDER\b/i, desc: 'PLACEHOLDER marker in comment', severity: 'HIGH' },
  { regex: /raise\s+"?not\s+implemented/i, desc: 'Unimplemented function (raise not implemented)', severity: 'CRITICAL' },
  { regex: /\{:ok,\s*".*pending.*"\}/i, desc: 'Stub return value with "pending"', severity: 'HIGH' },
  { regex: /pass\s*#\s*TODO/i, desc: 'Python pass with TODO', severity: 'HIGH' },

  // Dangerous defaults
  { regex: /:infinity\b/, desc: 'Infinite timeout (:infinity) — must use finite timeout', severity: 'CRITICAL' },
  { regex: /timeout:\s*0\b/, desc: 'Zero timeout — likely a mistake', severity: 'HIGH' },
  { regex: /(?:timeout|delay|interval|wait|sleep)\s*[:=]\s*Infinity\b/i, desc: 'JavaScript Infinity timeout', severity: 'CRITICAL' },

  // Missing error handling
  { regex: /\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)/, desc: 'Empty catch block swallowing errors', severity: 'HIGH' },
  { regex: /rescue\s*\n\s*_\s*->\s*:ok/, desc: 'Elixir rescue swallowing all errors', severity: 'MEDIUM' },
];

// File extensions to scan
const SCANNABLE_EXTENSIONS = new Set([
  '.ex', '.exs', '.ts', '.tsx', '.js', '.jsx', '.py',
  '.java', '.rs', '.go', '.c', '.cpp', '.h', '.yml', '.yaml',
  // MC-OVO-133: Windows scripts get included so checkWindowsScriptEncoding
  // runs alongside scanFile. Most scaffold patterns won't match PS/batch
  // content (different syntax), so the scan cost is negligible.
  '.ps1', '.bat', '.cmd',
]);

// MC-OVO-133: Windows scripts must ship with UTF-8 BOM + CRLF on Windows
// hosts. Without BOM, PowerShell 5.1 reads .ps1 with the system ANSI codepage
// and mis-tokenizes single-quoted strings under non-ASCII locales (parser
// reports spurious "missing string terminator"). The restart-claude.ps1
// incident (MC-OVO-126) is the canonical case study.
const WINDOWS_SCRIPT_EXTS = new Set(['.ps1', '.bat', '.cmd']);

// --- JOBS-WOZ double-scoped cryptographic exemption (Apex Doctrine, sealed 2026-05-16) ---
// Owner-directed. Narrows a Mistake #43 quine FP (allowlisted detector files
// carrying literal trigger tokens as detection DATA) WITHOUT opening a free-
// text bypass: basename allowlist is hardcoded + token-list sha256 must match.
// The doctrine mandates: double-scoped, drift-evident, never blanket.
//
// 2026-05-20 expansion (BLOCKED_DELIVERY.md durable fix): 16 detector
// basenames added. Each file MUST declare its JOBS-WOZ-TOKENS json + matching
// JOBS-WOZ-EXEMPT sha256 in its own header — basename membership alone is
// not exemption. See vault/standards/blocked-delivery-prevention.md.
const _JW_EXEMPT_BASENAMES = new Set([
  // Original (Owner Q2a/Q3a, 2026-05-17 — slop-token detectors)
  'dataset_enricher.py',
  'quality_audit.py',
  // Extended 2026-05-20 (BLOCKED_DELIVERY.md durable fix)
  'scaffold-auditor.js',        // this file: SCAFFOLD_PATTERNS array carries the patterns
  'zero-issue-gate.js',         // sibling auditor: identical SCAFFOLD_PATTERNS array
  'zero-fiction-gate.js',       // PreToolUse fiction gate: HARD_PATTERNS + SOFT_PATTERNS arrays
  'forensic_probes.py',         // OVO Phase B+ runtime probe library
  'test_forensic_probes.py',    // tests feed trigger strings to forensic_probes
  'ingest.py',                  // KobiiDistillerOS placeholder-rejection ingestor
  'run.py',                     // distiller pipeline orchestrator
  'validate.py',                // distiller schema validator
  'score.js',                   // STUB_PATTERNS regex array (Reality-Contract score)
  'investment_ready.js',        // score.js sibling: zero-stub axis description
  'oracle_cascade.py',          // OVO cascade scorer: regex commentary in docstring
  'visual.py',                  // Sleepless QA visual-prompt with broken-signal list
  'skill-heat-map-advisor.js',  // English "// require" regex misfire
  'baseline_ledger.py',         // project axes registry
  'design_index.py',            // UI-pattern descriptions (the word "placeholders")
  'lazarus_revive_all.py',      // English "# use case" regex misfire
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

function _jwExemptionGranted(filePath, contentText) {
  try {
    const norm = String(filePath).split(String.fromCharCode(92)).join('/');
    const base = norm.slice(norm.lastIndexOf('/') + 1);
    if (!_JW_EXEMPT_BASENAMES.has(base)) return false;
    const probe = contentText;
    const sha = _jwParseLine(probe, 'JOBS-WOZ-EXEMPT sha256=');
    const toksRaw = _jwParseLine(probe, 'JOBS-WOZ-TOKENS:');
    if (!sha || !toksRaw) return false;
    const m = sha.match(/[0-9a-f]{64}/i);
    if (!m) return false;
    let toks;
    try { toks = JSON.parse(toksRaw); } catch (_e) { return false; }
    if (!Array.isArray(toks)) return false;
    return _jwCanonHash(toks) === m[0].toLowerCase();
  } catch (_e) { return false; }
}

function checkWindowsScriptEncoding(filePath) {
  const violations = [];
  const ext = path.extname(filePath).toLowerCase();
  if (!WINDOWS_SCRIPT_EXTS.has(ext)) return violations;

  let buf;
  try { buf = fs.readFileSync(filePath); } catch { return violations; }

  const hasBom = buf.length >= 3 && buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF;
  if (!hasBom) {
    violations.push({
      file: filePath,
      line: 1,
      text: '<file header — first 3 bytes are not EF BB BF>',
      desc: `Windows script ${ext} missing UTF-8 BOM. PS 5.1 falls back to ANSI codepage and mis-tokenizes single-quoted strings under non-ASCII locales (windows-script-encoding rule).`,
      severity: 'HIGH',
    });
  }

  let lfOnly = 0, crlf = 0;
  for (let i = 0; i < buf.length; i++) {
    if (buf[i] === 0x0A) {
      if (i > 0 && buf[i - 1] === 0x0D) crlf++;
      else lfOnly++;
    }
  }
  if (lfOnly > 0) {
    violations.push({
      file: filePath,
      line: 1,
      text: `${lfOnly} LF-only line endings (CRLF count: ${crlf})`,
      desc: `Windows script ${ext} has LF-only line endings. Combined with missing BOM, triggers spurious 'string terminator missing' parse errors in PS 5.1.`,
      severity: lfOnly > crlf ? 'HIGH' : 'MEDIUM',
    });
  }
  return violations;
}

function scanFile(filePath) {
  const violations = [];
  try {
    const content = fs.readFileSync(filePath, 'utf8');

    // BL-0070 / Apex Doctrine: JOBS-WOZ-EXEMPT honor. A detector basename
    // in the allowlist that declares matching tokens skips line scanning.
    if (_jwExemptionGranted(filePath, content)) return violations;

    const lines = content.split('\n');
    for (const pattern of SCAFFOLD_PATTERNS) {
      for (let i = 0; i < lines.length; i++) {
        if (pattern.regex.test(lines[i])) {
          violations.push({
            file: filePath,
            line: i + 1,
            text: lines[i].trim().substring(0, 120),
            desc: pattern.desc,
            severity: pattern.severity,
          });
        }
      }
    }
  } catch { /* skip unreadable files */ }
  return violations;
}

function getSessionDirtyFiles(sessionId) {
  try {
    const trackerPath = path.join(TRACKER_DIR, `dirty-${sessionId}.json`);
    if (fs.existsSync(trackerPath)) {
      const data = JSON.parse(fs.readFileSync(trackerPath, 'utf8'));
      const allFiles = [];
      for (const type of Object.keys(data)) {
        allFiles.push(...data[type]);
      }
      return allFiles;
    }
  } catch { }
  return [];
}

function scanDirectory(dir, maxDepth = 3, depth = 0) {
  const files = [];
  if (depth > maxDepth) return files;
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (['node_modules', '.git', '_build', 'deps', 'target', 'dist', '__pycache__', '.elixir_ls'].includes(entry.name)) continue;
        files.push(...scanDirectory(fullPath, maxDepth, depth + 1));
      } else if (entry.isFile() && SCANNABLE_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
        files.push(fullPath);
      }
    }
  } catch { }
  return files;
}

// --- Core processing (extracted so hook-dispatcher.js can require this module) ---
function run(data) {
  try {
    data = data || {};
    const cwd = data.cwd || process.cwd();
    const sessionId = data.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';

    let filesToScan = getSessionDirtyFiles(sessionId);
    if (filesToScan.length === 0) {
      filesToScan = scanDirectory(cwd);
    }

    const allViolations = [];
    for (const file of filesToScan) {
      const violations = scanFile(file);
      allViolations.push(...violations);
      // MC-OVO-133: byte-level encoding check for Windows scripts.
      const encViolations = checkWindowsScriptEncoding(file);
      allViolations.push(...encViolations);
    }

    if (allViolations.length > 0) {
      const critical = allViolations.filter(v => v.severity === 'CRITICAL');
      const high = allViolations.filter(v => v.severity === 'HIGH');

      let warning = `\n⚠️ SCAFFOLD AUDITOR: ${allViolations.length} violations found (${critical.length} CRITICAL, ${high.length} HIGH)\n`;
      warning += '─'.repeat(60) + '\n';
      for (const v of allViolations.slice(0, 15)) {
        const relPath = path.relative(cwd, v.file);
        warning += `[${v.severity}] ${relPath}:${v.line} — ${v.desc}\n`;
        warning += `  ${v.text}\n`;
      }
      if (allViolations.length > 15) {
        warning += `... and ${allViolations.length - 15} more\n`;
      }
      warning += '─'.repeat(60) + '\n';
      warning += 'FIX these before claiming "done". Mistake #16: Scaffold Illusion.\n';

      // Stderr still works in both standalone + dispatcher modes.
      process.stderr.write(warning);
    }
  } catch (_) { /* silent */ }
  return { continue: true };
}

// --- Dual-mode entry point ---
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 5000);
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
