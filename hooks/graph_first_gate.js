#!/usr/bin/env node
/**
 * graph_first_gate.js — GK-12 Graph-First Enforcement (honest level-2).
 *
 * Fires on PreToolUse for exploration operations (Grep / Glob / a Bash or
 * PowerShell shell-search). Its ONLY action is to SURFACE an advisory: this
 * repo has a knowledge graph; a coordinate query may resolve the need in one
 * lookup before you grep the filesystem. It is the "navigate before you
 * explore" nudge made visible — exactly what GK-12 registers as its strength:
 *
 *   "detect / project / warn plus a route-compiler redirect — NOT a physical
 *    block. No in-process hook can stop a model mid-turn from choosing to grep."
 *
 * Honest contract (GK-12 / CO-10 ladder):
 *   - Level-2 (detect + redirect). It NEVER denies, NEVER blocks, NEVER exits 2.
 *   - Fail-open ABSOLUTE: any error, missing store, or unparseable input ->
 *     emit `{}` and exit 0. A gate that blocks work is worse than no gate.
 *   - Cheap: reads ONE small JSON file (the promoted global store, ~100 KB),
 *     never a per-repo cache (those can be tens of thousands of nodes).
 *   - Throttled: at most one advisory per (session, repo) per cooldown, so it
 *     nudges once, not on every grep (token discipline).
 *
 * Dual-mode: exports { run } for in-process EVENT_MAP use + unit tests, and
 * runs as a standalone stdin->stdout CLI child when invoked directly (the
 * shell-free CHAIN_MAP path the dispatcher uses on Windows).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const STATE_DIR = path.join(os.homedir(), '.claude', 'state', 'graphify');
const GLOBAL_FILE = path.join(STATE_DIR, 'graphify_global.json');
const THROTTLE_MS = 15 * 60 * 1000; // one nudge per repo per session per 15 min

// Shell tokens that mean "search / list the filesystem" — a Bash/PowerShell
// command containing one of these is an exploration op for GK-12 purposes.
const SHELL_EXPLORE = /(^|[\s;|&(])(grep|egrep|rg|ag|ack|find|ls|dir|cat|type|Get-ChildItem|gci|Select-String|sls|Get-Content|gc)([\s;|&)]|$)/;

// Tools that are ALWAYS an exploration op regardless of arguments.
const EXPLORE_TOOLS = new Set(['Grep', 'Glob']);

function isExploration(toolName, toolInput) {
  if (EXPLORE_TOOLS.has(toolName)) return true;
  if (toolName === 'Bash' || toolName === 'PowerShell') {
    const cmd = toolInput && typeof toolInput.command === 'string' ? toolInput.command : '';
    return SHELL_EXPLORE.test(cmd);
  }
  return false;
}

function normPath(p) {
  return String(p || '').replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
}

// Locate the current repo inside the global store by matching cwd against each
// indexed repo's stored (resolved) path. Returns { rid, rpLen, nodeCount } or null.
function repoEntryFor(cwd, store) {
  const nc = normPath(cwd);
  if (!nc) return null;
  const repos = (store && store.repos) || {};
  let best = null;
  for (const rid of Object.keys(repos)) {
    const rp = normPath(repos[rid] && repos[rid].path);
    if (!rp) continue;
    // cwd is the repo root or a subdirectory of it.
    if (nc === rp || nc.startsWith(rp + '/')) {
      // Prefer the deepest (most specific) matching repo.
      if (!best || rp.length > best.rpLen) {
        best = { rid, rpLen: rp.length, nodeCount: repos[rid].node_count || 0 };
      }
    }
  }
  return best;
}

// Best-effort per-(session,repo) throttle. A miss (no marker / stale marker)
// returns false = "advise now" and stamps the marker. Any fs error fails OPEN
// toward advising once (never toward blocking) but must never throw.
function throttled(sessionId, repoKey) {
  try {
    const safe = String(sessionId || 'nosess').replace(/[^a-zA-Z0-9]+/g, '') || 'nosess';
    const rk = String(repoKey || 'norepo').replace(/[^a-zA-Z0-9]+/g, '').slice(0, 24) || 'norepo';
    const marker = path.join(STATE_DIR, `.gf_${safe}_${rk}`);
    try {
      const st = fs.statSync(marker);
      if (Date.now() - st.mtimeMs < THROTTLE_MS) return true; // recently nudged
    } catch (_) { /* no marker yet — fall through to stamp + advise */ }
    try {
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(marker, '');
    } catch (_) { /* marker write is best-effort; a miss just re-nudges later */ }
    return false;
  } catch (_) {
    return false; // never let the throttle suppress into a block-like failure
  }
}

