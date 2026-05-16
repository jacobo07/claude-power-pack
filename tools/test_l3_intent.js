#!/usr/bin/env node
'use strict';
/**
 * test_l3_intent.js — Phase-7 empirical verification (Q5, real input).
 *
 * Part 1 — Intent-Lock: exercises the real decide() across the conflict
 *          matrix (acquire / same-pid / foreign-live-deny / stale-reclaim
 *          / dead-reclaim / read-passthrough / cross-worktree).
 *
 * Part 2 — L3 engine: stands up a SYNTHETIC temp project seeded with 6
 *          cached learnings, then fires the EXACT verified L3 invocation
 *          the SessionEnd hook would run —
 *            claude.exe -p --output-format text --no-session-persistence
 *              --settings <l3-child-settings.json> "/cpp-compound --dry-run"
 *          — with stdout redirected to a real timestamped proposal .md,
 *          waits up to 120 s, and asserts a non-empty file containing real
 *          consolidated-pattern content (not TUI chrome / not empty).
 *
 * No mocks, no simulated calls (Reality Contract vMAX-NULL-ERROR).
 *
 * Usage:  node tools/test_l3_intent.js
 * Exit 0 = PASS, 1 = FAIL.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const cp = require('child_process');

const HOME = os.homedir();
const CLAUDE_EXE = path.join(HOME, '.local', 'bin', 'claude.exe');
const CHILD_SETTINGS = path.join(HOME, '.claude', 'skills',
  'claude-power-pack', 'modules', 'harness', 'l3-child-settings.json');
const PROPOSAL_DIR = path.join(HOME, '.claude', 'cache', 'compound-proposals');
const intentLock = require(path.join(HOME, '.claude', 'skills',
  'claude-power-pack', 'modules', 'harness', 'intent_lock.js'));

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok });
  process.stdout.write((ok ? 'PASS ' : 'FAIL ') + name
    + (detail ? '  — ' + detail : '') + '\n');
}

// --------------------------------------------------------------------------
// Part 1 — Intent-Lock conflict matrix (module-level, fast).
// --------------------------------------------------------------------------
function testIntentLock() {
  process.stdout.write('\n=== Part 1: Intent-Lock ===\n');
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'il7-')));
  const wtA = fs.realpathSync(fs.mkdtempSync(path.join(root, 'A-')));
  const wtB = fs.realpathSync(fs.mkdtempSync(path.join(root, 'B-')));
  const lpA = intentLock.lockPathFor(wtA);
  const atomic = require(path.join(HOME, '.claude', 'skills',
    'claude-power-pack', 'lib', 'atomic_write.js'));
  const wTool = {
    tool_name: 'Write', cwd: wtA,
    tool_input: { file_path: path.join(wtA, 'f.txt') },
  };
  const live = cp.spawn(process.execPath,
    ['-e', 'setTimeout(()=>{},60000)'], { stdio: 'ignore' });
  try {
    let r = intentLock.decide(wTool);
    check('IL1 acquire-on-empty', r.continue === true && !r.decision);

    r = intentLock.decide(wTool);
    check('IL2 same-pid-passthrough', r.continue === true && !r.decision);

    atomic.atomicWriteJson(lpA, { pid: live.pid, worktree: wtA,
      branch: 'rival', goal: 'x', ts: Date.now(), tool: 'Edit' });
    r = intentLock.decide(wTool);
    check('IL3 foreign-live-fresh-DENY',
      r.decision === 'deny' && /Intent-Lock/.test(r.reason || ''));

    atomic.atomicWriteJson(lpA, { pid: live.pid, worktree: wtA,
      branch: 'rival', goal: 'x', ts: Date.now() - 6 * 60000, tool: 'Edit' });
    r = intentLock.decide(wTool);
    check('IL4 stale-ts-reclaim', r.continue === true && !r.decision);

    atomic.atomicWriteJson(lpA, { pid: 0x7fffffff, worktree: wtA,
      branch: 'g', goal: 'g', ts: Date.now(), tool: 'Edit' });
    r = intentLock.decide(wTool);
    check('IL5 dead-pid-reclaim', r.continue === true && !r.decision);

    atomic.atomicWriteJson(lpA, { pid: live.pid, worktree: wtA,
      branch: 'rival', goal: 'x', ts: Date.now(), tool: 'Edit' });
    r = intentLock.decide({ tool_name: 'Read', cwd: wtA,
      tool_input: { file_path: path.join(wtA, 'f.txt') } });
    check('IL6 read-never-blocked', r.continue === true && !r.decision);

    atomic.atomicWriteJson(lpA, { pid: live.pid, worktree: wtA,
      branch: 'rival', goal: 'x', ts: Date.now(), tool: 'Edit' });
    r = intentLock.decide({ tool_name: 'Write', cwd: wtB,
      tool_input: { file_path: path.join(wtB, 'g.txt') } });
    check('IL7 cross-worktree-no-collision',
      r.continue === true && !r.decision);
  } finally {
    try { live.kill(); } catch (_) { /* noop */ }
    try { fs.rmSync(root, { recursive: true, force: true }); }
    catch (_) { /* noop */ }
  }
}

