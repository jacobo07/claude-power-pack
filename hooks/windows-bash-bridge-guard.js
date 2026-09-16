#!/usr/bin/env node
/**
 * windows-bash-bridge-guard.js — PreToolUse hook on Bash.
 *
 * Sealed 2026-05-22 after the v620000.0 rebase incident: a `git pull --rebase`
 * launched via Bash background froze 6 git zombies for 100+ minutes because
 * the Git Bash / MSYS2 bridge dropped stdout on long-running git operations.
 * This hook is the enforcement arm of ~/.claude/CLAUDE.md → "Windows Bash
 * Bridge Reliability".
 *
 * ---------------------------------------------------------------------------
 * APERTURE EXTENSION 2026-09-02 (CostaLuz Lawyers session 84e33994).
 * ---------------------------------------------------------------------------
 * MEASURED, not theorised. A turn died mid-work; the Owner reported the same
 * dead screen "en todos mis repos". The forensic answer had three parts, and
 * the third is the one that matters:
 *
 *   1. `closer-guard.js` — the documented mechanical fix for dead screens — is
 *      a **Stop** hook. `~/.claude/logs/closer-guard-state.json` held NO entry
 *      for the hung session: every entry was a synthetic self-test or another
 *      session. It did not fail. It never ran. A turn that HANGS never reaches
 *      Stop, so a Stop hook is structurally blind to the entire hang family. It
 *      can only repair an ugly ENDING, never a missing one. Eleven classes of
 *      closer hardening were optimising the family that was already covered.
 *
 *   2. This guard COULD have prevented it — PreToolUse is the only layer that
 *      runs before the transport dies — but its aperture was wrong. It matched
 *      six program names chosen for VERBOSE OUTPUT (git/mix/gh/npm/pnpm/
 *      corepack) and missed every token that actually hung:
 *          `grep -rn ...`        first token `grep`   → not in the list
 *          `sed -n '1,60p' ...`  first token `sed`    → not in the list
 *          `python - <<'PY'`     first token `python` → CLAUDE.md calls this
 *                                MANDATORY PowerShell; the list never had it
 *          `... && grep -n ...`  second chunk         → only chunk 1 was read
 *
 *   3. ROOT CAUSE, and why it recurs in every repo regardless of how many times
 *      it is written down: the harness "auto mode" directive instructs, in
 *      plain words, *"read files with cat, head, or sed -n, search with grep
 *      and find, and make file changes with sed, heredocs ... rather than using
 *      the dedicated Read, Edit, or Write tools."* That is character-for-
 *      character the set this host's MSYS2 bridge hangs on. It is a DIRECTIVE
 *      COLLISION, not a lapse of memory: the harness instruction is
 *      host-independent, the hang is Windows-specific, so the collision fires
 *      in every repository and no amount of prose in CLAUDE.md resolves it —
 *      prose is advisory to a model that is already mid-instruction. Only a
 *      PreToolUse block executes regardless.
 *
 * Hence two enforced classes:
 *   A. MANDATORY_POWERSHELL — programs CLAUDE.md already routes to PowerShell.
 *   B. V15_READ_TOKEN      — the v15 token blocklist (cat/head/tail/grep/find/
 *      ls/wc/sed/awk), each of which has a dedicated bridge-free tool. The
 *      blocklist says "REJECT at plan time"; this makes that mechanical.
 *
 * Every chunk of a `&&` / `||` / `;` / `|` chain is inspected, not just the
 * first — CLAUDE.md's wording is "STARTS WITH **or contains in a chained
 * pipe**", and the chained-pipe shape is the documented dead-screen sentinel.
 * Heredoc BODIES are excluded from scanning so that prose inside a `<<'PY'`
 * payload cannot produce a false positive.
 *
 * DESIGN CONSTRAINTS (each load-bearing):
 *   - Fail-OPEN absolute. Any parse error / unexpected shape → pass. A buggy
 *     guard must never brick the workflow.
 *   - Kill switch: CLAUDE_BASH_GUARD=off.
 *   - Escape markers still honoured, but now LOGGED. "A guard's exemption is
 *     where its defect lives" (closer-guard.js). An exemption nobody can audit
 *     is indistinguishable from an absent rule, so every use is recorded to
 *     ~/.claude/state/bash-bridge-guard-escapes.log for the Owner to review.
 *   - Blocks are logged too, so the question "did this gate ever fire?" is
 *     answerable with an instrument rather than an assumption.
 *
 * Self-test (two-way, drives BOTH branches):
 *   node ~/.claude/hooks/tests/test-bash-bridge-guard-v15.js
 *
 * Input  (PreToolUse contract): { tool_name:"Bash", tool_input:{ command:"..." } }
 * Output: stdout JSON { decision:"block", reason } + exit 2 on block; else exit 0.
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const STATE_DIR = path.join(os.homedir(), ".claude", "state");

function logLine(file, line) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.appendFileSync(path.join(STATE_DIR, file), `${new Date().toISOString()}\t${line}\n`);
  } catch { /* logging is an optimisation, never a requirement */ }
}

