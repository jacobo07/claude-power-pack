#!/usr/bin/env node
/**
 * learning-sentinel.js — Compound Learnings Sentinel
 *
 * Modes (branch on data.hook_event_name):
 *   - SessionEnd: count NEW learning files since last /cpp-compound; if > threshold,
 *                 write LEARNINGS_PENDING.md marker at project root.
 *   - Stop (fallback): same logic, gated by session-once lockfile in os.tmpdir() so it
 *                      cannot fire per-turn even if SessionEnd is unsupported on this build.
 *   - SessionStart: if marker present, inject additionalContext. Also load global
 *                   ~/.claude/rules/*.md (the consumer wiring for produced rules).
 *
 * Sleepy contract (audit-locked):
 *   - First-ever observation per project = cold-start grace (initialize cursor, no marker).
 *   - Cursor only advances inside /cpp-compound Step 7 (this hook NEVER advances).
 *   - Always returns {continue:true}; silent on internal error; 3s stdin timeout.
 *   - State mutations wrapped in mkdir-mutex with >30s stale-lock recovery.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const STATE_FILE = path.join(os.homedir(), '.claude', 'state', 'compound-learnings.json');
const LOCK_DIR = STATE_FILE + '.lock';
const RULES_DIR = path.join(os.homedir(), '.claude', 'rules');
const STALE_LOCK_MS = 30_000;
const HEADER_PROBE_RE = /## Patterns|\*\*Takeaway:\*\*|\*\*Actionable takeaway:\*\*|## What Worked|## What Failed/;

// Apollo GraphQL auto-warmup (homedir-anchored: card lives in Power Pack, not cwd).
const APOLLO_CARD = path.join(
  os.homedir(), '.claude', 'skills', 'claude-power-pack',
  'vendor', 'apollo', 'ground-rules-card.md'
);
const GQL_DEP_RE = /^(@apollo\/(client|server|federation|rover|gateway|subgraph-server)|apollo-server.*|@apollo\/link.*|graphql|graphql-tag|graphql-request|@graphql-codegen\/.*|@graphql-tools\/.*|relay-runtime|urql|@urql\/.*)$/;
const GQL_SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', 'vendor', '.next',
  'out', 'coverage', '.turbo', '.cache', 'target'
]);

/**
 * Detect GraphQL signals in a project cwd. Cheap package.json dependency
 * check first; only falls back to a bounded fs walk (max-depth 4, early-exit
 * on first .graphql/.gql hit) if the dep check misses. Bounded so it cannot
 * blow the SessionStart 3s budget on a large monorepo.
 */
function detectGraphQLSignals(cwd) {
  try {
    const pj = path.join(cwd, 'package.json');
    if (fs.existsSync(pj)) {
      const j = JSON.parse(fs.readFileSync(pj, 'utf8'));
      const deps = Object.assign(
        {}, j.dependencies, j.devDependencies, j.peerDependencies
      );
      if (Object.keys(deps).some(k => GQL_DEP_RE.test(k))) return true;
    }
  } catch { /* malformed package.json — fall through to fs walk */ }

  const stack = [{ dir: cwd, depth: 0 }];
  let scanned = 0;
  while (stack.length) {
    const { dir, depth } = stack.pop();
    if (scanned > 4000) break;
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
    catch { continue; }
    for (const e of entries) {
      scanned++;
      if (e.isDirectory()) {
        if (depth < 4 && !GQL_SKIP_DIRS.has(e.name)) {
          stack.push({ dir: path.join(dir, e.name), depth: depth + 1 });
        }
      } else if (e.isFile() &&
                 (e.name.endsWith('.graphql') || e.name.endsWith('.gql'))) {
        return true;
      }
    }
  }
  return false;
}

function resolveProject(data) {
  const cwd = (data && data.cwd) || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const pid = cwd.replace(/[^a-zA-Z0-9-]/g, '-');
  return { cwd, pid };
}

function acquireLock() {
  const start = Date.now();
  while (true) {
    try {
      fs.mkdirSync(LOCK_DIR);
      return true;
    } catch (e) {
      if (e.code !== 'EEXIST') return false;
      let stat;
      try { stat = fs.statSync(LOCK_DIR); } catch { stat = null; }
      if (stat && (Date.now() - stat.mtimeMs > STALE_LOCK_MS)) {
        try { fs.rmdirSync(LOCK_DIR); continue; } catch { return false; }
      }
      if (Date.now() - start > 5000) return false;
      const end = Date.now() + 50;
      while (Date.now() < end) { /* spin briefly */ }
    }
  }
}

function releaseLock() {
  try { fs.rmdirSync(LOCK_DIR); } catch { /* noop */ }
}

