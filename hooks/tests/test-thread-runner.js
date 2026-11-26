#!/usr/bin/env node
// V-THREAD-* -- SPEC-HOOK-CHAIN-THREAD-RUNNER (vault/specs/hook-chain-thread-runner.md).
// Usage: node hooks/tests/test-thread-runner.js [<hook-dispatcher.js>] [<reference-dispatcher.js>]
//   arg1: dispatcher under test (default ~/.claude/hooks/hook-dispatcher.js)
//   arg2: reference dispatcher for the end-to-end parity gates (default: arg1 with CPP_HOOK_THREAD_RUNNER=off)
// Every gate is driven from both poles, and each has a mutant its predicate must reject.
const fs = require('fs'), os = require('os'), path = require('path');
const { spawnSync } = require('child_process');
const DISP = path.resolve(process.argv[2] || path.join(os.homedir(), '.claude', 'hooks', 'hook-dispatcher.js'));
const REF = process.argv[3] ? path.resolve(process.argv[3]) : null;
const HOOKS = path.dirname(DISP);
const d = require(DISP);
let pass = 0, fail = 0;
const ok = (id, cond, msg) => { if (cond) { pass++; console.log('PASS', id); } else { fail++; console.log('FAIL', id, '--', msg); } };
const mutantKilled = (id, pred, mutated) => ok(id + '-MUTANT', !pred(mutated), 'predicate accepted a mutant result');

const FIX = fs.mkdtempSync(path.join(os.tmpdir(), 'v-thread-'));
const fx = (name, body) => { const p = path.join(FIX, name); fs.writeFileSync(p, body); return p; };
const NODE = process.execPath;
const step = (abs, timeoutMs = 4000, extra = {}) => Object.assign({ exe: NODE, script: path.relative(HOOKS, abs), timeoutMs }, extra);
// A fresh session id per payload: some chain members speak once per session (the cross-project baseline
// advisory), so two runs sharing a session differ by that block alone (measured 2607 B vs 1880 B, 2026-11-26).
let SEQ = 0;
const bashPayload = (cmd, tool = 'Bash') => JSON.stringify({ hook_event_name: 'PreToolUse', tool_name: tool, tool_input: { command: cmd },
  session_id: 'v-thread-' + process.pid + '-' + (++SEQ), cwd: FIX });

