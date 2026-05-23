#!/usr/bin/env node
// CANONICAL SOURCE — Power Pack repo. Deployed to ~/.claude/hooks/ via
// install-global.ps1 + tools/install_global_core.py session-safety manifest
// pattern. Edit here, re-run install-global; never edit the deployed copy
// directly.
/**
 * research-intent-detector.js — Stop hook (Claude Power Pack).
 *
 * Source spec: claude-power-pack/vault/specs/deep-research-agent.md §7.2
 * Plan:        claude-power-pack/vault/plans/deep-research-agent-2026-05-23.md
 *
 * Fires on every assistant-turn Stop. Reads the LAST user prompt from the
 * current session's .jsonl. If the prompt matches the research-intent
 * regex AND meets the breadth-of-question gate (default-b decision from
 * spec §12: verb match + >= 80 words OR >= 3 question marks), spawn the
 * deep-research Python agent detached (cmd.exe /c start "" /B ...) so the
 * Stop hook returns to the harness in < 200 ms while the agent runs in
 * the background.
 *
 * Activation contract:
 *   - This hook is OWNER-pasted (Mirror-Sync-Direction doctrine: the
 *     installer never writes into ~/.claude/hooks/).
 *   - Registration is the one-shot `register-deep-research` consolidator
 *     in settings_merger.py.
 *
 * Opt-out: CLAUDEPP_DEEPRESEARCH_DISABLE=1 in env -> the hook still
 * fires but the spawn is skipped, with a single line written to the
 * auto-spawned log so the Owner sees the would-have-fired pattern.
 *
 * Safety:
 *   - Fail-OPEN: any exception writes a diagnostic to stderr and exits 0.
 *     A buggy intent detector MUST NOT block the Stop hook chain.
 *   - The detached spawn uses `start "" /B` so closing the parent
 *     window does not kill the child. The child writes to its own
 *     output stream (vault/research/<ts>_<slug>.md) and never tries
 *     to write back to this session.
 *   - Single-instance lock at vault/research/.deep-research.lock is
 *     held by the Python child, NOT by this hook — so the hook
 *     can fire multiple times safely; the child refuses to start if
 *     another run is in flight.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const child_process = require('child_process');

const HOME = os.homedir();
const PP_REPO = path.join(HOME, '.claude', 'skills', 'claude-power-pack');
const PROJECTS_DIR = path.join(HOME, '.claude', 'projects');
const RESEARCH_DIR = path.join(PP_REPO, 'vault', 'research');
const AUTO_LOG = path.join(RESEARCH_DIR, '.auto-spawned.log');
const DEEPRESEARCH_PY = path.join(
  PP_REPO, 'modules', 'deep-research', 'deep_research.py'
);

// Research-intent regex — Spanish + English. Word-boundary anchored. The
// list is intentionally narrow: every match is a *deliberate* research
// verb, not a generic question word. "What is X" alone does not match
// (too noisy); "research X" / "investiga X" does.
const RESEARCH_INTENT_RE = new RegExp(
  '\\b('
  + 'investiga(?:r|cion)?|investigate'
  + '|research'
  + '|analiza(?:r)?|analyse|analyze'
  + '|compara(?:r)?|compare'
  + '|deep[-\\s]?dive'
  + '|qu[eé]\\s+opciones'
  + '|how\\s+does|how\\s+do'
  + '|mercado\\s+de'
  + '|estado\\s+del\\s+arte'
  + ')\\b',
  'i'
);

const MIN_WORDS = 80;
const MIN_QUESTION_MARKS = 3;

function logErr(msg) {
  try { process.stderr.write('research-intent-detector: ' + msg + '\n'); }
  catch (_) { /* noop */ }
}

function failOpen(reason) {
  logErr('fail-open: ' + reason);
  process.exit(0);
}

function readStdin() {
  try {
    const buf = fs.readFileSync(0, 'utf-8');
    return buf ? JSON.parse(buf) : {};
  } catch (e) {
    failOpen('stdin parse: ' + e.message);
  }
}

