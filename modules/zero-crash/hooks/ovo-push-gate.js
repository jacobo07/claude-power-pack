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

// Match only at a command boundary (start-of-string, or after a shell separator
// like `;`, `|`, `&`, `\n`, `(`, or a backtick subshell). Prevents false positives
// where the tokens appear as literals inside quoted strings — e.g.
// `echo 'git push' | node hook.js` must NOT trigger the gate.
const BLOCK_REGEX = /(?:^|[;|&\n(`])\s*(?:git\s+(?:push|deploy)|npm\s+publish|gh\s+release\s+create)\b/;
const TTL_MS = 10 * 60 * 1000;

// Push AUTHORITY (Resource Residency W0, 2026-11-21). The 2026-11-20 23:53 push ran `& $g push -u origin <branch>`
// from the PowerShell tool: git called through a variable, which BLOCK_REGEX cannot see -- and the host's own Woz
// advisory tells agents to call git by full path. The same day BLOCK_REGEX blocked a command that only QUOTED the
// word pair inside a here-string. Detection therefore (1) blanks here-string bodies and quoted strings to Q first,
// (2) accepts git by name, path, variable or quoted path, with any flags (-C <dir>) before `push`.
const GIT_PUSH_REGEX = /(?:^|[;|\n(`{]|&&|\|\|)\s*(?:&\s*)?(?:[^\s;|&]*git(?:\.exe)?|\$[\w:]+|Q)(?:\s+(?!push\b)[^\s;|&]+)*\s+push\b/i;
const OTHER_PUBLISH_REGEX = /(?:^|[;|\n(`{]|&&|\|\|)\s*(?:npm\s+publish|gh\s+release\s+create)\b/i;

function blankQuoted(cmd) {
  return String(cmd)
    .replace(/@'[\s\S]*?'@/g, 'Q').replace(/@"[\s\S]*?"@/g, 'Q')      // PowerShell here-strings
    .replace(/<<-?\s*['"]?(\w+)['"]?[\s\S]*?\n\1\b/g, 'Q')             // shell heredocs
    .replace(/'[^'\n]*'/g, 'Q').replace(/"(?:[^"\\\n]|\\.)*"/g, 'Q');
}

function isPushShaped(cmd) {
  const b = blankQuoted(cmd);
  return GIT_PUSH_REGEX.test(b) || OTHER_PUBLISH_REGEX.test(b);
}

function pushAuthority(sessionId) {
  // Same semantics as tools/push_authority.py decide() (the owner of grant/revoke and of the pre-push layer),
  // evaluated IN-PROCESS: spawning python measured 19.4 s cold at 1.8 GB free RAM (2026-11-21), past this step's
  // 5 s dispatcher timeout, and a timed-out step fails open. Node scans the 670 records in 160-240 ms.
  // Parity is pinned by tools/test_push_authority.py, which drives both layers on the same fixtures.
  // An unreadable record is UNKNOWN (it could be this worker's): with no match elsewhere it refuses.
  const sid = String(sessionId || '').trim();
  if (sid.length < 8) return { allow: true };
  const dir = process.env.GSD_LONG_RUN_STATE_DIR || path.join(require('os').homedir(), '.claude', 'state');
  const missions = [];
  const unreadable = [];
  let names;
  try {
    names = fs.readdirSync(dir).filter((f) => /^gsd-mission-m-.*\.json$/.test(f));
  } catch (e) {
    return { allow: false, reason: `push authority UNKNOWN (state dir unreadable: ${e.code || e.message}); refusing` };
  }
  for (const f of names) {
    let text;
    try {
      text = fs.readFileSync(path.join(dir, f), 'utf8');
    } catch (e) {
      unreadable.push(`${f}:${e.code || 'ERR'}`);
      continue;
    }
    if (text.includes(sid)) missions.push(f.slice('gsd-mission-'.length, -'.json'.length));
  }
  if (!missions.length && unreadable.length) {
    return { allow: false, reason: `push authority UNKNOWN (unreadable mission records: ${unreadable.slice(0, 3).join(', ')}); refusing` };
  }
  if (!missions.length) return { allow: true };
  const gpath = path.join(dir, 'push-authority.json');
  let grants = {};
  if (fs.existsSync(gpath)) {
    try {
      grants = JSON.parse(fs.readFileSync(gpath, 'utf8'));
    } catch (e) {
      return { allow: false, reason: `push authority UNKNOWN (grants file unreadable: ${e.message}); refusing` };
    }
  }
  if (missions.some((m) => grants[m])) return { allow: true };
  return { allow: false, reason: `session ${sid.slice(0, 8)} is a worker of ${missions.join(', ')} and no push authority `
    + 'was granted. Commit only; the Owner grants with `python tools/push_authority.py grant --mission <id> --reason ...`.' };
}
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
  if (!isPushShaped(cmd)) return emit(0);

  // Authority first, in EVERY repo (not only .powerpack ones), and not bypassable by OVO_BYPASS.
  const auth = pushAuthority(input.session_id || process.env.CLAUDE_CODE_SESSION_ID || '');
  if (!auth.allow) return emit(2, `BLOCK (push authority): ${auth.reason}`);

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