function buildAdvisory(entry, globalCount, cwd) {
  const repoName = path.basename(String(cwd || '').replace(/[\\/]+$/, '')) || 'this repo';
  if (entry && entry.nodeCount) {
    return `Graph-First (GK-12, level-2 advisory — never blocks): the knowledge `
      + `graph already holds ${entry.nodeCount} coordinates for ${repoName} `
      + `(+${globalCount} cross-repo). Before exploring the filesystem, a `
      + `\`python modules/graphify/indexer.py --query --name <term>\` (or `
      + `--type hard_rule|decision|contract) may resolve this in one lookup. `
      + `Navigate the graph, not the files.`;
  }
  // Repo not yet indexed — honest about the residual (the un-navigated path).
  return `Graph-First (GK-12, level-2 advisory — never blocks): ${repoName} is `
    + `not in the knowledge graph yet (${globalCount} cross-repo coordinates `
    + `exist). \`python modules/graphify/indexer.py --repo "${String(cwd || '.')}"\` `
    + `would index it so future navigation resolves without exploration.`;
}

// --- Cross-project baseline injection --------------------------------------
//
// Until 2026-08-31 this hook read the promoted store and emitted `globalCount`
// -- a NUMBER. So what one project learned reached another project as a digit.
// The CEPS promoter (tools/ceps.py promote) now writes a real baseline; this
// reads it back, which is the half that closes the loop.
//
// Relevance is NECESSARY, never weighted (PR from feedback_constant_factors_
// rank_nothing: five of six scoring factors were per-item constants, so
// relevance 0.0 still cleared MANDATORY and 8 of 9 items activated). A pattern
// that does not match the command at hand emits NOTHING.
const PROMOTED_FILE = path.join(
  os.homedir(), '.claude', 'skills', 'claude-power-pack',
  'vault', 'ceps', 'promoted.jsonl'
);
const BASELINE_TOP_N = 3;

// A CEPS `subsystem` is `<transport>:<first token of the command>`, so half the
// live corpus is keyed on a NAVIGATION prefix (`bash:cd`) rather than on the
// failing tool -- the admission layer flags exactly this as identity_suspect.
// Matching on those keys would fire on every `cd`. Excluding them here is the
// producer's identity bug corrected on the read side, where it is cheap.
const NAV_TOKEN = new Set([
  'cd', 'ls', 'dir', 'echo', 'cat', 'type', 'pwd', 'set', 'export', 'env',
  'time', 'timeout', 'sudo', 'true', 'false', 'then', 'fi', 'do', 'done',
  'program', 'for', 'while', 'if', 'source', 'exec', 'nohup',
]);

function normToken(tok) {
  const base = String(tok || '').replace(/\\/g, '/').split('/').pop();
  return base.replace(/\.(exe|cmd|bat|ps1)$/i, '').toLowerCase();
}

// Programs the current command actually invokes: every token that is not a
// navigation word, a flag, or a path argument.
function programTokens(cmd) {
  const out = new Set();
  for (const seg of String(cmd || '').split(/[;|&]+|\s&&\s/)) {
    for (const raw of seg.trim().split(/\s+/)) {
      if (!raw || raw.startsWith('-')) continue;
      if (/^[A-Za-z_][\w.]*=/.test(raw)) continue; // VAR=value prefix
      const t = normToken(raw);
      if (!t || NAV_TOKEN.has(t)) continue;
      out.add(t);
      break; // first real program of this segment is the one that runs
    }
  }
  return out;
}

function loadPromoted() {
  try {
    if (!fs.existsSync(PROMOTED_FILE)) return [];
    return fs.readFileSync(PROMOTED_FILE, 'utf8')
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .map(l => { try { return JSON.parse(l); } catch (_) { return null; } })
      .filter(Boolean);
  } catch (_) {
    return []; // unreadable baseline -> silence, never an exception in a hook
  }
}

