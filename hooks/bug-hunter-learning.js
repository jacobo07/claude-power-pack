#!/usr/bin/env node
/**
 * bug-hunter-learning.js -- PostToolUse hook (Bash matcher).
 *
 * Detects exit-code transitions from non-zero to 0 on test runners
 * (`mix test`, `npm test`, `npm run test`, `pnpm test`, `yarn test`)
 * and emits a Learning Fragment to the InfinityOps Knowledge Vault
 * under `knowledge_vault/02_Doctrine/LEARNINGS/`.
 *
 * The fragment shape is binding per
 * `InfinityOps/02_Knowledge_Engine/Departments/DIS_Engineering/STANDARDS.md`
 * Gate 3 and matches the contract in `LEARNING_FLOW.ex`.
 *
 * State persistence:
 *   ~/.claude/state/test-status-<repo-hash>.json
 *
 * Triggers (output to stderr; hook always exits 0 -- this is informational,
 * never a blocker):
 *   [bug-hunter-learning] fail->pass detected: <runner> <repo>; fragment at <path>
 *
 * Scope guard: only emits when cwd is inside InfinityOps OR a registered
 * Holding sub-entity (per knowledge_vault/02_Knowledge_Engine/Canonical_Entity_Registry/*.yml).
 *
 * Authored: MC-IO-700.3, 2026-04-26.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');
const { execSync } = require('child_process');

const STATE_DIR = path.join(os.homedir(), '.claude', 'state');
const HOLDING_ROOT_HINT_FILES = ['knowledge_vault/02_Doctrine/INFINITYOPS_BASELINE_STANDARD.md'];
const VAULT_LEARNINGS_REL = 'knowledge_vault/02_Doctrine/LEARNINGS';
const TEST_RUNNER_REGEX = /^(?:.*&&\s*)?(mix\s+test|npm\s+(?:run\s+)?test|pnpm\s+test|yarn\s+test)\b/;

// 2026-09-16 -- STDIN DEADLOCK FIX. This was `fs.readFileSync(0, 'utf8')`,
// which BLOCKS THE EVENT LOOP: if the pipe never closes the process parks at
// zero CPU forever and no in-process watchdog can save it, because no timer is
// ever scheduled. The harness's per-hook budget kills the shell WRAPPER; a
// timeout kills the direct child only, and the survivor holds the inherited
// stdout pipe. bfb40a1 has the live measurement.
const { readStdinRaw, armHardExit } = require('./hook-utils');

const STDIN_BUDGET_MS = 2000;
const HARD_EXIT = armHardExit(STDIN_BUDGET_MS + 3000);

async function readStdinJson() {
  const { raw } = await readStdinRaw(STDIN_BUDGET_MS);
  clearTimeout(HARD_EXIT);
  try {
    // Unreadable and empty both become {} exactly as the old catch did. Safe
    // here because main's next step needs a tool_name and a command to do
    // anything at all: an advisory that cannot read its event stays silent,
    // which is the same silence as before.
    return JSON.parse(raw || '{}');
  } catch (_) {
    return {};
  }
}

function emit(msg) {
  if (msg) process.stderr.write(`[bug-hunter-learning] ${msg}\n`);
  process.exit(0);
}

function detectRunner(cmd) {
  if (!cmd || typeof cmd !== 'string') return null;
  const m = cmd.match(TEST_RUNNER_REGEX);
  if (!m) return null;
  if (m[1].startsWith('mix')) return 'mix';
  return 'npm'; // pnpm / yarn / npm all map to :npm in LEARNING_FLOW.ex contract
}

function findRepoRoot(startDir) {
  let cur = path.resolve(startDir || process.cwd());
  for (;;) {
    if (fs.existsSync(path.join(cur, '.git'))) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

// Find InfinityOps holding root by walking up from a sub-entity's repo root.
// Returns null if not inside the holding scope.
function findHoldingRoot(startDir) {
  let cur = path.resolve(startDir || process.cwd());
  for (;;) {
    if (HOLDING_ROOT_HINT_FILES.every((rel) => fs.existsSync(path.join(cur, rel)))) {
      return cur;
    }
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

function repoHash(repoPath) {
  return crypto.createHash('sha1').update(repoPath).digest('hex').slice(0, 12);
}

function readState(repoPath) {
  const f = path.join(STATE_DIR, `test-status-${repoHash(repoPath)}.json`);
  try {
    return JSON.parse(fs.readFileSync(f, 'utf8'));
  } catch (_) {
    return null;
  }
}

function writeState(repoPath, runner, exitCode) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
  } catch (_) {}
  const f = path.join(STATE_DIR, `test-status-${repoHash(repoPath)}.json`);
  const payload = {
    repo_path: repoPath,
    last_runner: runner,
    last_exit_code: exitCode,
    last_run_at: new Date().toISOString(),
  };
  try {
    fs.writeFileSync(f, JSON.stringify(payload, null, 2));
  } catch (_) {
    // Non-fatal; state persistence best-effort.
  }
}

function repoBasename(repoPath) {
  return path.basename(repoPath);
}

function gitDiffFilesBetween(repoPath, fromIso, toIso) {
  // Best-effort: use the index of changed files since the last fail run.
  // We don't have commit SHAs; we infer "files modified between fail and pass"
  // from `git status --porcelain` of currently-modified working-tree files,
  // since the user's edits to fix the fail are typically still uncommitted
  // when the next test passes.
  try {
    const out = execSync('git status --porcelain', {
      cwd: repoPath,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 5000,
      windowsHide: true,
    });
    return out
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.replace(/^.{0,3}/, '').trim())
      .filter(Boolean);
  } catch (_) {
    return [];
  }
}

function makeSlug(repoName, runner) {
  const ts = new Date()
    .toISOString()
    .replace(/[^0-9TZ]/g, '')
    .slice(0, 13);
  return `${repoName}-${runner}-${ts}`.toLowerCase().replace(/[^a-z0-9-]/g, '-');
}

function renderMarkdown(fragment) {
  const filesList = fragment.fix_files.map((f) => `  - \`${f}\``).join('\n');
  return [
    '---',
    'department: DIS_Engineering',
    `runner: ${fragment.runner}`,
    `repo: ${fragment.repo}`,
    `test_name: ${fragment.test_name}`,
    `invariant: ${fragment.invariant}`,
    `detected_at: ${fragment.detected_at}`,
    `fix_files_count: ${fragment.fix_files.length}`,
    '---',
    '',
    `# DIS Learning Fragment -- ${fragment.repo}`,
    '',
    `Test transitioned **fail -> pass** under the \`${fragment.runner}\` runner.`,
    '',
    `**Test:** \`${fragment.test_name}\``,
    '',
    '**Files modified between the prior fail and the current pass:**',
    filesList || '  - (none in working tree -- fix may be already committed)',
    '',
    '## Diff summary',
    '',
    fragment.fix_diff_summary || '(no summary captured by hook -- consult git log/diff)',
    '',
    '## v6000 invariant classification',
    '',
    `\`${fragment.invariant}\` -- see \`~/.claude/skills/claude-power-pack/modules/bug-hunter/baseline-v6000.md\``,
    'for the invariant definition. Next /bug-hunt run in this repo loads this fragment as a prior.',
    '',
    '## Authored by',
    '',
    `\`~/.claude/hooks/bug-hunter-learning.js\` (PostToolUse / Bash matcher) on fail->pass transition`,
    'detected via per-repo state file at `~/.claude/state/test-status-<hash>.json`.',
    '',
  ].join('\n');
}

function classifyInvariantFromFiles(files) {
  // Heuristic mapping: filename hints which v6000 invariant the fix maps to.
  // Returns one of INV1/INV2/INV3/INV4 or 'unclassified'.
  const joined = files.join(' ').toLowerCase();
  if (/(serializer|repo\.|migration|changeset|schema|persist|writefile|fwrite|encode|json\.dump)/.test(joined)) {
    return 'INV1';
  }
  if (/(deploy|release|reload|hot-?swap|require\.cache|import_lib|version|lock)/.test(joined)) {
    return 'INV2';
  }
  if (/(admin|debug|rcon|sudo|controller.*admin|router.*admin)/.test(joined)) {
    return 'INV3';
  }
  if (/(supervisor|spawn|task\.async|gen_?server|tokio|asyncio|promise|callback|worker|queue)/.test(joined)) {
    return 'INV4';
  }
  return 'unclassified';
}

function bestEffortTestName(cmd, runner) {
  // Try to extract a focused test name from the command, e.g.
  // `mix test test/foo_test.exs:42` -> `test/foo_test.exs:42`.
  const m = cmd.match(/(mix\s+test|npm\s+(?:run\s+)?test|pnpm\s+test|yarn\s+test)\s+(.+)/);
  if (m && m[2]) return m[2].trim();
  return runner === 'mix' ? '<full mix test suite>' : '<full npm test suite>';
}

// Async because readStdinJson() is now a Promise. Everything below is UNCHANGED.
async function main() {
  const input = await readStdinJson();

  // Only react to PostToolUse on Bash.
  if (input.tool_name !== 'Bash') return emit(null);

  const cmd = (input.tool_input && input.tool_input.command) || '';
  const runner = detectRunner(cmd);
  if (!runner) return emit(null);

  const cwd = (input.tool_input && input.tool_input.cwd) || process.cwd();
  const repoPath = findRepoRoot(cwd);
  if (!repoPath) return emit(null);

  // Determine current exit code: PostToolUse provides tool_response.success
  // (boolean) and may include exitCode. Best-effort.
  const tr = input.tool_response || {};
  const success = tr.success === true || tr.exitCode === 0;
  const currentExitCode = tr.exitCode != null ? tr.exitCode : (success ? 0 : 1);

  const prev = readState(repoPath);
  // Always update state.
  writeState(repoPath, runner, currentExitCode);

  // Only emit on fail->pass transition.
  if (!prev) return emit(`first ${runner} run in ${repoBasename(repoPath)}; baseline saved (exit ${currentExitCode}).`);
  if (prev.last_exit_code === 0 || currentExitCode !== 0) {
    return emit(`no transition (prev=${prev.last_exit_code}, curr=${currentExitCode}); state updated.`);
  }

  // We have a fail->pass transition. Find Holding root.
  const holdingRoot = findHoldingRoot(repoPath);
  if (!holdingRoot) {
    // Out of Holding scope; do nothing (don't pollute non-Holding repos).
    return emit('fail->pass detected but cwd is not inside InfinityOps Holding scope; skipping fragment emission.');
  }

  const repoName = repoBasename(repoPath);
  const fragment = {
    runner,
    repo: repoName,
    test_name: bestEffortTestName(cmd, runner),
    fix_files: gitDiffFilesBetween(repoPath, prev.last_run_at, new Date().toISOString()),
    fix_diff_summary: `${runner} test transitioned fail->pass; working-tree files captured below.`,
    detected_at: new Date().toISOString(),
    invariant: 'unclassified',
  };
  fragment.invariant = classifyInvariantFromFiles(fragment.fix_files);

  const slug = makeSlug(repoName, runner);
  const targetDir = path.join(holdingRoot, VAULT_LEARNINGS_REL);
  try {
    fs.mkdirSync(targetDir, { recursive: true });
  } catch (_) {}
  const filename = `${fragment.detected_at.replace(/[:.]/g, '-')}_dis_${slug}.md`;
  const targetPath = path.join(targetDir, filename);

  try {
    fs.writeFileSync(targetPath, renderMarkdown(fragment));
    return emit(`fail->pass detected: ${runner} ${repoName}; fragment at ${path.relative(holdingRoot, targetPath)} (invariant=${fragment.invariant}, files=${fragment.fix_files.length})`);
  } catch (err) {
    return emit(`fail->pass detected but write failed: ${err.message}`);
  }
}

// .catch is mandatory now that main is async: a rejection would otherwise
// escape unhandled, and a process that merely logs one stays ALIVE holding the
// inherited stdout pipe -- the stall this migration removes. emit() exits.
main().catch((err) => emit(`unhandled: ${err && err.message ? err.message : 'unknown'}`));
