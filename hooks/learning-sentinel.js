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
const RECOVERED_CACHE = path.join(os.homedir(), '.claude', 'state', 'recovered-composers.json');
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
      // L3 (SessionEnd only, gap #1: never on the Stop fallback). Detached,
      // triple-shielded background proposal extraction. Fail-open — must
      // never break SessionEnd.
      if (!isStopFallback) {
        try { maybeSpawnL3(cwd); } catch { /* never break SessionEnd */ }
      }
    }
    return;
  } finally {
    try { fs.rmdirSync(LOCK_DIR); } catch { /* may already be released */ }
  }
}

function readRecoveredAdvisory() {
  // Lazarus recovered-orphan advisory. Source data carries no project
  // attribution (recovered.old:scrape rows have project='?'), so this is
  // a GENERAL high-priority advisory, not a per-project law override.
  // Honest wiring: surface count + triage path + override semantics.
  try {
    if (!fs.existsSync(RECOVERED_CACHE)) return null;
    const raw = fs.readFileSync(RECOVERED_CACHE, 'utf8');
    const obj = JSON.parse(raw.charCodeAt(0) === 0xFEFF ? raw.slice(1) : raw);
    const n = obj && obj.count ? obj.count : 0;
    if (!n) return null;
    const comp = obj.composers || {};
    const top = Object.keys(comp).slice(0, 5);
    const lines = [
      '## Lazarus Recovered Sessions (override-priority)',
      '',
      n + ' RECOVERED-orphan composer session(s) exist in the Sovereign '
        + 'Vault \u2014 salvaged from state.vscdb.old.fixed.db, never '
        + 'reached a live transcript (.jsonl/.jsonl.live).',
      '',
      'Override semantics: if you resume one of these (via '
        + '`/cpp-resume-sovereign <composer_id>`), its retrieved-history '
        + 'block is AUTHORITATIVE context for that turn \u2014 it '
        + 'overrides assumptions in the live session buffer, because the '
        + 'live buffer never saw that work.',
      '',
      'Triage now: `python '
        + '~/.claude/skills/claude-power-pack/tools/vault_search.py '
        + '--list-recovered` (cache TTL 300s, '
        + 'recovered-composers.json).',
      '',
      'Top recovered composerIds: ' + (top.length ? top.join(', ') : 'n/a')
        + '.'
    ];
    return lines.join('\n');
  } catch (e) {
    return null;
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

  const recAdv = readRecoveredAdvisory();
  if (recAdv) ctx.unshift(recAdv);  // override-priority: first

  if (ctx.length === 0) return { continue: true };
  return {
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: ctx.join('\n\n---\n\n')
    }
  };
}

// ---------------------------------------------------------------------------
// L3 — detached background compound-proposal extractor.
//
// Triple shield (Q3): (a) single-flight mkdir-mutex l3-proposal.lock,
// (b) 60-min cooldown via l3-last-run.json, (c) CPP_L3_CHILD=1 recursion
// guard (also enforced at run() line 1). Lock-before-cooldown-read ordering
// (gap #8) makes the read-modify-write of l3-last-run.json atomic across
// concurrent panes. The detached child is unref'd and the parent does NOT
// release the lock (gap #4): the 60-min cooldown file (written pre-spawn,
// inside the lock) is the authoritative throttle; the mkdir-lock is a
// best-effort anti-stampede with a short 10-min stale-recovery window.
// Headless invocation empirically verified: `-p` is the real non-interactive
// flag; `--bare` is NOT used (it disables OAuth/keychain auth -> 401).
// ---------------------------------------------------------------------------
const L3_LOCK_DIR = path.join(os.homedir(), '.claude', 'state', 'l3-proposal.lock');
const L3_LAST_RUN = path.join(os.homedir(), '.claude', 'state', 'l3-last-run.json');
const L3_PROPOSAL_DIR = path.join(os.homedir(), '.claude', 'cache', 'compound-proposals');
const L3_COOLDOWN_MS = 60 * 60 * 1000; // 60 min
const L3_LOCK_STALE_MS = 10 * 60 * 1000; // 10 min anti-stampede window
const CLAUDE_EXE = path.join(os.homedir(), '.local', 'bin', 'claude.exe');

function l3AcquireLock() {
  try {
    fs.mkdirSync(L3_LOCK_DIR);
    return true;
  } catch (e) {
    if (e && e.code === 'EEXIST') {
      try {
        const age = Date.now() - fs.statSync(L3_LOCK_DIR).mtimeMs;
        if (age > L3_LOCK_STALE_MS) {
          fs.rmdirSync(L3_LOCK_DIR);
          fs.mkdirSync(L3_LOCK_DIR);
          return true;
        }
      } catch (_) { /* lost a race — treat as not acquired */ }
    }
    return false;
  }
}

function l3CooldownActive() {
  try {
    const raw = fs.readFileSync(L3_LAST_RUN, 'utf8');
    const obj = JSON.parse(raw.charCodeAt(0) === 0xFEFF ? raw.slice(1) : raw);
    const last = obj && Number(obj.ts);
    if (!last || Number.isNaN(last)) return false;
    return (Date.now() - last) < L3_COOLDOWN_MS;
  } catch (_) {
    return false; // no prior run -> not cooling down
  }
}

