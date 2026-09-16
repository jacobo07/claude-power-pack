#!/usr/bin/env node
/**
 * quality-skill-gate.js — Owner-ratified hard-block commit gate (v220000 / ceiling v5.5).
 *
 * Governance: CLAUDE.md "Governance ceiling v5.5 — Owner-ratified amendment"
 * + reports/verdicts/2026-05-15_ceiling_v5.5_ratification.md + VAC-GOV-220000.
 *
 * Scope (narrow, reversible, non-generalizing): a PreToolUse hook on Bash.
 * It DENIES `git commit` (exit-equivalent via permissionDecision:"deny")
 * iff the staged changeset includes >= MIN_SOURCE_FILES source files AND no
 * fresh quality-skill evidence receipt covers them. Every other commit and
 * every non-commit Bash command passes untouched. It does NOT touch
 * defaultMode, permissions.allow, or any unrelated rail.
 *
 * Evidence receipt: <repo>/.git/quality-skill-evidence.json
 *   { "ts": <epoch_seconds>, "files": [repo-relative source paths],
 *     "skills": ["code-reviewer", ...] }
 * Produced by running this file in recorder mode AFTER the quality skills:
 *   node quality-skill-gate.js --record <file1> <file2> ...
 *
 * Honest design notes:
 *  - The receipt lives in .git/ (per-clone, ephemeral, never committed) so it
 *    is genuinely session/worktree-scoped and cannot be smuggled via the repo.
 *  - A receipt is valid only if it is younger than RECEIPT_TTL_S and its file
 *    set is a superset of the staged source files (you reviewed what you ship).
 *  - Fail-OPEN only on its own internal error (never wedge the user's git over
 *    a bug in a governance convenience); fail-CLOSED on the policy condition.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const MIN_SOURCE_FILES = 3;
const RECEIPT_TTL_S = 6 * 60 * 60; // 6h — generous; one session.
const SOURCE_EXT = new Set([
  ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
  ".java", ".go", ".rs", ".rb", ".kt", ".scala", ".cs",
]);

function repoRoot(cwd) {
  return execSync("git rev-parse --show-toplevel", { cwd, encoding: "utf8", windowsHide: true }).trim();
}

function receiptPath(root) {
  return path.join(root, ".git", "quality-skill-evidence.json");
}

function stagedSourceFiles(root) {
  const out = execSync(
    "git diff --cached --name-only --diff-filter=ACM",
    { cwd: root, encoding: "utf8", windowsHide: true }
  );
  return out
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
    .filter((f) => SOURCE_EXT.has(path.extname(f).toLowerCase()));
}

// ---- recorder mode ---------------------------------------------------------
function record(argv) {
  const files = argv.filter((a) => !a.startsWith("--"));
  const root = repoRoot(process.cwd());
  const rel = files.map((f) =>
    path.relative(root, path.resolve(process.cwd(), f)).replace(/\\/g, "/")
  );
  const receipt = {
    ts: Math.floor(Date.now() / 1000),
    files: rel,
    skills: ["code-reviewer", "software-best-practices", "python-pro", "kobiicraft-review"],
    note: "v220000 ceiling v5.5 — quality-skill evidence",
  };
  fs.writeFileSync(receiptPath(root), JSON.stringify(receipt, null, 2));
  process.stdout.write(
    `[quality-skill-gate] receipt written: ${rel.length} file(s)\n`
  );
  return 0;
}

// ---- gate mode (PreToolUse) ------------------------------------------------
function allow() {
  process.stdout.write("{}");
  return 0;
}

function deny(reason) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    })
  );
  return 0;
}

function isGitCommit(cmd) {
  if (!cmd) return false;
  // Match `git commit ...` allowing leading env/cd and `git -C x commit`.
  return /\bgit\b[^\n&|;]*\bcommit\b/.test(cmd) && !/\bgit\b[^\n]*\b(log|show)\b/.test(cmd);
}

function runGate(event) {
  const cmd = event && event.tool_input && event.tool_input.command;
  if (!isGitCommit(cmd)) return allow();

  const cwd = (event && event.cwd) || process.cwd();
  let root;
  try {
    root = repoRoot(cwd);
  } catch (_e) {
    return allow(); // not a git repo / git missing — not our business
  }

  let staged;
  try {
    staged = stagedSourceFiles(root);
  } catch (_e) {
    return allow(); // never wedge git over our own failure
  }
  if (staged.length < MIN_SOURCE_FILES) return allow();

  const rp = receiptPath(root);
  if (!fs.existsSync(rp)) {
    return deny(
      `Governance ceiling v5.5: this commit stages ${staged.length} source files ` +
        `(>= ${MIN_SOURCE_FILES}) with NO quality-skill evidence receipt. Run the ` +
        `quality skills (code-reviewer / software-best-practices / python-pro / ` +
        `kobiicraft-review) on the changeset, then record evidence:\n` +
        `  node ~/.claude/hooks/quality-skill-gate.js --record ` +
        staged.join(" ") +
        `\nThen retry the commit. (Owner-ratified hard gate — not self-elevable.)`
    );
  }

  let receipt;
  try {
    receipt = JSON.parse(fs.readFileSync(rp, "utf8"));
  } catch (_e) {
    return deny("quality-skill evidence receipt is corrupt — re-run --record.");
  }

  const ageS = Math.floor(Date.now() / 1000) - (receipt.ts || 0);
  if (ageS > RECEIPT_TTL_S) {
    return deny(
      `quality-skill evidence receipt is stale (${ageS}s > ${RECEIPT_TTL_S}s). ` +
        `Re-run the quality skills + --record for the current changeset.`
    );
  }

  const covered = new Set((receipt.files || []).map((f) => f.replace(/\\/g, "/")));
  const missing = staged.filter((f) => !covered.has(f));
  if (missing.length > 0) {
    return deny(
      `quality-skill evidence does not cover ${missing.length} staged source ` +
        `file(s): ${missing.join(", ")}. Review them and re-run --record.`
    );
  }

  return allow();
}

function main() {
  const argv = process.argv.slice(2);
  if (argv.includes("--record")) {
    try {
      return record(argv.filter((a) => a !== "--record"));
    } catch (e) {
      process.stderr.write(`[quality-skill-gate] record failed: ${e.message}\n`);
      return 1;
    }
  }
  let raw = "";
  try {
    raw = fs.readFileSync(0, "utf8");
  } catch (_e) {
    raw = "";
  }
  let event = {};
  try {
    event = raw.trim() ? JSON.parse(raw) : {};
  } catch (_e) {
    return allow();
  }
  try {
    return runGate(event);
  } catch (_e) {
    return allow(); // fail-open on internal error only
  }
}

process.exit(main());
