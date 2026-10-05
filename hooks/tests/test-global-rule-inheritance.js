#!/usr/bin/env node
/**
 * Proves a global rule file is actually inherited -- at the MODEL BOUNDARY, not in a hook's source.
 *
 * Until 2026-10-05 this file assumed learning-sentinel.js was the inheritance mechanism and drilled its
 * directory glob. Measured on the K probe windows (incremental-cognition pillar K, 8f983bc6 and fa7e93cb), that
 * premise was false: the harness itself loads ~/.claude/rules/**\/*.md, recursively, as User instructions in
 * every session, so the hook was a second, non-recursive copy (it never saw common/ or python/) that put rule
 * text in context twice and pushed its own emission past the pipe budget. The hook no longer emits rules.
 *
 * So the claim "future sessions inherit this rule" is now judged where it is true or false -- in a real
 * transcript's startup window:
 *
 *   1. every rule file that existed when a recent real session started is in that session's `instructions`
 *      attachment (nested directories included);
 *   2. the predicate that says so goes red on a synthetic missing rule and green on a present one, so it cannot
 *      pass by accepting everything;
 *   3. learning-sentinel.js, driven for real, re-emits no rule text and stays inside the 4,096 B pipe budget;
 *   4. the destructive-state doctrine still asks the validate-to-effect question in the place it now lives.
 *
 * Run: node ~/.claude/hooks/tests/test-global-rule-inheritance.js
 *      (CPP_SENTINEL=<path> drives a canonical copy of the hook before it is deployed.)
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME_CLAUDE = path.join(os.homedir(), '.claude');
const RULES_DIR = path.join(HOME_CLAUDE, 'rules');
const PROJECTS = path.join(HOME_CLAUDE, 'projects');
const SENTINEL = process.env.CPP_SENTINEL || path.join(HOME_CLAUDE, 'hooks', 'learning-sentinel.js');
const DESTRUCTIVE_SKILL = path.join(HOME_CLAUDE, 'skills', 'destructive-state-authorization', 'SKILL.md');
const MAX_CANDIDATES = 25;

let failures = 0;
function ok(name, evidence) { console.log(`  PASS  ${name}${evidence ? ` — ${evidence}` : ''}`); }
function fail(name, diagnostic) { failures += 1; console.error(`  FAIL  ${name} — ${diagnostic}`); }

const norm = (p) => String(p).replace(/\\/g, '/').toLowerCase();

function ruleFiles(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...ruleFiles(p));
    else if (e.isFile() && e.name.endsWith('.md')) out.push(p);
  }
  return out;
}

/** -> {start: Date|null, paths: Set<normalized path>} from the rows before the first assistant row, or null. */
function startupInstructions(file) {
  let start = null;
  const paths = new Set();
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch { return null; }
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    let row;
    try { row = JSON.parse(line); } catch { continue; }
    if (!row || typeof row !== 'object') continue;
    if (row.type === 'assistant') break;
    if (!start && row.timestamp) start = new Date(row.timestamp);
    const a = row.attachment || {};
    if (a.type === 'instructions') for (const f of a.files || []) if (f && f.type === 'User' && f.path) paths.add(norm(f.path));
  }
  return paths.size ? { start, paths } : null;
}

/** The predicate under test: expected rule paths absent from a delivered set. */
function missingFrom(delivered, expected) {
  return expected.filter((p) => !delivered.has(norm(p)));
}

console.log('test-global-rule-inheritance');

