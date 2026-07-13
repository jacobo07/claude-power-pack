#!/usr/bin/env node
/**
 * cdio_visual_advisory.js — CDIO Integration I4.
 *
 * Fires on PreToolUse for a Write/Edit whose target is a visual surface (a frontend
 * file extension, or a filename naming a landing/dashboard/component/hero/onboarding/
 * pricing surface).
 *
 * Was: an advisory that REMINDED the agent to run a review. That made the anti-slop
 * standard depend on the agent remembering to invoke it — a gate you must remember to
 * call is not a gate (T-DESIGN-SLOP-001). Now it RUNS the gate.
 *
 * Two-tier contract, and the tiering is the whole design:
 *
 *   1. Project HAS a DESIGN.md  -> it has adopted the design system, so slop against
 *      its own declared system is refusable. Run tools/design_gate.py; on BLOCK,
 *      DENY the write with the concrete criticals (criterion + observed value).
 *   2. Project has NO DESIGN.md -> it never adopted the system. ADVISE (never deny).
 *      Forcing a design system onto a repo that never opted in would block legitimate
 *      work, and a gate whose false-positive blocks real work gets disabled, which is
 *      how you end up with no gate at all.
 *
 * The escape hatch exists by construction: DESIGN.md is not a visual-surface path, so
 * editing it is never blocked. A denied write is always fixable by fixing the system
 * it violates.
 *
 * Fail-open ABSOLUTELY: no python, spawn error, timeout, unparseable output, any throw
 * -> `{}` and exit 0. A broken gate must never be the reason good work stops. The only
 * thing it may ever stop is a surface that demonstrably violates its own DESIGN.md.
 *
 * A BLOCK is never throttled. The 15-minute throttle applies only to the advisory
 * nudge: a refusal that fires once and then goes quiet for 15 minutes is not a refusal.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const STATE_DIR = path.join(os.homedir(), '.claude', 'state', 'cdio');
const THROTTLE_MS = 15 * 60 * 1000;   // advisory nudge only — never a BLOCK
const GATE_TIMEOUT_MS = 6000;

// PP root = two levels up from hooks/ (…/claude-power-pack/hooks/this.js)
const PP_ROOT = path.resolve(__dirname, '..');
const GATE_SCRIPT = path.join(PP_ROOT, 'tools', 'design_gate.py');

const SURFACE_EXT = new Set([
  '.tsx', '.jsx', '.vue', '.svelte', '.html', '.htm', '.css', '.scss', '.sass',
]);
const SURFACE_NAME = /(landing|dashboard|onboarding|pricing|navbar|sidebar|hero|checkout|homepage|\bpage\b|layout|component)/i;
const WRITE_TOOLS = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit']);

function targetPath(toolInput) {
  if (!toolInput || typeof toolInput !== 'object') return '';
  return String(toolInput.file_path || toolInput.filePath || toolInput.path || '');
}

function isVisualSurface(toolName, toolInput) {
  if (!WRITE_TOOLS.has(toolName)) return false;
  const p = targetPath(toolInput);
  if (!p) return false;
  const ext = path.extname(p).toLowerCase();
  if (SURFACE_EXT.has(ext)) return true;
  return SURFACE_NAME.test(path.basename(p));
}

/**
 * Walk up from the surface toward the filesystem root looking for a DESIGN.md.
 * Stops at a .git directory (the project boundary) so a surface in project A can
 * never be judged against project B's design system. Returns '' when none is found.
 */
function findDesignMd(surfacePath) {
  try {
    let dir = path.dirname(path.resolve(surfacePath));
    for (let i = 0; i < 32; i += 1) {
      const candidate = path.join(dir, 'DESIGN.md');
      if (fs.existsSync(candidate)) return candidate;
      if (fs.existsSync(path.join(dir, '.git'))) return '';   // project boundary
      const parent = path.dirname(dir);
      if (parent === dir) return '';                          // filesystem root
      dir = parent;
    }
  } catch (_) { /* fall through to '' — fail-open */ }
  return '';
}

/** Resolve a python interpreter. Explicit override wins; then the common Windows
 *  install path; then PATH. Returns '' if none is usable (-> fail-open, no gate). */
function pythonExe() {
  const override = process.env.PP_PYTHON;
  if (override && fs.existsSync(override)) return override;
  const win = path.join(os.homedir(), 'AppData', 'Local', 'Programs',
                        'Python', 'Python312', 'python.exe');
  if (fs.existsSync(win)) return win;
  return process.platform === 'win32' ? 'python' : 'python3';
}

/** Run tools/design_gate.py against a DESIGN.md. Returns the parsed verdict, or null
 *  on ANY failure (missing script, no python, timeout, bad JSON) -> fail-open. */
function runGate(designMd) {
  try {
    if (!fs.existsSync(GATE_SCRIPT)) return null;
    const res = spawnSync(pythonExe(), [GATE_SCRIPT, designMd, '--json'], {
      encoding: 'utf8',
      timeout: GATE_TIMEOUT_MS,
      windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
    });
    if (!res || res.error || typeof res.stdout !== 'string') return null;
    let raw = res.stdout;
    if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
    const out = JSON.parse(raw);
    return out && typeof out.verdict === 'string' ? out : null;
  } catch (_) {
    return null;
  }
}

