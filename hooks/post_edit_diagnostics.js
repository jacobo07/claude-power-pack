#!/usr/bin/env node
/**
 * post_edit_diagnostics.js -- PostToolUse (Write|Edit|MultiEdit): check the file
 * that was just edited and hand any diagnostics back to the model as
 * additionalContext in the same turn.
 *
 * Spec: vault/specs/post-edit-diagnostics.md. Never blocks; silent when clean;
 * every path that could not check writes an `unchecked` log line, so "could not
 * check" is never confused with "checked, clean".
 *
 * Kill switch: CLAUDE_POST_EDIT_DIAG=off.
 * Test seams: POST_EDIT_DIAG_LOG (log path), POST_EDIT_DIAG_RUFF (ruff binary).
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { readStdinRaw, armHardExit } = require('./hook-utils');

const STDIN_BUDGET_MS = 2000;
// 4 s, not 2.5: `node --check` measured 1.6 s on a RAM-starved host (681 MB free),
// and a timeout here only ever degrades to `unchecked`, never to a false `clean`.
const CHECK_TIMEOUT_MS = 4000;
const MAX_FILE_BYTES = 2 * 1024 * 1024;
const MAX_LISTED = 20;
const LOG_ROTATE_BYTES = 1024 * 1024;
const EDIT_TOOLS = new Set(['Write', 'Edit', 'MultiEdit']);
const RUFF_RULES = 'E9,F63,F7,F82';

const t0 = Date.now();
const HARD_EXIT = armHardExit(9000, () => log({ outcome: 'unchecked', reason: 'hard-exit 9s' }));

const LOG_PATH = process.env.POST_EDIT_DIAG_LOG ||
  path.join(os.homedir(), '.claude', 'state', 'post-edit-diagnostics.jsonl');

function log(entry) {
  try {
    fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
    try {
      if (fs.statSync(LOG_PATH).size > LOG_ROTATE_BYTES) {
        fs.renameSync(LOG_PATH, LOG_PATH + '.1');
      }
    } catch { /* no log yet */ }
    const line = Object.assign({ ts: new Date().toISOString() }, entry,
      { ms: Date.now() - t0 });
    fs.appendFileSync(LOG_PATH, JSON.stringify(line) + '\n');
  } catch { /* logging must never break the hook */ }
}

function finish(entry, context) {
  log(entry);
  clearTimeout(HARD_EXIT);
  if (context) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: context },
    }));
  }
  process.exit(0);
}

// Each checker returns {diags: [{row, col, code, message}]} or {unchecked: reason}.

function checkPython(file) {
  const ruff = process.env.POST_EDIT_DIAG_RUFF || 'ruff';
  const r = spawnSync(ruff, ['check', '--select', RUFF_RULES, '--output-format', 'json',
    '--no-cache', file], { encoding: 'utf8', timeout: CHECK_TIMEOUT_MS, windowsHide: true });
  if (r.error) return { unchecked: `ruff: ${r.error.code || r.error.message}` };
  // ruff: 0 = clean, 1 = findings, 2 = ruff itself failed.
  if (r.status !== 0 && r.status !== 1) {
    return { unchecked: `ruff exit ${r.status}: ${String(r.stderr || '').trim().slice(0, 200)}` };
  }
  let items;
  try { items = JSON.parse(r.stdout || '[]'); } catch {
    return { unchecked: 'ruff output not JSON' };
  }
  return {
    diags: items.map((d) => ({
      row: d.location && d.location.row, col: d.location && d.location.column,
      code: d.code || 'syntax', message: d.message,
    })),
  };
}

function checkJs(file) {
  const r = spawnSync(process.execPath, ['--check', file],
    { encoding: 'utf8', timeout: CHECK_TIMEOUT_MS, windowsHide: true });
  if (r.error) return { unchecked: `node --check: ${r.error.code || r.error.message}` };
  if (r.status === 0) return { diags: [] };
  const err = String(r.stderr || '');
  // First line is "<file>:<row>"; the SyntaxError line carries the message.
  const rowM = err.match(/:(\d+)\r?\n/);
  const msgM = err.match(/^(SyntaxError|ReferenceError|TypeError): ([^\r\n]*)/m);
  if (!msgM) return { unchecked: `node --check exit ${r.status} without a SyntaxError line` };
  return { diags: [{ row: rowM ? Number(rowM[1]) : null, col: null,
    code: msgM[1], message: msgM[2] }] };
}

function checkJson(file) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) {
    return { unchecked: `read: ${e.code || e.message}` };
  }
  const diags = [];
  if (text.charCodeAt(0) === 0xFEFF) {
    diags.push({ row: 1, col: 1, code: 'BOM',
      message: 'file starts with a UTF-8 BOM; JSON.parse and Python json (utf-8) reject it' });
    text = text.slice(1);
  }
  try { JSON.parse(text); } catch (e) {
    diags.push({ row: null, col: null, code: 'JSONParse', message: e.message });
  }
  return { diags };
}

const CHECKERS = {
  '.py': checkPython,
  '.js': checkJs, '.mjs': checkJs, '.cjs': checkJs,
  '.json': checkJson,
};

function render(file, diags) {
  const lines = diags.slice(0, MAX_LISTED).map((d) => {
    const at = d.row ? `L${d.row}${d.col ? ':' + d.col : ''} ` : '';
    return `  ${at}${d.code} ${d.message}`;
  });
  if (diags.length > MAX_LISTED) lines.push(`  ... and ${diags.length - MAX_LISTED} more`);
  return `[post-edit-diagnostics] ${file}: ${diags.length} issue(s) after this edit\n` +
    lines.join('\n');
}

(async function main() {
  if (String(process.env.CLAUDE_POST_EDIT_DIAG || '').toLowerCase() === 'off') {
    finish({ outcome: 'disabled' });
  }
  const { raw } = await readStdinRaw(STDIN_BUDGET_MS);
  let payload;
  // A leading BOM (PowerShell 5.1 prepends one when piping to a native exe) would
  // make JSON.parse throw and turn every call into `unchecked`.
  try { payload = JSON.parse(String(raw || '').replace(/^\uFEFF/, '')); } catch {
    finish({ outcome: 'unchecked', reason: raw === null ? 'stdin unreadable' : 'stdin not JSON' });
  }
  const tool = String(payload.tool_name || '');
  if (!EDIT_TOOLS.has(tool)) finish({ tool, outcome: 'skipped', reason: 'not an edit tool' });

  const file = String((payload.tool_input && payload.tool_input.file_path) || '');
  const ext = path.extname(file).toLowerCase();
  const checker = CHECKERS[ext];
  if (!file) finish({ tool, outcome: 'unchecked', reason: 'no file_path' });
  if (!checker) finish({ tool, ext, outcome: 'skipped', reason: 'no checker for extension' });

  let size;
  try { size = fs.statSync(file).size; } catch (e) {
    finish({ tool, ext, outcome: 'unchecked', reason: `stat: ${e.code || e.message}` });
  }
  if (size > MAX_FILE_BYTES) finish({ tool, ext, outcome: 'skipped', reason: 'size' });

  const res = checker(file);
  if (res.unchecked) finish({ tool, ext, outcome: 'unchecked', reason: res.unchecked });
  if (res.diags.length === 0) finish({ tool, ext, outcome: 'clean', count: 0 });
  finish({ tool, ext, outcome: 'findings', count: res.diags.length }, render(file, res.diags));
})().catch((e) => {
  finish({ outcome: 'unchecked', reason: `internal: ${e && e.message}` });
});
