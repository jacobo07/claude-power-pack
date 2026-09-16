/**
 * Shared utilities for Claude Code hooks.
 * Import: const { readStdin, getPythonCommand, resolveHomePath } = require('./hook-utils');
 *
 * Standards: See GAL CD#12 for mandatory hook development rules.
 * HOOK_UTILS_VERSION=1.1.0
 */
const os = require('os');
const path = require('path');

/**
 * Read JSON from stdin with timeout. Cross-platform (no /dev/stdin).
 *
 * 2026-09-16 -- HARDENED. The previous version resolved on a timer, which made
 * it look bounded, and it was not. Three defects, all of which end in the same
 * place: a node process alive forever holding an inherited pipe.
 *
 *   1. The 'data' listener stayed ATTACHED after the timer fired. An attached
 *      listener on a flowing stream is a referenced libuv handle, so the event
 *      loop never empties and the process never exits -- the caller got its {}
 *      and the PROCESS still hung. "Resolved" and "exited" are different facts.
 *   2. NO 'error' HANDLER. An 'error' on a stream with no listener is rethrown
 *      as an uncaught exception, so a broken pipe took an unrelated exit path.
 *   3. A TIMEOUT WAS INDISTINGUISHABLE FROM EMPTY INPUT. Both resolved {}, so
 *      every caller treated "nobody told us anything" as "there was nothing to
 *      say" -- absence read as measured-zero, on the input to a guard.
 *
 * bfb40a1 fixed exactly this shape inside session-file-guard.js and said so in
 * its own commit message, which deliberately did NOT import this helper because
 * of the defects above. This brings the shared helper up to that template so
 * the two remaining callers (kg-sync-hook.js, token-shield-refresh.js) stop
 * inheriting the hang. kg-sync-hook.js was measured PARKED -- 11.6 min, zero
 * CPU, dead parent -- while this was being written.
 *
 * Backwards compatible on purpose: the resolved value is still a plain object,
 * so existing callers are unchanged. The new fact is carried on a
 * non-enumerable property, which JSON.stringify and Object.keys ignore, so a
 * caller that does not ask cannot be broken by it and a caller that does ask
 * can tell the three outcomes apart.
 *
 * @param {number} timeoutMs - Max ms to wait for stdin (default 3000)
 * @returns {Promise<object>} Parsed JSON, or {} -- carrying a non-enumerable
 *   `__stdin` of 'ok' | 'timeout' | 'empty' | 'parse-error' | 'stream-error'.
 */
/**
 * The raw form. Several hooks parse at the call site (`JSON.parse(readStdin() ||
 * '{}')`) or need the text itself to strip a BOM, and handing them a parsed
 * object would force a semantic change during what is supposed to be a pure
 * liveness migration.
 *
 * @param {number} timeoutMs
 * @returns {Promise<{raw: string|null, outcome: string}>} raw is null when
 *   nothing could be read -- which is NOT the same as '' (a producer that closed
 *   with nothing to say). A caller that collapses the two has reintroduced
 *   "absence read as measured-zero" on its own input.
 */
function readStdinRaw(timeoutMs = 3000) {
  return new Promise((resolve) => {
    let input = '';
    let settled = false;

    const finish = (raw, outcome) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      // Detach AND pause -- see the note on readStdin below.
      try {
        process.stdin.removeAllListeners('data');
        process.stdin.removeAllListeners('end');
        process.stdin.removeAllListeners('error');
        process.stdin.pause();
      } catch { /* a hook never throws out of its own input path */ }
      resolve({ raw, outcome });
    };

    const timer = setTimeout(() => finish(null, 'timeout'), timeoutMs);

    try {
      process.stdin.setEncoding('utf8');
      process.stdin.on('data', (chunk) => { input += chunk; });
      process.stdin.on('end', () => finish(input, input ? 'ok' : 'empty'));
      process.stdin.on('error', () => finish(null, 'stream-error'));
    } catch {
      finish(null, 'stream-error');
    }
  });
}

