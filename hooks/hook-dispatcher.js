#!/usr/bin/env node
/**
 * Hook Dispatcher — bundle multiple Claude Code hooks into one Node process.
 *
 * Why: each entry in settings.json hooks[] spawns a fresh Node process
 *      (~300–800 ms cold on Windows). Chains of N small hooks pay N × that
 *      cost on every event. This dispatcher loads hook modules in-process,
 *      runs them sequentially or in parallel, and merges their JSON outputs
 *      into a single response — paying only one Node spawn for N hooks.
 *
 * Usage in settings.json:
 *   {
 *     "hooks": [{
 *       "type": "command",
 *       "command": "node \"~/.claude/hooks/hook-dispatcher.js\" --event=PreToolUse-default",
 *       "timeout": 15
 *     }]
 *   }
 *
 * Hook contract: each bundled hook must export `module.exports = { run }`,
 * where `run(input)` returns (or resolves to) the same JSON object the
 * standalone script would have written to stdout. The original CLI mode
 * (gated by `if (require.main === module)`) stays intact for backwards
 * compatibility — Lazarus shell autoresume + manual invocation keep working.
 *
 * Output merge rules:
 *   - decision: "deny" wins over "allow" (most restrictive).
 *   - additionalContext: concatenated with "\n\n" separator.
 *   - hookSpecificOutput: shallow-merged (later hooks override same keys).
 *   - All other top-level keys: last-writer wins.
 *
 * Errors in any single hook are logged to ~/.claude/logs/hook-dispatcher-errors.log
 * and the dispatcher continues — no single hook can break the chain.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const HOME = os.homedir();
const LOG_DIR = path.join(HOME, '.claude', 'logs');
const ERROR_LOG = path.join(LOG_DIR, 'hook-dispatcher-errors.log');

// --- Event registry ---
// Add new bundles as more hooks get refactored to export `run()`.
const EVENT_MAP = {
  'PreToolUse-default': [
    './session-init.js',
    './lazarus-heartbeat.js',
    '../skills/claude-power-pack/modules/harness/intent_lock.js',
  ],
  'PostToolUse-default': [
    './gsd-context-monitor.js',
    './session-logger.js',
    './dna-flywheel.js',
    './trace-emitter.js',
  ],
  'UserPromptSubmit-default': [
    './power-pack-reminder.js',
    './baseline-translator.js',
  ],
  // In-process (require-based) bundles only. The Stop event is handled by
  // CHAIN_MAP below instead: those hooks are heterogeneous (one is Python)
  // and not all export run(), so they run as sequential CHILD processes
  // spawned WITHOUT a shell (shell:false) — see runChain().
};

// --- Child-process chain registry (Windows fork-storm fix) ---------------
// Root cause this solves: registering N separate `type:"command"` hooks on
// ONE event makes Claude Code spawn N shell wrappers near-simultaneously.
// On Windows the shell is Git Bash; ≳3 concurrent msys2 forks collapse the
// mount-table init with `add_item("\??\C:\Program Files\Git","/") errno 1`
// (a fatal bash startup crash → the hooks never even run).
//
// Mitigation (durable): collapse the whole event into ONE dispatcher
// process; run each sub-hook here SEQUENTIALLY via spawnSync with
// shell:false, so NO bash.exe is ever spawned for a sub-hook. One event =
// one shell wrapper max (same as the already-stable Pre/PostToolUse path).
//
// `timeoutMs` is real milliseconds (Claude Code's per-hook `timeout` was
// authored inconsistently in settings.json; canonicalised here).
const NODE_EXE = process.execPath; // the very node.exe running this — Win path, no bash
// Portable Python fallback (gap 2 fix, audit 2026-05-19): the prior
// `C:/Users/User/AppData/Local/...` literal broke every host whose
// Windows username is not "User" and every POSIX host. Honest contract:
// derive from os.homedir() if a Windows-style Python install is present;
// otherwise fall back to the PATH-resolved `python3`/`python` so the
// hook fails at registration (settings_merger checks isfile) rather
// than silently at runtime. Explicit CLAUDE_PY_EXE always wins.
const PY_EXE = process.env.CLAUDE_PY_EXE || (function () {
  const winFallback = path.join(os.homedir(), 'AppData', 'Local',
    'Programs', 'Python', 'Python312', 'python.exe');
  try { fs.accessSync(winFallback, fs.constants.X_OK); return winFallback; }
  catch (_) { /* not present — defer to PATH-resolved interpreter */ }
  return process.platform === 'win32' ? 'python.exe' : 'python3';
})();

