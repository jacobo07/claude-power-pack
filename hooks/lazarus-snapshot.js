#!/usr/bin/env node
/**
 * Lazarus Snapshot v2 — Stop hook (per-session)
 *
 * On session end, captures a rich context snapshot for `/resume` AND for
 * the multi-terminal revive pipeline.
 *
 * Writes:
 *   ~/.claude/lazarus/<project-id>/sessions/<session_id>.json  — per-session snapshot
 *   ~/.claude/lazarus/<project-id>/last_session.json           — legacy (for /resume compat)
 *   ~/.claude/lazarus/<project-id>/index.json                  — marks session as clean_exit
 *   ~/.claude/lazarus/global_index.json                        — project-level index
 *
 * Clean exit → removes per-session heartbeat + counter and does NOT
 * enqueue to pending_resume.txt (user intentionally ended that session).
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const HOME = os.homedir();
const CLAUDE_DIR = path.join(HOME, '.claude');
const LAZARUS_DIR = path.join(CLAUDE_DIR, 'lazarus');
const PLANS_DIR = path.join(CLAUDE_DIR, 'plans');

// MC-SYS-33: hardened atomic-write engine (BL-0014/18). Same call shape as the
// previous local atomicWrite(filePath, content) wrapper, but with mkdir-p,
// fsync, and Windows EPERM/EBUSY retry on rename.
//
// v240000.1 hook-hardening (VAC-ENV-240000): the canonical engine lives at
// PP lib/atomic_write.js, but parallel /ultra sessions sharing the PP working
// tree intermittently quarantine lib/ -> _quarantine/lib_dir/ (working-tree
// mv with no tracked delta), which made a hard require() throw
// MODULE_NOT_FOUND and silently kill this Stop hook. Resolve across known
// locations; fall back to a minimal inline impl so the hook NEVER hard-crashes.
function loadAtomicWrite() {
  const PP = path.join(HOME, '.claude', 'skills', 'claude-power-pack');
  const candidates = [
    path.join(PP, 'lib', 'atomic_write.js'),
    path.join(PP, '_quarantine', 'lib_dir', 'atomic_write.js'),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(c)) return require(c);
    } catch (_) { /* try next candidate */ }
  }
  return {
    atomicWriteText(filePath, text) {
      const target = path.resolve(filePath);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      const tmp = `${target}.tmp.${process.pid}.${Math.random().toString(16).slice(2)}`;
      fs.writeFileSync(tmp, text, 'utf8');
      fs.renameSync(tmp, target);
    },
    atomicWriteJson(filePath, obj, indent = 2) {
      this.atomicWriteText(filePath, JSON.stringify(obj, null, indent));
    },
  };
}
const { atomicWriteText: atomicWrite } = loadAtomicWrite();

function sanitizeProjectId(cwd) {
  return cwd.replace(/[^a-zA-Z0-9-]/g, '-');
}

function gitCmd(cmd, cwd) {
  try {
    return execSync(cmd, { cwd, encoding: 'utf8', timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true }).trim();
  } catch {
    return '';
  }
}

function ensureDir(d) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; }
}