function maybeSpawnL3(cwd) {
  // Defense-in-depth: run() already returns at line 1 if this is set.
  if (process.env.CPP_L3_CHILD === '1') return;
  if (!fs.existsSync(CLAUDE_EXE)) return; // no headless binary -> no-op

  // Scoped child permissions (user-authorized: scoped, NOT blanket bypass).
  // The headless child runs with a read-only allow-list (Read/Glob/Grep);
  // all mutation tools are denied at the permission layer, enforcing the
  // "READ + PROPOSE ONLY" pillar so the detached agent can never alter
  // rules/skills. No --dangerously-skip-permissions.
  const childSettings = path.join(os.homedir(), '.claude', 'skills',
    'claude-power-pack', 'modules', 'harness', 'l3-child-settings.json');
  if (!fs.existsSync(childSettings)) return; // no scoped policy -> no-op

  // (a) single-flight FIRST, so (b) cooldown read+write is atomic (gap #8).
  if (!l3AcquireLock()) return;
  let spawned = false;
  try {
    if (l3CooldownActive()) return; // released in finally (!spawned)

    // Record the run ts BEFORE spawning, inside the held lock — this is the
    // authoritative 60-min throttle even though the lock is best-effort.
    const writeStamp = resolveAtomicWriteJson();
    const stamp = { ts: Date.now(), pid: process.pid, cwd };
    if (writeStamp) writeStamp(L3_LAST_RUN, stamp);
    else {
      const tmp = L3_LAST_RUN + '.tmp.' + process.pid;
      fs.writeFileSync(tmp, JSON.stringify(stamp, null, 2));
      fs.renameSync(tmp, L3_LAST_RUN);
    }

    fs.mkdirSync(L3_PROPOSAL_DIR, { recursive: true });
    const safeTs = new Date().toISOString().replace(/[:.]/g, '-');
    const outPath = path.join(L3_PROPOSAL_DIR, safeTs + '.md');
    const fd = fs.openSync(outPath, 'w');

    // Verified invocation (tools/test_l3_intent.js 12/12): skill-scoped
    // `/cpp-compound` does NOT resolve for a Node-spawned child — only for
    // a direct shell-child of a live session. So invoke `claude -p` with a
    // DIRECT PROMPT pointing at the canonical pipeline spec
    // (compound-learnings SKILL.md) run in dry-run over the target corpus.
    // Parent-session markers are scrubbed (a child inheriting CLAUDECODE=1
    // is treated as nested and disables command/skill resolution).
    // Forward-slash paths: claude.exe's --add-dir/--settings arg parser
    // mishandles backslash argv (no shell).
    const fwd = p => p.replace(/\\/g, '/');
    const ppRepo = fwd(path.join(os.homedir(), '.claude', 'skills',
      'claude-power-pack'));
    const skillSpec = fwd(path.join(os.homedir(), '.claude', 'skills',
      'compound-learnings', 'SKILL.md'));
    const childEnv = Object.assign({}, process.env,
      { CPP_L3_CHILD: '1' });
    for (const k of Object.keys(childEnv)) {
      if (k === 'CLAUDECODE' || k.startsWith('CLAUDE_CODE_')
        || k === 'CLAUDE_PROJECT_DIR') delete childEnv[k];
    }
    const prompt = 'You are running the Compound Learnings pipeline in '
      + 'DRY-RUN mode (analysis only — do NOT write, edit or create any '
      + 'file, advance any cursor, or delete any marker). Read the '
      + 'canonical 8-step pipeline spec at ' + skillSpec + ' and follow '
      + 'it. Corpus: glob `' + fwd(cwd) + '/.claude/cache/learnings/'
      + '*.md` (fallback `' + fwd(cwd) + '/memory/sessions/session_*.md` '
      + 'header-filtered), read each, extract patterns from '
      + '"## Patterns" / "## What Worked" / "## What Failed" / '
      + '"**Takeaway:**" sections, consolidate, apply signal thresholds '
      + '(3+ = strong), and emit a markdown "## Compound Learnings — '
      + 'Dry Run Report" with a pattern frequency table and per-pattern '
      + 'proposal blocks. Output ONLY the report markdown.';
    const { spawn } = require('child_process');
    const child = spawn(
      CLAUDE_EXE,
      ['-p', '--output-format', 'text', '--no-session-persistence',
        '--add-dir', ppRepo, '--settings', fwd(childSettings), prompt],
      {
        cwd,
        detached: true,
        env: childEnv,
        stdio: ['ignore', fd, fd],
        windowsHide: true,
      }
    );
    child.unref();
    try { fs.closeSync(fd); } catch (_) { /* child holds its own handle */ }
    spawned = true;
    // Intentionally do NOT rmdir L3_LOCK_DIR here (gap #4): the child is
    // detached + running. The 10-min stale window auto-recovers it; the
    // 60-min cooldown above is the real throttle.
    return;
  } catch (_) {
    // Fail-open: never break SessionEnd.
  } finally {
    // Release the lock only if NO child was spawned (cooldown bail or
    // pre-spawn error) so the next eligible session is not blocked for the
    // 10-min stale window. On a successful spawn the lock is deliberately
    // held and recovered by the stale window (gap #4).
    if (!spawned) {
      try { fs.rmdirSync(L3_LOCK_DIR); } catch (_) { /* noop */ }
    }
  }
}

function run(data) {
  // L3 recursion kill (gap #1): a detached `claude` child spawned by L3
  // inherits CPP_L3_CHILD=1. This MUST be the first statement in run() —
  // before any SessionEnd marker pass — so the child can never re-enter
  // the sentinel and re-spawn. Bulletproof regardless of which hook events
  // the headless child emits.
  if (process.env.CPP_L3_CHILD === '1') return { continue: true };
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