const CHAIN_MAP = {
  'Stop-chain': [
    { exe: NODE_EXE, script: './zero-issue-gate.js', timeoutMs: 60000, block: true },
    { exe: NODE_EXE, script: './kobiiclaw-autoresearch.js', timeoutMs: 30000 },
    { exe: NODE_EXE, script: './trace-flusher.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: './session-summary.js', timeoutMs: 20000 },
    { exe: NODE_EXE, script: './scaffold-auditor.js', timeoutMs: 15000, block: true },
    { exe: NODE_EXE, script: './lazarus-snapshot.js', timeoutMs: 10000 },
    { exe: PY_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/context-watchdog.py', timeoutMs: 6000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/ram-watchdog.js', timeoutMs: 6000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/ram-shield.js', timeoutMs: 6000 },
    { exe: NODE_EXE, script: './learning-sentinel.js', timeoutMs: 6000 },
    { exe: NODE_EXE, script: './vault-heartbeat.js', timeoutMs: 8000 },
  ],
  // PreToolUse fork-storm fix (2026-05-21) — user explicitly authorized.
  // Root cause: settings.json registered 7 standalone PreToolUse hooks on
  // matcher=Bash and 9 on matcher=Edit|Write|*. Each `type:"command"`
  // entry makes Claude Code spawn a fresh git-bash MSYS2 wrapper; ≳3
  // concurrent forks collapse the mount-table init with `add_item errno 1`
  // (env_git_bash_fork_storm.md). Drift evidence: the user's OWN memory
  // file warned "NUNCA re-expandir hooks en settings.json" — but Owner
  // chose to add them anyway over time, and the cumulative count crossed
  // the danger threshold. Mitigation: collapse all per-matcher PreToolUse
  // hooks into these chains; settings.json then registers ONE dispatcher
  // entry per matcher. Same shell:false spawnSync model the Stop-chain
  // has used since 2026-05-15 — proven fork-storm-safe in production.
  'PreToolUse-Bash-chain': [
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/process-sandbox.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/ovo-push-gate.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/skill-heat-map-advisor.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './quality-skill-gate.js', timeoutMs: 15000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/rtk-core/rtk-rewrite.js', timeoutMs: 10000 },
  ],
  'PreToolUse-Edit-chain': [
    { exe: NODE_EXE, script: './secret-scanner.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './quality-gate.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './anti-thrash.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './readonly-prompts-guard.js', timeoutMs: 3000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/skill-heat-map-advisor.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: '../skills/claude-power-pack/modules/zero-crash/hooks/zero-fiction-gate.js', timeoutMs: 5000 },
    { exe: NODE_EXE, script: './jobs-woz-gatekeeper.js', timeoutMs: 20000 },
  ],
  'PreToolUse-Read-chain': [
    { exe: NODE_EXE, script: './gatekeeper-semantic.js', timeoutMs: 3000 },
    { exe: NODE_EXE, script: './anti-thrash.js', timeoutMs: 5000 },
  ],
};

// Run a chain of sub-hooks as sequential, shell-free child processes.
// Returns { outputs:[parsedJSON], blocked:bool, blockStderr:string }.
function runChain(event, chain, rawStdin) {
  const outputs = [];
  let blocked = false;
  const blockStderr = [];
  for (const step of chain) {
    const abs = path.join(__dirname, step.script);
    if (!fs.existsSync(abs)) { logError(event, step.script, new Error('script missing')); continue; }
    if (!fs.existsSync(step.exe)) { logError(event, step.script, new Error('interpreter missing: ' + step.exe)); continue; }
    let r;
    try {
      r = spawnSync(step.exe, [abs], {
        input: rawStdin,
        timeout: step.timeoutMs,
        shell: false,            // <-- the fix: never route a sub-hook through bash
        windowsHide: true,
        encoding: 'utf8',
        maxBuffer: 8 * 1024 * 1024,
      });
    } catch (e) { logError(event, step.script, e); continue; }
    if (r.error) { logError(event, step.script, r.error); }
    if (r.stdout) {
      const s = r.stdout.trim();
      if (s) { try { outputs.push(JSON.parse(s)); } catch (_) { /* non-JSON stdout: ignored, like Claude Code */ } }
    }
    // Stop blocking contract: exit code 2 blocks the stop; stderr is shown.
    if (step.block && r.status === 2) {
      blocked = true;
      if (r.stderr) blockStderr.push(String(r.stderr).trim());
    } else if (r.status && r.status !== 0 && r.status !== 2) {
      logError(event, step.script, new Error('exit ' + r.status + (r.stderr ? ': ' + String(r.stderr).slice(0, 400) : '')));
    }
  }
  return { outputs, blocked, blockStderr: blockStderr.join('\n') };
}

// --- Helpers ---
function logError(event, modPath, err) {
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const line = `${new Date().toISOString()} [${event}] ${modPath} ${err && err.stack ? err.stack : String(err)}\n`;
    fs.appendFileSync(ERROR_LOG, line);
  } catch (_) { /* logging must not throw */ }
}

function parseArgs() {
  for (const a of process.argv.slice(2)) {
    if (a.startsWith('--event=')) return a.slice('--event='.length);
  }
  return null;
}

function loadHook(relativePath) {
  try {
    return require(path.join(__dirname, relativePath));
  } catch (e) {
    logError('LOAD', relativePath, e);
    // Visible signal (gap #5): a silently-dropped hook is a scaffold
    // illusion (Mistake #16). Surface load failures on stderr so a broken
    // cross-tree require (e.g. hooks -> skills/.../intent_lock.js) is
    // never invisible. stderr does not pollute the JSON stdout contract.
    try {
      process.stderr.write('[hook-dispatcher] LOAD FAILED ' + relativePath
        + ': ' + (e && e.message ? e.message : String(e)) + '\n');
    } catch (_) { /* logging must not throw */ }
    return null;
  }
}

// --- Event-family schema constants (BL-2026-05-24, Stop-schema veto fix) ----
// Root-level fields the harness accepts on EVERY event. `hookSpecificOutput`
// is also allowed at root but its inner shape is event-gated below.
const ROOT_ALLOWED = new Set([
  'continue', 'suppressOutput', 'stopReason', 'decision', 'reason',
  'systemMessage', 'terminalSequence', 'permissionDecision',
  'hookSpecificOutput',
]);
// Only these 4 events accept hookSpecificOutput.additionalContext.
// Stop, SessionStart, SessionEnd do NOT — text MUST go to systemMessage.
const EVENTS_HSO_ADDITIONAL_CONTEXT = new Set([
  'UserPromptSubmit', 'PostToolUse', 'PostToolBatch',
]);

function familyOf(eventName) {
  if (!eventName) return null;
  for (const fam of [
    'Stop', 'PreToolUse', 'PostToolBatch', 'PostToolUse',
    'UserPromptSubmit', 'SessionStart', 'SessionEnd',
  ]) {
    if (eventName.startsWith(fam)) return fam;
  }
  return null;
}

// Final schema gate: whitelist root keys per family, salvage stranded text
// into systemMessage so no child-hook drift can produce schema-invalid JSON.
// Same guarantee whether sub-hooks emit legacy or current shape.
function sanitizeForSchema(merged, family) {
  if (!merged || typeof merged !== 'object') return {};
  const clean = {};
  const stranded = [];

  for (const k of Object.keys(merged)) {
    if (!ROOT_ALLOWED.has(k)) {
      if (k === 'additionalContext' && typeof merged[k] === 'string' && merged[k].length > 0) {
        stranded.push(merged[k]);
      }
      continue;
    }
    clean[k] = merged[k];
  }

  if (clean.hookSpecificOutput && typeof clean.hookSpecificOutput === 'object') {
    const hso = clean.hookSpecificOutput;
    if (family === 'PreToolUse') {
      const kept = { hookEventName: 'PreToolUse' };
      if (typeof hso.permissionDecision === 'string') kept.permissionDecision = hso.permissionDecision;
      if (typeof hso.permissionDecisionReason === 'string') kept.permissionDecisionReason = hso.permissionDecisionReason;
      if (hso.updatedInput && typeof hso.updatedInput === 'object') kept.updatedInput = hso.updatedInput;
      clean.hookSpecificOutput = kept;
    } else if (EVENTS_HSO_ADDITIONAL_CONTEXT.has(family)) {
      const kept = { hookEventName: family };
      if (typeof hso.additionalContext === 'string' && hso.additionalContext.length > 0) {
        kept.additionalContext = hso.additionalContext;
      }
      clean.hookSpecificOutput = kept;
    } else {
      if (typeof hso.additionalContext === 'string' && hso.additionalContext.length > 0) {
        stranded.push(hso.additionalContext);
      }
      delete clean.hookSpecificOutput;
    }
  }

  if (clean.decision != null) {
    if (family === 'PreToolUse') {
      delete clean.decision; // PreToolUse uses hookSpecificOutput.permissionDecision
    } else if (clean.decision === 'deny') {
      clean.decision = 'block';
    } else if (clean.decision === 'allow') {
      clean.decision = 'approve';
    } else if (clean.decision !== 'approve' && clean.decision !== 'block') {
      delete clean.decision;
    }
  }

  if (stranded.length > 0) {
    const existing = typeof clean.systemMessage === 'string' && clean.systemMessage.length > 0
      ? [clean.systemMessage] : [];
    clean.systemMessage = [...existing, ...stranded].join('\n\n');
  }

  return clean;
}

function mergeOutputs(outputs, eventName) {
  const merged = {};
  const contexts = [];
  let decisionDeny = false;
  let decisionAllow = false;
  // Stop schema: `continue` defaults to true; any explicit `false` wins.
  let continueSeen = false;
  let continueFalse = false;

  for (const out of outputs) {
    if (!out || typeof out !== 'object') continue;

    if (out.decision === 'deny') decisionDeny = true;
    else if (out.decision === 'allow') decisionAllow = true;

    if (Object.prototype.hasOwnProperty.call(out, 'continue')) {
      continueSeen = true;
      if (out.continue === false) continueFalse = true;
    }

    if (typeof out.additionalContext === 'string' && out.additionalContext.length > 0) {
      contexts.push(out.additionalContext);
    }

    if (out.hookSpecificOutput && typeof out.hookSpecificOutput === 'object') {
      merged.hookSpecificOutput = { ...(merged.hookSpecificOutput || {}), ...out.hookSpecificOutput };
      // Pull additionalContext out of child hookSpecificOutput too so it can
      // be re-routed by sanitizeForSchema for non-PreToolUse families.
      if (typeof out.hookSpecificOutput.additionalContext === 'string'
          && out.hookSpecificOutput.additionalContext.length > 0) {
        contexts.push(out.hookSpecificOutput.additionalContext);
      }
    }

    for (const k of Object.keys(out)) {
      if (k === 'decision' || k === 'additionalContext' || k === 'hookSpecificOutput' || k === 'continue') continue;
      merged[k] = out[k];
    }
  }

  if (eventName && eventName.startsWith('PreToolUse')) {
    if (decisionDeny || decisionAllow) {
      merged.hookSpecificOutput = {
        hookEventName: 'PreToolUse',
        ...(merged.hookSpecificOutput || {}),
        permissionDecision: decisionDeny ? 'deny' : 'allow',
      };
    }
  } else {
    if (decisionDeny) merged.decision = 'deny';
    else if (decisionAllow) merged.decision = 'allow';
  }

  if (continueSeen) merged.continue = !continueFalse;

  if (contexts.length > 0) {
    const joined = contexts.length === 1 ? contexts[0] : contexts.join('\n\n');
    if (eventName && eventName.startsWith('PreToolUse')) {
      merged.hookSpecificOutput = {
        hookEventName: 'PreToolUse',
        ...(merged.hookSpecificOutput || {}),
        additionalContext: joined,
      };
    } else {
      merged.additionalContext = joined;
    }
  }

  return merged;
}

async function runHook(event, modPath, data) {
  const mod = loadHook(modPath);
  if (!mod || typeof mod.run !== 'function') {
    logError(event, modPath, new Error('module missing run() export'));
    return null;
  }
  try {
    const result = mod.run(data);
    return await Promise.resolve(result);
  } catch (e) {
    logError(event, modPath, e);
    return null;
  }
}

function readStdin(timeoutMs) {
  return new Promise(resolve => {
    let input = '';
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      resolve(input);
    };
    const timer = setTimeout(finish, timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { input += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); finish(); });
    process.stdin.on('error', () => { clearTimeout(timer); finish(); });
  });
}

