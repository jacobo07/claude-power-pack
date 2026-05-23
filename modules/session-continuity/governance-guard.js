// <module>/governance-guard.js
// PreToolUse: fail-closed on (a) *.jsonl shadow-rename, (b) re-creating a /resume override.
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  let j = {}; try { j = JSON.parse(input || '{}'); } catch (_) { process.exit(0); }
  const t = j.tool_input || {};
  const cmd = String(t.command || '');
  const fp = String(t.file_path || '').replace(/\\/g, '/');
  const shadow = /mv\s+\S+\.jsonl\s+\S+\.jsonl\.live/.test(cmd) || /\.jsonl\.live/.test(cmd);
  const override = /\/\.claude\/commands\/resume\.md$/.test(fp);
  if (shadow || override) {
    console.error('[session-continuity:governance-guard] BLOCKED: ' +
      (shadow ? '.jsonl shadow-rename forbidden (Lazarus v3 root cause)' :
                'native /resume override forbidden — UI is canonical'));
    process.exit(2);
  }
  process.exit(0);
});
