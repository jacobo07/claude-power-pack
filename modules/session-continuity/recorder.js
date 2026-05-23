// <module>/recorder.js
// SessionStart hook: records {slot,project_id,session_id,cwd,ts,pid}. Never touches *.jsonl.
const R = require('./lib/registry');
if (process.env.LAZARUS_REG_ROOT) R._setRoot(process.env.LAZARUS_REG_ROOT);

function sanitize(cwd) {
  return String(cwd || '')
    .replace(/[\\/:]/g, '-')
    .replace(/[^A-Za-z0-9.-]/g, '-')
    .replace(/^-+/, 'C--')
    .replace(/-+$/, '');
}
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  let j = {};
  try { j = JSON.parse(input || '{}'); } catch (_) { /* malformed stdin: ignore, still record */ }
  const slot = process.env.LAZARUS_TERMINAL_KEY || ('pid:' + process.ppid);
  try {
    R.upsert({
      slot,
      project_id: sanitize(j.cwd),
      session_id: j.session_id || null,
      cwd: j.cwd || process.cwd(),
      pid: process.ppid,
    });
  } catch (_) { /* fail-open: never break the session over a registry write */ }
  process.exit(0);
});