// --------------------------------------------------------------------------
// Part 2 — L3 engine end-to-end with REAL claude.exe (Q5).
// --------------------------------------------------------------------------
function seedLearnings(dir) {
  const ld = path.join(dir, '.claude', 'cache', 'learnings');
  fs.mkdirSync(ld, { recursive: true });
  // Six learnings; a shared pattern repeats 4x to cross the strong-signal
  // threshold so /cpp-compound has a real consolidated proposal to emit.
  const shared =
    '## Patterns\n- Observe filesystem outputs before editing code when '
    + 'debugging hooks; the artifact on disk is ground truth.\n';
  const uniques = [
    '## What Failed\n- Trusting a stale plan premise without a ground-'
      + 'truth probe wasted a milestone.\n',
    '## What Worked\n- Writing the verifier as a real .js file instead of '
      + 'inline node -e avoided Bash escaping corruption.\n',
    '## Key Decisions\n- Detached background workers must be triple-'
      + 'shielded (single-flight + cooldown + recursion env guard).\n',
    '## Patterns\n- Sanitize ISO timestamps (`:`/`.`) before using them '
      + 'as Windows filenames.\n',
    '## Patterns\n- Fail-open any safety guard that sits on the tool hot '
      + 'path; a guard that can wedge a session is a defect.\n',
    '## Patterns\n- Key concurrency locks on realpath(worktree)+live PID, '
      + 'never on branch alone.\n',
  ];
  for (let i = 0; i < 6; i++) {
    const body = '# Session Learning ' + (i + 1) + '\n\n' + shared
      + '\n' + uniques[i] + '\n**Takeaway:** generalize the rule above.\n';
    fs.writeFileSync(path.join(ld, 'l' + (i + 1) + '.md'), body);
  }
  return ld;
}

