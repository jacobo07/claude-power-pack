#!/usr/bin/env node
/**
 * uqf_pre_edit_gate.js -- PreToolUse advisory for Write|Edit|MultiEdit
 * on .py files. Calls the PP code_quality signal evaluator with the
 * new content; if hits found, emits a pp-code-reviewer advisory via
 * hookSpecificOutput.additionalContext. NEVER blocks (advisory-only).
 *
 * Cooperates with the existing PreToolUse jobs-woz-gatekeeper.js: that
 * hook DENIES on quality_audit slop verdict; this hook only ADVISES on
 * AST anti-patterns from the UQF detectors. Both can fire on the same
 * Write -- they answer different questions.
 *
 * Fail-open by construction: any internal error -> exit 0 silent.
 *
 * Sealed BL-HOOKS-REG-001 (2026-05-29).
 */
'use strict';
const fs = require('fs');
const { execFileSync } = require('child_process');

const PY = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
const PP_PATH = 'C:\\Users\\User\\.claude\\skills\\claude-power-pack';

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
}

function newContent(toolName, ti) {
  if (toolName === 'Write') {
    return typeof ti.content === 'string' ? ti.content : '';
  }
  if (toolName === 'Edit') {
    return typeof ti.new_string === 'string' ? ti.new_string : '';
  }
  if (toolName === 'MultiEdit' && Array.isArray(ti.edits)) {
    return ti.edits.map((e) => (e && e.new_string) || '').join('\n');
  }
  return '';
}

function emitPass() {
  process.exit(0);
}

function emitAdvisory(text) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: text,
    },
  }));
  process.exit(0);
}

(function main() {
  let payload;
  try {
    payload = JSON.parse(readStdin() || '{}');
  } catch (_e) {
    emitPass();
  }
  const toolName = payload.tool_name || '';
  const ti = payload.tool_input || {};
  const realPath = String(ti.file_path || ti.path || '');
  if (!realPath || !realPath.toLowerCase().endsWith('.py')) {
    emitPass();
  }
  const content = newContent(toolName, ti);
  if (!content || content.length < 50) emitPass();

  let advisory = '';
  try {
    const code = JSON.stringify(content);
    const script =
      `import sys; sys.path.insert(0, r'${PP_PATH}');\n` +
      'from modules.pp_agents.signals.code_quality import evaluate;\n' +
      'from modules.pp_agents.proactive_core import (\n' +
      '    format_advisory, is_throttled, mark_fired);\n' +
      `code = ${code};\n` +
      "if is_throttled('pp-code-reviewer','pre-edit',15):\n" +
      "    print('')\n" +
      'else:\n' +
      "    sig = evaluate(code, 'pre-edit')\n" +
      '    if sig is None:\n' +
      "        print('')\n" +
      '    else:\n' +
      '        line = format_advisory(sig)\n' +
      "        mark_fired('pp-code-reviewer','pre-edit', line)\n" +
      '        print(line)';
    const out = execFileSync(PY, ['-c', script], {
      encoding: 'utf8', timeout: 5000, windowsHide: true,
    });
    advisory = (out || '').trim();
  } catch (_e) {
    advisory = '';
  }
  if (!advisory) emitPass();
  emitAdvisory(advisory);
})();