// --- Classes ---------------------------------------------------------------

// CLAUDE.md → "Rule: on Windows hosts, default to the PowerShell tool for:"
// git / mix / gh / node / npm / pnpm / corepack / python / pytest / pip / uv.
// R269: `node` was named in the comment above and MISSING from the Set below, so
// the file asserted a rule it did not enforce. A comment and a Set that disagree
// are not a style problem -- the comment is what a reader audits against, so the
// gap reads as covered and nobody looks again. CLAUDE.md qualifies this one as
// "node (when output is verbose)", which the guard cannot evaluate before running
// the command, and the failure is asymmetric: blocking a quiet `node` costs one
// pivot to PowerShell, while letting a verbose one through is the MSYS2 stdout
// drop this guard exists to prevent. So the unconditional reading is correct, and
// it is also the one the comment already claimed.
const MANDATORY_POWERSHELL = new Set([
  "git", "mix", "gh", "node", "npm", "pnpm", "corepack",
  "python", "python3", "py", "pytest", "pip", "pip3", "uv",
]);

// CLAUDE.md → "v15 token blocklist ... REJECT at plan time".
const V15_READ_TOKENS = new Set([
  "cat", "head", "tail", "grep", "rg", "find", "ls", "wc", "sed", "awk",
]);

// `wc -l file` is explicitly sanctioned SOLO in its batch, so it is advisory
// rather than blocked — the harm is the pipe and the batching, not the token.
const V15_ADVISORY_ONLY = new Set(["wc"]);

const PIVOT = {
  cat: "Read (direct)",
  head: "Read with `limit = N`",
  tail: "Read with `offset = <total> - N` (get the line count first if needed)",
  grep: "the Grep tool — dedicated, bridge-free",
  rg: "the Grep tool — dedicated, bridge-free",
  find: "the Glob tool — dedicated, bridge-free",
  ls: "the Glob tool, e.g. `Glob 'dir/*'`",
  sed: "Edit for mutations; Read for `sed -n 'A,Bp'`",
  awk: "Read + reasoning, or the PowerShell tool",
  wc: "Bash SOLO in its batch — never inside a pipe, never batched with Grep/Read",
};

const ESCAPE_MARKERS = ["# bash-safe", "--mc-bridge-ok", "# heredoc-required"];

// --- Parsing ---------------------------------------------------------------

/** Blank the CONTENT of quoted spans, preserving length, so that separators
 *  and command-looking words inside quotes never create phantom chunks. */
function maskQuotes(s) {
  return s
    .replace(/'[^']*'/g, (m) => `'${"x".repeat(Math.max(0, m.length - 2))}'`)
    .replace(/"(?:[^"\\]|\\.)*"/g, (m) => `"${"x".repeat(Math.max(0, m.length - 2))}"`);
}

/** Everything before the first heredoc opener. A `<<'PY' ... PY` body is
 *  arbitrary payload text, not shell commands; scanning it yields only false
 *  positives. The tokens that matter (`python`, `cat`) precede the opener. */
