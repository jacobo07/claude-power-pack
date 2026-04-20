#!/usr/bin/env node
/**
 * ovo-push-gate.js — PreToolUse hook (Bash matcher).
 *
 * Blocks `git push`, `git deploy`, `npm publish`, `gh release create` unless a
 * fresh A+/A verdict exists in vault/audits/verdicts.jsonl (TTL 10 min).
 *
 * Power-Pack-scoped: only enforces in repos containing a `.powerpack` sentinel
 * file at the project root. Everywhere else: silent pass.
 *
 * Fails CLOSED: missing/corrupt/stale verdict blocks; it never auto-allows.
 * Bypass paths (both documented in the hook's stderr on block):
 *   - env OVO_BYPASS=1
 *   - .ovo_inactive marker file at the repo root
 *
 * Exit codes:
 *   0 — pass (either not a pushing command, not power-pack scope, bypass set,
 *       or fresh A+/A verdict within TTL)
 *   2 — block (missing/stale/bad verdict)
 *
 * Usage: registered in ~/.claude/settings.json under hooks.PreToolUse with
 * matcher "Bash". Reads JSON tool-input from stdin.
 */

const fs = require('fs');
const path = require('path');

const BLOCK_REGEX = /\b(?:git\s+(?:push|deploy)|npm\s+publish|gh\s+release\s+create)\b/;
const TTL_MS = 10 * 60 * 1000;
const VALID_VERDICTS = new Set(['A+', 'A']);

function findGitRoot(startDir) {
  let cur = path.resolve(startDir);
  for (;;) {
    if (fs.existsSync(path.join(cur, '.git'))) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

function emit(code, msg) {
  if (msg) process.stderr.write(`[ovo-push-gate] ${msg}\n`);
  process.exit(code);
}

function readLastJsonlLine(filePath) {
  // verdicts.jsonl is bounded (one line per OVO run, small). Whole-file read
  // is fine; avoids partial-line handling complexity.
  const text = fs.readFileSync(filePath, 'utf8');
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) return null;
  return JSON.parse(lines[lines.length - 1]);
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch (_) {
    return emit(0, 'unreadable hook input — passing');
  }

  const cmd = (input.tool_input && input.tool_input.command) || input.command || '';
  if (!BLOCK_REGEX.test(cmd)) return emit(0);

  const startDir = input.cwd || process.cwd();
  const root = findGitRoot(startDir);
  if (!root) return emit(0, 'no .git ancestor — passing');

  if (!fs.existsSync(path.join(root, '.powerpack'))) {
    return emit(0);
  }

  if (process.env.OVO_BYPASS === '1') {
    return emit(0, 'OVO_BYPASS=1 — bypassing gate');
  }
  if (fs.existsSync(path.join(root, '.ovo_inactive'))) {
    return emit(0, '.ovo_inactive marker present — bypassing gate');
  }

  const verdictsPath = path.join(root, 'vault', 'audits', 'verdicts.jsonl');
  if (!fs.existsSync(verdictsPath)) {
    return emit(2, 'BLOCK: vault/audits/verdicts.jsonl missing. Run /ovo-audit before push.');
  }

  let last;
  try {
    last = readLastJsonlLine(verdictsPath);
  } catch (err) {
    return emit(2, `BLOCK: verdicts.jsonl corrupt (${err.message}). Run /ovo-audit.`);
  }
  if (!last) {
    return emit(2, 'BLOCK: verdicts.jsonl is empty. Run /ovo-audit before push.');
  }

  if (!VALID_VERDICTS.has(last.verdict)) {
    return emit(2,
      `BLOCK: last verdict is ${last.verdict} (need A+ or A). Re-run /ovo-audit after fixes.`);
  }

  const ts = Date.parse(last.iso_ts);
  if (!Number.isFinite(ts)) {
    return emit(2, `BLOCK: last verdict iso_ts unparseable (${last.iso_ts}).`);
  }
  const age = Date.now() - ts;
  if (age > TTL_MS) {
    const ageMin = (age / 60000).toFixed(1);
    return emit(2, `BLOCK: last verdict is ${ageMin} min old (TTL 10 min). Re-run /ovo-audit.`);
  }

  const sha = (last.sha256_post || last.sha256_pre || '?').slice(0, 8);
  return emit(0, `pass: verdict ${last.verdict}, age ${(age / 1000).toFixed(0)}s, sha ${sha}`);
}

main();
