#!/usr/bin/env node
// PreToolUse Secret Firewall gate -- HR-SECRET-001.
// Blocks Write/Edit/MultiEdit when content contains a CRITICAL secret.
// Fail-open on internal error: a gate must never block real work due
// to detector failure (per HR-SECRET doctrine).
'use strict';

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const PP_ROOT = path.resolve(__dirname, '..');
const PY = process.env.PYTHON_BIN
  || (process.platform === 'win32'
    ? 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
    : 'python3');
const DETECTOR_TIMEOUT_MS = 3000;
const RELEVANT_TOOLS = new Set(['Write', 'Edit', 'MultiEdit']);

const PY_SCRIPT = `import json, os, sys
sys.path.insert(0, os.environ['PP_ROOT'])
from modules.secret_firewall.detector import scan_text, Severity
text = sys.stdin.read()
hits = scan_text(text)
crit = [h for h in hits if h.severity == Severity.CRITICAL]
print(json.dumps({
    "critical_count": len(crit),
    "patterns": sorted({h.pattern_name for h in crit}),
}))
`;

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

function extractContent(toolInput) {
  if (!toolInput || typeof toolInput !== 'object') return '';
  const parts = [];
  if (typeof toolInput.content === 'string') parts.push(toolInput.content);
  if (typeof toolInput.new_string === 'string') parts.push(toolInput.new_string);
  if (Array.isArray(toolInput.edits)) {
    for (const e of toolInput.edits) {
      if (e && typeof e.new_string === 'string') parts.push(e.new_string);
    }
  }
  return parts.join('\n');
}

const DEBUG = !!process.env.SF_HOOK_DEBUG;
const trace = (label, obj) => {
  if (DEBUG) process.stderr.write(`[sf-hook] ${label}: ${JSON.stringify(obj)}\n`);
};

(async () => {
  let payload = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) payload += chunk;
  } catch (e) {
    trace('stdin-error', { message: e?.message });
    return emit({ continue: true });
  }
  // PowerShell 5.1 on Windows pipes strings to native exes with a UTF-8
  // BOM (﻿). JSON.parse rejects it. Strip a leading BOM defensively
  // (sibling lesson to memory/feedback_python_utf8_bom.md).
  if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1);
  trace('payload', { len: payload.length, head: payload.slice(0, 80) });

  let req;
  try {
    req = JSON.parse(payload);
  } catch (e) {
    trace('json-parse-error', { message: e?.message, head: payload.slice(0, 80) });
    return emit({ continue: true });
  }

  const toolName = req.tool_name || '';
  trace('tool', { toolName, relevant: RELEVANT_TOOLS.has(toolName) });
  if (!RELEVANT_TOOLS.has(toolName)) return emit({ continue: true });

  const content = extractContent(req.tool_input);
  trace('content', { len: content.length, head: content.slice(0, 80) });
  if (!content) return emit({ continue: true });

  let result;
  try {
    result = spawnSync(PY, ['-c', PY_SCRIPT], {
      input: content,
      env: { ...process.env, PP_ROOT },
      encoding: 'utf8',
      timeout: DETECTOR_TIMEOUT_MS,
      windowsHide: true,
    });
  } catch {
    return emit({ continue: true });
  }

  trace('subprocess', {
    status: result.status,
    signal: result.signal,
    stdout_len: (result.stdout || '').length,
    stderr_head: (result.stderr || '').slice(0, 200),
  });
  if (result.status !== 0 || !result.stdout) {
    return emit({ continue: true });
  }

  let info;
  try {
    info = JSON.parse(result.stdout.trim().split('\n').pop());
  } catch (e) {
    trace('info-parse-error', { message: e?.message, stdout: result.stdout.slice(0, 200) });
    return emit({ continue: true });
  }
  trace('info', info);

  if ((info.critical_count || 0) > 0) {
    return emit({
      continue: false,
      stopReason: 'HR-SECRET-001 -- Secret Firewall blocked '
        + toolName
        + '. Detected CRITICAL secret pattern(s): '
        + (info.patterns || []).join(', ')
        + '. Rotate the secret before retrying. Detector never logs raw values.',
    });
  }

  return emit({ continue: true });
})();
