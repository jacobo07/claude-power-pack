#!/usr/bin/env node
/**
 * prd-keyword-sentinel.js — UserPromptSubmit hook.
 *
 * When the submitted prompt carries a raw PRD (a `PRD:` header or a
 * `<prd>...</prd>` block), run the deterministic KARIMO parser and inject
 * the extracted `<prd-constraints rules="strict">` block into the model
 * context BEFORE the turn — so /ultra Phase 1 sees hard constraints up
 * front instead of re-deriving them.
 *
 * Output schema (canonical, post-2026-04-25): UserPromptSubmit supports
 *   { hookSpecificOutput: { hookEventName:'UserPromptSubmit',
 *                           additionalContext: '<string>' } }
 * (confirmed by the existing hook-dispatcher entry + BL-0040). Legacy
 * {decision:...} is rejected by the harness.
 *
 * Fail-open: any internal error exits 0 with empty stdout. A broken
 * sentinel must never brick prompt submission.
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const PARSER = path.join(
  os.homedir(), '.claude', 'skills', 'claude-power-pack',
  'modules', 'karimo-harness', 'prd_parser.py');

function pickPython() {
  const cands = [
    'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
    'python',
    'python3',
  ];
  for (const c of cands) {
    try {
      execFileSync(c, ['--version'], { stdio: 'ignore', windowsHide: true });
      return c;
    } catch (_e) { /* try next */ }
  }
  return 'python';
}

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); } catch (_e) { return ''; }
}

function extractPrd(prompt) {
  if (!prompt) return null;
  const block = prompt.match(/<prd>([\s\S]*?)<\/prd>/i);
  if (block && block[1].trim()) return block[1].trim();
  // `PRD:` header — take from that line to end of prompt.
  const m = prompt.match(/(^|\n)\s*PRD:\s*([\s\S]+)/i);
  if (m && m[2].trim().length > 40) return m[2].trim();
  return null;
}

function main() {
  let payload = {};
  try { payload = JSON.parse(readStdin() || '{}'); } catch (_e) { payload = {}; }
  const prompt = typeof payload.prompt === 'string' ? payload.prompt : '';

  const prd = extractPrd(prompt);
  if (!prd) { process.exit(0); }            // not a PRD prompt — silent pass

  if (!fs.existsSync(PARSER)) { process.exit(0); }  // parser absent — fail-open

  let block = '';
  try {
    block = execFileSync(pickPython(), [PARSER, '--emit-constraints'], {
      input: prd,
      encoding: 'utf8',
      timeout: 8000,
      maxBuffer: 1 << 20,
      windowsHide: true,
    }).trim();
  } catch (_e) {
    process.exit(0);                         // parser error — fail-open
  }
  if (!block || block.indexOf('<prd-constraints') === -1) { process.exit(0); }

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext:
        'KARIMO auto-ingested the PRD in this prompt. Treat the following '
        + 'as hard constraints for /ultra Phase 1 (do NOT re-derive):\n'
        + block,
    },
  }));
  process.exit(0);
}

try { main(); } catch (_e) { process.exit(0); }
