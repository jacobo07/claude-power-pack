#!/usr/bin/env node
'use strict';
// ---------------------------------------------------------------------------
// claude_md_linter_stop.js - Stop-hook size advisory for ~/.claude/CLAUDE.md
//   (CLAUDE.md Router M3, 2026-06-04, BL-CLAUDEMD-ROUTER)
//   (C2/C3 auto-compaction upgrade, 2026-07-26, BL-CLAUDEMD-COMPACT)
//
// v1 counted chars correctly and then told the agent to run
// `trim_claude_md.py`. By 2026-07-26 that trimmer reclaimed ZERO -- it removes
// provenance prose and that had already been harvested on 2026-07-04. So the
// gate fired accurately and prescribed something that could not work: dead
// advice is worse than no advice, because it looks like a remedy.
//
// v2 names WHAT TO MOVE. It measures every "## " section, skips the protected
// ones, and reports the largest sections that carry no vault pointer -- the
// real, actionable next step (PR-CLAUDE-MD-INDEX-FIRST-001).
//
// Thresholds live in vault/config/claude_md_thresholds.json, never here
// (C2 contract: configurable, not hardcoded). Missing/corrupt config -> the
// built-in defaults below, so the hook degrades to v1 behaviour, never off.
//
// Cheap by contract: two small file reads, no subprocess, no network.
// Fail-open absolute: any error -> {continue:true} and silence.
// ---------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const CM = path.join(HOME, '.claude', 'CLAUDE.md');
const CFG = path.join(HOME, '.claude', 'skills', 'claude-power-pack',
  'vault', 'config', 'claude_md_thresholds.json');
const BOM = 0xFEFF;

const DEFAULTS = {
  hard: 40000,
  margin: 38000,
  section_max: 900,
  max_suggestions: 3,
  protected: [
    'Windows Bash Bridge Reliability',
    'Parallel Subagent Limit on Windows',
    'HARD RULES',
    'Environment Awareness',
    'Critical Rules',
    'Reality Contract',
    'Token Efficiency',
    'PP Activation Criteria',
    'SDD-OS',
  ],
  destination: '~/.claude/knowledge_vault/claude-doctrine/',
};

function emit(o) {
  try { process.stdout.write(JSON.stringify(o)); } catch (e) { void e; }
}

function loadConfig() {
  try {
    const raw = JSON.parse(fs.readFileSync(CFG, 'utf8'));
    const cfg = Object.assign({}, DEFAULTS, raw);
    // A corrupt threshold must not silently disable the gate.
    for (const k of ['hard', 'margin', 'section_max', 'max_suggestions']) {
      if (typeof cfg[k] !== 'number' || !(cfg[k] > 0)) { cfg[k] = DEFAULTS[k]; }
    }
    if (!Array.isArray(cfg.protected)) { cfg.protected = DEFAULTS.protected; }
    return cfg;
  } catch (e) { void e; return DEFAULTS; }
}

// Split on level-2 headings; "### " stays with its parent section.
function sections(text) {
  const lines = text.split('\n');
  const marks = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('## ')) { marks.push(i); }
  }
  marks.push(lines.length);
  const out = [];
  for (let m = 0; m < marks.length - 1; m++) {
    const a = marks[m]; const b = marks[m + 1];
    const body = lines.slice(a, b).join('\n');
    out.push({ title: lines[a].slice(3).trim(), chars: body.length, body });
  }
  return out;
}

function hasPointer(body) {
  return /knowledge_vault\/[\w./-]+\.md|\.claude\/commands\/[\w-]+\.md/.test(body);
}

function isProtected(title, list) {
  return list.some((p) => title.indexOf(p) !== -1);
}

function candidates(text, cfg) {
  return sections(text)
    .filter((s) => s.chars > cfg.section_max)
    .filter((s) => !isProtected(s.title, cfg.protected))
    .filter((s) => !hasPointer(s.body))
    .sort((a, b) => b.chars - a.chars)
    .slice(0, cfg.max_suggestions);
}

function main() {
  try { fs.readFileSync(0, 'utf8'); } catch (e) { void e; }   // drain stdin

  const cfg = loadConfig();
  let text;
  try {
    text = fs.readFileSync(CM, 'utf8');
    if (text.charCodeAt(0) === BOM) { text = text.slice(1); }
  } catch (e) { void e; emit({ continue: true }); return; }   // no file -> silent

  const n = text.length;
  if (n < cfg.margin) { emit({ continue: true }); return; }

  const level = n >= cfg.hard ? 'ALERT' : 'WARN';
  const limit = n >= cfg.hard ? cfg.hard : cfg.margin;
  const lines = [
    `[claude_md_linter] ${level}: ~/.claude/CLAUDE.md = ${n} chars `
    + `(>= ${limit}).`,
  ];

  const cands = candidates(text, cfg);
  if (cands.length) {
    lines.push('Move the EXPLANATION of these to the vault, keep the TRIGGER '
      + '+ a pointer in CLAUDE.md (PR-CLAUDE-MD-INDEX-FIRST-001):');
    for (const c of cands) {
      lines.push(`  - "${c.title}" (${c.chars} chars, no vault pointer)`);
    }
    lines.push(`Destination: ${cfg.destination}`);
    lines.push('Protected sections are excluded from this list and must never '
      + 'be externalized -- a trigger behind a pointer is a rule that stops '
      + 'existing.');
  } else {
    lines.push('No unprotected section above '
      + `${cfg.section_max} chars lacks a vault pointer -- the remaining bulk `
      + 'is protected always-on doctrine. Reduce by retiring a rule, not by '
      + 'externalizing a trigger.');
  }

  emit({ continue: true, additionalContext: lines.join('\n') });
}

// Run as a hook; expose the pure parts when required as a module so the
// recommendation logic is testable against synthetic text without touching
// the real ~/.claude/CLAUDE.md.
if (require.main === module) {
  main();
} else {
  module.exports = {
    DEFAULTS, loadConfig, sections, hasPointer, isProtected, candidates,
  };
}