// MC-LAZ-26: pointer is a hint, not SSoT. The tmp pointer file gets cleaned by
// Windows Storage Sense / Disk Cleanup / TempCleaner between sessions, leaving
// `/lazarus` "Last session" with empty session_log_path, tool_summary, and
// last_intent — the warm-up profile that "no funciona". Fallback: scan the
// project's memory/sessions/ for the newest session_*.md and use that.
function getSessionLogPath(cwd) {
  const projectId = sanitizeProjectId(cwd);
  const pointerPath = path.join(os.tmpdir(), `claude-session-log-${projectId}.txt`);
  try {
    if (fs.existsSync(pointerPath)) {
      const raw = fs.readFileSync(pointerPath, 'utf8').trim();
      if (raw && fs.existsSync(raw)) return raw;
    }
  } catch { /* fall through to scan */ }
  const sessionsDir = path.join(CLAUDE_DIR, 'projects', projectId, 'memory', 'sessions');
  try {
    if (!fs.existsSync(sessionsDir)) return null;
    const newest = fs.readdirSync(sessionsDir)
      .filter(f => /^session_\d{4}-\d{2}-\d{2}_\d{4}\.md$/.test(f))
      .map(f => ({ f, p: path.join(sessionsDir, f), mtime: fs.statSync(path.join(sessionsDir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime)[0];
    return newest ? newest.p : null;
  } catch {
    return null;
  }
}

function extractLastIntent(logPath, count = 5) {
  if (!logPath || !fs.existsSync(logPath)) return [];
  try {
    const content = fs.readFileSync(logPath, 'utf8');
    const lines = content.split('\n')
      .filter(l => l.startsWith('- ') && l.includes('|'))
      .slice(-count);
    return lines.map(l => l.replace(/^- \d{2}:\d{2}\s*\|\s*/, '').trim());
  } catch {
    return [];
  }
}

function extractToolSummary(logPath) {
  if (!logPath || !fs.existsSync(logPath)) return {};
  try {
    const content = fs.readFileSync(logPath, 'utf8');
    const lines = content.split('\n').filter(l => l.startsWith('- '));
    const counts = {};
    for (const line of lines) {
      const match = line.match(/\| (\w+) \|/);
      if (match) {
        const tool = match[1];
        counts[tool] = (counts[tool] || 0) + 1;
      }
    }
    return counts;
  } catch {
    return {};
  }
}

function findActivePlan() {
  if (!fs.existsSync(PLANS_DIR)) return null;
  try {
    const files = fs.readdirSync(PLANS_DIR)
      .filter(f => f.endsWith('.md'))
      .map(f => ({
        name: f,
        path: path.join(PLANS_DIR, f),
        mtime: fs.statSync(path.join(PLANS_DIR, f)).mtimeMs,
      }))
      .sort((a, b) => b.mtime - a.mtime);
    const cutoff = Date.now() - (24 * 60 * 60 * 1000);
    const recent = files.find(f => f.mtime > cutoff);
    return recent ? recent.path : null;
  } catch {
    return null;
  }
}

function updateGlobalIndex(projectId, projectPath, timestamp) {
  const indexPath = path.join(LAZARUS_DIR, 'global_index.json');
  let index = {};
  try {
    if (fs.existsSync(indexPath)) {
      index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    }
  } catch { }
  index[projectId] = { project_path: projectPath, timestamp };
  const cutoff = Date.now() - (30 * 24 * 60 * 60 * 1000);
  for (const [id, entry] of Object.entries(index)) {
    if (new Date(entry.timestamp).getTime() < cutoff) delete index[id];
  }
  try { fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf8'); } catch { }
}

function markSessionCleanExit(snapshotDir, sessionId, cwd) {
  const indexPath = path.join(snapshotDir, 'index.json');
  const existing = readJson(indexPath) || { project_id: sanitizeProjectId(cwd), project_path: cwd, sessions: [] };
  const sessions = Array.isArray(existing.sessions) ? existing.sessions : [];
  const i = sessions.findIndex(s => s.session_id === sessionId);
  const now = new Date().toISOString();
  if (i >= 0) {
    sessions[i].status = 'clean_exit';
    sessions[i].last_seen = now;
    sessions[i].ended = now;
  } else {
    sessions.push({ session_id: sessionId, started: now, last_seen: now, ended: now, status: 'clean_exit', terminal_hint: '' });
  }
  existing.sessions = sessions;
  existing.updated = now;
  try { atomicWrite(indexPath, JSON.stringify(existing, null, 2)); } catch { }
}

/**
 * MC-LAZ-I: guard last_session.json writes.
 *
 * The legacy ~/.claude/lazarus/<pid>/last_session.json file is shared
 * across every session in a project (last-writer-wins). If session A
 * ends cleanly while session B is still alive, A's Stop hook would
 * blow away B's mid-mirror — so on a later laptop crash, /resume
 * picks A (older, ended) instead of B (latest, killed). That's the
 * "you landed in the session before the latest" bug the Owner hit.
 *
 * Rule: don't overwrite last_session.json if ANOTHER session has a
 * fresh heartbeat (< 5 min old). Let the currently-active session
 * keep owning the legacy pointer via its own mirror writes.
 */
const LEGACY_GUARD_FRESH_MS = 5 * 60 * 1000;
function shouldUpdateLegacyMirror(heartbeatsDir, mySessionId) {
  if (!fs.existsSync(heartbeatsDir)) return true;
  const cutoff = Date.now() - LEGACY_GUARD_FRESH_MS;
  try {
    for (const name of fs.readdirSync(heartbeatsDir)) {
      if (!name.endsWith('.lock')) continue;
      const sid = name.slice(0, -5);
      if (sid === mySessionId) continue;
      const p = path.join(heartbeatsDir, name);
      try {
        if (fs.statSync(p).mtimeMs >= cutoff) return false;
      } catch { /* unreadable — ignore */ }
    }
  } catch { /* unreadable dir — fail open */ }
  return true;
}

function removeFromPending(snapshotDir, sessionId) {
  const pendingPath = path.join(snapshotDir, 'pending_resume.txt');
  if (!fs.existsSync(pendingPath)) return;
  try {
    const lines = fs.readFileSync(pendingPath, 'utf8').split('\n').map(l => l.trim()).filter(Boolean);
    const remaining = lines.filter(l => l !== sessionId);
    if (remaining.length !== lines.length) {
      atomicWrite(pendingPath, remaining.join('\n') + (remaining.length ? '\n' : ''));
    }
  } catch { }
}

// --- Core processing (extracted so hook-dispatcher.js can require this module) ---
function run(data) {
  try {
    data = data || {};
    const cwd = data.cwd || process.cwd();
    const sessionId = data.session_id || 'unknown';
    const projectId = sanitizeProjectId(cwd);
    const now = new Date().toISOString();

    const branch = gitCmd('git rev-parse --abbrev-ref HEAD', cwd);
    const statusRaw = gitCmd('git status --porcelain', cwd);
    const uncommittedFiles = statusRaw
      ? statusRaw.split('\n').map(l => l.trim().replace(/^[A-Z?]+\s+/, '')).filter(Boolean)
      : [];
    const recentCommits = gitCmd('git log --oneline -5 2>/dev/null', cwd)
      .split('\n').filter(Boolean);

    const sessionLogPath = getSessionLogPath(cwd);
    const lastIntent = extractLastIntent(sessionLogPath);
    const toolSummary = extractToolSummary(sessionLogPath);
    const activePlan = findActivePlan();

    // MC-LAZ-15: context_metadata — WHITELISTED env capture only.
    // Captures terminal_label (LAZARUS_TERMINAL_KEY) for the
    // bindings/respawn flow. Explicitly does NOT capture API keys
    // or any other env var — secrets stay in the user's shell, never
    // hit the snapshot JSON. If you need additional vars, add them
    // here ONLY after a security review (e.g. CLAUDE_PROJECT_DIR is
    // safe; ANTHROPIC_API_KEY etc. are not).
    const contextMetadata = {
      cwd,
      terminal_label: process.env.LAZARUS_TERMINAL_KEY || null,
    };

    const snapshot = {
      project_id: projectId,
      project_path: cwd,
      timestamp: now,
      source: 'stop_hook',
      session_id: sessionId,
      branch: branch || 'unknown',
      uncommitted_files: uncommittedFiles.slice(0, 20),
      recent_commits: recentCommits,
      session_log_path: sessionLogPath,
      active_plan: activePlan,
      tool_summary: toolSummary,
      last_intent: lastIntent,
      context_metadata: contextMetadata,
    };

    const snapshotDir = path.join(LAZARUS_DIR, projectId);
    const sessionsDir = path.join(snapshotDir, 'sessions');
    ensureDir(snapshotDir);
    ensureDir(sessionsDir);

    try { atomicWrite(path.join(sessionsDir, `${sessionId}.json`), JSON.stringify(snapshot, null, 2)); } catch { }

    // MC-LAZ-23: bindings.json auto-populate. The chain was half-built —
    // snapshot.js captures LAZARUS_TERMINAL_KEY into terminal_label, and
    // lazarus-resolve-termkey.ps1 reads bindings.json, but nothing ever
    // wrote bindings.json. Result: termkey resolution always missed,
    // slot1/2/3 collapsed to the same fallback UUID, only one pane
    // revived. This block closes the gap idempotently per project.
    if (contextMetadata.terminal_label && sessionId && sessionId !== 'unknown') {
      try {
        const bindingsPath = path.join(snapshotDir, 'bindings.json');
        const existing = readJson(bindingsPath) || {};
        const terminal_keys = (existing && existing.terminal_keys) || {};
        if (terminal_keys[contextMetadata.terminal_label] !== sessionId) {
          terminal_keys[contextMetadata.terminal_label] = sessionId;
          atomicWrite(bindingsPath, JSON.stringify({
            terminal_keys,
            updated: now,
          }, null, 2));
        }
      } catch { /* best-effort */ }
    }

    // MC-LAZ-I: per-session snapshot above is canonical and always
    // written. The legacy last_session.json is shared across all
    // sessions in this project and only updated if no OTHER session
    // is currently alive — otherwise we'd clobber the live session's
    // mirror with our own clean-exit data, sending a future /resume
    // to the wrong (older) session.
    const heartbeatsDir = path.join(snapshotDir, 'heartbeats');
    if (shouldUpdateLegacyMirror(heartbeatsDir, sessionId)) {
      try { atomicWrite(path.join(snapshotDir, 'last_session.json'), JSON.stringify(snapshot, null, 2)); } catch { }
    }

    markSessionCleanExit(snapshotDir, sessionId, cwd);

    // MC-LAZ-24: zero-click auto-revive. Previously removeFromPending
    // dropped the session from the queue on clean exit, forcing the
    // next-open path through fallback-resolver — which returns ONE
    // most-recent-clean per project. With N panes in the same project,
    // they all collapse to the same UUID and collide on the jsonl
    // exclusive lock; only one revives, the rest get fresh shells.
    //
    // Instead: enqueue on clean exit so pending_resume.txt is a proper
    // FIFO that scales with pane count. De-duped (skip if already in),
    // newest-first, capped at 10 to bound growth. The bat's mutex-
    // protected pop (MC-LAZ-22) ensures each pane gets a distinct UUID.
    if (sessionId && sessionId !== 'unknown') {
      try {
        const pendingPath = path.join(snapshotDir, 'pending_resume.txt');
        let lines = [];
        if (fs.existsSync(pendingPath)) {
          lines = fs.readFileSync(pendingPath, 'utf8')
            .split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        }
        if (!lines.includes(sessionId)) {
          lines.unshift(sessionId);
          if (lines.length > 10) lines = lines.slice(0, 10);
          atomicWrite(pendingPath, lines.join('\n') + '\n');
        }
      } catch { /* best-effort */ }
    }

    updateGlobalIndex(projectId, cwd, now);

    // MC-LAZ-06e: Shadow-Folder auto-restore on clean exit.
    // restoreSelfToo=true also un-shadows our OWN .jsonl in case it
    // was renamed by a now-dead peer that never ran its own restore.
    // Critical asymmetric-crash recovery: without this, a survivor's
    // transcript stays invisible until panic-restore runs.
    if (process.env.LAZARUS_SHADOW_FOLDER === '1' && sessionId !== 'unknown') {
      try {
        const { restore } = require(path.join(
          os.homedir(),
          '.claude', 'skills', 'claude-power-pack',
          'lib', 'lazarus', 'shadow_engine.js',
        ));
        restore({ projectId, ownerSid: sessionId, restoreSelfToo: true });
      } catch { /* best-effort */ }
    }

    for (const p of [
      path.join(snapshotDir, 'heartbeats', `${sessionId}.lock`),
      path.join(snapshotDir, 'tool_counts', `${sessionId}.txt`),
      path.join(snapshotDir, 'heartbeat.lock'),
      path.join(snapshotDir, 'tool_count.txt'),
    ]) {
      try { fs.unlinkSync(p); } catch { /* already gone */ }
    }
  } catch (_) {
    // Silent — snapshot is best-effort, never block session end
  }
  return { continue: true };
}

// --- Dual-mode entry point ---
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { console.log(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 5000);

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
