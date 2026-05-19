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
 *       "command": "node \"C:/Users/User/.claude/hooks/hook-dispatcher.js\" --event=PreToolUse-default",
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
const PY_EXE = process.env.CLAUDE_PY_EXE
  || 'C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe';

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
    }

    for (const k of Object.keys(out)) {
      if (k === 'decision' || k === 'additionalContext' || k === 'hookSpecificOutput' || k === 'continue') continue;
      merged[k] = out[k];
    }
  }

  // 2026-05-14 schema migration (VAC-D-HOOK-001). The harness rejects bare
  // `decision: "allow"` at root for PreToolUse — must use
  // `hookSpecificOutput.permissionDecision`. For other events the legacy
  // `decision: "deny"`/`"block"` shape is still accepted. Sub-hooks may still
  // emit the legacy shape; we translate at merge time so the dispatcher
  // output always validates regardless of sub-hook drift.
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

  // For PreToolUse, additionalContext must live inside hookSpecificOutput.
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

// --- Main ---
(async () => {
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
    try { process.stdout.write(JSON.stringify(merged)); }
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
  try {
    process.stdout.write(JSON.stringify(merged));
  } catch (e) {
    logError(event, 'STDOUT', e);
    process.stdout.write('{}');
  }
  process.exit(0);
})();