// 1. Model-boundary delivery from the newest real session that loaded User instructions.
try {
  const rulesNorm = norm(RULES_DIR);
  const candidates = fs.readdirSync(PROJECTS, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .flatMap((d) => fs.readdirSync(path.join(PROJECTS, d.name)).filter((f) => f.endsWith('.jsonl'))
      .map((f) => path.join(PROJECTS, d.name, f)))
    .map((p) => ({ p, m: fs.statSync(p).mtimeMs }))
    .sort((a, b) => b.m - a.m)
    .slice(0, MAX_CANDIDATES * 8);
  let seen = 0;
  let found = null;
  for (const { p } of candidates) {
    if (seen >= MAX_CANDIDATES) break;
    const win = startupInstructions(p);
    if (!win) continue;
    seen += 1;
    if ([...win.paths].some((x) => x.startsWith(rulesNorm + '/')) && win.start) { found = { p, ...win }; break; }
  }
  if (!found) {
    fail('a recent real session carries ~/.claude/rules in its instructions',
      `no startup window among ${seen} recent transcripts lists a User rule file — this judged nothing`);
  } else {
    const all = ruleFiles(RULES_DIR);
    const expected = all.filter((p) => fs.statSync(p).birthtimeMs < found.start.getTime());
    const nested = expected.filter((p) => path.dirname(p) !== RULES_DIR);
    const missing = missingFrom(found.paths, expected);
    if (expected.length < 3) {
      fail('the population is large enough to judge', `${expected.length} rule files predate ${path.basename(found.p)}`);
    } else if (missing.length) {
      fail('every rule file reaches the model as an instruction',
        `${missing.length} of ${expected.length} absent from ${path.basename(found.p)}: ${missing.map((m) => path.relative(RULES_DIR, m)).join(', ')}`);
    } else {
      ok('every rule file reaches the model as an instruction',
        `${expected.length}/${expected.length} in ${path.basename(found.p)} (${nested.length} nested), ${all.length - expected.length} newer than that session`);
    }
  }
} catch (error) {
  fail('the model-boundary delivery can be judged', String(error && error.message));
}

// 2. The predicate, from both poles, on subjects that cannot drift.
{
  const delivered = new Set([norm('C:/h/.claude/rules/a.md'), norm('C:/h/.claude/rules/sub/b.md')]);
  const red = missingFrom(delivered, ['C:/h/.claude/rules/a.md', 'C:/h/.claude/rules/zz-never-delivered.md']);
  const green = missingFrom(delivered, ['C:\\h\\.claude\\rules\\sub\\b.md', 'C:/h/.claude/rules/a.md']);
  if (red.length === 1 && green.length === 0) ok('the delivery predicate separates a missing rule from a present one');
  else fail('the delivery predicate separates a missing rule from a present one', `red=${red.length} green=${green.length}`);
}

// 3. The hook, driven for real: no rule text re-emitted, inside the pipe budget.
try {
  const { execFileSync } = require('child_process');
  const raw = execFileSync(process.execPath, [SENTINEL], {
    input: JSON.stringify({ hook_event_name: 'SessionStart', session_id: 'inheritance-probe', cwd: process.cwd(), source: 'startup' }),
    encoding: 'utf8', timeout: 20000,
  });
  const out = raw.trim() ? JSON.parse(raw) : {};
  const ctx = (out.hookSpecificOutput && out.hookSpecificOutput.additionalContext) || '';
  const bytes = Buffer.byteLength(ctx, 'utf8');
  if (/### Global Rule/.test(ctx) || /delivered by file/.test(ctx)) {
    fail('learning-sentinel re-emits no rule text', 'rule bodies or the bundle pointer are back in the emission: the harness already delivers them');
  } else {
    ok('learning-sentinel re-emits no rule text');
  }
  if (bytes <= 4096) ok('the emission stays inside the pipe budget', `${bytes} B <= 4096 B`);
  else fail('the emission stays inside the pipe budget', `${bytes} B exceeds the 4096 B undrained-pipe buffer`);
} catch (error) {
  fail('learning-sentinel can be driven', `${error && error.message} — this judged nothing`);
}

// 4. Inheriting the FILE is not inheriting the LESSON. The destructive-state rule moved to a skill on
//    2026-09-29 (the rule file is now a pointer), so the doctrine is judged where it lives.
function demandsEffectIntervalAnalysis(body) {
  const lowered = body.toLowerCase().replace(/\s+/g, ' ');
  return (
    /between the final check and the (destruction|effect)/.test(lowered) &&
    /re-?authori[sz]e/.test(lowered) &&
    /(subprocess|await|process boundary)/.test(lowered)
  );
}
const STALE_ONLY_RULE = 'Capture what the user observed and refuse the operation when the current state no longer matches it.';
const INTERVAL_AWARE_RULE = 'Refuse when the state moved. The state cannot move between the final check and the destruction: '
  + 'enumerate every await and subprocess in that interval, and re-authorize each batch member.';
try {
  if (demandsEffectIntervalAnalysis(STALE_ONLY_RULE)) fail('a stale-only destructive rule is recognised as incomplete', 'predicate accepted it');
  else ok('a stale-only destructive rule is recognised as incomplete');
  if (demandsEffectIntervalAnalysis(INTERVAL_AWARE_RULE)) ok('an interval-aware destructive rule is recognised as complete');
  else fail('an interval-aware destructive rule is recognised as complete', 'predicate rejects text that states it');
  const pointer = fs.readFileSync(path.join(RULES_DIR, 'destructive-state-authorization.md'), 'utf8');
  if (!/destructive-state-authorization/.test(pointer)) fail('the inherited rule file points at the skill', 'pointer text lost');
  else ok('the inherited rule file points at the skill');
  if (demandsEffectIntervalAnalysis(fs.readFileSync(DESTRUCTIVE_SKILL, 'utf8'))) ok('the destructive-state skill forces the validate-to-effect question');
  else fail('the destructive-state skill forces the validate-to-effect question', `${DESTRUCTIVE_SKILL} no longer asks what can move between the final check and the effect`);
} catch (error) {
  fail('the destructive doctrine can be read and evaluated', String(error && error.message));
}

if (failures > 0) {
  console.error(`test-global-rule-inheritance: ${failures} failed`);
  process.exit(1);
}
console.log('test-global-rule-inheritance: all passed');
