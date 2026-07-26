#!/usr/bin/env node
'use strict';
// V-gates for the CLAUDE.md auto-compaction layer (BL-CLAUDEMD-COMPACT).
//   node tools/test_claude_md_compaction.js
// Exit 0 only when every gate passes.
const assert = require('assert');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOOK = path.join(__dirname, '..', 'hooks', 'claude_md_linter_stop.js');
const CFG = path.join(__dirname, '..', 'vault', 'config',
  'claude_md_thresholds.json');
const CM = path.join(os.homedir(), '.claude', 'CLAUDE.md');
const L = require(HOOK);

const pass = []; const fail = [];
const ok = (g, e) => { pass.push(g); console.log(`  [PASS] ${g}: ${e}`); };
const no = (g, d) => { fail.push(g); console.log(`  [FAIL] ${g}: ${d}`); };

function gate(name, fn) {
  try { fn(); } catch (e) { no(name, e.message); }
}

console.log('CLAUDE.md compaction done-gate (BL-CLAUDEMD-COMPACT)\n');

// --- V-CMD-THRESHOLDS-CONFIGURABLE --------------------------------------
gate('V-CMD-THRESHOLDS-CONFIGURABLE', () => {
  const g = 'V-CMD-THRESHOLDS-CONFIGURABLE';
  const raw = JSON.parse(fs.readFileSync(CFG, 'utf8'));
  for (const k of ['hard', 'margin', 'section_max', 'max_suggestions']) {
    assert(typeof raw[k] === 'number' && raw[k] > 0, `${k} missing/invalid`);
  }
  assert(Array.isArray(raw.protected) && raw.protected.length >= 5,
    'protected list too small');
  const src = fs.readFileSync(HOOK, 'utf8');
  // The hook may carry DEFAULTS as a fallback, but the live values must be
  // read from config -- assert it actually loads the file.
  assert(src.includes('claude_md_thresholds.json'), 'hook never reads config');
  const cfg = L.loadConfig();
  assert(cfg.margin === raw.margin, 'loadConfig ignored the config file');
  ok(g, `hard=${cfg.hard} margin=${cfg.margin} section_max=${cfg.section_max}, `
    + `${cfg.protected.length} protected, loaded from JSON`);
});

// --- V-CMD-CORRUPT-CONFIG-FAILS-SAFE ------------------------------------
gate('V-CMD-CORRUPT-CONFIG-FAILS-SAFE', () => {
  const g = 'V-CMD-CORRUPT-CONFIG-FAILS-SAFE';
  const backup = fs.readFileSync(CFG, 'utf8');
  try {
    fs.writeFileSync(CFG, '{ this is not json', 'utf8');
    const cfg = L.loadConfig();
    assert(cfg.hard === L.DEFAULTS.hard, 'corrupt config did not fall back');
    fs.writeFileSync(CFG, JSON.stringify({ hard: -5, margin: 'x' }), 'utf8');
    const cfg2 = L.loadConfig();
    assert(cfg2.hard === L.DEFAULTS.hard && cfg2.margin === L.DEFAULTS.margin,
      'nonsense values were accepted');
  } finally {
    fs.writeFileSync(CFG, backup, 'utf8');
  }
  ok(g, 'corrupt JSON and nonsense values both fall back to defaults');
});

// --- V-CMD-NAMES-SECTIONS -----------------------------------------------
gate('V-CMD-NAMES-SECTIONS', () => {
  const g = 'V-CMD-NAMES-SECTIONS';
  const cfg = L.loadConfig();
  const big = 'x'.repeat(2000);
  const synthetic = [
    '## Windows Bash Bridge Reliability (MANDATORY)', big, '',
    '## Some Bloated Doctrine', big, '',
    '## Already Delegated', big,
    'See `~/.claude/knowledge_vault/claude-doctrine/x-detail.md`.', '',
    '## Tiny Section', 'one line', '',
  ].join('\n');

  const c = L.candidates(synthetic, cfg);
  const titles = c.map((s) => s.title);
  assert(titles.includes('Some Bloated Doctrine'),
    'did not name the oversized undelegated section');
  assert(!titles.some((t) => t.indexOf('Windows Bash Bridge') !== -1),
    'PROTECTED section was recommended for externalization');
  assert(!titles.includes('Already Delegated'),
    'section with a vault pointer was recommended');
  assert(!titles.includes('Tiny Section'), 'small section was recommended');
  assert(c.length <= cfg.max_suggestions, 'exceeded max_suggestions');
  ok(g, `named [${titles.join(', ')}]; protected + delegated + small excluded`);
});

// --- V-CMD-ADVICE-IS-ALIVE ----------------------------------------------
gate('V-CMD-ADVICE-IS-ALIVE', () => {
  const g = 'V-CMD-ADVICE-IS-ALIVE';
  const src = fs.readFileSync(HOOK, 'utf8');
  const advice = src.slice(src.indexOf('function main'));
  assert(!/trim_claude_md\.py/.test(advice),
    'still prescribes the exhausted trimmer as the remedy');
  assert(/PR-CLAUDE-MD-INDEX-FIRST-001/.test(src),
    'advisory does not cite the addition policy');
  ok(g, 'remedy names sections to move, not the exhausted trimmer');
});

// --- V-CMD-HOOK-FAILS-OPEN ----------------------------------------------
gate('V-CMD-HOOK-FAILS-OPEN', () => {
  const g = 'V-CMD-HOOK-FAILS-OPEN';
  const out = execFileSync(process.execPath, [HOOK],
    { input: '{}', encoding: 'utf8', timeout: 8000 });
  const parsed = JSON.parse(out);
  assert(parsed.continue === true, 'hook did not return continue:true');
  ok(g, `real invocation returns continue:true (${out.length} bytes)`);
});

// --- V-CMD-UNDER-TARGET -------------------------------------------------
gate('V-CMD-UNDER-TARGET', () => {
  const g = 'V-CMD-UNDER-TARGET';
  const cfg = L.loadConfig();
  const n = fs.readFileSync(CM, 'utf8').length;
  assert(n < cfg.margin,
    `CLAUDE.md = ${n} chars, target < ${cfg.margin}`);
  ok(g, `CLAUDE.md = ${n} chars, ${cfg.margin - n} under the ${cfg.margin} `
    + `target (${cfg.hard - n} under the hard limit)`);
});

// --- V-CMD-POINTERS-RESOLVE ---------------------------------------------
gate('V-CMD-POINTERS-RESOLVE', () => {
  const g = 'V-CMD-POINTERS-RESOLVE';
  const text = fs.readFileSync(CM, 'utf8');
  const refs = [...new Set(
    (text.match(/`~\/\.claude\/[^`]+\.md`/g) || [])
      .map((s) => s.replace(/`/g, '')))];
  const dead = refs.filter((r) => !fs.existsSync(
    path.join(os.homedir(), r.replace('~/', ''))));
  assert(refs.length >= 8, `only ${refs.length} pointers found`);
  assert(dead.length === 0, `dead pointers: ${dead.join(', ')}`);
  ok(g, `${refs.length} vault pointers, all resolve on disk`);
});

const total = pass.length + fail.length;
console.log(`\nCMD_PASS=${pass.length}/${total}  threshold=${total}/${total}`);
if (fail.length) { console.log(`FAILING: ${fail.join(', ')}`); }
process.exit(fail.length ? 1 : 0);
