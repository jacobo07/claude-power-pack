// Feasibility probe: run an unchanged standalone hook script as (a) a child process, (b) a worker thread.
// Same stdin payload, same stdout capture. Read-only guard used: windows-bash-bridge-guard.js on a harmless command.
const { spawn } = require('child_process');
const { Worker } = require('worker_threads');
const path = require('path');
const os = require('os');
const script = path.join(os.homedir(), '.claude', 'hooks', process.argv[2] || 'windows-bash-bridge-guard.js');
const payload = JSON.stringify({ hook_event_name: 'PreToolUse', tool_name: process.argv[3] || 'Bash',
  tool_input: { command: process.argv[4] || 'echo hello' }, session_id: 'probe-thread-vs-spawn', cwd: os.tmpdir() });
const N = 8;

function viaSpawn() {
  return new Promise((res) => {
    const t = process.hrtime.bigint(); let out = '';
    const c = spawn(process.execPath, [script], { shell: false, windowsHide: true });
    c.stdout.on('data', (d) => (out += d));
    c.on('close', (code) => res({ ms: Number(process.hrtime.bigint() - t) / 1e6, code, out }));
    c.stdin.on('error', () => {}); c.stdin.end(payload);
  });
}
function viaThread() {
  return new Promise((res) => {
    const t = process.hrtime.bigint(); let out = '';
    const w = new Worker(script, { stdin: true, stdout: true, stderr: true });
    w.stdout.on('data', (d) => (out += d));
    w.on('error', (e) => res({ ms: Number(process.hrtime.bigint() - t) / 1e6, code: 'ERR ' + e.message, out }));
    w.on('exit', (code) => res({ ms: Number(process.hrtime.bigint() - t) / 1e6, code, out }));
    w.stdin.end(payload);
  });
}
const med = (v) => { const s = [...v].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
(async () => {
  const sp = [], th = [];
  for (let i = 0; i < N; i++) { sp.push(await viaSpawn()); th.push(await viaThread()); }   // interleaved
  const fmt = (r) => `median=${med(r.map((x) => x.ms)).toFixed(0)}ms min=${Math.min(...r.map((x) => x.ms)).toFixed(0)} max=${Math.max(...r.map((x) => x.ms)).toFixed(0)}`;
  console.log('script', path.basename(script));
  console.log('spawn  ', fmt(sp), 'exit', [...new Set(sp.map((x) => x.code))].join(','));
  console.log('thread ', fmt(th), 'exit', [...new Set(th.map((x) => x.code))].join(','));
  console.log('same stdout:', sp.every((x, i) => x.out === th[i].out), '| sample:', JSON.stringify(sp[0].out).slice(0, 120));
})();
