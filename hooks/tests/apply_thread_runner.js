// Applies SPEC-HOOK-CHAIN-THREAD-RUNNER to a hook-dispatcher.js copy. Targeted, anchor-checked, idempotent-refusing.
// Usage: node apply_thread_runner.js <in.js> <out.js>
const fs = require('fs');
const [, , IN, OUT] = process.argv;
let src = fs.readFileSync(IN, 'utf8');
if (src.includes('runStepThread')) { console.error('already patched'); process.exit(1); }
const EOL = src.includes('\r\n') ? '\r\n' : '\n';
const ANCHOR = 'function runStep(step, rawStdin) {\n  return new Promise((resolve) => {\n    const abs = path.join(__dirname, step.script);'.replace(/\n/g, EOL);
const n = src.split(ANCHOR).length - 1;
if (n !== 1) { console.error('anchor count ' + n + ' (expected 1)'); process.exit(1); }
const BLOCK = `// --- THREAD RUNNER (spec vault/specs/hook-chain-thread-runner.md; Owner go 2026-11-26, pane 8fd6ace9) ---------
// A node chain member runs UNCHANGED in a worker_threads Worker instead of a child process: same stdin, same
// stdout/stderr, and process.exit(code) inside the member ends only its thread and arrives here as \`status\`.
// MEASURED (laptop, 2026-11-26, 57 node members, one allow payload each, both runners): median 246 ms as a
// process, 57 ms as a thread, faster in 57/57, identical exit code and stdout. Why it matters: hooks were 53 s of a
// 211 s median turn (LAPTOP-turn-decomposition-7d.txt), and a process start costs 0.15-1+ s on a loaded host.
// NOT thread-safe, detected from source and kept on the child process: a member that reads fd 0 directly
// (fs.readFileSync(0)) reads the DISPATCHER's stdin inside a thread and hangs -- measured on claude_md_firewall.js
// and claude_md_linter_stop.js -- and a member that calls process.chdir (unsupported in workers).
// Order, critical lane, pool and mergeOutputs are untouched. An uncaught exception in a member is surfaced as
// status 1 plus its stack on stderr, as a child process would. A Worker that cannot start, or dies with a
// worker-incompatibility error before writing anything, is re-run ONCE as a child process (THREAD-FALLBACK line).
// Kill switch: CPP_HOOK_THREAD_RUNNER=off. Per member: runner:'spawn'. Proof: hooks/tests/test-thread-runner.js.
let WorkerCtor = null;
try { WorkerCtor = require('worker_threads').Worker; } catch (_) { WorkerCtor = null; }
const THREAD_UNSAFE_SRC = /readFileSync\\(\\s*0\\s*[,)]|readSync\\(\\s*0\\s*,|['"]\\/dev\\/stdin['"]|process\\.chdir\\(/;
const THREAD_INCOMPATIBLE = /ERR_WORKER_|not supported in workers|Module did not self-register/;
const THREAD_SAFE_CACHE = new Map();
function threadSafeSource(abs) {
  if (THREAD_SAFE_CACHE.has(abs)) return THREAD_SAFE_CACHE.get(abs);
  let ok = false;
  try { ok = !THREAD_UNSAFE_SRC.test(fs.readFileSync(abs, 'utf8')); } catch (_) { ok = false; }
  THREAD_SAFE_CACHE.set(abs, ok);
  return ok;
}
function useThreadRunner(step, abs) {
  if (!WorkerCtor || envSwitchOff('CPP_HOOK_THREAD_RUNNER')) return false;
  if (step.runner === 'spawn' || step.exe !== NODE_EXE) return false;
  return threadSafeSource(abs);
}

function runStepThread(step, rawStdin, abs) {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    let settled = false;
    let exitCode = null;
    let outEnded = false;
    let sawOut = false;
    let incompatible = false;
    let timer = null;
    let grace = null;
    let w = null;
    const handle = { kill: () => { try { if (w) w.terminate(); } catch (_) { /* already gone */ } } };
    const done = (res) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      clearTimeout(grace);
      LIVE_CHILDREN.delete(handle);
      resolve(res);
    };
    try {
      w = new WorkerCtor(abs, { stdin: true, stdout: true, stderr: true });
    } catch (e) { return done({ error: e, status: null, stdout: '', stderr: '', threadFallback: true }); }
    LIVE_CHILDREN.add(handle);   // reapLiveChildren() terminates it like a straggling child
    timer = setTimeout(() => {
      handle.kill();
      done({ error: new Error('ETIMEDOUT after ' + step.timeoutMs + 'ms'), status: null, stdout, stderr });
    }, step.timeoutMs);
    const CAP = 8 * 1024 * 1024;
    w.stdout.setEncoding('utf8');
    w.stderr.setEncoding('utf8');
    w.stdout.on('data', (d) => { sawOut = true; if (stdout.length < CAP) stdout += d; });
    w.stderr.on('data', (d) => { if (stderr.length < CAP) stderr += d; });
    const finish = () => {
      if (exitCode === null || !outEnded) return;
      if (incompatible) return done({ error: new Error(stderr.slice(0, 200)), status: null, stdout, stderr, threadFallback: true });
      done({ error: null, status: exitCode, stdout, stderr });
    };
    w.stdout.on('end', () => { outEnded = true; finish(); });
    w.on('error', (e) => {
      const msg = String((e && (e.stack || e.message)) || e);
      stderr += (stderr ? '\\n' : '') + msg;
      if (!sawOut && (THREAD_INCOMPATIBLE.test(msg) || /^ERR_WORKER_/.test(String((e && e.code) || '')))) incompatible = true;
    });
    w.on('exit', (code) => {
      exitCode = code;
      grace = setTimeout(() => { outEnded = true; finish(); }, 250);   // stdout 'end' normally precedes this
      finish();
    });
    try {
      w.stdin.on('error', () => { /* member closed stdin early */ });
      w.stdin.end(rawStdin);
    } catch (_) { /* fail-open */ }
  });
}

function runStep(step, rawStdin) {
  const abs = path.join(__dirname, step.script);
  if (!useThreadRunner(step, abs)) return runStepSpawn(step, rawStdin);
  return runStepThread(step, rawStdin, abs).then((res) => {
    if (!res.threadFallback) return res;
    logError('thread-runner', 'THREAD-FALLBACK ' + step.script, res.error || new Error('worker could not run'));
    return runStepSpawn(step, rawStdin);
  });
}

function runStepSpawn(step, rawStdin) {
  return new Promise((resolve) => {
    const abs = path.join(__dirname, step.script);`;
src = src.replace(ANCHOR, BLOCK.replace(/\n/g, EOL));
const EXP = 'module.exports = { sanitizeForSchema,';
if (src.split(EXP).length - 1 !== 1) { console.error('export anchor missing'); process.exit(1); }
src = src.replace(EXP, 'module.exports = { runStep, runStepSpawn, runStepThread, threadSafeSource, useThreadRunner, sanitizeForSchema,');
fs.writeFileSync(OUT, src);
console.log('patched ->', OUT, 'bytes', src.length);