function throttled(sessionId, familyKey) {
  try {
    const safe = String(sessionId || 'nosess').replace(/[^a-zA-Z0-9]+/g, '') || 'nosess';
    const fk = String(familyKey || 'nofam').replace(/[^a-zA-Z0-9]+/g, '').slice(0, 32) || 'nofam';
    const marker = path.join(STATE_DIR, `.cdio_${safe}_${fk}`);
    try {
      const st = fs.statSync(marker);
      if (Date.now() - st.mtimeMs < THROTTLE_MS) return true;
    } catch (_) { /* no marker — remind now */ }
    try {
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(marker, '');
    } catch (_) { /* best-effort */ }
    return false;
  } catch (_) {
    return false;
  }
}

function denyReason(surface, out) {
  const crits = (out.critical || [])
    .map(f => `  - ${f.criterion}: ${f.observed}\n    -> ${f.recommendation || ''}`.trimEnd())
    .join('\n');
  return `CDIO design gate: BLOCK (score ${out.score}). \`${path.basename(surface)}\` is a `
    + `visual surface in a project whose DESIGN.md violates the anti-slop standard `
    + `(T-DESIGN-SLOP-001).\n\nDESIGN.md: ${out.design_md}\n\nCritical:\n${crits}\n\n`
    + `Fix the design system, then retry the write. Editing DESIGN.md is never blocked. `
    + `Verify with: python tools/design_gate.py "${out.design_md}"`;
}

function adviseNoSystem(surface) {
  return `CDIO advisory: \`${path.basename(surface)}\` is a visual surface, and this `
    + `project has no DESIGN.md — so no aesthetic family is declared and the anti-slop `
    + `gate cannot evaluate it. Create one from modules/design-md/DESIGN.md.template `
    + `(run the CDIO-06 three-question picker first). Not blocking: a project that never `
    + `adopted the design system is not in violation of it.`;
}

function adviseReview(surface, out) {
  return `CDIO design gate: ${out.verdict} (score ${out.score}) on ${out.design_md}. `
    + `\`${path.basename(surface)}\` is a visual surface — the DESIGN.md clears the `
    + `anti-slop floor, which is necessary but NOT sufficient. Before declaring it done, `
    + `run cdio-reviewer against the RENDERED surface: PR-CDIO-REVIEW-GATE-001 requires a `
    + `Design Quality Score >= 80 and zero critical issues. This gate read the declared `
    + `tokens; it cannot see what you actually rendered.`;
}

/**
 * run(input) — the hook body. ALWAYS returns an object; NEVER throws.
 */
function run(input) {
  try {
    const data = input && typeof input === 'object' ? input : {};
    const toolName = data.tool_name || data.toolName || '';
    const toolInput = data.tool_input || data.toolInput || {};
    const sessionId = data.session_id || data.sessionId || '';

    if (!isVisualSurface(toolName, toolInput)) return {};
    const surface = targetPath(toolInput);

    const designMd = findDesignMd(surface);

    // Tier 2 — no DESIGN.md: the project never adopted the system. Advise, throttled.
    if (!designMd) {
      const familyKey = path.dirname(surface) + ':nosystem';
      if (throttled(sessionId, familyKey)) return {};
      return {
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          additionalContext: adviseNoSystem(surface),
        },
      };
    }

    // Tier 1 — the project HAS a DESIGN.md: run the real gate.
    const out = runGate(designMd);
    if (!out) return {};                       // fail-open: no python / broken gate

    if (out.verdict === 'BLOCK') {
      // NEVER throttled. A refusal that goes quiet for 15 minutes is not a refusal.
      return {
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: denyReason(surface, out),
        },
      };
    }

    // APPROVE / REVISE / SKIP -> surface the verdict, throttled per surface family.
    const familyKey = path.dirname(surface) + path.extname(surface);
    if (throttled(sessionId, familyKey)) return {};
    return {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: adviseReview(surface, out),
      },
    };
  } catch (_) {
    return {};   // fail-open absolute
  }
}

module.exports = { run, isVisualSurface, targetPath, findDesignMd, runGate };

// --- Standalone CLI (shell-free CHAIN_MAP child) --------------------------
if (require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => { raw += c; });
  process.stdin.on('end', () => {
    let data = {};
    if (raw && raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
    try { data = JSON.parse(raw || '{}'); } catch (_) { data = {}; }
    let out = {};
    try { out = run(data) || {}; } catch (_) { out = {}; }
    try { process.stdout.write(JSON.stringify(out)); } catch (_) { process.stdout.write('{}'); }
    process.exit(0);   // the DENY rides in the JSON, never in the exit code
  });
  process.stdin.on('error', () => { process.stdout.write('{}'); process.exit(0); });
}