// --- Module exports for unit tests (BL-2026-05-24 regression-guard) -------
// Exported BEFORE the IIFE so `require('./hook-dispatcher.js')` succeeds
// without triggering the CLI path. The IIFE below is gated by
// `require.main === module` so test imports do NOT block on stdin.
module.exports = { sanitizeForSchema, familyOf, mergeOutputs };

// --- Main (CLI path only — skipped when required as a module) ---
if (require.main === module) (async () => {
  const event = parseArgs();

  // --- Child-process chain path (Stop event — fork-storm-safe) ---
  if (event && CHAIN_MAP[event]) {
    const rawIn = await readStdin(3000);
    const { outputs, blocked, blockStderr } = runChain(event, CHAIN_MAP[event], rawIn || '');
    const merged = mergeOutputs(outputs, event);
    if (blocked) {
      merged.decision = 'block';
      if (blockStderr) merged.reason = blockStderr;
    }
    const safe = sanitizeForSchema(merged, familyOf(event));
    try { process.stdout.write(JSON.stringify(safe)); }
    catch (e) { logError(event, 'STDOUT', e); process.stdout.write('{}'); }
    process.exit(0);
  }

  const bundle = event ? EVENT_MAP[event] : null;

  if (!event || !bundle) {
    // Unknown event — emit empty payload, do not block tool use.
    process.stdout.write('{}');
    process.exit(0);
  }

  const raw = await readStdin(3000);
  let data = {};
  try { data = JSON.parse(raw || '{}'); } catch (_) { /* keep empty */ }

  // Sequential execution — preserves ordering semantics of original chain.
  // Switch to Promise.all if a future bundle has truly independent hooks.
  const outputs = [];
  for (const modPath of bundle) {
    const out = await runHook(event, modPath, data);
    outputs.push(out);
  }

  const merged = mergeOutputs(outputs, event);
  const safe = sanitizeForSchema(merged, familyOf(event));
  try {
    process.stdout.write(JSON.stringify(safe));
  } catch (e) {
    logError(event, 'STDOUT', e);
    process.stdout.write('{}');
  }
  process.exit(0);
})();