function readState() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return { schema_version: 1, threshold: 5, last_run_global: null, projects: {} };
    }
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return { schema_version: 1, threshold: 5, last_run_global: null, projects: {} };
  }
}

function resolveAtomicWriteJson() {
  try {
    const lib = require(
      path.join(os.homedir(), '.claude', 'skills', 'claude-power-pack', 'lib', 'atomic_write.js')
    );
    return typeof lib.atomicWriteJson === 'function' ? lib.atomicWriteJson : null;
  } catch {
    return null;
  }
}

function writeStateAtomic(state) {
  const aw = resolveAtomicWriteJson();
  if (aw) {
    try { aw(STATE_FILE, state, 2); return; } catch { /* fall through to local */ }
  }
  const tmp = STATE_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
  fs.renameSync(tmp, STATE_FILE);
}

function gatherLearningFiles(cwd) {
  const primary = path.join(cwd, '.claude', 'cache', 'learnings');
  const out = [];
  try {
    if (fs.existsSync(primary)) {
      for (const f of fs.readdirSync(primary)) {
        if (f.endsWith('.md')) out.push(path.join(primary, f));
      }
    }
  } catch { /* noop */ }
  if (out.length > 0) return out;

  const fallback = path.join(cwd, 'memory', 'sessions');
  try {
    if (!fs.existsSync(fallback)) return out;
    for (const f of fs.readdirSync(fallback)) {
      if (!f.startsWith('session_') || !f.endsWith('.md')) continue;
      const fp = path.join(fallback, f);
      try {
        const head = fs.readFileSync(fp, 'utf8').slice(0, 8192);
        if (HEADER_PROBE_RE.test(head)) out.push(fp);
      } catch { /* skip unreadable */ }
    }
  } catch { /* noop */ }
  return out;
}

function countNewSinceCursor(files, cursorIso) {
  const cursor = cursorIso ? new Date(cursorIso).getTime() : 0;
  let n = 0;
  for (const f of files) {
    try { if (fs.statSync(f).mtimeMs > cursor) n++; } catch { /* skip */ }
  }
  return n;
}

function writeMarker(cwd, count, cursorIso, source) {
  const marker = path.join(cwd, 'LEARNINGS_PENDING.md');
  const body = [
    '# Compound Learnings — Pending Consolidation',
    '',
    `**Pending count:** ${count} new learning files since ${cursorIso || 'cold-start'}.`,
    `**Source:** \`${source}\``,
    `**Detected at:** ${new Date().toISOString()}`,
    '',
    'Run `/cpp-compound` to extract patterns, propose artifacts, and consolidate.',
    'This marker auto-clears after a successful `/cpp-compound` run (Step 7).',
    ''
  ].join('\n');
  try { fs.writeFileSync(marker, body); } catch { /* silent */ }
}

function sessionOnceGuard(pid) {
  const guard = path.join(os.tmpdir(), `learning-sentinel-once-${pid}.flag`);
  try {
    fs.openSync(guard, 'wx');
    return true;
  } catch (e) {
    if (e.code === 'EEXIST') {
      try {
        const stat = fs.statSync(guard);
        if (Date.now() - stat.mtimeMs > 6 * 60 * 60 * 1000) {
          fs.unlinkSync(guard);
          fs.openSync(guard, 'wx');
          return true;
        }
      } catch { /* noop */ }
      return false;
    }
    return false;
  }
}

function handleSessionEndOrStop(data, isStopFallback) {
  const { cwd, pid } = resolveProject(data);
  if (isStopFallback && !sessionOnceGuard(pid)) return;

  if (!acquireLock()) return;
  try {
    const state = readState();
    if (!state.projects[pid] || state.projects[pid].last_run_iso === undefined) {
      state.projects[pid] = { last_run_iso: new Date().toISOString() };
      writeStateAtomic(state);
      return;
    }
    const cursor = state.projects[pid].last_run_iso;
    releaseLock();

    const files = gatherLearningFiles(cwd);
    if (files.length === 0) return;
    const count = countNewSinceCursor(files, cursor);
    const threshold = state.threshold || 5;
    if (count > threshold) {
      const source = files[0].includes(path.join('.claude', 'cache', 'learnings'))
        ? '.claude/cache/learnings/*.md'
        : 'memory/sessions/session_*.md (header-filtered)';
      writeMarker(cwd, count, cursor, source);
    }
    return;
  } finally {
    try { fs.rmdirSync(LOCK_DIR); } catch { /* may already be released */ }
  }
}