function findSessionJsonl(sessionId) {
  if (!sessionId) return null;
  let projs;
  try { projs = fs.readdirSync(PROJECTS_DIR); } catch (_) { return null; }
  for (const proj of projs) {
    const candidate = path.join(PROJECTS_DIR, proj, sessionId + '.jsonl');
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

// Walk the .jsonl tail and find the most recent user message (type=user
// with message.role=user). The tail (last 256 KB) is a safe upper bound
// for finding the latest few turns.
function lastUserPrompt(jsonlPath) {
  let stat;
  try { stat = fs.statSync(jsonlPath); } catch (_) { return null; }
  const start = Math.max(0, stat.size - 256 * 1024);
  const length = stat.size - start;
  if (length <= 0) return null;
  let buf;
  try {
    const fd = fs.openSync(jsonlPath, 'r');
    try {
      buf = Buffer.alloc(length);
      fs.readSync(fd, buf, 0, length, start);
    } finally { fs.closeSync(fd); }
  } catch (_) { return null; }
  const lines = buf.toString('utf-8').split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    let obj;
    try { obj = JSON.parse(line); } catch (_) { continue; }
    if (obj && obj.type === 'user') {
      const msg = obj.message || {};
      if (msg.role !== 'user') continue;
      const content = msg.content;
      if (typeof content === 'string') return content;
      if (Array.isArray(content)) {
        // Multi-part: collect text segments only.
        const parts = content
          .filter(c => c && c.type === 'text' && typeof c.text === 'string')
          .map(c => c.text);
        if (parts.length) return parts.join('\n');
      }
    }
  }
  return null;
}

function looksLikeResearchPrompt(prompt) {
  if (!prompt || typeof prompt !== 'string') return false;
  if (!RESEARCH_INTENT_RE.test(prompt)) return false;
  const words = prompt.trim().split(/\s+/).length;
  const qmarks = (prompt.match(/\?/g) || []).length;
  return words >= MIN_WORDS || qmarks >= MIN_QUESTION_MARKS;
}

function logAutoSpawn(entry) {
  try {
    fs.mkdirSync(RESEARCH_DIR, { recursive: true });
    fs.appendFileSync(AUTO_LOG, JSON.stringify(entry) + '\n', 'utf-8');
  } catch (_) { /* noop — never fail the hook */ }
}

function findPython() {
  // Honor an explicit override first.
  const fromEnv = process.env.CLAUDEPP_PY_EXE;
  if (fromEnv && fs.existsSync(fromEnv)) return fromEnv;
  // Then look in the obvious places. The user's host has Python at
  // AppData/Local/Programs/Python/Python312/python.exe.
  const candidates = [
    path.join(HOME, 'AppData', 'Local', 'Programs', 'Python',
               'Python312', 'python.exe'),
    path.join(HOME, 'AppData', 'Local', 'Programs', 'Python',
               'Python311', 'python.exe'),
    'python.exe',  // PATH fallback
    'python3',
  ];
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch (_) { /* noop */ }
  }
  return 'python';  // last-resort
}

function spawnDetached(prompt) {
  if (process.env.CLAUDEPP_DEEPRESEARCH_DISABLE === '1') {
    logAutoSpawn({
      ts: new Date().toISOString(),
      verdict: 'skipped-by-env',
      prompt: prompt.slice(0, 200),
    });
    return;
  }
  if (!fs.existsSync(DEEPRESEARCH_PY)) {
    logAutoSpawn({
      ts: new Date().toISOString(),
      verdict: 'script-missing',
      expected: DEEPRESEARCH_PY,
    });
    return;
  }
  const py = findPython();
  // Use `cmd.exe /c start "" /B` to fully detach on Windows (the empty
  // "" is the window title; /B suppresses a new console window). The
  // child writes its own output; nothing comes back to this hook.
  const args = [
    '/c', 'start', '""', '/B',
    py, DEEPRESEARCH_PY,
    '--prompt', prompt,
    '--depth', '2',
    '--breadth', '3',
    '--quiet',
  ];
  let child;
  try {
    child = child_process.spawn('cmd.exe', args, {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    child.unref();
  } catch (e) {
    logAutoSpawn({
      ts: new Date().toISOString(),
      verdict: 'spawn-failed',
      error: String(e),
    });
    return;
  }
  logAutoSpawn({
    ts: new Date().toISOString(),
    verdict: 'spawned',
    pid: child.pid || null,
    prompt: prompt.slice(0, 200),
    cmd_summary: 'python deep_research.py --depth 2 --breadth 3',
  });
}

function main() {
  // RECURSION GUARD (sealed 2026-05-23 mid-V2 empirical run).
  //
  // The python child calls claude.exe -p for each LLM step. claude.exe -p
  // runs the FULL Stop-hook chain in its own subprocess session. The
  // generate_serp_queries prompt contains the literal word "research"
  // AND exceeds 80 words, so the intent regex matches AND the breadth
  // gate passes -- triggering ANOTHER detached spawn from inside the
  // first run. The second spawn hits the lock (lockverdict=held) and
  // emits a 1KB "deep_research locked" template report. Repeats per
  // LLM call in the recursion tree.
  //
  // Fix: the python child sets CLAUDEPP_DEEPRESEARCH_RUNNING=1 in the
  // claude.exe subprocess env. We check it FIRST and exit silently.
  if (process.env.CLAUDEPP_DEEPRESEARCH_RUNNING === '1') {
    process.exit(0);
  }

  let input;
  try { input = readStdin(); } catch (_) { failOpen('readStdin'); }
  const sessionId = input && input.session_id;
  if (!sessionId) failOpen('no session_id in stdin');

  const jsonlPath = findSessionJsonl(sessionId);
  if (!jsonlPath) failOpen('jsonl not found for session ' + sessionId);

  const prompt = lastUserPrompt(jsonlPath);
  if (!prompt) failOpen('no recent user prompt found');

  if (!looksLikeResearchPrompt(prompt)) {
    // Not research-intent. This is the common case — exit silently to
    // keep the hook chain quiet. We don't log non-matches (would dwarf
    // the actual spawn signals).
    process.exit(0);
  }

  spawnDetached(prompt);
  process.exit(0);
}

try { main(); }
catch (e) { failOpen('top-level: ' + e.message); }
