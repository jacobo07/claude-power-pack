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
    // A DETECTOR THAT COULD NOT RUN HAS NOT CLEARED THE CONTENT.
    //
    // FAIL-CLOSED since 2026-09-15, by explicit Owner decision, reversing the
    // audible-fail-open that stood here. Both halves of that earlier reasoning
    // were right and it still had to go: making the absence AUDIBLE fixed the
    // "indistinguishable from a pass" half and left the security half untouched,
    // because a warning the model reads after the write has already happened is
    // a notification, not a gate.
    //
    // MEASURED 2026-09-15 -- same payload, same gate, twice:
    //   host at 844 MB free of 32 GB -> 8218 ms; the detector blew its 3000 ms
    //     budget, status !== 0, emitted {continue:true}, credential PASSED.
    //   host uncontended             ->  929 ms; detector 395 ms; DENIED on
    //     pattern anthropic_key.
    // Contention alone flipped a security verdict from deny to allow. That is
    // the whole argument: the thing deciding whether a credential may land was
    // host load, not content.
    //
    // WHAT FORCED THE REVERSAL -- the population, not the principle. The live
    // dispatcher log holds 15,574 timeout events, 256 of them THIS gate. So the
    // fail-open branch was not a rare degraded path, it was ordinary operation
    // 256 times over, and it fired TWICE inside the single session that made
    // this change, on that session's own edits.
    //
    // The old doctrine ("a detector failure must never block real work") is
    // preserved where it is actually true: this denies ONE tool call and tells
    // the agent what to do next. It never halts the agent -- see the
    // `continue:false` trap documented below, which is what "blocking real work"
    // originally meant and is still forbidden.
    //
    // The cost is real and accepted: on a starved host a legitimate write can be
    // refused. That is the correct direction to fail, and it is self-limiting --
    // the refusal names starvation, so the operator is pointed at the reaper and
    // at RAM rather than at a mystery.
    const why = (result.signal || result.error)
      ? 'detector timed out (host likely starved)'
      : `detector exited ${result.status}`;
    trace('fail-closed', { why, signal: result.signal });
    return emit({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: `HR-SECRET-001 could not be enforced on this `
          + `${toolName}: ${why}. The content was NOT scanned, so nothing cleared `
          + `it -- and an unenforced secret gate must not become permission. `
          + `This denies the TOOL only; the session is fine. If the host is `
          + `starved, run ~/.claude/hooks/orphan-dev-server-reaper.ps1 and retry. `
          + `Do NOT end the turn here: say what was denied and what you are doing `
          + `instead. A silent turn after a denial is a dead screen.`,
      },
    });
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
    // DENY THE TOOL, DO NOT HALT THE AGENT.
    //
    // This used to emit `{continue:false, stopReason}`. In the harness contract
    // `continue:false` halts the AGENT rather than denying the TOOL: the turn
    // ends at the tool boundary with no assistant text, and because the Stop
    // chain never runs, `closer-guard.js` -- whose whole job is to kill
    // text-less turns -- cannot see it. Measured 2026-09-04 on the sibling gate
    // `cascade_check_bash.js`, which carried the identical shape and produced
    // the cross-repo dead screen the Owner reports. See that file's header for
    // the one-session natural experiment that isolates the output shape as the
    // cause.
    //
    // Enforcement is UNCHANGED: `permissionDecision:'deny'` still blocks the
    // tool, and it is the same shape hook-dispatcher.js already synthesises for
    // exit-2 PreToolUse gates. What changes is that the model receives the
    // reason and can respond, instead of the session going dark.
    return emit({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: 'HR-SECRET-001 -- Secret Firewall denied '
          + toolName
          + '. Detected CRITICAL secret pattern(s): '
          + (info.patterns || []).join(', ')
          + '. Rotate the secret before retrying. Detector never logs raw values.'
          + ' Do NOT end the turn here: say what was denied and what you are '
          + 'doing instead. A silent turn after a denial is a dead screen.',
      },
    });
  }

  return emit({ continue: true });
})();