(async () => {
  if (typeof d.runStepThread !== 'function' || typeof d.runStepSpawn !== 'function') {
    ok('V-THREAD-EXPORTED', false, 'runStepThread/runStepSpawn not exported by ' + DISP);
    process.exit(1);
  }
  ok('V-THREAD-EXPORTED', true);

  // 1. Parity on real guards, allow pole and block pole.
  // console-popup-guard block pole: its own test's V-POPUP-SP-CMD-BLOCK case (PowerShell, cmd.exe not hidden).
  const guards = [['./windows-bash-bridge-guard.js', 'Bash', 'echo hello', 'git status'],
                  ['../skills/claude-power-pack/hooks/console-popup-guard.js', 'PowerShell', 'Start-Process notepad.exe',
                   "Start-Process cmd.exe -ArgumentList '/c ping -n 3 127.0.0.1'"],
                  ['../skills/claude-power-pack/hooks/capsule_mutation_guard.js', 'Bash', 'echo hello', null]];
  for (const [script, tool, allowCmd, blockCmd] of guards) {
    const abs = path.join(HOOKS, script);
    const s = { exe: NODE, script, timeoutMs: 8000 };
    for (const [pole, cmd] of [['ALLOW', allowCmd], ['BLOCK', blockCmd]]) {
      if (!cmd) continue;
      const a = await d.runStepSpawn(s, bashPayload(cmd, tool));
      const b = await d.runStepThread(s, bashPayload(cmd, tool), abs);
      const same = (r) => r.status === a.status && r.stdout.trim() === a.stdout.trim();
      const id = 'V-THREAD-PARITY-' + pole + '-' + path.basename(script, '.js');
      ok(id, same(b) && (pole === 'ALLOW' ? a.status === 0 : a.status === 2 || /"(block|deny)"/.test(a.stdout)),
        `spawn=${a.status}/${a.stdout.length}B thread=${b.status}/${b.stdout.length}B`);
      mutantKilled(id, same, Object.assign({}, b, { status: pole === 'ALLOW' ? 2 : 0 }));
    }
  }

  // 2. process.exit(2) mid-script blocks and truncates what follows (standalone contract inside a thread).
  const exitMid = fx('exit-mid.js', "process.stdout.write('{\"decision\":\"block\"}'); process.exit(2); process.stdout.write('AFTER');");
  const r2 = await d.runStepThread(step(exitMid), '{}', exitMid);
  const p2 = (r) => r.status === 2 && r.stdout === '{"decision":"block"}';
  ok('V-THREAD-EXIT-CODE', p2(r2), JSON.stringify({ s: r2.status, o: r2.stdout }));
  mutantKilled('V-THREAD-EXIT-CODE', p2, Object.assign({}, r2, { status: 0 }));

  // 3. A hung member is terminated at its timeout and reported ETIMEDOUT.
  const hang = fx('hang.js', 'for (;;) {}');
  const t0 = Date.now();
  const r3 = await d.runStepThread(step(hang, 800), '{}', hang);
  const el = Date.now() - t0;
  const p3 = (r, ms) => r.error && /ETIMEDOUT/.test(r.error.message) && ms < 800 + 1500;
  ok('V-THREAD-TIMEOUT', p3(r3, el), `elapsed=${el} err=${r3.error && r3.error.message}`);
  ok('V-THREAD-TIMEOUT-MUTANT', !p3({ error: null }, el) && !p3(r3, 800 + 60000), 'timeout predicate accepts no-terminate');

  // 4. An uncaught exception is status 1 with the stack on stderr, as a child process would give.
  const thrower = fx('throw.js', "throw new Error('boom-v-thread');");
  const r4 = await d.runStepThread(step(thrower), '{}', thrower);
  const p4 = (r) => r.status === 1 && /boom-v-thread/.test(r.stderr);
  ok('V-THREAD-UNCAUGHT', p4(r4), JSON.stringify({ s: r4.status, e: String(r4.stderr).slice(0, 80) }));
  mutantKilled('V-THREAD-UNCAUGHT', p4, Object.assign({}, r4, { status: 0 }));

  // 5. Members that read fd 0 (would hang in a thread) are detected and kept on the child process.
  const fd0 = fx('fd0.js', "const fs=require('fs'); const raw=fs.readFileSync(0,'utf8'); process.stdout.write('len'+raw.length);");
  ok('V-THREAD-FD0-DETECTED', d.threadSafeSource(fd0) === false && d.useThreadRunner(step(fd0), fd0) === false, 'fd0 member would run in a thread');
  ok('V-THREAD-FD0-REAL', d.threadSafeSource(path.join(HOOKS, '../skills/claude-power-pack/hooks/claude_md_firewall.js')) === false,
    'claude_md_firewall.js (measured hanger) not detected');
  const r5 = await d.runStep(step(fd0, 6000), '{"x":1}');
  ok('V-THREAD-FD0-RUNS', r5.status === 0 && r5.stdout === 'len7', JSON.stringify({ s: r5.status, o: r5.stdout, e: r5.error && r5.error.message }));
  const plain = fx('plain.js', "let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>process.stdout.write('got'+s.length));");
  ok('V-THREAD-PLAIN-USES-THREAD', d.useThreadRunner(step(plain), plain) === true, 'a plain stdin-stream member is not routed to the thread runner');
  const r5b = await d.runStep(step(plain), '{"x":1}');
  ok('V-THREAD-PLAIN-RUNS', r5b.status === 0 && r5b.stdout === 'got7', JSON.stringify({ s: r5b.status, o: r5b.stdout }));

  // 6. Kill switch and per-member opt-out.
  process.env.CPP_HOOK_THREAD_RUNNER = 'off';
  ok('V-THREAD-KILL-SWITCH', d.useThreadRunner(step(plain), plain) === false, 'switch off still routes to threads');
  delete process.env.CPP_HOOK_THREAD_RUNNER;
  ok('V-THREAD-KILL-SWITCH-POLE', d.useThreadRunner(step(plain), plain) === true, 'switch on does not route to threads');
  ok('V-THREAD-OPTOUT', d.useThreadRunner(step(plain, 4000, { runner: 'spawn' }), plain) === false, "runner:'spawn' ignored");
  ok('V-THREAD-PYTHON-SPAWN', d.useThreadRunner({ exe: 'python.exe', script: 'x.py' }, plain) === false, 'python member routed to a thread');

  // 7. Runtime incompatibility falls back once to the child process.
  const incompat = fx('incompat.js', "process['ch'+'dir'](require('os').tmpdir()); process.stdout.write('ran-ok');");
  const r7 = await d.runStep(step(incompat, 6000), '{}');
  ok('V-THREAD-FALLBACK', r7.status === 0 && r7.stdout === 'ran-ok', JSON.stringify({ s: r7.status, o: r7.stdout, e: r7.error && r7.error.message }));
  const r7t = await d.runStepThread(step(incompat), '{}', incompat);
  ok('V-THREAD-FALLBACK-POLE', r7t.threadFallback === true, 'thread runner did not flag the incompatible member');

  // 8. End to end through the dispatcher process: same stdout and exit code as the reference, block and allow.
  const runDisp = (file, event, payload, env) => {
    const t = Date.now();
    const r = spawnSync(NODE, [file, '--event=' + event], { input: payload, encoding: 'utf8', timeout: 90000,
      env: Object.assign({}, process.env, env || {}), windowsHide: true });
    return { status: r.status, out: (r.stdout || '').trim(), ms: Date.now() - t };
  };
  const refFile = REF || DISP, refEnv = REF ? {} : { CPP_HOOK_THREAD_RUNNER: 'off' };
  for (const [pole, cmd] of [['BLOCK', 'git status'], ['ALLOW', 'echo hello']]) {
    const a = runDisp(refFile, 'PreToolUse-Bash-chain', bashPayload(cmd), refEnv);   // each run its own session
    const b = runDisp(DISP, 'PreToolUse-Bash-chain', bashPayload(cmd), {});
    const same = (x) => x.status === a.status && x.out === a.out;
    ok('V-THREAD-E2E-BASH-' + pole, same(b), `ref=${a.status}/${a.out.length}B ${a.ms}ms test=${b.status}/${b.out.length}B ${b.ms}ms`);
    console.log(`  e2e ${pole}: reference ${a.ms} ms, under test ${b.ms} ms`);
    mutantKilled('V-THREAD-E2E-BASH-' + pole, same, Object.assign({}, b, { out: b.out + 'x' }));
  }
  const editPayload = JSON.stringify({ hook_event_name: 'PreToolUse', tool_name: 'Edit', session_id: 'v-thread', cwd: FIX,
    tool_input: { file_path: fx('target.txt', 'hello\n'), old_string: 'hello', new_string: 'hola' } });
  const ea = runDisp(refFile, 'PreToolUse-Edit-chain', editPayload, refEnv);
  const eb = runDisp(DISP, 'PreToolUse-Edit-chain', editPayload, {});
  ok('V-THREAD-E2E-EDIT-ALLOW', eb.status === ea.status, `ref=${ea.status} ${ea.ms}ms test=${eb.status} ${eb.ms}ms`);
  console.log(`  e2e EDIT: reference ${ea.ms} ms, under test ${eb.ms} ms`);

  console.log(`\nV-THREAD: ${pass} pass, ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