// A record is relevant iff a program in the current command appears among the
// record's own subsystems, once navigation prefixes are dropped from both.
function relevantPromotions(records, programs) {
  if (!programs || programs.size === 0) return [];
  const hits = [];
  for (const rec of records) {
    const keys = (rec.subsystems || [])
      .map(s => normToken(String(s).split(':').pop()))
      .filter(k => k && !NAV_TOKEN.has(k));
    if (keys.some(k => programs.has(k))) hits.push(rec);
  }
  // Most-travelled first: a pattern proven across more projects earns the slot.
  hits.sort((a, b) => (b.project_count || 0) - (a.project_count || 0));
  return hits.slice(0, BASELINE_TOP_N);
}

function buildBaselineAdvisory(records) {
  const lines = records.map(r =>
    `  - ${r.root_cause} (seen in ${r.project_count} projects) — `
    + `${r.prevention_rule || 'no rule recorded'}`);
  return `Cross-project baseline (advisory — never blocks): this estate has hit `
    + `the following in OTHER projects while running the same tooling. `
    + `Learned once, applied everywhere:\n${lines.join('\n')}`;
}

/**
 * run(input) — the hook body. `input` is the parsed PreToolUse JSON
 * ({ tool_name, tool_input, cwd, session_id, ... }). Returns the JSON object
 * the dispatcher merges. ALWAYS returns an object; NEVER throws.
 */
function run(input) {
  try {
    const data = input && typeof input === 'object' ? input : {};
    const toolName = data.tool_name || data.toolName || '';
    const toolInput = data.tool_input || data.toolInput || {};
    const cwd = data.cwd || data.workingDirectory || process.cwd();
    const sessionId = data.session_id || data.sessionId || '';

    // Baseline injection runs on ANY shell command, not just exploration: a
    // ModuleNotFoundError does not wait for you to grep. Checked first so an
    // ordinary `python x.py` -- never an exploration op -- still gets it.
    if (toolName === 'Bash' || toolName === 'PowerShell') {
      const programs = programTokens(toolInput && toolInput.command);
      const hits = relevantPromotions(loadPromoted(), programs);
      if (hits.length && !throttled(sessionId, 'xpb:' + [...programs].sort().join(','))) {
        return {
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            additionalContext: buildBaselineAdvisory(hits),
          },
        };
      }
    }

    if (!isExploration(toolName, toolInput)) return {};

    // Read ONLY the small promoted global store — never a per-repo cache.
    let store = {};
    try {
      if (fs.existsSync(GLOBAL_FILE)) {
        store = JSON.parse(fs.readFileSync(GLOBAL_FILE, 'utf8')) || {};
      }
    } catch (_) { store = {}; /* unreadable store -> advise as un-indexed */ }

    const globalCount = store.global_nodes ? Object.keys(store.global_nodes).length : 0;
    const entry = repoEntryFor(cwd, store);

    // Nothing to say if the graph is entirely empty (pre-first-index) — stay silent.
    if (globalCount === 0 && !(entry && entry.nodeCount)) return {};

    const repoKey = entry ? entry.rid : normPath(cwd);
    if (throttled(sessionId, repoKey)) return {};

    return {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: buildAdvisory(entry, globalCount, cwd),
      },
    };
  } catch (_) {
    return {}; // fail-open absolute — a detector must never break the tool
  }
}

module.exports = {
  run, isExploration, repoEntryFor, buildAdvisory,
  programTokens, relevantPromotions, loadPromoted, buildBaselineAdvisory,
};

// --- Standalone CLI (shell-free CHAIN_MAP child) --------------------------
if (require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => { raw += c; });
  process.stdin.on('end', () => {
    let data = {};
    try { data = JSON.parse(raw || '{}'); } catch (_) { data = {}; /* non-JSON stdin -> no-op */ }
    let out = {};
    try { out = run(data) || {}; } catch (_) { out = {}; /* fail-open */ }
    try { process.stdout.write(JSON.stringify(out)); } catch (_) { process.stdout.write('{}'); }
    process.exit(0); // NEVER exit 2 — GK-12 never blocks
  });
  process.stdin.on('error', () => { process.stdout.write('{}'); process.exit(0); });
}
