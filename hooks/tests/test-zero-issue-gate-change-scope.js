#!/usr/bin/env node
/**
 * zero-issue-gate judges the CHANGE, not the repository.
 *
 * Origin 2026-09-25 (Orca X, unattended P8 worker on GEX44): the gate ran `npx tsc --noEmit` against
 * a root tsconfig.json the repo never typechecks with (TypeScript 7 rejects it whatever the code),
 * wrote BLOCKED_DELIVERY.md after 10 "failures", and told the worker at every turn end to fix it
 * first. With compile corrected, the scaffold audit then flagged 37 upstream TODOs the worker never
 * touched. Both are one defect: a verdict about the repository presented as a verdict about the work.
 *
 * Every case drives the real hook as a subprocess against a disposable git repository:
 *   V-ZIG-SCOPE-UNTOUCHED     a pre-existing violation in an untouched file does not count
 *   V-ZIG-SCOPE-CHANGED       a violation the session adds does count, and blocks after 3
 *   V-ZIG-SCOPE-COMMITTED     a violation committed after the session base is still judged
 *   V-ZIG-SCOPE-NONGIT        no git -> the full scan, never a free pass
 *   V-ZIG-DECLARED-COMPILE    package.json's own typecheck runs instead of the registry's guess
 *   V-ZIG-BASELINE-RED        a compile red already present at the base is not counted
 *   V-ZIG-NEW-RED             a compile error the base did not have is counted and blocks
 *   V-ZIG-BASELINE-UNKNOWN    a baseline that could not be computed counts the failure (strict)
 *   V-ZIG-CONSECUTIVE         a pass resets the count, so 2 fails + pass + 2 fails never blocks
 *   V-ZIG-SELF-CLEAR          the gate's own block clears when that same gate passes
 *   V-ZIG-SELF-CLEAR-SCOPED   ...but a block for a gate that did not run, or a foreign file, stays
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync, execFileSync } = require('child_process');

const HOOK = path.join(__dirname, '..', 'zero-issue-gate.js');
const WIN_GIT = 'C:\\Program Files\\Git\\cmd\\git.exe';
const GIT = process.env.CPP_GIT_EXE || (fs.existsSync(WIN_GIT) ? WIN_GIT : 'git');
let passes = 0, fails = 0;
const ok = (g, m) => { passes++; console.log(`[PASS] ${g}: ${m}`); };
const bad = (g, m) => { fails++; console.log(`[FAIL] ${g}: ${m}`); };
const stamp = `${process.pid}-${Date.now()}`;
const made = [];

// Lives outside every fixture repository, so it is never part of the change under judgement.
const TOOLS = fs.mkdtempSync(path.join(os.tmpdir(), `zig-tools-${process.pid}-`));
made.push(TOOLS);
const ERRS = path.join(TOOLS, 'errs.js');
fs.writeFileSync(ERRS, [
  "const fs = require('fs');",
  "if (fs.existsSync('slow.flag')) { const end = Date.now() + 40000; while (Date.now() < end) {} }",
  "const t = fs.existsSync('errors.txt') ? fs.readFileSync('errors.txt', 'utf8').trim() : '';",
  "if (t) { console.error(t); process.exit(1); }",
].join('\n'));
const MARK = path.join(TOOLS, 'mark.js');
fs.writeFileSync(MARK, "require('fs').writeFileSync(process.argv[2], 'ran'); process.exit(0);");
const q = (p) => `"${p}"`;
const NODE = q(process.execPath);

function git(dir, ...args) {
  return execFileSync(GIT, ['-C', dir, ...args], { encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
}

function repo(tag, files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `zig-${tag}-${process.pid}-`));
  made.push(dir);
  git(dir, 'init', '-q');
  git(dir, 'config', 'user.email', 'zig@test');
  git(dir, 'config', 'user.name', 'zig');
  git(dir, 'config', 'core.autocrlf', 'false');
  for (const [name, body] of Object.entries(files)) fs.writeFileSync(path.join(dir, name), body);
  git(dir, 'add', '-A');
  git(dir, 'commit', '-q', '-m', 'base');
  return dir;
}

function drive(dir, sessionId, times) {
  let stderr = '';
  for (let i = 0; i < times; i++) {
    const r = spawnSync(process.execPath, [HOOK], {
      input: JSON.stringify({ cwd: dir, session_id: sessionId }),
      encoding: 'utf8', timeout: 90000, windowsHide: true,
      env: { ...process.env, ZERO_ISSUE_GATE_ENFORCE: '', CPP_GIT_EXE: GIT },
    });
    if (r.error) throw new Error(`HARNESS-FAILED: hook did not run: ${r.error.message}`);
    stderr += r.stderr || '';
  }
  return stderr;
}

const blocked = (dir) => fs.existsSync(path.join(dir, 'BLOCKED_DELIVERY.md'));
const blockBody = (dir) => (blocked(dir) ? fs.readFileSync(path.join(dir, 'BLOCKED_DELIVERY.md'), 'utf8') : '');
const BAD_LINE = 'const delay = Infinity;\n';
const NO_COMPILE = JSON.stringify({ compile: null, test: null });
const sid = (tag) => `zig-${tag}-${stamp}`;

// --- scope: untouched pre-existing violation ---
{
  const dir = repo('untouched', { '.claude-quality-gate.json': NO_COMPILE, 'old.js': BAD_LINE, 'clean.js': 'module.exports = 1;\n' });
  const s = sid('untouched');
  drive(dir, s, 1); // records the session base
  fs.writeFileSync(path.join(dir, 'clean.js'), 'module.exports = 2;\n');
  const err = drive(dir, s, 3);
  if (!blocked(dir) && !/SCAFFOLD AUDIT FAILED/.test(err)) ok('V-ZIG-SCOPE-UNTOUCHED', 'pre-existing violation in old.js not charged to a session that only edited clean.js');
  else bad('V-ZIG-SCOPE-UNTOUCHED', `blocked=${blocked(dir)} stderr=${JSON.stringify(err.slice(0, 300))}`);
}

// --- scope: violation the session adds ---
{
  const dir = repo('changed', { '.claude-quality-gate.json': NO_COMPILE, 'clean.js': 'module.exports = 1;\n' });
  const s = sid('changed');
  drive(dir, s, 1);
  fs.writeFileSync(path.join(dir, 'new.js'), BAD_LINE);
  drive(dir, s, 3);
  if (/Gate that failed: SCAFFOLD/.test(blockBody(dir)) && /new\.js/.test(blockBody(dir))) ok('V-ZIG-SCOPE-CHANGED', 'a violation added by the session blocks after 3, naming new.js');
  else bad('V-ZIG-SCOPE-CHANGED', `body=${JSON.stringify(blockBody(dir).slice(0, 300))}`);
}

// --- scope: committed after the base ---
{
  const dir = repo('committed', { '.claude-quality-gate.json': NO_COMPILE, 'clean.js': 'module.exports = 1;\n' });
  const s = sid('committed');
  drive(dir, s, 1);
  fs.writeFileSync(path.join(dir, 'new.js'), BAD_LINE);
  git(dir, 'add', '-A');
  git(dir, 'commit', '-q', '-m', 'session work');
  const err = drive(dir, s, 1);
  if (/SCAFFOLD AUDIT FAILED/.test(err) && /new\.js/.test(err)) ok('V-ZIG-SCOPE-COMMITTED', 'a committed session change is still judged against the session base');
  else bad('V-ZIG-SCOPE-COMMITTED', `stderr=${JSON.stringify(err.slice(0, 300))}`);
}

// --- scope: not a git repository -> full scan ---
{
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `zig-nongit-${process.pid}-`));
  made.push(dir);
  fs.writeFileSync(path.join(dir, '.claude-quality-gate.json'), NO_COMPILE);
  fs.writeFileSync(path.join(dir, 'old.js'), BAD_LINE);
  const err = drive(dir, sid('nongit'), 1);
  if (/SCAFFOLD AUDIT FAILED/.test(err) && /old\.js/.test(err)) ok('V-ZIG-SCOPE-NONGIT', 'without git the whole tree is scanned: no scope, no free pass');
  else bad('V-ZIG-SCOPE-NONGIT', `stderr=${JSON.stringify(err.slice(0, 300))}`);
}

// --- declared compile ---
{
  const marker = path.join(TOOLS, `declared-${stamp}.txt`);
  const pkg = { name: 'zig', private: true, scripts: { typecheck: `node "${MARK.replace(/\\/g, '/')}" "${marker.replace(/\\/g, '/')}"` } };
  const dir = repo('declared', { 'package.json': JSON.stringify(pkg), 'tsconfig.json': '{ "compilerOptions": { "baseUrl": "." } }' });
  // A run that timed out judged nothing (COMPILE INCONCLUSIVE, measured on a starved host): retry
  // once rather than report host load as a defect.
  let err = drive(dir, sid('declared'), 1);
  if (/COMPILE INCONCLUSIVE/.test(err)) err = drive(dir, sid('declared-retry'), 1);
  if (fs.existsSync(marker) && /ALL PASSED \([^)]*compile/.test(err)) ok('V-ZIG-DECLARED-COMPILE', "package.json's own typecheck ran and passed; the registry's `npx tsc` did not");
  else bad('V-ZIG-DECLARED-COMPILE', `marker=${fs.existsSync(marker)} stderr=${JSON.stringify(err.slice(0, 300))}`);
}

// --- declared compile resolves the project's own binaries, as `npm run` would, without npm ---
{
  const marker = path.join(TOOLS, `projbin-${stamp}.txt`);
  const pkg = { name: 'zig', private: true, scripts: { typecheck: 'zigtc' } };
  const dir = repo('projbin', { 'package.json': JSON.stringify(pkg) });
  const bin = path.join(dir, 'node_modules', '.bin');
  fs.mkdirSync(bin, { recursive: true });
  const call = `"${process.execPath}" "${MARK}" "${marker}"`;
  fs.writeFileSync(path.join(bin, 'zigtc.cmd'), `@echo off\r\n${call}\r\n`);
  fs.writeFileSync(path.join(bin, 'zigtc'), `#!/bin/sh\n${call}\n`, { mode: 0o755 });
  let err = drive(dir, sid('projbin'), 1);
  if (/COMPILE INCONCLUSIVE/.test(err)) err = drive(dir, sid('projbin-retry'), 1);
  if (fs.existsSync(marker) && /ALL PASSED \([^)]*compile/.test(err)) ok('V-ZIG-DECLARED-PROJECT-BIN', 'a declared script finds node_modules/.bin binaries without going through npm');
  else bad('V-ZIG-DECLARED-PROJECT-BIN', `marker=${fs.existsSync(marker)} stderr=${JSON.stringify(err.slice(0, 300))}`);
}

const compileOverride = (extra = {}) => JSON.stringify({ compile: `${NODE} ${q(ERRS)}`, compile_timeout_ms: 20000, test: null, ...extra });

// --- baseline red: same error before and after ---
{
  const dir = repo('baseline', { '.claude-quality-gate.json': compileOverride(), 'errors.txt': 'src/a.ts:3:1 - error TS2322: old debt\n', 'clean.js': '1;\n' });
  const s = sid('baseline');
  drive(dir, s, 1);
  fs.writeFileSync(path.join(dir, 'clean.js'), '2;\n');
  const err = drive(dir, s, 3);
  if (!blocked(dir) && /PRE-EXISTING/.test(err) && !/COMPILE FAILED/.test(err)) ok('V-ZIG-BASELINE-RED', 'a red already present at the base is reported as pre-existing and never counted');
  else bad('V-ZIG-BASELINE-RED', `blocked=${blocked(dir)} stderr=${JSON.stringify(err.slice(0, 400))}`);
}

// --- new red ---
{
  const dir = repo('newred', { '.claude-quality-gate.json': compileOverride(), 'errors.txt': 'src/a.ts:3:1 - error TS2322: old debt\n' });
  const s = sid('newred');
  drive(dir, s, 1);
  fs.writeFileSync(path.join(dir, 'errors.txt'), 'src/a.ts:9:1 - error TS2322: old debt\nsrc/b.ts:1:1 - error TS2304: brand new\n');
  drive(dir, s, 3);
  const body = blockBody(dir);
  if (/Gate that failed: COMPILE/.test(body) && /brand new/.test(body)) ok('V-ZIG-NEW-RED', 'an error absent at the base counts and blocks (a shifted line number is not new)');
  else bad('V-ZIG-NEW-RED', `body=${JSON.stringify(body.slice(0, 300))}`);
}

// --- baseline could not be computed -> strict ---
{
  const dir = repo('unknown', { '.claude-quality-gate.json': compileOverride({ compile_timeout_ms: 12000 }), 'errors.txt': 'src/a.ts:3:1 - error TS2322: old debt\n', 'slow.flag': 'x' });
  const s = sid('unknown');
  fs.unlinkSync(path.join(dir, 'slow.flag')); // the base still carries it, so only the baseline run is slow
  drive(dir, s, 3);
  if (/Gate that failed: COMPILE/.test(blockBody(dir))) ok('V-ZIG-BASELINE-UNKNOWN', 'no baseline in time -> the failure counts; the gate never passes on a guess');
  else bad('V-ZIG-BASELINE-UNKNOWN', `blocked=${blocked(dir)}`);
}

// --- consecutive ---
{
  const dir = repo('consec', { '.claude-quality-gate.json': compileOverride(), 'clean.js': '1;\n' });
  const s = sid('consec');
  drive(dir, s, 1);
  const errs = path.join(dir, 'errors.txt');
  fs.writeFileSync(errs, 'src/b.ts:1:1 - error TS2304: new\n');
  drive(dir, s, 2);
  fs.unlinkSync(errs);
  drive(dir, s, 1);
  fs.writeFileSync(errs, 'src/b.ts:1:1 - error TS2304: new\n');
  drive(dir, s, 2);
  if (!blocked(dir)) ok('V-ZIG-CONSECUTIVE', '2 failures, a pass, 2 failures -> no block: the count is consecutive');
  else bad('V-ZIG-CONSECUTIVE', 'blocked after a pass had intervened');
}

// --- self-clear ---
function writeBlock(dir, gate) {
  fs.writeFileSync(path.join(dir, 'BLOCKED_DELIVERY.md'),
    `# BLOCKED DELIVERY — x\n\n## Gate that failed: ${gate.toUpperCase()}\n\n### Kill-switch status: ACTIVE\n` +
    `This file was created because 3 consecutive attempts to fix the ${gate} gate failed.\n`);
}
{
  const dir = repo('clear', { '.claude-quality-gate.json': compileOverride(), 'clean.js': '1;\n' });
  writeBlock(dir, 'compile');
  const err = drive(dir, sid('clear'), 1);
  if (!blocked(dir) && /cleared/i.test(err)) ok('V-ZIG-SELF-CLEAR', 'the compile block is removed when the compile gate passes, and says so');
  else bad('V-ZIG-SELF-CLEAR', `blocked=${blocked(dir)} stderr=${JSON.stringify(err.slice(0, 300))}`);
}
{
  const a = repo('keep-test', { '.claude-quality-gate.json': compileOverride(), 'clean.js': '1;\n' });
  writeBlock(a, 'test'); // the test gate is opt-in and does not run here
  drive(a, sid('keep-test'), 1);
  const b = repo('keep-foreign', { '.claude-quality-gate.json': compileOverride(), 'clean.js': '1;\n' });
  fs.writeFileSync(path.join(b, 'BLOCKED_DELIVERY.md'), '# Blocked by a person\n\nGate that failed: COMPILE\n');
  drive(b, sid('keep-foreign'), 1);
  if (blocked(a) && blocked(b)) ok('V-ZIG-SELF-CLEAR-SCOPED', 'a block for a gate that did not run, and a file this gate did not write, both stay');
  else bad('V-ZIG-SELF-CLEAR-SCOPED', `test-block kept=${blocked(a)} foreign kept=${blocked(b)}`);
}

// --- a block survives a relay: the next session's vacuous pass must not clear it ---
{
  const dir = repo('carry', { '.claude-quality-gate.json': NO_COMPILE, 'clean.js': 'module.exports = 1;\n' });
  const a = sid('carry-a');
  drive(dir, a, 1);
  fs.writeFileSync(path.join(dir, 'new.js'), BAD_LINE);
  git(dir, 'add', '-A');
  git(dir, 'commit', '-q', '-m', 'epoch 1 work');
  drive(dir, a, 3);
  const written = /Gate that failed: SCAFFOLD/.test(blockBody(dir));
  const b = sid('carry-b'); // the relayed worker: a new session whose base is after the bad commit
  drive(dir, b, 1);
  fs.writeFileSync(path.join(dir, 'clean.js'), 'module.exports = 2;\n');
  drive(dir, b, 1);
  const kept = blocked(dir);
  fs.writeFileSync(path.join(dir, 'new.js'), 'const delay = 1000;\n');
  drive(dir, b, 1);
  const clearedWhenFixed = !blocked(dir);
  if (written && kept && clearedWhenFixed) ok('V-ZIG-BLOCK-SURVIVES-RELAY', 'a new session cannot clear a block naming a file it never fixed; fixing that file clears it');
  else bad('V-ZIG-BLOCK-SURVIVES-RELAY', `written=${written} kept=${kept} clearedWhenFixed=${clearedWhenFixed}`);
}

// --- a pre-existing compile red never clears a compile block ---
{
  const dir = repo('preclear', { '.claude-quality-gate.json': compileOverride(), 'errors.txt': 'src/a.ts:3:1 - error TS2322: old debt\n' });
  const s = sid('preclear');
  drive(dir, s, 1);
  writeBlock(dir, 'compile');
  const err = drive(dir, s, 1);
  if (blocked(dir) && /PRE-EXISTING/.test(err)) ok('V-ZIG-PREEXISTING-NO-CLEAR', 'only a real compile pass lifts a compile block; old debt at the base does not');
  else bad('V-ZIG-PREEXISTING-NO-CLEAR', `blocked=${blocked(dir)} stderr=${JSON.stringify(err.slice(0, 300))}`);
}

for (const d of made) { try { fs.rmSync(d, { recursive: true, force: true }); } catch (_) { /* tmp */ } }
console.log(`ZIG_SCOPE_PASS=${passes}/${passes + fails}  threshold=14/14`);
process.exit(fails === 0 ? 0 : 1);