function handleSessionStart(data) {
  const { cwd, pid } = resolveProject(data);
  const ctx = [];

  const marker = path.join(cwd, 'LEARNINGS_PENDING.md');
  if (fs.existsSync(marker)) {
    let body = '';
    try { body = fs.readFileSync(marker, 'utf8'); } catch { body = ''; }

    // L1 auto-prompt policy: global default knob + per-project opt-out.
    // GAP-7 runaway guard: directive_count grows on each SessionStart-with-marker;
    // /cpp-compound Step 7 resets it to 0 on successful cursor advance. After
    // DIRECTIVE_DEGRADE_AT consecutive directives without a reset, consolidation
    // is presumed stuck — suppress auto-invoke, surface a manual-intervention warning.
    const DIRECTIVE_DEGRADE_AT = 4;
    let directive = false;
    let degraded = false;
    let dcount = 0;

    if (acquireLock()) {
      try {
        const state = readState();
        const globalOn = state.auto_prompt_default !== false; // default ON
        const proj = state.projects[pid] || {};
        const projOn = proj.auto_prompt !== false;            // default ON
        directive = globalOn && projOn;

        if (directive) {
          dcount = (proj.directive_count || 0) + 1;
          if (dcount >= DIRECTIVE_DEGRADE_AT) degraded = true;
          proj.directive_count = dcount;
          state.projects[pid] = proj;
          writeStateAtomic(state);
        }
      } catch { /* keep safe defaults: directive=false → passive */ }
      finally { releaseLock(); }
    }

    if (directive && !degraded) {
      ctx.push(
        '## 🤖 Compound Learnings — AUTO-INVOKE\n' + body +
        '\n🤖 **AUTO-INVOKE `/cpp-compound` NOW.** This is a directive, not a suggestion. ' +
        'Step 6 artifact approvals (AskUserQuestion) remain human-gated for safety. ' +
        '(Auto-prompt #' + dcount + ' for this project; auto-suppresses after ' +
        DIRECTIVE_DEGRADE_AT + ' un-consolidated prompts.)'
      );
    } else if (directive && degraded) {
      ctx.push(
        '## ⚠️ Compound Learnings — STUCK (auto-invoke suppressed)\n' + body +
        '\n⚠️ `/cpp-compound` has been auto-prompted ' + dcount + ' times without the ' +
        'consolidation cursor advancing — Step 7 is likely partial-failing. Auto-invoke ' +
        'is now SUPPRESSED for this project to prevent a runaway loop. Investigate ' +
        'manually, then either run `/cpp-compound` (a successful run resets the counter) ' +
        'or delete `LEARNINGS_PENDING.md` to dismiss.'
      );
    } else {
      // Opt-out (global default OFF or per-project auto_prompt:false): passive L0 wording.
      ctx.push('## Compound Learnings Pending\n' + body + '\nRun `/cpp-compound` to consolidate.');
    }
  }

  try {
    if (fs.existsSync(RULES_DIR)) {
      const ruleFiles = fs.readdirSync(RULES_DIR).filter(f => f.endsWith('.md')).sort();
      for (const rf of ruleFiles) {
        try {
          const body = fs.readFileSync(path.join(RULES_DIR, rf), 'utf8');
          ctx.push(`### Global Rule: ${rf}\n${body}`);
        } catch { /* skip */ }
      }
    }
  } catch { /* noop */ }

  // Apollo GraphQL hybrid warmup: inline the ~80-token ground-rules card only
  // when the project shows a GraphQL signal. Full modules stay lazy (Q&A 2c).
  try {
    if (detectGraphQLSignals(cwd) && fs.existsSync(APOLLO_CARD)) {
      const card = fs.readFileSync(APOLLO_CARD, 'utf8');
      ctx.push(
        '### Apollo GraphQL Ground Rules (auto-warmed — GraphQL signal in project)\n'
        + card
      );
    }
  } catch { /* noop — never block SessionStart */ }

  if (ctx.length === 0) return { continue: true };
  return {
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: ctx.join('\n\n---\n\n')
    }
  };
}

function run(data) {
  try {
    data = data || {};
    const event = data.hook_event_name || data.event || '';
    if (event === 'SessionEnd') {
      handleSessionEndOrStop(data, false);
      return { continue: true };
    }
    if (event === 'Stop') {
      handleSessionEndOrStop(data, true);
      return { continue: true };
    }
    if (event === 'SessionStart') {
      return handleSessionStart(data);
    }
    return { continue: true };
  } catch {
    return { continue: true };
  }
}

if (require.main === module) {
  let input = '';
  const t = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { /* noop */ }
    process.exit(0);
  }, 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => input += c);
  process.stdin.on('end', () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(input); } catch { /* keep empty */ }
    try { console.log(JSON.stringify(run(data))); } catch { /* noop */ }
    process.exit(0);
  });
} else {
  module.exports = { run, resolveProject, gatherLearningFiles, countNewSinceCursor, detectGraphQLSignals };
}
