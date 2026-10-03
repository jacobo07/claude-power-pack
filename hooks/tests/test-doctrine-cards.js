#!/usr/bin/env node
// Tests for hooks/doctrine_cards.js (PLAN-SKILL-RESIDENCY C4, audit G'1-G'3, G'6, G'9, G'11).
// Every case runs the REAL card as a child process against a REAL scratch git repo and a transcript
// whose rows copy real shapes (Edit tool_use input, toolUseResult.structuredPatch). Hermetic: its own
// state dir; the live ledger is never written.
'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CARD = path.resolve(__dirname, '..', 'doctrine_cards.js');
const GIT = fs.existsSync('C:\\Program Files\\Git\\cmd\\git.exe') ? 'C:\\Program Files\\Git\\cmd\\git.exe' : 'git';
let pass = 0; let fail = 0;
const check = (name, cond, ev) => { if (cond) { pass++; console.log(`PASS ${name}: ${ev}`); } else { fail++; console.log(`FAIL ${name}: ${ev}`); } };

const OWN = 'def apply_discount(amount, pct):\n    return amount * (1 - pct / 100)\n';
const BASE = '"""Order pricing."""\n\nTAX_RATE = 0.21\n\n\ndef apply_discount(amount, pct):\n    return amount - pct\n';
const FOREIGN = '\n\ndef shipping(weight_kg):\n    return 4.95 if weight_kg <= 2 else 4.95 + 1.1 * (weight_kg - 2)\n';

function g(repo, ...a) { return spawnSync(GIT, ['-C', repo, ...a], { encoding: 'utf8' }); }

function scratch(tag) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), `dc-${tag}-`));
  const repo = path.join(root, 'repo');
  fs.mkdirSync(repo);
  fs.writeFileSync(path.join(repo, 'pricing.py'), BASE);
  fs.writeFileSync(path.join(repo, 'notes.md'), 'notes\n');
  g(repo, 'init', '-q'); g(repo, 'config', 'user.email', 't@x.invalid'); g(repo, 'config', 'user.name', 't');
  g(repo, 'config', 'core.autocrlf', 'false'); g(repo, 'add', '-A'); g(repo, 'commit', '-q', '-m', 'init');
  return { root, repo, state: path.join(root, 'state') };
}

// The session's own edit, recorded the way the harness records it.
function transcript(root, { sub = false, shellWrite = false } = {}) {
  const sid = 'sess-0001';
  const tp = path.join(root, `${sid}.jsonl`);
  const edit = { type: 'assistant', message: { content: [{ type: 'tool_use', id: 't1', name: 'Edit',
    input: { file_path: 'pricing.py', old_string: '    return amount - pct', new_string: '    return amount * (1 - pct / 100)' } }] } };
  const rows = [{ type: 'user', message: { content: 'fix the test' } }];
  if (!sub) rows.push(edit);
  if (shellWrite) rows.push({ type: 'assistant', message: { content: [{ type: 'tool_use', id: 't2', name: 'PowerShell',
    input: { command: "Add-Content pricing.py 'x = 1'" } }] } });
  fs.writeFileSync(tp, rows.map((r) => JSON.stringify(r)).join('\n') + '\n');
  if (sub) {
    const sd = path.join(root, sid, 'subagents');
    fs.mkdirSync(sd, { recursive: true });
    fs.writeFileSync(path.join(sd, 'agent-a.jsonl'), JSON.stringify(edit) + '\n');
  }
  return { sid, tp };
}

function run(s, t, command, mode = 'ledger', cwd = s.repo) {
  const env = { ...process.env, DOCTRINE_CARDS_STATE_DIR: s.state, CLAUDE_DOCTRINE_CARDS: mode };
  const r = spawnSync(process.execPath, [CARD], { input: JSON.stringify({ tool_name: 'PowerShell', session_id: t.sid,
    transcript_path: t.tp, cwd, tool_input: { command } }), encoding: 'utf8', env, timeout: 20000 });
  let out = {};
  try { out = JSON.parse(r.stdout || '{}'); } catch (_) { out = { raw: r.stdout }; }
  const lp = path.join(s.state, 'ledger.jsonl');
  const rows = fs.existsSync(lp) ? fs.readFileSync(lp, 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l)) : [];
  return { out, rows, last: rows[rows.length - 1], denied: ((out.hookSpecificOutput || {}).permissionDecision) === 'deny' };
}

const writeOwn = (s) => fs.writeFileSync(path.join(s.repo, 'pricing.py'), BASE.replace('    return amount - pct\n', '    return amount * (1 - pct / 100)\n'));
const writeOwnAndForeign = (s) => { writeOwn(s); fs.appendFileSync(path.join(s.repo, 'pricing.py'), FOREIGN); };

// 1. G'11: a non-commit command does no I/O (no ledger file at all).
{ const s = scratch('noop'); const t = transcript(s.root); writeOwnAndForeign(s);
  const r = run(s, t, 'git status --short');
  check('V-DC-NONCOMMIT-NO-IO', r.out.continue === true && !fs.existsSync(s.state), 'state dir absent after a non-commit call'); }

// 2. Kill switch.
{ const s = scratch('off'); const t = transcript(s.root); writeOwnAndForeign(s); g(s.repo, 'add', 'pricing.py');
  const r = run(s, t, 'git commit -m fix', 'off');
  check('V-DC-OFF', r.out.continue === true && !r.rows.length, 'off: no ledger, continue'); }

