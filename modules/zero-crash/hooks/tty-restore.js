#!/usr/bin/env node
/**
 * TTY Restore — PostToolUse Hook
 *
 * After Bash tool invocations, disables DECSET 1004 focus reporting
 * to prevent ^[[I^[[O escape sequences from leaking into Claude Code's prompt.
 *
 * Only activates for Bash tool calls. Silent no-op for all other tools.
 *
 * Part of Claude Power Pack — Zero-Crash Environment module.
 */

let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);

  try {
    const data = JSON.parse(input);
    const toolName = data.tool_name || '';

    // Only restore TTY after Bash tool calls
    if (toolName !== 'Bash') {
      process.exit(0);
      return;
    }

    // Disable focus reporting (DECSET 1004) — prevents ^[[I^[[O leakage
    // This is safe: focus reporting is an optional terminal feature
    // that child processes may enable but fail to disable on exit
    process.stdout.write('\x1b[?1004l');

    // Optional: report TTY restoration event for telemetry
    const apiKey = process.env.ZERO_CRASH_API_KEY;
    if (apiKey) {
      const fs = require('fs');
      const path = require('path');
      const os = require('os');
      const tracesDir = path.join(os.homedir(), '.claude', 'traces');
      try {
        if (!fs.existsSync(tracesDir)) fs.mkdirSync(tracesDir, { recursive: true });
        const sessionId = data.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';
        const bufferPath = path.join(tracesDir, `zc_tty_${sessionId}.jsonl`);
        fs.appendFileSync(bufferPath, JSON.stringify({
          type: 'tty_restore',
          timestamp: new Date().toISOString(),
          platform: process.platform,
        }) + '\n');
      } catch { /* best effort */ }
    }

  } catch { /* parse error — exit silently */ }

  process.exit(0);
});