function scannablePrefix(cmd) {
  const m = cmd.match(/<<-?\s*['"]?[A-Za-z_][A-Za-z0-9_]*['"]?/);
  return m ? cmd.slice(0, m.index) : cmd;
}

const LEADING_NOISE = [
  /^cd\s+(?:"[^"]*"|'[^']*'|\S+)\s*$/i, // a bare `cd path` chunk carries no verb
  /^(?:sudo|time|command|exec|nohup|env)\s+/i,
];

/** First meaningful token of one chunk, or "" if the chunk carries no verb. */
function chunkToken(rawChunk) {
  let c = rawChunk.trim();
  if (!c) return "";
  c = c.replace(/^[({!]\s*/, "");
  // leading env assignments: FOO=bar BAZ=qux cmd
  c = c.replace(/^(?:\w+=(?:"[^"]*"|'[^']*'|\S*)\s+)+/, "");
  c = c.replace(/^export\s+\w+=\S*\s*$/i, "");
  for (const re of LEADING_NOISE) {
    if (re.test(c)) c = c.replace(re, "");
  }
  c = c.trim();
  if (!c) return "";
  const tok = (c.match(/^(\S+)/) || [])[1] || "";
  // strip a path prefix: /usr/bin/grep → grep, ./foo.sh stays ./foo.sh
  const base = tok.includes("/") && !tok.startsWith("./") ? tok.split("/").pop() : tok;
  return base.toLowerCase();
}

/** Every chunk's leading token, in order. */
function chunkTokens(command) {
  const scanned = maskQuotes(scannablePrefix(command));
  return scanned
    .split(/&&|\|\||;|\||\n/)
    .map(chunkToken)
    .filter(Boolean);
}

// --- Classification --------------------------------------------------------

/**
 * @returns null when the command is fine, else
 *   { cls, token, position, chained }  — `position` is 0-based chunk index.
 */
function classifyCommand(command) {
  if (!command || !command.trim()) return null;

  // A POSIX-only script is exactly what Bash is for.
  if (/\bbash\s+\S+\.sh\b/i.test(command) || /^\.\/\S+\.sh\b/.test(command.trim())) {
    return null;
  }

  const tokens = chunkTokens(command);
  if (!tokens.length) return null;

  // Class A first: it names a program with a documented freeze history and a
  // one-line native pivot, so it is the more actionable verdict when a command
  // trips both (`grep ... && python ...`).
  for (let i = 0; i < tokens.length; i++) {
    if (MANDATORY_POWERSHELL.has(tokens[i])) {
      return { cls: "MANDATORY_POWERSHELL", token: tokens[i], position: i, chained: tokens.length > 1 };
    }
  }
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (!V15_READ_TOKENS.has(t)) continue;
    // `wc` alone is sanctioned; `wc` in a chain is not.
    if (V15_ADVISORY_ONLY.has(t) && tokens.length === 1) continue;
    return { cls: "V15_READ_TOKEN", token: t, position: i, chained: tokens.length > 1 };
  }
  return null;
}

// --- Reasons ---------------------------------------------------------------

function powershellEquivalent(token, command) {
  const rest = command.replace(new RegExp(`^.*?\\b${token}\\s+`, "is"), "");
  if (token === "git") {
    return ["  $g = 'C:\\Program Files\\Git\\cmd\\git.exe'", `  & $g ${rest}`].join("\n");
  }
  if (token === "mix") return `  & 'C:\\Program Files\\Elixir\\bin\\mix.bat' ${rest}`;
  if (["python", "python3", "py", "pytest", "pip", "pip3", "uv"].includes(token)) {
    return [
      "  $env:PYTHONIOENCODING='utf-8';",
      "  Set-Location '<absolute repo path>';",
      "  & 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' <script.py>",
    ].join("\n");
  }
  return `  & ${token} ${rest}`;
}

function reasonFor(v, command) {
  const head = [
    `Windows Bash Bridge Guard BLOCKED '${v.token}'` +
      (v.position > 0 ? ` (chunk ${v.position + 1} of a chained command)` : "") + ".",
    "",
  ];

  if (v.cls === "MANDATORY_POWERSHELL") {
    return head.concat([
      "Why: the Git Bash / MSYS2 bridge on Windows intermittently drops stdout",
      "for long-running or long-output commands. 13+ documented freezes across",
      "InfinityOps / TUA-X / KobiiCraft / CostaLuz. PowerShell-native has zero.",
      "",
      "~/.claude/CLAUDE.md routes this program to the PowerShell tool. That is",
      "a MANDATORY rule, not a preference.",
      "",
      "PowerShell equivalent:",
      powershellEquivalent(v.token, command),
      "",
      escapeHelp(),
    ]).join("\n");
  }

  return head.concat([
    `Why: '${v.token}' is on the CLAUDE.md **v15 token blocklist** — "REJECT at`,
    'plan time (not at retry-after-fail time)". Every token on that list has a',
    "dedicated tool that does not cross the MSYS2 bridge at all.",
    "",
    `PIVOT for '${v.token}' → ${PIVOT[v.token] || "the dedicated tool"}.`,
    "",
    v.chained
      ? "This command CHAINS (`&&`/`|`). The chained-pipe Bash shape combined with\n" +
        "a same-turn <task-notification> is the documented dead-screen hang: the\n" +
        "turn closes with no assistant text and only ESC recovers. That is the\n" +
        "exact failure this guard exists to make impossible."
      : "Prefer the dedicated tool even for a single call — results integrate with\n" +
        "the permission UI and file links, and cannot hang the bridge.",
    "",
    "Note: the harness 'auto mode' directive asks for cat/head/sed/grep/heredocs",
    "over the dedicated tools. On a Windows host that directive collides with",
    "this one, and ~/.claude/CLAUDE.md wins — its instructions OVERRIDE default",
    "behaviour by their own terms. This block is that precedence, executed.",
    "",
    escapeHelp(),
  ]).join("\n");
}

function escapeHelp() {
  return [
    "If Bash is genuinely required (POSIX-only .sh, no tool equivalent), add an",
    "escape marker — every use is logged for audit:",
    "  - `# bash-safe`      - `--mc-bridge-ok`      - `# heredoc-required`",
    "Kill switch for the whole guard: CLAUDE_BASH_GUARD=off",
  ].join("\n");
}

// --- Runner (pure; no process.exit, so tests can drive both branches) ------

function run(input, opts) {
  try {
    const platform = (opts && opts.platform) || process.platform;
    if (platform !== "win32") return { block: false, why: "not-windows" };
    if (String(process.env.CLAUDE_BASH_GUARD || "").toLowerCase() === "off") {
      return { block: false, why: "kill-switch" };
    }
    if (!input || input.tool_name !== "Bash") return { block: false, why: "not-bash" };

    const command = (input.tool_input && input.tool_input.command) || "";
    if (!command.trim()) return { block: false, why: "empty" };

    const lower = command.toLowerCase();
    const marker = ESCAPE_MARKERS.find((m) => lower.includes(m.toLowerCase()));
    if (marker) {
      logLine("bash-bridge-guard-escapes.log", `${marker}\t${command.slice(0, 200).replace(/\s+/g, " ")}`);
      return { block: false, why: `escape:${marker}` };
    }

    const verdict = classifyCommand(command);
    if (!verdict) return { block: false, why: "clean" };

    logLine("bash-bridge-guard-blocks.log", `${verdict.cls}\t${verdict.token}\t${command.slice(0, 200).replace(/\s+/g, " ")}`);
    return { block: true, cls: verdict.cls, token: verdict.token, reason: reasonFor(verdict, command) };
  } catch (e) {
    logLine("bash-bridge-guard-fail-open.log", `run: ${e && e.message}`);
    return { block: false, why: "fail-open" }; // fail-OPEN absolute
  }
}

module.exports = {
  run,
  classifyCommand,
  chunkTokens,
  MANDATORY_POWERSHELL,
  V15_READ_TOKENS,
};

// --- CLI entry point -------------------------------------------------------

if (require.main === module) {
  let raw = "";
  const t = setTimeout(() => { process.exit(0); }, 5000);
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (c) => { raw += c; });
  process.stdin.on("end", () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(raw || "{}"); } catch { process.exit(0); }
    const r = run(data);
    if (r.block) {
      // CHANNEL CONTRACT (fixed 2026-09-15, T-395). On PreToolUse the harness
      // reads STDERR when a hook exits 2; stdout is not the reason channel. This
      // block wrote the pivot to stdout only, so every block from 2026-09-02 to
      // 2026-09-15 reached the agent as "exit 2, which emitted no reason" -- the
      // guard fired correctly and taught nothing, which is how a block becomes a
      // blind-retry loop and then a dead turn. stderr FIRST (the load-bearing
      // channel), stdout kept for any consumer parsing the JSON shape.
      try { process.stderr.write(r.reason + "\n"); } catch {}
      try { process.stdout.write(JSON.stringify({ decision: "block", reason: r.reason })); } catch {}
      process.exit(2);
    }
    process.exit(0);
  });
}
