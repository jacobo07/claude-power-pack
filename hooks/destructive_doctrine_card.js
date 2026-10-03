#!/usr/bin/env node
// PreToolUse (Bash|PowerShell) -- the destructive-state-authorization doctrine card.
//
// WHY THIS EXISTS. On 2026-09-29 the rule `destructive-state-authorization` left the always-loaded
// prefix (~/.claude/rules) and became an on-demand Power Pack skill, after the P3 ablation measured no
// quality loss without it (REPORT.md). The same measurement showed a moved rule is NOT loaded by the
// model on its own: the two rules moved first were invoked in 0 of 8 verification runs. For most rules
// that is an accepted cost. For this one the failure is irreversible, so the rule must reach the moment
// of use by an EVENT, not by the model remembering to ask for it.
//
// WHAT IT DOES. The first time in a session that a shell command matches a destructive shape, the
// command is DENIED once with the core of the doctrine as the reason, and the model is told to load the
// skill and re-issue the command if it is still right. Later destructive commands in the same session
// pass: the card has been read, and a gate that blocks every `rm` would be switched off within a week.
//
// SHAPE. `permissionDecision:'deny'`, never `{continue:false}` -- the latter halts the agent and is the
// measured cross-repo dead screen (see cascade_check_bash.js defect (1)). Fail-OPEN on every internal
// error: this is a reminder, not the protection; cascade_check_bash.js keeps enforcing its registry.
//
// APERTURE, stated so nobody reads a pass as "nothing destructive happened": shell commands only.
// Deletion done from inside a program (os.remove, fs.unlinkSync, an ORM delete) is not seen. Heredoc and
// here-string bodies are elided first -- they are script text being WRITTEN, often to another machine.
//
// Kill switch: CLAUDE_DESTRUCTIVE_CARD=off. State: DESTRUCTIVE_CARD_STATE_DIR (tests) or
// ~/.claude/state/destructive-card/. Every judgement is appended to ledger.jsonl, so "did it run?"
// is one read (guard-event-reachability: build the counter before you need it).
'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const STATE_DIR = process.env.DESTRUCTIVE_CARD_STATE_DIR
  || path.join(os.homedir(), '.claude', 'state', 'destructive-card');

// Each entry: [name, pattern]. Matched against the command with literal bodies elided.
const SHAPES = [
  ['rm', /(?:^|[\s;&|(`])rm\s+/],
  ['Remove-Item', /\b(?:Remove-Item|rmdir|rd\s+\/s|del\s|erase\s)/i],
  ['git reset --hard', /\bgit\b[^\n;|&]*\breset\s+[^\n;|&]*--hard\b/],
  ['git clean -f', /\bgit\b[^\n;|&]*\bclean\s+-[a-zA-Z]*f/],
  ['git checkout/restore of paths', /\bgit\b[^\n;|&]*\b(?:checkout\s+(?:[^\n;|&]*\s)?--\s|restore\s)/],
  ['git push --force', /\bgit\b[^\n;|&]*\bpush\b[^\n;|&]*(?:--force\b|\s-f\b|--force-with-lease\b)/],
  ['git branch -D', /\bgit\b[^\n;|&]*\bbranch\s+[^\n;|&]*-D\b/],
  ['git stash drop/clear', /\bgit\b[^\n;|&]*\bstash\s+(?:drop|clear)\b/],
  ['git worktree remove', /\bgit\b[^\n;|&]*\bworktree\s+remove\b/],
  ['SQL destroy', /\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE|DELETE\s+FROM)\b/i],
  ['rmtree', /\bshutil\.rmtree\b/],
];

const CARD = [
  'destructive-state-authorization -- this command was NOT run (shown once per session).',
  'Before re-issuing it, answer:',
  '1. What exact state is being destroyed, and is it still the state that was reviewed? Identity is the',
  '   content actually on disk, not a timestamp, a size or a commit id.',
  '2. Could it hold work nobody looked at -- another pane, an autosave, an editor, an uncommitted change?',
  '3. Is it recoverable elsewhere (a commit, a backup)? If not, back it up first.',
  '4. For a batch: re-check each item immediately before its own deletion, and report what was actually',
  '   deleted, not what was requested.',
  '5. If the state moved, stop and say so; refusing is not failing.',
  'Full rule: invoke the `destructive-state-authorization` skill. If the command is still right, re-issue',
  'it unchanged -- it will not be stopped again this session. Do NOT end the turn here: say what you are',
  'doing next.',
].join('\n');

function elideLiteralBodies(cmd) {
  // Same contract as cascade_check_bash.js: a local execution sink means the body can run here.
  const LOCAL_SINK = /(?:\bInvoke-Expression\b|\biex\b\s|\|\s*(?:bash|sh|zsh)\b(?![^\n]*\bssh\b))/i;
  if (LOCAL_SINK.test(cmd)) return cmd;
  return cmd
    .replace(/@(['"])[\s\S]*?\1@/g, "'<here-string body elided>'")
    .replace(/<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1[\s\S]*?^[ \t]*\2[ \t]*$/gm, '<<HEREDOC_BODY_ELIDED');
}

function match(command) {
  const text = elideLiteralBodies(command);
  for (const [name, re] of SHAPES) if (re.test(text)) return name;
  return null;
}

function ledger(rec) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.appendFileSync(path.join(STATE_DIR, 'ledger.jsonl'), JSON.stringify({ ts: new Date().toISOString(), ...rec }) + '\n');
  } catch (_) { /* a receipt failure must not change the verdict */ }
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

async function main() {
  if ((process.env.CLAUDE_DESTRUCTIVE_CARD || '').toLowerCase() === 'off') return emit({ continue: true });
  let payload = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) payload += chunk;
  } catch (_) {
    return emit({ continue: true });
  }
  if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1); // PS 5.1 BOM on the pipe
  let req;
  try {
    req = JSON.parse(payload);
  } catch (_) {
    ledger({ decision: 'unparsed' });
    return emit({ continue: true });
  }
  if (!['Bash', 'PowerShell'].includes(req.tool_name || '')) return emit({ continue: true });
  const command = String((req.tool_input || {}).command || '');
  const shape = command.trim() ? match(command) : null;
  const session = String(req.session_id || 'unknown').replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 80);
  if (!shape) {
    ledger({ decision: 'pass', session });
    return emit({ continue: true });
  }
  const flag = path.join(STATE_DIR, `shown-${session}`);
  if (fs.existsSync(flag)) {
    ledger({ decision: 'pass-already-shown', session, shape });
    return emit({ continue: true });
  }
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(flag, new Date().toISOString());
  } catch (_) {
    // Could not record that the card was shown: denying now would deny forever. Fail open.
    ledger({ decision: 'pass-unrecordable', session, shape });
    return emit({ continue: true });
  }
  ledger({ decision: 'deny-card', session, shape });
  return emit({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: `[${shape}] ${CARD}`,
    },
  });
}

main().catch(() => emit({ continue: true }));
// LINEAGE (skill-capability pillar G): this card is compiled out of the skill named on the next line. When that
// skill changes, re-read it and re-derive the card text and this line together; tools/card_lineage.py fails until then.
// COMPILED-FROM: skill=destructive-state-authorization source=skills/destructive-state-authorization/SKILL.md sha256=2985bd97002abf0589a95080a7d29b447b7a703df9ccd319494dba45701cd0de commit=7f985799916ce6e12cbdc6e2495c47065366c14b