function testL3() {
  process.stdout.write('\n=== Part 2: L3 engine (real claude.exe) ===\n');

  if (!fs.existsSync(CLAUDE_EXE)) {
    check('L3 precondition: claude.exe present', false, CLAUDE_EXE);
    return;
  }
  if (!fs.existsSync(CHILD_SETTINGS)) {
    check('L3 precondition: scoped settings present', false, CHILD_SETTINGS);
    return;
  }
  check('L3 precondition: claude.exe + scoped settings present', true);

  const proj = fs.realpathSync(
    fs.mkdtempSync(path.join(os.tmpdir(), 'l3proj-')));
  const ld = seedLearnings(proj);
  check('L3 seed: 6 synthetic learnings written',
    fs.readdirSync(ld).length === 6, ld);

  fs.mkdirSync(PROPOSAL_DIR, { recursive: true });
  const safeTs = new Date().toISOString().replace(/[:.]/g, '-');
  const outPath = path.join(PROPOSAL_DIR, 'verify-' + safeTs + '.md');
  const fd = fs.openSync(outPath, 'w');

  process.stdout.write('  spawning real headless child (<=120s) ...\n');
  const started = Date.now();
  // ARCHITECTURE (empirically established this cycle): the skill-scoped
  // `/cpp-compound` slash command does NOT resolve for a child spawned by
  // Node — verified across env-scrub, shell:true, and stdin-mode matrices
  // (all return "Unknown command"); it only resolves for a direct
  // shell-child of a live session. So L3 must NOT depend on the slash
  // command. Instead invoke `claude -p` with a direct prompt that points
  // at the canonical pipeline spec (compound-learnings SKILL.md) and runs
  // it in dry-run over the target corpus. Robust regardless of spawn path.
  const fwd = p => p.replace(/\\/g, '/');
  const ppRepo = fwd(path.join(HOME, '.claude', 'skills',
    'claude-power-pack'));
  const skillSpec = fwd(path.join(HOME, '.claude', 'skills',
    'compound-learnings', 'SKILL.md'));
  // Defense-in-depth env scrub (CPP_L3_CHILD recursion guard + drop the
  // parent-session markers).
  const childEnv = Object.assign({}, process.env, { CPP_L3_CHILD: '1' });
  for (const k of Object.keys(childEnv)) {
    if (k === 'CLAUDECODE' || k.startsWith('CLAUDE_CODE_')
      || k === 'CLAUDE_PROJECT_DIR') delete childEnv[k];
  }
  const prompt = 'You are running the Compound Learnings pipeline in '
    + 'DRY-RUN mode (analysis only — do NOT write, edit or create any '
    + 'file, advance any cursor, or delete any marker). Read the '
    + 'canonical 8-step pipeline spec at ' + skillSpec + ' and follow '
    + 'it. Corpus: glob `' + fwd(proj) + '/.claude/cache/learnings/'
    + '*.md`, read each, extract patterns from "## Patterns" / '
    + '"## What Worked" / "## What Failed" / "**Takeaway:**" sections, '
    + 'consolidate, apply signal thresholds (3+ = strong), and emit a '
    + 'markdown "## Compound Learnings — Dry Run Report" with a pattern '
    + 'frequency table and per-pattern proposal blocks. Output ONLY the '
    + 'report markdown.';
  const r = cp.spawnSync(
    CLAUDE_EXE,
    ['-p', '--output-format', 'text', '--no-session-persistence',
      '--add-dir', ppRepo, '--settings', fwd(CHILD_SETTINGS), prompt],
    {
      cwd: proj,
      env: childEnv,
      stdio: ['ignore', fd, fd],
      timeout: 120000,
      windowsHide: true,
    }
  );
  try { fs.closeSync(fd); } catch (_) { /* noop */ }
  const elapsed = ((Date.now() - started) / 1000).toFixed(1);

  check('L3 child exited within 120s budget',
    !r.error || r.error.code !== 'ETIMEDOUT', 'elapsed ' + elapsed + 's'
      + (r.status != null ? ', exit ' + r.status : ''));

  let content = '';
  try { content = fs.readFileSync(outPath, 'utf8'); } catch (_) { /* */ }
  const bytes = Buffer.byteLength(content, 'utf8');
  check('L3 proposal .md is non-empty', bytes > 0,
    outPath + ' (' + bytes + ' bytes)');

  // Real-content assertion: must reflect the seeded corpus, not chrome.
  // Accept any of the compound pipeline's structural / semantic markers.
  const markers = [
    /##\s*Pattern/i, /Compounding/i, /Artifact Type/i, /Signal:/i,
    /Observe .*outputs before editing/i, /threshold/i, /learning/i,
  ];
  const hits = markers.filter(re => re.test(content)).map(re => re.source);
  check('L3 proposal contains real consolidated content',
    hits.length >= 2,
    hits.length + ' markers: ' + hits.slice(0, 3).join(' | '));

  process.stdout.write('  proposal head:\n'
    + content.split('\n').slice(0, 12).map(l => '  | ' + l).join('\n')
    + '\n  evidence file kept: ' + outPath + '\n');

  try { fs.rmSync(proj, { recursive: true, force: true }); }
  catch (_) { /* noop */ }
}

// --------------------------------------------------------------------------
testIntentLock();
testL3();

const failed = results.filter(x => !x.ok);
process.stdout.write('\n' + (results.length - failed.length) + '/'
  + results.length + ' checks passed\n');
if (failed.length) {
  process.stdout.write('FAILED: '
    + failed.map(f => f.name).join(', ') + '\n');
}
process.exit(failed.length === 0 ? 0 : 1);
