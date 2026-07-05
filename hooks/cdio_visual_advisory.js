#!/usr/bin/env node
/**
 * cdio_visual_advisory.js — CDIO Integration I4 (advisory level-2, never blocks).
 *
 * Fires on PreToolUse for a Write/Edit whose target is a visual surface (a
 * frontend file extension, or a filename naming a landing/dashboard/component/
 * hero/onboarding/pricing surface). Its ONLY action is to SURFACE a reminder:
 * this output is a visual experience; before declaring it done, run the
 * cdio-reviewer agent — the PP completion standard for visual output requires a
 * Design Quality Score >= 80 and zero critical issues (PR-CDIO-REVIEW-GATE-001).
 *
 * Honest contract (mirrors graph_first_gate GK-12 level-2):
 *   - Advisory only. NEVER denies, NEVER blocks, NEVER exits 2. No in-process
 *     hook can force an agent to run a review; it makes the gate visible.
 *   - Fail-open ABSOLUTE: any error / unparseable input -> `{}` and exit 0.
 *   - Throttled: at most one reminder per (session, surface-family) per cooldown,
 *     so it nudges once per surface, not on every edit (token discipline).
 *
 * Dual-mode: exports { run } for the dispatcher EVENT_MAP + unit tests, and runs
 * as a standalone stdin->stdout CLI child when invoked directly (the shell-free
 * CHAIN_MAP path the dispatcher uses on Windows).
 *
 * OWNER-SIDE WIRING (HR-001: the classifier blocks auto-editing settings.json):
 *   1. Copy this file to the live hooks dir:
 *        Copy-Item hooks/cdio_visual_advisory.js "$env:USERPROFILE\.claude\hooks\"
 *   2. Register it as a PreToolUse hook (matcher: "Write|Edit") in
 *      ~/.claude/settings.json, or add it to the PP hook-dispatcher EVENT_MAP.
 *   3. /restart to load (hooks cold-load).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const STATE_DIR = path.join(os.homedir(), '.claude', 'state', 'cdio');
const THROTTLE_MS = 15 * 60 * 1000; // one reminder per surface-family per 15 min

// Frontend surface file extensions — a Write/Edit to one is a visual output.
const SURFACE_EXT = new Set([
  '.tsx', '.jsx', '.vue', '.svelte', '.html', '.htm', '.css', '.scss', '.sass',
]);

// Filename keywords that name a visual surface even without a surface extension
// (e.g. a markdown landing spec, a python view). Kept tight to limit noise.
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

// Best-effort per-(session, surface-family) throttle. A miss returns false =
// "remind now" and stamps the marker. Any fs error fails OPEN toward reminding
// once; it must never throw.
function throttled(sessionId, familyKey) {
  try {
    const safe = String(sessionId || 'nosess').replace(/[^a-zA-Z0-9]+/g, '') || 'nosess';
    const fk = String(familyKey || 'nofam').replace(/[^a-zA-Z0-9]+/g, '').slice(0, 32) || 'nofam';
    const marker = path.join(STATE_DIR, `.cdio_${safe}_${fk}`);
    try {
      const st = fs.statSync(marker);
      if (Date.now() - st.mtimeMs < THROTTLE_MS) return true;
    } catch (_) { /* no marker yet — fall through to stamp + remind */ }
    try {
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(marker, '');
    } catch (_) { /* marker write best-effort; a miss just re-nudges later */ }
    return false;
  } catch (_) {
    return false;
  }
}

function buildAdvisory(p) {
  const name = path.basename(String(p || '')) || 'this surface';
  return `CDIO advisory (I4, never blocks): \`${name}\` is a visual surface. `
    + `Before declaring it done, run the cdio-reviewer agent — the PP completion `
    + `standard for visual output (PR-CDIO-REVIEW-GATE-001) requires a Design `
    + `Quality Score >= 80 AND zero critical issues. The review is deterministic `
    + `(modules.cdio.scorer) and grounded in the CDIO datasets — every finding `
    + `carries a criterion and an observed value, not an opinion.`;
}

/**
 * run(input) — the hook body. `input` is the parsed PreToolUse JSON. Returns the
 * JSON object the dispatcher merges. ALWAYS returns an object; NEVER throws.
 */
function run(input) {
  try {
    const data = input && typeof input === 'object' ? input : {};
    const toolName = data.tool_name || data.toolName || '';
    const toolInput = data.tool_input || data.toolInput || {};
    const sessionId = data.session_id || data.sessionId || '';

    if (!isVisualSurface(toolName, toolInput)) return {};

    const p = targetPath(toolInput);
    // Family key = directory + extension, so repeated edits to the same surface
    // area nudge once, not per file.
    const familyKey = path.dirname(p) + path.extname(p);
    if (throttled(sessionId, familyKey)) return {};

    return {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: buildAdvisory(p),
      },
    };
  } catch (_) {
    return {}; // fail-open absolute — an advisory must never break the tool
  }
}

module.exports = { run, isVisualSurface, targetPath, buildAdvisory };

// --- Standalone CLI (shell-free CHAIN_MAP child) --------------------------
if (require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => { raw += c; });
  process.stdin.on('end', () => {
    let data = {};
    // Strip a leading UTF-8 BOM: PowerShell 5.1 prepends one when piping to a
    // native exe, which would otherwise make JSON.parse throw (silent no-op).
    if (raw && raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
    try { data = JSON.parse(raw || '{}'); } catch (_) { data = {}; }
    let out = {};
    try { out = run(data) || {}; } catch (_) { out = {}; }
    try { process.stdout.write(JSON.stringify(out)); } catch (_) { process.stdout.write('{}'); }
    process.exit(0); // NEVER exit 2 — CDIO I4 never blocks
  });
  process.stdin.on('error', () => { process.stdout.write('{}'); process.exit(0); });
}