/**
 * Absolute backstop for a hook process.
 *
 * NOT unref'd, on purpose: an unref'd timer cannot hold the process alive long
 * enough to fire, and firing is the entire point. Returns the timer so the
 * caller clears it on every normal path.
 *
 * This is the load-bearing half of the template, and the reason is worth
 * stating: a mutation drill that kept the event loop busy with setInterval did
 * NOT hang the hook, because process.exit() is unconditional. What strands a
 * hook is never REACHING an exit call. So the backstop is not tidiness around
 * the edges -- it is the guarantee that an exit call happens at all.
 *
 * @param {number} ms
 * @param {function} [onFire] - optional logging; must not throw and must be cheap
 * @returns {NodeJS.Timeout}
 */
function armHardExit(ms, onFire) {
  return setTimeout(() => {
    try { if (typeof onFire === 'function') onFire(); } catch { /* never throw here */ }
    process.exit(0);
  }, ms);
}

function readStdin(timeoutMs = 3000) {
  return new Promise((resolve) => {
    let input = '';
    let settled = false;

    const finish = (value, outcome) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      // Detach AND pause. Removing the listener alone is not enough: a resumed
      // stream keeps its handle referenced. This pair is what turns "the read
      // timed out" into "the process can now exit".
      try {
        process.stdin.removeAllListeners('data');
        process.stdin.removeAllListeners('end');
        process.stdin.removeAllListeners('error');
        process.stdin.pause();
      } catch { /* a hook never throws out of its own input path */ }
      try {
        Object.defineProperty(value, '__stdin', {
          value: outcome, enumerable: false, configurable: true, writable: true,
        });
      } catch { /* frozen or exotic value: the outcome is a bonus, never a requirement */ }
      resolve(value);
    };

    const timer = setTimeout(() => finish({}, 'timeout'), timeoutMs);

    try {
      process.stdin.setEncoding('utf8');
      process.stdin.on('data', (chunk) => { input += chunk; });
      process.stdin.on('end', () => {
        if (!input) return finish({}, 'empty');
        try {
          const parsed = JSON.parse(input);
          finish(parsed && typeof parsed === 'object' ? parsed : {}, 'ok');
        } catch {
          finish({}, 'parse-error');
        }
      });
      process.stdin.on('error', () => finish({}, 'stream-error'));
    } catch {
      finish({}, 'stream-error');
    }
  });
}

/**
 * Output valid PreToolUse response and exit.
 *
 * 2026-04-25 update — schema migration. The legacy `{decision: 'allow'}`
 * shape is rejected by the current Claude Code harness with
 * "Hook JSON output validation failed — Invalid input" on every hook call.
 * The current canonical shape is `{hookSpecificOutput: {hookEventName:
 * 'PreToolUse', permissionDecision: 'allow'|'deny'|'ask',
 * permissionDecisionReason: '...'}}`. We also exploit the fact that exit-0
 * with empty stdout is universally interpreted as silent-allow across
 * schema versions, so the most common path (allow with no extra context)
 * emits nothing — that's the path that fires on every Bash call.
 *
 * @param {'allow'|'block'|'ask'} decision
 * @param {string} [additionalContext] - On 'allow' = advisory text; on 'block' = ignored (use reason)
 * @param {string} [reason] - Only for 'block' decisions
 */
function outputPreToolUse(decision, additionalContext, reason) {
  // Fast path: silent allow with no extra context. Universally valid,
  // produces zero stdout, no schema-validation noise.
  if (decision === 'allow' && !additionalContext) {
    process.exit(0);
  }
  const permissionDecision =
    decision === 'block' ? 'deny' :
    decision === 'allow' ? 'allow' :
    decision === 'ask'   ? 'ask'   : 'allow';
  const hookSpecificOutput = {
    hookEventName: 'PreToolUse',
    permissionDecision,
  };
  const why = decision === 'block' ? (reason || additionalContext) : additionalContext;
  if (why) hookSpecificOutput.permissionDecisionReason = why;
  console.log(JSON.stringify({ hookSpecificOutput }));
  process.exit(0);
}

/**
 * Output valid PostToolUse response and exit.
 * @param {string} [additionalContext] - If null, exits silently
 */
function outputPostToolUse(additionalContext) {
  if (additionalContext) {
    console.log(JSON.stringify({ additionalContext }));
  } else {
    console.log('{}');
  }
  process.exit(0);
}

/**
 * Output valid Stop hook response and exit.
 * @param {boolean} shouldContinue - true to allow session end, false to block
 */
