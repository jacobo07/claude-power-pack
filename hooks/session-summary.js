#!/usr/bin/env node
/**
 * Session Summary — Stop hook
 *
 * On session end, appends a summary section to the session log.
 * Counts tool calls by type from the log file entries.
 *
 * Phase 2 of Master Plan — Memory System Completion
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

function getSessionLogPath(cwd) {
  const projectId = cwd.replace(/[^a-zA-Z0-9-]/g, '-');
  const pointerPath = path.join(os.tmpdir(), `claude-session-log-${projectId}.txt`);
  try {
    if (fs.existsSync(pointerPath)) {
      return fs.readFileSync(pointerPath, 'utf8').trim();
    }
  } catch { }
  return null;
}

// --- Core processing (extracted so hook-dispatcher.js can require this module) ---
function run(data) {
  try {
    data = data || {};
    const cwd = data.cwd || process.cwd();
    const logPath = getSessionLogPath(cwd);
    if (!logPath || !fs.existsSync(logPath)) return { continue: true };

    const content = fs.readFileSync(logPath, 'utf8');
    const lines = content.split('\n').filter(l => l.startsWith('- '));

    const toolCounts = {};
    for (const line of lines) {
      const match = line.match(/\| (\w+) \|/);
      if (match) {
        const tool = match[1];
        toolCounts[tool] = (toolCounts[tool] || 0) + 1;
      }
    }

    const now = new Date();
    const summary = [
      '',
      '### Session Summary',
      `- Ended: ${now.toISOString().slice(0, 16)}`,
      `- Total tool calls: ${lines.length}`,
      `- Breakdown: ${Object.entries(toolCounts).map(([k, v]) => `${k}(${v})`).join(', ')}`,
      '',
    ].join('\n');

    fs.appendFileSync(logPath, summary);

    const projectId = cwd.replace(/[^a-zA-Z0-9-]/g, '-');
    const pointerPath = path.join(os.tmpdir(), `claude-session-log-${projectId}.txt`);
    try { fs.unlinkSync(pointerPath); } catch { }
  } catch (_) {
    // Silent
  }
  return { continue: true };
}

// --- Dual-mode entry point ---
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    let data = {};
    try { data = JSON.parse(input); } catch (_) { /* keep empty */ }
    console.log(JSON.stringify(run(data)));
    process.exit(0);
  });
} else {
  module.exports = { run };
}
