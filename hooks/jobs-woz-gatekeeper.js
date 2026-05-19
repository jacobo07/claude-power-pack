#!/usr/bin/env node
/**
 * jobs-woz-gatekeeper.js — PreToolUse Write|Edit enforcement.
 *
 * The wire between the Claude Write/Edit tool and the Jobs & Woz quality
 * checker. Scans the NEW content about to be written; if quality_audit.py
 * exits 5 (slop), the Write/Edit is denied with the persona veto reason.
 *
 * Decision schema (canonical, post 2026-04-25 migration — legacy
 * {decision:...} is rejected by the harness):
 *   deny  -> stdout JSON hookSpecificOutput.permissionDecision='deny', exit 0
 *   pass  -> exit 0, empty stdout
 *
 * Recursion-safe: the temp file is written with Node fs (NOT the Claude
 * tool), so this hook never re-triggers itself. quality_audit.py owns the
 * skip-set for governance/meta files (audit gaps #2/#3).
 *
 * Fail-open: any internal error in the gate must NOT brick the session —
 * a buggy guard that hard-blocks every write is worse than a missed veto.
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const AUDIT = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack\\tools\\quality_audit.py';

// --- JOBS-WOZ double-scoped cryptographic exemption (Owner Q2a/Q3a) ---
const _JW_EXEMPT_BASENAMES = new Set(['dataset_enricher.py', 'quality_audit.py']);
function _jwCanonHash(tokens) {
  const u = [...new Set(tokens.map(String))];
  u.sort((a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8')));
  return require('crypto').createHash('sha256').update(u.join(String.fromCharCode(10)), 'utf8').digest('hex');
}
function _jwParseLine(probe, marker) {
  const i = probe.indexOf(marker);
  if (i < 0) return null;
  let j = probe.indexOf(String.fromCharCode(10), i);
  if (j < 0) j = probe.length;
  return probe.slice(i + marker.length, j).trim();
}
function _jwExemptionGranted(realPath, toolName, contentText) {
  try {
    const norm = String(realPath).split(String.fromCharCode(92)).join('/');
    const base = norm.slice(norm.lastIndexOf('/') + 1);
    if (!_JW_EXEMPT_BASENAMES.has(base)) return false;
    let probe = contentText;
    if (toolName === 'Edit' || toolName === 'MultiEdit') {
      try { probe = require('fs').readFileSync(realPath, 'utf8'); } catch (_e) { probe = contentText; }
    }
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

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
}

function newContent(toolName, ti) {
  // Edit has NO `content` field (audit gap #1) — scan the added text.
  if (toolName === 'Write') return typeof ti.content === 'string' ? ti.content : '';
  if (toolName === 'Edit') return typeof ti.new_string === 'string' ? ti.new_string : '';
  if (toolName === 'MultiEdit' && Array.isArray(ti.edits)) {
    return ti.edits.map((e) => (e && e.new_string) || '').join('\n');
  }
  return '';
}

function emitDeny(reason) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    },
  }));
  process.exit(0);
}

function pass() { process.exit(0); }

(function main() {
  let payload;
  try {
    payload = JSON.parse(readStdin() || '{}');
  } catch (_e) {
    pass(); // unparseable stdin -> fail-open
  }
  const toolName = payload.tool_name || '';
  const ti = payload.tool_input || {};
  const realPath = String(ti.file_path || '').replace(/\\/g, '/');
  if (!realPath) pass();

  const content = newContent(toolName, ti);
  if (!content.trim()) pass(); // nothing meaningful to judge

  if (_jwExemptionGranted(realPath, toolName, content)) pass();

  // Temp copy preserves the real extension so quality_audit routes the
  // JOBS (UI) vs WOZ (code) lens correctly.
  const ext = path.extname(realPath) || '.txt';
  const tmp = path.join(os.tmpdir(), `jwg_${process.pid}_${Date.now()}${ext}`);
  try {
    fs.writeFileSync(tmp, content, 'utf8');
  } catch (_e) {
    pass(); // can't stage -> fail-open
  }

  let out = '';
  let code = 0;
  try {
    out = execFileSync(PY, [AUDIT, tmp, realPath], {
      encoding: 'utf8',
      timeout: 15000,
      windowsHide: true,
    });
  } catch (e) {
    if (e && typeof e.status === 'number') {
      code = e.status;
      out = (e.stdout || '').toString();
    } else {
      // python missing / timeout / spawn failure -> fail-open
      try { fs.unlinkSync(tmp); } catch (_x) { /* best effort */ }
      pass();
    }
  }
  try { fs.unlinkSync(tmp); } catch (_x) { /* best effort */ }

  if (code === 5) {
    const m = out.match(/VERDICT: VETO\s+\[([^\]]+)\][\s\S]*?THE ONE THING\s*\n\s*(.+)/);
    const who = m ? m[1] : 'STEVE JOBS / WOZNIAK';
    const why = m ? m[2].trim() : 'Slop detected in delivered surface.';
    emitDeny(`${who} VETO — ${path.basename(realPath)}: ${why} `
      + `Iterate (Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-visual.txt) `
      + `until VERDICT: SHIP. Recorded in global_vetoes.md.`);
  }
  pass();
})();