function outputStop(shouldContinue = true) {
  console.log(JSON.stringify({ continue: shouldContinue }));
  process.exit(0);
}

/**
 * Resolve a usable Python interpreter for child_process spawns.
 *
 * Hook subprocesses inherit a Windows shell PATH that does NOT include
 * `python.exe` in many configurations (Store stub aliases redirect to a
 * non-functional shim, and Python installed under %LOCALAPPDATA% is not
 * on the system PATH by default). Bare `python` then fails with
 * "command not found" at Stop time. We probe in priority:
 *   1. $CLAUDE_PYTHON (operator override)
 *   2. %LOCALAPPDATA%\Programs\Python\Python3*\python.exe (Per-user install)
 *   3. `py -3` (Windows Python Launcher — present on every Win11 install)
 *   4. bare `python` (POSIX fallback / last resort on Win)
 *
 * Returned string is shell-safe (already-quoted when it contains spaces)
 * so it drops into execSync templates directly. Memoized after first hit.
 *
 * @returns {string} interpreter invocation
 */
let _pythonCache = null;
function getPythonCommand() {
  if (_pythonCache) return _pythonCache;
  const fs = require('fs');
  if (process.platform !== 'win32') {
    _pythonCache = 'python3';
    return _pythonCache;
  }
  const override = process.env.CLAUDE_PYTHON;
  if (override && fs.existsSync(override)) {
    _pythonCache = override.includes(' ') ? `"${override}"` : override;
    return _pythonCache;
  }
  const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
  const programs = path.join(localAppData, 'Programs', 'Python');
  try {
    if (fs.existsSync(programs)) {
      const versions = fs.readdirSync(programs).filter(d => /^Python3\d+$/.test(d)).sort().reverse();
      for (const v of versions) {
        const exe = path.join(programs, v, 'python.exe');
        if (fs.existsSync(exe)) {
          _pythonCache = exe.includes(' ') ? `"${exe}"` : exe;
          return _pythonCache;
        }
      }
    }
  } catch { /* directory scan best-effort */ }
  const pyLauncher = 'C:\\Windows\\py.exe';
  if (fs.existsSync(pyLauncher)) {
    _pythonCache = 'py -3';
    return _pythonCache;
  }
  _pythonCache = 'python';
  return _pythonCache;
}

/**
 * Resolve a usable Node interpreter for child_process spawns.
 * Same rationale as getPythonCommand. Falls back to process.execPath
 * (the Node binary currently executing the hook) when bare `node` is
 * not on the inherited PATH.
 * @returns {string} shell-safe node invocation
 */
let _nodeCache = null;
function getNodeCommand() {
  if (_nodeCache) return _nodeCache;
  const exe = process.execPath;
  _nodeCache = exe && exe.includes(' ') ? `"${exe}"` : (exe || 'node');
  return _nodeCache;
}

/**
 * Resolve a path relative to the user's home directory.
 * Cross-platform: uses os.homedir() (never process.env.HOME alone).
 * @param {...string} segments - Path segments after home
 * @returns {string} Absolute path
 */
function resolveHomePath(...segments) {
  return path.join(os.homedir(), ...segments);
}

/**
 * Canonical safe-exit helper for every hook path.
 * GUARANTEES stdout JSON is written before the process dies — any hook that
 * calls process.exit without first writing valid JSON triggers Claude Code's
 * "Hook JSON output validation failed — Invalid input" error.
 *
 * Use this for every exit path, including stdinTimeout, early-returns, and
 * catch blocks. See knowledge_vault/gex44_antipatterns/hook-boundary-contract.md.
 *
 * @param {object} [payload={}] - JSON payload to emit (default: `{}` pass-through)
 * @param {number} [code=0]     - Exit code
 */
function safeExit(payload = {}, code = 0) {
  try { process.stdout.write(JSON.stringify(payload)); } catch { /* stdout already closed */ }
  process.exit(code);
}

module.exports = {
  readStdin,
  readStdinRaw,
  armHardExit,
  outputPreToolUse,
  outputPostToolUse,
  outputStop,
  safeExit,
  getPythonCommand,
  getNodeCommand,
  resolveHomePath,
};
