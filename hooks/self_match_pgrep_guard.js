#!/usr/bin/env node
// PreToolUse Bash: deny `pgrep -f` / `pkill -f` whose pattern matches the command's own text.
// The Bash tool runs `bash -c "... eval '<command>'"`, so such a pattern always finds the wrapper shell:
// a wait loop never ends, a pkill kills the caller. Spec: vault/specs/self-match-pgrep-guard.md. Fails open.
'use strict';

const OPTS_WITH_ARG = new Set(['-d', '-g', '-G', '-P', '-s', '-t', '-u', '-U', '-F', '--ns', '--nslist',
  '--signal', '--delimiter', '--pgroup', '--group', '--parent', '--session', '--terminal', '--euid', '--uid',
  '--pidfile']);

function tokenize(seg) {
  const out = [];
  let cur = '', q = null, has = false;
  for (let i = 0; i < seg.length; i++) {
    const c = seg[i];
    if (q) {
      if (c === q) { q = null; continue; }
      // bash keeps the backslash inside double quotes except before $ ` " \ newline (review F4)
      if (c === '\\' && q === '"' && i + 1 < seg.length && '$`"\\\n'.includes(seg[i + 1])) { cur += seg[++i]; continue; }
      cur += c; continue;
    }
    if (c === '"' || c === "'") { q = c; has = true; continue; }
    if (/\s/.test(c)) { if (cur || has) out.push(cur); cur = ''; has = false; continue; }
    if (c === '\\' && i + 1 < seg.length) { cur += seg[++i]; continue; }
    cur += c;
  }
  if (cur || has) out.push(cur);
  return out;
}

// Only a pgrep/pkill in COMMAND position runs; one inside prose (a commit message, an echo) does not (review F3).
// The opening quote of `bash -c '...'` / `eval '...'` counts as command position: that is the S17 stall shape.
const KEYWORD_BEFORE = /(^|[\s;&|(])(until|while|if|do|then|else|elif|time|exec|nohup|sudo|command|watch|xargs)$/;
function inCommandPosition(prefix) {
  const p = prefix.replace(/\s+$/, '');
  return p === '' || /[;&|(`!{\n]$/.test(p) || KEYWORD_BEFORE.test(p) ||
    /(^|\s)timeout(\s+-\S+)*\s+\S+$/.test(p) || /((^|\s)-c|(^|[\s;&|(])eval)\s*['"]$/.test(p);
}

// Each pgrep/pkill invocation: the text up to the next unquoted shell separator.
function invocations(cmd) {
  const res = [];
  const re = /(^|[\s;&|(`!'"])(pgrep|pkill)(?=\s)/g;
  let m;
  while ((m = re.exec(cmd)) !== null) {
    if (!inCommandPosition(cmd.slice(0, m.index + m[1].length))) continue;
    const start = m.index + m[0].length;
    let q = null, j = start;
    for (; j < cmd.length; j++) {
      const c = cmd[j];
      if (q) { if (c === q) q = null; else if (c === '\\' && q === '"') j++; continue; }
      if (c === '"' || c === "'") { q = c; continue; }
      if (c === '\\') { j++; continue; }
      if (';&|)\n`>'.includes(c)) break;
    }
    res.push({ tool: m[2], args: tokenize(cmd.slice(start, j)) });
  }
  return res;
}

function patternOf(args) {
  let full = false, pattern = null;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--full') { full = true; continue; }
    if (a === '--') { if (pattern === null && i + 1 < args.length) pattern = args[i + 1]; break; }   // review F1
    if (OPTS_WITH_ARG.has(a)) { i++; continue; }
    if (/^--[a-z-]+=/.test(a)) continue;
    // pkill signal: -9, -TERM, -HUP, -USR1, -SIGUSR1 (all caps, 3+ chars; checked before flag clusters) (review F1)
    if (/^-\d+$/.test(a) || /^-[A-Z][A-Z0-9]+$/.test(a)) continue;
    // flag cluster: -f, -af, -fu <user>; an argument-taking letter at the END of a cluster takes the next token (F2)
    if (/^-[A-Za-z]+$/.test(a)) { if (a.includes('f')) full = true; if (/[dgGPstuUF]$/.test(a)) i++; continue; }
    if (pattern === null) pattern = a;
  }
  return full ? pattern : null;
}

function verdict(command) {
  for (const inv of invocations(command)) {
    const pat = patternOf(inv.args);
    if (!pat || /[$`]/.test(pat)) continue;
    let rx;
    try { rx = new RegExp(pat); } catch (_) { continue; }
    if (rx.test(command)) return { tool: inv.tool, pattern: pat };
  }
  return null;
}

function main(raw) {
  let input;
  try { input = JSON.parse(raw || '{}'); } catch (_) { return null; }
  if (!input || input.tool_name !== 'Bash') return null;
  const cmd = String((input.tool_input || {}).command || '');
  if (!/\b(pgrep|pkill)\b/.test(cmd)) return null;
  const v = verdict(cmd);
  if (!v) return null;
  const first = v.pattern.replace(/^(\W*)(\w)/, '$1[$2]');
  return {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason:
        `SELF-MATCHING ${v.tool} -f: the pattern "${v.pattern}" matches this command's own text, and the Bash tool ` +
        `runs it inside a shell whose command line holds that text. ${v.tool === 'pkill' ? 'pkill would kill your own shell.' : 'pgrep always finds that shell, so a wait loop never ends (S17 W2 stall, 2026-11-07).'} ` +
        `Use a pattern that cannot match itself, e.g. "${first}", or wait on a pid (PID=$!; while kill -0 $PID; do sleep 30; done), ` +
        `or on a sentinel line in the run's log. Spec: vault/specs/self-match-pgrep-guard.md`,
    },
  };
}

if (require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (d) => { raw += d; });
  process.stdin.on('end', () => {
    let out = null;
    try { out = main(raw); } catch (_) { out = null; }
    if (out) process.stdout.write(JSON.stringify(out));
    process.exit(0);
  });
}

module.exports = { main, verdict, patternOf, invocations };
