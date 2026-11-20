// BCAP-2 Phase 9 canary driver: speaks MCP JSON-RPC over stdio to the REAL `ruflo mcp start` (3.78.0).
// Runs ONLY inside the isolated container (docker --network none, read-only rootfs, cap-drop ALL; see run_canary.sh).
// usage: node driver.cjs <steps.json>   steps = [{"list": true} | {"call": "<tool>", "args": {...}, "id": "<case>"}]
// Prints one JSON line per step: {case, tool, ok, isError, text(<=600 chars), error}. Never interprets results:
// the verdict is computed by run_canary.py against the gateway, so this file stays a dumb transport.
const { spawn } = require('child_process');
const fs = require('fs');
const steps = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const srv = spawn('node', ['/sb/node_modules/ruflo/bin/ruflo.js', 'mcp', 'start'], { cwd: process.cwd(), env: process.env });
let buf = '', nextId = 1; const waiters = {};
srv.stdout.on('data', d => {
  buf += d.toString();
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
    if (!line.startsWith('{')) continue;
    let m; try { m = JSON.parse(line); } catch { continue; }
    if (m.id && waiters[m.id]) { waiters[m.id](m); delete waiters[m.id]; }
  }
});
let stderr = ''; srv.stderr.on('data', d => { stderr += d.toString(); if (stderr.length > 20000) stderr = stderr.slice(-20000); });
function rpc(method, params, ms = 30000) {
  const id = nextId++;
  return new Promise(res => {
    const t = setTimeout(() => { delete waiters[id]; res({ timeout: true }); }, ms);
    waiters[id] = m => { clearTimeout(t); res(m); };
    srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  });
}
const out = o => process.stdout.write(JSON.stringify(o) + '\n');
(async () => {
  const init = await rpc('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'cpp-canary', version: '1' } }, 60000);
  out({ case: 'initialize', ok: !!init.result, server: init.result && init.result.serverInfo, error: init.error || (init.timeout && 'timeout') });
  srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  for (const s of steps) {
    if (s.write_file) {        // plant a fixture file (e.g. a repo CLAUDE.md carrying an injection)
      fs.mkdirSync(require('path').dirname(s.write_file), { recursive: true });
      fs.writeFileSync(s.write_file, s.content); out({ case: s.id, wrote: s.write_file }); continue;
    }
    if (s.check_file) {        // observe an effect on disk instead of trusting the tool's reply
      const ex = fs.existsSync(s.check_file);
      out({ case: s.id, check_file: s.check_file, exists: ex, head: ex ? fs.readFileSync(s.check_file, 'utf8').slice(0, 200) : null });
      continue;
    }
    if (s.check_proto) {      // client-side view only: pollution of the SERVER process is not observable here
      out({ case: s.id, note: 'server-process prototype not observable over stdio' }); continue;
    }
    if (s.list) {
      const r = await rpc('tools/list', {}, 60000);
      const tools = (r.result && r.result.tools) || [];
      out({ case: 'tools/list', ok: !!r.result, count: tools.length,
            tools: tools.filter(t => !s.filter || new RegExp(s.filter).test(t.name))
                        .map(t => ({ name: t.name, props: Object.keys((t.inputSchema && t.inputSchema.properties) || {}) })) });
      continue;
    }
    const r = await rpc('tools/call', { name: s.call, arguments: s.args || {} }, s.ms || 30000);
    const c = r.result && r.result.content;
    const text = Array.isArray(c) ? c.map(x => x.text || '').join(' ') : '';
    out({ case: s.id, tool: s.call, ok: !!r.result, isError: !!(r.result && r.result.isError), text: text.slice(0, 600),
          error: r.error ? (r.error.message || JSON.stringify(r.error)).slice(0, 300) : (r.timeout ? 'timeout' : null) });
  }
  out({ case: 'stderr_tail', text: stderr.slice(-800) });
  srv.kill('SIGTERM'); setTimeout(() => process.exit(0), 500);
})();
