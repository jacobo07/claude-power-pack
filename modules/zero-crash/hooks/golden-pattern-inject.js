#!/usr/bin/env node
/**
 * golden-pattern-inject.js
 * UserPromptSubmit hook — Ley DNA-400 companion.
 *
 * Scans ~/.claude/projects/<project>/memory/ for entries tagged #GOLDEN_PATTERN
 * and emits them as additional context for the current turn. Graceful degradation:
 * if the memory root is missing, emits nothing and exits 0 (never blocks).
 *
 * Invoked by Claude Code as a UserPromptSubmit hook. Register via:
 *   {"hooks": {"UserPromptSubmit": [{"type": "command", "command": "node <absolute-path>/golden-pattern-inject.js"}]}}
 *
 * Stdout contract: either empty, or a JSON object {"additionalContext": "<markdown>"}.
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

const MAX_PATTERNS = 10;
const TAG = "#GOLDEN_PATTERN";
const MEMORY_ROOT = path.join(os.homedir(), ".claude", "projects");

function safeListDir(p) {
  try {
    return fs.readdirSync(p, { withFileTypes: true });
  } catch {
    return [];
  }
}

function findMemoryFiles(root) {
  const hits = [];
  for (const entry of safeListDir(root)) {
    if (!entry.isDirectory()) continue;
    const memDir = path.join(root, entry.name, "memory");
    for (const f of safeListDir(memDir)) {
      if (f.isFile() && f.name.endsWith(".md")) {
        hits.push(path.join(memDir, f.name));
      }
    }
  }
  return hits;
}

function extractPatterns(filePath) {
  let text;
  try {
    text = fs.readFileSync(filePath, "utf8");
  } catch {
    return [];
  }
  const patterns = [];
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].includes(TAG)) continue;
    // Capture the heading line plus up to 6 lines of body until next heading or blank-heading gap
    const block = [lines[i]];
    for (let j = i + 1; j < lines.length && block.length < 7; j++) {
      if (lines[j].startsWith("### ") || lines[j].startsWith("## ")) break;
      block.push(lines[j]);
    }
    patterns.push({ file: filePath, text: block.join("\n").trim() });
  }
  return patterns;
}

function main() {
  if (!fs.existsSync(MEMORY_ROOT)) {
    process.exit(0);
  }
  const files = findMemoryFiles(MEMORY_ROOT);
  const all = [];
  for (const f of files) {
    for (const p of extractPatterns(f)) {
      all.push(p);
      if (all.length >= MAX_PATTERNS) break;
    }
    if (all.length >= MAX_PATTERNS) break;
  }
  if (all.length === 0) {
    process.exit(0);
  }

  const md = [
    "## Golden Patterns (auto-injected from memory — Ley DNA-400)",
    "",
    "Proven patterns from prior sessions. Treat as pre-validated context; prefer them over inventing new approaches.",
    "",
    ...all.map((p) => `- From \`${path.relative(os.homedir(), p.file)}\`:\n${p.text.split("\n").map((l) => `  > ${l}`).join("\n")}`),
  ].join("\n");

  process.stdout.write(JSON.stringify({ additionalContext: md }));
  process.exit(0);
}

try {
  main();
} catch (err) {
  // Never block the prompt on a hook error.
  process.stderr.write(`golden-pattern-inject: ${err && err.message ? err.message : err}\n`);
  process.exit(0);
}
