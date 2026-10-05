#!/usr/bin/env node
/**
 * quality-skill-gate.js --record must work in a LINKED git worktree.
 *
 * Measured 2026-10-05 (E1 mission on GEX44): in a worktree `.git` is a FILE, so a receipt
 * path of `<toplevel>/.git/quality-skill-evidence.json` failed ENOTDIR, and every commit
 * staging >= 3 source files was denied even after a real review. The receipt belongs in
 * the worktree's own git dir (`git rev-parse --absolute-git-dir`).
 *
 * Control: the main checkout still records into its `.git/` directory.
 * Run: node hooks/tests/test-quality-skill-gate-worktree.js   (exit 0 = all pass)
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync, spawnSync } = require("child_process");

const GATE = path.resolve(__dirname, "..", "quality-skill-gate.js");
let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log(`[OK] ${id}: ${ev}`); };
const bad = (id, d) => { fail++; console.log(`[FAIL] ${id}: ${d}`); };
const git = (cwd, ...a) => execFileSync("git", a, { cwd, encoding: "utf8", windowsHide: true }).trim();

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "qsg-wt-"));
const main = path.join(tmp, "main");
fs.mkdirSync(main);
git(main, "init", "-q");
git(main, "config", "user.email", "t@example.invalid");
git(main, "config", "user.name", "t");
fs.writeFileSync(path.join(main, "README"), "x\n");
git(main, "add", "README");
git(main, "commit", "-q", "-m", "init");
const wt = path.join(tmp, "wt");
git(main, "worktree", "add", "-q", wt);

function record(cwd) {
  return spawnSync(process.execPath, [GATE, "--record", "a.py", "b.py", "c.py"],
    { cwd, encoding: "utf8", windowsHide: true });
}

// V-QSG-WORKTREE-RECORD: the worktree records into its own git dir.
const r = record(wt);
const wtGitDir = git(wt, "rev-parse", "--absolute-git-dir");
const wtReceipt = path.join(wtGitDir, "quality-skill-evidence.json");
if (r.status === 0 && fs.existsSync(wtReceipt)) {
  ok("V-QSG-WORKTREE-RECORD", `receipt in ${path.basename(path.dirname(wtReceipt))}/`);
} else {
  bad("V-QSG-WORKTREE-RECORD", `rc=${r.status} exists=${fs.existsSync(wtReceipt)} err=${(r.stderr || "").slice(0, 160)}`);
}

// V-QSG-MAIN-RECORD (control): the main checkout still uses .git/.
const m = record(main);
const mainReceipt = path.join(main, ".git", "quality-skill-evidence.json");
if (m.status === 0 && fs.existsSync(mainReceipt)) {
  ok("V-QSG-MAIN-RECORD", "receipt in .git/");
} else {
  bad("V-QSG-MAIN-RECORD", `rc=${m.status} exists=${fs.existsSync(mainReceipt)}`);
}

// V-QSG-SCOPED: the two receipts are different files (worktree scoping kept).
if (path.resolve(wtReceipt) !== path.resolve(mainReceipt)) {
  ok("V-QSG-SCOPED", "worktree and main receipts are separate");
} else {
  bad("V-QSG-SCOPED", "worktree wrote the main checkout's receipt");
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(`QSG_WORKTREE_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
