#!/usr/bin/env node
/**
 * Process Sandbox Advisor — PreToolUse Hook
 *
 * Intercepts Bash tool calls containing risky binaries (emulators, servers,
 * display managers) that could corrupt Claude Code's TTY if run without
 * I/O redirection.
 *
 * ADVISORY ONLY — never blocks. Injects a warning into the conversation
 * suggesting the use of the zero-crash-sandbox wrapper.
 *
 * Part of Claude Power Pack — Zero-Crash Environment module.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

// Platform-aware log path: respects %TEMP% on Windows, /tmp on POSIX.
const ZERO_CRASH_LOG = path.join(os.tmpdir(), 'zero-crash', 'output.log');
// Redirect suffix is platform-aware too: cmd/pwsh use different syntax than bash,
// but the advisory text targets bash (pipeline form), so keep POSIX redirects when
// bash is the assumed shell, but present the target log path correctly.
const REDIRECT_SUFFIX = process.platform === 'win32'
  ? `> "${ZERO_CRASH_LOG}" 2>&1`
  : `> "${ZERO_CRASH_LOG}" 2>&1 < /dev/null &`;

// Load risky binaries from config or use defaults
let RISKY_BINARIES = ['Xvfb', 'dolphin', 'emulator', 'ffmpeg', 'gunicorn', 'uvicorn'];
try {
  const configPath = path.join(__dirname, '..', 'config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  if (config.process_sandbox?.risky_binaries) {
    RISKY_BINARIES = config.process_sandbox.risky_binaries;
  }
} catch { /* use defaults */ }

// Patterns indicating I/O is already redirected (safe)
const REDIRECT_PATTERNS = [
  />\s*\/dev\/null/,          // > /dev/null
  />\s*[^\s]+\.log/,          // > file.log
  /2>&1/,                     // stderr to stdout (usually with redirect)
  /< \/dev\/null/,            // stdin from /dev/null
  /\bnohup\b/,                // nohup wrapper
  /\bsetsid\b/,               // setsid wrapper
  /\bzero-crash-sandbox\b/,   // already using our wrapper
  /\| tee\b/,                 // piped to tee (logged)
];

let input = '';
const stdinTimeout = setTimeout(() => {
  console.log(JSON.stringify({ decision: 'allow' }));
  process.exit(0);
}, 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);

  try {
    const data = JSON.parse(input);
    const toolName = data.tool_name || '';

    // Only check Bash tool calls
    if (toolName !== 'Bash') {
      console.log(JSON.stringify({ decision: 'allow' }));
      return;
    }

    const command = data.tool_input?.command || '';
    if (!command) {
      console.log(JSON.stringify({ decision: 'allow' }));
      return;
    }

    // Check if command contains a risky binary
    const commandLower = command.toLowerCase();
    const matchedBinary = RISKY_BINARIES.find(bin => commandLower.includes(bin.toLowerCase()));

    if (!matchedBinary) {
      console.log(JSON.stringify({ decision: 'allow' }));
      return;
    }

    // Check if I/O is already redirected
    const isRedirected = REDIRECT_PATTERNS.some(pattern => pattern.test(command));

    if (isRedirected) {
      console.log(JSON.stringify({ decision: 'allow' }));
      return;
    }

    // Advisory warning: risky binary without redirection
    const warning = [
      `[Zero-Crash] WARNING: "${matchedBinary}" detected without I/O redirection.`,
      'This may corrupt the terminal (TTY). Consider using the sandbox wrapper:',
      `  zero-crash-sandbox ${command}`,
      'Or add I/O redirection manually:',
      `  ${command} ${REDIRECT_SUFFIX}`,
    ].join('\n');

    console.log(JSON.stringify({
      decision: 'allow',
      additionalContext: warning,
    }));

  } catch {
    console.log(JSON.stringify({ decision: 'allow' }));
  }
});