// 3. G'1 THE INCIDENT SHAPE: own edit + peer hunk in the SAME file, pathspec commit -> opportunity.
{ const s = scratch('same'); const t = transcript(s.root); writeOwnAndForeign(s);
  const r = run(s, t, "Set-Location 'X'; git add -- pricing.py; git commit -m fix -- pricing.py".replace("'X'", `'${s.repo}'`));
  check('V-DC-SAME-FILE-FOREIGN', r.last && r.last.decision === 'opportunity' && r.out.continue === true
    && r.last.foreign[0].file === 'pricing.py', `decision=${r.last && r.last.decision} basis=${r.last && r.last.basis}`);
  // Control: own lines only -> no_opportunity (a detector that flags everything fails here).
  const s2 = scratch('own'); const t2 = transcript(s2.root); writeOwn(s2); g(s2.repo, 'add', 'pricing.py');
  const r2 = run(s2, t2, 'git commit -m fix');
  check('V-DC-OWN-ONLY-CONTROL', r2.last && r2.last.decision === 'no_opportunity', `decision=${r2.last && r2.last.decision}`); }

// 4. G'2 commit forms: -am picks up unstaged tracked changes; `& $g -C $r` resolves variables; --amend is UNKNOWN.
{ const s = scratch('am'); const t = transcript(s.root); writeOwnAndForeign(s);
  const r = run(s, t, 'git commit -am fix');
  check('V-DC-COMMIT-AM', r.last && r.last.decision === 'opportunity' && r.last.basis === 'all-tracked', `basis=${r.last && r.last.basis}`);
  const cmd = `$g='${GIT}'; $r='${s.repo}'; & $g -C $r commit -am fix`;
  const r2 = run(s, t, cmd, 'ledger', os.tmpdir());
  check('V-DC-PS-VARIABLES', r2.last && r2.last.decision === 'opportunity', `repo from $r, cwd elsewhere: ${r2.last && r2.last.decision}`);
  const r3 = run(s, t, 'git commit --amend --no-edit');
  check('V-DC-AMEND-UNKNOWN', r3.last && r3.last.decision === 'unknown' && /amend/.test(r3.last.reason), `reason=${r3.last && r3.last.reason}`);
  const r4 = run(s, t, 'git add -A; git commit -m fix');
  check('V-DC-ADD-THEN-COMMIT', r4.last && r4.last.decision === 'opportunity' && r4.last.basis === 'add-then-commit', `basis=${r4.last && r4.last.basis}`);
  // index basis: unstaged foreign + nothing staged -> nothing in the commit -> no opportunity
  const r5 = run(s, t, 'git commit -m fix');
  check('V-DC-INDEX-BASIS', r5.last && r5.last.decision === 'no_opportunity' && r5.last.basis === 'index', `basis=${r5.last && r5.last.basis}`); }

// 5. G'3 deny mode: denies once with the card naming the hunk, the same commit then passes.
{ const s = scratch('deny'); const t = transcript(s.root); writeOwnAndForeign(s); g(s.repo, 'add', 'pricing.py');
  const r = run(s, t, 'git commit -m fix', 'deny');
  const reason = ((r.out.hookSpecificOutput || {}).permissionDecisionReason) || '';
  check('V-DC-DENY-CARD', r.denied && /pricing\.py @@/.test(reason) && /shipping/.test(reason) && r.last.decision === 'deny-card', reason.split('\n')[1] || '(no card)');
  const r2 = run(s, t, 'git commit -m fix', 'deny');
  check('V-DC-DENY-ONCE', !r2.denied && r2.last.decision === 'pass-after-card', `second=${r2.last.decision}`);
  // Ledger-only rows are never delivery: default mode never denies.
  const s3 = scratch('ledger'); const t3 = transcript(s3.root); writeOwnAndForeign(s3); g(s3.repo, 'add', 'pricing.py');
  const r3 = run(s3, t3, 'git commit -m fix');
  check('V-DC-LEDGER-NEVER-DENIES', !r3.denied && r3.last.decision === 'opportunity', 'ledger mode records, never blocks'); }

// 6. G'9 subagent edits count as the session's own.
{ const s = scratch('sub'); const t = transcript(s.root, { sub: true }); writeOwn(s); g(s.repo, 'add', 'pricing.py');
  const r = run(s, t, 'git commit -m fix');
  check('V-DC-SUBAGENT-OWN', r.last && r.last.decision === 'no_opportunity', `decision=${r.last && r.last.decision}`); }

// 7. A file the session wrote through the shell is UNKNOWN, not foreign.
{ const s = scratch('shell'); const t = transcript(s.root, { shellWrite: true }); writeOwnAndForeign(s); g(s.repo, 'add', 'pricing.py');
  const r = run(s, t, 'git commit -m fix');
  check('V-DC-SHELL-WRITE-UNKNOWN', r.last && r.last.decision === 'unknown' && r.last.unknown_files.includes('pricing.py'), `decision=${r.last && r.last.decision}`); }

// 8. Commit regex: both poles.
{ const { COMMIT_RE } = require(CARD);
  const yes = ['git commit -m x', '& $g -C $r commit -F f', "& 'C:\\Program Files\\Git\\cmd\\git.exe' commit -m x", 'git -C "a b" commit'];
  const no = ['git commit-tree abc', 'git log --grep commit', 'echo committed', 'git show HEAD'];
  check('V-DC-COMMIT-RE', yes.every((c) => COMMIT_RE.test(c)) && no.every((c) => !COMMIT_RE.test(c)), `${yes.length}+${no.length} cases`); }

console.log(`DOCTRINE_CARDS_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
