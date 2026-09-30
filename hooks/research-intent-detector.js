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
 * OFF BY DEFAULT (Owner, 2026-09-30). Automatic research is opt-in:
 * CLAUDEPP_DEEPRESEARCH_AUTO=1 turns it on. Measured over 227 reports
 * (2026-05-24..09-30): 155 empty, the rest mostly triggered by machine
 * text, and zero references to any report anywhere in the repo. Manual
 * runs (/cpp-deep-research) do not pass through this hook and still work.
 *
 * Kill switch: CLAUDEPP_DEEPRESEARCH_DISABLE=1 also stops manual runs
 * (deep_research.py refuses); with it set, an opted-in hook logs a
 * skipped-by-env line instead of spawning.
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

function entryText(obj) {
  const content = (obj.message || {}).content;
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    const parts = content
      .filter(c => c && c.type === 'text' && typeof c.text === 'string')
      .map(c => c.text);
    if (parts.length) return parts.join('\n');
  }
  return null;
}

// The most recent prompt the Owner TYPED, or null. type=user entries also
// carry skill expansions (isMeta), inter-session messages and command
// wrappers; measured 2026-09-30: 134 of 136 spawns in 7 days came from
// those, 2 from a human. Only origin.kind === 'human' counts, and if the
// newest text entry is machine-made the turn was not a research request.
function lastHumanPrompt(jsonlPath) {
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
    if (!obj || obj.type !== 'user') continue;
    if ((obj.message || {}).role !== 'user') continue;
    if (obj.isMeta) continue;                // skill/command expansion
    const text = entryText(obj);
    if (!text) continue;                     // tool_result-only entry
    const human = obj.origin && obj.origin.kind === 'human';
    if (!human) return null;
    if (/^\s*<command-/.test(text)) return null;   // slash command
    return text;
  }
  return null;
}

function promptSha(prompt) {
  return require('crypto').createHash('sha256').update(prompt, 'utf-8')
    .digest('hex').slice(0, 16);
}

// True when this exact prompt already produced a spawn (Stop fires again
// on the same prompt after a blocked closer or a resumed session).
function alreadySpawned(sha) {
  let text;
  try { text = fs.readFileSync(AUTO_LOG, 'utf-8'); } catch (_) { return false; }
  return text.includes('"prompt_sha":"' + sha + '"');
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
  const sha = promptSha(prompt);
  if (alreadySpawned(sha)) return;
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
  // Spawn python directly. detached gives it its own console and windowsHide
  // keeps that console hidden, so the git/node children it starts inherit a
  // hidden console instead of each opening a visible one. The old
  // `cmd /c start "" /B` route mangled the "" title under Node's quoting
  // (cmd does not honour \" escapes) and could pop a window stealing focus;
  // it also let cmd reinterpret the user's prompt (a `&` ran a second command).
  const args = [
    DEEPRESEARCH_PY,
    '--prompt', prompt,
    '--depth', '2',
    '--breadth', '3',
    '--quiet',
  ];
  let child;
  try {
    child = child_process.spawn(py, args, {
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
    prompt_sha: sha,
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

  // Opt-in (see header): without CLAUDEPP_DEEPRESEARCH_AUTO=1 nothing is
  // read, nothing is spawned, nothing is logged.
  if (process.env.CLAUDEPP_DEEPRESEARCH_AUTO !== '1') {
    process.exit(0);
  }

  let input;
  try { input = readStdin(); } catch (_) { failOpen('readStdin'); }
  const sessionId = input && input.session_id;
  if (!sessionId) failOpen('no session_id in stdin');

  const jsonlPath = findSessionJsonl(sessionId);
  if (!jsonlPath) failOpen('jsonl not found for session ' + sessionId);

  // null = the turn was not started by a typed prompt (skill expansion,
  // agent message, slash command). That is the common case: exit quietly.
  const prompt = lastHumanPrompt(jsonlPath);
  if (!prompt) process.exit(0);

  if (!looksLikeResearchPrompt(prompt)) {
    // Not research-intent. This is the common case — exit silently to
    // keep the hook chain quiet. We don't log non-matches (would dwarf
    // the actual spawn signals).
    process.exit(0);
  }

  // SREE. Before spending a research run, ask whether one already answered
  // this. `research_discovery.discover_for_cwd` computes exactly that --
  // prior research relevant to this directory, with an age -- and was an
  // audited ORPHAN with zero callers, so every repeat prompt spawned a full
  // run while the module that would have prevented it sat unreachable.
  // (Wired in 9909076, lost when 75d62ac copied the older live file over the
  // repo; restored 2026-09-30.)
  //
  // Its 24h window is the anti-fossilisation control: reuse is bounded by
  // freshness, so a stale answer expires into a real search instead of
  // hardening into a fact.
  const prior = priorResearch();
  if (prior) {
    logAutoSpawn({
      ts: new Date().toISOString(),
      status: 'skipped-prior-research',
      prompt_head: String(prompt).slice(0, 120),
      report_path: prior.report_path || '',
      age_hours: prior.age_hours,
    });
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'Stop',
        additionalContext:
          `[Woz] [deep-research] a prior run already covers this, ${prior.age_hours}h `
          + `old -- not spawning a new one.\n  ${prior.report_path}\n`
          + '  Re-run explicitly with /cpp-deep-research if it is stale.',
      },
    }));
    process.exit(0);
  }

  spawnDetached(prompt);
  process.exit(0);
}

/** Prior research for this cwd, or null. Fail-open in every direction:
 *  a discovery that errors, times out, or answers ambiguously must never
 *  suppress a real run -- skipping a needed search is the expensive
 *  mistake, not repeating one. */
function priorResearch() {
  try {
    const py = findPython();
    if (!py) return null;
    const r = child_process.spawnSync(py, [
      '-c',
      'import json,sys;'
      + 'sys.path.insert(0, r"' + PP_REPO + '");'
      + 'sys.path.insert(0, r"'
      + path.join(PP_REPO, 'modules', 'deep-research') + '");'
      + 'from research_discovery import discover_for_cwd;'
      + 'h = discover_for_cwd();'
      + 'print(json.dumps(h) if h else "")',
    ], { encoding: 'utf8', timeout: 5000, windowsHide: true });
    if (r.status !== 0 || !r.stdout) return null;
    const body = r.stdout.trim().split('\n').pop();
    if (!body) return null;
    const hit = JSON.parse(body);
    return (hit && hit.report_path) ? hit : null;
  } catch (_e) {
    return null;
  }
}

try { main(); }
catch (e) { failOpen('top-level: ' + e.message); }
