#!/usr/bin/env node
/**
 * Quality Gate Hook — PreToolUse
 *
 * Intercepts Write/Edit on specific file types and injects reminders:
 *   - Java files (.java): "Remember to run mvn compile before claiming done"
 *   - Config files (plugin.yml, config.yml): "Remember to deploy + clear .paper-remapped"
 *   - TypeScript/JS files: "Remember to run tsc --noEmit / npm test"
 *
 * Also tracks which files have been modified in the session (via temp file)
 * so a PostToolUse hook can reference the full list of dirty files.
 *
 * Phase 1 of Master Plan — Automation Hooks
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const TRACKER_DIR = path.join(os.tmpdir(), 'claude-quality-gate');
const SESSION_ID_ENV = process.env.CLAUDE_SESSION_ID || 'unknown';

function getTrackerPath(sessionId) {
  return path.join(TRACKER_DIR, `dirty-${sessionId}.json`);
}

function trackDirtyFile(sessionId, filePath, fileType) {
  try {
    if (!fs.existsSync(TRACKER_DIR)) {
      fs.mkdirSync(TRACKER_DIR, { recursive: true });
    }
    const trackerPath = getTrackerPath(sessionId);
    let tracker = {};
    if (fs.existsSync(trackerPath)) {
      tracker = JSON.parse(fs.readFileSync(trackerPath, 'utf8'));
    }
    if (!tracker[fileType]) tracker[fileType] = [];
    if (!tracker[fileType].includes(filePath)) {
      tracker[fileType].push(filePath);
    }
    fs.writeFileSync(trackerPath, JSON.stringify(tracker, null, 2));
  } catch { /* best effort */ }
}

function getReminder(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const basename = path.basename(filePath).toLowerCase();

  // Java source files
  if (ext === '.java') {
    return {
      type: 'java',
      msg: '☕ QUALITY GATE: Java file modified. Run `mvn compile` (or full build) before claiming "done". Check Mistake #23: Compile Without Deploy.',
    };
  }

  // Bukkit/Paper configs
  if (['plugin.yml', 'config.yml', 'server_context.yml'].includes(basename)) {
    return {
      type: 'config',
      msg: '📦 QUALITY GATE: Config file modified. Remember to deploy via SFTP + clear .paper-remapped. Check Mistake #16: Setup JAR Drift.',
    };
  }

  // TypeScript
  if (ext === '.ts' || ext === '.tsx') {
    return {
      type: 'typescript',
      msg: '🔷 QUALITY GATE: TypeScript file modified. Run `npx tsc --noEmit` before claiming done.',
    };
  }

  // Python
  if (ext === '.py') {
    return {
      type: 'python',
      msg: '🐍 QUALITY GATE: Python file modified. Run type checker / tests before claiming done.',
    };
  }

  // pom.xml
  if (basename === 'pom.xml') {
    return {
      type: 'maven',
      msg: '📋 QUALITY GATE: pom.xml modified. Run `mvn validate` to check for errors.',
    };
  }

  return null;
}

// 2026-04-25 schema migration. Legacy `{decision:'allow'}` shape is rejected
// by the current Claude Code harness with "Hook JSON output validation failed"
// noise on every Write/Edit. Migrated to: exit 0 with empty stdout = pass
// (universally schema-valid), schema-current `hookSpecificOutput.permissionDecisionReason`
// for advisory reminders. Reminder logic + dirty-file tracking unchanged —
// only the wire format of the decision changes.
function emitPass() { process.exit(0); }
function emitPassWithReminder(msg) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      permissionDecisionReason: msg,
    },
  }));
  process.exit(0);
}

let input = '';
const stdinTimeout = setTimeout(emitPass, 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const toolName = data.tool_name || '';

    // Only intercept Write and Edit — every other tool passes through.
    if (toolName !== 'Write' && toolName !== 'Edit') return emitPass();

    const toolInput = data.tool_input || {};
    const filePath = toolInput.file_path || '';
    const sessionId = data.session_id || SESSION_ID_ENV;

    if (!filePath) return emitPass();

    const reminder = getReminder(filePath);

    if (reminder) {
      trackDirtyFile(sessionId, filePath, reminder.type);
      return emitPassWithReminder(reminder.msg);
    }
    return emitPass();
  } catch (e) {
    return emitPass();
  }
});
