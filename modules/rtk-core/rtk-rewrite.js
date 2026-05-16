#!/usr/bin/env node
/*
 * rtk-rewrite.js — PreToolUse(Bash) command rewriter for Claude Power Pack.
 *
 * SHIP LOCATION: modules/rtk-core/rtk-rewrite.js (version-controlled).
 * ACTIVATION:    Owner copies this to ~/.claude/hooks/rtk-rewrite.js and
 *                registers the PreToolUse block (see INSTALL block at end),
 *                then /restart. The Power Pack auto-mode classifier denies
 *                a direct write into ~/.claude/hooks (self-persistence
 *                guard) — activation is an explicit Owner action by design.
 *
 * Node port of the upstream RTK delegator (hooks/claude/rtk-rewrite.sh).
 * Drops the jq + bash dependencies (Windows-friendly) and resolves the
 * binary by absolute path because ~/.claude/bin is NOT on PATH.
 *
 * Exit-code contract honored from `rtk rewrite <cmd>`:
 *   0  rewrite found, no permission rule  -> rewrite + auto-allow
 *   1  no RTK equivalent                  -> pass through unchanged
 *   2  deny rule matched                  -> pass through (native deny acts)
 *   3  ask rule matched                   -> rewrite, let Claude Code prompt
 *   *  binary absent / crash / timeout    -> pass through (fail-open)
 *
 * Fail-open is intentional: a compression proxy must never block a real
 * command. Any uncertainty resolves to "pass the original through".
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const RTK_BIN =
  process.env.RTK_BIN ||
  path.join(os.homedir(), '.claude', 'bin', 'rtk.exe');

const RTK_TIMEOUT_MS = 5000;

function passThrough() {
  process.exit(0);
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_e) {
    return '';
  }
}

function main() {
  const raw = readStdin();
  if (!raw || !raw.trim()) return passThrough();

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (_e) {
    return passThrough();
  }

  const toolInput =
    payload && typeof payload === 'object' ? payload.tool_input : null;
  const cmd =
    toolInput && typeof toolInput.command === 'string'
      ? toolInput.command
      : '';

  if (!cmd) return passThrough();
  if (!fs.existsSync(RTK_BIN)) return passThrough();

  let res;
  try {
    res = spawnSync(RTK_BIN, ['rewrite', cmd], {
      encoding: 'utf8',
      timeout: RTK_TIMEOUT_MS,
      shell: false,
      windowsHide: true,
    });
  } catch (_e) {
    return passThrough();
  }

  if (res.error || res.status === null) return passThrough();

  let rewritten = (res.stdout || '').replace(/\r?\n$/, '');

  // rtk emits a bare `rtk <args>` invocation. Bare `rtk` only resolves if
  // ~/.claude/bin is on PATH — it is NOT (verified). Anchor the emitted
  // command to the absolute binary so the rewrite runs in any shell,
  // including Claude Code's Bash context.
  if (/^rtk(\s|$)/.test(rewritten)) {
    rewritten = `"${RTK_BIN}"` + rewritten.slice(3);
  }

  switch (res.status) {
    case 0: {
      if (!rewritten || rewritten === cmd) return passThrough();
      const ti = Object.assign({}, toolInput, { command: rewritten });
      return emit({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow',
          permissionDecisionReason: 'RTK auto-rewrite',
          updatedInput: ti,
        },
      });
    }
    case 3: {
      if (!rewritten) return passThrough();
      const ti = Object.assign({}, toolInput, { command: rewritten });
      return emit({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          updatedInput: ti,
        },
      });
    }
    case 1:
    case 2:
    default:
      return passThrough();
  }
}

main();

/* ---------------------------------------------------------------------------
 * OWNER ACTIVATION (manual — auto-mode denies self-persistence by design)
 *
 * 1. Copy this file:
 *      cp "C:/Users/User/.claude/skills/claude-power-pack/modules/rtk-core/rtk-rewrite.js" \
 *         "C:/Users/User/.claude/hooks/rtk-rewrite.js"
 *
 * 2. Add to the PreToolUse array in ~/.claude/settings.json (after existing
 *    entries; mirrors the host's absolute-node-path convention):
 *
 *    {
 *      "matcher": "Bash",
 *      "hooks": [
 *        {
 *          "type": "command",
 *          "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/rtk-rewrite.js\"",
 *          "timeout": 10
 *        }
 *      ]
 *    }
 *
 * 3. /restart Claude Code. Verify: rtk gain   (after a few Bash calls)
 * ------------------------------------------------------------------------- */
