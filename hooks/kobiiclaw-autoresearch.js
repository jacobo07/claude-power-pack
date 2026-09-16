#!/usr/bin/env node
/**
 * KobiiClaw AutoResearch Hook v3 — AKOS injection only
 *
 * v3 (2026-08-14): removed the PROJECT_REGISTRY + trigger-file + lockfile
 * writes from v2. They had been confirmed dead code — v2's own comment said
 * the VPS engine "reads its own VPS-side state" and these local writes were
 * inert, kept only for backward-compat. Verified from this host: no
 * AutoResearch_* Windows scheduled task exists, and no SessionStart hook
 * pulls a VPS digest — so the "migrated to VPS" design was never actually
 * wired up locally. Writing ~30 now-unread JSON files a day for 3+ months
 * was pure waste; deleted rather than kept "for quick revert" (the project
 * registry now lives in one place: modules/autoresearch/config.json,
 * consumed by nightcrawler.py, which the /autoresearch skill invokes
 * directly — see ~/.claude/skills/autoresearch/instructions.md).
 *
 * What remains: best-effort AKOS knowledge injection on session exit. This
 * is unrelated to the dead trigger system and was not shown to be broken.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

function run(hookData) {
  hookData = hookData || {};
  const cwd = hookData.cwd || process.env.CLAUDE_CWD || process.cwd();

  // AKOS_ENGINE_PATH env var is the primary source; hardcoded path is a fallback for dev machine
  const akosEngine = process.env.AKOS_ENGINE_PATH || path.join(
    os.homedir(), 'Desktop', 'Cursor Projects', 'TUA-X', 'TUAX_UGC_SYSTEM',
    'tools', 'skool-scraper', 'knowledge_engine.py'
  );

  if (fs.existsSync(akosEngine)) {
    let pythonCmd;
    try {
      ({ getPythonCommand: pythonCmd } = require('./hook-utils'));
      pythonCmd = pythonCmd();
    } catch {
      pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    }
    try {
      execSync(`${pythonCmd} "${akosEngine}" inject "${cwd}"`, {
        timeout: 5000,
        stdio: 'ignore',
        windowsHide: true,
      });
    } catch {
      // AKOS injection is best-effort
    }
  }

  return { continue: true };
}

// --- Dual-mode entry point ---
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    console.log(JSON.stringify({ continue: true }));
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
